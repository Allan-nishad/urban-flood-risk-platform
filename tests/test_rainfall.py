"""
Tests for rainfall unit inspection, variable verification, and rate-to-depth conversion,
spatial remapping onto 1-km equal-area cells, and antecedent precipitation indices.
"""

from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import pytest

from floodrisk.processing.rainfall import (
    parse_and_validate_rainfall_units,
    convert_precipitation_to_depth_mm,
    IMERGDownloader,
    IMERGRasterReader,
    IMERGGridMapper,
    AntecedentPrecipitationEngine,
    create_mock_imerg_raster
)


def test_imerg_half_hourly_rate_conversion():
    """Verify 30-minute precipitationCal [mm/hr] correctly converts using 0.5 hour factor."""
    meta = parse_and_validate_rainfall_units(
        variable_name="precipitationCal",
        units_attribute="mm/hr",
        temporal_interval_minutes=30.0
    )
    assert meta["quantity_type"] == "rate"
    assert meta["conversion_factor"] == 0.5
    assert meta["converted_units"] == "mm"

    # Test numerical conversion
    rates = np.array([0.0, 10.0, 50.0])  # mm/hr
    depths, m = convert_precipitation_to_depth_mm(rates, "precipitationCal", "mm/hr", 30.0)
    assert np.allclose(depths, [0.0, 5.0, 25.0])


def test_imerg_daily_depth_no_unnecessary_multiplication():
    """CRITICAL TEST: Daily IMERG product is ALREADY accumulated depth; factor must be 1.0, not 0.5."""
    meta = parse_and_validate_rainfall_units(
        variable_name="precipitation",
        units_attribute="mm",
        temporal_interval_minutes=1440.0
    )
    assert meta["quantity_type"] == "depth"
    assert meta["conversion_factor"] == 1.0
    assert meta["converted_units"] == "mm"

    daily_vals = np.array([12.5, 84.0])
    depths, _ = convert_precipitation_to_depth_mm(daily_vals, "precipitation", "mm", 1440.0)
    assert np.allclose(depths, daily_vals)


def test_missing_or_unsupported_units_rejected():
    """Verify that absent or unrecognized units raise an exception instead of guessing."""
    with pytest.raises(ValueError, match="missing units attribute"):
        parse_and_validate_rainfall_units(variable_name="custom_sensor", units_attribute="")

    with pytest.raises(ValueError, match="Unrecognized precipitation units"):
        parse_and_validate_rainfall_units(variable_name="custom_sensor", units_attribute="furlongs_per_fortnight")


def test_imerg_downloader_url_and_script_generation(tmp_path):
    """Verify NASA GES DISC canonical URL synthesis and curl script generation."""
    target_dt = date(2022, 9, 4)
    url = IMERGDownloader.get_daily_url(target_dt)
    expected = (
        "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/"
        "2022/09/3B-DAY.MS.MRG.3IMERG.20220904-S000000-E235959.V07B.nc4"
    )
    assert url == expected

    # Date range generation
    start = date(2022, 8, 25)
    end = date(2022, 9, 10)
    pairs = IMERGDownloader.generate_date_range_urls(start, end)
    assert len(pairs) == 17
    assert pairs[0][0] == start
    assert pairs[-1][0] == end

    # Curl download script generation
    script_file = tmp_path / "download.sh"
    generated_path = IMERGDownloader.generate_curl_download_script(
        start_date=start,
        end_date=end,
        output_dir=tmp_path / "raw_imerg",
        script_path=script_file
    )
    assert generated_path.is_file()
    content = generated_path.read_text(encoding="utf-8")
    assert "--netrc" in content
    assert "3B-DAY.MS.MRG.3IMERG.20220904-S000000-E235959.V07B.nc4" in content


def test_imerg_raster_reading(tmp_path):
    """Verify reading of IMERG raster metadata, tags, and array orientation."""
    mock_raster = tmp_path / "mock_imerg_20220904.tif"
    create_mock_imerg_raster(mock_raster, west=77.0, north=13.5, rows=6, cols=6, base_rainfall_mm=40.0)

    raster_dict = IMERGRasterReader.read_imerg_raster(mock_raster, variable_name="precipitation")
    assert raster_dict["data"].shape == (6, 6)
    assert raster_dict["crs"] == "EPSG:4326"
    assert raster_dict["units_meta"]["converted_units"] == "mm"
    assert raster_dict["units_meta"]["conversion_factor"] == 1.0
    assert np.all(raster_dict["data"] >= 0.0)


