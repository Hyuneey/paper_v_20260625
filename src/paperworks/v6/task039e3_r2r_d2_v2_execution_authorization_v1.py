"""One-shot authorization boundary for the frozen D2 V2 INNER arm.

This module performs authority and custody validation only.  It never parses
scientific prediction records or label values and never constructs evidence
tokens, fusion decisions, predictions, episodes, or metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, NoReturn
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as recovery_custody
from paperworks.v6.task039e3_r2r_d2_v2_design_v1 import (
    D2_V1_COMBINED_PREDICTION_HASH,
    D2_V1_DESIGN_HASH,
    D2_V2_DESIGN_HASH,
    D2_V2_FUSION_FAMILY,
    D2_V2_ID,
    D2_V2_NATIVE_HORIZON_MAP_HASH,
    D2_V2_PRIMARY_TARGET_MECHANISM,
    FROZEN_D0_PREDICTION_HASH,
    FROZEN_D1_PREDICTION_HASH,
    FROZEN_SOURCE_MAP_HASH,
    NATIVE_TEMPORAL_AUTHORITY_TYPE,
    REQUIRED_DISTINCT_SOURCE_COUNT,
    TOKEN_EXPIRY_POLICY,
    TOKEN_START_POLICY,
    TRIGGER_CLASSES,
    build_d2_v2_design_authority_v1,
    canonical_config_document_v1,
    resolve_native_horizon_map_from_frozen_authorities_v1,
    validate_d2_v2_config_v1,
    validate_d2_v2_design_authority_v1,
    validate_native_horizon_map_document_v1,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-EXECUTION-AUTHORIZATION-V1"
D2_V2_EXECUTION_AUTHORIZATION_VERSION = "TASK039E3_R2R_D2_V2_INNER_EXECUTION_AUTHORIZATION_V1"
D2_V2_EXECUTION_AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_D2_V2_NATIVE_HORIZON_CORROBORATION_INNER_V1"
AUTHORIZATION_STATUS = "AUTHORIZED_FOR_FUTURE_D2_V2_INNER_EXECUTION"
SYNTHETIC_CONTRACT_ONLY = "SYNTHETIC_CONTRACT_ONLY"
REAL_CUSTODY_PREFLIGHT = "REAL_V2_PRIVATE_AND_RAW_LABEL_CUSTODY_PREFLIGHT"

V2_PRIVATE_BINDING_KEY = "TASK039E3_D2_V2_PRIVATE_EVIDENCE_ROOT_V1"
V2_PRIVATE_BINDING_FILE = ".env.d2_v2_custody.local"
V2_PRIVATE_NAMESPACE = "TASK039E3_D2_V2_PRIVATE_EVIDENCE_V1"
V2_PRIVATE_FILENAMES = (
    "task039e3_inner_d2_v2_fusion_evidence_v1.json",
    "task039e3_inner_d2_v2_metric_evidence_v1.json",
)
PRIVATE_CUSTODY_INFRASTRUCTURE_IDENTITY = recovery_custody.RECOVERY_CUSTODY_MODULE_IDENTITY
EXPECTED_PRIVATE_CUSTODY_INFRASTRUCTURE_IDENTITY = (
    "c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6"
)

LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_BYTE_SIZE = 1242017
LABEL_ROWS = 54000
D0_PREDICTION_RECORD_COUNT = 54000
D1_PREDICTION_RECORD_COUNT = 6031
SOURCE_MAP_ENTRY_COUNT = 42
SOURCE_MAP_DISTINCT_SOURCE_COUNT = 9
D0_PRESERVATION_POLICY = "EVERY_FROZEN_D0_ALARM_IS_A_D2_V2_ALARM"
NATIVE_HORIZON_UNIT = "ONE_SECOND_UNITS"
FIXED_GLOBAL_TEMPORAL_WINDOW = None

PRIMARY_METRIC_IDENTITIES = (
    "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS",
    "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600",
)
INCREMENTAL_METRIC_IDENTITIES = (
    "D0_MISSED_ATTACK_EVENTS_RECOVERED_BY_RULE_RECOVERY_DIVIDED_BY_ALL_D0_MISSED_ATTACK_EVENTS",
    "D2_ATTACK_EVENT_RECALL_MINUS_D0_ATTACK_EVENT_RECALL",
    "RULE_RECOVERY_ALARM_EPISODES_WITH_ZERO_ATTACK_EVENT_OVERLAP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600",
    "D2_NORMAL_FAR_EPISODES_PER_HOUR_MINUS_D0_NORMAL_FAR_EPISODES_PER_HOUR",
)
FUTURE_EXECUTION_ORDER = (
    "REPLAY_D2_V2_AUTHORIZATION",
    "VALIDATE_D2_V2_DESIGN",
    "VALIDATE_D0_PREDICTION",
    "VALIDATE_D1_PREDICTION",
    "VALIDATE_SOURCE_MAP",
    "VALIDATE_NATIVE_HORIZON_MAP",
    "PARSE_D0_AND_D1_PREDICTIONS",
    "CREATE_CAUSAL_EVIDENCE_TOKENS",
    "DERIVE_ACTIVE_DISTINCT_SOURCE_SETS",
    "COMPUTE_D2_V2_FUSION",
    "FREEZE_PRIVATE_FUSION_EVIDENCE_V2",
    "FREEZE_COMBINED_PREDICTION_V2",
    "VALIDATE_AND_PARSE_LABEL_TEST1",
    "COMPUTE_FROZEN_METRICS",
    "FREEZE_RESULT",
    "STOP",
)

DESIGN_REPORT_HASHES: dict[str, str] = {
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_DESIGN.json": "cf68f4bb6a9eac5a717d3fd644a40a073478afc5c859dd6b41531192226fa8d0",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_INPUT_AUTHORITY.json": "28dbbaef220962c70efdab9a607d47459c07006c5cc580b4ebd1b72eb7c44a83",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_NATIVE_HORIZON_AUTHORITY.json": "14aa91ff3f976fd86eca09c379ff10096fa7aae424ed4f926421888664c5eb8e",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_EVIDENCE_TOKEN_POLICY.json": "19324935f972ccc842a47d230dcc8e7328cd595d4c5e4cfe78de62bb286d3f61",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_CORROBORATION_POLICY.json": "ff64bfe98d32920305e759b4cf198355dfd96d7d56b25e341128d921a84cb726",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_METRIC_POLICY.json": "90c09592c524578332d13868770d70e887e7078c37eafe72bf43dd84d441811b",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_PROVENANCE.json": "a81bbf793d3e27ec67184887fb72938df11c209d7c2c0627972c13e584105676",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_INDEPENDENT_AUDIT.json": "f613cad8feb501814c9a56fa912c4d7145491b83b81fcb2ce34cd17355ba866e",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_READINESS.json": "073df848a77991e7f6d0138d5e6978230c46358250348b00d39f7d4364c15707",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_BUNDLE.json": "4e44860a3e3357965ec1ac04f5817ceefe90f41fe01fe6b86dac47d64b23fa6e",
    "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_RECEIPT.json": "df98ca12e6a83c5ae9d73c80f7a26f0b1189a3743101d5342ed908017304dd7f",
}
DESIGN_REPORT_BODY_HASH = "b9378667241bd710251830bb8f6084abbf8fab5e04c4f755ef0939c261144c6c"
DESIGN_REPORT_BUNDLE_HASH = DESIGN_REPORT_HASHES["TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_BUNDLE.json"]
DESIGN_REPORT_RECEIPT_HASH = DESIGN_REPORT_HASHES["TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_RECEIPT.json"]

SANITIZED_FAILURE_CODES = frozenset({
    "D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED",
    "D2_V2_AUTHORIZATION_PROVENANCE_REJECTED",
    "D2_V2_AUTHORIZATION_PREDICTION_CUSTODY_REJECTED",
    "D2_V2_AUTHORIZATION_SOURCE_MAP_REJECTED",
    "D2_V2_AUTHORIZATION_BLOCKED_NATIVE_HORIZON_MAP_MISMATCH",
    "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ROOT_INVALID",
    "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_WRITE_DENIED",
    "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_TARGET_EXISTS",
    "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_SYMLINK_REJECTED",
    "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ATOMIC_RENAME_FAILED",
    "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_RESIDUE_DETECTED",
    "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_UNEXPECTED",
    "D2_V2_AUTHORIZATION_LABEL_CUSTODY_REJECTED",
    "D2_V2_AUTHORIZATION_LABEL_HASH_REJECTED",
    "D2_V2_AUTHORIZATION_PREFLIGHT_FACTORY_CUSTODY_REJECTED",
    "D2_V2_AUTHORIZATION_FACTORY_CUSTODY_REJECTED",
    "D2_V2_AUTHORIZATION_ALREADY_ISSUED",
    "D2_V2_AUTHORIZATION_PREFLIGHT_ALREADY_ATTEMPTED",
})


class D2V2ExecutionAuthorizationError(RuntimeError):
    """A fixed, path-free authorization failure."""

    def __init__(self, code: str) -> None:
        safe = code if code in SANITIZED_FAILURE_CODES else "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_UNEXPECTED"
        self.code = safe
        super().__init__(safe)

    def __repr__(self) -> str:
        return f"D2V2ExecutionAuthorizationError({self.code!r})"


def _fail(code: str) -> NoReturn:
    raise D2V2ExecutionAuthorizationError(code) from None


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if type(value) is not dict:
            _fail("D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED")
        return value
    except D2V2ExecutionAuthorizationError:
        raise
    except BaseException:
        _fail("D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED")


def _validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    payload = dict(document)
    observed = payload.pop("artifact_hash", None)
    if observed != expected or stable_hash_v1(payload) != expected:
        _fail("D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED")


def _validate_design_report_markdown() -> None:
    path = _root() / "docs" / "task_reports" / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_REPORT.md"
    try:
        text = path.read_text(encoding="utf-8")
        begin = "<!-- BEGIN D2 V2 DESIGN REPORT PROVENANCE V1 -->"
        end = "<!-- END D2 V2 DESIGN REPORT PROVENANCE V1 -->"
        if text.count(begin) != 1 or text.count(end) != 1:
            _fail("D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED")
        body, footer = text.split(begin, 1)
        canonical_body = body.rstrip() + "\n"
        if sha256(canonical_body.encode("utf-8")).hexdigest() != DESIGN_REPORT_BODY_HASH:
            _fail("D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED")
        required = (
            f"Report-Self-Hash: {DESIGN_REPORT_BODY_HASH}",
            f"Bundle-Hash: {DESIGN_REPORT_BUNDLE_HASH}",
            f"Receipt-Hash: {DESIGN_REPORT_RECEIPT_HASH}",
        )
        if not footer.rstrip().endswith(end) or any(item not in footer for item in required):
            _fail("D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED")
    except D2V2ExecutionAuthorizationError:
        raise
    except BaseException:
        _fail("D2_V2_AUTHORIZATION_PUBLIC_AUTHORITY_REJECTED")


@dataclass(frozen=True)
class D2V2PublicAuthorityReplayV1:
    authority_set_hash: str
    d2_v2_design_hash: str
    d2_v1_design_hash: str
    d2_v1_combined_prediction_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    native_horizon_map_hash: str
    provenance_hash: str
    report_hashes: tuple[tuple[str, str], ...]


def replay_required_d2_v2_public_authorities_v1() -> D2V2PublicAuthorityReplayV1:
    design = build_d2_v2_design_authority_v1()
    validate_d2_v2_design_authority_v1(design)
    validate_d2_v2_config_v1(canonical_config_document_v1())
    reports = _root() / "docs" / "task_reports"
    for name, expected in DESIGN_REPORT_HASHES.items():
        _validate_self_hash(_load_json(reports / name), expected)
    _validate_design_report_markdown()
    provenance = _load_json(reports / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_PROVENANCE.json")
    exact_provenance: dict[str, Any] = {
        "d2_v1_negative_result_known": True,
        "d2_v1_failure_diagnostic_known": True,
        "test1_labels_used_in_prior_diagnostic": True,
        "label_file_read_during_this_design_task": False,
        "test1_feature_read_during_design": False,
        "test2_read_during_design": False,
        "d2_v2_predictions_observed_before_freeze": False,
        "d2_v2_metrics_observed_before_freeze": False,
        "alternative_v2_policies_executed": 0,
        "hypothetical_performance_calculations": 0,
        "parameter_sweeps": 0,
        "new_fixed_temporal_window_selected": False,
    }
    if any(provenance.get(key) != value for key, value in exact_provenance.items()):
        _fail("D2_V2_AUTHORIZATION_PROVENANCE_REJECTED")
    hashes = tuple(sorted(DESIGN_REPORT_HASHES.items()))
    payload = {
        "d2_v2_design_hash": D2_V2_DESIGN_HASH,
        "d2_v1_design_hash": D2_V1_DESIGN_HASH,
        "d2_v1_combined_prediction_hash": D2_V1_COMBINED_PREDICTION_HASH,
        "d0_prediction_hash": FROZEN_D0_PREDICTION_HASH,
        "d1_prediction_hash": FROZEN_D1_PREDICTION_HASH,
        "source_map_hash": FROZEN_SOURCE_MAP_HASH,
        "native_horizon_map_hash": D2_V2_NATIVE_HORIZON_MAP_HASH,
        "provenance_hash": DESIGN_REPORT_HASHES["TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_PROVENANCE.json"],
        "report_hashes": hashes,
    }
    return D2V2PublicAuthorityReplayV1(stable_hash_v1(payload), *payload.values())


def _validate_prediction_artifact(name: str, expected_hash: str, expected_type: str,
                                  expected_count: int) -> None:
    document = _load_json(_root() / "docs" / "task_reports" / name)
    _validate_self_hash(document, expected_hash)
    declared = document.get("row_count") if expected_count == 54000 else document.get("counts", {}).get("evaluated_count")
    if (document.get("artifact_type") != expected_type or declared != expected_count
            or document.get("label_blind") is not True
            or document.get("labels_accessed_before_prediction_freeze") is not False):
        _fail("D2_V2_AUTHORIZATION_PREDICTION_CUSTODY_REJECTED")


@dataclass(frozen=True, repr=False)
class D2V2NativeHorizonAuthorityReceiptV1:
    artifact_type: str
    schema_version: str
    authority_type: str
    design_hash: str
    source_map_hash: str
    native_horizon_map_hash: str
    relation_count: int
    unique_relation_count: int
    missing_horizon_count: int
    ambiguous_horizon_count: int
    label_derived_horizon_count: int
    test1_derived_horizon_count: int
    horizon_unit: str
    token_start_policy: str
    token_expiry_policy: str
    backdating_allowed: bool
    future_information_allowed: bool
    fixed_global_temporal_window: int | None
    diagnostic_gap_used_as_parameter: bool
    artifact_hash: str

    def _payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if key != "artifact_hash"}

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}

    def __repr__(self) -> str:
        return "<D2V2NativeHorizonAuthorityReceiptV1 validated=True>"


_ISSUED_HORIZON_RECEIPTS: dict[int, tuple[weakref.ReferenceType[D2V2NativeHorizonAuthorityReceiptV1], str]] = {}


def _issue_horizon_receipt(value: D2V2NativeHorizonAuthorityReceiptV1) -> D2V2NativeHorizonAuthorityReceiptV1:
    oid = id(value)
    _ISSUED_HORIZON_RECEIPTS[oid] = (weakref.ref(value, lambda _: _ISSUED_HORIZON_RECEIPTS.pop(oid, None)), value.artifact_hash)
    return value


def build_d2_v2_native_horizon_authority_receipt_v1() -> D2V2NativeHorizonAuthorityReceiptV1:
    reports = _root() / "docs" / "task_reports"
    source_map = _load_json(reports / "TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json")
    _validate_self_hash(source_map, FROZEN_SOURCE_MAP_HASH)
    resolved = resolve_native_horizon_map_from_frozen_authorities_v1(
        _load_json(reports / "TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json"),
        _load_json(reports / "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json"),
        source_map,
    )
    validate_native_horizon_map_document_v1(resolved.to_public_dict())
    provisional = D2V2NativeHorizonAuthorityReceiptV1(
        "D2V2NativeHorizonAuthorityReceiptV1", "1.0.0", NATIVE_TEMPORAL_AUTHORITY_TYPE,
        D2_V2_DESIGN_HASH, FROZEN_SOURCE_MAP_HASH, resolved.map_hash, 42, 42, 0, 0, 0, 0,
        NATIVE_HORIZON_UNIT, TOKEN_START_POLICY, TOKEN_EXPIRY_POLICY, False, False,
        None, False, "",
    )
    return _issue_horizon_receipt(replace(provisional, artifact_hash=stable_hash_v1(provisional._payload())))


def validate_d2_v2_native_horizon_authority_receipt_v1(
    value: D2V2NativeHorizonAuthorityReceiptV1,
) -> str:
    issued = _ISSUED_HORIZON_RECEIPTS.get(id(value))
    if (type(value) is not D2V2NativeHorizonAuthorityReceiptV1 or issued is None
            or issued[0]() is not value or issued[1] != value.artifact_hash):
        _fail("D2_V2_AUTHORIZATION_BLOCKED_NATIVE_HORIZON_MAP_MISMATCH")
    expected = build_d2_v2_native_horizon_authority_receipt_v1()
    if value.to_public_dict() != expected.to_public_dict():
        _fail("D2_V2_AUTHORIZATION_BLOCKED_NATIVE_HORIZON_MAP_MISMATCH")
    return value.artifact_hash


def _sanitize_custody_exception_v1(error: BaseException) -> str:
    if isinstance(error, recovery_custody.D2RecoveryCustodyV1Error):
        mapping = {
            "D2_RECOVERY_PRIVATE_CUSTODY_ROOT_INVALID": "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ROOT_INVALID",
            "D2_RECOVERY_PRIVATE_CUSTODY_WRITE_DENIED": "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_WRITE_DENIED",
            "D2_RECOVERY_PRIVATE_CUSTODY_TARGET_EXISTS": "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_TARGET_EXISTS",
            "D2_RECOVERY_PRIVATE_CUSTODY_SYMLINK_REJECTED": "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_SYMLINK_REJECTED",
            "D2_RECOVERY_PRIVATE_CUSTODY_ATOMIC_RENAME_FAILED": "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ATOMIC_RENAME_FAILED",
            "D2_RECOVERY_PRIVATE_CUSTODY_RESIDUE_DETECTED": "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_RESIDUE_DETECTED",
        }
        return mapping.get(error.code, "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_UNEXPECTED")
    if isinstance(error, PermissionError):
        return "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_WRITE_DENIED"
    if isinstance(error, FileExistsError):
        return "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_TARGET_EXISTS"
    if isinstance(error, IsADirectoryError):
        return "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ROOT_INVALID"
    return "D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_UNEXPECTED"


def _raise_sanitized_custody_failure_v1(error: BaseException) -> NoReturn:
    _fail(_sanitize_custody_exception_v1(error))


def _binding_value(path: Path, key: str) -> Path:
    try:
        if path.is_symlink() or not path.is_file():
            _fail("D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ROOT_INVALID")
        matches: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([A-Z0-9_]+)='(.*)'", line)
            if match and match.group(1) == key:
                matches.append(match.group(2).replace("'\"'\"'", "'"))
        if len(matches) != 1:
            _fail("D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ROOT_INVALID")
        return Path(matches[0])
    except D2V2ExecutionAuthorizationError:
        raise
    except BaseException as error:
        _raise_sanitized_custody_failure_v1(error)


def initialize_local_d2_v2_private_binding_v1() -> str:
    """Bind V2's logical namespace to the already-approved recovery root."""

    try:
        root = recovery_custody.load_recovery_private_root_v1()
        approved = root._path.resolve(strict=True)
        binding = _root() / V2_PRIVATE_BINDING_FILE
        if binding.exists():
            configured = _binding_value(binding, V2_PRIVATE_BINDING_KEY).resolve(strict=True)
            if configured != approved:
                _fail("D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ROOT_INVALID")
            return "D2_V2_PRIVATE_BINDING_READY"
        if binding.is_symlink():
            _fail("D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_SYMLINK_REJECTED")
        temporary = binding.with_suffix(binding.suffix + ".tmp")
        if temporary.exists() or temporary.is_symlink():
            _fail("D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_TARGET_EXISTS")
        escaped = str(approved).replace("'", "'\"'\"'")
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(f"{V2_PRIVATE_BINDING_KEY}='{escaped}'\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, binding)
        return "D2_V2_PRIVATE_BINDING_READY"
    except D2V2ExecutionAuthorizationError:
        raise
    except BaseException as error:
        _raise_sanitized_custody_failure_v1(error)


def _validate_v2_private_binding_v1() -> recovery_custody.D2RecoveryPrivateRootV1:
    try:
        root = recovery_custody.load_recovery_private_root_v1()
        configured = _binding_value(_root() / V2_PRIVATE_BINDING_FILE, V2_PRIVATE_BINDING_KEY).resolve(strict=True)
        if configured != root._path.resolve(strict=True):
            _fail("D2_V2_AUTHORIZATION_PRIVATE_CUSTODY_ROOT_INVALID")
        return root
    except D2V2ExecutionAuthorizationError:
        raise
    except BaseException as error:
        _raise_sanitized_custody_failure_v1(error)


def _raw_label_hash_v1() -> str:
    try:
        binding = _root() / ".env.custody.local"
        root = _binding_value(binding, "HAI_DATA_ROOT")
        label = root / "hai-23.05" / "label-test1.csv"
        if (root.is_symlink() or not root.is_dir() or label.is_symlink()
                or not label.is_file() or label.stat().st_size != LABEL_BYTE_SIZE):
            _fail("D2_V2_AUTHORIZATION_LABEL_CUSTODY_REJECTED")
        digest = sha256()
        with label.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except D2V2ExecutionAuthorizationError:
        raise
    except BaseException:
        _fail("D2_V2_AUTHORIZATION_LABEL_CUSTODY_REJECTED")


@dataclass(frozen=True, repr=False)
class D2V2ExecutionCustodyPreflightReceiptV1:
    artifact_type: str
    schema_version: str
    authorization_version: str
    authorization_scope: str
    custody_mode: str
    public_authority_set_hash: str
    d2_v2_design_hash: str
    d2_v1_design_hash: str
    d2_v1_combined_prediction_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    native_horizon_receipt_hash: str
    native_horizon_map_hash: str
    recovery_custody_module_identity: str
    v2_private_namespace: str
    private_root_configured: bool
    private_root_writable: bool
    private_root_outside_git: bool
    private_root_symlink: bool
    permission_policy: str
    atomic_create: bool
    atomic_rename: bool
    private_reopen: bool
    sentinel_cleanup: bool
    residue_count: int
    path_redaction_pass: bool
    label_expected_hash: str
    label_hash_match: bool
    label_hash_reads: int
    label_scientific_parses: int
    d0_prediction_artifact_validations: int
    d1_prediction_artifact_validations: int
    source_map_validations: int
    native_horizon_map_validations: int
    scientific_d0_prediction_parses: int
    scientific_d1_prediction_parses: int
    evidence_token_constructions: int
    fusion_computations: int
    combined_prediction_v2_freezes: int
    metric_computations: int
    d0_executions: int
    d1_executions: int
    d2_v1_executions: int
    d2_v2_executions: int
    test1_feature_accesses: int
    test2_accesses: int
    outer_executions: int
    private_paths_exposed: int
    real_preflight_attempts: int
    real_preflight_retries: int
    artifact_hash: str
    _replay: D2V2PublicAuthorityReplayV1 = field(repr=False, compare=False)
    _horizon: D2V2NativeHorizonAuthorityReceiptV1 = field(repr=False, compare=False)
    _custody: recovery_custody.D2RecoveryCustodyPreflightReceiptV1 | None = field(repr=False, compare=False)

    def _payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items()
                if not key.startswith("_") and key != "artifact_hash"}

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}

    def __repr__(self) -> str:
        return "<D2V2ExecutionCustodyPreflightReceiptV1 validated=True private_path=REDACTED>"


