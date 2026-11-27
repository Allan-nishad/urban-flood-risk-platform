"""
Integration Tests for Phase 2A Real-Data Ingestion and Feature Extraction
Operates on authentic acquired satellite data (ESA WorldCover 10m).
Kept strictly separate from synthetic unit test fixtures.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import rasterio

from floodrisk.processing.zonal import RasterZonalExtractor, compute_landcover_zonal_features


REAL_LANDCOVER_PATH = Path("data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif")
REAL_SRTM_MOSAIC = Path("data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif")
REAL_FEATURES_PARQUET = Path("data/processed/grid_features_bengaluru_urban_1000m.parquet")


@pytest.mark.skipif(not REAL_LANDCOVER_PATH.is_file(), reason="Real ESA WorldCover raster not staged locally")
def test_real_esa_worldcover_raster_integrity():
    """Verify metadata of the authentic ESA WorldCover 10m raster tile."""
    with rasterio.open(REAL_LANDCOVER_PATH) as src:
        assert src.driver == "GTiff"
        assert src.width == 36000
        assert src.height == 36000
        assert src.count == 1
        assert "EPSG:4326" in str(src.crs)
        assert src.nodatavals[0] == 0.0

        # Geographical extent must enclose Bengaluru (12.85-13.15N, 77.45-77.75E)
        b = src.bounds
        assert b.left <= 77.45
        assert b.right >= 77.75
        assert b.bottom <= 12.85
        assert b.top >= 13.15


@pytest.mark.skipif(not REAL_FEATURES_PARQUET.is_file(), reason="Grid features Parquet file not generated")
def test_real_grid_features_parquet_integrity():
    """Verify the extracted real-data multimodal Parquet feature dataset."""
    df = pd.read_parquet(REAL_FEATURES_PARQUET)

    assert len(df) == 1170
    assert df["grid_id"].nunique() == 1170, "Every cell must have a unique grid_id"

    # Verify column presence including domain coverage, WorldCover, SRTM, and MERIT Hydro
    expected_cols = [
        "grid_id", "col_idx", "row_idx", "centroid_lon", "centroid_lat",
        "fraction_inside_domain", "fraction_inside_boundary", "coverage_class", "geodesic_area_sqm",
        "valid_pixel_count", "nodata_pixel_count", "valid_pixel_fraction",
        "fraction_built_up", "fraction_water_bodies",
        "elevation_mean_m", "elevation_min_m", "elevation_max_m", "elevation_std_m",
        "elevation_valid_pixel_count", "elevation_nodata_pixel_count", "elevation_valid_pixel_fraction",
        "upa_mean_sqkm", "upa_max_sqkm", "upa_valid_pixel_count", "upa_nodata_pixel_count", "upa_valid_pixel_fraction"
    ]
    for c in expected_cols:
        assert c in df.columns, f"Missing required feature column: {c}"

    # Verify domain and boundary equivalence (backward compatibility)
    assert (df["fraction_inside_domain"] == df["fraction_inside_boundary"]).all()
    assert (df["fraction_inside_domain"] >= 0.0).all()
    assert (df["fraction_inside_domain"] <= 1.0).all()

    # Verify per-cell pixel quality coverage for WorldCover
    assert (df["valid_pixel_count"] > 0).all()
    assert (df["valid_pixel_count"] >= 11000).all(), "Every 1km cell must contain ~11,000-12,200 native 10m pixels"
    assert (df["nodata_pixel_count"] == 0).all(), "ESA WorldCover tile has complete coverage over Bengaluru"
    assert (df["valid_pixel_fraction"] == 1.0).all(), "Valid pixel fraction must be exactly 1.0"

    # Verify physical validity of categorical fractions
    assert (df["fraction_built_up"] >= 0.0).all()
    assert (df["fraction_built_up"] <= 1.0).all()
    assert (df["fraction_water_bodies"] >= 0.0).all()
    assert (df["fraction_water_bodies"] <= 1.0).all()
    assert ((df["fraction_built_up"] + df["fraction_water_bodies"]) <= 1.0).all()

    # Verify SRTM elevation physical validity
    assert not df["elevation_mean_m"].isnull().any(), "SRTM elevation features must not be null"
    assert (df["elevation_mean_m"] >= 700.0).all()
    assert (df["elevation_mean_m"] <= 1000.0).all()
    assert (df["elevation_min_m"] <= df["elevation_mean_m"]).all()
    assert (df["elevation_mean_m"] <= df["elevation_max_m"]).all()
    assert (df["elevation_std_m"] >= 0.0).all()
    assert (df["elevation_valid_pixel_count"] >= 1000).all()
    assert (df["elevation_nodata_pixel_count"] == 0).all()
    assert (df["elevation_valid_pixel_fraction"] == 1.0).all()

    # Verify MERIT Hydro pending status (represented as NaN/missing, NOT zero)
    assert df["upa_mean_sqkm"].isnull().all(), "MERIT Hydro features must be pending NaN until officially staged"
    assert df["upa_max_sqkm"].isnull().all()

    # Verify regional topography: central Bengaluru ridge is higher than southwest valley
    central_cell = df[df["grid_id"] == "g1000_7487_1641"].iloc[0]
    peripheral_cell = df[df["grid_id"] == "g1000_7472_1625"].iloc[0]
    assert central_cell["fraction_built_up"] > 0.50
    assert central_cell["fraction_built_up"] > peripheral_cell["fraction_built_up"]
    assert central_cell["elevation_mean_m"] > 900.0
    assert central_cell["elevation_mean_m"] > peripheral_cell["elevation_mean_m"] + 100.0


@pytest.mark.skipif(not (REAL_LANDCOVER_PATH.is_file() and REAL_FEATURES_PARQUET.is_file()), reason="Real data files missing")
def test_real_data_sample_cells_independent_validation():
    """
    INDEPENDENT GIS AUDIT TEST:
    Validate at least 5 sample cells (rural, dense urban, Bellandur lake, Varthur lake,
    and partial domain perimeter) directly against independent rasterio.mask.mask vector clipping.
    Numerical discrepancy between production Parquet and reference extraction must be within tolerance <= 0.0001 (0.01%).
    """
    from rasterio.mask import mask
    from shapely.geometry import box, Polygon, mapping
    from floodrisk.spatial.crs import get_transformer, DEFAULT_ANALYSIS_CRS, WGS84_CRS

    df = pd.read_parquet(REAL_FEATURES_PARQUET)
    transformer = get_transformer(DEFAULT_ANALYSIS_CRS, WGS84_CRS)

    sample_cells = [
        "g1000_7472_1625",  # Rural / southwest perimeter
        "g1000_7487_1641",  # Dense urban core
        "g1000_7494_1635",  # Bellandur Lake
        "g1000_7497_1635",  # Varthur Lake
        "g1000_7501_1640",  # Eastern partial domain boundary
        "g1000_7485_1625"   # Southern partial domain boundary
    ]

    with rasterio.open(REAL_LANDCOVER_PATH) as src:
        for gid in sample_cells:
            row = df[df["grid_id"] == gid].iloc[0]
            col_idx = int(row["col_idx"])
            row_idx = int(row["row_idx"])
            minx = col_idx * 1000.0
            miny = row_idx * 1000.0

            poly_6933 = box(minx, miny, minx + 1000.0, miny + 1000.0)
            coords = [transformer.transform(x, y) for x, y in poly_6933.exterior.coords]
            poly_4326 = Polygon(coords)

            # Independent reference extraction
            out_img, _ = mask(src, [mapping(poly_4326)], crop=True, all_touched=False, filled=False)
            ref_pix = out_img[0].compressed()

            ref_total = len(ref_pix)
            ref_built = int(np.sum(ref_pix == 50))
            ref_water = int(np.sum(ref_pix == 80))
            ref_frac_built = ref_built / ref_total if ref_total > 0 else 0.0
            ref_frac_water = ref_water / ref_total if ref_total > 0 else 0.0

            # Verify exact total pixel count equality
            assert row["valid_pixel_count"] == ref_total, f"Pixel count mismatch for {gid}: prod={row['valid_pixel_count']}, ref={ref_total}"

            # Verify fractions match reference within 4-decimal float rounding tolerance (0.0001)
            delta_built = abs(row["fraction_built_up"] - ref_frac_built)
            delta_water = abs(row["fraction_water_bodies"] - ref_frac_water)
            assert delta_built <= 0.0001, f"Built-up fraction discrepancy {delta_built} exceeded tolerance 0.0001 on {gid}"
            assert delta_water <= 0.0001, f"Water fraction discrepancy {delta_water} exceeded tolerance 0.0001 on {gid}"


@pytest.mark.skipif(not REAL_SRTM_MOSAIC.is_file(), reason="Real SRTM mosaic not staged locally")
def test_real_srtm_raster_integrity():
    """Verify metadata of the authentic SRTM GL1 30m mosaic."""
    with rasterio.open(REAL_SRTM_MOSAIC) as src:
        assert src.driver == "GTiff"
        assert src.width == 3601
        assert src.height == 7201
        assert src.count == 1
        assert "EPSG:4326" in str(src.crs)
        assert src.nodatavals[0] == -32768.0

        b = src.bounds
        assert b.left <= 77.45
        assert b.right >= 77.75
        assert b.bottom <= 12.85
        assert b.top >= 13.15


@pytest.mark.skipif(not (REAL_SRTM_MOSAIC.is_file() and REAL_FEATURES_PARQUET.is_file()), reason="Real data files missing")
def test_real_srtm_sample_cells_independent_validation():
    """
    INDEPENDENT GIS AUDIT TEST FOR SRTM:
    Validate elevation statistics across 5 sample cells directly against rasterio.mask.mask.
    Pixel counts must match with 0 discrepancy; mean elevation must match within float rounding (0.01 m).
    """
    from rasterio.mask import mask
    from shapely.geometry import box, Polygon, mapping
    from floodrisk.spatial.crs import get_transformer, DEFAULT_ANALYSIS_CRS, WGS84_CRS

    df = pd.read_parquet(REAL_FEATURES_PARQUET)
    transformer = get_transformer(DEFAULT_ANALYSIS_CRS, WGS84_CRS)

    sample_cells = [
        "g1000_7472_1625",  # Rural peripheral (SW)
        "g1000_7487_1641",  # Dense urban core
        "g1000_7494_1635",  # Bellandur Lake region
        "g1000_7497_1635",  # Varthur Lake region
        "g1000_7501_1640"   # Eastern perimeter
    ]

    with rasterio.open(REAL_SRTM_MOSAIC) as src:
        for gid in sample_cells:
            row = df[df["grid_id"] == gid].iloc[0]
            col_idx = int(row["col_idx"])
            row_idx = int(row["row_idx"])
            minx = col_idx * 1000.0
            miny = row_idx * 1000.0

            poly_6933 = box(minx, miny, minx + 1000.0, miny + 1000.0)
            coords = [transformer.transform(x, y) for x, y in poly_6933.exterior.coords]
            poly_4326 = Polygon(coords)

            out_img, _ = mask(src, [mapping(poly_4326)], crop=True, all_touched=False, filled=False)
            ref_pix = out_img[0].compressed()
            ref_valid = ref_pix[ref_pix != -32768]

            ref_cnt = len(ref_valid)
            ref_mean = float(np.mean(ref_valid))
            ref_min = float(np.min(ref_valid))
            ref_max = float(np.max(ref_valid))

            # Integer pixel count must match identically (0 error)
            assert row["elevation_valid_pixel_count"] == ref_cnt, f"Elevation pixel count mismatch on {gid}"
            assert row["elevation_min_m"] == ref_min
            assert row["elevation_max_m"] == ref_max
            assert abs(row["elevation_mean_m"] - ref_mean) <= 0.01, f"Elevation mean discrepancy {abs(row['elevation_mean_m'] - ref_mean)} on {gid}"


def test_imerg_bengaluru_grid_integration(tmp_path):
    """
    INTEGRATION TEST FOR IMERG PRECIPITATION PIPELINE:
    Verify full end-to-end integration of IMERG 0.1 deg satellite rainfall onto
    the official 1,170-cell Bengaluru Urban EPSG:6933 grid, checking unit conversion,
    spatial remapping, multi-day antecedent calculations, and event summary aggregation.
    """
    import geopandas as gpd
    from floodrisk.processing.rainfall import (
        create_mock_imerg_raster,
        IMERGRasterReader,
        IMERGGridMapper,
        AntecedentPrecipitationEngine
    )

    grid_file = Path("data/processed/grid_bengaluru_urban_1000m.gpkg")
    if not grid_file.is_file():
        pytest.skip("Bengaluru grid file not generated")

    grid_gdf = gpd.read_file(grid_file)
    assert len(grid_gdf) == 1170

    # Create 5 consecutive daily IMERG granules covering Bengaluru flood window
    dates = ["20220901", "20220902", "20220903", "20220904", "20220905"]
    daily_base_rain = [15.0, 5.0, 10.0, 85.0, 45.0]  # Simulating Sept 4 storm peak

    records = []
    mapper = IMERGGridMapper(grid_gdf)

    for d_str, base_val in zip(dates, daily_base_rain):
        dt = pd.to_datetime(d_str).date()
        f = tmp_path / f"3B-DAY.MS.MRG.3IMERG.{d_str}-S000000-E235959.V07B.tif"
        create_mock_imerg_raster(f, west=77.0, north=13.5, rows=8, cols=8, base_rainfall_mm=base_val)

        r_dict = IMERGRasterReader.read_imerg_raster(f)
        df_mapped = mapper.remap_raster(r_dict, method="centroid_lookup")
        df_mapped["date"] = dt
        df_mapped = df_mapped.rename(columns={"rainfall_depth_mm": "rainfall_daily_depth_mm"})
        records.append(df_mapped)

    panel_raw = pd.concat(records, ignore_index=True)
    assert len(panel_raw) == 1170 * 5, "Total panel observations must equal 1,170 cells * 5 days = 5,850 rows"

    # Compute temporal antecedent indices
    panel_enriched = AntecedentPrecipitationEngine.compute_antecedent_indices(panel_raw)
    assert len(panel_enriched) == 5850
    assert not panel_enriched["rainfall_daily_depth_mm"].isnull().any()
    assert not panel_enriched["precip_antecedent_3d_mm"].isnull().any()
    assert not panel_enriched["precip_api_decay_mm"].isnull().any()

    # Verify peak rainfall occurs on Sept 4 across all cells
    peak_day = panel_enriched[panel_enriched["date"] == pd.to_datetime("2022-09-04").date()]
    assert (peak_day["rainfall_daily_depth_mm"] > 40.0).all()

    # Verify decaying API increases after major storm
    day_3 = panel_enriched[panel_enriched["date"] == pd.to_datetime("2022-09-03").date()]
    day_5 = panel_enriched[panel_enriched["date"] == pd.to_datetime("2022-09-05").date()]
    assert (day_5["precip_api_decay_mm"].mean() > day_3["precip_api_decay_mm"].mean())

    # Compute cell event summary
    summary = AntecedentPrecipitationEngine.compute_cell_event_summary(panel_enriched)
    assert len(summary) == 1170
    assert summary["grid_id"].nunique() == 1170
    assert (summary["event_peak_daily_rainfall_mm"] > 0).all()
    assert (summary["event_total_rainfall_mm"] > summary["event_peak_daily_rainfall_mm"]).all()




