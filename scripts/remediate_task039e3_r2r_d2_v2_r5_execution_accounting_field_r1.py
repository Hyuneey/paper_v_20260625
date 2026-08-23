"""Public-only forensic remediation for the R5 accounting-field blocker.

This module never reads a scientific prediction, map, private evidence, label,
feature, or result payload.  It validates the frozen public accounting schema
and then fails closed if the committed R5 completion evidence is insufficient.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-EXECUTION-ACCOUNTING-FIELD-REMEDIATION-R1"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-r5-execution-accounting-field-remediation-r1"
BASE = "551a35ea2ba7618812c4bc9154c32d4ed9f8562f"
ACCOUNTING_HASH = "7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca"
R5_BLOCKER_HASH = "0ab5479d8e2f6367e214ddeceded63826d2d89d377f2aac00d2d909d5ab322e0"
R5_REPORT_HASH = "730d23ea6d29c679cab58165b9b8bbd6cb620c4cc9ba2ffc2bd0f31d61ed16dc"
ACCOUNTING_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_ACCOUNTING.json"
PRODUCER_PATH = ROOT / "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
R5_HARNESS_PATH = ROOT / "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r5.py"
R5_BLOCKER_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_R5_BLOCKER.json"
R5_REPORT_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_R5_BLOCKER_REPORT.md"
BLOCKER_CODE = "D2_V2_ACCOUNTING_REMEDIATION_R1_COMPLETION_EVIDENCE_REJECTED"
ROOT_CAUSE = "R5_REQUIRED_POST_ORACLE_GATES_NOT_COMPLETED_AND_SNAPSHOT_INCOMPLETE"
NONCANONICAL_FIELD = "d1_metric_reads"
CANONICAL_FIELD = "d1_metric_artifact_reads"


class AccountingRemediationError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise AccountingRemediationError(code)


def stable_hash(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return sha256(raw).hexdigest()


def validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if document.get("artifact_hash") != expected or stable_hash(payload) != expected:
        fail("D2_V2_ACCOUNTING_REMEDIATION_AUTHORITY_HASH_REJECTED")


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("D2_V2_ACCOUNTING_REMEDIATION_DUPLICATE_JSON_KEY_REJECTED")
        result[key] = value
    return result


def load_public_once(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=strict_object)
    except AccountingRemediationError:
        raise
    except BaseException:
        fail("D2_V2_ACCOUNTING_REMEDIATION_PUBLIC_METADATA_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_ACCOUNTING_REMEDIATION_PUBLIC_METADATA_REJECTED")
    return value


CORE_EXPECTED: dict[str, Any] = {
    "scientific_v2_execution_attempts": 1,
    "scientific_v2_execution_retries": 0,
    "d0_prediction_parses": 1,
    "d1_prediction_parses": 1,
    "source_map_reads": 1,
    "native_horizon_map_reads": 1,
    "alarming_d1_records_used": 788,
    "evidence_tokens_constructed": 788,
    "fusion_computations": 54000,
    "private_fusion_evidence_freezes": 1,
    "combined_prediction_v2_freezes": 1,
    "label_hash_reads": 1,
    "label_scientific_parses": 1,
    "label_before_combined_prediction_v2_access": False,
    "attack_event_derivations": 1,
    "v2_alarm_episode_derivations": 1,
    "d0_reference_episode_derivations": 1,
    "v2_rule_recovery_episode_derivations": 1,
    "primary_metric_computations": 2,
    "incremental_metric_computations": 4,
    "d0_executions": 0,
    "d1_executions": 0,
    "d2_v1_executions": 0,
    "d1_metric_artifact_reads": 0,
    "d2_v1_prediction_reads": 0,
    "d2_v1_metric_reads": 0,
    "d0_model_accesses": 0,
    "d0_score_accesses": 0,
    "d1_rule_reevaluations": 0,
    "test1_feature_accesses": 0,
    "test2_accesses": 0,
    "outer_executions": 0,
    "result_driven_changes": False,
    "private_paths_exposed": 0,
    "private_source_sets_exposed": 0,
    "private_label_values_exposed": 0,
}

ENVELOPE_TYPES: dict[str, type] = {
    "artifact_hash": str,
    "artifact_type": str,
    "schema_version": str,
    "created_at_utc": str,
    "task_id": str,
    "execution_run_hash": str,
    "push_attempted": bool,
    "remote_egress_status": str,
}

R5_EXPECTED_TO_CANONICAL: dict[str, str] = {
    "scientific_v2_execution_attempts": "scientific_v2_execution_attempts",
    "scientific_v2_execution_retries": "scientific_v2_execution_retries",
    "d0_prediction_parses": "d0_prediction_parses",
    "d1_prediction_parses": "d1_prediction_parses",
    "source_map_reads": "source_map_reads",
    "native_horizon_map_reads": "native_horizon_map_reads",
    "alarming_d1_records_used": "alarming_d1_records_used",
    "evidence_tokens_constructed": "evidence_tokens_constructed",
    "fusion_computations": "fusion_computations",
    "private_fusion_evidence_freezes": "private_fusion_evidence_freezes",
    "combined_prediction_v2_freezes": "combined_prediction_v2_freezes",
    "label_scientific_parses": "label_scientific_parses",
    "primary_metric_computations": "primary_metric_computations",
    "incremental_metric_computations": "incremental_metric_computations",
    "d0_executions": "d0_executions",
    "d1_executions": "d1_executions",
    "d2_v1_executions": "d2_v1_executions",
    "d0_score_accesses": "d0_score_accesses",
    "d1_rule_reevaluations": "d1_rule_reevaluations",
    "d1_metric_reads": "d1_metric_artifact_reads",
    "d2_v1_metric_reads": "d2_v1_metric_reads",
    "test1_feature_accesses": "test1_feature_accesses",
    "test2_accesses": "test2_accesses",
    "outer_executions": "outer_executions",
    "result_driven_changes": "result_driven_changes",
}

REQUIRED_R5_SNAPSHOT_FIELDS = frozenset({
    "d2_v2_design_hash_match", "d0_prediction_hash_match", "d1_prediction_hash_match",
    "source_map_hash_match", "native_horizon_map_hash_match", "native_horizon_relation_count",
    "native_horizon_missing_count", "native_horizon_ambiguous_count", "zero_horizon_token_count",
    "split_end_clipped_token_count", "native_horizon_corroboration_point_count",
    "rule_recovery_native_horizon_count", "d0_only_count",
    "d0_and_rule_corroboration_native_horizon_count", "none_count",
    "combined_prediction_v2_record_count", "combined_prediction_v2_unique_rows",
    "attack_event_count", "v2_alarm_episode_count", "d0_alarm_episode_count",
    "v2_rule_recovery_episode_count", "v2_detected_attack_event_count",
    "v2_attack_event_recall", "v2_normal_false_alarm_episode_count", "normal_exposure_seconds",
    "v2_normal_far", "d0_attack_event_recall", "d0_normal_far", "d0_missed_attack_event_count",
    "d0_missed_events_recovered", "d0_missed_recovery_rate", "incremental_attack_event_recall",
    "normal_v2_rule_recovery_false_alarm_episode_count", "added_normal_rule_recovery_far",
    "incremental_normal_false_alarm_episode_count", "incremental_normal_far",
    "duplicate_json_key_count", "self_hash_field_collision_count", "referenced_hash_collision_count",
    "leakage_audit_completed", "report_schema_validation_completed",
})


@dataclass(frozen=True)
class AccountingSchemaAudit:
    total_fields: int
    exact_name_matches: int
    schema_proven_name_corrections: int
    unresolved_field_mismatches: int


def producer_schema_keys(source: str) -> frozenset[str]:
    start = source.find("    accounting_core = {")
    end = source.find("    accounting_identity =", start)
    if start < 0 or end < 0:
        fail("D2_V2_ACCOUNTING_REMEDIATION_PRODUCER_SCHEMA_REJECTED")
    block = source[start:end]
    keys = frozenset(part.split('"', 2)[1] for part in block.splitlines() if '"' in part)
    if keys != frozenset(CORE_EXPECTED):
        fail("D2_V2_ACCOUNTING_REMEDIATION_PRODUCER_SCHEMA_REJECTED")
    if NONCANONICAL_FIELD in keys or CANONICAL_FIELD not in keys:
        fail("D2_V2_ACCOUNTING_REMEDIATION_CANONICAL_FIELD_REJECTED")
    return keys


def validate_accounting(
    document: Mapping[str, Any], producer_source: str, expected_hash: str = ACCOUNTING_HASH,
) -> AccountingSchemaAudit:
    validate_self_hash(document, expected_hash)
    producer_schema_keys(producer_source)
    expected_fields = frozenset(CORE_EXPECTED) | frozenset(ENVELOPE_TYPES)
    if frozenset(document) != expected_fields:
        fail("D2_V2_ACCOUNTING_REMEDIATION_ACCOUNTING_SCHEMA_REJECTED")
    for key, expected in CORE_EXPECTED.items():
        if type(document[key]) is not type(expected) or document[key] != expected:
            fail("D2_V2_ACCOUNTING_REMEDIATION_ACCOUNTING_VALUE_REJECTED")
    for key, expected_type in ENVELOPE_TYPES.items():
        if type(document[key]) is not expected_type:
            fail("D2_V2_ACCOUNTING_REMEDIATION_ACCOUNTING_TYPE_REJECTED")
    if document["artifact_type"] != "D2V2ExecutionAccountingV1" or document["schema_version"] != "1.0.0":
        fail("D2_V2_ACCOUNTING_REMEDIATION_ACCOUNTING_IDENTITY_REJECTED")
    if document["push_attempted"] or document["remote_egress_status"] != "LOCAL_ONLY_NOT_PUSHED":
        fail("D2_V2_ACCOUNTING_REMEDIATION_EGRESS_REJECTED")
    if len(set(R5_EXPECTED_TO_CANONICAL.values())) != len(R5_EXPECTED_TO_CANONICAL):
        fail("D2_V2_ACCOUNTING_REMEDIATION_DUPLICATE_SEMANTIC_MAPPING_REJECTED")
    if set(R5_EXPECTED_TO_CANONICAL.values()) - set(document):
        fail("D2_V2_ACCOUNTING_REMEDIATION_UNKNOWN_FIELD_REJECTED")
    corrections = sum(key != value for key, value in R5_EXPECTED_TO_CANONICAL.items())
    return AccountingSchemaAudit(len(document), len(document) - corrections, corrections, 0)


def validate_r5_blocker(document: Mapping[str, Any]) -> tuple[str, ...]:
    validate_self_hash(document, R5_BLOCKER_HASH)
    required = {
        "status": "blocked_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_harness_remediation_r5",
        "blocker_code": "D2_V2_R5_EXECUTION_ACCOUNTING_REJECTED",
        "metric_oracle_completed": True,
        "fusion_evidence_v2_hash_match": True,
        "combined_prediction_v2_hash_match": True,
        "metric_evidence_v2_hash_match": True,
        "prediction_before_label_pass": True,
        "prediction_divergences": 0,
        "d0_preservation_violations": 0,
        "trigger_class_violations": 0,
        "post_result_freeze_mutations": 0,
    }
    if any(document.get(key) != value for key, value in required.items()):
        fail("D2_V2_ACCOUNTING_REMEDIATION_R5_BLOCKER_REJECTED")
    return tuple(sorted(REQUIRED_R5_SNAPSHOT_FIELDS - set(document)))


def validate_r5_report(raw: bytes) -> None:
    marker = b"<!-- BEGIN D2 V2 RESULT INTEGRITY R5 BLOCKER PROVENANCE V1 -->"
    if raw.count(marker) != 1:
        fail("D2_V2_ACCOUNTING_REMEDIATION_R5_REPORT_REJECTED")
    prefix = raw[:raw.index(marker)]
    if not prefix.endswith(b"\n") or sha256(prefix[:-1]).hexdigest() != R5_REPORT_HASH:
        fail("D2_V2_ACCOUNTING_REMEDIATION_R5_REPORT_REJECTED")


def r5_control_flow(source: str) -> dict[str, Any]:
    start = source.find("def run_audit()")
    end = source.find("\ndef main()", start)
    if start < 0 or end < 0:
        fail("D2_V2_ACCOUNTING_REMEDIATION_R5_CONTROL_FLOW_REJECTED")
    body = source[start:end]
    names = (
        "metric_evidence", "public_metrics", "accounting", "parse_closure",
        "leakage", "adversarial", "report_schema",
    )
    probes = (
        "if metric_document != expected_metric", "validate_public_metrics(",
        "validate_result_accounting(", "guard.require_exact()", "leakage = leakage_audit(",
        "attacks, accepted = adversarial()", "reports, markdown = build_reports(",
    )
    positions = {name: body.find(probe) for name, probe in zip(names, probes)}
    if any(value < 0 for value in positions.values()):
        fail("D2_V2_ACCOUNTING_REMEDIATION_R5_CONTROL_FLOW_REJECTED")
    actual = tuple(sorted(positions, key=positions.get))
    expected = ("metric_evidence", "public_metrics", "parse_closure", "leakage", "adversarial", "report_schema", "accounting")
    return {
        "actual_order": actual,
        "required_order": expected,
        "accounting_before_parse_closure": positions["accounting"] < positions["parse_closure"],
        "accounting_before_leakage": positions["accounting"] < positions["leakage"],
        "accounting_before_adversarial": positions["accounting"] < positions["adversarial"],
        "accounting_before_report_schema": positions["accounting"] < positions["report_schema"],
        "completion_order_pass": actual == expected,
    }


def _synthetic_producer_source() -> str:
    lines = ["def producer():", "    accounting_core = {"]
    lines.extend(f'        "{key}": 0,' for key in CORE_EXPECTED)
    lines.extend(["    }", "    accounting_identity = None"])
    return "\n".join(lines)


def _synthetic_accounting() -> dict[str, Any]:
    document: dict[str, Any] = {
        "artifact_type": "D2V2ExecutionAccountingV1", "schema_version": "1.0.0",
        "created_at_utc": "2026-01-01T00:00:00Z", "task_id": "synthetic",
        "execution_run_hash": "a" * 64, **CORE_EXPECTED, "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    }
    document["artifact_hash"] = stable_hash(document)
    return document


def adversarial_contract() -> tuple[int, int]:
    baseline = _synthetic_accounting()
    mutations: list[tuple[dict[str, Any], str | None]] = []
    for key, value in (
        ("d1_metric_reads", 0), ("d1_metric_read", 0), (CANONICAL_FIELD, 1),
        (CANONICAL_FIELD, False), ("scientific_v2_execution_attempts", 2),
        ("scientific_v2_execution_retries", 1), ("d0_executions", 1),
        ("d1_executions", 1), ("d2_v1_executions", 1), ("d0_score_accesses", 1),
        ("d1_rule_reevaluations", 1), ("test1_feature_accesses", 1),
        ("test2_accesses", 1), ("outer_executions", 1),
        ("result_driven_changes", True), ("push_attempted", True),
        ("remote_egress_status", "PUSHED"), ("artifact_type", "forged"),
        ("schema_version", "2.0.0"),
    ):
        candidate = dict(baseline); candidate[key] = value
        candidate["artifact_hash"] = stable_hash({k: v for k, v in candidate.items() if k != "artifact_hash"})
        mutations.append((candidate, None))
    missing = dict(baseline); missing.pop(CANONICAL_FIELD)
    missing["artifact_hash"] = stable_hash({k: v for k, v in missing.items() if k != "artifact_hash"})
    mutations.append((missing, None))
    stale = dict(baseline); stale["task_id"] = "substituted"
    mutations.append((stale, str(baseline["artifact_hash"])))
    accepted = 0
    for candidate, forced_hash in mutations:
        expected = forced_hash or str(candidate["artifact_hash"])
        try:
            validate_accounting(candidate, _synthetic_producer_source(), expected)
        except AccountingRemediationError:
            continue
        accepted += 1
    return len(mutations), accepted


def git(*args: str) -> str:
    process = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if process.returncode:
        fail("D2_V2_ACCOUNTING_REMEDIATION_GIT_REJECTED")
    return process.stdout.strip()


def real_remediation() -> dict[str, Any]:
    if git("rev-parse", "--abbrev-ref", "HEAD") != BRANCH or git("status", "--porcelain"):
        fail("D2_V2_ACCOUNTING_REMEDIATION_WORKTREE_REJECTED")
    blocker = load_public_once(R5_BLOCKER_PATH)
    missing_snapshot_fields = validate_r5_blocker(blocker)
    validate_r5_report(R5_REPORT_PATH.read_bytes())
    producer_source = PRODUCER_PATH.read_text(encoding="utf-8")
    accounting = load_public_once(ACCOUNTING_PATH)
    schema = validate_accounting(accounting, producer_source)
    control = r5_control_flow(R5_HARNESS_PATH.read_text(encoding="utf-8"))
    attacks, accepted = adversarial_contract()
    if accepted:
        fail("D2_V2_ACCOUNTING_REMEDIATION_ACCEPTED_INVALID")
    eligible = not missing_snapshot_fields and control["completion_order_pass"]
    return {
        "status": "BLOCKED" if not eligible else "PASS",
        "blocker_code": BLOCKER_CODE if not eligible else "NONE",
        "root_cause": ROOT_CAUSE if not eligible else "NONE",
        "accounting_hash_match": True,
        "accounting_schema_match": True,
        "canonical_d1_metric_field": CANONICAL_FIELD,
        "canonical_d1_metric_field_value": accounting[CANONICAL_FIELD],
        "r5_noncanonical_field": NONCANONICAL_FIELD,
        "field_semantic_equivalence_pass": True,
        "full_accounting_field_count_audited": schema.total_fields,
        "exact_name_matches": schema.exact_name_matches,
        "schema_proven_name_corrections": schema.schema_proven_name_corrections,
        "unresolved_accounting_mismatches": schema.unresolved_field_mismatches,
        "all_execution_accounting_semantics_pass": True,
        "missing_required_snapshot_field_count": len(missing_snapshot_fields),
        "missing_required_snapshot_fields": missing_snapshot_fields,
        "r5_control_flow": control,
        "completion_eligible": eligible,
        "independent_attacks": attacks,
        "accepted_invalid": accepted,
        "scientific_artifacts_reopened": False,
        "accounting_public_metadata_parses": 1,
        "label_parses": 0,
        "test1_feature_accesses": 0,
        "test2_accesses": 0,
        "outer_executions": 0,
        "authoritative_scientific_executions": 0,
        "result_driven_changes": False,
        "private_path_exposures": 0,
    }


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_ACCOUNTING_REMEDIATION_ARGUMENTS_REJECTED")
        return 2
    try:
        result = real_remediation()
    except AccountingRemediationError as error:
        print(error.code)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False))
    if not result["completion_eligible"]:
        print(BLOCKER_CODE)
        return 1
    print("D2_V2_RESULT_INTEGRITY_AUDITED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
