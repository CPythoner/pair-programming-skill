# Pair Dashboard

The dashboard reads `.pair` state and generates a local HTML view.

## Export

```python
from dashboard.collector import collect_dashboard
from dashboard.export import export_html

snapshot = collect_dashboard('.pair')
export_html(snapshot, '.pair/dashboard/index.html')
```

The generated page shows:

- current session status
- implementation plan progress
- historical events
- recorded pitfalls
