"""Poll dashboard inputs and regenerate their static projection when they change."""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .collector import collect_dashboard
from .export import export_dashboard
from .model import DashboardSnapshot, WorkspaceSnapshot
from .workspace import collect_workspace, project_paths


def _fingerprint(pair_dir: Path) -> dict[str, tuple[int, str]]:
    paths = [
        pair_dir / f"{name}.{extension}"
        for name in ("manifest", "progress", "pitfalls")
        for extension in ("yaml", "json")
    ]
    paths.append(pair_dir / "events.jsonl")
    paths.extend(path for path in (pair_dir / "sessions").glob("*") if path.suffix in {".md", ".yaml", ".json"} and path.is_file())
    paths.extend((pair_dir / "operations").glob("*.yaml"))
    files = {}
    for path in paths:
        try:
            modified = path.stat().st_mtime_ns
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except FileNotFoundError:
            # A source may be created, removed, or replaced between polling reads.
            continue
        files[str(path.relative_to(pair_dir))] = (modified, digest)
    return files


def _workspace_fingerprint(workspace: Path) -> dict[str, tuple[int, str]]:
    files = {}
    for project in project_paths(workspace):
        files[f"{project.name}/.pair/"] = (0, "directory")
        try:
            files.update({f"{project.name}/{name}": value for name, value in _fingerprint(project / ".pair").items()})
        except OSError as exc:
            files[f"{project.name}/read-error"] = (0, str(exc))
    return files


def _refresh(pair_dir: Path, output: Path, json_only: bool, workspace: Path | None = None, previous=None):
    # Parse before writing, so incomplete/invalid state preserves the last good view.
    snapshot = collect_workspace(workspace) if workspace is not None else collect_dashboard(pair_dir)
    if isinstance(snapshot, DashboardSnapshot):
        errors = [warning for warning in snapshot.warnings if warning.startswith("Cannot read ")]
        if errors:
            raise ValueError("; ".join(errors))
    else:
        for project in snapshot.projects:
            errors = [warning for warning in project.snapshot.warnings if warning.startswith("Cannot read ")] if project.snapshot is not None else []
            if errors:
                project.error = "; ".join(errors)
                project.snapshot = None
    snapshot = _with_freshness(snapshot, {"mode": "watch", "state": "fresh", "checked_at": datetime.now(timezone.utc).isoformat(), "error": None})
    if isinstance(snapshot, WorkspaceSnapshot) and isinstance(previous, WorkspaceSnapshot):
        last_valid = {project.path: project.snapshot for project in previous.projects if project.snapshot is not None}
        for project in snapshot.projects:
            if project.error and project.path in last_valid:
                project.snapshot = _with_freshness(last_valid[project.path], {
                    "mode": "watch", "state": "stale", "checked_at": snapshot.freshness["checked_at"], "error": project.error,
                })
    export_dashboard(snapshot, output, json_only)
    return snapshot


def watch_dashboard(
    pair_dir: Path = Path(".pair"),
    output: Path | None = None,
    json_only: bool = False,
    interval: float = 1.0,
    workspace: Path | None = None,
) -> None:
    """Generate once, then poll until interrupted; never modify Pair source state."""
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("Polling interval must be a finite number greater than zero")
    pair_dir = Path(pair_dir).expanduser()
    workspace = Path(workspace).expanduser() if workspace is not None else None
    default_output = workspace / ".pair/dashboard" if workspace is not None else pair_dir / "dashboard"
    dashboard_dir = Path(output).expanduser() if output is not None else default_output
    fingerprint = (lambda: _workspace_fingerprint(workspace)) if workspace is not None else (lambda: _fingerprint(pair_dir))
    observed = fingerprint()
    snapshot = _refresh(pair_dir, dashboard_dir, json_only, workspace)
    for name in (["data.json"] if json_only else ["index.html", "data.json"]):
        print((dashboard_dir / name).resolve(), flush=True)
    print(
        f"Watching {(workspace or pair_dir).resolve()} every {interval:g}s. Press Ctrl-C to stop.",
        flush=True,
    )
    pending_refresh = False
    last_error = None
    while True:
        time.sleep(interval)
        try:
            current = fingerprint()
        except OSError as exc:
            pending_refresh = True
            message = f"Dashboard watch failed: {exc}. Watching continues."
            if message != last_error:
                print(message, flush=True)
                last_error = message
                _publish_stale(snapshot, dashboard_dir, json_only, str(exc))
            continue
        changed = sorted(
            name for name in observed.keys() | current.keys()
            if observed.get(name) != current.get(name)
        )
        for name in changed:
            action = "created" if name not in observed else "removed" if name not in current else "changed"
            print(f"{name} {action}", flush=True)
        if changed:
            observed = current
            pending_refresh = True
        if not pending_refresh:
            continue
        try:
            refreshed = _refresh(pair_dir, dashboard_dir, json_only, workspace, snapshot)
        except (ValueError, OSError) as exc:
            message = f"Dashboard refresh failed: {exc}. Watching continues."
            if message != last_error:
                print(message, flush=True)
                last_error = message
                _publish_stale(snapshot, dashboard_dir, json_only, str(exc))
            continue
        if isinstance(refreshed, WorkspaceSnapshot):
            previous = {project.name: project.snapshot.current_step for project in snapshot.projects if project.snapshot is not None}
            for project in refreshed.projects:
                if project.error:
                    print(f"Project {project.name} read error: {project.error}", flush=True)
                elif previous.get(project.name) != project.snapshot.current_step:
                    print(f"{project.name} Step: {previous.get(project.name) or '(none)'} -> {project.snapshot.current_step or '(none)'}", flush=True)
        elif refreshed.current_step != snapshot.current_step:
            print(
                f"Step: {snapshot.current_step or '(none)'} -> {refreshed.current_step or '(none)'}",
                flush=True,
            )
        snapshot = refreshed
        pending_refresh = False
        last_error = None
        print("Dashboard refreshed", flush=True)


def _publish_stale(snapshot, output: Path, json_only: bool, error: str) -> None:
    stale = _with_freshness(snapshot, {"mode": "watch", "state": "stale", "checked_at": datetime.now(timezone.utc).isoformat(), "error": error})
    try:
        export_dashboard(stale, output, json_only)
    except OSError as exc:
        # If the output itself is temporarily unwritable, retry on the next poll.
        print(f"Cannot publish stale status: {exc}", flush=True)


def _with_freshness(snapshot, freshness):
    def project_view(view):
        actions = view.actions
        if freshness.get("state") == "stale":
            actions = [{"kind": "source", "title": "Resolve source read error", "detail": "The view contains the last valid state. Restore readable source records before continuing.", "command": "/pair status"}]
        return replace(view, freshness=freshness, actions=actions)

    if isinstance(snapshot, WorkspaceSnapshot):
        return replace(snapshot, freshness=freshness, projects=[
            replace(project, snapshot=project_view(project.snapshot)) if project.snapshot is not None else project
            for project in snapshot.projects
        ])
    return project_view(snapshot)
