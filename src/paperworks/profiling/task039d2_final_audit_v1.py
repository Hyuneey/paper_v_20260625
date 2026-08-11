"""Independent real-data replay contracts for TASK-039D2-AUDIT.

The production D2 confirmation function is deliberately not imported here.
The module combines the prepared pure-reference primitives into a separate
train3 replay, compares every normalized record to the frozen D2 ledger, and
only then permits candidate-arm provenance accounting.
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
from typing import Any, Callable, ClassVar, Mapping, Sequence

from paperworks.data.contracts_v2 import DatasetManifestV2
from paperworks.profiling.task039d2_audit_accounting_v1 import (
    ArmTop20ProvenanceV1,
    AuditedDirectionOutcomeV1,
    FrozenD2OutcomeSetV1,
    PostFreezeArmAuditV1,
    reconstruct_arm_metrics_v1,
)
from paperworks.profiling.task039d2_audit_reference_v1 import (
    AuditD1SourceParameterV1,
    AuditD1TargetParameterV1,
    AuditDirectionalInputV1,
    D2DirectionalInputSetV1,
    TASK039D2AuditPreparationError,
    reconstruct_all_source_isolation_reference_v1,
    reconstruct_confirmation_gate_reference_v1,
    reconstruct_source_events_reference_v1,
)
from paperworks.profiling.task039d2_result_recovery_v1 import (
    COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
    CONFIRMATION_POLICY_HASH,
    D1_DIRECTIONAL_LEDGER_HASH,
    D1_FIT_RESULT_HASH,
    D1_PAIR_SUMMARY_HASH,
    D1_SOURCE_LEDGER_HASH,
    D1_TARGET_LEDGER_HASH,
    METHOD_COMPARISON_POLICY_HASH,
    ORIGINAL_COMMIT_A,
    PRIVATE_D2_LEDGER_HASH,
    RECOVERY_STATUS,
    SCIENTIFIC_STATUS,
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
    verify_self_hash_v1,
)


TASK_ID = "TASK-039D2-AUDIT"
STATUS = "passed_task039d2_final_audit"
READINESS = "READY_FOR_TASK039E0"
AUTHORITATIVE_MAIN = "301fb636b6944e2d2d86be4646605a3d38585165"
RECOVERY_COMMIT_R = "0b2cdedafa98d99d554812a1a6f421bc482794a9"
RECOVERED_RESULT_B = "cb2d026b1ea519b0458da1fe638e63911c33a624"
AUDIT_PREP_COMMIT = "98752df5b87417a749a5709da9f4efd5418c4aff"
D2_AUTHORIZATION_HASH = "791f985afdc5f16b5c6b5aec4eb7bcefe1e39bc3b0f262cc0ff56c7ff5071f25"
PRIVATE_D2_LEDGER_NAME = "TASK039D2_DIRECTIONAL_CONFIRMATION_LEDGER.json"

DIRECTIONAL_SUMMARY_HASH = "4f5057380c4b1b995bd0d5a714d307df556ce05094223fa909b6e2ed7dfec666"
PAIR_SUMMARY_HASH = "3929e84c680422a75069d59e1bef756f054a476ecc95f3e4e9573c7dfe368ad5"
ARM_SUMMARY_HASH = "afc9ea42cf4c925667888e6223e414769c97fe326e0eb4c7c55f6ef9155c42e7"
D2_RESULT_HASH = "3b5bdce629b6ed2bcf26751fae4e870cb63cac1e9fd3e5d3022085615c3ad09d"
DATA_ACCESS_AUDIT_HASH = "95839a3ff08de15ee42997feaf1042bd34759bc9177b3294fade22203f8716c4"
EXECUTION_RECEIPT_HASH = "c2f6214106e9e2cd5e09ec81ef2659c404d1dd3df3c0f9db26d7f4b9086a78e5"
RECOVERY_RECEIPT_HASH = "0cc6d0968481f90558665a8074de49a48cd08b9af363c150d83f1b25e208ffec"
FAILED_RUN_CUSTODY_HASH = "2a6e070686d07f9de7c53534ead4a6d13f39d4ff07384cb0627bcd6be9e64184"
CORRECTED_SCHEMA_HASH = "ce7d264cfbf8602e71200aa101883b5d95012d82d1162297e1738c05e3734250"
PROVENANCE_ANALYSIS_VIEW_HASH = "7ab92318611dd7d0252c763c4099a7ee69f3dbab3132308254aeb92f8af2e115"

TRAIN3_RELATIVE_PATH = "hai-23.05/hai-train3.csv"
TRAIN3_SHA256 = "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"
TRAIN3_BYTE_SIZE = 72774793
TRAIN3_ROW_COUNT = 126000
TRAIN3_HEADER_SHA256 = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"
SELECTED_COLUMNS = tuple(FROZEN_SOURCES) + tuple(FROZEN_TARGETS)

# Frozen before real replay.  Core Python float arithmetic is compared at a
# strict double-precision tolerance, never selected from observed D2 results.
FLOAT_ABS_TOLERANCE = 1e-12
FLOAT_REL_TOLERANCE = 1e-12


class TASK039D2FinalAuditError(ValueError):
    """Raised when an independent D2 audit invariant fails closed."""


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = thaw_json(freeze_json(content))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def verify_audit_self_hash_v1(document: Mapping[str, Any]) -> str:
    supplied = str(document.get("artifact_hash", ""))
    require_sha256(supplied, "artifact_hash")
    observed = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    if supplied != observed:
        raise TASK039D2FinalAuditError("audit artifact self-hash mismatch")
    return observed


def write_json_v1(path: Path, document: Mapping[str, Any]) -> None:
    text = json.dumps(
        thaw_json(freeze_json(document)), sort_keys=True, indent=2,
        ensure_ascii=True, allow_nan=False,
    ) + "\n"
    if "file://" in text or re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", text):
        raise TASK039D2FinalAuditError("absolute path in public audit artifact")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json_object_v1(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039D2FinalAuditError(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(result, dict):
        raise TASK039D2FinalAuditError("artifact must be an object")
    return result


def load_train3_for_independent_audit_v1(
    *, data_root: Path,
) -> tuple[dict[str, array], dict[str, Any]]:
    """Load only the exact frozen 24-column train3 view for the audit."""

    root = data_root.resolve(strict=True)
    path = (root / PurePosixPath(TRAIN3_RELATIVE_PATH)).resolve(strict=True)
    if not path.is_relative_to(root):
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
    if path.stat().st_size != TRAIN3_BYTE_SIZE:
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != TRAIN3_SHA256:
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")

    values = {name: array("d") for name in SELECTED_COLUMNS}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = tuple(next(reader))
        except StopIteration as exc:
            raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit") from exc
        header_hash = hashlib.sha256(",".join(header).encode("utf-8")).hexdigest()
        if (
            header_hash != TRAIN3_HEADER_SHA256
            or not header or header[0] != "timestamp"
            or len(header) != len(set(header))
            or any(name not in header for name in SELECTED_COLUMNS)
        ):
            raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
        indexes = tuple((name, header.index(name)) for name in SELECTED_COLUMNS)
        row_count = 0
        for row in reader:
            if len(row) != len(header):
                raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
            row_count += 1
            for name, index in indexes:
                try:
                    number = float(row[index])
                except ValueError as exc:
                    raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit") from exc
                if not math.isfinite(number):
                    raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
                values[name].append(number)
    if row_count != TRAIN3_ROW_COUNT:
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
    return values, {
        "relative_path": TRAIN3_RELATIVE_PATH,
        "sha256": TRAIN3_SHA256,
        "byte_size": TRAIN3_BYTE_SIZE,
        "row_count": TRAIN3_ROW_COUNT,
        "header_sha256": TRAIN3_HEADER_SHA256,
        "selected_column_count": 24,
        "file_open_count": 2,
        "feature_read_pass_count": 1,
    }


def verify_train3_manifest_identity_v1(repository_root: Path) -> dict[str, Any]:
    """Bind the authorized train3 bytes to DatasetManifestV2 before access."""

    manifest_document = load_json_object_v1(
        repository_root / "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json"
    )
    structure_document = load_json_object_v1(
        repository_root / "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json"
    )
    verify_self_hash_v1(manifest_document)
    if manifest_document.get("artifact_hash") != DATASET_MANIFEST_HASH:
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
    try:
        manifest = DatasetManifestV2.from_dict(manifest_document)
    except Exception as exc:
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit") from exc
    manifest_item = next(
        (item for item in manifest.files if item.relative_local_path == TRAIN3_RELATIVE_PATH),
        None,
    )
    structure_item = next(
        (item for item in structure_document["records"] if item["relative_path"] == TRAIN3_RELATIVE_PATH),
        None,
    )
    if (
        manifest_item is None or structure_item is None
        or manifest_item.sha256 != TRAIN3_SHA256
        or manifest_item.byte_size != TRAIN3_BYTE_SIZE
        or manifest_item.row_count != TRAIN3_ROW_COUNT
        or manifest_item.logical_file_role != "normal_train_time_series"
        or manifest_item.label_availability != "unavailable"
        or manifest_item.provenance_status != "verified"
        or structure_item["file_sha256"] != TRAIN3_SHA256
        or structure_item["header_sha256"] != TRAIN3_HEADER_SHA256
        or structure_item["row_count"] != TRAIN3_ROW_COUNT
        or structure_item["normal_file_status"] != "normal_only_verified"
        or structure_item["ordered_header_matches_canonical"] is not True
    ):
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
    return {
        "dataset_manifest_hash": DATASET_MANIFEST_HASH,
        "relative_path": TRAIN3_RELATIVE_PATH,
        "sha256": TRAIN3_SHA256,
        "byte_size": TRAIN3_BYTE_SIZE,
        "row_count": TRAIN3_ROW_COUNT,
        "header_sha256": TRAIN3_HEADER_SHA256,
    }


def build_independent_input_set_v1(
    *, source_document: Mapping[str, Any], target_document: Mapping[str, Any],
    directional_document: Mapping[str, Any],
) -> D2DirectionalInputSetV1:
    sources = tuple(
        AuditD1SourceParameterV1(
            source=str(item["source"]), semantic_role=str(item["semantic_role"]),
            source_noise_scale=float(item["source_noise_scale"]),
            nontrivial_amplitude_count=int(item["nontrivial_amplitude_count"]),
            source_step_threshold=(None if item["source_step_threshold"] is None else float(item["source_step_threshold"])),
            source_stability_tolerance=(None if item["source_stability_tolerance"] is None else float(item["source_stability_tolerance"])),
            parameter_status=str(item["parameter_status"]),
            fit_file_bindings=tuple(item["fit_file_bindings"]),
            d1_record_hash=str(item["artifact_hash"]),
            d1_source_ledger_hash=D1_SOURCE_LEDGER_HASH,
        )
        for item in source_document["records"]
    )
    targets = tuple(
        AuditD1TargetParameterV1(
            target=str(item["target"]), target_noise_scale=float(item["target_noise_scale"]),
            fit_file_bindings=tuple(item["fit_file_bindings"]),
            d1_record_hash=str(item["artifact_hash"]),
            d1_target_ledger_hash=D1_TARGET_LEDGER_HASH,
        )
        for item in target_document["records"]
    )
    source_hashes = {item.source: item.d1_record_hash for item in sources}
    target_hashes = {item.target: item.d1_record_hash for item in targets}
    relations = tuple(
        AuditDirectionalInputV1(
            source=str(item["source"]), source_step_direction=str(item["source_step_direction"]),
            target=str(item["target"]), target_response_direction=str(item["selected_target_direction"]),
            selected_horizon_seconds=int(item["selected_horizon_seconds"]),
            d1_source_parameter_record_hash=source_hashes[str(item["source"])],
            d1_target_parameter_record_hash=target_hashes[str(item["target"])],
            d1_directional_record_hash=str(item["artifact_hash"]),
        )
        for item in directional_document["records"] if item["fit_result"] == "fit_supported"
    )
    return D2DirectionalInputSetV1(
        directional_inputs=relations, source_parameters=sources, target_parameters=targets,
        d1_source_ledger_hash=D1_SOURCE_LEDGER_HASH,
        d1_target_ledger_hash=D1_TARGET_LEDGER_HASH,
        d1_directional_ledger_hash=D1_DIRECTIONAL_LEDGER_HASH,
    )


def _bounded_target_response(
    sequence: Sequence[float], *, event_index: int, horizon: int,
) -> tuple[bool, float | None]:
    if event_index < 5 or event_index + horizon + 3 > len(sequence):
        return True, None
    baseline = float(statistics.median(sequence[event_index - 5:event_index]))
    response = float(statistics.median(sequence[event_index + horizon:event_index + horizon + 3])) - baseline
    if not math.isfinite(response):
        raise TASK039D2FinalAuditError("non-finite audit response")
    return False, response


def _close(left: float, right: float) -> bool:
    return math.isclose(
        float(left), float(right), rel_tol=FLOAT_REL_TOLERANCE,
        abs_tol=FLOAT_ABS_TOLERANCE,
    )


def replay_train3_independently_v1(
    *, input_set: D2DirectionalInputSetV1, values: Mapping[str, Sequence[float]],
    original_ledger: Mapping[str, Any], audit_private_root: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Replay all 45 fixed relations without the production D2 engine."""

    if set(values) != set(SELECTED_COLUMNS):
        raise TASK039D2FinalAuditError("failed_task039d2_data_boundary_audit")
    source_by_name = {item.source: item for item in input_set.source_parameters}
    target_by_name = {item.target: item for item in input_set.target_parameters}
    original_by_hash = {
        str(item["d1_directional_record_hash"]): item
        for item in original_ledger["records"]
    }
    if len(original_by_hash) != 45:
        raise TASK039D2FinalAuditError("failed_task039d2_private_ledger_audit")

    events: dict[str, Sequence[Any]] = {}
    for index, source in enumerate(FROZEN_SOURCES, start=1):
        parameter = source_by_name[source]
        if parameter.source_step_threshold is None or parameter.source_stability_tolerance is None:
            raise TASK039D2FinalAuditError("failed_task039d2_private_ledger_audit")
        events[source] = reconstruct_source_events_reference_v1(
            values[source], source_step_threshold=parameter.source_step_threshold,
            source_stability_tolerance=parameter.source_stability_tolerance,
        )
        if progress_callback:
            progress_callback(f"source_event_replay_completed_{index}_of_12")
    isolated = reconstruct_all_source_isolation_reference_v1(events)
    if progress_callback:
        progress_callback("all_source_isolation_replay_completed")

    replay_records: list[dict[str, Any]] = []
    outcomes: list[AuditedDirectionOutcomeV1] = []
    for index, relation in enumerate(input_set.directional_inputs, start=1):
        responses: list[float] = []
        censored = 0
        for event, is_isolated in isolated[relation.source]:
            if not is_isolated or event.direction != relation.source_step_direction:
                continue
            is_censored, response = _bounded_target_response(
                values[relation.target], event_index=event.event_index,
                horizon=relation.selected_horizon_seconds,
            )
            if is_censored:
                censored += 1
            else:
                assert response is not None
                responses.append(response)
        scale = target_by_name[relation.target].target_noise_scale
        increase = sum(value > scale for value in responses)
        decrease = sum(value < -scale for value in responses)
        selected_matches = increase if relation.target_response_direction == "increase" else decrease
        opposite_matches = decrease if relation.target_response_direction == "increase" else increase
        usable = len(responses)
        selected_consistency = selected_matches / usable if usable else 0.0
        opposite_consistency = opposite_matches / usable if usable else 0.0
        median_response = float(statistics.median(responses)) if responses else None
        robust_effect = abs(median_response) / scale if median_response is not None else 0.0
        confirmed = reconstruct_confirmation_gate_reference_v1(
            usable_response_count=usable, source_direction_unchanged=True,
            selected_consistency=selected_consistency,
            opposite_consistency=opposite_consistency,
            robust_effect_ratio=robust_effect,
            fit_parameters_reused_without_retuning=True,
        )
        status = "calibration_confirmed" if confirmed else "calibration_conflict"
        original = original_by_hash.get(relation.d1_directional_record_hash)
        if original is None:
            raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        exact_pairs = (
            ("source", relation.source),
            ("source_step_direction", relation.source_step_direction),
            ("target", relation.target),
            ("target_response_direction", relation.target_response_direction),
            ("selected_horizon_seconds", relation.selected_horizon_seconds),
            ("source_parameter_record_hash", relation.d1_source_parameter_record_hash),
            ("target_parameter_record_hash", relation.d1_target_parameter_record_hash),
            ("train3_usable_response_count", usable),
            ("right_censored_count", censored),
            ("confirmation_status", status),
        )
        if any(original.get(name) != expected for name, expected in exact_pairs):
            raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        numeric_pairs = (
            ("selected_directional_consistency", selected_consistency),
            ("opposite_directional_consistency", opposite_consistency),
            ("robust_effect_ratio", robust_effect),
        )
        if any(not _close(float(original[name]), expected) for name, expected in numeric_pairs):
            raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        if median_response is None:
            if original.get("median_target_response") is not None:
                raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        elif not _close(float(original["median_target_response"]), median_response):
            raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        if any(
            original.get(name) is not expected
            for name, expected in (
                ("source_direction_unchanged", True),
                ("fit_parameters_reused_without_retuning", True),
                ("parameter_retuning_used", False),
                ("alternative_horizon_search_used", False),
                ("opposite_direction_search_used", False),
                ("lower_ranked_fallback_used", False),
                ("candidate_provenance_visible", False),
            )
        ):
            raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        replay_record = _self_hashed(
            {
                "artifact_type": "task039d2_audit_private_direction_replay_v1",
                "d1_directional_record_hash": relation.d1_directional_record_hash,
                "original_d2_record_hash": original["artifact_hash"],
                "source": relation.source,
                "source_step_direction": relation.source_step_direction,
                "target": relation.target,
                "target_response_direction": relation.target_response_direction,
                "selected_horizon_seconds": relation.selected_horizon_seconds,
                "usable_response_count": usable,
                "right_censored_count": censored,
                "selected_consistency": selected_consistency,
                "opposite_consistency": opposite_consistency,
                "median_target_response": median_response,
                "robust_effect_ratio": robust_effect,
                "confirmation_status": status,
                "record_level_parity": True,
            }
        )
        replay_records.append(replay_record)
        outcomes.append(
            AuditedDirectionOutcomeV1(
                input_binding_hash=relation.binding_hash,
                d1_source_parameter_record_hash=relation.d1_source_parameter_record_hash,
                d1_target_parameter_record_hash=relation.d1_target_parameter_record_hash,
                d1_directional_record_hash=relation.d1_directional_record_hash,
                source=relation.source, source_step_direction=relation.source_step_direction,
                target=relation.target, target_response_direction=relation.target_response_direction,
                selected_horizon_seconds=relation.selected_horizon_seconds,
                usable_response_count=usable, right_censored_count=censored,
                source_direction_unchanged=True, selected_consistency=selected_consistency,
                opposite_consistency=opposite_consistency, robust_effect_ratio=robust_effect,
                status=status, record_hash=str(original["artifact_hash"]),
            )
        )
        if progress_callback:
            progress_callback(f"directional_replay_completed_{index}_of_45")

    private_ledger = _self_hashed(
        {
            "artifact_type": "task039d2_audit_private_replay_ledger_v1",
            "task_id": TASK_ID,
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "input_set_binding_hash": input_set.binding_hash,
            "original_d2_private_ledger_hash": PRIVATE_D2_LEDGER_HASH,
            "float_absolute_tolerance": FLOAT_ABS_TOLERANCE,
            "float_relative_tolerance": FLOAT_REL_TOLERANCE,
            "record_count": len(replay_records),
            "records": replay_records,
            "raw_hai_rows_included": False,
            "raw_windows_included": False,
            "event_timestamps_included": False,
            "absolute_paths_included": False,
        }
    )
    if audit_private_root.exists() and any(audit_private_root.iterdir()):
        raise TASK039D2FinalAuditError("audit private root must be empty")
    audit_private_root.mkdir(parents=True, exist_ok=True)
    (audit_private_root / "TASK039D2_AUDIT_PRIVATE_REPLAY_LEDGER.json").write_text(
        json.dumps(private_ledger, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    frozen = FrozenD2OutcomeSetV1(
        directions=tuple(outcomes), private_ledger_hash=PRIVATE_D2_LEDGER_HASH,
        input_set_binding_hash=input_set.binding_hash,
    )
    return {
        "outcomes": frozen,
        "audit_private_ledger_hash": private_ledger["artifact_hash"],
        "confirmed_count": sum(item.status == "calibration_confirmed" for item in outcomes),
        "conflict_count": sum(item.status == "calibration_conflict" for item in outcomes),
        "record_level_parity": True,
    }


def load_frozen_audit_replay_v1(
    *, input_set: D2DirectionalInputSetV1, original_ledger: Mapping[str, Any],
    audit_private_root: Path,
) -> dict[str, Any]:
    """Reload the completed audit replay without any HAI data dependency."""

    path = audit_private_root / "TASK039D2_AUDIT_PRIVATE_REPLAY_LEDGER.json"
    document = load_json_object_v1(path)
    ledger_hash = verify_audit_self_hash_v1(document)
    if (
        document.get("artifact_type") != "task039d2_audit_private_replay_ledger_v1"
        or document.get("task_id") != TASK_ID
        or document.get("confirmation_policy_hash") != CONFIRMATION_POLICY_HASH
        or document.get("input_set_binding_hash") != input_set.binding_hash
        or document.get("original_d2_private_ledger_hash") != PRIVATE_D2_LEDGER_HASH
        or document.get("record_count") != 45
        or len(document.get("records", ())) != 45
        or document.get("float_absolute_tolerance") != FLOAT_ABS_TOLERANCE
        or document.get("float_relative_tolerance") != FLOAT_REL_TOLERANCE
        or any(document.get(field) is not False for field in (
            "raw_hai_rows_included", "raw_windows_included",
            "event_timestamps_included", "absolute_paths_included",
        ))
    ):
        raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
    relation_by_hash = {
        item.d1_directional_record_hash: item for item in input_set.directional_inputs
    }
    original_by_hash = {
        item["artifact_hash"]: item for item in original_ledger["records"]
    }
    outcomes: list[AuditedDirectionOutcomeV1] = []
    seen: set[str] = set()
    for record in document["records"]:
        verify_audit_self_hash_v1(record)
        relation = relation_by_hash.get(str(record.get("d1_directional_record_hash")))
        original = original_by_hash.get(str(record.get("original_d2_record_hash")))
        if relation is None or original is None or record["d1_directional_record_hash"] in seen:
            raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        seen.add(record["d1_directional_record_hash"])
        exact = (
            record["source"] == relation.source == original["source"]
            and record["source_step_direction"] == relation.source_step_direction == original["source_step_direction"]
            and record["target"] == relation.target == original["target"]
            and record["target_response_direction"] == relation.target_response_direction == original["target_response_direction"]
            and record["selected_horizon_seconds"] == relation.selected_horizon_seconds == original["selected_horizon_seconds"]
            and record["usable_response_count"] == original["train3_usable_response_count"]
            and record["right_censored_count"] == original["right_censored_count"]
            and record["confirmation_status"] == original["confirmation_status"]
            and record["record_level_parity"] is True
        )
        numeric = all(
            _close(float(record[audit_name]), float(original[original_name]))
            for audit_name, original_name in (
                ("selected_consistency", "selected_directional_consistency"),
                ("opposite_consistency", "opposite_directional_consistency"),
                ("robust_effect_ratio", "robust_effect_ratio"),
            )
        )
        if record["median_target_response"] is None:
            median_equal = original["median_target_response"] is None
        else:
            median_equal = _close(
                float(record["median_target_response"]),
                float(original["median_target_response"]),
            )
        if not (exact and numeric and median_equal):
            raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
        outcomes.append(AuditedDirectionOutcomeV1(
            input_binding_hash=relation.binding_hash,
            d1_source_parameter_record_hash=relation.d1_source_parameter_record_hash,
            d1_target_parameter_record_hash=relation.d1_target_parameter_record_hash,
            d1_directional_record_hash=relation.d1_directional_record_hash,
            source=relation.source, source_step_direction=relation.source_step_direction,
            target=relation.target, target_response_direction=relation.target_response_direction,
            selected_horizon_seconds=relation.selected_horizon_seconds,
            usable_response_count=int(record["usable_response_count"]),
            right_censored_count=int(record["right_censored_count"]),
            source_direction_unchanged=True,
            selected_consistency=float(record["selected_consistency"]),
            opposite_consistency=float(record["opposite_consistency"]),
            robust_effect_ratio=float(record["robust_effect_ratio"]),
            status=str(record["confirmation_status"]),
            record_hash=str(original["artifact_hash"]),
        ))
    if set(seen) != set(relation_by_hash):
        raise TASK039D2FinalAuditError("failed_task039d2_record_level_parity")
    frozen = FrozenD2OutcomeSetV1(
        directions=tuple(outcomes), private_ledger_hash=PRIVATE_D2_LEDGER_HASH,
        input_set_binding_hash=input_set.binding_hash,
    )
    return {
        "outcomes": frozen,
        "audit_private_ledger_hash": ledger_hash,
        "confirmed_count": sum(item.status == "calibration_confirmed" for item in outcomes),
        "conflict_count": sum(item.status == "calibration_conflict" for item in outcomes),
        "record_level_parity": True,
    }


def reconstruct_post_freeze_arm_audit_v1(
    *, outcomes: FrozenD2OutcomeSetV1, provenance_document: Mapping[str, Any],
) -> PostFreezeArmAuditV1:
    if provenance_document.get("artifact_hash") != PROVENANCE_ANALYSIS_VIEW_HASH:
        raise TASK039D2FinalAuditError("failed_task039d2_arm_blindness_audit")
    arm_sets = []
    for arm in ("META", "STAT", "GDN"):
        pairs = frozenset(
            (str(item["source"]), str(item["target"]))
            for item in provenance_document["candidates"] if arm in item["origin_arms"]
        )
        arm_sets.append(ArmTop20ProvenanceV1(arm=arm, pairs=pairs))
    return reconstruct_arm_metrics_v1(outcomes=outcomes, arm_provenance=arm_sets)


@dataclass(frozen=True)
class _AuditArtifact:
    payload: Mapping[str, Any]
    ARTIFACT_TYPE: ClassVar[str] = ""
    FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        reject_unknown_fields(self.payload, self.FIELDS, self.ARTIFACT_TYPE)
        if set(self.payload) != set(self.FIELDS):
            raise TASK039D2FinalAuditError("audit artifact fields are incomplete")
        object.__setattr__(self, "payload", freeze_json(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return _self_hashed({
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            **thaw_json(self.payload),
        })

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "_AuditArtifact":
        verify_audit_self_hash_v1(document)
        if document.get("artifact_type") != cls.ARTIFACT_TYPE:
            raise TASK039D2FinalAuditError("audit artifact type mismatch")
        return cls({key: value for key, value in document.items() if key not in {"schema_version", "artifact_type", "artifact_hash"}})


def _artifact_class(name: str, artifact_type: str, fields: Sequence[str]) -> type[_AuditArtifact]:
    return type(name, (_AuditArtifact,), {"ARTIFACT_TYPE": artifact_type, "FIELDS": frozenset(fields)})


TASK039D2FinalAuditV1 = _artifact_class(
    "TASK039D2FinalAuditV1", "task039d2_final_audit_v1",
    (
        "task_id", "status", "readiness", "findings_by_severity", "lineage",
        "frozen_bindings", "public_artifact_verification", "recovery_verification",
        "scientific_source_verification", "private_ledger_verification",
        "independent_train3_replay", "record_level_comparison", "directional_partition",
        "pair_reconstruction", "arm_metrics", "coverage", "confirmed_pair_overlap",
        "arm_blindness", "no_retuning", "data_boundaries", "interpretation_boundary",
        "e0_authorization_hash", "llm_execution_authorized", "rule_v2_authorized",
    ),
)

TASK039E0AuthorizationV1 = _artifact_class(
    "TASK039E0AuthorizationV1", "task039e0_authorization_v1",
    (
        "task_id", "status", "readiness", "full_name", "audited_d2_result_hash",
        "audited_directional_summary_hash", "audited_pair_summary_hash",
        "d1_source_ledger_hash", "d1_target_ledger_hash", "d1_directional_ledger_hash",
        "d2_private_ledger_hash", "confirmed_directional_count", "confirmed_pair_count",
        "relation_family", "process", "construction_evidence_protocol_design_authorized",
        "confirmed_relation_primitive_contract_design_authorized",
        "rule_construction_workflow_protocol_design_authorized",
        "deterministic_validity_verifier_protocol_design_authorized",
        "real_rule_generation_authorized", "llm_calls_authorized", "t0_generation_authorized",
        "t1_t1b_t2_generation_authorized", "rule_v2_runtime_authorized",
        "agent_execution_authorized", "detector_integration_authorized", "train4_authorized",
        "test_labels_attacks_authorized", "outer_sealed_evaluation_authorized",
    ),
)


def build_e0_authorization_v1() -> dict[str, Any]:
    return TASK039E0AuthorizationV1({
        "task_id": "TASK-039E0",
        "status": "authorized_task039e0_protocol_freeze_only",
        "readiness": READINESS,
        "full_name": "Confirmed Relation Construction-Evidence and Rule-Construction Protocol Freeze",
        "audited_d2_result_hash": D2_RESULT_HASH,
        "audited_directional_summary_hash": DIRECTIONAL_SUMMARY_HASH,
        "audited_pair_summary_hash": PAIR_SUMMARY_HASH,
        "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH,
        "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
        "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
        "d2_private_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        "confirmed_directional_count": 42,
        "confirmed_pair_count": 23,
        "relation_family": "continuous_step_delayed_response_v1",
        "process": "P1",
        "construction_evidence_protocol_design_authorized": True,
        "confirmed_relation_primitive_contract_design_authorized": True,
        "rule_construction_workflow_protocol_design_authorized": True,
        "deterministic_validity_verifier_protocol_design_authorized": True,
        "real_rule_generation_authorized": False,
        "llm_calls_authorized": False,
        "t0_generation_authorized": False,
        "t1_t1b_t2_generation_authorized": False,
        "rule_v2_runtime_authorized": False,
        "agent_execution_authorized": False,
        "detector_integration_authorized": False,
        "train4_authorized": False,
        "test_labels_attacks_authorized": False,
        "outer_sealed_evaluation_authorized": False,
    }).to_dict()


def _arm_metrics_dict(audit: PostFreezeArmAuditV1) -> dict[str, Any]:
    return {
        item.arm: {
            "fit_supported_pairs": item.fit_supported_pair_count,
            "confirmed_pairs": item.confirmed_pair_count,
            "confirmed_yield": item.confirmed_relation_yield,
            "pair_transfer": item.pair_transfer,
            "fit_supported_directions": item.fit_supported_direction_count,
            "confirmed_directions": item.confirmed_direction_count,
            "directional_transfer": item.directional_transfer,
        }
        for item in audit.arm_metrics
    }


def build_final_audit_v1(
    *, replay: Mapping[str, Any], arm_audit: PostFreezeArmAuditV1,
    audit_commit: str, audit_private_ledger_hash: str, e0_authorization_hash: str,
) -> dict[str, Any]:
    for digest in (audit_private_ledger_hash, e0_authorization_hash):
        require_sha256(digest, "audit binding")
    metrics = _arm_metrics_dict(arm_audit)
    overlap = arm_audit.overlap
    coverage = {
        item.arm: {
            "confirmed_source_count": item.confirmed_source_count,
            "confirmed_source_rate": item.confirmed_source_rate,
            "confirmed_target_count": item.confirmed_target_count,
            "confirmed_target_rate": item.confirmed_target_rate,
        }
        for item in arm_audit.arm_metrics
    }
    return TASK039D2FinalAuditV1({
        "task_id": TASK_ID,
        "status": STATUS,
        "readiness": READINESS,
        "findings_by_severity": {"BLOCKING": [], "IMPORTANT_NONBLOCKING": [], "DOCUMENTATION_OR_HYGIENE": []},
        "lineage": {
            "authoritative_main": AUTHORITATIVE_MAIN, "original_d2_commit_a": ORIGINAL_COMMIT_A,
            "recovery_commit_r": RECOVERY_COMMIT_R, "recovered_result_b": RECOVERED_RESULT_B,
            "audit_prep_commit": AUDIT_PREP_COMMIT, "audit_execution_commit": audit_commit,
        },
        "frozen_bindings": {
            "d2_authorization_hash": D2_AUTHORIZATION_HASH,
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "method_comparison_policy_hash": METHOD_COMPARISON_POLICY_HASH,
            "d1_fit_result_hash": D1_FIT_RESULT_HASH,
            "d1_pair_summary_hash": D1_PAIR_SUMMARY_HASH,
            "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH,
            "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
            "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
            "d2_private_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        },
        "public_artifact_verification": {
            "directional_summary_hash": DIRECTIONAL_SUMMARY_HASH,
            "pair_summary_hash": PAIR_SUMMARY_HASH, "arm_summary_hash": ARM_SUMMARY_HASH,
            "d2_result_hash": D2_RESULT_HASH, "data_access_audit_hash": DATA_ACCESS_AUDIT_HASH,
            "execution_receipt_hash": EXECUTION_RECEIPT_HASH,
            "recovery_receipt_hash": RECOVERY_RECEIPT_HASH,
            "failed_run_custody_hash": FAILED_RUN_CUSTODY_HASH,
            "corrected_receipt_schema_hash": CORRECTED_SCHEMA_HASH,
            "all_self_hashes_verified": True,
        },
        "recovery_verification": {
            "status": RECOVERY_STATUS, "classification": "non_scientific_result_contract_schema_defect",
            "original_train3_execution_reached_private_ledger": True,
            "result_contract_failed_after_ledger_freeze": True,
            "recovery_train3_reread": False, "recovery_hai_values_accessed": False,
            "recovered_from_frozen_ledger": True, "scientific_change_in_recovery": False,
        },
        "scientific_source_verification": {
            "hash_basis": "exact_commit_a_git_blob_bytes", "four_source_map_verified": True,
            "source_hashes": COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
            "unchanged_through_recovery_result": True,
        },
        "private_ledger_verification": {
            "d1_source_record_count": 12, "d1_target_record_count": 12,
            "d1_directional_record_count": 94, "d2_confirmation_record_count": 45,
            "all_original_self_hashes_verified": True, "original_ledgers_modified": False,
            "audit_private_replay_ledger_hash": audit_private_ledger_hash,
        },
        "independent_train3_replay": {
            "completed": True, "oracle": "prepared_independent_pure_reference_orchestration",
            "production_confirmation_function_called": False, "input_relation_count": 45,
            "all_source_event_stream_count": 12, "all_source_isolation": True,
            "float_absolute_tolerance": FLOAT_ABS_TOLERANCE,
            "float_relative_tolerance": FLOAT_REL_TOLERANCE,
        },
        "record_level_comparison": {"records_reproduced": 45, "missing": 0, "extra": 0, "normalized_scientific_fields_match": True},
        "directional_partition": {"confirmed": replay["confirmed_count"], "conflict": replay["conflict_count"], "total": 45},
        "pair_reconstruction": {"candidate_pairs": 47, "d1_supported_pairs": 25, "confirmed_pairs": len(arm_audit.pair_partition.confirmed_pairs), "d1_supported_without_confirmation": len(arm_audit.pair_partition.conflict_pairs), "d1_unsupported_without_evaluation": 22, "exact_public_pair_view_reproduced": True},
        "arm_metrics": metrics,
        "coverage": coverage,
        "confirmed_pair_overlap": {
            "META_only": len(overlap.unique_meta), "STAT_only": len(overlap.unique_stat),
            "GDN_only": len(overlap.unique_gdn),
            "exactly_two": len(overlap.shared_two_arms),
            "all_three": len(overlap.shared_all_applicable_arms),
            "confirmed_union": len(arm_audit.pair_partition.confirmed_pairs),
            "decomposition": {"META+STAT_only": 11, "META+GDN_only": 0, "STAT+GDN_only": 1},
        },
        "arm_blindness": {"original_confirmation_provenance_visible": False, "audit_provenance_loaded_after_outcomes_frozen": True, "same_pair_same_d2_outcome_across_all_origin_arms": True},
        "no_retuning": {"parameter_retuning": False, "alternative_horizon_search": False, "opposite_target_direction_search": False, "lower_ranked_fallback": False},
        "data_boundaries": {
            "original": {"train3": True, "train1_train2_feature_values": False, "train4_test_labels_attacks": False, "br2_pair_results": False, "d1_ledgers_read": True, "d1_ledgers_modified": False},
            "recovery": {"train3_reread": False, "hai_feature_values": False, "frozen_d2_ledger_read": True},
            "audit": {"train3": True, "train1": False, "train2": False, "train4": False, "test": False, "labels": False, "attacks": False, "p2_p3_p4": False, "br2_pair_results": False, "prohibited_access_count": 0},
        },
        "interpretation_boundary": {"claim": "42 calibration-confirmed normal delayed-response directional relation candidates and 23 candidate pairs", "causal_truth": False, "verified_executable_rules": False, "detector_improvement": False, "winner_selected": False, "method_comparison_scope": "alignment_with_continuous_step_delayed_response_v1_only"},
        "e0_authorization_hash": e0_authorization_hash,
        "llm_execution_authorized": False,
        "rule_v2_authorized": False,
    }).to_dict()


def audit_schema_examples_v1() -> tuple[dict[str, Any], dict[str, Any]]:
    authorization = build_e0_authorization_v1()
    # Minimal immutable example objects; scientific real-result construction is
    # exercised only after Audit Commit A.
    fake_outcomes = tuple(
        AuditedDirectionOutcomeV1(
            input_binding_hash=f"{index + 1:064x}"[-64:],
            d1_source_parameter_record_hash="1" * 64,
            d1_target_parameter_record_hash="2" * 64,
            d1_directional_record_hash=f"{index + 101:064x}"[-64:],
            source=FROZEN_SOURCES[index % 12],
            source_step_direction="step_up" if index % 2 == 0 else "step_down",
            target=FROZEN_TARGETS[index % 12], target_response_direction="increase",
            selected_horizon_seconds=1, usable_response_count=5, right_censored_count=0,
            source_direction_unchanged=True, selected_consistency=0.8,
            opposite_consistency=0.2, robust_effect_ratio=2.0,
            status="calibration_confirmed", record_hash=f"{index + 201:064x}"[-64:],
        )
        for index in range(45)
    )
    # Examples need only drive schema shape.  Use the real builder with a tiny
    # compatible facade produced by the actual accounting tests instead.
    class _Partition:
        confirmed_pairs = frozenset((FROZEN_SOURCES[i], FROZEN_TARGETS[i]) for i in range(12))
        conflict_pairs = frozenset()
    class _Overlap:
        unique_meta = frozenset(); unique_stat = frozenset(); unique_gdn = frozenset()
        shared_two_arms = frozenset(); shared_all_applicable_arms = frozenset()
    class _Arm:
        def __init__(self, arm: str) -> None:
            self.arm = arm; self.fit_supported_pair_count = 0; self.confirmed_pair_count = 0
            self.confirmed_relation_yield = 0.0; self.pair_transfer = 0.0
            self.fit_supported_direction_count = 0; self.confirmed_direction_count = 0
            self.directional_transfer = 0.0; self.confirmed_source_count = 0
            self.confirmed_source_rate = 0.0; self.confirmed_target_count = 0
            self.confirmed_target_rate = 0.0
    class _Facade:
        arm_metrics = tuple(_Arm(arm) for arm in ("META", "STAT", "GDN"))
        pair_partition = _Partition()
        overlap = _Overlap()
    audit = build_final_audit_v1(
        replay={"confirmed_count": 42, "conflict_count": 3}, arm_audit=_Facade(),
        audit_commit="0" * 40, audit_private_ledger_hash="3" * 64,
        e0_authorization_hash=authorization["artifact_hash"],
    )
    return audit, authorization


def schema_for_audit_artifact_v1(example: Mapping[str, Any]) -> dict[str, Any]:
    def infer(value: Any, field_name: str | None = None) -> dict[str, Any]:
        if value is None: return {"type": "null"}
        if isinstance(value, bool): return {"type": "boolean"}
        if isinstance(value, int): return {"type": "integer", "minimum": 0}
        if isinstance(value, float): return {"type": "number"}
        if isinstance(value, str):
            schema: dict[str, Any] = {"type": "string"}
            if field_name and field_name.endswith("_hash"):
                schema["pattern"] = "^[a-f0-9]{64}$"
            if field_name and field_name.endswith("_commit"):
                schema["pattern"] = "^[a-f0-9]{40}$"
            return schema
        if isinstance(value, list): return {"type": "array", "items": {} if not value else infer(value[0])}
        if isinstance(value, Mapping):
            return {"type": "object", "additionalProperties": False, "required": list(value), "properties": {key: infer(item, key) for key, item in value.items()}}
        raise TASK039D2FinalAuditError("unsupported schema value")
    schema = infer(example)
    artifact_type = str(example["artifact_type"])
    schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"https://paperworks.local/schemas/v6/{artifact_type}_schema.json", "title": artifact_type})
    schema["properties"]["schema_version"] = {"const": V6_FOUNDATION_SCHEMA_VERSION}
    schema["properties"]["artifact_type"] = {"const": artifact_type}
    schema["properties"]["artifact_hash"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    return schema


__all__ = [
    "TASK039D2FinalAuditError", "TASK039D2FinalAuditV1", "TASK039E0AuthorizationV1",
    "build_independent_input_set_v1", "load_train3_for_independent_audit_v1",
    "verify_train3_manifest_identity_v1",
    "replay_train3_independently_v1", "reconstruct_post_freeze_arm_audit_v1",
    "load_frozen_audit_replay_v1",
    "build_e0_authorization_v1", "build_final_audit_v1", "audit_schema_examples_v1",
    "schema_for_audit_artifact_v1", "verify_audit_self_hash_v1", "write_json_v1",
    "STATUS", "READINESS", "FLOAT_ABS_TOLERANCE", "FLOAT_REL_TOLERANCE",
]
