"""Run TASK-039C-META from one exact clean implementation commit.

The runner reads only the public C0 freeze, an ignored reviewed-metadata
declaration, the pinned official technical manual bytes for identity
verification, and the pinned official P1 physical graph.  It has no CSV input.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from paperworks.candidates.metadata_candidate_discovery_v1 import (  # noqa: E402
    MetadataCandidateDiscoveryError,
    assert_public_metadata_payload_v1,
    build_metadata_candidate_result_v1,
    data_access_audit_payload_v1,
    discover_metadata_pair_records_v1,
    evidence_ledger_payload_v1,
    load_frozen_c0_universe_v1,
    load_official_physical_graph_v1,
    load_reviewed_metadata_evidence_v1,
    verify_official_reference_file_v1,
)
from paperworks.v6.common import canonical_json_v1  # noqa: E402


C0_CONFIG = REPOSITORY_ROOT / "configs/v6/task039c0_candidate_discovery_protocol.json"
C0_BUNDLE = REPOSITORY_ROOT / "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json"
RESULT_SCHEMA = REPOSITORY_ROOT / "schemas/v6/metadata_candidate_result_v1_schema.json"
PUBLIC_RESULT = REPOSITORY_ROOT / "docs/task_reports/TASK-039C_META_RESULT.json"
PUBLIC_AUDIT = REPOSITORY_ROOT / "docs/task_reports/TASK-039C_META_DATA_ACCESS_AUDIT.json"
PUBLIC_REPORT = REPOSITORY_ROOT / "docs/task_reports/TASK-039C_META_REPORT.md"
PRIVATE_LEDGER = (
    REPOSITORY_ROOT
    / "artifacts/task039c_meta/TASK-039C_META_EVIDENCE_LEDGER.json"
)
DEFAULT_EVIDENCE_INPUT = (
    REPOSITORY_ROOT
    / "artifacts/task039c_meta/TASK-039C_META_REVIEWED_EVIDENCE_INPUT.json"
)
REQUIRED_BASE = "b6522fb83c4cb92d355f98af778f9a6a3c73362f"
REMOTE_BRANCH = "origin/task-039c-meta"


def _run_git(arguments: Sequence[str], *, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _git_success(arguments: Sequence[str]) -> bool:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.returncode == 0


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MetadataCandidateDiscoveryError(f"{path.name} is not a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _verify_execution_state(expected_code_commit: str) -> None:
    head = _run_git(["rev-parse", "HEAD"])
    if head != expected_code_commit:
        raise MetadataCandidateDiscoveryError("execution HEAD is not exact Commit A")
    if _run_git(["status", "--porcelain=v1"]):
        raise MetadataCandidateDiscoveryError("execution worktree is not clean")
    if not _git_success(["merge-base", "--is-ancestor", REQUIRED_BASE, "HEAD"]):
        raise MetadataCandidateDiscoveryError("Commit A does not descend from frozen C0")
    if not _git_success(["merge-base", "--is-ancestor", REMOTE_BRANCH, "HEAD"]):
        raise MetadataCandidateDiscoveryError("META execution diverged from its remote base")
    left_right = _run_git(["rev-list", "--left-right", "--count", f"{REMOTE_BRANCH}...HEAD"])
    counts = tuple(int(item) for item in left_right.split())
    if counts != (0, 1):
        raise MetadataCandidateDiscoveryError(
            "Commit A must be exactly one clean commit ahead of the remote C0 base"
        )


def _verify_ignored_evidence_input(path: Path) -> None:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise MetadataCandidateDiscoveryError(
            "reviewed evidence input must remain in ignored repository storage"
        ) from exc
    if relative.as_posix() != (
        "artifacts/task039c_meta/TASK-039C_META_REVIEWED_EVIDENCE_INPUT.json"
    ):
        raise MetadataCandidateDiscoveryError("reviewed evidence input location changed")
    completed = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", relative.as_posix()],
        cwd=REPOSITORY_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise MetadataCandidateDiscoveryError("reviewed evidence input is not ignored")


def _report_markdown(result: Mapping[str, Any]) -> str:
    tiers = result["tier_counts"]
    shortfall = result["candidate_shortfall"]
    return "\n".join(
        (
            "# TASK-039C-META Report",
            "",
            f"Status: `{result['status']}`",
            "",
            "## Result",
            "",
            "The exact frozen P1 Boiler 144-pair universe was ranked using only",
            "the pinned official HAI technical manual, the approved official P1",
            "physical graph, reviewed tag mappings, and the five documented P1",
            "control subsystems. Unsupported pairs remain only in the private",
            "self-hashed audit ledger and never pad a top-K view.",
            "",
            f"- Evaluated pairs: {result['evaluated_pair_count']}",
            f"- Supported pairs: {result['supported_count']}",
            f"- Unsupported pairs: {result['unsupported_count']}",
            f"- M1 explicit: {tiers['M1_EXPLICIT']}",
            f"- M2 graph adjacent: {tiers['M2_GRAPH_ADJACENT']}",
            f"- M3 subsystem supported: {tiers['M3_SUBSYSTEM_SUPPORTED']}",
            f"- Top10 returned: {len(result['top10_identities'])}",
            f"- Top20 returned: {len(result['top20_identities'])}",
            f"- Top40 returned: {len(result['top40_identities'])}",
            (
                "- Candidate shortfall: "
                + ", ".join(
                    f"{key}={str(value['candidate_shortfall']).lower()}"
                    for key, value in shortfall.items()
                )
            ),
            "",
            "## Identity and boundary",
            "",
            f"- Result hash: `{result['artifact_hash']}`",
            f"- Evidence-ledger hash: `{result['evidence_ledger_hash']}`",
            f"- Data-access audit hash: `{result['data_access_audit_ref']}`",
            "- Real HAI feature values accessed: `false`",
            "- BR2 pair supervision used: `false`",
            "- Cross-arm score used: `false`",
            "- Numerical weighting used: `false`",
            "- Official graph role: `weak_relation_reference_not_causal_truth`",
            "",
            "This artifact claims candidate priority only. It does not claim",
            "causality, delayed-response validation, anomaly rules, confirmed",
            "normal relations, or root cause.",
            "",
        )
    )


def run(
    *,
    official_checkout: Path,
    evidence_input_path: Path,
    expected_code_commit: str,
    created_at: str,
) -> dict[str, Any]:
    _verify_execution_state(expected_code_commit)
    _verify_ignored_evidence_input(evidence_input_path)

    manual_path = official_checkout / "hai_dataset_technical_details.pdf"
    graph_path = official_checkout / "graph/boiler/phy_boiler.json"
    verify_official_reference_file_v1(
        path=manual_path, reference_kind="technical_manual"
    )
    graph = load_official_physical_graph_v1(graph_path)
    evidence = load_reviewed_metadata_evidence_v1(evidence_input_path)
    universe = load_frozen_c0_universe_v1(
        config_payload=_load_json(C0_CONFIG),
        bundle_payload=_load_json(C0_BUNDLE),
    )
    records = discover_metadata_pair_records_v1(
        universe=universe, evidence=evidence, graph=graph
    )
    ledger = evidence_ledger_payload_v1(
        records=records, evidence_input_hash=evidence.evidence_input_hash
    )
    audit = data_access_audit_payload_v1(
        code_commit=expected_code_commit,
        created_at=created_at,
        evidence_input_hash=evidence.evidence_input_hash,
    )
    result = build_metadata_candidate_result_v1(
        records=records,
        code_commit=expected_code_commit,
        created_at=created_at,
        evidence_ledger_hash=str(ledger["artifact_hash"]),
        data_access_audit_ref=str(audit["artifact_hash"]),
    )

    schema = _load_json(RESULT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(result)
    assert_public_metadata_payload_v1(result)
    assert_public_metadata_payload_v1(audit)

    _write_json(PRIVATE_LEDGER, ledger)
    _write_json(PUBLIC_AUDIT, audit)
    _write_json(PUBLIC_RESULT, result)
    PUBLIC_REPORT.write_text(_report_markdown(result), encoding="utf-8")

    return {
        "candidate_shortfall": result["candidate_shortfall"],
        "data_access_audit_hash": audit["artifact_hash"],
        "evaluated_pair_count": result["evaluated_pair_count"],
        "evidence_ledger_hash": ledger["artifact_hash"],
        "result_hash": result["artifact_hash"],
        "status": result["status"],
        "supported_count": result["supported_count"],
        "tier_counts": result["tier_counts"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-checkout", type=Path, required=True)
    parser.add_argument("--evidence-input", type=Path, default=DEFAULT_EVIDENCE_INPUT)
    parser.add_argument("--expected-code-commit", required=True)
    parser.add_argument("--created-at", default="2026-08-10T00:00:00+09:00")
    args = parser.parse_args()
    try:
        summary = run(
            official_checkout=args.official_checkout,
            evidence_input_path=args.evidence_input,
            expected_code_commit=args.expected_code_commit,
            created_at=args.created_at,
        )
    except (MetadataCandidateDiscoveryError, OSError, ValueError) as exc:
        print(f"failed_metadata_candidate_contract: {exc}", file=sys.stderr)
        return 1
    print(canonical_json_v1(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
