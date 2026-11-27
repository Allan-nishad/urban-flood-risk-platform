"""
Tests for Historical Flood Event Inventory, Evidence Classification, and Grid Association.
Enforces strict scientific provenance, spatial uncertainty handling, and safeguards
against false precision and fabricated flood labels.
"""

from datetime import date
from pathlib import Path
import pandas as pd
import geopandas as gpd
import pytest

from floodrisk.processing.events import (
    EvidenceCategory,
    LocationAccuracy,
    VerificationStatus,
    FloodIncidentRecord,
    GridIncidentAssociator,
    FloodEventInventory,
    get_canonical_source_registry,
    get_canonical_bengaluru_2022_incidents
)


@pytest.fixture
def sample_grid_gdf():
    """Load the official 1,170-cell Bengaluru Urban grid."""
    grid_path = Path("data/processed/grid_bengaluru_urban_1000m.gpkg")
    if not grid_path.is_file():
        pytest.skip("Grid file not generated")
    return gpd.read_file(grid_path)


def test_unique_incident_ids():
    """Verify that all canonical incidents have globally unique IDs."""
    incidents = get_canonical_bengaluru_2022_incidents()
    ids = [i.event_id for i in incidents]
    assert len(ids) == len(set(ids)), "All incident event_ids must be unique"

    inventory = FloodEventInventory()
    inventory.add_record(incidents[0])
    with pytest.raises(ValueError, match="Duplicate event_id"):
        inventory.add_record(incidents[0])


def test_valid_coordinate_ranges():
    """Verify that all georeferenced coordinates fall within valid Bengaluru bounds."""
    incidents = get_canonical_bengaluru_2022_incidents()
    for inc in incidents:
        if inc.latitude is not None and inc.longitude is not None:
            assert 12.80 <= inc.latitude <= 13.20, f"Latitude {inc.latitude} outside Bengaluru domain for {inc.event_id}"
            assert 77.40 <= inc.longitude <= 77.80, f"Longitude {inc.longitude} outside Bengaluru domain for {inc.event_id}"


def test_missing_location_handling(sample_grid_gdf):
    """
    CRITICAL SAFEGUARD: City-level or district-level records MUST NEVER be assigned to a specific grid cell.
    Their grid_id must remain None.
    """
    associator = GridIncidentAssociator(sample_grid_gdf)
    city_rec = FloodIncidentRecord(
        event_id="ev_test_citywide",
        event_date=date(2022, 9, 5),
        location_name="Bengaluru Urban Citywide",
        evidence_category=EvidenceCategory.RAINFALL_ONLY,
        location_accuracy=LocationAccuracy.DISTRICT_OR_CITY_LEVEL,
        spatial_uncertainty_m=15000.0,
        event_description="Citywide meteorological summary",
        source_organisation="KSNDMC",
        source_title="Rainfall Bulletin",
        source_url="https://ksndmc.karnataka.gov.in",
        source_publication_date=date(2022, 9, 5),
        retrieval_date=date(2026, 11, 5),
        evidence_reference="Overview"
    )
    res = associator.associate_incident(city_rec)
    assert res.grid_id is None, "Citywide record must not receive a grid_id"
    assert res.boundary_proximity_flag is False


def test_grid_association_and_boundary_ambiguity(sample_grid_gdf):
    """Verify point-in-polygon assignment and boundary proximity threshold flagging."""
    associator = GridIncidentAssociator(sample_grid_gdf)
    incidents = get_canonical_bengaluru_2022_incidents()
    associated = associator.associate_all(incidents, boundary_buffer_m=100.0)

    # Rainbow Drive Layout check
    rd_rec = next(r for r in associated if r.event_id == "ev_20220905_002")
    assert rd_rec.grid_id == "g1000_7496_1633"
    assert rd_rec.boundary_proximity_flag is False  # dist is 257.2 m > 100 m

    # HSR Layout check (dist = 1.8 m, very close to boundary)
    hsr_rec = next(r for r in associated if r.event_id == "ev_20220905_010")
    assert hsr_rec.grid_id == "g1000_7491_1633"
    assert hsr_rec.boundary_proximity_flag is True, "HSR Layout (dist 1.8m) must have boundary proximity flagged"
    assert hsr_rec.distance_to_cell_boundary_m < 10.0


def test_rainfall_only_never_positive_flood_label():
    """
    CRITICAL METHODOLOGICAL TEST:
    Rainfall-only records must be classified as RAINFALL_ONLY and never as confirmed inundation.
    """
    incidents = get_canonical_bengaluru_2022_incidents()
    rainfall_records = [r for r in incidents if r.evidence_category == EvidenceCategory.RAINFALL_ONLY]
    assert len(rainfall_records) >= 2

    for r in rainfall_records:
        assert r.evidence_category != EvidenceCategory.CONFIRMED_INUNDATION
        assert r.evidence_category != EvidenceCategory.REPORTED_WATERLOGGING
        assert "Rainfall-only record" in r.review_notes or "must NEVER be converted" in r.review_notes


def test_unreported_cells_no_automatic_negative_labels(sample_grid_gdf):
    """
    CRITICAL ETHICAL/SCIENTIFIC TEST:
    Absence of a flood report in a 1-km cell does NOT prove that the cell was dry.
    Verify that unassociated cells are NOT assigned negative (0) labels.
    """
    associator = GridIncidentAssociator(sample_grid_gdf)
    incidents = associator.associate_all(get_canonical_bengaluru_2022_incidents())
    inventory = FloodEventInventory(incidents)
    df_events = inventory.to_dataframe()

    reported_cells = set(df_events["grid_id"].dropna().unique())
    all_grid_cells = set(sample_grid_gdf["grid_id"].unique())

    # There are 1,170 total cells and ~17 reported cells
    assert len(reported_cells) < len(all_grid_cells)
    unreported_cells = all_grid_cells - reported_cells
    assert len(unreported_cells) > 1000

    # Ensure the inventory dataframe contains ONLY reported incidents and does NOT manufacture negative labels
    assert "flood_label" not in df_events.columns
    assert set(df_events["grid_id"].dropna()).issubset(reported_cells)


def test_source_provenance_and_urls():
    """Verify that every incident has complete and valid source provenance."""
    incidents = get_canonical_bengaluru_2022_incidents()
    for inc in incidents:
        assert inc.source_organisation != ""
        assert inc.source_title != ""
        assert inc.source_url.startswith("http")
        assert inc.source_publication_date is not None
        assert inc.retrieval_date is not None


def test_deliverable_parquet_files_integrity():
    """Verify the saved event inventory and source registry Parquet files."""
    inv_path = Path("data/processed/flood_event_inventory_bengaluru.parquet")
    reg_path = Path("data/processed/flood_source_registry_bengaluru.parquet")

    assert inv_path.is_file(), "flood_event_inventory_bengaluru.parquet must exist"
    assert reg_path.is_file(), "flood_source_registry_bengaluru.parquet must exist"

    df_inv = pd.read_parquet(inv_path)
    assert len(df_inv) == 21
    assert df_inv["event_id"].nunique() == 21
    assert "evidence_category" in df_inv.columns
    assert "grid_id" in df_inv.columns
    assert "distance_to_cell_boundary_m" in df_inv.columns

    df_reg = pd.read_parquet(reg_path)
    assert len(df_reg) >= 5
    assert "source_id" in df_reg.columns
    assert "organisation" in df_reg.columns
    assert "reliability_tier" in df_reg.columns

