from __future__ import annotations

import json
from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


ROOT = Path(__file__).resolve().parents[1]
EXPOSURE = (
    "The TASK-037E outer partition is a previously exposed follow-up validation "
    "partition. Rule generation used only the generation partition and rule "
    "selection used only the inner partition, but the broader experiment design "
    "followed prior inspection of outer results. Therefore TASK-037E does not "
    "support an untouched confirmatory superiority claim."
)


def _verify(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = payload.pop("report_hash")
    assert expected == sha256_json(payload)
    return payload


def test_commit_a_config_and_candidate_report_are_safe() -> None:
    config = json.loads(
        (
            ROOT
            / "configs/argos_reproduction/task037e_error_conditioned_aggregator.json"
        ).read_text(encoding="utf-8")
    )
    assert config["expected_executable_rule_count"] == 83
    assert config["detector_variants"] == ["LSTMADalpha", "LSTMADbeta"]
    assert config["selection_policy"]["no_op_candidate_required"] is True
    assert config["selection_policy"]["joint_pair_search"] is False
    assert config["aggregator_policy"]["order"] == [
        "fp_correction",
        "fn_compensation",
    ]
    assert config["outer_exposure_limitation"] == EXPOSURE
    registry = _verify(
        ROOT / "docs/task_reports/TASK-037E_CANDIDATE_REGISTRY.json"
    )
    assert len(registry["records"]) == 83
    serialized = json.dumps(registry)
    assert "source_values" not in serialized
    assert "target_values" not in serialized
    assert "C:\\\\Users" not in serialized


def test_result_reports_are_hash_valid_when_present() -> None:
    config = json.loads(
        (
            ROOT
            / "configs/argos_reproduction/task037e_error_conditioned_aggregator.json"
        ).read_text(encoding="utf-8")
    )
    for relative in config["reports"].values():
        path = ROOT / relative
        if path.suffix == ".json" and path.exists():
            payload = _verify(path)
            assert payload["test_accessed"] is False
            assert payload["outer_exposure_limitation"] == EXPOSURE


def test_new_modules_have_no_provider_agent_or_test_loader_surface() -> None:
    paths = [
        ROOT / "experiments/argos_reproduction/error_rule_full_inner_runtime.py",
        ROOT / "experiments/argos_reproduction/directional_rule_selection.py",
        ROOT / "experiments/argos_reproduction/selected_rule_outer_runtime.py",
        ROOT / "experiments/argos_reproduction/aggregator_outer_validation.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "openai" not in combined.lower()
    assert "provider_client" not in combined
    assert "RepairAgent" not in combined
    assert "ReviewAgent" not in combined
    assert "TestLabels" not in combined
