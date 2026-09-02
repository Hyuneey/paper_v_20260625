#!/usr/bin/env python3
"""Close EXP-01B public audit lineage without retraining.

The original scientific result and disposition are immutable inputs.  This
post-execution closure replays the nine private checkpoints, recomputes only
the omitted embedding/attention evidence and matched controls, and publishes
ordered arm identities plus a self-hashed result bundle.  It opens only the
four authorized normal splits and has no label/test/held-out capability.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
import math
import os
from pathlib import Path
import statistics
from typing import Any, Iterable, Mapping, Sequence

import run_exp01b_gdn_xai as original

from paperworks.validation_v2.exp01_relation_confirmation_v2 import (
    fit_and_confirm_arbitrary_union_v2,
)
from paperworks.validation_v2.exp01_scientific_v1 import (
    FEATURE_ORDER_HASH,
    PAIR_UNIVERSE,
    PAIR_UNIVERSE_HASH,
)
from paperworks.validation_v2.exp01b_backend_v1 import (
    Exp01BDeviceTrainingConfigV1,
    Exp01BLineageEvidenceV1,
    evaluate_exp01b_lineage_v1,
    evaluate_selected_edge_masks_v1,
)
from paperworks.validation_v2.exp01b_checkpoint_v1 import (
    Exp01BCheckpointReceiptV1,
    checkpoint_set_receipt_v1,
    checkpoint_state_hash_v1,
)
from paperworks.validation_v2.exp01b_contract_v1 import EVALUATION_BUDGETS, PRIMARY_BUDGET, VIEWS
from paperworks.validation_v2.exp01b_functional_v1 import matched_random_controls_v1
from paperworks.validation_v2.exp01b_ranking_v1 import (
    aggregate_seed_percentiles_v1,
    deterministic_ranking_v1,
    directional_relation_yield_at_k_v1,
    equal_weight_augmented_scores_v1,
    functional_consensus_v1,
    jaccard_at_k_v1,
    precision_recall_ndcg_at_k_v1,
    ranking_membership_percentiles_v1,
    target_local_percentiles_v1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


PUBLIC_ROOT = Path("research_control_center/validation_v2/exp01b_gdn_xai")
RESULT_ROOT = PUBLIC_ROOT / "results"
RECEIPT_ROOT = PUBLIC_ROOT / "receipts"
PRIVATE_ROOT = Path("artifacts/validation_v2/exp01b_gdn_xai/private")
PRIVATE_LINEAGE_CACHE = PRIVATE_ROOT / "lineage_cache_v2"
ORIGINAL_RESULT_NAMES = (
    "EXP01B_DISPOSITION.json",
    "EXP01B_CHECKPOINT_SET_RECEIPT.json",
    "EXP01B_RANKING_RESULTS.csv",
    "EXP01B_STABILITY_RESULTS.csv",
    "EXP01B_FUNCTIONAL_RESULTS.csv",
    "EXP01B_RULE_CONVERSION_RESULTS.csv",
)


class Exp01BLineageClosureError(RuntimeError):
    pass


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Exp01BLineageClosureError("EXP01B_LINEAGE_INPUT_UNAVAILABLE") from exc
    if type(value) is not dict:
        raise Exp01BLineageClosureError("EXP01B_LINEAGE_INPUT_INVALID")
    return value


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _write_new_json(path: Path, body: Mapping[str, Any], *, hash_field: str = "receipt_hash") -> dict[str, Any]:
    document = {**body, hash_field: stable_hash_v1(body)}
    original._assert_public_document_safe(document)
    original._write_new(path, document)
    return document


def _write_new_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        raise Exp01BLineageClosureError(f"EXP01B_EMPTY_PUBLIC_TABLE:{path.name}")
    columns = tuple(rows[0])
    if any(tuple(row) != columns for row in rows):
        raise Exp01BLineageClosureError(f"EXP01B_INCONSISTENT_PUBLIC_TABLE:{path.name}")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    payload = buffer.getvalue().encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    if path.read_bytes() != payload:
        raise Exp01BLineageClosureError("EXP01B_PUBLIC_TABLE_REOPEN_MISMATCH")
    return sha256(payload).hexdigest()


def _write_atomic_private_json(path: Path, document: Mapping[str, Any]) -> None:
    """Persist one resumable private cache entry and verify its bytes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(document) + b"\n"
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    if path.exists() or temporary.exists():
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_TARGET_EXISTS")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    if path.read_bytes() != payload:
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_REOPEN_MISMATCH")


def _implementation_identity(root: Path) -> dict[str, Any]:
    files = {
        "lineage_script": "scripts/finalize_exp01b_public_lineage.py",
        "lineage_backend": "src/paperworks/validation_v2/exp01b_backend_v1.py",
    }
    hashes = {name: _sha256_file(root / path) for name, path in files.items()}
    body = {
        "algorithm": "EXP01B_VECTORIZED_ATTENTION_LINEAGE_V2",
        "files": files,
        "file_sha256": hashes,
    }
    return {**body, "implementation_hash": stable_hash_v1(body)}


