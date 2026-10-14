"""Pair programming dashboard data collection utilities."""

from .collector import collect_dashboard
from .model import DashboardSnapshot

__all__ = ["DashboardSnapshot", "collect_dashboard"]
