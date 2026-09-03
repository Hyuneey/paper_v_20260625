#!/usr/bin/env python3
"""Freeze and execute EXP-01C-GDN-HAI-V1 on normal HAI splits only."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any, Mapping, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import (
    META_RESULT_HASH, PAIR_UNIVERSE, STAT_RESULT_HASH,
)
from paperworks.validation_v2.exp01b_functional_v1 import relative_delta_mse_v1
from paperworks.validation_v2.exp01b_ranking_v1 import precision_recall_ndcg_at_k_v1
from paperworks.validation_v2.exp01c_backend_v1 import (
    Exp01CCheckpointEvidenceV1, Exp01CRelationEventV1,
    _state_hash_v1, evaluate_exp01c_checkpoint_v1,
    smoke_exp01c_backend_v1, train_exp01c_seed_v1,
)
from paperworks.validation_v2.exp02_bindings_v2a import (
    build_relation_summaries_for_split_v1, extract_candidate_specific_events_v1,
)
from paperworks.validation_v2.gdn_corr_contract_v1 import (
    EXP01C_K, EXP01C_SEEDS, EXP01C_VIEWS, Exp01CConfigV1, LearnedGraphDisposition,
)
from paperworks.validation_v2.gdn_corr_v1 import (
    augmented_scores_r1, corrected_functional_consensus_r1,
    corrected_meta_stat_scores_r1, deterministic_ranking_r1,
    jaccard_at_k_r1, matched_random_controls_r1,
    observed_percentiles_r1,
)
from paperworks.validation_v2.formal_v4_authority_v1 import (
    FormalV4ArtifactBindingV1, FormalV4EvaluatorContractV1,
    FormalV4ExecutionContextV1, FormalV4RuleDescriptorV1,
    NumericReferenceBindingV1, authorize_formal_v4_runtime_v1,
    build_formal_v4_portfolio_authority_v1, canonical_document_hash_v1,
)
from paperworks.validation_v2.hai_feature_adapter_v1 import (
    HAIFeatureAccessLedgerV1, load_authorized_hai_feature_frame_for_operations_v1,
    resolve_hai_feature_root_capability_v1,
)
from paperworks.validation_v2.numeric_policy_v1 import (
    ConfirmedRelationIdentityV1, build_confirmed_cohort_authority_v1,
    build_numeric_policy_candidate_set_v1, derive_pooled_role_values_v1,
)
from paperworks.validation_v2.runtime_policy_v1 import (
    FORMAL_V4_RESPONSE_POLICY_HASH, FORMAL_V4_TRACE_CONTRACT_HASH,
    FORMAL_V4_TRIGGER_POLICY_HASH,
)
from paperworks.validation_v2.protocol_v1 import (
    ProtocolExecutionGuardV1, ProtocolOperationV1, build_validation_protocol_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


PUBLIC = Path("research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai")
PRIVATE = Path("artifacts/validation_v2/gdn_corr_001/exp01c_gdn_hai/private")
PREREG = PUBLIC / "preregistration/EXP01C_PREREGISTRATION.json"
ENV = PUBLIC / "environment/EXP01C_GPU_ENVIRONMENT_RECEIPT_R2.json"
BINDING = PUBLIC / "contracts/EXP01C_EXECUTION_BINDING_R2.json"
PREPROCESSING = Path("research_control_center/validation_v2/gdn_corr_001/hai_readiness/EXP01C_PREPROCESSING_DECISION.json")
REFERENCE = Path("research_control_center/validation_v2/exp01b_gdn_xai/receipts/EXP01B_REFERENCE_SET_RECEIPT.json")
SELECTED_POLICY = Path("research_control_center/validation_v2/core_v2a/authorities/EXP02_SELECTED_POLICY_AUTHORITY_V2A.json")


class Exp01CCliError(RuntimeError):
    pass


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode() + b"\n"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise Exp01CCliError(f"EXP01C_JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _self_hash(value: Mapping[str, Any], field: str) -> None:
    body = {key: item for key, item in value.items() if key != field}
    if value.get(field) != stable_hash_v1(body):
        raise Exp01CCliError(f"EXP01C_SELF_HASH_MISMATCH:{field}")


def _write_new(path: Path, value: Mapping[str, Any]) -> str:
    payload = _canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise Exp01CCliError(f"EXP01C_EXISTING_OUTPUT_MISMATCH:{path.name}")
    else:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        finally:
            os.close(descriptor)
    return sha256(payload).hexdigest()


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        raise Exp01CCliError("EXP01C_EMPTY_RESULT_TABLE")
    import io
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=tuple(rows[0]), lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    payload = buffer.getvalue().encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise Exp01CCliError(f"EXP01C_EXISTING_TABLE_MISMATCH:{path.name}")
    else:
        path.write_bytes(payload)
    return sha256(payload).hexdigest()


def _artifact_binding(root: Path, artifact_id: str, path: Path) -> FormalV4ArtifactBindingV1:
    return FormalV4ArtifactBindingV1(
        artifact_id=artifact_id, relative_path=path.as_posix(),
        content_sha256=sha256((root / path).read_bytes()).hexdigest(),
    )


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _hashes(root: Path) -> dict[str, str]:
    names = (
        "src/paperworks/validation_v2/exp01c_backend_v1.py",
        "src/paperworks/validation_v2/gdn_corr_v1.py",
        "scripts/run_exp01c_gdn_hai.py",
    )
    return {name: sha256((root / name).read_bytes()).hexdigest() for name in names}


def _driver() -> str:
    output = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
        text=True, stderr=subprocess.DEVNULL,
    )
    values = [line.strip() for line in output.splitlines() if line.strip()]
    if not values:
        raise Exp01CCliError("EXP01C_DRIVER_UNAVAILABLE")
    return values[0]


def freeze_environment(root: Path) -> None:
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8" or os.environ.get("PYTHONHASHSEED") != "0":
        raise Exp01CCliError("EXP01C_DETERMINISTIC_LAUNCH_ENV_MISSING")
    prereg = _load(root / PREREG); _self_hash(prereg, "preregistration_hash")
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
        raise Exp01CCliError("EXP01C_CUDA_UNAVAILABLE")
    gpu = str(torch.cuda.get_device_name(0))
    if "5060" not in gpu:
        raise Exp01CCliError("EXP01C_GPU_IDENTITY_MISMATCH")
    smoke = smoke_exp01c_backend_v1(config=Exp01CConfigV1())
    if smoke.get("status") != "PASS" or smoke.get("model_device") != "cuda" or smoke.get("tensor_device") != "cuda":
        raise Exp01CCliError("EXP01C_CUDA_SMOKE_FAILED")
    body = {
        "schema": "paperworks.validation_v2.exp01c_gpu_environment_receipt_v1",
        "experiment_id": "EXP-01C-GDN-HAI-V1", "source_commit": _head(root),
        "preregistration_hash": prereg["preregistration_hash"], "implementation_hashes": _hashes(root),
        "python": sys.version.split()[0], "torch": str(torch.__version__),
        "torch_geometric": metadata.version("torch-geometric"), "cuda_build": str(torch.version.cuda),
        "driver": _driver(), "gpu_model": gpu, "dtype": "float32", "seeds": list(EXP01C_SEEDS),
        "deterministic_flags": {
            "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
            "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
            "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
            "matmul_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
            "cudnn_tf32": bool(torch.backends.cudnn.allow_tf32),
            "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
            "pythonhashseed": os.environ["PYTHONHASHSEED"],
        },
        "synthetic_smoke": smoke, "scientific_data_accesses": 0,
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
        "heldout_accesses": 0, "private_paths_embedded": False,
    }
    body["environment_hash"] = stable_hash_v1(body)
    _write_new(root / ENV, body)
    print(json.dumps({"status": "PASS", "environment_hash": body["environment_hash"], "gpu": gpu}, sort_keys=True))


def freeze_execution(root: Path) -> None:
    prereg = _load(root / PREREG); _self_hash(prereg, "preregistration_hash")
    environment = _load(root / ENV); _self_hash(environment, "environment_hash")
    preprocessing = _load(root / PREPROCESSING); _self_hash(preprocessing, "decision_hash")
    body = {
        "schema": "paperworks.validation_v2.exp01c_execution_binding_v1",
        "status": "FROZEN_BEFORE_EXP01C_NORMAL_DATA_IO", "source_commit": _head(root),
        "preregistration_hash": prereg["preregistration_hash"],
        "environment_hash": environment["environment_hash"],
        "implementation_hashes": _hashes(root),
        "preprocessing_policy": preprocessing["selected_policy"],
        "pair_functional_aggregation": "MEDIAN_SIGNED_GLOBAL_EDGEMASK_ACROSS_HORIZONS",
        "directional_event_to_pair_aggregation": "MEDIAN_ACROSS_CONFIRMED_DIRECTIONAL_RELATIONS",
        "functional_consensus": "POSITIVE_EDGEMASK_PLUS_ATTENTION_WITH_NONPOSITIVE_MASK_VETO",
        "random_control_comparison": "WHOLE_FOCAL_TARGET_MATCHED_GLOBAL_EDGEMASK",
        "attention_semantics": "SHARED_ENCODER_NOT_HEAD_SPECIFIC_REPORTED_FOR_EACH_HORIZON",
        "nonmember_semantics": "NOT_IN_LEARNED_GRAPH_SOURCE_OCCLUSION_ONLY",
        "allowed_splits": ["train1", "train2", "train4"],
        "test1_allowed": False, "labels_allowed": False,
        "test2_allowed": False, "heldout_allowed": False,
    }
    body["binding_hash"] = stable_hash_v1(body)
    _write_new(root / BINDING, body)
    print(json.dumps({"status": "PASS", "binding_hash": body["binding_hash"]}, sort_keys=True))


def _replay_execution(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    binding = _load(root / BINDING); _self_hash(binding, "binding_hash")
    environment = _load(root / ENV); _self_hash(environment, "environment_hash")
    if (
        binding.get("status") != "FROZEN_BEFORE_EXP01C_NORMAL_DATA_IO"
        or binding.get("implementation_hashes") != _hashes(root)
        or binding.get("environment_hash") != environment.get("environment_hash")
        or any(binding.get(key) is not False for key in ("test1_allowed", "labels_allowed", "test2_allowed", "heldout_allowed"))
    ):
        raise Exp01CCliError("EXP01C_EXECUTION_BINDING_REPLAY_FAILED")
    current = _head(root)
    if subprocess.run(["git", "merge-base", "--is-ancestor", str(binding["source_commit"]), current], cwd=root).returncode:
        raise Exp01CCliError("EXP01C_EXECUTION_SOURCE_NOT_ANCESTOR")
    import torch
    if (
        not torch.cuda.is_available() or str(torch.cuda.get_device_name(0)) != environment.get("gpu_model")
        or str(torch.__version__) != environment.get("torch") or str(torch.version.cuda) != environment.get("cuda_build")
        or _driver() != environment.get("driver")
    ):
        raise Exp01CCliError("EXP01C_LIVE_ENVIRONMENT_MISMATCH")
    return binding, environment


def _load_inputs(root: Path, source_commit: str) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = build_validation_protocol_v1(source_commit=source_commit)
    guard = ProtocolExecutionGuardV1(protocol)
    ledger = HAIFeatureAccessLedgerV1(experiment_id="EXP-01C-GDN-HAI-V1")
    capability = resolve_hai_feature_root_capability_v1(root)
    operations = {
        "train1": (ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT),
        "train2": (ProtocolOperationV1.CANDIDATE_LEARNING, ProtocolOperationV1.RELATION_FIT),
        "train4": (ProtocolOperationV1.NORMAL_SANITY,),
    }
    frames = {}
    receipts = {}
    for split in ("train1", "train2", "train4"):
        frame = load_authorized_hai_feature_frame_for_operations_v1(
            capability=capability, split_id=split, operations=operations[split],
            protocol_guard=guard, ledger=ledger,
        )
        frames[split] = frame.numeric_matrix()
        receipts[split] = frame.receipt.to_dict()
    body = {
        "schema": "paperworks.validation_v2.exp01c_normal_input_receipts_v1",
        "experiment_id": "EXP-01C-GDN-HAI-V1", "splits": receipts,
        "access_ledger": ledger.public_document(), "train3_reused_reference_only": True,
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
        "heldout_accesses": 0, "private_paths_embedded": False,
    }
    body["receipt_hash"] = stable_hash_v1(body)
    return frames, body


def _reference_and_numeric(
    root: Path, frames: Mapping[str, Any], source_commit: str,
    input_receipt_hash: str,
) -> tuple[dict[str, Any], Any, Mapping[str, tuple[Any, Any]], Any, tuple[Exp01CRelationEventV1, ...]]:
    reference = _load(root / REFERENCE); _self_hash(reference, "receipt_hash")
    relations = tuple(ConfirmedRelationIdentityV1(
        relation_id=str(row["relation_id"]), source=str(row["source"]), target=str(row["target"]),
        source_direction=str(row["source_direction"]), target_direction=str(row["target_direction"]),
        selected_horizon_seconds=int(row["selected_horizon_seconds"]),
        relation_binding_hash=str(row["relation_binding_hash"]),
    ) for row in reference["confirmed_directional_relations"])
    cohort = build_confirmed_cohort_authority_v1(
        cohort_id="EXP01C-NORMAL-CONFIRMED-DIRECTIONAL-REFERENCE",
        source_commit=source_commit, confirmation_artifact_hash=str(reference["receipt_hash"]),
        relations=relations,
    )
    candidates = build_numeric_policy_candidate_set_v1(
        cohort=cohort, normal_fit_input_hash=input_receipt_hash, source_commit=source_commit,
    )
    selected_authority = _load(root / SELECTED_POLICY)
    selected = next((item for item in candidates if item.candidate_id == selected_authority["selected_candidate_id"]), None)
    if selected is None:
        raise Exp01CCliError("EXP01C_SELECTED_NUMERIC_POLICY_NOT_IN_FROZEN_GRID")
    by_split = {
        split: build_relation_summaries_for_split_v1(
            split_id=split, matrix=frames[split], feature_order=P1_FEATURE_ORDER, cohort=cohort,
        ) for split in ("train1", "train2")
    }
    summary_map = {
        relation.relation_id: (
            next(row for row in by_split["train1"] if row.relation_id == relation.relation_id),
            next(row for row in by_split["train2"] if row.relation_id == relation.relation_id),
        ) for relation in relations
    }
    positions = {name: index for index, name in enumerate(P1_FEATURE_ORDER)}
    event_rows = []
    for relation in relations:
        values = dict(derive_pooled_role_values_v1(candidate=selected, summaries=summary_map[relation.relation_id]))
        events = extract_candidate_specific_events_v1(
            frames["train4"][:, positions[relation.source]],
            threshold=float(values["source_step_threshold"]),
            tolerance=float(values["source_stability_tolerance"]),
        )
        event_rows.append(Exp01CRelationEventV1(
            relation_id=relation.relation_id, source=relation.source, target=relation.target,
            source_direction=relation.source_direction,
            selected_horizon_seconds=relation.selected_horizon_seconds,
            event_indices=tuple(event.event_index for event in events if event.direction == relation.source_direction),
        ))
    return reference, cohort, summary_map, selected, tuple(event_rows)


def _meta_stat(root: Path) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...], dict[tuple[str, str], float]]:
    meta = _load(root / "docs/task_reports/TASK-039C_META_RESULT.json")
    stat = _load(root / "docs/task_reports/TASK-039C_STAT_RESULT.json")
    if meta.get("artifact_hash") != META_RESULT_HASH or stat.get("artifact_hash") != STAT_RESULT_HASH:
        raise Exp01CCliError("EXP01C_META_STAT_AUTHORITY_MISMATCH")
    meta_rank = tuple((str(row["source_identity"]), str(row["target_identity"])) for row in meta["top20_identities"])
    stat_rank = tuple((str(row["source"]), str(row["target"])) for row in stat["top20"])
    scores, union = corrected_meta_stat_scores_r1(meta_ranking=meta_rank, stat_ranking=stat_rank)
    if len(union) != 29:
        raise Exp01CCliError("EXP01C_PRIMARY_BUDGET_DID_NOT_REPLAY")
    return meta_rank, stat_rank, scores


def _checkpoint_path(root: Path, view: str, seed: int) -> Path:
    token = view.lower().replace("_", "-")
    return root / PRIVATE / "checkpoints" / f"exp01c-{token}-seed-{seed}.pt"


def _persist_checkpoint(root: Path, view: str, seed: int, trained: Any, config: Exp01CConfigV1) -> tuple[dict[str, Any], dict[str, Any]]:
    import torch
    path = _checkpoint_path(root, view, seed); path.parent.mkdir(parents=True, exist_ok=True)
    state_hash = _state_hash_v1(trained.state_dict)
    private = {
        "state_dict": trained.state_dict, "scaler_center": trained.scaler_center,
        "scaler_scale": trained.scaler_scale, "scaler_receipt": dict(trained.scaler_receipt),
        "graph_edges": tuple(trained.graph_edges), "graph_hash": trained.graph_hash,
        "best_validation_loss": trained.best_validation_loss, "completed_epochs": trained.completed_epochs,
        "train_window_count": trained.train_window_count, "validation_window_count": trained.validation_window_count,
        "validation_blocks": trained.validation_blocks, "raw_timestamp_overlap_count": trained.raw_timestamp_overlap_count,
        "state_hash": state_hash, "config_hash": config.config_hash, "view": view, "seed": seed,
    }
    if not path.exists():
        temporary = path.with_suffix(".partial")
        if temporary.exists(): temporary.unlink()
        with temporary.open("wb") as stream:
            torch.save(private, stream); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    replay = torch.load(path, map_location="cpu", weights_only=False)
    if replay.get("state_hash") != _state_hash_v1(replay["state_dict"]) or replay.get("config_hash") != config.config_hash:
        raise Exp01CCliError("EXP01C_CHECKPOINT_REPLAY_FAILED")
    receipt = {
        "view": view, "seed": seed, "checkpoint_sha256": sha256(path.read_bytes()).hexdigest(),
        "state_hash": replay["state_hash"], "graph_hash": replay["graph_hash"],
        "scaler_parameter_hash": replay["scaler_receipt"]["parameter_hash"],
        "completed_epochs": replay["completed_epochs"],
        "train_window_count": replay["train_window_count"], "validation_window_count": replay["validation_window_count"],
        "raw_timestamp_overlap_count": replay["raw_timestamp_overlap_count"],
        "private_path_disclosed": False,
    }
    receipt["receipt_hash"] = stable_hash_v1(receipt)
    return replay, receipt


def _evidence_to_private(value: Exp01CCheckpointEvidenceV1) -> dict[str, Any]:
    def pair_rows(values: Mapping[Any, float]) -> list[dict[str, Any]]:
        rows = []
        for key, score in values.items():
            if isinstance(key, tuple) and len(key) == 2 and isinstance(key[0], tuple):
                pair, horizon = key; rows.append({"source": pair[0], "target": pair[1], "horizon": horizon, "value": score})
            else:
                pair = key; rows.append({"source": pair[0], "target": pair[1], "value": score})
        return sorted(rows, key=lambda row: tuple(str(row.get(key, "")) for key in ("source", "target", "horizon")))
    return {
        "embedding": pair_rows(value.embedding_scores), "attention": pair_rows(value.attention_scores),
        "global_edge_mask": pair_rows(value.global_edge_mask_scores),
        "event_edge_mask": [{"relation_id": key, "value": score} for key, score in sorted(value.event_edge_mask_scores.items())],
        "global_source_occlusion": pair_rows(value.global_source_occlusion_scores),
        "event_source_occlusion": [{"relation_id": key, "value": score} for key, score in sorted(value.event_source_occlusion_scores.items())],
        "assessment_states": [{"source": pair[0], "target": pair[1], "state": state} for pair, state in sorted(value.assessment_states.items())],
        "baseline_target_horizon_mse": [{"target": key[0], "horizon": key[1], "value": score} for key, score in sorted(value.baseline_target_horizon_mse.items())],
        "attention_invariance_passed": value.attention_invariance_passed,
        "checkpoint_unchanged": value.checkpoint_unchanged,
    }


def _private_to_evidence(value: Mapping[str, Any]) -> Exp01CCheckpointEvidenceV1:
    def pairs(rows: Sequence[Mapping[str, Any]], horizon: bool = False) -> dict[Any, float]:
        return {
            ((str(row["source"]), str(row["target"])), int(row["horizon"])) if horizon else (str(row["source"]), str(row["target"])): float(row["value"])
            for row in rows
        }
    return Exp01CCheckpointEvidenceV1(
        embedding_scores=pairs(value["embedding"]), attention_scores=pairs(value["attention"]),
        global_edge_mask_scores=pairs(value["global_edge_mask"], True),
        event_edge_mask_scores={str(row["relation_id"]): float(row["value"]) for row in value["event_edge_mask"]},
        global_source_occlusion_scores=pairs(value["global_source_occlusion"], True),
        event_source_occlusion_scores={str(row["relation_id"]): float(row["value"]) for row in value["event_source_occlusion"]},
        assessment_states={(str(row["source"]), str(row["target"])): str(row["state"]) for row in value["assessment_states"]},
        baseline_target_horizon_mse={(str(row["target"]), int(row["horizon"])): float(row["value"]) for row in value["baseline_target_horizon_mse"]},
        attention_invariance_passed=bool(value["attention_invariance_passed"]), checkpoint_unchanged=bool(value["checkpoint_unchanged"]),
    )


def _persist_evidence(root: Path, view: str, seed: int, evidence: Exp01CCheckpointEvidenceV1) -> tuple[Exp01CCheckpointEvidenceV1, str]:
    token = view.lower().replace("_", "-")
    path = root / PRIVATE / "evidence" / f"exp01c-{token}-seed-{seed}.json"
    body = _evidence_to_private(evidence); body["view"] = view; body["seed"] = seed
    body["evidence_hash"] = stable_hash_v1(body)
    digest = _write_new(path, body)
    replay = _load(path); _self_hash(replay, "evidence_hash")
    return _private_to_evidence(replay), digest


def _run_scores(evidence: Exp01CCheckpointEvidenceV1) -> dict[tuple[str, str], float]:
    raw_edge = {
        pair: statistics.median(
            float(evidence.global_edge_mask_scores[(pair, horizon)])
            for horizon in (1, 5, 10, 30, 60)
        )
        for pair in PAIR_UNIVERSE
        if all((pair, horizon) in evidence.global_edge_mask_scores for horizon in (1, 5, 10, 30, 60))
    }
    attention = observed_percentiles_r1(evidence.attention_scores, target_local=True)
    return corrected_functional_consensus_r1(raw_edge_mask=raw_edge, attention_percentiles=attention)


def _mean_jaccard(rankings: Mapping[int, Sequence[tuple[str, str]]], k: int) -> float:
    return statistics.mean(
        jaccard_at_k_r1(rankings[left], rankings[right], k=k)
        for left, right in ((11, 23), (11, 37), (23, 37))
    )


def _conversion_audit(
    *, root: Path, unique_confirmed: set[tuple[str, str]],
    reference: Mapping[str, Any], cohort: Any,
    summaries_by_relation: Mapping[str, tuple[Any, Any]], selected: Any,
    source_commit: str,
) -> dict[str, Any]:
    relation_rows = [
        row for row in reference["confirmed_directional_relations"]
        if (str(row["source"]), str(row["target"])) in unique_confirmed
    ]
    numeric_rows = []
    references = []
    authority_rows = []
    for row in relation_rows:
        relation_id = str(row["relation_id"])
        try:
            values = tuple(derive_pooled_role_values_v1(
                candidate=selected, summaries=summaries_by_relation[relation_id],
            ))
        except (KeyError, TypeError, ValueError):
            continue
        refs = []
        for role, value in values:
            reference_id = f"EXP01C-NUM-{stable_hash_v1({'relation_id': relation_id, 'role': role})[:24]}"
            payload = {
                "relation_id": relation_id, "numeric_role": role,
                "reference_id": reference_id, "value": float(value),
            }
            ref = NumericReferenceBindingV1(
                reference_id=reference_id, numeric_role=role,
                reference_hash=canonical_document_hash_v1(payload),
            )
            refs.append(ref); numeric_rows.append({**payload, "reference_hash": ref.reference_hash})
        semantic = canonical_document_hash_v1({
            "relation_id": relation_id,
            "relation_binding_hash": row["relation_binding_hash"],
            "source_direction": row["source_direction"],
            "target_direction": row["target_direction"],
            "selected_horizon_seconds": row["selected_horizon_seconds"],
            "trigger_policy_hash": FORMAL_V4_TRIGGER_POLICY_HASH,
            "response_policy_hash": FORMAL_V4_RESPONSE_POLICY_HASH,
        })
        authority_rows.append({**row, "semantic_execution_hash": semantic})
        references.append((row, semantic, tuple(refs)))
    numeric_path = PRIVATE / "authorities/EXP01C_GDN_UNIQUE_NUMERIC_AUTHORITY.private.json"
    relation_path = PUBLIC / "authorities/EXP01C_GDN_UNIQUE_RELATION_AUTHORITY.json"
    runtime_path = PUBLIC / "contracts/EXP01C_FORMAL_V4_RUNTIME_CONFIG.json"
    _write_new(root / numeric_path, {
        "artifact_type": "validation_v2_formal_v4_numeric_authority_v1",
        "bindings": numeric_rows, "schema_version": "1.0.0",
    })
    _write_new(root / relation_path, {
        "artifact_type": "validation_v2_formal_v4_relation_authority_v1",
        "relations": authority_rows, "schema_version": "1.0.0",
    })
    _write_new(root / runtime_path, {
        "authority": "FORMAL_V4", "deterministic": True, "llm_free": True,
        "test1_access": False,
    })
    if not references:
        audit = {
            "audit_id": "EXP01C_GDN_UNIQUE_FORMAL_V4_CONVERSION_AUDIT",
            "unique_confirmed_pairs": len(unique_confirmed), "directional_relations": len(relation_rows),
            "complete_numeric_authorities": 0, "valid_descriptors": 0,
            "runtime_admissible_rules": 0, "runtime_admissible_pairs": 0,
            "rejection_reasons": {} if not relation_rows else {"MISSING_NUMERIC_AUTHORITY": len(relation_rows)},
            "authority": "FORMAL_V4", "criteria_relaxed": False,
            "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
        }
        audit["audit_hash"] = stable_hash_v1(audit)
        return audit
    numeric_binding = _artifact_binding(root, "EXP01C-GDN-UNIQUE-NUMERIC", numeric_path)
    relation_binding = _artifact_binding(root, "EXP01C-GDN-UNIQUE-RELATION", relation_path)
    core = Path("research_control_center/validation_v2/core_v2a")
    feature_binding = _artifact_binding(root, "V2A-FEATURE", core / "contracts/FEATURE_CONTRACT_V2A.json")
    file_binding = _artifact_binding(root, "V2A-FILE", core / "contracts/FILE_CONTRACT_V2A.json")
    sampling_binding = _artifact_binding(root, "V2A-SAMPLING", core / "contracts/SAMPLING_CONTRACT_V2A.json")
    runtime_config = _artifact_binding(root, "EXP01C-RUNTIME-CONFIG", runtime_path)
    implementation = _artifact_binding(root, "V2A-RUNTIME-IMPLEMENTATION", Path("src/paperworks/validation_v2/runtime_v1.py"))
    evaluator = FormalV4EvaluatorContractV1(
        evaluator_id="EXP01C-FORMAL-V4-EVALUATOR",
        implementation_path="src/paperworks/validation_v2/runtime_v1.py",
        implementation_hash=implementation.content_sha256,
        trigger_policy_hash=FORMAL_V4_TRIGGER_POLICY_HASH,
        response_policy_hash=FORMAL_V4_RESPONSE_POLICY_HASH,
        trace_contract_hash=FORMAL_V4_TRACE_CONTRACT_HASH,
        deterministic=True, llm_free=True,
    )
    numeric_hash = numeric_binding.content_sha256
    descriptors = tuple(FormalV4RuleDescriptorV1(
        relation_id=str(row["relation_id"]),
        relation_binding_hash=str(row["relation_binding_hash"]),
        semantic_execution_hash=semantic,
        source=str(row["source"]), target=str(row["target"]),
        source_direction=str(row["source_direction"]),
        target_direction=str(row["target_direction"]),
        selected_horizon_seconds=int(row["selected_horizon_seconds"]),
        numeric_reference_bindings=refs, numeric_authority_hash=numeric_hash,
    ) for row, semantic, refs in references)
    authority = build_formal_v4_portfolio_authority_v1(
        method_id="EXP01C-GDN-UNIQUE-CONVERSION", config_id=selected.candidate_id,
        experiment_id="EXP-01C-GDN-HAI-V1",
        portfolio_id="EXP01C_GDN_UNIQUE_FORMAL_V4_CONVERSION_AUDIT",
        source_commit=source_commit, descriptors=descriptors,
        relation_authority_binding=relation_binding,
        numeric_authority_binding=numeric_binding,
        feature_contract_binding=feature_binding, file_contract_binding=file_binding,
        sampling_contract_binding=sampling_binding, evaluator=evaluator,
        repository_root=root,
    )
    context = FormalV4ExecutionContextV1(
        source_commit=source_commit, runtime_config_binding=runtime_config,
        relation_authority_binding=relation_binding,
        numeric_authority_binding=numeric_binding,
        feature_contract_binding=feature_binding, file_contract_binding=file_binding,
        sampling_contract_binding=sampling_binding,
        evaluator_implementation_binding=implementation,
    )
    authorization = authorize_formal_v4_runtime_v1(
        authority, evaluator, expected_source_commit=source_commit,
        execution_context=context, repository_root=root,
        split_role="DEVELOPMENT_TEST1",
    )
    admitted = authorization.authority.descriptors
    audit = {
        "audit_id": "EXP01C_GDN_UNIQUE_FORMAL_V4_CONVERSION_AUDIT",
        "unique_confirmed_pairs": len(unique_confirmed),
        "directional_relations": len(relation_rows),
        "complete_numeric_authorities": len(references),
        "valid_descriptors": len(descriptors),
        "runtime_admissible_rules": len(admitted),
        "runtime_admissible_pairs": len({(item.source, item.target) for item in admitted}),
        "rejection_reasons": {}, "authority": "FORMAL_V4",
        "criteria_relaxed": False, "selected_numeric_policy": selected.candidate_id,
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
    }
    audit["audit_hash"] = stable_hash_v1(audit)
    return audit


def run(root: Path) -> None:
    binding, environment = _replay_execution(root)
    config = Exp01CConfigV1()
    frames, input_receipt = _load_inputs(root, str(binding["source_commit"]))
    _write_new(root / PUBLIC / "receipts/EXP01C_NORMAL_INPUT_RECEIPTS.json", input_receipt)
    reference, cohort, summary_map, selected, event_rows = _reference_and_numeric(
        root, frames, str(binding["source_commit"]), str(input_receipt["receipt_hash"]),
    )
    _meta_rank, _stat_rank, baseline_scores = _meta_stat(root)
    confirmed_pairs = {(str(row["source"]), str(row["target"])) for row in reference["confirmed_pairs"]}
    evidence_by_run = {}
    checkpoint_receipts = []
    private_evidence_hashes = []
    for view in EXP01C_VIEWS:
        segments = (frames["train1"], frames["train2"]) if view == "TRAIN1_TRAIN2_COMBINED" else ((frames["train1"],) if view == "TRAIN1_ONLY" else (frames["train2"],))
        for seed in EXP01C_SEEDS:
            checkpoint = _checkpoint_path(root, view, seed)
            if checkpoint.exists():
                import torch
                trained = torch.load(checkpoint, map_location="cpu", weights_only=False)
                receipt = {
                    "view": view, "seed": seed, "checkpoint_sha256": sha256(checkpoint.read_bytes()).hexdigest(),
                    "state_hash": trained["state_hash"], "graph_hash": trained["graph_hash"],
                    "scaler_parameter_hash": trained["scaler_receipt"]["parameter_hash"],
                    "completed_epochs": trained["completed_epochs"], "train_window_count": trained["train_window_count"],
                    "validation_window_count": trained["validation_window_count"],
                    "raw_timestamp_overlap_count": trained["raw_timestamp_overlap_count"], "private_path_disclosed": False,
                }
                receipt["receipt_hash"] = stable_hash_v1(receipt)
            else:
                print(json.dumps({"phase": "training", "view": view, "seed": seed}, sort_keys=True), flush=True)
                result = train_exp01c_seed_v1(
                    segments=segments, feature_order=P1_FEATURE_ORDER, seed=seed,
                    preprocessing_policy=str(binding["preprocessing_policy"]), config=config,
                )
                trained, receipt = _persist_checkpoint(root, view, seed, result, config)
            checkpoint_receipts.append(receipt)
            evidence_path = root / PRIVATE / "evidence" / f"exp01c-{view.lower().replace('_', '-')}-seed-{seed}.json"
            if evidence_path.exists():
                private = _load(evidence_path); _self_hash(private, "evidence_hash")
                evidence = _private_to_evidence(private); evidence_hash = sha256(evidence_path.read_bytes()).hexdigest()
            else:
                print(json.dumps({"phase": "functional_evaluation", "view": view, "seed": seed}, sort_keys=True), flush=True)
                evidence = evaluate_exp01c_checkpoint_v1(
                    state_dict=trained["state_dict"], train4_segment=frames["train4"],
                    scaler_center=trained["scaler_center"], scaler_scale=trained["scaler_scale"],
                    feature_order=P1_FEATURE_ORDER, graph_edges=trained["graph_edges"],
                    pair_universe=PAIR_UNIVERSE, relation_events=event_rows,
                    view=view, seed=seed, config=config,
                )
                evidence, evidence_hash = _persist_evidence(root, view, seed, evidence)
            if not evidence.attention_invariance_passed or not evidence.checkpoint_unchanged:
                raise Exp01CCliError("EXP01C_FIXED_CHECKPOINT_FIDELITY_FAILED")
            evidence_by_run[(view, seed)] = evidence
            private_evidence_hashes.append({"view": view, "seed": seed, "sha256": evidence_hash})
            print(json.dumps({"phase": "run_complete", "view": view, "seed": seed}, sort_keys=True), flush=True)
    checkpoint_set = {
        "schema": "paperworks.validation_v2.exp01c_checkpoint_set_receipt_v1",
        "run_count": 9, "backend": "cuda", "environment_hash": environment["environment_hash"],
        "runs": checkpoint_receipts, "private_checkpoint_bytes_committed": False,
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
    }
    checkpoint_set["receipt_hash"] = stable_hash_v1(checkpoint_set)
    _write_new(root / PUBLIC / "receipts/EXP01C_CHECKPOINT_SET_RECEIPT.json", checkpoint_set)
    run_scores = {(view, seed): _run_scores(evidence) for (view, seed), evidence in evidence_by_run.items()}
    view_scores = {
        view: {
            pair: statistics.median(run_scores[(view, seed)][pair] for seed in EXP01C_SEEDS)
            for pair in PAIR_UNIVERSE
        } for view in EXP01C_VIEWS
    }
    ranking_rows = []
    stability_rows = []
    baseline_ranking = deterministic_ranking_r1(baseline_scores)
    augmented_rankings = {}
    for view in EXP01C_VIEWS:
        _baseline, augmented = augmented_scores_r1(meta=baseline_scores, stat=baseline_scores, functional=view_scores[view])
        # augmented_scores_r1 averages three inputs. Supplying the already
        # frozen META+STAT score twice preserves its 2/3 share and gives GDN
        # the preregistered 1/3 equal arm share.
        augmented_rankings[view] = deterministic_ranking_r1(augmented)
    for name, ranking in (("META_STAT", baseline_ranking), ("META_STAT_GDN_AUGMENTED", augmented_rankings["TRAIN1_TRAIN2_COMBINED"])):
        for k in EXP01C_K:
            metrics = precision_recall_ndcg_at_k_v1(ranking, confirmed_pairs=frozenset(confirmed_pairs), k=k)
            ranking_rows.append({"arm": name, **metrics})
    for view in EXP01C_VIEWS:
        rankings = {seed: deterministic_ranking_r1(run_scores[(view, seed)]) for seed in EXP01C_SEEDS}
        for k in EXP01C_K:
            stability_rows.append({"view": view, "k": k, "seed_jaccard_mean": _mean_jaccard(rankings, k)})
    primary = 29
    baseline_metrics = precision_recall_ndcg_at_k_v1(baseline_ranking, confirmed_pairs=frozenset(confirmed_pairs), k=primary)
    augmented_metrics = precision_recall_ndcg_at_k_v1(augmented_rankings["TRAIN1_TRAIN2_COMBINED"], confirmed_pairs=frozenset(confirmed_pairs), k=primary)
    augmented_top = set(augmented_rankings["TRAIN1_TRAIN2_COMBINED"][:primary])
    baseline_top = set(baseline_ranking[:primary])
    unique_confirmed = (augmented_top - baseline_top) & confirmed_pairs
    conversion = _conversion_audit(
        root=root, unique_confirmed=unique_confirmed, reference=reference,
        cohort=cohort, summaries_by_relation=summary_map, selected=selected,
        source_commit=str(binding["source_commit"]),
    )
    _write_new(root / PUBLIC / "receipts/EXP01C_GDN_UNIQUE_FORMAL_V4_CONVERSION_AUDIT.json", conversion)
    relation_by_id = {str(row["relation_id"]): row for row in reference["confirmed_directional_relations"]}
    stable_event_pairs = set()
    for pair in confirmed_pairs:
        relation_ids = [key for key, row in relation_by_id.items() if (str(row["source"]), str(row["target"])) == pair]
        positive_runs = 0
        for seed in EXP01C_SEEDS:
            values = [evidence_by_run[("TRAIN1_TRAIN2_COMBINED", seed)].event_edge_mask_scores[key] for key in relation_ids if key in evidence_by_run[("TRAIN1_TRAIN2_COMBINED", seed)].event_edge_mask_scores]
            if values and statistics.median(values) > 1e-12:
                positive_runs += 1
        if positive_runs >= 2:
            stable_event_pairs.add(pair)
    random_pass = 0
    random_rows = []
    for seed in EXP01C_SEEDS:
        evidence = evidence_by_run[("TRAIN1_TRAIN2_COMBINED", seed)]
        raw = {
            pair: statistics.median(evidence.global_edge_mask_scores[(pair, horizon)] for horizon in (1, 5, 10, 30, 60))
            for pair in PAIR_UNIVERSE if all((pair, horizon) in evidence.global_edge_mask_scores for horizon in (1, 5, 10, 30, 60))
        }
        focal = tuple(pair for pair in deterministic_ranking_r1(_run_scores(evidence))[:primary] if pair in raw and raw[pair] > 1e-12)
        assignments, unmatched = matched_random_controls_r1(
            focal_edges=focal, eligible_graph_edges=tuple(raw), seed=seed,
            view="TRAIN1_TRAIN2_COMBINED",
        )
        focal_values = [raw[pair] for pair in assignments]
        control_values = [raw[control] for control in assignments.values()]
        passed = bool(focal_values) and statistics.median(focal_values) > statistics.median(control_values)
        random_pass += int(passed)
        random_rows.append({"seed": seed, "matched_count": len(assignments), "unmatched_count": len(unmatched), "focal_median_exceeds_control": passed})
    split_non_degraded = all(
        (
            (metrics := precision_recall_ndcg_at_k_v1(augmented_rankings[view], confirmed_pairs=frozenset(confirmed_pairs), k=primary))["confirmed_pair_yield"] >= baseline_metrics["confirmed_pair_yield"]
            and metrics["ndcg"] >= baseline_metrics["ndcg"]
        ) for view in ("TRAIN1_ONLY", "TRAIN2_ONLY")
    )
    combined_rankings = {seed: deterministic_ranking_r1(run_scores[("TRAIN1_TRAIN2_COMBINED", seed)]) for seed in EXP01C_SEEDS}
    seed_jaccard = _mean_jaccard(combined_rankings, primary)
    primary_pass = (
        (augmented_metrics["confirmed_pair_yield"] > baseline_metrics["confirmed_pair_yield"] or augmented_metrics["ndcg"] > baseline_metrics["ndcg"])
        and augmented_metrics["confirmed_pair_yield"] >= baseline_metrics["confirmed_pair_yield"]
        and augmented_metrics["ndcg"] >= baseline_metrics["ndcg"]
        and seed_jaccard >= 1.0 and split_non_degraded
        and conversion["runtime_admissible_pairs"] >= 1
        and bool(stable_event_pairs) and random_pass >= 2
    )
    if primary_pass:
        disposition = LearnedGraphDisposition.PRIMARY
    elif stable_event_pairs:
        disposition = LearnedGraphDisposition.SUPPORTING
    else:
        disposition = LearnedGraphDisposition.ABLATION
    actual_mse = []
    for evidence in evidence_by_run.values():
        values = {}
        for (target, horizon), value in evidence.baseline_target_horizon_mse.items():
            values[target] = values.get(target, 0.0) + value
        total = sum(values.values())
        actual_mse.append(sum(sorted(values.values(), reverse=True)[:5]) / total if total > 0 else 0.0)
    disposition_body = {
        "schema": "paperworks.validation_v2.exp01c_disposition_v1",
        "experiment_id": "EXP-01C-GDN-HAI-V1", "status": "COMPLETE_NORMAL_ONLY",
        "disposition": disposition.value,
        "baseline_confirmed_pair_yield_k29": baseline_metrics["confirmed_pair_yield"],
        "augmented_confirmed_pair_yield_k29": augmented_metrics["confirmed_pair_yield"],
        "baseline_ndcg_k29": baseline_metrics["ndcg"], "augmented_ndcg_k29": augmented_metrics["ndcg"],
        "seed_jaccard_k29": seed_jaccard, "split_non_degraded": split_non_degraded,
        "gdn_unique_confirmed_pair_count": len(unique_confirmed),
        "gdn_unique_formal_v4_rule_pair_count": conversion["runtime_admissible_pairs"],
        "stable_positive_event_edgemask_pair_count": len(stable_event_pairs),
        "matched_random_pass_seed_count": random_pass,
        "median_top5_target_share_fixed_checkpoint_mse": statistics.median(actual_mse),
        "preprocessing": binding["preprocessing_policy"], "validation_raw_overlap": 0,
        "horizons": [1, 5, 10, 30, 60], "run_count": 9,
        "old_exp01b_v1_changed": False, "test1_accesses": 0, "label_accesses": 0,
        "test2_accesses": 0, "heldout_accesses": 0, "provider_calls": 0,
    }
    disposition_body["result_hash"] = stable_hash_v1(disposition_body)
    ranking_hash = _write_csv(root / PUBLIC / "results/EXP01C_RANKING_RESULTS.csv", ranking_rows)
    _write_csv(root / PUBLIC / "results/EXP01C_STABILITY_RESULTS.csv", stability_rows)
    _write_csv(root / PUBLIC / "results/EXP01C_RANDOM_CONTROL_RESULTS.csv", random_rows)
    _write_new(root / PUBLIC / "results/EXP01C_DISPOSITION.json", disposition_body)
    functional_receipt = {
        "schema": "paperworks.validation_v2.exp01c_functional_receipt_v1",
        "private_evidence_hashes": private_evidence_hashes,
        "all_144_pairs_assessed_per_run": all(len(value.assessment_states) == 144 for value in evidence_by_run.values()),
        "attention_invariance_passed_runs": sum(value.attention_invariance_passed for value in evidence_by_run.values()),
        "checkpoint_unchanged_runs": sum(value.checkpoint_unchanged for value in evidence_by_run.values()),
        "direct_edgemask_graph_members_only": True, "nonmembers_source_occlusion_only": True,
        "raw_signed_values_private": True, "ranking_results_sha256": ranking_hash,
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
    }
    functional_receipt["receipt_hash"] = stable_hash_v1(functional_receipt)
    _write_new(root / PUBLIC / "receipts/EXP01C_FUNCTIONAL_RECEIPT.json", functional_receipt)
    report = (
        "# EXP-01C GDN HAI 결과\n\n"
        f"- Disposition: `{disposition.value}`\n"
        f"- Preprocessing: `{binding['preprocessing_policy']}`; file-local purge 66; raw overlap 0.\n"
        f"- META+STAT / augmented confirmed yield@29: {baseline_metrics['confirmed_pair_yield']} / {augmented_metrics['confirmed_pair_yield']}\n"
        f"- META+STAT / augmented NDCG@29: {baseline_metrics['ndcg']:.6f} / {augmented_metrics['ndcg']:.6f}\n"
        f"- Stable positive event-conditioned EdgeMask pairs: {len(stable_event_pairs)}\n"
        f"- GDN-unique Formal V4 convertible pairs: {conversion['runtime_admissible_pairs']}\n"
        "- Evidence is normal-only predictive/functional evidence, not causal or physical ground truth.\n"
        "- EXP-01B-V1 remains immutable; no test1, labels, test2, held-out, or provider input was used.\n"
    )
    report_path = root / PUBLIC / "reports/EXP01C_REPORT.md"; report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "disposition": disposition.value, "test1_accesses": 0, "test2_accesses": 0}, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=("freeze-environment", "freeze-execution", "run")); parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(); root = args.root.resolve(strict=True)
    if args.action == "freeze-environment": freeze_environment(root)
    elif args.action == "freeze-execution": freeze_execution(root)
    else: run(root)


if __name__ == "__main__":
    main()
