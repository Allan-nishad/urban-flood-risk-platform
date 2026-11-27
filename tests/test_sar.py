"""
Unit and Integration Tests for Sentinel-1A SAR Processing, Backscatter Differencing,
Candidate Water/Flood Detection, Evidence Comparison, and Grid Feature Aggregation.
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from rasterio.transform import from_origin
import rasterio

from floodrisk.processing.sar import (
    CANONICAL_SENTINEL1_SCENES,
    MatchClassification,
    Sentinel1SceneRegistry,
    SARBackscatterDifferencer,
    SARCandidateWaterDetector,
    SARIncidentEvidenceComparator,
    SARDomainGridAggregator,
    create_mock_sar_pair,
    create_study_domain_sar_rasters,
    process_sentinel1_pipeline
)
from click.testing import CliRunner
from floodrisk.cli import main


class TestSentinel1SAR:

    def test_canonical_scenes_metadata(self):
        """Verify canonical Sentinel-1A Level-1 GRDH scenes on Relative Orbit 165 Descending."""
        pre = CANONICAL_SENTINEL1_SCENES["pre_event"]
        evt = CANONICAL_SENTINEL1_SCENES["event_peak"]
        post = CANONICAL_SENTINEL1_SCENES["post_event"]

        assert pre["platform"] == "Sentinel-1A"
        assert pre["relative_orbit"] == 165
        assert pre["flight_direction"] == "DESCENDING"
        assert pre["frame_number"] == 549
        assert pre["polarisation"] == "VV+VH"

        assert evt["relative_orbit"] == 165
        assert evt["flight_direction"] == "DESCENDING"
        assert evt["frame_number"] == 549

        assert post["relative_orbit"] == 165
        assert post["flight_direction"] == "DESCENDING"
        assert post["frame_number"] == 549

        # Verify exact same-orbit compatibility
        records = Sentinel1SceneRegistry.get_scene_pair_records()
        assert len(records) == 1
        pair = records[0]
        assert pair["relative_orbit"] == 165
        assert pair["flight_direction"] == "DESCENDING"
        assert pair["geometry_compatibility"].startswith("EXACT_MATCH")
        assert pair["time_difference_days"] == 24.0
        assert "Relative Orbit 91 rejected" in pair["notes"]

    def test_backscatter_differencing_math(self):
        """Verify mathematical correctness of dB difference and linear ratio."""
        # Case 1: Specular drop (open water inundation): pre = -8.0 dB, post = -16.0 dB
        pre = np.array([[-8.0, -10.0], [-18.0, np.nan]], dtype=np.float32)
        post = np.array([[-16.0, -5.0], [-18.0, -8.0]], dtype=np.float32)

        delta_db, ratio_lin, valid_mask = SARBackscatterDifferencer.compute_difference(pre, post)

        assert valid_mask[0, 0] is True or valid_mask[0, 0] == 1
        assert valid_mask[1, 1] is False or valid_mask[1, 1] == 0  # nan in pre

        # Pixel 0,0: post (-16) - pre (-8) = -8.0 dB
        assert np.isclose(delta_db[0, 0], -8.0, atol=1e-5)
        # linear ratio: 10^(-8/10) = 10^(-0.8) ~= 0.158489
        expected_ratio = 10.0 ** (-8.0 / 10.0)
        assert np.isclose(ratio_lin[0, 0], expected_ratio, atol=1e-5)

        # Pixel 0,1: double-bounce surge: post (-5) - pre (-10) = +5.0 dB
        assert np.isclose(delta_db[0, 1], 5.0, atol=1e-5)
        assert np.isclose(ratio_lin[0, 1], 10.0 ** (5.0 / 10.0), atol=1e-5)

        # Pixel 1,0: permanent water: post (-18) - pre (-18) = 0.0 dB
        assert np.isclose(delta_db[1, 0], 0.0, atol=1e-5)
        assert np.isclose(ratio_lin[1, 0], 1.0, atol=1e-5)

    def test_candidate_water_and_flood_detection(self):
        """Verify candidate water, flood change, and double-bounce detection rules."""
        detector = SARCandidateWaterDetector(
            water_threshold_db=-14.0,
            change_threshold_db=-2.5,
            double_bounce_threshold_db=2.5
        )

        # 4 pixels:
        # 0: Specular new flood (pre=-8 dB, post=-16 dB, built_up=False, perm=False) -> candidate_flood_change
        # 1: Permanent water (pre=-18 dB, post=-18 dB, built_up=False, perm=True) -> candidate_surface_water ONLY (not flood change)
        # 2: Double-bounce urban (pre=-8 dB, post=-4 dB, built_up=True, perm=False) -> double_bounce_candidate
        # 3: Unflooded dry urban (pre=-8 dB, post=-8 dB, built_up=True, perm=False) -> none
        pre = np.array([-8.0, -18.0, -8.0, -8.0], dtype=np.float32)
        post = np.array([-16.0, -18.0, -4.0, -8.0], dtype=np.float32)
        perm = np.array([False, True, False, False], dtype=bool)
        built = np.array([False, False, True, True], dtype=bool)

        res = detector.detect_candidate_water(pre, post, permanent_water_mask=perm, built_up_mask=built)

        # Pixel 0: candidate surface water and candidate flood change
        assert res["candidate_surface_water"][0] == True
        assert res["candidate_flood_change"][0] == True
        assert res["double_bounce_candidate"][0] == False

        # Pixel 1: candidate surface water, but NOT flood change (permanent water)
        assert res["candidate_surface_water"][1] == True
        assert res["candidate_flood_change"][1] == False
        assert res["double_bounce_candidate"][1] == False

        # Pixel 2: urban double bounce
        assert res["candidate_surface_water"][2] == False
        assert res["candidate_flood_change"][2] == False
        assert res["double_bounce_candidate"][2] == True

        # Pixel 3: unflooded
        assert res["candidate_surface_water"][3] == False
        assert res["candidate_flood_change"][3] == False
        assert res["double_bounce_candidate"][3] == False

    def test_incident_evidence_groups_and_exclusion(self, tmp_path):
        """Strictly test three-tier validation grouping and verify Group C is never a positive anchor."""
        incidents_data = [
            # Group A: confirmed_inundation
            {
                "event_id": "ev_001",
                "location_name": "Confirmed Site",
                "evidence_category": "confirmed_inundation",
                "latitude": 12.92,
                "longitude": 77.68,
                "spatial_uncertainty_m": 100.0,
                "grid_id": "g1000_7495_1635",
                "location_accuracy": "exact_point",
                "boundary_proximity_flag": False
            },
            # Group B: reported_waterlogging
            {
                "event_id": "ev_002",
                "location_name": "Waterlogged Road",
                "evidence_category": "reported_waterlogging",
                "latitude": 12.94,
                "longitude": 77.74,
                "spatial_uncertainty_m": 150.0,
                "grid_id": "g1000_7501_1637",
                "location_accuracy": "landmark_vicinity",
                "boundary_proximity_flag": True
            },
            # Group C: rainfall_only
            {
                "event_id": "ev_003",
                "location_name": "Rain Gauge Station",
                "evidence_category": "rainfall_only",
                "latitude": 12.97,
                "longitude": 77.69,
                "spatial_uncertainty_m": 50.0,
                "grid_id": "g1000_7496_1641",
                "location_accuracy": "exact_point",
                "boundary_proximity_flag": False
            },
            # Group C: unverified_report
            {
                "event_id": "ev_004",
                "location_name": "General Rumor",
                "evidence_category": "unverified_report",
                "latitude": 12.95,
                "longitude": 77.65,
                "spatial_uncertainty_m": 500.0,
                "grid_id": "g1000_7490_1638",
                "location_accuracy": "locality_centroid",
                "boundary_proximity_flag": False
            }
        ]
        inc_df = pd.DataFrame(incidents_data)

        # Create mock candidate change raster
        r_path = tmp_path / "mock_change.tif"
        arr = np.zeros((100, 100), dtype=np.uint8)
        # Put flood change at (12.92, 77.68)
        t = from_origin(77.60, 13.00, 0.002, 0.002)
        inv_t = ~t
        c, r = inv_t @ (77.68, 12.92)
        arr[int(r)-2:int(r)+3, int(c)-2:int(c)+3] = 1

        with rasterio.open(
            r_path, "w", driver="GTiff", height=100, width=100, count=1,
            dtype="uint8", crs="EPSG:4326", transform=t
        ) as dst:
            dst.write(arr, 1)

        grid_gdf = gpd.GeoDataFrame(
            {"grid_id": ["g1000_7495_1635"], "geometry": [gpd.points_from_xy([7495000], [1635000], crs="EPSG:6933")[0].buffer(500)]},
            crs="EPSG:6933"
        )

        comparator = SARIncidentEvidenceComparator(inc_df)
        comp_res = comparator.compare_with_candidate_raster(r_path, grid_gdf)

        assert len(comp_res) == 4

        # Group A
        r_a = comp_res[comp_res["event_id"] == "ev_001"].iloc[0]
        assert r_a["validation_group"] == "Group A (Primary)"
        assert r_a["match_classification"] == MatchClassification.DIRECT_MATCH.value
        assert r_a["buffer_intersects_candidate"] is True or r_a["buffer_intersects_candidate"] == 1
        assert r_a["candidate_pixels_in_buffer"] > 0

        # Group B: has boundary warning
        r_b = comp_res[comp_res["event_id"] == "ev_002"].iloc[0]
        assert r_b["validation_group"] == "Group B (Secondary)"
        assert "Grid assignment ambiguous" in r_b["sar_interpretation"]

        # Group C: rainfall_only
        r_c1 = comp_res[comp_res["event_id"] == "ev_003"].iloc[0]
        assert r_c1["validation_group"] == "Group C (Excluded)"
        assert r_c1["match_classification"] == MatchClassification.EXCLUDED_GROUP.value
        assert r_c1["buffer_intersects_candidate"] is False or r_c1["buffer_intersects_candidate"] == 0
        assert "Strictly excluded" in r_c1["sar_interpretation"]
        assert "rainfall_only" in r_c1["sar_interpretation"]

        # Group C: unverified_report
        r_c2 = comp_res[comp_res["event_id"] == "ev_004"].iloc[0]
        assert r_c2["validation_group"] == "Group C (Excluded)"
        assert r_c2["match_classification"] == MatchClassification.EXCLUDED_GROUP.value
        assert r_c2["buffer_intersects_candidate"] is False or r_c2["buffer_intersects_candidate"] == 0
        assert "Strictly excluded" in r_c2["sar_interpretation"]

    def test_domain_grid_aggregation_completeness(self):
        """Verify SARDomainGridAggregator produces complete features across 1,170 cells."""
        grid_feat_p = Path("data/processed/sentinel1_grid_features_bengaluru.parquet")
        assert grid_feat_p.is_file(), f"Missing deliverable: {grid_feat_p}"

        df = pd.read_parquet(grid_feat_p)
        assert len(df) == 1170, f"Expected 1,170 cells, got {len(df)}"

        expected_cols = [
            "grid_id", "sar_valid_pixels", "sar_valid_coverage_pct",
            "sar_pre_vv_mean_db", "sar_pre_vv_std_db", "sar_event_vv_mean_db", "sar_event_vv_std_db",
            "sar_delta_vv_mean_db", "sar_linear_ratio_mean",
            "sar_candidate_water_pixels", "sar_candidate_water_pct", "sar_candidate_water_area_m2",
            "sar_candidate_flood_pixels", "sar_candidate_flood_pct", "sar_candidate_flood_area_m2",
            "sar_double_bounce_pixels", "sar_double_bounce_pct",
            "sar_incident_count_in_cell", "sar_has_incident_intersection"
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing expected column: {col}"

        # Check physical ranges
        assert (df["sar_valid_coverage_pct"] >= 99.0).all()
        assert (df["sar_pre_vv_mean_db"] > -30.0).all() and (df["sar_pre_vv_mean_db"] < 10.0).all()
        assert (df["sar_event_vv_mean_db"] > -30.0).all() and (df["sar_event_vv_mean_db"] < 10.0).all()
        assert (df["sar_candidate_water_pct"] >= 0.0).all() and (df["sar_candidate_water_pct"] <= 100.0).all()
        assert (df["sar_candidate_flood_pct"] >= 0.0).all() and (df["sar_candidate_flood_pct"] <= 100.0).all()
        assert (df["sar_double_bounce_pct"] >= 0.0).all() and (df["sar_double_bounce_pct"] <= 100.0).all()

        # Cells with incidents should have incident counts > 0
        inc_cells = df[df["sar_incident_count_in_cell"] > 0]
        assert len(inc_cells) > 0, "Expected at least 1 grid cell with incident count > 0"

    def test_cli_download_and_process_sar(self):
        """Test download-sar and process-sar CLI commands."""
        runner = CliRunner()

        # Test download-sar
        res_dl = runner.invoke(main, ["download-sar"])
        assert res_dl.exit_code == 0
        assert "SENTINEL-1A SAR DATA RETRIEVAL & SCENE REGISTRY" in res_dl.output
        assert "Relative Orbit 165" in res_dl.output or "Orbit 165" in res_dl.output

        # Verify scripts exist
        assert Path("scripts/download_sentinel1_cdse.sh").is_file()
        assert Path("scripts/download_sentinel1_asf.sh").is_file()

        # Test process-sar
        res_pr = runner.invoke(main, ["process-sar"])
        assert res_pr.exit_code == 0
        assert "SENTINEL-1A SAR FLOOD-EVENT PROCESSING PIPELINE" in res_pr.output
        assert "PROCESSING COMPLETED:" in res_pr.output
        assert "Total Grid Cells:            1170" in res_pr.output

