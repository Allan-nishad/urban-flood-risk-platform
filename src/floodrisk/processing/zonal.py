"""
Zonal Geospatial Feature Extraction Engine
Performs memory-safe, windowed raster extraction across 1-km equal-area grid cells.
Uses exact vector geometry masking (pixel-center inclusion; all_touched=False)
to eliminate rectangular bounding-box edge effects and pixel leakage.
Retains native source resolutions and provides complete feature-level provenance metadata.
Strictly disclaims that resampled rainfall creates localized spatial information.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds, transform as window_transform
from rasterio.features import geometry_mask
from shapely.geometry import box, Polygon, MultiPolygon, mapping

from ..spatial.crs import ensure_crs, get_transformer, WGS84_CRS, DEFAULT_ANALYSIS_CRS


@dataclass
class GridFeatureMetadata:
    """Rigorous lineage metadata for every derived grid feature."""
    grid_id: str
    feature_name: str
    feature_value: float
    units: str
    source_dataset: str
    native_resolution: str
    processing_method: str
    aggregation_statistic: str
    nodata_handling: str
    spatial_precision_note: str
    extracted_at: str


@dataclass
class CategoricalZonalResult:
    """Detailed pixel statistics for categorical raster extractions (e.g. land cover)."""
    grid_id: str
    total_cell_pixels: int
    valid_pixel_count: int
    nodata_pixel_count: int
    valid_pixel_fraction: float
    class_counts: Dict[int, int]
    class_fractions: Dict[int, float]
    fraction_built_up: float
    fraction_water_bodies: float
    features: List[GridFeatureMetadata]


@dataclass
class ContinuousZonalResult:
    """Detailed statistics for continuous raster extractions (e.g. DEM, Upstream Area)."""
    grid_id: str
    total_cell_pixels: int
    valid_pixel_count: int
    nodata_pixel_count: int
    valid_pixel_fraction: float
    mean: float
    min: float
    max: float
    std: float
    features: List[GridFeatureMetadata]


class RasterZonalExtractor:
    """
    Memory-efficient windowed raster extraction and zonal aggregation engine.
    Extracts native sub-arrays using integer enclosing windows and applies exact
    vector geometry masks (all_touched=False for pixel-center inclusion).
    Completely eliminates polygon-window edge effects and pixel leakage.
    """

    def __init__(self, raster_path: Union[str, Path], source_dataset_name: str, native_resolution: str):
        self.raster_path = Path(raster_path)
        if not self.raster_path.is_file():
            raise FileNotFoundError(f"Raster file not found: {self.raster_path.resolve()}")

        self.source_dataset_name = source_dataset_name
        self.native_resolution = native_resolution
        self.src = rasterio.open(self.raster_path)
        self.crs = self.src.crs
        self.nodata = self.src.nodatavals[0] if self.src.nodatavals else None

        # Transformer from analysis CRS (EPSG:6933) to native raster CRS
        self.transformer = get_transformer(DEFAULT_ANALYSIS_CRS, str(self.crs))

    def close(self):
        if self.src and not self.src.closed:
            self.src.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def transform_geometry_to_native(
        self,
        geom_6933: Union[Polygon, MultiPolygon]
    ) -> Union[Polygon, MultiPolygon]:
        """Transform geometry coordinates from EPSG:6933 to the raster's native CRS."""
        if geom_6933.is_empty:
            return geom_6933

        if isinstance(geom_6933, Polygon):
            coords = [self.transformer.transform(x, y) for x, y in geom_6933.exterior.coords]
            holes = []
            for h in geom_6933.interiors:
                holes.append([self.transformer.transform(x, y) for x, y in h.coords])
            return Polygon(coords, holes)
        elif isinstance(geom_6933, MultiPolygon):
            polys = []
            for p in geom_6933.geoms:
                coords = [self.transformer.transform(x, y) for x, y in p.exterior.coords]
                holes = [[self.transformer.transform(x, y) for x, y in h.coords] for h in p.interiors]
                polys.append(Polygon(coords, holes))
            return MultiPolygon(polys)
        raise TypeError(f"Unsupported geometry type: {type(geom_6933)}")

    def read_window_for_geometry(
        self,
        geom_6933: Union[Polygon, MultiPolygon],
        band: int = 1,
        all_touched: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, Optional[float]]:
        """
        Extract windowed raster data and exact inside-geometry mask.
        Transforms geometry to raster native CRS, calculates integer enclosing window,
        reads pixels, and evaluates exact pixel-center inclusion (all_touched=False).

        Returns:
            data: 2D numpy array of raster values in integer enclosing window.
            inside_mask: 2D boolean array (True where pixel center falls inside geometry).
            nodata: Nodata value of the raster.
        """
        poly_native = self.transform_geometry_to_native(geom_6933)
        if poly_native.is_empty:
            return np.empty((0, 0)), np.empty((0, 0), dtype=bool), self.nodata

        p_minx, p_miny, p_maxx, p_maxy = poly_native.bounds

        # Raw floating window from bounds
        raw_win = from_bounds(p_minx, p_miny, p_maxx, p_maxy, transform=self.src.transform)

        # Expand to integer pixel enclosing window
        c_off = int(math.floor(raw_win.col_off))
        r_off = int(math.floor(raw_win.row_off))
        w = int(math.ceil(raw_win.col_off + raw_win.width)) - c_off
        h = int(math.ceil(raw_win.row_off + raw_win.height)) - r_off

        int_win = rasterio.windows.Window(c_off, r_off, max(w, 1), max(h, 1))
        win_trans = window_transform(int_win, self.src.transform)

        # Boundless read with fill value = nodata
        fill_val = self.nodata if self.nodata is not None else 0
        data = self.src.read(band, window=int_win, boundless=True, fill_value=fill_val)

        # Geometry mask: invert=True means True for pixels whose center is inside the polygon
        inside_mask = geometry_mask(
            [mapping(poly_native)],
            out_shape=data.shape,
            transform=win_trans,
            all_touched=all_touched,
            invert=True
        )

        return data, inside_mask, self.nodata

    def read_window_for_cell_bounds(
        self,
        minx_6933: float,
        miny_6933: float,
        maxx_6933: float,
        maxy_6933: float,
        band: int = 1,
        all_touched: bool = False,
        mask_outside: bool = True
    ) -> Tuple[np.ndarray, Optional[float]]:
        """
        Extract windowed raster data for cell bounding box coordinates.
        Uses exact polygon masking so pixels outside the cell polygon are set to nodata.
        Backward-compatible signature returning (data, nodata).
        """
        geom = box(minx_6933, miny_6933, maxx_6933, maxy_6933)
        data, inside_mask, nodata = self.read_window_for_geometry(geom, band=band, all_touched=all_touched)

        if mask_outside:
            fill = nodata if nodata is not None else 0
            masked_data = np.where(inside_mask, data, fill)
            return masked_data, nodata
        return data, nodata

    def extract_categorical_zonal_stats(
        self,
        geom_6933: Union[Polygon, MultiPolygon],
        grid_id: str,
        band: int = 1,
        all_touched: bool = False,
        nodata_value: Optional[float] = None
    ) -> CategoricalZonalResult:
        """
        Extract comprehensive categorical statistics (e.g. land cover classes)
        with exact pixel-center geometry masking.
        """
        data, inside_mask, default_nodata = self.read_window_for_geometry(
            geom_6933, band=band, all_touched=all_touched
        )
        eff_nodata = nodata_value if nodata_value is not None else default_nodata

        total_pixels = int(np.sum(inside_mask))
        if total_pixels == 0:
            return CategoricalZonalResult(
                grid_id=grid_id,
                total_cell_pixels=0,
                valid_pixel_count=0,
                nodata_pixel_count=0,
                valid_pixel_fraction=0.0,
                class_counts={},
                class_fractions={},
                fraction_built_up=0.0,
                fraction_water_bodies=0.0,
                features=[]
            )

        # Inside pixels valid mask
        if eff_nodata is not None:
            valid_mask = inside_mask & (data != eff_nodata) & (data > 0)
        else:
            valid_mask = inside_mask & (data > 0)

        valid_count = int(np.sum(valid_mask))
        nodata_count = int(total_pixels - valid_count)
        valid_frac = float(valid_count / total_pixels) if total_pixels > 0 else 0.0

        cell_valid_data = data[valid_mask]
        built_up_count = int(np.sum(cell_valid_data == 50))
        water_count = int(np.sum(cell_valid_data == 80))

        frac_built = float(built_up_count / valid_count) if valid_count > 0 else 0.0
        frac_water = float(water_count / valid_count) if valid_count > 0 else 0.0

        # Unique classes
        classes, counts = np.unique(cell_valid_data, return_counts=True)
        class_counts = {int(c): int(cnt) for c, cnt in zip(classes, counts)}
        class_fractions = {int(c): float(cnt / valid_count) for c, cnt in zip(classes, counts)} if valid_count > 0 else {}

        now_ts = datetime.now(timezone.utc).isoformat()
        features = [
            GridFeatureMetadata(
                grid_id=grid_id,
                feature_name="fraction_built_up",
                feature_value=round(frac_built, 4),
                units="fraction [0-1]",
                source_dataset=self.source_dataset_name,
                native_resolution=self.native_resolution,
                processing_method="Exact polygon-masked pixel-center histogram ratio",
                aggregation_statistic="fraction (Class 50)",
                nodata_handling=f"Filtered NoData pixels ({eff_nodata})",
                spatial_precision_note="Built-up urban density inside exact 1-km cell polygon",
                extracted_at=now_ts
            ),
            GridFeatureMetadata(
                grid_id=grid_id,
                feature_name="fraction_water_bodies",
                feature_value=round(frac_water, 4),
                units="fraction [0-1]",
                source_dataset=self.source_dataset_name,
                native_resolution=self.native_resolution,
                processing_method="Exact polygon-masked pixel-center histogram ratio",
                aggregation_statistic="fraction (Class 80)",
                nodata_handling=f"Filtered NoData pixels ({eff_nodata})",
                spatial_precision_note="Water body footprint inside exact 1-km cell polygon",
                extracted_at=now_ts
            )
        ]

        return CategoricalZonalResult(
            grid_id=grid_id,
            total_cell_pixels=total_pixels,
            valid_pixel_count=valid_count,
            nodata_pixel_count=nodata_count,
            valid_pixel_fraction=round(valid_frac, 6),
            class_counts=class_counts,
            class_fractions=class_fractions,
            fraction_built_up=round(frac_built, 4),
            fraction_water_bodies=round(frac_water, 4),
            features=features
        )

    def extract_continuous_zonal_stats(
        self,
        geom_6933: Union[Polygon, MultiPolygon],
        grid_id: str,
        feature_prefix: str,
        units: str,
        band: int = 1,
        all_touched: bool = False,
        nodata_value: Optional[float] = None
    ) -> ContinuousZonalResult:
        """
        Extract continuous summary statistics (mean, min, max, std)
        with exact pixel-center geometry masking.
        """
        data, inside_mask, default_nodata = self.read_window_for_geometry(
            geom_6933, band=band, all_touched=all_touched
        )
        eff_nodata = nodata_value if nodata_value is not None else default_nodata

        total_pixels = int(np.sum(inside_mask))
        if total_pixels == 0:
            return ContinuousZonalResult(
                grid_id=grid_id,
                total_cell_pixels=0,
                valid_pixel_count=0,
                nodata_pixel_count=0,
                valid_pixel_fraction=0.0,
                mean=np.nan, min=np.nan, max=np.nan, std=np.nan,
                features=[]
            )

        if eff_nodata is not None:
            valid_mask = inside_mask & (data != eff_nodata) & ~np.isnan(data)
        else:
            valid_mask = inside_mask & ~np.isnan(data)

        valid_count = int(np.sum(valid_mask))
        nodata_count = int(total_pixels - valid_count)
        valid_frac = float(valid_count / total_pixels) if total_pixels > 0 else 0.0

        cell_valid_data = data[valid_mask]
        now_ts = datetime.now(timezone.utc).isoformat()

        if valid_count == 0:
            return ContinuousZonalResult(
                grid_id=grid_id,
                total_cell_pixels=total_pixels,
                valid_pixel_count=0,
                nodata_pixel_count=nodata_count,
                valid_pixel_fraction=0.0,
                mean=np.nan, min=np.nan, max=np.nan, std=np.nan,
                features=[]
            )

        mean_val = float(np.mean(cell_valid_data))
        min_val = float(np.min(cell_valid_data))
        max_val = float(np.max(cell_valid_data))
        std_val = float(np.std(cell_valid_data)) if valid_count > 1 else 0.0

        features = [
            GridFeatureMetadata(
                grid_id=grid_id,
                feature_name=f"{feature_prefix}_mean",
                feature_value=round(mean_val, 2),
                units=units,
                source_dataset=self.source_dataset_name,
                native_resolution=self.native_resolution,
                processing_method="Exact polygon-masked windowed mean",
                aggregation_statistic="mean",
                nodata_handling=f"Filtered NoData pixels ({eff_nodata})",
                spatial_precision_note=f"Mean {feature_prefix} within exact 1-km cell footprint",
                extracted_at=now_ts
            ),
            GridFeatureMetadata(
                grid_id=grid_id,
                feature_name=f"{feature_prefix}_min",
                feature_value=round(min_val, 2),
                units=units,
                source_dataset=self.source_dataset_name,
                native_resolution=self.native_resolution,
                processing_method="Exact polygon-masked windowed min",
                aggregation_statistic="min",
                nodata_handling=f"Filtered NoData pixels ({eff_nodata})",
                spatial_precision_note=f"Minimum {feature_prefix} within exact 1-km cell footprint",
                extracted_at=now_ts
            ),
            GridFeatureMetadata(
                grid_id=grid_id,
                feature_name=f"{feature_prefix}_max",
                feature_value=round(max_val, 2),
                units=units,
                source_dataset=self.source_dataset_name,
                native_resolution=self.native_resolution,
                processing_method="Exact polygon-masked windowed max",
                aggregation_statistic="max",
                nodata_handling=f"Filtered NoData pixels ({eff_nodata})",
                spatial_precision_note=f"Maximum {feature_prefix} within exact 1-km cell footprint",
                extracted_at=now_ts
            ),
            GridFeatureMetadata(
                grid_id=grid_id,
                feature_name=f"{feature_prefix}_std",
                feature_value=round(std_val, 2),
                units=units,
                source_dataset=self.source_dataset_name,
                native_resolution=self.native_resolution,
                processing_method="Exact polygon-masked windowed std",
                aggregation_statistic="std",
                nodata_handling=f"Filtered NoData pixels ({eff_nodata})",
                spatial_precision_note=f"Standard deviation of {feature_prefix} within exact 1-km cell footprint",
                extracted_at=now_ts
            )
        ]

        return ContinuousZonalResult(
            grid_id=grid_id,
            total_cell_pixels=total_pixels,
            valid_pixel_count=valid_count,
            nodata_pixel_count=nodata_count,
            valid_pixel_fraction=round(valid_frac, 6),
            mean=round(mean_val, 2),
            min=round(min_val, 2),
            max=round(max_val, 2),
            std=round(std_val, 2),
            features=features
        )


