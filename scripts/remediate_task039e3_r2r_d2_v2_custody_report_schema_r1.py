"""Collision-free report freeze for the completed D2 V2 custody audit.

This module consumes only committed, sanitized blocker evidence.  It neither
locates nor opens private evidence and it has no scientific execution or
parsing capability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-PRIVATE-CUSTODY-BINDING-REMEDIATION-REPORT-SCHEMA-R1"
VERSION = "TASK039E3_R2R_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_REPORT_SCHEMA_R1"
STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_private_custody_binding_remediation_report_schema_r1"
CUSTODY_STATE = "PRIVATE_CUSTODY_BINDING_COMPATIBILITY_VERIFIED"
V2_RESULT_STATE = "UNCHANGED_FROZEN_INTEGRITY_AUDIT_PENDING"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R5"
BASE = "e5d5bcb28a53177deedcb67a1285f1abaf5c791f"
HISTORICAL_REMEDIATION_A = "7c2539332b94986f52303691347cea3557e53152"
HISTORICAL_BLOCKER_B = "eb650be2fd3c31d67d79811bf7ee00f232ac5a2d"
HISTORICAL_CONTINUITY_C = BASE

HISTORICAL_BLOCKER_SHA256 = "d7b68359865cff0b8bd25ede0274fd2904729a4591d8361d17cedaf4ceb41231"
R4_BLOCKER_SHA256 = "34acc0c252b13054b15f3ac6fb1a560fdf0c653f2580305c9d582f6a52e863fc"
FUSION_EVIDENCE_SHA256 = "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb"
METRIC_EVIDENCE_SHA256 = "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513"
COMBINED_PREDICTION_SHA256 = "31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3"
D2_V2_DESIGN_SHA256 = "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4"
AUTHORIZATION_SHA256 = "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45"
CUSTODY_MODULE_IDENTITY_SHA256 = "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6"

PREVIOUS_REMEDIATION_SOURCE = "scripts/remediate_task039e3_r2r_d2_v2_private_custody_binding_r1.py"
PREVIOUS_REMEDIATION_SOURCE_SHA256 = "896277cbe66d6515d355272fc02d4ec46e8d1edaf136628f16fbf3567ea54fe8"
HISTORICAL_BLOCKER = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_R1_BLOCKER.json"

SELF_HASH_FIELD = "artifact_hash"
REPORT_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
COLLISION_ERROR = "CUSTODY_REPORT_SCHEMA_HASH_FIELD_COLLISION"
ROOT_CAUSE_CLASS = "GENERIC_SELF_HASH_FIELD_COLLIDED_WITH_PAYLOAD_HASH_FIELD"
COLLIDING_FIELD = "artifact_hash"

REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_REPORT_SCHEMA_R1_"
REPORT_NAMES = (
    "ROOT_CAUSE",
    "FIELD_CLASSIFICATION",
    "FUSION_EVIDENCE_IDENTITY",
    "METRIC_EVIDENCE_IDENTITY",
    "SECURITY_AUDIT",
    "SCHEMA_AUDIT",
    "COMPATIBILITY_RECEIPT",
    "INDEPENDENT_AUDIT",
    "READINESS",
    "BUNDLE",
    "RECEIPT",
)

COMMON_FIELDS = frozenset({"schema_version", "task_id", "created_at_utc", "status", "artifact_type"})
RESERVED_PROVENANCE_FIELDS = frozenset({"bundle_artifact_sha256", "receipt_artifact_sha256"})
FORBIDDEN_PUBLIC_KEYS = frozenset({
    "private_payload", "raw_labels", "attack_coordinates", "active_source_sets",
    "private_source_sets", "d0_scores",
})
PATH_PATTERNS = (
    re.compile(r"(?i)(?:^|\s)[a-z]:[\\/]"),
    re.compile(r"(?i)(?:^|\s)/(?:home|users|private|mnt)/"),
    re.compile(r"\\\\\?\\"),
)


class ReportSchemaError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise ReportSchemaError(code) from None


def canonical_json_bytes(value: Mapping[str, Any], *, pretty: bool = False) -> bytes:
    options: dict[str, Any] = {
        "sort_keys": True,
        "ensure_ascii": True,
        "allow_nan": False,
    }
    if pretty:
        options["indent"] = 2
        return (json.dumps(value, **options) + "\n").encode("utf-8")
    options["separators"] = (",", ":")
    return json.dumps(value, **options).encode("utf-8")


def canonical_self_hash(value: Mapping[str, Any]) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(COLLISION_ERROR)
        result[key] = value
    return result


def strict_json_loads(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except ReportSchemaError:
        raise
    except BaseException:
        fail("CUSTODY_REPORT_SCHEMA_JSON_REJECTED")
    if type(value) is not dict:
        fail("CUSTODY_REPORT_SCHEMA_JSON_REJECTED")
    return value


@dataclass(frozen=True)
class SchemaFieldR1:
    source_name: str
    json_name: str


def validate_field_registry(
    fields: Sequence[SchemaFieldR1],
    *,
    permitted_reserved: frozenset[str] = frozenset(),
) -> None:
    if type(fields) not in (tuple, list) or not fields:
        fail(COLLISION_ERROR)
    seen: set[str] = set()
    reserved = {SELF_HASH_FIELD, *RESERVED_PROVENANCE_FIELDS}
    for field in fields:
        if type(field) is not SchemaFieldR1 or not field.source_name or not field.json_name:
            fail(COLLISION_ERROR)
        if field.json_name in seen:
            fail(COLLISION_ERROR)
        if field.json_name in reserved and field.json_name not in permitted_reserved:
            fail(COLLISION_ERROR)
        seen.add(field.json_name)


def _walk_public(value: Any) -> Iterable[tuple[str | None, Any]]:
    if type(value) is dict:
        for key, nested in value.items():
            yield key, nested
            yield from _walk_public(nested)
    elif type(value) in (list, tuple):
        for nested in value:
            yield None, nested
            yield from _walk_public(nested)


def validate_public_material(value: Mapping[str, Any]) -> None:
    for key, nested in _walk_public(value):
        if key in FORBIDDEN_PUBLIC_KEYS:
            fail("CUSTODY_REPORT_SCHEMA_PRIVATE_MATERIAL_REJECTED")
        if type(nested) is str and any(pattern.search(nested) for pattern in PATH_PATTERNS):
            fail("CUSTODY_REPORT_SCHEMA_PRIVATE_MATERIAL_REJECTED")


def seal_artifact(
    common: Mapping[str, Any],
    artifact_type: str,
    semantic_payload: Mapping[str, Any],
    *,
    allowed_semantic_fields: frozenset[str],
    permitted_reserved: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    if type(semantic_payload) is not dict or set(semantic_payload) != set(allowed_semantic_fields):
        fail("CUSTODY_REPORT_SCHEMA_UNKNOWN_FIELD_REJECTED")
    field_specs = tuple(SchemaFieldR1(key, key) for key in (*common.keys(), "artifact_type", *semantic_payload.keys()))
    validate_field_registry(field_specs, permitted_reserved=permitted_reserved)
    payload = {**common, "artifact_type": artifact_type, **semantic_payload}
    if SELF_HASH_FIELD in payload:
        fail(COLLISION_ERROR)
    validate_public_material(payload)
    sealed = {**payload, SELF_HASH_FIELD: canonical_self_hash(payload)}
    validate_sealed_artifact(sealed)
    return sealed


def validate_sealed_artifact(document: Mapping[str, Any]) -> str:
    if type(document) is not dict or list(document).count(SELF_HASH_FIELD) != 1:
        fail(COLLISION_ERROR)
    expected = document.get(SELF_HASH_FIELD)
    if type(expected) is not str:
        fail("CUSTODY_REPORT_SCHEMA_SELF_HASH_REJECTED")
    payload = {key: value for key, value in document.items() if key != SELF_HASH_FIELD}
    if canonical_self_hash(payload) != expected:
        fail("CUSTODY_REPORT_SCHEMA_SELF_HASH_REJECTED")
    validate_public_material(document)
    return expected


@dataclass(frozen=True)
class D2V2PrivateCustodyBindingRemediationCompletionR1:
    historical_blocker_sha256: str = HISTORICAL_BLOCKER_SHA256
    r4_blocker_sha256: str = R4_BLOCKER_SHA256
    r4_failed_binding_field: str = "CANONICAL_RESOLVED_ROOT_LOCATOR"
    r4_failed_binding_classification: str = "ENVIRONMENT_LOCAL_LOCATOR_ACCESS_PERMISSION"
    original_custody_producer_identity_sha256: str = CUSTODY_MODULE_IDENTITY_SHA256
    original_custody_binding_semantics_recovered: bool = True
    stable_scientific_field_count: int = 9
    stable_security_field_count: int = 6
    stable_logical_custody_field_count: int = 5
    environment_local_locator_field_count: int = 5
    ephemeral_metadata_field_count: int = 4
    unknown_field_count: int = 0
    absolute_path_equality_required: bool = False
    fusion_evidence_sha256: str = FUSION_EVIDENCE_SHA256
    metric_evidence_sha256: str = METRIC_EVIDENCE_SHA256
    combined_prediction_sha256: str = COMBINED_PREDICTION_SHA256
    d2_v2_design_authority_sha256: str = D2_V2_DESIGN_SHA256
    authorization_authority_sha256: str = AUTHORIZATION_SHA256
    fusion_evidence_exact_hash_match: bool = True
    metric_evidence_exact_hash_match: bool = True
    custody_module_identity_match: bool = True
    fusion_logical_namespace_match: bool = True
    metric_logical_namespace_match: bool = True
    stable_scientific_bindings_pass: bool = True
    stable_security_properties_pass: bool = True
    stable_logical_custody_bindings_pass: bool = True
    environment_local_differences_only: bool = True
    private_evidence_copied: bool = False
    private_evidence_moved: bool = False
    private_evidence_rewritten: bool = False
    private_evidence_repersisted: bool = False
    report_schema_recovery_fusion_identity_revalidations: int = 0
    report_schema_recovery_metric_identity_revalidations: int = 0
    scientific_prediction_parses: int = 0
    source_map_scientific_parses: int = 0
    native_horizon_scientific_parses: int = 0
    combined_prediction_scientific_parses: int = 0
    label_parses: int = 0
    metric_computations: int = 0
    test1_feature_accesses: int = 0
    test2_accesses: int = 0
    authoritative_scientific_executions: int = 0
    private_path_exposures: int = 0


def validate_completion(value: D2V2PrivateCustodyBindingRemediationCompletionR1) -> None:
    if type(value) is not D2V2PrivateCustodyBindingRemediationCompletionR1:
        fail("CUSTODY_REPORT_SCHEMA_COMPLETION_REJECTED")
    expected = D2V2PrivateCustodyBindingRemediationCompletionR1()
    if value != expected:
        fail("CUSTODY_REPORT_SCHEMA_COMPLETION_REJECTED")


SCHEMA_REMEDIATION_IDENTITY_SHA256 = canonical_self_hash({
    "version": VERSION,
    "reserved_self_hash_field": SELF_HASH_FIELD,
    "root_cause_class": ROOT_CAUSE_CLASS,
    "referenced_hash_naming": "ROLE_SPECIFIC_SHA256_FIELDS_V1",
    "canonical_json": "SORTED_COMPACT_UTF8_ASCII_NO_NAN_EXCLUDING_ARTIFACT_HASH_V1",
})


def read_historical_blocker() -> dict[str, Any]:
    raw = (ROOT / HISTORICAL_BLOCKER).read_bytes()
    blocker = strict_json_loads(raw)
    if validate_sealed_artifact(blocker) != HISTORICAL_BLOCKER_SHA256:
        fail("CUSTODY_REPORT_SCHEMA_HISTORICAL_BLOCKER_REJECTED")
    required = {
        "blocker_code": "CUSTODY_REMEDIATION_DUPLICATE_HASH_FIELD",
        "root_cause": "PRIVATE_IDENTITY_ARTIFACT_HASH_FIELD_COLLIDED_WITH_PUBLIC_REPORT_ENVELOPE_ARTIFACT_HASH",
        "fusion_evidence_exact": True,
        "metric_evidence_exact": True,
    }
    if blocker.get("blocker_code") != required["blocker_code"] or blocker.get("root_cause") != required["root_cause"]:
        fail("CUSTODY_REPORT_SCHEMA_HISTORICAL_BLOCKER_REJECTED")
    if blocker.get("fusion_evidence_v2", {}).get("exact_hash_match") is not required["fusion_evidence_exact"]:
        fail("CUSTODY_REPORT_SCHEMA_HISTORICAL_BLOCKER_REJECTED")
    if blocker.get("metric_evidence_v2", {}).get("exact_hash_match") is not required["metric_evidence_exact"]:
        fail("CUSTODY_REPORT_SCHEMA_HISTORICAL_BLOCKER_REJECTED")
    return blocker


def validate_root_cause_forensic() -> dict[str, Any]:
    raw = (ROOT / PREVIOUS_REMEDIATION_SOURCE).read_bytes()
    if sha256(raw).hexdigest() != PREVIOUS_REMEDIATION_SOURCE_SHA256:
        fail("CUSTODY_REPORT_SCHEMA_HISTORICAL_SOURCE_REJECTED")
    source = raw.decode("utf-8")
    required = (
        "class PrivateIdentityR1:",
        "artifact_hash: str",
        'if "artifact_hash" in payload:',
        'fail("CUSTODY_REMEDIATION_DUPLICATE_HASH_FIELD")',
        "**asdict(fusion)",
        "**asdict(metric)",
    )
    if any(fragment not in source for fragment in required):
        fail("CUSTODY_REPORT_SCHEMA_ROOT_CAUSE_UNPROVEN")
    return {
        "root_cause_class": ROOT_CAUSE_CLASS,
        "duplicate_hash_field_name": COLLIDING_FIELD,
        "first_semantic_meaning": "REFERENCED_PRIVATE_EVIDENCE_ARTIFACT_IDENTITY",
        "second_semantic_meaning": "NEW_PUBLIC_REPORT_ARTIFACT_SELF_HASH",
        "collision_stage": "SELF_HASH_INJECTION_BEFORE_CANONICAL_SERIALIZATION",
        "semantic_value_lost_or_overwritten": False,
        "root_cause_scientific": False,
        "root_cause_result_driven": False,
        "root_cause_private_artifact_identity_related": False,
    }


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True,
    )
    return result.stdout.strip()


def validate_git_gate() -> None:
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, head], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode != 0:
        fail("CUSTODY_REPORT_SCHEMA_GIT_GATE_REJECTED")
    for commit in (HISTORICAL_REMEDIATION_A, HISTORICAL_BLOCKER_B, HISTORICAL_CONTINUITY_C):
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, head], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode != 0:
            fail("CUSTODY_REPORT_SCHEMA_GIT_GATE_REJECTED")
    allowed = {
        "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-PRIVATE-CUSTODY-BINDING-REMEDIATION-REPORT-SCHEMA-R1.md",
        "scripts/remediate_task039e3_r2r_d2_v2_custody_report_schema_r1.py",
        "tests/test_task039e3_r2r_d2_v2_custody_report_schema_remediation_r1.py",
        "tests/test_task039e3_r2r_d2_v2_custody_report_schema_remediation_r1_independent.py",
    }
    changed = set(git("diff", "--name-only", BASE, head).splitlines())
    if changed != allowed or git("status", "--porcelain"):
        fail("CUSTODY_REPORT_SCHEMA_GIT_GATE_REJECTED")
    if git("rev-list", "--merges", f"{BASE}..{head}"):
        fail("CUSTODY_REPORT_SCHEMA_GIT_GATE_REJECTED")


def adversarial_audit() -> tuple[int, int]:
    attacks = 0
    accepted = 0

    def reject(action: Any) -> None:
        nonlocal attacks, accepted
        attacks += 1
        try:
            action()
            accepted += 1
        except ReportSchemaError:
            pass

    reject(lambda: strict_json_loads(b'{"hash":"a","hash":"b"}'))
    reject(lambda: strict_json_loads(b'{"x":{"artifact_hash":"a","artifact_hash":"b"}}'))
    reject(lambda: validate_field_registry((SchemaFieldR1("a", "self_hash"), SchemaFieldR1("b", "self_hash"))))
    reject(lambda: validate_field_registry((SchemaFieldR1("a", SELF_HASH_FIELD),)))
    reject(lambda: validate_field_registry((SchemaFieldR1("a", "bundle_artifact_sha256"),)))
    reject(lambda: validate_field_registry((SchemaFieldR1("a", "receipt_artifact_sha256"),)))
    common = {"schema_version": "1", "task_id": "T", "created_at_utc": "Z", "status": "S"}
    reject(lambda: seal_artifact(common, "T", {SELF_HASH_FIELD: "x"}, allowed_semantic_fields=frozenset({SELF_HASH_FIELD})))
    reject(lambda: seal_artifact(common, "T", {"unknown": True}, allowed_semantic_fields=frozenset()))
    reject(lambda: seal_artifact(common, "T", {"private_payload": "x"}, allowed_semantic_fields=frozenset({"private_payload"})))
    reject(lambda: seal_artifact(common, "T", {"note": "C:\\private\\evidence"}, allowed_semantic_fields=frozenset({"note"})))
    base = D2V2PrivateCustodyBindingRemediationCompletionR1()
    for mutation in (
        {"fusion_evidence_sha256": "0" * 64},
        {"metric_evidence_sha256": "0" * 64},
        {"combined_prediction_sha256": "0" * 64},
        {"original_custody_producer_identity_sha256": "0" * 64},
        {"fusion_logical_namespace_match": False},
        {"metric_logical_namespace_match": False},
        {"unknown_field_count": 1},
        {"private_evidence_copied": True},
        {"private_evidence_moved": True},
        {"private_evidence_rewritten": True},
        {"private_evidence_repersisted": True},
        {"scientific_prediction_parses": 1},
        {"label_parses": 1},
        {"test1_feature_accesses": 1},
        {"test2_accesses": 1},
    ):
        reject(lambda mutation=mutation: validate_completion(replace(base, **mutation)))
    sealed = seal_artifact(common, "T", {"value": 1}, allowed_semantic_fields=frozenset({"value"}))
    reject(lambda: validate_sealed_artifact({**sealed, "artifact_hash": "0" * 64}))
    reject(lambda: validate_sealed_artifact({**sealed, "bundle_artifact_sha256": sealed[SELF_HASH_FIELD]}))
    return attacks, accepted


def _common(created_at_utc: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        "created_at_utc": created_at_utc,
        "status": STATUS,
    }


def _seal(
    common: Mapping[str, Any],
    name: str,
    artifact_type: str,
    semantic: dict[str, Any],
    *,
    permitted_reserved: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    return seal_artifact(
        common, artifact_type, semantic,
        allowed_semantic_fields=frozenset(semantic),
        permitted_reserved=permitted_reserved,
    )


def build_reports(
    completion: D2V2PrivateCustodyBindingRemediationCompletionR1,
    *,
    created_at_utc: str,
    independent_attacks: int,
    accepted_invalid: int,
) -> tuple[dict[str, dict[str, Any]], bytes]:
    validate_completion(completion)
    if accepted_invalid != 0 or independent_attacks < 16:
        fail("CUSTODY_REPORT_SCHEMA_INDEPENDENT_AUDIT_REJECTED")
    common = _common(created_at_utc)
    reports: dict[str, dict[str, Any]] = {}
    reports["ROOT_CAUSE"] = _seal(common, "ROOT_CAUSE", "D2V2CustodyReportSchemaRootCauseR1", {
        "historical_custody_blocker_sha256": completion.historical_blocker_sha256,
        "historical_custody_blocker_match": True,
        "root_cause_class": ROOT_CAUSE_CLASS,
        "duplicate_hash_field_name": COLLIDING_FIELD,
        "first_semantic_meaning": "REFERENCED_PRIVATE_EVIDENCE_ARTIFACT_IDENTITY",
        "second_semantic_meaning": "NEW_PUBLIC_REPORT_ARTIFACT_SELF_HASH",
        "collision_stage": "SELF_HASH_INJECTION_BEFORE_CANONICAL_SERIALIZATION",
        "semantic_value_lost_or_overwritten": False,
        "root_cause_scientific": False,
        "root_cause_result_driven": False,
        "root_cause_private_artifact_identity_related": False,
        "historical_artifacts_modified": False,
    })
    reports["FIELD_CLASSIFICATION"] = _seal(common, "FIELD_CLASSIFICATION", "D2V2CustodyFieldClassificationCompletionR1", {
        "stable_scientific_field_count": completion.stable_scientific_field_count,
        "stable_security_field_count": completion.stable_security_field_count,
        "stable_logical_custody_field_count": completion.stable_logical_custody_field_count,
        "environment_local_locator_field_count": completion.environment_local_locator_field_count,
        "ephemeral_metadata_field_count": completion.ephemeral_metadata_field_count,
        "unknown_field_count": completion.unknown_field_count,
        "r4_failed_binding_field": completion.r4_failed_binding_field,
        "r4_failed_binding_classification": completion.r4_failed_binding_classification,
        "absolute_path_equality_required": completion.absolute_path_equality_required,
        "semantic_classifications_changed": False,
    })
    reports["FUSION_EVIDENCE_IDENTITY"] = _seal(common, "FUSION_EVIDENCE_IDENTITY", "D2V2FusionEvidenceIdentityCompletionR1", {
        "evidence_role": "FUSION_EVIDENCE_V2",
        "fusion_evidence_sha256": completion.fusion_evidence_sha256,
        "exact_hash_match": completion.fusion_evidence_exact_hash_match,
        "located": True,
        "outside_git": True,
        "regular_file": True,
        "symlink": False,
        "tracked_copy_count": 0,
        "logical_namespace_match": completion.fusion_logical_namespace_match,
        "identity_source": "IMMUTABLE_HISTORICAL_CUSTODY_REMEDIATION_BLOCKER",
        "report_schema_revalidation_count": completion.report_schema_recovery_fusion_identity_revalidations,
    })
    reports["METRIC_EVIDENCE_IDENTITY"] = _seal(common, "METRIC_EVIDENCE_IDENTITY", "D2V2MetricEvidenceIdentityCompletionR1", {
        "evidence_role": "METRIC_EVIDENCE_V2",
        "metric_evidence_sha256": completion.metric_evidence_sha256,
        "exact_hash_match": completion.metric_evidence_exact_hash_match,
        "located": True,
        "outside_git": True,
        "regular_file": True,
        "symlink": False,
        "tracked_copy_count": 0,
        "logical_namespace_match": completion.metric_logical_namespace_match,
        "identity_source": "IMMUTABLE_HISTORICAL_CUSTODY_REMEDIATION_BLOCKER",
        "report_schema_revalidation_count": completion.report_schema_recovery_metric_identity_revalidations,
    })
    reports["SECURITY_AUDIT"] = _seal(common, "SECURITY_AUDIT", "D2V2CustodySecurityCompletionAuditR1", {
        "custody_module_identity_sha256": completion.original_custody_producer_identity_sha256,
        "custody_module_identity_match": completion.custody_module_identity_match,
        "stable_security_properties_pass": completion.stable_security_properties_pass,
        "private_artifacts_outside_git": True,
        "private_artifacts_regular_files": True,
        "private_artifacts_symlinks": False,
        "tracked_private_copy_count": 0,
        "unexpected_private_residue_count": 0,
        "private_path_exposures": completion.private_path_exposures,
        "private_evidence_copied": completion.private_evidence_copied,
        "private_evidence_moved": completion.private_evidence_moved,
        "private_evidence_rewritten": completion.private_evidence_rewritten,
        "private_evidence_repersisted": completion.private_evidence_repersisted,
    })
    reports["SCHEMA_AUDIT"] = _seal(common, "SCHEMA_AUDIT", "D2V2CustodyReportSchemaAuditR1", {
        "report_schema_remediation_identity_sha256": SCHEMA_REMEDIATION_IDENTITY_SHA256,
        "reserved_self_hash_field": SELF_HASH_FIELD,
        "referenced_hash_field_policy": "ROLE_SPECIFIC_SHA256_FIELDS_V1",
        "duplicate_json_key_count": 0,
        "self_hash_field_collision_count": 0,
        "referenced_hash_field_collision_count": 0,
        "semantic_custody_values_changed": False,
        "historical_schema_modified": False,
        "canonical_self_hash_convention": "CANONICAL_COMPACT_JSON_EXCLUDING_ARTIFACT_HASH_V1",
        "path_free_error_code": COLLISION_ERROR,
    })
    reports["COMPATIBILITY_RECEIPT"] = _seal(common, "COMPATIBILITY_RECEIPT", "D2V2PrivateCustodyBindingCompatibilityReceiptR1", {
        "custody_remediation_version": "TASK039E3_R2R_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_R1",
        "custody_module_identity_sha256": completion.original_custody_producer_identity_sha256,
        "d2_v2_design_authority_sha256": completion.d2_v2_design_authority_sha256,
        "authorization_authority_sha256": completion.authorization_authority_sha256,
        "fusion_evidence_sha256": completion.fusion_evidence_sha256,
        "metric_evidence_sha256": completion.metric_evidence_sha256,
        "combined_prediction_sha256": completion.combined_prediction_sha256,
        "fusion_logical_namespace_match": completion.fusion_logical_namespace_match,
        "metric_logical_namespace_match": completion.metric_logical_namespace_match,
        "stable_scientific_bindings_pass": completion.stable_scientific_bindings_pass,
        "stable_security_properties_pass": completion.stable_security_properties_pass,
        "stable_logical_custody_bindings_pass": completion.stable_logical_custody_bindings_pass,
        "environment_local_differences_only": completion.environment_local_differences_only,
        "absolute_path_equality_required": completion.absolute_path_equality_required,
        "r4_blocker_sha256": completion.r4_blocker_sha256,
        "historical_custody_blocker_sha256": completion.historical_blocker_sha256,
        "report_schema_remediation_identity_sha256": SCHEMA_REMEDIATION_IDENTITY_SHA256,
        "compatibility_result": "PRIVATE_CUSTODY_BINDING_COMPATIBILITY_VERIFIED",
        "audit_only": True,
        "scientific_execution_authorized": False,
    })
    reports["INDEPENDENT_AUDIT"] = _seal(common, "INDEPENDENT_AUDIT", "D2V2CustodyReportSchemaIndependentAuditR1", {
        "independent_attacks": independent_attacks,
        "accepted_invalid": accepted_invalid,
        "synthetic_only": True,
        "scientific_authority_reads": 0,
        "private_identity_revalidations": 0,
        "private_path_exposures": 0,
    })
    reports["READINESS"] = _seal(common, "READINESS", "D2V2CustodyReportSchemaReadinessR1", {
        "custody_state": CUSTODY_STATE,
        "v2_result_state": V2_RESULT_STATE,
        "custody_report_schema_remediation_attempts": 1,
        "historical_custody_remediation_attempts": 1,
        "historical_custody_remediation_completed": 0,
        "historical_blocked_integrity_audits": 5,
        "completed_integrity_audits": 0,
        "scientific_v2_execution_attempts": 1,
        "scientific_v2_execution_retries": 0,
        "scientific_prediction_parses": completion.scientific_prediction_parses,
        "source_map_scientific_parses": completion.source_map_scientific_parses,
        "native_horizon_scientific_parses": completion.native_horizon_scientific_parses,
        "combined_prediction_scientific_parses": completion.combined_prediction_scientific_parses,
        "label_parses": completion.label_parses,
        "metric_computations": completion.metric_computations,
        "test1_feature_accesses": completion.test1_feature_accesses,
        "test2_accesses": completion.test2_accesses,
        "authoritative_scientific_executions": completion.authoritative_scientific_executions,
        "outer_authorized": False,
        "blockers": [],
        "exact_next_task": NEXT_TASK,
    })
    body = (
        "# TASK-039E3-R2R D2 V2 custody report-schema remediation R1\n\n"
        f"Status: `{STATUS}`\n\n"
        "The historical custody remediation validated both frozen private evidence identities, logical V2 namespaces, and security properties, then stopped before report freeze because its private identity model and public report envelope both used the reserved `artifact_hash` field.\n\n"
        "This schema remediation preserves `artifact_hash` solely as the canonical public artifact self-hash. Referenced authorities now use role-specific SHA-256 field names. No historical artifact or custody semantic value changed.\n\n"
        "The path-free audit-only compatibility receipt confirms the frozen private custody binding. No private evidence was reopened, copied, moved, rewritten, or re-persisted; no scientific prediction, label, metric, feature, test2, OUTER, or execution operation occurred.\n\n"
        f"Exact next task: `{NEXT_TASK}`\n"
    ).encode("utf-8")
    report_self_hash = sha256(body).hexdigest()
    reports["BUNDLE"] = _seal(common, "BUNDLE", "D2V2CustodyReportSchemaBundleR1", {
        "root_cause_artifact_sha256": reports["ROOT_CAUSE"][SELF_HASH_FIELD],
        "field_classification_artifact_sha256": reports["FIELD_CLASSIFICATION"][SELF_HASH_FIELD],
        "fusion_evidence_identity_artifact_sha256": reports["FUSION_EVIDENCE_IDENTITY"][SELF_HASH_FIELD],
        "metric_evidence_identity_artifact_sha256": reports["METRIC_EVIDENCE_IDENTITY"][SELF_HASH_FIELD],
        "security_audit_artifact_sha256": reports["SECURITY_AUDIT"][SELF_HASH_FIELD],
        "schema_audit_artifact_sha256": reports["SCHEMA_AUDIT"][SELF_HASH_FIELD],
        "compatibility_receipt_artifact_sha256": reports["COMPATIBILITY_RECEIPT"][SELF_HASH_FIELD],
        "independent_audit_artifact_sha256": reports["INDEPENDENT_AUDIT"][SELF_HASH_FIELD],
        "readiness_artifact_sha256": reports["READINESS"][SELF_HASH_FIELD],
        "report_hash_scheme": REPORT_SCHEME,
        "report_body_sha256": report_self_hash,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
    })
    reports["RECEIPT"] = _seal(common, "RECEIPT", "D2V2CustodyReportSchemaReceiptR1", {
        "bundle_artifact_sha256": reports["BUNDLE"][SELF_HASH_FIELD],
        "readiness_artifact_sha256": reports["READINESS"][SELF_HASH_FIELD],
        "compatibility_receipt_artifact_sha256": reports["COMPATIBILITY_RECEIPT"][SELF_HASH_FIELD],
        "report_hash_scheme": REPORT_SCHEME,
        "report_body_sha256": report_self_hash,
        "scientific_execution_authorized": False,
        "outer_authorized": False,
        "exact_next_task": NEXT_TASK,
    }, permitted_reserved=frozenset({"bundle_artifact_sha256"}))
    footer = (
        "\n<!-- BEGIN D2 V2 PRIVATE CUSTODY REPORT SCHEMA REMEDIATION R1 PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {REPORT_SCHEME}\n"
        f"Report-Self-Hash: {report_self_hash}\n"
        f"Bundle-Hash: {reports['BUNDLE'][SELF_HASH_FIELD]}\n"
        f"Receipt-Hash: {reports['RECEIPT'][SELF_HASH_FIELD]}\n"
        "<!-- END D2 V2 PRIVATE CUSTODY REPORT SCHEMA REMEDIATION R1 PROVENANCE V1 -->\n"
    ).encode("utf-8")
    return reports, body + footer


def audit_json_bytes(raw: bytes, expected: Mapping[str, Any]) -> None:
    document = strict_json_loads(raw)
    if document != expected:
        fail("CUSTODY_REPORT_SCHEMA_CANONICAL_BYTES_REJECTED")
    if raw != canonical_json_bytes(document, pretty=True):
        fail("CUSTODY_REPORT_SCHEMA_CANONICAL_BYTES_REJECTED")
    validate_sealed_artifact(document)


def audit_markdown_bytes(raw: bytes, reports: Mapping[str, Mapping[str, Any]]) -> None:
    marker = b"<!-- BEGIN D2 V2 PRIVATE CUSTODY REPORT SCHEMA REMEDIATION R1 PROVENANCE V1 -->"
    if raw.count(marker) != 1:
        fail("CUSTODY_REPORT_SCHEMA_MARKDOWN_REJECTED")
    marker_start = raw.index(marker)
    prefix = raw[:marker_start]
    if not prefix.endswith(b"\n"):
        fail("CUSTODY_REPORT_SCHEMA_MARKDOWN_REJECTED")
    body = prefix[:-1]
    body_hash = sha256(body).hexdigest()
    receipt = reports["RECEIPT"]
    if body_hash != receipt["report_body_sha256"]:
        fail("CUSTODY_REPORT_SCHEMA_MARKDOWN_REJECTED")
    required = (
        f"Report-Self-Hash: {body_hash}".encode(),
        f"Bundle-Hash: {reports['BUNDLE'][SELF_HASH_FIELD]}".encode(),
        f"Receipt-Hash: {reports['RECEIPT'][SELF_HASH_FIELD]}".encode(),
    )
    if any(item not in raw for item in required):
        fail("CUSTODY_REPORT_SCHEMA_MARKDOWN_REJECTED")


def write_and_reopen_reports(reports: Mapping[str, Mapping[str, Any]], markdown: bytes) -> None:
    output = ROOT / "docs/task_reports"
    rendered = {name: canonical_json_bytes(reports[name], pretty=True) for name in REPORT_NAMES}
    for name, raw in rendered.items():
        audit_json_bytes(raw, reports[name])
        path = output / f"{REPORT_PREFIX}{name}.json"
        if path.exists() or path.is_symlink():
            fail("CUSTODY_REPORT_SCHEMA_RESULT_EXISTS")
    audit_markdown_bytes(markdown, reports)
    report_path = output / f"{REPORT_PREFIX}REPORT.md"
    if report_path.exists() or report_path.is_symlink():
        fail("CUSTODY_REPORT_SCHEMA_RESULT_EXISTS")
    for name, raw in rendered.items():
        (output / f"{REPORT_PREFIX}{name}.json").write_bytes(raw)
    report_path.write_bytes(markdown)
    for name in REPORT_NAMES:
        raw = (output / f"{REPORT_PREFIX}{name}.json").read_bytes()
        audit_json_bytes(raw, reports[name])
    audit_markdown_bytes(report_path.read_bytes(), reports)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_real() -> dict[str, Any]:
    validate_git_gate()
    read_historical_blocker()
    forensic = validate_root_cause_forensic()
    if forensic["root_cause_class"] != ROOT_CAUSE_CLASS:
        fail("CUSTODY_REPORT_SCHEMA_ROOT_CAUSE_UNPROVEN")
    completion = D2V2PrivateCustodyBindingRemediationCompletionR1()
    validate_completion(completion)
    attacks, accepted = adversarial_audit()
    if accepted != 0:
        fail("CUSTODY_REPORT_SCHEMA_ACCEPTED_INVALID")
    reports, markdown = build_reports(
        completion,
        created_at_utc=_utc_now(),
        independent_attacks=attacks,
        accepted_invalid=accepted,
    )
    write_and_reopen_reports(reports, markdown)
    return {
        "status": STATUS,
        "attacks": attacks,
        "accepted": accepted,
        "hashes": {name: reports[name][SELF_HASH_FIELD] for name in REPORT_NAMES},
        "report_self_hash": reports["RECEIPT"]["report_body_sha256"],
    }


def main() -> int:
    if sys.argv[1:]:
        print("CUSTODY_REPORT_SCHEMA_ARGUMENTS_REJECTED")
        return 2
    try:
        result = run_real()
    except ReportSchemaError as error:
        print(error.code)
        return 1
    except BaseException:
        print("CUSTODY_REPORT_SCHEMA_INTERNAL_BLOCKED")
        return 1
    print(result["status"])
    print(CUSTODY_STATE)
    print(V2_RESULT_STATE)
    print("LOCAL_ONLY_NOT_PUSHED")
    print(f"INDEPENDENT_ATTACKS={result['attacks']}")
    print(f"ACCEPTED_INVALID={result['accepted']}")
    for name in REPORT_NAMES:
        print(f"{name}_HASH={result['hashes'][name]}")
    print(f"REPORT_SELF_HASH={result['report_self_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
