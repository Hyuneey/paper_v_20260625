"""Freeze authoritative TASK-039E0 artifacts without private or HAI access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from paperworks.v6.common import canonical_json_v1
from paperworks.v6.task039e0_rule_construction_protocol_v1 import (
    ConstructionEvidenceMaterializationPolicyV1,
    ConstructionMetricPolicyV1,
    FairGenerationBudgetPolicyV2,
    LLMDirectNumberEvaluationPolicyV1,
    T1BSelectionPolicyV1,
    T2DeterministicControllerPolicyV1,
    TASK039E0ProtocolBundleV1,
    TASK039E0ProtocolError,
    TASK039E0ValidityPolicyV2,
    TASK039E1AuthorizationV1,
    load_confirmed_relation_cohort_v1,
    schema_for_example_v1,
    source_blob_sha256_v1,
    verify_self_hash_v1,
)
from paperworks.v6.task039e0_validity_v2 import (
    PreparedValidityResultV2,
    ValidityIssueV2,
)


ARTIFACT_FILES = {
    "confirmed_relation_identity_cohort_v1": "TASK-039E0_CONFIRMED_RELATION_COHORT.json",
    "fair_generation_budget_policy_v2": "TASK-039E0_BUDGET_POLICY.json",
    "t1b_selection_policy_v1": "TASK-039E0_T1B_SELECTION_POLICY.json",
    "t2_deterministic_controller_policy_v1": "TASK-039E0_CONTROLLER_POLICY.json",
    "task039e0_validity_policy_v2": "TASK-039E0_VALIDITY_POLICY.json",
    "construction_evidence_materialization_policy_v1": "TASK-039E0_EVIDENCE_MATERIALIZATION_POLICY.json",
    "llm_direct_number_evaluation_policy_v1": "TASK-039E0_DIRECT_NUMBER_POLICY.json",
    "construction_metric_policy_v1": "TASK-039E0_CONSTRUCTION_METRIC_POLICY.json",
    "task039e0_protocol_bundle_v1": "TASK-039E0_PROTOCOL_BUNDLE.json",
    "task039e1_authorization_v1": "TASK-039E1_AUTHORIZATION.json",
}

SCHEMA_FILES = {
    artifact_type: f"{artifact_type}_schema.json"
    for artifact_type in ARTIFACT_FILES
}
SCHEMA_FILES["task039e0_prepared_validity_result_v2"] = (
    "task039e0_prepared_validity_result_v2_schema.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TASK039E0ProtocolError(f"JSON object required: {path.name}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json_v1(value) + "\n", encoding="utf-8", newline="\n")


def _validate_public_input(path: Path, expected_hash: str) -> dict[str, Any]:
    document = _read_json(path)
    if document.get("artifact_hash") != expected_hash or not verify_self_hash_v1(document):
        raise TASK039E0ProtocolError(f"public input binding differs: {path.name}")
    return document


def build_artifacts(repository_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    reports = repository_root / "docs" / "task_reports"
    directional = _validate_public_input(
        reports / "TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json",
        "4f5057380c4b1b995bd0d5a714d307df556ce05094223fa909b6e2ed7dfec666",
    )
    _validate_public_input(
        reports / "TASK-039D2_PAIR_CONFIRMATION_SUMMARY.json",
        "3929e84c680422a75069d59e1bef756f054a476ecc95f3e4e9573c7dfe368ad5",
    )
    _validate_public_input(
        reports / "TASK-039D2_RESULT.json",
        "3b5bdce629b6ed2bcf26751fae4e870cb63cac1e9fd3e5d3022085615c3ad09d",
    )
    authorization = _validate_public_input(
        reports / "TASK-039E0_AUTHORIZATION.json",
        "d209b8332705535b8addc62e186e834288ab7c12f8454e8be85265321b663ae6",
    )
    if authorization.get("readiness") != "READY_FOR_TASK039E0":
        raise TASK039E0ProtocolError("E0 authorization readiness differs")

    cohort = load_confirmed_relation_cohort_v1(directional)
    budget = FairGenerationBudgetPolicyV2()
    t1b = T1BSelectionPolicyV1(budget.artifact_hash)
    prep_verifier_hash = source_blob_sha256_v1(
        repository_root, "src/paperworks/v6/task039e0_validity_v1.py"
    )
    validity = TASK039E0ValidityPolicyV2(budget.artifact_hash, prep_verifier_hash)
    controller = T2DeterministicControllerPolicyV1(
        budget.artifact_hash, validity.artifact_hash
    )
    materialization = ConstructionEvidenceMaterializationPolicyV1(
        cohort.artifact_hash, cohort.identity_list_hash
    )
    direct_number = LLMDirectNumberEvaluationPolicyV1(budget.artifact_hash)
    metrics = ConstructionMetricPolicyV1()
    bundle = TASK039E0ProtocolBundleV1(
        cohort_hash=cohort.artifact_hash,
        identity_list_hash=cohort.identity_list_hash,
        budget_policy_hash=budget.artifact_hash,
        t1b_selection_policy_hash=t1b.artifact_hash,
        controller_policy_hash=controller.artifact_hash,
        validity_policy_hash=validity.artifact_hash,
        materialization_policy_hash=materialization.artifact_hash,
        direct_number_policy_hash=direct_number.artifact_hash,
        metric_policy_hash=metrics.artifact_hash,
    )
    e1 = TASK039E1AuthorizationV1(
        protocol_bundle_hash=bundle.artifact_hash,
        cohort_hash=cohort.artifact_hash,
        identity_list_hash=cohort.identity_list_hash,
        materialization_policy_hash=materialization.artifact_hash,
    )
    artifacts = {
        item["artifact_type"]: item
        for item in (
            cohort.to_dict(), budget.to_dict(), t1b.to_dict(), controller.to_dict(),
            validity.to_dict(), materialization.to_dict(), direct_number.to_dict(),
            metrics.to_dict(), bundle.to_dict(), e1.to_dict(),
        )
    }
    sample_validity = PreparedValidityResultV2(
        proposal_hash="0" * 64,
        relation_binding_hash="1" * 64,
        evidence_bundle_hash="2" * 64,
        construction_provenance_hash="3" * 64,
        budget_policy_hash=budget.artifact_hash,
        status="rejected",
        issues=(
            ValidityIssueV2(
                code="VALIDITY_MALFORMED_DSL",
                field="proposal",
                repairability="repairable",
                t2_action_class="revise",
            ),
        ),
    ).to_dict()
    return artifacts, sample_validity


def freeze(repository_root: Path) -> dict[str, str]:
    root = repository_root.resolve()
    artifacts, sample_validity = build_artifacts(root)
    reports = root / "docs" / "task_reports"
    schemas = root / "schemas" / "v6"
    for artifact_type, filename in ARTIFACT_FILES.items():
        document = artifacts[artifact_type]
        _write_json(reports / filename, document)
        _write_json(schemas / SCHEMA_FILES[artifact_type], schema_for_example_v1(document))
    _write_json(
        schemas / SCHEMA_FILES["task039e0_prepared_validity_result_v2"],
        schema_for_example_v1(sample_validity),
    )

    bundle = artifacts["task039e0_protocol_bundle_v1"]
    cohort = artifacts["confirmed_relation_identity_cohort_v1"]
    e1 = artifacts["task039e1_authorization_v1"]
    report = f"""# TASK-039E0 Rule-Construction Protocol Freeze

