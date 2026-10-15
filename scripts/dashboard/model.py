from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PlanItem:
    """A single implementation plan item."""
    id: str
    title: str
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)
    readiness: str = "unknown"
    blocked_by: list[str] = field(default_factory=list)
    origin: str = "unknown"


@dataclass
class DashboardEvent:
    """A historical pair programming event."""
    time: str
    event: str
    actor: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    step: str | None = None


@dataclass
class PitfallItem:
    """A discovered implementation pitfall."""
    id: str
    title: str
    description: str | None = None
    severity: str | None = None
    affected_scope: list[str] = field(default_factory=list)
    resolution: str | None = None


@dataclass
class DashboardSnapshot:
    """Serializable dashboard input model."""
    project: str
    status: str = "unknown"
    current_step: str | None = None
    total_steps: int = 0
    completed_steps: int = 0
    plan: list[PlanItem] = field(default_factory=list)
    events: list[DashboardEvent] = field(default_factory=list)
    pitfalls: list[PitfallItem] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    phase: str = "unknown"
    updated_at: str | None = None
    warnings: list[str] = field(default_factory=list)
    graph: dict[str, Any] = field(default_factory=dict)
    ownership: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    knowledge: dict[str, list[str]] = field(default_factory=dict)
    actions: list[dict[str, str]] = field(default_factory=list)
    sessions: list[dict[str, Any]] = field(default_factory=list)
    freshness: dict[str, Any] = field(default_factory=lambda: {"mode": "snapshot", "state": "fresh", "error": None})
    workspace_link: str | None = None
    progress_known: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkspaceProject:
    name: str
    path: str
    artifact_dir: str
    snapshot: DashboardSnapshot | None = None
    error: str | None = None


@dataclass
class WorkspaceSnapshot:
    root: str
    projects: list[WorkspaceProject] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    freshness: dict[str, Any] = field(default_factory=lambda: {"mode": "snapshot", "state": "fresh", "error": None})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
