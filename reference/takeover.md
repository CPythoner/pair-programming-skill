# Selective Takeover

`/pair take` is a first-class workflow, not a failure state.

The user may intentionally delegate low-value or difficult work.

## Supported scopes

- step
- file
- symbol
- tests
- build
- dependencies
- tooling
- remaining
- all

## Before modifying Human Workspace

Capture:
- branch;
- HEAD;
- status;
- staged diff;
- unstaged binary diff;
- relevant untracked files.

Write the checkpoint under `.pair/checkpoints/<timestamp>/`.

## Choose application mode

### Semantic port — preferred

Use when Human implementation differs from Guide.

Read the intent of the reference delta, then implement that intent against current Human code.

This is the safest default.

### Cherry-pick Guide commit

Use only when:
- current state matches expected predecessor;
- no unrelated changes overlap;
- the whole guide step is requested.

### 3-way patch

Use when the source is close but not commit-aligned.

### Manual adaptation

Use when:
- symbol-level takeover;
- file has significant human edits;
- API shape changed;
- re-plan has diverged.

## Conflict policy

Never choose "theirs" for an entire file just because Shadow has a working version.

Preserve user changes unless they contradict requested behavior.

If a clean automated application is impossible, manually port the requested behavior.

## After takeover

1. Show what was changed.
2. Explain adaptations.
3. Run validation.
4. Update origin:
   - `ai`: entirely delegated;
   - `mixed`: user + AI both materially implemented it.
5. Return control to Human mode.
