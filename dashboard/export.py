"""Dashboard export helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .model import DashboardSnapshot
from .renderer import render_dashboard


def export_json(snapshot: DashboardSnapshot, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def export_html(snapshot: DashboardSnapshot, output: Path) -> None:
    render_dashboard(snapshot, output)
