"""Factory-custodied authorization for the first real INNER D1 utility run.

This module is an authorization boundary, not an execution bridge.  Its sole
real-data operation is a one-attempt custody preflight that hashes the exact
test1 files and validates the already materialized MAIN and supplement
registries.  It never parses CSV rows or labels, derives events, evaluates a
rule, computes a metric, or opens test2.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import task039e3_r2r_utility_evaluator_authority_v1 as evaluator_authority
from paperworks.v6 import task039e3_r2r_utility_normal_only_authority_v1 as main_authority
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-EXECUTION-AUTHORIZATION-V1"
AUTHORIZATION_VERSION = "TASK039E3_R2R_UTILITY_INNER_EXECUTION_AUTHORIZATION_V1"
AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_COMMON42_D1_RULE_ONLY_INNER_V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_execution_authorization_v1"
BLOCK_STATUS = "blocked_task039e3_r2r_utility_inner_execution_authorization_v1"

SYNTHETIC_CONTRACT_ONLY = "SYNTHETIC_CONTRACT_ONLY"
REAL_CUSTODY_PREFLIGHT = "REAL_CUSTODY_PREFLIGHT"
FUTURE_INNER_D1_RULE_ONLY = "FUTURE_INNER_D1_RULE_ONLY"

R3_IMPLEMENTATION_COMMIT = "429a00358ea7a3fba416f1e82652b41963fe707d"
R3_FREEZE_COMMIT = "25a87728a1b23f4a5ed862cc37a1be50aff260be"
R3_INDEPENDENT_AUDIT_COMMIT_A = "64a11a7f9c9cee6e6035d1deff2644af644c404d"
R3_INDEPENDENT_AUDIT_COMMIT_B = "1a961eadc4813acfc959580c0558f0bf33aa5c7c"
R3_COMPLETION_AUDIT_HASH = "2992599eed2d2205bd9e2192515dff47168386281da865c511fbadb1bf55a1a7"
R3_HARNESS_CORRECTION_RECEIPT_HASH = "4a7c8d558669fad79d439c4f6d1788b9615f848fdcb2b89e8f41534375e1eae1"
R3_INDEPENDENT_READINESS_HASH = "0cf12f2bf819d3662b88dd2c960445e59fcf7d09faa10d5679d8670495a56fa2"
R3_INDEPENDENT_BUNDLE_HASH = "c55cec5bac2fb8b700ae09beec521591e4be3ea9c8672bb8b213a41c26591035"
R3_INDEPENDENT_AUDIT_RECEIPT_HASH = "6f671aff17ea193ebf862af0739ee0bee22634f3f337944c14c90172acde34e0"
R3_IMPLEMENTATION_IDENTITY = "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"

EVALUATOR_AUTHORITY_BUNDLE_HASH = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"
V4_AUTHORITY_HASH = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
COMMON_PORTFOLIO = "COMMON-42"
COMMON_RELATION_COUNT = 42

MAIN_AUTHORITY_VERSION = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"
MAIN_DESCRIPTOR_HASH = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
MAIN_REFERENCE_SET_HASH = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
MAIN_REFERENCE_COUNT = 420
MAIN_PRIVATE_REGISTRY_HASH = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
MAIN_LOCATOR_HASH = "b5588c04d08d88d4ee2a2d319708e62d10bc04330baeb7591876f076270e4ac4"
MAIN_MATERIALIZED_AUDIT_RECEIPT_HASH = "1f319fd7283040a4e866df3ac7d679e896142162084209bf00962947256c2bf1"

SUPPLEMENT_AUTHORITY_VERSION = "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1"
SUPPLEMENT_PURPOSE = "CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY"
SUPPLEMENT_DESCRIPTOR_HASH = "d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927"
SUPPLEMENT_REFERENCE_SET_HASH = "5139cae6e454318f0ca4317f3f5eaa5f775bd4f75261c4110ea610815929b580"
SUPPLEMENT_REFERENCE_COUNT = 6
SUPPLEMENT_PRIVATE_REGISTRY_HASH = "12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf"
SUPPLEMENT_LOCATOR_HASH = "8c11872dca6a0c8b2544c2988dd57c969ddc036f51b04578d936fdc3a60757ac"

COMBINED_SOURCE_CENSUS_CONTRACT_HASH = "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
SOURCE_CENSUS_EVENT_POLICY_HASH = "3fb20068feff44632be3e4e6917183d52fea5616feec68ede5e9b62f95ecb390"
CROSS_SOURCE_ISOLATION_POLICY_HASH = "f62075523632a7573d28e95ca7f0402d87e62977f4a2f14f4eaf2b9a58f0e280"

DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
TEST1_FEATURE_FILENAME = "hai-test1.csv"
TEST1_FEATURE_SHA256 = "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
TEST1_LABEL_FILENAME = "label-test1.csv"
TEST1_LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
EXPECTED_PHYSICAL_RANGE = (0, 54000)
EXPECTED_LOGICAL_RANGE = (0, 54000)
EXPECTED_PHYSICAL_ROW_COUNT = 54000
VIRTUAL_PURGE_SECONDS = 120
UTILITY_EVENT_POLICY_HASH = "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4"
METRIC_POLICY_HASH = "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a"
RUNTIME_FEATURE_SCHEMA_COUNTS = (12, 10, 22)
COMMON_MATERIALIZATION_FOOTPRINT = (9, 10, 19)

HAI_DATA_ROOT_ENV = "HAI_DATA_ROOT"
MAIN_REGISTRY_ENV = main_authority.PRIVATE_LOCATOR_ENV
SUPPLEMENT_REGISTRY_ENV = supplement.PRIVATE_AUTHORITY_ENV
MAIN_LOCATOR_ENV = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1_LOCATOR"
SUPPLEMENT_LOCATOR_ENV = "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1_LOCATOR"

_AUDIT_FILES = {
    "completion": (
        "TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_COMPLETION_AUDIT.json",
        R3_COMPLETION_AUDIT_HASH,
    ),
    "harness": (
        "TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_HARNESS_CORRECTION_RECEIPT.json",
        R3_HARNESS_CORRECTION_RECEIPT_HASH,
    ),
    "readiness": (
        "TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_READINESS.json",
        R3_INDEPENDENT_READINESS_HASH,
    ),
    "bundle": (
        "TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_BUNDLE.json",
        R3_INDEPENDENT_BUNDLE_HASH,
    ),
    "receipt": (
        "TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_RECEIPT.json",
        R3_INDEPENDENT_AUDIT_RECEIPT_HASH,
    ),
}

_PUBLIC_V4_INPUTS = {
    "executable_equivalence": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json",
    "evidence_manifest": "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
    "dataset_manifest": "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json",
    "csv_structure_report": "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json",
    "c0_config": "configs/v6/task039c0_candidate_discovery_protocol.json",
    "br2_config": "configs/v6/task039br2_hai_continuous_step_feasibility.json",
    "materialized_audit_receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json",
}


class InnerExecutionAuthorizationV1Error(ValueError):
    """An exact authorization or custody invariant differs."""


def _repository_root_v1() -> Path:
    return Path(__file__).resolve(strict=True).parents[3]


def _load_public_self_hashed_v1(path: Path, expected_hash: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise InnerExecutionAuthorizationV1Error("required evaluator audit artifact is unavailable")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InnerExecutionAuthorizationV1Error(
            "required evaluator audit artifact is invalid"
        ) from exc
    if type(document) is not dict or document.get("artifact_hash") != expected_hash:
        raise InnerExecutionAuthorizationV1Error("required evaluator audit identity differs")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != expected_hash:
        raise InnerExecutionAuthorizationV1Error("required evaluator audit self-hash differs")
    return document


@dataclass(frozen=True)
class EvaluatorAuditReplayV1:
    completion_audit_hash: str
    harness_correction_receipt_hash: str
    readiness_hash: str
    bundle_hash: str
    independent_audit_receipt_hash: str
    implementation_identity: str
    independently_audited: bool
    full_independent_audit_completed: bool
    inner_execution_authorization_ready: bool


def replay_required_evaluator_audit_authority_v1() -> EvaluatorAuditReplayV1:
    """Replay the five tracked R3 authority artifacts without private access."""

    report_root = _repository_root_v1() / "docs" / "task_reports"
    documents = {
        key: _load_public_self_hashed_v1(report_root / filename, expected)
        for key, (filename, expected) in _AUDIT_FILES.items()
    }
    completion = documents["completion"]
    bundle = documents["bundle"]
    receipt = documents["receipt"]
    readiness = documents["readiness"]
    flags = readiness.get("flags")
    if (
        completion.get("r3_control", {}).get("implementation_identity")
        != R3_IMPLEMENTATION_IDENTITY
        or completion.get("lineage", {}).get("r3_implementation")
        != R3_IMPLEMENTATION_COMMIT
        or completion.get("lineage", {}).get("r3_freeze") != R3_FREEZE_COMMIT
        or completion.get("lineage", {}).get("audit_commit_a")
        != R3_INDEPENDENT_AUDIT_COMMIT_A
        or bundle.get("r3_implementation_commit") != R3_IMPLEMENTATION_COMMIT
        or bundle.get("r3_freeze_commit") != R3_FREEZE_COMMIT
        or bundle.get("audit_commit_a") != R3_INDEPENDENT_AUDIT_COMMIT_A
        or receipt.get("r3_implementation_identity") != R3_IMPLEMENTATION_IDENTITY
        or type(flags) is not dict
        or flags.get("UTILITY_EVALUATOR_V1_INDEPENDENTLY_AUDITED") is not True
        or flags.get("UTILITY_EVALUATOR_V1_FULL_INDEPENDENT_AUDIT_COMPLETED") is not True
        or flags.get("UTILITY_INNER_EXECUTION_AUTHORIZATION_READY") is not True
        or flags.get("UTILITY_OUTER_EXECUTION_AUTHORIZATION_READY") is not False
        or flags.get("REAL_UTILITY_EXECUTION_AUTHORIZED") is not False
    ):
        raise InnerExecutionAuthorizationV1Error("R3 evaluator audit replay differs")
    return EvaluatorAuditReplayV1(
        R3_COMPLETION_AUDIT_HASH,
        R3_HARNESS_CORRECTION_RECEIPT_HASH,
        R3_INDEPENDENT_READINESS_HASH,
        R3_INDEPENDENT_BUNDLE_HASH,
        R3_INDEPENDENT_AUDIT_RECEIPT_HASH,
        R3_IMPLEMENTATION_IDENTITY,
        True,
        True,
        True,
    )


@dataclass(frozen=True)
class InnerExecutionCustodyPreflightReceiptV1:
    authorization_version: str
    authorization_scope: str
    custody_mode: str
    sanitized_custody_identity: str
    main_locator_expected_hash: str
    main_locator_observed_hash: str
    main_locator_hash_match: bool
    main_registry_expected_hash: str
    main_registry_observed_hash: str
    main_registry_hash_match: bool
    supplement_locator_expected_hash: str
    supplement_locator_observed_hash: str
    supplement_locator_hash_match: bool
    supplement_registry_expected_hash: str
    supplement_registry_observed_hash: str
    supplement_registry_hash_match: bool
    test1_feature_expected_hash: str
    test1_feature_observed_hash: str
    test1_feature_hash_match: bool
    test1_label_expected_hash: str
    test1_label_observed_hash: str
    test1_label_hash_match: bool
    main_locator_reads: int
    main_registry_custody_validations: int
    supplement_locator_reads: int
    supplement_registry_custody_validations: int
    test1_feature_hash_passes: int
    test1_label_hash_passes: int
    test2_touched: bool
    scientific_parsing_performed: bool
    scientific_feature_parse_count: int
    scientific_label_parse_count: int
    attack_event_derivation_count: int
    rule_execution_count: int
    metric_computation_count: int
    detector_execution_count: int
    real_utility_computations: int
    private_numeric_values_exposed: int
    private_paths_exposed: int
    custody_preflight_hash: str

    def _payload(self) -> dict[str, object]:
        return {
            key: value
            for key, value in self.__dict__.items()
            if key != "custody_preflight_hash"
        }

    def to_public_dict(self) -> dict[str, object]:
        return {**self._payload(), "artifact_hash": self.custody_preflight_hash}


_ISSUED_PREFLIGHT_RECEIPTS: dict[
    int, tuple[weakref.ReferenceType[InnerExecutionCustodyPreflightReceiptV1], str, str, str]
] = {}


def _issue_preflight_receipt_v1(
    receipt: InnerExecutionCustodyPreflightReceiptV1,
) -> InnerExecutionCustodyPreflightReceiptV1:
    object_id = id(receipt)

    def cleanup(dead_ref: weakref.ReferenceType[InnerExecutionCustodyPreflightReceiptV1]) -> None:
        issued = _ISSUED_PREFLIGHT_RECEIPTS.get(object_id)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_PREFLIGHT_RECEIPTS.pop(object_id, None)

    receipt_ref = weakref.ref(receipt, cleanup)
    _ISSUED_PREFLIGHT_RECEIPTS[object_id] = (
        receipt_ref,
        receipt.custody_preflight_hash,
        receipt.custody_mode,
        receipt.sanitized_custody_identity,
    )
    return receipt


def _build_preflight_receipt_v1(*, custody_mode: str) -> InnerExecutionCustodyPreflightReceiptV1:
    if custody_mode not in {SYNTHETIC_CONTRACT_ONLY, REAL_CUSTODY_PREFLIGHT}:
        raise InnerExecutionAuthorizationV1Error("custody preflight mode differs")
    real = custody_mode == REAL_CUSTODY_PREFLIGHT
    read_count = 1 if real else 0
    sanitized_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_sanitized_custody_identity_v1",
            "authorization_scope": AUTHORIZATION_SCOPE,
            "main_locator": MAIN_LOCATOR_HASH,
            "main_registry": MAIN_PRIVATE_REGISTRY_HASH,
            "supplement_locator": SUPPLEMENT_LOCATOR_HASH,
            "supplement_registry": SUPPLEMENT_PRIVATE_REGISTRY_HASH,
            "test1_feature": TEST1_FEATURE_SHA256,
            "test1_label": TEST1_LABEL_SHA256,
            "test2_touched": False,
        }
    )
    provisional = InnerExecutionCustodyPreflightReceiptV1(
        AUTHORIZATION_VERSION,
        AUTHORIZATION_SCOPE,
        custody_mode,
        sanitized_identity,
        MAIN_LOCATOR_HASH,
        MAIN_LOCATOR_HASH,
        True,
        MAIN_PRIVATE_REGISTRY_HASH,
        MAIN_PRIVATE_REGISTRY_HASH,
        True,
        SUPPLEMENT_LOCATOR_HASH,
        SUPPLEMENT_LOCATOR_HASH,
        True,
        SUPPLEMENT_PRIVATE_REGISTRY_HASH,
        SUPPLEMENT_PRIVATE_REGISTRY_HASH,
        True,
        TEST1_FEATURE_SHA256,
        TEST1_FEATURE_SHA256,
        True,
        TEST1_LABEL_SHA256,
        TEST1_LABEL_SHA256,
        True,
        read_count,
        read_count,
        read_count,
        read_count,
        read_count,
        read_count,
        False,
        False,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "",
    )
    return replace(
        provisional,
        custody_preflight_hash=stable_hash_v1(provisional._payload()),
    )


def build_synthetic_inner_execution_custody_preflight_receipt_v1(
) -> InnerExecutionCustodyPreflightReceiptV1:
    """Issue a path-free mock receipt for static contract tests only."""

    return _issue_preflight_receipt_v1(
        _build_preflight_receipt_v1(custody_mode=SYNTHETIC_CONTRACT_ONLY)
    )


def validate_inner_execution_custody_preflight_receipt_v1(
    receipt: InnerExecutionCustodyPreflightReceiptV1,
    *,
    require_real: bool = False,
) -> str:
    if type(receipt) is not InnerExecutionCustodyPreflightReceiptV1:
        raise InnerExecutionAuthorizationV1Error("custody preflight receipt type differs")
    issued = _ISSUED_PREFLIGHT_RECEIPTS.get(id(receipt))
    if (
        issued is None
        or issued[0]() is not receipt
        or issued[1] != receipt.custody_preflight_hash
        or issued[2] != receipt.custody_mode
        or issued[3] != receipt.sanitized_custody_identity
    ):
        raise InnerExecutionAuthorizationV1Error("custody preflight factory issuance differs")
    expected = _build_preflight_receipt_v1(custody_mode=receipt.custody_mode)
    if receipt != expected or receipt.to_public_dict() != expected.to_public_dict():
        raise InnerExecutionAuthorizationV1Error("custody preflight semantic replay differs")
    if require_real and receipt.custody_mode != REAL_CUSTODY_PREFLIGHT:
        raise InnerExecutionAuthorizationV1Error("real custody preflight is required")
    return receipt.custody_preflight_hash


def _path_from_environment_v1(name: str) -> Path:
    value = os.environ.get(name)
    if type(value) is not str or not value:
        raise InnerExecutionAuthorizationV1Error("required custody environment binding is absent")
    return Path(value)


def _resolve_regular_file_v1(path: Path, *, repository_root: Path, outside_git: bool) -> Path:
    try:
        if path.is_symlink():
            raise InnerExecutionAuthorizationV1Error("custody file symlink substitution rejected")
        resolved = path.resolve(strict=True)
        if not resolved.is_file() or resolved.is_symlink():
            raise InnerExecutionAuthorizationV1Error("custody file is not a regular file")
        if outside_git and (resolved == repository_root or repository_root in resolved.parents):
            raise InnerExecutionAuthorizationV1Error("private custody file entered the repository")
        return resolved
    except OSError as exc:
        raise InnerExecutionAuthorizationV1Error("required custody file is unavailable") from exc


def _read_bytes_once_v1(path: Path) -> bytes:
    before = path.resolve(strict=True)
    try:
        with before.open("rb") as stream:
            content = stream.read()
    except OSError as exc:
        raise InnerExecutionAuthorizationV1Error("required custody file cannot be read") from exc
    after = path.resolve(strict=True)
    if before != after or path.is_symlink() or not after.is_file():
        raise InnerExecutionAuthorizationV1Error("custody file changed during validation")
    return content


def _json_from_custody_bytes_v1(content: bytes) -> dict[str, Any]:
    try:
        document = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InnerExecutionAuthorizationV1Error("custody JSON is invalid") from exc
    if type(document) is not dict:
        raise InnerExecutionAuthorizationV1Error("custody JSON must be an object")
    return document


_REAL_PREFLIGHT_ATTEMPTED = False


def perform_inner_execution_custody_preflight_v1(
) -> InnerExecutionCustodyPreflightReceiptV1:
    """Perform the sole bounded real custody preflight; never retry in-process."""

    global _REAL_PREFLIGHT_ATTEMPTED
    if _REAL_PREFLIGHT_ATTEMPTED:
        raise InnerExecutionAuthorizationV1Error("real custody preflight is single-attempt")
    _REAL_PREFLIGHT_ATTEMPTED = True
    try:
        repository_root = _repository_root_v1().resolve(strict=True)
        main_locator_path = _resolve_regular_file_v1(
            _path_from_environment_v1(MAIN_LOCATOR_ENV),
            repository_root=repository_root,
            outside_git=True,
        )
        main_registry_path = _resolve_regular_file_v1(
            _path_from_environment_v1(MAIN_REGISTRY_ENV),
            repository_root=repository_root,
            outside_git=True,
        )
        supplement_locator_path = _resolve_regular_file_v1(
            _path_from_environment_v1(SUPPLEMENT_LOCATOR_ENV),
            repository_root=repository_root,
            outside_git=True,
        )
        supplement_registry_path = _resolve_regular_file_v1(
            _path_from_environment_v1(SUPPLEMENT_REGISTRY_ENV),
            repository_root=repository_root,
            outside_git=True,
        )

        main_locator_document = _json_from_custody_bytes_v1(
            _read_bytes_once_v1(main_locator_path)
        )
        main_execution_authorization = (
            main_authority.load_committed_materialization_execution_authorization_r1(
                repository_root
            )
        )
        observed_main_locator = main_authority.validate_local_locator_manifest_v1(
            main_locator_document,
            repository_root=repository_root,
            execution_authorization=main_execution_authorization,
        )
        embedded_main_registry = _resolve_regular_file_v1(
            Path(str(main_locator_document.get("absolute_private_authority_path", ""))),
            repository_root=repository_root,
            outside_git=True,
        )
        if embedded_main_registry != main_registry_path:
            raise InnerExecutionAuthorizationV1Error("MAIN locator target differs")
        main_registry_bytes = _read_bytes_once_v1(main_registry_path)
        sha256(main_registry_bytes).hexdigest()
        observed_main_registry = main_authority.validate_private_registry_document_v1(
            _json_from_custody_bytes_v1(main_registry_bytes),
            main_authority.build_common42_authority_v1(),
        )

        supplement_locator_document = _json_from_custody_bytes_v1(
            _read_bytes_once_v1(supplement_locator_path)
        )
        observed_supplement_locator = supplement.validate_local_locator_document_v1(
            supplement_locator_document,
            repository_root=repository_root,
        )
        embedded_supplement_registry = _resolve_regular_file_v1(
            Path(str(supplement_locator_document.get("absolute_private_authority_path", ""))),
            repository_root=repository_root,
            outside_git=True,
        )
        if embedded_supplement_registry != supplement_registry_path:
            raise InnerExecutionAuthorizationV1Error("supplement locator target differs")
        supplement_registry_bytes = _read_bytes_once_v1(supplement_registry_path)
        sha256(supplement_registry_bytes).hexdigest()
        observed_supplement_registry = (
            supplement.validate_supplement_private_registry_document_v1(
                _json_from_custody_bytes_v1(supplement_registry_bytes)
            )
        )

        data_root = _path_from_environment_v1(HAI_DATA_ROOT_ENV)
        if data_root.is_symlink():
            raise InnerExecutionAuthorizationV1Error("HAI data root symlink rejected")
        data_root = data_root.resolve(strict=True)
        if not data_root.is_dir():
            raise InnerExecutionAuthorizationV1Error("HAI data root is unavailable")
        test1_root = data_root / "hai-23.05"
        feature_path = _resolve_regular_file_v1(
            test1_root / TEST1_FEATURE_FILENAME,
            repository_root=repository_root,
            outside_git=False,
        )
        label_path = _resolve_regular_file_v1(
            test1_root / TEST1_LABEL_FILENAME,
            repository_root=repository_root,
            outside_git=False,
        )
        observed_feature_hash = sha256(_read_bytes_once_v1(feature_path)).hexdigest()
        observed_label_hash = sha256(_read_bytes_once_v1(label_path)).hexdigest()

        observed = (
            observed_main_locator,
            observed_main_registry,
            observed_supplement_locator,
            observed_supplement_registry,
            observed_feature_hash,
            observed_label_hash,
        )
        expected = (
            MAIN_LOCATOR_HASH,
            MAIN_PRIVATE_REGISTRY_HASH,
            SUPPLEMENT_LOCATOR_HASH,
            SUPPLEMENT_PRIVATE_REGISTRY_HASH,
            TEST1_FEATURE_SHA256,
            TEST1_LABEL_SHA256,
        )
        if observed != expected:
            raise InnerExecutionAuthorizationV1Error("one or more custody identities differ")
    except InnerExecutionAuthorizationV1Error:
        raise
    except Exception as exc:
        raise InnerExecutionAuthorizationV1Error("custody preflight failed closed") from exc
    return _issue_preflight_receipt_v1(
        _build_preflight_receipt_v1(custody_mode=REAL_CUSTODY_PREFLIGHT)
    )


@dataclass(frozen=True)
class InnerExecutionAuthorizationV1:
    authorization_version: str
    authorization_scope: str
    authorization_status: str
    r3_implementation_identity: str
    r3_independent_audit_receipt_hash: str
    r3_completion_audit_hash: str
    evaluator_authority_bundle_hash: str
    v4_authority_hash: str
    common_portfolio: str
    common_relation_count: int
    t2_authorized: bool
    main_authority_version: str
    main_descriptor_hash: str
    main_reference_set_hash: str
    main_private_registry_expected_hash: str
    main_locator_expected_hash: str
    supplement_authority_version: str
    supplement_purpose: str
    supplement_descriptor_hash: str
    supplement_reference_set_hash: str
    supplement_private_registry_expected_hash: str
    supplement_locator_expected_hash: str
    combined_source_census_contract_hash: str
    source_census_event_policy_hash: str
    cross_source_isolation_policy_hash: str
    dataset_manifest_id: str
    inner_split_id: str
    feature_filename: str
    feature_sha256: str
    label_filename: str
    label_sha256: str
    expected_physical_range: tuple[int, int]
    expected_logical_range: tuple[int, int]
    expected_physical_row_count: int
    virtual_purge_seconds: int
    purge_policy_hash: str
    utility_event_policy_hash: str
    metric_policy_hash: str
    runtime_feature_schema_counts: tuple[int, int, int]
    common_materialization_footprint: tuple[int, int, int]
    execution_mode: str
    experiment_arm: str
    d0_authorized: bool
    d1_authorized: bool
    d2_authorized: bool
    detector_authorized: bool
    outer_authorized: bool
    fusion_authorized: bool
    threshold_recalibration_authorized: bool
    rule_regeneration_authorized: bool
    metric_modification_authorized: bool
    test2_authorized: bool
    custody_preflight_hash: str
    utility_evaluator_v1_independently_audited: bool
    utility_evaluator_v1_full_independent_audit_completed: bool
    utility_inner_execution_authorization_ready: bool
    utility_inner_execution_authorized: bool
    utility_inner_d1_execution_authorization_issued: bool
    utility_inner_d1_executed: bool
    utility_outer_execution_authorization_ready: bool
    utility_outer_execution_authorized: bool
    real_utility_execution_authorized: bool
    authorization_hash: str
    _preflight_receipt: InnerExecutionCustodyPreflightReceiptV1 = field(
        repr=False, compare=False
    )
    _evaluator_bundle: evaluator_authority.EvaluatorAuthorityBundleV1 = field(
        repr=False, compare=False
    )
    _implementation_authority: evaluator_authority.EvaluatorImplementationAuthorityV1 = field(
        repr=False, compare=False
    )

    def _payload(self) -> dict[str, object]:
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_") and key != "authorization_hash"
        }

    def to_public_dict(self) -> dict[str, object]:
        return {**self._payload(), "artifact_hash": self.authorization_hash}


_ISSUED_AUTHORIZATIONS: dict[
    int,
    tuple[
        weakref.ReferenceType[InnerExecutionAuthorizationV1],
        str,
        weakref.ReferenceType[InnerExecutionCustodyPreflightReceiptV1],
        str,
        weakref.ReferenceType[evaluator_authority.EvaluatorAuthorityBundleV1],
        weakref.ReferenceType[evaluator_authority.EvaluatorImplementationAuthorityV1],
        str,
        str,
        str,
    ],
] = {}
_REAL_AUTHORIZATION_ISSUED = False


def _build_current_evaluator_authorities_v1() -> tuple[
    evaluator_authority.EvaluatorAuthorityBundleV1,
    evaluator_authority.EvaluatorImplementationAuthorityV1,
]:
    repository_root = _repository_root_v1()
    try:
        public_inputs = {
            name: json.loads((repository_root / relative).read_text(encoding="utf-8"))
            for name, relative in _PUBLIC_V4_INPUTS.items()
        }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InnerExecutionAuthorizationV1Error(
            "canonical public V4 inputs are unavailable"
        ) from exc
    canonical_v4 = v4.build_utility_protocol_v4_canonical_authority(**public_inputs)
    bundle = evaluator_authority.build_evaluator_authority_bundle_v1(canonical_v4)
    implementation = evaluator_authority.build_evaluator_implementation_authority_v1(bundle)
    if (
        bundle.bundle_hash != EVALUATOR_AUTHORITY_BUNDLE_HASH
        or implementation.implementation_identity != R3_IMPLEMENTATION_IDENTITY
        or evaluator_authority.CURRENT_EVALUATOR_IMPLEMENTATION_IDENTITY
        != R3_IMPLEMENTATION_IDENTITY
    ):
        raise InnerExecutionAuthorizationV1Error("current evaluator authority differs")
    return bundle, implementation


def _build_expected_authorization_v1(
    receipt: InnerExecutionCustodyPreflightReceiptV1,
    bundle: evaluator_authority.EvaluatorAuthorityBundleV1,
    implementation: evaluator_authority.EvaluatorImplementationAuthorityV1,
) -> InnerExecutionAuthorizationV1:
    real = receipt.custody_mode == REAL_CUSTODY_PREFLIGHT
    mode = FUTURE_INNER_D1_RULE_ONLY if real else SYNTHETIC_CONTRACT_ONLY
    provisional = InnerExecutionAuthorizationV1(
        AUTHORIZATION_VERSION,
        AUTHORIZATION_SCOPE,
        PASS_STATUS if real else "synthetic_contract_only",
        R3_IMPLEMENTATION_IDENTITY,
        R3_INDEPENDENT_AUDIT_RECEIPT_HASH,
        R3_COMPLETION_AUDIT_HASH,
        EVALUATOR_AUTHORITY_BUNDLE_HASH,
        V4_AUTHORITY_HASH,
        COMMON_PORTFOLIO,
        COMMON_RELATION_COUNT,
        False,
        MAIN_AUTHORITY_VERSION,
        MAIN_DESCRIPTOR_HASH,
        MAIN_REFERENCE_SET_HASH,
        MAIN_PRIVATE_REGISTRY_HASH,
        MAIN_LOCATOR_HASH,
        SUPPLEMENT_AUTHORITY_VERSION,
        SUPPLEMENT_PURPOSE,
        SUPPLEMENT_DESCRIPTOR_HASH,
        SUPPLEMENT_REFERENCE_SET_HASH,
        SUPPLEMENT_PRIVATE_REGISTRY_HASH,
        SUPPLEMENT_LOCATOR_HASH,
        COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
        SOURCE_CENSUS_EVENT_POLICY_HASH,
        CROSS_SOURCE_ISOLATION_POLICY_HASH,
        DATASET_MANIFEST_ID,
        INNER_SPLIT_ID,
        TEST1_FEATURE_FILENAME,
        TEST1_FEATURE_SHA256,
        TEST1_LABEL_FILENAME,
        TEST1_LABEL_SHA256,
        EXPECTED_PHYSICAL_RANGE,
        EXPECTED_LOGICAL_RANGE,
        EXPECTED_PHYSICAL_ROW_COUNT,
        VIRTUAL_PURGE_SECONDS,
        v4.PURGE_POLICY_HASH,
        UTILITY_EVENT_POLICY_HASH,
        METRIC_POLICY_HASH,
        RUNTIME_FEATURE_SCHEMA_COUNTS,
        COMMON_MATERIALIZATION_FOOTPRINT,
        mode,
        "D1",
        False,
        real,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        receipt.custody_preflight_hash,
        True,
        True,
        True,
        real,
        real,
        False,
        False,
        False,
        False,
        "",
        receipt,
        bundle,
        implementation,
    )
    return replace(
        provisional,
        authorization_hash=stable_hash_v1(provisional._payload()),
    )


def _issue_authorization_custody_v1(
    authorization: InnerExecutionAuthorizationV1,
) -> InnerExecutionAuthorizationV1:
    object_id = id(authorization)

    def cleanup(dead_ref: object) -> None:
        issued = _ISSUED_AUTHORIZATIONS.get(object_id)
        if issued is not None and any(ref is dead_ref for ref in (issued[0], issued[2], issued[4], issued[5])):
            _ISSUED_AUTHORIZATIONS.pop(object_id, None)

    authorization_ref = weakref.ref(authorization, cleanup)
    receipt_ref = weakref.ref(authorization._preflight_receipt, cleanup)
    bundle_ref = weakref.ref(authorization._evaluator_bundle, cleanup)
    implementation_ref = weakref.ref(authorization._implementation_authority, cleanup)
    _ISSUED_AUTHORIZATIONS[object_id] = (
        authorization_ref,
        authorization.authorization_hash,
        receipt_ref,
        authorization.custody_preflight_hash,
        bundle_ref,
        implementation_ref,
        authorization.r3_independent_audit_receipt_hash,
        authorization.dataset_manifest_id,
        authorization.inner_split_id,
    )
    return authorization


def issue_inner_execution_authorization_v1(
    receipt: InnerExecutionCustodyPreflightReceiptV1,
) -> InnerExecutionAuthorizationV1:
    """Issue one real authorization, or a non-scientific synthetic test object."""

    global _REAL_AUTHORIZATION_ISSUED
    validate_inner_execution_custody_preflight_receipt_v1(receipt)
    replay_required_evaluator_audit_authority_v1()
    if receipt.custody_mode == REAL_CUSTODY_PREFLIGHT:
        if _REAL_AUTHORIZATION_ISSUED:
            raise InnerExecutionAuthorizationV1Error("real INNER D1 authorization already issued")
        _REAL_AUTHORIZATION_ISSUED = True
    bundle, implementation = _build_current_evaluator_authorities_v1()
    return _issue_authorization_custody_v1(
        _build_expected_authorization_v1(receipt, bundle, implementation)
    )


def validate_inner_execution_authorization_v1(
    authorization: InnerExecutionAuthorizationV1,
    receipt: InnerExecutionCustodyPreflightReceiptV1,
    *,
    require_real: bool = False,
) -> str:
    if type(authorization) is not InnerExecutionAuthorizationV1:
        raise InnerExecutionAuthorizationV1Error("INNER authorization type differs")
    issued = _ISSUED_AUTHORIZATIONS.get(id(authorization))
    if (
        issued is None
        or issued[0]() is not authorization
        or issued[1] != authorization.authorization_hash
        or issued[2]() is not receipt
        or issued[3] != receipt.custody_preflight_hash
        or issued[4]() is not authorization._evaluator_bundle
        or issued[5]() is not authorization._implementation_authority
        or issued[6] != R3_INDEPENDENT_AUDIT_RECEIPT_HASH
        or issued[7] != DATASET_MANIFEST_ID
        or issued[8] != INNER_SPLIT_ID
    ):
        raise InnerExecutionAuthorizationV1Error("INNER authorization factory issuance differs")
    validate_inner_execution_custody_preflight_receipt_v1(receipt, require_real=require_real)
    replay_required_evaluator_audit_authority_v1()
    evaluator_authority.validate_evaluator_authority_bundle_v1(
        authorization._evaluator_bundle
    )
    evaluator_authority.validate_evaluator_implementation_authority_v1(
        authorization._implementation_authority,
        authorization._evaluator_bundle,
    )
    if authorization._preflight_receipt is not receipt:
        raise InnerExecutionAuthorizationV1Error("authorization preflight custody differs")
    expected = _build_expected_authorization_v1(
        receipt,
        authorization._evaluator_bundle,
        authorization._implementation_authority,
    )
    if authorization != expected or authorization.to_public_dict() != expected.to_public_dict():
        raise InnerExecutionAuthorizationV1Error("INNER authorization semantic replay differs")
    if require_real and (
        authorization.execution_mode != FUTURE_INNER_D1_RULE_ONLY
        or authorization.utility_inner_execution_authorized is not True
        or authorization.utility_inner_d1_execution_authorization_issued is not True
        or authorization.d1_authorized is not True
    ):
        raise InnerExecutionAuthorizationV1Error("real INNER D1 authorization is required")
    return authorization.authorization_hash


__all__ = [
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_VERSION",
    "BLOCK_STATUS",
    "COMMON_RELATION_COUNT",
    "DATASET_MANIFEST_ID",
    "EXPECTED_PHYSICAL_ROW_COUNT",
    "FUTURE_INNER_D1_RULE_ONLY",
    "INNER_SPLIT_ID",
    "InnerExecutionAuthorizationV1",
    "InnerExecutionAuthorizationV1Error",
    "InnerExecutionCustodyPreflightReceiptV1",
    "MAIN_LOCATOR_ENV",
    "PASS_STATUS",
    "R3_IMPLEMENTATION_IDENTITY",
    "R3_INDEPENDENT_AUDIT_RECEIPT_HASH",
    "SUPPLEMENT_LOCATOR_ENV",
    "SYNTHETIC_CONTRACT_ONLY",
    "TEST1_FEATURE_SHA256",
    "TEST1_LABEL_SHA256",
    "build_synthetic_inner_execution_custody_preflight_receipt_v1",
    "issue_inner_execution_authorization_v1",
    "perform_inner_execution_custody_preflight_v1",
    "replay_required_evaluator_audit_authority_v1",
    "validate_inner_execution_authorization_v1",
    "validate_inner_execution_custody_preflight_receipt_v1",
]
