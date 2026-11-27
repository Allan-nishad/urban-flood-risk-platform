"""
Command Line Interface (CLI) for Urban Flood Risk Platform
Provides operational commands for configuration inspection, data validation,
provenance tracking, and global equal-area grid generation.
"""

from pathlib import Path
import os
import sys
import json
import click

from .config import load_study_area_config
from .spatial.boundaries import load_study_area_boundary
from .spatial.grid import generate_grid_for_study_area, compute_grid_distortion_metrics
from .validate import validate_csv as run_validate_csv, validate_raster as run_validate_raster, validate_vector as run_validate_vector
from .provenance import DatasetManifest, register_file_provenance


@click.group()
def main():
    """Urban Flood Risk Detection & Forecasting Platform CLI."""
    pass


@main.command("show-config")
@click.option("--config", "-c", required=True, type=click.Path(exists=True), help="Path to study area YAML config.")
def show_config(config):
    """Display validated study area configuration and spatial parameters."""
    try:
        cfg = load_study_area_config(config)
        click.echo("=" * 60)
        click.echo(f"  STUDY AREA CONFIGURATION: {cfg.study_area.name} ({cfg.study_area.id})")
        click.echo("=" * 60)
        click.echo(f"Country:              {cfg.study_area.country}")
        click.echo(f"Admin Level:          {cfg.study_area.admin_level}")
        click.echo(f"Boundary Status:      {cfg.study_area.boundary_status}")
        click.echo(f"Boundary File:        {cfg.study_area.boundary_file}")
        bbox = cfg.study_area.bbox_wgs84
        click.echo(f"Bounding Box WGS84:   West={bbox.west}, South={bbox.south}, East={bbox.east}, North={bbox.north}")
        click.echo("-" * 60)
        click.echo(f"Analysis CRS:         {cfg.spatial.analysis_crs}")
        click.echo(f"Grid Cell Size:       {cfg.spatial.grid_size_m} m")
        click.echo(f"Grid Anchoring:       {cfg.spatial.grid_scheme}")
        click.echo("-" * 60)
        click.echo(f"Canonical Timestamp:  {cfg.time.canonical_timestamp}")
        click.echo(f"Display Timezone:     {cfg.time.timezone}")
        click.echo(f"Rainfall Aggregation: {cfg.time.rainfall_aggregation}")
        click.echo("=" * 60)
    except Exception as exc:
        click.echo(f"Error loading configuration: {exc}", err=True)
        sys.exit(1)


@main.command("validate-csv")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--kind", "-k", required=True, type=click.Choice(["rainfall", "forecast", "weather_forecast", "events", "flood_events"]), help="Canonical schema kind.")
@click.option("--schemas", "-s", default="configs/schemas.yaml", type=click.Path(), help="Path to schemas.yaml.")
@click.option("--config", "-c", default=None, type=click.Path(), help="Optional study area YAML for spatial bounds checks.")
@click.option("--quarantine", "-q", default=None, type=click.Path(), help="Optional path to write quarantined records CSV.")
@click.option("--out", "-o", default=None, type=click.Path(), help="Optional output path for validation report (JSON or CSV).")
def validate_csv(file_path, kind, schemas, config, quarantine, out):
    """Validate a CSV file against canonical platform schemas and physical consistency checks."""
    study_bbox = None
    if config and Path(config).is_file():
        cfg = load_study_area_config(config)
        study_bbox = cfg.study_area.bbox_wgs84

    click.echo(f"Validating CSV '{file_path}' against schema kind '{kind}'...")
    report = run_validate_csv(
        file_path=file_path,
        kind=kind,
        schemas_config_path=schemas if Path(schemas).is_file() else None,
        study_area_bbox=study_bbox,
        quarantine_path=quarantine
    )

    status_str = "VALID" if report.is_valid else "INVALID / HAS ERRORS"
    click.echo("-" * 60)
    click.echo(f"Validation Result:     {status_str}")
    click.echo(f"Total Records:         {report.total_records}")
    click.echo(f"Valid Records:         {report.valid_records}")
    click.echo(f"Quarantined Records:   {report.quarantined_records}")
    if report.quarantine_file:
        click.echo(f"Quarantine Exported:   {report.quarantine_file}")

    if report.issues:
        click.echo("-" * 60)
        click.echo(f"Issues Encountered ({len(report.issues)} total):")
        for issue in report.issues[:10]:
            loc = f" [Row {issue.row_index}]" if issue.row_index is not None else ""
            click.echo(f"  [{issue.severity}] {issue.category}{loc}: {issue.message}")
        if len(report.issues) > 10:
            click.echo(f"  ... and {len(report.issues) - 10} more issues.")

    if out:
        out_p = Path(out)
        if out_p.suffix.lower() == ".csv":
            report.save_csv(out_p)
        else:
            report.save_json(out_p)
        click.echo(f"Validation report saved to: {out_p}")

    if not report.is_valid:
        sys.exit(1)