def test_imerg_spatial_grid_remapping(tmp_path):
    """Verify remapping of 0.1° IMERG rainfall to 1-km EPSG:6933 grid cells."""
    # Create a synthetic 4-cell EPSG:6933 grid over Bengaluru domain
    # Projected coordinates around (7480000, 1640000)
    geoms = [
        box(7480000, 1640000, 7481000, 1641000),
        box(7481000, 1640000, 7482000, 1641000),
        box(7480000, 1641000, 7481000, 1642000),
        box(7481000, 1641000, 7482000, 1642000)
    ]
    grid_gdf = gpd.GeoDataFrame({
        "grid_id": [f"g1000_test_{i}" for i in range(4)],
        "geometry": geoms
    }, crs="EPSG:6933")

    mock_raster = tmp_path / "mock_imerg_bengaluru.tif"
    create_mock_imerg_raster(mock_raster, west=77.0, north=13.5, rows=10, cols=10, base_rainfall_mm=50.0)
    raster_dict = IMERGRasterReader.read_imerg_raster(mock_raster)

    mapper = IMERGGridMapper(grid_gdf)
    assert "1-km grid remapping provides spatial indexing alignment only" in mapper.SCIENTIFIC_DISCLAIMER

    # 1. Centroid lookup method
    df_centroid = mapper.remap_raster(raster_dict, method="centroid_lookup")
    assert len(df_centroid) == 4
    assert df_centroid["rainfall_depth_mm"].notnull().all()
    assert (df_centroid["rainfall_depth_mm"] > 0).all()

    # 2. Bilinear interpolation method
    df_bilinear = mapper.remap_raster(raster_dict, method="bilinear")
    assert len(df_bilinear) == 4
    assert df_bilinear["rainfall_depth_mm"].notnull().all()
    assert (df_bilinear["rainfall_depth_mm"] > 0).all()


def test_antecedent_precipitation_engine_calculations():
    """Verify exact mathematical calculation of 3-day, 7-day, 14-day antecedent rainfall and decaying API."""
    # Build 5-day time series for a single test cell
    # Daily precipitation: Day 1: 10 mm, Day 2: 20 mm, Day 3: 30 mm, Day 4: 40 mm, Day 5: 50 mm
    dates = pd.date_range("2022-09-01", periods=5, freq="D")
    df_input = pd.DataFrame({
        "grid_id": ["g1000_test"] * 5,
        "date": dates,
        "rainfall_daily_depth_mm": [10.0, 20.0, 30.0, 40.0, 50.0]
    })

    enriched = AntecedentPrecipitationEngine.compute_antecedent_indices(
        df_input, decay_coefficient=0.85, max_decay_window_days=14
    )

    # Day 1: No antecedent rainfall
    assert enriched.loc[0, "precip_antecedent_3d_mm"] == 0.0
    assert enriched.loc[0, "precip_api_decay_mm"] == 0.0

    # Day 2: Prior day is Day 1 (10 mm)
    assert enriched.loc[1, "precip_antecedent_3d_mm"] == 10.0
    # API = 10 * 0.85^1 = 8.5
    assert np.isclose(enriched.loc[1, "precip_api_decay_mm"], 8.5, atol=0.01)

    # Day 3: Prior days are Day 2 (20 mm) and Day 1 (10 mm)
    assert enriched.loc[2, "precip_antecedent_3d_mm"] == 30.0
    # API = 20 * 0.85^1 + 10 * 0.85^2 = 17.0 + 7.225 = 24.225 -> 24.23
    assert np.isclose(enriched.loc[2, "precip_api_decay_mm"], 24.23, atol=0.02)

    # Day 4: Prior 3 days are Day 3 (30), Day 2 (20), Day 1 (10) -> Sum = 60
    assert enriched.loc[3, "precip_antecedent_3d_mm"] == 60.0
    # API = 30 * 0.85^1 + 20 * 0.85^2 + 10 * 0.85^3 = 25.5 + 14.45 + 6.14125 = 46.09
    assert np.isclose(enriched.loc[3, "precip_api_decay_mm"], 46.09, atol=0.02)

    # Day 5: Prior 3 days are Day 4 (40), Day 3 (30), Day 2 (20) -> Sum = 90
    assert enriched.loc[4, "precip_antecedent_3d_mm"] == 90.0

    # Event summary check
    summary = AntecedentPrecipitationEngine.compute_cell_event_summary(enriched)
    assert summary.loc[0, "event_peak_daily_rainfall_mm"] == 50.0
    assert summary.loc[0, "event_total_rainfall_mm"] == 150.0
    assert summary.loc[0, "event_max_antecedent_3d_mm"] == 90.0
    assert summary.loc[0, "event_rainy_days_count"] == 5
    assert summary.loc[0, "event_heavy_rain_days_count"] == 0  # None >= 64.5 mm
