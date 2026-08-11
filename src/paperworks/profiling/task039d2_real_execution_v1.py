"""Authorized one-way TASK-039D2 confirmation on HAI train3.

The module validates the independent D1-audit authorization before any private
or data-root operation.  Scientific confirmation is arm blind; candidate-arm
provenance is accepted only by a separate post-freeze analysis function.
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
from typing import Any, ClassVar, Mapping, Sequence

from paperworks.data.contracts_v2 import DatasetManifestV2
from paperworks.profiling.task039d1_final_audit_v1 import (
    TASK039D2AuthorizationV1,
    verify_audit_self_hash_v1,
)
from paperworks.profiling.task039d1_fit_v1 import (
    SELECTED_COLUMNS,
    SELECTED_COLUMN_HASH,
    assert_public_payload_safe_v1,
    verify_d1_self_hash_v1,
)
from paperworks.profiling.task039d1_execution_optimization_v1 import (
    classify_all_source_isolation_indexed_v1,
    extract_sustained_step_events_linear_v1,
)
from paperworks.profiling.task039d2_confirmation_v1 import (
    D1ParameterLedgerBindingsV1,
    D1SourceParameterRecordV1,
    D1TargetParameterRecordV1,
    ConfirmableDirectionalRelationV1,
    apply_exact_confirmation_gate_v1,
    evaluate_train3_target_response_window_v1,
)
from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    freeze_json,
    reject_unknown_fields,
    require_sha256,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    CANDIDATE_COHORT_HASH,
    CANDIDATE_IDENTITY_LIST_HASH,
    DATASET_MANIFEST_HASH,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
    PROCESS_ID,
    CandidateProvenanceAnalysisViewV1,
    verify_self_hash_v1,
)


TASK_ID = "TASK-039D2"
STATUS = "passed_task039d2_one_way_train3_confirmation"
BRANCH = "task-039d2-train3-confirmation"
AUDIT_COMMIT = "301fb636b6944e2d2d86be4646605a3d38585165"
PREP_COMMIT = "826820aed3bb6c4205977454c00a9b618a7b6b69"
D2_AUTHORIZATION_HASH = "791f985afdc5f16b5c6b5aec4eb7bcefe1e39bc3b0f262cc0ff56c7ff5071f25"
D0_PROTOCOL_BUNDLE_HASH = "888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb"
CONFIRMATION_POLICY_HASH = "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"
METHOD_COMPARISON_POLICY_HASH = "0ccc7a97a5e9b3fe1e5a8a54828ec8f8f7e6482c62eb63f7df62d804c8cae39e"
D1_FIT_RESULT_HASH = "a2767945ef3cec5fa80c3e131b98fdc8a1eeecaa69a97461988d8da90a4e06d3"
D1_PAIR_SUMMARY_HASH = "a466057faa20eacd0692b6a9c19fbbb5b8968135ba4c018310a076aa0393d4f2"
D1_ARM_SUMMARY_HASH = "6589930085ed0d5d87224ef9da88984b1d52d5e2c7bd1e8b295539b6d0da15e8"
D1_SOURCE_LEDGER_HASH = "3eb6ff199dbc67b183d35a804754e557bdfa869a899c754e551cd77e8dcfb304"
D1_TARGET_LEDGER_HASH = "f36f4b424c85b228043f9685a22a25c73d6b165e28714b627cf51e8bbb77f96e"
D1_DIRECTIONAL_LEDGER_HASH = "e372d7ccf4a7dde5f7ccd91049cc73b443b3b19a3a0c563f451aea50e8faddc7"
PROVENANCE_ANALYSIS_VIEW_HASH = "7ab92318611dd7d0252c763c4099a7ee69f3dbab3132308254aeb92f8af2e115"
TRAIN3_RELATIVE_PATH = "hai-23.05/hai-train3.csv"
TRAIN3_SHA256 = "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"
TRAIN3_BYTE_SIZE = 72774793
TRAIN3_ROW_COUNT = 126000
TRAIN3_HEADER_SHA256 = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"

PRIVATE_SOURCE_NAME = "TASK-039D1_SOURCE_PARAMETER_LEDGER.json"
PRIVATE_TARGET_NAME = "TASK-039D1_TARGET_PARAMETER_LEDGER.json"
PRIVATE_DIRECTIONAL_NAME = "TASK-039D1_DIRECTIONAL_FIT_LEDGER.json"
PRIVATE_D2_NAME = "TASK039D2_DIRECTIONAL_CONFIRMATION_LEDGER.json"


class TASK039D2ExecutionError(ValueError):
    """Raised when real D2 authorization, input, or execution fails closed."""


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = thaw_json(freeze_json(content))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def verify_d2_self_hash_v1(document: Mapping[str, Any]) -> str:
    supplied = str(document.get("artifact_hash", ""))
    require_sha256(supplied, "artifact_hash")
    observed = stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"})
    if supplied != observed:
        raise TASK039D2ExecutionError("D2 artifact self-hash mismatch")
    return observed


def write_json_v1(path: Path, document: Mapping[str, Any], *, public: bool) -> None:
    if public:
        assert_public_payload_safe_v1(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(thaw_json(freeze_json(document)), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_authorization_v1(document: Mapping[str, Any]) -> TASK039D2AuthorizationV1:
    """Validate the exact audit-issued authorization without touching a path."""

    try:
        if verify_audit_self_hash_v1(document) != D2_AUTHORIZATION_HASH:
            raise TASK039D2ExecutionError("blocked_task039d2_authorization_mismatch")
        parsed = TASK039D2AuthorizationV1.from_dict(document)
    except Exception as exc:
        raise TASK039D2ExecutionError("blocked_task039d2_authorization_mismatch") from exc
    expected = {
        "status": "authorized_task039d2_one_way_train3_confirmation",
        "readiness": "READY_FOR_TASK039D2",
        "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
        "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
        "d1_fit_result_hash": D1_FIT_RESULT_HASH,
        "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH,
        "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
        "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
        "d1_pair_summary_hash": D1_PAIR_SUMMARY_HASH,
        "candidate_count": 47,
        "input_directional_relations": "d1_fit_supported_only",
        "input_directional_relation_count": 45,
        "supported_pair_context_count": 25,
        "train3_feature_values_authorized": True,
        "train1_train2_feature_value_refitting_authorized": False,
        "train4_authorized": False,
        "test_labels_attacks_authorized": False,
        "br2_pair_results_authorized": False,
        "candidate_arm_evidence_visible_to_confirmation_engine": False,
        "parameter_retuning_authorized": False,
        "alternative_horizon_search_authorized": False,
        "opposite_target_direction_search_authorized": False,
        "rule_v2_authorized": False,
        "agent_authorized": False,
        "detector_runtime_authorized": False,
        "separate_clean_d2_execution_code_commit_required": True,
        "d2_executed_by_this_artifact": False,
    }
    if any(document.get(key) != value for key, value in expected.items()):
        raise TASK039D2ExecutionError("blocked_task039d2_authorization_mismatch")
    return parsed


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039D2ExecutionError(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039D2ExecutionError("required artifact must be a JSON object")
    return value


def validate_external_roots_v1(
    *, repository_root: Path, data_root_value: str, d1_private_value: str,
    d2_private_value: str,
) -> tuple[Path, Path, Path]:
    raws = (data_root_value, d1_private_value, d2_private_value)
    if any(not value or ".." in Path(value).parts for value in raws):
        raise TASK039D2ExecutionError("D2 roots must be explicit and traversal-free")
    repository = repository_root.resolve(strict=True)
    data_root = Path(data_root_value).resolve(strict=True)
    d1_private = Path(d1_private_value).resolve(strict=True)
    candidate = Path(d2_private_value)
    d2_private = candidate.resolve(strict=candidate.exists())
    roots = (data_root, d1_private, d2_private)
    if len(set(roots)) != 3:
        raise TASK039D2ExecutionError("D2 roots must be distinct")
    if any(root.is_relative_to(repository) or repository.is_relative_to(root) for root in roots):
        raise TASK039D2ExecutionError("D2 roots must remain outside Git")
    return roots


@dataclass(frozen=True)
class D1PrivateInputsV1:
    source_document: Mapping[str, Any]
    target_document: Mapping[str, Any]
    directional_document: Mapping[str, Any]
    source_records: tuple[D1SourceParameterRecordV1, ...]
    target_records: tuple[D1TargetParameterRecordV1, ...]
    relations: tuple[ConfirmableDirectionalRelationV1, ...]
    parameter_bindings: D1ParameterLedgerBindingsV1


def load_d1_private_inputs_v1(private_root: Path) -> D1PrivateInputsV1:
    expected_names = {PRIVATE_SOURCE_NAME, PRIVATE_TARGET_NAME, PRIVATE_DIRECTIONAL_NAME}
    if {path.name for path in private_root.iterdir() if path.is_file()} != expected_names:
        raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
    source = _load_json(private_root / PRIVATE_SOURCE_NAME)
    target = _load_json(private_root / PRIVATE_TARGET_NAME)
    directional = _load_json(private_root / PRIVATE_DIRECTIONAL_NAME)
    expected = (
        (source, D1_SOURCE_LEDGER_HASH, 12, "task039d1_source_parameter_ledger_v1"),
        (target, D1_TARGET_LEDGER_HASH, 12, "task039d1_target_parameter_ledger_v1"),
        (directional, D1_DIRECTIONAL_LEDGER_HASH, 94, "task039d1_directional_fit_ledger_v1"),
    )
    for document, digest, count, artifact_type in expected:
        if (
            verify_d1_self_hash_v1(document) != digest
            or document.get("record_count") != count
            or document.get("artifact_type") != artifact_type
        ):
            raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
        for record in document["records"]:
            verify_d1_self_hash_v1(record)

    source_wrappers = tuple(
        D1SourceParameterRecordV1(
            source=record["source"], semantic_role=record["semantic_role"],
            source_noise_scale=record["source_noise_scale"],
            nontrivial_amplitude_count=record["nontrivial_amplitude_count"],
            source_step_threshold=record["source_step_threshold"],
            source_stability_tolerance=record["source_stability_tolerance"],
            parameter_status=record["parameter_status"],
            fit_file_bindings=tuple(record["fit_file_bindings"]),
            d1_parameter_record_hash=record["artifact_hash"],
            source_parameter_ledger_hash=D1_SOURCE_LEDGER_HASH,
        )
        for record in source["records"]
    )
    target_wrappers = tuple(
        D1TargetParameterRecordV1(
            target=record["target"], target_noise_scale=record["target_noise_scale"],
            fit_file_bindings=tuple(record["fit_file_bindings"]),
            d1_parameter_record_hash=record["artifact_hash"],
            target_parameter_ledger_hash=D1_TARGET_LEDGER_HASH,
        )
        for record in target["records"]
    )
    if {item.source for item in source_wrappers} != set(FROZEN_SOURCES):
        raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
    if {item.target for item in target_wrappers} != set(FROZEN_TARGETS):
        raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
    if any(item.parameter_status != "supported" for item in source_wrappers):
        raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
    source_by_name = {item.source: item for item in source_wrappers}
    target_by_name = {item.target: item for item in target_wrappers}
    selected = [record for record in directional["records"] if record["fit_result"] == "fit_supported"]
    if len(selected) != 45:
        raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
    relations: list[ConfirmableDirectionalRelationV1] = []
    identities: set[tuple[str, str, str]] = set()
    for record in selected:
        identity = (record["source"], record["target"], record["source_step_direction"])
        if identity in identities:
            raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
        identities.add(identity)
        source_record = source_by_name[record["source"]]
        target_record = target_by_name[record["target"]]
        if (
            record["source_parameter_ref"] != source_record.d1_parameter_record_hash
            or record["target_parameter_ref"] != target_record.d1_parameter_record_hash
            or record["selected_target_direction"] is None
            or record["selected_horizon_seconds"] is None
            or record["lower_ranked_fallback_used"]
            or record["candidate_arm_evidence_visible"]
        ):
            raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
        relations.append(
            ConfirmableDirectionalRelationV1(
                source=record["source"],
                source_step_direction=record["source_step_direction"],
                target=record["target"],
                target_response_direction=record["selected_target_direction"],
                d1_selected_horizon_seconds=record["selected_horizon_seconds"],
                source_noise_scale_reference=source_record.d1_parameter_record_hash,
                source_threshold_reference=source_record.d1_parameter_record_hash,
                source_stability_tolerance_reference=source_record.d1_parameter_record_hash,
                target_scale_reference=target_record.d1_parameter_record_hash,
                d1_directional_record_hash=record["artifact_hash"],
            )
        )
    return D1PrivateInputsV1(
        source_document=freeze_json(source), target_document=freeze_json(target),
        directional_document=freeze_json(directional),
        source_records=source_wrappers, target_records=target_wrappers,
        relations=tuple(relations),
        parameter_bindings=D1ParameterLedgerBindingsV1(D1_SOURCE_LEDGER_HASH, D1_TARGET_LEDGER_HASH),
    )


@dataclass
class D2DataAccessStateV1:
    prohibited_access_count: int = 0
    file_open_count: int = 0
    feature_read_pass_count: int = 0
    train3_accessed: bool = False


def expected_train3_identity_v1(repository_root: Path) -> dict[str, Any]:
    manifest_document = _load_json(repository_root / "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json")
    structure_document = _load_json(repository_root / "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json")
    verify_self_hash_v1(manifest_document)
    if manifest_document["artifact_hash"] != DATASET_MANIFEST_HASH:
        raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
    try:
        manifest = DatasetManifestV2.from_dict(manifest_document)
    except Exception as exc:
        raise TASK039D2ExecutionError("failed_task039d2_data_boundary") from exc
    manifest_item = next((item for item in manifest.files if item.relative_local_path == TRAIN3_RELATIVE_PATH), None)
    structure_item = next((item for item in structure_document["records"] if item["relative_path"] == TRAIN3_RELATIVE_PATH), None)
    if (
        manifest_item is None or structure_item is None
        or manifest_item.sha256 != TRAIN3_SHA256 or manifest_item.byte_size != TRAIN3_BYTE_SIZE
        or manifest_item.row_count != TRAIN3_ROW_COUNT
        or manifest_item.logical_file_role != "normal_train_time_series"
        or manifest_item.label_availability != "unavailable"
        or manifest_item.provenance_status != "verified"
        or structure_item["file_sha256"] != TRAIN3_SHA256
        or structure_item["header_sha256"] != TRAIN3_HEADER_SHA256
        or structure_item["normal_file_status"] != "normal_only_verified"
        or structure_item["ordered_header_matches_canonical"] is not True
    ):
        raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
    return {
        "relative_path": TRAIN3_RELATIVE_PATH, "sha256": TRAIN3_SHA256,
        "byte_size": TRAIN3_BYTE_SIZE, "row_count": TRAIN3_ROW_COUNT,
        "header_sha256": TRAIN3_HEADER_SHA256,
    }


def load_authorized_train3_values_v1(
    *, data_root: Path, expected: Mapping[str, Any], state: D2DataAccessStateV1,
) -> tuple[dict[str, array], dict[str, Any]]:
    if expected.get("relative_path") != TRAIN3_RELATIVE_PATH:
        state.prohibited_access_count += 1
        raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
    root = data_root.resolve(strict=True)
    path = (root / PurePosixPath(TRAIN3_RELATIVE_PATH)).resolve(strict=True)
    if not path.is_relative_to(root):
        state.prohibited_access_count += 1
        raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
    observed_size = path.stat().st_size
    digest = hashlib.sha256()
    state.file_open_count += 1
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    observed_hash = digest.hexdigest()
    if observed_size != TRAIN3_BYTE_SIZE or observed_hash != TRAIN3_SHA256:
        raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
    values = {name: array("d") for name in SELECTED_COLUMNS}
    state.file_open_count += 1
    state.feature_read_pass_count += 1
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = tuple(next(reader))
        except StopIteration as exc:
            raise TASK039D2ExecutionError("failed_task039d2_data_boundary") from exc
        header_hash = hashlib.sha256(",".join(header).encode("utf-8")).hexdigest()
        if (
            header_hash != TRAIN3_HEADER_SHA256 or not header or header[0] != "timestamp"
            or len(header) != len(set(header)) or any(name not in header for name in SELECTED_COLUMNS)
        ):
            raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
        indexes = tuple((name, header.index(name)) for name in SELECTED_COLUMNS)
        row_count = 0
        for row in reader:
            if len(row) != len(header):
                raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
            row_count += 1
            for name, index in indexes:
                try:
                    numeric = float(row[index])
                except ValueError as exc:
                    raise TASK039D2ExecutionError("failed_task039d2_data_boundary") from exc
                if not math.isfinite(numeric):
                    raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
                values[name].append(numeric)
    if row_count != TRAIN3_ROW_COUNT:
        raise TASK039D2ExecutionError("failed_task039d2_data_boundary")
    state.train3_accessed = True
    return values, {
        "relative_path": TRAIN3_RELATIVE_PATH, "sha256": observed_hash,
        "byte_size": observed_size, "row_count": row_count,
        "header_sha256": header_hash, "file_identity_match": True,
        "header_identity_match": True,
    }


def confirm_relations_one_way_v1(
    *, values: Mapping[str, Sequence[float]], private_inputs: D1PrivateInputsV1,
) -> dict[str, Any]:
    """Evaluate the 45 fixed D1 relations without provenance or search."""

    if set(values) != set(SELECTED_COLUMNS) or len(private_inputs.relations) != 45:
        raise TASK039D2ExecutionError("failed_task039d2_arm_blindness")
    sources = {item.source: item for item in private_inputs.source_records}
    targets = {item.target: item for item in private_inputs.target_records}
    events = {}
    for source in FROZEN_SOURCES:
        record = sources[source]
        if record.source_step_threshold is None or record.source_stability_tolerance is None:
            raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
        events[source] = extract_sustained_step_events_linear_v1(
            values[source], source_step_threshold=record.source_step_threshold,
            source_stability_tolerance=record.source_stability_tolerance,
        )
    isolated = classify_all_source_isolation_indexed_v1(events)
    private_records: list[dict[str, Any]] = []
    for relation in private_inputs.relations:
        responses: list[float] = []
        right_censored = 0
        for event, is_isolated in isolated[relation.source]:
            if not is_isolated or event.direction != relation.source_step_direction:
                continue
            censored, response = evaluate_train3_target_response_window_v1(
                values[relation.target], event_index=event.event_index,
                selected_horizon_seconds=relation.d1_selected_horizon_seconds,
            )
            if censored:
                right_censored += 1
            else:
                assert response is not None
                responses.append(response)
        scale = targets[relation.target].target_noise_scale
        increase = sum(response > scale for response in responses)
        decrease = sum(response < -scale for response in responses)
        selected, opposite = (increase, decrease) if relation.target_response_direction == "increase" else (decrease, increase)
        usable = len(responses)
        selected_consistency = selected / usable if usable else 0.0
        opposite_consistency = opposite / usable if usable else 0.0
        median_response = float(statistics.median(responses)) if responses else None
        effect_ratio = abs(median_response) / scale if median_response is not None else 0.0
        confirmed = apply_exact_confirmation_gate_v1(
            usable_responses=usable, source_direction_unchanged=True,
            selected_consistency=selected_consistency, opposite_consistency=opposite_consistency,
            robust_effect_ratio=effect_ratio, fit_parameters_reused_without_retuning=True,
        )
        content = {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d2_directional_confirmation_record_v1",
            "d1_directional_record_hash": relation.d1_directional_record_hash,
            "relation_binding_hash": relation.artifact_hash,
            "source": relation.source, "source_step_direction": relation.source_step_direction,
            "target": relation.target, "target_response_direction": relation.target_response_direction,
            "selected_horizon_seconds": relation.d1_selected_horizon_seconds,
            "source_parameter_record_hash": sources[relation.source].d1_parameter_record_hash,
            "target_parameter_record_hash": targets[relation.target].d1_parameter_record_hash,
            "train3_usable_response_count": usable,
            "right_censored_count": right_censored,
            "selected_directional_consistency": selected_consistency,
            "opposite_directional_consistency": opposite_consistency,
            "median_target_response": median_response,
            "robust_effect_ratio": effect_ratio,
            "source_direction_unchanged": True,
            "fit_parameters_reused_without_retuning": True,
            "parameter_retuning_used": False,
            "alternative_horizon_search_used": False,
            "opposite_direction_search_used": False,
            "lower_ranked_fallback_used": False,
            "candidate_provenance_visible": False,
            "confirmation_status": "calibration_confirmed" if confirmed else "calibration_conflict",
        }
        private_records.append(_self_hashed(content))
    if len(private_records) != 45 or len({item["d1_directional_record_hash"] for item in private_records}) != 45:
        raise TASK039D2ExecutionError("failed_task039d2_result_contract")
    ledger = _self_hashed(
        {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d2_directional_confirmation_ledger_v1",
            "task_id": TASK_ID, "status": "frozen_task039d2_directional_confirmations",
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
            "record_count": 45, "records": private_records,
            "raw_train3_rows_included": False, "raw_windows_included": False,
            "event_timestamps_included": False, "absolute_paths_included": False,
        }
    )
    return {"ledger": ledger, "events_by_source": events, "isolated_by_source": isolated}


@dataclass(frozen=True)
class _D2Artifact:
    payload: Mapping[str, Any]
    ARTIFACT_TYPE: ClassVar[str] = ""
    FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        reject_unknown_fields(self.payload, self.FIELDS, self.ARTIFACT_TYPE)
        if set(self.payload) != set(self.FIELDS):
            raise TASK039D2ExecutionError(f"{self.ARTIFACT_TYPE} fields are incomplete")
        object.__setattr__(self, "payload", freeze_json(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return _self_hashed({"schema_version": V6_FOUNDATION_SCHEMA_VERSION, "artifact_type": self.ARTIFACT_TYPE, **thaw_json(self.payload)})

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "_D2Artifact":
        verify_d2_self_hash_v1(document)
        if document.get("schema_version") != V6_FOUNDATION_SCHEMA_VERSION or document.get("artifact_type") != cls.ARTIFACT_TYPE:
            raise TASK039D2ExecutionError("D2 artifact identity mismatch")
        return cls({key: value for key, value in document.items() if key not in {"schema_version", "artifact_type", "artifact_hash"}})


def _artifact_class(name: str, artifact_type: str, fields: Sequence[str]) -> type[_D2Artifact]:
    return type(name, (_D2Artifact,), {"ARTIFACT_TYPE": artifact_type, "FIELDS": frozenset(fields)})


TASK039D2DataAccessAuditV1 = _artifact_class(
    "TASK039D2DataAccessAuditV1", "task039d2_data_access_audit_v1",
    ("task_id", "status", "dataset_manifest_id", "process", "authorized_file", "file_record", "selected_column_hash", "selected_column_count", "file_open_count", "feature_read_pass_count", "train3_accessed", "train1_feature_values_accessed", "train2_feature_values_accessed", "train4_accessed", "test_accessed", "labels_accessed", "attacks_accessed", "p2_p3_p4_values_accessed", "br2_pair_results_accessed", "candidate_provenance_visible_during_confirmation", "d1_private_ledgers_accessed", "d1_private_ledgers_modified", "raw_train3_values_persisted", "raw_windows_persisted", "event_timestamps_publicly_persisted", "absolute_local_paths_persisted", "prohibited_access_count"),
)
TASK039D2DirectionalConfirmationSummaryV1 = _artifact_class(
    "TASK039D2DirectionalConfirmationSummaryV1", "task039d2_directional_confirmation_summary_v1",
    ("task_id", "status", "authorization_hash", "confirmation_policy_hash", "d1_directional_ledger_hash", "input_relation_count", "confirmed_directional_count", "conflict_directional_count", "relations", "private_ledger_hash", "private_ledger_record_count", "private_ledger_storage_boundary", "private_ledger_contents_public", "parameter_retuning_used", "alternative_horizon_search_used", "opposite_direction_search_used", "lower_ranked_fallback_used", "candidate_provenance_visible_during_confirmation"),
)
TASK039D2PairConfirmationSummaryV1 = _artifact_class(
    "TASK039D2PairConfirmationSummaryV1", "task039d2_pair_confirmation_summary_v1",
    ("task_id", "status", "d1_pair_summary_hash", "directional_confirmation_summary_hash", "candidate_count", "d1_fit_supported_pair_count", "d1_fit_unsupported_pair_count", "pairs_with_confirmed_direction_count", "d1_supported_pairs_without_confirmed_direction_count", "pair_records", "outcomes_frozen_before_provenance_join"),
)
TASK039D2ArmConfirmationSummaryV1 = _artifact_class(
    "TASK039D2ArmConfirmationSummaryV1", "task039d2_arm_confirmation_summary_v1",
    ("task_id", "status", "method_comparison_policy_hash", "pair_confirmation_summary_hash", "provenance_analysis_view_hash", "primary_k", "arms", "confirmed_pair_overlap", "same_pair_same_d2_outcome_across_all_origin_arms", "provenance_joined_after_outcomes_frozen", "winner_selected", "claim_boundary"),
)
TASK039D2ResultV1 = _artifact_class(
    "TASK039D2ResultV1", "task039d2_result_v1",
    ("task_id", "status", "authorization_hash", "d0_protocol_bundle_hash", "confirmation_policy_hash", "method_comparison_policy_hash", "candidate_cohort_hash", "candidate_identity_list_hash", "d1_fit_result_hash", "d1_pair_summary_hash", "d1_source_ledger_hash", "d1_target_ledger_hash", "d1_directional_ledger_hash", "input_directional_relation_count", "supported_pair_context_count", "confirmed_directional_count", "conflict_directional_count", "pairs_with_confirmed_direction_count", "directional_confirmation_summary_hash", "pair_confirmation_summary_hash", "arm_confirmation_summary_hash", "data_access_audit_hash", "private_confirmation_ledger_hash", "parameter_retuning_used", "alternative_horizon_search_used", "opposite_direction_search_used", "lower_ranked_fallback_used", "winner_selected", "rule_v2_authorized", "agent_authorized", "runtime_authority", "claim_boundary"),
)
TASK039D2RealExecutionReceiptV1 = _artifact_class(
    "TASK039D2RealExecutionReceiptV1", "task039d2_real_execution_receipt_v1",
    ("task_id", "status", "execution_code_commit", "synthetic_prep_merge_commit", "audit_commit", "authorization_hash", "scientific_source_hashes", "execution_phase_order", "outcomes_frozen_before_provenance_join", "scientific_source_changed_after_first_train3_read", "private_ledger_hash", "directional_summary_hash", "pair_summary_hash", "arm_summary_hash", "result_hash", "data_access_audit_hash", "input_relation_count", "parameter_retuning_used", "alternative_horizon_search_used", "opposite_direction_search_used", "lower_ranked_fallback_used", "train3_accessed", "train1_train2_feature_values_accessed", "train4_test_labels_attacks_accessed", "br2_pair_results_accessed", "candidate_provenance_visible_during_confirmation", "rule_v2_authorized", "recommended_next_task"),
)

ARTIFACT_CLASSES = (
    TASK039D2DataAccessAuditV1, TASK039D2DirectionalConfirmationSummaryV1,
    TASK039D2PairConfirmationSummaryV1, TASK039D2ArmConfirmationSummaryV1,
    TASK039D2ResultV1, TASK039D2RealExecutionReceiptV1,
)
ARTIFACT_CLASS_BY_TYPE = {item.ARTIFACT_TYPE: item for item in ARTIFACT_CLASSES}


def build_directional_summary_v1(ledger: Mapping[str, Any]) -> dict[str, Any]:
    verify_d2_self_hash_v1(ledger)
    relations = [
        {
            "source": record["source"], "source_step_direction": record["source_step_direction"],
            "target": record["target"], "target_response_direction": record["target_response_direction"],
            "selected_horizon_seconds": record["selected_horizon_seconds"],
            "d1_directional_record_hash": record["d1_directional_record_hash"],
            "confirmation_status": record["confirmation_status"],
            "private_confirmation_record_hash": record["artifact_hash"],
        }
        for record in ledger["records"]
    ]
    confirmed = sum(item["confirmation_status"] == "calibration_confirmed" for item in relations)
    return TASK039D2DirectionalConfirmationSummaryV1(
        {
            "task_id": TASK_ID, "status": "frozen_task039d2_directional_confirmation_summary",
            "authorization_hash": D2_AUTHORIZATION_HASH, "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
            "input_relation_count": 45, "confirmed_directional_count": confirmed,
            "conflict_directional_count": 45 - confirmed, "relations": relations,
            "private_ledger_hash": ledger["artifact_hash"], "private_ledger_record_count": 45,
            "private_ledger_storage_boundary": "outside_git", "private_ledger_contents_public": False,
            "parameter_retuning_used": False, "alternative_horizon_search_used": False,
            "opposite_direction_search_used": False, "lower_ranked_fallback_used": False,
            "candidate_provenance_visible_during_confirmation": False,
        }
    ).to_dict()


def build_pair_summary_v1(
    *, d1_pair_summary: Mapping[str, Any], directional_summary: Mapping[str, Any],
) -> dict[str, Any]:
    if verify_d1_self_hash_v1(d1_pair_summary) != D1_PAIR_SUMMARY_HASH:
        raise TASK039D2ExecutionError("failed_task039d2_private_input_binding")
    verify_d2_self_hash_v1(directional_summary)
    directions: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for relation in directional_summary["relations"]:
        directions.setdefault((relation["source"], relation["target"]), []).append(relation)
    pair_records = []
    for item in d1_pair_summary["pair_outcomes"]:
        pair = (item["source"], item["target"])
        evaluated = directions.get(pair, [])
        d1_supported = item["pair_fit_status"] == "fit_supported_pair"
        confirmed = any(record["confirmation_status"] == "calibration_confirmed" for record in evaluated)
        if d1_supported != bool(evaluated):
            raise TASK039D2ExecutionError("failed_task039d2_result_contract")
        pair_records.append(
            {"source": pair[0], "target": pair[1], "d1_fit_supported_pair": d1_supported,
             "d2_evaluated_direction_count": len(evaluated),
             "has_d2_confirmed_directional_relation": confirmed}
        )
    confirmed_pairs = sum(item["has_d2_confirmed_directional_relation"] for item in pair_records)
    return TASK039D2PairConfirmationSummaryV1(
        {"task_id": TASK_ID, "status": "frozen_task039d2_pair_confirmation_summary",
         "d1_pair_summary_hash": D1_PAIR_SUMMARY_HASH,
         "directional_confirmation_summary_hash": directional_summary["artifact_hash"],
         "candidate_count": 47, "d1_fit_supported_pair_count": 25,
         "d1_fit_unsupported_pair_count": 22,
         "pairs_with_confirmed_direction_count": confirmed_pairs,
         "d1_supported_pairs_without_confirmed_direction_count": 25 - confirmed_pairs,
         "pair_records": pair_records, "outcomes_frozen_before_provenance_join": True}
    ).to_dict()


def load_provenance_after_outcomes_frozen_v1(
    *, provenance_path: Path, directional_path: Path, pair_path: Path,
    expected_directional_hash: str, expected_pair_hash: str,
) -> dict[str, Any]:
    for path, digest in ((directional_path, expected_directional_hash), (pair_path, expected_pair_hash)):
        if not path.is_file() or verify_d2_self_hash_v1(_load_json(path)) != digest:
            raise TASK039D2ExecutionError("failed_task039d2_arm_blindness")
    provenance = _load_json(provenance_path)
    verify_self_hash_v1(provenance)
    if provenance.get("artifact_hash") != PROVENANCE_ANALYSIS_VIEW_HASH:
        raise TASK039D2ExecutionError("failed_task039d2_arm_blindness")
    CandidateProvenanceAnalysisViewV1.from_dict(provenance)
    return provenance


def build_arm_summary_v1(
    *, d1_arm_summary: Mapping[str, Any], pair_summary: Mapping[str, Any],
    directional_summary: Mapping[str, Any], provenance: Mapping[str, Any],
) -> dict[str, Any]:
    if verify_d1_self_hash_v1(d1_arm_summary) != D1_ARM_SUMMARY_HASH:
        raise TASK039D2ExecutionError("failed_task039d2_result_contract")
    pair_by_key = {(item["source"], item["target"]): item for item in pair_summary["pair_records"]}
    direction_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for item in directional_summary["relations"]:
        direction_by_pair.setdefault((item["source"], item["target"]), []).append(item)
    provenance_by_key = {(item["source"], item["target"]): item for item in provenance["candidates"]}
    if set(pair_by_key) != set(provenance_by_key) or len(pair_by_key) != 47:
        raise TASK039D2ExecutionError("failed_task039d2_arm_blindness")
    d1_fit = {item["arm"]: item for item in d1_arm_summary["arms"]}
    expected_fit = {"META": (16, 29), "STAT": (17, 33), "GDN": (5, 7)}
    arms = []
    for arm in ("META", "STAT", "GDN"):
        arm_pairs = [pair for pair, item in provenance_by_key.items() if arm in item["origin_arms"]]
        if len(arm_pairs) != 20 or (d1_fit[arm]["pair_fit_supported_count"], d1_fit[arm]["directional_fit_supported_count"]) != expected_fit[arm]:
            raise TASK039D2ExecutionError("failed_task039d2_result_contract")
        confirmed_pairs = [pair for pair in arm_pairs if pair_by_key[pair]["has_d2_confirmed_directional_relation"]]
        confirmed_directions = [item for pair in arm_pairs for item in direction_by_pair.get(pair, []) if item["confirmation_status"] == "calibration_confirmed"]
        sources = {item["source"] for item in confirmed_directions}
        targets = {item["target"] for item in confirmed_directions}
        fit_pairs, fit_directions = expected_fit[arm]
        arms.append(
            {"arm": arm, "top20_pair_count": 20,
             "d1_fit_supported_pair_count": fit_pairs,
             "d1_pair_fit_support_yield": fit_pairs / 20.0,
             "d1_directional_fit_supported_count": fit_directions,
             "d2_confirmed_pair_count": len(confirmed_pairs),
             "confirmed_relation_yield_at_20": len(confirmed_pairs) / 20.0,
             "pair_fit_to_confirmation_transfer": len(confirmed_pairs) / fit_pairs if fit_pairs else 0.0,
             "directional_confirmation_count": len(confirmed_directions),
             "directional_transfer": len(confirmed_directions) / fit_directions if fit_directions else 0.0,
             "distinct_confirmed_source_count": len(sources),
             "distinct_confirmed_source_coverage_at_20": len(sources) / 12.0,
             "distinct_confirmed_target_count": len(targets),
             "distinct_confirmed_target_coverage_at_20": len(targets) / 12.0}
        )
    confirmed_pairs = [pair for pair, item in pair_by_key.items() if item["has_d2_confirmed_directional_relation"]]
    categories = {name: [] for name in ("META_only", "STAT_only", "GDN_only", "META_STAT_only", "META_GDN_only", "STAT_GDN_only", "all_three")}
    name_by_arms = {
        ("META",): "META_only", ("STAT",): "STAT_only", ("GDN",): "GDN_only",
        ("META", "STAT"): "META_STAT_only", ("META", "GDN"): "META_GDN_only",
        ("STAT", "GDN"): "STAT_GDN_only", ("META", "STAT", "GDN"): "all_three",
    }
    for pair in confirmed_pairs:
        origin = tuple(arm for arm in ("META", "STAT", "GDN") if arm in provenance_by_key[pair]["origin_arms"])
        categories[name_by_arms[origin]].append({"source": pair[0], "target": pair[1]})
    overlap = {name: {"count": len(items), "pairs": items} for name, items in categories.items()}
    overlap["confirmed_union_count"] = len(confirmed_pairs)
    overlap["shared_by_exactly_two_count"] = sum(len(categories[name]) for name in ("META_STAT_only", "META_GDN_only", "STAT_GDN_only"))
    return TASK039D2ArmConfirmationSummaryV1(
        {"task_id": TASK_ID, "status": "descriptive_task039d2_arm_confirmation_summary",
         "method_comparison_policy_hash": METHOD_COMPARISON_POLICY_HASH,
         "pair_confirmation_summary_hash": pair_summary["artifact_hash"],
         "provenance_analysis_view_hash": PROVENANCE_ANALYSIS_VIEW_HASH,
         "primary_k": 20, "arms": arms, "confirmed_pair_overlap": overlap,
         "same_pair_same_d2_outcome_across_all_origin_arms": True,
         "provenance_joined_after_outcomes_frozen": True, "winner_selected": False,
         "claim_boundary": "one-way train3 confirmation metrics; no candidate-method winner"}
    ).to_dict()


def build_data_access_audit_v1(*, state: D2DataAccessStateV1, file_record: Mapping[str, Any]) -> dict[str, Any]:
    return TASK039D2DataAccessAuditV1(
        {"task_id": TASK_ID, "status": "passed_task039d2_data_boundary",
         "dataset_manifest_id": DATASET_MANIFEST_HASH, "process": PROCESS_ID,
         "authorized_file": TRAIN3_RELATIVE_PATH, "file_record": dict(file_record),
         "selected_column_hash": SELECTED_COLUMN_HASH, "selected_column_count": 24,
         "file_open_count": state.file_open_count, "feature_read_pass_count": state.feature_read_pass_count,
         "train3_accessed": state.train3_accessed,
         "train1_feature_values_accessed": False, "train2_feature_values_accessed": False,
         "train4_accessed": False, "test_accessed": False, "labels_accessed": False,
         "attacks_accessed": False, "p2_p3_p4_values_accessed": False,
         "br2_pair_results_accessed": False,
         "candidate_provenance_visible_during_confirmation": False,
         "d1_private_ledgers_accessed": True, "d1_private_ledgers_modified": False,
         "raw_train3_values_persisted": False, "raw_windows_persisted": False,
         "event_timestamps_publicly_persisted": False, "absolute_local_paths_persisted": False,
         "prohibited_access_count": state.prohibited_access_count}
    ).to_dict()


def build_result_v1(
    *, directional: Mapping[str, Any], pair: Mapping[str, Any], arm: Mapping[str, Any],
    access: Mapping[str, Any], private_ledger_hash: str,
) -> dict[str, Any]:
    return TASK039D2ResultV1(
        {"task_id": TASK_ID, "status": STATUS, "authorization_hash": D2_AUTHORIZATION_HASH,
         "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
         "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
         "method_comparison_policy_hash": METHOD_COMPARISON_POLICY_HASH,
         "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
         "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
         "d1_fit_result_hash": D1_FIT_RESULT_HASH, "d1_pair_summary_hash": D1_PAIR_SUMMARY_HASH,
         "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH, "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
         "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
         "input_directional_relation_count": 45, "supported_pair_context_count": 25,
         "confirmed_directional_count": directional["confirmed_directional_count"],
         "conflict_directional_count": directional["conflict_directional_count"],
         "pairs_with_confirmed_direction_count": pair["pairs_with_confirmed_direction_count"],
         "directional_confirmation_summary_hash": directional["artifact_hash"],
         "pair_confirmation_summary_hash": pair["artifact_hash"],
         "arm_confirmation_summary_hash": arm["artifact_hash"],
         "data_access_audit_hash": access["artifact_hash"],
         "private_confirmation_ledger_hash": private_ledger_hash,
         "parameter_retuning_used": False, "alternative_horizon_search_used": False,
         "opposite_direction_search_used": False, "lower_ranked_fallback_used": False,
         "winner_selected": False, "rule_v2_authorized": False,
         "agent_authorized": False, "runtime_authority": False,
         "claim_boundary": "one-way train3 calibration confirmation; not causality, rule validity, or anomaly performance"}
    ).to_dict()


def build_execution_receipt_v1(
    *, execution_code_commit: str, prep_merge_commit: str,
    scientific_source_hashes: Mapping[str, str], private_ledger_hash: str,
    directional: Mapping[str, Any], pair: Mapping[str, Any], arm: Mapping[str, Any],
    result: Mapping[str, Any], access: Mapping[str, Any],
) -> dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9]{40}", execution_code_commit) or not re.fullmatch(r"[a-f0-9]{40}", prep_merge_commit):
        raise TASK039D2ExecutionError("invalid execution lineage")
    return TASK039D2RealExecutionReceiptV1(
        {"task_id": TASK_ID, "status": STATUS, "execution_code_commit": execution_code_commit,
         "synthetic_prep_merge_commit": prep_merge_commit, "audit_commit": AUDIT_COMMIT,
         "authorization_hash": D2_AUTHORIZATION_HASH,
         "scientific_source_hashes": dict(scientific_source_hashes),
         "execution_phase_order": [
             "1_validate_d2_authorization", "2_validate_d1_private_ledgers",
             "3_construct_45_arm_blind_relations", "4_open_train3",
             "5_extract_all_source_events", "6_freeze_all_source_isolation",
             "7_evaluate_45_one_way_confirmations", "8_freeze_private_confirmation_ledger",
             "9_freeze_public_directional_and_pair_outcomes", "10_load_candidate_provenance",
             "11_calculate_candidate_method_metrics"],
         "outcomes_frozen_before_provenance_join": True,
         "scientific_source_changed_after_first_train3_read": False,
         "private_ledger_hash": private_ledger_hash,
         "directional_summary_hash": directional["artifact_hash"], "pair_summary_hash": pair["artifact_hash"],
         "arm_summary_hash": arm["artifact_hash"], "result_hash": result["artifact_hash"],
         "data_access_audit_hash": access["artifact_hash"], "input_relation_count": 45,
         "parameter_retuning_used": False, "alternative_horizon_search_used": False,
         "opposite_direction_search_used": False, "lower_ranked_fallback_used": False,
         "train3_accessed": True, "train1_train2_feature_values_accessed": False,
         "train4_test_labels_attacks_accessed": False, "br2_pair_results_accessed": False,
         "candidate_provenance_visible_during_confirmation": False,
         "rule_v2_authorized": False, "recommended_next_task": "TASK-039D2-AUDIT"}
    ).to_dict()


def schema_for_d2_artifact_v1(example: Mapping[str, Any]) -> dict[str, Any]:
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
            return {"type": "string", **({"pattern": "^[a-f0-9]{64}$"} if field_name and field_name.endswith("_hash") else {})}
        if isinstance(value, list):
            return {"type": "array", "items": {} if not value else infer(value[0])}
        if isinstance(value, Mapping):
            return {"type": "object", "additionalProperties": False, "required": list(value), "properties": {key: infer(item, key) for key, item in value.items()}}
        raise TASK039D2ExecutionError("unsupported schema example")
    schema = infer(example)
    artifact_type = str(example["artifact_type"])
    schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"https://paperworks.local/schemas/v6/{artifact_type}_schema.json", "title": artifact_type})
    schema["properties"]["schema_version"] = {"const": V6_FOUNDATION_SCHEMA_VERSION}
    schema["properties"]["artifact_type"] = {"const": artifact_type}
    schema["properties"]["artifact_hash"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    return schema


def d2_schema_examples_v1() -> dict[str, dict[str, Any]]:
    digest = "0" * 64
    directional = TASK039D2DirectionalConfirmationSummaryV1(
        {"task_id": TASK_ID, "status": "frozen_task039d2_directional_confirmation_summary",
         "authorization_hash": D2_AUTHORIZATION_HASH, "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
         "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH, "input_relation_count": 45,
         "confirmed_directional_count": 0, "conflict_directional_count": 45,
         "relations": [{"source": FROZEN_SOURCES[0], "source_step_direction": "step_up", "target": FROZEN_TARGETS[0], "target_response_direction": "increase", "selected_horizon_seconds": 5, "d1_directional_record_hash": digest, "confirmation_status": "calibration_conflict", "private_confirmation_record_hash": digest}],
         "private_ledger_hash": digest, "private_ledger_record_count": 45,
         "private_ledger_storage_boundary": "outside_git", "private_ledger_contents_public": False,
         "parameter_retuning_used": False, "alternative_horizon_search_used": False,
         "opposite_direction_search_used": False, "lower_ranked_fallback_used": False,
         "candidate_provenance_visible_during_confirmation": False}
    ).to_dict()
    pair = TASK039D2PairConfirmationSummaryV1(
        {"task_id": TASK_ID, "status": "frozen_task039d2_pair_confirmation_summary",
         "d1_pair_summary_hash": D1_PAIR_SUMMARY_HASH, "directional_confirmation_summary_hash": directional["artifact_hash"],
         "candidate_count": 47, "d1_fit_supported_pair_count": 25, "d1_fit_unsupported_pair_count": 22,
         "pairs_with_confirmed_direction_count": 0, "d1_supported_pairs_without_confirmed_direction_count": 25,
         "pair_records": [{"source": FROZEN_SOURCES[0], "target": FROZEN_TARGETS[0], "d1_fit_supported_pair": True, "d2_evaluated_direction_count": 1, "has_d2_confirmed_directional_relation": False}],
         "outcomes_frozen_before_provenance_join": True}
    ).to_dict()
    arm = TASK039D2ArmConfirmationSummaryV1(
        {"task_id": TASK_ID, "status": "descriptive_task039d2_arm_confirmation_summary",
         "method_comparison_policy_hash": METHOD_COMPARISON_POLICY_HASH,
         "pair_confirmation_summary_hash": pair["artifact_hash"], "provenance_analysis_view_hash": PROVENANCE_ANALYSIS_VIEW_HASH,
         "primary_k": 20, "arms": [{"arm": name, "top20_pair_count": 20, "d1_fit_supported_pair_count": fitp, "d1_pair_fit_support_yield": fitp / 20.0, "d1_directional_fit_supported_count": fitd, "d2_confirmed_pair_count": 0, "confirmed_relation_yield_at_20": 0.0, "pair_fit_to_confirmation_transfer": 0.0, "directional_confirmation_count": 0, "directional_transfer": 0.0, "distinct_confirmed_source_count": 0, "distinct_confirmed_source_coverage_at_20": 0.0, "distinct_confirmed_target_count": 0, "distinct_confirmed_target_coverage_at_20": 0.0} for name, fitp, fitd in (("META", 16, 29), ("STAT", 17, 33), ("GDN", 5, 7))],
         "confirmed_pair_overlap": {"META_only": {"count": 0, "pairs": []}, "STAT_only": {"count": 0, "pairs": []}, "GDN_only": {"count": 0, "pairs": []}, "META_STAT_only": {"count": 0, "pairs": []}, "META_GDN_only": {"count": 0, "pairs": []}, "STAT_GDN_only": {"count": 0, "pairs": []}, "all_three": {"count": 0, "pairs": []}, "confirmed_union_count": 0, "shared_by_exactly_two_count": 0},
         "same_pair_same_d2_outcome_across_all_origin_arms": True, "provenance_joined_after_outcomes_frozen": True,
         "winner_selected": False, "claim_boundary": "one-way train3 confirmation metrics; no candidate-method winner"}
    ).to_dict()
    access = TASK039D2DataAccessAuditV1(
        {"task_id": TASK_ID, "status": "passed_task039d2_data_boundary", "dataset_manifest_id": DATASET_MANIFEST_HASH,
         "process": PROCESS_ID, "authorized_file": TRAIN3_RELATIVE_PATH,
         "file_record": {"relative_path": TRAIN3_RELATIVE_PATH, "sha256": TRAIN3_SHA256, "byte_size": TRAIN3_BYTE_SIZE, "row_count": TRAIN3_ROW_COUNT, "header_sha256": TRAIN3_HEADER_SHA256, "file_identity_match": True, "header_identity_match": True},
         "selected_column_hash": SELECTED_COLUMN_HASH, "selected_column_count": 24, "file_open_count": 2, "feature_read_pass_count": 1,
         "train3_accessed": True, "train1_feature_values_accessed": False, "train2_feature_values_accessed": False,
         "train4_accessed": False, "test_accessed": False, "labels_accessed": False, "attacks_accessed": False,
         "p2_p3_p4_values_accessed": False, "br2_pair_results_accessed": False,
         "candidate_provenance_visible_during_confirmation": False, "d1_private_ledgers_accessed": True,
         "d1_private_ledgers_modified": False, "raw_train3_values_persisted": False, "raw_windows_persisted": False,
         "event_timestamps_publicly_persisted": False, "absolute_local_paths_persisted": False, "prohibited_access_count": 0}
    ).to_dict()
    result = build_result_v1(directional=directional, pair=pair, arm=arm, access=access, private_ledger_hash=digest)
    receipt = build_execution_receipt_v1(execution_code_commit="1" * 40, prep_merge_commit="2" * 40, scientific_source_hashes={"src/paperworks/profiling/task039d2_real_execution_v1.py": digest}, private_ledger_hash=digest, directional=directional, pair=pair, arm=arm, result=result, access=access)
    artifacts = (access, directional, pair, arm, result, receipt)
    return {item["artifact_type"]: item for item in artifacts}


__all__ = [
    "TASK039D2ExecutionError", "D1PrivateInputsV1", "D2DataAccessStateV1",
    "TASK039D2DataAccessAuditV1", "TASK039D2DirectionalConfirmationSummaryV1",
    "TASK039D2PairConfirmationSummaryV1", "TASK039D2ArmConfirmationSummaryV1",
    "TASK039D2ResultV1", "TASK039D2RealExecutionReceiptV1", "ARTIFACT_CLASSES",
    "ARTIFACT_CLASS_BY_TYPE", "validate_authorization_v1", "validate_external_roots_v1",
    "load_d1_private_inputs_v1", "expected_train3_identity_v1", "load_authorized_train3_values_v1",
    "confirm_relations_one_way_v1", "build_directional_summary_v1", "build_pair_summary_v1",
    "load_provenance_after_outcomes_frozen_v1", "build_arm_summary_v1", "build_data_access_audit_v1",
    "build_result_v1", "build_execution_receipt_v1", "schema_for_d2_artifact_v1",
    "d2_schema_examples_v1", "verify_d2_self_hash_v1", "write_json_v1", "STATUS",
]
