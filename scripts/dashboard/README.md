# Pair Dashboard

Generate a static dashboard from `.pair` state.

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
└── assets/
    ├── style.css
    └── app.js
```

Options:

```bash
python3 -m scripts.dashboard.main --json
python3 -m scripts.dashboard.main --pair-dir ./project/.pair
python3 -m scripts.dashboard.main --output ./dashboard-output
```

The same options work with the absolute script path. JSON-only generation writes only
`data.json` and leaves any previously generated HTML and assets untouched.

Canonical inputs are `manifest.yaml`, `progress.yaml`, `pitfalls.yaml`, and Markdown
summaries in `sessions/`. Legacy `.json` state and `events.jsonl` remain supported;
YAML takes precedence. Plan titles come from manifest, and completion comes from progress.
Session summary timestamps use file modification time, labeled in the view and JSON.
Missing state is shown explicitly. Invalid state and unsupported schema versions fail
with an error instead of being presented as an empty successful snapshot.

Only generated files are written. No source state, Git refs, or implementation code is
changed or initialized.

## Validation

From the skill repository:

```bash
python3 -m pytest tests/dashboard
python3 scripts/validate-package.py
```
