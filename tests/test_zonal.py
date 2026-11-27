"""
Tests for Phase 2A zonal raster extraction, windowed reading, and feature-level provenance metadata.
"""

from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import box, Polygon
import rasterio
from rasterio.transform import from_origin

from floodrisk.processing.zonal import (
    RasterZonalExtractor,
    compute_terrain_zonal_features,
    compute_hydrology_zonal_features,
    compute_landcover_zonal_features,
    create_rainfall_grid_feature,
    GridFeatureMetadata,
    CategoricalZonalResult,
    ContinuousZonalResult
)


def test_windowed_raster_extraction(synthetic_valid_raster: Path):
    """Verify memory-efficient windowed raster extraction for a 1-km cell bounding box."""
    with RasterZonalExtractor(synthetic_valid_raster, "Synthetic DEM", "30 m") as extractor:
        # Cell bounds in EPSG:6933 corresponding to test region
        data, nodata = extractor.read_window_for_cell_bounds(
            minx_6933=7472000.0,
            miny_6933=1625000.0,
            maxx_6933=7473000.0,
            maxy_6933=1626000.0
        )
        assert isinstance(data, np.ndarray)
        assert data.ndim == 2
        assert data.size > 0


def test_terrain_zonal_feature_computation():
    """Verify statistical elevation features and NoData filtering."""
    mock_elev_data = np.array([
        [900, 910, 920],
        [890, -32768, 930],  # Contains NoData
        [880, 895, 940]
    ], dtype=np.int16)

    features = compute_terrain_zonal_features(mock_elev_data, nodata=-32768, grid_id="g1000_7472_1625")
    assert len(features) == 4
    feat_dict = {f.feature_name: f.feature_value for f in features}

    assert feat_dict["elevation_min_m"] == 880.0
    assert feat_dict["elevation_max_m"] == 940.0
    assert 905.0 < feat_dict["elevation_mean_m"] < 915.0

    # Lineage and units check
    for f in features:
        assert f.grid_id == "g1000_7472_1625"
        assert f.units == "metres"
        assert f.source_dataset == "SRTM GL1 30m DEM"
        assert "Filtered NoData" in f.nodata_handling


def test_hydrology_zonal_feature_computation():
    """Verify upstream contributing area (upa) max and mean calculations."""
    mock_upa_data = np.array([
        [0.5, 1.2, 5.8],
        [0.8, -9999.0, 120.4],
        [1.1, 2.4, 250.0]
    ], dtype=np.float32)

    features = compute_hydrology_zonal_features(mock_upa_data, nodata=-9999.0, grid_id="g1000_7472_1625")
    assert len(features) == 2
    feat_dict = {f.feature_name: f.feature_value for f in features}

    assert feat_dict["upa_max_sqkm"] == 250.0
    assert feat_dict["upa_mean_sqkm"] > 0.0


def test_landcover_zonal_fractions():
    """Verify categorical fraction extraction for built-up and water bodies."""
    # 50: built-up, 80: water, 10: trees
    mock_lc_data = np.array([
        [50, 50, 10, 10],
        [50, 50, 80, 10],
        [10, 10, 80, 80],
        [10, 10, 10, 10]
    ], dtype=np.uint8)

    features = compute_landcover_zonal_features(mock_lc_data, nodata=0, grid_id="g1000_7472_1625")
    feat_dict = {f.feature_name: f.feature_value for f in features}

    # 4 out of 16 pixels are built-up (25%)
    assert feat_dict["fraction_built_up"] == 0.25
    # 3 out of 16 pixels are water (18.75%)
    assert feat_dict["fraction_water_bodies"] == 0.1875


def test_rainfall_feature_disclaimer_retention():
    """Verify that cell-level rainfall explicitly retains the scientific resolution disclaimer."""
    feature = create_rainfall_grid_feature(
        precipitation_mm=42.5,
        grid_id="g1000_7472_1625",
        source_dataset="NASA GPM IMERG V07B",
        native_resolution="0.1 degree (~10 km)"
    )
    assert feature.feature_name == "daily_precipitation_mm"
    assert feature.feature_value == 42.5
    assert feature.units == "mm"
    assert "DISCLAIMER" in feature.spatial_precision_note
    assert "indexing alignment only" in feature.spatial_precision_note


