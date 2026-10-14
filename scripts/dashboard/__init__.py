"""Pair Dashboard generation utilities."""

from pathlib import Path

from .collector import collect_dashboard


def run_dashboard(
    pair_dir: Path = Path(".pair"),
    output: Path | None = None,
    json_only: bool = False,
) -> None:
    # Import lazily so `python -m scripts.dashboard.main` does not pre-load main.
    from .main import run_dashboard as generate

    generate(pair_dir=pair_dir, output=output, json_only=json_only)

__all__ = ["collect_dashboard", "run_dashboard"]
