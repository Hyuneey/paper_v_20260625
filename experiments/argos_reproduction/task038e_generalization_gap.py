"""Inner-to-outer branch generalization gap calculations."""

from __future__ import annotations

from typing import Any, Mapping


def generalization_record(
    *,
    branch: str,
    variant: str,
    arm: str,
    inner_f1: float,
    outer_f1: float,
    a0_inner_f1: float,
    a0_outer_f1: float,
) -> dict[str, Any]:
    inner_delta = inner_f1 - a0_inner_f1
    outer_delta = outer_f1 - a0_outer_f1
    return {
        "branch_id": branch,
        "detector_variant": variant,
        "arm": arm,
        "inner_macro_point_F1": inner_f1,
        "outer_macro_point_F1": outer_f1,
        "generalization_gap": inner_f1 - outer_f1,
        "inner_delta_vs_A0": inner_delta,
        "outer_delta_vs_A0": outer_delta,
        "transfer_gap": inner_delta - outer_delta,
    }
