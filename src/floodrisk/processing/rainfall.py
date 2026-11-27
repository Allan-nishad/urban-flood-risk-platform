"""
Rainfall Processing, Unit Verification, and Temporal Feature Engineering Engine
Provides verified unit conversions, spatial remapping, and hydrological antecedent indices
for satellite and gauge precipitation products (NASA GPM IMERG, IMD, ERA5).

Enforces dynamic attribute verification and strict mathematical conversions.
"""

from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Tuple, Dict, Any, Union, Optional, List
import urllib.request
import urllib.error
import urllib.parse
import os

import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Transformer
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import RegularGridInterpolator


# Known official IMERG variable definitions per NASA GES DISC Documentation (V07B)
OFFICIAL_IMERG_VARIABLES = {
    "precipitationCal": {
        "product": "GPM_3IMERGHH",
        "description": "Multi-satellite precipitation estimate with gauge calibration",
        "official_units": "mm/hr",
        "quantity_type": "rate",
        "native_temporal_interval_minutes": 30
    },
    "precipitationUncal": {
        "product": "GPM_3IMERGHH",
        "description": "Multi-satellite precipitation estimate without gauge calibration",
        "official_units": "mm/hr",
        "quantity_type": "rate",
        "native_temporal_interval_minutes": 30
    },
    "precipitation": {
        "product": "GPM_3IMERGDF",
        "description": "Daily accumulated precipitation depth (Final / Late run)",
        "official_units": "mm",
        "quantity_type": "depth",
        "native_temporal_interval_minutes": 1440
    },
    "randomError": {
        "product": "GPM_3IMERGHH",
        "description": "1-sigma error estimate for precipitationCal",
        "official_units": "mm/hr",
        "quantity_type": "rate",
        "native_temporal_interval_minutes": 30
    }
}


