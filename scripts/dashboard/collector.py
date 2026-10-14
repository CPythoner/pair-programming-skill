from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .model import DashboardEvent, DashboardSnapshot, PitfallItem, PlanItem


def _read_state(pair_dir: Path, name: str) -> dict:
    # Canonical YAML wins; JSON is supported for early dashboard snapshots only.
    path = pair_dir / f"{name}.yaml"
    if path.exists():
        try:
            import yaml
        except ImportError as exc:
            requirements = Path(__file__).with_name("requirements.txt")
            raise ValueError(
                "YAML state requires PyYAML. Install it with "
                f'python3 -m pip install -r "{requirements}"'
            ) from exc
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    else:
        path = pair_dir / f"{name}.json"
        if not path.exists():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Expected a state mapping in {path}")
    version = value.get("schema_version", value.get("version", 1))
    if version != 1:
        raise ValueError(f"Unsupported schema version {version!r} in {path}")
    return value


def _mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _items(value: object) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _modified_time(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _load_events(pair_dir: Path) -> list[DashboardEvent]:
    events: list[DashboardEvent] = []
    history = pair_dir / "events.jsonl"
    lines = history.read_text(encoding="utf-8").splitlines() if history.exists() else []
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(DashboardEvent(
                time=str(item.get("time", "")),
                event=str(item.get("event", "unknown")),
                actor=item.get("actor"),
                details=item,
                step=item.get("step", item.get("current_step")),
            ))
    for path in sorted((pair_dir / "sessions").glob("*.md")):
        summary = path.read_text(encoding="utf-8")
        step = re.search(r"(?m)^- Current step:[ \t]*([^\n]*)", summary)
        events.append(DashboardEvent(
            time=_modified_time(path),
            event=f"Session summary: {path.stem}",
            step=(step.group(1).strip() or None) if step else None,
            details={"source": str(path.relative_to(pair_dir)), "time_source": "file_mtime"},
        ))
    events.sort(key=lambda item: item.time)
    return events


def collect_dashboard(pair_dir: Path) -> DashboardSnapshot:
    pair_dir = Path(pair_dir)
    progress = _read_state(pair_dir, "progress")
    manifest = _read_state(pair_dir, "manifest")
    pitfalls = _read_state(pair_dir, "pitfalls")
    states = _mapping(progress.get("steps"))
    reference_steps = manifest.get("steps", progress.get("plan", []))
    plan = []
    for n, item in enumerate(_items(reference_steps)):
        step_id = str(item.get("id", n + 1))
        # A Guide step in manifest does not prove Human completion.
        state = _mapping(states.get(step_id))
        status = state.get("status", "pending") if "steps" in manifest else item.get("status", "pending")
        plan.append(PlanItem(id=step_id, title=str(item.get("title", "Untitled")), status=str(status)))
    pitfall_items = [
        PitfallItem(
            id=str(item.get("id", n + 1)),
            title=str(item.get("title", "Untitled")),
            description=item.get("description", item.get("symptom")),
            severity=item.get("severity"),
            affected_scope=_strings(item.get("affected_files")) + _strings(item.get("affected_symbols")),
            resolution=item.get("resolution", item.get("workaround")),
        )
        for n, item in enumerate(_items(pitfalls.get("pitfalls")))
    ]
    sources = [
        pair_dir / f"{name}.{extension}"
        for name in ("manifest", "progress", "pitfalls")
        for extension in ("yaml", "json")
        if (pair_dir / f"{name}.{extension}").is_file()
        and (extension == "yaml" or not (pair_dir / f"{name}.yaml").exists())
    ]
    sources.extend(path for path in (pair_dir / "sessions").glob("*.md") if path.is_file())
    if (pair_dir / "events.jsonl").is_file():
        sources.append(pair_dir / "events.jsonl")
    phase = str(progress.get("phase", "unknown"))
    status = progress.get("status") or (
        "attention_required" if _mapping(progress.get("recovery")).get("state") == "attention_required"
        else progress.get("design_status") if phase == "design" else phase
    ) or "unknown"
    return DashboardSnapshot(
        project=str(_mapping(manifest.get("repository")).get("name") or manifest.get("project") or pair_dir.resolve().parent.name),
        status=str(status),
        current_step=progress.get("current_step"),
        total_steps=len(plan),
        completed_steps=sum(1 for item in plan if item.status in {"done", "completed"}),
        plan=plan,
        events=_load_events(pair_dir),
        pitfalls=pitfall_items,
        phase=phase,
        updated_at=max((_modified_time(path) for path in sources), default=None),
        warnings=[f"Missing {name} state" for name in ("manifest", "progress", "pitfalls")
                  if not any((pair_dir / f"{name}.{ext}").exists() for ext in ("yaml", "json"))],
    )