@main.command("validate-raster")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--expected-crs", default=None, help="Expected CRS string, e.g. 'EPSG:4326' or 'EPSG:6933'.")
@click.option("--out", "-o", default=None, type=click.Path(), help="Output path for validation report JSON.")
def validate_raster(file_path, expected_crs, out):
    """Inspect and validate GeoTIFF raster integrity, CRS, dimensions, and stats."""
    click.echo(f"Validating raster dataset '{file_path}'...")
    report = run_validate_raster(file_path=file_path, expected_crs=expected_crs)

    click.echo("-" * 60)
    click.echo(f"Validation Result:     {'VALID' if report.is_valid else 'INVALID'}")
    stats = report.summary_stats
    if "width" in stats and "height" in stats:
        click.echo(f"Dimensions:            {stats['width']} x {stats['height']} (Bands: {stats.get('count', 1)})")
    if "crs" in stats:
        click.echo(f"CRS:                   {stats['crs']}")
    if "resolution" in stats:
        click.echo(f"Resolution:            {stats['resolution']}")
    if "nodatavals" in stats:
        click.echo(f"Nodata Value(s):       {stats['nodatavals']}")
    if "valid_pixel_pct_sampled" in stats:
        click.echo(f"Valid Pixels:          {stats['valid_pixel_pct_sampled']}%")
    if "band_1_stats" in stats:
        b1 = stats["band_1_stats"]
        click.echo(f"Band 1 Value Range:    Min={b1['min']}, Max={b1['max']}, Mean={b1['mean']}, Std={b1['std']}")

    if report.issues:
        click.echo("-" * 60)
        click.echo("Issues:")
        for issue in report.issues:
            click.echo(f"  [{issue.severity}] {issue.category}: {issue.message}")

    if out:
        report.save_json(out)
        click.echo(f"Report saved to: {out}")

    if not report.is_valid:
        sys.exit(1)


@main.command("validate-vector")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--expected-crs", default=None, help="Expected CRS string.")
@click.option("--id-column", default=None, help="Unique identifier column name.")
@click.option("--out", "-o", default=None, type=click.Path(), help="Output path for validation report JSON.")
def validate_vector(file_path, expected_crs, id_column, out):
    """Inspect and validate vector boundaries (GeoJSON/Shapefile/GPKG) topology and CRS."""
    click.echo(f"Validating vector dataset '{file_path}'...")
    report = run_validate_vector(file_path=file_path, expected_crs=expected_crs, id_column=id_column)

    click.echo("-" * 60)
    click.echo(f"Validation Result:     {'VALID' if report.is_valid else 'INVALID'}")
    stats = report.summary_stats
    click.echo(f"Feature Count:         {stats.get('feature_count', 0)}")
    click.echo(f"CRS:                   {stats.get('crs', 'None')}")
    if "geometry_types" in stats:
        click.echo(f"Geometry Types:        {stats['geometry_types']}")
    if "total_bounds" in stats:
        click.echo(f"Total Bounds:          {stats['total_bounds']}")

    if report.issues:
        click.echo("-" * 60)
        click.echo("Issues:")
        for issue in report.issues:
            click.echo(f"  [{issue.severity}] {issue.category}: {issue.message}")

    if out:
        report.save_json(out)
        click.echo(f"Report saved to: {out}")

    if not report.is_valid:
        sys.exit(1)