def compute_terrain_zonal_features(
    data: np.ndarray,
    nodata: Optional[float],
    grid_id: str,
    inside_mask: Optional[np.ndarray] = None
) -> List[GridFeatureMetadata]:
    """
    Extract statistical terrain descriptors from SRTM 30m windowed pixels.
    Supports optional inside_mask for exact polygon pixel filtering.
    """
    if inside_mask is not None:
        if nodata is not None:
            valid_mask = inside_mask & (data != nodata) & ~np.isnan(data)
        else:
            valid_mask = inside_mask & ~np.isnan(data)
    else:
        if nodata is not None:
            valid_mask = (data != nodata) & ~np.isnan(data)
        else:
            valid_mask = ~np.isnan(data)

    valid_pixels = data[valid_mask]
    now_ts = datetime.now(timezone.utc).isoformat()

    if len(valid_pixels) == 0:
        return [
            GridFeatureMetadata(
                grid_id=grid_id,
                feature_name="elevation_mean_m",
                feature_value=np.nan,
                units="metres",
                source_dataset="SRTM GL1 30m DEM",
                native_resolution="1 arc-second (~30 m)",
                processing_method="Windowed raster aggregation",
                aggregation_statistic="mean",
                nodata_handling="Filtered NoData pixels (-32768)",
                spatial_precision_note="Captures regional macro-topography inside 1-km cell",
                extracted_at=now_ts
            )
        ]

    elev_mean = float(np.mean(valid_pixels))
    elev_min = float(np.min(valid_pixels))
    elev_max = float(np.max(valid_pixels))
    elev_std = float(np.std(valid_pixels)) if len(valid_pixels) > 1 else 0.0

    return [
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="elevation_mean_m",
            feature_value=round(elev_mean, 2),
            units="metres",
            source_dataset="SRTM GL1 30m DEM",
            native_resolution="1 arc-second (~30 m)",
            processing_method="Windowed raster aggregation",
            aggregation_statistic="mean",
            nodata_handling="Filtered NoData pixels (-32768)",
            spatial_precision_note="Captures regional macro-topography inside 1-km cell",
            extracted_at=now_ts
        ),
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="elevation_min_m",
            feature_value=round(elev_min, 2),
            units="metres",
            source_dataset="SRTM GL1 30m DEM",
            native_resolution="1 arc-second (~30 m)",
            processing_method="Windowed raster aggregation",
            aggregation_statistic="min",
            nodata_handling="Filtered NoData pixels (-32768)",
            spatial_precision_note="Local drainage depression bottom within 1-km cell",
            extracted_at=now_ts
        ),
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="elevation_max_m",
            feature_value=round(elev_max, 2),
            units="metres",
            source_dataset="SRTM GL1 30m DEM",
            native_resolution="1 arc-second (~30 m)",
            processing_method="Windowed raster aggregation",
            aggregation_statistic="max",
            nodata_handling="Filtered NoData pixels (-32768)",
            spatial_precision_note="Local topographic ridge within 1-km cell",
            extracted_at=now_ts
        ),
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="elevation_std_m",
            feature_value=round(elev_std, 2),
            units="metres",
            source_dataset="SRTM GL1 30m DEM",
            native_resolution="1 arc-second (~30 m)",
            processing_method="Windowed raster aggregation",
            aggregation_statistic="std",
            nodata_handling="Filtered NoData pixels (-32768)",
            spatial_precision_note="Terrain roughness / vertical relief inside 1-km cell",
            extracted_at=now_ts
        )
    ]


