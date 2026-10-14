"""Command entrypoint for generating Pair Dashboard artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

if __package__:
    from .collector import collect_dashboard
    from .export import export_html, export_json
else:
    # Installed skills must run from the user's project, not the skill directory.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from dashboard.collector import collect_dashboard
    from dashboard.export import export_html, export_json


def run_dashboard(
    pair_dir: Path = Path(".pair"),
    output: Path | None = None,
    json_only: bool = False,
) -> None:
    snapshot = collect_dashboard(pair_dir)
    dashboard_dir = Path(output) if output is not None else pair_dir / "dashboard"

    export_json(snapshot, dashboard_dir / "data.json")
    if not json_only:
        export_html(snapshot, dashboard_dir / "index.html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Pair Dashboard")
    parser.add_argument("--pair-dir", type=Path, default=Path(".pair"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="Export data.json only")
    args = parser.parse_args()

    try:
        run_dashboard(
            pair_dir=args.pair_dir,
            output=args.output,
            json_only=args.json,
        )
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Dashboard generation failed: {exc}\n")

    dashboard_dir = args.output if args.output is not None else args.pair_dir / "dashboard"
    for name in (["data.json"] if args.json else ["index.html", "data.json"]):
        print((dashboard_dir / name).resolve())


if __name__ == "__main__":
    main()