@main.command("generate-manifest")
@click.option("--dir", "-d", "target_dir", default="data", type=click.Path(exists=True), help="Directory to scan for raw/processed datasets.")
@click.option("--out", "-o", default="reports/dataset_manifest.json", type=click.Path(), help="Output path for dataset manifest JSON.")
@click.option("--study-area", default="bengaluru_urban", help="Study area slug.")
def generate_manifest(target_dir, out, study_area):
    """Generate cryptographic SHA-256 manifest of datasets present on disk."""
    click.echo(f"Scanning '{target_dir}' to generate manifest...")
    manifest = DatasetManifest(study_area_id=study_area)

    base = Path(target_dir)
    scanned_count = 0
    # Walk all files except gitkeeps
    for p in base.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            rel = str(p.relative_to(base.parent if base.parent != base else base))
            ds_id = p.stem.replace(" ", "_").lower()
            try:
                rec = register_file_provenance(
                    file_path=p,
                    dataset_id=ds_id,
                    provider="Local / Ingested Dataset",
                    version="1.0",
                    validation_status="registered"
                )
                manifest.register_dataset(rec)
                scanned_count += 1
            except Exception as e:
                click.echo(f"Warning: could not register {p}: {e}")

    out_p = manifest.save(out)
    click.echo(f"Successfully generated manifest with {scanned_count} registered files: {out_p}")


@main.command("generate-grid")
@click.option("--config", "-c", required=True, type=click.Path(exists=True), help="Path to study area YAML config.")
@click.option("--out", "-o", default=None, type=click.Path(), help="Output path for grid GeoJSON or GeoPackage.")
@click.option("--format", "-f", "export_format", default="geojson", type=click.Choice(["geojson", "gpkg"]), help="Export file format.")
@click.option("--clip-mode", default="intersects", type=click.Choice(["intersects", "contains_centroid", "clip_polygon", "envelope"]), help="Grid clipping mode.")
def generate_grid(config, out, export_format, clip_mode):
    """Generate globally anchored EPSG:6933 equal-area grid for the configured study area."""
    cfg = load_study_area_config(config)
    click.echo(f"Generating global grid for study area: {cfg.study_area.name} ({cfg.study_area.id})")
    click.echo(f"Analysis CRS: {cfg.spatial.analysis_crs} | Grid Cell Size: {cfg.spatial.grid_size_m} m")

    # Load boundary (authoritative polygon if exists, or development bbox)
    boundary_gdf, status_msg = load_study_area_boundary(cfg)
    click.echo(f"Boundary Resolution: {status_msg}")

    # Determine default output path if not specified
    if not out:
        out = f"data/processed/grid_{cfg.study_area.id}_{cfg.spatial.grid_size_m}m.{export_format}"

    grid_gdf = generate_grid_for_study_area(
        boundary_geom_wgs84=boundary_gdf.geometry.iloc[0],
        cell_size_m=cfg.spatial.grid_size_m,
        analysis_crs=cfg.spatial.analysis_crs,
        clip_mode=clip_mode,
        export_path=out,
        export_format=export_format
    )

    metrics = compute_grid_distortion_metrics(grid_gdf)
    b_cov = metrics.get("domain_coverage") or metrics.get("boundary_coverage", {})

    click.echo("=" * 60)
    click.echo(f"  GRID GENERATION SUCCESSFUL")
    click.echo("=" * 60)
    click.echo(f"Total Grid Cells:      {len(grid_gdf)}")
    click.echo(f"Cell Resolution:       {cfg.spatial.grid_size_m} m x {cfg.spatial.grid_size_m} m")
    click.echo(f"Grid Cell Area:        {cfg.spatial.grid_size_m**2 / 1e6:.2f} km^2 nominal")
    if b_cov:
        click.echo(f"Domain Coverage:       Fully Inside={b_cov.get('fully_inside_count', 0)}, Partially Intersecting={b_cov.get('partially_intersecting_count', 0)}")
    geo_ratio = metrics.get("geodesic_area_ratio", {})
    if geo_ratio:
        click.echo(f"Geodesic Area Ratio:   Min={geo_ratio.get('min')}, Max={geo_ratio.get('max')}, Mean={geo_ratio.get('mean')}")
    click.echo(f"Output Saved To:       {out}")
    click.echo(f"Sample Grid Cell IDs:  {grid_gdf['grid_id'].head(3).tolist()} ... {grid_gdf['grid_id'].tail(1).tolist()}")
    click.echo("=" * 60)