def compute_hydrology_zonal_features(
    data: np.ndarray,
    nodata: Optional[float],
    grid_id: str,
    inside_mask: Optional[np.ndarray] = None
) -> List[GridFeatureMetadata]:
    """
    Extract upstream contributing area (upa) statistics from MERIT Hydro 90m windowed pixels.
    Supports optional inside_mask for exact polygon pixel filtering.
    """
    if inside_mask is not None:
        if nodata is not None:
            valid_mask = inside_mask & (data != nodata) & (data >= 0.0) & ~np.isnan(data)
        else:
            valid_mask = inside_mask & (data >= 0.0) & ~np.isnan(data)
    else:
        if nodata is not None:
            valid_mask = (data != nodata) & (data >= 0.0) & ~np.isnan(data)
        else:
            valid_mask = (data >= 0.0) & ~np.isnan(data)

    valid_pixels = data[valid_mask]
    now_ts = datetime.now(timezone.utc).isoformat()

    if len(valid_pixels) == 0:
        return []

    upa_max = float(np.max(valid_pixels))
    upa_mean = float(np.mean(valid_pixels))

    return [
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="upa_max_sqkm",
            feature_value=round(upa_max, 3),
            units="km^2",
            source_dataset="MERIT Hydro v1.0.1 (upa band)",
            native_resolution="3 arc-seconds (~90 m)",
            processing_method="Windowed raster zonal maximum",
            aggregation_statistic="max",
            nodata_handling="Filtered nodata (-9999.0)",
            spatial_precision_note="Peak upstream contributing drainage area crossing cell",
            extracted_at=now_ts
        ),
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="upa_mean_sqkm",
            feature_value=round(upa_mean, 3),
            units="km^2",
            source_dataset="MERIT Hydro v1.0.1 (upa band)",
            native_resolution="3 arc-seconds (~90 m)",
            processing_method="Windowed raster zonal mean",
            aggregation_statistic="mean",
            nodata_handling="Filtered nodata (-9999.0)",
            spatial_precision_note="Mean regional drainage accumulation inside 1-km cell",
            extracted_at=now_ts
        )
    ]


