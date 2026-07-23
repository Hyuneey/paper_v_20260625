"""Replay only committed TASK-037E selected rules on values-only outer windows."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.error_rule_full_inner_runtime import (
    rule_path,
    split_values_path,
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    git_clean_commit,
    read_json,
    sha256_file,
)
from experiments.argos_reproduction.multi_rule_full_window_runtime import (
    deterministic_replay_matches,
    execute_full_window_rule,
)
from experiments.argos_reproduction.multi_rule_runtime import (
    inspect_image,
    isolation_probe,
)


class SelectedRuleOuterRuntimeError(RuntimeError):
    """Raised when committed selection or selected-rule replay fails closed."""


def _committed_file_matches(path: Path) -> bool:
    relative = path.resolve().relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout == path.read_bytes()


def verify_committed_selection(
    config: Mapping[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    commit = git_clean_commit()
    records: list[dict[str, Any]] = []
    for key, direction in (("fn_selection", "FN"), ("fp_selection", "FP")):
        path = ROOT / config["reports"][key]
        report = verify_hashed_report(path)
        if (
            not _committed_file_matches(path)
            or report["status"] != "selection_frozen_before_outer_access"
            or report["direction"] != direction
            or report["selection_unit_count"] != 20
        ):
            raise SelectedRuleOuterRuntimeError("TASK037E_SELECTION_NOT_COMMITTED")
        records.extend(report["records"])
    if len(records) != 40:
        raise SelectedRuleOuterRuntimeError("TASK037E_SELECTION_UNIT_COUNT_MISMATCH")
    return commit, records


def _outer_output_directory(
    config: Mapping[str, Any], slot_id: str, replay: int
) -> Path:
    return (
        ROOT
        / config["private_roots"]["task037e"]
        / "outer"
        / "rule_predictions"
        / slot_id
        / f"replay_{replay}"
    )


def outer_rule_prediction_path(
    config: Mapping[str, Any], slot_id: str
) -> Path:
    return _outer_output_directory(config, slot_id, 1) / "output_labels.npy"


def run_selected_outer_replay(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    selection_commit, selected = verify_committed_selection(config)
    registry = verify_hashed_report(ROOT / config["candidate_registry"])
    registry_by_hash = {
        item["rule_sha256"]: item for item in registry["records"]
    }
    image = inspect_image(config)
    if (
        image["image_id"] != config["image"]["expected_image_id"]
        or image["image_digest"] != config["image"]["expected_image_digest"]
    ):
        raise SelectedRuleOuterRuntimeError("TASK037E_RUNTIME_IMAGE_MISMATCH")
    probe = isolation_probe(config, image["image_id"])
    if probe["status"] != "passed":
        raise SelectedRuleOuterRuntimeError("TASK037E_ISOLATION_PROBE_FAILED")
    records: list[dict[str, Any]] = []
    for selection in selected:
        base = {
            key: selection[key]
            for key in ("detector_variant", "kpi_id", "direction", "selected_candidate_type")
        }
        if selection["selected_candidate_type"] == "no_op":
            records.append(
                {
                    **base,
                    "selected_rule_hash": None,
                    "selected_slot_id": None,
                    "terminal_status": "no_op",
                    "runtime_attempted": False,
                    "deterministic_replay_passed": True,
                }
            )
            continue
        rule_hash = selection["selected_rule_hash"]
        candidate = registry_by_hash.get(rule_hash)
        if (
            not candidate
            or candidate["slot_id"] != selection["selected_slot_id"]
            or candidate["detector_variant"] != selection["detector_variant"]
            or candidate["kpi_id"] != selection["kpi_id"]
            or candidate["direction"] != selection["direction"]
        ):
            raise SelectedRuleOuterRuntimeError("TASK037E_SELECTED_RULE_LINEAGE_MISMATCH")
        rule = rule_path(config, candidate)
        if sha256_file(rule) != rule_hash:
            raise SelectedRuleOuterRuntimeError("TASK037E_SELECTED_RULE_HASH_MISMATCH")
        values = split_values_path(config, candidate["kpi_id"], "outer")
        first = execute_full_window_rule(
            config,
            image,
            run_id=f"task037e:outer:{candidate['slot_id']}:1",
            rule_path=rule,
            rule_sha256=rule_hash,
            values_path=values,
            output_directory=_outer_output_directory(config, candidate["slot_id"], 1),
        )
        second = execute_full_window_rule(
            config,
            image,
            run_id=f"task037e:outer:{candidate['slot_id']}:2",
            rule_path=rule,
            rule_sha256=rule_hash,
            values_path=values,
            output_directory=_outer_output_directory(config, candidate["slot_id"], 2),
        )
        replay = (
            first["runtime_status"] == "executable_rule"
            and second["runtime_status"] == "executable_rule"
            and deterministic_replay_matches(first, second)
        )
        records.append(
            {
                **base,
                "selected_rule_hash": rule_hash,
                "selected_slot_id": candidate["slot_id"],
                "terminal_status": (
                    "selected_rule_outer_executable"
                    if replay
                    else "selected_rule_outer_runtime_failure"
                ),
                "runtime_attempted": True,
                "outer_input_hash": first.get("input_sha256"),
                "outer_prediction_hash": first.get("prediction_sha256") if replay else None,
                "prediction_length": first.get("output_count"),
                "predicted_positive_count": first.get("predicted_positive_count"),
                "deterministic_replay_passed": replay,
                "replay_1_status": first.get("runtime_status"),
                "replay_2_status": second.get("runtime_status"),
                "labels_mounted": False,
            }
        )
    counts = Counter(item["terminal_status"] for item in records)
    failed = counts.get("selected_rule_outer_runtime_failure", 0)
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "selected_rule_outer_runtime_report",
        "status": (
            "selected_outer_predictions_frozen"
            if failed == 0
            else "selected_rule_outer_runtime_failure"
        ),
        "selection_commit": selection_commit,
        "selection_unit_count": len(records),
        "selected_non_noop_count": sum(item["runtime_attempted"] for item in records),
        "terminal_status_counts": dict(sorted(counts.items())),
        "records": records,
        "image": image,
        "isolation": probe,
        "outer_labels_loaded_during_runtime": False,
        "selected_rule_substitution_performed": False,
        "test_accessed": False,
        "provider_calls": 0,
        "agent_calls": 0,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    return write_hashed_report(ROOT / config["reports"]["outer_runtime"], report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037e_error_conditioned_aggregator.json",
    )
    args = parser.parse_args()
    report = run_selected_outer_replay((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "selected_non_noop": report["selected_non_noop_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "selected_outer_predictions_frozen" else 2


if __name__ == "__main__":
    raise SystemExit(main())
