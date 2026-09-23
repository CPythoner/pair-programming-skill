# Shadow Pitfall Journal

Shadow is a disposable implementation workspace, but the knowledge learned there is not
disposable.

The Pitfall Journal preserves failures, wrong assumptions, hidden constraints, and
non-obvious fixes so they can be taught proactively during Guided Reconstruction.

## Canonical file

```text
.pair/pitfalls.yaml
```

Use stable IDs: `P001`, `P002`, ...

## Record threshold

Create an entry when a problem has reusable engineering value, including:

- a failed implementation that required reasoning to correct;
- an incorrect assumption about repository behavior;
- a build/toolchain/dependency/platform surprise;
- lifecycle, ownership, concurrency, ordering, or state-machine traps;
- an edge case exposed by testing;
- a workaround or compatibility constraint;
- an unresolved issue that could affect the Human implementation.

Do not record every typo or routine compiler error. Record it only when the underlying cause
teaches something reusable.

## Evidence before certainty

Prefer entries backed by:
- failing/passing tests;
- compiler/linker output summaries;
- runtime observations;
- source inspection;
- documentation already trusted by the project.

If root cause is uncertain, say so and keep status unresolved. Do not convert a hypothesis
into a fact.

## Entry lifecycle

1. Allocate stable ID.
2. Record symptom/trigger and evidence.
3. Record wrong assumption/failed approach if meaningful.
4. Investigate root cause.
5. Record resolution/workaround.
6. Validate the fix.
7. During reverse decomposition, map to Guide steps.
8. During Guided Reconstruction, proactively surface at the mapped step.
9. Track user communication in `.pair/progress.yaml`.

Never delete an entry just because it was resolved.

## Mapping

Pitfall -> Guide:
`related_steps: [registry, plugin-lifecycle]`

Guide -> Pitfall:
each manifest step has:
`pitfall_ids: [P001, P004]`

Feature-wide:
`related_steps: ["*"]`

## Teaching behavior

A pitfall explanation should usually be short:

```text
Shadow pitfall P004
Symptom: ...
Root cause: ...
What matters for this step: ...
Avoid: ...
```

Do not reveal unrelated full reference code unless the user asks.

## Review behavior

Known pitfalls act like targeted review assertions.

If P004 says "callback may run after owner destruction", review the Human implementation
specifically for lifetime ordering even if the code differs completely from Shadow.

If the Human implementation structurally avoids the pitfall, say so rather than forcing the
Shadow fix.

## Completion

A feature cannot be considered fully handed off while:
- a blocker/high unresolved pitfall is undocumented in the final handoff; or
- a pitfall relevant to completed Human steps has never been surfaced when it would
  materially affect maintainability.

The goal is not to tell the user every failed experiment. The goal is to transfer the
important engineering knowledge that Shadow exploration discovered.