Status: `passed_task039e0_rule_construction_protocol_freeze`

The audited public D2 result contributes exactly 42 confirmed directional
relation identities spanning 23 source-target pair contexts. No ranking or
candidate-method preference is created.

## Timing and budgets

The historical PREP V1 statement remains unchanged. Authoritative V2 records
that relation identities and their count were visible at budget freeze, while
private calibrated values, materialized evidence, proposals, validity results,
and utility results were not. This is a `methodological_timing_disclosure`.

- T0/T1/T1-B/T2 generation calls per relation: `0/1/3/max 3`.
- T1-B makes exactly three independent, feedback-free calls and selects the
  lowest admissible call index.
- T2 is deterministic, may retrieve once, and cannot add a fourth call.
- `no_rule` is a valid construction outcome, separate from transport failure
  and runtime abstention.

## Authority boundary

Main-arm numeric origin is deterministic calibrated evidence. The isolated
T1 direct-number ablation is one-shot and cannot grant validity or runtime
authority. E1 may materialize approved evidence from private ledgers without
opening HAI. No provider, proposal, Rule v2, Agent, detector, or runtime action
is authorized here.

- Confirmed identity-list hash: `{cohort['identity_list_hash']}`
- Confirmed cohort hash: `{cohort['artifact_hash']}`
- Protocol bundle hash: `{bundle['artifact_hash']}`
- E1 authorization hash: `{e1['artifact_hash']}`
"""
    (reports / "TASK-039E0_REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    return {
        "cohort_hash": str(cohort["artifact_hash"]),
        "identity_list_hash": str(cohort["identity_list_hash"]),
        "budget_hash": str(artifacts["fair_generation_budget_policy_v2"]["artifact_hash"]),
        "controller_hash": str(artifacts["t2_deterministic_controller_policy_v1"]["artifact_hash"]),
        "validity_hash": str(artifacts["task039e0_validity_policy_v2"]["artifact_hash"]),
        "metric_hash": str(artifacts["construction_metric_policy_v1"]["artifact_hash"]),
        "bundle_hash": str(bundle["artifact_hash"]),
        "e1_authorization_hash": str(e1["artifact_hash"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.repository_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
