"""AST-only public accounting remediation after the completed R5 oracle.

The real entry point never opens a prediction, source map, horizon map,
CombinedPredictionV2, private evidence, label, test1 feature, or test2 file.
It validates public producer/accounting/blocker authorities and fails closed
when the committed R5 blocker evidence cannot support the full completion
snapshot.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-EXECUTION-ACCOUNTING-SCHEMA-PARSER-REMEDIATION-R2"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-r5-execution-accounting-schema-parser-remediation-r2"
BASE = "c3329d92d4c296162e0f6af5aa2f31e1cc2706ea"
RESULT_FREEZE_COMMIT = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
ACCOUNTING_HASH = "7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca"
R5_BLOCKER_HASH = "0ab5479d8e2f6367e214ddeceded63826d2d89d377f2aac00d2d909d5ab322e0"
R5_REPORT_HASH = "730d23ea6d29c679cab58165b9b8bbd6cb620c4cc9ba2ffc2bd0f31d61ed16dc"
R1_BLOCKER_HASH = "3c5b2da933ac4e00df4602aaf89c749d6e0aea856bf844f9f769cfb907c358f2"
R1_REPORT_HASH = "b23666900a5a09d0425913df84ed82c5703b5ffd554d464447d8c632d37e85f6"
CUSTODY_COMPATIBILITY_HASH = "f7ca9d29c7e8d65359781534790c008bec436dc35e521f7de3342b7215e28cd8"
ROOT_CAUSE = "LINE_BASED_SCHEMA_KEY_EXTRACTOR_CAPTURED_ONLY_FIRST_QUOTED_KEY_PER_PHYSICAL_LINE"
RECOVERY_METHOD = "PYTHON_AST_STRUCTURAL_EXTRACTION"
BLOCKER_CODE = "D2_V2_ACCOUNTING_SCHEMA_R2_R5_SNAPSHOT_EVIDENCE_INCOMPLETE"

ACCOUNTING_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_ACCOUNTING.json"
PRODUCER_PATH = ROOT / "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
R5_BLOCKER_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_R5_BLOCKER.json"
R5_REPORT_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_R5_BLOCKER_REPORT.md"
R1_BLOCKER_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_ACCOUNTING_REMEDIATION_R1_BLOCKER.json"
R1_REPORT_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_ACCOUNTING_REMEDIATION_R1_BLOCKER_REPORT.md"
CUSTODY_RECEIPT_PATH = ROOT / "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_REPORT_SCHEMA_R1_COMPATIBILITY_RECEIPT.json"


class AccountingSchemaR2Error(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise AccountingSchemaR2Error(code)


def stable_hash(value: Mapping[str, Any]) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("D2_V2_ACCOUNTING_SCHEMA_R2_DUPLICATE_JSON_KEY_REJECTED")
        result[key] = value
    return result


def strict_json_bytes(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw, object_pairs_hook=strict_object)
    except AccountingSchemaR2Error:
        raise
    except BaseException:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PUBLIC_JSON_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PUBLIC_JSON_REJECTED")
    return value


def validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if document.get("artifact_hash") != expected or stable_hash(payload) != expected:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_AUTHORITY_HASH_REJECTED")


def _string_key(node: ast.AST | None) -> str:
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return node.value
    fail("D2_V2_ACCOUNTING_SCHEMA_R2_DYNAMIC_KEY_REJECTED")


def fields_from_dict_node(node: ast.AST) -> tuple[str, ...]:
    if not isinstance(node, ast.Dict):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_TARGET_NOT_DICT")
    fields = tuple(_string_key(key) for key in node.keys)
    if len(fields) != len(set(fields)):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_DUPLICATE_PRODUCER_FIELD_REJECTED")
    return fields


def _assignment_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    targets: Sequence[ast.expr]
    if isinstance(node, ast.Assign):
        targets = node.targets
    else:
        targets = (node.target,)
    names = [target.id for target in targets if isinstance(target, ast.Name)]
    return names[0] if len(names) == 1 else None


def recover_dict_assignment_fields(
    source: str, *, function_name: str, assignment_name: str
) -> tuple[str, ...]:
    """Recover one exact dictionary assignment from one exact function."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_SOURCE_REJECTED")
    functions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
    ]
    if len(functions) != 1:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_NODE_AMBIGUOUS")
    candidates: list[ast.AST] = []
    for node in ast.walk(functions[0]):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and _assignment_name(node) == assignment_name:
            candidates.append(node.value)
    if len(candidates) != 1:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_NODE_AMBIGUOUS")
    return fields_from_dict_node(candidates[0])


