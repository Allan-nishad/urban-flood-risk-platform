"""
Tests for cryptographic SHA-256 checksums, dataset manifest generation, and integrity verification.
"""

from pathlib import Path
import pytest
from floodrisk.provenance import (
    compute_sha256,
    register_file_provenance,
    DatasetManifest
)


def test_compute_sha256(tmp_path: Path):
    """Verify deterministic SHA-256 hash generation."""
    test_file = tmp_path / "hash_test.txt"
    test_file.write_text("Urban flood risk platform reproducibility test", encoding="utf-8")

    digest1 = compute_sha256(test_file)
    digest2 = compute_sha256(test_file)
    assert digest1 == digest2
    assert len(digest1) == 64


def test_register_provenance_and_tamper_detection(tmp_path: Path):
    """Verify registration, serialization, and detection of subsequent file modification."""
    sample_data = tmp_path / "sample_raster.tif"
    sample_data.write_bytes(b"\x00\x01\x02\x03\x04\x05")

    manifest = DatasetManifest(study_area_id="bengaluru_urban")
    record = register_file_provenance(
        file_path=sample_data,
        dataset_id="srtm_sample",
        provider="USGS/NASA",
        version="GL1v003",
        crs="EPSG:4326"
    )
    manifest.register_dataset(record)

    # Initial integrity check: must pass
    results = manifest.verify_integrity()
    assert results["srtm_sample"]["verified"] is True
    assert results["srtm_sample"]["status"] == "VALID"

    # Save and reload manifest
    manifest_file = tmp_path / "manifest.json"
    manifest.save(manifest_file)
    loaded_manifest = DatasetManifest.load(manifest_file)
    assert "srtm_sample" in loaded_manifest.datasets

    # Tamper with the raw file: append byte
    with open(sample_data, "ab") as f:
        f.write(b"\xFF")

    # Re-verify: must catch tampering/corruption
    tamper_results = loaded_manifest.verify_integrity()
    assert tamper_results["srtm_sample"]["verified"] is False
    assert tamper_results["srtm_sample"]["status"] == "TAMPERED_OR_CORRUPT"


def test_register_non_existent_file_raises_error():
    """Verify that registering a non-existent file raises FileNotFoundError (no fabricated files)."""
    with pytest.raises(FileNotFoundError):
        register_file_provenance(
            file_path="data/raw/terrain/ghost_file.tif",
            dataset_id="ghost",
            provider="None",
            version="1.0"
        )

