"""Exact deserialization/replay of immutable V2A, not a new portfolio producer."""
from __future__ import annotations
from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path

from .formal_v4_authority_v1 import (
    FormalV4ArtifactBindingV1, FormalV4RuleDescriptorV1, NumericReferenceBindingV1,
    FormalV4PortfolioAuthorityV1, FormalV4EvaluatorContractV1, FormalV4ExecutionContextV1,
    authorize_formal_v4_runtime_v1,
)
from .runtime_policy_v1 import FORMAL_V4_TRIGGER_POLICY_HASH, FORMAL_V4_RESPONSE_POLICY_HASH, FORMAL_V4_TRACE_CONTRACT_HASH


def load_v2a_runtime_v1(root: Path):
    public = Path("research_control_center/validation_v2/core_v2a")
    doc = json.loads((root/public/"authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json").read_text())
    descriptors = []
    for row in doc["descriptors"]:
        kwargs = {f.name: row[f.name] for f in fields(FormalV4RuleDescriptorV1)}
        kwargs["numeric_reference_bindings"] = tuple(NumericReferenceBindingV1(**r) for r in kwargs["numeric_reference_bindings"])
        descriptor = FormalV4RuleDescriptorV1(**kwargs)
        if descriptor.to_dict() != row:
            raise ValueError("FROZEN_DESCRIPTOR_REPLAY_MISMATCH")
        descriptors.append(descriptor)
    kwargs = {f.name: doc[f.name] for f in fields(FormalV4PortfolioAuthorityV1)}
    kwargs["descriptors"] = tuple(descriptors)
    kwargs["allowed_split_roles"] = tuple(kwargs["allowed_split_roles"])
    for key in tuple(kwargs):
        if key.endswith("_binding"):
            kwargs[key] = FormalV4ArtifactBindingV1(**kwargs[key])
    authority = FormalV4PortfolioAuthorityV1(**kwargs)
    if authority.to_dict() != doc:
        raise ValueError("FROZEN_PORTFOLIO_REPLAY_MISMATCH")
    def binding(artifact_id, relative):
        return FormalV4ArtifactBindingV1(artifact_id, str(relative).replace("\\", "/"), sha256((root/relative).read_bytes()).hexdigest())
    runtime = binding("V2A-RUNTIME-IMPLEMENTATION", Path("src/paperworks/validation_v2/runtime_v1.py"))
    evaluator = FormalV4EvaluatorContractV1(evaluator_id="V2A-FORMAL-V4-EVALUATOR-V1", implementation_path=runtime.relative_path,
        implementation_hash=runtime.content_sha256, trigger_policy_hash=FORMAL_V4_TRIGGER_POLICY_HASH,
        response_policy_hash=FORMAL_V4_RESPONSE_POLICY_HASH, trace_contract_hash=FORMAL_V4_TRACE_CONTRACT_HASH,
        deterministic=True, llm_free=True)
    context = FormalV4ExecutionContextV1(source_commit=authority.source_commit,
        runtime_config_binding=binding("V2A-RUNTIME-CONFIG",public/"contracts/RUNTIME_CONFIG_V2A.json"),
        evaluator_implementation_binding=runtime,
        **{key:getattr(authority,key) for key in ("relation_authority_binding","numeric_authority_binding","feature_contract_binding","file_contract_binding","sampling_contract_binding")})
    bundle = authorize_formal_v4_runtime_v1(authority,evaluator,expected_source_commit=authority.source_commit,
        execution_context=context, repository_root=root, split_role="DEVELOPMENT_TEST1")
    old_receipt = json.loads((root/public/"authorities/V2A_FORMAL_V4_RUNTIME_AUTHORIZATION.json").read_text())
    if bundle.receipt.to_dict() != old_receipt:
        raise ValueError("FROZEN_RUNTIME_AUTHORIZATION_REPLAY_MISMATCH")
    return bundle, context