_ISSUED_PREFLIGHTS: dict[int, tuple[weakref.ReferenceType[D2V2ExecutionCustodyPreflightReceiptV1], str]] = {}
_REAL_PREFLIGHT_ATTEMPTED = False


def _issue_preflight(value: D2V2ExecutionCustodyPreflightReceiptV1) -> D2V2ExecutionCustodyPreflightReceiptV1:
    oid = id(value)
    _ISSUED_PREFLIGHTS[oid] = (weakref.ref(value, lambda _: _ISSUED_PREFLIGHTS.pop(oid, None)), value.artifact_hash)
    return value


def _build_preflight(replay: D2V2PublicAuthorityReplayV1,
                     horizon: D2V2NativeHorizonAuthorityReceiptV1,
                     custody: recovery_custody.D2RecoveryCustodyPreflightReceiptV1 | None,
                     *, real: bool) -> D2V2ExecutionCustodyPreflightReceiptV1:
    enabled = real
    provisional = D2V2ExecutionCustodyPreflightReceiptV1(
        "D2V2ExecutionCustodyPreflightReceiptV1", "1.0.0",
        D2_V2_EXECUTION_AUTHORIZATION_VERSION, D2_V2_EXECUTION_AUTHORIZATION_SCOPE,
        REAL_CUSTODY_PREFLIGHT if real else SYNTHETIC_CONTRACT_ONLY,
        replay.authority_set_hash, D2_V2_DESIGN_HASH, D2_V1_DESIGN_HASH,
        D2_V1_COMBINED_PREDICTION_HASH, FROZEN_D0_PREDICTION_HASH,
        FROZEN_D1_PREDICTION_HASH, FROZEN_SOURCE_MAP_HASH, horizon.artifact_hash,
        D2_V2_NATIVE_HORIZON_MAP_HASH, PRIVATE_CUSTODY_INFRASTRUCTURE_IDENTITY,
        V2_PRIVATE_NAMESPACE, enabled, enabled, enabled, False,
        recovery_custody.PRIVATE_ROOT_PERMISSION_POLICY, enabled, enabled, enabled,
        enabled, 0, enabled, LABEL_SHA256, enabled, 1 if real else 0, 0,
        1 if real else 0, 1 if real else 0, 1 if real else 0, 1 if real else 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1 if real else 0, 0, "", replay, horizon, custody,
    )
    return replace(provisional, artifact_hash=stable_hash_v1(provisional._payload()))


