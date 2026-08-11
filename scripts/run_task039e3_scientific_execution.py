#!/usr/bin/env python3
"""Run authorized TASK-039E3 from one exact clean execution commit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from paperworks.v6.task039e3_live_transport_v1 import LiveOpenAIChatCompletionsTransportV1
from paperworks.v6.task039e3_scientific_execution_v1 import (
    compute_scientific_source_hashes_v1,
    run_authorized_scientific_execution_v1,
    validate_git_execution_state_v1,
    validate_private_roots_v1,
    validate_public_preflight_v1,
    write_public_artifacts_v1,
)


def _report(artifacts: dict[str, dict[str, object]]) -> str:
    if "receipt" in artifacts:
        summary = artifacts["summary"]
        return "\n".join(
            [
                "# TASK-039E3 Scientific Execution Report",
                "",
                f"Status: `{summary['status']}`",
                "",
                "The exact frozen construction-only protocol completed for all 42 relations.",
                "No HAI, labels, attacks, detector utility, Rule v2, or runtime authority was used.",
                "Individual proposals and calibrated private evidence remain outside Git.",
                "",
                f"Scientific calls: `{summary['scientific_calls']}`.",
                f"Transport attempts: `{summary['transport_attempts']}`.",
                "Winner selected: `false`.",
                "Next required task: `TASK-039E3-AUDIT`.",
                "",
            ]
        )
    if "failure" in artifacts:
        failure = artifacts["failure"]
        return "\n".join(
            [
                "# TASK-039E3 Scientific Execution Failure",
                "",
                f"Status: `{failure['status']}`",
                "",
                f"Failure classification: `{failure['failure_classification']}`.",
                "The run failed closed. Automatic resume and relation skipping remain unauthorized.",
                "No Rule v2 or runtime authority was created.",
                "",
            ]
        )
    capability = artifacts["capability"]
    return "\n".join(
        [
            "# TASK-039E3 Capability Gate",
            "",
            f"Status: `{capability['status']}`",
            "",
            "The non-scientific capability probe did not authorize scientific calls.",
            "No model fallback or configuration modification was used.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--expected-execution-commit", required=True)
    args = parser.parse_args()
    repository = Path(args.repository_root).resolve(strict=True)

    # These validations intentionally precede both private evidence and credentials.
    preflight = validate_public_preflight_v1(repository)
    validate_git_execution_state_v1(
        repository, expected_execution_commit=args.expected_execution_commit
    )
    e1_value = os.environ.get("TASK039E1_PRIVATE_ROOT", "")
    e3_value = os.environ.get("TASK039E3_PRIVATE_ROOT", "")
    e1_root, e3_root = validate_private_roots_v1(
        repository_root=repository,
        e1_private_value=e1_value,
        e3_private_value=e3_value,
    )

    # This is the only credential read in the live E3 path.
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({
            "status": "blocked_task039e3_credential_unavailable",
            "provider_contacted": False,
            "scientific_calls": 0,
        }, sort_keys=True))
        return 3

    source_hashes = compute_scientific_source_hashes_v1(repository)
    transport = LiveOpenAIChatCompletionsTransportV1(api_key=api_key)
    artifacts = run_authorized_scientific_execution_v1(
        repository_root=repository,
        execution_commit=args.expected_execution_commit,
        e1_private_root=e1_root,
        e3_private_root=e3_root,
        transport=transport,
        preflight=preflight,
        source_hashes=source_hashes,
    )
    write_public_artifacts_v1(repository, artifacts)
    report_path = repository / "docs" / "task_reports" / "TASK-039E3_REPORT.md"
    with report_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(_report(artifacts))
    status = (
        artifacts["receipt"]["status"]
        if "receipt" in artifacts
        else artifacts["failure"]["status"]
        if "failure" in artifacts
        else artifacts["capability"]["status"]
    )
    print(json.dumps({"status": status}, sort_keys=True))
    return 0 if "receipt" in artifacts else 4


if __name__ == "__main__":
    sys.exit(main())
