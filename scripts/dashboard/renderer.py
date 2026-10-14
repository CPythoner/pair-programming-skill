from __future__ import annotations

import html
from pathlib import Path

from .model import DashboardSnapshot


def render_dashboard(snapshot: DashboardSnapshot, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    assets = output.parent / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "style.css").write_text(_STYLE, encoding="utf-8")
    (assets / "app.js").write_text(_SCRIPT, encoding="utf-8")
    output.write_text(_render_html(snapshot), encoding="utf-8")


def _escape(value: object) -> str:
    return html.escape(str(value)) if value not in (None, "") else "Unknown"


_STATES = {
    "done": ("done", "Completed", "✓"),
    "completed": ("done", "Completed", "✓"),
    "complete": ("done", "Complete", "✓"),
    "active": ("active", "Active", "▶"),
    "shadow": ("active", "Shadow", "▶"),
    "guide": ("active", "Guide", "▶"),
    "guided_reconstruction": ("active", "Guided reconstruction", "▶"),
    "review": ("review", "In review", "◷"),
    "awaiting_approval": ("review", "Awaiting approval", "◷"),
    "blocked": ("blocked", "Blocked", "!"),
    "attention_required": ("blocked", "Attention required", "!"),
    "pending": ("pending", "Pending", "○"),
    "design": ("pending", "Design", "○"),
    "skipped": ("muted", "Skipped", "−"),
    "superseded": ("muted", "Superseded", "−"),
}


def _state(value: str) -> tuple[str, str, str]:
    return _STATES.get(value, ("muted", str(value or "Unknown").replace("_", " "), "○"))


def _badge(value: str) -> str:
    kind, label, _ = _state(value)
    return f'<span class="badge badge-{kind}"><span class="badge-dot" aria-hidden="true"></span>{_escape(label)}</span>'


def _time(value: str | None) -> str:
    if not value:
        return '<span class="muted">Unknown</span>'
    return f'<time datetime="{_escape(value)}">{_escape(value)}</time>'


def _render_html(snapshot: DashboardSnapshot) -> str:
    total = snapshot.total_steps
    percent = max(0, min(100, round(snapshot.completed_steps / total * 100))) if total > 0 else None
    completion = f'{percent}<span class="percent-sign">%</span>' if percent is not None else "—"
    progress_label = f"{percent}% of steps completed" if percent is not None else "No plan recorded"
    progress_meter = (
        f'<progress class="progress-bar" value="{percent}" max="100" aria-label="{progress_label}"></progress>'
        if percent is not None else '<div class="progress-bar" aria-hidden="true"></div>'
    )
    progress_summary = f"{snapshot.completed_steps} of {total} steps completed" if total > 0 else "No implementation steps recorded yet."
    current = next((item for item in snapshot.plan if item.id == snapshot.current_step), None)
    current_title = _escape(current.title if current else snapshot.current_step or "No current step")
    current_badge = _badge(current.status) if current else '<span class="muted">No step state recorded</span>'
    plan_rows = []
    for number, item in enumerate(snapshot.plan, 1):
        kind, _, marker = _state(item.status)
        is_current = item.id == snapshot.current_step
        current_attribute = ' aria-current="step"' if is_current else ""
        current_label = '<span class="current-label">Current step</span>' if is_current else ""
        plan_rows.append(f'''<li id="step-{number}" class="step step-{kind}{' step-current' if is_current else ''}"{current_attribute}>
          <span class="step-marker" aria-hidden="true">{marker}</span>
          <div class="step-copy"><div class="step-heading"><strong>{_escape(item.title)}</strong>{current_label}</div>
            <span class="step-id">{number:02d} / {_escape(item.id)}</span></div>
          {_badge(item.status)}
        </li>''')
    plan = '<ol class="step-list">' + "".join(plan_rows) + "</ol>" if plan_rows else (
        '<div class="empty-state"><span class="empty-symbol" aria-hidden="true">○</span>'
        '<h3>No plan recorded</h3><p>Implementation steps will appear when a plan is available.</p></div>'
    )
    events = "".join(
        f'<li class="event"><span class="event-dot" aria-hidden="true"></span>'
        f'<div><div class="event-time">{_time(item.time)}</div><strong>{_escape(item.event)}</strong>'
        f'<p class="event-meta">Actor: {_escape(item.actor)} · Step: {_escape(item.step)}</p>'
        f"""{'<p class="event-meta">Time from file modification</p>' if item.details.get('time_source') == 'file_mtime' else ''}"""
        '</div></li>'
        for item in snapshot.events
    )
    events = f'<ol class="event-list">{events}</ol>' if events else (
        '<div class="empty-state"><span class="empty-symbol" aria-hidden="true">◷</span>'
        '<h3>No session history</h3><p>Recorded session events will appear here.</p></div>'
    )
    pitfall_rows = []
    for item in snapshot.pitfalls:
        severity = {"blocker": "blocked", "high": "blocked", "medium": "review", "low": "muted"}.get(item.severity, "muted")
        pitfall_rows.append(f'''<li class="pitfall">
          <div class="pitfall-heading"><span class="step-id">{_escape(item.id)}</span>
            <span class="badge badge-{severity}">{_escape(item.severity)}</span></div>
          <h3>{_escape(item.title)}</h3><p>{_escape(item.description)}</p>
          <dl class="pitfall-details"><dt>Scope</dt><dd>{_escape(', '.join(item.affected_scope))}</dd>
            <dt>Resolution</dt><dd>{_escape(item.resolution)}</dd></dl>
        </li>''')
    pitfalls = '<ul class="pitfall-list">' + "".join(pitfall_rows) + "</ul>" if pitfall_rows else (
        '<div class="empty-state"><span class="empty-symbol" aria-hidden="true">◇</span>'
        '<h3>No pitfalls recorded</h3><p>Recorded issues and their resolutions will appear here.</p></div>'
    )
    warnings = "".join(f"<li>{_escape(item)}</li>" for item in snapshot.warnings)
    warnings = f'<aside class="notice" aria-labelledby="availability"><h2 id="availability">State availability</h2><ul>{warnings}</ul></aside>' if warnings else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pair Dashboard · {_escape(snapshot.project)}</title>
  <link rel="stylesheet" href="assets/style.css">
  <script src="assets/app.js" defer></script>