def _score_rows(scores: Mapping[tuple[str, str], float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (source, target), value in sorted(scores.items()):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_SCORE_NONFINITE")
        rows.append({"source": source, "target": target, "value": numeric})
    return rows


def _scores_from_rows(rows: object) -> dict[tuple[str, str], float]:
    if type(rows) is not list:
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_SCORE_ROWS_INVALID")
    result: dict[tuple[str, str], float] = {}
    for row in rows:
        if type(row) is not dict:
            raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_SCORE_ROW_INVALID")
        pair = (str(row.get("source")), str(row.get("target")))
        value = float(row.get("value"))
        if pair in result or pair not in PAIR_UNIVERSE or not math.isfinite(value):
            raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_SCORE_IDENTITY_INVALID")
        result[pair] = value
    return result


def _cache_identity(
    *, run_id: str, view: str, seed: int,
    checkpoint_receipt: Exp01BCheckpointReceiptV1,
    scientific_input_receipt_hashes: Mapping[str, str],
    original_input_receipt_hash: str, preregistration_hash: str,
    environment_hash: str, source_commit: str,
    implementation: Mapping[str, Any], config: Exp01BDeviceTrainingConfigV1,
) -> dict[str, Any]:
    body = {
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "run_id": run_id,
        "view": view,
        "seed": seed,
        "checkpoint_receipt_hash": checkpoint_receipt.public_document()["receipt_hash"],
        "checkpoint_sha256": checkpoint_receipt.checkpoint_sha256,
        "checkpoint_state_hash": checkpoint_receipt.state_hash,
        "graph_hash": checkpoint_receipt.graph_hash,
        "normal_split_receipt_hashes": dict(sorted(scientific_input_receipt_hashes.items())),
        "original_normal_input_receipt_hash": original_input_receipt_hash,
        "preregistration_hash": preregistration_hash,
        "environment_hash": environment_hash,
        "training_config_hash": config.hyperparameter_hash,
        "execution_backend_hash": config.execution_backend_hash,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "pair_universe_hash": PAIR_UNIVERSE_HASH,
        "source_commit": source_commit,
        "implementation_hash": implementation["implementation_hash"],
        "dtype": "float32",
        "device": config.device,
        "batch_size": config.batch_size,
        "attention_atol": 1e-7,
        "attention_rtol": 1e-6,
    }
    return {**body, "identity_hash": stable_hash_v1(body)}


def _cache_document(
    *, identity: Mapping[str, Any], evidence: Exp01BLineageEvidenceV1,
) -> dict[str, Any]:
    body = {
        "schema": "paperworks.validation_v2.exp01b_private_lineage_cache_v2",
        "schema_version": "2.0.0",
        "status": "COMPLETE",
        "identity": dict(identity),
        "embedding_scores": _score_rows(evidence.embedding_scores),
        "attention_scores": _score_rows(evidence.attention_scores),
        "attention_invariance_passed": evidence.attention_invariance_passed,
        "graph_edges": [list(edge) for edge in evidence.graph_edges],
        "graph_hash": evidence.graph_hash,
        "training_reexecuted": False,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
    }
    return {**body, "cache_hash": stable_hash_v1(body)}


def _load_private_cache(
    path: Path, *, expected_identity: Mapping[str, Any],
) -> Exp01BLineageEvidenceV1 | None:
    if not path.exists():
        return None
    document = _load_json(path)
    body = {key: value for key, value in document.items() if key != "cache_hash"}
    if (
        document.get("cache_hash") != stable_hash_v1(body)
        or document.get("schema") != "paperworks.validation_v2.exp01b_private_lineage_cache_v2"
        or document.get("status") != "COMPLETE"
        or document.get("identity") != dict(expected_identity)
        or document.get("training_reexecuted") is not False
        or any(int(document.get(key, -1)) != 0 for key in (
            "test1_accesses", "label_accesses", "test2_accesses", "heldout_accesses",
        ))
    ):
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_IDENTITY_REPLAY_FAILED")
    graph_rows = document.get("graph_edges")
    if type(graph_rows) is not list:
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_GRAPH_INVALID")
    graph = tuple((str(row[0]), str(row[1])) for row in graph_rows if type(row) is list and len(row) == 2)
    if len(graph) != len(graph_rows) or len(graph) != len(set(graph)):
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_GRAPH_INVALID")
    if stable_hash_v1({"graph_edges": graph}) != document.get("graph_hash"):
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_GRAPH_HASH_MISMATCH")
    embedding = _scores_from_rows(document.get("embedding_scores"))
    attention = _scores_from_rows(document.get("attention_scores"))
    if set(embedding) != set(PAIR_UNIVERSE) or not set(attention).issubset(PAIR_UNIVERSE):
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_ARM_CLOSURE_MISMATCH")
    return Exp01BLineageEvidenceV1(
        embedding_scores=embedding,
        attention_scores=attention,
        attention_invariance_passed=bool(document.get("attention_invariance_passed")),
        graph_edges=graph,
        graph_hash=str(document.get("graph_hash")),
    )


def _persist_private_cache(
    path: Path, *, identity: Mapping[str, Any], evidence: Exp01BLineageEvidenceV1,
) -> str:
    document = _cache_document(identity=identity, evidence=evidence)
    _write_atomic_private_json(path, document)
    replay = _load_private_cache(path, expected_identity=identity)
    if replay is None or replay.graph_hash != evidence.graph_hash:
        raise Exp01BLineageClosureError("EXP01B_PRIVATE_CACHE_POSTWRITE_REPLAY_FAILED")
    return str(document["cache_hash"])


def _read_functional_rows(path: Path) -> dict[tuple[str, str, int], dict[tuple[str, str], float]]:
    result: dict[tuple[str, str, int], dict[tuple[str, str], float]] = {}
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (str(row["arm"]), str(row["view"]), int(row["seed"]))
            pair = (str(row["source"]), str(row["target"]))
            if pair not in PAIR_UNIVERSE:
                raise Exp01BLineageClosureError("EXP01B_FUNCTIONAL_PAIR_OUTSIDE_UNIVERSE")
            result.setdefault(key, {})[pair] = float(row["relative_delta_mse"])
    expected = {
        (arm, view, seed)
        for arm in ("GDN_EDGEMASK", "GDN_SOURCE_OCCLUSION")
        for view in VIEWS
        for seed in (11, 23, 37)
    }
    if set(result) != expected:
        raise Exp01BLineageClosureError("EXP01B_FUNCTIONAL_ARM_CLOSURE_MISMATCH")
    return result


def _checkpoint_receipt(torch_module: Any, path: Path) -> tuple[dict[str, Any], Exp01BCheckpointReceiptV1]:
    with path.open("rb") as stream:
        payload = torch_module.load(stream, map_location="cpu", weights_only=False)
    if type(payload) is not dict or type(payload.get("state_dict")) is not dict:
        raise Exp01BLineageClosureError("EXP01B_CHECKPOINT_PAYLOAD_INVALID")
    receipt = Exp01BCheckpointReceiptV1(
        run_id=str(payload.get("run_id")),
        view=str(payload.get("view")),
        seed=int(payload.get("seed")),
        checkpoint_sha256=_sha256_file(path),
        state_hash=checkpoint_state_hash_v1(payload["state_dict"]),
        training_config_hash=str(payload.get("training_config_hash")),
        environment_hash=str(payload.get("environment_hash")),
        graph_hash=str(payload.get("graph_hash")),
        byte_size=path.stat().st_size,
    )
    return payload, receipt


def _mean_pairwise_jaccard(rankings: Mapping[int, Sequence[tuple[str, str]]], k: int) -> float:
    return statistics.mean(
        jaccard_at_k_v1(rankings[left], rankings[right], k=k)
        for left, right in ((11, 23), (11, 37), (23, 37))
    )


def _reference_rows(
    *, train1: Any, train2: Any, train3: Any, receipt_hashes: Mapping[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    confirmation = fit_and_confirm_arbitrary_union_v2(
        candidate_pairs=PAIR_UNIVERSE,
        train1_matrix=train1,
        train2_matrix=train2,
        train3_matrix=train3,
        feature_order=P1_FEATURE_ORDER,
        train1_read_receipt_hash=receipt_hashes["train1"],
        train2_read_receipt_hash=receipt_hashes["train2"],
        train3_read_receipt_hash=receipt_hashes["train3"],
    )
    ledger = confirmation.private_ledger
    ledger_hash = str(ledger.get("ledger_hash"))
    directional: list[dict[str, Any]] = []
    for item in ledger.get("directional_confirmation", ()):
        if not bool(item.get("confirmed")):
            continue
        identity = {
            "namespace": "EXP01B_NORMAL_CONFIRMED_DIRECTIONAL_RELATION_V1",
            "source": str(item["source"]),
            "target": str(item["target"]),
            "source_direction": str(item["source_direction"]),
            "target_direction": str(item["target_direction"]),
            "selected_horizon_seconds": int(item["horizon"]),
            "confirmation_ledger_hash": ledger_hash,
        }
        binding = stable_hash_v1(identity)
        directional.append({
            "relation_id": f"EXP01B-REL-{binding[:24]}",
            "source": identity["source"],
            "target": identity["target"],
            "source_direction": identity["source_direction"],
            "target_direction": identity["target_direction"],
            "selected_horizon_seconds": identity["selected_horizon_seconds"],
            "relation_binding_hash": binding,
        })
    directional.sort(key=lambda row: str(row["relation_id"]))
    pair_set = sorted({(str(row["source"]), str(row["target"])) for row in directional})
    pairs = [{"source": source, "target": target} for source, target in pair_set]
    return pairs, directional, ledger_hash


def _rank_rows(
    *, arm: str, view: str, scores: Mapping[tuple[str, str], float],
) -> tuple[tuple[tuple[str, str], ...], list[dict[str, Any]]]:
    ranking = deterministic_ranking_v1(scores)
    rows = [
        {"arm": arm, "view": view, "rank": rank, "source": pair[0], "target": pair[1]}
        for rank, pair in enumerate(ranking, start=1)
    ]
    return ranking, rows


def _write_lineage_input_attempt(
    root: Path, *, closure_input_receipt: Mapping[str, Any],
    original_input_receipt_hash: str,
) -> tuple[dict[str, Any], list[str]]:
    """Append an access receipt while preserving interrupted attempt history."""

    receipt_root = root / RECEIPT_ROOT
    base = receipt_root / "EXP01B_LINEAGE_CLOSURE_INPUT_RECEIPT.json"
    attempts = sorted(receipt_root.glob("EXP01B_LINEAGE_CLOSURE_INPUT_ATTEMPT_*.json"))
    history_paths = ([base] if base.exists() else []) + attempts
    history_hashes: list[str] = []
    cumulative = {split: 1 for split in ("train1", "train2", "train3", "train4")}
    previous_hash: str | None = None
    for path in history_paths:
        document = _load_json(path)
        body = {key: value for key, value in document.items() if key != "receipt_hash"}
        if document.get("receipt_hash") != stable_hash_v1(body):
            raise Exp01BLineageClosureError("EXP01B_LINEAGE_INPUT_HISTORY_HASH_MISMATCH")
        counts = document.get("cumulative_known_split_open_counts")
        if type(counts) is not dict or set(counts) != set(cumulative):
            raise Exp01BLineageClosureError("EXP01B_LINEAGE_INPUT_HISTORY_COUNT_INVALID")
        cumulative = {split: int(counts[split]) for split in cumulative}
        history_hashes.append(str(document["receipt_hash"]))
        previous_hash = str(document["receipt_hash"])
    next_counts = {split: cumulative[split] + 1 for split in cumulative}
    attempt_number = len(history_paths) + 1
    body = {
        **{key: value for key, value in closure_input_receipt.items() if key != "receipt_hash"},
        "schema": "paperworks.validation_v2.exp01b_lineage_closure_input_attempt_v2",
        "purpose": "DETERMINISTIC_POST_EXECUTION_PUBLIC_LINEAGE_CLOSURE",
        "closure_attempt": attempt_number,
        "training_reexecuted": False,
        "cumulative_known_split_open_counts": next_counts,
        "original_input_receipt_hash": original_input_receipt_hash,
        "previous_attempt_receipt_hash": previous_hash,
        "previous_attempt_interrupted_before_public_result": bool(history_paths),
    }
    path = receipt_root / f"EXP01B_LINEAGE_CLOSURE_INPUT_ATTEMPT_{attempt_number:03d}.json"
    current = _write_new_json(path, body)
    return current, [*history_hashes, str(current["receipt_hash"])]


def finalize(root: Path) -> None:
    preregistration = original._validate_preregistration(root)
    environment_document, environment = original._replay_environment(
        root, str(preregistration["preregistration_hash"]),
    )
    import torch

    original._assert_live_environment_matches_receipt(
        document=environment_document, environment=environment, torch_module=torch,
    )
    meta_ranking, stat_ranking, rule_conversion = original._load_rankings_and_conversion(root)
    scientific_inputs, closure_input_receipt = original._load_normal_inputs(
        root, source_commit=original._head(root),
    )
    original_input_receipt_hash = str(
        _load_json(root / original.NORMAL_RECEIPT)["receipt_hash"]
    )
    input_receipt, input_receipt_history = _write_lineage_input_attempt(
        root,
        closure_input_receipt=closure_input_receipt,
        original_input_receipt_hash=original_input_receipt_hash,
    )

    original_result = _load_json(root / RESULT_ROOT / "EXP01B_DISPOSITION.json")
    if original_result.get("disposition") != "GDN_ABLATION_ONLY":
        raise Exp01BLineageClosureError("EXP01B_ORIGINAL_DISPOSITION_CHANGED")
    functional = _read_functional_rows(root / RESULT_ROOT / "EXP01B_FUNCTIONAL_RESULTS.csv")
    config = Exp01BDeviceTrainingConfigV1(device="cuda")
    implementation = _implementation_identity(root)
    source_commit = original._head(root)
    evidence: dict[tuple[str, int], Any] = {}
    checkpoint_payloads: dict[tuple[str, int], dict[str, Any]] = {}
    checkpoint_receipts: list[Exp01BCheckpointReceiptV1] = []
    lineage_cache_hashes: dict[str, str] = {}
    private_root = (root / PRIVATE_ROOT).resolve(strict=True)
    cache_root = (root / PRIVATE_LINEAGE_CACHE).resolve()
    schedule = tuple((view, seed) for view in VIEWS for seed in (11, 23, 37))
    for position, (view, seed) in enumerate(schedule, start=1):
        run_id = f"exp01b-{view.lower().replace('_', '-')}-seed-{seed}"
        payload, receipt = _checkpoint_receipt(torch, private_root / f"{run_id}.pt")
        if receipt.run_id != run_id or receipt.view != view or receipt.seed != seed:
            raise Exp01BLineageClosureError("EXP01B_CHECKPOINT_SCHEDULE_MISMATCH")
        checkpoint_payloads[(view, seed)] = payload
        checkpoint_receipts.append(receipt)
        identity = _cache_identity(
            run_id=run_id, view=view, seed=seed, checkpoint_receipt=receipt,
            scientific_input_receipt_hashes=scientific_inputs.receipt_hashes,
            original_input_receipt_hash=original_input_receipt_hash,
            preregistration_hash=str(preregistration["preregistration_hash"]),
            environment_hash=str(environment_document["environment"]["environment_hash"]),
            source_commit=source_commit, implementation=implementation, config=config,
        )
        cache_path = cache_root / f"{run_id}.json"
        cached = _load_private_cache(cache_path, expected_identity=identity)
        if cached is not None:
            evidence[(view, seed)] = cached
            cache_hash = str(_load_json(cache_path)["cache_hash"])
            print(f"[{position}/9] {run_id}: verified cache hit", flush=True)
        else:
            print(f"[{position}/9] {run_id}: optimized fixed-checkpoint replay", flush=True)
            record = evaluate_exp01b_lineage_v1(
                state_dict=payload["state_dict"],
                train4_segments=(scientific_inputs.train4,),
                feature_order=P1_FEATURE_ORDER,
                expected_graph_hash=receipt.graph_hash,
                config=config,
            )
            cache_hash = _persist_private_cache(
                cache_path, identity=identity, evidence=record,
            )
            evidence[(view, seed)] = record
            print(f"[{position}/9] {run_id}: cache frozen and replayed", flush=True)
        lineage_cache_hashes[run_id] = cache_hash
    if checkpoint_set_receipt_v1(checkpoint_receipts) != _load_json(
        root / RESULT_ROOT / "EXP01B_CHECKPOINT_SET_RECEIPT.json"
    ):
        raise Exp01BLineageClosureError("EXP01B_CHECKPOINT_SET_REPLAY_MISMATCH")

    reference_pairs, directional_rows, confirmation_ledger_hash = _reference_rows(
        train1=scientific_inputs.train1,
        train2=scientific_inputs.train2,
        train3=scientific_inputs.train3,
        receipt_hashes=scientific_inputs.receipt_hashes,
    )
    confirmed_pairs = frozenset((row["source"], row["target"]) for row in reference_pairs)
    directional_pairs = tuple((row["source"], row["target"]) for row in directional_rows)
    if (
        len(reference_pairs) != int(original_result["normal_confirmed_pair_count"])
        or len(directional_rows) != int(original_result["normal_confirmed_directional_relation_count"])
    ):
        raise Exp01BLineageClosureError("EXP01B_REFERENCE_REPLAY_MISMATCH")

    reference_body = {
        "schema": "paperworks.validation_v2.exp01b_normal_confirmed_reference_receipt_v1",
        "schema_version": "1.0.0",
        "experiment_id": "EXP-01B-GDN-XAI-V1",
        "reference_wording": "normal-confirmed relation reference",
        "causal_ground_truth": False,
        "universe_pair_count": 144,
        "confirmed_pair_count": len(reference_pairs),
        "confirmed_directional_relation_count": len(directional_rows),
        "confirmed_pairs": reference_pairs,
        "confirmed_directional_relations": directional_rows,
        "private_confirmation_ledger_hash": confirmation_ledger_hash,
        "arm_blind": True,
        "train_splits": ["train1", "train2"],
        "confirmation_split": "train3",
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "private_paths_disclosed": False,
    }
    reference_receipt = _write_new_json(
        root / RECEIPT_ROOT / "EXP01B_REFERENCE_SET_RECEIPT.json", reference_body,
    )

    arm_seed_scores: dict[tuple[str, str, int], dict[tuple[str, str], float]] = {}
    for view in VIEWS:
        for seed in (11, 23, 37):
            record = evidence[(view, seed)]
            edge = target_local_percentiles_v1(functional[("GDN_EDGEMASK", view, seed)])
            attention = target_local_percentiles_v1(record.attention_scores)
            arm_seed_scores[("GDN_EMBEDDING", view, seed)] = target_local_percentiles_v1(record.embedding_scores)
            arm_seed_scores[("GDN_ATTENTION", view, seed)] = attention
            arm_seed_scores[("GDN_EDGEMASK", view, seed)] = edge
            arm_seed_scores[("GDN_SOURCE_OCCLUSION", view, seed)] = target_local_percentiles_v1(
                functional[("GDN_SOURCE_OCCLUSION", view, seed)]
            )
            arm_seed_scores[("GDN_FUNCTIONAL_CONSENSUS", view, seed)] = functional_consensus_v1(
                edge_mask=edge, attention=attention,
            )

    aggregate_scores: dict[tuple[str, str], dict[tuple[str, str], float]] = {}
    gdn_arms = (
        "GDN_EMBEDDING", "GDN_ATTENTION", "GDN_EDGEMASK",
        "GDN_SOURCE_OCCLUSION", "GDN_FUNCTIONAL_CONSENSUS",
    )
    for arm in gdn_arms:
        for view in VIEWS:
            aggregate_scores[(arm, view)] = aggregate_seed_percentiles_v1({
                seed: arm_seed_scores[(arm, view, seed)] for seed in (11, 23, 37)
            })

    pair_ranking_rows: list[dict[str, Any]] = []
    seed_ranking_rows: list[dict[str, Any]] = []
    aggregate_rankings: dict[tuple[str, str], tuple[tuple[str, str], ...]] = {}
    seed_rankings: dict[tuple[str, str, int], tuple[tuple[str, str], ...]] = {}
    for arm in gdn_arms:
        for view in VIEWS:
            ranking, rows = _rank_rows(arm=arm, view=view, scores=aggregate_scores[(arm, view)])
            aggregate_rankings[(arm, view)] = ranking
            pair_ranking_rows.extend(rows)
            for seed in (11, 23, 37):
                seed_ranking = deterministic_ranking_v1(arm_seed_scores[(arm, view, seed)])
                seed_rankings[(arm, view, seed)] = seed_ranking
                seed_ranking_rows.extend({
                    "arm": arm, "view": view, "seed": seed, "rank": rank,
                    "source": pair[0], "target": pair[1],
                } for rank, pair in enumerate(seed_ranking, start=1))

    meta_percentile = ranking_membership_percentiles_v1(meta_ranking)
    stat_percentile = ranking_membership_percentiles_v1(stat_ranking)
    meta_stat_scores, augmented_scores = equal_weight_augmented_scores_v1(
        meta=meta_percentile,
        stat=stat_percentile,
        gdn_functional_consensus=aggregate_scores[("GDN_FUNCTIONAL_CONSENSUS", "TRAIN1_TRAIN2_COMBINED")],
    )
    global_scores = {
        "META": meta_percentile,
        "STAT": stat_percentile,
        "META_STAT": meta_stat_scores,
        "META_STAT_GDN_AUGMENTED": augmented_scores,
    }
    for arm, scores in global_scores.items():
        ranking, rows = _rank_rows(arm=arm, view="GLOBAL", scores=scores)
        aggregate_rankings[(arm, "GLOBAL")] = ranking
        pair_ranking_rows.extend(rows)

    metric_rows: list[dict[str, Any]] = []
    for (arm, view), ranking in sorted(aggregate_rankings.items()):
        for k in EVALUATION_BUDGETS:
            metrics = precision_recall_ndcg_at_k_v1(ranking, confirmed_pairs=confirmed_pairs, k=k)
            metric_rows.append({
                "arm": arm, "view": view, **metrics,
                "confirmed_directional_relation_yield": directional_relation_yield_at_k_v1(
                    ranking, directional_relation_pairs=directional_pairs, k=k,
                ),
            })

    old_ranking_path = root / RESULT_ROOT / "EXP01B_RANKING_RESULTS.csv"
    with old_ranking_path.open("r", encoding="utf-8", newline="") as stream:
        old_rows = list(csv.DictReader(stream))
    replay_lookup = {
        (row["arm"], int(row["k"])): row
        for row in metric_rows if row["view"] == "GLOBAL"
    }
    for row in old_rows:
        observed = replay_lookup[(str(row["arm"]), int(row["k"]))]
        for field in ("confirmed_pair_yield", "confirmed_directional_relation_yield"):
            if int(row[field]) != int(observed[field]):
                raise Exp01BLineageClosureError("EXP01B_RANKING_COUNT_REPLAY_MISMATCH")
        for field in ("precision", "recall", "ndcg"):
            if abs(float(row[field]) - float(observed[field])) > 1e-12:
                raise Exp01BLineageClosureError("EXP01B_RANKING_VALUE_REPLAY_MISMATCH")

    stability_rows: list[dict[str, Any]] = []
    for arm in gdn_arms:
        for k in EVALUATION_BUDGETS:
            combined = {
                seed: seed_rankings[(arm, "TRAIN1_TRAIN2_COMBINED", seed)]
                for seed in (11, 23, 37)
            }
            train1 = {seed: seed_rankings[(arm, "TRAIN1_ONLY", seed)] for seed in (11, 23, 37)}
            train2 = {seed: seed_rankings[(arm, "TRAIN2_ONLY", seed)] for seed in (11, 23, 37)}
            stability_rows.append({
                "arm": arm,
                "k": k,
                "combined_seed_jaccard_mean": _mean_pairwise_jaccard(combined, k),
                "train1_seed_jaccard_mean": _mean_pairwise_jaccard(train1, k),
                "train2_seed_jaccard_mean": _mean_pairwise_jaccard(train2, k),
                "split_jaccard_aggregate": jaccard_at_k_v1(
                    aggregate_rankings[(arm, "TRAIN1_ONLY")],
                    aggregate_rankings[(arm, "TRAIN2_ONLY")], k=k,
                ),
                "split_jaccard_seed_mean": statistics.mean(
                    jaccard_at_k_v1(train1[seed], train2[seed], k=k)
                    for seed in (11, 23, 37)
                ),
            })

    matched_rows: list[dict[str, Any]] = []
    matched_seed_passes = 0
    matched_counts: dict[str, int] = {}
    for seed in (11, 23, 37):
        view = "TRAIN1_TRAIN2_COMBINED"
        edge_raw = functional[("GDN_EDGEMASK", view, seed)]
        edge_ranking = deterministic_ranking_v1(target_local_percentiles_v1(edge_raw))
        focal = tuple(pair for pair in edge_ranking[:PRIMARY_BUDGET] if pair in edge_raw)
        graph = evidence[(view, seed)].graph_edges
        assignments: list[tuple[tuple[str, str], tuple[str, str]]] = []
        for pair in focal:
            try:
                control = matched_random_controls_v1(
                    focal_edges=(pair,), eligible_graph_edges=graph, seed=seed,
                )[pair][0]
            except ValueError:
                continue
            assignments.append((pair, control))
        controls = tuple(sorted({control for _, control in assignments}))
        control_scores = evaluate_selected_edge_masks_v1(
            state_dict=checkpoint_payloads[(view, seed)]["state_dict"],
            train4_segments=(scientific_inputs.train4,),
            feature_order=P1_FEATURE_ORDER,
            graph_edges=graph,
            selected_edges=controls,
            config=config,
        )
        for focal_pair, control_pair in assignments:
            matched_rows.append({
                "view": view, "seed": seed,
                "focal_source": focal_pair[0], "focal_target": focal_pair[1],
                "control_source": control_pair[0], "control_target": control_pair[1],
                "focal_relative_delta_mse": edge_raw[focal_pair],
                "control_relative_delta_mse": control_scores[control_pair],
            })
        matched_counts[str(seed)] = len(assignments)
        if assignments and statistics.median(edge_raw[pair] for pair, _ in assignments) > statistics.median(
            control_scores[pair] for _, pair in assignments
        ):
            matched_seed_passes += 1
    if (
        matched_counts != {str(key): int(value) for key, value in original_result["matched_random_comparison_counts"].items()}
        or matched_seed_passes != int(original_result["edge_mask_exceeds_matched_random_combined_seed_count"])
    ):
        raise Exp01BLineageClosureError("EXP01B_MATCHED_RANDOM_REPLAY_MISMATCH")

    table_hashes = {
        "EXP01B_ARM_PAIR_RANKINGS.csv": _write_new_csv(
            root / RESULT_ROOT / "EXP01B_ARM_PAIR_RANKINGS.csv", pair_ranking_rows,
        ),
        "EXP01B_ARM_SEED_RANKINGS.csv": _write_new_csv(
            root / RESULT_ROOT / "EXP01B_ARM_SEED_RANKINGS.csv", seed_ranking_rows,
        ),
        "EXP01B_ARM_METRICS.csv": _write_new_csv(
            root / RESULT_ROOT / "EXP01B_ARM_METRICS.csv", metric_rows,
        ),
        "EXP01B_ARM_STABILITY.csv": _write_new_csv(
            root / RESULT_ROOT / "EXP01B_ARM_STABILITY.csv", stability_rows,
        ),
        "EXP01B_MATCHED_RANDOM_CONTROLS.csv": _write_new_csv(
            root / RESULT_ROOT / "EXP01B_MATCHED_RANDOM_CONTROLS.csv", matched_rows,
        ),
    }
    original_hashes = {name: _sha256_file(root / RESULT_ROOT / name) for name in ORIGINAL_RESULT_NAMES}

    cache_receipt = _write_new_json(
        root / RECEIPT_ROOT / "EXP01B_LINEAGE_CACHE_RECEIPT.json",
        {
            "schema": "paperworks.validation_v2.exp01b_lineage_cache_receipt_v2",
            "schema_version": "2.0.0",
            "experiment_id": "EXP-01B-GDN-XAI-V1",
            "status": "COMPLETE_NINE_CHECKPOINT_CACHE_CLOSURE",
            "cache_count": len(lineage_cache_hashes),
            "run_cache_hashes": dict(sorted(lineage_cache_hashes.items())),
            "implementation": implementation,
            "source_commit": source_commit,
            "private_cache_committed": False,
            "private_paths_disclosed": False,
            "training_reexecuted": False,
            "test1_accesses": 0,
            "label_accesses": 0,
            "test2_accesses": 0,
            "heldout_accesses": 0,
        },
    )

    attention_receipt = _write_new_json(
        root / RECEIPT_ROOT / "EXP01B_ATTENTION_CAPTURE_RECEIPT.json",
        {
            "schema": "paperworks.validation_v2.exp01b_attention_capture_receipt_v1",
            "schema_version": "1.0.0", "experiment_id": "EXP-01B-GDN-XAI-V1",
            "checkpoint_count": 9, "capture_count": 9,
            "capture_status": "AVAILABLE_INVARIANCE_PASS",
            "prediction_invariance_pass_count": 9,
            "atol": 1e-7, "rtol": 1e-6,
            "arm_pair_ranking_sha256": table_hashes["EXP01B_ARM_PAIR_RANKINGS.csv"],
            "arm_seed_ranking_sha256": table_hashes["EXP01B_ARM_SEED_RANKINGS.csv"],
            "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
            "heldout_accesses": 0, "private_paths_disclosed": False,
        },
    )
    edgemask_receipt = _write_new_json(
        root / RECEIPT_ROOT / "EXP01B_EDGEMASK_RECEIPT.json",
        {
            "schema": "paperworks.validation_v2.exp01b_edgemask_receipt_v1",
            "schema_version": "1.0.0", "experiment_id": "EXP-01B-GDN-XAI-V1",
            "fixed_checkpoint": True, "target_specific_mse": True,
            "no_edge_refill": True, "matched_random_policy": "TARGET_GRAPH_SEED_VIEW_MASK_CARDINALITY",
            "functional_results_sha256": original_hashes["EXP01B_FUNCTIONAL_RESULTS.csv"],
            "matched_controls_sha256": table_hashes["EXP01B_MATCHED_RANDOM_CONTROLS.csv"],
            "matched_seed_pass_count": matched_seed_passes,
            "matched_comparison_counts": matched_counts,
            "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
            "heldout_accesses": 0, "private_paths_disclosed": False,
        },
    )
    occlusion_receipt = _write_new_json(
        root / RECEIPT_ROOT / "EXP01B_OCCLUSION_RECEIPT.json",
        {
            "schema": "paperworks.validation_v2.exp01b_occlusion_receipt_v1",
            "schema_version": "1.0.0", "experiment_id": "EXP-01B-GDN-XAI-V1",
            "role": "SECONDARY_ROBUSTNESS_ONLY",
            "transform": "FIXED_SEED_WITHIN_FILE_SOURCE_HISTORY_BLOCK_PERMUTATION_V1",
            "file_local": True, "cross_split_mixing": False,
            "functional_results_sha256": original_hashes["EXP01B_FUNCTIONAL_RESULTS.csv"],
            "arm_pair_ranking_sha256": table_hashes["EXP01B_ARM_PAIR_RANKINGS.csv"],
            "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
            "heldout_accesses": 0, "private_paths_disclosed": False,
        },
    )

    receipt_hashes = {
        "lineage_input": input_receipt["receipt_hash"],
        "lineage_input_history": input_receipt_history,
        "lineage_cache": cache_receipt["receipt_hash"],
        "reference": reference_receipt["receipt_hash"],
        "attention": attention_receipt["receipt_hash"],
        "edgemask": edgemask_receipt["receipt_hash"],
        "occlusion": occlusion_receipt["receipt_hash"],
    }
    freeze_body = {
        "schema": "paperworks.validation_v2.exp01b_public_result_freeze_v2",
        "schema_version": "2.0.0", "experiment_id": "EXP-01B-GDN-XAI-V1",
        "status": "COMPLETE_NORMAL_ONLY_PUBLIC_LINEAGE_CLOSED",
        "closure_type": "POST_EXECUTION_DETERMINISTIC_REPLAY_NO_RETRAINING",
        "original_result_hash": original_result["result_hash"],
        "original_scientific_run_source_commit": environment_document["source_commit"],
        "lineage_closure_source_commit": original._head(root),
        "lineage_implementation": implementation,
        "preregistration_hash": preregistration["preregistration_hash"],
        "environment_receipt_hash": environment_document["receipt_hash"],
        "checkpoint_set_receipt_hash": original_result["checkpoint_set_receipt_hash"],
        "original_file_sha256": original_hashes,
        "lineage_table_sha256": table_hashes,
        "lineage_receipt_hashes": receipt_hashes,
        "lineage_resume_attempt_count": len(input_receipt_history),
        "interrupted_attempts_preserved": len(input_receipt_history) - 1,
        "arm_closure": ["META", "STAT", "META_STAT", *gdn_arms, "META_STAT_GDN_AUGMENTED"],
        "ranking_identity_rows": len(pair_ranking_rows),
        "seed_ranking_identity_rows": len(seed_ranking_rows),
        "metric_rows": len(metric_rows),
        "stability_rows": len(stability_rows),
        "disposition": "GDN_ABLATION_ONLY",
        "disposition_changed": False,
        "training_reexecuted": False,
        "hyperparameters_changed": False,
        "selection_rule_changed": False,
        "stable_unique_metric_qualification": "POSITIVE_EDGEMASK_IN_AT_LEAST_TWO_COMBINED_SEEDS_ONLY; NOT A SPLIT_STABILITY CLAIM",
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0,
        "heldout_accesses": 0, "provider_calls": 0,
        "private_paths_disclosed": False,
    }
    _write_new_json(
        root / RESULT_ROOT / "EXP01B_PUBLIC_RESULT_FREEZE_V2.json",
        freeze_body, hash_field="freeze_hash",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    finalize(args.repository_root.resolve(strict=True))


if __name__ == "__main__":
    main()
