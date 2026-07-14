"""Execution-independent prediction and fusion diagnostics for ARGOS audits."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


COMPOSITIONS = (
    "rule_only",
    "detector_only",
    "combined_fn_max",
    "combined_fp_min",
)


class PredictionValidationError(ValueError):
    """Raised when supplied prediction labels violate the frozen protocol."""


@dataclass(frozen=True)
class ConfusionCounts:
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int


@dataclass(frozen=True)
class PointMetrics:
    precision: float
    recall: float
    point_f1: float


def sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_binary_labels(name: str, values: Iterable[object]) -> tuple[int, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise PredictionValidationError(f"{name} must be a one-dimensional label array")

    try:
        items = list(values)
    except TypeError as exc:
        raise PredictionValidationError(f"{name} must be iterable") from exc

    normalized: list[int] = []
    for index, value in enumerate(items):
        if isinstance(value, (list, tuple, dict, set)):
            raise PredictionValidationError(
                f"{name}[{index}] is nested; only one-dimensional labels are allowed"
            )
        try:
            integer = int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise PredictionValidationError(
                f"{name}[{index}] is not a binary label"
            ) from exc
        if integer not in (0, 1) or value != integer:
            raise PredictionValidationError(
                f"{name}[{index}] must be exactly 0 or 1"
            )
        normalized.append(integer)
    return tuple(normalized)


def _require_same_length(
    reference_name: str,
    reference: Sequence[int],
    candidate_name: str,
    candidate: Sequence[int],
) -> None:
    if len(reference) != len(candidate):
        raise PredictionValidationError(
            f"{candidate_name} length {len(candidate)} does not match "
            f"{reference_name} length {len(reference)}"
        )


def compose_prediction_labels(
    composition: str,
    *,
    rule_prediction_labels: Iterable[object] | None = None,
    detector_prediction_labels: Iterable[object] | None = None,
) -> tuple[int, ...]:
    if composition not in COMPOSITIONS:
        raise PredictionValidationError(f"unsupported composition: {composition}")

    rule = (
        validate_binary_labels("rule_prediction_labels", rule_prediction_labels)
        if rule_prediction_labels is not None
        else None
    )
    detector = (
        validate_binary_labels(
            "detector_prediction_labels", detector_prediction_labels
        )
        if detector_prediction_labels is not None
        else None
    )

    if composition == "rule_only":
        if rule is None:
            raise PredictionValidationError("rule_only requires rule predictions")
        return rule
    if composition == "detector_only":
        if detector is None:
            raise PredictionValidationError(
                "detector_only requires detector predictions"
            )
        return detector

    if rule is None or detector is None:
        raise PredictionValidationError(
            f"{composition} requires both rule and detector predictions"
        )
    _require_same_length(
        "rule_prediction_labels", rule, "detector_prediction_labels", detector
    )

    if composition == "combined_fn_max":
        return tuple(max(detector_value, rule_value) for detector_value, rule_value in zip(detector, rule))
    return tuple(min(detector_value, rule_value) for detector_value, rule_value in zip(detector, rule))


def calculate_confusion_counts(
    ground_truth_labels: Iterable[object], prediction_labels: Iterable[object]
) -> ConfusionCounts:
    ground_truth = validate_binary_labels("ground_truth_labels", ground_truth_labels)
    predictions = validate_binary_labels("prediction_labels", prediction_labels)
    _require_same_length(
        "ground_truth_labels", ground_truth, "prediction_labels", predictions
    )

    true_positive = sum(gt == 1 and pred == 1 for gt, pred in zip(ground_truth, predictions))
    false_positive = sum(gt == 0 and pred == 1 for gt, pred in zip(ground_truth, predictions))
    true_negative = sum(gt == 0 and pred == 0 for gt, pred in zip(ground_truth, predictions))
    false_negative = sum(gt == 1 and pred == 0 for gt, pred in zip(ground_truth, predictions))
    return ConfusionCounts(
        true_positive=true_positive,
        false_positive=false_positive,
        true_negative=true_negative,
        false_negative=false_negative,
    )


def calculate_point_metrics(counts: ConfusionCounts) -> PointMetrics:
    precision_denominator = counts.true_positive + counts.false_positive
    recall_denominator = counts.true_positive + counts.false_negative
    precision = (
        counts.true_positive / precision_denominator
        if precision_denominator
        else 0.0
    )
    recall = (
        counts.true_positive / recall_denominator if recall_denominator else 0.0
    )
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return PointMetrics(precision=precision, recall=recall, point_f1=f1)


def evaluate_prediction_arrays(
    *,
    ground_truth_labels: Iterable[object],
    rule_prediction_labels: Iterable[object] | None,
    detector_prediction_labels: Iterable[object] | None,
    compositions: Sequence[str] = COMPOSITIONS,
) -> dict[str, object]:
    ground_truth = validate_binary_labels("ground_truth_labels", ground_truth_labels)
    if not ground_truth:
        raise PredictionValidationError("ground_truth_labels must not be empty")

    rule = (
        validate_binary_labels("rule_prediction_labels", rule_prediction_labels)
        if rule_prediction_labels is not None
        else None
    )
    detector = (
        validate_binary_labels(
            "detector_prediction_labels", detector_prediction_labels
        )
        if detector_prediction_labels is not None
        else None
    )
    if rule is not None:
        _require_same_length(
            "ground_truth_labels", ground_truth, "rule_prediction_labels", rule
        )
    if detector is not None:
        _require_same_length(
            "ground_truth_labels",
            ground_truth,
            "detector_prediction_labels",
            detector,
        )

    results: dict[str, object] = {}
    for composition in compositions:
        prediction = compose_prediction_labels(
            composition,
            rule_prediction_labels=rule,
            detector_prediction_labels=detector,
        )
        counts = calculate_confusion_counts(ground_truth, prediction)
        metrics = calculate_point_metrics(counts)
        results[composition] = {
            "prediction_count": len(prediction),
            "prediction_hash": sha256_json(prediction),
            "confusion_counts": asdict(counts),
            "metrics": asdict(metrics),
        }

    return {
        "input_count": len(ground_truth),
        "ground_truth_hash": sha256_json(ground_truth),
        "rule_prediction_hash": sha256_json(rule) if rule is not None else None,
        "detector_prediction_hash": (
            sha256_json(detector) if detector is not None else None
        ),
        "compositions": results,
    }


def run_protocol(
    config_path: Path, output_override: Path | None = None
) -> Mapping[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    fixture = config["synthetic_fixture"]
    evaluation = evaluate_prediction_arrays(
        ground_truth_labels=fixture["ground_truth_labels"],
        rule_prediction_labels=fixture["rule_prediction_labels"],
        detector_prediction_labels=fixture["detector_prediction_labels"],
        compositions=config["compositions"],
    )
    report: dict[str, object] = {
        "schema_version": "1.0",
        "artifact_type": "task029_evaluation_harness_report",
        "task_id": "TASK-029",
        "created_at": config["report_created_at"],
        "protocol_id": config["protocol_id"],
        "config_hash": sha256_json(config),
        "harness_sha256": sha256_file(Path(__file__)),
        "fixture": {
            "fixture_id": fixture["fixture_id"],
            "fixture_kind": "synthetic_non_kpi_non_swat",
            "label_count": evaluation["input_count"],
        },
        "evaluation": evaluation,
        "metrics": {
            "pa_free_point_metrics": True,
            "paper_faithful_pa_metrics_implemented": False,
        },
        "boundaries": {
            "generated_code_loaded": False,
            "generated_code_executed": False,
            "captured_rule_accessed": False,
            "provider_called": False,
            "detector_executed": False,
            "kpi_accessed": False,
            "swat_accessed": False,
            "benchmark_claim": False,
        },
    }
    report["report_hash"] = sha256_json(report)

    output_path = output_override or Path(config["output_report"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    report = run_protocol(args.config)
    print(
        json.dumps(
            {
                "task_id": report["task_id"],
                "fixture_kind": report["fixture"]["fixture_kind"],
                "generated_code_executed": report["boundaries"][
                    "generated_code_executed"
                ],
                "report_hash": report["report_hash"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
