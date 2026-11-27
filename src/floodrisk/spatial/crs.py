"""
Coordinate Reference Systems (CRS) Engine
Standardises spatial operations to EPSG:6933 (WGS 84 / NSIDC EASE-Grid 2.0 Global;
Lambert Cylindrical Equal Area, Standard Parallel 30°N)
and handles bidirectional transformations with WGS84 (EPSG:4326) and source projections.
"""

from typing import Tuple, Union
import numpy as np
import pyproj
import shapely
from shapely.geometry import box, Polygon, MultiPolygon
try:
    from shapely import transform as shapely_transform_v2
except ImportError:
    shapely_transform_v2 = None
from shapely.ops import transform as shapely_transform_ops

DEFAULT_ANALYSIS_CRS = "EPSG:6933"
WGS84_CRS = "EPSG:4326"


def ensure_crs(crs_input: Union[str, pyproj.CRS]) -> pyproj.CRS:
    """Parse and validate any CRS string, EPSG code, or pyproj.CRS instance."""
    if isinstance(crs_input, pyproj.CRS):
        return crs_input
    try:
        return pyproj.CRS.from_user_input(crs_input)
    except Exception as exc:
        raise ValueError(f"Invalid or unrecognised CRS: '{crs_input}'. Error: {exc}") from exc


def get_transformer(
    source_crs: Union[str, pyproj.CRS],
    target_crs: Union[str, pyproj.CRS]
) -> pyproj.Transformer:
    """
    Get a thread-safe pyproj Transformer configured with always_xy=True.

    Parameters
    ----------
    source_crs : Union[str, pyproj.CRS]
        Source coordinate reference system.
    target_crs : Union[str, pyproj.CRS]
        Target coordinate reference system.

    Returns
    -------
    pyproj.Transformer
    """
    src = ensure_crs(source_crs)
    tgt = ensure_crs(target_crs)
    return pyproj.Transformer.from_crs(src, tgt, always_xy=True)


def transform_point(
    x: float,
    y: float,
    source_crs: Union[str, pyproj.CRS] = WGS84_CRS,
    target_crs: Union[str, pyproj.CRS] = DEFAULT_ANALYSIS_CRS
) -> Tuple[float, float]:
    """Transform a single (x, y) coordinate pair between CRS definitions."""
    transformer = get_transformer(source_crs, target_crs)
    tx, ty = transformer.transform(x, y)
    return (float(tx), float(ty))


def transform_geometry(
    geometry: Union[Polygon, MultiPolygon],
    source_crs: Union[str, pyproj.CRS],
    target_crs: Union[str, pyproj.CRS]
):
    """
    Transform a Shapely geometry from source_crs to target_crs.
    """
    src = ensure_crs(source_crs)
    tgt = ensure_crs(target_crs)
    if src == tgt:
        return geometry

    transformer = get_transformer(src, tgt)
    if shapely_transform_v2 is not None:
        return shapely_transform_v2(
            geometry,
            lambda coords: np.column_stack(transformer.transform(coords[:, 0], coords[:, 1]))
        )
    return shapely_transform_ops(transformer.transform, geometry)


def transform_bounds(
    bounds: Tuple[float, float, float, float],
    source_crs: Union[str, pyproj.CRS],
    target_crs: Union[str, pyproj.CRS],
    densify_pts: int = 21
) -> Tuple[float, float, float, float]:
    """
    Accurately transform a bounding box (minx, miny, maxx, maxy) across CRS boundaries
    by densifying along the perimeter to account for non-linear projection curvature.

    Parameters
    ----------
    bounds : Tuple[float, float, float, float]
        (minx, miny, maxx, maxy) in source_crs.
    source_crs : Union[str, pyproj.CRS]
    target_crs : Union[str, pyproj.CRS]
    densify_pts : int
        Number of points to sample along each side of the bounding box.

    Returns
    -------
    Tuple[float, float, float, float]
        (minx, miny, maxx, maxy) in target_crs.
    """
    src = ensure_crs(source_crs)
    tgt = ensure_crs(target_crs)
    if src == tgt:
        return bounds

    minx, miny, maxx, maxy = bounds
    # Construct a polygon box in source CRS and transform
    bbox_geom = box(minx, miny, maxx, maxy)
    # Segmentize polygon exterior for high accuracy across non-linear projections
    segmentized = bbox_geom.segmentize(max_segment_length=max((maxx - minx), (maxy - miny)) / max(densify_pts, 1))
    transformed_geom = transform_geometry(segmentized, src, tgt)
    return transformed_geom.bounds
