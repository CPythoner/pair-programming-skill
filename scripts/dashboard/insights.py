"""Derived workflow views; none of these calculations change source state."""

from __future__ import annotations

from collections import Counter

from .model import PlanItem

COMPLETED = {"completed", "done", "complete"}
TERMINAL_OPERATIONS = ("completed", "abandoned")


def analyze_plan(plan: list[PlanItem]) -> dict:
    counts = Counter(step.id for step in plan)
    nodes = {step.id: step for step in plan}
    errors = [f"Duplicate step ID: {name}" for name, count in counts.items() if count > 1]
    invalid = {name for name, count in counts.items() if count > 1}
    remaining = {}
    edges = []
    for step in plan:
        remaining[step.id] = set(step.dependencies)
        for dependency in step.dependencies:
            if dependency not in nodes:
                errors.append(f"Step {step.id} has missing dependency: {dependency}")
                invalid.add(step.id)
            else:
                edges.append([dependency, step.id])
    layers = []
    while remaining:
        ready = [step.id for step in plan if step.id in remaining and not remaining[step.id]]
        ready = list(dict.fromkeys(ready))
        if not ready:
            break
        layers.append(ready)
        for name in ready:
            remaining.pop(name)
        for dependencies in remaining.values():
            dependencies.difference_update(ready)
    # Unresolved nodes can be a cycle or downstream of missing/cyclic dependencies.
    if remaining:
        unresolved = set(remaining)
        cyclic = set()
        for name in unresolved:
            stack = list(nodes[name].dependencies)
            visited = set()
            while stack:
                candidate = stack.pop()
                if candidate == name:
                    cyclic.add(name)
                    break
                if candidate in visited or candidate not in unresolved:
                    continue
                visited.add(candidate)
                stack.extend(nodes[candidate].dependencies)
        if cyclic:
            errors.append("Dependency cycle: " + ", ".join(sorted(cyclic)))
        invalid.update(unresolved)
    for step in plan:
        step.blocked_by = [name for name in step.dependencies if name not in nodes or nodes[name].status not in COMPLETED]
        if step.status in COMPLETED:
            step.readiness = "completed"
        elif step.status in {"skipped", "superseded"}:
            step.readiness = "inactive"
        elif step.id in invalid:
            step.readiness = "unknown"
        elif step.status in {"active", "review"}:
            step.readiness = "waiting" if step.blocked_by else "in_progress"
        elif step.status == "pending":
            step.readiness = "waiting" if step.blocked_by else "ready"
        else:
            step.readiness = "unknown"
    return {"layers": layers, "edges": edges, "errors": errors}


def implementation_origin(plan: list[PlanItem]) -> dict:
    completed = [step for step in plan if step.status in COMPLETED]
    counts = dict.fromkeys(("human", "ai", "mixed", "unknown"), 0)
    for step in completed:
        counts[step.origin if step.origin in counts else "unknown"] += 1
    total = len(completed)
    return {
        "unit": "completed_steps", "total": total, "counts": counts,
        "percentages": {name: round(count / total * 100, 1) if total else None for name, count in counts.items()},
        "known": total - counts["unknown"],
        "coverage": round((total - counts["unknown"]) / total * 100, 1) if total else None,
        "source": "progress.steps[*].origin",
    }


def validation_summary(manifest: dict, progress: dict) -> dict:
    validation = manifest.get("validation") or {}
    validation = validation if isinstance(validation, dict) else {}
    records = validation.get("last_results") or []
    records = records if isinstance(records, list) else []
    statuses = [item.get("status") if isinstance(item, dict) else None for item in records]
    status = "unknown"
    if "failed" in statuses:
        status = "failed"
    elif "limited" in statuses:
        status = "limited"
    elif statuses and all(value == "passed" for value in statuses):
        status = "passed"
    commands = validation.get("commands") or []
    return {
        "status": status, "recorded_results": len(records),
        "commands": [str(command) for command in commands] if isinstance(commands, list) else [],
        "source": "manifest.validation.last_results",
    }


