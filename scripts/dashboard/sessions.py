"""Read session facts; generated history never becomes a source of truth."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from .state import load_mapping


def _timestamp(value: object) -> str | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid session timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"Session timestamp must include timezone: {value}")
    return parsed.isoformat()


def collect_sessions(pair_dir: Path) -> tuple[list[dict], list[str]]:
    records, warnings = [], []
    paths = sorted(path for path in (pair_dir / "sessions").glob("*") if path.suffix in {".md", ".yaml", ".json"} and path.is_file())
    for path in paths:
        source = str(path.relative_to(pair_dir))
        try:
            metadata = None
            content = path.read_text(encoding="utf-8")
            if path.suffix != ".md":
                metadata = load_mapping(path, content)
            elif content.startswith("---\n"):
                closing = content.find("\n---\n", 4)
                if closing < 0:
                    raise ValueError("Session frontmatter is not closed")
                metadata = load_mapping(path, content[4:closing], yaml_content=True)
            if metadata is None:
                step = re.search(r"(?m)^- Current step:[ \t]*([^\n]*)", content)
                record = {
                    "id": "legacy-" + hashlib.sha256(source.encode()).hexdigest()[:20],
                    "title": f"Session summary: {path.stem}", "feature_slug": None,
                    "status": "unknown", "started_at": None, "ended_at": None,
                    "current_step": (step.group(1).strip() or None) if step else None,
                    "actor": None, "legacy": True,
                }
            else:
                allowed = {"schema_version", "version", "id", "title", "feature_slug", "status", "started_at", "ended_at", "current_step", "actor"}
                if not ("schema_version" in metadata or "version" in metadata):
                    raise ValueError("Session metadata requires schema_version")
                if set(metadata) - allowed:
                    raise ValueError("Unexpected session metadata fields: " + ", ".join(sorted(str(key) for key in set(metadata) - allowed)))
                required = ("id", "title", "feature_slug", "status", "started_at")
                if any(key not in metadata for key in required):
                    raise ValueError("Session metadata requires id, title, feature_slug, status and started_at")
                if not isinstance(metadata["id"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", metadata["id"]):
                    raise ValueError("Session ID must be a stable identifier (letters, digits, dot, underscore or hyphen)")
                if metadata["status"] not in ("active", "completed", "abandoned", "unknown"):
                    raise ValueError(f"Invalid session status: {metadata['status']}")
                if not all(isinstance(metadata[key], str) and metadata[key] for key in ("title", "feature_slug")):
                    raise ValueError("Session title and feature_slug must be nonempty strings")
                if any(metadata.get(key) is not None and not isinstance(metadata[key], str) for key in ("actor", "current_step")):
                    raise ValueError("Session actor and current_step must be strings or null")
                record = {key: str(metadata[key]) for key in ("id", "title", "feature_slug", "status")}
                record.update(
                    started_at=_timestamp(metadata.get("started_at")),
                    ended_at=_timestamp(metadata.get("ended_at")),
                    current_step=str(metadata["current_step"]) if metadata.get("current_step") else None,
                    actor=str(metadata["actor"]) if metadata.get("actor") else None,
                    legacy=False,
                )
                if record["started_at"] and record["ended_at"] and datetime.fromisoformat(record["ended_at"]) < datetime.fromisoformat(record["started_at"]):
                    raise ValueError("Session ended_at precedes started_at")
            record.update(source=source, source_modified_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat())
            record["history_file"] = "history/session-" + hashlib.sha256(record["id"].encode()).hexdigest() + ".json"
            records.append(record)
        except (OSError, ValueError) as exc:
            warnings.append(f"Cannot read {source}: {exc}")
    counts = Counter(record["id"] for record in records)
    for record in records:
        if counts[record["id"]] > 1:
            record["history_file"] = None
    warnings.extend(f"Duplicate session ID: {name}; history export disabled for conflicting records" for name, count in counts.items() if count > 1)
    records.sort(key=lambda record: (
        bool(record["ended_at"] or record["started_at"]),
        datetime.fromisoformat(record["ended_at"] or record["started_at"]).timestamp() if record["ended_at"] or record["started_at"] else 0,
        record["source"],
    ), reverse=True)
    return records, warnings
