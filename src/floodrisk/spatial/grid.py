"""
Global Equal-Area Spatial Grid Engine
Implements globally anchored, boundary-independent grid generation using EPSG:6933
(WGS 84 / NSIDC EASE-Grid 2.0 Global; Lambert Cylindrical Equal Area).
Standardised grid ID format: g{cell_size_m}_{col}_{row}
Ensures stable, unique cell identifiers regardless of study area bounding extent or execution scope.
Includes geodesic area and side-length distortion analysis on the WGS84 ellipsoid.
"""

import math
from pathlib import Path
from typing import Tuple, List, Optional, Literal, Union, Dict, Any
import numpy as np
import pandas as pd
import geopandas as gpd
import pyproj
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.ops import unary_union

from .crs import (
    DEFAULT_ANALYSIS_CRS,
    WGS84_CRS,
    get_transformer,
    transform_bounds,
    transform_geometry
)


def compute_global_cell_index(x: float, y: float, cell_size_m: int) -> Tuple[int, int]:
    """
    Compute integer global column and row indices for a coordinate (x, y) in EPSG:6933.

    Anchored at (0.0, 0.0) global origin.
    col = floor(x / cell_size_m)
    row = floor(y / cell_size_m)
    """
    col = int(math.floor(x / cell_size_m))
    row = int(math.floor(y / cell_size_m))
    return col, row


def format_grid_id(col: int, row: int, cell_size_m: int) -> str:
    """
    Generate canonical standardised grid cell identifier string.

    Format: g{cell_size_m}_{col}_{row}
    Example: g1000_7472_1625
    """
    return f"g{cell_size_m}_{col}_{row}"