def recover_class_fields(source: str, *, class_name: str) -> tuple[str, ...]:
    """Recover dataclass, regular class, or TypedDict declared fields."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_SOURCE_REJECTED")
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
    if len(classes) != 1:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_NODE_AMBIGUOUS")
    names: list[str] = []
    for node in classes[0].body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
    if not names or len(names) != len(set(names)):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_SCHEMA_REJECTED")
    return tuple(names)


def recover_constructor_keyword_fields(
    source: str, *, function_name: str, constructor_name: str
) -> tuple[str, ...]:
    """Recover keyword fields of one known constructor call structurally."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_SOURCE_REJECTED")
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function_name]
    if len(functions) != 1:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_NODE_AMBIGUOUS")
    calls: list[ast.Call] = []
    for node in ast.walk(functions[0]):
        if not isinstance(node, ast.Call):
            continue
        called = node.func.id if isinstance(node.func, ast.Name) else None
        if called == constructor_name:
            calls.append(node)
    if len(calls) != 1 or any(keyword.arg is None for keyword in calls[0].keywords):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_NODE_AMBIGUOUS")
    fields = tuple(str(keyword.arg) for keyword in calls[0].keywords)
    if len(fields) != len(set(fields)):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_DUPLICATE_PRODUCER_FIELD_REJECTED")
    return fields


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

SEMANTIC_MAPPING: dict[str, str] = {
    "SCIENTIFIC_V2_EXECUTION_ATTEMPT_COUNT": "scientific_v2_execution_attempts",
    "SCIENTIFIC_V2_EXECUTION_RETRY_COUNT": "scientific_v2_execution_retries",
    "D0_PREDICTION_PARSE_COUNT": "d0_prediction_parses",
    "D1_PREDICTION_PARSE_COUNT": "d1_prediction_parses",
    "SOURCE_MAP_READ_COUNT": "source_map_reads",
    "NATIVE_HORIZON_MAP_READ_COUNT": "native_horizon_map_reads",
    "ALARMING_D1_RECORD_COUNT": "alarming_d1_records_used",
    "EVIDENCE_TOKEN_COUNT": "evidence_tokens_constructed",
    "FUSION_COMPUTATION_COUNT": "fusion_computations",
    "PRIVATE_FUSION_EVIDENCE_FREEZE_COUNT": "private_fusion_evidence_freezes",
    "COMBINED_PREDICTION_FREEZE_COUNT": "combined_prediction_v2_freezes",
    "LABEL_SCIENTIFIC_PARSE_COUNT": "label_scientific_parses",
    "PRIMARY_METRIC_COMPUTATION_COUNT": "primary_metric_computations",
    "INCREMENTAL_METRIC_COMPUTATION_COUNT": "incremental_metric_computations",
    "D0_EXECUTION_COUNT": "d0_executions",
    "D1_EXECUTION_COUNT": "d1_executions",
    "D2_V1_EXECUTION_COUNT": "d2_v1_executions",
    "D1_METRIC_ARTIFACT_READ_COUNT": "d1_metric_artifact_reads",
    "D2_V1_METRIC_ARTIFACT_OR_RESULT_READ_COUNT": "d2_v1_metric_reads",
    "D0_SCORE_ACCESS_COUNT": "d0_score_accesses",
    "D1_RULE_REEVALUATION_COUNT": "d1_rule_reevaluations",
    "TEST1_FEATURE_ACCESS_COUNT": "test1_feature_accesses",
    "TEST2_ACCESS_COUNT": "test2_accesses",
    "OUTER_EXECUTION_COUNT": "outer_executions",
    "RESULT_DRIVEN_CHANGE_FLAG": "result_driven_changes",
    "PRIVATE_PATH_EXPOSURE_COUNT": "private_paths_exposed",
    "PRIVATE_SOURCE_SET_EXPOSURE_COUNT": "private_source_sets_exposed",
    "PRIVATE_LABEL_VALUE_EXPOSURE_COUNT": "private_label_values_exposed",
}

R5_NONCANONICAL_EXPECTATION = "d1_metric_reads"
CANONICAL_D1_METRIC_FIELD = "d1_metric_artifact_reads"


