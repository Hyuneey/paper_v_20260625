"""Run the independent TASK-039E1 private-ledger replay audit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

from paperworks.v6.task039e1_final_audit_v1 import (
    AUDIT_PREP_COMMIT,
    DATA_ACCESS_AUDIT_HASH,
    D1_DIRECTIONAL_LEDGER_HASH,
    D1_SOURCE_LEDGER_HASH,
    D1_TARGET_LEDGER_HASH,
    D2_CONFIRMATION_LEDGER_HASH,
    E1_COMMIT_A,
    E1_COMMIT_B,
    E1_PRIVATE_LEDGER_HASH,
    EXECUTION_RECEIPT_HASH,
    MATERIALIZATION_RESULT_HASH,
    PRIVATE_AUDIT_LEDGER_NAME,
    PRIVATE_D2_LEDGER_NAME,
    PRIVATE_DIRECTIONAL_LEDGER_NAME,
    PRIVATE_E1_LEDGER_NAME,
    PRIVATE_SOURCE_LEDGER_NAME,
    PRIVATE_TARGET_LEDGER_NAME,
    PUBLIC_COHORT_HASH,
    PUBLIC_MANIFEST_HASH,
    TASK039E1FinalAuditError,
    WINDOW_BUNDLE_HASH,
    assert_public_safe_v1,
    audit_replay_ledger_v1,
    build_audit_artifact_v1,
    build_e2_authorization_v1,
    independent_resolve_reference_v1,
    independently_replay_materialization_v1,
    read_json_v1,
    reconstruct_public_result_artifacts_v1,
    schema_documents_v1,
    validate_external_roots_v1,
    validate_ledger_v1,
    verify_self_hash_v1,
    write_json_v1,
)


PUBLIC_INPUTS = {
    "window": ("TASK-039E1_WINDOW_CONSTANT_BUNDLE.json", WINDOW_BUNDLE_HASH),
    "private_binding": ("TASK-039E1_PRIVATE_LEDGER_BINDING.json", None),
    "manifest": ("TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json", PUBLIC_MANIFEST_HASH),
    "cohort": ("TASK-039E1_CONSTRUCTION_EVIDENCE_COHORT.json", PUBLIC_COHORT_HASH),
    "result": ("TASK-039E1_MATERIALIZATION_RESULT.json", MATERIALIZATION_RESULT_HASH),
    "access": ("TASK-039E1_DATA_ACCESS_AUDIT.json", DATA_ACCESS_AUDIT_HASH),
    "receipt": ("TASK-039E1_EXECUTION_RECEIPT.json", EXECUTION_RECEIPT_HASH),
}
AUTHORIZED_B_CHANGES = {
    "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_COHORT.json",
    "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
    "docs/task_reports/TASK-039E1_DATA_ACCESS_AUDIT.json",
    "docs/task_reports/TASK-039E1_EXECUTION_RECEIPT.json",
    "docs/task_reports/TASK-039E1_MATERIALIZATION_RESULT.json",
    "docs/task_reports/TASK-039E1_PRIVATE_LEDGER_BINDING.json",
    "docs/task_reports/TASK-039E1_REPORT.md",
    "docs/task_reports/TASK-039E1_WINDOW_CONSTANT_BUNDLE.json",
}


def _git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=root, text=True, encoding="utf-8"
    ).strip()


def _private_file(root: Path, name: str) -> Path:
    path = (root / name).resolve(strict=True)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise TASK039E1FinalAuditError(
            "private artifact escaped its custody root"
        ) from exc
    return path


def _verify_git_preflight(root: Path, audit_execution_code_commit: str) -> None:
    if _git(root, "rev-parse", "HEAD") != audit_execution_code_commit:
        raise TASK039E1FinalAuditError("audit must run from exact clean Audit Commit A")
    if _git(root, "status", "--porcelain"):
        raise TASK039E1FinalAuditError("audit worktree must be clean before private replay")
    for ancestor in (E1_COMMIT_A, E1_COMMIT_B, AUDIT_PREP_COMMIT):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
            cwd=root,
            check=False,
        )
        if result.returncode != 0:
            raise TASK039E1FinalAuditError("required audit lineage is not an ancestor")
    changed = set(
        filter(None, _git(root, "diff", "--name-only", E1_COMMIT_A, E1_COMMIT_B).splitlines())
    )
    if changed != AUTHORIZED_B_CHANGES:
        raise TASK039E1FinalAuditError("failed_task039e1_commit_separation_audit")


def _validate_public_preflight(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    reports = root / "docs" / "task_reports"
    authorization = read_json_v1(reports / "TASK-039E1_AUTHORIZATION.json")
    verify_self_hash_v1(authorization, expected_hash="03ad2a9e534d553cad75aa811090c1255988156bf1d2a217fb6b883620e05580")
    required_authority = {
        "confirmed_relation_count": 42,
        "d1_source_private_ledger_read_authorized": True,
        "d1_target_private_ledger_read_authorized": True,
        "d1_directional_private_ledger_read_authorized": True,
        "d2_private_confirmation_ledger_read_authorized": True,
        "hai_access_authorized": False,
        "llm_calls_authorized": False,
        "rule_v2_materialization_authorized": False,
        "detector_runtime_authorized": False,
    }
    if any(authorization.get(key) != value for key, value in required_authority.items()):
        raise TASK039E1FinalAuditError("E1 authorization differs from the frozen boundary")
    cohort = read_json_v1(reports / "TASK-039E0_CONFIRMED_RELATION_COHORT.json")
    verify_self_hash_v1(cohort, expected_hash="e71fa69999dbc18310ebb1730fd1d0ea36403763e891b99841ab8cef7ec18732")
    artifacts: dict[str, dict[str, Any]] = {}
    for key, (name, expected_hash) in PUBLIC_INPUTS.items():
        document = read_json_v1(reports / name)
        observed = verify_self_hash_v1(document, expected_hash=expected_hash)
        if key == "private_binding" and document.get("private_ledger_hash") != E1_PRIVATE_LEDGER_HASH:
            raise TASK039E1FinalAuditError("E1 private-ledger public binding differs")
        if observed != document["artifact_hash"]:
            raise TASK039E1FinalAuditError("public artifact hash mismatch")
        assert_public_safe_v1(document)
        artifacts[key] = document
    return cohort, artifacts


def _negative_resolver_checks(private: Mapping[str, Any]) -> None:
    binding = private["numeric_bindings"][0]
    kwargs = {
        "proposal_numeric_reference": binding["numeric_reference"],
        "relation_binding_hash": private["relation_binding_hash"],
        "numeric_role": binding["numeric_role"],
        "private_evidence_record_hash": private["artifact_hash"],
        "private_evidence": private,
    }
    mutations = (
        {"relation_binding_hash": "0" * 64},
        {"numeric_role": "target_noise_scale"},
        {"proposal_numeric_reference": "0" * 64},
        {"private_evidence_record_hash": "0" * 64},
    )
    for mutation in mutations:
        try:
            independent_resolve_reference_v1(**{**kwargs, **mutation})
        except TASK039E1FinalAuditError:
            pass
        else:
            raise TASK039E1FinalAuditError("independent resolver accepted a mismatched field")
    unapproved = dict(private)
    unapproved["construction_evidence_status"] = "rejected"
    try:
        independent_resolve_reference_v1(**{**kwargs, "private_evidence": unapproved})
    except TASK039E1FinalAuditError:
        pass
    else:
        raise TASK039E1FinalAuditError("independent resolver accepted unapproved evidence")


def _compare_public_reconstruction(
    replay: Mapping[str, Any], public: Mapping[str, Mapping[str, Any]]
) -> None:
    reconstructed = reconstruct_public_result_artifacts_v1(replay)
    expected = {
        "window": replay["window"],
        "private_binding": replay["private_binding"],
        "manifest": replay["manifest"],
        "cohort": replay["cohort"],
        **reconstructed,
    }
    for key, document in expected.items():
        if document != public[key]:
            raise TASK039E1FinalAuditError("failed_task039e1_public_reconstruction")


def _report(audit: Mapping[str, Any], e2: Mapping[str, Any]) -> str:
    return f"""# TASK-039E1 Final Audit

