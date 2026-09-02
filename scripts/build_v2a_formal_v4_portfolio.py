#!/usr/bin/env python3
"""Materialize the selected V2A numeric policy as a Formal V4 portfolio.

This phase consumes only the already-frozen private EXP-02 numeric authority;
it does not reopen HAI data or any evaluation split.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

from paperworks.validation_v2.formal_v4_authority_v1 import (
    FormalV4ArtifactBindingV1,
    FormalV4EvaluatorContractV1,
    FormalV4ExecutionContextV1,
    FormalV4RuleDescriptorV1,
    NumericReferenceBindingV1,
    authorize_formal_v4_runtime_v1,
    build_formal_v4_portfolio_authority_v1,
    canonical_document_hash_v1,
)
from paperworks.validation_v2.runtime_policy_v1 import (
    FORMAL_V4_RESPONSE_POLICY_HASH,
    FORMAL_V4_TRACE_CONTRACT_HASH,
    FORMAL_V4_TRIGGER_POLICY_HASH,
)


PUBLIC = Path("research_control_center/validation_v2/core_v2a")
PRIVATE = Path("artifacts/validation_v2/core_v2a/private")


def _canonical(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def _write_new(path: Path, value: Mapping[str, Any], *, private: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(value)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if private else 0o644)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    if path.read_bytes() != payload:
        raise RuntimeError("V2A_PORTFOLIO_REOPEN_MISMATCH")
    return sha256(payload).hexdigest()


def _binding(root: Path, artifact_id: str, relative: Path) -> FormalV4ArtifactBindingV1:
    posix = relative.as_posix()
    return FormalV4ArtifactBindingV1(artifact_id, posix, sha256((root / relative).read_bytes()).hexdigest())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repository_root.resolve(strict=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    selected_path = root / PRIVATE / "EXP02_SELECTED_NUMERIC_AUTHORITY_V2A.private.json"
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    if selected.get("artifact_type") != "validation_v2a_private_formal_v4_numeric_authority_v1":
        raise RuntimeError("V2A_PRIVATE_NUMERIC_AUTHORITY_INVALID")

    numeric_rows = []
    relation_rows = []
    descriptor_inputs = []
    for item in selected["relations"]:
        relation = item["relation"]
        roles = tuple((str(role), float(value)) for role, value in item["roles"])
        references = []
        for index, (role, value) in enumerate(roles):
            reference_id = f"V2A-NUM-{relation['relation_id']}-{index:02d}"
            payload = {"numeric_role": role, "reference_id": reference_id, "relation_id": relation["relation_id"], "value": value}
            reference_hash = canonical_document_hash_v1(payload)
            numeric_rows.append({**payload, "reference_hash": reference_hash})
            references.append(NumericReferenceBindingV1(role, reference_id, reference_hash))
        semantic_hash = canonical_document_hash_v1({
            "relation_id": relation["relation_id"],
            "relation_binding_hash": relation["relation_binding_hash"],
            "source_direction": relation["source_direction"],
            "target_direction": relation["target_direction"],
            "selected_horizon_seconds": relation["selected_horizon_seconds"],
            "trigger_policy_hash": FORMAL_V4_TRIGGER_POLICY_HASH,
            "response_policy_hash": FORMAL_V4_RESPONSE_POLICY_HASH,
        })
        relation_row = {
            "relation_id": relation["relation_id"],
            "relation_binding_hash": relation["relation_binding_hash"],
            "semantic_execution_hash": semantic_hash,
            "source": relation["source"], "target": relation["target"],
            "source_direction": relation["source_direction"],
            "target_direction": relation["target_direction"],
            "selected_horizon_seconds": relation["selected_horizon_seconds"],
        }
        relation_rows.append(relation_row)
        descriptor_inputs.append((relation_row, tuple(references)))

    numeric_relative = PRIVATE / "FORMAL_V4_NUMERIC_AUTHORITY_V2A.private.json"
    _write_new(root / numeric_relative, {
        "artifact_type": "validation_v2_formal_v4_numeric_authority_v1",
        "bindings": numeric_rows, "schema_version": "1.0.0",
    }, private=True)
    relation_relative = PUBLIC / "authorities/FORMAL_V4_RELATION_AUTHORITY_V2A.json"
    _write_new(root / relation_relative, {
        "artifact_type": "validation_v2_formal_v4_relation_authority_v1",
        "relations": relation_rows, "schema_version": "1.0.0",
    })
    contract_documents = {
        "FEATURE_CONTRACT_V2A.json": {"artifact_type": "validation_v2a_feature_contract", "feature_scope": "P1_37_ORDER_FROZEN", "labels": False},
        "FILE_CONTRACT_V2A.json": {"artifact_type": "validation_v2a_file_contract", "development_split": "test1", "heldout_authorized": False},
        "SAMPLING_CONTRACT_V2A.json": {"artifact_type": "validation_v2a_sampling_contract", "sampling": "FILE_LOCAL_STRICT_ONE_SECOND"},
        "RUNTIME_CONFIG_V2A.json": {"artifact_type": "validation_v2a_runtime_config", "authority": "FORMAL_V4", "llm_free": True, "deterministic": True},
    }
    for filename, document in contract_documents.items():
        _write_new(root / PUBLIC / "contracts" / filename, document)

    numeric_binding = _binding(root, "V2A-NUMERIC-AUTHORITY", numeric_relative)
    relation_binding = _binding(root, "V2A-RELATION-AUTHORITY", relation_relative)
    feature_binding = _binding(root, "V2A-FEATURE-CONTRACT", PUBLIC / "contracts/FEATURE_CONTRACT_V2A.json")
    file_binding = _binding(root, "V2A-FILE-CONTRACT", PUBLIC / "contracts/FILE_CONTRACT_V2A.json")
    sampling_binding = _binding(root, "V2A-SAMPLING-CONTRACT", PUBLIC / "contracts/SAMPLING_CONTRACT_V2A.json")
    runtime_config_binding = _binding(root, "V2A-RUNTIME-CONFIG", PUBLIC / "contracts/RUNTIME_CONFIG_V2A.json")
    runtime_relative = Path("src/paperworks/validation_v2/runtime_v1.py")
    runtime_binding = _binding(root, "V2A-RUNTIME-IMPLEMENTATION", runtime_relative)
    evaluator = FormalV4EvaluatorContractV1(
        evaluator_id="V2A-FORMAL-V4-EVALUATOR-V1",
        implementation_path=runtime_relative.as_posix(),
        implementation_hash=runtime_binding.content_sha256,
        trigger_policy_hash=FORMAL_V4_TRIGGER_POLICY_HASH,
        response_policy_hash=FORMAL_V4_RESPONSE_POLICY_HASH,
        trace_contract_hash=FORMAL_V4_TRACE_CONTRACT_HASH,
        deterministic=True, llm_free=True,
    )
    descriptors = tuple(FormalV4RuleDescriptorV1(
        relation_id=row["relation_id"], relation_binding_hash=row["relation_binding_hash"],
        semantic_execution_hash=row["semantic_execution_hash"], source=row["source"], target=row["target"],
        source_direction=row["source_direction"], target_direction=row["target_direction"],
        selected_horizon_seconds=row["selected_horizon_seconds"], numeric_reference_bindings=refs,
        numeric_authority_hash=numeric_binding.content_sha256,
    ) for row, refs in descriptor_inputs)
    authority = build_formal_v4_portfolio_authority_v1(
        method_id="VALIDATION-V2A-VERIFIED-RELATIONAL-RULE-ONLY",
        config_id="EXP02-SELECTED-POLICY-V2A", experiment_id="EXP-04-V2A",
        portfolio_id="VALIDATION_V2A_RELATIONAL_RULE_PORTFOLIO", source_commit=commit,
        descriptors=descriptors, relation_authority_binding=relation_binding,
        numeric_authority_binding=numeric_binding, feature_contract_binding=feature_binding,
        file_contract_binding=file_binding, sampling_contract_binding=sampling_binding,
        evaluator=evaluator, repository_root=root,
    )
    context = FormalV4ExecutionContextV1(
        source_commit=commit, runtime_config_binding=runtime_config_binding,
        relation_authority_binding=relation_binding, numeric_authority_binding=numeric_binding,
        feature_contract_binding=feature_binding, file_contract_binding=file_binding,
        sampling_contract_binding=sampling_binding, evaluator_implementation_binding=runtime_binding,
    )
    authorized = authorize_formal_v4_runtime_v1(
        authority, evaluator, expected_source_commit=commit, execution_context=context,
        repository_root=root, split_role="DEVELOPMENT_TEST1",
    )
    _write_new(root / PUBLIC / "authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json", authority.to_dict())
    _write_new(root / PUBLIC / "authorities/V2A_FORMAL_V4_RUNTIME_AUTHORIZATION.json", authorized.receipt.to_dict())
    _write_new(root / PUBLIC / "authorities/V2A_PORTFOLIO_MANIFEST.json", {
        "artifact_type": "V2A_PORTFOLIO_MANIFEST",
        "portfolio_id": authority.portfolio_id,
        "relation_count": len(descriptors), "rule_count": len(descriptors),
        "excluded_no_rule_count": 0,
        "candidate_discovery": "META_PLUS_STAT",
        "numeric_policy": selected["candidate"]["candidate_id"],
        "authority_family": "FORMAL_V4",
        "portfolio_hash": authority.authority_hash,
        "runtime_authorization_hash": authorized.receipt.authorization_hash,
        "source_commit": commit, "test1_accesses": 0, "test2_accesses": 0,
        "label_accesses": 0, "heldout_accesses": 0,
    })


if __name__ == "__main__":
    main()
