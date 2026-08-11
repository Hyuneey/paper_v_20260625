"""TASK-039D1 arm-blind normal relation fit profiling.

The scientific entry point in this module consumes only the frozen
``ProfilingIdentityViewV1`` and the two authorized fit-file value maps.  Arm
provenance is deliberately handled by a separate post-freeze function.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
from array import array
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar, Mapping, MutableMapping, Sequence

from paperworks.data.contracts_v2 import DatasetManifestV2
from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    freeze_json,
    reject_unknown_fields,
    require_finite,
    require_sha256,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    BR1_PROTOCOL_BUNDLE_HASH,
    CANDIDATE_COHORT_HASH,
    CANDIDATE_IDENTITY_LIST_HASH,
    DATASET_MANIFEST_HASH,
    FIT_FILES,
    FROZEN_SOURCES,
    FROZEN_SOURCE_ROLES,
    FROZEN_TARGETS,
    HORIZONS,
    PROCESS_ID,
    RELATION_FAMILY,
    CandidateProvenanceAnalysisViewV1,
    ProfilingIdentityViewV1,
    RelationProfilingProtocolError,
    assert_arm_blind_identity_record_v1,
    authorize_br2_reference_v1,
    authorize_value_access_v1,
    classify_all_source_isolation_v1,
    derive_multi_file_source_parameters_v1,
    derive_multi_file_target_scale_v1,
    extract_file_local_events_v1,
    rank_direction_horizon_v1,
    selected_fit_gate_v1,
    verify_self_hash_v1,
)


TASK_ID = "TASK-039D1"
STATUS = "passed_task039d1_normal_relation_fit_profiling"
BASE_COMMIT = "c622c082c053176eab170b6176a343eb2cb35384"
BRANCH = "task-039d1-relation-fit-profiling"
D0_CONFIG_HASH = "92358db70576e944f003f983f03ee1f9f20475b8d92efbce4590d17e92d95faf"
D0_PROTOCOL_BUNDLE_HASH = "888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb"
D1_AUTHORIZATION_HASH = "e3ec4316d26520efe4a93d1bf790f36633ed692fa5f9fb9458c26d2a9ad16467"
PROFILING_IDENTITY_VIEW_HASH = "ec1186ec71c20f240c6fb1c7f4b7cd0054882ac8032f6bfb3940274e772f5b7e"
PROVENANCE_ANALYSIS_VIEW_HASH = "7ab92318611dd7d0252c763c4099a7ee69f3dbab3132308254aeb92f8af2e115"

SOURCE_SCALE_POLICY_HASH = "47831757a6f66e0c860a0589391f610aa99213291278861a8c5f260a7fe54233"
SOURCE_EVENT_POLICY_HASH = "1f07a72b380b9ffb2ceb42e029517ef42716145062a57b1770d118b9db252342"
TARGET_RESPONSE_POLICY_HASH = "4b007b9511152396e03722ad8ce0e9cf659ebef2760cef5110414e4ce4bcbeaf"
DIRECTION_SELECTION_POLICY_HASH = "0026c57f83502f67b1a0d055b22eec42ac08e05eeb6709ffe9cb55ee28d5839b"
FIT_GATE_POLICY_HASH = "da2442ad641aa035c37e738bd8a20521f3e5b46a1801f02fee8dbdcba3520344"
CONFIRMATION_POLICY_HASH = "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"
METHOD_COMPARISON_POLICY_HASH = "0ccc7a97a5e9b3fe1e5a8a54828ec8f8f7e6482c62eb63f7df62d804c8cae39e"
NUMERIC_EVIDENCE_POLICY_HASH = "2cdc0b12724f549a165d7fad870b69b602d4eb0c2e0006dcd1780c88c2b8fcbc"

AUTHORIZED_RELATIVE_FILES = (
    "hai-23.05/hai-train1.csv",
    "hai-23.05/hai-train2.csv",
)
SELECTED_COLUMNS = FROZEN_SOURCES + FROZEN_TARGETS
SELECTED_COLUMN_HASH = stable_hash_v1({"columns": list(SELECTED_COLUMNS)})
SOURCE_DIRECTIONS = ("step_up", "step_down")
TARGET_DIRECTIONS = ("increase", "decrease")

RESULT_PATH_NAMES = (
    "TASK-039D1_DATA_ACCESS_AUDIT.json",
    "TASK-039D1_PAIR_FIT_SUMMARY.json",
    "TASK-039D1_FIT_RESULT.json",
    "TASK-039D1_ARM_FIT_SUMMARY.json",
    "TASK-039D1_EXECUTION_RECEIPT.json",
    "TASK-039D1_REPORT.md",
)

PRIVATE_SOURCE_LEDGER_NAME = "TASK-039D1_SOURCE_PARAMETER_LEDGER.json"
PRIVATE_TARGET_LEDGER_NAME = "TASK-039D1_TARGET_PARAMETER_LEDGER.json"
PRIVATE_DIRECTIONAL_LEDGER_NAME = "TASK-039D1_DIRECTIONAL_FIT_LEDGER.json"

_ABSOLUTE_WINDOWS = re.compile(r"^[A-Za-z]:[\\/]")
_PUBLIC_NUMERIC_KEYS = frozenset(
    {
        "source_noise_scale",
        "source_step_threshold",
        "source_stability_tolerance",
        "target_noise_scale",
        "median_response",
        "robust_effect_ratio",
        "direction_selection_candidates",
        "event_index",
        "event_timestamps",
        "raw_values",
        "raw_windows",
    }
)


class TASK039D1Error(ValueError):
    """Raised when D1 execution or a D1 result contract fails closed."""


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = thaw_json(freeze_json(content))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def verify_d1_self_hash_v1(document: Mapping[str, Any]) -> str:
    supplied = document.get("artifact_hash")
    require_sha256(str(supplied), "artifact_hash")
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    observed = stable_hash_v1(content)
    if supplied != observed:
        raise TASK039D1Error("artifact_hash does not match content")
    return observed


@dataclass(frozen=True)
class _D1Artifact:
    payload: Mapping[str, Any]
    ARTIFACT_TYPE: ClassVar[str] = ""
    PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        try:
            reject_unknown_fields(self.payload, self.PAYLOAD_FIELDS, self.ARTIFACT_TYPE)
        except V6FoundationError as exc:
            raise TASK039D1Error(str(exc)) from exc
        missing = self.PAYLOAD_FIELDS - set(self.payload)
        if missing:
            raise TASK039D1Error(f"{self.ARTIFACT_TYPE} missing fields: {sorted(missing)}")
        object.__setattr__(self, "payload", freeze_json(self.payload))
        self._validate()

    def _validate(self) -> None:
        value = thaw_json(self.payload)
        kind = self.ARTIFACT_TYPE
        if kind.endswith("ledger_binding_v1"):
            require_sha256(value["ledger_hash"], "ledger_hash")
            if value["storage_boundary"] != "outside_git" or value["private_contents_public"]:
                raise TASK039D1Error("private-ledger binding exceeds public boundary")
        elif kind == "task039d1_pair_fit_summary_v1":
            _validate_pair_summary(value)
        elif kind == "task039d1_fit_result_v1":
            if value["status"] != STATUS or value["candidate_count"] != 47:
                raise TASK039D1Error("D1 fit-result identity is invalid")
            if value["directional_opportunity_count"] != 94:
                raise TASK039D1Error("D1 directional count is invalid")
            if value["task039d2_authorized"] or value["rule_v2_authorized"]:
                raise TASK039D1Error("D1 result exceeds its authority")
            if value["candidate_arm_evidence_visible_to_profiler"]:
                raise TASK039D1Error("D1 result violates arm blindness")
            if value["lower_ranked_fallback_used"] or value["merged_cross_arm_score_used"]:
                raise TASK039D1Error("D1 result violates no-fallback/unscored policy")
        elif kind == "task039d1_arm_fit_summary_v1":
            arms = value["arms"]
            if [item["arm"] for item in arms] != ["META", "STAT", "GDN"]:
                raise TASK039D1Error("D1 arm-summary order is invalid")
            if any(item["top20_pair_count"] != 20 for item in arms):
                raise TASK039D1Error("D1 arm summary must use frozen top20")
            if value["winner_selected"] or not value["same_pair_same_d1_outcome_across_all_origin_arms"]:
                raise TASK039D1Error("D1 arm-summary claim/invariance is invalid")
        elif kind == "task039d1_data_access_audit_v1":
            if not value["train1_accessed"] or not value["train2_accessed"]:
                raise TASK039D1Error("D1 authorized fit files were not both accessed")
            forbidden = (
                "train3_accessed", "train4_accessed", "test_accessed",
                "labels_accessed", "attacks_accessed", "p2_p3_p4_values_accessed",
                "br2_pair_results_accessed", "candidate_arm_evidence_visible_during_profiling",
                "raw_values_persisted", "raw_windows_persisted",
                "event_timestamps_publicly_persisted", "absolute_local_paths_persisted",
            )
            if any(value[name] for name in forbidden) or value["prohibited_access_count"] != 0:
                raise TASK039D1Error("D1 data boundary was violated")
        elif kind == "task039d1_execution_receipt_v1":
            if value["status"] != STATUS or value["execution_code_commit"] == BASE_COMMIT:
                raise TASK039D1Error("D1 execution receipt has invalid lineage")
            if not value["outcomes_frozen_before_provenance_join"]:
                raise TASK039D1Error("D1 provenance join occurred too early")
            if value["scientific_code_changed_after_first_value_read"]:
                raise TASK039D1Error("D1 scientific source changed after execution")
            if value["task039d2_authorized"] or value["rule_v2_authorized"]:
                raise TASK039D1Error("D1 execution receipt exceeds its authority")

    def _content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            **thaw_json(self.payload),
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content(), "artifact_hash": self.artifact_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "_D1Artifact":
        allowed = cls.PAYLOAD_FIELDS | {"schema_version", "artifact_type", "artifact_hash"}
        reject_unknown_fields(data, allowed, cls.ARTIFACT_TYPE)
        if data.get("schema_version") != V6_FOUNDATION_SCHEMA_VERSION:
            raise TASK039D1Error("schema_version must be 1.0.0")
        if data.get("artifact_type") != cls.ARTIFACT_TYPE:
            raise TASK039D1Error("artifact_type mismatch")
        result = cls({key: data[key] for key in cls.PAYLOAD_FIELDS})
        if data.get("artifact_hash") != result.artifact_hash:
            raise TASK039D1Error("artifact_hash mismatch")
        return result


def _artifact_class(name: str, artifact_type: str, fields: Sequence[str]) -> type[_D1Artifact]:
    return type(
        name,
        (_D1Artifact,),
        {"ARTIFACT_TYPE": artifact_type, "PAYLOAD_FIELDS": frozenset(fields)},
    )


TASK039D1SourceParameterLedgerBindingV1 = _artifact_class(
    "TASK039D1SourceParameterLedgerBindingV1",
    "task039d1_source_parameter_ledger_binding_v1",
    ("record_count", "ledger_hash", "storage_boundary", "private_contents_public"),
)
TASK039D1TargetParameterLedgerBindingV1 = _artifact_class(
    "TASK039D1TargetParameterLedgerBindingV1",
    "task039d1_target_parameter_ledger_binding_v1",
    ("record_count", "ledger_hash", "storage_boundary", "private_contents_public"),
)
TASK039D1DirectionalFitLedgerBindingV1 = _artifact_class(
    "TASK039D1DirectionalFitLedgerBindingV1",
    "task039d1_directional_fit_ledger_binding_v1",
    ("record_count", "ledger_hash", "storage_boundary", "private_contents_public"),
)
TASK039D1PairFitSummaryV1 = _artifact_class(
    "TASK039D1PairFitSummaryV1",
    "task039d1_pair_fit_summary_v1",
    (
        "task_id", "status", "d0_protocol_bundle_hash", "candidate_cohort_hash",
        "profiling_identity_view_hash", "candidate_count", "directional_opportunity_count",
        "pair_fit_supported_count", "pair_fit_unsupported_count",
        "directional_status_counts", "pair_outcomes", "lower_ranked_fallback_used",
        "candidate_arm_evidence_visible_to_profiler",
    ),
)
TASK039D1FitResultV1 = _artifact_class(
    "TASK039D1FitResultV1",
    "task039d1_fit_result_v1",
    (
        "task_id", "status", "d0_protocol_bundle_hash", "d1_authorization_hash",
        "candidate_cohort_hash", "candidate_identity_list_hash", "candidate_count",
        "directional_opportunity_count", "source_parameter_record_count",
        "source_parameter_supported_count", "source_parameter_unsupported_count",
        "target_parameter_record_count", "pair_fit_supported_count",
        "pair_fit_unsupported_count", "directional_fit_supported_count",
        "direction_unstable_count", "fit_unsupported_directional_count",
        "other_failure_counts", "source_ledger_binding", "target_ledger_binding",
        "directional_ledger_binding", "pair_summary_hash", "data_access_audit_hash",
        "candidate_arm_evidence_visible_to_profiler", "lower_ranked_fallback_used",
        "merged_cross_arm_score_used", "numeric_parameter_class",
        "construction_confirmed", "rule_authority", "runtime_authority",
        "task039d2_authorized", "rule_v2_authorized", "claim_boundary",
    ),
)
TASK039D1ArmFitSummaryV1 = _artifact_class(
    "TASK039D1ArmFitSummaryV1",
    "task039d1_arm_fit_summary_v1",
    (
        "task_id", "status", "pair_summary_hash", "provenance_analysis_view_hash",
        "primary_k", "arms", "same_pair_same_d1_outcome_across_all_origin_arms",
        "scientific_profiles_per_unique_pair", "provenance_joined_after_outcomes_frozen",
        "d2_confirmation_metrics_calculated", "winner_selected", "claim_boundary",
    ),
)
TASK039D1DataAccessAuditV1 = _artifact_class(
    "TASK039D1DataAccessAuditV1",
    "task039d1_data_access_audit_v1",
    (
        "task_id", "status", "dataset_manifest_id", "process", "authorized_files",
        "file_records", "selected_column_hash", "selected_column_count",
        "file_open_count", "feature_read_pass_count", "train1_accessed",
        "train2_accessed", "train3_accessed", "train4_accessed", "test_accessed",
        "labels_accessed", "attacks_accessed", "p2_p3_p4_values_accessed",
        "br2_pair_results_accessed", "candidate_arm_evidence_visible_during_profiling",
        "raw_values_persisted", "raw_windows_persisted",
        "event_timestamps_publicly_persisted", "absolute_local_paths_persisted",
        "timestamp_values_persisted", "timestamp_header_structural_verification_only",
        "prohibited_access_count",
    ),
)
TASK039D1ExecutionReceiptV1 = _artifact_class(
    "TASK039D1ExecutionReceiptV1",
    "task039d1_execution_receipt_v1",
    (
        "task_id", "status", "execution_code_commit", "base_commit",
        "d0_config_hash", "d0_protocol_bundle_hash", "d1_authorization_hash",
        "component_policy_hashes", "candidate_cohort_hash", "candidate_identity_list_hash",
        "profiling_identity_view_hash", "provenance_analysis_view_hash",
        "dataset_manifest_hash", "br1_protocol_bundle_hash", "scientific_source_hashes",
        "execution_phase_order", "outcomes_frozen_before_provenance_join",
        "scientific_code_changed_after_first_value_read", "source_ledger_binding_hash",
        "target_ledger_binding_hash", "directional_ledger_binding_hash",
        "pair_summary_hash", "fit_result_hash", "arm_fit_summary_hash",
        "data_access_audit_hash", "candidate_count", "directional_opportunity_count",
        "lower_ranked_fallback_used", "candidate_arm_evidence_visible_to_profiler",
        "br2_pair_results_accessed", "merged_cross_arm_score_used",
        "train3_accessed", "train4_accessed", "test_labels_attacks_accessed",
        "task039d2_authorized", "rule_v2_authorized", "recommended_next_task",
    ),
)

ARTIFACT_CLASSES: tuple[type[_D1Artifact], ...] = (
    TASK039D1SourceParameterLedgerBindingV1,
    TASK039D1TargetParameterLedgerBindingV1,
    TASK039D1DirectionalFitLedgerBindingV1,
    TASK039D1PairFitSummaryV1,
    TASK039D1FitResultV1,
    TASK039D1ArmFitSummaryV1,
    TASK039D1DataAccessAuditV1,
    TASK039D1ExecutionReceiptV1,
)
ARTIFACT_CLASS_BY_TYPE = {item.ARTIFACT_TYPE: item for item in ARTIFACT_CLASSES}


def _validate_pair_summary(value: Mapping[str, Any]) -> None:
    if value["task_id"] != TASK_ID or value["candidate_count"] != 47:
        raise TASK039D1Error("pair summary identity is invalid")
    if value["directional_opportunity_count"] != 94:
        raise TASK039D1Error("pair summary directional count is invalid")
    outcomes = value["pair_outcomes"]
    pairs = [(item["source"], item["target"]) for item in outcomes]
    if len(pairs) != 47 or len(set(pairs)) != 47:
        raise TASK039D1Error("pair summary must contain 47 unique pairs")
    allowed_directional = {"fit_supported", "fit_unsupported", "direction_unstable"}
    for item in outcomes:
        if set(item) != {"source", "target", "step_up_status", "step_down_status", "pair_fit_status"}:
            raise TASK039D1Error("pair outcome fields are not closed")
        if item["step_up_status"] not in allowed_directional or item["step_down_status"] not in allowed_directional:
            raise TASK039D1Error("directional fit status is invalid")
        supported = "fit_supported" in {item["step_up_status"], item["step_down_status"]}
        expected = "fit_supported_pair" if supported else "fit_unsupported_pair"
        if item["pair_fit_status"] != expected:
            raise TASK039D1Error("pair aggregation is inconsistent")
    supported_count = sum(item["pair_fit_status"] == "fit_supported_pair" for item in outcomes)
    if value["pair_fit_supported_count"] != supported_count or value["pair_fit_unsupported_count"] != 47 - supported_count:
        raise TASK039D1Error("pair summary counts do not match records")
    if value["lower_ranked_fallback_used"] or value["candidate_arm_evidence_visible_to_profiler"]:
        raise TASK039D1Error("pair summary violates protocol boundary")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039D1Error(f"required public artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039D1Error(f"public artifact must be an object: {path.name}")
    return value


def write_json_v1(path: Path, document: Mapping[str, Any], *, public: bool) -> None:
    if public:
        assert_public_payload_safe_v1(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(thaw_json(freeze_json(document)), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def assert_public_payload_safe_v1(value: Any, *, key: str | None = None) -> None:
    if key in _PUBLIC_NUMERIC_KEYS:
        raise TASK039D1Error(f"private numeric/event field entered public artifact: {key}")
    if isinstance(value, Mapping):
        for item_key, item in value.items():
            assert_public_payload_safe_v1(item, key=str(item_key))
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_safe_v1(item, key=key)
        return
    if isinstance(value, str):
        if _ABSOLUTE_WINDOWS.match(value) or value.startswith("/") or "\\Users\\" in value:
            raise TASK039D1Error("absolute local path entered public artifact")


def validate_external_roots_v1(
    *, repository_root: Path, data_root_value: str, private_root_value: str
) -> tuple[Path, Path]:
    for label, raw in (("HAI_DATA_ROOT", data_root_value), ("TASK039D_PRIVATE_ROOT", private_root_value)):
        if not raw or ".." in Path(raw).parts:
            raise TASK039D1Error(f"{label} must be an explicit traversal-free path")
    repository = repository_root.resolve(strict=True)
    data_root = Path(data_root_value).resolve(strict=True)
    private_candidate = Path(private_root_value)
    private_root = private_candidate.resolve(strict=private_candidate.exists())
    if data_root == private_root:
        raise TASK039D1Error("data and private roots must be distinct")
    if data_root.is_relative_to(repository) or private_root.is_relative_to(repository):
        raise TASK039D1Error("external roots must remain outside the Git repository")
    if repository.is_relative_to(data_root) or repository.is_relative_to(private_root):
        raise TASK039D1Error("external roots may not contain the Git repository")
    return data_root, private_root


@dataclass
class DataAccessStateV1:
    prohibited_access_count: int = 0
    file_open_count: int = 0
    feature_read_pass_count: int = 0
    train1_accessed: bool = False
    train2_accessed: bool = False

    def authorize(self, relative_path: str, columns: Sequence[str]) -> None:
        normalized = PurePosixPath(relative_path).as_posix()
        expected_columns = tuple(columns)
        try:
            if normalized != relative_path or PurePosixPath(relative_path).is_absolute():
                raise TASK039D1Error("relative data path is not normalized")
            if relative_path not in AUTHORIZED_RELATIVE_FILES:
                raise TASK039D1Error("failed_task039d1_data_boundary")
            authorize_value_access_v1(
                task_id=TASK_ID,
                relative_file=PurePosixPath(relative_path).name,
            )
            if expected_columns != SELECTED_COLUMNS:
                raise TASK039D1Error("D1 may read only the frozen 24 P1 columns")
        except (TASK039D1Error, RelationProfilingProtocolError) as exc:
            self.prohibited_access_count += 1
            raise TASK039D1Error("failed_task039d1_data_boundary") from exc


def reject_br2_pair_input_v1(*, artifact_name: str, purpose: str = "scientific_input") -> None:
    try:
        authorize_br2_reference_v1(purpose=purpose, artifact_name=artifact_name)
    except RelationProfilingProtocolError as exc:
        raise TASK039D1Error("failed_task039d1_data_boundary") from exc


def load_expected_file_identities_v1(repository_root: Path) -> tuple[dict[str, Any], ...]:
    manifest_document = _load_json(repository_root / "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json")
    structure_document = _load_json(repository_root / "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json")
    verify_self_hash_v1(manifest_document)
    if manifest_document["artifact_hash"] != DATASET_MANIFEST_HASH:
        raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
    report_hash = structure_document.get("report_hash")
    report_content = {key: value for key, value in structure_document.items() if key != "report_hash"}
    if report_hash != stable_hash_v1(report_content):
        raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
    try:
        manifest = DatasetManifestV2.from_dict(manifest_document)
    except (KeyError, TypeError, ValueError) as exc:
        raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch") from exc
    if manifest.manifest_id != DATASET_MANIFEST_HASH or manifest.nominal_sampling_interval_seconds != 1.0:
        raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
    manifest_files = {item.relative_local_path: item for item in manifest.files}
    structure_files = {item["relative_path"]: item for item in structure_document["records"]}
    result: list[dict[str, Any]] = []
    for relative in AUTHORIZED_RELATIVE_FILES:
        manifest_item = manifest_files.get(relative)
        structure_item = structure_files.get(relative)
        if (
            manifest_item is None
            or structure_item is None
            or manifest_item.logical_file_role != "normal_train_time_series"
            or manifest_item.label_availability != "unavailable"
            or manifest_item.provenance_status != "verified"
            or manifest_item.sha256 != structure_item.get("file_sha256")
            or manifest_item.byte_size != structure_item.get("byte_size")
            or manifest_item.row_count != structure_item.get("row_count")
            or structure_item.get("header_sha256") != "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"
            or structure_item.get("normal_file_status") != "normal_only_verified"
            or structure_item.get("timestamp_field") != "timestamp"
            or structure_item.get("ordered_header_matches_canonical") is not True
        ):
            raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
        result.append(
            {
                "relative_path": relative,
                "sha256": manifest_item.sha256,
                "byte_size": manifest_item.byte_size,
                "row_count": manifest_item.row_count,
                "header_sha256": structure_item["header_sha256"],
            }
        )
    return tuple(result)


def _stream_sha256(path: Path, state: DataAccessStateV1) -> str:
    digest = hashlib.sha256()
    state.file_open_count += 1
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_selected_columns(
    path: Path,
    *,
    expected: Mapping[str, Any],
    state: DataAccessStateV1,
) -> tuple[dict[str, array], dict[str, Any]]:
    observed_size = path.stat().st_size
    observed_sha = _stream_sha256(path, state)
    if observed_size != expected["byte_size"] or observed_sha != expected["sha256"]:
        raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
    values = {name: array("d") for name in SELECTED_COLUMNS}
    state.file_open_count += 1
    state.feature_read_pass_count += 1
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = tuple(next(reader))
        except StopIteration as exc:
            raise TASK039D1Error("authorized HAI CSV is empty") from exc
        raw_header = ",".join(header).encode("utf-8")
        header_hash = hashlib.sha256(raw_header).hexdigest()
        if header_hash != expected["header_sha256"] or len(header) != len(set(header)):
            raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
        if not header or header[0] != "timestamp" or any(name not in header for name in SELECTED_COLUMNS):
            raise TASK039D1Error("failed_task039d1_data_boundary")
        indexes = tuple((name, header.index(name)) for name in SELECTED_COLUMNS)
        row_count = 0
        for row in reader:
            if len(row) != len(header):
                raise TASK039D1Error("authorized HAI CSV contains malformed row")
            row_count += 1
            for name, index in indexes:
                try:
                    numeric = float(row[index])
                except ValueError as exc:
                    raise TASK039D1Error("authorized P1 value is not numeric") from exc
                if not math.isfinite(numeric):
                    raise TASK039D1Error("authorized P1 value is not finite")
                values[name].append(numeric)
    if row_count != expected["row_count"]:
        raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
    return values, {
        "relative_path": expected["relative_path"],
        "sha256": observed_sha,
        "byte_size": observed_size,
        "row_count": row_count,
        "header_sha256": header_hash,
        "file_identity_match": True,
        "header_identity_match": True,
    }


def load_authorized_fit_values_v1(
    *,
    data_root: Path,
    expected_file_identities: Sequence[Mapping[str, Any]],
    state: DataAccessStateV1,
) -> tuple[dict[str, dict[str, array]], tuple[dict[str, Any], ...]]:
    if tuple(item["relative_path"] for item in expected_file_identities) != AUTHORIZED_RELATIVE_FILES:
        raise TASK039D1Error("blocked_task039d1_dataset_identity_mismatch")
    result: dict[str, dict[str, array]] = {}
    file_records: list[dict[str, Any]] = []
    root = data_root.resolve(strict=True)
    for expected in expected_file_identities:
        relative = str(expected["relative_path"])
        state.authorize(relative, SELECTED_COLUMNS)
        path = (root / PurePosixPath(relative)).resolve(strict=True)
        if not path.is_relative_to(root):
            state.prohibited_access_count += 1
            raise TASK039D1Error("failed_task039d1_data_boundary")
        values, record = _read_selected_columns(path, expected=expected, state=state)
        short_name = PurePosixPath(relative).name
        result[short_name] = values
        file_records.append(record)
        if short_name == FIT_FILES[0]:
            state.train1_accessed = True
        elif short_name == FIT_FILES[1]:
            state.train2_accessed = True
    if set(result) != set(FIT_FILES):
        raise TASK039D1Error("failed_task039d1_data_boundary")
    return result, tuple(file_records)


def optimized_target_response_v1(
    values: Sequence[float], *, event_index: int, horizon_seconds: int,
) -> tuple[bool, float | None]:
    """Evaluate the frozen response formula on an already validated sequence.

    Unlike the older public helper, this function does not make a full tuple
    copy for every event.  Synthetic parity tests bind it to the accepted
    scalar helper before HAI execution.
    """

    if horizon_seconds not in HORIZONS:
        raise TASK039D1Error("response horizon is not frozen")
    if event_index < 5 or event_index + horizon_seconds + 3 > len(values):
        return True, None
    baseline = float(statistics.median(values[event_index - 5:event_index]))
    response_level = float(
        statistics.median(values[event_index + horizon_seconds:event_index + horizon_seconds + 3])
    )
    response = response_level - baseline
    if not math.isfinite(response):
        raise TASK039D1Error("target response is not finite")
    return False, response


def _direction_statistics(
    *,
    target_values: Mapping[str, Sequence[float]],
    classified_events: Mapping[str, Sequence[tuple[Any, bool]]],
    source_direction: str,
    target_noise_scale: float,
    horizon: int,
    target_direction: str,
) -> dict[str, Any]:
    pooled_responses: list[float] = []
    file_stats: dict[str, dict[str, Any]] = {}
    for file_name in FIT_FILES:
        events = [
            event for event, isolated in classified_events[file_name]
            if isolated and event.direction == source_direction
        ]
        responses: list[float] = []
        censored = 0
        for event in events:
            right_censored, response = optimized_target_response_v1(
                target_values[file_name],
                event_index=event.event_index,
                horizon_seconds=horizon,
            )
            if right_censored:
                censored += 1
            else:
                assert response is not None
                responses.append(response)
        increase_matches = sum(response > target_noise_scale for response in responses)
        decrease_matches = sum(response < -target_noise_scale for response in responses)
        selected_matches = increase_matches if target_direction == "increase" else decrease_matches
        opposite_matches = decrease_matches if target_direction == "increase" else increase_matches
        usable = len(responses)
        file_stats[file_name] = {
            "usable_response_count": usable,
            "right_censored_count": censored,
            "directional_match_count": selected_matches,
            "opposite_direction_match_count": opposite_matches,
            "selected_directional_consistency": selected_matches / usable if usable else 0.0,
            "opposite_directional_consistency": opposite_matches / usable if usable else 0.0,
        }
        pooled_responses.extend(responses)
    total_usable = len(pooled_responses)
    total_matches = sum(file_stats[name]["directional_match_count"] for name in FIT_FILES)
    median_response = float(statistics.median(pooled_responses)) if pooled_responses else None
    robust_effect = abs(median_response) / target_noise_scale if median_response is not None else 0.0
    return {
        "target_direction": target_direction,
        "horizon_seconds": horizon,
        "train1": file_stats[FIT_FILES[0]],
        "train2": file_stats[FIT_FILES[1]],
        "total_usable_responses": total_usable,
        "pooled_directional_consistency": total_matches / total_usable if total_usable else 0.0,
        "pooled_median_response": median_response,
        "pooled_robust_effect_ratio": robust_effect,
    }


def _selection_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "target_direction": record["target_direction"],
        "horizon_seconds": record["horizon_seconds"],
        "pooled_directional_consistency": record["pooled_directional_consistency"],
        "pooled_robust_effect_ratio": record["pooled_robust_effect_ratio"],
        "train1_selected_consistency": record["train1"]["selected_directional_consistency"],
        "train1_opposite_consistency": record["train1"]["opposite_directional_consistency"],
        "train2_selected_consistency": record["train2"]["selected_directional_consistency"],
        "train2_opposite_consistency": record["train2"]["opposite_directional_consistency"],
    }


def _record_hash(record: Mapping[str, Any]) -> dict[str, Any]:
    return _self_hashed(record)


def _private_ledger(
    artifact_type: str,
    records: Sequence[Mapping[str, Any]],
    *,
    execution_code_commit: str,
) -> dict[str, Any]:
    return _self_hashed(
        {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": artifact_type,
            "task_id": TASK_ID,
            "execution_code_commit": execution_code_commit,
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "record_count": len(records),
            "records": list(records),
            "raw_hai_rows_included": False,
            "raw_windows_included": False,
            "event_timestamps_included": False,
            "attack_test_label_information_included": False,
            "absolute_paths_included": False,
        }
    )


def evaluate_arm_blind_fit_v1(
    *,
    identity_view_document: Mapping[str, Any],
    fit_values: Mapping[str, Mapping[str, Sequence[float]]],
    fit_file_bindings: Mapping[str, str],
    execution_code_commit: str,
) -> dict[str, Any]:
    """Evaluate all 47 pairs exactly once without loading arm provenance."""

    verify_self_hash_v1(identity_view_document)
    if identity_view_document.get("artifact_hash") != PROFILING_IDENTITY_VIEW_HASH:
        raise TASK039D1Error("blocked_task039d1_authorization_mismatch")
    view = ProfilingIdentityViewV1.from_dict(identity_view_document)
    identities = list(view.to_dict()["candidates"])
    if len(identities) != 47:
        raise TASK039D1Error("blocked_task039d1_cohort_identity_mismatch")
    for record in identities:
        assert_arm_blind_identity_record_v1(record)
    if set(fit_values) != set(FIT_FILES):
        raise TASK039D1Error("failed_task039d1_data_boundary")
    if set(fit_file_bindings) != set(FIT_FILES):
        raise TASK039D1Error("fit file bindings are incomplete")
    for digest in fit_file_bindings.values():
        require_sha256(digest, "fit_file_binding")
    for file_name in FIT_FILES:
        if set(fit_values[file_name]) != set(SELECTED_COLUMNS):
            raise TASK039D1Error("scientific values exceed the frozen 24-column view")

    source_records: list[dict[str, Any]] = []
    source_record_by_name: dict[str, dict[str, Any]] = {}
    source_parameters: dict[str, Mapping[str, Any]] = {}
    source_events_by_file: dict[str, dict[str, Sequence[Any]]] = {
        file_name: {} for file_name in FIT_FILES
    }
    for source in FROZEN_SOURCES:
        parameters = derive_multi_file_source_parameters_v1(
            tuple(fit_values[file_name][source] for file_name in FIT_FILES)
        )
        source_parameters[source] = parameters
        if parameters["status"] == "supported":
            extracted = extract_file_local_events_v1(
                {file_name: fit_values[file_name][source] for file_name in FIT_FILES},
                source_step_threshold=float(parameters["source_step_threshold"]),
                source_stability_tolerance=float(parameters["source_stability_tolerance"]),
            )
        else:
            extracted = {file_name: () for file_name in FIT_FILES}
        for file_name in FIT_FILES:
            source_events_by_file[file_name][source] = extracted[file_name]
        record = _record_hash(
            {
                "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
                "artifact_type": "task039d1_source_parameter_record_v1",
                "source": source,
                "semantic_role": FROZEN_SOURCE_ROLES[source],
                "source_noise_scale": parameters["source_noise_scale"],
                "nontrivial_amplitude_count": parameters["nontrivial_amplitude_count"],
                "source_step_threshold": parameters["source_step_threshold"],
                "source_stability_tolerance": parameters["source_stability_tolerance"],
                "parameter_status": parameters["status"],
                "parameter_class": "normal_relation_profile_fit_derived",
                "fit_file_bindings": [fit_file_bindings[name] for name in FIT_FILES],
            }
        )
        source_records.append(record)
        source_record_by_name[source] = record

    isolated_by_file: dict[str, Mapping[str, Sequence[tuple[Any, bool]]]] = {}
    for file_name in FIT_FILES:
        isolated_by_file[file_name] = classify_all_source_isolation_v1(source_events_by_file[file_name])

    target_records: list[dict[str, Any]] = []
    target_record_by_name: dict[str, dict[str, Any]] = {}
    target_scales: dict[str, float] = {}
    for target in FROZEN_TARGETS:
        scale = derive_multi_file_target_scale_v1(
            tuple(fit_values[file_name][target] for file_name in FIT_FILES)
        )
        target_scales[target] = scale
        record = _record_hash(
            {
                "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
                "artifact_type": "task039d1_target_parameter_record_v1",
                "target": target,
                "target_noise_scale": scale,
                "parameter_class": "normal_relation_profile_fit_derived",
                "fit_file_bindings": [fit_file_bindings[name] for name in FIT_FILES],
            }
        )
        target_records.append(record)
        target_record_by_name[target] = record

    directional_records: list[dict[str, Any]] = []
    pair_outcomes: list[dict[str, Any]] = []
    directional_status_counts = {
        "fit_supported": 0,
        "direction_unstable": 0,
        "fit_unsupported": 0,
    }
    failure_counts = {
        "insufficient_nontrivial_amplitudes": 0,
        "fit_gate_not_satisfied": 0,
    }
    for identity in identities:
        source, target = identity["source"], identity["target"]
        pair_direction_status: dict[str, str] = {}
        for source_direction in SOURCE_DIRECTIONS:
            source_support: dict[str, int] = {}
            stream_refs: dict[str, str] = {}
            for file_name in FIT_FILES:
                classified = isolated_by_file[file_name][source]
                selected_events = [
                    event for event, isolated in classified
                    if isolated and event.direction == source_direction
                ]
                source_support[file_name] = len(selected_events)
                stream_refs[file_name] = stable_hash_v1(
                    {
                        "file_binding": fit_file_bindings[file_name],
                        "source": source,
                        "source_step_direction": source_direction,
                        "retained_isolated_event_indices": [event.event_index for event in selected_events],
                    }
                )
            candidates: list[dict[str, Any]] = []
            selected_detail: Mapping[str, Any] | None = None
            if source_parameters[source]["status"] != "supported":
                fit_status = "fit_unsupported"
                failure_reason = "insufficient_nontrivial_amplitudes"
                failure_counts[failure_reason] += 1
            else:
                target_values = {file_name: fit_values[file_name][target] for file_name in FIT_FILES}
                classified_for_source = {
                    file_name: isolated_by_file[file_name][source] for file_name in FIT_FILES
                }
                for target_direction in TARGET_DIRECTIONS:
                    for horizon in HORIZONS:
                        candidates.append(
                            _direction_statistics(
                                target_values=target_values,
                                classified_events=classified_for_source,
                                source_direction=source_direction,
                                target_noise_scale=target_scales[target],
                                horizon=horizon,
                                target_direction=target_direction,
                            )
                        )
                projected = [_selection_projection(item) for item in candidates]
                selected_projection = rank_direction_horizon_v1(projected)
                if selected_projection is None:
                    fit_status = "direction_unstable"
                    failure_reason = "direction_unstable"
                else:
                    selected_detail = next(
                        item for item in candidates
                        if item["target_direction"] == selected_projection["target_direction"]
                        and item["horizon_seconds"] == selected_projection["horizon_seconds"]
                    )
                    selected_gate_record = {
                        **selected_projection,
                        "total_usable_responses": selected_detail["total_usable_responses"],
                        "train1_usable_responses": selected_detail["train1"]["usable_response_count"],
                        "train2_usable_responses": selected_detail["train2"]["usable_response_count"],
                    }
                    if selected_fit_gate_v1(selected_gate_record):
                        fit_status = "fit_supported"
                        failure_reason = None
                    else:
                        fit_status = "fit_unsupported"
                        failure_reason = "fit_gate_not_satisfied"
                        failure_counts[failure_reason] += 1
            directional_status_counts[fit_status] += 1
            pair_direction_status[source_direction] = fit_status
            record = _record_hash(
                {
                    "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
                    "artifact_type": "task039d1_directional_fit_record_v1",
                    "source": source,
                    "target": target,
                    "source_step_direction": source_direction,
                    "source_parameter_ref": source_record_by_name[source]["artifact_hash"],
                    "target_parameter_ref": target_record_by_name[target]["artifact_hash"],
                    "source_isolated_event_support_by_file": source_support,
                    "source_event_stream_refs": stream_refs,
                    "direction_selection_candidates": candidates,
                    "selected_target_direction": None if selected_detail is None else selected_detail["target_direction"],
                    "selected_horizon_seconds": None if selected_detail is None else selected_detail["horizon_seconds"],
                    "selected_train1_consistency": None if selected_detail is None else selected_detail["train1"]["selected_directional_consistency"],
                    "selected_train2_consistency": None if selected_detail is None else selected_detail["train2"]["selected_directional_consistency"],
                    "selected_pooled_consistency": None if selected_detail is None else selected_detail["pooled_directional_consistency"],
                    "selected_median_response": None if selected_detail is None else selected_detail["pooled_median_response"],
                    "selected_robust_effect_ratio": None if selected_detail is None else selected_detail["pooled_robust_effect_ratio"],
                    "fit_result": fit_status,
                    "failure_reason": failure_reason,
                    "lower_ranked_fallback_used": False,
                    "candidate_arm_evidence_visible": False,
                }
            )
            directional_records.append(record)
        pair_status = (
            "fit_supported_pair"
            if "fit_supported" in pair_direction_status.values()
            else "fit_unsupported_pair"
        )
        pair_outcomes.append(
            {
                "source": source,
                "target": target,
                "step_up_status": pair_direction_status["step_up"],
                "step_down_status": pair_direction_status["step_down"],
                "pair_fit_status": pair_status,
            }
        )

    source_ledger = _private_ledger(
        "task039d1_source_parameter_ledger_v1", source_records,
        execution_code_commit=execution_code_commit,
    )
    target_ledger = _private_ledger(
        "task039d1_target_parameter_ledger_v1", target_records,
        execution_code_commit=execution_code_commit,
    )
    directional_ledger = _private_ledger(
        "task039d1_directional_fit_ledger_v1", directional_records,
        execution_code_commit=execution_code_commit,
    )
    supported_pairs = sum(item["pair_fit_status"] == "fit_supported_pair" for item in pair_outcomes)
    pair_summary = TASK039D1PairFitSummaryV1(
        {
            "task_id": TASK_ID,
            "status": "frozen_task039d1_pair_fit_outcomes",
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "profiling_identity_view_hash": PROFILING_IDENTITY_VIEW_HASH,
            "candidate_count": 47,
            "directional_opportunity_count": 94,
            "pair_fit_supported_count": supported_pairs,
            "pair_fit_unsupported_count": 47 - supported_pairs,
            "directional_status_counts": directional_status_counts,
            "pair_outcomes": pair_outcomes,
            "lower_ranked_fallback_used": False,
            "candidate_arm_evidence_visible_to_profiler": False,
        }
    )
    return {
        "source_ledger": source_ledger,
        "target_ledger": target_ledger,
        "directional_ledger": directional_ledger,
        "pair_summary": pair_summary,
        "failure_counts": failure_counts,
    }


def ledger_binding_v1(
    artifact_class: type[_D1Artifact], *, ledger: Mapping[str, Any]
) -> _D1Artifact:
    verify_d1_self_hash_v1(ledger)
    return artifact_class(
        {
            "record_count": ledger["record_count"],
            "ledger_hash": ledger["artifact_hash"],
            "storage_boundary": "outside_git",
            "private_contents_public": False,
        }
    )


def build_data_access_audit_v1(
    *, state: DataAccessStateV1, file_records: Sequence[Mapping[str, Any]]
) -> _D1Artifact:
    return TASK039D1DataAccessAuditV1(
        {
            "task_id": TASK_ID,
            "status": "passed_task039d1_data_boundary",
            "dataset_manifest_id": DATASET_MANIFEST_HASH,
            "process": PROCESS_ID,
            "authorized_files": list(AUTHORIZED_RELATIVE_FILES),
            "file_records": list(file_records),
            "selected_column_hash": SELECTED_COLUMN_HASH,
            "selected_column_count": len(SELECTED_COLUMNS),
            "file_open_count": state.file_open_count,
            "feature_read_pass_count": state.feature_read_pass_count,
            "train1_accessed": state.train1_accessed,
            "train2_accessed": state.train2_accessed,
            "train3_accessed": False,
            "train4_accessed": False,
            "test_accessed": False,
            "labels_accessed": False,
            "attacks_accessed": False,
            "p2_p3_p4_values_accessed": False,
            "br2_pair_results_accessed": False,
            "candidate_arm_evidence_visible_during_profiling": False,
            "raw_values_persisted": False,
            "raw_windows_persisted": False,
            "event_timestamps_publicly_persisted": False,
            "absolute_local_paths_persisted": False,
            "timestamp_values_persisted": False,
            "timestamp_header_structural_verification_only": True,
            "prohibited_access_count": state.prohibited_access_count,
        }
    )


def build_fit_result_v1(
    *,
    outcomes: Mapping[str, Any],
    source_binding: _D1Artifact,
    target_binding: _D1Artifact,
    directional_binding: _D1Artifact,
    data_access_audit: _D1Artifact,
) -> _D1Artifact:
    pair_summary = outcomes["pair_summary"]
    pair_document = pair_summary.to_dict()
    counts = pair_document["directional_status_counts"]
    source_records = outcomes["source_ledger"]["records"]
    source_supported = sum(item["parameter_status"] == "supported" for item in source_records)
    return TASK039D1FitResultV1(
        {
            "task_id": TASK_ID,
            "status": STATUS,
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "d1_authorization_hash": D1_AUTHORIZATION_HASH,
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
            "candidate_count": 47,
            "directional_opportunity_count": 94,
            "source_parameter_record_count": 12,
            "source_parameter_supported_count": source_supported,
            "source_parameter_unsupported_count": 12 - source_supported,
            "target_parameter_record_count": 12,
            "pair_fit_supported_count": pair_document["pair_fit_supported_count"],
            "pair_fit_unsupported_count": pair_document["pair_fit_unsupported_count"],
            "directional_fit_supported_count": counts["fit_supported"],
            "direction_unstable_count": counts["direction_unstable"],
            "fit_unsupported_directional_count": counts["fit_unsupported"],
            "other_failure_counts": dict(outcomes["failure_counts"]),
            "source_ledger_binding": source_binding.to_dict(),
            "target_ledger_binding": target_binding.to_dict(),
            "directional_ledger_binding": directional_binding.to_dict(),
            "pair_summary_hash": pair_summary.artifact_hash,
            "data_access_audit_hash": data_access_audit.artifact_hash,
            "candidate_arm_evidence_visible_to_profiler": False,
            "lower_ranked_fallback_used": False,
            "merged_cross_arm_score_used": False,
            "numeric_parameter_class": "normal_relation_profile_fit_derived",
            "construction_confirmed": False,
            "rule_authority": False,
            "runtime_authority": False,
            "task039d2_authorized": False,
            "rule_v2_authorized": False,
            "claim_boundary": "fit-supported normal delayed-response relation candidate",
        }
    )


def load_provenance_after_outcomes_frozen_v1(
    *, provenance_path: Path, frozen_pair_summary_path: Path, expected_pair_summary_hash: str
) -> dict[str, Any]:
    if not frozen_pair_summary_path.is_file():
        raise TASK039D1Error("pair outcomes must be written before provenance is loaded")
    frozen = _load_json(frozen_pair_summary_path)
    if verify_d1_self_hash_v1(frozen) != expected_pair_summary_hash:
        raise TASK039D1Error("frozen pair-summary hash mismatch before provenance join")
    provenance = _load_json(provenance_path)
    verify_self_hash_v1(provenance)
    if provenance.get("artifact_hash") != PROVENANCE_ANALYSIS_VIEW_HASH:
        raise TASK039D1Error("provenance-analysis view identity mismatch")
    CandidateProvenanceAnalysisViewV1.from_dict(provenance)
    return provenance


def build_arm_fit_summary_v1(
    *, pair_summary_document: Mapping[str, Any], provenance_document: Mapping[str, Any]
) -> _D1Artifact:
    verify_d1_self_hash_v1(pair_summary_document)
    verify_self_hash_v1(provenance_document)
    outcomes = {
        (item["source"], item["target"]): item
        for item in pair_summary_document["pair_outcomes"]
    }
    provenance_pairs = {
        (item["source"], item["target"]): item
        for item in provenance_document["candidates"]
    }
    if set(outcomes) != set(provenance_pairs) or len(outcomes) != 47:
        raise TASK039D1Error("arm provenance and frozen pair outcomes differ")
    arms: list[dict[str, Any]] = []
    for arm in ("META", "STAT", "GDN"):
        pairs = [pair for pair, record in provenance_pairs.items() if arm in record["origin_arms"]]
        if len(pairs) != 20:
            raise TASK039D1Error("frozen arm top20 membership changed")
        pair_supported = sum(outcomes[pair]["pair_fit_status"] == "fit_supported_pair" for pair in pairs)
        directional_supported = sum(
            outcomes[pair][direction] == "fit_supported"
            for pair in pairs
            for direction in ("step_up_status", "step_down_status")
        )
        arms.append(
            {
                "arm": arm,
                "top20_pair_count": 20,
                "pair_fit_supported_count": pair_supported,
                "pair_fit_support_yield": pair_supported / 20.0,
                "directional_fit_supported_count": directional_supported,
            }
        )
    return TASK039D1ArmFitSummaryV1(
        {
            "task_id": TASK_ID,
            "status": "fit_only_descriptive_arm_summary",
            "pair_summary_hash": pair_summary_document["artifact_hash"],
            "provenance_analysis_view_hash": PROVENANCE_ANALYSIS_VIEW_HASH,
            "primary_k": 20,
            "arms": arms,
            "same_pair_same_d1_outcome_across_all_origin_arms": True,
            "scientific_profiles_per_unique_pair": 1,
            "provenance_joined_after_outcomes_frozen": True,
            "d2_confirmation_metrics_calculated": False,
            "winner_selected": False,
            "claim_boundary": "descriptive fit-only candidate-method yield; no winner",
        }
    )


def build_execution_receipt_v1(
    *,
    execution_code_commit: str,
    scientific_source_hashes: Mapping[str, str],
    source_binding: _D1Artifact,
    target_binding: _D1Artifact,
    directional_binding: _D1Artifact,
    pair_summary: _D1Artifact,
    fit_result: _D1Artifact,
    arm_summary: _D1Artifact,
    data_access: _D1Artifact,
) -> _D1Artifact:
    return TASK039D1ExecutionReceiptV1(
        {
            "task_id": TASK_ID,
            "status": STATUS,
            "execution_code_commit": execution_code_commit,
            "base_commit": BASE_COMMIT,
            "d0_config_hash": D0_CONFIG_HASH,
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "d1_authorization_hash": D1_AUTHORIZATION_HASH,
            "component_policy_hashes": {
                "source_scale": SOURCE_SCALE_POLICY_HASH,
                "source_event": SOURCE_EVENT_POLICY_HASH,
                "target_response": TARGET_RESPONSE_POLICY_HASH,
                "direction_selection": DIRECTION_SELECTION_POLICY_HASH,
                "fit_gate": FIT_GATE_POLICY_HASH,
                "train3_confirmation_planned_not_executed": CONFIRMATION_POLICY_HASH,
                "method_comparison": METHOD_COMPARISON_POLICY_HASH,
                "numeric_evidence_authority": NUMERIC_EVIDENCE_POLICY_HASH,
            },
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
            "profiling_identity_view_hash": PROFILING_IDENTITY_VIEW_HASH,
            "provenance_analysis_view_hash": PROVENANCE_ANALYSIS_VIEW_HASH,
            "dataset_manifest_hash": DATASET_MANIFEST_HASH,
            "br1_protocol_bundle_hash": BR1_PROTOCOL_BUNDLE_HASH,
            "scientific_source_hashes": dict(scientific_source_hashes),
            "execution_phase_order": [
                "1_load_arm_blind_identity_view",
                "2_derive_shared_source_target_parameters",
                "3_evaluate_47_pairs_and_94_directional_opportunities",
                "4_freeze_private_scientific_ledgers",
                "5_freeze_public_pair_and_fit_outcomes",
                "6_load_provenance_analysis_view",
                "7_calculate_descriptive_arm_fit_summary",
            ],
            "outcomes_frozen_before_provenance_join": True,
            "scientific_code_changed_after_first_value_read": False,
            "source_ledger_binding_hash": source_binding.artifact_hash,
            "target_ledger_binding_hash": target_binding.artifact_hash,
            "directional_ledger_binding_hash": directional_binding.artifact_hash,
            "pair_summary_hash": pair_summary.artifact_hash,
            "fit_result_hash": fit_result.artifact_hash,
            "arm_fit_summary_hash": arm_summary.artifact_hash,
            "data_access_audit_hash": data_access.artifact_hash,
            "candidate_count": 47,
            "directional_opportunity_count": 94,
            "lower_ranked_fallback_used": False,
            "candidate_arm_evidence_visible_to_profiler": False,
            "br2_pair_results_accessed": False,
            "merged_cross_arm_score_used": False,
            "train3_accessed": False,
            "train4_accessed": False,
            "test_labels_attacks_accessed": False,
            "task039d2_authorized": False,
            "rule_v2_authorized": False,
            "recommended_next_task": "TASK-039D1-AUDIT",
        }
    )


def schema_for_d1_artifact_v1(example: Mapping[str, Any]) -> dict[str, Any]:
    def infer(value: Any, field_name: str | None = None) -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int):
            return {"type": "integer", "minimum": 0}
        if isinstance(value, float):
            return {"type": "number"}
        if isinstance(value, str):
            if field_name and (field_name.endswith("_hash") or field_name.endswith("_ref")):
                return {"type": "string", "pattern": "^[a-f0-9]{64}$"}
            return {"type": "string"}
        if isinstance(value, list):
            if not value:
                return {"type": "array", "items": {}}
            schemas = [infer(item) for item in value]
            unique: list[dict[str, Any]] = []
            for item in schemas:
                if item not in unique:
                    unique.append(item)
            return {"type": "array", "items": unique[0] if len(unique) == 1 else {"anyOf": unique}}
        if isinstance(value, Mapping):
            return {
                "type": "object",
                "additionalProperties": False,
                "required": list(value),
                "properties": {key: infer(item, key) for key, item in value.items()},
            }
        raise TASK039D1Error("unsupported schema value")

    schema = infer(example)
    artifact_type = str(example["artifact_type"])
    schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://paperworks.local/schemas/v6/{artifact_type}_schema.json",
            "title": artifact_type,
        }
    )
    schema["properties"]["schema_version"] = {"const": V6_FOUNDATION_SCHEMA_VERSION}
    schema["properties"]["artifact_type"] = {"const": artifact_type}
    schema["properties"]["artifact_hash"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    return schema


def d1_schema_examples_v1() -> dict[str, dict[str, Any]]:
    digest = "0" * 64
    source_binding = TASK039D1SourceParameterLedgerBindingV1(
        {"record_count": 12, "ledger_hash": digest, "storage_boundary": "outside_git", "private_contents_public": False}
    )
    target_binding = TASK039D1TargetParameterLedgerBindingV1(
        {"record_count": 12, "ledger_hash": digest, "storage_boundary": "outside_git", "private_contents_public": False}
    )
    directional_binding = TASK039D1DirectionalFitLedgerBindingV1(
        {"record_count": 94, "ledger_hash": digest, "storage_boundary": "outside_git", "private_contents_public": False}
    )
    pair_outcomes = [
        {
            "source": source,
            "target": FROZEN_TARGETS[index % len(FROZEN_TARGETS)],
            "step_up_status": "fit_unsupported",
            "step_down_status": "direction_unstable",
            "pair_fit_status": "fit_unsupported_pair",
        }
        for index, source in enumerate((FROZEN_SOURCES * 4)[:47])
    ]
    # Synthetic schema examples need unique keys even though only shape matters.
    for index, item in enumerate(pair_outcomes):
        item["source"] = FROZEN_SOURCES[index % 12]
        item["target"] = FROZEN_TARGETS[(index // 12 + index) % 12]
    if len({(item["source"], item["target"]) for item in pair_outcomes}) != 47:
        pair_outcomes = [
            {
                "source": FROZEN_SOURCES[index // 12],
                "target": FROZEN_TARGETS[index % 12],
                "step_up_status": "fit_unsupported",
                "step_down_status": "direction_unstable",
                "pair_fit_status": "fit_unsupported_pair",
            }
            for index in range(47)
        ]
    pair = TASK039D1PairFitSummaryV1(
        {
            "task_id": TASK_ID,
            "status": "frozen_task039d1_pair_fit_outcomes",
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "profiling_identity_view_hash": PROFILING_IDENTITY_VIEW_HASH,
            "candidate_count": 47,
            "directional_opportunity_count": 94,
            "pair_fit_supported_count": 0,
            "pair_fit_unsupported_count": 47,
            "directional_status_counts": {"fit_supported": 0, "direction_unstable": 47, "fit_unsupported": 47},
            "pair_outcomes": pair_outcomes,
            "lower_ranked_fallback_used": False,
            "candidate_arm_evidence_visible_to_profiler": False,
        }
    )
    access = TASK039D1DataAccessAuditV1(
        {
            "task_id": TASK_ID, "status": "passed_task039d1_data_boundary",
            "dataset_manifest_id": DATASET_MANIFEST_HASH, "process": PROCESS_ID,
            "authorized_files": list(AUTHORIZED_RELATIVE_FILES),
            "file_records": [
                {"relative_path": path, "sha256": digest, "byte_size": 1, "row_count": 1,
                 "header_sha256": digest, "file_identity_match": True, "header_identity_match": True}
                for path in AUTHORIZED_RELATIVE_FILES
            ],
            "selected_column_hash": SELECTED_COLUMN_HASH, "selected_column_count": 24,
            "file_open_count": 4, "feature_read_pass_count": 2,
            "train1_accessed": True, "train2_accessed": True, "train3_accessed": False,
            "train4_accessed": False, "test_accessed": False, "labels_accessed": False,
            "attacks_accessed": False, "p2_p3_p4_values_accessed": False,
            "br2_pair_results_accessed": False,
            "candidate_arm_evidence_visible_during_profiling": False,
            "raw_values_persisted": False, "raw_windows_persisted": False,
            "event_timestamps_publicly_persisted": False, "absolute_local_paths_persisted": False,
            "timestamp_values_persisted": False,
            "timestamp_header_structural_verification_only": True,
            "prohibited_access_count": 0,
        }
    )
    fit = TASK039D1FitResultV1(
        {
            "task_id": TASK_ID, "status": STATUS,
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "d1_authorization_hash": D1_AUTHORIZATION_HASH,
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
            "candidate_count": 47, "directional_opportunity_count": 94,
            "source_parameter_record_count": 12, "source_parameter_supported_count": 12,
            "source_parameter_unsupported_count": 0, "target_parameter_record_count": 12,
            "pair_fit_supported_count": 0, "pair_fit_unsupported_count": 47,
            "directional_fit_supported_count": 0, "direction_unstable_count": 47,
            "fit_unsupported_directional_count": 47,
            "other_failure_counts": {"insufficient_nontrivial_amplitudes": 0, "fit_gate_not_satisfied": 47},
            "source_ledger_binding": source_binding.to_dict(),
            "target_ledger_binding": target_binding.to_dict(),
            "directional_ledger_binding": directional_binding.to_dict(),
            "pair_summary_hash": pair.artifact_hash, "data_access_audit_hash": access.artifact_hash,
            "candidate_arm_evidence_visible_to_profiler": False,
            "lower_ranked_fallback_used": False, "merged_cross_arm_score_used": False,
            "numeric_parameter_class": "normal_relation_profile_fit_derived",
            "construction_confirmed": False, "rule_authority": False, "runtime_authority": False,
            "task039d2_authorized": False, "rule_v2_authorized": False,
            "claim_boundary": "fit-supported normal delayed-response relation candidate",
        }
    )
    arm = TASK039D1ArmFitSummaryV1(
        {
            "task_id": TASK_ID, "status": "fit_only_descriptive_arm_summary",
            "pair_summary_hash": pair.artifact_hash,
            "provenance_analysis_view_hash": PROVENANCE_ANALYSIS_VIEW_HASH,
            "primary_k": 20,
            "arms": [
                {"arm": name, "top20_pair_count": 20, "pair_fit_supported_count": 0,
                 "pair_fit_support_yield": 0.0, "directional_fit_supported_count": 0}
                for name in ("META", "STAT", "GDN")
            ],
            "same_pair_same_d1_outcome_across_all_origin_arms": True,
            "scientific_profiles_per_unique_pair": 1,
            "provenance_joined_after_outcomes_frozen": True,
            "d2_confirmation_metrics_calculated": False, "winner_selected": False,
            "claim_boundary": "descriptive fit-only candidate-method yield; no winner",
        }
    )
    execution = build_execution_receipt_v1(
        execution_code_commit="1" * 40,
        scientific_source_hashes={"task039d1_fit_v1.py": digest},
        source_binding=source_binding, target_binding=target_binding,
        directional_binding=directional_binding, pair_summary=pair,
        fit_result=fit, arm_summary=arm, data_access=access,
    )
    artifacts = (source_binding, target_binding, directional_binding, pair, fit, arm, access, execution)
    return {artifact.ARTIFACT_TYPE: artifact.to_dict() for artifact in artifacts}


def source_file_sha256_v1(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "TASK039D1Error", "TASK039D1SourceParameterLedgerBindingV1",
    "TASK039D1TargetParameterLedgerBindingV1", "TASK039D1DirectionalFitLedgerBindingV1",
    "TASK039D1PairFitSummaryV1", "TASK039D1FitResultV1", "TASK039D1ArmFitSummaryV1",
    "TASK039D1DataAccessAuditV1", "TASK039D1ExecutionReceiptV1", "ARTIFACT_CLASSES",
    "ARTIFACT_CLASS_BY_TYPE", "DataAccessStateV1", "validate_external_roots_v1",
    "load_expected_file_identities_v1", "load_authorized_fit_values_v1",
    "optimized_target_response_v1", "evaluate_arm_blind_fit_v1", "ledger_binding_v1",
    "build_data_access_audit_v1", "build_fit_result_v1",
    "load_provenance_after_outcomes_frozen_v1", "build_arm_fit_summary_v1",
    "build_execution_receipt_v1", "schema_for_d1_artifact_v1", "d1_schema_examples_v1",
    "verify_d1_self_hash_v1", "write_json_v1", "assert_public_payload_safe_v1",
    "reject_br2_pair_input_v1", "source_file_sha256_v1", "TASK_ID", "STATUS",
    "BASE_COMMIT", "BRANCH", "RESULT_PATH_NAMES", "PRIVATE_SOURCE_LEDGER_NAME",
    "PRIVATE_TARGET_LEDGER_NAME", "PRIVATE_DIRECTIONAL_LEDGER_NAME",
    "AUTHORIZED_RELATIVE_FILES", "SELECTED_COLUMNS", "SELECTED_COLUMN_HASH",
]
