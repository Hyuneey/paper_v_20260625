#!/usr/bin/env python3
"""Freeze and execute the normal-only V2A META+STAT / EXP-02 path.

``freeze`` consumes only committed public authorities. ``execute`` refuses to
open train1/train2/train4 unless the exact three scientific bindings replay.
Neither phase contains a label, test1, test2, held-out, or provider adapter.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

from paperworks.validation_v2.core_v2a_authority_v1 import (
    build_meta_stat_candidate_union_authority_v1,
    build_v2a_confirmed_cohort_v1,
)
from paperworks.validation_v2.exp02_bindings_v2a import (
    binding_specifications_v1,
    build_relation_summaries_for_split_v1,
    build_selection_summary_from_census_v1,
    canonical_hash_v1,
    evaluate_candidate_on_train4_v1,
    implementation_hashes_v1,
)
from paperworks.validation_v2.exp02_runner_v1 import (
    build_frozen_scientific_binding_v1,
    frozen_scientific_binding_from_dict_v1,
    validate_scientific_binding_bundle_v1,
)
from paperworks.validation_v2.hai_feature_adapter_v1 import (
    HAIFeatureAccessLedgerV1,
    load_authorized_hai_feature_frame_v1,
    resolve_hai_feature_root_capability_v1,
)
from paperworks.validation_v2.numeric_policy_v1 import (
    build_normal_policy_selection_authority_v1,
    build_numeric_policy_candidate_set_v1,
    candidate_set_hash_v1,
    derive_pooled_role_values_v1,
    select_numeric_policy_on_train4_v1,
)
from paperworks.validation_v2.protocol_v1 import (
    ProtocolExecutionGuardV1,
    ProtocolOperationV1,
    build_validation_protocol_v1,
)


PUBLIC_ROOT = Path("research_control_center/validation_v2/core_v2a")
PRIVATE_ROOT = Path("artifacts/validation_v2/core_v2a/private")
META_PATH = Path("docs/task_reports/TASK-039C_META_RESULT.json")
STAT_PATH = Path("docs/task_reports/TASK-039C_STAT_RESULT.json")
DIRECTIONAL_PATH = Path("docs/task_reports/TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json")
BINDING_IDS = (
    "EXP02-BIND-QUANTILE",
    "EXP02-BIND-RELATION-SUMMARY",
    "EXP02-BIND-OPPORTUNITY-CENSUS",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise RuntimeError("V2A_PUBLIC_DOCUMENT_INVALID")
    return value


def _bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _bytes(value)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    if path.read_bytes() != payload:
        raise RuntimeError("V2A_ATOMIC_REOPEN_MISMATCH")


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _authorities(root: Path, source_commit: str):
    meta = _load(root / META_PATH)
    stat = _load(root / STAT_PATH)
    directional = _load(root / DIRECTIONAL_PATH)
    candidate = build_meta_stat_candidate_union_authority_v1(
        meta_document=meta, stat_document=stat, source_commit=source_commit,
    )
    cohort, cohort_binding = build_v2a_confirmed_cohort_v1(
        candidate_authority=candidate,
        directional_confirmation_document=directional,
        source_commit=source_commit,
    )
    return candidate, cohort, cohort_binding


def freeze(root: Path) -> None:
    source_commit = _head(root)
    candidate, cohort, cohort_binding = _authorities(root, source_commit)
    specifications = binding_specifications_v1()
    implementations = implementation_hashes_v1()
    config_hash = canonical_hash_v1({
        "experiment": "EXP-02", "candidate_count": 37,
        "cross_source_policy": specifications["EXP02-BIND-OPPORTUNITY-CENSUS"]["cross_source_trigger_universe"],
        "selection": ["ZERO_COVERAGE_LOSS", "FALSE_SECONDS", "FALSE_EPISODES", "ABSTAIN", "FIT_VARIABILITY", "COMPLEXITY", "COMMON_TOTAL_TIE"],
    })
    bindings = tuple(build_frozen_scientific_binding_v1(
        binding_id=binding_id,
        contract_id=f"V2A-{binding_id}-V1",
        specification_hash=canonical_hash_v1(specifications[binding_id]),
        implementation_hash=implementations[binding_id],
        configuration_hash=config_hash,
        source_commit=source_commit,
    ) for binding_id in BINDING_IDS)
    bundle = validate_scientific_binding_bundle_v1(
        bindings, expected_binding_hashes={item.binding_id: item.self_hash for item in bindings},
        source_commit=source_commit,
    )
    base = root / PUBLIC_ROOT
    _write_new(base / "authorities/VALIDATION_V2_META_STAT_CANDIDATE_UNION_AUTHORITY_V1.json", candidate.to_dict())
    _write_new(base / "authorities/V2A_CONFIRMED_COHORT_AUTHORITY.json", cohort.to_dict())
    _write_new(base / "authorities/V2A_CONFIRMED_COHORT_BINDING.json", cohort_binding.to_dict())
    _write_new(base / "bindings/EXP02_SCIENTIFIC_BINDING_BUNDLE_V2A.json", {
        "artifact_type": "validation_v2a_exp02_scientific_binding_bundle_v1",
        "bindings": [item.to_dict() for item in bindings],
        "bundle_receipt": bundle.to_dict(),
        "labels_allowed": False, "test1_allowed": False, "test2_allowed": False,
    })


def _ratio(value: Any) -> dict[str, Any]:
    return value.to_dict()


def execute(root: Path) -> None:
    bundle_doc = _load(root / PUBLIC_ROOT / "bindings/EXP02_SCIENTIFIC_BINDING_BUNDLE_V2A.json")
    bindings = tuple(frozen_scientific_binding_from_dict_v1(item) for item in bundle_doc["bindings"])
    source_commit = bindings[0].source_commit
    bundle = validate_scientific_binding_bundle_v1(
        bindings, expected_binding_hashes={item.binding_id: item.self_hash for item in bindings},
        source_commit=source_commit,
    )
    if bundle.to_dict() != bundle_doc["bundle_receipt"] or bundle.labels_allowed or bundle.test1_allowed or bundle.test2_allowed:
        raise RuntimeError("V2A_BINDING_BUNDLE_REPLAY_FAILED")
    candidate_authority, cohort, cohort_binding = _authorities(root, source_commit)
    protocol = build_validation_protocol_v1(source_commit=source_commit)
    guard = ProtocolExecutionGuardV1(protocol)
    access = HAIFeatureAccessLedgerV1(experiment_id="EXP-02-V2A")
    capability = resolve_hai_feature_root_capability_v1(root)
    frames = {}
    for split in ("train1", "train2"):
        frames[split] = load_authorized_hai_feature_frame_v1(
            capability=capability, split_id=split,
            operation=ProtocolOperationV1.NUMERIC_FIT,
            protocol_guard=guard, ledger=access,
        )
    feature_order = tuple(item.source for item in ())
    from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER
    feature_order = tuple(P1_FEATURE_ORDER)
    summaries_by_split = {
        split: build_relation_summaries_for_split_v1(
            split_id=split, matrix=frames[split].numeric_matrix(),
            feature_order=feature_order, cohort=cohort,
        ) for split in ("train1", "train2")
    }
    summary_pairs = {
        relation.relation_id: tuple(
            next(item for item in summaries_by_split[split] if item.relation_id == relation.relation_id)
            for split in ("train1", "train2")
        ) for relation in cohort.relations
    }
    fit_receipts = {split: frames[split].receipt.to_dict() for split in ("train1", "train2")}
    normal_fit_input_hash = canonical_hash_v1({"fit_receipts": fit_receipts})
    candidates = build_numeric_policy_candidate_set_v1(
        cohort=cohort, normal_fit_input_hash=normal_fit_input_hash, source_commit=source_commit,
    )
    candidate_set_hash = candidate_set_hash_v1(candidates)
    frames["train4"] = load_authorized_hai_feature_frame_v1(
        capability=capability, split_id="train4",
        operation=ProtocolOperationV1.NORMAL_POLICY_SELECTION,
        protocol_guard=guard, ledger=access,
    )
    train4_receipt = frames["train4"].receipt.to_dict()
    selection_authority = build_normal_policy_selection_authority_v1(
        protocol=protocol, candidate_set_hash=candidate_set_hash,
        cohort_hash=cohort.cohort_hash, cohort_relations=len(cohort.relations),
        train4_input_hash=train4_receipt["file_sha256"],
        normal_exposure_seconds=train4_receipt["row_count"],
        metric_contract_hash=canonical_hash_v1(binding_specifications_v1()["EXP02-BIND-OPPORTUNITY-CENSUS"]),
    )
    public_rows = []
    summaries = []
    for policy in candidates:
        census = evaluate_candidate_on_train4_v1(
            candidate=policy, cohort=cohort, summaries_by_relation=summary_pairs,
            train4_matrix=frames["train4"].numeric_matrix(), feature_order=feature_order,
        )
        summary = build_selection_summary_from_census_v1(
            candidate=policy, census=census, selection_authority=selection_authority, protocol=protocol,
        )
        summaries.append(summary)
        public_rows.append({
            "candidate_id": policy.candidate_id, "candidate_hash": policy.candidate_hash,
            "retained_relations": census.retained_relations,
            "opportunity_relations": census.opportunity_relations,
            "pass_count": census.pass_count, "fail_count": census.fail_count,
            "abstain_count": census.abstain_count,
            "unsupported_relation_count": census.unsupported_relation_count,
            "system_error_count": census.system_error_count,
            "false_alarm_seconds": census.false_alarm_seconds,
            "false_alarm_episodes": census.false_alarm_episodes,
            "normal_exposure_seconds": census.normal_exposure_seconds,
            "false_alarm_seconds_per_hour": _ratio(summary.false_alarm_seconds_per_hour),
            "false_alarm_episodes_per_hour": _ratio(summary.false_alarm_episodes_per_hour),
            "opportunity_coverage": _ratio(summary.opportunity_coverage),
            "evaluation_coverage": _ratio(summary.evaluation_coverage),
            "relation_retention": _ratio(summary.relation_retention),
            "abstain_rate": _ratio(summary.abstain_rate),
            "fit_split_variability": [summary.split_variability.numerator, summary.split_variability.denominator],
            "summary_hash": summary.summary_hash,
        })
    result = select_numeric_policy_on_train4_v1(
        candidates=candidates, summaries=tuple(summaries),
        selection_authority=selection_authority, protocol=protocol,
    )
    selected = next(item for item in candidates if item.candidate_hash == result.selected_candidate_hash)
    private_numeric = {
        "artifact_type": "validation_v2a_private_formal_v4_numeric_authority_v1",
        "candidate": selected.to_dict(),
        "cohort_hash": cohort.cohort_hash,
        "relations": [{
            "relation": relation.to_dict(),
            "roles": [[role, value] for role, value in derive_pooled_role_values_v1(
                candidate=selected, summaries=summary_pairs[relation.relation_id],
            )],
        } for relation in cohort.relations],
    }
    private_hash = sha256(_bytes(private_numeric)).hexdigest()
    private_path = root / PRIVATE_ROOT / "EXP02_SELECTED_NUMERIC_AUTHORITY_V2A.private.json"
    _write_new(private_path, private_numeric)
    public = {
        "artifact_type": "EXP02_NORMAL_SELECTION_RESULTS_V2A",
        "status": "COMPLETE_QA_PENDING",
        "source_commit": source_commit,
        "candidate_authority_hash": candidate_authority.authority_hash,
        "cohort_hash": cohort.cohort_hash,
        "binding_bundle_hash": bundle.self_hash,
        "candidate_count": len(candidates),
        "selected_candidate_id": result.selected_candidate_id,
        "selected_candidate_hash": result.selected_candidate_hash,
        "selection_result_hash": result.result_hash,
        "selection_authority_hash": selection_authority.authority_hash,
        "private_numeric_authority_hash": private_hash,
        "normal_split_receipts": {**fit_receipts, "train4": train4_receipt},
        "candidate_results": public_rows,
        "access_ledger": access.public_document(),
        "test1_accesses": 0, "test2_accesses": 0, "label_accesses": 0,
        "private_paths_exposed": 0,
    }
    public["result_hash"] = canonical_hash_v1(public)
    _write_new(root / PUBLIC_ROOT / "results/EXP02_RESULTS_V2A.json", public)
    _write_new(root / PUBLIC_ROOT / "authorities/EXP02_SELECTED_POLICY_AUTHORITY_V2A.json", {
        "artifact_type": "EXP02_SELECTED_POLICY_AUTHORITY_V2A",
        "selected_candidate_id": result.selected_candidate_id,
        "selected_candidate_hash": result.selected_candidate_hash,
        "numeric_authority_hash": private_hash,
        "cohort_hash": cohort.cohort_hash,
        "selection_result_hash": result.result_hash,
        "labels_allowed": False, "runtime_authority": False,
        "test1_accesses": 0, "test2_accesses": 0,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("freeze", "execute"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repository_root.resolve(strict=True)
    if args.phase == "freeze":
        freeze(root)
    else:
        execute(root)


if __name__ == "__main__":
    main()
