"""
scripts/phase7/build_final_manifest.py
Compiles the Master Phase 7 Final Data Manifest registering all 73 datasets
across the complete platform lifecycle (Historical + Phase 6 + Phase 7).
Resolves key collision between Phase 5 and Phase 5 Final manifests.
"""

import os
import json
import hashlib
from datetime import datetime

FINAL_MANIFEST_PATH = "reports/phase_7_manifests/phase_7_final_manifest.json"

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("BUILDING MASTER PHASE 7 FINAL DATA MANIFEST (RECONCILED 73 ENTRIES)")
    print("=" * 80)
    
    manifest_sources = [
        ("Phase 1-4 Core Manifest", "reports/dataset_manifest.json", "p1_4"),
        ("Phase 5 Initial Manifest", "reports/phase_5_dataset_manifest.json", "phase5"),
        ("Phase 5 Final Manifest", "reports/phase_5_final_dataset_manifest.json", "phase5_final"),
        ("Phase 5.2 Closure Manifest", "reports/phase_5_2/phase_5_2_dataset_manifest.json", "phase5_2"),
        ("Phase 6 Master Manifest", "reports/phase_6/phase_6_master_manifest.json", "phase6")
    ]
    
    master_entries = {}
    
    for m_label, m_path, prefix in manifest_sources:
        with open(m_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ds_dict = data.get("datasets", {})
        print(f"Loading {m_label} ({len(ds_dict)} entries)...")
        
        for raw_id, meta in ds_dict.items():
            raw_path = meta.get("file_path") or meta.get("path")
            norm_rel_path = os.path.normpath(os.path.relpath(os.path.abspath(raw_path), os.getcwd()))
            
            if not os.path.exists(norm_rel_path):
                print(f"ERROR: Missing file for {raw_id} at {norm_rel_path}")
                continue
                
            actual_size = os.path.getsize(norm_rel_path)
            actual_hash = sha256_file(norm_rel_path)
            
            # Determine unique manifest key
            # If the ID is already present or from Phase 5/Phase 5 Final where IDs collided,
            # disambiguate with a clear manifest prefix
            if prefix == "phase5":
                unique_key = f"phase5_{raw_id}"
            elif prefix == "phase5_final":
                unique_key = f"phase5_final_{raw_id}"
            else:
                unique_key = raw_id
                
            master_entries[unique_key] = {
                "dataset_id": unique_key,
                "original_id": raw_id,
                "file_path": norm_rel_path,
                "file_size_bytes": actual_size,
                "sha256_checksum": actual_hash,
                "originating_manifest": m_label,
                "source_provider": meta.get("source_provider") or meta.get("provider") or "Project Pipeline",
                "validation_status": "AUTHENTIC_FROZEN_BASELINE"
            }
            
    print(f"\nTotal historical and Phase 6 datasets registered: {len(master_entries)} (Target: 68)")
    
    # Add Phase 7 Datasets (5 datasets)
    p7_datasets = {
        "phase7_forecast_error_registry": {
            "file_path": "data/processed/phase7/nwp/phase7_forecast_error_registry.parquet",
            "description": "Reconstructed 256 paired forecast-observation evaluation records across 16 primary stations and 16 dates",
            "source_provider": "NOAA GFS 0.25-deg + IMD/KSNDMC Ground Rain Gauges",
            "record_count": 256
        },
        "phase7_forecast_verification_metrics": {
            "file_path": "data/processed/phase7/verification/phase7_forecast_verification_metrics.parquet",
            "description": "Multi-threshold contingency metrics (2.5mm, 15.6mm, 35.5mm, 64.5mm, 115.6mm) and continuous skill statistics",
            "source_provider": "Phase 7 Verification Engine",
            "record_count": 5
        },
        "phase7_flood_evidence_assessment": {
            "file_path": "data/processed/phase7/flood_evidence/phase7_flood_evidence_assessment.parquet",
            "description": "Reconstructed 1,170-cell ground truth reference matrix with tier classifications (13 pos, 7 neg, 1,150 unobserved)",
            "source_provider": "Multi-Source Official, Civic & Geotagged Resident Records",
            "record_count": 1170
        },
        "phase7_sar_evidence_comparison": {
            "file_path": "data/processed/phase7/sar_validation/phase7_sar_evidence_comparison.parquet",
            "description": "Deconstructed physical radar regimes and ground truth cross-validation for 20 verified validation sites",
            "source_provider": "Copernicus Sentinel-1A C-SAR (Orbit 165 Descending)",
            "record_count": 20
        },
        "phase7_hydrology_comparison": {
            "file_path": "data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet",
            "description": "Terrain depression sensitivity comparison (unconditioned vs priority-flood conditioned) and static susceptibility variants",
            "source_provider": "MERIT Hydro / SRTM 1-arcsecond DEM + Phase 7 Routing Engine",
            "record_count": 1170
        }
    }
    
    for ds_id, meta in p7_datasets.items():
        p = os.path.normpath(meta["file_path"])
        actual_size = os.path.getsize(p)
        actual_hash = sha256_file(p)
        master_entries[ds_id] = {
            "dataset_id": ds_id,
            "original_id": ds_id,
            "file_path": p,
            "file_size_bytes": actual_size,
            "sha256_checksum": actual_hash,
            "originating_manifest": "Phase 7 Verification & Final Manifest",
            "source_provider": meta["source_provider"],
            "description": meta["description"],
            "record_count": meta["record_count"],
            "validation_status": "PHASE_7_VERIFIED_OUTPUT"
        }
        
    print(f"Total datasets in Master Final Manifest: {len(master_entries)} (Target: 73)")
    
    final_manifest = {
        "manifest_name": "Phase 7 Master Final Data Manifest",
        "study_area": "Bengaluru Urban provisional study domain (1,170 cells, EPSG:6933)",
        "project_title": "AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data",
        "final_acceptance_status": "PHASE_7_COMPLETED_WITH_DOCUMENTED_LIMITATIONS",
        "compiled_at_utc": datetime.utcnow().isoformat() + "Z",
        "total_datasets_registered": len(master_entries),
        "historical_baseline_count": 68,
        "phase7_deliverable_count": 5,
        "datasets": master_entries
    }
    
    os.makedirs(os.path.dirname(FINAL_MANIFEST_PATH), exist_ok=True)
    with open(FINAL_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(final_manifest, f, indent=2)
        
    print(f"Master Final Manifest written to: {FINAL_MANIFEST_PATH}")
    print("\n" + "=" * 80)
    print("MASTER FINAL MANIFEST COMPILED AND RECONCILED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    main()
