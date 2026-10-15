from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .model import DashboardEvent, DashboardSnapshot, PitfallItem, PlanItem
from .insights import COMPLETED, analyze_plan, implementation_origin, step_consistency, validation_summary, workflow_actions
from .sessions import collect_sessions
from .state import load_mapping


def _read_state(pair_dir: Path, name: str) -> dict:
    # Canonical YAML wins; JSON is supported for early dashboard snapshots only.
    path = pair_dir / f"{name}.yaml"
    if not path.exists():
        path = pair_dir / f"{name}.json"
    return load_mapping(path) if path.exists() else {}


def _mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _items(value: object) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _step_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f'Invalid {field}: expected a non-empty string step ID; quote numeric IDs such as "01" in YAML')
    return value


def _modified_time(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _load_events(pair_dir: Path, sessions: list[dict], warnings: list[str]) -> list[DashboardEvent]:
    events: list[DashboardEvent] = []
    history = pair_dir / "events.jsonl"
    lines = history.read_text(encoding="utf-8").splitlines() if history.exists() else []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            warnings.append(f"Cannot read events.jsonl:{number}: Invalid JSON event")
            continue
        if isinstance(item, dict):
            events.append(DashboardEvent(
                time=str(item.get("time", "")),
                event=str(item.get("event", "unknown")),
                actor=item.get("actor"),
                details=item,
                step=item.get("step", item.get("current_step")),
            ))
        else:
            warnings.append(f"Cannot read events.jsonl:{number}: Expected an event mapping")
    for session in sessions:
        recorded_time = session["ended_at"] or session["started_at"]
        events.append(DashboardEvent(
            time=recorded_time or session["source_modified_at"],
            event=session["title"], actor=session["actor"], step=session["current_step"],
            details={"source": session["source"], "time_source": "recorded" if recorded_time else "file_mtime"},
        ))
    def event_order(item):
        try:
            timestamp = datetime.fromisoformat(item.time.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                return (0, 0)
            return (1, timestamp.timestamp())
        except ValueError:
            return (0, 0)
    events.sort(key=event_order)
    return events


def collect_dashboard(pair_dir: Path) -> DashboardSnapshot:
    pair_dir = Path(pair_dir)
    progress = _read_state(pair_dir, "progress")
    manifest = _read_state(pair_dir, "manifest")
    pitfalls = _read_state(pair_dir, "pitfalls")
    for name, state, key, shape in (
        ("progress", progress, "steps", dict), ("manifest", manifest, "steps", list),
        ("pitfalls", pitfalls, "pitfalls", list),
    ):
        if key in state and not isinstance(state[key], shape):
            raise ValueError(f"Invalid {name}.{key}: expected {shape.__name__}")
    sessions, warnings = collect_sessions(pair_dir)
    operations = []
    operation_sources = sorted((pair_dir / "operations").glob("*.yaml"))
    for path in operation_sources:
        try:
            operation = _mapping(load_mapping(path).get("operation"))
            if isinstance(operation.get("id"), str) and operation["id"] and isinstance(operation.get("status"), str):
                operations.append(operation)
            else:
                warnings.append(f"Cannot read {path.relative_to(pair_dir)}: Missing operation ID")
        except (OSError, ValueError) as exc:
            warnings.append(f"Cannot read {path.relative_to(pair_dir)}: {exc}")
    states = _mapping(progress.get("steps"))
    progress_known = isinstance(progress.get("steps"), dict) or isinstance(progress.get("plan"), list)
    if any(not isinstance(value, dict) for value in states.values()):
        raise ValueError("Invalid progress.steps: each step must be a mapping")
    for step_id in states:
        _step_id(step_id, "progress.steps key")
    current_step = progress.get("current_step") or None
    if progress.get("current_step") not in (None, ""):
        current_step = _step_id(progress["current_step"], "progress.current_step")
    reference_steps = manifest.get("steps", progress.get("plan", []))
    if not isinstance(reference_steps, list) or any(not isinstance(item, dict) for item in reference_steps):
        raise ValueError("Invalid plan: expected a list of step mappings")
    plan = []
    invalid_dependencies = []
    for n, item in enumerate(reference_steps):
        step_id = _step_id(item.get("id") if "steps" in manifest else item.get("id", str(n + 1)), f"plan step {n + 1} ID")
        # A Guide step in manifest does not prove Human completion.
        state = _mapping(states.get(step_id))
        status = state.get("status", "pending" if progress_known else "unknown") if "steps" in progress or "steps" in manifest else item.get("status", "pending")
        origin = state.get("origin", "unknown")
        dependencies = item.get("dependencies", [])
        if not isinstance(dependencies, list) or any(not isinstance(value, str) for value in dependencies):
            invalid_dependencies.append(step_id)
        plan.append(PlanItem(
            id=step_id, title=str(item.get("title", "Untitled")), status=str(status),
            dependencies=_strings(item.get("dependencies")),
            origin=origin if origin in ("human", "ai", "mixed") else "unknown",
        ))
    graph = analyze_plan(plan)
    for name in invalid_dependencies:
        graph["errors"].append(f"Step {name} dependencies must be a list of step IDs")
        for step in plan:
            if step.id == name:
                step.readiness = "unknown"
    validation = validation_summary(manifest, progress)
    actions = workflow_actions(manifest, progress, plan, graph, validation, operations)
    warnings.extend(step_consistency(plan, progress))
    if any("operations/" in warning for warning in warnings):
        actions.insert(0, {"kind": "recovery", "title": "Inspect unreadable takeover journals", "detail": "Operation state is incomplete; inspect the source warnings.", "command": "/pair status"})
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
    sources.extend(path for path in (pair_dir / "sessions").glob("*") if path.is_file() and path.suffix in {".md", ".yaml", ".json"})
    sources.extend(path for path in operation_sources if path.is_file())
    if (pair_dir / "events.jsonl").is_file():
        sources.append(pair_dir / "events.jsonl")
    phase = str(progress.get("phase", "unknown"))
    status = progress.get("status") or (
        "attention_required" if _mapping(progress.get("recovery")).get("state") == "attention_required"
        else progress.get("design_status") if phase == "design" else phase
    ) or "unknown"
    events = _load_events(pair_dir, sessions, warnings)
    if not progress_known:
        warnings.append("Progress step state is unavailable; completion percentage is unknown")
    return DashboardSnapshot(
        project=str(_mapping(manifest.get("repository")).get("name") or manifest.get("project") or pair_dir.resolve().parent.name),
        status=str(status),
        current_step=current_step,
        total_steps=sum(step.status not in {"skipped", "superseded"} for step in plan),
        completed_steps=sum(1 for item in plan if item.status in COMPLETED),
        plan=plan,
        events=events,
        pitfalls=pitfall_items,
        phase=phase,
        updated_at=max((_modified_time(path) for path in sources), default=None),
        warnings=warnings + [f"Missing {name} state" for name in ("manifest", "progress", "pitfalls")
                  if not any((pair_dir / f"{name}.{ext}").exists() for ext in ("yaml", "json"))],
        graph=graph, ownership=implementation_origin(plan), validation=validation, actions=actions,
        knowledge={name: [str(item) for item in _mapping(progress.get("knowledge")).get(name, [])]
                   for name in ("covered", "revisit") if isinstance(_mapping(progress.get("knowledge")).get(name, []), list)},
        sessions=sessions,
        progress_known=progress_known,
    )