def step_consistency(plan: list[PlanItem], progress: dict) -> list[str]:
    """Report contradictory pointers without guessing which source value to change."""
    issues = []
    current = progress.get("current_step")
    ids = {step.id for step in plan}
    in_progress = [step.id for step in plan if step.status in {"active", "review"}]
    if current and current not in ids:
        issues.append(f"Current step {current!r} is missing from the plan; reconcile Pair state")
    elif current:
        other = [name for name in in_progress if name != current]
        if other:
            issues.append(f"In-progress steps {', '.join(other)} differ from current step {current!r}; reconcile Pair state")
    elif in_progress:
        issues.append(f"No current step is recorded, but steps {', '.join(in_progress)} are in progress; reconcile Pair state")
    incomplete = [step.id for step in plan if step.status not in COMPLETED | {"skipped", "superseded"}]
    if progress.get("phase") == "complete" and incomplete:
        issues.append(f"Workflow phase is complete, but steps {', '.join(incomplete)} are incomplete; reconcile Pair state")
    return issues


def workflow_actions(manifest: dict, progress: dict, plan: list[PlanItem], graph: dict, validation: dict, operations: list[dict]) -> list[dict[str, str]]:
    actions = []

    def add(kind, title, detail, command):
        actions.append({"kind": kind, "title": title, "detail": detail, "command": command})

    recovery = progress.get("recovery") or {}
    if isinstance(recovery, dict) and recovery.get("state") == "attention_required":
        add("recovery", "Reconcile workspace state", str(recovery.get("classification") or "Recovery needs attention"), "/pair status")
    active = progress.get("active_operation") or {}
    journals = {item.get("id"): item for item in operations}
    pending = [item for item in operations if item.get("status") not in TERMINAL_OPERATIONS]
    if isinstance(active, dict) and isinstance(active.get("id"), str) and active["id"]:
        journal = journals.get(active["id"])
        if journal and journal.get("status") in TERMINAL_OPERATIONS:
            add("recovery", "Reconcile stale takeover metadata", str(active["id"]), "/pair status")
        elif not journal and active.get("status") not in TERMINAL_OPERATIONS:
            pending.append(active)
    for item in pending:
        add("takeover", "Reconcile unfinished takeover", f"{item.get('id', 'Unknown')} · {item.get('status', 'unknown')}", "/pair status")
    design = manifest.get("design") or {}
    design = design if isinstance(design, dict) else {}
    design_status = design.get("status") or progress.get("design_status")
    if design_status == "awaiting_approval" or (
        design_status == "approved" and design.get("revision") != design.get("approved_revision")
    ):
        add("approval", "Review pending design approval", f"Design revision {design.get('revision', progress.get('design_revision', 'unknown'))}", "/pair explain design")
    if validation["status"] == "failed":
        add("validation", "Review recorded validation failures", "A recorded check failed; inspect its evidence before continuing.", "/pair review")
    if graph["errors"]:
        add("plan", "Resolve plan dependencies", "; ".join(graph["errors"]), "/pair rebase-plan")
    issues = step_consistency(plan, progress)
    if issues:
        add("recovery", "Reconcile step progress", "; ".join(issues), "/pair status")
    if not actions and progress.get("phase") != "guided_reconstruction":
        add("phase", "Inspect workflow phase", f"Recorded phase: {progress.get('phase') or 'unknown'}. Check phase and validation evidence before starting a guided step.", "/pair status")
    if not actions:
        current = next((step for step in plan if step.id == progress.get("current_step")), None)
        if current and current.blocked_by:
            add("plan", "Resolve current-step prerequisites", "Waiting on " + ", ".join(current.blocked_by), "/pair status")
        elif current and current.readiness == "in_progress":
            command = "review" if current.status == "review" else "next"
            add("step", "Continue current step", current.title, f"/pair {command} {current.id}")
        else:
            ready = next((step for step in plan if step.readiness == "ready"), None)
            if ready:
                add("step", "Next ready step", ready.title, f"/pair next {ready.id}")
            else:
                add("status", "Inspect workflow status", "No ready step is recorded. Review dependencies and completion evidence.", "/pair status")
    return actions
