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
            events.append(
                DashboardEvent(
                    time=str(item.get("time", "")),
                    event=str(item.get("event", "unknown")),
                    actor=item.get("actor"),
                    details=item,
                )
            )
    return events


def collect_dashboard(pair_dir: Path) -> DashboardSnapshot:
    """Collect dashboard data from a project's .pair directory.

    The collector is intentionally tolerant: older pair sessions can still be
    rendered when optional state files do not exist.
    """

    pair_dir = Path(pair_dir)
    progress = _read_json(pair_dir / "progress.json")
    manifest = _read_json(pair_dir / "manifest.json")
    pitfalls = _read_json(pair_dir / "pitfalls.json")

    raw_plan = progress.get("plan", [])
    plan = [
        PlanItem(
            id=str(item.get("id", index + 1)),
            title=str(item.get("title", "Untitled")),
            status=str(item.get("status", "pending")),
        )
        for index, item in enumerate(raw_plan)
        if isinstance(item, dict)
    ]

    raw_pitfalls = pitfalls.get("pitfalls", [])
    pitfall_items = [
        PitfallItem(
            id=str(item.get("id", index + 1)),
            title=str(item.get("title", "Untitled")),
            description=item.get("description"),
        )
        for index, item in enumerate(raw_pitfalls)
        if isinstance(item, dict)
    ]

    completed = sum(1 for item in plan if item.status in {"done", "completed"})

    return DashboardSnapshot(
        project=str(manifest.get("project", pair_dir.parent.name)),
        status=str(progress.get("status", "unknown")),
        current_step=progress.get("current_step"),
        total_steps=len(plan),
        completed_steps=completed,
        plan=plan,
        events=_load_events(pair_dir),
        pitfalls=pitfall_items,
    )
