"""Static HTML renderer for Pair Dashboard snapshots."""

from __future__ import annotations

import html
from pathlib import Path

from .model import DashboardSnapshot


def render_dashboard(snapshot: DashboardSnapshot, output: Path) -> None:
    """Render a self-contained dashboard HTML file."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_render_html(snapshot), encoding="utf-8")


def _render_html(snapshot: DashboardSnapshot) -> str:
    plan = "".join(
        f"<li class='{html.escape(item.status)}'>{html.escape(item.title)}</li>"
        for item in snapshot.plan
    )
    events = "".join(
        f"<li>{html.escape(event.timestamp)} - {html.escape(event.event)}</li>"
        for event in snapshot.events
    )
    pitfalls = "".join(
        f"<li>{html.escape(item.title)}</li>" for item in snapshot.pitfalls
    )

    return f"""<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>Pair Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; background:#f6f7f9; }}
.card {{ background:white; border-radius:12px; padding:20px; margin-bottom:16px; }}
.done {{ color:green; }}
.active {{ color:#2563eb; }}
</style>
</head>
<body>
<h1>Pair Programming Dashboard</h1>
<div class='card'>
<h2>Status</h2>
<p>{html.escape(snapshot.status)}</p>
<p>Generated: {html.escape(snapshot.generated_at)}</p>
</div>
<div class='card'><h2>Plan</h2><ul>{plan}</ul></div>
<div class='card'><h2>Timeline</h2><ul>{events}</ul></div>
<div class='card'><h2>Pitfalls</h2><ul>{pitfalls}</ul></div>
</body>
</html>"""