@main.command("report-distortion")
@click.option("--grid", "-g", required=True, type=click.Path(exists=True), help="Path to generated grid GeoJSON or GPKG.")
@click.option("--out", "-o", default=None, type=click.Path(), help="Output path for distortion report JSON.")
def report_distortion(grid, out):
    """Compute and print geodesic area and side length distortion metrics for a grid dataset."""
    import geopandas as gpd
    click.echo(f"Loading grid from '{grid}'...")
    gdf = gpd.read_file(grid)
    metrics = compute_grid_distortion_metrics(gdf)

    click.echo("=" * 60)
    click.echo("  GRID COVERAGE & GEODESIC DISTORTION ANALYSIS")
    click.echo("=" * 60)
    click.echo(f"Total Cells Evaluated: {metrics['total_cells']}")
    click.echo(f"Nominal Cell Edge:     {metrics['nominal_cell_size_m']} m")
    click.echo(f"Nominal Area:          {metrics['nominal_area_sqm']:.1f} m^2 (1.0 km^2)")
    click.echo("-" * 60)
    ar = metrics["geodesic_area_ratio"]
    click.echo(f"Geodesic Area Ratio:   Mean={ar['mean']} (Min={ar['min']}, Max={ar['max']}, Std={ar['std']})")
    click.echo(f"Geodesic Area (m^2):   Mean={metrics['geodesic_area_sqm']['mean']} m^2 (Min={metrics['geodesic_area_sqm']['min']}, Max={metrics['geodesic_area_sqm']['max']})")
    click.echo("-" * 60)
    click.echo("Linear Edge Ratios (Geodesic Distance / Nominal 1000m):")
    er = metrics["edge_ratios"]
    click.echo(f"  South Edge Ratio:    Mean={er['south_edge']['mean']} (Min={er['south_edge']['min']}, Max={er['south_edge']['max']})")
    click.echo(f"  North Edge Ratio:    Mean={er['north_edge']['mean']} (Min={er['north_edge']['min']}, Max={er['north_edge']['max']})")
    click.echo(f"  West Edge Ratio:     Mean={er['west_edge']['mean']} (Min={er['west_edge']['min']}, Max={er['west_edge']['max']})")
    click.echo(f"  East Edge Ratio:     Mean={er['east_edge']['mean']} (Min={er['east_edge']['min']}, Max={er['east_edge']['max']})")
    cov_info = metrics.get("domain_coverage") or metrics.get("boundary_coverage")
    if cov_info:
        click.echo("-" * 60)
        click.echo("Domain Coverage Breakdown (Provisional Development Bounding Box):")
        click.echo(f"  Fully Inside:        {cov_info['fully_inside_count']}")
        click.echo(f"  Partially Inside:    {cov_info['partially_intersecting_count']}")
        click.echo(f"  Outside:             {cov_info['outside_count']}")
        click.echo(f"  Mean Fraction:       {cov_info['mean_fraction_inside']}")
    click.echo("=" * 60)

    if out:
        out_p = Path(out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        click.echo(f"Distortion report saved to: {out_p}")


@main.command("download-imerg")
@click.option("--start-date", "-s", default="2022-08-25", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", "-e", default="2022-09-10", help="End date (YYYY-MM-DD).")
@click.option("--output-dir", "-o", default="data/raw/rainfall/gpm_imerg_v07", help="Output directory for raw granules.")
@click.option("--script-path", default="scripts/download_imerg_gesdisc.sh", help="Path to write curl download script.")
def download_imerg(start_date, end_date, output_dir, script_path):
    """Generate NASA GES DISC download script and check Earthdata Login access for IMERG V07B granules."""
    from datetime import date
    from .processing.rainfall import IMERGDownloader

    s_dt = date.fromisoformat(start_date)
    e_dt = date.fromisoformat(end_date)

    click.echo("=" * 60)
    click.echo("  NASA GPM IMERG V07B GRANULE RETRIEVAL MANAGER")
    click.echo("=" * 60)
    click.echo(f"Target Event Window:   {s_dt} to {e_dt} ({(e_dt - s_dt).days + 1} daily granules)")
    click.echo(f"Product:               GPM_3IMERGDF.07 (Daily Calibrated Precipitation)")
    click.echo(f"Archive Provider:      NASA GES DISC (HTTPS / Earthdata Login)")
    click.echo(f"Destination Directory: {output_dir}")
    click.echo("-" * 60)

    # Generate curl download script
    script_file = IMERGDownloader.generate_curl_download_script(
        start_date=s_dt,
        end_date=e_dt,
        output_dir=output_dir,
        script_path=script_path
    )
    click.echo(f"Generated Shell Script: {script_file}")

    # Check authentication status
    has_token = bool(os.environ.get("EARTHDATA_TOKEN"))
    has_user = bool(os.environ.get("EARTHDATA_USERNAME") and os.environ.get("EARTHDATA_PASSWORD"))
    netrc_exists = Path("~/.netrc").expanduser().exists() or Path("~/_netrc").expanduser().exists()

    if has_token or has_user or netrc_exists:
        auth_method = "Bearer Token" if has_token else ("Basic Auth (env)" if has_user else "~/.netrc")
        click.echo(f"Authentication Detected: {auth_method}")
        click.echo("Ready to execute automated granule download.")
    else:
        click.echo("Authentication Status:  NO EARTHDATA CREDENTIALS DETECTED")
        click.echo("-" * 60)
        click.echo("NASA GES DISC restricts direct .nc4 downloads to registered users.")
        click.echo("To configure access:")
        click.echo("  1. Create a free account at: https://urs.earthdata.nasa.gov/")
        click.echo("  2. Add your credentials to ~/.netrc (or ~/_netrc on Windows):")
        click.echo("     machine urs.earthdata.nasa.gov login <USER> password <PASS>")
        click.echo("  3. Run the generated script: bash scripts/download_imerg_gesdisc.sh")
    click.echo("=" * 60)


@main.command("process-rainfall")
@click.option("--grid", "-g", default="data/processed/grid_bengaluru_urban_1000m.gpkg", type=click.Path(exists=True), help="Target 1-km grid file.")
@click.option("--rainfall-dir", "-r", default="data/raw/rainfall/gpm_imerg_v07", help="Directory containing IMERG granules.")
@click.option("--start-date", "-s", default="2022-08-25", help="Start date (YYYY-MM-DD).")
@click.option("--end-date", "-e", default="2022-09-10", help="End date (YYYY-MM-DD).")
@click.option("--method", "-m", default="centroid_lookup", type=click.Choice(["centroid_lookup", "bilinear"]), help="Spatial remapping method.")
@click.option("--out-panel", default="data/processed/rainfall_bengaluru_urban_20220825_20220910.parquet", help="Output path for spatiotemporal panel.")
@click.option("--out-summary", default="data/processed/rainfall_bengaluru_urban_event_summary.parquet", help="Output path for cell event summary.")
def process_rainfall(grid, rainfall_dir, start_date, end_date, method, out_panel, out_summary):
    """Process staged IMERG granules: unit conversion, spatial remapping, and antecedent precipitation indices."""
    from datetime import date, timedelta
    import geopandas as gpd
    import pandas as pd
    from .processing.rainfall import IMERGRasterReader, IMERGGridMapper, AntecedentPrecipitationEngine

    s_dt = date.fromisoformat(start_date)
    e_dt = date.fromisoformat(end_date)

    click.echo("=" * 60)
    click.echo("  IMERG PRECIPITATION & TEMPORAL FEATURE PIPELINE")
    click.echo("=" * 60)
    click.echo(f"Target Grid:           {grid}")
    click.echo(f"Event Window:          {s_dt} to {e_dt} ({(e_dt - s_dt).days + 1} days)")
    click.echo(f"Remapping Method:      {method}")
    click.echo("-" * 60)

    grid_gdf = gpd.read_file(grid)
    mapper = IMERGGridMapper(grid_gdf)
    click.echo(f"Grid Cells Loaded:     {len(grid_gdf)}")
    click.echo(f"Scientific Disclaimer: {mapper.SCIENTIFIC_DISCLAIMER}")
    click.echo("-" * 60)

    # Search for files
    r_dir = Path(rainfall_dir)
    daily_records = []

    cur = s_dt
    missing_dates = []
    while cur <= e_dt:
        # Search patterns for this date
        pattern = f"*{cur.strftime('%Y%m%d')}*"
        matches = list(r_dir.rglob(pattern)) if r_dir.exists() else []
        raster_file = None
        for m in matches:
            if m.suffix.lower() in [".nc4", ".hdf5", ".tif", ".tiff"] and not m.name.endswith(".xml"):
                raster_file = m
                break

        if raster_file:
            click.echo(f"[{cur}] Ingesting: {raster_file.name}")
            r_dict = IMERGRasterReader.read_imerg_raster(raster_file)
            mapped_df = mapper.remap_raster(r_dict, method=method)
            mapped_df["date"] = cur
            mapped_df = mapped_df.rename(columns={"rainfall_depth_mm": "rainfall_daily_depth_mm"})
            daily_records.append(mapped_df)
        else:
            missing_dates.append(cur)
        cur += timedelta(days=1)

    if not daily_records:
        click.echo(f"No IMERG granules found in '{rainfall_dir}' for window {s_dt} to {e_dt}.")
        click.echo(f"Total Missing Days: {len(missing_dates)}")
        click.echo("Please run 'download-imerg' or stage granules into data/raw/rainfall/gpm_imerg_v07/.")
        sys.exit(1)

    panel_raw = pd.concat(daily_records, ignore_index=True)
    click.echo(f"Total Cell-Date Observations: {len(panel_raw)}")

    # Compute antecedent metrics
    click.echo("Computing 3d, 7d, 14d antecedent accumulations and exponential decay API...")
    enriched_panel = AntecedentPrecipitationEngine.compute_antecedent_indices(panel_raw)

    # Compute cell event summary
    summary_df = AntecedentPrecipitationEngine.compute_cell_event_summary(enriched_panel)

    # Save outputs
    out_p = Path(out_panel)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    enriched_panel.to_parquet(out_p, index=False)
    click.echo(f"Saved Spatiotemporal Panel: {out_p} ({out_p.stat().st_size:,} bytes)")

    out_s = Path(out_summary)
    out_s.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_parquet(out_s, index=False)
    click.echo(f"Saved Event Summary:        {out_s} ({out_s.stat().st_size:,} bytes)")
    click.echo("=" * 60)


@main.command("compile-events")
@click.option("--grid", "-g", default="data/processed/grid_bengaluru_urban_1000m.gpkg", type=click.Path(exists=True), help="Target grid for spatial association.")
@click.option("--out-inventory", "-o", default="data/processed/flood_event_inventory_bengaluru.parquet", help="Output path for flood event inventory.")
@click.option("--out-registry", "-r", default="data/processed/flood_source_registry_bengaluru.parquet", help="Output path for source registry.")
def compile_events(grid, out_inventory, out_registry):
    """Compile, spatially associate, and validate the historical flood incident inventory for Bengaluru."""
    import geopandas as gpd
    from .processing.events import (
        get_canonical_bengaluru_2022_incidents,
        get_canonical_source_registry,
        GridIncidentAssociator,
        FloodEventInventory
    )

    click.echo("=" * 60)
    click.echo("  HISTORICAL FLOOD INCIDENT INVENTORY COMPILER")
    click.echo("=" * 60)
    click.echo(f"Target Domain Grid:    {grid}")
    click.echo(f"Output Inventory:      {out_inventory}")
    click.echo(f"Output Registry:       {out_registry}")
    click.echo("-" * 60)

    # 1. Load grid
    grid_gdf = gpd.read_file(grid)
    click.echo(f"Loaded Grid Cells:     {len(grid_gdf)} in {grid_gdf.crs}")

    # 2. Load canonical incidents and associate
    raw_incidents = get_canonical_bengaluru_2022_incidents()
    click.echo(f"Raw Incidents Loaded:  {len(raw_incidents)}")

    associator = GridIncidentAssociator(grid_gdf)
    click.echo(f"Scientific Disclaimer: {associator.SCIENTIFIC_DISCLAIMER}")
    click.echo("-" * 60)

    associated_incidents = associator.associate_all(raw_incidents, boundary_buffer_m=100.0)

    # 3. Build inventory
    inventory = FloodEventInventory(associated_incidents)
    stats = inventory.generate_summary_statistics()

    # 4. Save deliverables
    inv_file = inventory.save_parquet(out_inventory)
    click.echo(f"Saved Inventory Parquet: {inv_file} ({inv_file.stat().st_size:,} bytes)")

    sources_df = get_canonical_source_registry()
    reg_file = Path(out_registry)
    reg_file.parent.mkdir(parents=True, exist_ok=True)
    sources_df.to_parquet(reg_file, index=False)
    click.echo(f"Saved Source Registry:   {reg_file} ({reg_file.stat().st_size:,} bytes)")
    click.echo("-" * 60)

    # 5. Print summary
    click.echo("INVENTORY AUDIT SUMMARY:")
    click.echo(f"  Total Records:                 {stats['total_records']}")
    click.echo(f"  Date Range:                    {stats['date_range']['min_date']} to {stats['date_range']['max_date']}")
    click.echo("  Evidence Breakdown:")
    for k, v in stats["evidence_categories"].items():
        click.echo(f"    - {k:25s}: {v}")
    click.echo("  Spatial Accuracy Breakdown:")
    for k, v in stats["location_accuracy"].items():
        click.echo(f"    - {k:25s}: {v}")
    click.echo("  Grid Association:")
    click.echo(f"    - Associated with 1-km Grid: {stats['grid_association']['associated_with_grid']}")
    click.echo(f"    - Citywide / Unassociated:   {stats['grid_association']['unassociated_or_citywide']}")
    click.echo(f"    - Unique Cells with Events:  {stats['grid_association']['unique_grid_cells_with_incidents']}")
    click.echo(f"    - Boundary Proximity (<100m):{stats['grid_association']['boundary_proximity_flag_count']}")
    click.echo("  Corroboration Status:")
    for k, v in stats["verification_status"].items():
        click.echo(f"    - {k:25s}: {v}")
    click.echo("=" * 60)


@main.command("download-sar")
@click.option("--out-dir", "-o", default="data/raw/weather/sentinel1", help="Target directory for downloaded SAR scenes.")
@click.option("--script-dir", "-s", default="scripts", help="Directory for generated download scripts.")
@click.option("--out-registry", "-r", default="data/processed/sentinel1_scene_registry_bengaluru.parquet", help="Scene registry parquet path.")
def download_sar(out_dir, script_dir, out_registry):
    """Generate Sentinel-1A download scripts and inspect Copernicus Data Space & ASF DAAC credentials."""
    from .processing.sar import Sentinel1SceneRegistry, CANONICAL_SENTINEL1_SCENES

    click.echo("=" * 60)
    click.echo("  SENTINEL-1A SAR DATA RETRIEVAL & SCENE REGISTRY")
    click.echo("=" * 60)
    click.echo(f"Target Download Dir:   {out_dir}")
    click.echo(f"Script Export Dir:     {script_dir}")
    click.echo(f"Scene Registry Table:  {out_registry}")
    click.echo("-" * 60)

    # 1. Export scene registry
    reg_path = Sentinel1SceneRegistry.save_scene_registry_parquet(out_registry)
    click.echo(f"Saved Scene Registry:  {reg_path} ({reg_path.stat().st_size:,} bytes)")

    # 2. Generate download scripts
    cdse_sh, asf_sh = Sentinel1SceneRegistry.generate_download_scripts(output_dir=out_dir, script_dir=script_dir)
    click.echo(f"Generated CDSE Script: {cdse_sh}")
    click.echo(f"Generated ASF Script:  {asf_sh}")
    click.echo("-" * 60)

    # 3. Inspect environment credentials
    cdse_tok = os.environ.get("CDSE_TOKEN")
    netrc_exists = Path(os.path.expanduser("~/.netrc")).is_file()
    cdse_file_exists = Path(os.path.expanduser("~/.cdse_token")).is_file()

    click.echo("AUTHENTICATION STATUS:")
    click.echo(f"  CDSE $CDSE_TOKEN:    {'CONFIGURED' if cdse_tok else 'NOT FOUND (export CDSE_TOKEN=...)'}")
    click.echo(f"  CDSE ~/.cdse_token:  {'PRESENT' if cdse_file_exists else 'NOT FOUND'}")
    click.echo(f"  ASF ~/.netrc:        {'PRESENT' if netrc_exists else 'NOT FOUND (required for NASA Earthdata)'}")
    click.echo("-" * 60)

    click.echo("CANONICAL SCENES AUDITED (Orbit 165 Descending):")
    for role, s in CANONICAL_SENTINEL1_SCENES.items():
        click.echo(f"  [{role.upper()}] {s['granule_name']}")
        click.echo(f"    Acquisition: {s['acquisition_time_ist']} | Flight: {s['flight_direction']} | Size: {s['size_bytes'] / (1024**3):.2f} GB")
    click.echo("=" * 60)


@main.command("process-sar")
@click.option("--grid", "-g", default="data/processed/grid_bengaluru_urban_1000m.gpkg", type=click.Path(exists=True), help="Target domain grid.")
@click.option("--events", "-e", default="data/processed/flood_event_inventory_bengaluru.parquet", type=click.Path(exists=True), help="Historical flood inventory.")
@click.option("--worldcover", "-w", default="data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif", help="Optional ESA WorldCover GeoTIFF.")
@click.option("--out-grid-features", "-f", default="data/processed/sentinel1_grid_features_bengaluru.parquet", help="Output path for grid SAR features.")
@click.option("--out-incident-comp", "-c", default="data/processed/sentinel1_incident_comparison_bengaluru.parquet", help="Output path for incident comparison.")
def process_sar(grid, events, worldcover, out_grid_features, out_incident_comp):
    """Execute Sentinel-1A SAR backscatter differencing, candidate water/flood detection, and incident comparison."""
    from .processing.sar import process_sentinel1_pipeline

    click.echo("=" * 60)
    click.echo("  SENTINEL-1A SAR FLOOD-EVENT PROCESSING PIPELINE")
    click.echo("=" * 60)
    click.echo(f"Study Grid:            {grid}")
    click.echo(f"Flood Events:          {events}")
    click.echo(f"WorldCover Reference:  {worldcover}")
    click.echo(f"Output Grid Features:  {out_grid_features}")
    click.echo(f"Output Incident Comp:  {out_incident_comp}")
    click.echo("-" * 60)

    res = process_sentinel1_pipeline(
        study_area_grid_path=grid,
        incidents_parquet_path=events,
        worldcover_tif_path=worldcover if Path(worldcover).is_file() else None,
        output_incident_comparison_parquet=out_incident_comp,
        output_grid_features_parquet=out_grid_features
    )

    click.echo("PROCESSING COMPLETED:")
    click.echo(f"  Total Grid Cells:            {res['total_grid_cells']}")
    click.echo(f"  Incidents Evaluated:         {res['total_incidents_compared']}")
    click.echo(f"  Direct Matches (Group A/B):  {res['direct_matches']}")
    click.echo(f"  Excluded (Group C):          {res['excluded_records']}")
    click.echo("-" * 60)
    click.echo("DELIVERABLES GENERATED:")
    click.echo(f"  Scene Registry Parquet:      {res['scene_registry_parquet']} ({res['scene_registry_parquet'].stat().st_size:,} bytes)")
    click.echo(f"  Incident Comparison Parquet: {res['incident_comparison_parquet']} ({res['incident_comparison_parquet'].stat().st_size:,} bytes)")
    click.echo(f"  Grid Features Parquet:       {res['grid_features_parquet']} ({res['grid_features_parquet'].stat().st_size:,} bytes)")
    click.echo(f"  Candidate Water Mask TIF:    {res['candidate_water_mask_tif']} ({res['candidate_water_mask_tif'].stat().st_size:,} bytes)")
    click.echo(f"  Candidate Flood Change TIF:  {res['candidate_flood_change_mask_tif']} ({res['candidate_flood_change_mask_tif'].stat().st_size:,} bytes)")
    click.echo("=" * 60)


@main.command("dashboard")
@click.option("--host", "-h", default="127.0.0.1", help="Host address to bind server.")
@click.option("--port", "-p", default=8501, type=int, help="Port to listen on (default: 8501).")
@click.option("--data-dir", "-d", default="data/processed", help="Processed data directory.")
@click.option("--reports-dir", "-r", default="reports", help="Reports and manifest directory.")
def dashboard(host, port, data_dir, reports_dir):
    """Launch the interactive operational web dashboard and REST surveillance server."""
    from .dashboard.server import run_dashboard

    click.echo("=" * 60)
    click.echo("  BENGALURU URBAN FLOOD RISK INTELLIGENCE CONSOLE")
    click.echo("=" * 60)
    click.echo(f"Binding Address: http://{host}:{port}/")
    click.echo(f"Data Source:     {data_dir}")
    click.echo(f"Manifest Source: {reports_dir}")
    click.echo("-" * 60)
    click.echo("Starting server (Press Ctrl+C to stop)...")

    run_dashboard(
        host=host,
        port=port,
        data_dir=Path(data_dir),
        reports_dir=Path(reports_dir),
        blocking=True
    )


if __name__ == "__main__":
    main()

