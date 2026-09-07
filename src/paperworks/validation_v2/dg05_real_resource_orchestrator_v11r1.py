"""V11R1 source-to-projection orchestration using frozen V5 components only."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .dg05_execution_closure_v1 import (
    PhysicalFileIdentityV2, build_expected_prediction_cell_census_v1,
    digest, file_sha256, project_attack_feature_file_v1,
)
from .dg05_metric_surface_v2 import persist_canonical_v1
from .multipanel_custody_v1 import (
    FROZEN_ATTACK_FILE_CENSUS_HASH_V2, FROZEN_AUTHORITY_SOURCE_COMMIT_V2,
    FrozenPhysicalFileAuthorityV2, frozen_feature_allowlist_authorities_v2,
)


class DG05V11R1RealResourceOrchestratorError(ValueError):
    pass


def prepare_frozen_v5_resources_v11r1(*, verified_plan: Mapping[str, Any],
                                      work_root: Path, adapter_implementation_hash: str,
                                      source_commit: str, dispatch: Any) -> dict[str, Any]:
    """Create only frozen physical/projection/timestamp authorities.

    The plan has already passed custody replay.  This function is deliberately
    the sole source-to-projection bridge and delegates each parse to
    ``project_attack_feature_file_v1``.
    """
    if work_root.exists():
        raise DG05V11R1RealResourceOrchestratorError("V11R1_OUTPUT_NAMESPACE_REUSE_REJECTED")
    work_root.mkdir(parents=True)
    allowlists = frozen_feature_allowlist_authorities_v2()
    rows=[]; sources={}
    for item in verified_plan["files"]:
        panel=str(item["panel_id"]); file_id=str(item["file_id"])
        if panel not in allowlists or (panel,file_id) in sources:
            raise DG05V11R1RealResourceOrchestratorError("V11R1_PLAN_IDENTITY_INVALID")
        source=Path(item["path"])
        # ``header_hash`` is the exact full custody header, while the frozen
        # positive allowlist below is the projection authority.  They are not
        # interchangeable: official attack files may carry non-feature
        # columns (for example Attack) which the frozen adapter excludes.
        # The adapter independently enforces the allowlist when it parses the
        # source, so this orchestration layer must preserve the custody hash.
        if type(item.get("header_hash")) is not str or len(item["header_hash"]) != 64:
            raise DG05V11R1RealResourceOrchestratorError("V11R1_CUSTODY_HEADER_HASH_REQUIRED")
        rows.append(PhysicalFileIdentityV2(panel,file_id,file_sha256(source),item["header_hash"],item["official_source_hash"]))
        sources[(panel,file_id)]=source
    physical=FrozenPhysicalFileAuthorityV2(tuple(rows),FROZEN_ATTACK_FILE_CENSUS_HASH_V2,verified_plan["physical_custody_hash"],FROZEN_AUTHORITY_SOURCE_COMMIT_V2)
    physical.validate()
    if len(physical.files)!=10: raise DG05V11R1RealResourceOrchestratorError("V11R1_PHYSICAL_CUSTODY_CENSUS_FAILED")
    persist_canonical_v1(work_root/"physical-authority.json",physical.document())
    projections={}; timestamps={}
    for item in physical.files:
        destination=work_root/"projections"/item.panel_id/f"{item.file_id}.jsonl"
        projection,timestamp=project_attack_feature_file_v1(source=sources[(item.panel_id,item.file_id)],destination=destination,physical_file=item,panel_authority=allowlists[item.panel_id],file_id=item.file_id,adapter_implementation_hash=adapter_implementation_hash,source_commit=source_commit)
        projections[(item.panel_id,item.file_id)]=(projection,destination); timestamps[(item.panel_id,item.file_id)]=timestamp
        persist_canonical_v1(work_root/"projection-authorities"/item.panel_id/f"{item.file_id}.json",projection.document())
        persist_canonical_v1(work_root/"timestamp-authorities"/item.panel_id/f"{item.file_id}.json",timestamp.document())
    census=build_expected_prediction_cell_census_v1(physical=physical,dispatch=dispatch)
    return {"physical":physical,"projections":projections,"timestamps":timestamps,"census":census,"projection_adapter":"project_attack_feature_file_v1"}