</head>
<body>
<a class="skip-link" href="#dashboard">Skip to dashboard</a>
<main id="dashboard">
  <header class="page-header">
    <div class="brand"><span class="brand-mark" aria-hidden="true">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="11" height="11" rx="2" stroke="currentColor" stroke-width="1.7"/><rect x="10" y="10" width="11" height="11" rx="2" fill="currentColor"/></svg>
    </span><div><p class="eyebrow">Pair programming control center</p><h1>Pair Dashboard</h1></div></div>
    <div class="header-actions">
      <button id="theme-toggle" class="button button-quiet" type="button" hidden aria-label="Theme: System. Switch to light theme.">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M17 11a7 7 0 0 1-8-8 7 7 0 1 0 8 8Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
        <span>Theme: System</span>
      </button>
      <a class="button" href="data.json" download="pair-dashboard.json">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M10 3v9m-3-3 3 3 3-3M4 13v4h12v-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Export JSON
      </a>
    </div>
  </header>
  <nav class="tabs" aria-label="Dashboard sections">
    <a href="#session">Status</a><a href="#progress">Progress</a><a href="#plan">Plan</a>
    <a href="#timeline">Timeline</a><a href="#pitfalls">Pitfalls</a>
    <span class="snapshot-label"><span class="badge-dot" aria-hidden="true"></span>Read-only snapshot</span>
  </nav>
  {warnings}
  <div class="overview">
    <section id="session" class="panel status-panel" aria-labelledby="status-title">
      <div class="panel-heading"><h2 id="status-title">Status</h2>{_badge(snapshot.status)}</div>
      <p class="project-name">{_escape(snapshot.project)}</p>
      <dl class="session-details">
        <dt>Phase</dt><dd>{_escape(snapshot.phase).replace('_', ' ')}</dd>
        <dt>Updated</dt><dd>{_time(snapshot.updated_at)}</dd>
      </dl>
    </section>
    <section id="progress" class="panel progress-panel" aria-labelledby="progress-title">
      <div class="panel-heading"><h2 id="progress-title">Progress</h2><span class="eyebrow">Completion</span></div>
      <div class="progress-summary"><span class="completion">{completion}</span><span class="muted">{progress_summary}</span></div>
      {progress_meter}
      <div class="current-step"><div><span class="eyebrow">Current step</span><strong>{current_title}</strong></div>{current_badge}</div>
    </section>
  </div>
  <section id="plan" class="panel plan-panel" aria-labelledby="plan-title">
    <div class="panel-heading"><h2 id="plan-title">Plan timeline</h2><span class="section-count">{len(snapshot.plan)} steps</span></div>
    {plan}
  </section>
  <div class="details-grid">
    <section id="timeline" class="panel" aria-labelledby="timeline-title">
      <div class="panel-heading"><h2 id="timeline-title">Timeline</h2><span class="section-count">{len(snapshot.events)} events</span></div>
      {events}
    </section>
    <section id="pitfalls" class="panel" aria-labelledby="pitfalls-title">
      <div class="panel-heading"><h2 id="pitfalls-title">Pitfalls</h2><span class="section-count">{len(snapshot.pitfalls)} recorded</span></div>
      {pitfalls}
    </section>
  </div>
  <footer><span>Pair Dashboard <span aria-hidden="true">/</span> Static snapshot</span><span>Generated {_time(snapshot.generated_at)}</span></footer>
