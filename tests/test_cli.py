"""
Tests for Command Line Interface (CLI) operational commands.
"""

from pathlib import Path
from click.testing import CliRunner
from floodrisk.cli import main


def test_cli_show_config():
    """Verify show-config command outputs formatted Bengaluru details."""
    runner = CliRunner()
    result = runner.invoke(main, ["show-config", "--config", "configs/areas/bengaluru.yaml"])
    assert result.exit_code == 0
    assert "Bengaluru Urban" in result.output
    assert "EPSG:6933" in result.output
    assert "1000 m" in result.output


def test_cli_validate_csv(synthetic_valid_rainfall_csv: Path):
    """Verify validate-csv command passes on clean synthetic rainfall."""
    runner = CliRunner()
    result = runner.invoke(main, ["validate-csv", str(synthetic_valid_rainfall_csv), "--kind", "rainfall"])
    assert result.exit_code == 0
    assert "VALID" in result.output
    assert "Total Records:         3" in result.output


def test_cli_validate_raster(synthetic_valid_raster: Path):
    """Verify validate-raster command succeeds on valid GeoTIFF."""
    runner = CliRunner()
    result = runner.invoke(main, ["validate-raster", str(synthetic_valid_raster)])
    assert result.exit_code == 0
    assert "20 x 20" in result.output
    assert "EPSG:4326" in result.output


def test_cli_validate_vector(synthetic_valid_vector: Path):
    """Verify validate-vector command succeeds on GeoJSON boundary."""
    runner = CliRunner()
    result = runner.invoke(main, ["validate-vector", str(synthetic_valid_vector)])
    assert result.exit_code == 0
    assert "Feature Count:         1" in result.output


def test_cli_generate_grid(tmp_path: Path):
    """Verify generate-grid command creates equal-area grid output with g{size}_{col}_{row} format."""
    out_grid = tmp_path / "bengaluru_grid_test.geojson"
    runner = CliRunner()
    result = runner.invoke(main, [
        "generate-grid",
        "--config", "configs/areas/bengaluru.yaml",
        "--out", str(out_grid),
        "--format", "geojson"
    ])
    assert result.exit_code == 0
    assert "GRID GENERATION SUCCESSFUL" in result.output
    assert "g1000_" in result.output
    assert out_grid.is_file()


def test_cli_report_distortion(tmp_path: Path):
    """Verify report-distortion CLI computes and displays geodesic distortion."""
    out_grid = tmp_path / "test_dist_grid.geojson"
    runner = CliRunner()
    runner.invoke(main, [
        "generate-grid",
        "--config", "configs/areas/bengaluru.yaml",
        "--out", str(out_grid),
        "--format", "geojson"
    ])

    out_report = tmp_path / "distortion.json"
    result = runner.invoke(main, [
        "report-distortion",
        "--grid", str(out_grid),
        "--out", str(out_report)
    ])
    assert result.exit_code == 0
    assert "GRID COVERAGE & GEODESIC DISTORTION ANALYSIS" in result.output
    assert "Geodesic Area Ratio" in result.output
    assert out_report.is_file()


def test_cli_download_imerg(tmp_path: Path):
    """Verify download-imerg CLI generates download script and checks Earthdata status."""
    script_file = tmp_path / "test_download.sh"
    runner = CliRunner()
    result = runner.invoke(main, [
        "download-imerg",
        "--start-date", "2022-09-01",
        "--end-date", "2022-09-03",
        "--script-path", str(script_file)
    ])
    assert result.exit_code == 0
    assert "NASA GPM IMERG V07B GRANULE RETRIEVAL MANAGER" in result.output
    assert script_file.is_file()


def test_cli_process_rainfall(tmp_path: Path):
    """Verify process-rainfall CLI processes granules into spatiotemporal panel and event summary."""
    from floodrisk.processing.rainfall import create_mock_imerg_raster

    # Create 3 daily mock granules in tmp_path
    dates = ["20220901", "20220902", "20220903"]
    for d in dates:
        f = tmp_path / f"3B-DAY.MS.MRG.3IMERG.{d}-S000000-E235959.V07B.tif"
        create_mock_imerg_raster(f, west=77.0, north=13.5, rows=8, cols=8, base_rainfall_mm=30.0)

    out_panel = tmp_path / "panel.parquet"
    out_summary = tmp_path / "summary.parquet"

    runner = CliRunner()
    result = runner.invoke(main, [
        "process-rainfall",
        "--grid", "data/processed/grid_bengaluru_urban_1000m.gpkg",
        "--rainfall-dir", str(tmp_path),
        "--start-date", "2022-09-01",
        "--end-date", "2022-09-03",
        "--out-panel", str(out_panel),
        "--out-summary", str(out_summary)
    ])
    assert result.exit_code == 0
    assert "IMERG PRECIPITATION & TEMPORAL FEATURE PIPELINE" in result.output
    assert "Total Cell-Date Observations: 3510" in result.output
    assert out_panel.is_file()
    assert out_summary.is_file()


