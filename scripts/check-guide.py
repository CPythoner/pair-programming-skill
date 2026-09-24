#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Sequence


@dataclass
class CommitReport:
    commit: str
    subject: str
    files: int
    effective_diff_lines: int
    binary_files: list[str]
    warnings: list[str]
    failures: list[str]


def git(args: Sequence[str], *, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def is_ancestor(base: str, guide: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, guide],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def diff_stats(parent: str, commit: str) -> tuple[int, int, list[str]]:
    raw = git(["diff", "--numstat", parent, commit])
    files = 0
    lines = 0
    binary: list[str] = []
    if not raw:
        return files, lines, binary

    for row in raw.splitlines():
        parts = row.split("\t", 2)
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        files += 1
        if added == "-" or deleted == "-":
            binary.append(path)
            continue
        lines += int(added) + int(deleted)
    return files, lines, binary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check structural quality of a Pair Programming Guide Branch."
    )
    parser.add_argument("--base", required=True, help="Recorded feature baseline revision")
    parser.add_argument("--guide", required=True, help="Guide branch/ref to inspect")
    parser.add_argument("--solution", help="Verified Shadow solution ref for final-tree comparison")
    parser.add_argument("--preferred-files", type=int, default=3)
    parser.add_argument("--preferred-lines", type=int, default=150)
    parser.add_argument("--hard-lines", type=int, default=300)
    parser.add_argument(
        "--allow-hard-limit",
        action="append",
        default=[],
        metavar="COMMIT_PREFIX",
        help="Acknowledge a documented size_exception_reason for a specific commit",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.preferred_files < 1 or args.preferred_lines < 1 or args.hard_lines < 1:
        parser.error("line/file limits must be positive")
    if args.hard_lines < args.preferred_lines:
        parser.error("--hard-lines must be >= --preferred-lines")

    for rev in [args.base, args.guide, args.solution]:
        if rev:
            try:
                git(["rev-parse", "--verify", rev])
            except RuntimeError as exc:
                print(f"ERROR: cannot resolve {rev!r}: {exc}", file=sys.stderr)
                return 2

    if not is_ancestor(args.base, args.guide):
        print(
            f"ERROR: base {args.base!r} is not an ancestor of guide {args.guide!r}",
            file=sys.stderr,
        )
        return 2

    commits_text = git(["rev-list", "--reverse", f"{args.base}..{args.guide}"])
    commits = [c for c in commits_text.splitlines() if c]
    merge_text = git(["rev-list", "--merges", f"{args.base}..{args.guide}"])
    merge_commits = [c for c in merge_text.splitlines() if c]

    global_failures: list[str] = []
    global_warnings: list[str] = []

    if not commits:
        global_failures.append("guide contains no commits after baseline")
    if merge_commits:
        global_failures.append(
            "guide history contains merge commits: " + ", ".join(c[:12] for c in merge_commits)
        )

    reports: list[CommitReport] = []
    step_subject = re.compile(r"^pair\(step:[^)]+\):\s+\S+")

    for commit in commits:
        subject = git(["show", "-s", "--format=%s", commit])
        parent = git(["rev-parse", f"{commit}^"])
        file_count, effective_lines, binary_files = diff_stats(parent, commit)
        warnings: list[str] = []
        failures: list[str] = []

        if not step_subject.search(subject):
            warnings.append("commit subject does not use pair(step:<id>): marker")
        if file_count > args.preferred_files:
            warnings.append(
                f"changes {file_count} files (preferred <= {args.preferred_files})"
            )
        if effective_lines > args.preferred_lines:
            warnings.append(
                f"changes {effective_lines} effective lines "
                f"(preferred <= {args.preferred_lines})"
            )

        allowed = any(commit.startswith(prefix) for prefix in args.allow_hard_limit)
        if effective_lines > args.hard_lines:
            message = (
                f"changes {effective_lines} effective lines "
                f"(hard limit {args.hard_lines})"
            )
            if allowed:
                warnings.append(message + "; acknowledged size exception")
            else:
                failures.append(
                    message
                    + "; record size_exception_reason and rerun with "
                    f"--allow-hard-limit {commit[:12]}"
                )

        if binary_files:
            warnings.append(
                "binary files are excluded from effective-line count: "
                + ", ".join(binary_files)
            )

        reports.append(
            CommitReport(
                commit=commit,
                subject=subject,
                files=file_count,
                effective_diff_lines=effective_lines,
                binary_files=binary_files,
                warnings=warnings,
                failures=failures,
            )
        )

    guide_tree = git(["rev-parse", f"{args.guide}^{{tree}}"])
    solution_tree = None
    final_tree_equal = None
    if args.solution:
        solution_tree = git(["rev-parse", f"{args.solution}^{{tree}}"])
        final_tree_equal = guide_tree == solution_tree
        if not final_tree_equal:
            global_warnings.append(
                "Guide and Shadow solution final trees differ; behavioral equivalence "
                "must be verified and intentional differences documented"
            )

    failure_count = len(global_failures) + sum(len(r.failures) for r in reports)
    warning_count = len(global_warnings) + sum(len(r.warnings) for r in reports)

    result = {
        "base": git(["rev-parse", args.base]),
        "guide": git(["rev-parse", args.guide]),
        "solution": git(["rev-parse", args.solution]) if args.solution else None,
        "guide_tree": guide_tree,
        "solution_tree": solution_tree,
        "final_tree_equal": final_tree_equal,
        "commit_count": len(commits),
        "warnings": global_warnings,
        "failures": global_failures,
        "commits": [asdict(r) for r in reports],
        "summary": {
            "warning_count": warning_count,
            "failure_count": failure_count,
            "status": "failed" if failure_count else ("warnings" if warning_count else "passed"),
        },
    }

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Guide: {args.guide} ({len(commits)} commits)")
        for report in reports:
            print(
                f"- {report.commit[:12]}  files={report.files}  "
                f"lines={report.effective_diff_lines}  {report.subject}"
            )
            for warning in report.warnings:
                print(f"  WARN: {warning}")
            for failure in report.failures:
                print(f"  FAIL: {failure}")
        for warning in global_warnings:
            print(f"WARN: {warning}")
        for failure in global_failures:
            print(f"FAIL: {failure}")
        print(
            f"Result: {result['summary']['status']} "
            f"({warning_count} warnings, {failure_count} failures)"
        )

    return 1 if failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
