"""
Operational Web Dashboard Module for Urban Flood Risk Platform.
Provides lightweight HTTP REST server and interactive Leaflet-based visualization console.
"""

from .server import run_dashboard, load_dashboard_data, DashboardRequestHandler

__all__ = ["run_dashboard", "load_dashboard_data", "DashboardRequestHandler"]

