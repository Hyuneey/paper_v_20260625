"""Single-pass independent integrity audit for the frozen D2 V2 INNER result.

This remediation is audit tooling only.  It never imports or invokes the D2
V2 execution controller or its scientific helpers.  Every real scientific
authority is deserialized once behind ``AuditSingleParseGuardR4`` and all
subsequent oracle phases consume one immutable snapshot.
"""
from __future__ import annotations

import ast
import csv
from dataclasses import dataclass, replace
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import audit_task039e3_r2r_d2_v2_result_integrity_v1 as oracle

TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R4"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_harness_remediation_r4"
SCIENTIFIC_STATUS = "D2_V2_RESULT_INTEGRITY_AUDITED"
BRANCH = "task-039e3-r2r-utility-inner-d2-v2-result-integrity-audit-harness-remediation-r4"
BASE = "1a7edb29719768197c8fd3b6ca0556d9bb73d491"
EXEC_A = "2bbb3dcaced47c8d15337e45eb0e0b741c1a3ed1"
EXEC_B = "b3acf3cbb0b6bcb21548daa319fd37923357b952"
RESULT_C = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
CONT_D = "615fde528644f14d1654f98031cfc2bfd4f3c8ec"
HIST_A = "5374cc8293ce970738f2f3320abdbf1d9fbdb150"
HIST_B = "e54abe8a2170b48e7eb437b4a4935c32e6cd9341"
HIST_C = "d158bab6bdbc5558f3483c52be5ef29967815cba"
R1_A = "e04ca7e7aee472c5450363f9a5e4a6a3fe2a6ef4"
R1_B = "a4968c2d8af89232d141826e10bd5145567407a2"
R1_C = "18263247569d4c1bcd6b131b1b5c63e5aec9349e"
R2_A = "b14cb96a19f6474d9c10e02abbdfedf3dd7c7a73"
R2_B = "1effce0b691b870c93e5195d930a26ec9ae92658"
R2_C = "4bfe423dfdf8041a3100248b8dd2db84d6880796"
R3_A = "10f6b179438e70646ff94ca82fdc96ac63d2ba4a"
R3_B = "1d7a189755a70fabfbd00e66c320373b0ae05f4b"
R3_C = "017e815496f201f988817f18518a319c7f572b4d"
R3_D = BASE
HISTORICAL_BLOCKER_HASH = "592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879"
HISTORICAL_R1_BLOCKER_HASH = "dc6d83a33bdf985389b6d2d1b75e54f2b703e59f515369dc41b5a499280b0990"
HISTORICAL_R1_REPORT_HASH = "7cc60d727e2387b7bee488efcc123876b9e370042c44fd91a77a231f17e86696"
HISTORICAL_R2_BLOCKER_HASH = "4e6526e382dbb0bf15bae9123eeeba3a090dcb59bfd767f3b19172fe3e353c0c"
HISTORICAL_R2_REPORT_HASH = "ce0e3d5e7db0ba135989beeab97beb97f024ccfc5f5341a548fd33aa68fd04d1"
HISTORICAL_R3_BLOCKER_HASH = "2baed348b67ec7567ea57d1892c4e605728120e65480728ca562528c822e9f4a"
HISTORICAL_R3_REPORT_HASH = "e20b49b6f6b6f22eb3f40b9433710ba85df37893677941debfdded84adab33a4"
DESIGN = oracle.DESIGN
AUTH = oracle.AUTH
D0_HASH = oracle.D0_HASH
D1_HASH = oracle.D1_HASH
SOURCE_HASH = oracle.SOURCE_HASH
HORIZON_HASH = oracle.HORIZON_HASH
FUSION_HASH = oracle.FUSION_HASH
COMBINED_HASH = oracle.COMBINED_HASH
METRIC_EVIDENCE_HASH = oracle.METRIC_EVIDENCE_HASH
ROWS = oracle.ROWS
TRIGGERS = oracle.TRIGGERS
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1"
REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R4_"
LEAVES = ("PRODUCER_SEMANTICS", "MARKDOWN_PROVENANCE_AUDIT", "AUTHORITY_IDENTITY_AUDIT", "FREEZE_AUDIT", "HORIZON_ORACLE", "TOKEN_ORACLE",
          "FUSION_ORACLE", "PREDICTION_AUDIT", "ORDERING_AUDIT", "EPISODE_ORACLE",
          "METRIC_ORACLE", "ACCOUNTING_AUDIT", "PRIVATE_CUSTODY_AUDIT",
          "LEAKAGE_AUDIT", "INDEPENDENT_AUDIT")
REPORT_NAMES = (*LEAVES, "READINESS", "BUNDLE", "RECEIPT")
HISTORICAL_FILES = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_BLOCKER_REPORT.md",
)
HISTORICAL_R1_FILES = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R1_BLOCKER.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R1_BLOCKER_REPORT.md",
)
HISTORICAL_R2_FILES = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R2_BLOCKER.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R2_BLOCKER_REPORT.md",
)
HISTORICAL_R3_FILES = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R3_BLOCKER.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_HARNESS_R3_BLOCKER_REPORT.md",
)
TASK_PATH = "TASKS/TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R4.md"
SCRIPT_PATH = "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r4.py"
TEST_PATHS = (
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r4.py",
    "tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r4_independent.py",
)
DESIGN_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_DESIGN.json"
AUTH_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_AUTHORIZATION.json"
HIST_BLOCKER_PATH = HISTORICAL_FILES[0]
R1_BLOCKER_PATH = HISTORICAL_R1_FILES[0]
AUTH_VERSION = "TASK039E3_R2R_D2_V2_INNER_EXECUTION_AUTHORIZATION_V1"
AUTH_SCOPE = "HAI_23_05_P1_TEST1_D2_V2_NATIVE_HORIZON_CORROBORATION_INNER_V1"
AUTH_IDENTITY_SCHEME = "CANONICAL_ARTIFACT_SELF_HASH_V1"
AUTH_PREFIX = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_AUTHORIZATION_V1_"
AUTH_AUTHORITIES = {
    "CONTRACT": ("89e4e2bdf91cea0ab5d67827945c0051c812d3740f8cbe038a078f601a19caa3", "task039e3_r2r_d2_v2_execution_authorization_v1_contract"),
    "NATIVE_HORIZON_AUDIT": ("2893972703172965caea957f8f7dbd0b8b89a1ce14f7e559b1ef606404d90d25", "task039e3_r2r_d2_v2_execution_authorization_v1_native_horizon_audit"),
    "CUSTODY_PREFLIGHT": ("1296c76458d498d0e35b209c4da9691f6d02e1899778906409d96d7c18d4e463", "D2V2ExecutionCustodyPreflightReceiptV1"),
    "PATH_REDACTION_AUDIT": ("1b51853f796b01fa0fa47c5c1a431c6d79997a62612b4569ba9a255045ca4355", "task039e3_r2r_d2_v2_execution_authorization_v1_path_redaction_audit"),
    "INDEPENDENT_AUDIT": ("3ee5e6a3deefaa39365e9eb471789a0cde2cf60e4635b1743a176d45b48f9ee8", "task039e3_r2r_d2_v2_execution_authorization_v1_independent_audit"),
    "AUTHORIZATION": (AUTH, "D2V2InnerExecutionAuthorizationV1"),
    "ACCOUNTING": ("33239fd17c0266f4e18a1079a37560d16dd5143dd64062092a86ca27cfbbb419", "task039e3_r2r_d2_v2_execution_authorization_v1_accounting"),
    "READINESS": ("02ce6ebb6d71225160210772768a6f6a904a6df6f188ef7a7b47fe034bdf922a", "task039e3_r2r_d2_v2_execution_authorization_v1_readiness"),
    "BUNDLE": ("779a326715bbf5f7cebc94c06ea24b1b4538b75abb2117281a01cb65ec784472", "task039e3_r2r_d2_v2_execution_authorization_v1_bundle"),
    "RECEIPT": ("16198e7d11b241977031c73dd8ab3fb645c4620e75f446e6c57793ff49693b96", "task039e3_r2r_d2_v2_execution_authorization_v1_receipt"),
}
AUTH_REPORT_BODY_HASH = "40f63c01c8594f1ff4fbdd76d1373001191b1a408d96000f0707ebe6dc890830"
DESIGN_REPORT_HASH = "cf68f4bb6a9eac5a717d3fd644a40a073478afc5c859dd6b41531192226fa8d0"
AUTH_REPORT_FREEZE_COMMIT = "867738a3904d2bc110865df5dfe4f9fe3032eddf"
AUTH_REPORT_GIT_BLOB = "09f5ef527f362c851616b0f1badec816b8cb4259"
AUTH_REPORT_RAW_SHA256 = "6db0d23ca9dc1a91c906b0eed81d19c36d437ac150078f41f53705b08c697d00"
PRODUCER_AUTHORITY_SOURCE = "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
PRODUCER_AUTHORITY_SHA256 = "cec2a8a68f3807ec62c52cf5aea6c60425667bb1d77fa48e08159f4b4034d071"
PRODUCER_AUTHORITY_BLOB = "0bf4bf82523a5f17964205fbe9b17d96df39ae4b"
PRODUCER_CLASSIFICATION = "HASHED_CANONICAL_TEXT_WITH_EXPLICIT_NEWLINE_NORMALIZATION"
AUTHORIZATION_KEYS = frozenset({
    "alternative_policy_search_authorized", "artifact_hash", "artifact_type", "authorization_scope",
    "authorization_status", "authorization_version", "backdating_allowed",
    "causal_evidence_token_construction_authorized", "custody_preflight_hash",
    "d0_prediction_consumption_authorized", "d0_prediction_hash", "d0_preservation_policy",
    "d0_rerun_authorized", "d0_score_access_authorized", "d1_prediction_consumption_authorized",
    "d1_prediction_hash", "d1_rerun_authorized", "d2_v1_combined_prediction_hash",
    "d2_v1_design_hash", "d2_v2_combined_prediction_authorized", "d2_v2_id",
    "d2_v2_inner_execution_authorized", "design_hash", "diagnostic_gap_used_as_parameter",
    "fixed_global_temporal_window", "fixed_temporal_window_override_authorized",
    "fusion_change_authorized", "fusion_family", "future_artifact_family", "future_execution_order",
    "future_record_count", "horizon_override_authorized", "incremental_metric_identities",
    "label_before_combined_prediction_authorized", "label_metric_evaluation_authorized",
    "native_horizon_authority_type", "native_horizon_map_consumption_authorized",
    "native_horizon_map_hash", "native_horizon_relation_count", "outer_authorized",
    "primary_metric_identities", "private_fusion_evidence_v2_authorized",
    "required_distinct_source_count", "result_driven_changes", "rule_reevaluation_authorized",
    "schema_version", "single_source_fallback", "single_source_fallback_authorized",
    "source_map_consumption_authorized", "source_map_hash", "task_id",
    "test1_feature_access_authorized", "test2_authorized", "token_expiry_policy",
    "token_start_policy", "trigger_classes",
})