def build_synthetic_d2_v2_execution_custody_preflight_receipt_v1() -> D2V2ExecutionCustodyPreflightReceiptV1:
    replay = replay_required_d2_v2_public_authorities_v1()
    horizon = build_d2_v2_native_horizon_authority_receipt_v1()
    return _issue_preflight(_build_preflight(replay, horizon, None, real=False))


def validate_d2_v2_execution_custody_preflight_receipt_v1(
    value: D2V2ExecutionCustodyPreflightReceiptV1, *, require_real: bool = False,
) -> str:
    issued = _ISSUED_PREFLIGHTS.get(id(value))
    if (type(value) is not D2V2ExecutionCustodyPreflightReceiptV1 or issued is None
            or issued[0]() is not value or issued[1] != value.artifact_hash):
        _fail("D2_V2_AUTHORIZATION_PREFLIGHT_FACTORY_CUSTODY_REJECTED")
    validate_d2_v2_native_horizon_authority_receipt_v1(value._horizon)
    real = value.custody_mode == REAL_CUSTODY_PREFLIGHT
    if real:
        if value._custody is None:
            _fail("D2_V2_AUTHORIZATION_PREFLIGHT_FACTORY_CUSTODY_REJECTED")
        recovery_custody.validate_d2_recovery_custody_preflight_v1(value._custody)
    expected = _build_preflight(value._replay, value._horizon, value._custody, real=real)
    if value.to_public_dict() != expected.to_public_dict() or (require_real and not real):
        _fail("D2_V2_AUTHORIZATION_PREFLIGHT_FACTORY_CUSTODY_REJECTED")
    return value.artifact_hash


