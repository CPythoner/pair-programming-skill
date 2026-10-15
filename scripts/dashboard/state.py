"""Versioned state parsing shared by read-only dashboard collectors."""

from __future__ import annotations

import json
from pathlib import Path


def load_mapping(path: Path, content: str | None = None, *, yaml_content: bool = False) -> dict:
    content = path.read_text(encoding="utf-8") if content is None else content
    if path.suffix == ".json" and not yaml_content:
        try:
            value = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    else:
        try:
            import yaml
        except ImportError as exc:
            requirements = Path(__file__).with_name("requirements.txt")
            raise ValueError(f'YAML state requires PyYAML. Install it with python3 -m pip install -r "{requirements}"') from exc
        try:
            value = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Expected a state mapping in {path}")
    version = value.get("schema_version", value.get("version", 1))
    if type(version) is not int or version != 1:
        raise ValueError(f"Unsupported schema version {version!r} in {path}")
    return value
