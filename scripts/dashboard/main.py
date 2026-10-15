"""Command entrypoint for generating Pair Dashboard artifacts."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

if __package__:
    from .collector import collect_dashboard
    from .export import export_dashboard
    from .watch import watch_dashboard
    from .workspace import collect_workspace
else:
    # Installed skills must run from the user's project, not the skill directory.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from dashboard.collector import collect_dashboard
    from dashboard.export import export_dashboard
    from dashboard.watch import watch_dashboard
    from dashboard.workspace import collect_workspace


def run_dashboard(
    pair_dir: Path = Path(".pair"),
    output: Path | None = None,
    json_only: bool = False,
) -> None:
    pair_dir = Path(pair_dir).expanduser()
    snapshot = collect_dashboard(pair_dir)
    dashboard_dir = Path(output).expanduser() if output is not None else pair_dir / "dashboard"

    export_dashboard(snapshot, dashboard_dir, json_only)


def run_workspace_dashboard(workspace: Path, output: Path | None = None, json_only: bool = False) -> None:
    workspace = Path(workspace).expanduser()
    snapshot = collect_workspace(workspace)
    export_dashboard(snapshot, Path(output).expanduser() if output is not None else workspace / ".pair/dashboard", json_only)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Pair Dashboard")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--pair-dir", type=Path)
    inputs.add_argument("--workspace", type=Path, help="Scan direct child projects containing .pair")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="Export JSON artifacts only, including session history")
    parser.add_argument("--watch", action="store_true", help="Poll Pair state and regenerate on changes")
    parser.add_argument("--interval", type=float, default=1.0, help="Watch polling interval in seconds (default: 1)")
    args = parser.parse_args()
    for name in ("pair_dir", "workspace", "output"):
        value = getattr(args, name)
        if value is not None:
            setattr(args, name, value.expanduser())
    if not math.isfinite(args.interval) or args.interval <= 0:
        parser.error("--interval must be a finite number greater than zero")

    try:
        if args.watch:
            watch_dashboard(
                pair_dir=args.pair_dir or Path(".pair"),
                output=args.output,
                json_only=args.json,
                interval=args.interval,
                workspace=args.workspace,
            )
        elif args.workspace is not None:
            run_workspace_dashboard(args.workspace, output=args.output, json_only=args.json)
        else:
            run_dashboard(
                pair_dir=args.pair_dir or Path(".pair"),
                output=args.output,
                json_only=args.json,
            )
    except KeyboardInterrupt:
        if args.watch:
            print("\nDashboard watch stopped.")
            return
        parser.exit(130, "\nDashboard generation interrupted.\n")
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Dashboard generation failed: {exc}\n")

    default_output = args.workspace.expanduser() / ".pair/dashboard" if args.workspace is not None else (args.pair_dir or Path(".pair")) / "dashboard"
    dashboard_dir = args.output if args.output is not None else default_output
    for name in (["data.json"] if args.json else ["index.html", "data.json"]):
        print((dashboard_dir / name).resolve())


if __name__ == "__main__":
    main()