## Status

`{audit['status']}`

Readiness: `{audit['readiness']}`

## Independent replay

- E1 Commit A/B separation: verified
- D1 source/target/directional private ledgers: verified
- D2 confirmation private ledger: verified
- E1 private construction-evidence ledger: verified
- private records independently reproduced: `42`
- numeric bindings and references independently reproduced: `462`
- each of the 11 frozen numeric roles occurs exactly `42` times
- D0 window bundle reproduced: `{WINDOW_BUNDLE_HASH}`
- positive resolver replays: `462`
- resolver mismatch and unapproved-evidence guards: passed

## Public reconstruction

- confirmed relation primitives: `42`
- approved numeric evidence bundles: `42`
- public manifest entries: `42`
- public manifest: `{PUBLIC_MANIFEST_HASH}`
- construction-evidence cohort: `{PUBLIC_COHORT_HASH}`
- materialization result: `{MATERIALIZATION_RESULT_HASH}`
- byte-semantic equality with committed public artifacts: verified

## Boundaries

- HAI accessed by audit: `false`
- private numeric values public: `false`
- original ledgers modified: `false`
- LLM called: `false`
- rule generated: `false`
- runtime authority: `false`
- E2 authorization: `{e2['artifact_hash']}`
- E2 authority: configuration/protocol freeze only
- real T0/T1/T1-B/T2 generation: unauthorized
"""


def write_schemas(root: Path) -> None:
    for name, document in schema_documents_v1().items():
        write_json_v1(root / "schemas" / "v6" / f"{name}_schema.json", document, public=False)


def execute(
    *,
    root: Path,
    d1_private_value: str,
    d2_private_value: str,
    e1_private_value: str,
    audit_private_value: str,
    audit_execution_code_commit: str,
) -> dict[str, str]:
    _verify_git_preflight(root, audit_execution_code_commit)
    cohort, public = _validate_public_preflight(root)

    d1_root, d2_root, e1_root, audit_root = validate_external_roots_v1(
        repository_root=root,
        d1_private_value=d1_private_value,
        d2_private_value=d2_private_value,
        e1_private_value=e1_private_value,
        audit_private_value=audit_private_value,
    )
    source_document = read_json_v1(_private_file(d1_root, PRIVATE_SOURCE_LEDGER_NAME))
    target_document = read_json_v1(_private_file(d1_root, PRIVATE_TARGET_LEDGER_NAME))
    d1_document = read_json_v1(_private_file(d1_root, PRIVATE_DIRECTIONAL_LEDGER_NAME))
    d2_document = read_json_v1(_private_file(d2_root, PRIVATE_D2_LEDGER_NAME))
    e1_document = read_json_v1(_private_file(e1_root, PRIVATE_E1_LEDGER_NAME))
    source = validate_ledger_v1(
        source_document, expected_hash=D1_SOURCE_LEDGER_HASH,
        expected_type="task039d1_source_parameter_ledger_v1", expected_count=12,
    )
    target = validate_ledger_v1(
        target_document, expected_hash=D1_TARGET_LEDGER_HASH,
        expected_type="task039d1_target_parameter_ledger_v1", expected_count=12,
    )
    d1 = validate_ledger_v1(
        d1_document, expected_hash=D1_DIRECTIONAL_LEDGER_HASH,
        expected_type="task039d1_directional_fit_ledger_v1", expected_count=94,
    )
    d2 = validate_ledger_v1(
        d2_document, expected_hash=D2_CONFIRMATION_LEDGER_HASH,
        expected_type="task039d2_directional_confirmation_ledger_v1", expected_count=45,
    )
    validate_ledger_v1(
        e1_document, expected_hash=E1_PRIVATE_LEDGER_HASH,
        expected_type="task039e1_private_construction_evidence_ledger_v1", expected_count=42,
    )

    replay = independently_replay_materialization_v1(
        cohort_document=cohort, source_records=source, target_records=target,
        d1_records=d1, d2_records=d2,
    )
    if replay["private_ledger"] != e1_document:
        raise TASK039E1FinalAuditError("failed_task039e1_private_ledger_audit")
    if replay["private_ledger"]["artifact_hash"] != E1_PRIVATE_LEDGER_HASH:
        raise TASK039E1FinalAuditError("failed_task039e1_numeric_reference_replay")
    _negative_resolver_checks(replay["private_ledger"]["records"][0])
    _compare_public_reconstruction(replay, public)

    private_audit = audit_replay_ledger_v1(
        replay["private_ledger"]["records"],
        audit_execution_code_commit=audit_execution_code_commit,
    )
    write_json_v1(audit_root / PRIVATE_AUDIT_LEDGER_NAME, private_audit, public=False)
    verify_self_hash_v1(read_json_v1(audit_root / PRIVATE_AUDIT_LEDGER_NAME), expected_hash=private_audit["artifact_hash"])

    # Re-read and re-hash every original ledger after the only private write.
    for path, expected in (
        (_private_file(d1_root, PRIVATE_SOURCE_LEDGER_NAME), D1_SOURCE_LEDGER_HASH),
        (_private_file(d1_root, PRIVATE_TARGET_LEDGER_NAME), D1_TARGET_LEDGER_HASH),
        (_private_file(d1_root, PRIVATE_DIRECTIONAL_LEDGER_NAME), D1_DIRECTIONAL_LEDGER_HASH),
        (_private_file(d2_root, PRIVATE_D2_LEDGER_NAME), D2_CONFIRMATION_LEDGER_HASH),
        (_private_file(e1_root, PRIVATE_E1_LEDGER_NAME), E1_PRIVATE_LEDGER_HASH),
    ):
        verify_self_hash_v1(read_json_v1(path), expected_hash=expected)

    e2 = build_e2_authorization_v1()
    audit = build_audit_artifact_v1(
        audit_execution_code_commit=audit_execution_code_commit,
        audit_replay_ledger_hash=private_audit["artifact_hash"],
        e2_authorization_hash=e2["artifact_hash"],
    )
    schemas = schema_documents_v1()
    if set(audit) != set(schemas["task039e1_final_audit_v1"]["required"]):
        raise TASK039E1FinalAuditError("audit artifact differs from its closed schema")
    if set(e2) != set(schemas["task039e2_authorization_v1"]["required"]):
        raise TASK039E1FinalAuditError("E2 authorization differs from its closed schema")
    reports = root / "docs" / "task_reports"
    write_json_v1(reports / "TASK-039E1_FINAL_AUDIT.json", audit, public=True)
    write_json_v1(reports / "TASK-039E2_AUTHORIZATION.json", e2, public=True)
    (reports / "TASK-039E1_FINAL_AUDIT.md").write_text(
        _report(audit, e2), encoding="utf-8", newline="\n"
    )
    return {
        "audit_artifact_hash": audit["artifact_hash"],
        "audit_replay_ledger_hash": private_audit["artifact_hash"],
        "e2_authorization_hash": e2["artifact_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-schemas-only", action="store_true")
    parser.add_argument("--audit-execution-code-commit")
    parser.add_argument("--d1-private-root", default=os.environ.get("TASK039D_PRIVATE_ROOT", ""))
    parser.add_argument("--d2-private-root", default=os.environ.get("TASK039D2_PRIVATE_ROOT", ""))
    parser.add_argument("--e1-private-root", default=os.environ.get("TASK039E1_PRIVATE_ROOT", ""))
    parser.add_argument("--audit-private-root", default=os.environ.get("TASK039E1_AUDIT_PRIVATE_ROOT", ""))
    args = parser.parse_args()
    root = args.repository_root.resolve(strict=True)
    if args.write_schemas_only:
        write_schemas(root)
        return 0
    if not args.audit_execution_code_commit:
        parser.error("--audit-execution-code-commit is required")
    result = execute(
        root=root,
        d1_private_value=args.d1_private_root,
        d2_private_value=args.d2_private_root,
        e1_private_value=args.e1_private_root,
        audit_private_value=args.audit_private_root,
        audit_execution_code_commit=args.audit_execution_code_commit,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