class GlobalEqualAreaGrid:
    """
    Globally anchored equal-area grid generator and spatial partitioner in EPSG:6933.
    """

    def __init__(self, crs: str = DEFAULT_ANALYSIS_CRS, cell_size_m: int = 1000):
        self.crs = crs
        self.cell_size_m = cell_size_m
        self.to_wgs84 = get_transformer(self.crs, WGS84_CRS)
        self.from_wgs84 = get_transformer(WGS84_CRS, self.crs)
        self.geod = pyproj.Geod(ellps="WGS84")

    def generate_cells_for_bounds(
        self,
        bounds_6933: Tuple[float, float, float, float]
    ) -> List[dict]:
        """
        Generate global grid cell records covering the specified EPSG:6933 bounding box.
        Computes projected attributes, WGS84 geographic references, and exact geodesic measurements.
        """
        minx, miny, maxx, maxy = bounds_6933
        s = self.cell_size_m
        nominal_area = float(s * s)

        col_start = int(math.floor(minx / s))
        col_end = int(math.floor(maxx / s))
        row_start = int(math.floor(miny / s))
        row_end = int(math.floor(maxy / s))

        cells = []
        for c in range(col_start, col_end + 1):
            cell_minx = c * s
            cell_maxx = (c + 1) * s
            cent_x = cell_minx + (s / 2.0)

            for r in range(row_start, row_end + 1):
                cell_miny = r * s
                cell_maxy = (r + 1) * s
                cent_y = cell_miny + (s / 2.0)

                # Geographic centroid in WGS84
                lon_c, lat_c = self.to_wgs84.transform(cent_x, cent_y)

                # Four corners in WGS84 for geodesic edge and area calculation
                lon_sw, lat_sw = self.to_wgs84.transform(cell_minx, cell_miny)
                lon_se, lat_se = self.to_wgs84.transform(cell_maxx, cell_miny)
                lon_ne, lat_ne = self.to_wgs84.transform(cell_maxx, cell_maxy)
                lon_nw, lat_nw = self.to_wgs84.transform(cell_minx, cell_maxy)

                # 1. Geodesic area on WGS84 ellipsoid
                lons = [lon_sw, lon_se, lon_ne, lon_nw, lon_sw]
                lats = [lat_sw, lat_se, lat_ne, lat_nw, lat_sw]
                geo_area, _ = self.geod.polygon_area_perimeter(lons, lats)
                geodesic_area_sqm = abs(geo_area)
                geodesic_area_diff_sqm = geodesic_area_sqm - nominal_area
                geodesic_area_ratio = geodesic_area_sqm / nominal_area

                # 2. Geodesic side lengths along cell perimeter (WGS84 ellipsoid)
                _, _, dist_south = self.geod.inv(lon_sw, lat_sw, lon_se, lat_se)
                _, _, dist_north = self.geod.inv(lon_nw, lat_nw, lon_ne, lat_ne)
                _, _, dist_west = self.geod.inv(lon_sw, lat_sw, lon_nw, lat_nw)
                _, _, dist_east = self.geod.inv(lon_se, lat_se, lon_ne, lat_ne)

                geom_6933 = box(cell_minx, cell_miny, cell_maxx, cell_maxy)
                grid_id = format_grid_id(c, r, s)

                cells.append({
                    "grid_id": grid_id,
                    "col_idx": c,
                    "row_idx": r,
                    "cell_size_m": s,
                    "centroid_x_6933": round(cent_x, 2),
                    "centroid_y_6933": round(cent_y, 2),
                    "centroid_lon": round(float(lon_c), 7),
                    "centroid_lat": round(float(lat_c), 7),
                    "minx_6933": cell_minx,
                    "miny_6933": cell_miny,
                    "maxx_6933": cell_maxx,
                    "maxy_6933": cell_maxy,
                    "nominal_area_sqkm": round(nominal_area / 1e6, 4),
                    "nominal_area_sqm": nominal_area,
                    "geodesic_area_sqm": float(geodesic_area_sqm),
                    "geodesic_area_diff_sqm": float(geodesic_area_diff_sqm),
                    "geodesic_area_ratio": float(geodesic_area_ratio),
                    "geodesic_south_edge_m": float(dist_south),
                    "geodesic_north_edge_m": float(dist_north),
                    "geodesic_west_edge_m": float(dist_west),
                    "geodesic_east_edge_m": float(dist_east),
                    "edge_ratio_south": float(dist_south / s),
                    "edge_ratio_north": float(dist_north / s),
                    "edge_ratio_west": float(dist_west / s),
                    "edge_ratio_east": float(dist_east / s),
                    "geometry": geom_6933
                })

        return cells

    def create_grid_gdf(
        self,
        boundary_geometry: Union[Polygon, MultiPolygon],
        boundary_crs: str = WGS84_CRS,
        clip_mode: Literal["intersects", "contains_centroid", "clip_polygon", "envelope"] = "intersects"
    ) -> gpd.GeoDataFrame:
        """
        Create a GeoDataFrame of global grid cells intersecting or clipped to the given domain geometry.
        Computes fraction_inside_domain and coverage_class for every cell.
        Retains fraction_inside_boundary as a backward-compatible alias.
        """
        # Transform boundary to analysis CRS (EPSG:6933)
        study_geom_6933 = transform_geometry(boundary_geometry, boundary_crs, self.crs)
        if not study_geom_6933.is_valid:
            study_geom_6933 = study_geom_6933.buffer(0)

        bounds = study_geom_6933.bounds
        cell_records = self.generate_cells_for_bounds(bounds)

        if not cell_records:
            return gpd.GeoDataFrame(columns=["grid_id", "geometry"], crs=self.crs)

        gdf = gpd.GeoDataFrame(cell_records, crs=self.crs)
        cell_area = float(self.cell_size_m * self.cell_size_m)

        # Compute fraction_inside_domain and coverage_class for every generated cell
        inter_geoms = gdf.geometry.intersection(study_geom_6933)
        inter_areas = inter_geoms.area
        fractions = (inter_areas / cell_area).clip(lower=0.0, upper=1.0)

        gdf["fraction_inside_domain"] = fractions.round(6)
        # Retain backward-compatible alias for existing pipelines
        gdf["fraction_inside_boundary"] = gdf["fraction_inside_domain"]

        # Classify coverage status
        coverage_classes = []
        for frac in gdf["fraction_inside_domain"]:
            if frac >= 0.9999:
                coverage_classes.append("fully_inside")
            elif frac > 0.0:
                coverage_classes.append("partially_intersecting")
            else:
                coverage_classes.append("outside")
        gdf["coverage_class"] = coverage_classes

        if clip_mode == "envelope":
            return gdf

        if clip_mode == "intersects":
            mask = gdf["fraction_inside_domain"] > 0.0
            return gdf[mask].copy().reset_index(drop=True)

        if clip_mode == "contains_centroid":
            centroids = gdf.geometry.centroid
            mask = centroids.within(study_geom_6933)
            return gdf[mask].copy().reset_index(drop=True)

        if clip_mode == "clip_polygon":
            mask = gdf["fraction_inside_domain"] > 0.0
            intersecting = gdf[mask].copy()
            intersecting["geometry"] = intersecting.geometry.intersection(study_geom_6933)
            return intersecting[~intersecting.geometry.is_empty].copy().reset_index(drop=True)

        raise ValueError(f"Unknown clip_mode: {clip_mode}")


