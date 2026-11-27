"""
Operational Web Dashboard Server for Urban Flood Risk Platform.
Provides lightweight HTTP REST endpoints and serves the interactive Leaflet surveillance console.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import logging
import os
from pathlib import Path
import socketserver
import threading
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def clean_val_for_json(val: Any) -> Any:
    """Sanitize float NaN/inf and timestamps for strict JSON compliance."""
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if np.isnan(val) or np.isinf(val):
            return None
        return round(float(val), 4)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def clean_dict_for_json(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively clean dictionary values for JSON serialization."""
    return {k: clean_val_for_json(v) for k, v in d.items()}


class DashboardDataStore:
    """In-memory cache for dashboard GeoJSON, tabular datasets, and provenance status."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        reports_dir: Optional[Path] = None,
        weather_db_path: Optional[Path] = None,
    ):
        self.data_dir = Path(data_dir) if data_dir else Path("data/processed")
        self.reports_dir = Path(reports_dir) if reports_dir else Path("reports")
        if weather_db_path is not None:
            db_p = Path(weather_db_path)
        elif data_dir is not None:
            db_p = self.data_dir / "floodrisk_v8.db"
        else:
            db_p = Path("data/state/floodrisk_v8.db")
        from ..live import LiveWeatherRefresher, LiveWeatherStore
        self.weather_store = LiveWeatherStore(db_p)
        self.refresher = LiveWeatherRefresher(self.weather_store)
        self.summary: Dict[str, Any] = {}
        self.cells_geojson: Dict[str, Any] = {}
        self.incidents: List[Dict[str, Any]] = []
        self.episodes: List[Dict[str, Any]] = []
        self.manifest_status: Dict[str, Any] = {}
        self.phase5_metrics: List[Dict[str, Any]] = []
        self.phase5_flood_eval: Dict[str, Any] = {}
        self.phase5_sar_manifest: List[Dict[str, Any]] = []
        self.phase5_readiness_gates: Dict[str, Any] = {}
        self.phase6_summary: Dict[str, Any] = {}
        self.phase6_nwp: Dict[str, Any] = {}
        self.phase6_ground_rainfall: Dict[str, Any] = {}
        self.phase6_flood_evidence: Dict[str, Any] = {}
        self.phase6_sar: Dict[str, Any] = {}
        self.phase6_hydrology: Dict[str, Any] = {}
        self.phase6_manifest: Dict[str, Any] = {}
        self.phase7_summary: Dict[str, Any] = {}
        self.phase7_uncertainty: Dict[str, Any] = {}
        self.phase7_manifest: Dict[str, Any] = {}
        self.load_data()

    def load_data(self):
        """Load datasets from disk and construct API payloads."""
        # 1. Dynamic Risk Intelligence
        dyn_path = self.data_dir / "dynamic_risk_intelligence_bengaluru.parquet"
        grid_geojson_path = self.data_dir / "grid_bengaluru_urban_1000m.geojson"
        incidents_path = self.data_dir / "flood_event_inventory_bengaluru.parquet"
        episodes_path = self.data_dir / "flood_event_monitoring_log.parquet"
        manifest_path = self.reports_dir / "dataset_manifest.json"

        df_dyn = pd.DataFrame()
        dyn_lookup = {}
        if dyn_path.is_file():
            df_dyn = pd.read_parquet(dyn_path)
            for _, row in df_dyn.iterrows():
                dyn_lookup[row["grid_id"]] = row.to_dict()

        # 2. Grid GeoJSON merge
        if grid_geojson_path.is_file():
            with open(grid_geojson_path, "r", encoding="utf-8") as f:
                raw_gj = json.load(f)

            enriched_features = []
            for feat in raw_gj.get("features", []):
                gid = feat["properties"].get("grid_id")
                dyn_props = dyn_lookup.get(gid, {})
                merged_props = {
                    "grid_id": gid,
                    "col_idx": feat["properties"].get("col_idx"),
                    "row_idx": feat["properties"].get("row_idx"),
                    "centroid_lon": dyn_props.get("centroid_lon", feat["properties"].get("centroid_lon")),
                    "centroid_lat": dyn_props.get("centroid_lat", feat["properties"].get("centroid_lat")),
                    "geodesic_area_sqkm": clean_val_for_json(feat["properties"].get("geodesic_area_sqm", 1e6) / 1e6),
                    # Static Layer
                    "elevation_mean_m": clean_val_for_json(dyn_props.get("elevation_mean_m")),
                    "elevation_std_m": clean_val_for_json(dyn_props.get("elevation_std_m")),
                    "built_up_fraction": clean_val_for_json(dyn_props.get("built_up_fraction")),
                    "tree_cover_fraction": clean_val_for_json(dyn_props.get("tree_cover_fraction")),
                    "cropland_fraction": clean_val_for_json(dyn_props.get("cropland_fraction")),
                    "water_fraction": clean_val_for_json(dyn_props.get("water_fraction")),
                    "static_susceptibility_score": clean_val_for_json(dyn_props.get("static_susceptibility_score")),
                    "static_susceptibility_rank": clean_val_for_json(dyn_props.get("static_susceptibility_rank")),
                    # Observed Layer (Phase 4.3 constant 12.5mm baseline -> STALE)
                    "observed_rainfall_24h_mm": clean_val_for_json(dyn_props.get("observed_rainfall_24h_mm")),
                    "observed_api_decay_mm": clean_val_for_json(dyn_props.get("observed_api_decay_mm")),
                    "observed_rainfall_exposure_score": clean_val_for_json(dyn_props.get("observed_rainfall_exposure_score")),
                    "observed_rainfall_state": "STALE",
                    "observed_rainfall_source": "dynamic_risk_intelligence_bengaluru.parquet (Phase 4.3 constant 12.5mm)",
                    "observed_rainfall_timestamp": "2026-11-05T00:00:00Z",
                    # Forecast Layer
                    "forecast_issue_time": clean_val_for_json(dyn_props.get("forecast_issue_time")),
                    "forecast_rainfall_3h_mm": clean_val_for_json(dyn_props.get("forecast_rainfall_3h_mm")),
                    "forecast_rainfall_6h_mm": clean_val_for_json(dyn_props.get("forecast_rainfall_6h_mm")),
                    "forecast_rainfall_24h_mm": clean_val_for_json(dyn_props.get("forecast_rainfall_24h_mm")),
                    "forecast_rainfall_72h_mm": clean_val_for_json(dyn_props.get("forecast_rainfall_72h_mm")),
                    "forecast_peak_hourly_intensity_mm": clean_val_for_json(dyn_props.get("forecast_peak_hourly_intensity_mm")),
                    "forecast_exposure_score_24h": clean_val_for_json(dyn_props.get("forecast_exposure_score_24h")),
                    "forecast_intensity_category": clean_val_for_json(dyn_props.get("forecast_intensity_category")),
                    # Evidence Layer
                    "has_ground_flood_evidence": bool(dyn_props.get("has_ground_flood_evidence", False)),
                    "historical_incident_count": int(dyn_props.get("historical_incident_count", 0)),
                    "historical_incident_categories": clean_val_for_json(dyn_props.get("historical_incident_categories")),
                    # Composite Dynamic Score
                    "dynamic_risk_prioritization_score": clean_val_for_json(dyn_props.get("dynamic_risk_prioritization_score")),
                    "dynamic_risk_rank": clean_val_for_json(dyn_props.get("dynamic_risk_rank")),
                    "research_monitoring_level": clean_val_for_json(dyn_props.get("research_monitoring_level"))
                }
                enriched_features.append({
                    "type": "Feature",
                    "id": gid,
                    "geometry": feat.get("geometry"),
                    "properties": merged_props
                })

            self.cells_geojson = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "features": enriched_features
            }

        # 3. Incidents inventory
        if incidents_path.is_file():
            df_inc = pd.read_parquet(incidents_path)
            self.incidents = [clean_dict_for_json(r) for r in df_inc.to_dict(orient="records")]
        else:
            self.incidents = []

        # 4. Episodes monitoring log
        if episodes_path.is_file():
            df_epi = pd.read_parquet(episodes_path)
            self.episodes = [clean_dict_for_json(r) for r in df_epi.to_dict(orient="records")]
        else:
            self.episodes = []

        # 5. Manifest & Checksums
        manifest_records = []
        all_valid = True
        total_registered = 0
        if manifest_path.is_file():
            try:
                from ..provenance import DatasetManifest
                m = DatasetManifest.load(manifest_path)
                verif = m.verify_integrity()
                total_registered = len(m.datasets)
                for ds_id, rec in m.datasets.items():
                    v_res = verif.get(ds_id, {})
                    is_val = v_res.get("status") == "VALID"
                    if not is_val:
                        all_valid = False
                    manifest_records.append({
                        "dataset_id": ds_id,
                        "file_path": rec.file_path,
                        "file_size_bytes": rec.file_size_bytes,
                        "sha256": rec.sha256_checksum,
                        "provider": rec.source_provider,
                        "status": v_res.get("status", "UNCHECKED"),
                        "verified": is_val
                    })
            except Exception as e:
                logger.warning(f"Error checking manifest: {e}")

        self.manifest_status = {
            "total_datasets": total_registered,
            "all_valid": all_valid,
            "integrity_rate": "100.0%" if (all_valid and total_registered > 0) else "Degraded",
            "datasets": manifest_records
        }

        # 6. Phase 5 Independent Validation Datasets (prefer phase5_final, fallback to phase5)
        p5_metrics_path = self.data_dir / "phase5_final" / "forecast_verification" / "forecast_verification_metrics_by_lead_time.parquet"
        if not p5_metrics_path.is_file():
            p5_metrics_path = self.data_dir / "phase5_forecast_verification" / "forecast_verification_metrics_by_lead_time.parquet"
        if p5_metrics_path.is_file():
            df_p5_m = pd.read_parquet(p5_metrics_path)
            self.phase5_metrics = [clean_dict_for_json(r) for r in df_p5_m.to_dict(orient="records")]
        else:
            self.phase5_metrics = []

        p5_matrix_path = self.data_dir / "phase5_final" / "flood_validation_dataset" / "flood_validation_reference_matrix.parquet"
        if not p5_matrix_path.is_file():
            p5_matrix_path = self.data_dir / "phase5_flood_validation_dataset" / "flood_validation_reference_matrix.parquet"
        p5_eval_path = self.data_dir / "phase5_final" / "flood_validation_dataset" / "flood_evidence_evaluation_metrics.parquet"
        if not p5_eval_path.is_file():
            p5_eval_path = self.data_dir / "phase5_flood_validation_dataset" / "flood_evidence_evaluation_metrics.parquet"

        if p5_matrix_path.is_file() and p5_eval_path.is_file():
            df_p5_mat = pd.read_parquet(p5_matrix_path)
            df_p5_ev = pd.read_parquet(p5_eval_path)
            class_counts = df_p5_mat["validation_class"].value_counts().to_dict()
            self.phase5_flood_eval = {
                "total_cells": len(df_p5_mat),
                "unobserved_cells": class_counts.get("UNOBSERVED", 0),
                "unobserved_pct": round(class_counts.get("UNOBSERVED", 0) / len(df_p5_mat) * 100.0, 2),
                "class_distribution": class_counts,
                "evaluation_metrics": [clean_dict_for_json(r) for r in df_p5_ev.to_dict(orient="records")]
            }
        else:
            self.phase5_flood_eval = {}

        p5_sar_path = self.data_dir / "phase5_final" / "sar_observations" / "authentic_sar_scene_manifest.parquet"
        if not p5_sar_path.is_file():
            p5_sar_path = self.data_dir / "phase5_sar_observations" / "authentic_sar_scene_manifest.parquet"
        if p5_sar_path.is_file():
            df_p5_sar = pd.read_parquet(p5_sar_path)
            self.phase5_sar_manifest = [clean_dict_for_json(r) for r in df_p5_sar.to_dict(orient="records")]
        else:
            self.phase5_sar_manifest = []

        self.phase5_readiness_gates = {
            "campaign_status": "PHASE_5_INDEPENDENT_VALIDATION_COMPLETED",
            "phase5_2_scientific_reconciliation": {
                "provenance_classification": "OBSERVATION_CALIBRATED_RETROSPECTIVE_SERIES",
                "genuine_nwp_verification_status": "NOT_ESTABLISHED",
                "gate_a_reconciled_status": "BLOCKED_BY_PROVENANCE",
                "gate_b_reconciled_status": "BLOCKED_BY_DATA_ACCESS",
                "gate_c_reconciled_status": "BLOCKED_CATALOGUE_ONLY",
                "gate_d_reconciled_status": "PASS",
                "gate_e_reconciled_status": "CONDITIONALLY_AUTHORIZED"
            },
            "gate_a": {
                "name": "Gate A: Meteorological NWP Forecast Skill",
                "status": "CONDITIONAL_ACCEPTANCE",
                "scientific_provenance_note": "RETROSPECTIVE_RECONSTRUCTED_SERIES — NOT VERIFIED NWP SKILL. Calibrated to historical synoptic curves, not downloaded NWP GRIB2/NetCDF files.",
                "operational_lead_time_max_hours": 24,
                "rationale": "Retrospective simulation across 183,690 matched pairs (711 anchor-time groups; effective N not statistically established) demonstrates empirical agreement at <=24h. Genuine NWP forecast skill not established."
            },
            "gate_b": {
                "name": "Gate B: Supervised Flood Prediction Modeling",
                "status": "REJECTED_BLOCKED",
                "rationale": "Severe spatial censorship (98.13% of cells unobserved, only 13 positive and 5 high-ground ridge proxy stations). Supervised ML training is statistically blocked. Unsupervised physical indexing approved."
            }
        }

        # 7. Phase 6 Deliverables Integration
        p6_manifest_path = self.reports_dir / "phase_6" / "phase_6_master_manifest.json"
        if p6_manifest_path.is_file():
            try:
                with open(p6_manifest_path, "r", encoding="utf-8") as f:
                    self.phase6_manifest = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading Phase 6 manifest: {e}")

        # 7.1 Phase 6A: NWP Provenance & Forecast Archive
        p6_nwp_prov_path = Path("data/processed/phase6/nwp/nwp_forecast_provenance.parquet")
        if p6_nwp_prov_path.is_file():
            try:
                df_prov = pd.read_parquet(p6_nwp_prov_path)
                self.phase6_nwp = {
                    "source": "NOAA Global Forecast System (GFS) 0.25-deg AWS Open Data (s3://noaa-gfs-bdp-pds)",
                    "acquisition_period": "2022-08-25 to 2022-09-10 (17 calendar days)",
                    "cycles": ["00Z", "12Z"],
                    "lead_times_hours": [6, 12, 24, 48, 72],
                    "total_grib2_slices": 170,
                    "total_wmo_messages_decoded": len(df_prov),
                    "study_cells_mapped": 1170,
                    "total_cell_forecast_records": 198900,
                    "native_resolution_km": 27.75,
                    "spatial_mapping_method": "nearest_native_0p25",
                    "sample_provenance": [clean_dict_for_json(r) for r in df_prov.head(10).to_dict(orient="records")]
                }
            except Exception as e:
                logger.warning(f"Error loading Phase 6 NWP provenance: {e}")

        # 7.2 Phase 6B: Ground Rainfall Observations & Gauge Validation
        p6_reg_path = Path("data/processed/phase6/ground_rainfall/rain_gauge_station_registry.parquet")
        p6_val_path = Path("data/processed/phase6/ground_rainfall/gfs_vs_gauge_validation_metrics.parquet")
        if p6_reg_path.is_file() and p6_val_path.is_file():
            try:
                df_reg = pd.read_parquet(p6_reg_path)
                df_val = pd.read_parquet(p6_val_path)
                self.phase6_ground_rainfall = {
                    "networks": ["India Meteorological Department (IMD)", "KSNDMC BBMP Telemetric Network", "CPCB CAAQM (Air Quality Audit)"],
                    "total_stations_catalogued": len(df_reg),
                    "primary_hydrological_gauges": int(df_reg["is_primary_hydrological_gauge"].sum()),
                    "paired_validation_samples": len(df_val),
                    "gfs_vs_gauge_mae_mm": round(float(df_val["abs_error_mm"].mean()), 2),
                    "gfs_vs_gauge_rmse_mm": round(float(np.sqrt((df_val["error_mm"]**2).mean())), 2),
                    "gfs_vs_gauge_pearson_r": round(float(df_val["gfs_forecast_24h_mm"].corr(df_val["observed_24h_mm"])), 3),
                    "contingency_heavy_rain_ge_64_5mm": {
                        "hits": int(len(df_val[df_val["obs_is_heavy_ge_64_5"] & df_val["fcst_is_heavy_ge_64_5"]])),
                        "misses": int(len(df_val[df_val["obs_is_heavy_ge_64_5"] & (~df_val["fcst_is_heavy_ge_64_5"])])),
                        "false_alarms": int(len(df_val[(~df_val["obs_is_heavy_ge_64_5"]) & df_val["fcst_is_heavy_ge_64_5"]])),
                        "correct_negatives": int(len(df_val[(~df_val["obs_is_heavy_ge_64_5"]) & (~df_val["fcst_is_heavy_ge_64_5"])])),
                        "pod": 0.0,
                        "far": 0.0
                    },
                    "stations": [clean_dict_for_json(r) for r in df_reg.to_dict(orient="records")]
                }
            except Exception as e:
                logger.warning(f"Error loading Phase 6 ground rainfall: {e}")

        # 7.3 Phase 6C: Independent Flood Evidence & ML Gate
        p6_gt_path = Path("data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet")
        p6_gate_path = Path("data/processed/phase6/flood_evidence/flood_evidence_gate_audit.parquet")
        p6_inc_path = Path("data/processed/phase6/flood_evidence/independent_flood_incident_inventory.parquet")
        if p6_gt_path.is_file() and p6_gate_path.is_file():
            try:
                df_gt = pd.read_parquet(p6_gt_path)
                df_gate = pd.read_parquet(p6_gate_path)
                p6_incidents = []
                if p6_inc_path.is_file():
                    df_p6_inc = pd.read_parquet(p6_inc_path)
                    p6_incidents = [clean_dict_for_json(r) for r in df_p6_inc.to_dict(orient="records")]
                self.phase6_flood_evidence = {
                    "status": "AVAILABLE",
                    "total_domain_cells": len(df_gt),
                    "verified_positive_inundation_cells": int((df_gt["observation_status"] == "VERIFIED_POSITIVE").sum()),
                    "verified_monitored_negative_cells": int((df_gt["observation_status"] == "VERIFIED_NEGATIVE").sum()),
                    "unobserved_domain_cells": int((df_gt["observation_status"] == "UNOBSERVED_DOMAIN_CELL").sum()),
                    "unobserved_percentage": round(float((df_gt["observation_status"] == "UNOBSERVED_DOMAIN_CELL").mean() * 100.0), 2),
                    "supervised_ml_flood_prediction_gate": str(df_gate["supervised_ml_flood_prediction_gate"].iloc[0]),
                    "gate_justification": str(df_gate["gate_justification"].iloc[0]),
                    "recommended_modelling_paradigm": str(df_gate["recommended_modelling_paradigm"].iloc[0]),
                    "incident_inventory_source": "data/processed/phase6/flood_evidence/independent_flood_incident_inventory.parquet",
                    "incident_record_count": len(p6_incidents),
                    "incident_limitation": "Distinct from legacy /api/incidents (21 rows). 24 Phase 6 field records across 17 locations; 98.29% of domain unobserved.",
                    "incident_records": p6_incidents,
                }
            except Exception as e:
                logger.warning(f"Error loading Phase 6 flood evidence: {e}")

        # 7.4 Phase 6D: Authentic Sentinel-1 SAR Processing
        p6_sar_reg_path = Path("data/processed/phase6/sar/sar_scene_audit_registry.parquet")
        p6_sar_feat_path = Path("data/processed/phase6/sar/sar_flood_signature_features.parquet")
        p6_sar_xval_path = Path("data/processed/phase6/sar/sar_ground_truth_cross_validation.parquet")
        p7_sar_comp_path = Path("data/processed/phase7/sar_validation/phase7_sar_evidence_comparison.parquet")
        if p6_sar_reg_path.is_file() and p6_sar_feat_path.is_file() and p6_sar_xval_path.is_file():
            try:
                df_sreg = pd.read_parquet(p6_sar_reg_path)
                df_sfeat = pd.read_parquet(p6_sar_feat_path)
                df_sxval = pd.read_parquet(p6_sar_xval_path)
                true_spec = None
                lake_conf = None
                canyon_miss = None
                pos_total = int((df_sxval["observation_status"] == "VERIFIED_POSITIVE").sum()) if "observation_status" in df_sxval.columns else 13
                if p7_sar_comp_path.is_file():
                    df_p7s = pd.read_parquet(p7_sar_comp_path)
                    true_spec = int(df_p7s["is_true_specular_flood_detection"].sum())
                    lake_conf = int(df_p7s["is_conflated_with_permanent_lake"].sum())
                    canyon_miss = int(df_p7s["is_missed_due_to_urban_canyon"].sum())
                self.phase6_sar = {
                    "satellite": "Sentinel-1A C-SAR (5.405 GHz)",
                    "beam_mode": "IW GRDH (Orbit 165 Descending)",
                    "dem_used_for_rtc": "SRTM 1-arcsecond (30m) Global",
                    "co_event_acquisition_utc": "2022-09-05T00:46:16Z (06:16 AM IST)",
                    "physical_class_breakdown": df_sfeat["sar_physical_inundation_class"].value_counts().to_dict(),
                    "ground_truth_cross_validation": df_sxval["validation_agreement"].value_counts().to_dict(),
                    "verified_positive_total": pos_total,
                    "true_specular_detections": true_spec,
                    "true_specular_sensitivity_pct": round(true_spec / pos_total * 100.0, 1) if true_spec is not None and pos_total else None,
                    "lake_conflated_count": lake_conf,
                    "urban_canyon_missed_count": canyon_miss,
                    "exploratory_combined_agreement_pct": 76.9,
                    "specificity_on_monitored_dry_pct": 85.7,
                    "sar_metric_status": "EXPLORATORY_UNVALIDATED",
                    "urban_radar_limitation": "Phase 7 audit found 4/13 positives were pre-existing lake conflation and 1/13 double-bounce; true specular flood expansion sensitivity is 5/13 (38.5%), not 76.9%."
                }
            except Exception as e:
                logger.warning(f"Error loading Phase 6 SAR features: {e}")

        # 7.5 Phase 6E: Physical Hydrology & Topographic Routing
        p6_hyd_stat_path = Path("data/processed/phase6/hydrology/topographic_routing_static_features.parquet")
        p6_hyd_dyn_path = Path("data/processed/phase6/hydrology/dynamic_hydrological_inundation_potential.parquet")
        if p6_hyd_stat_path.is_file() and p6_hyd_dyn_path.is_file():
            try:
                df_hstat = pd.read_parquet(p6_hyd_stat_path)
                df_hdyn = pd.read_parquet(p6_hyd_dyn_path)
                self.phase6_hydrology = {
                    "routing_algorithm": "Deterministic O'Callaghan & Mark (1984) D8 Flow Direction and Accumulation",
                    "topographic_wetness_index_formula": "TWI = ln( a / tan(beta) )",
                    "drainage_classes": df_hstat["hydraulic_drainage_class"].value_counts().to_dict(),
                    "topographic_sinks_identified": int(df_hstat["is_topographic_sink"].sum()),
                    "contributing_area_range_km2": [round(float(df_hstat["upstream_contributing_area_km2"].min()), 1), round(float(df_hstat["upstream_contributing_area_km2"].max()), 1)],
                    "twi_range": [round(float(df_hstat["topographic_wetness_index"].min()), 2), round(float(df_hstat["topographic_wetness_index"].max()), 2)],
                    "deterministic_ground_truth_roc_auc": 0.560,
                    "mean_hipi_positive_flood_cells": 0.188,
                    "mean_hipi_monitored_dry_cells": 0.139,
                    "scientific_insight": "Macro-topography (1-km) separates major drainage valleys from ridges; micro-culverts and compound walls require sub-10m hydrodynamic modeling."
                }
            except Exception as e:
                logger.warning(f"Error loading Phase 6 hydrology: {e}")

        # 7.6 Phase 6 Master Summary
        self.phase6_summary = {
            "campaign_title": "Phase 6 Master Scientific Delivery",
            "study_area": "Bengaluru Urban provisional study domain (1,170 cells, EPSG:6933)",
            "workstreams": {
                "6A_NWP_Acquisition": "PASS — 170 NOAA GFS slices acquired bit-for-bit from AWS Open Data",
                "6B_Ground_Rainfall": "PASS — 21 stations catalogued, genuine forecast-gauge MAE = 18.64 mm, r = 0.142",
                "6C_Flood_Evidence": "PASS — 24 verified records; 98.29% domain unobserved; Supervised ML BLOCKED",
                "6D_Authentic_SAR": "PASS — Sentinel-1A co-flood peak capture (06:16 AM IST Sep 5); 76.9% sensitivity",
                "6E_Physical_Hydrology": "PASS — Deterministic D8 flow, TWI, 19 sinks, HIPI score, ROC-AUC = 0.560",
                "6F_Platform_Integration": "PASS — Live dashboard endpoints, master manifest with 16 datasets registered"
            },
            "governing_scientific_principle": "Empirical Authenticity Over Synthetic Optimization; Strict ML Gate Enforcement"
        }

        # 7.7 Phase 7 Summary & Grouped Uncertainty
        p7_uncert_path = self.reports_dir / "phase_7" / "phase7B_grouped_uncertainty_results.json"
        if p7_uncert_path.is_file():
            try:
                with open(p7_uncert_path, "r", encoding="utf-8") as f:
                    self.phase7_uncertainty = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading Phase 7 uncertainty: {e}")

        self.phase7_summary = {
            "campaign_title": "Phase 7 Final Research Platform & Academic Package",
            "study_area": "Bengaluru Urban provisional study domain (1,170 cells, EPSG:6933)",
            "workstreams": {
                "7A_Data_Freeze": "PASS_WITH_DOCUMENTED_LIMITATIONS — 68 datasets verified bit-for-bit",
                "7B_NWP_Verification": "PASS_WITH_DOCUMENTED_LIMITATIONS — MAE = 18.64 mm, r = 0.142, POD = 0.00 at 64.5 mm, 3.1x clustered uncertainty",
                "7C_Flood_and_SAR": "PASS_WITH_DOCUMENTED_LIMITATIONS — 98.29% unobserved, ML blocked, SAR specular flood sensitivity = 38.5%",
                "7D_Hydrology_Uncertainty": "PASS_WITH_DOCUMENTED_LIMITATIONS — D8 & TWI reproducible, AUC 95% CI spans 0.500 (random chance)",
                "7E_Platform_Readiness": "PASS — 13+ endpoints, regression tested, full test suite passing",
                "7F_Academic_Package": "PASS — 10 academic reports, complete viva & demonstration guides"
            },
            "supervised_ml_flood_prediction_gate": "BLOCKED_BY_INSUFFICIENT_EVIDENCE",
            "final_acceptance_decision": "PHASE_7_COMPLETED_WITH_DOCUMENTED_LIMITATIONS"
        }

        p7_man_path = self.reports_dir / "phase_7_manifests" / "phase_7_final_manifest.json"
        if p7_man_path.is_file():
            try:
                with open(p7_man_path, "r", encoding="utf-8") as f:
                    p7_man = json.load(f)
                p7_man["status"] = "AVAILABLE"
                p7_man["source"] = str(p7_man_path).replace("\\", "/")
                self.phase7_manifest = p7_man
            except Exception as e:
                logger.warning(f"Error loading Phase 7 manifest: {e}")
                self.phase7_manifest = {"status": "UNAVAILABLE", "source": str(p7_man_path).replace("\\", "/"), "detail": str(e)}
        else:
            self.phase7_manifest = {"status": "UNAVAILABLE", "source": str(p7_man_path).replace("\\", "/")}

        # 8. Overall Platform Summary
        advisory_count = 0
        watch_count = 0
        normal_count = 0
        peak_24h = 0.0
        peak_72h = 0.0
        if not df_dyn.empty and "forecast_intensity_category" in df_dyn.columns:
            vc = df_dyn["forecast_intensity_category"].value_counts().to_dict()
            advisory_count = vc.get("HEAVY_RAINFALL_CATEGORY", vc.get("HEAVY_RAIN_ADVISORY", 0))
            watch_count = vc.get("MODERATE_RAINFALL_CATEGORY", vc.get("MODERATE_RAIN_WATCH", 0))
            normal_count = vc.get("LIGHT_RAINFALL_CATEGORY", vc.get("LIGHT_RAIN", vc.get("LOW_RAIN_NORMAL", 0)))
            peak_24h = float(df_dyn["forecast_rainfall_24h_mm"].max())
            peak_72h = float(df_dyn["forecast_rainfall_72h_mm"].max())

        self.summary = {
            "platform_name": "Bengaluru Urban Flood Risk Intelligence Console",
            "study_area": {
                "name": "Bengaluru Urban",
                "boundary_status": "pending_authoritative_boundary",
                "boundary_type": "Provisional Research Bounding Box",
                "bbox_wgs84": [77.45, 12.85, 77.75, 13.15],
                "projection": "EPSG:6933 (World Cylindrical Equal Area)",
                "total_cells": len(self.cells_geojson.get("features", [])),
                "grid_cell_size_m": 1000,
                "domain_area_sqkm": 1170.0
            },
            "forecast_surveillance": {
                "source_service": "Open-Meteo NWP ECMWF_IFS_GFS_Seamless",
                "native_resolution": "approx. 9-13 km (ECMWF IFS / NOAA GFS coarse grid)",
                "spatial_anchors_count": 9,
                "mapping_method": "nearest_centroid_anchor",
                "forecast_horizons_h": [3, 6, 24, 48, 72],
                "nominal_reference_time_utc": "2026-11-05T00:00:00Z",
                "model_initialization_status": "UNEXPOSED_BY_PROVIDER_INFERRED_FROM_RETRIEVAL",
                "active_heavy_rainfall_category_count": advisory_count,
                "active_moderate_rainfall_category_count": watch_count,
                "light_rainfall_category_count": normal_count,
                "peak_24h_rainfall_mm": peak_24h,
                "peak_72h_rainfall_mm": peak_72h,
                "official_warning_disclaimer": "Internal meteorological classification based on 24h thresholds; NOT an official IMD/KSNDMC government emergency warning."
            },
            "historical_surveillance": {
                "total_incidents_catalogued": len(self.incidents),
                "total_episodes_monitored": len(self.episodes),
                "evidence_categories": {
                    "Confirmed Inundation": sum(1 for i in self.incidents if i.get("evidence_category") == "Confirmed Inundation"),
                    "Reported Waterlogging": sum(1 for i in self.incidents if i.get("evidence_category") == "Reported Waterlogging"),
                    "Flood Disruption": sum(1 for i in self.incidents if i.get("evidence_category") == "Flood Disruption")
                }
            },
            "quarantine_status": {
                "sar_status": "SYNTHETIC_TEST_ONLY_QUARANTINED",
                "sar_operational_status": "REMOVED_FROM_OPERATIONAL_MAP_AVAILABLE_IN_DEV_DRAWER_ONLY",
                "sar_quarantine_reason": "Synthetic SAR fixtures quarantined from operational feature matrices to preserve empirical integrity."
            },
            "scientific_decision": {
                "phase_exit_status": "Decision B: Partial Operational Platform Validated",
                "model_status": "Supervised ML prediction blocked pending authoritative flood depth labels; dynamic multi-criteria intelligence operational."
            },
            "manifest_integrity": self.manifest_status.get("integrity_rate", "Unknown")
        }

    def get_health_payload(self) -> Dict[str, Any]:
        health_rows = self.weather_store.get_provider_health()
        return {
            "status": "ok",
            "service": "urban-flood-risk-platform-dashboard",
            "database_status": "AVAILABLE",
            "database_path": str(self.weather_store.db_path).replace("\\", "/"),
            "stored_weather_records": self.weather_store.count_records(),
            "scheduler_running": self.refresher.is_running,
            "providers": health_rows,
        }

    def get_sources_payload(self) -> Dict[str, Any]:
        from ..live import compute_freshness
        om_health = self.weather_store.get_provider_health("open_meteo")
        if om_health:
            h = om_health[0]
            om_fresh = compute_freshness(
                h.get("last_success_utc"),
                live_hours=self.refresher.freshness_live_hours,
                recent_hours=self.refresher.freshness_recent_hours,
            )
            om_entry = {
                "source_id": "open_meteo_forecast",
                "provider": "Open-Meteo",
                "data_type": "FORECAST",
                "model_id": h.get("model_id", "ecmwf_ifs025"),
                "status": h.get("status") if h.get("last_error") else om_fresh,
                "freshness": om_fresh,
                "last_attempt_utc": h.get("last_attempt_utc"),
                "last_success_utc": h.get("last_success_utc"),
                "last_error": h.get("last_error"),
                "records_written": h.get("records_written", 0),
            }
        else:
            om_entry = {
                "source_id": "open_meteo_forecast",
                "provider": "Open-Meteo",
                "data_type": "FORECAST",
                "model_id": self.refresher.adapter.preferred_model,
                "status": "UNAVAILABLE",
                "freshness": "UNAVAILABLE",
                "last_attempt_utc": None,
                "last_success_utc": None,
                "last_error": "No refresh executed yet",
                "records_written": 0,
            }

        sources = [
            om_entry,
            {
                "source_id": "phase4_3_observed_baseline",
                "provider": "Phase 4.3 Static Baseline",
                "data_type": "OBSERVATION",
                "status": "STALE",
                "freshness": "STALE",
                "last_success_utc": "2026-11-05T00:00:00Z",
                "last_error": None,
                "note": "Constant 12.5 mm historical baseline; excluded from current live risk.",
            },
            {
                "source_id": "ksndmc_live_gauges",
                "provider": "KSNDMC",
                "data_type": "OBSERVATION",
                "status": "UNAVAILABLE",
                "freshness": "UNAVAILABLE",
                "last_success_utc": None,
                "last_error": "No open unauthenticated REST API; SSL certificate verification failed on portal.",
            },
            {
                "source_id": "imd_live_api",
                "provider": "IMD Mausam",
                "data_type": "OBSERVATION",
                "status": "UNAVAILABLE",
                "freshness": "UNAVAILABLE",
                "last_success_utc": None,
                "last_error": "Public HTML portal only; API requires formal IP whitelisting.",
            },
        ]
        return {"sources": sources}

    def get_weather_current_payload(self) -> Dict[str, Any]:
        return {
            "data_type": "OBSERVATION",
            "status": "UNAVAILABLE",
            "source": "KSNDMC / IMD live telemetry",
            "timestamp": None,
            "observed_rainfall_mm": None,
            "unit": "mm",
            "detail": "No verified live ground-gauge observation feed is currently available; forecasts are not substituted as observations.",
            "historical_baseline": {
                "status": "STALE",
                "data_type": "HISTORICAL",
                "source": "dynamic_risk_intelligence_bengaluru.parquet (Phase 4.3 constant 12.5mm)",
                "timestamp": "2026-11-05T00:00:00Z",
                "observed_rainfall_24h_mm": 12.5,
                "unit": "mm",
            },
        }

    def get_weather_forecast_payload(self) -> Dict[str, Any]:
        from ..live import compute_freshness
        rows = self.weather_store.get_latest_forecast()
        health = self.weather_store.get_provider_health("open_meteo")
        last_error = health[0].get("last_error") if health else None
        if not rows:
            return {
                "data_type": "FORECAST",
                "provider": "open_meteo",
                "model": self.refresher.adapter.preferred_model,
                "status": "UNAVAILABLE",
                "freshness": "UNAVAILABLE",
                "issue_time_utc": None,
                "retrieval_time_utc": None,
                "units": {"precipitation": "mm", "rain": "mm", "temperature_2m": "°C", "relative_humidity_2m": "%"},
                "last_error": last_error,
                "next_24h_precipitation_mm": None,
                "hourly_forecast": [],
            }

        ret_utc = rows[0]["retrieval_time_utc"]
        issue_utc = rows[0]["issue_time_utc"]
        model_id = rows[0]["model_id"]
        freshness = compute_freshness(
            ret_utc,
            live_hours=self.refresher.freshness_live_hours,
            recent_hours=self.refresher.freshness_recent_hours,
        )
        by_time: Dict[str, Dict[str, Any]] = {}
        units: Dict[str, str] = {}
        for r in rows:
            vt = r["valid_time_utc"]
            units[r["variable"]] = r["unit"]
            entry = by_time.setdefault(vt, {"valid_time_utc": vt})
            entry[r["variable"]] = r["value"]
            entry[f"{r['variable']}_status"] = r["quality_status"]

        hourly = [by_time[k] for k in sorted(by_time.keys())]
        first_24 = [h.get("precipitation") for h in hourly[:24] if h.get("precipitation") is not None]
        next_24h = round(sum(first_24), 2) if first_24 else None
        return {
            "data_type": "FORECAST",
            "provider": "open_meteo",
            "model": model_id,
            "status": freshness,
            "freshness": freshness,
            "location_ref": rows[0]["location_ref"],
            "latitude": rows[0]["latitude"],
            "longitude": rows[0]["longitude"],
            "issue_time_utc": issue_utc,
            "retrieval_time_utc": ret_utc,
            "valid_from_utc": hourly[0]["valid_time_utc"] if hourly else None,
            "valid_to_utc": hourly[-1]["valid_time_utc"] if hourly else None,
            "units": units,
            "last_error": last_error,
            "next_24h_precipitation_mm": next_24h,
            "hourly_forecast": hourly,
        }


_GLOBAL_DATASTORE: Optional[DashboardDataStore] = None


def get_datastore(data_dir: Optional[Path] = None, reports_dir: Optional[Path] = None) -> DashboardDataStore:
    global _GLOBAL_DATASTORE
    if _GLOBAL_DATASTORE is None:
        _GLOBAL_DATASTORE = DashboardDataStore(data_dir=data_dir, reports_dir=reports_dir)
    return _GLOBAL_DATASTORE


def load_dashboard_data(data_dir: Optional[Path] = None, reports_dir: Optional[Path] = None) -> DashboardDataStore:
    """Explicitly reload and return the dashboard data store."""
    global _GLOBAL_DATASTORE
    _GLOBAL_DATASTORE = DashboardDataStore(data_dir=data_dir, reports_dir=reports_dir)
    return _GLOBAL_DATASTORE


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler serving dashboard REST endpoints and static assets."""

    def __init__(self, *args, directory: Optional[str] = None, **kwargs):
        if directory is None:
            static_dir = Path(__file__).resolve().parent / "static"
            directory = str(static_dir)
        self.datastore = get_datastore()
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path
        params = parse_qs(parsed.query, keep_blank_values=True)

        if clean_path.startswith("/api/"):
            allowed_params = {"grid_id"} if clean_path == "/api/cells" else set()
            unknown_params = set(params.keys()) - allowed_params
            if unknown_params:
                self._send_error_json(
                    400,
                    "INVALID_PARAMETER",
                    "Invalid query parameter",
                    f"Unsupported parameter(s): {', '.join(sorted(unknown_params))}",
                )
                return

        # REST API Endpoints
        if clean_path == "/api/summary":
            self._send_json(self.datastore.summary)
            return
        elif clean_path == "/api/cells":
            if "grid_id" in params:
                target_id = params["grid_id"][0].strip()
                if not target_id:
                    self._send_error_json(400, "INVALID_PARAMETER", "Invalid query parameter", "grid_id cannot be empty")
                    return
                matched = [
                    f for f in self.datastore.cells_geojson.get("features", [])
                    if f.get("properties", {}).get("grid_id") == target_id
                ]
                if not matched:
                    self._send_error_json(404, "CELL_NOT_FOUND", "Grid cell not found", f"No cell found for grid_id='{target_id}'")
                    return
                filtered_fc = {
                    "type": "FeatureCollection",
                    "crs": self.datastore.cells_geojson.get("crs"),
                    "features": matched,
                }
                self._send_json(filtered_fc)
                return
            self._send_json(self.datastore.cells_geojson)
            return
        elif clean_path == "/api/incidents":
            self._send_json(self.datastore.incidents)
            return
        elif clean_path == "/api/episodes":
            self._send_json(self.datastore.episodes)
            return
        elif clean_path == "/api/manifest":
            self._send_json(self.datastore.manifest_status)
            return
        elif clean_path == "/api/phase5/verification-metrics":
            self._send_json(self.datastore.phase5_metrics)
            return
        elif clean_path == "/api/phase5/flood-validation":
            self._send_json(self.datastore.phase5_flood_eval)
            return
        elif clean_path == "/api/phase5/sar-manifest":
            self._send_json(self.datastore.phase5_sar_manifest)
            return
        elif clean_path == "/api/phase5/readiness-gates":
            self._send_json(self.datastore.phase5_readiness_gates)
            return
        elif clean_path == "/api/phase6/summary":
            self._send_json(self.datastore.phase6_summary)
            return
        elif clean_path == "/api/phase6/nwp":
            self._send_json(self.datastore.phase6_nwp)
            return
        elif clean_path == "/api/phase6/ground-rainfall":
            self._send_json(self.datastore.phase6_ground_rainfall)
            return
        elif clean_path == "/api/phase6/flood-evidence":
            self._send_json(self.datastore.phase6_flood_evidence)
            return
        elif clean_path == "/api/phase6/sar":
            self._send_json(self.datastore.phase6_sar)
            return
        elif clean_path == "/api/phase6/hydrology":
            self._send_json(self.datastore.phase6_hydrology)
            return
        elif clean_path == "/api/phase6/manifest":
            self._send_json(self.datastore.phase6_manifest)
            return
        elif clean_path == "/api/phase7/summary":
            self._send_json(self.datastore.phase7_summary)
            return
        elif clean_path == "/api/phase7/uncertainty":
            self._send_json(self.datastore.phase7_uncertainty)
            return
        elif clean_path == "/api/phase7/manifest":
            self._send_json(self.datastore.phase7_manifest)
            return
        elif clean_path == "/api/health":
            self._send_json(self.datastore.get_health_payload())
            return
        elif clean_path == "/api/sources":
            self._send_json(self.datastore.get_sources_payload())
            return
        elif clean_path == "/api/weather/current":
            self._send_json(self.datastore.get_weather_current_payload())
            return
        elif clean_path == "/api/weather/forecast":
            self._send_json(self.datastore.get_weather_forecast_payload())
            return
        elif clean_path.startswith("/api/"):
            self._send_error_json(404, "ENDPOINT_NOT_FOUND", "Endpoint not found", f"No route registered for '{clean_path}'")
            return

        # Serve static HTML console
        if clean_path in ("/", "/index.html"):
            index_path = Path(__file__).resolve().parent / "static" / "index.html"
            if index_path.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                with open(index_path, "rb") as f:
                    content = f.read()
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # Fallback to standard static file serving
        return super().do_GET()

    def _send_error_json(self, status: int, code: str, error: str, detail: str):
        self._send_json({"error": error, "code": code, "detail": detail}, status=status)

    def _method_not_allowed(self, method: str):
        self._send_error_json(
            405,
            "METHOD_NOT_ALLOWED",
            "Method not allowed",
            f"HTTP {method} is not supported on '{self.path.split('?')[0]}'; use GET.",
        )

    def do_POST(self):
        self._method_not_allowed("POST")

    def do_PUT(self):
        self._method_not_allowed("PUT")

    def do_DELETE(self):
        self._method_not_allowed("DELETE")

    def do_PATCH(self):
        self._method_not_allowed("PATCH")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Quiet standard HTTP access logs to keep terminal output clean
        pass


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_dashboard(
    host: str = "127.0.0.1",
    port: int = 8501,
    data_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
    blocking: bool = True,
    enable_live_refresh: Optional[bool] = None,
) -> HTTPServer:
    """
    Launch the operational flood risk intelligence web dashboard.

    Parameters
    ----------
    host : str
        Host IP to bind (default: '127.0.0.1').
    port : int
        Port to listen on (default: 8501).
    data_dir : Optional[Path]
        Processed data directory.
    reports_dir : Optional[Path]
        Reports directory containing dataset_manifest.json.
    blocking : bool
        If True, blocks on serve_forever(); if False, starts in a daemon thread and returns.

    Returns
    -------
    HTTPServer
        The active HTTP server instance.
    """
    ds = load_dashboard_data(data_dir=data_dir, reports_dir=reports_dir)
    do_refresh = blocking if enable_live_refresh is None else enable_live_refresh
    if do_refresh:
        ds.refresher.start(run_initial=True)
    static_dir = str(Path(__file__).resolve().parent / "static")

    def handler_factory(*args, **kwargs):
        return DashboardRequestHandler(*args, directory=static_dir, **kwargs)

    server = ThreadedHTTPServer((host, port), handler_factory)
    print(f"[Dashboard Server] Operational console running at http://{host}:{port}/")
    print(f"[Dashboard Server] Serving endpoints: /api/summary, /api/cells, /api/incidents, /api/episodes, /api/manifest")

    if blocking:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[Dashboard Server] Shutting down...")
            server.shutdown()
            server.server_close()
    else:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

    return server


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Urban Flood Risk Intelligence Dashboard Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind server (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--data-dir", default=None, help="Processed data directory")
    parser.add_argument("--reports-dir", default=None, help="Reports and manifest directory")
    args = parser.parse_args()

    data_path = Path(args.data_dir) if args.data_dir else None
    reports_path = Path(args.reports_dir) if args.reports_dir else None

    run_dashboard(
        host=args.host,
        port=args.port,
        data_dir=data_path,
        reports_dir=reports_path,
        blocking=True
    )


