"""Execute TASK-039C-STAT from the exact clean implementation commit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.candidates.statistical_candidate_discovery_v1 import (  # noqa: E402
    EXPECTED_BASE_COMMIT,
    EXPECTED_BRANCH,
    EXPECTED_FILES,
    STATDataAccessLedgerV1,
    StatisticalCandidateDiscoveryError,
    build_data_access_audit_v1,
    build_private_ledger_v1,
    build_public_result_v1,
    discover_statistical_candidates_v1,
    load_frozen_c0_bundle_v1,
    load_verified_file_identities_v1,
    read_authorized_stat_file_v1,
    verify_vectorized_parity_v1,
)


COMMIT_A_MESSAGE = "TASK-039C-STAT implement statistical discovery"
COMMIT_A_PATHS = frozenset(
    {
        "schemas/v6/statistical_candidate_result_v1_schema.json",
        "scripts/run_task039c_stat.py",
        "src/paperworks/candidates/statistical_candidate_discovery_v1.py",
        "tests/test_task039c_stat.py",
    }
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--hai-root", type=Path, required=True)
    parser.add_argument("--private-output-root", type=Path, required=True)
    parser.add_argument("--public-output-root", type=Path, required=True)
    parser.add_argument("--execution-code-commit", required=True)
    return parser.parse_args()


def _git(repository: Path, *arguments: str) -> str:
    command = [
        "git",
        "-c",
        f"safe.directory={repository.as_posix()}",
        "-C",
        str(repository),
        *arguments,
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc
    return completed.stdout.strip()


def _assert_clean_commit_a(repository: Path, execution_code_commit: str) -> None:
    if (
        len(execution_code_commit) != 40
        or _git(repository, "rev-parse", "--abbrev-ref", "HEAD") != EXPECTED_BRANCH
        or _git(repository, "rev-parse", "HEAD") != execution_code_commit
        or _git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")
    try:
        count = int(_git(repository, "rev-list", "--count", f"{EXPECTED_BASE_COMMIT}..HEAD"))
    except ValueError as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc
    changed = frozenset(
        item
        for item in _git(
            repository, "diff", "--name-only", f"{EXPECTED_BASE_COMMIT}..HEAD"
        ).splitlines()
        if item
    )
    if (
        count != 1
        or changed != COMMIT_A_PATHS
        or _git(repository, "log", "-1", "--format=%s") != COMMIT_A_MESSAGE
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")


def _assert_roots(
    repository: Path, data_root: Path, private_root: Path, public_root: Path
) -> None:
    if (
        data_root == repository
        or repository in data_root.parents
        or private_root == repository
        or repository in private_root.parents
        or public_root != repository / "docs" / "task_reports"
        or data_root == private_root
        or data_root in private_root.parents
        or private_root in data_root.parents
    ):
        raise StatisticalCandidateDiscoveryError("failed_stat_data_boundary")


def _write_new_json(path: Path, document: Mapping[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, indent=2, sort_keys=True, ensure_ascii=True)
            handle.write("\n")
    except OSError as exc:
        raise StatisticalCandidateDiscoveryError(
            "failed_stat_protocol_compliance"
        ) from exc


def main() -> int:
    args = _arguments()
    repository = args.repository_root.resolve()
    data_root = args.hai_root.resolve()
    private_root = args.private_output_root.resolve()
    public_root = args.public_output_root.resolve()
    _assert_clean_commit_a(repository, args.execution_code_commit)
    _assert_roots(repository, data_root, private_root, public_root)

    private_path = private_root / "TASK-039C_STAT_PRIVATE_LEDGER.json"
    audit_path = public_root / "TASK-039C_STAT_DATA_ACCESS_AUDIT.json"
    result_path = public_root / "TASK-039C_STAT_RESULT.json"
    if any(path.exists() for path in (private_path, audit_path, result_path)):
        raise StatisticalCandidateDiscoveryError("failed_stat_protocol_compliance")

    bundle = load_frozen_c0_bundle_v1(repository)
    identities = load_verified_file_identities_v1(repository)
    if tuple(item.relative_path for item in identities) != EXPECTED_FILES:
        raise StatisticalCandidateDiscoveryError("failed_stat_file_identity")
    columns = bundle.universe_policy.source_variables + bundle.universe_policy.target_variables

    # The precommitted independent parity gate runs before either real file opens.
    verify_vectorized_parity_v1()
    access_ledger = STATDataAccessLedgerV1(allowed_columns=columns)
    matrices = tuple(
        read_authorized_stat_file_v1(
            data_root=data_root,
            identity=identity,
            columns=columns,
            bundle=bundle,
            ledger=access_ledger,
        )
        for identity in identities
    )
    ranked = discover_statistical_candidates_v1(
        bundle=bundle,
        train1=matrices[0],
        train2=matrices[1],
    )
    created_at = datetime.now(timezone.utc).isoformat()
    private_document = build_private_ledger_v1(
        ranked_pairs=ranked,
        execution_code_commit=args.execution_code_commit,
        created_at=created_at,
    )
    audit_document = build_data_access_audit_v1(
        ledger=access_ledger,
        private_ledger_hash=private_document["artifact_hash"],
        execution_code_commit=args.execution_code_commit,
        created_at=created_at,
    )
    result_document = build_public_result_v1(
        ranked_pairs=ranked,
        private_ledger_hash=private_document["artifact_hash"],
        data_access_audit_hash=audit_document["artifact_hash"],
        execution_code_commit=args.execution_code_commit,
        created_at=created_at,
    )

    private_root.mkdir(parents=True, exist_ok=True)
    _write_new_json(private_path, private_document)
    _write_new_json(audit_path, audit_document)
    _write_new_json(result_path, result_document)
    print(
        json.dumps(
            {
                "status": result_document["status"],
                "evaluated_pair_count": result_document["evaluated_pair_count"],
                "supported_stable_count": result_document["supported_stable_count"],
                "direction_unstable_count": result_document["direction_unstable_count"],
                "ranking_hash": result_document["ranking_hash"],
                "data_access_audit_hash": audit_document["artifact_hash"],
                "artifact_hash": result_document["artifact_hash"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
