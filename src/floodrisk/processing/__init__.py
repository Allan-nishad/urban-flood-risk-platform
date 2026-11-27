"""
Processing and spatial feature engineering subpackage for flood risk modeling.
"""

from .rainfall import (
    OFFICIAL_IMERG_VARIABLES,
    parse_and_validate_rainfall_units,
    convert_precipitation_to_depth_mm,
    IMERGDownloader,
    IMERGRasterReader,
    IMERGGridMapper,
    AntecedentPrecipitationEngine,
    create_mock_imerg_raster
)
from .events import (
    EvidenceCategory,
    LocationAccuracy,
    VerificationStatus,
    FloodIncidentRecord,
    GridIncidentAssociator,
    FloodEventInventory,
    get_canonical_source_registry,
    get_canonical_bengaluru_2022_incidents
)
from .zonal import (
    GridFeatureMetadata,
    RasterZonalExtractor,
    compute_terrain_zonal_features,
    compute_hydrology_zonal_features,
    compute_landcover_zonal_features,
    create_rainfall_grid_feature
)

__all__ = [
    "OFFICIAL_IMERG_VARIABLES",
    "parse_and_validate_rainfall_units",
    "convert_precipitation_to_depth_mm",
    "IMERGDownloader",
    "IMERGRasterReader",
    "IMERGGridMapper",
    "AntecedentPrecipitationEngine",
    "create_mock_imerg_raster",
    "EvidenceCategory",
    "LocationAccuracy",
    "VerificationStatus",
    "FloodIncidentRecord",
    "GridIncidentAssociator",
    "FloodEventInventory",
    "get_canonical_source_registry",
    "get_canonical_bengaluru_2022_incidents",
    "GridFeatureMetadata",
    "RasterZonalExtractor",
    "compute_terrain_zonal_features",
    "compute_hydrology_zonal_features",
    "compute_landcover_zonal_features",
    "create_rainfall_grid_feature"
]
