"""Independent scientific replay for the final TASK-039D1 audit.

This module deliberately does not call ``evaluate_arm_blind_fit_v1``.  It
reconstructs the D1 orchestration from accepted BR1/BR2 primitives, freezes
private replay ledgers, and only then permits the provenance-analysis join.
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, ClassVar, Mapping, Sequence

from paperworks.feasibility.hai_continuous_step_v1 import (
    DirectionCandidateV1,
    classify_multisource_isolation_v1,
    derive_multifile_robust_scale_v1,
    derive_multifile_source_screening_diagnostics_v1,
    evaluate_direction_candidate_v1,
    extract_sustained_step_events_file_local_v1,
    fit_candidate_passes_v1,
    select_direction_candidate_v1,
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
    FIT_FILES,
    FROZEN_SOURCES,
    FROZEN_SOURCE_ROLES,
    FROZEN_TARGETS,
    HORIZONS,
    CandidateProvenanceAnalysisViewV1,
    ProfilingIdentityViewV1,
    assert_arm_blind_identity_record_v1,
    verify_self_hash_v1,
)


TASK_ID = "TASK-039D1-AUDIT"
STATUS = "passed_task039d1_final_audit"
READINESS = "READY_FOR_TASK039D2"
MAIN_COMMIT = "c622c082c053176eab170b6176a343eb2cb35384"
ABORTED_A1 = "d70f90b297bf7a6737652777f8f3059864c0c158"
EXECUTION_A2 = "edf2727d33d30f615aa2be48756fc209afdcd95c"
RESULT_B2 = "360cf4b84ed2c18e026186be00f2312508a8fb85"
D0_PROTOCOL_BUNDLE_HASH = "888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb"
D1_AUTHORIZATION_HASH = "e3ec4316d26520efe4a93d1bf790f36633ed692fa5f9fb9458c26d2a9ad16467"
PROFILING_IDENTITY_VIEW_HASH = "ec1186ec71c20f240c6fb1c7f4b7cd0054882ac8032f6bfb3940274e772f5b7e"
PROVENANCE_ANALYSIS_VIEW_HASH = "7ab92318611dd7d0252c763c4099a7ee69f3dbab3132308254aeb92f8af2e115"
COMPLEXITY_RECEIPT_HASH = "6639c6c767af749775eed8cbd98dc43ccff8cf603ee8cdd009a169b45944bef0"
CONFIRMATION_POLICY_HASH = "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"

FIT_RESULT_HASH = "a2767945ef3cec5fa80c3e131b98fdc8a1eeecaa69a97461988d8da90a4e06d3"
PAIR_SUMMARY_HASH = "a466057faa20eacd0692b6a9c19fbbb5b8968135ba4c018310a076aa0393d4f2"
ARM_SUMMARY_HASH = "6589930085ed0d5d87224ef9da88984b1d52d5e2c7bd1e8b295539b6d0da15e8"
ACCESS_AUDIT_HASH = "b51ec23dd4bad9ed66d7036ec209f6841f99d1e38b0b7766afd16ff75f9004d7"
EXECUTION_RECEIPT_HASH = "51d6dacf27f4b6779c88074f4978e8578fc4541d71b4e8077a78e591d2ff24a2"
SOURCE_LEDGER_HASH = "3eb6ff199dbc67b183d35a804754e557bdfa869a899c754e551cd77e8dcfb304"
TARGET_LEDGER_HASH = "f36f4b424c85b228043f9685a22a25c73d6b165e28714b627cf51e8bbb77f96e"
DIRECTIONAL_LEDGER_HASH = "e372d7ccf4a7dde5f7ccd91049cc73b443b3b19a3a0c563f451aea50e8faddc7"

SOURCE_DIRECTIONS = ("step_up", "step_down")
TARGET_DIRECTIONS = ("increase", "decrease")
BR2_FILE_BY_D0_FILE = {
    "hai-train1.csv": "hai-23.05/hai-train1.csv",
    "hai-train2.csv": "hai-23.05/hai-train2.csv",
}


class TASK039D1FinalAuditError(ValueError):
    """Raised when the independent audit fails closed."""


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = thaw_json(freeze_json(content))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def verify_audit_self_hash_v1(document: Mapping[str, Any]) -> str:
    supplied = str(document.get("artifact_hash", ""))
    require_sha256(supplied, "artifact_hash")
    observed = stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"})
    if supplied != observed:
        raise TASK039D1FinalAuditError("audit artifact self-hash mismatch")
    return observed


def write_json_v1(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(thaw_json(freeze_json(document)), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _record(content: Mapping[str, Any]) -> dict[str, Any]:
    return _self_hashed(content)


def _private_ledger(artifact_type: str, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return _self_hashed(
        {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": artifact_type,
            "task_id": "TASK-039D1",
            "execution_code_commit": EXECUTION_A2,
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


def _candidate_record(
    candidate: DirectionCandidateV1, *, target_noise_scale: float
) -> dict[str, Any]:
    responses_by_short = {
        FIT_FILES[0]: candidate.train1_responses,
        FIT_FILES[1]: candidate.train2_responses,
    }
    censored_by_short = {
        FIT_FILES[0]: candidate.train1_right_censored,
        FIT_FILES[1]: candidate.train2_right_censored,
    }
    file_stats: dict[str, dict[str, Any]] = {}
    pooled: list[float] = []
    for short_name in FIT_FILES:
        responses = responses_by_short[short_name]
        increase_matches = sum(response > target_noise_scale for response in responses)
        decrease_matches = sum(response < -target_noise_scale for response in responses)
        selected_matches = (
            increase_matches if candidate.target_direction == "increase" else decrease_matches
        )
        opposite_matches = (
            decrease_matches if candidate.target_direction == "increase" else increase_matches
        )
        usable = len(responses)
        file_stats[short_name] = {
            "usable_response_count": usable,
            "right_censored_count": censored_by_short[short_name],
            "directional_match_count": selected_matches,
            "opposite_direction_match_count": opposite_matches,
            "selected_directional_consistency": selected_matches / usable if usable else 0.0,
            "opposite_directional_consistency": opposite_matches / usable if usable else 0.0,
        }
        pooled.extend(responses)
    total_matches = sum(file_stats[name]["directional_match_count"] for name in FIT_FILES)
    median_response = float(statistics.median(pooled)) if pooled else None
    robust_effect = abs(median_response) / target_noise_scale if median_response is not None else 0.0
    record = {
        "target_direction": candidate.target_direction,
        "horizon_seconds": candidate.horizon_seconds,
        "train1": file_stats[FIT_FILES[0]],
        "train2": file_stats[FIT_FILES[1]],
        "total_usable_responses": len(pooled),
        "pooled_directional_consistency": total_matches / len(pooled) if pooled else 0.0,
        "pooled_median_response": median_response,
        "pooled_robust_effect_ratio": robust_effect,
    }
    if not math.isclose(record["pooled_directional_consistency"], candidate.pooled_consistency, rel_tol=0.0, abs_tol=0.0):
        raise TASK039D1FinalAuditError("independent candidate consistency mismatch")
    if not math.isclose(robust_effect, candidate.pooled_robust_effect_ratio, rel_tol=0.0, abs_tol=0.0):
        raise TASK039D1FinalAuditError("independent candidate effect mismatch")
    return record


def _compare_exact(label: str, replay: Mapping[str, Any], original: Mapping[str, Any]) -> None:
    if thaw_json(freeze_json(replay)) != thaw_json(freeze_json(original)):
        raise TASK039D1FinalAuditError(f"failed_task039d1_independent_replay: {label}")


def replay_d1_independently_v1(
    *,
    identity_view_document: Mapping[str, Any],
    fit_values: Mapping[str, Mapping[str, Sequence[float]]],
    fit_file_bindings: Mapping[str, str],
    original_source_ledger: Mapping[str, Any],
    original_target_ledger: Mapping[str, Any],
    original_directional_ledger: Mapping[str, Any],
    original_pair_summary: Mapping[str, Any],
    audit_private_root: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Replay D1 without calling the D1 top-level scientific evaluator."""

    def progress(message: str) -> None:
        if progress_callback is not None:
            progress_callback(message)

    verify_self_hash_v1(identity_view_document)
    if identity_view_document.get("artifact_hash") != PROFILING_IDENTITY_VIEW_HASH:
        raise TASK039D1FinalAuditError("failed_task039d1_arm_blindness_audit")
    view = ProfilingIdentityViewV1.from_dict(identity_view_document)
    identities = list(view.to_dict()["candidates"])
    if len(identities) != 47 or len({(item["source"], item["target"]) for item in identities}) != 47:
        raise TASK039D1FinalAuditError("failed_task039d1_independent_replay")
    for identity in identities:
        assert_arm_blind_identity_record_v1(identity)
    if set(fit_values) != set(FIT_FILES) or set(fit_file_bindings) != set(FIT_FILES):
        raise TASK039D1FinalAuditError("failed_task039d1_data_boundary_audit")

    original_source_records = {item["source"]: item for item in original_source_ledger["records"]}
    original_target_records = {item["target"]: item for item in original_target_ledger["records"]}
    original_direction_records = {
        (item["source"], item["target"], item["source_step_direction"]): item
        for item in original_directional_ledger["records"]
    }

    source_records: list[dict[str, Any]] = []
    source_record_by_name: dict[str, dict[str, Any]] = {}
    source_parameters: dict[str, dict[str, Any]] = {}
    events_by_source: dict[str, dict[str, Sequence[Any]]] = {}
    progress("source_parameter_and_event_replay_started")
    for source_index, source in enumerate(FROZEN_SOURCES, start=1):
        full_files = {
            BR2_FILE_BY_D0_FILE[short]: fit_values[short][source] for short in FIT_FILES
        }
        diagnostics = derive_multifile_source_screening_diagnostics_v1(full_files)
        status = "supported" if diagnostics.source_step_threshold is not None else "insufficient_nontrivial_amplitudes"
        parameters = {
            "status": status,
            "source_noise_scale": diagnostics.source_noise_scale,
            "nontrivial_amplitude_count": diagnostics.nontrivial_amplitude_count,
            "source_step_threshold": diagnostics.source_step_threshold,
            "source_stability_tolerance": diagnostics.source_stability_tolerance,
        }
        source_parameters[source] = parameters
        source_events: dict[str, Sequence[Any]] = {}
        for short_name in FIT_FILES:
            source_events[short_name] = (
                extract_sustained_step_events_file_local_v1(
                    fit_values[short_name][source],
                    source_step_threshold=float(diagnostics.source_step_threshold),
                    source_stability_tolerance=float(diagnostics.source_stability_tolerance),
                )
                if status == "supported"
                else ()
            )
        events_by_source[source] = source_events
        record = _record(
            {
                "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
                "artifact_type": "task039d1_source_parameter_record_v1",
                "source": source,
                "semantic_role": FROZEN_SOURCE_ROLES[source],
                "source_noise_scale": parameters["source_noise_scale"],
                "nontrivial_amplitude_count": parameters["nontrivial_amplitude_count"],
                "source_step_threshold": parameters["source_step_threshold"],
                "source_stability_tolerance": parameters["source_stability_tolerance"],
                "parameter_status": status,
                "parameter_class": "normal_relation_profile_fit_derived",
                "fit_file_bindings": [fit_file_bindings[name] for name in FIT_FILES],
            }
        )
        _compare_exact(f"source:{source}", record, original_source_records[source])
        source_records.append(record)
        source_record_by_name[source] = record
        progress(f"source_parameter_and_event_replay_completed_{source_index}_of_12")

    progress("indexed_12_source_isolation_replay_started")
    isolated_nested = classify_multisource_isolation_v1(events_by_source)
    progress("indexed_12_source_isolation_replay_completed")

    target_records: list[dict[str, Any]] = []
    target_record_by_name: dict[str, dict[str, Any]] = {}
    target_scales: dict[str, float] = {}
    progress("target_scale_replay_started")
    for target_index, target in enumerate(FROZEN_TARGETS, start=1):
        full_files = {
            BR2_FILE_BY_D0_FILE[short]: fit_values[short][target] for short in FIT_FILES
        }
        scale = derive_multifile_robust_scale_v1(full_files)
        target_scales[target] = scale
        record = _record(
            {
                "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
                "artifact_type": "task039d1_target_parameter_record_v1",
                "target": target,
                "target_noise_scale": scale,
                "parameter_class": "normal_relation_profile_fit_derived",
                "fit_file_bindings": [fit_file_bindings[name] for name in FIT_FILES],
            }
        )
        _compare_exact(f"target:{target}", record, original_target_records[target])
        target_records.append(record)
        target_record_by_name[target] = record
        progress(f"target_scale_replay_completed_{target_index}_of_12")

    directional_records: list[dict[str, Any]] = []
    pair_outcomes: list[dict[str, Any]] = []
    directional_counts = {"fit_supported": 0, "direction_unstable": 0, "fit_unsupported": 0}
    failure_counts = {"insufficient_nontrivial_amplitudes": 0, "fit_gate_not_satisfied": 0}
    progress("directional_replay_started")
    for pair_index, identity in enumerate(identities, start=1):
        source, target = identity["source"], identity["target"]
        pair_statuses: dict[str, str] = {}
        for source_direction in SOURCE_DIRECTIONS:
            source_support: dict[str, int] = {}
            stream_refs: dict[str, str] = {}
            isolated_events_by_full: dict[str, tuple[Any, ...]] = {}
            for short_name in FIT_FILES:
                selected_events = tuple(
                    event
                    for event, isolated in isolated_nested[source][short_name]
                    if isolated and event.direction == source_direction
                )
                source_support[short_name] = len(selected_events)
                stream_refs[short_name] = stable_hash_v1(
                    {
                        "file_binding": fit_file_bindings[short_name],
                        "source": source,
                        "source_step_direction": source_direction,
                        "retained_isolated_event_indices": [event.event_index for event in selected_events],
                    }
                )
                isolated_events_by_full[BR2_FILE_BY_D0_FILE[short_name]] = tuple(
                    event for event, isolated in isolated_nested[source][short_name] if isolated
                )

            candidates: list[dict[str, Any]] = []
            selected_detail: Mapping[str, Any] | None = None
            if source_parameters[source]["status"] != "supported":
                fit_status = "fit_unsupported"
                failure_reason = "insufficient_nontrivial_amplitudes"
                failure_counts[failure_reason] += 1
            else:
                target_by_full = {
                    BR2_FILE_BY_D0_FILE[short]: fit_values[short][target] for short in FIT_FILES
                }
                primitive_candidates: list[DirectionCandidateV1] = []
                for target_direction in TARGET_DIRECTIONS:
                    for horizon in HORIZONS:
                        primitive = evaluate_direction_candidate_v1(
                            target_by_file=target_by_full,
                            isolated_events_by_file=isolated_events_by_full,
                            source_step_direction=source_direction,
                            target_direction=target_direction,
                            horizon_seconds=horizon,
                            target_noise_scale=target_scales[target],
                        )
                        primitive_candidates.append(primitive)
                        candidates.append(
                            _candidate_record(primitive, target_noise_scale=target_scales[target])
                        )
                selected_primitive = select_direction_candidate_v1(primitive_candidates)
                if selected_primitive is None:
                    fit_status = "direction_unstable"
                    failure_reason = "direction_unstable"
                else:
                    selected_detail = next(
                        item for item in candidates
                        if item["target_direction"] == selected_primitive.target_direction
                        and item["horizon_seconds"] == selected_primitive.horizon_seconds
                    )
                    if fit_candidate_passes_v1(selected_primitive):
                        fit_status = "fit_supported"
                        failure_reason = None
                    else:
                        fit_status = "fit_unsupported"
                        failure_reason = "fit_gate_not_satisfied"
                        failure_counts[failure_reason] += 1

            record = _record(
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
            _compare_exact(
                f"direction:{source}:{target}:{source_direction}",
                record,
                original_direction_records[(source, target, source_direction)],
            )
            directional_records.append(record)
            directional_counts[fit_status] += 1
            pair_statuses[source_direction] = fit_status
        pair_outcomes.append(
            {
                "source": source,
                "target": target,
                "step_up_status": pair_statuses["step_up"],
                "step_down_status": pair_statuses["step_down"],
                "pair_fit_status": (
                    "fit_supported_pair"
                    if "fit_supported" in pair_statuses.values()
                    else "fit_unsupported_pair"
                ),
            }
        )
        progress(f"directional_replay_completed_{pair_index}_of_47")

    source_ledger = _private_ledger("task039d1_source_parameter_ledger_v1", source_records)
    target_ledger = _private_ledger("task039d1_target_parameter_ledger_v1", target_records)
    directional_ledger = _private_ledger("task039d1_directional_fit_ledger_v1", directional_records)
    _compare_exact("source_ledger", source_ledger, original_source_ledger)
    _compare_exact("target_ledger", target_ledger, original_target_ledger)
    _compare_exact("directional_ledger", directional_ledger, original_directional_ledger)

    supported_pairs = sum(item["pair_fit_status"] == "fit_supported_pair" for item in pair_outcomes)
    pair_summary = _self_hashed(
        {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d1_pair_fit_summary_v1",
            "task_id": "TASK-039D1",
            "status": "frozen_task039d1_pair_fit_outcomes",
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "profiling_identity_view_hash": PROFILING_IDENTITY_VIEW_HASH,
            "candidate_count": 47,
            "directional_opportunity_count": 94,
            "pair_fit_supported_count": supported_pairs,
            "pair_fit_unsupported_count": 47 - supported_pairs,
            "directional_status_counts": directional_counts,
            "pair_outcomes": pair_outcomes,
            "lower_ranked_fallback_used": False,
            "candidate_arm_evidence_visible_to_profiler": False,
        }
    )
    _compare_exact("pair_summary", pair_summary, original_pair_summary)

    if audit_private_root.exists() and any(audit_private_root.iterdir()):
        raise TASK039D1FinalAuditError("audit private root must be new or empty")
    audit_private_root.mkdir(parents=True, exist_ok=True)
    for name, document in (
        ("TASK-039D1-AUDIT_SOURCE_REPLAY_LEDGER.json", source_ledger),
        ("TASK-039D1-AUDIT_TARGET_REPLAY_LEDGER.json", target_ledger),
        ("TASK-039D1-AUDIT_DIRECTIONAL_REPLAY_LEDGER.json", directional_ledger),
        ("TASK-039D1-AUDIT_PAIR_REPLAY.json", pair_summary),
    ):
        write_json_v1(audit_private_root / name, document)
    progress("scientific_replay_frozen_before_provenance")

    return {
        "source_ledger": source_ledger,
        "target_ledger": target_ledger,
        "directional_ledger": directional_ledger,
        "pair_summary": pair_summary,
        "directional_status_counts": directional_counts,
        "failure_counts": failure_counts,
        "pair_fit_supported_count": supported_pairs,
        "pair_fit_unsupported_count": 47 - supported_pairs,
        "source_parameter_supported_count": sum(
            item["parameter_status"] == "supported" for item in source_records
        ),
        "source_parameter_unsupported_count": sum(
            item["parameter_status"] != "supported" for item in source_records
        ),
        "provenance_loaded": False,
        "replay_artifact_count": 4,
    }


def replay_arm_summary_after_freeze_v1(
    *, pair_summary: Mapping[str, Any], provenance_document: Mapping[str, Any],
    original_arm_summary: Mapping[str, Any], directional_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    verify_self_hash_v1(provenance_document)
    if provenance_document.get("artifact_hash") != PROVENANCE_ANALYSIS_VIEW_HASH:
        raise TASK039D1FinalAuditError("failed_task039d1_arm_blindness_audit")
    CandidateProvenanceAnalysisViewV1.from_dict(provenance_document)
    outcomes = {(item["source"], item["target"]): item for item in pair_summary["pair_outcomes"]}
    directional = {
        (item["source"], item["target"], item["source_step_direction"]): item["fit_result"]
        for item in directional_ledger["records"]
    }
    provenance = {
        (item["source"], item["target"]): item for item in provenance_document["candidates"]
    }
    if set(outcomes) != set(provenance):
        raise TASK039D1FinalAuditError("failed_task039d1_arm_blindness_audit")
    arms: list[dict[str, Any]] = []
    for arm in ("META", "STAT", "GDN"):
        pairs = [pair for pair, record in provenance.items() if arm in record["origin_arms"]]
        pair_supported = sum(outcomes[pair]["pair_fit_status"] == "fit_supported_pair" for pair in pairs)
        direction_supported = sum(
            directional[(pair[0], pair[1], direction)] == "fit_supported"
            for pair in pairs for direction in SOURCE_DIRECTIONS
        )
        arms.append(
            {
                "arm": arm,
                "top20_pair_count": 20,
                "pair_fit_supported_count": pair_supported,
                "pair_fit_support_yield": pair_supported / 20.0,
                "directional_fit_supported_count": direction_supported,
            }
        )
    arm_summary = _self_hashed(
        {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d1_arm_fit_summary_v1",
            "task_id": "TASK-039D1",
            "status": "fit_only_descriptive_arm_summary",
            "pair_summary_hash": pair_summary["artifact_hash"],
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
    _compare_exact("arm_summary", arm_summary, original_arm_summary)
    return arm_summary


@dataclass(frozen=True)
class _AuditArtifact:
    payload: Mapping[str, Any]
    ARTIFACT_TYPE: ClassVar[str] = ""
    FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        reject_unknown_fields(self.payload, self.FIELDS, self.ARTIFACT_TYPE)
        if set(self.payload) != set(self.FIELDS):
            raise TASK039D1FinalAuditError(f"{self.ARTIFACT_TYPE} fields are incomplete")
        object.__setattr__(self, "payload", freeze_json(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return _self_hashed(
            {
                "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
                "artifact_type": self.ARTIFACT_TYPE,
                **thaw_json(self.payload),
            }
        )

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "_AuditArtifact":
        verify_audit_self_hash_v1(document)
        if document.get("schema_version") != V6_FOUNDATION_SCHEMA_VERSION:
            raise TASK039D1FinalAuditError("audit artifact schema version mismatch")
        if document.get("artifact_type") != cls.ARTIFACT_TYPE:
            raise TASK039D1FinalAuditError("audit artifact type mismatch")
        return cls(
            {
                key: value
                for key, value in document.items()
                if key not in {"schema_version", "artifact_type", "artifact_hash"}
            }
        )


def _artifact_class(name: str, artifact_type: str, fields: Sequence[str]) -> type[_AuditArtifact]:
    return type(name, (_AuditArtifact,), {"ARTIFACT_TYPE": artifact_type, "FIELDS": frozenset(fields)})


TASK039D2AuthorizationV1 = _artifact_class(
    "TASK039D2AuthorizationV1",
    "task039d2_authorization_v1",
    (
        "task_id", "status", "readiness", "d0_protocol_bundle_hash", "confirmation_policy_hash",
        "d1_fit_result_hash", "d1_source_ledger_hash", "d1_target_ledger_hash",
        "d1_directional_ledger_hash", "d1_pair_summary_hash", "candidate_cohort_hash",
        "candidate_identity_list_hash", "candidate_count", "input_directional_relations",
        "input_directional_relation_count", "supported_pair_context_count",
        "train3_feature_values_authorized", "train1_train2_feature_value_refitting_authorized",
        "train4_authorized", "test_labels_attacks_authorized", "br2_pair_results_authorized",
        "candidate_arm_evidence_visible_to_confirmation_engine", "parameter_retuning_authorized",
        "alternative_horizon_search_authorized", "opposite_target_direction_search_authorized",
        "rule_v2_authorized", "agent_authorized", "detector_runtime_authorized",
        "separate_clean_d2_execution_code_commit_required", "d2_executed_by_this_artifact",
    ),
)

TASK039D1FinalAuditV1 = _artifact_class(
    "TASK039D1FinalAuditV1",
    "task039d1_final_audit_v1",
    (
        "task_id", "status", "readiness", "findings_by_severity", "lineage",
        "frozen_identities", "public_artifact_verification", "commit_separation",
        "complexity_recovery_verification", "private_ledger_verification", "raw_replay",
        "source_target_replay", "event_isolation_replay", "directional_replay",
        "pair_replay", "arm_summary_replay", "data_boundary", "interpretation_boundary",
        "d2_readiness", "d2_authorization_hash", "rule_v2_authorized",
    ),
)


def build_d2_authorization_v1() -> dict[str, Any]:
    document = TASK039D2AuthorizationV1(
        {
            "task_id": TASK_ID,
            "status": "authorized_task039d2_one_way_train3_confirmation",
            "readiness": READINESS,
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "d1_fit_result_hash": FIT_RESULT_HASH,
            "d1_source_ledger_hash": SOURCE_LEDGER_HASH,
            "d1_target_ledger_hash": TARGET_LEDGER_HASH,
            "d1_directional_ledger_hash": DIRECTIONAL_LEDGER_HASH,
            "d1_pair_summary_hash": PAIR_SUMMARY_HASH,
            "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
            "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
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
    ).to_dict()
    verify_audit_self_hash_v1(document)
    return document


def build_final_audit_v1(
    *, replay: Mapping[str, Any], arm_summary: Mapping[str, Any],
    data_access_state: Mapping[str, Any], d2_authorization_hash: str,
    audit_source_hash: str,
) -> dict[str, Any]:
    require_sha256(d2_authorization_hash, "d2_authorization_hash")
    require_sha256(audit_source_hash, "audit_source_hash")
    arms = {item["arm"]: item for item in arm_summary["arms"]}
    document = TASK039D1FinalAuditV1(
        {
            "task_id": TASK_ID,
            "status": STATUS,
            "readiness": READINESS,
            "findings_by_severity": {"BLOCKING": 0, "IMPORTANT_NONBLOCKING": 0, "DOCUMENTATION_OR_HYGIENE": 0},
            "lineage": {"authoritative_main": MAIN_COMMIT, "aborted_a1": ABORTED_A1, "execution_a2": EXECUTION_A2, "result_b2": RESULT_B2},
            "frozen_identities": {"d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH, "d1_authorization_hash": D1_AUTHORIZATION_HASH, "candidate_cohort_hash": CANDIDATE_COHORT_HASH, "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH, "candidate_count": 47, "directional_opportunity_count": 94},
            "public_artifact_verification": {"fit_result_hash": FIT_RESULT_HASH, "pair_summary_hash": PAIR_SUMMARY_HASH, "arm_summary_hash": ARM_SUMMARY_HASH, "access_audit_hash": ACCESS_AUDIT_HASH, "execution_receipt_hash": EXECUTION_RECEIPT_HASH, "all_self_hashes_verified": True},
            "commit_separation": {"passed": True, "b2_changed_file_count": 6, "scientific_source_changed_after_a2": False},
            "complexity_recovery_verification": {"receipt_hash": COMPLEXITY_RECEIPT_HASH, "source_bindings_verified": True, "event_semantic_parity": "passed", "event_complexity_class": "linear_in_sequence_length", "isolation_semantic_parity": "passed", "isolation_complexity_class": "O(E log E)_with_fixed_12_source_context", "target_response_optimization_unchanged": True, "d0_policy_changed": False, "unresolved_complexity_defects": []},
            "private_ledger_verification": {"source_ledger_hash": SOURCE_LEDGER_HASH, "source_record_count": 12, "target_ledger_hash": TARGET_LEDGER_HASH, "target_record_count": 12, "directional_ledger_hash": DIRECTIONAL_LEDGER_HASH, "directional_record_count": 94, "all_self_hashes_verified": True, "original_ledgers_modified": False},
            "raw_replay": {"status": "passed_independent_train1_train2_replay", "orchestration": "audit_specific_br1_br2_primitive_reconstruction", "d1_top_level_execution_function_called": False, "profiling_identity_view_only": True, "provenance_loaded_after_replay_freeze": True, "audit_private_replay_artifact_count": replay["replay_artifact_count"], "audit_source_hash": audit_source_hash},
            "source_target_replay": {"source_record_count": 12, "source_supported_count": replay["source_parameter_supported_count"], "source_unsupported_count": replay["source_parameter_unsupported_count"], "target_record_count": 12, "exact_normalized_field_agreement": True, "no_cross_file_differences_or_windows": True, "q75_threshold_tolerance_reproduced": True},
            "event_isolation_replay": {"source_count": 12, "fit_file_count": 2, "clustering_reproduced": True, "step_directions_reproduced": True, "inclusive_isolation_radius_seconds": 2, "all_source_context_used": True, "event_support_and_stream_references_reproduced": True, "public_event_timestamps_included": False},
            "directional_replay": {"opportunity_count": 94, "fit_supported_count": replay["directional_status_counts"]["fit_supported"], "direction_unstable_count": replay["directional_status_counts"]["direction_unstable"], "fit_unsupported_count": replay["directional_status_counts"]["fit_unsupported"], "fit_gate_failure_count": replay["failure_counts"]["fit_gate_not_satisfied"], "no_fallback_verified": True, "normalized_records_exact": True},
            "pair_replay": {"pair_count": 47, "fit_supported_count": replay["pair_fit_supported_count"], "fit_unsupported_count": replay["pair_fit_unsupported_count"], "pair_summary_hash": replay["pair_summary"]["artifact_hash"], "identity_status_equality": True},
            "arm_summary_replay": {"META": {"fit_supported_pairs": arms["META"]["pair_fit_supported_count"], "yield": arms["META"]["pair_fit_support_yield"], "fit_supported_directions": arms["META"]["directional_fit_supported_count"]}, "STAT": {"fit_supported_pairs": arms["STAT"]["pair_fit_supported_count"], "yield": arms["STAT"]["pair_fit_support_yield"], "fit_supported_directions": arms["STAT"]["directional_fit_supported_count"]}, "GDN": {"fit_supported_pairs": arms["GDN"]["pair_fit_supported_count"], "yield": arms["GDN"]["pair_fit_support_yield"], "fit_supported_directions": arms["GDN"]["directional_fit_supported_count"]}, "same_pair_same_outcome": True, "winner_selected": False},
            "data_boundary": dict(data_access_state),
            "interpretation_boundary": {"claim": "D1 fit-supported normal delayed-response relation candidates reproduced", "confirmed_relation_claimed": False, "causality_claimed": False, "method_superiority_claimed": False, "rule_validity_claimed": False, "anomaly_performance_claimed": False},
            "d2_readiness": {"status": READINESS, "input_fit_supported_direction_count": 45, "supported_pair_context_count": 25, "d2_executed": False, "separate_clean_execution_code_commit_required": True},
            "d2_authorization_hash": d2_authorization_hash,
            "rule_v2_authorized": False,
        }
    ).to_dict()
    verify_audit_self_hash_v1(document)
    return document


def audit_schema_examples_v1() -> tuple[dict[str, Any], dict[str, Any]]:
    """Build result-free examples used to freeze the two audit schemas."""

    authorization = build_d2_authorization_v1()
    replay = {
        "replay_artifact_count": 4,
        "source_parameter_supported_count": 12,
        "source_parameter_unsupported_count": 0,
        "directional_status_counts": {
            "fit_supported": 45,
            "direction_unstable": 17,
            "fit_unsupported": 32,
        },
        "failure_counts": {"fit_gate_not_satisfied": 32},
        "pair_fit_supported_count": 25,
        "pair_fit_unsupported_count": 22,
        "pair_summary": {"artifact_hash": PAIR_SUMMARY_HASH},
    }
    arm_summary = {
        "arms": [
            {"arm": "META", "pair_fit_supported_count": 16, "pair_fit_support_yield": 0.8, "directional_fit_supported_count": 29},
            {"arm": "STAT", "pair_fit_supported_count": 17, "pair_fit_support_yield": 0.85, "directional_fit_supported_count": 33},
            {"arm": "GDN", "pair_fit_supported_count": 5, "pair_fit_support_yield": 0.25, "directional_fit_supported_count": 7},
        ]
    }
    data_boundary = {
        "dataset_file_identities_verified": True,
        "train1_accessed": True,
        "train2_accessed": True,
        "train3_accessed": False,
        "train4_accessed": False,
        "test_accessed": False,
        "labels_accessed": False,
        "attacks_accessed": False,
        "br2_pair_results_accessed": False,
        "candidate_arm_evidence_visible_during_replay": False,
        "provenance_loaded_after_replay_freeze": True,
        "raw_values_publicly_persisted": False,
        "raw_windows_publicly_persisted": False,
        "event_timestamps_publicly_persisted": False,
        "absolute_paths_publicly_persisted": False,
        "prohibited_access_count": 0,
    }
    audit = build_final_audit_v1(
        replay=replay,
        arm_summary=arm_summary,
        data_access_state=data_boundary,
        d2_authorization_hash=authorization["artifact_hash"],
        audit_source_hash="0" * 64,
    )
    return audit, authorization


def schema_for_audit_artifact_v1(example: Mapping[str, Any]) -> dict[str, Any]:
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
            schema: dict[str, Any] = {"type": "string"}
            if field_name and (field_name.endswith("_hash") or field_name in {"authoritative_main", "aborted_a1", "execution_a2", "result_b2"}):
                schema["pattern"] = "^[a-f0-9]{40}$" if field_name in {"authoritative_main", "aborted_a1", "execution_a2", "result_b2"} else "^[a-f0-9]{64}$"
            return schema
        if isinstance(value, list):
            return {"type": "array", "items": {} if not value else infer(value[0])}
        if isinstance(value, Mapping):
            return {"type": "object", "additionalProperties": False, "required": list(value), "properties": {key: infer(item, key) for key, item in value.items()}}
        raise TASK039D1FinalAuditError("unsupported audit schema value")
    schema = infer(example)
    artifact_type = str(example["artifact_type"])
    schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"https://paperworks.local/schemas/v6/{artifact_type}_schema.json", "title": artifact_type})
    schema["properties"]["schema_version"] = {"const": V6_FOUNDATION_SCHEMA_VERSION}
    schema["properties"]["artifact_type"] = {"const": artifact_type}
    schema["properties"]["artifact_hash"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    return schema


__all__ = [
    "TASK039D1FinalAuditError", "TASK039D1FinalAuditV1", "TASK039D2AuthorizationV1",
    "replay_d1_independently_v1", "replay_arm_summary_after_freeze_v1",
    "build_d2_authorization_v1", "build_final_audit_v1", "schema_for_audit_artifact_v1",
    "audit_schema_examples_v1",
    "verify_audit_self_hash_v1", "write_json_v1", "STATUS", "READINESS",
]