def generate_global_grid_for_bounds(
    bbox_wgs84: Tuple[float, float, float, float],
    cell_size_m: int = 1000,
    analysis_crs: str = DEFAULT_ANALYSIS_CRS
) -> gpd.GeoDataFrame:
    """
    Generate global equal-area grid cells covering a WGS84 bounding box (west, south, east, north).
    """
    grid_engine = GlobalEqualAreaGrid(crs=analysis_crs, cell_size_m=cell_size_m)
    bounds_6933 = transform_bounds(bbox_wgs84, WGS84_CRS, analysis_crs)
    cells = grid_engine.generate_cells_for_bounds(bounds_6933)
    return gpd.GeoDataFrame(cells, crs=analysis_crs)


def generate_grid_for_study_area(
    boundary_geom_wgs84: Union[Polygon, MultiPolygon],
    cell_size_m: int = 1000,
    analysis_crs: str = DEFAULT_ANALYSIS_CRS,
    clip_mode: Literal["intersects", "contains_centroid", "clip_polygon", "envelope"] = "intersects",
    export_path: Optional[Union[str, Path]] = None,
    export_format: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Generate globally anchored grid for any study area geometry and optionally export to disk.
    Supports GeoJSON (RFC 7946 EPSG:4326) and GeoPackage (native EPSG:6933).
    """
    grid_engine = GlobalEqualAreaGrid(crs=analysis_crs, cell_size_m=cell_size_m)
    gdf = grid_engine.create_grid_gdf(
        boundary_geometry=boundary_geom_wgs84,
        boundary_crs=WGS84_CRS,
        clip_mode=clip_mode
    )

    if export_path:
        out_p = Path(export_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fmt = (export_format or out_p.suffix.lstrip(".").lower())

        if fmt in ["geojson", "json"]:
            gdf_wgs84 = gdf.to_crs(WGS84_CRS)
            gdf_wgs84.to_file(out_p, driver="GeoJSON")
        elif fmt in ["gpkg", "geopackage"]:
            gdf.to_file(out_p, driver="GPKG")
        else:
            raise ValueError(f"Unsupported export format '{fmt}'. Choose 'geojson' or 'gpkg'.")

    return gdf


def compute_grid_distortion_metrics(gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    """
    Compute comprehensive statistical summary of geodesic area and linear edge distortion
    across all grid cells in the given GeoDataFrame. Retains full double-precision metrics.
    """
    if gdf.empty:
        return {"total_cells": 0}

    s_edge = gdf["cell_size_m"].iloc[0] if "cell_size_m" in gdf.columns else 1000
    nominal_area = float(s_edge * s_edge)

    report = {
        "crs_metadata": {
            "crs_id": "EPSG:6933",
            "crs_name": "WGS 84 / NSIDC EASE-Grid 2.0 Global",
            "projection_method": "Lambert Cylindrical Equal Area (EPSG:9835)",
            "standard_parallel": "30.0 degrees North/South",
            "natural_origin": "0.0 degrees (Greenwich / Equator)",
            "ellipsoid": "WGS 84 (semi-major: 6378137.0 m, inverse flattening: 298.257223563)"
        },
        "total_cells": len(gdf),
        "nominal_cell_size_m": int(s_edge),
        "nominal_area_sqm": nominal_area,
        "geodesic_area_sqm": {
            "min": float(gdf["geodesic_area_sqm"].min()),
            "max": float(gdf["geodesic_area_sqm"].max()),
            "mean": float(gdf["geodesic_area_sqm"].mean()),
            "std": float(gdf["geodesic_area_sqm"].std())
        },
        "geodesic_area_diff_sqm": {
            "min": float(gdf["geodesic_area_diff_sqm"].min()) if "geodesic_area_diff_sqm" in gdf.columns else float(gdf["geodesic_area_sqm"].min() - nominal_area),
            "max": float(gdf["geodesic_area_diff_sqm"].max()) if "geodesic_area_diff_sqm" in gdf.columns else float(gdf["geodesic_area_sqm"].max() - nominal_area),
            "mean": float(gdf["geodesic_area_diff_sqm"].mean()) if "geodesic_area_diff_sqm" in gdf.columns else float(gdf["geodesic_area_sqm"].mean() - nominal_area),
            "std": float(gdf["geodesic_area_diff_sqm"].std()) if "geodesic_area_diff_sqm" in gdf.columns else float(gdf["geodesic_area_sqm"].std())
        },
        "geodesic_area_ratio": {
            "min": float(gdf["geodesic_area_ratio"].min()),
            "max": float(gdf["geodesic_area_ratio"].max()),
            "mean": float(gdf["geodesic_area_ratio"].mean()),
            "std": float(gdf["geodesic_area_ratio"].std())
        },
        "edge_lengths_m": {
            "south_edge": {
                "min": float(gdf["geodesic_south_edge_m"].min()),
                "max": float(gdf["geodesic_south_edge_m"].max()),
                "mean": float(gdf["geodesic_south_edge_m"].mean())
            },
            "north_edge": {
                "min": float(gdf["geodesic_north_edge_m"].min()),
                "max": float(gdf["geodesic_north_edge_m"].max()),
                "mean": float(gdf["geodesic_north_edge_m"].mean())
            },
            "west_edge": {
                "min": float(gdf["geodesic_west_edge_m"].min()),
                "max": float(gdf["geodesic_west_edge_m"].max()),
                "mean": float(gdf["geodesic_west_edge_m"].mean())
            },
            "east_edge": {
                "min": float(gdf["geodesic_east_edge_m"].min()),
                "max": float(gdf["geodesic_east_edge_m"].max()),
                "mean": float(gdf["geodesic_east_edge_m"].mean())
            }
        },
        "edge_ratios": {
            "south_edge": {
                "min": float(gdf["edge_ratio_south"].min()),
                "max": float(gdf["edge_ratio_south"].max()),
                "mean": float(gdf["edge_ratio_south"].mean())
            },
            "north_edge": {
                "min": float(gdf["edge_ratio_north"].min()),
                "max": float(gdf["edge_ratio_north"].max()),
                "mean": float(gdf["edge_ratio_north"].mean())
            },
            "west_edge": {
                "min": float(gdf["edge_ratio_west"].min()),
                "max": float(gdf["edge_ratio_west"].max()),
                "mean": float(gdf["edge_ratio_west"].mean())
            },
            "east_edge": {
                "min": float(gdf["edge_ratio_east"].min()),
                "max": float(gdf["edge_ratio_east"].max()),
                "mean": float(gdf["edge_ratio_east"].mean())
            }
        }
    }

    if "fraction_inside_domain" in gdf.columns or "fraction_inside_boundary" in gdf.columns:
        cov_col = "fraction_inside_domain" if "fraction_inside_domain" in gdf.columns else "fraction_inside_boundary"
        cov_counts = gdf["coverage_class"].value_counts().to_dict() if "coverage_class" in gdf.columns else {}
        domain_cov = {
            "fully_inside_count": int(cov_counts.get("fully_inside", 0)),
            "partially_intersecting_count": int(cov_counts.get("partially_intersecting", 0)),
            "outside_count": int(cov_counts.get("outside", 0)),
            "mean_fraction_inside": float(round(gdf[cov_col].mean(), 4))
        }
        report["domain_coverage"] = domain_cov
        # Retain boundary_coverage for backward compatibility with previous reports
        report["boundary_coverage"] = domain_cov

    return report
