# Pair Dashboard

Generate a static Pair Programming Control Center from `.pair` state.

Requires Python 3.10+. Install YAML support in the Python environment used for generation:

```bash
python3 -m pip install -r /absolute/path/to/pair-programming/scripts/dashboard/requirements.txt
```

## Usage

```bash
python3 -m scripts.dashboard.main
```

The module command runs from the skill repository. When the skill is installed in a
different directory, run its script by absolute path **from the user's project root**:

```bash
python3 /absolute/path/to/pair-programming/scripts/dashboard/main.py
```

`/pair dashboard`, `$pair-programming dashboard`, and `/pair-programming dashboard`
all route to this generator. Open the generated `index.html` directly in a browser;
no server or npm build is required.

Generated files:

```
.pair/dashboard/
├── index.html
├── data.json
├── history/          # JSON exports rebuilt from source session records
└── assets/
    ├── style.css
    └── app.js
```

Options:

```bash
python3 -m scripts.dashboard.main --json
python3 -m scripts.dashboard.main --pair-dir ./project/.pair
python3 -m scripts.dashboard.main --output ./dashboard-output
python3 -m scripts.dashboard.main --watch
python3 -m scripts.dashboard.main --watch --interval 0.5 --json
python3 -m scripts.dashboard.main --workspace ~/workspace
python3 -m scripts.dashboard.main --workspace ~/workspace --watch
```

The same options work with the absolute script path. JSON-only generation writes JSON
artifacts (`data.json` and session history), leaving existing HTML and assets untouched.
`--workspace` and `--pair-dir` are mutually exclusive. Workspace output defaults to
`<workspace>/.pair/dashboard`; `--output` overrides it.

Canonical inputs are `manifest.yaml`, `progress.yaml`, `pitfalls.yaml`, and Markdown
summaries in `sessions/`, structured session metadata, and operation journals. Legacy `.json` state and `events.jsonl` remain supported;
YAML takes precedence. Plan titles come from manifest, and completion comes from progress.
Session summary timestamps use file modification time, labeled in the view and JSON.
Missing state is shown explicitly. Invalid state and unsupported schema versions fail
with an error instead of being presented as an empty successful snapshot.

Only generated files are written. No source state, Git refs, or implementation code is
changed or initialized.

## Watch mode

`/pair dashboard --watch` performs one generation, then polls the source state every
second. Adjust the interval with `--interval <seconds>`; it must be positive and finite.
The mode works with custom input/output paths and JSON-only generation.

```bash
python3 /absolute/path/to/pair-programming/scripts/dashboard/main.py --watch --pair-dir ./project/.pair
```

Example terminal output:

```text
Watching /path/to/project/.pair every 1s. Press Ctrl-C to stop.
progress.yaml changed
Step: parser -> tests
Dashboard refreshed
```

It monitors the three canonical YAML state files, Markdown/YAML/JSON session records directly
under `sessions/`, operation journals, legacy JSON state, and `events.jsonl`. File creation/deletion and
content changes are detected, including edits that preserve the file size and timestamp.
Generated files under `.pair/dashboard/` are excluded from monitoring.

Invalid intermediate state preserves the last valid business values. The generated view
and JSON gain a stale warning, error and check time; successful recovery clears these.
The watcher
retries and reports identical errors only once. Ctrl-C exits cleanly. This refreshes
the static artifacts; reload an open HTML page to see changes. No web server or new
Python dependency is introduced.

## Metrics and navigation

The page separates workflow phase, step completion, recorded validation, and knowledge
coverage. Step completion excludes skipped/superseded steps; missing progress is unknown.
Dependencies come from manifest, observed statuses from progress. Readiness is derived
without rewriting status; invalid graphs are reported rather than guessing an ordering.
The attention section suggests the next safe `/pair` command as selectable text.

Implementation origin counts completed steps as human/ai/mixed/unknown, with the denominator
and record coverage shown. Mixed is a separate category, not a guessed Human/AI split.

## Sessions and workspace

New sessions use `templates/session-summary.md` YAML frontmatter or equivalent JSON/YAML
metadata, following `schemas/session.schema.json`. The reader checks metadata fields,
supported version, stable IDs and timezone-aware timestamps. The Pair workflow records the
stable ID and actual times/outcome. Dashboard generation does not initialize those records.
Legacy summaries retain unknown start/end/outcome. Source edits/deletions are reflected in
rebuildable `history/` JSON exports; repeated Watch refreshes do not create new sessions.

Workspace mode scans direct children containing `.pair`, excluding hidden/dependency
directories and symlinks. Each project has its own detail page and history. Bad projects
show a read error without preventing others from rendering. No cross-project average is shown.

## Validation

From the skill repository:

```bash
python3 -m pytest tests/dashboard
python3 scripts/validate-package.py
```
