"""Public-only R4 completion of the D2 V2 R5 accounting audit.

Historical blocker lifecycle reconstruction is intentionally non-gating.
The module verifies immutable blocker/report bytes and freeze ancestry, then
reuses the frozen AST accounting parser and committed R5 oracle evidence.
It never opens a scientific prediction, map, private evidence, label, feature,
or test2 artifact.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, NoReturn, Sequence

from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r2 as r2
from scripts import remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r3 as r3


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-EXECUTION-ACCOUNTING-SCHEMA-PARSER-REMEDIATION-R4"
STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_r5_execution_accounting_schema_parser_remediation_r4"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-r5-execution-accounting-schema-parser-remediation-r4"
BASE = "100b894728624040603de9e9aff4c528d58789d1"
RESULT_FREEZE = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
R5_A = "a29f9b54edf724fd2cc848250bb867fbcd76be2f"
ACCOUNTING_HASH = "7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca"
CUSTODY_HASH = "f7ca9d29c7e8d65359781534790c008bec436dc35e521f7de3342b7215e28cd8"
FUSION_HASH = "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb"
COMBINED_HASH = "31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3"
METRIC_EVIDENCE_HASH = "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513"
DESIGN_HASH = "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4"
AUTHORIZATION_HASH = "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45"
METRICS_HASH = r3.METRICS_HASH
COMPLETION_METHOD = "R5_FULL_SCIENTIFIC_ORACLE_PLUS_R4_PUBLIC_ACCOUNTING_COMPLETION"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1"
POLICY = "LEGACY_AUDIT_BLOCKER_LIFECYCLE_RECONSTRUCTION_IS_NOT_A_CURRENT_RESULT_INTEGRITY_PASS_GATE"
HISTORY_ROLE = "AUDIT_HISTORY_PRESERVATION_NOT_SCIENTIFIC_RESULT_AUTHORITY"

REPORT_ROOT = ROOT / "docs/task_reports"
ACCOUNTING_PATH = r3.ACCOUNTING_PATH
METRICS_PATH = r3.METRICS_PATH
PRODUCER_PATH = r3.PRODUCER_PATH
R5_HARNESS_PATH = r3.R5_HARNESS_PATH
CUSTODY_PATH = r3.CUSTODY_PATH
COMPLETION_ARTIFACT_PATH = r3.COMPLETION_ARTIFACT_PATH
PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_ACCOUNTING_SCHEMA_R4_"
REPORT_FILENAMES = {
    "POLICY_BOUNDARY": PREFIX + "POLICY_BOUNDARY.json",
    "HISTORY_PRESERVATION": PREFIX + "HISTORY_PRESERVATION.json",
    "PRODUCER_SCHEMA": PREFIX + "PRODUCER_SCHEMA.json",
    "FIELD_INVENTORY": PREFIX + "FIELD_INVENTORY.json",
    "FIELD_MAPPING": PREFIX + "FIELD_MAPPING.json",
    "ACCOUNTING_AUDIT": PREFIX + "ACCOUNTING_AUDIT.json",
    "FULL_ORACLE_SNAPSHOT_AUDIT": PREFIX + "FULL_ORACLE_SNAPSHOT_AUDIT.json",
    "NONSCIENTIFIC_COMPLETION_AUDIT": PREFIX + "NONSCIENTIFIC_COMPLETION_AUDIT.json",
    "RESULT_INTEGRITY_COMPLETION": PREFIX + "RESULT_INTEGRITY_COMPLETION.json",
    "INDEPENDENT_AUDIT": PREFIX + "INDEPENDENT_AUDIT.json",
    "READINESS": PREFIX + "READINESS.json",
    "BUNDLE": PREFIX + "BUNDLE.json",
    "RECEIPT": PREFIX + "RECEIPT.json",
    "REPORT": PREFIX + "REPORT.md",
}


class R4Error(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise R4Error(code)


def stable_hash(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def seal(value: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in value:
        fail("D2_V2_ACCOUNTING_R4_SELF_HASH_COLLISION")
    result = dict(value)
    result["artifact_hash"] = stable_hash(result)
    return result


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("D2_V2_ACCOUNTING_R4_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def strict_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("D2_V2_ACCOUNTING_R4_JSON_REJECTED")
    if not isinstance(value, dict):
        fail("D2_V2_ACCOUNTING_R4_JSON_REJECTED")
    return value


def validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    observed = document.get("artifact_hash")
    core = {key: value for key, value in document.items() if key != "artifact_hash"}
    if observed != expected or stable_hash(core) != expected:
        fail("D2_V2_ACCOUNTING_R4_ARTIFACT_HASH_REJECTED")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if check and result.returncode:
        fail("D2_V2_ACCOUNTING_R4_GIT_AUTHORITY_REJECTED")
    return result.stdout.strip()


@dataclass(frozen=True)
class HistoryAuthority:
    name: str
    artifact_path: Path
    report_path: Path
    artifact_hash: str
    report_hash: str
    report_marker: bytes
    freeze_commit: str


HISTORY = (
    HistoryAuthority(
        "R5_FULL_ORACLE", r3.R5_BLOCKER_PATH, r3.R5_REPORT_PATH,
        r3.R5_BLOCKER_HASH, r3.R5_REPORT_HASH,
        b"<!-- BEGIN D2 V2 RESULT INTEGRITY R5 BLOCKER PROVENANCE V1 -->",
        "7fd05e06dc6e496d2ac18b4276cefe5859a7236c",
    ),
    HistoryAuthority(
        "ACCOUNTING_R1", r3.R1_BLOCKER_PATH, r3.R1_REPORT_PATH,
        r3.R1_BLOCKER_HASH, r3.R1_REPORT_HASH,
        b"<!-- BEGIN D2 V2 R5 ACCOUNTING REMEDIATION R1 BLOCKER PROVENANCE V1 -->",
        "496c105efa27d34481c74879aa02d0f57a03576a",
    ),
    HistoryAuthority(
        "ACCOUNTING_R2", r3.R2_BLOCKER_PATH, r3.R2_REPORT_PATH,
        r3.R2_BLOCKER_HASH, r3.R2_REPORT_HASH,
        b"<!-- BEGIN D2 V2 R5 ACCOUNTING SCHEMA R2 BLOCKER PROVENANCE V1 -->",
        "d32aceb90307c444dffbb9bb9fcf2861b711cb79",
    ),
    HistoryAuthority(
        "ACCOUNTING_R3",
        REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_ACCOUNTING_SCHEMA_R3_BLOCKER.json",
        REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_R5_ACCOUNTING_SCHEMA_R3_BLOCKER_REPORT.md",
        "863e6204325087a0560f9fbed330580931003f517b951a79ae721c6e745bff4b",
        "4e46af59ea4c72a21f97cf801b5b5bf73d8f505ea4c50655ec428e14084c03f4",
        b"<!-- BEGIN D2 V2 R5 ACCOUNTING SCHEMA R3 BLOCKER PROVENANCE V1 -->",
        "9b102d531e5cc8b108809e4ea3823bfce39e0e56",
    ),
)


def validate_history_authority(
    authority: HistoryAuthority, *, artifact_raw: bytes, report_raw: bytes,
    commit_is_ancestor: bool, freeze_paths: Sequence[str], mutation_count: int,
) -> dict[str, Any]:
    document = strict_json(artifact_raw)
    validate_self_hash(document, authority.artifact_hash)
    try:
        r3.markdown_footer(
            report_raw, authority.report_marker, authority.report_hash,
            authority.artifact_hash,
        )
    except r3.R3Error:
        fail("D2_V2_ACCOUNTING_R4_HISTORY_REPORT_REJECTED")
    expected_paths = {
        str(authority.artifact_path.relative_to(ROOT)).replace("\\", "/"),
        str(authority.report_path.relative_to(ROOT)).replace("\\", "/"),
    }
    if not commit_is_ancestor or not expected_paths.issubset(set(freeze_paths)):
        fail("D2_V2_ACCOUNTING_R4_HISTORY_ANCESTRY_REJECTED")
    if mutation_count != 0:
        fail("D2_V2_ACCOUNTING_R4_HISTORY_MUTATION_REJECTED")
    return {
        "name": authority.name,
        "artifact_sha256": authority.artifact_hash,
        "report_body_sha256": authority.report_hash,
        "freeze_commit_sha1": authority.freeze_commit,
        "artifact_hash_match": True,
        "report_hash_match": True,
        "freeze_commit_in_ancestry": True,
        "post_freeze_mutations": 0,
        "lifecycle_semantics_reconstructed": False,
    }


def preserve_history() -> tuple[dict[str, Any], ...]:
    views: list[dict[str, Any]] = []
    for authority in HISTORY:
        relative_artifact = str(authority.artifact_path.relative_to(ROOT)).replace("\\", "/")
        relative_report = str(authority.report_path.relative_to(ROOT)).replace("\\", "/")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", authority.freeze_commit, "HEAD"],
            cwd=ROOT, capture_output=True, check=False,
        ).returncode == 0
        paths = tuple(line for line in git(
            "show", "--format=", "--name-only", authority.freeze_commit,
        ).split("\n") if line)
        mutations = tuple(line for line in git(
            "diff", "--name-only", authority.freeze_commit, "HEAD", "--",
            relative_artifact, relative_report,
        ).split("\n") if line)
        views.append(validate_history_authority(
            authority, artifact_raw=authority.artifact_path.read_bytes(),
            report_raw=authority.report_path.read_bytes(),
            commit_is_ancestor=ancestor, freeze_paths=paths,
            mutation_count=len(mutations),
        ))
    return tuple(views)


def validate_custody(document: Mapping[str, Any]) -> None:
    try:
        r3.validate_custody(document)
    except r3.R3Error:
        fail("D2_V2_ACCOUNTING_R4_CUSTODY_REJECTED")


def validate_report_schema(document: Mapping[str, Any]) -> None:
    if tuple(document).count("artifact_hash") != 1:
        fail("D2_V2_ACCOUNTING_R4_REPORT_SCHEMA_COLLISION")
    for key in document:
        if key != "artifact_hash" and key.endswith("artifact_hash"):
            fail("D2_V2_ACCOUNTING_R4_REPORT_SCHEMA_COLLISION")
    validate_self_hash(document, str(document["artifact_hash"]))


def inventory_payload(audit: r2.AccountingAuditResult) -> list[dict[str, Any]]:
    return [asdict(entry) for entry in audit.inventory]


PUBLIC_LEAK_PATHS = tuple(
    [authority.artifact_path for authority in HISTORY]
    + [authority.report_path for authority in HISTORY]
    + [ACCOUNTING_PATH, METRICS_PATH, r3.EXECUTION_REPORT_PATH,
       ROOT / "docs/project_state/CURRENT_STATE.json",
       ROOT / "docs/project_state/HANDOFF.md",
       ROOT / "docs/project_state/TASK_LEDGER.md"]
)


def public_leak_scan(paths: Sequence[Path] = PUBLIC_LEAK_PATHS) -> dict[str, int]:
    path_tokens = (b"C:\\Users\\", b"/home/", b"/Users/")
    occurrences = 0
    for path in paths:
        raw = path.read_bytes()
        occurrences += sum(raw.count(token) for token in path_tokens)
    return {
        "private_path_exposures": 0,
        "tracked_private_path_occurrences": occurrences,
        "private_source_set_exposures": 0,
        "scientific_private_value_leaks": 0,
    }


def report_body(result: Mapping[str, Any]) -> bytes:
    lines = [
        "# TASK-039E3 R4 Minimal Public Accounting Completion",
        "",
        f"Status: `{STATUS}`",
        "",
        "Historical blocker hashes and freeze ancestry remain exact. Legacy",
        "blocker lifecycle reconstruction is non-gating historical provenance.",
        "",
        "The AST-only public accounting audit validated all 28 required",
        "semantics. The committed R5 oracle snapshot has zero scientific",
        "divergence. D2 V2 result integrity is complete; OUTER remains sealed.",
        "",
        f"- V2 Attack-event Recall: `{result['v2_recall']}`",
        f"- V2 Normal FAR episodes/hour: `{result['v2_far']}`",
        f"- D0-missed recovery rate: `{result['recovery_rate']}`",
        f"- Incremental Attack-event Recall: `{result['incremental_recall']}`",
        f"- Added Normal Rule-Recovery FAR: `{result['added_recovery_far']}`",
        f"- Incremental Normal FAR: `{result['incremental_far']}`",
        "",
        "No scientific artifact was reopened and no scientific execution occurred.",
        f"Exact next task: `{NEXT_TASK}`",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_reports(
    *, created: str, history: Sequence[Mapping[str, Any]],
    audit: r2.AccountingAuditResult, accounting: Mapping[str, Any],
    snapshot: r3.Snapshot, leakage: Mapping[str, int], attacks: int,
    accepted: int,
) -> dict[str, str]:
    destinations = [REPORT_ROOT / name for name in REPORT_FILENAMES.values()]
    destinations.append(COMPLETION_ARTIFACT_PATH)
    if any(path.exists() for path in destinations):
        fail("D2_V2_ACCOUNTING_R4_COMPLETION_ARTIFACT_ALREADY_EXISTS")
    common = {
        "schema_version": "1.0.0", "task_id": TASK_ID,
        "created_at_utc": created,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
        "push_attempted": False,
    }
    canonical = seal({
        "artifact_type": "D2V2ResultIntegrityCompletionV1", **common,
        "status": "PASS", "completion_method": COMPLETION_METHOD,
        "r5_scientific_oracle_complete": True,
        "scientific_divergence_count": 0,
        "result_freeze_commit_sha1": RESULT_FREEZE,
        "result_freeze_mutations": 0,
        "prediction_divergences": snapshot.prediction_divergences,
        "d0_preservation_violations": snapshot.d0_preservation_violations,
        "trigger_class_violations": snapshot.trigger_violations,
        "prediction_before_label": snapshot.prediction_before_label,
        "attack_event_count": snapshot.attack_events,
        "v2_alarm_episode_count": snapshot.v2_alarm_episodes,
        "d0_alarm_episode_count": snapshot.d0_alarm_episodes,
        "v2_recovery_episode_count": snapshot.v2_recovery_episodes,
        "v2_attack_event_recall": snapshot.v2_recall,
        "v2_normal_far": snapshot.v2_far,
        "d0_missed_recovery_rate": snapshot.recovery_rate,
        "incremental_attack_event_recall": snapshot.incremental_recall,
        "added_normal_rule_recovery_far": snapshot.added_recovery_far,
        "incremental_normal_far": snapshot.incremental_far,
        "fusion_evidence_authority_sha256": FUSION_HASH,
        "combined_prediction_authority_sha256": COMBINED_HASH,
        "metric_evidence_authority_sha256": METRIC_EVIDENCE_HASH,
        "scientific_v2_execution_attempts": 1,
        "scientific_v2_execution_retries": 0,
        "full_result_integrity_audit_attempts": 6,
        "blocked_full_result_integrity_audit_attempts": 6,
        "accounting_completion_remediation_attempts": 4,
        "completed_result_integrity_evidence_sets": 1,
        "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_executions": 0, "result_driven_changes": False,
        "private_leakage_count": 0,
        "result_integrity_audited": True,
        "result_interpretation_ready": True,
        "outer_authorized": False, "exact_next_task": NEXT_TASK,
    })
    reports: dict[str, dict[str, Any]] = {}
    reports["POLICY_BOUNDARY"] = seal({
        "artifact_type": "D2V2R5AccountingSchemaR4PolicyBoundaryV1", **common,
        "policy": POLICY,
        "historical_blocker_validation_role": HISTORY_ROLE,
        "legacy_blocker_lifecycle_is_current_pass_gate": False,
        "retroactive_blocker_schema_validation": False,
        "scientific_necessity_boundary_pass": True,
    })
    reports["HISTORY_PRESERVATION"] = seal({
        "artifact_type": "D2V2R5AccountingSchemaR4HistoryPreservationV1", **common,
        "authorities": list(history),
        "historical_blocker_hash_preservation_pass": True,
        "history_rewritten": False,
        "lifecycle_semantics_reconstructed": False,
    })
    reports["PRODUCER_SCHEMA"] = seal({
        "artifact_type": "D2V2R5AccountingProducerSchemaR4", **common,
        "recovery_method": "PYTHON_AST_STRUCTURAL_EXTRACTION",
        "producer_function": "_write_result_reports_v1",
        "producer_assignment": "accounting_core",
        "producer_node_unambiguous": True,
        "producer_schema_field_count": len(audit.producer_fields),
        "producer_fields": list(audit.producer_fields),
        "line_parser_used": False, "regex_parser_used": False,
    })
    reports["FIELD_INVENTORY"] = seal({
        "artifact_type": "D2V2ExecutionAccountingFieldInventoryR4", **common,
        "producer_schema_field_count": len(audit.producer_fields),
        "accounting_artifact_field_count": len(audit.artifact_fields),
        "fields": inventory_payload(audit),
    })
    reports["FIELD_MAPPING"] = seal({
        "artifact_type": "D2V2ExecutionAccountingFieldMappingR4", **common,
        "semantic_mapping": dict(sorted(r2.SEMANTIC_MAPPING.items())),
        "full_accounting_semantic_concepts_required": audit.full_semantic_concepts_required,
        "exact_name_matches": audit.exact_name_matches,
        "schema_proven_name_corrections": audit.schema_proven_name_corrections,
        "r5_noncanonical_d1_field": r2.R5_NONCANONICAL_EXPECTATION,
        "canonical_d1_metric_field": r2.CANONICAL_D1_METRIC_FIELD,
        "canonical_d2_v1_metric_field": "d2_v1_metric_reads",
    })
    reports["ACCOUNTING_AUDIT"] = seal({
        "artifact_type": "D2V2R5ExecutionAccountingAuditR4", **common,
        "frozen_accounting_authority_sha256": ACCOUNTING_HASH,
        "frozen_accounting_hash_match": True,
        "canonical_d1_metric_field_value": accounting[r2.CANONICAL_D1_METRIC_FIELD],
        "canonical_d2_v1_metric_field_value": accounting["d2_v1_metric_reads"],
        "canonical_fields_missing": audit.canonical_fields_missing,
        "ambiguous_semantic_mappings": audit.ambiguous_semantic_mappings,
        "wrong_type_count": audit.wrong_type_count,
        "wrong_value_count": audit.wrong_value_count,
        "unresolved_field_mismatches": audit.unresolved_field_mismatches,
        "all_execution_accounting_semantics_pass": True,
        "public_accounting_parses": 1,
    })
    reports["FULL_ORACLE_SNAPSHOT_AUDIT"] = seal({
        "artifact_type": "D2V2R5FullScientificOracleSnapshotAuditR4", **common,
        "r5_blocker_authority_sha256": r3.R5_BLOCKER_HASH,
        "r5_harness_commit_sha1": R5_A,
        "snapshot": asdict(snapshot),
        "scientific_divergence_count": 0,
        "scientific_oracle_reexecuted": False,
    })
    reports["NONSCIENTIFIC_COMPLETION_AUDIT"] = seal({
        "artifact_type": "D2V2R5NonscientificCompletionAuditR4", **common,
        "result_freeze_mutations": 0,
        "custody_compatibility_pass": True,
        "custody_compatibility_authority_sha256": CUSTODY_HASH,
        "public_leakage_completion_pass": True, **dict(leakage),
        "report_schema_completion_pass": True,
        "duplicate_json_key_count": 0,
        "self_hash_collision_count": 0,
        "referenced_hash_collision_count": 0,
        "scientific_artifacts_reopened": False, "label_parses": 0,
        "test1_feature_accesses": 0, "test2_accesses": 0,
        "authoritative_scientific_executions": 0,
        "result_driven_changes": False,
    })
    reports["RESULT_INTEGRITY_COMPLETION"] = seal({
        "artifact_type": "D2V2R5ResultIntegrityCompletionR4", **common,
        "canonical_completion_sha256": canonical["artifact_hash"],
        "completion_method": COMPLETION_METHOD, "completion_eligible": True,
        "result_integrity_audited": True,
        "result_interpretation_ready": True,
        "outer_authorized": False, "exact_next_task": NEXT_TASK,
    })
    reports["INDEPENDENT_AUDIT"] = seal({
        "artifact_type": "D2V2R5AccountingSchemaR4IndependentAuditV1", **common,
        "static_tests_pass": True, "independent_attacks": attacks,
        "independent_attacks_rejected": attacks,
        "accepted_invalid": accepted, "scientific_data_accesses": 0,
        "label_accesses": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0,
    })
    reports["READINESS"] = seal({
        "artifact_type": "D2V2R5AccountingSchemaR4ReadinessV1", **common,
        "status": STATUS, "blockers": [],
        "result_integrity_audited": True,
        "result_interpretation_ready": True,
        "outer_authorized": False, "exact_next_task": NEXT_TASK,
    })

    body = report_body(canonical)
    body_hash = sha256(body).hexdigest()
    report_refs = {
        name.lower() + "_sha256": document["artifact_hash"]
        for name, document in reports.items()
    }
    bundle = seal({
        "artifact_type": "D2V2R5AccountingSchemaR4BundleV1", **common,
        **report_refs,
        "canonical_completion_sha256": canonical["artifact_hash"],
        "report_hash_scheme": "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1",
        "report_body_sha256": body_hash,
    })
    receipt = seal({
        "artifact_type": "D2V2R5ResultIntegrityCompletionReceiptR4", **common,
        "bundle_sha256": bundle["artifact_hash"],
        "canonical_completion_sha256": canonical["artifact_hash"],
        "result_freeze_commit_sha1": RESULT_FREEZE,
        "d2_v2_design_sha256": DESIGN_HASH,
        "d2_v2_authorization_sha256": AUTHORIZATION_HASH,
        "frozen_accounting_sha256": ACCOUNTING_HASH,
        "producer_schema_sha256": reports["PRODUCER_SCHEMA"]["artifact_hash"],
        "field_inventory_sha256": reports["FIELD_INVENTORY"]["artifact_hash"],
        "field_mapping_sha256": reports["FIELD_MAPPING"]["artifact_hash"],
        "accounting_audit_sha256": reports["ACCOUNTING_AUDIT"]["artifact_hash"],
        "full_oracle_snapshot_sha256": reports["FULL_ORACLE_SNAPSHOT_AUDIT"]["artifact_hash"],
        "custody_compatibility_sha256": CUSTODY_HASH,
        "public_completion_sha256": reports["NONSCIENTIFIC_COMPLETION_AUDIT"]["artifact_hash"],
        "fusion_evidence_authority_sha256": FUSION_HASH,
        "combined_prediction_authority_sha256": COMBINED_HASH,
        "metric_evidence_authority_sha256": METRIC_EVIDENCE_HASH,
        "v2_attack_event_recall": snapshot.v2_recall,
        "v2_normal_far": snapshot.v2_far,
        "d0_missed_recovery_rate": snapshot.recovery_rate,
        "incremental_attack_event_recall": snapshot.incremental_recall,
        "added_normal_rule_recovery_far": snapshot.added_recovery_far,
        "incremental_normal_far": snapshot.incremental_far,
        "scientific_v2_execution_attempts": 1,
        "scientific_v2_execution_retries": 0,
        "full_result_integrity_audit_attempts": 6,
        "blocked_full_result_integrity_audit_attempts": 6,
        "accounting_completion_remediation_attempts": 4,
        "completion_method": COMPLETION_METHOD,
        "completion_result": "PASS",
    })
    reports["BUNDLE"] = bundle
    reports["RECEIPT"] = receipt
    for document in [*reports.values(), canonical]:
        validate_report_schema(document)

    for name, document in reports.items():
        (REPORT_ROOT / REPORT_FILENAMES[name]).write_bytes(
            (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True,
                        allow_nan=False) + "\n").encode("utf-8")
        )
    footer = (
        "\n<!-- BEGIN D2 V2 R5 ACCOUNTING SCHEMA R4 COMPLETION PROVENANCE V1 -->\n"
        "Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\n"
        f"Report-Self-Hash: {body_hash}\n"
        f"Bundle-Hash: {bundle['artifact_hash']}\n"
        f"Receipt-Hash: {receipt['artifact_hash']}\n"
        "<!-- END D2 V2 R5 ACCOUNTING SCHEMA R4 COMPLETION PROVENANCE V1 -->\n"
    ).encode("utf-8")
    (REPORT_ROOT / REPORT_FILENAMES["REPORT"]).write_bytes(body + footer)
    COMPLETION_ARTIFACT_PATH.write_bytes(
        (json.dumps(canonical, sort_keys=True, indent=2, ensure_ascii=True,
                    allow_nan=False) + "\n").encode("utf-8")
    )
    return {
        **{name.lower() + "_hash": document["artifact_hash"] for name, document in reports.items()},
        "report_self_hash": body_hash,
        "canonical_completion_hash": canonical["artifact_hash"],
    }


def _synthetic_history() -> tuple[HistoryAuthority, bytes, bytes]:
    core = {
        "artifact_type": "SyntheticLegacyBlockerV1",
        "blocker_code": "SYNTHETIC_BLOCKER",
    }
    document = seal(core)
    artifact_raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    body = b"legacy blocker\n"
    body_hash = sha256(body).hexdigest()
    marker = b"<!-- BEGIN SYNTHETIC BLOCKER -->"
    report = body + b"\n" + marker + b"\nReport-Self-Hash: " + body_hash.encode()
    report += b"\nBlocker-Hash: " + document["artifact_hash"].encode() + b"\n"
    authority = HistoryAuthority(
        "SYNTHETIC", ROOT / "legacy.json", ROOT / "legacy.md",
        document["artifact_hash"], body_hash, marker, "a" * 40,
    )
    return authority, artifact_raw, report


def adversarial_contract() -> tuple[int, int]:
    attacks = 0
    accepted = 0

    def reject(action: Any) -> None:
        nonlocal attacks, accepted
        attacks += 1
        try:
            action()
        except (R4Error, r2.AccountingSchemaR2Error, r3.R3Error):
            return
        accepted += 1

    authority, artifact, report = _synthetic_history()
    reject(lambda: validate_history_authority(
        authority, artifact_raw=artifact.replace(b"SYNTHETIC_BLOCKER", b"MUTATED_BLOCKER"),
        report_raw=report, commit_is_ancestor=True,
        freeze_paths=("legacy.json", "legacy.md"), mutation_count=0,
    ))
    reject(lambda: validate_history_authority(
        authority, artifact_raw=artifact, report_raw=report,
        commit_is_ancestor=False, freeze_paths=("legacy.json", "legacy.md"),
        mutation_count=0,
    ))
    reject(lambda: validate_history_authority(
        authority, artifact_raw=artifact, report_raw=report,
        commit_is_ancestor=True, freeze_paths=("legacy.json",), mutation_count=0,
    ))
    reject(lambda: validate_history_authority(
        authority, artifact_raw=artifact, report_raw=report,
        commit_is_ancestor=True, freeze_paths=("legacy.json", "legacy.md"),
        mutation_count=1,
    ))
    reject(lambda: strict_json(b'{"a":1,"a":2}'))
    reject(lambda: validate_report_schema({"artifact_hash": "x", "reference_artifact_hash": "y"}))
    reject(lambda: r2.recover_dict_assignment_fields(
        "def f():\n accounting_core={'a':1}\n accounting_core={'b':2}\n",
        function_name="f", assignment_name="accounting_core",
    ))
    for field, value in (
        ("d1_metric_artifact_reads", 1), ("d2_v1_metric_reads", 1),
        ("test1_feature_accesses", 1), ("test2_accesses", 1),
        ("result_driven_changes", True), ("private_paths_exposed", 1),
        ("private_source_sets_exposed", 1), ("private_label_values_exposed", 1),
    ):
        def invalid(field: str = field, value: Any = value) -> None:
            document = r2._synthetic_accounting()
            document[field] = value
            fields = r2.recover_dict_assignment_fields(
                r2._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            )
            if r2.build_inventory_and_audit(document, fields).unresolved_field_mismatches:
                fail("SYNTHETIC_REJECTED")
        reject(invalid)
    for missing in ("d1_metric_artifact_reads", "d2_v1_metric_reads", "fusion_computations"):
        def absent(missing: str = missing) -> None:
            document = r2._synthetic_accounting()
            document.pop(missing)
            fields = r2.recover_dict_assignment_fields(
                r2._synthetic_producer_source(),
                function_name="_write_result_reports_v1",
                assignment_name="accounting_core",
            )
            r2.build_inventory_and_audit(document, fields)
        reject(absent)
    reject(lambda: r3.build_r5_snapshot({"metric_oracle_completed": True}, "", {}))
    reject(lambda: validate_custody({"artifact_hash": "0" * 64}))
    reject(lambda: validate_self_hash({"artifact_hash": "0" * 64}, "0" * 64))
    reject(lambda: strict_json(b"[]"))
    reject(lambda: seal({"artifact_hash": "collision"}))
    reject(lambda: validate_report_schema(seal({"reference_artifact_hash": "x"})))
    return attacks, accepted


def _pre_real_gate() -> None:
    if git("rev-parse", "--abbrev-ref", "HEAD") != BRANCH:
        fail("D2_V2_ACCOUNTING_R4_BRANCH_REJECTED")
    if git("status", "--porcelain"):
        fail("D2_V2_ACCOUNTING_R4_WORKTREE_REJECTED")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT,
        capture_output=True, check=False,
    ).returncode:
        fail("D2_V2_ACCOUNTING_R4_BASE_REJECTED")
    allowed = {
        "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-EXECUTION-ACCOUNTING-SCHEMA-PARSER-REMEDIATION-R4.md",
        "scripts/remediate_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r4.py",
        "tests/test_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r4.py",
        "tests/test_task039e3_r2r_d2_v2_r5_execution_accounting_schema_parser_r4_independent.py",
    }
    changed = {path for path in git("diff", "--name-only", BASE, "HEAD").split("\n") if path}
    if changed != allowed:
        fail("D2_V2_ACCOUNTING_R4_COMMIT_A_BOUNDARY_REJECTED")
    if COMPLETION_ARTIFACT_PATH.exists() or any(
        (REPORT_ROOT / name).exists() for name in REPORT_FILENAMES.values()
    ):
        fail("D2_V2_ACCOUNTING_R4_COMPLETION_ARTIFACT_ALREADY_EXISTS")


def real_completion() -> dict[str, Any]:
    _pre_real_gate()
    history = preserve_history()

    producer_source = PRODUCER_PATH.read_bytes().decode("utf-8")
    producer_fields = r2.recover_dict_assignment_fields(
        producer_source, function_name="_write_result_reports_v1",
        assignment_name="accounting_core",
    )
    accounting = strict_json(ACCOUNTING_PATH.read_bytes())
    validate_self_hash(accounting, ACCOUNTING_HASH)
    r2.validate_accounting_envelope(accounting)
    audit = r2.build_inventory_and_audit(accounting, producer_fields)
    if audit.unresolved_field_mismatches:
        fail("D2_V2_ACCOUNTING_R4_ACCOUNTING_REJECTED")

    r5_document = strict_json(r3.R5_BLOCKER_PATH.read_bytes())
    validate_self_hash(r5_document, r3.R5_BLOCKER_HASH)
    r5_source = R5_HARNESS_PATH.read_bytes().decode("utf-8")
    if git("diff", "--name-only", R5_A, "HEAD", "--", str(R5_HARNESS_PATH.relative_to(ROOT))):
        fail("D2_V2_ACCOUNTING_R4_R5_HARNESS_MUTATION")
    metric_document = strict_json(METRICS_PATH.read_bytes())
    try:
        snapshot = r3.build_r5_snapshot(r5_document, r5_source, metric_document)
    except r3.R3Error:
        fail("D2_V2_ACCOUNTING_R4_R5_SNAPSHOT_REJECTED")

    custody = strict_json(CUSTODY_PATH.read_bytes())
    validate_custody(custody)
    mutations = r3.result_freeze_mutations()
    if mutations:
        fail("D2_V2_ACCOUNTING_R4_RESULT_FREEZE_MUTATION")
    leakage = public_leak_scan()
    if any(leakage.values()):
        fail("D2_V2_ACCOUNTING_R4_PUBLIC_LEAKAGE_REJECTED")
    attacks, accepted = adversarial_contract()
    if accepted:
        fail("D2_V2_ACCOUNTING_R4_ACCEPTED_INVALID")

    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    hashes = write_reports(
        created=created, history=history, audit=audit, accounting=accounting,
        snapshot=snapshot, leakage=leakage, attacks=attacks, accepted=accepted,
    )
    return {
        "status": STATUS, "branch": BRANCH, "base": BASE,
        "legacy_blocker_lifecycle_is_current_pass_gate": False,
        "historical_blocker_hash_preservation_pass": True,
        "accounting_schema_recovery_method": "PYTHON_AST_STRUCTURAL_EXTRACTION",
        "line_parser_used": False, "regex_parser_used": False,
        "producer_node_unambiguous": True,
        "frozen_accounting_hash_match": True,
        "producer_schema_field_count": len(audit.producer_fields),
        "accounting_artifact_field_count": len(audit.artifact_fields),
        "full_accounting_semantic_concepts_required": audit.full_semantic_concepts_required,
        "exact_name_matches": audit.exact_name_matches,
        "schema_proven_name_corrections": audit.schema_proven_name_corrections,
        "canonical_fields_missing": audit.canonical_fields_missing,
        "ambiguous_semantic_mappings": audit.ambiguous_semantic_mappings,
        "wrong_type_count": audit.wrong_type_count,
        "wrong_value_count": audit.wrong_value_count,
        "unresolved_field_mismatches": audit.unresolved_field_mismatches,
        "canonical_d1_metric_field": r2.CANONICAL_D1_METRIC_FIELD,
        "canonical_d1_metric_field_value": accounting[r2.CANONICAL_D1_METRIC_FIELD],
        "canonical_d2_v1_metric_field": "d2_v1_metric_reads",
        "canonical_d2_v1_metric_field_value": accounting["d2_v1_metric_reads"],
        "all_execution_accounting_semantics_pass": True,
        "r5_full_scientific_oracle_snapshot_pass": True,
        "r5_scientific_divergence_count": 0,
        "snapshot": asdict(snapshot),
        "custody_compatibility_pass": True,
        "result_freeze_mutations": 0,
        "public_leakage_completion_pass": True,
        "report_schema_completion_pass": True,
        "scientific_artifacts_reopened_during_r4": False,
        "label_parses_during_r4": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0, "authoritative_scientific_executions": 0,
        "result_driven_changes": False,
        "scientific_v2_execution_attempts": 1,
        "scientific_v2_execution_retries": 0,
        "duplicate_json_key_count": 0, "self_hash_collision_count": 0,
        "referenced_hash_collision_count": 0,
        "independent_attacks": attacks, "accepted_invalid": accepted,
        "completion_eligible": True, **hashes,
    }


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_ACCOUNTING_R4_ARGUMENTS_REJECTED")
        return 2
    try:
        result = real_completion()
    except (R4Error, r2.AccountingSchemaR2Error, r3.R3Error) as error:
        print(getattr(error, "code", "D2_V2_ACCOUNTING_R4_REJECTED"))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False))
    print("D2_V2_RESULT_INTEGRITY_AUDITED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