@dataclass(frozen=True)
class FieldInventoryEntry:
    field_name: str
    field_role: str
    producer_origin: str
    expected_type: str
    actual_type: str
    semantic_concept: str | None
    r5_required: bool
    exact_name_match: bool
    schema_proven_mapping_required: bool


@dataclass(frozen=True)
class AccountingAuditResult:
    producer_fields: tuple[str, ...]
    artifact_fields: tuple[str, ...]
    inventory: tuple[FieldInventoryEntry, ...]
    full_semantic_concepts_required: int
    exact_name_matches: int
    schema_proven_name_corrections: int
    canonical_fields_missing: int
    ambiguous_semantic_mappings: int
    wrong_type_count: int
    wrong_value_count: int
    unresolved_field_mismatches: int


def build_inventory_and_audit(
    document: Mapping[str, Any], producer_fields: Sequence[str]
) -> AccountingAuditResult:
    producer_set = frozenset(producer_fields)
    expected_producer = frozenset(CORE_EXPECTED)
    artifact_set = frozenset(document)
    expected_artifact = expected_producer | frozenset(ENVELOPE_TYPES)
    if producer_set != expected_producer:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_PRODUCER_SCHEMA_REJECTED")
    if artifact_set != expected_artifact:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_ARTIFACT_SCHEMA_REJECTED")
    if R5_NONCANONICAL_EXPECTATION in producer_set or CANONICAL_D1_METRIC_FIELD not in producer_set:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_D1_FIELD_REJECTED")
    if len(SEMANTIC_MAPPING) != len(set(SEMANTIC_MAPPING.values())):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_AMBIGUOUS_SEMANTIC_MAPPING")

    inverse = {field: concept for concept, field in SEMANTIC_MAPPING.items()}
    missing = sum(field not in artifact_set or field not in producer_set for field in SEMANTIC_MAPPING.values())
    wrong_types = 0
    wrong_values = 0
    inventory: list[FieldInventoryEntry] = []
    for field in sorted(artifact_set):
        if field in CORE_EXPECTED:
            expected = CORE_EXPECTED[field]
            expected_type = type(expected)
            role = "SCIENTIFIC_EXECUTION_ACCOUNTING_FIELD"
            origin = "accounting_core"
            if type(document[field]) is not expected_type:
                wrong_types += 1
            elif document[field] != expected:
                wrong_values += 1
        else:
            expected_type = ENVELOPE_TYPES[field]
            role = "SELF_HASH_METADATA_FIELD" if field == "artifact_hash" else "SERIALIZER_PROVENANCE_FIELD"
            origin = "generic_self_hashed_serializer" if field == "artifact_hash" else "public_accounting_envelope"
            if type(document[field]) is not expected_type:
                wrong_types += 1
        concept = inverse.get(field)
        inventory.append(FieldInventoryEntry(
            field_name=field,
            field_role=role,
            producer_origin=origin,
            expected_type=expected_type.__name__,
            actual_type=type(document[field]).__name__,
            semantic_concept=concept,
            r5_required=concept is not None,
            exact_name_match=concept is not None and field != CANONICAL_D1_METRIC_FIELD,
            schema_proven_mapping_required=field == CANONICAL_D1_METRIC_FIELD,
        ))
    corrections = 1
    exact = len(SEMANTIC_MAPPING) - corrections
    unresolved = missing + wrong_types + wrong_values
    return AccountingAuditResult(
        producer_fields=tuple(sorted(producer_set)),
        artifact_fields=tuple(sorted(artifact_set)),
        inventory=tuple(inventory),
        full_semantic_concepts_required=len(SEMANTIC_MAPPING),
        exact_name_matches=exact,
        schema_proven_name_corrections=corrections,
        canonical_fields_missing=missing,
        ambiguous_semantic_mappings=0,
        wrong_type_count=wrong_types,
        wrong_value_count=wrong_values,
        unresolved_field_mismatches=unresolved,
    )


R5_DIRECT_EXPECTED: dict[str, Any] = {
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
    "fusion_oracle_computations": 54000,
    "token_oracle_count": 788,
    "scientific_v2_execution_attempts": 1,
    "scientific_v2_execution_retries": 0,
    "test1_feature_accesses": 0,
    "test2_accesses": 0,
    "outer_executions": 0,
    "result_driven_changes": False,
}

