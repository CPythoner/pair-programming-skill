# Pair Dashboard

Generate a static dashboard from `.pair` state.

## Usage

```bash
python -m scripts.dashboard.main
```

Generated files:

```
.pair/dashboard/
├── index.html
└── data.json
```

Options:

```bash
python -m scripts.dashboard.main --json
python -m scripts.dashboard.main --pair-dir ./project/.pair
python -m scripts.dashboard.main --output ./dashboard-output
```