def perform_d2_v2_execution_custody_preflight_v1() -> D2V2ExecutionCustodyPreflightReceiptV1:
    global _REAL_PREFLIGHT_ATTEMPTED
    if _REAL_PREFLIGHT_ATTEMPTED:
        _fail("D2_V2_AUTHORIZATION_PREFLIGHT_ALREADY_ATTEMPTED")
    _REAL_PREFLIGHT_ATTEMPTED = True
    replay = replay_required_d2_v2_public_authorities_v1()
    _validate_prediction_artifact(
        "TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json",
        FROZEN_D0_PREDICTION_HASH, "ScientificDetectorPredictionArtifactV1",
        D0_PREDICTION_RECORD_COUNT,
    )
    _validate_prediction_artifact(
        "TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json",
        FROZEN_D1_PREDICTION_HASH, "task039e3_r2r_scientific_rule_prediction_artifact_v1",
        D1_PREDICTION_RECORD_COUNT,
    )
    horizon = build_d2_v2_native_horizon_authority_receipt_v1()
    _validate_v2_private_binding_v1()
    try:
        custody = recovery_custody.perform_d2_recovery_custody_preflight_v1()
        recovery_custody.validate_d2_recovery_custody_preflight_v1(custody)
    except BaseException as error:
        _raise_sanitized_custody_failure_v1(error)
    if _raw_label_hash_v1() != LABEL_SHA256:
        _fail("D2_V2_AUTHORIZATION_LABEL_HASH_REJECTED")
    return _issue_preflight(_build_preflight(replay, horizon, custody, real=True))


