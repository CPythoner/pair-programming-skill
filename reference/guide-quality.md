# Guide Branch Quality Contract

Guide Branch is a teaching artifact, not merely a replay of the final Shadow diff.

The quality target is:

> correct + dependency-aware + verifiable + teachable

## Commit contract

Each Guide commit should:

1. represent one primary concept;
2. have satisfied dependencies;
3. avoid unrelated refactors;
4. avoid introducing later-step concepts early;
5. prefer 1-3 files;
6. prefer about 150 effective diff lines;
7. stay below the configured hard line limit unless `size_exception_reason` is recorded;
8. compile when practical;
9. have focused verification;
10. use a stable step marker in the commit subject;
11. map known relevant Pitfalls.

A large cohesive mechanical change may exceed preferred limits. Size alone is not a
correctness failure; unexplained size is a Guide quality failure.

## Intermediate validity

Prefer every commit to leave the repository buildable.

If that is not practical, the manifest step must record:

```yaml
quality:
  focused_validation: true
  intermediate_build: false
  alternative_verification: "..."
```

Do not silently leave an invalid intermediate tree.

## Future-step leakage

Before freezing a Guide commit, inspect its diff for concepts assigned to later steps.

Examples:

- Step 2 should not quietly add Step 4 locking;
- Step 3 should not include final integration tests unless they are intentionally the
  verification for Step 3;
- dependency configuration should not be modified before the step that needs it.

If leakage is unavoidable, explain it in the step metadata.

## Automated structural check

Run:

```bash
python3 scripts/check-guide.py \
  --base <baseline> \
  --guide <guide-ref> \
  --solution <solution-ref>
```

The checker reports:

- commit order;
- merge commits;
- changed-file count per commit;
- effective diff lines per commit;
- preferred/hard limit violations;
- final Guide/Solution tree identity when `--solution` is provided.

Structural checks cannot prove teachability or behavioral equivalence. They complement, not
replace, focused validation and semantic review.

## Manifest result

Record the latest quality check:

```yaml
guide_quality:
  status: passed
  checked_at: "..."
  base: "<sha>"
  guide_head: "<sha>"
  solution_commit: "<sha>"
  checker: "scripts/check-guide.py"
  warnings: []
  failures: []
```

Use:

- `passed` when structural and semantic checks are clean;
- `warnings` when explained exceptions remain;
- `failed` when Guide should not be used for reconstruction yet.

## Final equivalence

Guide final tree may differ mechanically from Shadow solution.

Before Guided Reconstruction, verify:

- acceptance criteria;
- externally observable behavior;
- relevant tests;
- build/package behavior;
- generated artifacts when relevant;
- intentional differences.

Document intentional differences. Do not claim equivalence from tree comparison alone.
