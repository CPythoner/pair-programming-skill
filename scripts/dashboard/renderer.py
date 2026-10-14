from __future__ import annotations

import html
from pathlib import Path

from .model import DashboardSnapshot


def render_dashboard(snapshot: DashboardSnapshot, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_render_html(snapshot), encoding="utf-8")


def _render_html(snapshot: DashboardSnapshot) -> str:
    plan = "".join(f"<li>{html.escape(item.title)} - {html.escape(item.status)}</li>" for item in snapshot.plan)
    events = "".join(f"<li>{html.escape(item.time)} - {html.escape(item.event)}</li>" for item in snapshot.events)
    pitfalls = "".join(f"<li>{html.escape(item.title)}</li>" for item in snapshot.pitfalls)
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>Pair Dashboard</title></head><body><h1>Pair Programming Dashboard</h1><h2>{html.escape(snapshot.status)}</h2><h3>Plan</h3><ul>{plan}</ul><h3>Timeline</h3><ul>{events}</ul><h3>Pitfalls</h3><ul>{pitfalls}</ul></body></html>"""