@dataclass(frozen=True, repr=False)
class D2V2InnerExecutionAuthorizationV1:
    artifact_type: str
    schema_version: str
    task_id: str
    authorization_version: str
    authorization_scope: str
    authorization_status: str
    custody_preflight_hash: str
    d2_v2_id: str
    fusion_family: str
    design_hash: str
    d2_v1_design_hash: str
    d2_v1_combined_prediction_hash: str
    d0_prediction_hash: str
    d1_prediction_hash: str
    source_map_hash: str
    native_horizon_map_hash: str
    native_horizon_authority_type: str
    native_horizon_relation_count: int
    token_start_policy: str
    token_expiry_policy: str
    backdating_allowed: bool
    required_distinct_source_count: int
    single_source_fallback: bool
    fixed_global_temporal_window: int | None
    diagnostic_gap_used_as_parameter: bool
    d0_preservation_policy: str
    trigger_classes: tuple[str, ...]
    future_artifact_family: str
    future_record_count: int
    future_execution_order: tuple[str, ...]
    primary_metric_identities: tuple[str, ...]
    incremental_metric_identities: tuple[str, ...]
    d2_v2_inner_execution_authorized: bool
    d2_v2_combined_prediction_authorized: bool
    d0_prediction_consumption_authorized: bool
    d1_prediction_consumption_authorized: bool
    source_map_consumption_authorized: bool
    native_horizon_map_consumption_authorized: bool
    causal_evidence_token_construction_authorized: bool
    private_fusion_evidence_v2_authorized: bool
    label_metric_evaluation_authorized: bool
    label_before_combined_prediction_authorized: bool
    test1_feature_access_authorized: bool
    d0_rerun_authorized: bool
    d1_rerun_authorized: bool
    rule_reevaluation_authorized: bool
    d0_score_access_authorized: bool
    single_source_fallback_authorized: bool
    fixed_temporal_window_override_authorized: bool
    horizon_override_authorized: bool
    fusion_change_authorized: bool
    alternative_policy_search_authorized: bool
    test2_authorized: bool
    outer_authorized: bool
    result_driven_changes: bool
    authorization_hash: str
    _preflight: D2V2ExecutionCustodyPreflightReceiptV1 = field(repr=False, compare=False)

    def _payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items()
                if not key.startswith("_") and key != "authorization_hash"}

    def to_public_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.authorization_hash}

    def __repr__(self) -> str:
        return "<D2V2InnerExecutionAuthorizationV1 validated=True private_path=REDACTED>"


