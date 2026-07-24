"""Persist bounded inner-only Review regression evidence privately."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from experiments.argos_reproduction.expanded_kpi_cohort import (
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.review_regression_samples import (
    RegressionSample,
    extract_regression_samples,
)


def freeze_regression_evidence(
    *,
    output_path: Path,
    values: Sequence[float],
    labels: Sequence[int],
    detector_predictions: Sequence[int],
    rule_predictions: Sequence[int],
    direction: str,
) -> tuple[tuple[RegressionSample, ...], str]:
    samples = extract_regression_samples(
        split="inner",
        values=values,
        labels=labels,
        detector_predictions=detector_predictions,
        rule_predictions=rule_predictions,
        direction=direction,
        maximum_samples=3,
        maximum_window_length=20,
    )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "split": "inner",
        "direction": direction,
        "window_count": len(samples),
        "windows": [sample.to_dict() for sample in samples],
    }
    payload["evidence_hash"] = sha256_json(payload)
    write_json(output_path, payload)
    return samples, str(payload["evidence_hash"])
