"""Integrated multi-event grid dataset builder and 15-point evidence-quality audit."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import geopandas as gpd
import pandas as pd

from .sar_refinement import classify_sar_cell_state


def build_integrated_event_grid_dataset(
    df_catalog: pd.DataFrame,
    df_ep_rain: pd.DataFrame,
    df_scenes: pd.DataFrame,
    audit_meta: Dict[str, Any],
    grid_path: Path | str = Path("data/processed/grid_bengaluru_urban_1000m.gpkg"),
    hydro_path: Path | str = Path("data/processed/phase6/hydrology/topographic_routing_static_features.parquet"),
    p7_hydro_path: Path | str = Path("data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet"),
    dyn_path: Path | str = Path("data/processed/dynamic_risk_intelligence_bengaluru.parquet"),
    p6_gt_path: Path | str = Path("data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet"),
    p7_sar_path: Path | str = Path("data/processed/phase7/sar_validation/phase7_sar_evidence_comparison.parquet"),
    out_dir: Path | str = Path("data/phase8"),
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Build `flood_event_grid_dataset.parquet` strictly preserving unobserved & proxy states."""
    out_p = Path(out_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    gdf_grid = gpd.read_file(grid_path)
    df_hydro = pd.read_parquet(hydro_path)
    df_p7h = pd.read_parquet(p7_hydro_path)
    df_dyn = pd.read_parquet(dyn_path)
    df_gt = pd.read_parquet(p6_gt_path)
    df_p7s = pd.read_parquet(p7_sar_path)

    # Static terrain & landcover lookup keyed by grid_id
    static_df = gdf_grid[["grid_id", "col_idx", "row_idx", "centroid_lon", "centroid_lat"]].merge(
        df_hydro[["grid_id", "elevation_m", "slope_deg", "upstream_contributing_area_km2", "topographic_wetness_index", "hydraulic_drainage_class"]],
        on="grid_id", how="left",
    ).merge(
        df_p7h[["grid_id", "depression_depth_m", "is_closed_sink"]],
        on="grid_id", how="left",
    ).merge(
        df_dyn[["grid_id", "built_up_fraction", "tree_cover_fraction", "cropland_fraction", "water_fraction"]],
        on="grid_id", how="left",
    )

    rain_lookup = df_ep_rain.set_index("event_id").to_dict(orient="index")
    sar_lookup = df_p7s.set_index("grid_id").to_dict(orient="index")
    gt_lookup = df_gt.set_index("grid_id").to_dict(orient="index")

    dry_controls = set(audit_meta.get("monitored_dry_control_grid_ids", []))
    scene_counts_by_ev = df_scenes[~df_scenes["scene_id"].str.startswith("QUERY_ERROR_")].groupby("event_id").size().to_dict() if not df_scenes.empty else {}

    records: List[Dict[str, Any]] = []
    for _, ep in df_catalog.iterrows():
        ev_id = str(ep["event_id"])
        ev_status = str(ep["verification_status"])
        linked_raw = str(ep.get("linked_grid_ids") or "").strip()
        pos_gids = {g.strip() for g in linked_raw.split(",") if g.strip()}
        rain_info = rain_lookup.get(ev_id, {})
        has_sar_scenes = scene_counts_by_ev.get(ev_id, 0) > 0

        for _, cell in static_df.iterrows():
            gid = str(cell["grid_id"])
            # Determine transparent evidence label & status
            if gid in pos_gids:
                if ev_status == "CONFIRMED":
                    flood_label = 1
                    ev_state = "CONFIRMED_FLOOD"
                elif ev_status == "CORROBORATED":
                    flood_label = 1
                    ev_state = "CORROBORATED_FLOOD"
                else:
                    flood_label = None
                    ev_state = "REPORTED_FLOOD"
                lbl_src = str(ep["evidence_source"])
                lbl_conf = str(ep["confidence"])
                match_method = "EXACT_POINT_IN_CELL_EPSG6933"
            elif ev_id == "EP_2022_09_05" and gid in dry_controls:
                # 7 monitored dry control sites verified during Sep 5, 2022
                flood_label = 0
                ev_state = "PROXY_NEGATIVE"
                lbl_src = "KSNDMC/IMD/BBMP_MONITORED_CONTROL_STATIONS"
                lbl_conf = "HIGH"
                match_method = "MONITORED_STATION_POINT_IN_CELL"
            elif ev_id in ("EP_2022_08_30", "EP_2022_09_05") and gid in gt_lookup and gt_lookup[gid]["observation_status"] == "VERIFIED_NEGATIVE":
                flood_label = 0
                ev_state = "PROXY_NEGATIVE"
                lbl_src = "PHASE6_GROUND_TRUTH_MATRIX"
                lbl_conf = "HIGH"
                match_method = "MONITORED_STATION_POINT_IN_CELL"
            else:
                # Never convert unknown or unobserved cells into negative labels!
                flood_label = None
                ev_state = "UNKNOWN" if not pos_gids else "UNOBSERVED"
                lbl_src = "NONE"
                lbl_conf = "UNOBSERVED"
                match_method = "LOCALITY_UNMAPPED_HIGH_UNCERTAINTY" if not pos_gids else "UNOBSERVED_DOMAIN_CELL"

            # SAR evidence (only 2022-09-05 has processed pixel-level SAR delta in repo right now)
            if ev_id == "EP_2022_09_05" and gid in sar_lookup:
                s_info = sar_lookup[gid]
                sar_delta = float(s_info["sar_delta_vv_db"])
                sar_state = classify_sar_cell_state(
                    sar_delta_vv_db=sar_delta,
                    water_fraction=float(cell["water_fraction"]),
                    built_up_fraction=float(cell["built_up_fraction"]),
                    tree_cover_fraction=float(cell["tree_cover_fraction"]),
                    is_permanent_water_conflated=bool(s_info["is_conflated_with_permanent_lake"]),
                )
            else:
                sar_delta = None
                sar_state = "NO_VALID_OBSERVATION" if not has_sar_scenes else "UNPROCESSED_CDSE_CATALOG_ONLY"

            records.append({
                "event_id": ev_id,
                "grid_id": gid,
                "event_timestamp_utc": str(ep["event_start_utc"]),
                "predictor_observation_timestamp_utc": str(ep["event_start_utc"]),
                "spatial_matching_method": match_method,
                # Terrain & landcover
                "elevation_m": float(cell["elevation_m"]),
                "slope_deg": float(cell["slope_deg"]),
                "upstream_contributing_area_km2": float(cell["upstream_contributing_area_km2"]),
                "topographic_wetness_index": float(cell["topographic_wetness_index"]),
                "depression_depth_m": float(cell["depression_depth_m"]),
                "is_closed_sink": int(cell["is_closed_sink"]),
                "built_up_fraction": float(cell["built_up_fraction"]),
                "tree_cover_fraction": float(cell["tree_cover_fraction"]),
                "cropland_fraction": float(cell["cropland_fraction"]),
                "water_fraction": float(cell["water_fraction"]),
                # Strictly pre-event ERA5-Land rainfall features
                "era5_rain_24h_pre_mm": rain_info.get("era5_rain_24h_pre_mm"),
                "era5_rain_72h_pre_mm": rain_info.get("era5_rain_72h_pre_mm"),
                "era5_rain_7d_pre_mm": rain_info.get("era5_rain_7d_pre_mm"),
                "era5_rain_14d_pre_mm": rain_info.get("era5_rain_14d_pre_mm"),
                "era5_api_7d_pre_mm": rain_info.get("era5_api_7d_pre_mm"),
                "rainfall_classification": rain_info.get("rainfall_classification", "UNAVAILABLE"),
                # SAR evidence
                "sar_delta_vv_db": sar_delta,
                "sar_evidence_state": sar_state,
                # Target & provenance
                "flood_label": flood_label,
                "evidence_status": ev_state,
                "label_source": lbl_src,
                "label_confidence": lbl_conf,
                "missing_data_flags": "SAR_UNPROCESSED" if sar_delta is None else "NONE",
            })

    df_out = pd.DataFrame(records)
    df_out.to_parquet(out_p / "flood_event_grid_dataset.parquet", index=False)

    # 15-point Evidence Quality & Independence Audit
    ev_counts = df_out["evidence_status"].value_counts().to_dict()
    pos_events = df_out[df_out["flood_label"] == 1]["event_id"].nunique()
    neg_events = df_out[df_out["flood_label"] == 0]["event_id"].nunique()
    years = sorted(df_catalog["event_start_utc"].str[:4].unique().tolist())

    quality_audit = {
        "1_independent_events_identified": int(len(df_catalog)),
        "2_confirmed_events": int((df_catalog["verification_status"] == "CONFIRMED").sum()),
        "3_corroborated_events": int((df_catalog["verification_status"] == "CORROBORATED").sum()),
        "4_reported_unverified_events": int((df_catalog["verification_status"] == "REPORTED").sum()),
        "5_distinct_affected_grid_cells_positive": int(df_out[df_out["flood_label"] == 1]["grid_id"].nunique()),
        "6_confirmed_or_corroborated_flood_positive_records": int((df_out["flood_label"] == 1).sum()),
        "7_verified_negative_records": int(ev_counts.get("VERIFIED_NON_FLOOD", 0)),
        "8_proxy_negative_records": int(ev_counts.get("PROXY_NEGATIVE", 0)),
        "9_unknown_or_unobserved_records": int(ev_counts.get("UNOBSERVED", 0) + ev_counts.get("UNKNOWN", 0)),
        "10_temporal_coverage_years": years,
        "11_spatial_domain_cells_per_event": 1170,
        "12_satellite_scenes_catalogued": int(len(df_scenes[~df_scenes["scene_id"].str.startswith("QUERY_ERROR_")])) if not df_scenes.empty else 0,
        "13_historical_rainfall_episodes_covered": int(df_ep_rain["era5_rain_24h_pre_mm"].notna().sum()) if not df_ep_rain.empty else 0,
        "14_sar_missing_rate_pct": round(float(df_out["sar_delta_vv_db"].isna().mean() * 100.0), 2),
        "15_duplicate_p2_p6_grid_ids_merged": int(audit_meta.get("overlapping_grid_id_count", 0)),
        "ml_validation_readiness": {
            "events_with_positive_labels": int(pos_events),
            "events_with_negative_labels": int(neg_events),
            "loeo_feasible": bool(pos_events >= 5 and neg_events >= 3),
            "assessment": (
                f"Expanded from 1 to {pos_events} flood-positive episodes, but only {neg_events} episode(s) have "
                "verified/proxy non-flood control cells. Multi-event non-flood control expansion across 2020-2025 "
                "is required before robust LOEO supervised training."
            ),
        },
    }
    with open(out_p / "evidence_quality_audit.json", "w", encoding="utf-8") as f:
        json.dump(quality_audit, f, indent=2)

    return df_out, quality_audit