_ISSUED_AUTHORIZATIONS: dict[int, tuple[weakref.ReferenceType[D2V2InnerExecutionAuthorizationV1], str]] = {}
_REAL_AUTHORIZATION_ISSUED = False


def _build_authorization(preflight: D2V2ExecutionCustodyPreflightReceiptV1) -> D2V2InnerExecutionAuthorizationV1:
    real = preflight.custody_mode == REAL_CUSTODY_PREFLIGHT
    provisional = D2V2InnerExecutionAuthorizationV1(
        "D2V2InnerExecutionAuthorizationV1", "1.0.0", TASK_ID,
        D2_V2_EXECUTION_AUTHORIZATION_VERSION, D2_V2_EXECUTION_AUTHORIZATION_SCOPE,
        AUTHORIZATION_STATUS if real else SYNTHETIC_CONTRACT_ONLY,
        preflight.artifact_hash, D2_V2_ID, D2_V2_FUSION_FAMILY, D2_V2_DESIGN_HASH,
        D2_V1_DESIGN_HASH, D2_V1_COMBINED_PREDICTION_HASH, FROZEN_D0_PREDICTION_HASH,
        FROZEN_D1_PREDICTION_HASH, FROZEN_SOURCE_MAP_HASH,
        D2_V2_NATIVE_HORIZON_MAP_HASH, NATIVE_TEMPORAL_AUTHORITY_TYPE, 42,
        TOKEN_START_POLICY, TOKEN_EXPIRY_POLICY, False, REQUIRED_DISTINCT_SOURCE_COUNT,
        False, None, False, D0_PRESERVATION_POLICY, TRIGGER_CLASSES,
        "ScientificCombinedPredictionArtifactV2", 54000, FUTURE_EXECUTION_ORDER,
        PRIMARY_METRIC_IDENTITIES, INCREMENTAL_METRIC_IDENTITIES,
        real, real, real, real, real, real, real, real, real,
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, "", preflight,
    )
    return replace(provisional, authorization_hash=stable_hash_v1(provisional._payload()))