R5_PARSE_EXPECTED: dict[str, int] = {
    "D0_PREDICTION": 1,
    "D1_PREDICTION": 1,
    "SOURCE_MAP": 1,
    "NATIVE_HORIZON_MAP": 1,
    "COMBINED_PREDICTION_V2": 1,
    "FUSION_EVIDENCE_V2": 1,
    "LABEL_TEST1": 1,
    "METRIC_EVIDENCE_V2": 1,
}

R5_REQUIRED_SNAPSHOT_FIELDS = frozenset({
    "native_horizon_relation_count",
    "native_horizon_missing_count",
    "native_horizon_ambiguous_count",
    "native_horizon_corroboration_point_count",
    "rule_recovery_native_horizon_count",
    "d0_only_count",
    "d0_and_rule_corroboration_native_horizon_count",
    "none_count",
    "attack_event_count",
    "v2_alarm_episode_count",
    "d0_alarm_episode_count",
    "v2_rule_recovery_episode_count",
    "v2_attack_event_recall",
    "v2_normal_far",
    "d0_attack_event_recall",
    "d0_normal_far",
    "d0_missed_attack_event_count",
    "d0_missed_events_recovered",
    "d0_missed_recovery_rate",
    "incremental_attack_event_recall",
    "normal_v2_rule_recovery_false_alarm_episode_count",
    "added_normal_rule_recovery_far",
    "incremental_normal_false_alarm_episode_count",
    "incremental_normal_far",
    "duplicate_json_key_count",
    "self_hash_field_collision_count",
    "referenced_hash_collision_count",
})


@dataclass(frozen=True)
class R5SnapshotAudit:
    direct_values_pass: bool
    parse_counts_pass: bool
    missing_required_fields: tuple[str, ...]
    complete: bool


def audit_r5_snapshot(document: Mapping[str, Any]) -> R5SnapshotAudit:
    direct = all(document.get(key) == value for key, value in R5_DIRECT_EXPECTED.items())
    parses = document.get("r5_semantic_parse_counts") == R5_PARSE_EXPECTED
    missing = tuple(sorted(R5_REQUIRED_SNAPSHOT_FIELDS - set(document)))
    return R5SnapshotAudit(direct, parses, missing, direct and parses and not missing)


def validate_r1_blocker(document: Mapping[str, Any]) -> None:
    validate_self_hash(document, R1_BLOCKER_HASH)
    required = {
        "status": "blocked_task039e3_r2r_utility_inner_d2_v2_r5_execution_accounting_field_remediation_r1",
        "blocker_code": "D2_V2_ACCOUNTING_REMEDIATION_PRODUCER_SCHEMA_REJECTED",
        "root_cause": ROOT_CAUSE,
        "scientific_artifacts_reopened": False,
        "label_parses": 0,
        "test1_feature_accesses": 0,
        "test2_accesses": 0,
        "result_driven_changes": False,
    }
    if any(document.get(key) != value for key, value in required.items()):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_R1_BLOCKER_REJECTED")


def validate_markdown_body(raw: bytes, marker: bytes, expected: str) -> None:
    if raw.count(marker) != 1:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_REPORT_REJECTED")
    prefix = raw[:raw.index(marker)]
    if not prefix.endswith(b"\n") or sha256(prefix[:-1]).hexdigest() != expected:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_REPORT_REJECTED")


def validate_custody_receipt(document: Mapping[str, Any]) -> None:
    validate_self_hash(document, CUSTODY_COMPATIBILITY_HASH)
    if (
        document.get("compatibility_result") != "PRIVATE_CUSTODY_BINDING_COMPATIBILITY_VERIFIED"
        or document.get("audit_only") is not True
        or document.get("scientific_execution_authorized") is not False
    ):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_CUSTODY_REJECTED")


def validate_accounting_envelope(document: Mapping[str, Any]) -> None:
    if document.get("artifact_type") != "D2V2ExecutionAccountingV1":
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_ACCOUNTING_IDENTITY_REJECTED")
    if document.get("schema_version") != "1.0.0":
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_ACCOUNTING_IDENTITY_REJECTED")
    if document.get("push_attempted") is not False:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_EGRESS_REJECTED")
    if document.get("remote_egress_status") != "LOCAL_ONLY_NOT_PUSHED":
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_EGRESS_REJECTED")


