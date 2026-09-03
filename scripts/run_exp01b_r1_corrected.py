#!/usr/bin/env python3
"""Execute the preregistered EXP-01B-R1 correction without retraining."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import META_RESULT_HASH, PAIR_UNIVERSE, STAT_RESULT_HASH
from paperworks.validation_v2.exp01b_contract_v1 import VIEWS
from paperworks.validation_v2.exp02_bindings_v2a import build_relation_summaries_for_split_v1
from paperworks.validation_v2.formal_v4_authority_v1 import (
    FormalV4ArtifactBindingV1, FormalV4EvaluatorContractV1,
    FormalV4ExecutionContextV1, FormalV4RuleDescriptorV1,
    NumericReferenceBindingV1, authorize_formal_v4_runtime_v1,
    build_formal_v4_portfolio_authority_v1, canonical_document_hash_v1,
)
from paperworks.validation_v2.gdn_corr_r1_runner_v1 import (
    R1EvidenceInputsV1, analyze_exp01b_r1_v1,
)
from paperworks.validation_v2.hai_feature_adapter_v1 import (
    HAIFeatureAccessLedgerV1, load_authorized_hai_feature_frame_v1,
    resolve_hai_feature_root_capability_v1,
)
from paperworks.validation_v2.numeric_policy_v1 import (
    ConfirmedRelationIdentityV1, build_confirmed_cohort_authority_v1,
    build_numeric_policy_candidate_set_v1, derive_pooled_role_values_v1,
)
from paperworks.validation_v2.protocol_v1 import (
    ProtocolExecutionGuardV1, ProtocolOperationV1, build_validation_protocol_v1,
)
from paperworks.validation_v2.runtime_policy_v1 import (
    FORMAL_V4_RESPONSE_POLICY_HASH, FORMAL_V4_TRACE_CONTRACT_HASH,
    FORMAL_V4_TRIGGER_POLICY_HASH,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


PUBLIC = Path("research_control_center/validation_v2/gdn_corr_001")
CONTRACT = PUBLIC / "contracts/EXP01B_R1_CORRECTION_CONTRACT.json"
EXECUTION_BINDING = PUBLIC / "contracts/EXP01B_R1_EXECUTION_BINDING.json"
RESULTS = PUBLIC / "exp01b_r1/results"
REPORTS = PUBLIC / "exp01b_r1/reports"
RECEIPTS = PUBLIC / "exp01b_r1/receipts"
PRIVATE = Path("artifacts/validation_v2/gdn_corr_001/exp01b_r1/private")
V2A_PUBLIC = Path("research_control_center/validation_v2/core_v2a")


class R1ExecutionError(RuntimeError):
    pass


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode() + b"\n"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise R1ExecutionError(f"EXP01B_R1_JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _write_new(path: Path, value: Mapping[str, Any], *, private: bool = False) -> str:
    payload = _canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise R1ExecutionError(f"EXP01B_R1_EXISTING_OUTPUT_MISMATCH:{path.name}")
        return sha256(payload).hexdigest()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    if path.read_bytes() != payload:
        raise R1ExecutionError(f"EXP01B_R1_REOPEN_MISMATCH:{path.name}")
    return sha256(payload).hexdigest()


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> str:
    if not rows:
        raise R1ExecutionError("EXP01B_R1_EMPTY_TABLE")
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = tuple(rows[0])
    import io
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    payload = buffer.getvalue().encode()
    if path.exists():
        if path.read_bytes() != payload:
            raise R1ExecutionError(f"EXP01B_R1_EXISTING_TABLE_MISMATCH:{path.name}")
    else:
        path.write_bytes(payload)
    return sha256(payload).hexdigest()


def _self_hash(document: Mapping[str, Any], field: str) -> None:
    body = {key: value for key, value in document.items() if key != field}
    if document.get(field) != stable_hash_v1(body):
        raise R1ExecutionError(f"EXP01B_R1_SELF_HASH_MISMATCH:{field}")


def _rankings(root: Path) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    meta = _load(root / "docs/task_reports/TASK-039C_META_RESULT.json")
    stat = _load(root / "docs/task_reports/TASK-039C_STAT_RESULT.json")
    if meta.get("artifact_hash") != META_RESULT_HASH or stat.get("artifact_hash") != STAT_RESULT_HASH:
        raise R1ExecutionError("EXP01B_R1_META_STAT_AUTHORITY_MISMATCH")
    meta_ranking = tuple((str(row["source_identity"]), str(row["target_identity"])) for row in meta["top20_identities"])
    stat_ranking = tuple((str(row["source"]), str(row["target"])) for row in stat["top20"])
    return meta_ranking, stat_ranking


def _reference(root: Path) -> tuple[frozenset[tuple[str, str]], tuple[tuple[str, str], ...], list[dict[str, Any]], str]:
    document = _load(root / "research_control_center/validation_v2/exp01b_gdn_xai/receipts/EXP01B_REFERENCE_SET_RECEIPT.json")
    _self_hash(document, "receipt_hash")
    pairs = frozenset((str(row["source"]), str(row["target"])) for row in document["confirmed_pairs"])
    relations = list(document["confirmed_directional_relations"])
    directional = tuple((str(row["source"]), str(row["target"])) for row in relations)
    return pairs, directional, relations, str(document["receipt_hash"])


def _private_evidence(private_root: Path) -> tuple[
    dict[tuple[str, int], dict[tuple[str, str], float]],
    dict[tuple[str, int], dict[tuple[str, str], float]],
    dict[tuple[str, int], tuple[tuple[str, str], ...]],
]:
    embedding = {}; attention = {}; graphs = {}
    for view in VIEWS:
        token = view.lower().replace("_", "-")
        for seed in (11, 23, 37):
            path = private_root / "lineage_cache_v2" / f"exp01b-{token}-seed-{seed}.json"
            document = _load(path)
            _self_hash(document, "cache_hash")
            if document.get("training_reexecuted") is not False or any(document.get(key) != 0 for key in ("test1_accesses", "label_accesses", "test2_accesses", "heldout_accesses")):
                raise R1ExecutionError("EXP01B_R1_PRIVATE_EVIDENCE_BOUNDARY_MISMATCH")
            def scores(name: str) -> dict[tuple[str, str], float]:
                return {(str(row["source"]), str(row["target"])): float(row["value"]) for row in document[name]}
            embedding[(view, seed)] = scores("embedding_scores")
            attention[(view, seed)] = scores("attention_scores")
            graphs[(view, seed)] = tuple(
                pair for pair in ((str(row[0]), str(row[1])) for row in document["graph_edges"])
                if pair in PAIR_UNIVERSE
            )
    return embedding, attention, graphs


def _functional(root: Path) -> dict[tuple[str, int], dict[tuple[str, str], float]]:
    path = root / "research_control_center/validation_v2/exp01b_gdn_xai/results/EXP01B_FUNCTIONAL_RESULTS.csv"
    result: dict[tuple[str, int], dict[tuple[str, str], float]] = {}
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["arm"] != "GDN_EDGEMASK":
                continue
            key = (row["view"], int(row["seed"]))
            result.setdefault(key, {})[(row["source"], row["target"])] = float(row["relative_delta_mse"])
    return result


def _binding_file(root: Path, artifact_id: str, relative: Path) -> FormalV4ArtifactBindingV1:
    return FormalV4ArtifactBindingV1(artifact_id, relative.as_posix(), sha256((root / relative).read_bytes()).hexdigest())


def _convert_unique_relations(
    root: Path, unique_pairs: Sequence[tuple[str, str]], relation_rows: Sequence[Mapping[str, Any]],
    *, source_commit: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    selected = _load(root / V2A_PUBLIC / "authorities/EXP02_SELECTED_POLICY_AUTHORITY_V2A.json")
    selected_id = str(selected["selected_candidate_id"])
    identities = tuple(ConfirmedRelationIdentityV1(
        relation_id=f"R1-{row['relation_id']}", source=str(row["source"]), target=str(row["target"]),
        source_direction=str(row["source_direction"]), target_direction=str(row["target_direction"]),
        selected_horizon_seconds=int(row["selected_horizon_seconds"]),
        relation_binding_hash=canonical_document_hash_v1({
            "namespace": "EXP01B_R1_GDN_UNIQUE", "parent": row["relation_binding_hash"],
            "source": row["source"], "target": row["target"],
            "source_direction": row["source_direction"], "target_direction": row["target_direction"],
            "horizon": row["selected_horizon_seconds"],
        }),
    ) for row in relation_rows if (str(row["source"]), str(row["target"])) in set(unique_pairs))
    if not identities:
        return {"relations": [], "numeric": []}, {
            "unique_confirmed_pairs": len(unique_pairs), "directional_relations": 0,
            "complete_numeric_authorities": 0, "valid_descriptors": 0,
            "runtime_admissible_rules": 0, "runtime_admissible_pairs": 0,
            "rejection_reasons": {"NO_GDN_UNIQUE_CONFIRMED_DIRECTIONAL_RELATION": len(unique_pairs)},
        }
    cohort = build_confirmed_cohort_authority_v1(
        cohort_id="EXP01B_R1_GDN_UNIQUE_CONFIRMED_COHORT", source_commit=source_commit,
        confirmation_artifact_hash=canonical_document_hash_v1({"reference": "EXP01B_NORMAL_CONFIRMED_REFERENCE"}),
        relations=identities,
    )
    protocol = build_validation_protocol_v1(source_commit=source_commit)
    guard = ProtocolExecutionGuardV1(protocol)
    ledger = HAIFeatureAccessLedgerV1(experiment_id="EXP-01B-R1-RULE-CONVERSION")
    capability = resolve_hai_feature_root_capability_v1(root)
    frames = {split: load_authorized_hai_feature_frame_v1(
        capability=capability, split_id=split, operation=ProtocolOperationV1.NUMERIC_FIT,
        protocol_guard=guard, ledger=ledger,
    ) for split in ("train1", "train2")}
    summaries = {split: build_relation_summaries_for_split_v1(
        split_id=split, matrix=frames[split].numeric_matrix(), feature_order=tuple(P1_FEATURE_ORDER), cohort=cohort,
    ) for split in ("train1", "train2")}
    receipt_hash = canonical_document_hash_v1({split: frames[split].receipt.to_dict() for split in ("train1", "train2")})
    candidates = build_numeric_policy_candidate_set_v1(cohort=cohort, normal_fit_input_hash=receipt_hash, source_commit=source_commit)
    candidate = next((item for item in candidates if item.candidate_id == selected_id), None)
    if candidate is None:
        raise R1ExecutionError("EXP01B_R1_SELECTED_POLICY_NOT_IN_FROZEN_GRID")
    by_relation = {relation.relation_id: tuple(
        next(item for item in summaries[split] if item.relation_id == relation.relation_id)
        for split in ("train1", "train2")
    ) for relation in identities}
    private_relations = []
    for relation in identities:
        private_relations.append({
            "relation": relation.to_dict(),
            "roles": [[role, value] for role, value in derive_pooled_role_values_v1(candidate=candidate, summaries=by_relation[relation.relation_id])],
        })
    references = []
    numeric_rows = []
    relation_authority_rows = []
    for item in private_relations:
        relation = item["relation"]
        refs = []
        for index, (role, value) in enumerate(item["roles"]):
            identity = {"relation_id": relation["relation_id"], "numeric_role": role, "value": value}
            reference_id = f"R1-NUM-{relation['relation_id']}-{index:02d}"
            reference_payload = {"relation_id": relation["relation_id"], "numeric_role": role, "reference_id": reference_id, "value": float(value)}
            ref = NumericReferenceBindingV1(role, reference_id, canonical_document_hash_v1(reference_payload))
            refs.append(ref)
            numeric_rows.append({**reference_payload, "reference_hash": ref.reference_hash})
        semantic = canonical_document_hash_v1({
            "relation_id": relation["relation_id"], "relation_binding_hash": relation["relation_binding_hash"],
            "source_direction": relation["source_direction"], "target_direction": relation["target_direction"],
            "selected_horizon_seconds": relation["selected_horizon_seconds"],
            "trigger_policy_hash": FORMAL_V4_TRIGGER_POLICY_HASH, "response_policy_hash": FORMAL_V4_RESPONSE_POLICY_HASH,
        })
        relation_authority_rows.append({**relation, "semantic_execution_hash": semantic})
        references.append((relation, semantic, tuple(refs)))
    numeric_relative = PRIVATE / "GDN_UNIQUE_FORMAL_V4_NUMERIC_AUTHORITY.private.json"
    _write_new(root / numeric_relative, {
        "artifact_type": "validation_v2_formal_v4_numeric_authority_v1",
        "bindings": numeric_rows, "schema_version": "1.0.0",
    }, private=True)
    numeric_hash = sha256((root / numeric_relative).read_bytes()).hexdigest()
    relation_relative = RECEIPTS / "GDN_UNIQUE_RELATION_AUTHORITY.json"
    _write_new(root / relation_relative, {
        "artifact_type": "validation_v2_formal_v4_relation_authority_v1",
        "relations": relation_authority_rows, "schema_version": "1.0.0",
    })
    runtime_relative = PUBLIC / "exp01b_r1/contracts/RUNTIME_CONFIG.json"
    _write_new(root / runtime_relative, {"authority": "FORMAL_V4", "deterministic": True, "llm_free": True, "test1_access": False})
    numeric_binding = _binding_file(root, "EXP01B-R1-NUMERIC", numeric_relative)
    relation_binding = _binding_file(root, "EXP01B-R1-RELATION", relation_relative)
    feature_binding = _binding_file(root, "V2A-FEATURE", V2A_PUBLIC / "contracts/FEATURE_CONTRACT_V2A.json")
    file_binding = _binding_file(root, "V2A-FILE", V2A_PUBLIC / "contracts/FILE_CONTRACT_V2A.json")
    sampling_binding = _binding_file(root, "V2A-SAMPLING", V2A_PUBLIC / "contracts/SAMPLING_CONTRACT_V2A.json")
    runtime_config = _binding_file(root, "EXP01B-R1-RUNTIME-CONFIG", runtime_relative)
    runtime_impl = _binding_file(root, "V2A-RUNTIME-IMPLEMENTATION", Path("src/paperworks/validation_v2/runtime_v1.py"))
    evaluator = FormalV4EvaluatorContractV1(
        evaluator_id="EXP01B-R1-FORMAL-V4-EVALUATOR", implementation_path="src/paperworks/validation_v2/runtime_v1.py",
        implementation_hash=runtime_impl.content_sha256, trigger_policy_hash=FORMAL_V4_TRIGGER_POLICY_HASH,
        response_policy_hash=FORMAL_V4_RESPONSE_POLICY_HASH, trace_contract_hash=FORMAL_V4_TRACE_CONTRACT_HASH,
        deterministic=True, llm_free=True,
    )
    descriptors = tuple(FormalV4RuleDescriptorV1(
        relation_id=relation["relation_id"], relation_binding_hash=relation["relation_binding_hash"], semantic_execution_hash=semantic,
        source=relation["source"], target=relation["target"], source_direction=relation["source_direction"],
        target_direction=relation["target_direction"], selected_horizon_seconds=relation["selected_horizon_seconds"],
        numeric_reference_bindings=refs, numeric_authority_hash=numeric_hash,
    ) for relation, semantic, refs in references)
    authority = build_formal_v4_portfolio_authority_v1(
        method_id="EXP01B-R1-GDN-UNIQUE-CONVERSION", config_id=selected_id, experiment_id="EXP-01B-R1",
        portfolio_id="GDN_UNIQUE_FORMAL_V4_CONVERSION_AUDIT_V1", source_commit=source_commit,
        descriptors=descriptors, relation_authority_binding=relation_binding, numeric_authority_binding=numeric_binding,
        feature_contract_binding=feature_binding, file_contract_binding=file_binding, sampling_contract_binding=sampling_binding,
        evaluator=evaluator, repository_root=root,
    )
    context = FormalV4ExecutionContextV1(
        source_commit=source_commit, runtime_config_binding=runtime_config, relation_authority_binding=relation_binding,
        numeric_authority_binding=numeric_binding, feature_contract_binding=feature_binding, file_contract_binding=file_binding,
        sampling_contract_binding=sampling_binding, evaluator_implementation_binding=runtime_impl,
    )
    authorization = authorize_formal_v4_runtime_v1(
        authority, evaluator, expected_source_commit=source_commit, execution_context=context,
        repository_root=root, split_role="DEVELOPMENT_TEST1",
    )
    audit = {
        "audit_id": "GDN_UNIQUE_FORMAL_V4_CONVERSION_AUDIT_V1",
        "unique_confirmed_pairs": len(unique_pairs), "directional_relations": len(identities),
        "complete_numeric_authorities": len(identities), "valid_descriptors": len(descriptors),
        "runtime_admissible_rules": len(authorization.authority.descriptors),
        "runtime_admissible_pairs": len({(item.source, item.target) for item in authorization.authority.descriptors}),
        "rejection_reasons": {}, "selected_numeric_policy": selected_id,
        "access_ledger": ledger.public_document(), "test1_accesses": 0, "label_accesses": 0,
        "test2_accesses": 0, "heldout_accesses": 0,
    }
    return {"candidate": candidate.to_dict(), "relations": private_relations}, audit


def execute(root: Path, private_root: Path) -> None:
    contract = _load(root / CONTRACT); _self_hash(contract, "contract_hash")
    binding_path = root / EXECUTION_BINDING.with_name("EXP01B_R1_EXECUTION_BINDING_R2.json")
    binding = _load(binding_path); _self_hash(binding, "binding_hash")
    if binding.get("contract_hash") != contract["contract_hash"]:
        raise R1ExecutionError("EXP01B_R1_EXECUTION_BINDING_CONTRACT_MISMATCH")
    old = _load(root / "research_control_center/validation_v2/exp01b_gdn_xai/results/EXP01B_DISPOSITION.json")
    old_bytes = (root / "research_control_center/validation_v2/exp01b_gdn_xai/results/EXP01B_DISPOSITION.json").read_bytes()
    meta, stat = _rankings(root)
    confirmed, directional, relation_rows, reference_hash = _reference(root)
    embedding, attention, graphs = _private_evidence(private_root)
    edge_mask = _functional(root)
    inputs = R1EvidenceInputsV1(meta, stat, confirmed, directional, embedding, attention, edge_mask, graphs)
    preliminary = analyze_exp01b_r1_v1(inputs, unique_executable_rule_pair_count=0)
    _private_numeric, conversion = _convert_unique_relations(
        root, preliminary.gdn_unique_confirmed_pairs, relation_rows, source_commit=str(binding["source_commit"]),
    )
    result = analyze_exp01b_r1_v1(inputs, unique_executable_rule_pair_count=int(conversion["runtime_admissible_pairs"]))
    metric_hash = _write_csv(root / RESULTS / "EXP01B_R1_CORRECTED_RESULTS.csv", result.metric_rows)
    _write_csv(root / RESULTS / "EXP01B_R1_STABILITY_RESULTS.csv", result.stability_rows)
    _write_csv(root / RESULTS / "EXP01B_R1_RANDOM_CONTROL_RESULTS.csv", result.random_rows)
    conversion_body = {**conversion, "reference_receipt_hash": reference_hash, "private_numeric_values_exposed": False}
    conversion_body["audit_hash"] = stable_hash_v1(conversion_body)
    _write_new(root / RECEIPTS / "GDN_UNIQUE_FORMAL_V4_CONVERSION_AUDIT_V1.json", conversion_body)
    disposition_body = {
        "schema": "paperworks.validation_v2.exp01b_r1_disposition_v1", "experiment_id": "EXP-01B-R1",
        "immutable_parent_disposition": old["disposition"], "corrected_disposition": result.disposition.value,
        "disposition_evidence": result.disposition_evidence.__dict__,
        "gdn_unique_confirmed_pairs": [list(pair) for pair in result.gdn_unique_confirmed_pairs],
        "signed_edgemask_counts": dict(result.signed_counts), "corrected_results_sha256": metric_hash,
        "parent_result_hash": old["result_hash"], "contract_hash": contract["contract_hash"],
        "execution_binding_hash": binding["binding_hash"], "retraining": False,
        "test1_accesses": 0, "label_accesses": 0, "test2_accesses": 0, "heldout_accesses": 0,
    }
    disposition_body["result_hash"] = stable_hash_v1(disposition_body)
    _write_new(root / RESULTS / "EXP01B_R1_DISPOSITION.json", disposition_body)
    comparison = (
        "# EXP-01B-R1 corrected comparison\n\n"
        f"- Frozen EXP-01B-V1 disposition: `{old['disposition']}` (unchanged)\n"
        f"- Corrected R1 disposition: `{result.disposition.value}`\n"
        "- Corrections: positive observed percentiles with tie equality, signed EdgeMask, whole-focal random controls, and true Formal V4 conversion.\n"
        f"- GDN-unique normal-confirmed pairs: {len(result.gdn_unique_confirmed_pairs)}\n"
        f"- Runtime-admissible GDN-unique pairs: {conversion['runtime_admissible_pairs']}\n"
        "- No retraining; test1/labels/test2/held-out accesses: 0.\n"
        "- R1 does not rewrite or supersede the original protocol-specific result.\n"
    )
    path = root / REPORTS / "EXP01B_R1_COMPARISON_TO_FROZEN_V1.md"; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(comparison, encoding="utf-8", newline="\n")
    if (root / "research_control_center/validation_v2/exp01b_gdn_xai/results/EXP01B_DISPOSITION.json").read_bytes() != old_bytes:
        raise R1ExecutionError("EXP01B_V1_RESULT_MUTATED")
    print(json.dumps({"status": "PASS", "corrected_disposition": result.disposition.value, "conversion": conversion, "test1_accesses": 0, "test2_accesses": 0}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path.cwd()); parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args(); execute(args.root.resolve(strict=True), args.private_root.resolve(strict=True))


if __name__ == "__main__":
    main()