def _issue_authorization(value: D2V2InnerExecutionAuthorizationV1) -> D2V2InnerExecutionAuthorizationV1:
    oid = id(value)
    _ISSUED_AUTHORIZATIONS[oid] = (weakref.ref(value, lambda _: _ISSUED_AUTHORIZATIONS.pop(oid, None)), value.authorization_hash)
    return value


def issue_d2_v2_inner_execution_authorization_v1(
    preflight: D2V2ExecutionCustodyPreflightReceiptV1,
) -> D2V2InnerExecutionAuthorizationV1:
    global _REAL_AUTHORIZATION_ISSUED
    validate_d2_v2_execution_custody_preflight_receipt_v1(preflight)
    if preflight.custody_mode == REAL_CUSTODY_PREFLIGHT:
        if _REAL_AUTHORIZATION_ISSUED:
            _fail("D2_V2_AUTHORIZATION_ALREADY_ISSUED")
        _REAL_AUTHORIZATION_ISSUED = True
    return _issue_authorization(_build_authorization(preflight))


def validate_d2_v2_inner_execution_authorization_v1(
    value: D2V2InnerExecutionAuthorizationV1,
    preflight: D2V2ExecutionCustodyPreflightReceiptV1,
    *, require_real: bool = False,
) -> str:
    issued = _ISSUED_AUTHORIZATIONS.get(id(value))
    if (type(value) is not D2V2InnerExecutionAuthorizationV1 or issued is None
            or issued[0]() is not value or issued[1] != value.authorization_hash
            or value._preflight is not preflight):
        _fail("D2_V2_AUTHORIZATION_FACTORY_CUSTODY_REJECTED")
    validate_d2_v2_execution_custody_preflight_receipt_v1(preflight, require_real=require_real)
    expected = _build_authorization(preflight)
    if value.to_public_dict() != expected.to_public_dict():
        _fail("D2_V2_AUTHORIZATION_FACTORY_CUSTODY_REJECTED")
    if require_real and value.d2_v2_inner_execution_authorized is not True:
        _fail("D2_V2_AUTHORIZATION_FACTORY_CUSTODY_REJECTED")
    return value.authorization_hash


__all__ = [
    "D2V2ExecutionAuthorizationError",
    "D2V2ExecutionCustodyPreflightReceiptV1",
    "D2V2InnerExecutionAuthorizationV1",
    "D2V2NativeHorizonAuthorityReceiptV1",
    "D2_V2_EXECUTION_AUTHORIZATION_SCOPE",
    "D2_V2_EXECUTION_AUTHORIZATION_VERSION",
    "build_d2_v2_native_horizon_authority_receipt_v1",
    "build_synthetic_d2_v2_execution_custody_preflight_receipt_v1",
    "initialize_local_d2_v2_private_binding_v1",
    "issue_d2_v2_inner_execution_authorization_v1",
    "perform_d2_v2_execution_custody_preflight_v1",
    "replay_required_d2_v2_public_authorities_v1",
    "validate_d2_v2_execution_custody_preflight_receipt_v1",
    "validate_d2_v2_inner_execution_authorization_v1",
    "validate_d2_v2_native_horizon_authority_receipt_v1",
]
