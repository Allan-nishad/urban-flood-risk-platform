"""
Pytest Fixtures and Synthetic Test Data Generators
All datasets here are strictly synthetic and used exclusively for automated testing.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box, Polygon
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def synthetic_valid_rainfall_csv(tmp_path: Path) -> Path:
    """Creates a small valid synthetic rainfall CSV."""
    df = pd.DataFrame([
        {
            "observation_time": "2024-05-01T00:00:00Z",
            "precipitation_mm": 12.5,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "grid_id": "g1000_7381_1384",
            "station_id": "SYN_BLR_01",
            "source": "SYNTHETIC_TEST_PROVIDER",
            "quality_flag": 0
        },
        {
            "observation_time": "2024-05-01T01:00:00Z",
            "precipitation_mm": 0.0,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "grid_id": "g1000_7381_1384",
            "station_id": "SYN_BLR_01",
            "source": "SYNTHETIC_TEST_PROVIDER",
            "quality_flag": 0
        },
        {
            "observation_time": "2024-05-01T02:00:00Z",
            "precipitation_mm": 45.2,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "grid_id": "g1000_7381_1384",
            "station_id": "SYN_BLR_01",
            "source": "SYNTHETIC_TEST_PROVIDER",
            "quality_flag": 0
        }
    ])
    p = tmp_path / "synthetic_valid_rainfall.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def synthetic_corrupt_rainfall_csv(tmp_path: Path) -> Path:
    """Creates a synthetic rainfall CSV containing negative values, bad dates, and invalid coordinates."""
    df = pd.DataFrame([
        {
            "observation_time": "2024-05-01T00:00:00Z",
            "precipitation_mm": 15.0,
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        {
            # Negative rainfall
            "observation_time": "2024-05-01T01:00:00Z",
            "precipitation_mm": -8.4,
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        {
            # Bad timestamp
            "observation_time": "NOT_A_VALID_DATE",
            "precipitation_mm": 5.0,
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        {
            # Invalid latitude
            "observation_time": "2024-05-01T03:00:00Z",
            "precipitation_mm": 2.1,
            "latitude": 195.0,
            "longitude": 77.5946
        }
    ])
    p = tmp_path / "synthetic_corrupt_rainfall.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def synthetic_missing_col_csv(tmp_path: Path) -> Path:
    """Rainfall CSV missing precipitation_mm column."""
    df = pd.DataFrame([
        {"observation_time": "2024-05-01T00:00:00Z", "station_id": "SYN_01"}
    ])
    p = tmp_path / "synthetic_missing_col.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def synthetic_empty_csv(tmp_path: Path) -> Path:
    """Empty 0-byte file."""
    p = tmp_path / "synthetic_empty.csv"
    p.touch()
    return p


@pytest.fixture
def synthetic_weather_forecast_csv(tmp_path: Path) -> Path:
    """Valid and leaking forecast scenarios."""
    df = pd.DataFrame([
        {
            "forecast_issue_time": "2024-05-01T00:00:00Z",
            "valid_time": "2024-05-01T06:00:00Z",
            "precipitation_mm": 22.0,
            "forecast_model": "SYNTHETIC_GFS"
        },
        {
            # Information leakage: issue time > valid time
            "forecast_issue_time": "2024-05-01T12:00:00Z",
            "valid_time": "2024-05-01T06:00:00Z",
            "precipitation_mm": 18.0,
            "forecast_model": "SYNTHETIC_GFS"
        }
    ])
    p = tmp_path / "synthetic_forecast.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def synthetic_flood_events_csv(tmp_path: Path) -> Path:
    df = pd.DataFrame([
        {
            "event_id": "SYN_EVENT_001",
            "event_start": "2022-09-05T14:30:00Z",
            "event_end": "2022-09-06T08:00:00Z",
            "source": "BBMP_DISASTER_LOG",
            "admin_area": "Mahadevapura",
            "latitude": 12.9982,
            "longitude": 77.6958,
            "spatial_precision": "point_exact",
            "severity": "severe",
            "description": "Synthetic test event for underpass waterlogging."
        }
    ])
    p = tmp_path / "synthetic_flood_events.csv"
    df.to_csv(p, index=False)
    return p


@pytest.fixture
def synthetic_valid_raster(tmp_path: Path) -> Path:
    """Generates a small valid GeoTIFF with EPSG:4326 and mock elevation data."""
    p = tmp_path / "synthetic_dem.tif"
    width, height = 20, 20
    transform = from_origin(77.5, 13.0, 0.01, 0.01)
    data = (np.arange(width * height, dtype=np.int16).reshape((height, width)) + 800)

    with rasterio.open(
        p,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
        nodata=-32768
    ) as dst:
        dst.write(data, 1)

    return p


@pytest.fixture
def synthetic_raster_no_crs(tmp_path: Path) -> Path:
    """Generates a GeoTIFF intentionally lacking CRS metadata."""
    p = tmp_path / "synthetic_no_crs.tif"
    width, height = 10, 10
    transform = from_origin(0, 0, 1, 1)
    data = np.ones((height, width), dtype=np.uint8) * 42

    with rasterio.open(
        p,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=data.dtype,
        transform=transform
    ) as dst:
        dst.write(data, 1)

    return p


@pytest.fixture
def synthetic_valid_vector(tmp_path: Path) -> Path:
    """Generates a valid polygon GeoPackage/GeoJSON."""
    poly = box(77.55, 12.95, 77.65, 13.05)
    gdf = gpd.GeoDataFrame([{"name": "Synthetic Ward A", "geometry": poly}], crs="EPSG:4326")
    p = tmp_path / "synthetic_boundary.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return p


@pytest.fixture
def synthetic_invalid_vector(tmp_path: Path) -> Path:
    """Generates a vector dataset containing a self-intersecting bowtie polygon."""
    # Self-intersecting hourglass / bowtie polygon (invalid topology)
    bowtie = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    gdf = gpd.GeoDataFrame([{"id": 1, "geometry": bowtie}], crs="EPSG:4326")
    p = tmp_path / "synthetic_invalid_geom.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return p

