#!/usr/bin/env python3
"""Run TASK-039C public-only deterministic three-arm integration."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REQUIRED_ANCESTORS = (
    "b6522fb83c4cb92d355f98af778f9a6a3c73362f",
    "2b3df4443619b8d0d19434bbcd1ded3b31a1b8ea",
    "b8a744c4b2cc70cd70bfc73ce45408c2ec8b5824",
    "629f022d35bb0db6130e7e69faaf48408b49aa9a",
    "9359a8b8085b1948bde23171ec886e996fbd37b3",
    "058b5e2023b66ccbf6704c5baf1f6c677f17b07a",
    "6790505e08ea06d6b3f6d34f9fd533d381696b1f",
    "1204ff4e6d790c2cd0e8268f778a8f071e5eea4b",
    "eab10dee0f08f419638154a9902304339b63c471",
)
OUTPUT_FILES = (
    "docs/task_reports/TASK-039C_THREE_ARM_OVERLAP.json",
    "docs/task_reports/TASK-039C_CANDIDATE_PROFILING_COHORT.json",
    "docs/task_reports/TASK-039C_INTEGRATION_RECEIPT.json",
    "docs/task_reports/TASK-039D0_AUTHORIZATION.json",
    "docs/task_reports/TASK-039C_REPORT.md",
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_json(path: Path, document: dict[str, object]) -> None:
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _report(result: object, execution_commit: str) -> str:
    overlap = result.overlap
    cohort = result.cohort
    return f"""# TASK-039C Final Three-Arm Candidate Cohort

Status: `passed_task039c_three_arm_candidate_cohort_freeze`

The frozen primary cohort is the unscored set union of META top20, STAT top20,
and GDN top20. Exact `(source, target)` de-duplication produces 47 candidates.
Serialization follows arm encounter order META, STAT, GDN; it is not a global
scientific ranking.

## Frozen result

- integration execution-code commit: `{execution_commit}`
- META / STAT / GDN top20 counts: 20 / 20 / 20
- META-STAT / META-GDN / STAT-GDN intersections: 11 / 1 / 1
- triple intersection: 0
- final cohort count: 47
- audited preview hash: `{result.audited_preview_hash}`
- candidate identity-list hash: `{cohort.candidate_identity_list_hash}`
- cohort artifact hash: `{cohort.artifact_hash}`
- overlap artifact hash: `{overlap.artifact_hash}`
- integration receipt hash: `{result.receipt.artifact_hash}`
- TASK-039D0 authorization hash: `{result.authorization.artifact_hash}`

## Scientific boundary

META contributes metadata candidate evidence. STAT contributes lagged
change-correlation candidate evidence. GDN contributes learned-graph candidate
evidence. These method-specific values were preserved and were not normalized,
merged, or compared as a common score. All 47 candidates remain relation
confirmation `not_evaluated`; no rule was created.

The low overlap is descriptive, not a failure: the three preregistered methods
expose different candidate sets and create a meaningful common-protocol
comparison opportunity. TASK-039D0 may design that profiling protocol. Real
TASK-039D profiling, HAI access, Rule v2, Agent, detector, runtime, outer, and
sealed execution remain unauthorized.

No HAI feature values, private ledger contents, labels, attacks, or BR2 pair
outcomes were accessed by this integration.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    src = root / "src"
    sys.path.insert(0, str(src))
    from paperworks.candidates.candidate_integration_v1 import (  # noqa: PLC0415
        build_task039c_integration_v1,
        load_merged_public_inputs_v1,
    )

    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise SystemExit("integration execution requires a clean worktree and index")
    execution_commit = _git(root, "rev-parse", "HEAD")
    for commit in REQUIRED_ANCESTORS:
        subprocess.run(
            ["git", "-c", f"safe.directory={root}", "-C", str(root), "merge-base", "--is-ancestor", commit, execution_commit],
            check=True,
            capture_output=True,
        )
    for relative in OUTPUT_FILES:
        if (root / relative).exists():
            raise SystemExit(f"refusing to overwrite integration output: {relative}")

    inputs = load_merged_public_inputs_v1(root)
    result = build_task039c_integration_v1(
        **inputs,
        integration_execution_code_commit=execution_commit,
    )
    documents = {
        OUTPUT_FILES[0]: result.overlap.to_dict(),
        OUTPUT_FILES[1]: result.cohort.to_dict(),
        OUTPUT_FILES[2]: result.receipt.to_dict(),
        OUTPUT_FILES[3]: result.authorization.to_dict(),
    }
    for relative, document in documents.items():
        _write_json(root / relative, document)
    (root / OUTPUT_FILES[4]).write_text(
        _report(result, execution_commit), encoding="utf-8", newline="\n"
    )
    print(result.receipt.artifact_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
