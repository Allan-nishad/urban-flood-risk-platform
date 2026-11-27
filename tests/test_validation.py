"""
Tests for CSV, raster, and vector validation engines, error detection, and quarantine handling.
"""

from pathlib import Path
import pytest
from floodrisk.validate import validate_csv, validate_raster, validate_vector


def test_valid_rainfall_csv(synthetic_valid_rainfall_csv: Path):
    """Verify that a schema-conforming rainfall CSV passes validation without errors."""
    report = validate_csv(synthetic_valid_rainfall_csv, kind="rainfall")
    assert report.is_valid is True
    assert report.total_records == 3
    assert report.valid_records == 3
    assert report.quarantined_records == 0
    assert "precipitation_mm" in report.summary_stats
    assert report.summary_stats["precipitation_mm"]["min"] == 0.0
    assert report.summary_stats["precipitation_mm"]["max"] == 45.2


def test_missing_required_columns(synthetic_missing_col_csv: Path):
    """Verify that omitting required precipitation_mm column triggers an immediate validation ERROR."""
    report = validate_csv(synthetic_missing_col_csv, kind="rainfall")
    assert report.is_valid is False
    assert any(i.category == "MISSING_REQUIRED_COLUMNS" for i in report.issues)


def test_corrupt_rainfall_negative_and_bad_timestamp(synthetic_corrupt_rainfall_csv: Path, tmp_path: Path):
    """Verify detection of negative rainfall, unparseable dates, and quarantine export."""
    quarantine_out = tmp_path / "quarantined_rainfall.csv"
    report = validate_csv(
        synthetic_corrupt_rainfall_csv,
        kind="rainfall",
        quarantine_path=quarantine_out
    )

    assert report.is_valid is False
    assert report.quarantined_records > 0

    # Ensure quarantine file exists and contains quarantine_reasons
    assert quarantine_out.is_file()
    with open(quarantine_out, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Negative rainfall value detected" in content
    assert "Unparseable datetime" in content


def test_empty_csv_file(synthetic_empty_csv: Path):
    """Verify empty 0-byte file check."""
    report = validate_csv(synthetic_empty_csv, kind="rainfall")
    assert report.is_valid is False
    assert any(i.category == "EMPTY_FILE" for i in report.issues)


def test_weather_forecast_leakage_detection(synthetic_weather_forecast_csv: Path):
    """Verify that forecast issue time > valid time is detected as an information leakage hazard."""
    report = validate_csv(synthetic_weather_forecast_csv, kind="weather_forecast")
    assert any("leakage" in i.message.lower() for i in report.issues)


def test_valid_raster_inspection(synthetic_valid_raster: Path):
    """Verify successful inspection of a valid GeoTIFF raster."""
    report = validate_raster(synthetic_valid_raster)
    assert report.is_valid is True
    assert report.summary_stats["width"] == 20
    assert report.summary_stats["height"] == 20
    assert "EPSG:4326" in report.summary_stats["crs"]
    assert report.summary_stats["valid_pixel_pct_sampled"] > 90.0


def test_raster_missing_crs(synthetic_raster_no_crs: Path):
    """Verify detection of raster missing coordinate reference system (CRS)."""
    report = validate_raster(synthetic_raster_no_crs)
    assert report.is_valid is False
    assert any(i.category == "MISSING_CRS" for i in report.issues)


def test_valid_vector_inspection(synthetic_valid_vector: Path):
    """Verify successful validation of standard valid vector polygon."""
    report = validate_vector(synthetic_valid_vector)
    assert report.is_valid is True
    assert report.summary_stats["feature_count"] == 1


def test_invalid_vector_geometry(synthetic_invalid_vector: Path):
    """Verify detection of self-intersecting / topologically invalid geometries."""
    report = validate_vector(synthetic_invalid_vector)
    assert report.is_valid is False
    assert any(i.category == "INVALID_GEOMETRIES" for i in report.issues)


def test_validation_report_export(synthetic_valid_rainfall_csv: Path, tmp_path: Path):
    """Verify export of validation report to JSON and CSV formats."""
    report = validate_csv(synthetic_valid_rainfall_csv, kind="rainfall")
    json_path = tmp_path / "report.json"
    csv_path = tmp_path / "report.csv"

    report.save_json(json_path)
    report.save_csv(csv_path)

    assert json_path.is_file()
    assert csv_path.is_file()

