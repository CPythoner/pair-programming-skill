# Reverse Decomposition Rules

Perform reverse decomposition only after the Shadow implementation is complete and verified.

## Goal

Decompose the solution into **cognitive units**, not batches of file edits.

Good steps:

```text
Step 1 Define RequestId value object
Step 2 Add pending-request index
Step 3 Route response lookup through the index
Step 4 Protect index with existing reactor-thread invariant
Step 5 Add timeout cleanup tests
```

Poor steps:

```text
Step 1 Modify foo.h
Step 2 Modify foo.cpp
Step 3 Modify test.cpp
```

## Decomposition algorithm

### 1. Extract semantic changes from the final diff

Group the final implementation into semantic categories:

- data model / invariant
- contract / interface
- algorithm
- integration
- lifecycle / ownership
- concurrency
- failure path
- persistence / protocol
- build / package
- tests

### 2. Build the dependency graph

For each semantic change, determine:

- which types or APIs must exist first;
- which callers depend on it;
- which tests can validate it independently.

### 3. Choose a teaching order

Prefer:

- stable concepts before complex integration;
- local verification before system-level verification;
- steps with a clear "why" before steps with more difficult boundary conditions.

### 4. Control step size

Default guidance:

- 1 primary concept;
- 1–3 files;
- about 150 effective diff lines;
- 1 explicit validation point.

If a step must exceed the configured hard limit, record `size_exception_reason`.

### 5. Rebuild the Guide Branch

Do not simply cherry-pick exploratory Shadow history.

Start from the recorded baseline and reconstruct each step commit deliberately. Every commit
must follow the Guide Commit Contract in `reference/guide-quality.md`:

- one primary concept;
- dependencies already satisfied;
- no unrelated refactors;
- no avoidable leakage from later steps;
- preferably 1–3 files and about 150 effective diff lines;
- any hard-limit exception recorded with `size_exception_reason`;
- focused validation;
- a stable step marker in the commit subject.

### 6. Run the Guide structural check

Run:

```bash
python3 scripts/check-guide.py --base <baseline> --guide <guide-ref> --solution <solution-ref>
```

Record warnings, failures, and the check timestamp under `manifest.guide_quality`.

Structural checking can detect commit granularity, non-linear history, diff size, and final-tree
differences. It does not replace semantic review or behavioral validation.

### 7. Verify Guide/Solution equivalence

At minimum compare:

- acceptance criteria;
- public behavior;
- tests;
- relevant generated artifacts;
- final build.

The Guide final tree does not need to be byte-identical to the Shadow solution, but it must be
behaviorally equivalent or have every intentional difference explained.

Enter Guided Reconstruction only after Guide quality is not `failed` and behavioral
equivalence has been verified.
