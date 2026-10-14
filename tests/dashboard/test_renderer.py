from pathlib import Path
from html.parser import HTMLParser

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


class DashboardLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for attribute in ("href", "src"):
            if attribute in attrs:
                self.links.append(attrs[attribute])


def test_all_generated_navigation_and_asset_paths_exist(canonical_pair):
    run_dashboard(pair_dir=canonical_pair)
    output = canonical_pair / "dashboard"
    parser = DashboardLinks()
    parser.feed((output / "index.html").read_text())

    assert {"session", "progress", "plan", "timeline", "pitfalls"} <= parser.ids
    for link in parser.links:
        if link.startswith("#"):
            assert link[1:] in parser.ids
        else:
            assert (output / link).is_file(), f"Missing dashboard resource: {link}"


def test_untrusted_state_is_escaped_in_static_html(canonical_pair):
    (canonical_pair / "manifest.yaml").write_text(
        'repository:\n  name: "<script>alert(1)</script>"\n'
        'steps:\n  - id: parser\n    title: "<img src=x onerror=alert(1)>"\n'
    )
    run_dashboard(pair_dir=canonical_pair)
    content = (canonical_pair / "dashboard/index.html").read_text()

    assert "<script>alert(1)</script>" not in content
    assert "<img src=x onerror=alert(1)>" not in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
    assert "&lt;img src=x onerror=alert(1)&gt;" in content
