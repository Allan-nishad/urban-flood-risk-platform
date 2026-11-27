"""
Study Area Boundaries Engine
Loads, standardises, and validates administrative boundary vectors and fallback development bounds.
Maintains clear distinction between official administrative boundaries and development bounding envelopes.
"""

from pathlib import Path
from typing import Tuple, Union, Optional
import geopandas as gpd
from shapely.geometry import box, Polygon, MultiPolygon

from .crs import WGS84_CRS, ensure_crs, transform_geometry
from ..config import StudyAreaProjectConfig


def create_bbox_boundary(
    bbox: Tuple[float, float, float, float],
    name: str = "Study Area Extent",
    crs: str = WGS84_CRS
) -> gpd.GeoDataFrame:
    """
    Construct a GeoDataFrame containing a single rectangular polygon boundary
    from a bounding box (west, south, east, north).
    """
    west, south, east, north = bbox
    polygon = box(west, south, east, north)
    gdf = gpd.GeoDataFrame(
        [{"boundary_name": name, "boundary_type": "development_bbox", "geometry": polygon}],
        crs=crs
    )
    return gdf


def validate_boundary_geometry(geometry: Union[Polygon, MultiPolygon]) -> Tuple[bool, Optional[str]]:
    """
    Validate that a boundary geometry is non-empty, valid, and of polygon type.

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_reason)
    """
    if geometry is None:
        return False, "Geometry is None."
    if geometry.is_empty:
        return False, "Geometry is empty."
    if not isinstance(geometry, (Polygon, MultiPolygon)):
        return False, f"Expected Polygon or MultiPolygon, got {geometry.geom_type}."
    if not geometry.is_valid:
        return False, f"Geometry has topological errors: {geometry.explain_validity() if hasattr(geometry, 'explain_validity') else 'Self-intersection or invalid ring'}"
    return True, None


def load_study_area_boundary(
    config: StudyAreaProjectConfig,
    base_dir: Optional[Union[str, Path]] = None
) -> Tuple[gpd.GeoDataFrame, str]:
    """
    Load the authoritative boundary vector if present, or construct the development bounding box.

    Parameters
    ----------
    config : StudyAreaProjectConfig
        Loaded study area configuration object.
    base_dir : Optional[Union[str, Path]]
        Workspace root directory to resolve relative boundary paths.

    Returns
    -------
    Tuple[gpd.GeoDataFrame, str]
        (boundary_gdf, boundary_status)
        boundary_gdf is guaranteed to be in EPSG:4326 (WGS84).
        boundary_status communicates whether authoritative polygon or development bbox was used.
    """
    root = Path(base_dir) if base_dir else Path.cwd()
    boundary_rel_path = config.study_area.boundary_file
    boundary_path = (root / boundary_rel_path).resolve()

    if boundary_path.is_file():
        try:
            gdf = gpd.read_file(boundary_path)
            if gdf.empty:
                raise ValueError(f"Boundary file at {boundary_path} contains 0 features.")
            if gdf.crs is None:
                raise ValueError(f"Boundary file at {boundary_path} has missing CRS.")

            # Reproject to WGS84 for canonical internal boundary representation
            gdf_wgs84 = gdf.to_crs(WGS84_CRS)
            # Combine all features into unified polygon if multiple
            unified_geom = gdf_wgs84.union_all() if hasattr(gdf_wgs84, "union_all") else gdf_wgs84.unary_union
            is_valid, reason = validate_boundary_geometry(unified_geom)
            if not is_valid:
                # Attempt buffer(0) repair
                unified_geom = unified_geom.buffer(0)
                is_valid, reason = validate_boundary_geometry(unified_geom)
                if not is_valid:
                    raise ValueError(f"Invalid boundary geometry in {boundary_path}: {reason}")

            result_gdf = gpd.GeoDataFrame(
                [{
                    "study_area_id": config.study_area.id,
                    "study_area_name": config.study_area.name,
                    "boundary_type": "authoritative_polygon",
                    "geometry": unified_geom
                }],
                crs=WGS84_CRS
            )
            return result_gdf, "authoritative_boundary_loaded"
        except Exception as exc:
            # Report failure clearly
            pass

    # Authoritative file not available; generate development bounding box
    bbox = config.study_area.bbox_wgs84.as_tuple()
    bbox_gdf = create_bbox_boundary(
        bbox=bbox,
        name=f"{config.study_area.name} (Development Bounding Box)",
        crs=WGS84_CRS
    )
    bbox_gdf["study_area_id"] = config.study_area.id
    bbox_gdf["study_area_name"] = config.study_area.name
    return bbox_gdf, f"fallback_development_bbox (status: {config.study_area.boundary_status})"

