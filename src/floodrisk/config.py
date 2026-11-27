"""
Geographic & Platform Configuration Management
Provides typed, validated configuration schemas for study areas, datasets, and runtime paths.
Designed to be geography-agnostic.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class BBoxWGS84(BaseModel):
    """Geographic bounding box in WGS84 coordinates (EPSG:4326)."""
    west: float = Field(..., description="Westernmost longitude in decimal degrees (-180 to 180)")
    south: float = Field(..., description="Southernmost latitude in decimal degrees (-90 to 90)")
    east: float = Field(..., description="Easternmost longitude in decimal degrees (-180 to 180)")
    north: float = Field(..., description="Northernmost latitude in decimal degrees (-90 to 90)")

    @field_validator("west", "east")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude {v} must be between -180.0 and 180.0 degrees.")
        return v

    @field_validator("south", "north")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude {v} must be between -90.0 and 90.0 degrees.")
        return v

    @model_validator(mode="after")
    def validate_bbox_extents(self) -> "BBoxWGS84":
        if self.west >= self.east:
            raise ValueError(f"Invalid bounding box: west ({self.west}) must be strictly less than east ({self.east}).")
        if self.south >= self.north:
            raise ValueError(f"Invalid bounding box: south ({self.south}) must be strictly less than north ({self.north}).")
        return self

    def as_tuple(self) -> tuple[float, float, float, float]:
        """Return (west, south, east, north)."""
        return (self.west, self.south, self.east, self.north)


class StudyAreaConfig(BaseModel):
    """Specification of an administrative or regional study area."""
    id: str = Field(..., description="Machine-readable unique study area slug (e.g., 'bengaluru_urban')")
    name: str = Field(..., description="Human-readable study area name")
    country: str = Field("India", description="Country name")
    admin_level: str = Field("district", description="Administrative classification (district, city, state, basin)")
    bbox_wgs84: BBoxWGS84 = Field(..., description="Development bounding box in EPSG:4326")
    boundary_file: Path = Field(..., description="Path to authoritative vector boundary file")
    boundary_status: str = Field("pending_authoritative_boundary", description="Status of the boundary dataset")
    boundary_notes: Optional[str] = Field(None, description="Lineage notes or boundary caveats")


class SpatialConfig(BaseModel):
    """Spatial processing and common analysis grid parameters."""
    analysis_crs: str = Field("EPSG:6933", description="Canonical equal-area CRS for grid generation and analysis")
    grid_size_m: int = Field(1000, gt=0, description="Square grid cell edge length in metres")
    grid_scheme: str = Field("global_equal_area_square", description="Grid anchoring specification")

    @field_validator("analysis_crs")
    @classmethod
    def validate_crs(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("analysis_crs must not be empty.")
        return v.strip()


class TimeConfig(BaseModel):
    """Temporal reference and aggregation parameters."""
    timezone: str = Field("Asia/Kolkata", description="Local timezone for human presentation and reporting")
    canonical_timestamp: str = Field("UTC", description="Canonical internal storage and processing timezone")
    rainfall_aggregation: str = Field("daily", description="Default temporal aggregation granularity")


class PathsConfig(BaseModel):
    """Base directory paths relative to the platform root."""
    raw: Path = Field(Path("data/raw"))
    interim: Path = Field(Path("data/interim"))
    processed: Path = Field(Path("data/processed"))
    external: Path = Field(Path("data/external"))
    reports: Path = Field(Path("reports"))


class StudyAreaProjectConfig(BaseModel):
    """Composite root configuration model for a study area."""
    study_area: StudyAreaConfig
    spatial: SpatialConfig = Field(default_factory=SpatialConfig)
    time: TimeConfig = Field(default_factory=TimeConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)


def load_study_area_config(config_path: str | Path) -> StudyAreaProjectConfig:
    """
    Load, parse and validate a YAML study-area configuration file.

    Parameters
    ----------
    config_path : str | Path
        Path to the YAML configuration file.

    Returns
    -------
    StudyAreaProjectConfig
        Validated Pydantic configuration object.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    ValueError
        If the YAML is invalid or violates schema validation rules.
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Study area configuration file not found at: {path.resolve()}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Error parsing YAML file at {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Configuration file {path} must contain a top-level YAML mapping/dictionary.")

    return StudyAreaProjectConfig.model_validate(data)


def load_yaml_config(path: str | Path) -> Dict[str, Any]:
    """Helper to load a raw YAML mapping with descriptive error handling."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Configuration file not found: {p.resolve()}")
    try:
        with open(p, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse YAML file at {p}: {exc}") from exc
    if not isinstance(content, dict):
        raise ValueError(f"File {p} does not contain a valid YAML dictionary.")
    return content

