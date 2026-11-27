"""
Comprehensive Data Validation Engine
Validates CSV tabular streams (rainfall, weather forecasts, flood events),
raster geospatial datasets (DEM, hydrology, land cover), and vector boundary layers.
Provides structured quarantine handling and multi-format validation reports (JSON/CSV).
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.errors import RasterioIOError

from .config import load_yaml_config, BBoxWGS84


@dataclass
class ValidationIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    category: str
    message: str
    row_index: Optional[int] = None
    column: Optional[str] = None


@dataclass
class ValidationReport:
    file_path: str
    dataset_type: str  # "csv", "raster", "vector"
    schema_kind: Optional[str] = None
    is_valid: bool = True
    validated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_records: int = 0
    valid_records: int = 0
    quarantined_records: int = 0
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)
    quarantine_file: Optional[str] = None

    def add_issue(self, severity: str, category: str, message: str, row_index: Optional[int] = None, column: Optional[str] = None):
        self.issues.append(ValidationIssue(severity=severity, category=category, message=message, row_index=row_index, column=column))
        if severity.upper() == "ERROR":
            self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save_json(self, path: Union[str, Path]) -> Path:
        out_p = Path(path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return out_p

    def save_csv(self, path: Union[str, Path]) -> Path:
        """Export issues list and overall summary to CSV."""
        out_p = Path(path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        if self.issues:
            df = pd.DataFrame([asdict(i) for i in self.issues])
        else:
            df = pd.DataFrame([{
                "severity": "INFO",
                "category": "VALIDATION_PASSED",
                "message": "All integrity checks passed successfully.",
                "row_index": None,
                "column": None
            }])
        df["file_path"] = self.file_path
        df["is_valid"] = self.is_valid
        df["total_records"] = self.total_records
        df.to_csv(out_p, index=False)
        return out_p


def validate_csv(
    file_path: Union[str, Path],
    kind: str,
    schemas_config_path: Optional[Union[str, Path]] = None,
    study_area_bbox: Optional[BBoxWGS84] = None,
    quarantine_path: Optional[Union[str, Path]] = None
) -> ValidationReport:
    """
    Validate tabular CSV against canonical platform schemas (rainfall, weather_forecast, flood_events).

    Quarantines corrupted, negative, unparseable, or invalid coordinate records with diagnostic reasons.
    """
    p = Path(file_path)
    # Normalise kind
    kind_map = {
        "rainfall": "rainfall",
        "rain": "rainfall",
        "forecast": "weather_forecast",
        "weather_forecast": "weather_forecast",
        "events": "flood_events",
        "flood_events": "flood_events"
    }
    normalized_kind = kind_map.get(kind.lower())
    if not normalized_kind:
        raise ValueError(f"Unknown CSV validation kind '{kind}'. Must be one of: {list(kind_map.keys())}")

    report = ValidationReport(file_path=str(p.resolve()), dataset_type="csv", schema_kind=normalized_kind)

    # 1. File existence check
    if not p.is_file():
        report.add_issue("ERROR", "FILE_NOT_FOUND", f"Target CSV file does not exist: {p.resolve()}")
        return report

    # 2. Empty file check
    if p.stat().st_size == 0:
        report.add_issue("ERROR", "EMPTY_FILE", f"CSV file is 0 bytes: {p.resolve()}")
        return report

    # Read schema definition if present
    schema_spec = {}
    if schemas_config_path and Path(schemas_config_path).is_file():
        schemas_cfg = load_yaml_config(schemas_config_path)
        schema_spec = schemas_cfg.get("schemas", {}).get(normalized_kind, {})

    required_cols = list(schema_spec.get("required_columns", {}).keys())
    if not required_cols:
        # Fallback to internal canonical defaults if schema config not supplied
        if normalized_kind == "rainfall":
            required_cols = ["observation_time", "precipitation_mm"]
        elif normalized_kind == "weather_forecast":
            required_cols = ["forecast_issue_time", "valid_time", "precipitation_mm"]
        elif normalized_kind == "flood_events":
            required_cols = ["event_id", "event_start", "source"]

    try:
        df = pd.read_csv(p)
    except Exception as exc:
        report.add_issue("ERROR", "CSV_PARSE_ERROR", f"Failed to parse CSV file: {exc}")
        return report

    report.total_records = len(df)
    if df.empty:
        report.add_issue("ERROR", "NO_DATA", "CSV contains headers but 0 data rows.")
        return report

    # 3. Required columns check
    missing_required = [col for col in required_cols if col not in df.columns]
    if missing_required:
        report.add_issue("ERROR", "MISSING_REQUIRED_COLUMNS", f"Missing mandatory columns: {missing_required}")
        return report

    # 4. Detailed row-by-row & column validation with quarantine tracking
    quarantine_reasons = {}

    def flag_row(idx: int, reason: str, severity: str = "ERROR", category: str = "DATA_QUALITY", col: Optional[str] = None):
        if idx not in quarantine_reasons:
            quarantine_reasons[idx] = []
        quarantine_reasons[idx].append(reason)
        report.add_issue(severity, category, reason, row_index=idx, column=col)

    # Missing value counts
    missing_counts = df.isnull().sum().to_dict()
    report.summary_stats["missing_values"] = missing_counts

    # Check for empty values in required columns
    for col in required_cols:
        null_indices = df[df[col].isnull()].index.tolist()
        for idx in null_indices:
            flag_row(idx, f"Required column '{col}' is null or missing.", col=col)

    # Timestamp parsing
    timestamp_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower() or "start" in c.lower() or "end" in c.lower()]
    for col in timestamp_cols:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
            bad_ts_indices = df[df[col].notnull() & parsed.isnull()].index.tolist()
            for idx in bad_ts_indices:
                flag_row(idx, f"Unparseable datetime '{df.loc[idx, col]}' in column '{col}'. Expected ISO 8601.", col=col)

    # Precipitation checks
    if "precipitation_mm" in df.columns:
        # Numeric type check
        precip_num = pd.to_numeric(df["precipitation_mm"], errors="coerce")
        bad_num = df[df["precipitation_mm"].notnull() & precip_num.isnull()].index.tolist()
        for idx in bad_num:
            flag_row(idx, f"Non-numeric value in precipitation_mm: '{df.loc[idx, 'precipitation_mm']}'", col="precipitation_mm")

        # Negative rainfall check
        neg_indices = df[precip_num < 0.0].index.tolist()
        for idx in neg_indices:
            val = df.loc[idx, "precipitation_mm"]
            flag_row(idx, f"Negative rainfall value detected: {val} mm. Physical precipitation cannot be negative.", col="precipitation_mm")

        # Extreme value sanity warning
        extreme_indices = df[precip_num > 1500.0].index.tolist()
        for idx in extreme_indices:
            report.add_issue("WARNING", "EXTREME_VALUE", f"Unusually high rainfall (>1500mm): {df.loc[idx, 'precipitation_mm']} mm", row_index=idx, column="precipitation_mm")

        valid_precip = precip_num[precip_num >= 0.0]
        if not valid_precip.empty:
            report.summary_stats["precipitation_mm"] = {
                "min": float(valid_precip.min()),
                "max": float(valid_precip.max()),
                "mean": float(round(valid_precip.mean(), 3)),
                "std": float(round(valid_precip.std(), 3)) if len(valid_precip) > 1 else 0.0
            }

    # Weather forecast specific check: issue_time <= valid_time
    if normalized_kind == "weather_forecast" and "forecast_issue_time" in df.columns and "valid_time" in df.columns:
        issue_dt = pd.to_datetime(df["forecast_issue_time"], errors="coerce", utc=True)
        valid_dt = pd.to_datetime(df["valid_time"], errors="coerce", utc=True)
        leakage_mask = (issue_dt > valid_dt)
        for idx in df[leakage_mask].index.tolist():
            flag_row(idx, f"Forecast issue time ({df.loc[idx, 'forecast_issue_time']}) is later than target valid time ({df.loc[idx, 'valid_time']}). Information leakage hazard.")

    # Geographic coordinate checks
    has_lat = "latitude" in df.columns
    has_lon = "longitude" in df.columns
    if has_lat and has_lon:
        lat_num = pd.to_numeric(df["latitude"], errors="coerce")
        lon_num = pd.to_numeric(df["longitude"], errors="coerce")

        bad_coords = df[(lat_num < -90.0) | (lat_num > 90.0) | (lon_num < -180.0) | (lon_num > 180.0)].index.tolist()
        for idx in bad_coords:
            flag_row(idx, f"Invalid geographic coordinates (lat={df.loc[idx, 'latitude']}, lon={df.loc[idx, 'longitude']}). Out of WGS84 range.")

        # Study area bounding box check
        if study_area_bbox:
            outside_bbox = df[
                (lat_num < study_area_bbox.south) | (lat_num > study_area_bbox.north) |
                (lon_num < study_area_bbox.west) | (lon_num > study_area_bbox.east)
            ].index.tolist()
            for idx in outside_bbox:
                report.add_issue(
                    "WARNING",
                    "OUTSIDE_STUDY_AREA",
                    f"Coordinate ({df.loc[idx, 'latitude']}, {df.loc[idx, 'longitude']}) lies outside study area bounding box.",
                    row_index=idx
                )

    # Duplicate records check
    dup_mask = df.duplicated(keep=False)
    if dup_mask.any():
        num_dups = int(dup_mask.sum())
        report.add_issue("WARNING", "DUPLICATE_RECORDS", f"Found {num_dups} duplicate records across all columns.")

    # Quarantine handling
    quarantined_indices = sorted(list(quarantine_reasons.keys()))
    report.quarantined_records = len(quarantined_indices)
    report.valid_records = report.total_records - report.quarantined_records

    if quarantined_indices and quarantine_path:
        q_path = Path(quarantine_path)
        q_path.parent.mkdir(parents=True, exist_ok=True)
        q_df = df.iloc[quarantined_indices].copy()
        q_df["quarantine_reasons"] = ["; ".join(quarantine_reasons[i]) for i in quarantined_indices]
        q_df.to_csv(q_path, index=False)
        report.quarantine_file = str(q_path.resolve())

    # Data coverage summary
    primary_time_col = None
    for cand in ["observation_time", "forecast_issue_time", "event_start"]:
        if cand in df.columns:
            primary_time_col = cand
            break

    if primary_time_col:
        valid_ts = pd.to_datetime(df.loc[~df.index.isin(quarantined_indices), primary_time_col], errors="coerce", utc=True).dropna()
        if not valid_ts.empty:
            report.summary_stats["temporal_coverage"] = {
                "column": primary_time_col,
                "start_utc": valid_ts.min().isoformat(),
                "end_utc": valid_ts.max().isoformat(),
                "duration_days": round((valid_ts.max() - valid_ts.min()).total_seconds() / 86400, 2)
            }

    return report


def validate_raster(
    file_path: Union[str, Path],
    expected_crs: Optional[str] = None
) -> ValidationReport:
    """
    Validate raster geospatial dataset (GeoTIFF) file integrity, dimensions, CRS,
    band count, resolution, bounding box, nodata values, valid pixel ratio, and statistics.
    """
    p = Path(file_path)
    report = ValidationReport(file_path=str(p.resolve()), dataset_type="raster")

    if not p.is_file():
        report.add_issue("ERROR", "FILE_NOT_FOUND", f"Raster file not found: {p.resolve()}")
        return report

    try:
        with rasterio.open(p) as src:
            report.summary_stats["driver"] = src.driver
            report.summary_stats["width"] = src.width
            report.summary_stats["height"] = src.height
            report.summary_stats["count"] = src.count
            report.summary_stats["dtypes"] = [str(dt) for dt in src.dtypes]
            report.summary_stats["nodatavals"] = [nv for nv in src.nodatavals]
            report.summary_stats["resolution"] = [float(res) for res in src.res]
            report.summary_stats["bounds"] = {
                "left": float(src.bounds.left),
                "bottom": float(src.bounds.bottom),
                "right": float(src.bounds.right),
                "top": float(src.bounds.top)
            }

            # CRS check
            if src.crs is None:
                report.add_issue("ERROR", "MISSING_CRS", "Raster does not define a Coordinate Reference System (CRS).")
            else:
                report.summary_stats["crs"] = str(src.crs)
                if expected_crs:
                    src_crs_str = src.crs.to_string().upper()
                    if expected_crs.upper() not in src_crs_str:
                        report.add_issue("WARNING", "CRS_MISMATCH", f"Expected CRS '{expected_crs}', got '{src_crs_str}'.")

            # Check dimensions
            if src.width <= 0 or src.height <= 0:
                report.add_issue("ERROR", "ZERO_DIMENSIONS", f"Raster dimensions invalid: {src.width}x{src.height}")

            # Sample first band for statistics and valid pixel percentage safely
            # Read small overview or window if very large to prevent memory overflow
            max_sample_dim = 1000
            decimation = max(1, max(src.width // max_sample_dim, src.height // max_sample_dim))
            sample_data = src.read(1, out_shape=(src.height // decimation, src.width // decimation))

            nodata_val = src.nodatavals[0] if src.nodatavals else None
            if nodata_val is not None:
                valid_mask = (sample_data != nodata_val) & ~np.isnan(sample_data)
            else:
                valid_mask = ~np.isnan(sample_data)

            total_sampled_pixels = int(sample_data.size)
            valid_pixels = int(np.sum(valid_mask))
            valid_pct = (valid_pixels / total_sampled_pixels * 100.0) if total_sampled_pixels > 0 else 0.0

            report.summary_stats["valid_pixel_pct_sampled"] = round(valid_pct, 2)
            report.total_records = total_sampled_pixels
            report.valid_records = valid_pixels

            if valid_pixels == 0:
                report.add_issue("ERROR", "NO_VALID_DATA_PIXELS", "Raster contains 100% nodata / NaN pixels.")
            else:
                valid_vals = sample_data[valid_mask]
                report.summary_stats["band_1_stats"] = {
                    "min": float(np.min(valid_vals)),
                    "max": float(np.max(valid_vals)),
                    "mean": float(round(float(np.mean(valid_vals)), 3)),
                    "std": float(round(float(np.std(valid_vals)), 3))
                }

    except RasterioIOError as rio_err:
        report.add_issue("ERROR", "CORRUPTED_RASTER", f"Cannot open raster file; possibly corrupted: {rio_err}")
    except Exception as exc:
        report.add_issue("ERROR", "RASTER_INSPECTION_ERROR", f"Error inspecting raster: {exc}")

    return report


def validate_vector(
    file_path: Union[str, Path],
    expected_crs: Optional[str] = None,
    id_column: Optional[str] = None
) -> ValidationReport:
    """
    Validate vector geospatial dataset (GeoJSON, GeoPackage, Shapefile) geometry integrity,
    CRS, empty geometries, topological validity, and identifier uniqueness.
    """
    p = Path(file_path)
    report = ValidationReport(file_path=str(p.resolve()), dataset_type="vector")

    if not p.is_file():
        report.add_issue("ERROR", "FILE_NOT_FOUND", f"Vector file not found: {p.resolve()}")
        return report

    try:
        gdf = gpd.read_file(p)
    except Exception as exc:
        report.add_issue("ERROR", "VECTOR_READ_ERROR", f"Failed to parse vector file: {exc}")
        return report

    report.total_records = len(gdf)
    report.summary_stats["feature_count"] = len(gdf)
    report.summary_stats["columns"] = list(gdf.columns)

    if gdf.empty:
        report.add_issue("ERROR", "EMPTY_VECTOR", "Vector file contains 0 features.")
        return report

    # CRS verification
    if gdf.crs is None:
        report.add_issue("ERROR", "MISSING_CRS", "Vector dataset has no defined CRS.")
    else:
        crs_str = gdf.crs.to_string()
        report.summary_stats["crs"] = crs_str
        if expected_crs and expected_crs.upper() not in crs_str.upper():
            report.add_issue("WARNING", "CRS_MISMATCH", f"Expected CRS '{expected_crs}', got '{crs_str}'.")

    # Geometry checks
    empty_geom_count = int(gdf.geometry.is_empty.sum())
    null_geom_count = int(gdf.geometry.isnull().sum())
    if empty_geom_count > 0:
        report.add_issue("ERROR", "EMPTY_GEOMETRIES", f"Found {empty_geom_count} empty geometry features.")
    if null_geom_count > 0:
        report.add_issue("ERROR", "NULL_GEOMETRIES", f"Found {null_geom_count} null geometry features.")

    # Topological validity check
    invalid_mask = ~gdf.geometry.is_valid
    invalid_count = int(invalid_mask.sum())
    if invalid_count > 0:
        report.add_issue("ERROR", "INVALID_GEOMETRIES", f"Found {invalid_count} geometrically invalid features (self-intersections or ring collapse).")

    # Geometry types
    geom_types = gdf.geometry.geom_type.value_counts().to_dict()
    report.summary_stats["geometry_types"] = geom_types

    # Identifier uniqueness check
    if id_column and id_column in gdf.columns:
        dups = int(gdf[id_column].duplicated().sum())
        if dups > 0:
            report.add_issue("ERROR", "DUPLICATE_IDENTIFIERS", f"Found {dups} duplicate IDs in column '{id_column}'.")

    # Bounding extent
    total_bounds = gdf.total_bounds
    report.summary_stats["total_bounds"] = {
        "minx": float(total_bounds[0]),
        "miny": float(total_bounds[1]),
        "maxx": float(total_bounds[2]),
        "maxy": float(total_bounds[3])
    }

    report.valid_records = report.total_records - (empty_geom_count + null_geom_count + invalid_count)
    return report

