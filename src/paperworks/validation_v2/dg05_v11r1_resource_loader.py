"""Resource-plan validation for the V11R1 unified entrypoint.

The real branch validates the plan and every payload hash before a caller may
open a feature container.  This module deliberately performs no CSV parsing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import file_hash, load_self_hashed, self_hashed
from .dg05_v11r1_resource_materializer import load_exact_custody_receipt_v11r1


class DG05V11R1ResourceError(ValueError):
    pass


def verify_plan(*, custody_receipt_path: Path, plan_path: Path | None = None,
                plan_document: Mapping[str, Any] | None = None) -> dict[str, Any]:
    # The historical recovery receipt is immutable/self-hashed but was not
    # published in canonical one-line serialization; replay its documented
    # byte-independent hash contract rather than requiring a packaging format.
    receipt=load_exact_custody_receipt_v11r1(custody_receipt_path)
    if (plan_path is None) == (plan_document is None):
        raise DG05V11R1ResourceError("V11R1_EXACTLY_ONE_RUNTIME_PLAN_REQUIRED")
    plan=load_self_hashed(plan_path,"dg05_v11r1_protected_resource_plan_v1") if plan_path is not None else dict(plan_document or {})
    if plan_document is not None:
        body={key:item for key,item in plan.items() if key!="self_hash"}
        if plan.get("schema")!="dg05_v11r1_protected_resource_plan_v1" or plan.get("self_hash")!=self_hashed(body)["self_hash"]:
            raise DG05V11R1ResourceError("V11R1_PRIVATE_RUNTIME_PLAN_REPLAY_FAILED")
    if plan.get("physical_custody_hash") != receipt["self_hash"] or len(plan.get("files",[])) != 10:
        raise DG05V11R1ResourceError("V11R1_PHYSICAL_CUSTODY_PLAN_MISMATCH")
    expected={(row["panel_id"],row["file_id"],row["actual_sha256"]) for row in receipt["files"]}
    observed=set()
    for row in plan["files"]:
        path=Path(row["path"])
        key=(row.get("panel_id"),row.get("file_id"),row.get("sha256"))
        if key not in expected or path.is_symlink() or not path.is_file() or file_hash(path) != row["sha256"]:
            raise DG05V11R1ResourceError("V11R1_PHYSICAL_PAYLOAD_REPLAY_FAILED")
        observed.add(key)
    if observed != expected:
        raise DG05V11R1ResourceError("V11R1_PHYSICAL_CUSTODY_CENSUS_FAILED")
    return self_hashed({"schema":"dg05_v11r1_resource_preflight_v1","status":"PASS","physical_custody_hash":receipt["self_hash"],"file_count":10,"csv_parser_invocations":0,"feature_rows_opened":0,"feature_values_inspected":0})
