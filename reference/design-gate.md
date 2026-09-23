# Design Gate

The design gate prevents an underspecified feature goal from turning directly into code.

## Classification

A `/pair plan` input is implementation-ready only if the agent can implement it without
inventing material architecture decisions.

A concrete design normally covers:
- scope and intended behavior;
- affected components;
- contracts/interfaces;
- important data/control flow;
- relevant ownership/lifetime/concurrency;
- material error and edge-case behavior;
- verification/acceptance criteria.

A feature request, issue title, or one-line goal is not a design.

## Canonical artifact

Every plan has one canonical saved design:

```text
.pair/design.md
```

If the user provided the design, normalize it without silently changing decisions.
If the input is incomplete, the agent authors the design based on the actual repository.

## Approval

AI-authored or materially completed designs require explicit user approval before
implementation.

Approval is bound to a revision:

```yaml
design:
  status: approved
  revision: 3
  approved_revision: 3
```

The implementation gate is open only when:

```text
status == approved && revision == approved_revision
```

If the design changes materially:
- increment revision;
- set status to awaiting_approval;
- reset approved_revision to 0;
- clear approval timestamp/evidence;
- return progress phase to design.

## Allowed actions while awaiting approval

Allowed:
- inspect code for design purposes;
- edit/review/explain the design;
- status reporting;
- answer questions;
- explicitly approve the current revision.

Not allowed:
- create Shadow implementation branches/worktrees;
- edit production/source code for the feature;
- generate the full implementation;
- use `/pair take` to bypass the gate;
- begin Guided Reconstruction.

## User-provided complete design

When `/pair plan` itself includes or references an implementation-ready design, treat that
submission as approved for implementation unless the user explicitly asks for design
review/planning only. Save the canonical design and record it as `user_provided`.

## Approval examples

These may approve the current revision when context is unambiguous:
- 确认
- 方案没问题
- 按这个方案实现
- 开始实现
- approved

Do not infer approval from silence or unrelated follow-up questions.
