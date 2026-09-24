# Shadow Pitfall Journal

Shadow is a disposable implementation workspace, but the knowledge learned there is not
disposable.

The Pitfall Journal preserves failures, wrong assumptions, hidden constraints, and
non-obvious fixes so they can be taught proactively during Guided Reconstruction and applied
during takeover/review.

## Canonical file

```text
.pair/pitfalls.yaml
```

Use stable IDs: `P001`, `P002`, ...

Schema: `schemas/pitfalls.schema.json`.

## Record threshold

Create an entry when a problem has reusable engineering value, including:

- a failed implementation that required reasoning to correct;
- an incorrect assumption about repository behavior;
- a build/toolchain/dependency/platform surprise;
- lifecycle, ownership, concurrency, ordering, or state-machine traps;
- an edge case exposed by testing;
- a workaround or compatibility constraint;
- an unresolved issue that could affect Human implementation.

Do not record every typo or routine compiler error.

## Evidence and confidence

Record how the pitfall was discovered:

```yaml
confidence: confirmed
discovered_by: [test, runtime]
```

Use:

- `confirmed` — supported by direct evidence;
- `probable` — strong evidence, root cause not fully isolated;
- `hypothesis` — plausible but unconfirmed.

Do not teach a hypothesis as established fact.

## Contextual applicability

A Pitfall is more useful when it can be matched to current work without depending only on a
precomputed step ID.

Record:

```yaml
affected_files: []
affected_symbols: []

applies_when:
  files: []
  symbols: []
  platforms: []
  configurations: []
  conditions: []
```

Keep `related_steps` too. Step mapping is the strongest pedagogical signal; contextual
fields make the journal resilient when Human implementation diverges or `/pair rebase-plan`
changes later steps.

## Entry lifecycle

1. allocate stable ID;
2. record symptom/trigger/evidence;
3. set confidence honestly;
4. record wrong assumption/failed approach when useful;
5. investigate root cause;
6. record resolution/workaround;
7. validate;
8. map to Guide steps and contextual applicability;
9. define review/teaching guidance;
10. proactively surface when matched;
11. track communication in `.pair/progress.yaml`.

Never delete an entry just because it was resolved.

## Matching algorithm

Before `/pair next`, `/pair review`, or `/pair take`, build a set of relevant Pitfalls.

Match in this order:

1. `related_steps` contains current step ID;
2. `related_steps` contains `"*"`;
3. current changed/target file intersects `affected_files` or `applies_when.files`;
4. current target symbol intersects `affected_symbols` or `applies_when.symbols`;
5. active platform/configuration/condition matches `applies_when`;
6. unresolved blocker/high Pitfall is feature-wide and could affect the operation.

Deduplicate by Pitfall ID.

Record why it matched:

```yaml
pitfalls:
  P004:
    surfaced: true
    surfaced_at_step: plugin-lifecycle
    discussed: false
    last_matched_by:
      - step
      - symbol
```

Do not surface a Pitfall merely because a weak textual similarity exists.

## Teaching metadata

Optional teaching guidance:

```yaml
review_assertion: "callback cannot outlive owner"

teach:
  timing: before_step
  hint_level: 1
  summary: "Unregister before owner destruction."
```

`timing` may be:

- `before_step`;
- `during_review`;
- `on_takeover`;
- `handoff`.

This is guidance, not permission to hide a high-severity Pitfall until later.

## Guide mapping

Pitfall -> Guide:

```yaml
related_steps: [registry, plugin-lifecycle]
```

Guide -> Pitfall:

```yaml
pitfall_ids: [P001, P004]
```

Feature-wide:

```yaml
related_steps: ["*"]
```

## Teaching behavior

A concise warning usually contains:

```text
Shadow pitfall P004
Evidence/confidence: ...
Symptom: ...
Root cause: ...
What matters now: ...
Avoid: ...
```

Do not reveal unrelated full reference code unless asked.

## Review behavior

Known Pitfalls act like targeted semantic assertions.

Use `review_assertion` when present. If Human code structurally avoids the pitfall, say so
rather than forcing the Shadow fix.

## Takeover behavior

Before applying delegated code:

- match relevant Pitfalls against scope;
- add matched IDs to operation preflight;
- apply known `avoidance` / resolution knowledge during semantic port;
- report which Pitfalls the delegated change handles.

## Completion

A feature cannot be considered fully handed off while:

- blocker/high unresolved Pitfalls are omitted from final handoff; or
- a materially relevant Pitfall for completed Human work has never been surfaced.

The goal is transfer of reusable engineering knowledge, not a log of every failed experiment.
