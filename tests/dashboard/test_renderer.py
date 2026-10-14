from pathlib import Path

from scripts.dashboard.main import run_dashboard


def test_dashboard_generates_html_and_json(tmp_path: Path) -> None:
    pair_dir = tmp_path / ".pair"
    pair_dir.mkdir()

    output = tmp_path / "dashboard"
    run_dashboard(pair_dir=pair_dir, output=output)

    assert (output / "data.json").exists()
    assert (output / "index.html").exists()


def test_dashboard_json_only(tmp_path: Path) -> None:
    pair_dir = tmp_path / ".pair"
    pair_dir.mkdir()

    output = tmp_path / "dashboard"
    run_dashboard(pair_dir=pair_dir, output=output, json_only=True)

    assert (output / "data.json").exists()
    assert not (output / "index.html").exists()
