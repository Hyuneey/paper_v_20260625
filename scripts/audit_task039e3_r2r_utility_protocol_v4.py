"""Independent public-only attack oracle for TASK-039E3 Utility Protocol V4.

The primary oracle in this module reconstructs COMMON, numeric references,
feature scope, and regression identities from lower committed public
authorities using only the Python standard library.  Production V4 validators
are invoked only as attack subjects.  The private registry and HAI files are
never resolved or opened.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, fields, replace
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping

import paperworks.v6.task039e3_r2r_utility_protocol_v4 as v4


AUTHORITY_VERSION = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"
CALIBRATION_POLICY_VERSION = "TASK039D0_CONTINUOUS_STEP_CALIBRATION_V1"
COMMON_AUTHORITY_HASH = "3bd07e1c2baf375bde86a2310b529dda40962e027edbd77485f431dc244730ff"
EXECUTABLE_EQUIVALENCE_HASH = "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f"
E1_MANIFEST_HASH = "ee8c5b7e9895f5f6afdd1be2563244e3b82dca9c3eadca502dd522940931e3ae"
AUTHORITY_DEFINITION_HASH = "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de"
CALIBRATION_POLICY_HASH = "4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881"
NORMAL_INPUT_IDENTITY_SET_HASH = "cc502d87daf19a1511f868c1c767045a4457d505d195b0214f244d1910fe0cda"
PRIVATE_REGISTRY_CONTENT_HASH = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
MATERIALIZED_AUDIT_RECEIPT_HASH = "1f319fd7283040a4e866df3ac7d679e896142162084209bf00962947256c2bf1"
EXPECTED_DESCRIPTOR_HASH = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
EXPECTED_REFERENCE_SET_HASH = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
EXPECTED_V4_AUTHORITY_HASH = "2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1"
EXPECTED_FEATURE_REPORT_HASH = "62fd76bd541437694aff274db865670f24eecbabf3c736f32893bd97081564b8"
EXPECTED_RUNTIME_SCHEMA_HASH = "e7a0c46d28491b9d03a333a0ad1e87d686a982bafba072861913e05fb6c50b58"
HISTORICAL_E1_HASH = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
HISTORICAL_REGISTRY_HASH = "59e81b261801f28eefc917256dc628af704a14b4064161972d01545968555271"

CORRECTED_REGRESSION_HASHES = (
    "e50300efd372fb8a5c4567a6fa9e3277e36804506b306ea0053f7fc4ab48ceed",
    "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4",
    "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a",
)
HISTORICAL_WRONG_REGRESSION_HASHES = (
    "e50300ef65ae8ab71631c00125fe6d694397714daf220a3a3a7df79115ce68bb",
    "6e4a446743cbd8c69cd93b9ccbd660b1f4e30f63f75575d37dd57bb6ab4c8250",
    "4c7b6cfd2c18ddc5a6ca5b13285fc2acb67e4bda43fd8436dbb1e302164a1da0",
)

ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)

PATHS = {
    "executable": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json",
    "evidence": "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
    "dataset": "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json",
    "csv": "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json",
    "c0": "configs/v6/task039c0_candidate_discovery_protocol.json",
    "br2": "configs/v6/task039br2_hai_continuous_step_feasibility.json",
    "audit_receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json",
    "feature_report": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_V3_FEATURE_SCHEMA.json",
    "regression_numeric": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_REAUDIT_NUMERIC_AUTHORITY.json",
    "event_policy": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EVENT_POLICY.json",
    "metric_policy": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_METRIC_POLICY.json",
}


class IndependentAuditError(ValueError):
    """Sanitized independent-oracle failure."""


def stable_hash(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(repo_root: Path, key: str) -> dict[str, Any]:
    document = json.loads((repo_root / PATHS[key]).read_text(encoding="utf-8"))
    if type(document) is not dict:
        raise IndependentAuditError(f"AUDIT_DOCUMENT_TYPE:{key}")
    return document


def verify_self_hash(document: Mapping[str, Any], expected: str, key: str = "artifact_hash") -> None:
    if document.get(key) != expected:
        raise IndependentAuditError("AUDIT_FROZEN_HASH")
    payload = {name: value for name, value in document.items() if name != key}
    if stable_hash(payload) != expected:
        raise IndependentAuditError("AUDIT_SELF_HASH")


def reference_identity(relation: Mapping[str, Any], role: str) -> str:
    preimage = {
        "authority_version": AUTHORITY_VERSION,
        "relation_binding_hash": relation["relation_binding_hash"],
        "semantic_execution_hash": relation["semantic_execution_hash"],
        "numeric_role": role,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "normal_input_identity_set": NORMAL_INPUT_IDENTITY_SET_HASH,
        "common42_authority_hash": COMMON_AUTHORITY_HASH,
    }
    return f"{AUTHORITY_VERSION}:{stable_hash(preimage)}"


def reconstruct_common(repo_root: Path) -> dict[str, Any]:
    executable = load_json(repo_root, "executable")
    evidence = load_json(repo_root, "evidence")
    verify_self_hash(executable, EXECUTABLE_EQUIVALENCE_HASH)
    verify_self_hash(evidence, E1_MANIFEST_HASH)
    records = executable.get("relation_records")
    entries = evidence.get("entries")
    if type(records) is not list or type(entries) is not list or len(records) != 42 or len(entries) != 42:
        raise IndependentAuditError("AUDIT_COMMON_CARDINALITY")
    by_binding = {entry["relation_binding_hash"]: entry for entry in entries}
    if len(by_binding) != 42:
        raise IndependentAuditError("AUDIT_COMMON_DUPLICATE")
    relations: list[dict[str, Any]] = []
    historical: set[str] = set()
    for record in sorted(records, key=lambda item: item["relation_binding_hash"]):
        signature = record.get("executable_signature")
        if type(signature) is not dict or stable_hash(signature) != record.get("semantic_execution_hash"):
            raise IndependentAuditError("AUDIT_COMMON_SEMANTIC")
        if record.get("common_arm_cells") != ["T0", "T1", "T1-B"]:
            raise IndependentAuditError("AUDIT_COMMON_MEMBERSHIP")
        binding = record["relation_binding_hash"]
        entry = by_binding.get(binding)
        if entry is None:
            raise IndependentAuditError("AUDIT_COMMON_MANIFEST_JOIN")
        expected = {
            "source": signature["source"],
            "target": signature["target"],
            "source_step_direction": signature["source_step_direction"],
            "target_response_direction": signature["target_response_direction"],
            "selected_horizon_seconds": signature["selected_delay_horizon_seconds"],
        }
        if any(entry.get(name) != value for name, value in expected.items()):
            raise IndependentAuditError("AUDIT_COMMON_MANIFEST_SEMANTIC")
        historical_rows = entry.get("numeric_references")
        if type(historical_rows) is not list or len(historical_rows) != 11:
            raise IndependentAuditError("AUDIT_HISTORICAL_REFERENCE_CARDINALITY")
        historical.update(row["numeric_reference"] for row in historical_rows)
        relations.append(
            {
                "relation_identity": entry["relation_identity"],
                "relation_binding_hash": binding,
                "semantic_execution_hash": record["semantic_execution_hash"],
                "source": signature["source"],
                "target": signature["target"],
                "source_direction": signature["source_step_direction"],
                "target_direction": signature["target_response_direction"],
                "selected_horizon_seconds": signature["selected_delay_horizon_seconds"],
                "historical_reference_by_role": {
                    row["numeric_role"]: row["numeric_reference"] for row in historical_rows
                },
            }
        )
    references = [reference_identity(relation, role) for relation in relations for role in ROLES]
    reference_set_hash = stable_hash(
        {
            "authority_version": AUTHORITY_VERSION,
            "reference_count": len(references),
            "reference_identities": sorted(references),
        }
    )
    if len(set(references)) != 420 or reference_set_hash != EXPECTED_REFERENCE_SET_HASH:
        raise IndependentAuditError("AUDIT_REFERENCE_SET")
    return {
        "relations": relations,
        "references": tuple(references),
        "reference_set_hash": reference_set_hash,
        "historical_references": frozenset(historical),
        "sources": tuple(sorted({item["source"] for item in relations})),
        "targets": tuple(sorted({item["target"] for item in relations})),
    }


def reconstruct_numeric_descriptor(common: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "artifact_type": "task039e3_r2r_utility_protocol_v4_numeric_authority_descriptor",
        "authority_definition_hash": AUTHORITY_DEFINITION_HASH,
        "authority_version": AUTHORITY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "common42_authority_hash": COMMON_AUTHORITY_HASH,
        "common_executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "materialized_authority_audit_receipt_hash": MATERIALIZED_AUDIT_RECEIPT_HASH,
        "new_reference_set_hash": common["reference_set_hash"],
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "private_registry_content_hash": PRIVATE_REGISTRY_CONTENT_HASH,
        "record_count": 420,
        "reference_count": 420,
        "relation_count": 42,
        "role_count": 10,
        "schema_version": "4.0.0",
        "t2_utility_scope_authorized": False,
    }
    descriptor_hash = stable_hash(payload)
    if descriptor_hash != EXPECTED_DESCRIPTOR_HASH:
        raise IndependentAuditError("AUDIT_DESCRIPTOR_HASH")
    return {**payload, "descriptor_hash": descriptor_hash}


def reconstruct_rule_documents(
    common: Mapping[str, Any], descriptor_hash: str
) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    for relation in common["relations"]:
        bindings = [
            {"numeric_role": role, "reference_identity": reference_identity(relation, role)}
            for role in ROLES
        ]
        payload = {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_rule_descriptor",
            "numeric_authority_descriptor_hash": descriptor_hash,
            "numeric_reference_bindings": bindings,
            "relation_binding_hash": relation["relation_binding_hash"],
            "relation_identity": relation["relation_identity"],
            "schema_version": "4.0.0",
            "selected_horizon_seconds": relation["selected_horizon_seconds"],
            "semantic_execution_hash": relation["semantic_execution_hash"],
            "source": relation["source"],
            "source_direction": relation["source_direction"],
            "target": relation["target"],
            "target_direction": relation["target_direction"],
        }
        result.append({**payload, "descriptor_hash": stable_hash(payload)})
    if len(result) != 42 or len({item["descriptor_hash"] for item in result}) != 42:
        raise IndependentAuditError("AUDIT_RULE_DESCRIPTOR_SET")
    return tuple(result)


def reconstruct_feature_oracle(repo_root: Path, common: Mapping[str, Any]) -> dict[str, Any]:
    report = load_json(repo_root, "feature_report")
    verify_self_hash(report, EXPECTED_FEATURE_REPORT_HASH)
    c0 = load_json(repo_root, "c0")
    source_rows = c0.get("common_universe", {}).get("source_identities")
    if type(source_rows) is not list:
        raise IndependentAuditError("AUDIT_SOURCE_METADATA")
    sources = tuple(sorted(row["variable_name"] for row in source_rows))
    targets = tuple(common["targets"])
    union = tuple(sorted(set(sources) | set(targets)))
    report_rows = report.get("features")
    if type(report_rows) is not list:
        raise IndependentAuditError("AUDIT_FEATURE_REPORT_ROWS")
    report_by_name = {row["feature_name"]: row for row in report_rows}
    if tuple(sorted(report_by_name)) != union:
        raise IndependentAuditError("AUDIT_FEATURE_REPORT_SET")
    for source_row in source_rows:
        item = report_by_name[source_row["variable_name"]]
        if item["role"] != "source" or item["metadata_authority_hash"] != source_row["metadata_record_hash"]:
            raise IndependentAuditError("AUDIT_SOURCE_FEATURE_BINDING")
    executable = load_json(repo_root, "executable")
    target_metadata = {
        row["variable_name"]: row
        for row in c0["common_universe"]["target_identities"]
    }
    for target in targets:
        item = report_by_name[target]
        if item["role"] != "target" or item["metadata_authority_hash"] != target_metadata[target]["metadata_record_hash"]:
            raise IndependentAuditError("AUDIT_TARGET_FEATURE_BINDING")
    entries = []
    for name in union:
        row = report_by_name[name]
        entries.append(
            {
                "expected_logical_type": "finite_real_scalar",
                "expected_raw_representation": "strict_decimal_numeric_token",
                "feature_name": name,
                "finite_value_policy": "FINITE_REQUIRED_FAIL_CLOSED",
                "metadata_authority_hash": row["metadata_authority_hash"],
                "missing_value_policy": "PROHIBITED_NO_AUTHORIZED_MISSING_TOKEN",
                "role": row["role"],
                "unit_identity": None,
            }
        )
    runtime_payload = {
        "artifact_type": "p1_utility_feature_schema_v3",
        "feature_entries": entries,
        "label_field": {
            "feature_name": "label",
            "expected_raw_representation": "exact token 0 or 1",
            "expected_logical_type": "strict_binary_integer",
            "encoding": {"normal": 0, "attack": 1},
            "metadata_authority_hash": "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2",
            "separate_from_feature_parser": True,
        },
        "metadata_authorities": {
            "dataset_manifest": "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2",
            "csv_structure_report": "d4f43034e9402806a4f34da943a1e39191503f8f54465d6d1f98b9cdc31bb7c9",
            "candidate_universe_config": "d703d7ec0b87694b53cd4d2b3768ca32efca00cd3bdc3ce12933fc6c8c36d34f",
            "br2_continuous_step_config": "c101a4cd988b926d160b527d20afe9cdd2590093f9aeb820897dea77dd15783b",
            "executable_equivalence": EXECUTABLE_EQUIVALENCE_HASH,
            "utility_view": "4445c98c0a22e4f53a5679b39b52a984adf342eb02fe893d5d53256ea2133e24",
            "feature_order": "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57",
            "source_identity": "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234",
        },
        "missing_or_ambiguous_feature_type_count": 0,
        "required_source_count": 12,
        "required_target_count": 10,
        "schema_version": "3.0.0",
        "timestamp_field": {
            "feature_name": "timestamp",
            "expected_raw_representation": "ISO-8601-compatible source timestamp",
            "expected_logical_type": "timestamp",
            "timezone": "source_unspecified",
            "metadata_authority_hash": "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2",
        },
        "type_authority_basis": "COMMITTED_CONTINUOUS_STEP_NUMERIC_SEMANTICS_AND_VARIABLE_METADATA_BINDINGS",
    }
    runtime_hash = stable_hash(runtime_payload)
    if runtime_hash != EXPECTED_RUNTIME_SCHEMA_HASH:
        raise IndependentAuditError("AUDIT_RUNTIME_FEATURE_HASH")
    if (len(sources), len(targets), len(union)) != (12, 10, 22):
        raise IndependentAuditError("AUDIT_EVALUATOR_FEATURE_COUNTS")
    if (len(common["sources"]), len(common["targets"]), len(set(common["sources"]) | set(common["targets"]))) != (9, 10, 19):
        raise IndependentAuditError("AUDIT_COMMON_FEATURE_COUNTS")
    return {
        "sources": sources,
        "targets": targets,
        "union": union,
        "common_sources": common["sources"],
        "common_targets": common["targets"],
        "common_union": tuple(sorted(set(common["sources"]) | set(common["targets"]))),
        "report_hash": EXPECTED_FEATURE_REPORT_HASH,
        "runtime_hash": runtime_hash,
        "runtime_payload": runtime_payload,
    }


def reconstruct_regression_hashes(repo_root: Path) -> tuple[str, str, str]:
    documents = (
        load_json(repo_root, "regression_numeric"),
        load_json(repo_root, "event_policy"),
        load_json(repo_root, "metric_policy"),
    )
    for document, expected in zip(documents, CORRECTED_REGRESSION_HASHES, strict=True):
        verify_self_hash(document, expected)
    return CORRECTED_REGRESSION_HASHES


def load_subject(repo_root: Path) -> tuple[v4.UtilityProtocolV4CanonicalAuthority, dict[str, Any]]:
    documents = {key: load_json(repo_root, key) for key in ("executable", "evidence", "dataset", "csv", "c0", "br2", "audit_receipt")}
    authority = v4.build_utility_protocol_v4_canonical_authority(
        executable_equivalence=documents["executable"],
        evidence_manifest=documents["evidence"],
        dataset_manifest=documents["dataset"],
        csv_structure_report=documents["csv"],
        c0_config=documents["c0"],
        br2_config=documents["br2"],
        materialized_audit_receipt=documents["audit_receipt"],
    )
    return authority, documents


@dataclass
class AttackResult:
    category: str
    cases: int = 0
    rejected: int = 0
    accepted: int = 0
    accepted_case_ids: tuple[str, ...] = ()


class AttackCollector:
    def __init__(self, category: str) -> None:
        self.category = category
        self.cases = 0
        self.rejected = 0
        self.accepted_ids: list[str] = []

    def expect_reject(self, case_id: str, operation: Callable[[], object]) -> None:
        self.cases += 1
        try:
            operation()
        except Exception:
            self.rejected += 1
        else:
            self.accepted_ids.append(case_id)

    def result(self) -> AttackResult:
        return AttackResult(
            self.category,
            self.cases,
            self.rejected,
            len(self.accepted_ids),
            tuple(self.accepted_ids),
        )


def bypass_mutation(value: object, **changes: object) -> object:
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


def opportunity_payload(value: v4.CanonicalOpportunityV4) -> dict[str, Any]:
    return {
        "canonical_row_time_identity": value.canonical_row_time_identity,
        "dataset_manifest_identity": value.dataset_manifest_identity,
        "event_policy_hash": value.event_policy_hash,
        "numeric_authority_descriptor_hash": value.numeric_authority_descriptor_hash,
        "opportunity_enumeration_policy_hash": value.opportunity_enumeration_policy_hash,
        "physical_row_index": value.physical_row_index,
        "relation_binding_hash": value.relation_binding_hash,
        "relation_identity": value.relation_identity,
        "rule_descriptor_hash": value.rule_descriptor_hash,
        "selected_horizon_seconds": value.selected_horizon_seconds,
        "semantic_execution_hash": value.semantic_execution_hash,
        "source": value.source,
        "source_direction": value.source_direction,
        "source_file_identity": value.source_file_identity,
        "split_identity": value.split_identity,
        "target": value.target,
        "target_direction": value.target_direction,
        "timestamp_identity": value.timestamp_identity,
    }


def self_rehash_opportunity(value: v4.CanonicalOpportunityV4) -> v4.CanonicalOpportunityV4:
    object.__setattr__(value, "opportunity_id", stable_hash(opportunity_payload(value)))
    return value


TERMINAL_HASH_FIELDS = (
    "opportunity_id",
    "rule_descriptor_hash",
    "source_qualification_identity",
    "target_window_input_identity",
    "target_noise_reference_identity",
    "numeric_authority_descriptor_hash",
    "transition_policy_hash",
    "physical_row_count",
    "within_split",
    "target_context_available",
    "response_matched",
    "target_evaluation_state",
    "decision_row_time_identity",
    "alarm_emitted",
    "abstention_reason",
)


def self_rehash_terminal(value: v4.TargetEvaluationStateV4) -> v4.TargetEvaluationStateV4:
    object.__setattr__(
        value,
        "terminal_state_provenance_hash",
        stable_hash({name: getattr(value, name) for name in TERMINAL_HASH_FIELDS}),
    )
    return value


def self_rehash_source(value: v4.SourceQualificationStateV4) -> v4.SourceQualificationStateV4:
    payload = {
        "opportunity_id": value.opportunity_id,
        "rule_descriptor_hash": value.rule_descriptor_hash,
        "source_window_identity": value.source_window_identity,
        "retained_source_event_identity": value.retained_source_event_identity,
        "retained_source_event_census_hash": value.retained_source_event_census_hash,
        "source_step_reference_identity": value.source_step_reference_identity,
        "source_stability_reference_identity": value.source_stability_reference_identity,
        "event_policy_hash": value.event_policy_hash,
        "state": value.state,
    }
    object.__setattr__(value, "source_qualification_identity", stable_hash(payload))
    return value


def run_attacks(repo_root: Path) -> dict[str, AttackResult]:
    common_oracle = reconstruct_common(repo_root)
    descriptor_oracle = reconstruct_numeric_descriptor(common_oracle)
    rule_oracle = reconstruct_rule_documents(common_oracle, descriptor_oracle["descriptor_hash"])
    feature_oracle = reconstruct_feature_oracle(repo_root, common_oracle)
    reconstruct_regression_hashes(repo_root)
    authority, documents = load_subject(repo_root)
    if authority.authority_hash != EXPECTED_V4_AUTHORITY_HASH:
        raise IndependentAuditError("AUDIT_V4_AUTHORITY_HASH")
    if authority.numeric_authority.to_dict() != descriptor_oracle:
        raise IndependentAuditError("AUDIT_NUMERIC_DESCRIPTOR_REPLAY")
    if tuple(item.to_dict() for item in authority.rule_descriptors) != rule_oracle:
        raise IndependentAuditError("AUDIT_RULE_DESCRIPTOR_REPLAY")
    if authority.feature_schema.canonical_runtime_schema_hash != feature_oracle["runtime_hash"]:
        raise IndependentAuditError("AUDIT_FEATURE_RUNTIME_REPLAY")

    results: dict[str, AttackResult] = {}

    t2 = AttackCollector("t2")
    for name, portfolio in (
        ("t2", "T2"),
        ("t2_39", "T2-39"),
        ("fake_historical", "historical_T2_subset"),
        ("caller_39_common", "COMMON-39"),
    ):
        t2.expect_reject(name, lambda portfolio=portfolio: v4.authorize_canonical_full_census_plan_v4(authority, portfolio_identity=portfolio))
    results["t2"] = t2.result()

    numeric = AttackCollector("numeric")
    numeric_changes = (
        ("registry", {"private_registry_content_hash": "f" * 64}),
        ("historical_registry", {"private_registry_content_hash": HISTORICAL_REGISTRY_HASH}),
        ("historical_e1", {"private_registry_content_hash": HISTORICAL_E1_HASH}),
        ("audit_receipt", {"materialized_authority_audit_receipt_hash": "f" * 64}),
        ("authority_version", {"authority_version": "TASK039E3_HISTORICAL"}),
        ("authority_definition", {"authority_definition_hash": "f" * 64}),
        ("calibration", {"calibration_policy_hash": "f" * 64}),
        ("common", {"common42_authority_hash": "f" * 64}),
        ("normal_input", {"normal_input_identity_set_hash": "f" * 64}),
        ("reference_set", {"new_reference_set_hash": "f" * 64}),
        ("direct_number_hash", {"private_registry_content_hash": stable_hash({"direct_numbers": True})}),
        ("t2_grant", {"t2_utility_scope_authorized": True}),
    )
    for name, changes in numeric_changes:
        def operation(changes: Mapping[str, Any] = changes) -> object:
            candidate = replace(authority.numeric_authority, **changes)
            return v4.validate_numeric_authority_descriptor_v4(candidate, v4.build_common42_public_authority_v4(documents["executable"], documents["evidence"]), documents["audit_receipt"])
        numeric.expect_reject(name, operation)
    numeric.expect_reject("direct_number_mapping", lambda: v4.validate_numeric_authority_descriptor_v4({"numeric_value": 1.0}, None, documents["audit_receipt"]))
    results["numeric"] = numeric.result()

    references = AttackCollector("references")
    rule = authority.rule_descriptors[0]
    bindings = rule.numeric_reference_bindings
    candidates: tuple[tuple[str, object], ...] = (
        ("missing", bindings[:-1]),
        ("extra", (*bindings, bindings[-1])),
        ("reordered", tuple(reversed(bindings))),
        ("role_swap", (("target_noise_scale", bindings[0][1]), *bindings[1:])),
        ("historical", ((bindings[0][0], common_oracle["relations"][0]["historical_reference_by_role"][bindings[0][0]]), *bindings[1:])),
        ("direct_number", ((bindings[0][0], "DIRECT_NUMBER:1"), *bindings[1:])),
        ("unknown_reference", ((bindings[0][0], f"{AUTHORITY_VERSION}:{'f' * 64}"), *bindings[1:])),
    )
    for name, changed in candidates:
        references.expect_reject(
            name,
            lambda changed=changed: v4.validate_canonical_rule_descriptor_v4(
                replace(rule, numeric_reference_bindings=changed), authority
            ),
        )
    results["references"] = references.result()

    rules = AttackCollector("rules")
    rule_changes = (
        ("relation_identity", {"relation_identity": "directional_relation:foreign"}),
        ("binding", {"relation_binding_hash": "f" * 64}),
        ("semantic", {"semantic_execution_hash": "f" * 64}),
        ("source", {"source": "P1_FCV02Z"}),
        ("target", {"target": "P1_TIT03"}),
        ("source_direction", {"source_direction": "step_down" if rule.source_direction == "step_up" else "step_up"}),
        ("target_direction", {"target_direction": "decrease" if rule.target_direction == "increase" else "increase"}),
        ("horizon", {"selected_horizon_seconds": 60 if rule.selected_horizon_seconds != 60 else 30}),
        ("numeric_descriptor", {"numeric_authority_descriptor_hash": "f" * 64}),
    )
    for name, changes in rule_changes:
        rules.expect_reject(name, lambda changes=changes: v4.validate_canonical_rule_descriptor_v4(replace(rule, **changes), authority))
    results["rules"] = rules.result()

    row = v4.build_canonical_row_time_identity_v4(source_file_identity="hai-test1.csv", physical_row_index=100, timestamp_identity="a" * 64)
    opportunity = v4.build_canonical_opportunity_v4(authority, relation_binding_hash=rule.relation_binding_hash, row_time=row)
    opportunity_attacks = AttackCollector("opportunity")
    opportunity_changes = (
        ("dataset", {"dataset_manifest_identity": "f" * 64}),
        ("split", {"split_identity": v4.OUTER_SPLIT_ID}),
        ("source_file", {"source_file_identity": "hai-test2.csv"}),
        ("relation_binding", {"relation_binding_hash": "f" * 64}),
        ("semantic", {"semantic_execution_hash": "f" * 64}),
        ("source", {"source": "P1_FCV02Z"}),
        ("target", {"target": "P1_TIT03"}),
        ("source_direction", {"source_direction": "step_down" if opportunity.source_direction == "step_up" else "step_up"}),
        ("target_direction", {"target_direction": "decrease" if opportunity.target_direction == "increase" else "increase"}),
        ("horizon", {"selected_horizon_seconds": 60 if opportunity.selected_horizon_seconds != 60 else 30}),
        ("row_identity", {"canonical_row_time_identity": "f" * 64}),
        ("rule_descriptor", {"rule_descriptor_hash": "f" * 64}),
        ("numeric_descriptor", {"numeric_authority_descriptor_hash": "f" * 64}),
        ("event_policy", {"event_policy_hash": "f" * 64}),
        ("enumeration_policy", {"opportunity_enumeration_policy_hash": "f" * 64}),
        ("physical_row_type", {"physical_row_index": 100.0}),
    )
    for name, changes in opportunity_changes:
        def operation(changes: Mapping[str, Any] = changes) -> object:
            changed = self_rehash_opportunity(bypass_mutation(opportunity, **changes))
            return v4.validate_canonical_opportunity_v4(changed, authority)
        opportunity_attacks.expect_reject(name, operation)
    def coherent_time_mutation() -> object:
        changed = bypass_mutation(opportunity, timestamp_identity="f" * 64)
        row_payload = {
            "dataset_manifest_identity": changed.dataset_manifest_identity,
            "physical_row_index": changed.physical_row_index,
            "source_file_identity": changed.source_file_identity,
            "split_identity": changed.split_identity,
            "timestamp_identity": changed.timestamp_identity,
        }
        object.__setattr__(changed, "canonical_row_time_identity", stable_hash(row_payload))
        self_rehash_opportunity(changed)
        return v4.validate_canonical_opportunity_v4(changed, authority)
    opportunity_attacks.expect_reject("self_consistent_time_identity_substitution", coherent_time_mutation)
    results["opportunity"] = opportunity_attacks.result()

    census = AttackCollector("census")
    for name, kwargs in (
        ("sample_n", {"sample_n": 10}),
        ("max_opportunities", {"max_opportunities": 10}),
        ("denominator", {"caller_denominator": 10}),
        ("opportunity_records", {"opportunity_records": ()}),
        ("relation_subset", {"relation_subset": authority.rule_descriptors[:39]}),
        ("numeric_descriptor", {"numeric_descriptor": "caller"}),
        ("caller_rule_library", {"rule_library": authority.rule_descriptors[:39]}),
    ):
        census.expect_reject(name, lambda kwargs=kwargs: v4.authorize_canonical_full_census_plan_v4(authority, **kwargs))
    census.expect_reject(
        "fabricated_plan",
        lambda: v4.validate_canonical_full_census_plan_v4(
            replace(authority.full_census_plan, event_policy_hash="f" * 64), authority
        ),
    )
    # The public opportunity-set validator is a second census-like boundary.
    # It must not grant an identity to caller-selected empty, partial, or
    # one-row relation sets that were never derived from the canonical plan
    # and frame.
    one_row_opportunities = tuple(
        sorted(
            (
                v4.build_canonical_opportunity_v4(
                    authority,
                    relation_binding_hash=item.relation_binding_hash,
                    row_time=row,
                )
                for item in authority.rule_descriptors
            ),
            key=lambda item: (item.relation_binding_hash, item.canonical_row_time_identity),
        )
    )
    census.expect_reject(
        "caller_empty_opportunity_set",
        lambda: v4.validate_canonical_opportunity_set_v4((), authority),
    )
    census.expect_reject(
        "caller_singleton_opportunity_set",
        lambda: v4.validate_canonical_opportunity_set_v4(one_row_opportunities[:1], authority),
    )
    census.expect_reject(
        "caller_39_relation_opportunity_set",
        lambda: v4.validate_canonical_opportunity_set_v4(one_row_opportunities[:39], authority),
    )
    census.expect_reject(
        "caller_42_relation_one_row_set",
        lambda: v4.validate_canonical_opportunity_set_v4(one_row_opportunities, authority),
    )
    results["census"] = census.result()

    feature = AttackCollector("feature")
    schema = authority.feature_schema
    feature_changes = (
        ("missing_source", {"source_features": schema.source_features[:-1]}),
        ("extra_source", {"source_features": (*schema.source_features, "P1_UNKNOWN")}),
        ("missing_target", {"target_features": schema.target_features[:-1]}),
        ("extra_target", {"target_features": (*schema.target_features, "P1_TIT03")}),
        ("metadata_hash", {"metadata_authorities": (*schema.metadata_authorities[:-1], (schema.metadata_authorities[-1][0], "f" * 64))}),
        ("runtime_hash", {"canonical_runtime_schema_hash": "f" * 64}),
        ("report_hash", {"canonical_v3_schema_report_hash": "f" * 64}),
        ("reduce_12_to_9", {"source_features": schema.common_source_footprint}),
        ("expand_19_to_22", {"common_source_footprint": schema.source_features, "common_feature_footprint": schema.union_features}),
        ("union_substitution", {"union_features": (*schema.union_features[:-1], "P1_UNKNOWN")}),
    )
    for name, changes in feature_changes:
        def operation(changes: Mapping[str, Any] = changes) -> object:
            candidate = replace(schema, **changes)
            common_subject = v4.build_common42_public_authority_v4(documents["executable"], documents["evidence"])
            return v4.validate_canonical_feature_schema_v4(
                candidate,
                dataset_manifest=documents["dataset"],
                csv_structure_report=documents["csv"],
                c0_config=documents["c0"],
                br2_config=documents["br2"],
                executable_equivalence=documents["executable"],
                common_authority=common_subject,
            )
        feature.expect_reject(name, operation)
    changed_c0 = deepcopy(documents["c0"])
    changed_c0["common_universe"]["source_identities"][0]["semantic_role"] = "process_sensor"
    feature.expect_reject(
        "source_role_lower_metadata",
        lambda: v4.build_canonical_feature_schema_v4(
            dataset_manifest=documents["dataset"], csv_structure_report=documents["csv"],
            c0_config=changed_c0, br2_config=documents["br2"], executable_equivalence=documents["executable"],
            common_authority=v4.build_common42_public_authority_v4(documents["executable"], documents["evidence"]),
        ),
    )
    results["feature"] = feature.result()

    scalar = AttackCollector("scalar")
    scalar_base = dict(integer_value=1, boolean_value=True, float_value=1.0, string_value="identity", tuple_value=(1,))
    scalar_cases = (
        ("bool_as_int", {"integer_value": True}),
        ("float_as_int", {"integer_value": 1.0}),
        ("string_as_int", {"integer_value": "1"}),
        ("int_as_bool", {"boolean_value": 1}),
        ("float_as_bool", {"boolean_value": 1.0}),
        ("string_as_bool", {"boolean_value": "true"}),
        ("int_as_float", {"float_value": 1}),
        ("bool_as_float", {"float_value": True}),
        ("string_as_float", {"float_value": "1"}),
        ("nan", {"float_value": float("nan")}),
        ("positive_inf", {"float_value": float("inf")}),
        ("negative_inf", {"float_value": float("-inf")}),
        ("list_as_tuple", {"tuple_value": [1]}),
        ("generator_as_tuple", {"tuple_value": (value for value in (1,))}),
        ("string_as_tuple", {"tuple_value": "1"}),
    )
    for name, changes in scalar_cases:
        scalar.expect_reject(name, lambda changes=changes: v4.validate_strict_scalar_policy_v4(**{**scalar_base, **changes}))
    # Exact nested container typing is part of the scalar policy.  These
    # mutations bypass dataclass construction and then exercise the top-level
    # authoritative consumer.  JSON serialization normalizes list/tuple, so a
    # self-hash check alone is not an exact-type oracle.
    schema_container_changes = (
        ("schema_source_features_list", {"source_features": list(schema.source_features)}),
        ("schema_target_features_list", {"target_features": list(schema.target_features)}),
        ("schema_union_features_list", {"union_features": list(schema.union_features)}),
        ("schema_common_source_list", {"common_source_footprint": list(schema.common_source_footprint)}),
        ("schema_common_target_list", {"common_target_footprint": list(schema.common_target_footprint)}),
        ("schema_common_union_list", {"common_feature_footprint": list(schema.common_feature_footprint)}),
        ("schema_metadata_outer_list", {"metadata_authorities": list(schema.metadata_authorities)}),
        (
            "schema_metadata_inner_lists",
            {"metadata_authorities": tuple([key, value] for key, value in schema.metadata_authorities)},
        ),
    )
    for name, changes in schema_container_changes:
        def top_level_container_replay(changes: Mapping[str, Any] = changes) -> object:
            changed_schema = bypass_mutation(schema, **changes)
            changed_authority = bypass_mutation(authority, feature_schema=changed_schema)
            return v4.validate_utility_protocol_v4_authority(changed_authority)
        scalar.expect_reject(name, top_level_container_replay)
    results["scalar"] = scalar.result()

    source_state = v4.build_source_qualification_state_v4(
        opportunity,
        authority,
        source_window_identity="b" * 64,
        retained_source_event_identity="c" * 64,
        retained_source_event_census_hash="d" * 64,
    )
    terminal_state = v4.transition_target_evaluation_v4(
        opportunity,
        source_state,
        authority,
        target_window_input_identity="e" * 64,
        within_split=True,
        target_context_available=True,
        response_matched=True,
    )
    terminal = AttackCollector("terminal")
    terminal.expect_reject("direct_terminal_constructor", lambda: v4.TargetEvaluationStateV4())
    terminal.expect_reject("direct_source_constructor", lambda: v4.SourceQualificationStateV4())
    terminal_changes = (
        ("wrong_opportunity_parent", {"opportunity_id": "f" * 64}),
        ("wrong_rule_parent", {"rule_descriptor_hash": "f" * 64}),
        ("wrong_numeric_authority", {"numeric_authority_descriptor_hash": "f" * 64}),
        ("wrong_source_parent", {"source_qualification_identity": "f" * 64}),
        ("wrong_transition_hash", {"transition_policy_hash": "f" * 64}),
        ("wrong_terminal_hash", {"terminal_state_provenance_hash": "f" * 64}),
        ("physical_row_float", {"physical_row_count": 54000.0}),
        ("alarm_int", {"alarm_emitted": 0}),
    )
    for name, changes in terminal_changes:
        terminal.expect_reject(
            name,
            lambda changes=changes: v4.validate_target_evaluation_state_v4(
                bypass_mutation(terminal_state, **changes), opportunity, source_state, authority
            ),
        )
    def self_consistent_target_window_substitution() -> object:
        changed = self_rehash_terminal(bypass_mutation(terminal_state, target_window_input_identity="f" * 64))
        return v4.validate_target_evaluation_state_v4(changed, opportunity, source_state, authority)
    terminal.expect_reject("self_consistent_target_window_substitution", self_consistent_target_window_substitution)
    def self_consistent_interior_split() -> object:
        changed = bypass_mutation(
            terminal_state,
            within_split=False,
            target_evaluation_state="abstain",
            decision_row_time_identity=None,
            alarm_emitted=False,
            abstention_reason="split_boundary",
        )
        self_rehash_terminal(changed)
        return v4.validate_target_evaluation_state_v4(changed, opportunity, source_state, authority)
    terminal.expect_reject("self_consistent_interior_split_boundary", self_consistent_interior_split)
    def self_consistent_source_window_substitution() -> object:
        changed_source = self_rehash_source(bypass_mutation(source_state, source_window_identity="f" * 64))
        changed_terminal = bypass_mutation(terminal_state, source_qualification_identity=changed_source.source_qualification_identity)
        self_rehash_terminal(changed_terminal)
        return v4.validate_target_evaluation_state_v4(changed_terminal, opportunity, changed_source, authority)
    terminal.expect_reject("self_consistent_source_window_substitution", self_consistent_source_window_substitution)
    terminal.expect_reject(
        "caller_response_outcome_switch",
        lambda: v4.validate_target_evaluation_state_v4(
            v4.transition_target_evaluation_v4(
                opportunity, source_state, authority, target_window_input_identity="e" * 64,
                within_split=True, target_context_available=True, response_matched=False,
            ),
            opportunity, source_state, authority,
        ),
    )
    results["terminal"] = terminal.result()

    regression = AttackCollector("regression")
    for index in range(3):
        changed = list(CORRECTED_REGRESSION_HASHES)
        changed[index] = "f" * 64
        regression.expect_reject(f"generic_{index}", lambda changed=tuple(changed): v4.validate_regression_authorities_v4(*changed))
        historical = list(CORRECTED_REGRESSION_HASHES)
        historical[index] = HISTORICAL_WRONG_REGRESSION_HASHES[index]
        regression.expect_reject(f"historical_{index}", lambda historical=tuple(historical): v4.validate_regression_authorities_v4(*historical))
    results["regression"] = regression.result()
    return results


def audit_summary(repo_root: Path) -> dict[str, Any]:
    common = reconstruct_common(repo_root)
    descriptor = reconstruct_numeric_descriptor(common)
    feature = reconstruct_feature_oracle(repo_root, common)
    regression = reconstruct_regression_hashes(repo_root)
    attacks = run_attacks(repo_root)
    total = sum(item.cases for item in attacks.values())
    rejected = sum(item.rejected for item in attacks.values())
    accepted = sum(item.accepted for item in attacks.values())
    return {
        "common": {
            "relations": len(common["relations"]),
            "references": len(common["references"]),
            "sources": len(common["sources"]),
            "targets": len(common["targets"]),
        },
        "numeric_descriptor_hash": descriptor["descriptor_hash"],
        "reference_set_hash": common["reference_set_hash"],
        "feature": {
            "evaluator_sources": len(feature["sources"]),
            "evaluator_targets": len(feature["targets"]),
            "evaluator_union": len(feature["union"]),
            "common_sources": len(feature["common_sources"]),
            "common_targets": len(feature["common_targets"]),
            "common_union": len(feature["common_union"]),
            "report_hash": feature["report_hash"],
            "runtime_hash": feature["runtime_hash"],
        },
        "regression_hashes": list(regression),
        "attacks": {
            name: {
                "cases": item.cases,
                "rejected": item.rejected,
                "accepted": item.accepted,
                "accepted_case_ids": list(item.accepted_case_ids),
            }
            for name, item in attacks.items()
        },
        "totals": {"cases": total, "rejected": rejected, "accepted": accepted},
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    summary = audit_summary(root)
    print(json.dumps(summary, sort_keys=True, indent=2))