</main>
</body>
</html>
"""


_STYLE = """\
:root {
  color-scheme: light;
  --bg: #f3f5f7; --panel: #fff; --panel-soft: #f7f9fa; --fg: #17212e;
  --muted: #5c697a; --border: #dde3e9; --accent: #087755;
  --accent-soft: #e7f4ed; --warning: #8b5809; --warning-soft: #fff4df;
  --danger: #ba3943; --danger-soft: #fcecef; --shadow: 0 2px 8px #17212e04;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px; line-height: 1.55;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #0d1117; --panel: #151b23; --panel-soft: #1b232d; --fg: #edf1f5;
    --muted: #a0adbc; --border: #2a3441; --accent: #64dca7;
    --accent-soft: #18382e; --warning: #f0c075; --warning-soft: #352b1a;
    --danger: #f2949c; --danger-soft: #382127; --shadow: none;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0d1117; --panel: #151b23; --panel-soft: #1b232d; --fg: #edf1f5;
  --muted: #a0adbc; --border: #2a3441; --accent: #64dca7;
  --accent-soft: #18382e; --warning: #f0c075; --warning-soft: #352b1a;
  --danger: #f2949c; --danger-soft: #382127; --shadow: none;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 24px; }
body { margin: 0; background: var(--bg); color: var(--fg); }
main { max-width: 1168px; margin: auto; padding: 36px 28px 24px; overflow-wrap: anywhere; }
h1, h2, h3, p, ol, ul, dl { margin: 0; }
h1 { font-size: 28px; font-weight: 650; line-height: 1.3; letter-spacing: -.8px; }
h2 { font-size: 15px; font-weight: 650; letter-spacing: -.15px; }
h3 { font-size: 14px; font-weight: 600; }
a { color: inherit; }
button { font: inherit; color: inherit; cursor: pointer; }
[hidden] { display: none !important; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
.skip-link { position: absolute; top: 8px; left: 12px; padding: 8px 12px; background: var(--panel); z-index: 2; transform: translateY(-150%); }
.skip-link:focus { transform: translateY(0); }
.page-header, .brand, .header-actions, .panel-heading, .pitfall-heading { display: flex; align-items: center; }
.page-header { justify-content: space-between; gap: 24px; }
.brand { gap: 14px; min-width: 0; }
.brand-mark { display: grid; place-items: center; flex: 0 0 44px; height: 44px; border-radius: 12px; background: var(--accent-soft); color: var(--accent); }
.eyebrow { display: block; color: var(--muted); font-size: 10px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase; }
.brand .eyebrow { margin-bottom: 4px; }
.header-actions { flex-wrap: wrap; gap: 8px; }
.button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 40px; padding: 8px 12px; border: 1px solid var(--border); border-radius: 7px; background: var(--panel); text-decoration: none; font-size: 12px; font-weight: 550; transition: background .16s, border-color .16s; }
.button-quiet { background: transparent; }
.button:hover { background: var(--panel-soft); border-color: var(--muted); }
.tabs { display: flex; align-items: center; flex-wrap: wrap; gap: 4px 24px; margin: 28px 0 24px; border-bottom: 1px solid var(--border); }
.tabs a { display: flex; align-items: center; min-height: 44px; padding: 8px 0 12px; border-bottom: 2px solid transparent; text-decoration: none; color: var(--muted); font-size: 12px; font-weight: 550; transition: color .16s, border-color .16s; }
.tabs a:hover, .tabs a[aria-current="location"] { color: var(--accent); border-color: var(--accent); }
.snapshot-label { display: flex; align-items: center; gap: 7px; margin-left: auto; color: var(--muted); font-size: 11px; }
.snapshot-label .badge-dot { color: var(--accent); }
.overview, .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.panel { min-width: 0; padding: 24px; border: 1px solid var(--border); border-radius: 12px; background: var(--panel); box-shadow: var(--shadow); }
.panel-heading { justify-content: space-between; gap: 16px; margin-bottom: 24px; }
.section-count { color: var(--muted); font-size: 11px; white-space: nowrap; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 9px; border-radius: 5px; font-size: 10px; font-weight: 600; line-height: 1.5; background: var(--panel-soft); color: var(--muted); }
.badge-dot { display: inline-block; flex: 0 0 5px; width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.badge-done, .badge-active { color: var(--accent); background: var(--accent-soft); }
.badge-review { color: var(--warning); background: var(--warning-soft); }
.badge-blocked { color: var(--danger); background: var(--danger-soft); }
.project-name { margin: 0 0 26px; font-size: 23px; font-weight: 600; line-height: 1.4; letter-spacing: -.6px; }
.session-details { display: grid; grid-template-columns: 72px minmax(0, 1fr); gap: 12px; font-size: 12px; }
dt, .muted { color: var(--muted); } dd { margin: 0; }
.progress-summary { display: flex; align-items: baseline; flex-wrap: wrap; gap: 16px; margin-top: -8px; }
.completion { font-size: 48px; font-weight: 600; line-height: 1.2; letter-spacing: -2px; font-variant-numeric: tabular-nums; }
.percent-sign { margin-left: 3px; color: var(--muted); font-size: 23px; letter-spacing: 0; }
.progress-summary .muted { font-size: 12px; }
.progress-bar { display: block; appearance: none; width: 100%; height: 7px; margin: 18px 0 22px; border: 0; border-radius: 4px; overflow: hidden; background: var(--border); accent-color: var(--accent); }
.progress-bar::-webkit-progress-bar { background: var(--border); border-radius: 4px; }
.progress-bar::-webkit-progress-value { background: var(--accent); border-radius: 4px; }
.progress-bar::-moz-progress-bar { background: var(--accent); border-radius: 4px; }
.current-step { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.current-step strong { display: block; margin-top: 4px; font-size: 12px; font-weight: 550; }
.current-step .muted { font-size: 11px; }
.plan-panel { margin: 20px 0; }
.step-list, .event-list, .pitfall-list { list-style: none; padding: 0; }
.step { position: relative; display: grid; grid-template-columns: 28px minmax(0, 1fr) auto; align-items: center; gap: 16px; min-height: 76px; padding: 14px 14px; border-radius: 7px; }
.step:not(:last-child)::after { position: absolute; content: ""; left: 27px; top: 51px; bottom: -25px; width: 1px; background: var(--border); }
.step-marker { display: grid; place-items: center; z-index: 1; width: 28px; height: 28px; border: 1px solid var(--border); border-radius: 50%; background: var(--panel); color: var(--muted); font-size: 12px; }
.step-done .step-marker { border-color: var(--accent-soft); color: var(--accent); background: var(--accent-soft); }
.step-active .step-marker { border-color: var(--accent); color: var(--accent); }
.step-blocked .step-marker { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-soft); }
.step-review .step-marker { color: var(--warning); }
.step-current { background: var(--accent-soft); }
.step-heading { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 12px; }
.step-heading strong { font-size: 13px; font-weight: 550; }
.step-id { color: var(--muted); font-size: 10px; font-family: ui-monospace, "SFMono-Regular", Consolas, monospace; }
.current-label { color: var(--accent); font-size: 9px; font-weight: 650; text-transform: uppercase; letter-spacing: .6px; }
.step-copy .step-id { display: block; margin-top: 4px; }
.event { display: grid; grid-template-columns: 8px minmax(0, 1fr); gap: 14px; padding: 0 0 24px; }
.event:last-child { padding-bottom: 0; }
.event-dot { margin-top: 7px; width: 6px; height: 6px; border-radius: 50%; background: var(--muted); }
.event-time { color: var(--muted); font-size: 10px; margin-bottom: 6px; }
.event strong { font-size: 12px; font-weight: 550; }
.event-meta { color: var(--muted); font-size: 10px; margin-top: 5px; }
.pitfall + .pitfall { margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border); }
.pitfall-heading { justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.pitfall h3 { margin-bottom: 8px; }
.pitfall p { color: var(--muted); font-size: 12px; }
.pitfall-details { display: grid; grid-template-columns: 68px minmax(0, 1fr); gap: 8px; margin-top: 16px; font-size: 11px; }
.empty-state { padding: 20px 12px 28px; text-align: center; }
.empty-symbol { display: block; margin-bottom: 10px; font-size: 28px; color: var(--muted); }
.empty-state p { max-width: 280px; margin: 8px auto 0; color: var(--muted); font-size: 12px; }
.notice { margin-bottom: 20px; padding: 16px 20px; border: 1px solid var(--border); border-left: 3px solid var(--warning); border-radius: 7px; background: var(--panel); }
.notice h2 { margin-bottom: 6px; font-size: 12px; color: var(--warning); }
.notice ul { padding-left: 18px; color: var(--muted); font-size: 12px; }
footer { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px 24px; padding-top: 24px; color: var(--muted); font-size: 10px; }
footer span[aria-hidden] { margin: 0 8px; }
@media (max-width: 760px) {
  main { padding: 24px 20px; }
  .page-header { align-items: flex-start; flex-wrap: wrap; gap: 18px; }
  .overview, .details-grid { grid-template-columns: 1fr; gap: 16px; }
  .snapshot-label { display: none; }
  .panel { padding: 20px; }
  .plan-panel { margin: 16px 0; }
}
@media (max-width: 420px) {
  main { padding: 20px 12px; }
  h1 { font-size: 24px; }
  .brand .eyebrow { font-size: 8px; letter-spacing: .8px; }
  .tabs { gap: 4px 18px; margin-top: 20px; }
  .panel { padding: 18px 16px; }
  .panel-heading { flex-wrap: wrap; gap: 10px; }
  .step { grid-template-columns: 24px minmax(0, 1fr); gap: 12px; padding: 12px 8px; }
  .step-marker { width: 24px; height: 24px; }
  .step:not(:last-child)::after { left: 19px; top: 41px; bottom: -22px; }
  .step > .badge { grid-column: 2; justify-self: start; }
  .progress-summary { gap: 8px 12px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { transition: none !important; }
}
"""

# Everything is already rendered in HTML; this enhancement also works over file://.
_SCRIPT = """\
document.querySelectorAll('time[datetime]').forEach((element) => {
  const value = new Date(element.dateTime);
  if (!Number.isNaN(value.getTime())) {
    element.textContent = value.toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }
});

const themeControl = document.getElementById('theme-toggle');
const themes = ['system', 'light', 'dark'];
let theme = 'system';
try {
  const saved = localStorage.getItem('pair-dashboard-theme');
  if (themes.includes(saved)) theme = saved;
} catch (_) { /* Storage may be unavailable when opened directly as a local file. */ }
function applyTheme() {
  if (theme === 'system') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.dataset.theme = theme;
  const name = theme.charAt(0).toUpperCase() + theme.slice(1);
  themeControl.querySelector('span').textContent = 'Theme: ' + name;
  const next = themes[(themes.indexOf(theme) + 1) % themes.length];
  themeControl.setAttribute('aria-label', 'Theme: ' + name + '. Switch to ' + next + ' theme.');
}
if (themeControl) {
  applyTheme();
  themeControl.hidden = false;
  themeControl.addEventListener('click', () => {
    theme = themes[(themes.indexOf(theme) + 1) % themes.length];
    applyTheme();
    try { localStorage.setItem('pair-dashboard-theme', theme); } catch (_) { }
  });
}

const tabs = Array.from(document.querySelectorAll('.tabs a'));
function highlightTab(id) {
  tabs.forEach((tab) => {
    if (tab.hash === '#' + id) tab.setAttribute('aria-current', 'location');
    else tab.removeAttribute('aria-current');
  });
}
highlightTab(window.location.hash.slice(1) || 'session');
window.addEventListener('hashchange', () => highlightTab(window.location.hash.slice(1) || 'session'));
"""
