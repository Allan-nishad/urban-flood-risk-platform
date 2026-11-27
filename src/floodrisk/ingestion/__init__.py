"""Data Ingestion and Registration Engine.
Handles controlled staging of external and raw files into canonical workspace directories.
Guarantees raw files remain immutable and generates initial provenance entries upon registration.
"""

from pathlib import Path
import shutil
from typing import Optional, Union, Dict, Any
from ..provenance import compute_sha256, register_file_provenance, DatasetProvenanceRecord


def stage_raw_file(
    source_file: Union[str, Path],
    target_category: str,
    base_dir: Optional[Union[str, Path]] = None,
    overwrite: bool = False
) -> Path:
    """Stage an incoming dataset into the canonical data/raw/{target_category}/ directory.
    Guarantees raw files are never silently overwritten.
    """
    src = Path(source_file)
    if not src.is_file():
        raise FileNotFoundError(f"Source file to stage not found: {src.resolve()}")

    root = Path(base_dir) if base_dir else Path.cwd()
    dest_dir = root / "data" / "raw" / target_category
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_file = dest_dir / src.name
    if dest_file.exists() and not overwrite:
        if compute_sha256(src) == compute_sha256(dest_file):
            return dest_file
        raise FileExistsError(
            f"Raw destination file {dest_file} already exists and overwrite=False. "
            f"Raw files are strictly immutable to prevent accidental data corruption."
        )

    shutil.copy2(src, dest_file)
    return dest_file


def stage_boundary_file(
    source_file: Union[str, Path],
    study_area_id: str,
    base_dir: Optional[Union[str, Path]] = None,
    overwrite: bool = False
) -> Path:
    """Stage an incoming boundary file into data/raw/boundaries/."""
    src = Path(source_file)
    if not src.is_file():
        raise FileNotFoundError(f"Boundary file not found: {src.resolve()}")

    root = Path(base_dir) if base_dir else Path.cwd()
    dest_dir = root / "data" / "raw" / "boundaries"
    dest_dir.mkdir(parents=True, exist_ok=True)

    suffix = src.suffix
    dest_file = dest_dir / f"{study_area_id}_boundary{suffix}"
    if dest_file.exists() and not overwrite:
        if compute_sha256(src) == compute_sha256(dest_file):
            return dest_file
        raise FileExistsError(f"Destination boundary file {dest_file} exists.")

    shutil.copy2(src, dest_file)
    return dest_file