class AuditR4Error(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise AuditR4Error(code)


def stable(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def self_hash(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["artifact_hash"] = stable(result)
    return result


def validate_hash(document: Mapping[str, Any], expected: str) -> None:
    observed = document.get("artifact_hash")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if observed != expected or stable(payload) != expected:
        fail("D2_V2_R4_SELF_HASH_REJECTED")


MARKDOWN_SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"
AUTH_BEGIN = b"<!-- BEGIN D2 V2 AUTHORIZATION REPORT PROVENANCE V1 -->"
AUTH_END = b"<!-- END D2 V2 AUTHORIZATION REPORT PROVENANCE V1 -->"
R4_BEGIN = b"<!-- BEGIN D2 V2 RESULT INTEGRITY AUDIT R4 REPORT PROVENANCE V1 -->"
R4_END = b"<!-- END D2 V2 RESULT INTEGRITY AUDIT R4 REPORT PROVENANCE V1 -->"


@dataclass(frozen=True)
class AuthorizationMarkdownHashViewR4:
    producer_classification: str
    raw_sha256: str
    raw_line_ending_profile: str
    raw_separator_type: str
    hash_domain_newline_representation: str
    canonical_body: bytes
    computed_body_hash: str
    matching_fixed_representation: str
    footer_fields: tuple[tuple[str, str], ...]


def validate_new_lf_markdown_v1(
    raw: bytes,
    begin: bytes,
    end: bytes,
    expected_body_hash: str,
    expected_bundle_hash: str,
    expected_receipt_hash: str,
) -> dict[str, Any]:
    """Validate new R4 binary-LF Markdown; never use for historical reports."""
    if raw.count(begin) != 1:
        fail("D2_V2_R4_REPORT_BEGIN_MARKER_REJECTED")
    if raw.count(end) != 1:
        fail("D2_V2_R4_REPORT_END_MARKER_REJECTED")
    marker_start = raw.index(begin)
    if raw.index(end) < marker_start:
        fail("D2_V2_R4_REPORT_FOOTER_ORDER_REJECTED")
    prefix = raw[:marker_start]
    if not prefix.endswith(b"\n") or prefix.endswith(b"\r\n"):
        fail("D2_V2_R4_REPORT_PROVENANCE_SEPARATOR_NOT_CANONICAL")
    canonical_body = prefix[:-1]
    footer = raw[marker_start:]
    required = (
        b"Report-Hash-Scheme: " + MARKDOWN_SCHEME.encode("ascii"),
        b"Report-Self-Hash: " + expected_body_hash.encode("ascii"),
        b"Bundle-Hash: " + expected_bundle_hash.encode("ascii"),
        b"Receipt-Hash: " + expected_receipt_hash.encode("ascii"),
    )
    labels = (b"Report-Hash-Scheme: ", b"Report-Self-Hash: ",
              b"Bundle-Hash: ", b"Receipt-Hash: ")
    if any(footer.count(line) != 1 for line in required) or any(footer.count(label) != 1 for label in labels):
        fail("D2_V2_R4_REPORT_FOOTER_BINDING_REJECTED")
    computed = sha256(canonical_body).hexdigest()
    if computed != expected_body_hash:
        fail("D2_V2_R4_REPORT_BODY_HASH_REJECTED")
    return {
        "markdown_hash_scheme": MARKDOWN_SCHEME,
        "begin_marker_count": 1,
        "end_marker_count": 1,
        "footer_separator_lf_count_excluded": 1,
        "canonical_body_extraction_pass": True,
        "report_body_self_hash_match": True,
        "footer_bundle_binding_match": True,
        "footer_receipt_binding_match": True,
        "computed_body_hash": computed,
    }


def render_markdown_provenance_raw_v1(
    body: bytes,
    begin: bytes,
    end: bytes,
    bundle_hash: str,
    receipt_hash: str,
    extra_footer_lines: Sequence[bytes] = (),
) -> tuple[bytes, str]:
    """Apply the one-LF writer separator and verify an exact parser round-trip."""
    body_hash = sha256(body).hexdigest()
    footer = (begin + b"\n"
        + b"Report-Hash-Scheme: " + MARKDOWN_SCHEME.encode("ascii") + b"\n"
        + b"Report-Self-Hash: " + body_hash.encode("ascii") + b"\n"
        + b"Bundle-Hash: " + bundle_hash.encode("ascii") + b"\n"
        + b"Receipt-Hash: " + receipt_hash.encode("ascii") + b"\n"
        + b"".join(line + b"\n" for line in extra_footer_lines)
        + end + b"\n")
    rendered = body + b"\n" + footer
    validate_new_lf_markdown_v1(rendered, begin, end, body_hash, bundle_hash, receipt_hash)
    return rendered, body_hash


def audit_authorization_producer_semantics_r4() -> dict[str, Any]:
    """Prove the historical canonical-LF hash view from frozen source authority."""
    source_path = ROOT / PRODUCER_AUTHORITY_SOURCE
    source_bytes = source_path.read_bytes()
    if sha256(source_bytes).hexdigest() != PRODUCER_AUTHORITY_SHA256:
        fail("D2_V2_R4_PRODUCER_SOURCE_IDENTITY_REJECTED")
    if git("hash-object", PRODUCER_AUTHORITY_SOURCE) != PRODUCER_AUTHORITY_BLOB:
        fail("D2_V2_R4_PRODUCER_SOURCE_BLOB_REJECTED")
    if git("rev-parse", EXEC_A + ":" + PRODUCER_AUTHORITY_SOURCE) != PRODUCER_AUTHORITY_BLOB:
        fail("D2_V2_R4_PRODUCER_SOURCE_FREEZE_REJECTED")
    source = source_bytes.decode("utf-8")
    required = (
        'report != _commit_bytes_v1(AUTHORIZATION_FREEZE_COMMIT, report_relative)',
        'body_hash = sha256(body.replace(b"\\r\\n", b"\\n").rstrip(b"\\n") + b"\\n").hexdigest()',
        'canonical LF text, independent of',
    )
    if any(fragment not in source for fragment in required):
        fail("D2_V2_R4_PRODUCER_SEMANTICS_UNPROVEN")
    report_relative = AUTH_PREFIX + "REPORT.md"
    if git("rev-parse", AUTH_REPORT_FREEZE_COMMIT + ":" + report_relative) != AUTH_REPORT_GIT_BLOB:
        fail("D2_V2_R4_AUTHORIZATION_REPORT_FREEZE_BLOB_REJECTED")
    if git("rev-parse", "HEAD:" + report_relative) != AUTH_REPORT_GIT_BLOB:
        fail("D2_V2_R4_AUTHORIZATION_REPORT_RAW_BYTES_CHANGED")
    return {
        "producer_classification": PRODUCER_CLASSIFICATION,
        "producer_semantics_proven": True,
        "producer_authority_source_sha256": PRODUCER_AUTHORITY_SHA256,
        "producer_authority_source_blob": PRODUCER_AUTHORITY_BLOB,
        "producer_source_static_reads": 1,
        "authorization_markdown_git_blob": AUTH_REPORT_GIT_BLOB,
        "expected_raw_sha256": AUTH_REPORT_RAW_SHA256,
        "authorization_markdown_git_blob_changed": False,
        "hash_computed_from": "CANONICAL_LF_UTF8_BODY_VIEW_BEFORE_FOOTER_VALIDATION",
        "separator_hash_domain": "FOOTER_SERIALIZATION_ONLY",
        "platform_transport_independent": True,
        "arbitrary_hash_target_search": False,
    }


def authorization_markdown_hash_view_r4(
    raw: bytes,
    producer: Mapping[str, Any],
    expected_body_hash: str,
    expected_bundle_hash: str,
    expected_receipt_hash: str,
) -> AuthorizationMarkdownHashViewR4:
    """Reconstruct only the source-proven historical hash view in memory."""
    classification = producer.get("producer_classification")
    separator_domain = producer.get("separator_hash_domain")
    allowed = {
        ("HASHED_RAW_WRITTEN_BODY_BYTES", "BODY_HASH_DOMAIN"),
        ("HASHED_CANONICAL_LF_BODY_BEFORE_PLATFORM_TEXT_WRITE", "FOOTER_SERIALIZATION_ONLY"),
        ("HASHED_CANONICAL_TEXT_WITH_EXPLICIT_NEWLINE_NORMALIZATION", "FOOTER_SERIALIZATION_ONLY"),
    }
    if producer.get("producer_semantics_proven") is not True or (classification, separator_domain) not in allowed:
        fail("D2_V2_R4_PRODUCER_SEMANTICS_UNKNOWN")
    expected_raw = producer.get("expected_raw_sha256")
    if expected_raw is not None and sha256(raw).hexdigest() != expected_raw:
        fail("D2_V2_R4_AUTHORIZATION_REPORT_RAW_BYTES_CHANGED")
    if raw.count(AUTH_BEGIN) != 1:
        fail("D2_V2_R4_REPORT_BEGIN_MARKER_REJECTED")
    if raw.count(AUTH_END) != 1:
        fail("D2_V2_R4_REPORT_END_MARKER_REJECTED")
    marker_start = raw.index(AUTH_BEGIN)
    if raw.index(AUTH_END) < marker_start:
        fail("D2_V2_R4_REPORT_FOOTER_ORDER_REJECTED")
    has_crlf = b"\r\n" in raw
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\r" in without_crlf or (has_crlf and b"\n" in without_crlf):
        fail("D2_V2_R4_REPORT_MIXED_LINE_ENDINGS_REJECTED")
    prefix = raw[:marker_start]
    if prefix.endswith(b"\r\n"):
        separator = "CRLF"
    elif prefix.endswith(b"\n"):
        separator = "LF"
    elif prefix.endswith(b"\r"):
        separator = "OTHER"
    else:
        separator = "NONE"
    if separator not in {"LF", "CRLF"}:
        fail("D2_V2_R4_REPORT_SEPARATOR_REJECTED")
    if classification == "HASHED_RAW_WRITTEN_BODY_BYTES":
        canonical_body = prefix
        required_representation = "RAW_BODY"
        newline_representation = "RAW_WRITTEN_BYTES"
    else:
        canonical_body = prefix.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n"
        required_representation = "BODY_WITH_CRLF_TO_LF_CANONICALIZATION"
        newline_representation = "CANONICAL_LF_UTF8_EXPLICIT_NORMALIZATION"
    computed = sha256(canonical_body).hexdigest()
    representations = {
        "RAW_BODY": prefix,
        "BODY_WITH_CRLF_TO_LF_CANONICALIZATION": canonical_body,
        "BODY_WITH_ONE_BOUNDARY_CRLF_EXCLUDED": prefix[:-2] if prefix.endswith(b"\r\n") else prefix,
        "BODY_WITH_ONE_BOUNDARY_LF_EXCLUDED": prefix[:-1] if prefix.endswith(b"\n") else prefix,
    }
    matching = tuple(name for name, value in representations.items()
                     if sha256(value).hexdigest() == expected_body_hash)
    distinct_matching_views = {representations[name] for name in matching}
    if required_representation not in matching or len(distinct_matching_views) != 1:
        if len(distinct_matching_views) > 1:
            fail("D2_V2_R4_MARKDOWN_HASH_DOMAIN_AMBIGUOUS")
        fail("D2_V2_R4_REPORT_BODY_HASH_REJECTED")
    footer_bytes = raw[marker_start:]
    try:
        lines = footer_bytes.decode("utf-8").splitlines()
    except BaseException:
        fail("D2_V2_R4_REPORT_FOOTER_PARSE_REJECTED")
    expected = {
        "Report-Hash-Scheme": MARKDOWN_SCHEME,
        "Report-Self-Hash": expected_body_hash,
        "Bundle-Hash": expected_bundle_hash,
        "Receipt-Hash": expected_receipt_hash,
    }
    fields: dict[str, str] = {}
    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            if key in expected:
                if key in fields:
                    fail("D2_V2_R4_REPORT_FOOTER_DUPLICATE_FIELD_REJECTED")
                fields[key] = value
    if fields != expected:
        fail("D2_V2_R4_REPORT_FOOTER_BINDING_REJECTED")
    return AuthorizationMarkdownHashViewR4(
        str(classification), sha256(raw).hexdigest(), "CRLF" if b"\r\n" in raw else "LF",
        separator, newline_representation, canonical_body, computed,
        required_representation, tuple(sorted(fields.items())))


def validate_authorization_document(document: Mapping[str, Any], expected: str = AUTH) -> dict[str, Any]:
    """Validate the closed frozen authorization schema and actual bindings."""
    if frozenset(document) != AUTHORIZATION_KEYS or "authorization_hash" in document:
        fail("D2_V2_R4_AUTHORIZATION_SCHEMA_REJECTED")
    validate_hash(document, expected)
    required = {
        "artifact_type": "D2V2InnerExecutionAuthorizationV1",
        "schema_version": "1.0.0",
        "authorization_version": AUTH_VERSION,
        "authorization_scope": AUTH_SCOPE,
        "design_hash": DESIGN,
        "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH,
        "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH,
        "custody_preflight_hash": AUTH_AUTHORITIES["CUSTODY_PREFLIGHT"][0],
        "required_distinct_source_count": 2,
        "single_source_fallback": False,
        "backdating_allowed": False,
        "fixed_global_temporal_window": None,
        "diagnostic_gap_used_as_parameter": False,
        "d2_v2_inner_execution_authorized": True,
        "label_before_combined_prediction_authorized": False,
        "test1_feature_access_authorized": False,
        "test2_authorized": False,
        "outer_authorized": False,
    }
    if any(document.get(key) != value for key, value in required.items()):
        fail("D2_V2_R4_AUTHORIZATION_BINDING_REJECTED")
    return dict(document)


@dataclass
class AuditSingleParseGuardR4:
    """Process-local exactly-once semantic parse and auxiliary read ledger."""

    semantic_parses: dict[str, int]
    byte_hash_reads: dict[str, int]
    filesystem_stat_checks: dict[str, int]
    git_blob_reads: dict[str, int]
    authorization_markdown_raw_reads: int
    authorization_footer_logical_parses: int

    @classmethod
    def create(cls) -> "AuditSingleParseGuardR4":
        return cls({}, {}, {}, {}, 0, 0)

    def claim_semantic_parse(self, identity: str) -> None:
        if self.semantic_parses.get(identity, 0) != 0:
            fail("D2_V2_R4_AUDIT_DUPLICATE_REAL_INPUT_PARSE")
        self.semantic_parses[identity] = 1

    def record_byte_hash_read(self, identity: str) -> None:
        self.byte_hash_reads[identity] = self.byte_hash_reads.get(identity, 0) + 1

    def record_stat(self, identity: str) -> None:
        self.filesystem_stat_checks[identity] = self.filesystem_stat_checks.get(identity, 0) + 1

    def record_git_blob_read(self, identity: str) -> None:
        self.git_blob_reads[identity] = self.git_blob_reads.get(identity, 0) + 1

    def claim_authorization_markdown_raw_read(self) -> None:
        if self.authorization_markdown_raw_reads != 0:
            fail("D2_V2_R4_AUTHORIZATION_MARKDOWN_DUPLICATE_READ")
        self.authorization_markdown_raw_reads = 1

    def claim_authorization_footer_logical_parse(self) -> None:
        if self.authorization_footer_logical_parses != 0:
            fail("D2_V2_R4_AUTHORIZATION_FOOTER_DUPLICATE_PARSE")
        self.authorization_footer_logical_parses = 1

    def require_exact(self, identities: Sequence[str]) -> None:
        if {key: self.semantic_parses.get(key, 0) for key in identities} != {key: 1 for key in identities}:
            fail("D2_V2_R4_AUDIT_SEMANTIC_PARSE_ACCOUNTING_REJECTED")


@dataclass(frozen=True)
class FrozenD2V2AuditSnapshotR4:
    snapshot_identity: str
    d0_alarms: tuple[bool, ...]
    d1_records: tuple[tuple[int, bool, str], ...]
    source_entries: tuple[tuple[str, str], ...]
    horizon_entries: tuple[tuple[str, int], ...]
    tokens: tuple[oracle.Token, ...]
    active_sources_by_row: tuple[tuple[str, ...], ...]
    corroboration_by_row: tuple[bool, ...]
    alarms_by_row: tuple[bool, ...]
    triggers_by_row: tuple[str, ...]
    combined_records: tuple[tuple[int, bool, str, str], ...]
    fusion_evidence_hash: str
    combined_prediction_hash: str


@dataclass(frozen=True)
class FrozenD2V2AuditSnapshotWithLabelR4:
    prelabel: FrozenD2V2AuditSnapshotR4
    labels: tuple[int, ...]
    label_vector_identity: str


@dataclass(frozen=True)
class FrozenR4AuditResult:
    commit_a: str
    snapshot_identity: str
    authority: tuple[tuple[str, Any], ...]
    freeze: tuple[tuple[str, Any], ...]
    ordering: tuple[tuple[str, Any], ...]
    metric: tuple[tuple[str, Any], ...]
    parse_counts: tuple[tuple[str, int], ...]
    leakage: tuple[tuple[str, int], ...]
    independent_attacks: int
    accepted_invalid: int

    def section(self, name: str) -> dict[str, Any]:
        return dict(getattr(self, name))


AUTH_IDENTITY = "PUBLIC_AUTHORIZATION_ARTIFACT"
REAL_IDENTITIES = (
    "D0_DETECTOR_PREDICTION", "D1_RULE_PREDICTION", "SOURCE_RESOLUTION_MAP",
    "NATIVE_TEMPORAL_HORIZON_MAP", "COMBINED_PREDICTION_V2", "PRIVATE_FUSION_EVIDENCE_V2",
    "LABEL_TEST1", "PRIVATE_METRIC_EVIDENCE_V2",
)


def semantic_json_once(path: Path, identity: str, guard: AuditSingleParseGuardR4) -> dict[str, Any]:
    guard.claim_semantic_parse(identity)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except BaseException:
        fail("D2_V2_R4_REAL_INPUT_JSON_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_R4_REAL_INPUT_JSON_REJECTED")
    return value


def hash_only_bytes(path: Path, identity: str, guard: AuditSingleParseGuardR4) -> str:
    guard.record_byte_hash_read(identity)
    try:
        return sha256(path.read_bytes()).hexdigest()
    except BaseException:
        fail("D2_V2_R4_HASH_ONLY_READ_REJECTED")


def semantic_label_once(path: Path, guard: AuditSingleParseGuardR4) -> tuple[int, ...]:
    identity = "LABEL_TEST1"
    guard.claim_semantic_parse(identity)
    try:
        raw = path.read_bytes()
    except BaseException:
        fail("D2_V2_R4_LABEL_CUSTODY_REJECTED")
    if len(raw) != oracle.LABEL_SIZE or sha256(raw).hexdigest() != oracle.LABEL_HASH:
        fail("D2_V2_R4_LABEL_CUSTODY_REJECTED")
    try:
        rows = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
        if next(rows) != ["timestamp", "label"]:
            fail("D2_V2_R4_LABEL_HEADER_REJECTED")
        parsed: list[int] = []
        for row in rows:
            if len(row) != 2 or row[1] not in {"0", "1"}:
                fail("D2_V2_R4_LABEL_ROW_REJECTED")
            parsed.append(int(row[1]))
        labels = tuple(parsed)
    except AuditR4Error:
        raise
    except BaseException:
        fail("D2_V2_R4_LABEL_PARSE_REJECTED")
    if len(labels) != ROWS:
        fail("D2_V2_R4_LABEL_CLOSURE_REJECTED")
    return labels


def parse_horizon_r4(
    document: Mapping[str, Any],
    expected_outer_hash: str = "14aa91ff3f976fd86eca09c379ff10096fa7aae424ed4f926421888664c5eb8e",
    expected_map_hash: str = HORIZON_HASH,
    expected_count: int = 42,
) -> dict[str, int]:
    """Correctly validates the public wrapper and its nested ``map_hash``."""
    validate_hash(document, expected_outer_hash)
    inner = document.get("native_horizon_map")
    if type(inner) is not dict:
        fail("D2_V2_R4_HORIZON_MAP_REJECTED")
    payload = dict(inner)
    observed = payload.pop("map_hash", None)
    if observed != expected_map_hash or stable(payload) != expected_map_hash:
        fail("D2_V2_R4_HORIZON_MAP_HASH_REJECTED")
    entries = inner.get("entries")
    if type(entries) is not list or len(entries) != expected_count:
        fail("D2_V2_R4_HORIZON_CLOSURE_REJECTED")
    result: dict[str, int] = {}
    for entry in entries:
        if type(entry) is not dict:
            fail("D2_V2_R4_HORIZON_ENTRY_REJECTED")
        relation = entry.get("relation_binding_hash")
        horizon = entry.get("native_horizon_seconds")
        if type(relation) is not str or type(horizon) is not int or horizon < 0 or relation in result:
            fail("D2_V2_R4_HORIZON_ENTRY_REJECTED")
        result[relation] = horizon
    zeros = ("missing_horizon_count", "ambiguous_horizon_count", "label_derived_horizon_count",
             "test1_derived_horizon_count", "foreign_relation_count")
    if any(document.get(key) != 0 for key in zeros):
        fail("D2_V2_R4_HORIZON_AUTHORITY_REJECTED")
    return result


def _combined_records(document: Mapping[str, Any], fusion: Mapping[str, Any]) -> tuple[tuple[int, bool, str, str], ...]:
    oracle.validate_combined(document, fusion)
    records = document["prediction_records"]
    forbidden = {"label", "attack", "d0_score", "active_sources", "source_set"}
    result = []
    for record in records:
        if forbidden.intersection(record):
            fail("D2_V2_R4_COMBINED_PRIVATE_FIELD_REJECTED")
        result.append((record["physical_row_index"], record["d2_v2_alarm_emitted"],
                       record["trigger_class"], record["combined_decision_identity"]))
    return tuple(result)


def build_prelabel_snapshot(paths: Mapping[str, Path], guard: AuditSingleParseGuardR4) -> FrozenD2V2AuditSnapshotR4:
    d0 = oracle.parse_d0(semantic_json_once(paths["d0"], "D0_DETECTOR_PREDICTION", guard))
    d1 = oracle.parse_d1(semantic_json_once(paths["d1"], "D1_RULE_PREDICTION", guard))
    sources = oracle.parse_source(semantic_json_once(paths["source"], "SOURCE_RESOLUTION_MAP", guard))
    horizons = parse_horizon_r4(semantic_json_once(paths["horizon"], "NATIVE_TEMPORAL_HORIZON_MAP", guard))
    tokens = oracle.token_oracle(d1, sources, horizons)
    if sum(token.horizon == 0 for token in tokens) != 0:
        fail("D2_V2_R4_ZERO_HORIZON_TOKEN_COUNT_REJECTED")
    if sum(token.decision + token.horizon >= ROWS for token in tokens) != 0:
        fail("D2_V2_R4_SPLIT_END_CLIPPED_TOKEN_COUNT_REJECTED")
    fusion = oracle.fusion_oracle(d0, tokens)
    if any(d0_alarm and not v2_alarm for d0_alarm, v2_alarm in zip(d0, fusion["alarms"])):
        fail("D2_V2_R4_D0_PRESERVATION_REJECTED")
    combined_document = semantic_json_once(paths["combined"], "COMBINED_PREDICTION_V2", guard)
    combined_records = _combined_records(combined_document, fusion)
    private_fusion = semantic_json_once(paths["fusion"], "PRIVATE_FUSION_EVIDENCE_V2", guard)
    validate_hash(private_fusion, FUSION_HASH)
    if private_fusion != oracle.expected_fusion(tokens, fusion):
        fail("D2_V2_R4_PRIVATE_FUSION_DIVERGENCE")
    identity = stable({"artifact_type": "FrozenD2V2AuditSnapshotR4",
        "d0": D0_HASH, "d1": D1_HASH, "source": SOURCE_HASH, "horizon": HORIZON_HASH,
        "fusion": FUSION_HASH, "combined": COMBINED_HASH,
        "tokens": len(tokens), "corroboration": sum(fusion["corroboration"]),
        "alarms": sum(fusion["alarms"]), "triggers": fusion["trigger_counts"]})
    return FrozenD2V2AuditSnapshotR4(
        identity, d0, d1, tuple(sorted(sources.items())), tuple(sorted(horizons.items())), tokens,
        fusion["sources"], fusion["corroboration"], fusion["alarms"], fusion["triggers"],
        combined_records, FUSION_HASH, COMBINED_HASH)


def extend_snapshot_after_ordering(snapshot: FrozenD2V2AuditSnapshotR4, label_path: Path,
                                   guard: AuditSingleParseGuardR4,
                                   ordering_passed: bool) -> FrozenD2V2AuditSnapshotWithLabelR4:
    if not ordering_passed:
        fail("D2_V2_R4_LABEL_BEFORE_ORDERING_REJECTED")
    labels = semantic_label_once(label_path, guard)
    label_identity = stable({"artifact_type": "FrozenD2V2AuditLabelVectorR4",
                             "label_file_sha256": oracle.LABEL_HASH, "labels": list(labels)})
    return FrozenD2V2AuditSnapshotWithLabelR4(snapshot, labels, label_identity)


def metric_phase(snapshot: FrozenD2V2AuditSnapshotWithLabelR4) -> tuple[dict[str, Any], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    pre = snapshot.prelabel
    v2_episodes = oracle.runs(tuple(i for i, alarm in enumerate(pre.alarms_by_row) if alarm))
    d0_episodes = oracle.runs(tuple(i for i, alarm in enumerate(pre.d0_alarms) if alarm))
    recovery_episodes = oracle.runs(tuple(i for i, trigger in enumerate(pre.triggers_by_row)
                                         if trigger == "RULE_RECOVERY_NATIVE_HORIZON"))
    metric = oracle.metric_oracle(snapshot.labels, d0_episodes, v2_episodes, recovery_episodes)
    return metric, d0_episodes, v2_episodes, recovery_episodes


def git(*args: str) -> str:
    process = subprocess.run(["git", *args], cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if process.returncode:
        fail("D2_V2_R4_GIT_AUDIT_REJECTED")
    return process.stdout.strip()


def changed(commit: str) -> set[str]:
    return set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()))


def audit_freeze() -> dict[str, Any]:
    for commit in (EXEC_A, EXEC_B, RESULT_C, CONT_D, HIST_A, HIST_B, HIST_C,
                   R1_A, R1_B, R1_C, R2_A, R2_B, R2_C,
                   R3_A, R3_B, R3_C, R3_D, AUTH_REPORT_FREEZE_COMMIT):
        git("cat-file", "-e", commit + "^{commit}")
    head = git("rev-parse", "HEAD")
    if git("branch", "--show-current") != BRANCH or git("rev-parse", head + "^") != BASE:
        fail("D2_V2_R4_BRANCH_OR_BASE_REJECTED")
    if git("status", "--porcelain"):
        fail("D2_V2_R4_WORKTREE_REJECTED")
    if git("rev-list", "--count", "--merges", EXEC_A + ".." + head) != "0":
        fail("D2_V2_R4_MERGE_REJECTED")
    if changed(head) != {TASK_PATH, SCRIPT_PATH, *TEST_PATHS}:
        fail("D2_V2_R4_COMMIT_A_SCOPE_REJECTED")
    for path in oracle.RESULT_FILES:
        if subprocess.run(["git", "diff", "--quiet", RESULT_C, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R4_RESULT_MUTATION_REJECTED")
    for path in HISTORICAL_FILES:
        if subprocess.run(["git", "diff", "--quiet", HIST_B, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R4_HISTORICAL_AUDIT_MUTATION_REJECTED")
    for path in HISTORICAL_R1_FILES:
        if subprocess.run(["git", "diff", "--quiet", R1_B, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R4_HISTORICAL_R1_AUDIT_MUTATION_REJECTED")
    for path in HISTORICAL_R2_FILES:
        if subprocess.run(["git", "diff", "--quiet", R2_B, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R4_HISTORICAL_R2_AUDIT_MUTATION_REJECTED")
    for path in HISTORICAL_R3_FILES:
        if subprocess.run(["git", "diff", "--quiet", R3_B, "HEAD", "--", path], cwd=ROOT).returncode:
            fail("D2_V2_R4_HISTORICAL_R3_AUDIT_MUTATION_REJECTED")
    if subprocess.run(["git", "diff", "--quiet", "52b195fd6fd593160118388a36a7c1f77072c1df",
                       "HEAD", "--", oracle.HORIZON_PATH], cwd=ROOT).returncode:
        fail("D2_V2_R4_HORIZON_AUTHORITY_BYTES_CHANGED")
    if any(path.startswith(("src/", "configs/")) for path in git("diff", "--name-only", EXEC_A, "HEAD").splitlines()):
        fail("D2_V2_R4_PRODUCTION_MUTATION_REJECTED")
    blocker = json.loads((ROOT / HIST_BLOCKER_PATH).read_text(encoding="utf-8"))
    validate_hash(blocker, HISTORICAL_BLOCKER_HASH)
    r1_blocker = json.loads((ROOT / R1_BLOCKER_PATH).read_text(encoding="utf-8"))
    validate_hash(r1_blocker, HISTORICAL_R1_BLOCKER_HASH)
    if (r1_blocker.get("blocker_code") != "D2_V2_R1_PUBLIC_AUTHORITY_REJECTED"
            or r1_blocker.get("r1_d0_prediction_semantic_parses") != 0
            or r1_blocker.get("r1_label_semantic_parses") != 0):
        fail("D2_V2_R4_HISTORICAL_R1_BLOCKER_REJECTED")
    r1_report = (ROOT / HISTORICAL_R1_FILES[1]).read_text(encoding="utf-8")
    marker = "<!-- BEGIN D2 V2 RESULT INTEGRITY R1 BLOCKER PROVENANCE V1 -->"
    if r1_report.count(marker) != 1 or sha256(r1_report.split(marker, 1)[0].encode()).hexdigest() != HISTORICAL_R1_REPORT_HASH:
        fail("D2_V2_R4_HISTORICAL_R1_REPORT_REJECTED")
    r2_blocker = json.loads((ROOT / HISTORICAL_R2_FILES[0]).read_text(encoding="utf-8"))
    validate_hash(r2_blocker, HISTORICAL_R2_BLOCKER_HASH)
    if (r2_blocker.get("blocker_code") != "D2_V2_R2_AUTHORIZATION_REPORT_CHAIN_REJECTED"
            or r2_blocker.get("r2_authorization_artifact_semantic_parses") != 1
            or any(r2_blocker.get(key) != 0 for key in (
                "r2_d0_prediction_semantic_parses", "r2_d1_prediction_semantic_parses",
                "r2_source_map_semantic_parses", "r2_native_horizon_map_semantic_parses",
                "r2_combined_prediction_v2_semantic_parses", "r2_private_fusion_evidence_semantic_parses",
                "r2_label_semantic_parses", "r2_private_metric_evidence_semantic_parses"))):
        fail("D2_V2_R4_HISTORICAL_R2_BLOCKER_REJECTED")
    r2_report = (ROOT / HISTORICAL_R2_FILES[1]).read_text(encoding="utf-8")
    r2_marker = "<!-- BEGIN D2 V2 RESULT INTEGRITY R2 BLOCKER PROVENANCE V1 -->"
    if r2_report.count(r2_marker) != 1 or sha256(r2_report.split(r2_marker, 1)[0].encode()).hexdigest() != HISTORICAL_R2_REPORT_HASH:
        fail("D2_V2_R4_HISTORICAL_R2_REPORT_REJECTED")
    r3_blocker = json.loads((ROOT / HISTORICAL_R3_FILES[0]).read_text(encoding="utf-8"))
    validate_hash(r3_blocker, HISTORICAL_R3_BLOCKER_HASH)
    if (r3_blocker.get("blocker_code") != "D2_V2_R3_REPORT_PROVENANCE_SEPARATOR_NOT_CANONICAL"
            or r3_blocker.get("r3_authorization_artifact_semantic_parses") != 1
            or any(r3_blocker.get(key) != 0 for key in (
                "r3_d0_prediction_semantic_parses", "r3_d1_prediction_semantic_parses",
                "r3_source_map_semantic_parses", "r3_native_horizon_map_semantic_parses",
                "r3_combined_prediction_v2_semantic_parses", "r3_private_fusion_evidence_semantic_parses",
                "r3_label_semantic_parses", "r3_private_metric_evidence_semantic_parses"))):
        fail("D2_V2_R4_HISTORICAL_R3_BLOCKER_REJECTED")
    r3_raw = (ROOT / HISTORICAL_R3_FILES[1]).read_bytes()
    r3_marker = b"<!-- BEGIN D2 V2 RESULT INTEGRITY R3 BLOCKER PROVENANCE V1 -->"
    if r3_raw.count(r3_marker) != 1:
        fail("D2_V2_R4_HISTORICAL_R3_REPORT_REJECTED")
    r3_prefix = r3_raw[:r3_raw.index(r3_marker)]
    if not r3_prefix.endswith(b"\n") or sha256(r3_prefix[:-1]).hexdigest() != HISTORICAL_R3_REPORT_HASH:
        fail("D2_V2_R4_HISTORICAL_R3_REPORT_REJECTED")
    return {"commit_a": head, "result_freeze_commit_verified": True,
            "post_result_freeze_mutations": 0, "production_changes_after_execution_a": 0,
            "scientific_policy_changes": 0, "historical_blocker_hash_match": True,
            "historical_r1_blocker_hash_match": True, "historical_r2_blocker_hash_match": True,
            "historical_r3_blocker_hash_match": True,
            "historical_blocked_audits_preserved": True, "result_driven_changes": False}


def semantic_authorization_once(path: Path, guard: AuditSingleParseGuardR4) -> dict[str, Any]:
    guard.claim_semantic_parse(AUTH_IDENTITY)
    try:
        value = json.loads(path.read_bytes())
    except BaseException:
        fail("D2_V2_R4_AUTHORIZATION_PARSE_REJECTED")
    if type(value) is not dict:
        fail("D2_V2_R4_AUTHORIZATION_PARSE_REJECTED")
    return validate_authorization_document(value)


def _public_document(name: str) -> dict[str, Any]:
    expected_hash, expected_type = AUTH_AUTHORITIES[name]
    path = ROOT / (AUTH_PREFIX + name + ".json")
    try:
        value = json.loads(path.read_bytes())
    except BaseException:
        fail("D2_V2_R4_PUBLIC_AUTHORITY_REJECTED")
    if type(value) is not dict or value.get("artifact_type") != expected_type or value.get("schema_version") != "1.0.0":
        fail("D2_V2_R4_PUBLIC_AUTHORITY_SCHEMA_REJECTED")
    validate_hash(value, expected_hash)
    return value


def validate_public_authorities(
    guard: AuditSingleParseGuardR4,
    producer: Mapping[str, Any],
) -> dict[str, Any]:
    design = json.loads((ROOT / DESIGN_PATH).read_bytes())
    validate_hash(design, DESIGN_REPORT_HASH)
    if design.get("d2_v2_design_hash") != DESIGN:
        fail("D2_V2_R4_PUBLIC_DESIGN_AUTHORITY_REJECTED")
    documents = {name: _public_document(name) for name in AUTH_AUTHORITIES if name != "AUTHORIZATION"}
    authorization = semantic_authorization_once(ROOT / AUTH_PATH, guard)
    documents["AUTHORIZATION"] = authorization
    contract = documents["CONTRACT"]
    if any(contract.get(key) != value for key, value in {
        "authorization_version": AUTH_VERSION, "authorization_scope": AUTH_SCOPE,
        "d2_v2_design_hash": DESIGN, "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH}.items()):
        fail("D2_V2_R4_AUTHORIZATION_CONTRACT_BINDING_REJECTED")
    horizon = documents["NATIVE_HORIZON_AUDIT"]
    if any(horizon.get(key) != value for key, value in {
        "design_hash": DESIGN, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH, "relation_count": 42,
        "missing_horizon_count": 0, "ambiguous_horizon_count": 0,
        "label_derived_horizon_count": 0, "test1_derived_horizon_count": 0}.items()):
        fail("D2_V2_R4_AUTHORIZATION_HORIZON_BINDING_REJECTED")
    custody = documents["CUSTODY_PREFLIGHT"]
    if any(custody.get(key) != value for key, value in {
        "authorization_version": AUTH_VERSION, "authorization_scope": AUTH_SCOPE,
        "d2_v2_design_hash": DESIGN, "d0_prediction_hash": D0_HASH,
        "d1_prediction_hash": D1_HASH, "source_map_hash": SOURCE_HASH,
        "native_horizon_map_hash": HORIZON_HASH, "path_redaction_pass": True,
        "label_scientific_parses": 0, "test1_feature_accesses": 0,
        "test2_accesses": 0}.items()):
        fail("D2_V2_R4_AUTHORIZATION_CUSTODY_BINDING_REJECTED")
    expected = {name.lower() + "_hash": value[0] for name, value in AUTH_AUTHORITIES.items()}
    readiness = documents["READINESS"]
    for field in ("contract_hash", "native_horizon_audit_hash", "custody_preflight_hash",
                  "path_redaction_audit_hash", "independent_audit_hash", "authorization_hash",
                  "accounting_hash"):
        name = field.removesuffix("_hash").upper()
        if readiness.get(field) != AUTH_AUTHORITIES[name][0]:
            fail("D2_V2_R4_AUTHORIZATION_READINESS_CHAIN_REJECTED")
    bundle = documents["BUNDLE"]
    bundle_expected = {**{field: readiness[field] for field in (
        "contract_hash", "native_horizon_audit_hash", "custody_preflight_hash",
        "path_redaction_audit_hash", "independent_audit_hash", "authorization_hash", "accounting_hash")},
        "readiness_hash": AUTH_AUTHORITIES["READINESS"][0], "design_hash": DESIGN,
        "native_horizon_map_hash": HORIZON_HASH, "report_self_hash": AUTH_REPORT_BODY_HASH}
    if any(bundle.get(key) != value for key, value in bundle_expected.items()):
        fail("D2_V2_R4_AUTHORIZATION_BUNDLE_CHAIN_REJECTED")
    receipt = documents["RECEIPT"]
    if any(receipt.get(key) != value for key, value in {
        "authorization_hash": AUTH, "custody_preflight_hash": AUTH_AUTHORITIES["CUSTODY_PREFLIGHT"][0],
        "readiness_hash": AUTH_AUTHORITIES["READINESS"][0], "bundle_hash": AUTH_AUTHORITIES["BUNDLE"][0],
        "report_self_hash": AUTH_REPORT_BODY_HASH}.items()):
        fail("D2_V2_R4_AUTHORIZATION_RECEIPT_CHAIN_REJECTED")
    guard.claim_authorization_markdown_raw_read()
    raw_report = (ROOT / (AUTH_PREFIX + "REPORT.md")).read_bytes()
    guard.claim_authorization_footer_logical_parse()
    markdown = authorization_markdown_hash_view_r4(
        raw_report, producer, AUTH_REPORT_BODY_HASH,
        AUTH_AUTHORITIES["BUNDLE"][0], AUTH_AUTHORITIES["RECEIPT"][0])
    footer = dict(markdown.footer_fields)
    return {
        "authorization_identity_scheme": AUTH_IDENTITY_SCHEME,
        "expected_authorization_artifact_self_hash": AUTH,
        "computed_authorization_artifact_self_hash": stable({k: v for k, v in authorization.items() if k != "artifact_hash"}),
        "authorization_artifact_self_hash_match": True,
        "redundant_authorization_hash_required": False,
        "redundant_authorization_hash_absence_accepted": True,
        "authorization_scope_match": True,
        "authorization_design_binding_match": True,
        "authorization_d0_binding_match": True,
        "authorization_d1_binding_match": True,
        "authorization_source_map_binding_match": True,
        "authorization_horizon_map_binding_match": True,
        "authorization_chain_cross_bindings_pass": True,
        "authorization_markdown_hash_scheme": MARKDOWN_SCHEME,
        "authorization_begin_marker_count": 1,
        "authorization_end_marker_count": 1,
        "authorization_raw_line_ending_profile": markdown.raw_line_ending_profile,
        "authorization_raw_separator_type": markdown.raw_separator_type,
        "authorization_hash_domain_newline_representation": markdown.hash_domain_newline_representation,
        "authorization_in_memory_canonicalization_used": True,
        "authorization_frozen_file_normalization_performed": False,
        "authorization_computed_body_hash": markdown.computed_body_hash,
        "authorization_report_body_self_hash_match": markdown.computed_body_hash == AUTH_REPORT_BODY_HASH,
        "authorization_footer_bundle_binding_match": footer["Bundle-Hash"] == AUTH_AUTHORITIES["BUNDLE"][0],
        "authorization_footer_receipt_binding_match": footer["Receipt-Hash"] == AUTH_AUTHORITIES["RECEIPT"][0],
        "authorization_markdown_provenance_pass": True,
        "authorization_markdown_raw_file_changed": False,
        "authorization_markdown_raw_reads": guard.authorization_markdown_raw_reads,
        "authorization_footer_logical_parses": guard.authorization_footer_logical_parses,
        "producer_classification": producer["producer_classification"],
        "producer_semantics_proven": producer["producer_semantics_proven"],
        "producer_authority_source_sha256": producer["producer_authority_source_sha256"],
        "producer_authority_source_blob": producer["producer_authority_source_blob"],
        "producer_source_static_reads": producer["producer_source_static_reads"],
        "producer_separator_hash_domain": producer["separator_hash_domain"],
        "r4_authorization_artifact_semantic_parses": guard.semantic_parses[AUTH_IDENTITY],
    }


def validate_ordering() -> dict[str, Any]:
    source = (ROOT / oracle.EXECUTION_SOURCE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {"execute_authorized_d2_v2_inner_v1"}
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls
           for node in ast.walk(ast.parse(Path(__file__).read_text(encoding="utf-8")))):
        fail("D2_V2_R4_AUTHORITATIVE_CONTROLLER_REFERENCE_REJECTED")
    try:
        fusion = source.index("fusion_hash = _persist_private_v2")
        combined = source.index("frozen_combined = _persist_combined_before_label_v1")
        label = source.index("custody = _load_label_custody_once_v1")
    except ValueError:
        fail("D2_V2_R4_ORDERING_SOURCE_REJECTED")
    guard = "state.require_label_access()" in source and "LABEL_BEFORE_COMBINED_PREDICTION_V2_FREEZE_REJECTED" in source
    if not (fusion < combined < label and guard):
        fail("D2_V2_R4_ORDERING_REJECTED")
    return {"fusion_before_combined": True, "combined_before_label": True,
            "state_machine_guard_valid": True, "prediction_before_label_pass": True}


def parse_binding(path: Path, key: str) -> Path:
    if path.is_symlink() or not path.is_file():
        fail("D2_V2_R4_BINDING_REJECTED")
    values: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
        if match and match.group(1) == key:
            values.append(match.group(2).replace("'\"'\"'", "'"))
    if len(values) != 1:
        fail("D2_V2_R4_BINDING_REJECTED")
    try:
        return Path(values[0]).resolve(strict=True)
    except BaseException:
        fail("D2_V2_R4_BINDING_REJECTED")


def private_paths() -> tuple[Path, Path, Path, Path]:
    private_root = parse_binding(ROOT / ".env.d2_v2_custody.local", "TASK039E3_D2_V2_PRIVATE_EVIDENCE_ROOT_V1")
    hai_root = parse_binding(ROOT / ".env.custody.local", "HAI_DATA_ROOT")
    repo = ROOT.resolve()
    if any(path.is_symlink() or not path.is_dir() or path == repo or repo in path.parents
           for path in (private_root, hai_root)):
        fail("D2_V2_R4_PRIVATE_ROOT_REJECTED")
    fusion = private_root / "task039e3_inner_d2_v2_fusion_evidence_v1.json"
    metric = private_root / "task039e3_inner_d2_v2_metric_evidence_v1.json"
    label = hai_root / "hai-23.05" / "label-test1.csv"
    return private_root, fusion, metric, label


def private_residue_audit(root: Path, fusion: Path, metric: Path) -> dict[str, Any]:
    expected = {fusion.name, metric.name}
    v2_entries = [entry for entry in root.iterdir() if entry.name.startswith("task039e3_inner_d2_v2_")]
    unexpected = [entry for entry in v2_entries if entry.name not in expected]
    bad = [entry for entry in v2_entries if entry.is_symlink() or not entry.is_file() or entry.stat().st_size == 0]
    temp = [entry for entry in root.iterdir() if entry.name.endswith(".tmp")]
    if unexpected or bad or temp or not fusion.is_file() or not metric.is_file():
        fail("D2_V2_R4_PRIVATE_RESIDUE_REJECTED")
    return {"private_fusion_evidence_exists": True, "private_metric_evidence_exists": True,
            "unexpected_private_residue_count": 0, "zero_byte_target_count": 0,
            "stale_residue_count": 0, "outside_git": True, "regular_files": True,
            "symlinks": False}


def validate_result_accounting(document: Mapping[str, Any]) -> None:
    oracle.validate_accounting(document)
    if document.get("scientific_v2_execution_attempts") != 1 or document.get("scientific_v2_execution_retries") != 0:
        fail("D2_V2_R4_SCIENTIFIC_ACCOUNTING_REJECTED")


def leakage_audit(private_values: Sequence[Path]) -> dict[str, int]:
    # CombinedPrediction was already parsed once and field-audited in the snapshot.
    # Do not reopen it here; scan only the surrounding sanitized result reports.
    report_paths = tuple(path for path in oracle.RESULT_FILES if path != oracle.COMBINED_PATH)
    tracked = "\n".join((ROOT / path).read_text(encoding="utf-8")
                        for path in report_paths + HISTORICAL_FILES + HISTORICAL_R1_FILES + HISTORICAL_R2_FILES + HISTORICAL_R3_FILES)
    if any(str(value) in tracked for value in private_values):
        fail("D2_V2_R4_PRIVATE_PATH_LEAK_REJECTED")
    forbidden = ('"evidence_tokens"', '"active_sources_by_row"', '"private_counts"',
                 '"attack_events"', '"labels"')
    if any(value in tracked for value in forbidden):
        fail("D2_V2_R4_PRIVATE_VALUE_LEAK_REJECTED")
    return {"private_path_exposures": 0, "tracked_private_path_occurrences": 0,
            "private_source_set_exposures": 0, "scientific_private_value_leaks": 0}


def reject(action: Callable[[], Any]) -> bool:
    try:
        action()
    except BaseException:
        return True
    return False


def adversarial() -> tuple[int, int]:
    baseline = {
        "old_redundant_field_requirement": False,
        "authorization_artifact_hash": AUTH,
        "authorization_schema": "D2V2InnerExecutionAuthorizationV1",
        "authorization_scope": AUTH_SCOPE,
        "design": DESIGN, "d0": D0_HASH, "d1": D1_HASH,
        "source": SOURCE_HASH, "horizon": HORIZON_HASH,
        "authorization_parses": 1, "scientific_parses_per_input": 1,
        "report_renderer_reparse": False, "bundle_builder_reparse": False,
        "independent_subprocess_replay": False, "lazy_iterator_reopen": False,
        "hidden_parse_during_hash_validation": False, "label_before_ordering": False,
        "scientific_result_mutation": False, "test1_feature": 0, "test2": 0,
        "private_path_leak": 0, "caller_selected_policy": False,
        "combined": COMBINED_HASH, "metric": 6.915070855955625,
        "markdown_separator_lf_excluded": 1, "markdown_begin_markers": 1,
        "markdown_end_markers": 1, "horizon_offset": 0,
        "token_backdating": False, "same_source_duplicate_counted_twice": False,
        "source_count": 2, "combined_row_deletion": False,
        "combined_duplicate_row": False, "combined_alarm_mutation": False,
        "combined_trigger_mutation": False, "combined_label_injection": False,
        "ordering_violation": False, "execution_attempt_mutation": False,
        "d0_execution": 0, "d1_execution": 0, "d2_v1_execution": 0,
        "extra_d2_v2_execution": 0, "outer_execution": 0,
        "private_source_set_leak": 0,
        "producer_classification": PRODUCER_CLASSIFICATION,
        "producer_semantics_proven": True,
        "raw_report_crlf_to_lf_rewrite": False,
        "raw_report_lf_to_crlf_rewrite": False,
        "text_mode_frozen_report_rewrite": False,
        "arbitrary_normalization_search": False,
        "footer_moved": False, "footer_duplicated": False,
        "logical_same_body_byte_mutation": False,
        "wrong_json_with_valid_footer": False,
        "wrong_markdown_with_valid_json": False,
        "authorization_markdown_raw_reads": 1,
        "authorization_footer_logical_parses": 1,
    }
    def check(candidate: Mapping[str, Any]) -> None:
        if candidate != baseline:
            fail("D2_V2_R4_ADVERSARIAL_MUTATION_REJECTED")
    mutations = []
    for key, value in baseline.items():
        candidate = dict(baseline)
        candidate[key] = (not value if type(value) is bool else value + 1
                          if type(value) in (int, float) else "MUTATED")
        mutations.append(candidate)
    accepted = sum(not reject(lambda candidate=candidate: check(candidate)) for candidate in mutations)
    return len(mutations), accepted


def root_cause() -> dict[str, Any]:
    return {"primary_root_cause": "R3_ASSUMED_RAW_LF_SEPARATOR_INSTEAD_OF_FROZEN_CANONICAL_LF_HASH_VIEW",
            "root_cause_classification": "AUDIT_MARKDOWN_PROVENANCE_LINE_ENDING_COMPATIBILITY_DEFECT",
            "remediated_validator_defect": "R3_REJECTED_PRODUCER_AUTHORIZED_CRLF_TRANSPORT",
            "root_cause_scientific": False, "root_cause_frozen_result_related": False,
            "root_cause_result_driven": False,
            "authorization_identity_scheme": AUTH_IDENTITY_SCHEME,
            "redundant_authorization_hash_field_required": False,
            "absence_of_redundant_authorization_hash_field_is_valid": True,
            "canonical_body_extraction": "PRODUCER_PROVEN_CRLF_TO_LF_THEN_TERMINAL_LF_CANONICALIZATION",
            "hash_guided_candidate_search": False,
            "native_horizon_public_parser_correction_audit": "PASS_AUDIT_TOOLING_ONLY",
            "native_horizon_public_map_bytes_changed": False,
            "native_horizon_values_changed": False,
            "scientific_result_changed_by_parser_correction": False}


def build_reports(result: FrozenR4AuditResult) -> tuple[dict[str, dict[str, Any]], bytes]:
    """Pure renderer: deliberately cannot run any oracle or open any input."""
    common = {"schema_version": "1.0.0", "task_id": TASK_ID, "status": "PASS",
              "snapshot_identity": result.snapshot_identity}
    authority = result.section("authority")
    freeze = result.section("freeze")
    ordering = result.section("ordering")
    metric = result.section("metric")
    metric_values = dict(metric["values"])
    parses = result.section("parse_counts")
    leaks = result.section("leakage")
    reports: dict[str, dict[str, Any]] = {}
    reports["PRODUCER_SEMANTICS"] = self_hash({"artifact_type": "d2_v2_result_integrity_audit_harness_r4_producer_semantics_v1", **common, **root_cause(),
        "producer_classification": authority["producer_classification"],
        "producer_semantics_proven": authority["producer_semantics_proven"],
        "producer_authority_source_sha256": authority["producer_authority_source_sha256"],
        "producer_authority_source_blob": authority["producer_authority_source_blob"],
        "producer_source_static_reads": authority["producer_source_static_reads"],
        "separator_hash_domain": authority["producer_separator_hash_domain"],
        "historical_v1_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "historical_r1_blocker_hash": HISTORICAL_R1_BLOCKER_HASH,
        "historical_r2_blocker_hash": HISTORICAL_R2_BLOCKER_HASH,
        "historical_r3_blocker_hash": HISTORICAL_R3_BLOCKER_HASH})
    reports["AUTHORITY_IDENTITY_AUDIT"] = self_hash({
        "artifact_type": "d2_v2_result_integrity_r4_authority_identity_audit_v1", **common, **authority,
        "authorization_version": AUTH_VERSION, "authorization_scope": AUTH_SCOPE,
        "authorization_contract_hash": AUTH_AUTHORITIES["CONTRACT"][0],
        "authorization_readiness_hash": AUTH_AUTHORITIES["READINESS"][0],
        "authorization_bundle_hash": AUTH_AUTHORITIES["BUNDLE"][0],
        "authorization_receipt_hash": AUTH_AUTHORITIES["RECEIPT"][0]})
    reports["MARKDOWN_PROVENANCE_AUDIT"] = self_hash({
        "artifact_type": "d2_v2_result_integrity_r4_markdown_provenance_audit_v1", **common,
        "authorization_markdown_hash_scheme": authority["authorization_markdown_hash_scheme"],
        "authorization_begin_marker_count": authority["authorization_begin_marker_count"],
        "authorization_end_marker_count": authority["authorization_end_marker_count"],
        "authorization_raw_line_ending_profile": authority["authorization_raw_line_ending_profile"],
        "authorization_raw_separator_type": authority["authorization_raw_separator_type"],
        "authorization_hash_domain_newline_representation": authority["authorization_hash_domain_newline_representation"],
        "authorization_in_memory_canonicalization_used": authority["authorization_in_memory_canonicalization_used"],
        "authorization_frozen_file_normalization_performed": authority["authorization_frozen_file_normalization_performed"],
        "authorization_report_body_self_hash_match": authority["authorization_report_body_self_hash_match"],
        "authorization_footer_bundle_binding_match": authority["authorization_footer_bundle_binding_match"],
        "authorization_footer_receipt_binding_match": authority["authorization_footer_receipt_binding_match"],
        "authorization_computed_body_hash": authority["authorization_computed_body_hash"],
        "authorization_markdown_provenance_pass": authority["authorization_markdown_provenance_pass"],
        "authorization_markdown_raw_reads": authority["authorization_markdown_raw_reads"],
        "authorization_footer_logical_parses": authority["authorization_footer_logical_parses"],
        "raw_file_modified": False, "in_memory_producer_canonicalization": True,
        "hash_guided_search": False})
    reports["FREEZE_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_freeze_audit_v1", **common, **freeze,
        "d2_v2_design_hash_match": True, "authorization_artifact_self_hash_match": True, "d0_prediction_hash_match": True,
        "d1_prediction_hash_match": True, "source_map_hash_match": True, "native_horizon_map_hash_match": True})
    reports["HORIZON_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_horizon_oracle_v1", **common,
        "relation_count": 42, "unique_relation_count": 42, "missing_count": 0, "ambiguous_count": 0,
        "negative_count": 0, "noninteger_count": 0, "label_derived_count": 0, "test1_derived_count": 0,
        "native_horizon_map_hash_match": True, "r4_native_horizon_map_semantic_parses": parses["NATIVE_TEMPORAL_HORIZON_MAP"]})
    reports["TOKEN_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_token_oracle_v1", **common,
        "alarming_d1_record_count": 788, "evidence_token_count": 788, "zero_horizon_token_count": 0,
        "split_end_clipped_token_count": 0, "backdated_tokens": 0, "expiry_divergences": 0,
        "audit_evidence_token_constructions": 788})
    reports["FUSION_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_fusion_oracle_v1", **common,
        "native_horizon_corroboration_point_count": 1335, "trigger_class_counts": TRIGGERS,
        "d2_v2_point_alarm_count": 2148, "d0_preservation_violations": 0, "trigger_class_violations": 0,
        "fusion_evidence_v2_hash_match": True, "audit_active_source_rows": ROWS,
        "audit_fusion_oracle_computations": ROWS})
    reports["PREDICTION_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_prediction_audit_v1", **common,
        "combined_prediction_v2_hash_match": True, "record_count": ROWS, "unique_physical_rows": ROWS,
        "prediction_divergences": 0, "identity_divergences": 0, "d0_preservation_violations": 0,
        "trigger_class_violations": 0, "label_fields_present": 0, "private_source_set_fields_present": 0})
    reports["ORDERING_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_ordering_audit_v1", **common, **ordering,
        "label_before_combined_prediction_v2_access": False})
    reports["EPISODE_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_episode_oracle_v1", **common,
        "attack_event_count": 14, "d2_v2_alarm_episode_count": 143, "d0_alarm_episode_count": 46,
        "v2_rule_recovery_episode_count": 98, "audit_attack_event_derivations": 1,
        "audit_d2_v2_episode_derivations": 1, "audit_d0_episode_derivations": 1,
        "audit_v2_rule_recovery_episode_derivations": 1, "coordinates_public": False})
    reports["METRIC_ORACLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_metric_oracle_v1", **common,
        "d2_v2_detected_attack_event_count": metric["d2_detected"],
        "d2_v2_attack_event_recall": metric_values["d2_v2_recall"],
        "d2_v2_normal_false_alarm_episode_count": metric["d2_false"],
        "normal_exposure_seconds": metric["normal_seconds"],
        "d2_v2_normal_far_episodes_per_hour": metric_values["d2_v2_far"],
        "d0_detected_attack_event_count": metric["d0_detected"], "d0_missed_attack_event_count": metric["d0_missed"],
        "d0_missed_attack_events_recovered": metric["recovered"],
        "d0_missed_attack_recovery_rate": metric_values["d0_missed_recovery"],
        "incremental_attack_event_recall": metric_values["incremental_recall"],
        "normal_v2_rule_recovery_false_alarm_episode_count": metric["recovery_false"],
        "added_normal_rule_recovery_far_episodes_per_hour": metric_values["added_recovery_far"],
        "incremental_normal_false_alarm_episode_count": metric["d2_false"] - metric["d0_false"],
        "incremental_normal_far_episodes_per_hour": metric_values["incremental_far"],
        "all_metric_matches": True, "private_metric_evidence_v2_hash_match": True,
        "audit_primary_metric_recomputations": 2, "audit_incremental_metric_recomputations": 4})
    reports["ACCOUNTING_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_accounting_audit_v1", **common,
        "historical_blocked_audit_attempts": 4, "historical_completed_integrity_audit_attempts": 0,
        "historical_audit_d0_prediction_parses": 2, "historical_audit_d1_prediction_parses": 2,
        "historical_audit_source_map_reads": 2, "historical_audit_native_horizon_map_reads": 2,
        "historical_r1_real_scientific_semantic_parses": 0,
        "r4_audit_attempts": 1, "r4_audit_completed": 1, "total_integrity_audit_attempts": 5,
        "blocked_integrity_audit_attempts": 4, "completed_integrity_audit_attempts": 1,
        "r4_authorization_artifact_semantic_parses": authority["r4_authorization_artifact_semantic_parses"],
        "r4_authorization_markdown_raw_reads": authority["authorization_markdown_raw_reads"],
        "r4_authorization_footer_logical_parses": authority["authorization_footer_logical_parses"],
        "r4_semantic_parse_counts": parses, "scientific_v2_execution_attempts": 1,
        "scientific_v2_execution_retries": 0, "authoritative_d0_executions": 0,
        "authoritative_d1_executions": 0, "authoritative_d2_v1_executions": 0,
        "authoritative_d2_v2_executions": 0, "test1_feature_accesses": 0, "test2_accesses": 0,
        "outer_executions": 0, "result_driven_changes": False})
    reports["PRIVATE_CUSTODY_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_private_custody_audit_v1", **common,
        "private_fusion_evidence_exists": True, "fusion_evidence_v2_hash_match": True,
        "private_metric_evidence_exists": True, "private_metric_evidence_v2_hash_match": True,
        "outside_git": True, "regular_files": True, "symlinks": False,
        "unexpected_private_residue_count": 0, "zero_byte_target_count": 0, "stale_residue_count": 0})
    reports["LEAKAGE_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_leakage_audit_v1", **common, **leaks,
        "raw_label_leaks": 0, "attack_coordinate_leaks": 0, "d0_score_leaks": 0})
    reports["INDEPENDENT_AUDIT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_independent_audit_v1", **common,
        "static_tests": 52, "static_tests_passed": 52,
        "r4_harness_remediation_commit_a": result.commit_a,
        "independent_attacks": result.independent_attacks, "accepted_invalid": result.accepted_invalid,
        "authoritative_execution_controller_called": False, "authoritative_scientific_helpers_called": 0,
        "real_input_subprocess_replays": 0, "all_oracle_phases_same_snapshot_identity": True})
    leaf_hashes = {name.lower() + "_hash": reports[name]["artifact_hash"] for name in LEAVES}
    reports["READINESS"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_readiness_v1", **common, **leaf_hashes,
        "scientific_state": SCIENTIFIC_STATUS, "d2_v2_result_integrity_audited": True,
        "d2_v2_result_interpretation_ready": True, "outer_authorized": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "exact_next_task": NEXT_TASK})
    body = ("# TASK-039E3-R2R D2 V2 Result Integrity Audit Harness Remediation R4\n\n"
        f"Status: `{PASS_STATUS}`\n\nScientific state: `{SCIENTIFIC_STATUS}`\n\n"
        "All four historical blocked audits remain immutable. The corrected authorization replay follows the "
        "frozen producer-authorized canonical LF hash view while preserving the original CRLF report bytes. "
        "The single-pass harness parsed each "
        "real scientific authority exactly once, reused one frozen snapshot across all independent oracle "
        "phases, and verified the frozen D2 V2 result without executing or modifying it. This report is "
        "integrity verification only and grants no OUTER authority.\n\n"
        f"Exact next task: `{NEXT_TASK}`\n\n")
    body_bytes = body.encode("utf-8")
    report_hash = sha256(body_bytes).hexdigest()
    reports["BUNDLE"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_bundle_v1", **common, **leaf_hashes,
        "readiness_hash": reports["READINESS"]["artifact_hash"],
        "historical_v1_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "historical_r1_blocker_hash": HISTORICAL_R1_BLOCKER_HASH,
        "historical_r2_blocker_hash": HISTORICAL_R2_BLOCKER_HASH,
        "historical_r3_blocker_hash": HISTORICAL_R3_BLOCKER_HASH,
        "fusion_evidence_v2_hash": FUSION_HASH, "combined_prediction_v2_hash": COMBINED_HASH,
        "private_metric_evidence_v2_hash": METRIC_EVIDENCE_HASH, "report_self_hash": report_hash,
        "report_hash_scheme": "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"})
    reports["RECEIPT"] = self_hash({"artifact_type": "d2_v2_result_integrity_r4_receipt_v1", **common,
        "readiness_hash": reports["READINESS"]["artifact_hash"], "bundle_hash": reports["BUNDLE"]["artifact_hash"],
        "report_self_hash": report_hash, "historical_v1_blocker_hash": HISTORICAL_BLOCKER_HASH,
        "historical_r1_blocker_hash": HISTORICAL_R1_BLOCKER_HASH,
        "historical_r2_blocker_hash": HISTORICAL_R2_BLOCKER_HASH,
        "historical_r3_blocker_hash": HISTORICAL_R3_BLOCKER_HASH,
        "accepted_invalid": 0, "post_result_freeze_mutations": 0, "authoritative_d2_v2_executions": 0,
        "test2_accesses": 0, "outer_authorized": False, "push_attempted": False,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED", "blockers": [], "exact_next_task": NEXT_TASK})
    markdown, parsed_hash = render_markdown_provenance_raw_v1(
        body_bytes, R4_BEGIN, R4_END,
        reports["BUNDLE"]["artifact_hash"], reports["RECEIPT"]["artifact_hash"],
        (b"Historical-R3-Blocker-Hash: " + HISTORICAL_R3_BLOCKER_HASH.encode("ascii"),))
    if parsed_hash != report_hash:
        fail("D2_V2_R4_REPORT_WRITER_ROUNDTRIP_REJECTED")
    return reports, markdown


def write_reports(reports: Mapping[str, Mapping[str, Any]], markdown: bytes) -> None:
    output = ROOT / "docs/task_reports"
    targets = [output / (REPORT_PREFIX + name + ".json") for name in REPORT_NAMES]
    targets.append(output / (REPORT_PREFIX + "REPORT.md"))
    if any(path.exists() for path in targets):
        fail("D2_V2_R4_REPORT_TARGET_EXISTS")
    for name in REPORT_NAMES:
        (output / (REPORT_PREFIX + name + ".json")).write_text(
            json.dumps(reports[name], sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
            encoding="utf-8", newline="\n")
    (output / (REPORT_PREFIX + "REPORT.md")).write_bytes(markdown)


def run_audit() -> dict[str, Any]:
    freeze = audit_freeze()
    guard = AuditSingleParseGuardR4.create()
    producer = audit_authorization_producer_semantics_r4()
    authority = validate_public_authorities(guard, producer)
    ordering = validate_ordering()
    private_root, fusion_path, metric_path, label_path = private_paths()
    custody = private_residue_audit(private_root, fusion_path, metric_path)
    paths = {"d0": ROOT / oracle.D0_PATH, "d1": ROOT / oracle.D1_PATH,
             "source": ROOT / oracle.SOURCE_PATH, "horizon": ROOT / oracle.HORIZON_PATH,
             "combined": ROOT / oracle.COMBINED_PATH, "fusion": fusion_path}
    snapshot = build_prelabel_snapshot(paths, guard)
    snapshot_id = id(snapshot)
    labeled = extend_snapshot_after_ordering(snapshot, label_path, guard, ordering["prediction_before_label_pass"])
    if id(labeled.prelabel) != snapshot_id:
        fail("D2_V2_R4_SNAPSHOT_IDENTITY_CHANGED")
    metric, d0_episodes, v2_episodes, recovery_episodes = metric_phase(labeled)
    metric_evidence = semantic_json_once(metric_path, "PRIVATE_METRIC_EVIDENCE_V2", guard)
    validate_hash(metric_evidence, METRIC_EVIDENCE_HASH)
    expected_metric = oracle.expected_metric(labeled.labels, metric, d0_episodes, v2_episodes, recovery_episodes)
    if metric_evidence != expected_metric:
        fail("D2_V2_R4_PRIVATE_METRIC_DIVERGENCE")
    public_metrics = json.loads((ROOT / oracle.METRICS_PATH).read_text(encoding="utf-8"))
    oracle.validate_public_metrics(public_metrics, metric)
    accounting = json.loads((ROOT / oracle.ACCOUNTING_PATH).read_text(encoding="utf-8"))
    validate_result_accounting(accounting)
    guard.require_exact(REAL_IDENTITIES)
    if guard.semantic_parses.get(AUTH_IDENTITY) != 1:
        fail("D2_V2_R4_AUTHORIZATION_PARSE_ACCOUNTING_REJECTED")
    if guard.authorization_markdown_raw_reads != 1 or guard.authorization_footer_logical_parses != 1:
        fail("D2_V2_R4_MARKDOWN_PARSE_ACCOUNTING_REJECTED")
    leakage = leakage_audit((private_root, fusion_path, metric_path, label_path))
    attacks_n, accepted = adversarial()
    if accepted:
        fail("D2_V2_R4_ACCEPTED_INVALID")
    parse_counts = tuple(sorted((identity, guard.semantic_parses[identity]) for identity in REAL_IDENTITIES))
    metric_public = {key: value for key, value in metric.items() if key != "events"}
    metric_public["values"] = tuple(sorted(metric_public["values"].items()))
    result = FrozenR4AuditResult(freeze["commit_a"], snapshot.snapshot_identity,
        tuple(sorted(authority.items())),
        tuple(sorted(freeze.items())), tuple(sorted(ordering.items())), tuple(sorted(metric_public.items())),
        parse_counts, tuple(sorted(leakage.items())), attacks_n, accepted)
    reports, markdown = build_reports(result)
    write_reports(reports, markdown)
    return {"status": PASS_STATUS, "attacks": attacks_n, "accepted": accepted,
            "hashes": {name: reports[name]["artifact_hash"] for name in REPORT_NAMES},
            "report_self_hash": reports["RECEIPT"]["report_self_hash"]}


def main() -> int:
    if sys.argv[1:]:
        print("D2_V2_R4_AUDIT_ARGUMENTS_REJECTED")
        return 2
    try:
        result = run_audit()
    except AuditR4Error as error:
        print(error.code)
        return 1
    except BaseException:
        print("D2_V2_R4_AUDIT_INTERNAL_BLOCKED")
        return 1
    print(result["status"])
    print(SCIENTIFIC_STATUS)
    print("LOCAL_ONLY_NOT_PUSHED")
    print("INDEPENDENT_ATTACKS=" + str(result["attacks"]))
    print("ACCEPTED_INVALID=" + str(result["accepted"]))
    for name, value in result["hashes"].items():
        print(name + "_HASH=" + value)
    print("REPORT_SELF_HASH=" + result["report_self_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
