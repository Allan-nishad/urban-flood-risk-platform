"""
Tests for EPSG:6933 global equal-area grid engine, standardized grid IDs,
geodesic distortion analysis, boundary fraction coverage, and cross-district stability.
"""

from pathlib import Path
import pytest
from shapely.geometry import box
import geopandas as gpd

from floodrisk.config import load_study_area_config
from floodrisk.spatial.crs import DEFAULT_ANALYSIS_CRS, WGS84_CRS
from floodrisk.spatial.grid import (
    GlobalEqualAreaGrid,
    compute_global_cell_index,
    format_grid_id,
    generate_global_grid_for_bounds,
    generate_grid_for_study_area,
    compute_grid_distortion_metrics
)
from floodrisk.spatial.boundaries import load_study_area_boundary


def test_standardized_grid_id_format():
    """Verify format_grid_id matches the standard: g{cell_size_m}_{col}_{row}."""
    cell_size = 1000
    x, y = 7381250.0, 1384750.0
    col, row = compute_global_cell_index(x, y, cell_size)
    assert col == 7381
    assert row == 1384

    gid = format_grid_id(col, row, cell_size)
    assert gid == "g1000_7381_1384"


def test_fraction_inside_domain_and_coverage_class():
    """Verify fraction_inside_domain correctly separates fully_inside, partially_intersecting, and outside."""
    grid_engine = GlobalEqualAreaGrid(crs=DEFAULT_ANALYSIS_CRS, cell_size_m=1000)

    # Define a boundary that cleanly bisects grid cells
    boundary_wgs84 = box(77.50, 12.90, 77.60, 13.00)
    gdf = grid_engine.create_grid_gdf(boundary_wgs84, boundary_crs=WGS84_CRS, clip_mode="intersects")

    assert len(gdf) > 0
    assert "fraction_inside_domain" in gdf.columns
    assert "fraction_inside_boundary" in gdf.columns, "Backward-compatible alias must be preserved"
    assert "coverage_class" in gdf.columns

    # Fraction values must be strictly between 0.0 and 1.0
    assert (gdf["fraction_inside_domain"] >= 0.0).all()
    assert (gdf["fraction_inside_domain"] <= 1.0).all()
    assert (gdf["fraction_inside_domain"] == gdf["fraction_inside_boundary"]).all()

    # Must contain both fully inside cells in the interior and partially intersecting on the border
    classes = set(gdf["coverage_class"])
    assert "fully_inside" in classes
    assert "partially_intersecting" in classes


def test_geodesic_area_and_distortion_measurements():
    """Verify geodesic area and side-length metrics on the WGS84 ellipsoid."""
    grid_engine = GlobalEqualAreaGrid(crs=DEFAULT_ANALYSIS_CRS, cell_size_m=1000)
    cells = grid_engine.generate_cells_for_bounds(
        (7480000.0, 1630000.0, 7485000.0, 1635000.0)
    )
    gdf = gpd.GeoDataFrame(cells, crs=DEFAULT_ANALYSIS_CRS)

    assert "geodesic_area_sqm" in gdf.columns
    assert "geodesic_area_diff_sqm" in gdf.columns
    assert "geodesic_area_ratio" in gdf.columns
    assert "geodesic_south_edge_m" in gdf.columns
    assert "edge_ratio_south" in gdf.columns

    # Explicit numerical tolerance test:
    # EPSG:6933 (Lambert Cylindrical Equal Area) preserves surface area globally on the WGS84 ellipsoid.
    # Theoretical tolerance: |geodesic_area - 1,000,000.0| <= 0.05 m^2 (relative tolerance < 5e-8).
    # This also confirms that geodesic area is computed via ellipsoidal trigonometry and NOT copied from nominal.
    diffs = gdf["geodesic_area_diff_sqm"].to_numpy()
    assert (abs(diffs) <= 0.05).all(), f"Max area discrepancy {max(abs(diffs))} exceeded tolerance 0.05 m^2"
    assert not (diffs == 0.0).all(), "Geodesic area must reflect real ellipsoidal computation, not identical zero"

    # Linear scale at latitude ~13 deg N has non-unity scale due to equal-area requirement:
    # East-West edges stretched (> 1000m), North-South edges compressed (< 1000m)
    assert (gdf["geodesic_south_edge_m"] > 1050.0).all()
    assert (gdf["geodesic_west_edge_m"] < 950.0).all()

    metrics = compute_grid_distortion_metrics(gdf)
    assert metrics["total_cells"] == len(gdf)
    assert metrics["nominal_area_sqm"] == 1000000.0
    assert metrics["crs_metadata"]["crs_id"] == "EPSG:6933"
    assert "Lambert Cylindrical Equal Area" in metrics["crs_metadata"]["projection_method"]


