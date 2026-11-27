"""
Data Provenance and Reproducibility Tracking Engine
Calculates cryptographic SHA-256 checksums, tracks lineage, schema versions,
and records immutable dataset manifests for auditability and scientific reproducibility.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


def compute_sha256(file_path: Union[str, Path], chunk_size: int = 1024 * 1024) -> str:
    """
    Compute cryptographic SHA-256 hash of a file by streaming chunks.
    Preserves low memory overhead even for multi-gigabyte raster files.
    """
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Cannot compute checksum; file not found: {p.resolve()}")

    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclass
class DatasetProvenanceRecord:
    dataset_id: str
    original_filename: str
    file_path: str
    file_size_bytes: int
    sha256_checksum: str
    source_provider: str
    dataset_version: str
    source_url_or_collection: Optional[str] = None
    download_timestamp: Optional[str] = None
    geographic_coverage: str = "Unspecified"
    temporal_coverage: Optional[str] = None
    crs: Optional[str] = None
    native_resolution: Optional[str] = None
    units: Optional[str] = None
    validation_status: str = "unvalidated"
    processing_history: List[Dict[str, Any]] = field(default_factory=list)
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_processing_step(self, step_name: str, parameters: Dict[str, Any], output_path: Optional[str] = None):
        """Append an immutable processing step with timestamp to provenance history."""
        self.processing_history.append({
            "step": step_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "parameters": parameters,
            "output_path": output_path
        })


@dataclass
class DatasetManifest:
    """
    Project-wide dataset manifest cataloguing verified source files,
    provenance metadata, and validation states.
    """
    manifest_version: str = "1.0.0"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    study_area_id: Optional[str] = None
    datasets: Dict[str, DatasetProvenanceRecord] = field(default_factory=dict)

    def register_dataset(self, record: DatasetProvenanceRecord):
        self.datasets[record.dataset_id] = record

    def get_record(self, dataset_id: str) -> Optional[DatasetProvenanceRecord]:
        return self.datasets.get(dataset_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "generated_at": self.generated_at,
            "study_area_id": self.study_area_id,
            "datasets": {k: asdict(v) for k, v in self.datasets.items()}
        }

    def save(self, path: Union[str, Path]) -> Path:
        out_p = Path(path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return out_p

    @classmethod
    def load(cls, path: Union[str, Path]) -> "DatasetManifest":
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Manifest file does not exist: {p.resolve()}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        manifest = cls(
            manifest_version=data.get("manifest_version", "1.0.0"),
            generated_at=data.get("generated_at", datetime.now(timezone.utc).isoformat()),
            study_area_id=data.get("study_area_id")
        )
        for k, v in data.get("datasets", {}).items():
            record = DatasetProvenanceRecord(**v)
            manifest.register_dataset(record)
        return manifest

    def verify_integrity(self) -> Dict[str, Dict[str, Any]]:
        """
        Recompute SHA-256 for all registered files on disk to detect tampering or corruption.

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping dataset_id to integrity verification result.
        """
        results = {}
        for ds_id, record in self.datasets.items():
            p = Path(record.file_path)
            if not p.is_file():
                results[ds_id] = {
                    "status": "MISSING",
                    "expected_sha256": record.sha256_checksum,
                    "actual_sha256": None,
                    "verified": False,
                    "reason": "File not found on disk."
                }
            else:
                current_sha256 = compute_sha256(p)
                match = (current_sha256 == record.sha256_checksum)
                results[ds_id] = {
                    "status": "VALID" if match else "TAMPERED_OR_CORRUPT",
                    "expected_sha256": record.sha256_checksum,
                    "actual_sha256": current_sha256,
                    "verified": match,
                    "reason": "Checksum match." if match else "Checksum mismatch."
                }
        return results


def register_file_provenance(
    file_path: Union[str, Path],
    dataset_id: str,
    provider: str,
    version: str,
    source_url: Optional[str] = None,
    units: Optional[str] = None,
    native_resolution: Optional[str] = None,
    crs: Optional[str] = None,
    geographic_coverage: str = "India",
    temporal_coverage: Optional[str] = None,
    validation_status: str = "verified_valid"
) -> DatasetProvenanceRecord:
    """
    Inspect an existing file on disk and construct a verified DatasetProvenanceRecord.
    Raises FileNotFoundError if file does not exist. Never fabricates file existence.
    """
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Cannot register dataset: file does not exist at {p.resolve()}")

    file_size = p.stat().st_size
    checksum = compute_sha256(p)

    return DatasetProvenanceRecord(
        dataset_id=dataset_id,
        original_filename=p.name,
        file_path=str(p.resolve()),
        file_size_bytes=file_size,
        sha256_checksum=checksum,
        source_provider=provider,
        dataset_version=version,
        source_url_or_collection=source_url,
        units=units,
        native_resolution=native_resolution,
        crs=crs,
        geographic_coverage=geographic_coverage,
        temporal_coverage=temporal_coverage,
        validation_status=validation_status
    )

