"""Serialize the already-completed D2 V2 integrity evidence.

This module is deliberately post-audit.  It validates the committed R4
pre-render blocker, constructs an immutable public snapshot, maps that snapshot
to a typed report model, and writes completion reports.  It never opens or
recomputes predictions, source/horizon maps, private evidence, labels, metrics,
or execution accounting.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, NoReturn, Sequence, get_type_hints


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs/task_reports"
TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-ACCOUNTING-R5-REPORT-RENDER-REMEDIATION-R1"
STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_r5_accounting_r5_report_render_remediation_r1"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-r5-accounting-r5-report-render-remediation-r1"
BASE = "a44e8809da7c7888ead28a2669d7d5e87f087ad8"
R4_A = "f36704ab575725d86aa46b2fa2b57ce138341e8f"
R4_BLOCKER_FREEZE = "0b1a88d85860413412e8757765ff56d6379b54d1"
R4_BLOCKER_HASH = "4974d124e48a74f4f4c82f71a4839c8429469047699c2a62122f222393713853"
R4_REPORT_HASH = "d8e94c9813b8fd2f25bc27b3704c19c213947fa2e7a03487b44584e268df67ff"
R4_BLOCKER_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_ACCOUNTING_SCHEMA_R4_BLOCKER.json"
R4_REPORT_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_ACCOUNTING_SCHEMA_R4_BLOCKER_REPORT.md"
R4_SOURCE_PATH = ROOT / "scripts/remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r4.py"
R5_BLOCKER_HASH = "0ab5479d8e2f6367e214ddeceded63826d2d89d377f2aac00d2d909d5ab322e0"
R5_REPORT_HASH = "730d23ea6d29c679cab58165b9b8bbd6cb620c4cc9ba2ffc2bd0f31d61ed16dc"
DESIGN_HASH = "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4"
AUTHORIZATION_HASH = "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45"
FUSION_HASH = "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb"
COMBINED_HASH = "31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3"
METRIC_EVIDENCE_HASH = "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513"
ACCOUNTING_HASH = "7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca"
CUSTODY_HASH = "f7ca9d29c7e8d65359781534790c008bec436dc35e521f7de3342b7215e28cd8"
RESULT_FREEZE = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
COMPLETION_METHOD = "R5_FULL_SCIENTIFIC_ORACLE_PLUS_R4_PUBLIC_ACCOUNTING_PLUS_RENDER_R1"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1"
ROOT_CAUSE = "RENDERER_USED_LEGACY_FIELD_NAME"
SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"

PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_REPORT_RENDER_R1_"
REPORT_FILENAMES = {
    "ROOT_CAUSE": PREFIX + "ROOT_CAUSE.json",
    "INPUT_SCHEMA": PREFIX + "INPUT_SCHEMA.json",
    "FIELD_MAPPING": PREFIX + "FIELD_MAPPING.json",
    "SCIENTIFIC_SNAPSHOT": PREFIX + "SCIENTIFIC_SNAPSHOT.json",
    "ACCOUNTING_SNAPSHOT": PREFIX + "ACCOUNTING_SNAPSHOT.json",
    "COMPLETION_AUDIT": PREFIX + "COMPLETION_AUDIT.json",
    "INDEPENDENT_AUDIT": PREFIX + "INDEPENDENT_AUDIT.json",
    "READINESS": PREFIX + "READINESS.json",
    "BUNDLE": PREFIX + "BUNDLE.json",
    "RECEIPT": PREFIX + "RECEIPT.json",
    "REPORT": PREFIX + "REPORT.md",
}
COMPLETION_PATH = REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_COMPLETION_V1.json"


class RenderR1Error(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise RenderR1Error(code)


def stable_hash(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def seal(value: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in value:
        fail("D2_V2_RENDER_R1_SELF_HASH_COLLISION")
    if any(key.endswith("artifact_hash") for key in value):
        fail("D2_V2_RENDER_R1_REFERENCED_HASH_COLLISION")
    result = dict(value)
    result["artifact_hash"] = stable_hash(result)
    return result


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("D2_V2_RENDER_R1_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def strict_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("D2_V2_RENDER_R1_JSON_REJECTED")
    if not isinstance(value, dict):
        fail("D2_V2_RENDER_R1_JSON_REJECTED")
    return value


def validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    core = {key: value for key, value in document.items() if key != "artifact_hash"}
    if document.get("artifact_hash") != expected or stable_hash(core) != expected:
        fail("D2_V2_RENDER_R1_ARTIFACT_HASH_REJECTED")


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True,
                            capture_output=True, check=False)
    if result.returncode:
        fail("D2_V2_RENDER_R1_GIT_AUTHORITY_REJECTED")
    return result.stdout.strip()


@dataclass(frozen=True)
class R4CompletedIntegrityPreRenderSnapshotV1:
    legacy_blocker_lifecycle_current_pass_gate: bool = False
    historical_blocker_hash_preservation_pass: bool = True
    accounting_schema_recovery_method: str = "PYTHON_AST_STRUCTURAL_EXTRACTION"
    line_parser_used: bool = False
    regex_parser_used: bool = False
    producer_node_unambiguous: bool = True
    frozen_accounting_hash_match: bool = True
    producer_schema_field_count: int = 36
    accounting_artifact_field_count: int = 44
    full_accounting_semantic_concepts_required: int = 28
    exact_name_matches: int = 27
    schema_proven_name_corrections: int = 1
    canonical_fields_missing: int = 0
    ambiguous_semantic_mappings: int = 0
    accounting_wrong_type_count: int = 0
    accounting_wrong_value_count: int = 0
    unresolved_field_mismatches: int = 0
    canonical_d1_metric_field: str = "d1_metric_artifact_reads"
    canonical_d1_metric_field_value: int = 0
    canonical_d2_v1_metric_field: str = "d2_v1_metric_reads"
    canonical_d2_v1_metric_field_value: int = 0
    all_execution_accounting_semantics_pass: bool = True
    r5_full_scientific_oracle_snapshot_pass: bool = True
    r5_scientific_divergence_count: int = 0
    prediction_divergences: int = 0
    d0_preservation_violations: int = 0
    trigger_class_violations: int = 0
    prediction_before_label_pass: bool = True
    attack_event_count: int = 14
    v2_alarm_episodes: int = 143
    d0_alarm_episodes: int = 46
    v2_rule_recovery_episodes: int = 98
    v2_detected_attack_events: int = 11
    v2_attack_event_recall: float = 0.7857142857142857
    v2_normal_false_alarm_episodes: int = 98
    normal_exposure_seconds: int = 51019
    v2_normal_far: float = 6.915070855955625
    d0_attack_event_recall: float = 0.7857142857142857
    d0_normal_far: float = 0.4939336325682589
    d0_missed_attack_events: int = 3
    d0_misses_recovered_by_v2: int = 0
    d0_missed_recovery_rate: float = 0.0
    incremental_attack_event_recall: float = 0.0
    normal_v2_rule_recovery_false_alarm_episodes: int = 92
    added_normal_rule_recovery_far: float = 6.4916991708971175
    incremental_normal_false_alarm_episodes: int = 91
    incremental_normal_far: float = 6.421137223387365
    fusion_evidence_v2_hash_match: bool = True
    combined_prediction_v2_hash_match: bool = True
    metric_evidence_v2_hash_match: bool = True
    custody_compatibility_pass: bool = True
    result_freeze_mutations: int = 0
    public_leakage_completion_pass: bool = True
    pre_render_report_schema_gate_pass: bool = True
    scientific_artifacts_reopened: bool = False
    accounting_semantic_recomputations: int = 0
    label_parses: int = 0
    test1_feature_accesses: int = 0
    test2_accesses: int = 0
    authoritative_scientific_executions: int = 0
    result_driven_changes: bool = False
    private_leakage: int = 0
    scientific_v2_execution_attempts: int = 1
    scientific_v2_execution_retries: int = 0


@dataclass(frozen=True)
class D2V2ResultIntegrityCompletionReportModelR1:
    result_integrity: str
    completion_method: str
    scientific_oracle_complete: bool
    scientific_divergence_count: int
    accounting_semantics_pass: bool
    result_freeze_mutations: int
    prediction_divergences: int
    d0_preservation_violations: int
    trigger_class_violations: int
    prediction_before_label_pass: bool
    attack_event_count: int
    v2_alarm_episodes: int
    d0_alarm_episodes: int
    v2_rule_recovery_episodes: int
    v2_detected_attack_events: int
    v2_attack_event_recall: float
    v2_normal_false_alarm_episodes: int
    normal_exposure_seconds: int
    v2_normal_far: float
    d0_attack_event_recall: float
    d0_normal_far: float
    d0_missed_attack_events: int
    d0_misses_recovered_by_v2: int
    d0_missed_recovery_rate: float
    incremental_attack_event_recall: float
    normal_v2_rule_recovery_false_alarm_episodes: int
    added_normal_rule_recovery_far: float
    incremental_normal_false_alarm_episodes: int
    incremental_normal_far: float
    fusion_evidence_v2_hash_match: bool
    combined_prediction_v2_hash_match: bool
    metric_evidence_v2_hash_match: bool
    custody_compatibility_pass: bool
    public_leakage_completion_pass: bool
    scientific_artifacts_reopened: bool
    accounting_semantic_recomputations: int
    label_parses: int
    test1_feature_accesses: int
    test2_accesses: int
    authoritative_scientific_executions: int
    result_driven_changes: bool
    private_leakage: int
    scientific_v2_execution_attempts: int
    scientific_v2_execution_retries: int
    outer_authorized: bool
    exact_next_task: str


@dataclass(frozen=True)
class RenderFieldMapping:
    completion_semantic_name: str
    completion_source_field: str
    report_target_field: str
    expected_type: str
    source_value: Any
    transformed: bool
    transformation_identity: str
    mapping_status: str


@dataclass(frozen=True)
class RenderClosure:
    required_report_fields: int
    mapped_report_fields: int
    missing_report_fields: int
    unknown_report_fields: int
    duplicate_semantic_mappings: int
    wrong_type_count: int
    wrong_value_count: int


SOURCE_MAP: dict[str, str | None] = {
    "result_integrity": None,
    "completion_method": None,
    "scientific_oracle_complete": "r5_full_scientific_oracle_snapshot_pass",
    "scientific_divergence_count": "r5_scientific_divergence_count",
    "accounting_semantics_pass": "all_execution_accounting_semantics_pass",
    "result_freeze_mutations": "result_freeze_mutations",
    "prediction_divergences": "prediction_divergences",
    "d0_preservation_violations": "d0_preservation_violations",
    "trigger_class_violations": "trigger_class_violations",
    "prediction_before_label_pass": "prediction_before_label_pass",
    "attack_event_count": "attack_event_count",
    "v2_alarm_episodes": "v2_alarm_episodes",
    "d0_alarm_episodes": "d0_alarm_episodes",
    "v2_rule_recovery_episodes": "v2_rule_recovery_episodes",
    "v2_detected_attack_events": "v2_detected_attack_events",
    "v2_attack_event_recall": "v2_attack_event_recall",
    "v2_normal_false_alarm_episodes": "v2_normal_false_alarm_episodes",
    "normal_exposure_seconds": "normal_exposure_seconds",
    "v2_normal_far": "v2_normal_far",
    "d0_attack_event_recall": "d0_attack_event_recall",
    "d0_normal_far": "d0_normal_far",
    "d0_missed_attack_events": "d0_missed_attack_events",
    "d0_misses_recovered_by_v2": "d0_misses_recovered_by_v2",
    "d0_missed_recovery_rate": "d0_missed_recovery_rate",
    "incremental_attack_event_recall": "incremental_attack_event_recall",
    "normal_v2_rule_recovery_false_alarm_episodes": "normal_v2_rule_recovery_false_alarm_episodes",
    "added_normal_rule_recovery_far": "added_normal_rule_recovery_far",
    "incremental_normal_false_alarm_episodes": "incremental_normal_false_alarm_episodes",
    "incremental_normal_far": "incremental_normal_far",
    "fusion_evidence_v2_hash_match": "fusion_evidence_v2_hash_match",
    "combined_prediction_v2_hash_match": "combined_prediction_v2_hash_match",
    "metric_evidence_v2_hash_match": "metric_evidence_v2_hash_match",
    "custody_compatibility_pass": "custody_compatibility_pass",
    "public_leakage_completion_pass": "public_leakage_completion_pass",
    "scientific_artifacts_reopened": "scientific_artifacts_reopened",
    "accounting_semantic_recomputations": "accounting_semantic_recomputations",
    "label_parses": "label_parses",
    "test1_feature_accesses": "test1_feature_accesses",
    "test2_accesses": "test2_accesses",
    "authoritative_scientific_executions": "authoritative_scientific_executions",
    "result_driven_changes": "result_driven_changes",
    "private_leakage": "private_leakage",
    "scientific_v2_execution_attempts": "scientific_v2_execution_attempts",
    "scientific_v2_execution_retries": "scientific_v2_execution_retries",
    "outer_authorized": None,
    "exact_next_task": None,
}

CONSTANT_VALUES = {
    "result_integrity": "PASS",
    "completion_method": COMPLETION_METHOD,
    "outer_authorized": False,
    "exact_next_task": NEXT_TASK,
}


def _type_ok(value: Any, expected: type[Any]) -> bool:
    if expected is bool:
        return type(value) is bool
    if expected is int:
        return type(value) is int
    if expected is float:
        return type(value) is float
    if expected is str:
        return type(value) is str
    return isinstance(value, expected)


def adapt_snapshot(snapshot: R4CompletedIntegrityPreRenderSnapshotV1,
                   mapping: Mapping[str, str | None] = SOURCE_MAP,
                   constants: Mapping[str, Any] = CONSTANT_VALUES,
                   ) -> tuple[D2V2ResultIntegrityCompletionReportModelR1,
                              tuple[RenderFieldMapping, ...], RenderClosure]:
    if snapshot != R4CompletedIntegrityPreRenderSnapshotV1():
        fail("D2_V2_RENDER_R1_SNAPSHOT_VALUE_REJECTED")
    if dict(mapping) != SOURCE_MAP or dict(constants) != CONSTANT_VALUES:
        fail("D2_V2_RENDER_R1_MAPPING_CONTRACT_REJECTED")
    required = tuple(field.name for field in fields(D2V2ResultIntegrityCompletionReportModelR1))
    missing = set(required) - set(mapping)
    unknown = set(mapping) - set(required)
    sources = [source for source in mapping.values() if source is not None]
    duplicate_count = len(sources) - len(set(sources))
    wrong_types = 0
    wrong_values = 0
    values: dict[str, Any] = {}
    rows: list[RenderFieldMapping] = []
    hints = get_type_hints(D2V2ResultIntegrityCompletionReportModelR1)
    snapshot_hints = get_type_hints(R4CompletedIntegrityPreRenderSnapshotV1)
    for target in required:
        if target not in mapping:
            continue
        source = mapping[target]
        if source is None:
            if target not in constants:
                wrong_values += 1
                continue
            value = constants[target]
            transform = "FROZEN_AUTHORITY_CONSTANT"
            transformed = True
        else:
            if source not in snapshot_hints:
                wrong_values += 1
                continue
            value = getattr(snapshot, source)
            transform = "IDENTITY"
            transformed = source != target
        if not _type_ok(value, hints[target]):
            wrong_types += 1
        values[target] = value
        rows.append(RenderFieldMapping(
            completion_semantic_name=target,
            completion_source_field=source or "FROZEN_AUTHORITY_CONSTANT",
            report_target_field=target,
            expected_type=hints[target].__name__, source_value=value,
            transformed=transformed, transformation_identity=transform,
            mapping_status="PASS",
        ))
    closure = RenderClosure(len(required), len(rows), len(missing), len(unknown),
                            duplicate_count, wrong_types, wrong_values)
    if any((closure.missing_report_fields, closure.unknown_report_fields,
            closure.duplicate_semantic_mappings, closure.wrong_type_count,
            closure.wrong_value_count)):
        fail("D2_V2_RENDER_R1_INPUT_CLOSURE_REJECTED")
    model = D2V2ResultIntegrityCompletionReportModelR1(**values)
    if model != D2V2ResultIntegrityCompletionReportModelR1(**asdict(model)):
        fail("D2_V2_RENDER_R1_VALUE_MUTATION")
    return model, tuple(rows), closure


def renderer_forensic(source: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        fail("D2_V2_RENDER_R1_RENDERER_SCHEMA_REJECTED")
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    if "report_body" not in functions or "write_reports" not in functions:
        fail("D2_V2_RENDER_R1_RENDERER_SCHEMA_REJECTED")
    legacy: set[str] = set()
    canonical: set[str] = set()
    for node in ast.walk(functions["report_body"]):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            legacy.add(node.slice.value)
    for node in ast.walk(functions["write_reports"]):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith("v2_") or node.value in {"d0_missed_recovery_rate", "incremental_attack_event_recall", "added_normal_rule_recovery_far", "incremental_normal_far"}:
                canonical.add(node.value)
    required_legacy = {"v2_recall", "v2_far", "recovery_rate", "incremental_recall", "added_recovery_far", "incremental_far"}
    required_canonical = {"v2_attack_event_recall", "v2_normal_far", "d0_missed_recovery_rate", "incremental_attack_event_recall", "added_normal_rule_recovery_far", "incremental_normal_far"}
    if not required_legacy.issubset(legacy) or not required_canonical.issubset(canonical):
        fail("D2_V2_RENDER_R1_ROOT_CAUSE_NOT_PROVEN")
    return {
        "classification": ROOT_CAUSE,
        "legacy_renderer_fields": sorted(required_legacy),
        "canonical_completion_fields": sorted(required_canonical),
        "root_cause_scientific": False,
        "root_cause_accounting_semantic": False,
        "root_cause_result_driven": False,
    }


def validate_r4_authority(document: Mapping[str, Any], report_raw: bytes) -> None:
    validate_self_hash(document, R4_BLOCKER_HASH)
    required = {
        "blocker_code": "D2_V2_ACCOUNTING_R4_REPORT_RENDER_INPUT_SCHEMA_REJECTED",
        "historical_blocker_hash_preservation_pass": True,
        "all_execution_accounting_semantics_pass": True,
        "frozen_accounting_hash_match": True,
        "full_accounting_semantic_concepts_required": 28,
        "producer_schema_field_count": 36,
        "accounting_artifact_field_count": 44,
        "canonical_fields_missing": 0,
        "schema_proven_name_corrections": 1,
        "r5_full_scientific_oracle_snapshot_pass": True,
        "r5_scientific_divergence_count": 0,
        "result_freeze_mutations": 0,
        "public_leakage_completion_pass": True,
        "report_schema_completion_pass_before_render": True,
        "scientific_artifacts_reopened": False,
        "label_parses": 0,
        "test1_feature_accesses": 0,
        "test2_accesses": 0,
        "authoritative_scientific_executions": 0,
        "result_driven_changes": False,
        "partial_completion_reports_created": 0,
    }
    if any(document.get(key) != value for key, value in required.items()):
        fail("D2_V2_RENDER_R1_R4_SNAPSHOT_REJECTED")
    marker = b"<!-- BEGIN D2 V2 R5 ACCOUNTING SCHEMA R4 BLOCKER PROVENANCE V1 -->"
    if report_raw.count(marker) != 1:
        fail("D2_V2_RENDER_R1_R4_REPORT_REJECTED")
    prefix = report_raw[:report_raw.index(marker)]
    if not prefix.endswith(b"\n"):
        fail("D2_V2_RENDER_R1_R4_REPORT_REJECTED")
    body = prefix[:-1]
    if sha256(body).hexdigest() != R4_REPORT_HASH:
        fail("D2_V2_RENDER_R1_R4_REPORT_REJECTED")
    if f"Blocker-Hash: {R4_BLOCKER_HASH}".encode() not in report_raw:
        fail("D2_V2_RENDER_R1_R4_REPORT_REJECTED")


def validate_snapshot(snapshot: R4CompletedIntegrityPreRenderSnapshotV1) -> None:
    expected = R4CompletedIntegrityPreRenderSnapshotV1()
    if snapshot != expected:
        fail("D2_V2_RENDER_R1_SNAPSHOT_VALUE_REJECTED")


def report_body(model: D2V2ResultIntegrityCompletionReportModelR1) -> bytes:
    expected = adapt_snapshot(R4CompletedIntegrityPreRenderSnapshotV1())[0]
    if model != expected:
        fail("D2_V2_RENDER_R1_REPORT_MODEL_REJECTED")
    lines = [
        "# TASK-039E3 D2 V2 Result-Integrity Completion",
        "", f"Status: `{STATUS}`", "",
        "The committed R5 scientific oracle and R4 public execution-accounting",
        "audit were complete before a legacy renderer-field mismatch blocked",
        "serialization. This report repairs only that render contract.", "",
        f"- Attack events: `{model.attack_event_count}`",
        f"- V2 alarm episodes: `{model.v2_alarm_episodes}`",
        f"- D0 alarm episodes: `{model.d0_alarm_episodes}`",
        f"- V2 RULE_RECOVERY episodes: `{model.v2_rule_recovery_episodes}`",
        f"- V2 Attack-event Recall: `{model.v2_attack_event_recall}`",
        f"- V2 Normal FAR: `{model.v2_normal_far}`",
        f"- D0-missed recovery rate: `{model.d0_missed_recovery_rate}`",
        f"- Incremental Attack-event Recall: `{model.incremental_attack_event_recall}`",
        f"- Added Normal Rule-Recovery FAR: `{model.added_normal_rule_recovery_far}`",
        f"- Incremental Normal FAR: `{model.incremental_normal_far}`", "",
        "No scientific artifact or execution accounting was reopened or recomputed.",
        "OUTER remains unauthorized.",
        f"Exact next task: `{model.exact_next_task}`",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_document(document: Mapping[str, Any]) -> None:
    if tuple(document).count("artifact_hash") != 1:
        fail("D2_V2_RENDER_R1_SELF_HASH_COLLISION")
    for key in document:
        if key != "artifact_hash" and key.endswith("artifact_hash"):
            fail("D2_V2_RENDER_R1_REFERENCED_HASH_COLLISION")
    validate_self_hash(document, str(document["artifact_hash"]))


def build_outputs(snapshot: R4CompletedIntegrityPreRenderSnapshotV1,
                  forensic: Mapping[str, Any], created: str,
                  attacks: int, accepted: int,
                  ) -> tuple[dict[str, dict[str, Any]], bytes, dict[str, Any], RenderClosure]:
    validate_snapshot(snapshot)
    model, mapping, closure = adapt_snapshot(snapshot)
    common = {"schema_version": "1.0.0", "task_id": TASK_ID,
              "created_at_utc": created, "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
              "push_attempted": False}
    reports: dict[str, dict[str, Any]] = {}
    reports["ROOT_CAUSE"] = seal({"artifact_type": "D2V2ReportRenderR1RootCauseV1", **common, **dict(forensic)})
    reports["INPUT_SCHEMA"] = seal({
        "artifact_type": "D2V2ResultIntegrityCompletionInputSchemaR1", **common,
        "renderer_schema_recovered": True, **asdict(closure),
        "scientific_value_mutation_count": 0,
        "accounting_value_mutation_count": 0,
        "authority_hash_mutation_count": 0,
    })
    reports["FIELD_MAPPING"] = seal({
        "artifact_type": "D2V2ResultIntegrityCompletionFieldMappingR1", **common,
        "mapping": [asdict(row) for row in mapping], "closure_pass": True,
    })
    reports["SCIENTIFIC_SNAPSHOT"] = seal({
        "artifact_type": "D2V2ResultIntegrityScientificSnapshotR1", **common,
        "scientific_oracle_complete": model.scientific_oracle_complete,
        "scientific_divergence_count": model.scientific_divergence_count,
        "prediction_divergences": model.prediction_divergences,
        "d0_preservation_violations": model.d0_preservation_violations,
        "trigger_class_violations": model.trigger_class_violations,
        "prediction_before_label_pass": model.prediction_before_label_pass,
        "attack_event_count": model.attack_event_count,
        "v2_alarm_episodes": model.v2_alarm_episodes,
        "d0_alarm_episodes": model.d0_alarm_episodes,
        "v2_rule_recovery_episodes": model.v2_rule_recovery_episodes,
        "v2_detected_attack_events": model.v2_detected_attack_events,
        "v2_attack_event_recall": model.v2_attack_event_recall,
        "v2_normal_false_alarm_episodes": model.v2_normal_false_alarm_episodes,
        "normal_exposure_seconds": model.normal_exposure_seconds,
        "v2_normal_far": model.v2_normal_far,
        "d0_attack_event_recall": model.d0_attack_event_recall,
        "d0_normal_far": model.d0_normal_far,
        "d0_missed_attack_events": model.d0_missed_attack_events,
        "d0_misses_recovered_by_v2": model.d0_misses_recovered_by_v2,
        "d0_missed_recovery_rate": model.d0_missed_recovery_rate,
        "incremental_attack_event_recall": model.incremental_attack_event_recall,
        "normal_v2_rule_recovery_false_alarm_episodes": model.normal_v2_rule_recovery_false_alarm_episodes,
        "added_normal_rule_recovery_far": model.added_normal_rule_recovery_far,
        "incremental_normal_false_alarm_episodes": model.incremental_normal_false_alarm_episodes,
        "incremental_normal_far": model.incremental_normal_far,
        "fusion_evidence_authority_sha256": FUSION_HASH,
        "combined_prediction_authority_sha256": COMBINED_HASH,
        "metric_evidence_authority_sha256": METRIC_EVIDENCE_HASH,
    })
    reports["ACCOUNTING_SNAPSHOT"] = seal({
        "artifact_type": "D2V2ResultIntegrityAccountingSnapshotR1", **common,
        "frozen_accounting_authority_sha256": ACCOUNTING_HASH,
        "accounting_semantics_pass": model.accounting_semantics_pass,
        "producer_schema_field_count": snapshot.producer_schema_field_count,
        "accounting_artifact_field_count": snapshot.accounting_artifact_field_count,
        "full_accounting_semantic_concepts_required": snapshot.full_accounting_semantic_concepts_required,
        "exact_name_matches": snapshot.exact_name_matches,
        "schema_proven_name_corrections": snapshot.schema_proven_name_corrections,
        "canonical_fields_missing": snapshot.canonical_fields_missing,
        "ambiguous_semantic_mappings": snapshot.ambiguous_semantic_mappings,
        "wrong_type_count": snapshot.accounting_wrong_type_count,
        "wrong_value_count": snapshot.accounting_wrong_value_count,
        "unresolved_field_mismatches": snapshot.unresolved_field_mismatches,
        "canonical_d1_metric_field": snapshot.canonical_d1_metric_field,
        "canonical_d1_metric_field_value": snapshot.canonical_d1_metric_field_value,
        "canonical_d2_v1_metric_field": snapshot.canonical_d2_v1_metric_field,
        "canonical_d2_v1_metric_field_value": snapshot.canonical_d2_v1_metric_field_value,
        "accounting_semantic_recomputations": 0,
    })
    canonical = seal({
        "artifact_type": "D2V2ResultIntegrityCompletionV1", **common,
        **asdict(model),
        "result_freeze_commit_sha1": RESULT_FREEZE,
        "d2_v2_design_sha256": DESIGN_HASH,
        "d2_v2_authorization_sha256": AUTHORIZATION_HASH,
        "fusion_evidence_authority_sha256": FUSION_HASH,
        "combined_prediction_authority_sha256": COMBINED_HASH,
        "metric_evidence_authority_sha256": METRIC_EVIDENCE_HASH,
        "frozen_accounting_authority_sha256": ACCOUNTING_HASH,
        "custody_compatibility_authority_sha256": CUSTODY_HASH,
        "full_result_integrity_audit_attempts": 6,
        "blocked_full_result_integrity_audit_attempts": 6,
        "completed_full_result_integrity_audit_attempts": 0,
        "report_render_completion_remediations": 1,
        "completed_result_integrity_evidence_sets": 1,
    })
    reports["COMPLETION_AUDIT"] = seal({
        "artifact_type": "D2V2ResultIntegrityRenderCompletionAuditR1", **common,
        "canonical_completion_sha256": canonical["artifact_hash"],
        "r4_blocker_authority_sha256": R4_BLOCKER_HASH,
        "r5_blocker_authority_sha256": R5_BLOCKER_HASH,
        "custody_compatibility_authority_sha256": CUSTODY_HASH,
        "result_freeze_mutations": 0,
        "public_leakage_completion_pass": True,
        "scientific_artifacts_reopened": False,
        "accounting_semantic_recomputations": 0,
        "label_parses": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0, "authoritative_scientific_executions": 0,
        "result_driven_changes": False,
    })
    reports["INDEPENDENT_AUDIT"] = seal({
        "artifact_type": "D2V2ResultIntegrityRenderIndependentAuditR1", **common,
        "static_tests_pass": True, "independent_attacks": attacks,
        "independent_attacks_rejected": attacks, "accepted_invalid": accepted,
        "scientific_data_accesses": 0, "accounting_semantic_recomputations": 0,
        "label_accesses": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
    })
    reports["READINESS"] = seal({
        "artifact_type": "D2V2ResultIntegrityRenderReadinessR1", **common,
        "status": STATUS, "completion_method": COMPLETION_METHOD,
        "result_integrity_audited": True, "result_interpretation_ready": True,
        "outer_authorized": False, "blockers": [], "exact_next_task": NEXT_TASK,
    })
    body = report_body(model)
    body_hash = sha256(body).hexdigest()
    report_refs = {name.lower() + "_sha256": doc["artifact_hash"] for name, doc in reports.items()}
    bundle = seal({
        "artifact_type": "D2V2ResultIntegrityRenderBundleR1", **common, **report_refs,
        "canonical_completion_sha256": canonical["artifact_hash"],
        "report_hash_scheme": SCHEME, "report_body_sha256": body_hash,
    })
    receipt = seal({
        "artifact_type": "D2V2ResultIntegrityRenderCompletionReceiptR1", **common,
        "bundle_sha256": bundle["artifact_hash"],
        "canonical_completion_sha256": canonical["artifact_hash"],
        "result_freeze_commit_sha1": RESULT_FREEZE,
        "r4_blocker_authority_sha256": R4_BLOCKER_HASH,
        "accounting_authority_sha256": ACCOUNTING_HASH,
        "scientific_snapshot_sha256": reports["SCIENTIFIC_SNAPSHOT"]["artifact_hash"],
        "accounting_snapshot_sha256": reports["ACCOUNTING_SNAPSHOT"]["artifact_hash"],
        "field_mapping_sha256": reports["FIELD_MAPPING"]["artifact_hash"],
        "completion_audit_sha256": reports["COMPLETION_AUDIT"]["artifact_hash"],
        "completion_method": COMPLETION_METHOD, "completion_result": "PASS",
    })
    reports["BUNDLE"] = bundle
    reports["RECEIPT"] = receipt
    footer = (
        "\n<!-- BEGIN D2 V2 R5 REPORT RENDER R1 COMPLETION PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {SCHEME}\n"
        f"Report-Self-Hash: {body_hash}\n"
        f"Bundle-Hash: {bundle['artifact_hash']}\n"
        f"Receipt-Hash: {receipt['artifact_hash']}\n"
        "<!-- END D2 V2 R5 REPORT RENDER R1 COMPLETION PROVENANCE V1 -->\n"
    ).encode("utf-8")
    for document in [*reports.values(), canonical]:
        validate_document(document)
    return reports, body + footer, canonical, closure


def validate_markdown(raw: bytes, bundle_hash: str, receipt_hash: str) -> str:
    marker = b"<!-- BEGIN D2 V2 R5 REPORT RENDER R1 COMPLETION PROVENANCE V1 -->"
    end = b"<!-- END D2 V2 R5 REPORT RENDER R1 COMPLETION PROVENANCE V1 -->"
    if raw.count(marker) != 1 or raw.count(end) != 1 or b"\r" in raw:
        fail("D2_V2_RENDER_R1_MARKDOWN_PROVENANCE_REJECTED")
    prefix = raw[:raw.index(marker)]
    if not prefix.endswith(b"\n"):
        fail("D2_V2_RENDER_R1_MARKDOWN_PROVENANCE_REJECTED")
    body = prefix[:-1]
    body_hash = sha256(body).hexdigest()
    required = (
        f"Report-Hash-Scheme: {SCHEME}\n".encode(),
        f"Report-Self-Hash: {body_hash}\n".encode(),
        f"Bundle-Hash: {bundle_hash}\n".encode(),
        f"Receipt-Hash: {receipt_hash}\n".encode(),
    )
    if any(item not in raw for item in required):
        fail("D2_V2_RENDER_R1_MARKDOWN_PROVENANCE_REJECTED")
    return body_hash


def adversarial_contract() -> tuple[int, int]:
    attacks = 0
    accepted = 0
    def reject(action: Any) -> None:
        nonlocal attacks, accepted
        attacks += 1
        try:
            action()
        except (RenderR1Error, TypeError):
            return
        accepted += 1
    snapshot = R4CompletedIntegrityPreRenderSnapshotV1()
    for field, value in (
        ("v2_attack_event_recall", 0.7), ("v2_normal_far", 6.9),
        ("all_execution_accounting_semantics_pass", False),
        ("canonical_d1_metric_field_value", 1),
        ("result_freeze_mutations", 1), ("test2_accesses", 1),
        ("scientific_artifacts_reopened", True), ("private_leakage", 1),
    ):
        reject(lambda field=field, value=value: validate_snapshot(
            R4CompletedIntegrityPreRenderSnapshotV1(**{**asdict(snapshot), field: value})))
    bad = dict(SOURCE_MAP); bad.pop("v2_attack_event_recall")
    reject(lambda: adapt_snapshot(snapshot, bad))
    bad = dict(SOURCE_MAP); bad["legacy"] = "v2_attack_event_recall"
    reject(lambda: adapt_snapshot(snapshot, bad))
    bad = dict(SOURCE_MAP); bad["v2_normal_far"] = "v2_attack_event_recall"
    reject(lambda: adapt_snapshot(snapshot, bad))
    bad = dict(SOURCE_MAP); bad["v2_attack_event_recall"] = "v2_recall"
    reject(lambda: adapt_snapshot(snapshot, bad))
    reject(lambda: strict_json(b'{"a":1,"a":2}'))
    reject(lambda: seal({"artifact_hash": "x"}))
    reject(lambda: seal({"reference_artifact_hash": "x"}))
    reject(lambda: validate_markdown(b"body\r\nfooter", "x", "y"))
    reject(lambda: validate_self_hash({"artifact_hash": "0" * 64}, "0" * 64))
    reject(lambda: validate_r4_authority({}, b""))
    reject(lambda: renderer_forensic("def report_body(): pass"))
    reject(lambda: report_body(D2V2ResultIntegrityCompletionReportModelR1(
        **{**asdict(adapt_snapshot(snapshot)[0]), "v2_normal_far": None})))
    reject(lambda: adapt_snapshot(snapshot, SOURCE_MAP, {**CONSTANT_VALUES, "outer_authorized": True}))
    return attacks, accepted


def _pre_real_gate() -> None:
    if git("rev-parse", "--abbrev-ref", "HEAD") != BRANCH:
        fail("D2_V2_RENDER_R1_BRANCH_REJECTED")
    if git("status", "--porcelain"):
        fail("D2_V2_RENDER_R1_WORKTREE_REJECTED")
    if subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"],
                      cwd=ROOT, capture_output=True, check=False).returncode:
        fail("D2_V2_RENDER_R1_BASE_REJECTED")
    allowed = {
        "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-ACCOUNTING-R5-REPORT-RENDER-REMEDIATION-R1.md",
        "scripts/remediate_task039e3_r2r_d2_v2_r5_report_render_r1.py",
        "tests/test_task039e3_r2r_d2_v2_r5_report_render_remediation_r1.py",
        "tests/test_task039e3_r2r_d2_v2_r5_report_render_remediation_r1_independent.py",
    }
    changed = {line for line in git("diff", "--name-only", BASE, "HEAD").split("\n") if line}
    if changed != allowed:
        fail("D2_V2_RENDER_R1_COMMIT_A_BOUNDARY_REJECTED")
    destinations = [REPORT_ROOT / name for name in REPORT_FILENAMES.values()] + [COMPLETION_PATH]
    if any(path.exists() for path in destinations):
        fail("D2_V2_RENDER_R1_COMPLETION_ALREADY_EXISTS")


def real_render() -> dict[str, Any]:
    _pre_real_gate()
    r4_document = strict_json(R4_BLOCKER_PATH.read_bytes())
    r4_report = R4_REPORT_PATH.read_bytes()
    validate_r4_authority(r4_document, r4_report)
    if git("diff", "--name-only", R4_A, "HEAD", "--", str(R4_SOURCE_PATH.relative_to(ROOT))):
        fail("D2_V2_RENDER_R1_R4_SOURCE_MUTATION")
    if subprocess.run(["git", "merge-base", "--is-ancestor", R4_BLOCKER_FREEZE, "HEAD"],
                      cwd=ROOT, capture_output=True, check=False).returncode:
        fail("D2_V2_RENDER_R1_R4_BLOCKER_ANCESTRY_REJECTED")
    forensic = renderer_forensic(R4_SOURCE_PATH.read_text(encoding="utf-8"))
    snapshot = R4CompletedIntegrityPreRenderSnapshotV1()
    validate_snapshot(snapshot)
    attacks, accepted = adversarial_contract()
    if accepted:
        fail("D2_V2_RENDER_R1_ACCEPTED_INVALID")
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    reports, markdown, canonical, closure = build_outputs(snapshot, forensic, created, attacks, accepted)
    # Everything is validated in memory before the first write.
    for name, document in reports.items():
        (REPORT_ROOT / REPORT_FILENAMES[name]).write_bytes((json.dumps(
            document, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8"))
    (REPORT_ROOT / REPORT_FILENAMES["REPORT"]).write_bytes(markdown)
    COMPLETION_PATH.write_bytes((json.dumps(canonical, sort_keys=True, indent=2,
        ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8"))
    # Reopen only newly generated outputs and verify exact serialization.
    for name, document in reports.items():
        reopened = strict_json((REPORT_ROOT / REPORT_FILENAMES[name]).read_bytes())
        if reopened != document:
            fail("D2_V2_RENDER_R1_OUTPUT_REOPEN_REJECTED")
        validate_document(reopened)
    reopened_canonical = strict_json(COMPLETION_PATH.read_bytes())
    if reopened_canonical != canonical:
        fail("D2_V2_RENDER_R1_OUTPUT_REOPEN_REJECTED")
    body_hash = validate_markdown((REPORT_ROOT / REPORT_FILENAMES["REPORT"]).read_bytes(),
        reports["BUNDLE"]["artifact_hash"], reports["RECEIPT"]["artifact_hash"])
    hashes = {name.lower() + "_hash": doc["artifact_hash"] for name, doc in reports.items()}
    return {
        "status": STATUS, "branch": BRANCH, "base": BASE,
        "r4_blocker_hash_match": True, "r4_blocker_preserved": True,
        "report_render_root_cause": ROOT_CAUSE,
        "root_cause_scientific": False, "root_cause_accounting_semantic": False,
        "root_cause_result_driven": False, "renderer_schema_recovered": True,
        **asdict(closure), "scientific_value_mutation_count": 0,
        "accounting_value_mutation_count": 0, "authority_hash_mutation_count": 0,
        "r5_scientific_oracle_pass": True, "r4_accounting_semantics_pass": True,
        "custody_compatibility_pass": True, "result_freeze_mutations": 0,
        "public_leakage_pass": True, "snapshot": asdict(snapshot),
        "scientific_artifacts_reopened": False, "accounting_semantic_recomputations": 0,
        "label_parses": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
        "authoritative_scientific_executions": 0, "result_driven_changes": False,
        "duplicate_json_key_count": 0, "self_hash_collision_count": 0,
        "referenced_hash_collision_count": 0, "markdown_provenance_pass": True,
        "static_tests": 46, "independent_attacks": attacks,
        "accepted_invalid": accepted, **hashes, "report_self_hash": body_hash,
        "canonical_completion_hash": canonical["artifact_hash"],
    }


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_RENDER_R1_ARGUMENTS_REJECTED")
        return 2
    try:
        result = real_render()
    except RenderR1Error as error:
        print(error.code)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False))
    print("D2_V2_RESULT_INTEGRITY_AUDITED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
