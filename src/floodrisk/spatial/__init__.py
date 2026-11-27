"""
Spatial processing subpackage for coordinate reference systems, global equal-area grids, and boundary management.
"""

from .crs import (
    DEFAULT_ANALYSIS_CRS,
    WGS84_CRS,
    get_transformer,
    transform_bounds,
    transform_geometry,
    ensure_crs
)
from .grid import (
    GlobalEqualAreaGrid,
    generate_global_grid_for_bounds,
    generate_grid_for_study_area,
    compute_grid_distortion_metrics,
    format_grid_id,
    compute_global_cell_index
)
from .boundaries import (
    load_study_area_boundary,
    create_bbox_boundary,
    validate_boundary_geometry
)

__all__ = [
    "DEFAULT_ANALYSIS_CRS",
    "WGS84_CRS",
    "get_transformer",
    "transform_bounds",
    "transform_geometry",
    "ensure_crs",
    "GlobalEqualAreaGrid",
    "generate_global_grid_for_bounds",
    "generate_grid_for_study_area",
    "compute_grid_distortion_metrics",
    "format_grid_id",
    "compute_global_cell_index",
    "load_study_area_boundary",
    "create_bbox_boundary",
    "validate_boundary_geometry"
]