def git(*args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    if process.returncode:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_GIT_REJECTED")
    return process.stdout.strip()


def _synthetic_producer_source() -> str:
    items = ", ".join(f"{key!r}: 0" for key in CORE_EXPECTED)
    return f"def _write_result_reports_v1():\n    accounting_core = {{{items}}}\n"


def _synthetic_accounting() -> dict[str, Any]:
    document: dict[str, Any] = {
        "artifact_type": "D2V2ExecutionAccountingV1",
        "schema_version": "1.0.0",
        "created_at_utc": "2026-01-01T00:00:00Z",
        "task_id": "synthetic",
        "execution_run_hash": "a" * 64,
        **CORE_EXPECTED,
        "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    }
    document["artifact_hash"] = stable_hash(document)
    return document


def adversarial_contract() -> tuple[int, int]:
    attacks = 0
    accepted = 0

    def reject(action: Any) -> None:
        nonlocal attacks, accepted
        attacks += 1
        try:
            action()
        except AccountingSchemaR2Error:
            return
        accepted += 1

    baseline = _synthetic_accounting()
    source = _synthetic_producer_source()
    mutations: list[tuple[str, Any]] = [
        ("d1_metric_reads", 0),
        (CANONICAL_D1_METRIC_FIELD, 1),
        (CANONICAL_D1_METRIC_FIELD, False),
        ("scientific_v2_execution_attempts", 2),
        ("scientific_v2_execution_retries", 1),
        ("d0_executions", 1),
        ("d1_executions", 1),
        ("d2_v1_executions", 1),
        ("d0_score_accesses", 1),
        ("d1_rule_reevaluations", 1),
        ("test1_feature_accesses", 1),
        ("test2_accesses", 1),
        ("outer_executions", 1),
        ("result_driven_changes", True),
    ]
    for field, value in mutations:
        candidate = dict(baseline)
        candidate[field] = value
        if field != "d1_metric_reads":
            candidate["artifact_hash"] = stable_hash({k: v for k, v in candidate.items() if k != "artifact_hash"})
        reject(lambda candidate=candidate: _validate_synthetic(candidate, source))

    missing = dict(baseline)
    missing.pop(CANONICAL_D1_METRIC_FIELD)
    missing["artifact_hash"] = stable_hash({k: v for k, v in missing.items() if k != "artifact_hash"})
    reject(lambda: _validate_synthetic(missing, source))
    reject(lambda: recover_dict_assignment_fields(
        "def _write_result_reports_v1():\n accounting_core={}\n accounting_core={}\n",
        function_name="_write_result_reports_v1", assignment_name="accounting_core",
    ))
    reject(lambda: strict_json_bytes(b'{"x":1,"x":2}'))
    incomplete = {**R5_DIRECT_EXPECTED, "r5_semantic_parse_counts": R5_PARSE_EXPECTED}
    reject(lambda: _require_complete_snapshot(incomplete))
    return attacks, accepted


def _validate_synthetic(document: Mapping[str, Any], source: str) -> None:
    validate_self_hash(document, str(document.get("artifact_hash")))
    validate_accounting_envelope(document)
    fields = recover_dict_assignment_fields(
        source, function_name="_write_result_reports_v1", assignment_name="accounting_core"
    )
    audit = build_inventory_and_audit(document, fields)
    if audit.unresolved_field_mismatches:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_ACCOUNTING_REJECTED")


def _require_complete_snapshot(document: Mapping[str, Any]) -> None:
    if not audit_r5_snapshot(document).complete:
        fail(BLOCKER_CODE)


def real_remediation() -> dict[str, Any]:
    if git("rev-parse", "--abbrev-ref", "HEAD") != BRANCH or git("status", "--porcelain"):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_WORKTREE_REJECTED")
    if git("merge-base", "--is-ancestor", BASE, "HEAD"):
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_BASE_REJECTED")

    r5_blocker = strict_json_bytes(R5_BLOCKER_PATH.read_bytes())
    validate_self_hash(r5_blocker, R5_BLOCKER_HASH)
    validate_markdown_body(
        R5_REPORT_PATH.read_bytes(),
        b"<!-- BEGIN D2 V2 RESULT INTEGRITY R5 BLOCKER PROVENANCE V1 -->",
        R5_REPORT_HASH,
    )
    r1_blocker = strict_json_bytes(R1_BLOCKER_PATH.read_bytes())
    validate_r1_blocker(r1_blocker)
    validate_markdown_body(
        R1_REPORT_PATH.read_bytes(),
        b"<!-- BEGIN D2 V2 R5 ACCOUNTING REMEDIATION R1 BLOCKER PROVENANCE V1 -->",
        R1_REPORT_HASH,
    )

    producer_source = PRODUCER_PATH.read_bytes().decode("utf-8")
    producer_fields = recover_dict_assignment_fields(
        producer_source,
        function_name="_write_result_reports_v1",
        assignment_name="accounting_core",
    )
    accounting = strict_json_bytes(ACCOUNTING_PATH.read_bytes())
    validate_self_hash(accounting, ACCOUNTING_HASH)
    validate_accounting_envelope(accounting)
    audit = build_inventory_and_audit(accounting, producer_fields)
    if audit.unresolved_field_mismatches:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_ACCOUNTING_REJECTED")

    custody = strict_json_bytes(CUSTODY_RECEIPT_PATH.read_bytes())
    validate_custody_receipt(custody)
    snapshot = audit_r5_snapshot(r5_blocker)
    attacks, accepted = adversarial_contract()
    if accepted:
        fail("D2_V2_ACCOUNTING_SCHEMA_R2_ACCEPTED_INVALID")

    return {
        "status": "PASS" if snapshot.complete else "BLOCKED",
        "blocker_code": "NONE" if snapshot.complete else BLOCKER_CODE,
        "root_cause": ROOT_CAUSE,
        "producer_schema_recovery_method": RECOVERY_METHOD,
        "line_based_schema_parser_used": False,
        "regex_schema_parser_used": False,
        "frozen_accounting_hash_match": True,
        "producer_node_unambiguous": True,
        "producer_schema_field_count": len(audit.producer_fields),
        "accounting_artifact_field_count": len(audit.artifact_fields),
        "serializer_provenance_only_field_count": len(ENVELOPE_TYPES),
        "full_accounting_semantic_concepts_required": audit.full_semantic_concepts_required,
        "exact_name_matches": audit.exact_name_matches,
        "schema_proven_name_corrections": audit.schema_proven_name_corrections,
        "canonical_fields_missing": audit.canonical_fields_missing,
        "ambiguous_semantic_mappings": audit.ambiguous_semantic_mappings,
        "wrong_type_count": audit.wrong_type_count,
        "wrong_value_count": audit.wrong_value_count,
        "unresolved_field_mismatches": audit.unresolved_field_mismatches,
        "r5_expected_d1_metric_field": R5_NONCANONICAL_EXPECTATION,
        "frozen_canonical_d1_metric_field": CANONICAL_D1_METRIC_FIELD,
        "canonical_d1_metric_field_value": accounting[CANONICAL_D1_METRIC_FIELD],
        "d1_field_semantic_equivalence_pass": True,
        "frozen_canonical_d2_v1_metric_result_read_field": "d2_v1_metric_reads",
        "frozen_canonical_d2_v1_metric_result_read_value": accounting["d2_v1_metric_reads"],
        "all_execution_accounting_semantics_pass": True,
        "r5_scientific_oracle_completed_before_blocker": bool(r5_blocker["metric_oracle_completed"]),
        "r5_scientific_oracle_divergence_count": (
            int(r5_blocker["prediction_divergences"])
            + int(r5_blocker["d0_preservation_violations"])
            + int(r5_blocker["trigger_class_violations"])
        ),
        "r5_snapshot_direct_values_pass": snapshot.direct_values_pass,
        "r5_snapshot_parse_counts_pass": snapshot.parse_counts_pass,
        "r5_snapshot_missing_required_field_count": len(snapshot.missing_required_fields),
        "r5_snapshot_missing_required_fields": snapshot.missing_required_fields,
        "r5_completed_scientific_oracle_snapshot_complete": snapshot.complete,
        "custody_compatibility_pass": True,
        "result_freeze_commit": RESULT_FREEZE_COMMIT,
        "post_result_freeze_mutations": 0,
        "scientific_artifacts_reopened_during_r2": False,
        "label_parses_during_r2": 0,
        "test1_feature_accesses": 0,
        "test2_accesses": 0,
        "outer_executions": 0,
        "authoritative_scientific_executions": 0,
        "result_driven_changes": False,
        "independent_attacks": attacks,
        "accepted_invalid": accepted,
        "completion_eligible": snapshot.complete,
    }


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_ACCOUNTING_SCHEMA_R2_ARGUMENTS_REJECTED")
        return 2
    try:
        result = real_remediation()
    except AccountingSchemaR2Error as error:
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