def compute_landcover_zonal_features(
    data: np.ndarray,
    nodata: Optional[float],
    grid_id: str,
    inside_mask: Optional[np.ndarray] = None
) -> List[GridFeatureMetadata]:
    """
    Extract categorical surface cover fractions from ESA WorldCover 10m windowed pixels.
    Class 50: Built-up land cover.
    Class 80: Permanent open water bodies.
    Supports optional inside_mask for exact polygon pixel filtering.
    """
    if inside_mask is not None:
        if nodata is not None:
            valid_mask = inside_mask & (data != nodata) & (data > 0)
        else:
            valid_mask = inside_mask & (data > 0)
    else:
        if nodata is not None:
            valid_mask = (data != nodata) & (data > 0)
        else:
            valid_mask = (data > 0)

    valid_pixels = data[valid_mask]
    now_ts = datetime.now(timezone.utc).isoformat()
    total_valid = len(valid_pixels)

    if total_valid == 0:
        return []

    built_up_count = np.sum(valid_pixels == 50)
    water_count = np.sum(valid_pixels == 80)

    fraction_built_up = float(built_up_count / total_valid)
    fraction_water = float(water_count / total_valid)

    return [
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="fraction_built_up",
            feature_value=round(fraction_built_up, 4),
            units="fraction [0-1]",
            source_dataset="ESA WorldCover 10m v200",
            native_resolution="10 metres",
            processing_method="Categorical pixel histogram ratio",
            aggregation_statistic="fraction (Class 50)",
            nodata_handling="Filtered NoData pixels (0)",
            spatial_precision_note="Built-up urban density inside 1-km cell",
            extracted_at=now_ts
        ),
        GridFeatureMetadata(
            grid_id=grid_id,
            feature_name="fraction_water_bodies",
            feature_value=round(fraction_water, 4),
            units="fraction [0-1]",
            source_dataset="ESA WorldCover 10m v200",
            native_resolution="10 metres",
            processing_method="Categorical pixel histogram ratio",
            aggregation_statistic="fraction (Class 80)",
            nodata_handling="Filtered NoData pixels (0)",
            spatial_precision_note="Lake / retention reservoir water body footprint inside 1-km cell",
            extracted_at=now_ts
        )
    ]


