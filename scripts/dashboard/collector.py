from __future__ import annotations

import json
from pathlib import Path

from .model import DashboardEvent, DashboardSnapshot, PitfallItem, PlanItem


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _load_events(pair_dir: Path) -> list[DashboardEvent]:
    events: list[DashboardEvent] = []
    history = pair_dir / "events.jsonl"
    if not history.exists():
        return events
    for line in history.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(DashboardEvent(time=str(item.get("time", "")), event=str(item.get("event", "unknown")), actor=item.get("actor"), details=item))
    return events


def collect_dashboard(pair_dir: Path) -> DashboardSnapshot:
    pair_dir = Path(pair_dir)
    progress = _read_json(pair_dir / "progress.json")
    manifest = _read_json(pair_dir / "manifest.json")
    pitfalls = _read_json(pair_dir / "pitfalls.json")
    plan = [PlanItem(id=str(i.get("id", n + 1)), title=str(i.get("title", "Untitled")), status=str(i.get("status", "pending"))) for n, i in enumerate(progress.get("plan", [])) if isinstance(i, dict)]
    pitfall_items = [PitfallItem(id=str(i.get("id", n + 1)), title=str(i.get("title", "Untitled")), description=i.get("description")) for n, i in enumerate(pitfalls.get("pitfalls", [])) if isinstance(i, dict)]
    return DashboardSnapshot(project=str(manifest.get("project", pair_dir.parent.name)), status=str(progress.get("status", "unknown")), current_step=progress.get("current_step"), total_steps=len(plan), completed_steps=sum(1 for i in plan if i.status in {"done", "completed"}), plan=plan, events=_load_events(pair_dir), pitfalls=pitfall_items)
