"""V11R1 release gate; successor-only and non-scientific."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .dg05_production_chain_v11 import (
    PREACCESS_MODE, REAL_MODE, canonical_bytes, digest, file_hash,
    load_self_hashed, self_hashed,
)

PREDECESSOR_RELEASE = "a61688ce4f0c49e27e703298ff6a9b1ac4dbea18176041a3b81896b2b4a503ad"
PREDECESSOR_CLOSURE = "acb18572322a5e8918c8006d26a7eb795766e8248974c6d5302cd6b0bb2257fb"
PREDECESSOR_BINDING = "b1ff12619382bd3755b8d6f20cd1ed5cbfae42787a0a54d4b8c9b5a7281d4037"
V5_SHA256 = "ea16f4475de97a224af35627cada524bca1183285cda0ebeede26b54d1b42525"


class DG05ProductionChainV11R1Error(ValueError):
    pass


def build_manifest(*, repository_root: Path, source_commit: str,
                   implementation_paths: dict[str, Path]) -> dict[str, Any]:
    required = {"successor_gate", "unified_runner", "resource_loader", "v11_bridge", "v5_kernel"}
    if set(implementation_paths) != required:
        raise DG05ProductionChainV11R1Error("V11R1_IMPLEMENTATION_CENSUS_REQUIRED")
    roots = repository_root.resolve()
    rows=[]
    for name, path in sorted(implementation_paths.items()):
        resolved=path.resolve()
        if roots not in resolved.parents or not resolved.is_file() or resolved.is_symlink():
            raise DG05ProductionChainV11R1Error("V11R1_IMPLEMENTATION_PATH_INVALID")
        rows.append({"logical_name":name,"relative_path":resolved.relative_to(roots).as_posix(),"byte_hash":file_hash(resolved)})
    kernel=next(row for row in rows if row["logical_name"]=="v5_kernel")
    if kernel["byte_hash"] != V5_SHA256:
        raise DG05ProductionChainV11R1Error("FROZEN_V5_SCIENTIFIC_KERNEL_MUTATED")
    return self_hashed({"schema":"dg05_executable_v11r1_candidate_manifest_v1","designation":"DG05_EXECUTABLE_V11R1","status":"CANDIDATE_AWAITING_EXACT_USER_APPROVAL","approval_status":"NOT_APPROVED","implementation_source_commit":source_commit,"predecessor_release_hash":PREDECESSOR_RELEASE,"predecessor_closure_hash":PREDECESSOR_CLOSURE,"predecessor_execution_binding_hash":PREDECESSOR_BINDING,"predecessor_disposition":"APPROVED_NOT_EXECUTED_SUPERSEDED_FOR_REAL_ENTRYPOINT_COMPLETENESS","scenario_authority_hash":"2bd2bb4d4a6b8eacf5caaa44b36b5d41e06514e9521ac08789cfe5d268245e38","p1_authority_hash":"eda3cdc46e0fc044b38f6c1c3f1c45330b93d6a85d3e52a36381936fbb88a737","physical_custody_hash":"46b1319363731aeb050133b92aee0f5d37db0879cb6066ceaee70191cdd3fbaa","implementation_authorities":rows,"frozen_v5_kernel_hash":V5_SHA256,"same_runner_for_preaccess_and_real":True,"heldout_predictions_observed":0,"heldout_metrics_observed":0})


def initialize(*, manifest_path: Path, expected_hash: str, repository_root: Path,
               mode: str, user_approved_release_hash: str | None) -> dict[str, Any]:
    manifest=load_self_hashed(manifest_path,"dg05_executable_v11r1_candidate_manifest_v1")
    if manifest["self_hash"] != expected_hash:
        raise DG05ProductionChainV11R1Error("V11R1_RELEASE_HASH_MISMATCH")
    if (manifest.get("predecessor_release_hash"),manifest.get("predecessor_closure_hash"),manifest.get("predecessor_execution_binding_hash")) != (PREDECESSOR_RELEASE,PREDECESSOR_CLOSURE,PREDECESSOR_BINDING):
        raise DG05ProductionChainV11R1Error("V11R1_PREDECESSOR_BINDING_MISMATCH")
    root=repository_root.resolve()
    for row in manifest["implementation_authorities"]:
        path=(root/row["relative_path"]).resolve()
        if root not in path.parents or not path.is_file() or file_hash(path)!=row["byte_hash"]:
            raise DG05ProductionChainV11R1Error("V11R1_IMPLEMENTATION_BYTE_REPLAY_FAILED")
    if mode == PREACCESS_MODE:
        authorized=False
    elif mode == REAL_MODE:
        if user_approved_release_hash != manifest["self_hash"]:
            raise DG05ProductionChainV11R1Error("EXACT_V11R1_USER_APPROVAL_REQUIRED")
        authorized=True
    else:
        raise DG05ProductionChainV11R1Error("V11R1_MODE_REQUIRED")
    return self_hashed({"schema":"dg05_v11r1_initialized_state_v1","mode":mode,"release_hash":manifest["self_hash"],"protected_access_authorized":authorized,"compatibility_authority":"OUTER_V11R1_APPROVAL_IS_SOLE_ACCESS_AUTHORITY","heldout_predictions":0,"heldout_metrics":0})
