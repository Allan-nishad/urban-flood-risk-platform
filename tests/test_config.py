"""
Tests for study area and platform configuration loading and validation.
"""

from pathlib import Path
import pytest
from floodrisk.config import load_study_area_config, StudyAreaProjectConfig, BBoxWGS84


def test_load_valid_bengaluru_config():
    """Verify that the official Bengaluru configuration file loads and validates cleanly."""
    cfg_path = Path("configs/areas/bengaluru.yaml")
    assert cfg_path.is_file(), "bengaluru.yaml must exist."

    cfg = load_study_area_config(cfg_path)
    assert isinstance(cfg, StudyAreaProjectConfig)
    assert cfg.study_area.id == "bengaluru_urban"
    assert cfg.spatial.analysis_crs == "EPSG:6933"
    assert cfg.spatial.grid_size_m == 1000
    assert cfg.time.timezone == "Asia/Kolkata"
    assert cfg.time.canonical_timestamp == "UTC"

    bbox = cfg.study_area.bbox_wgs84
    assert bbox.west == 77.45
    assert bbox.south == 12.85
    assert bbox.east == 77.75
    assert bbox.north == 13.15


def test_load_valid_mysuru_config():
    """Verify that a second geographic configuration (Mysuru) loads with identical engine compatibility."""
    cfg_path = Path("configs/areas/mysuru.yaml")
    assert cfg_path.is_file(), "mysuru.yaml must exist."

    cfg = load_study_area_config(cfg_path)
    assert cfg.study_area.id == "mysuru_urban"
    assert cfg.spatial.analysis_crs == "EPSG:6933"
    assert cfg.spatial.grid_size_m == 1000


def test_load_valid_bengaluru_rural_config():
    """Verify that contiguous Bengaluru Rural configuration loads with identical engine compatibility."""
    cfg_path = Path("configs/areas/bengaluru_rural.yaml")
    assert cfg_path.is_file(), "bengaluru_rural.yaml must exist."

    cfg = load_study_area_config(cfg_path)
    assert cfg.study_area.id == "bengaluru_rural"
    assert cfg.spatial.analysis_crs == "EPSG:6933"
    assert cfg.spatial.grid_size_m == 1000


def test_missing_config_raises_file_not_found():
    """Verify appropriate exception on non-existent config path."""
    with pytest.raises(FileNotFoundError):
        load_study_area_config("configs/areas/non_existent_city.yaml")


def test_invalid_bbox_west_greater_than_east():
    """Verify validation rejects west >= east bounding box."""
    with pytest.raises(ValueError, match="west.*must be strictly less than east"):
        BBoxWGS84(west=80.0, south=12.0, east=75.0, north=13.0)


def test_invalid_bbox_south_greater_than_north():
    """Verify validation rejects south >= north bounding box."""
    with pytest.raises(ValueError, match="south.*must be strictly less than north"):
        BBoxWGS84(west=75.0, south=15.0, east=76.0, north=12.0)


def test_invalid_bbox_out_of_range():
    """Verify validation rejects latitude/longitude beyond valid physical Earth ranges."""
    with pytest.raises(ValueError):
        BBoxWGS84(west=-195.0, south=10.0, east=75.0, north=12.0)
    with pytest.raises(ValueError):
        BBoxWGS84(west=75.0, south=-95.0, east=76.0, north=12.0)

