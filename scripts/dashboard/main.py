"""Command entrypoint for generating Pair Dashboard artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from .collector import collect_dashboard
from .export import export_html, export_json


def run_dashboard(
    pair_dir: Path = Path('.pair'),
    output: Path | None = None,
    json_only: bool = False,
) -> None:
    snapshot = collect_dashboard(pair_dir)
    dashboard_dir = output or pair_dir / 'dashboard'

    export_json(snapshot, dashboard_dir / 'data.json')
    if not json_only:
        export_html(snapshot, dashboard_dir / 'index.html')


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate Pair Dashboard')
    parser.add_argument('--pair-dir', type=Path, default=Path('.pair'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    run_dashboard(
        pair_dir=args.pair_dir,
        output=args.output,
        json_only=args.json,
    )


if __name__ == '__main__':
    main()
