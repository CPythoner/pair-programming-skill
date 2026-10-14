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


@dataclass
class DashboardEvent:
    """A historical pair programming event."""
    time: str
    event: str
    actor: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PitfallItem:
    """A discovered implementation pitfall."""
    id: str
    title: str
    description: str | None = None


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