def create_rainfall_grid_feature(
    precipitation_mm: float,
    grid_id: str,
    source_dataset: str = "NASA GPM IMERG V07B",
    native_resolution: str = "0.1 degree (~10 km)"
) -> GridFeatureMetadata:
    """
    Map verified accumulated rainfall depth to a 1-km grid cell.
    Explicitly includes scientific disclaimer that spatial mapping does NOT create new spatial information.
    """
    now_ts = datetime.now(timezone.utc).isoformat()
    return GridFeatureMetadata(
        grid_id=grid_id,
        feature_name="daily_precipitation_mm",
        feature_value=round(float(precipitation_mm), 2),
        units="mm",
        source_dataset=source_dataset,
        native_resolution=native_resolution,
        processing_method="Area-weighted zonal intersection",
        aggregation_statistic="weighted_mean",
        nodata_handling="Validated non-negative physical values",
        spatial_precision_note=(
            "DISCLAIMER: Cell rainfall reflects regional sampling of the native 10-km satellite footprint. "
            "Resampling to a 1-km grid provides indexing alignment only and does NOT create micro-convective spatial information."
        ),
        extracted_at=now_ts
    )


def extract_grid_features_batch(
    grid_gdf: gpd.GeoDataFrame,
    landcover_raster_path: Union[str, Path],
    output_parquet_path: Optional[Union[str, Path]] = None,
    all_touched: bool = False
) -> pd.DataFrame:
    """
    Batch feature extraction pipeline for 1-km equal-area grid cells.
    Applies exact geometry masking (all_touched=False for pixel-center inclusion).
    Computes per-cell valid/nodata quality columns and categorical fractions.
    """
    lc_path = Path(landcover_raster_path)
    if not lc_path.is_file():
        raise FileNotFoundError(f"Land cover raster not found: {lc_path}")

    records = []
    with RasterZonalExtractor(lc_path, source_dataset_name="ESA WorldCover 10m v200", native_resolution="10 m") as extractor:
        for _, row in grid_gdf.iterrows():
            grid_id = str(row["grid_id"])
            geom = row.geometry

            # Extract exact categorical statistics
            res = extractor.extract_categorical_zonal_stats(
                geom_6933=geom,
                grid_id=grid_id,
                all_touched=all_touched,
                nodata_value=0.0
            )

            domain_frac = float(row.get("fraction_inside_domain", row.get("fraction_inside_boundary", 1.0)))

            rec = {
                "grid_id": grid_id,
                "col_idx": int(row["col_idx"]),
                "row_idx": int(row["row_idx"]),
                "centroid_lon": float(row["centroid_lon"]),
                "centroid_lat": float(row["centroid_lat"]),
                "fraction_inside_domain": domain_frac,
                "fraction_inside_boundary": domain_frac,
                "coverage_class": str(row.get("coverage_class", "fully_inside")),
                "geodesic_area_sqm": float(row.get("geodesic_area_sqm", 1000000.0)),
                "valid_pixel_count": int(res.valid_pixel_count),
                "nodata_pixel_count": int(res.nodata_pixel_count),
                "valid_pixel_fraction": float(res.valid_pixel_fraction),
                "fraction_built_up": float(res.fraction_built_up),
                "fraction_water_bodies": float(res.fraction_water_bodies)
            }
            records.append(rec)

    df_out = pd.DataFrame(records)

    if output_parquet_path:
        out_p = Path(output_parquet_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_parquet(out_p, index=False)

    return df_out


def extract_multimodal_grid_features(
    grid_gdf: gpd.GeoDataFrame,
    landcover_raster_path: Optional[Union[str, Path]] = None,
    srtm_raster_path: Optional[Union[str, Path]] = None,
    merit_hydro_raster_path: Optional[Union[str, Path]] = None,
    existing_features_df: Optional[pd.DataFrame] = None,
    output_parquet_path: Optional[Union[str, Path]] = None,
    all_touched: bool = False
) -> pd.DataFrame:
    """
    Multimodal feature extraction pipeline for 1-km equal-area grid cells.
    Integrates ESA WorldCover 10m land cover, SRTM GL1 30m DEM elevation,
    and MERIT Hydro 90m upstream contributing area (upa).
    Enforces exact pixel-center geometry masking (all_touched=False).
    Missing/unacquired layers are kept explicitly pending as NaN.
    """
    # 1. Base table from existing features or freshly extracted WorldCover
    if existing_features_df is not None:
        df_base = existing_features_df.copy()
    elif landcover_raster_path and Path(landcover_raster_path).is_file():
        df_base = extract_grid_features_batch(
            grid_gdf=grid_gdf,
            landcover_raster_path=landcover_raster_path,
            all_touched=all_touched
        )
    else:
        # Construct base attributes from grid GeoDataFrame
        base_records = []
        for _, row in grid_gdf.iterrows():
            gid = str(row["grid_id"])
            d_frac = float(row.get("fraction_inside_domain", row.get("fraction_inside_boundary", 1.0)))
            base_records.append({
                "grid_id": gid,
                "col_idx": int(row["col_idx"]),
                "row_idx": int(row["row_idx"]),
                "centroid_lon": float(row["centroid_lon"]),
                "centroid_lat": float(row["centroid_lat"]),
                "fraction_inside_domain": d_frac,
                "fraction_inside_boundary": d_frac,
                "coverage_class": str(row.get("coverage_class", "fully_inside")),
                "geodesic_area_sqm": float(row.get("geodesic_area_sqm", 1000000.0)),
                "fraction_built_up": np.nan,
                "fraction_water_bodies": np.nan,
                "valid_pixel_count": np.nan,
                "nodata_pixel_count": np.nan,
                "valid_pixel_fraction": np.nan
            })
        df_base = pd.DataFrame(base_records)

    # 2. Extract SRTM GL1 30m terrain features if available
    if srtm_raster_path and Path(srtm_raster_path).is_file():
        srtm_p = Path(srtm_raster_path)
        srtm_records = []
        with RasterZonalExtractor(srtm_p, source_dataset_name="SRTM GL1 30m DEM", native_resolution="1 arc-second (~30 m)") as ext:
            for _, row in grid_gdf.iterrows():
                gid = str(row["grid_id"])
                res = ext.extract_continuous_zonal_stats(
                    geom_6933=row.geometry,
                    grid_id=gid,
                    feature_prefix="elevation",
                    units="metres",
                    nodata_value=-32768.0,
                    all_touched=all_touched
                )
                srtm_records.append({
                    "grid_id": gid,
                    "elevation_mean_m": float(res.mean),
                    "elevation_min_m": float(res.min),
                    "elevation_max_m": float(res.max),
                    "elevation_std_m": float(res.std),
                    "elevation_valid_pixel_count": int(res.valid_pixel_count),
                    "elevation_nodata_pixel_count": int(res.nodata_pixel_count),
                    "elevation_valid_pixel_fraction": float(res.valid_pixel_fraction)
                })
        df_srtm = pd.DataFrame(srtm_records)
        df_merged = pd.merge(df_base, df_srtm, on="grid_id", how="left")
    else:
        # Explicit pending placeholder
        df_merged = df_base.copy()
        df_merged["elevation_mean_m"] = np.nan
        df_merged["elevation_min_m"] = np.nan
        df_merged["elevation_max_m"] = np.nan
        df_merged["elevation_std_m"] = np.nan
        df_merged["elevation_valid_pixel_count"] = np.nan
        df_merged["elevation_nodata_pixel_count"] = np.nan
        df_merged["elevation_valid_pixel_fraction"] = np.nan

    # 3. Extract MERIT Hydro 90m features if available
    if merit_hydro_raster_path and Path(merit_hydro_raster_path).is_file():
        mh_p = Path(merit_hydro_raster_path)
        mh_records = []
        with RasterZonalExtractor(mh_p, source_dataset_name="MERIT Hydro v1.0.1 (upa band)", native_resolution="3 arc-seconds (~90 m)") as ext:
            for _, row in grid_gdf.iterrows():
                gid = str(row["grid_id"])
                res = ext.extract_continuous_zonal_stats(
                    geom_6933=row.geometry,
                    grid_id=gid,
                    feature_prefix="upa",
                    units="km^2",
                    nodata_value=-9999.0,
                    all_touched=all_touched
                )
                mh_records.append({
                    "grid_id": gid,
                    "upa_mean_sqkm": float(res.mean),
                    "upa_max_sqkm": float(res.max),
                    "upa_valid_pixel_count": int(res.valid_pixel_count),
                    "upa_nodata_pixel_count": int(res.nodata_pixel_count),
                    "upa_valid_pixel_fraction": float(res.valid_pixel_fraction)
                })
        df_mh = pd.DataFrame(mh_records)
        df_final = pd.merge(df_merged, df_mh, on="grid_id", how="left")
    else:
        # Explicit pending placeholder (represented as missing/NaN, never zero)
        df_final = df_merged.copy()
        df_final["upa_mean_sqkm"] = np.nan
        df_final["upa_max_sqkm"] = np.nan
        df_final["upa_valid_pixel_count"] = np.nan
        df_final["upa_nodata_pixel_count"] = np.nan
        df_final["upa_valid_pixel_fraction"] = np.nan

    # Integrity verification
    if len(df_final) != len(grid_gdf):
        raise ValueError(f"Merged row count ({len(df_final)}) does not match grid cell count ({len(grid_gdf)})")
    if df_final["grid_id"].duplicated().any():
        raise ValueError("Duplicate grid_id detected in merged feature matrix")

    if output_parquet_path:
        out_p = Path(output_parquet_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_parquet(out_p, index=False)

    return df_final