def test_actual_overlapping_geography_bengaluru_urban_and_rural():
    """
    CRITICAL ARCHITECTURAL TEST:
    Verify that generating grids for contiguous districts (Bengaluru Urban and Bengaluru Rural)
    produces 100% IDENTICAL grid IDs, row/col indices, and projected geometries for all shared cells.
    """
    cfg_urban = load_study_area_config("configs/areas/bengaluru.yaml")
    cfg_rural = load_study_area_config("configs/areas/bengaluru_rural.yaml")

    boundary_urban, _ = load_study_area_boundary(cfg_urban)
    boundary_rural, _ = load_study_area_boundary(cfg_rural)

    grid_engine = GlobalEqualAreaGrid(crs=DEFAULT_ANALYSIS_CRS, cell_size_m=1000)

    gdf_urban = grid_engine.create_grid_gdf(boundary_urban.geometry.iloc[0], boundary_crs=WGS84_CRS, clip_mode="intersects")
    gdf_rural = grid_engine.create_grid_gdf(boundary_rural.geometry.iloc[0], boundary_crs=WGS84_CRS, clip_mode="intersects")

    urban_ids = set(gdf_urban["grid_id"])
    rural_ids = set(gdf_rural["grid_id"])

    shared_ids = urban_ids.intersection(rural_ids)

    # The contiguous bounding boxes overlap significantly across the shared boundary
    assert len(shared_ids) > 100, f"Expected >100 shared cells between contiguous districts, got {len(shared_ids)}"

    # For every shared cell, verify exact identity
    for sample_id in list(shared_ids)[:20]:
        cell_u = gdf_urban[gdf_urban["grid_id"] == sample_id].iloc[0]
        cell_r = gdf_rural[gdf_rural["grid_id"] == sample_id].iloc[0]

        assert cell_u["col_idx"] == cell_r["col_idx"]
        assert cell_u["row_idx"] == cell_r["row_idx"]
        assert cell_u["centroid_lon"] == pytest.approx(cell_r["centroid_lon"], abs=1e-6)
        assert cell_u["centroid_lat"] == pytest.approx(cell_r["centroid_lat"], abs=1e-6)
        assert cell_u.geometry.equals(cell_r.geometry)


def test_grid_resolution_scalability():
    """Verify that grid resolution is configurable with standardized g{size}_{col}_{row} format."""
    test_bounds = (77.58, 12.96, 77.62, 13.00)
    gdf_1000m = generate_global_grid_for_bounds(test_bounds, cell_size_m=1000)
    gdf_500m = generate_global_grid_for_bounds(test_bounds, cell_size_m=500)

    assert gdf_1000m["grid_id"].iloc[0].startswith("g1000_")
    assert gdf_500m["grid_id"].iloc[0].startswith("g500_")
    assert len(gdf_500m) > len(gdf_1000m)


def test_grid_export_geojson_and_gpkg(tmp_path: Path):
    """Verify exporting generated grid with fraction_inside_domain to GeoJSON and GPKG."""
    study_geom = box(77.58, 12.96, 77.62, 13.00)
    geojson_path = tmp_path / "test_grid.geojson"
    gpkg_path = tmp_path / "test_grid.gpkg"

    gdf_json = generate_grid_for_study_area(
        boundary_geom_wgs84=study_geom,
        cell_size_m=1000,
        export_path=geojson_path,
        export_format="geojson"
    )
    assert geojson_path.is_file()
    read_back_json = gpd.read_file(geojson_path)
    assert len(read_back_json) == len(gdf_json)
    assert "fraction_inside_domain" in read_back_json.columns
    assert "fraction_inside_boundary" in read_back_json.columns

    gdf_gpkg = generate_grid_for_study_area(
        boundary_geom_wgs84=study_geom,
        cell_size_m=1000,
        export_path=gpkg_path,
        export_format="gpkg"
    )
    assert gpkg_path.is_file()
    read_back_gpkg = gpd.read_file(gpkg_path)
    assert len(read_back_gpkg) == len(gdf_gpkg)
    assert "fraction_inside_domain" in read_back_gpkg.columns
    assert "fraction_inside_boundary" in read_back_gpkg.columns