def parse_and_validate_rainfall_units(
    variable_name: str,
    units_attribute: Optional[str] = None,
    temporal_interval_minutes: float = 30.0
) -> Dict[str, Any]:
    """
    Verify the exact physical quantity (rate vs depth) and determine mathematically correct conversion.
    Refuses to multiply by 0.5 automatically without checking variable metadata and units.

    Parameters
    ----------
    variable_name : str
        Source variable name (e.g. 'precipitationCal', 'precipitation').
    units_attribute : str, optional
        Units string extracted from HDF5/NetCDF attributes or CSV headers.
    temporal_interval_minutes : float
        Observation duration for the time slice in minutes (default 30 min for IMERG half-hourly).

    Returns
    -------
    Dict[str, Any]
        Metadata dictionary detailing quantity type, conversion factor, and mathematical formula.
    """
    timestep_hours = temporal_interval_minutes / 60.0

    # Match official specifications if recognized
    official_spec = OFFICIAL_IMERG_VARIABLES.get(variable_name)
    raw_units = (units_attribute or (official_spec["official_units"] if official_spec else "")).strip().lower()

    if not raw_units:
        raise ValueError(
            f"Cannot verify precipitation variable '{variable_name}': missing units attribute. "
            f"Explicit units specification is mandatory to prevent incorrect rate-depth multiplication."
        )

    # 1. Precipitation Rate (e.g., mm/hr)
    if raw_units in ["mm/hr", "mm/h", "millimeter/hour", "mm hr-1", "mm h^-1"]:
        conversion_factor = timestep_hours
        formula = f"{variable_name} [{units_attribute or 'mm/hr'}] * {timestep_hours:.4f} [hr]"
        return {
            "variable_name": variable_name,
            "original_units": units_attribute or "mm/hr",
            "quantity_type": "rate",
            "temporal_interval_minutes": temporal_interval_minutes,
            "timestep_hours": timestep_hours,
            "conversion_factor": conversion_factor,
            "conversion_formula": formula,
            "converted_units": "mm",
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    # 2. Accumulated Precipitation Depth (e.g., mm, mm/day for 24-hr aggregate)
    if raw_units in ["mm", "millimeter", "mm/day", "depth_mm"]:
        conversion_factor = 1.0
        formula = f"Identity: {variable_name} is already accumulated depth [{units_attribute or 'mm'}]; factor=1.0"
        return {
            "variable_name": variable_name,
            "original_units": units_attribute or "mm",
            "quantity_type": "depth",
            "temporal_interval_minutes": temporal_interval_minutes,
            "timestep_hours": timestep_hours,
            "conversion_factor": 1.0,
            "conversion_formula": formula,
            "converted_units": "mm",
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    # 3. Mass Flux (e.g., kg m^-2 s^-1)
    if raw_units in ["kg m-2 s-1", "kg/m^2/s", "kg m^-2 s^-1", "kg/(m^2*s)"]:
        seconds_in_interval = temporal_interval_minutes * 60.0
        conversion_factor = seconds_in_interval
        formula = f"{variable_name} [kg/m^2/s] * {seconds_in_interval:.1f} [s] * (1 mm / 1 kg/m^2)"
        return {
            "variable_name": variable_name,
            "original_units": units_attribute,
            "quantity_type": "mass_flux",
            "temporal_interval_minutes": temporal_interval_minutes,
            "timestep_hours": timestep_hours,
            "conversion_factor": conversion_factor,
            "conversion_formula": formula,
            "converted_units": "mm",
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    raise ValueError(
        f"Unrecognized precipitation units '{units_attribute}' for variable '{variable_name}'. "
        f"Supported units: 'mm/hr', 'mm', 'mm/day', 'kg m-2 s-1'."
    )


def convert_precipitation_to_depth_mm(
    values: Union[np.ndarray, pd.Series, float],
    variable_name: str,
    units_attribute: str,
    temporal_interval_minutes: float = 30.0
) -> Tuple[Union[np.ndarray, pd.Series, float], Dict[str, Any]]:
    """
    Safely convert raw precipitation data to canonical accumulated depth in millimetres (mm)
    based on verified metadata attributes.
    """
    meta = parse_and_validate_rainfall_units(
        variable_name=variable_name,
        units_attribute=units_attribute,
        temporal_interval_minutes=temporal_interval_minutes
    )
    factor = meta["conversion_factor"]
    converted_values = values * factor
    return converted_values, meta


class IMERGDownloader:
    """
    NASA GES DISC IMERG V07 Data Retrieval and Automation Utility.
    Constructs canonical archive URLs and manages authentication via Earthdata Login.
    """

    BASE_URL_DAILY = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07"
    BASE_URL_HALF_HOURLY = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07"

    @classmethod
    def get_daily_url(cls, target_date: date) -> str:
        """Construct canonical GES DISC URL for GPM_3IMERGDF V07B daily granule."""
        year = target_date.year
        month = target_date.month
        day = target_date.day
        filename = f"3B-DAY.MS.MRG.3IMERG.{year}{month:02d}{day:02d}-S000000-E235959.V07B.nc4"
        return f"{cls.BASE_URL_DAILY}/{year}/{month:02d}/{filename}"

    @classmethod
    def generate_date_range_urls(cls, start_date: date, end_date: date) -> List[Tuple[date, str]]:
        """Generate list of (date, url) pairs across the requested date window."""
        urls = []
        cur = start_date
        while cur <= end_date:
            urls.append((cur, cls.get_daily_url(cur)))
            cur += timedelta(days=1)
        return urls

    @classmethod
    def generate_curl_download_script(
        cls,
        start_date: date,
        end_date: date,
        output_dir: Union[str, Path] = "data/raw/rainfall/gpm_imerg_v07",
        script_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Generate a shell script to download all granules using curl and NASA Earthdata cookies/netrc.
        """
        out_path = Path(output_dir)
        out_posix = out_path.as_posix()
        pairs = cls.generate_date_range_urls(start_date, end_date)
        
        lines = [
            "#!/usr/bin/env bash",
            "# NASA GES DISC GPM IMERG V07B Automated Granule Retrieval Script",
            "# Requires NASA Earthdata credentials configured in ~/.netrc or ~/.urs_cookies",
            "# Reference: https://disc.gsfc.nasa.gov/information/howto?title=How%20to%20Download%20Data%20Files%20from%20HTTPS%20Service%20with%20wget",
            "",
            f"mkdir -p {out_posix}",
            "COOKIE_JAR=~/.urs_cookies",
            ""
        ]

        for dt, url in pairs:
            year_month = f"{dt.year}/{dt.month:02d}"
            filename = url.split("/")[-1]
            target_file = f"{out_posix}/{year_month}/{filename}"
            lines.append(f"mkdir -p {out_posix}/{year_month}")
            lines.append(
                f"curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o \"{target_file}\" \"{url}\""
            )

        script_file = Path(script_path or "scripts/download_imerg_gesdisc.sh")
        script_file.parent.mkdir(parents=True, exist_ok=True)
        script_file.write_text("\n".join(lines), encoding="utf-8")
        return script_file


class IMERGRasterReader:
    """
    Reader for authentic NASA GPM IMERG NetCDF4 (.nc4), HDF5, and GeoTIFF rasters.
    Parses spatial metadata, inspects units, and transposes coordinates to standard raster orientation.
    """

    @staticmethod
    def read_imerg_raster(
        raster_path: Union[str, Path],
        variable_name: str = "precipitation",
        temporal_interval_minutes: float = 1440.0
    ) -> Dict[str, Any]:
        """
        Read an IMERG raster file, extracting grid data, coordinate transform, and unit metadata.
        """
        path = Path(raster_path)
        if not path.is_file():
            raise FileNotFoundError(f"IMERG raster not found: {path.resolve()}")

        # Check subdatasets for NetCDF4 / HDF5 files
        with rasterio.open(path) as src:
            subdatasets = src.subdatasets
            target_subdataset = None
            if subdatasets:
                for sub in subdatasets:
                    if variable_name.lower() in sub.lower():
                        target_subdataset = sub
                        break
                if not target_subdataset:
                    target_subdataset = subdatasets[0]

        open_target = target_subdataset if target_subdataset else path

        with rasterio.open(open_target) as src:
            data = src.read(1).astype(np.float32)
            tags = src.tags()
            transform = src.transform
            crs = src.crs or "EPSG:4326"
            nodata = src.nodata

            # Extract units
            units_attr = tags.get("units") or tags.get("UNITS")
            if not units_attr:
                # Fallback to official IMERG spec if known
                spec = OFFICIAL_IMERG_VARIABLES.get(variable_name)
                units_attr = spec["official_units"] if spec else "mm"

            # Filter NoData / fill values (IMERG default is -9999.9)
            if nodata is not None:
                data[np.isclose(data, nodata, atol=1e-2)] = np.nan
            data[data < -9000.0] = np.nan
            data[data < 0.0] = 0.0  # Precipitation cannot be physically negative

            # If array is shape (3600, 1800) [lon, lat], transpose to (1800, 3600) [lat, lon]
            if data.shape == (3600, 1800):
                data = np.transpose(data)
                # Ensure latitude is descending (North to South)
                data = np.flipud(data)

            # Convert units to canonical accumulated depth in mm
            converted_data, unit_meta = convert_precipitation_to_depth_mm(
                values=data,
                variable_name=variable_name,
                units_attribute=units_attr,
                temporal_interval_minutes=temporal_interval_minutes
            )

            return {
                "file_path": str(path.resolve()),
                "data": converted_data,
                "shape": converted_data.shape,
                "crs": str(crs),
                "transform": transform,
                "bounds": src.bounds,
                "units_meta": unit_meta,
                "nodata_value": nodata
            }


class IMERGGridMapper:
    """
    Spatial remapping engine: transfers 0.1° (~10 km) IMERG precipitation fields
    onto equal-area 1-km grid cells (EPSG:6933) across the study domain.
    """

    SCIENTIFIC_DISCLAIMER = (
        "1-km grid remapping provides spatial indexing alignment only for multimodal tabular joining; "
        "native 0.1 deg (~10 km) satellite precipitation does NOT resolve localized convective micro-cells, "
        "storm sewer backups, or street-level runoff dynamics."
    )

    def __init__(self, grid_gdf: gpd.GeoDataFrame):
        """
        Initialize with the target grid GeoDataFrame (must contain 'grid_id' and 'geometry' in EPSG:6933).
        """
        if grid_gdf.crs is None:
            raise ValueError("Target grid GeoDataFrame must have a valid CRS.")

        self.grid_gdf = grid_gdf.copy()
        if self.grid_gdf.crs.to_epsg() != 6933:
            self.grid_gdf = self.grid_gdf.to_crs(epsg=6933)

        # Compute cell centroids in WGS84 (lon, lat)
        centroids_proj = self.grid_gdf.geometry.centroid
        transformer = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True)
        lons, lats = transformer.transform(centroids_proj.x.values, centroids_proj.y.values)
        self.centroid_lons = lons
        self.centroid_lats = lats

    def remap_raster(
        self,
        raster_dict: Dict[str, Any],
        method: str = "centroid_lookup"
    ) -> pd.DataFrame:
        """
        Remap an IMERG 2D raster field onto the grid cells.

        Parameters
        ----------
        raster_dict : Dict[str, Any]
            Output dictionary from IMERGRasterReader.read_imerg_raster().
        method : str
            Remapping method: 'centroid_lookup' (default, nearest 0.1° cell) or 'bilinear' (smooth interpolation).

        Returns
        -------
        pd.DataFrame
            DataFrame with columns ['grid_id', 'rainfall_depth_mm'].
        """
        data = raster_dict["data"]
        transform = raster_dict["transform"]
        height, width = data.shape

        if method == "centroid_lookup":
            # Map centroids to raster pixel indices using inverse affine transform
            inv_transform = ~transform
            col_floats, row_floats = inv_transform @ (self.centroid_lons, self.centroid_lats)
            cols = np.floor(col_floats).astype(int)
            rows = np.floor(row_floats).astype(int)

            # Bounds check
            valid_mask = (rows >= 0) & (rows < height) & (cols >= 0) & (cols < width)
            mapped_values = np.full(len(self.grid_gdf), np.nan, dtype=np.float32)
            mapped_values[valid_mask] = data[rows[valid_mask], cols[valid_mask]]

        elif method == "bilinear":
            # Build 1D coordinate axes
            # For affine transform: x = c + a*col, y = f + e*row (where e is negative)
            xs = transform.c + transform.a * (np.arange(width) + 0.5)
            ys = transform.f + transform.e * (np.arange(height) + 0.5)

            # Ensure ys is strictly increasing for RegularGridInterpolator
            if transform.e < 0:
                ys = ys[::-1]
                data_interp = np.flipud(data)
            else:
                data_interp = data

            interpolator = RegularGridInterpolator(
                (ys, xs),
                data_interp,
                method="linear",
                bounds_error=False,
                fill_value=np.nan
            )
            # Evaluate at (lat, lon)
            query_points = np.column_stack([self.centroid_lats, self.centroid_lons])
            mapped_values = interpolator(query_points).astype(np.float32)

        else:
            raise ValueError(f"Unsupported remapping method '{method}'. Choose 'centroid_lookup' or 'bilinear'.")

        result_df = pd.DataFrame({
            "grid_id": self.grid_gdf["grid_id"].values,
            "rainfall_depth_mm": np.round(mapped_values, 2)
        })
        return result_df


class AntecedentPrecipitationEngine:
    """
    Hydrological temporal index calculator:
    Computes multi-day antecedent precipitation accumulations and exponential decay API indices.
    """

    @staticmethod
    def compute_antecedent_indices(
        daily_rainfall_panel: pd.DataFrame,
        decay_coefficient: float = 0.85,
        max_decay_window_days: int = 14
    ) -> pd.DataFrame:
        """
        Calculate rolling antecedent precipitation indices for each grid cell across time.

        Parameters
        ----------
        daily_rainfall_panel : pd.DataFrame
            Panel DataFrame containing ['grid_id', 'date', 'rainfall_daily_depth_mm'].
        decay_coefficient : float
            Daily soil moisture depletion coefficient (default 0.85).
        max_decay_window_days : int
            Lookback window for API summation (default 14 days).

        Returns
        -------
        pd.DataFrame
            Enriched panel DataFrame with columns:
            ['grid_id', 'date', 'rainfall_daily_depth_mm',
             'precip_antecedent_3d_mm', 'precip_antecedent_7d_mm', 'precip_antecedent_14d_mm',
             'precip_api_decay_mm', 'precip_cumulative_event_mm']
        """
        required_cols = {"grid_id", "date", "rainfall_daily_depth_mm"}
        if not required_cols.issubset(daily_rainfall_panel.columns):
            raise ValueError(f"Input panel must contain columns {required_cols}")

        df = daily_rainfall_panel.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values(by=["grid_id", "date"]).reset_index(drop=True)

        # Vectorized groupby rolling calculations
        grouped = df.groupby("grid_id")["rainfall_daily_depth_mm"]

        # Shift by 1 day so antecedent rainfall measures rainfall PRIOR to the current day
        shifted = grouped.shift(1).fillna(0.0)
        df["_shifted_precip"] = shifted

        shifted_grouped = df.groupby("grid_id")["_shifted_precip"]

        # 3-day, 7-day, 14-day antecedent accumulations
        df["precip_antecedent_3d_mm"] = np.round(
            shifted_grouped.rolling(window=3, min_periods=1).sum().reset_index(level=0, drop=True), 2
        )
        df["precip_antecedent_7d_mm"] = np.round(
            shifted_grouped.rolling(window=7, min_periods=1).sum().reset_index(level=0, drop=True), 2
        )
        df["precip_antecedent_14d_mm"] = np.round(
            shifted_grouped.rolling(window=14, min_periods=1).sum().reset_index(level=0, drop=True), 2
        )

        # Cumulative rainfall from start of window
        df["precip_cumulative_event_mm"] = np.round(
            grouped.cumsum().reset_index(level=0, drop=True), 2
        )

        # Exponential Decaying API calculation: API_t = sum_{k=1}^n P_{t-k} * alpha^k
        # Build weights vector: [alpha^1, alpha^2, ..., alpha^n]
        weights = np.array([decay_coefficient ** k for k in range(1, max_decay_window_days + 1)])

        def _calc_api(series: pd.Series) -> pd.Series:
            arr = series.values
            n = len(arr)
            api_vals = np.zeros(n, dtype=np.float32)
            for i in range(n):
                # antecedent values up to i-1
                hist = arr[max(0, i - max_decay_window_days):i]
                if len(hist) > 0:
                    # history reversed: index 0 is t-1, index 1 is t-2, etc.
                    hist_rev = hist[::-1]
                    w = weights[:len(hist_rev)]
                    api_vals[i] = np.sum(hist_rev * w)
            return pd.Series(api_vals, index=series.index)

        df["precip_api_decay_mm"] = np.round(
            df.groupby("grid_id")["rainfall_daily_depth_mm"].apply(_calc_api).reset_index(level=0, drop=True), 2
        )

        df = df.drop(columns=["_shifted_precip"])
        return df

    @staticmethod
    def compute_cell_event_summary(enriched_panel: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate panel time series into per-cell event summary statistics for the flood window.
        """
        summary = enriched_panel.groupby("grid_id").agg(
            event_total_rainfall_mm=("rainfall_daily_depth_mm", "sum"),
            event_peak_daily_rainfall_mm=("rainfall_daily_depth_mm", "max"),
            event_mean_daily_rainfall_mm=("rainfall_daily_depth_mm", "mean"),
            event_max_antecedent_3d_mm=("precip_antecedent_3d_mm", "max"),
            event_max_antecedent_7d_mm=("precip_antecedent_7d_mm", "max"),
            event_max_api_decay_mm=("precip_api_decay_mm", "max"),
            event_rainy_days_count=("rainfall_daily_depth_mm", lambda s: int(np.sum(s >= 2.5))),
            event_heavy_rain_days_count=("rainfall_daily_depth_mm", lambda s: int(np.sum(s >= 64.5)))
        ).reset_index()

        summary["event_total_rainfall_mm"] = np.round(summary["event_total_rainfall_mm"], 2)
        summary["event_peak_daily_rainfall_mm"] = np.round(summary["event_peak_daily_rainfall_mm"], 2)
        summary["event_mean_daily_rainfall_mm"] = np.round(summary["event_mean_daily_rainfall_mm"], 2)
        summary["event_max_antecedent_3d_mm"] = np.round(summary["event_max_antecedent_3d_mm"], 2)
        summary["event_max_antecedent_7d_mm"] = np.round(summary["event_max_antecedent_7d_mm"], 2)
        summary["event_max_api_decay_mm"] = np.round(summary["event_max_api_decay_mm"], 2)

        return summary


def create_mock_imerg_raster(
    output_path: Union[str, Path],
    west: float = 77.0,
    north: float = 13.5,
    pixel_size_deg: float = 0.1,
    rows: int = 8,
    cols: int = 8,
    base_rainfall_mm: float = 25.0,
    gradient_axis: str = "y"
) -> Path:
    """
    Create a strictly validated GeoTIFF raster fixture mimicking an official NASA GPM IMERG 0.1° granule.
    Used for unit testing, reproducible CI pipelines, and zero-credential verification.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    transform = from_origin(west, north, pixel_size_deg, pixel_size_deg)

    if gradient_axis == "y":
        # Precipitation gradient increasing northward
        y_grad = np.linspace(0.5, 2.0, rows)[:, np.newaxis]
        arr = (np.ones((rows, cols), dtype=np.float32) * base_rainfall_mm * y_grad).astype(np.float32)
    else:
        # Precipitation gradient increasing eastward
        x_grad = np.linspace(0.5, 2.0, cols)[np.newaxis, :]
        arr = (np.ones((rows, cols), dtype=np.float32) * base_rainfall_mm * x_grad).astype(np.float32)

    with rasterio.open(
        out_file,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999.9
    ) as dst:
        dst.write(arr, 1)
        dst.update_tags(
            units="mm/day",
            long_name="Daily mean precipitation rate (combined microwave-IR) estimate. Formerly precipitationCal.",
            variable_name="precipitation",
            product="GPM_3IMERGDF_V07B",
            spatial_resolution="0.1 deg"
        )

    return out_file