def test_polygon_window_edge_effect_elimination(tmp_path: Path):
    """
    CRITICAL AUDIT TEST:
    Verify that pixels inside the rectangular read window but outside the polygon
    are strictly excluded by geometry masking, preventing pixel leakage into zonal statistics.
    """
    # Create a 20x20 synthetic raster in EPSG:4326
    # Pixels inside (5..15, 5..15) are water (80), pixels outside are built-up (50)
    width, height = 20, 20
    data = np.ones((height, width), dtype=np.uint8) * 50  # Background = built-up (50)
    data[5:15, 5:15] = 80  # Center block = water (80)

    p = tmp_path / "synthetic_leak_test.tif"
    transform = from_origin(77.50, 13.00, 0.001, 0.001)

    with rasterio.open(
        p, "w", driver="GTiff", height=height, width=width, count=1,
        dtype=data.dtype, crs="EPSG:4326", transform=transform, nodata=0
    ) as dst:
        dst.write(data, 1)

    with RasterZonalExtractor(p, "Synthetic Landcover", "10 m") as extractor:
        # Define a polygon in EPSG:6933 that transforms to the central water block (lon 77.505 to 77.515, lat 12.985 to 12.995)
        # We transform back to EPSG:6933 to create geom_6933
        from floodrisk.spatial.crs import get_transformer, WGS84_CRS, DEFAULT_ANALYSIS_CRS
        to_6933 = get_transformer(WGS84_CRS, DEFAULT_ANALYSIS_CRS)
        
        x0, y0 = to_6933.transform(77.505, 12.985)
        x1, y1 = to_6933.transform(77.515, 12.995)
        geom_6933 = box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

        # 1. Test read_window_for_geometry with exact mask
        raw_data, inside_mask, nodata = extractor.read_window_for_geometry(geom_6933, band=1, all_touched=False)
        assert np.sum(inside_mask) > 0
        assert np.sum(~inside_mask) > 0, "Enclosing rectangular window must contain outside pixels"

        # The inside pixels must be pure water (80) with 0 built-up (50) leakage!
        inside_pixels = raw_data[inside_mask]
        assert (inside_pixels == 80).all(), "Zero pixels of built-up background (50) must leak into water polygon"

        # 2. Test categorical stats
        cat_res = extractor.extract_categorical_zonal_stats(geom_6933, grid_id="g1000_test", nodata_value=0)
        assert cat_res.fraction_water_bodies == 1.0
        assert cat_res.fraction_built_up == 0.0
        assert cat_res.nodata_pixel_count == 0


def test_continuous_zonal_stats_and_nodata_filtering(tmp_path: Path):
    """Verify continuous zonal statistics (mean, min, max, std) and NoData exclusion."""
    width, height = 10, 10
    data = np.full((height, width), 900.0, dtype=np.float32)
    data[2:8, 2:8] = 950.0
    data[3, 3] = -9999.0  # Embedded NoData

    p = tmp_path / "synthetic_cont.tif"
    transform = from_origin(77.50, 13.00, 0.001, 0.001)

    with rasterio.open(
        p, "w", driver="GTiff", height=height, width=width, count=1,
        dtype=data.dtype, crs="EPSG:4326", transform=transform, nodata=-9999.0
    ) as dst:
        dst.write(data, 1)

    with RasterZonalExtractor(p, "Synthetic DEM", "30 m") as extractor:
        from floodrisk.spatial.crs import get_transformer, WGS84_CRS, DEFAULT_ANALYSIS_CRS
        to_6933 = get_transformer(WGS84_CRS, DEFAULT_ANALYSIS_CRS)
        x0, y0 = to_6933.transform(77.502, 12.992)
        x1, y1 = to_6933.transform(77.508, 12.998)
        geom = box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

        res = extractor.extract_continuous_zonal_stats(geom, grid_id="g1000_test_cont", feature_prefix="elevation", units="metres")
        assert res.valid_pixel_count > 0
        assert res.nodata_pixel_count >= 1
        assert res.mean == pytest.approx(950.0, abs=1.0)
        assert res.min == 950.0
        assert len(res.features) == 4


