"""Resource-plan validation for the V11R1 unified entrypoint.

The real branch validates the plan and every payload hash before a caller may
open a feature container.  This module deliberately performs no CSV parsing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .dg05_production_chain_v11 import file_hash, load_self_hashed, self_hashed


class DG05V11R1ResourceError(ValueError):
    pass


def verify_plan(*, plan_path: Path, custody_receipt_path: Path) -> dict[str, Any]:
    receipt=load_self_hashed(custody_receipt_path,"hai22_kaggle_exact_payload_recovery_receipt_v1")
    plan=load_self_hashed(plan_path,"dg05_v11r1_protected_resource_plan_v1")
    if plan.get("physical_custody_hash") != receipt["self_hash"] or len(plan.get("files",[])) != 10:
        raise DG05V11R1ResourceError("V11R1_PHYSICAL_CUSTODY_PLAN_MISMATCH")
    expected={(row["panel_id"],row["file_id"],row["actual_sha256"]) for row in receipt["files"]}
    observed=set()
    for row in plan["files"]:
        path=Path(row["path"])
        key=(row.get("panel_id"),row.get("file_id"),row.get("sha256"))
        if key not in expected or not path.is_file() or file_hash(path) != row["sha256"]:
            raise DG05V11R1ResourceError("V11R1_PHYSICAL_PAYLOAD_REPLAY_FAILED")
        observed.add(key)
    if observed != expected:
        raise DG05V11R1ResourceError("V11R1_PHYSICAL_CUSTODY_CENSUS_FAILED")
    return self_hashed({"schema":"dg05_v11r1_resource_preflight_v1","status":"PASS","physical_custody_hash":receipt["self_hash"],"file_count":10,"csv_parser_invocations":0,"feature_rows_opened":0,"feature_values_inspected":0})
