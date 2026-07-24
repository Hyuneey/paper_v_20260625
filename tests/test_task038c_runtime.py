from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def test_review_runtime_uses_generation_and_inner_two_run_containers() -> None:
    source = (
        ROOT / "experiments/argos_reproduction/reviewed_rule_runtime.py"
    ).read_text(encoding="utf-8")
    assert 'for fixture in ("target", "contrast")' in source
    assert 'config["reports"]["parent_registry"]' in source
    assert 'parent_row[f"{fixture}_chunk_hash"]' in source
    assert source.count("for replay in (1, 2)") >= 2
    assert '"labels_mounted": False' in source
    assert '"detector_predictions_mounted": False' in source


def test_review_runtime_has_no_host_execution_api() -> None:
    source = (
        ROOT / "experiments/argos_reproduction/reviewed_rule_runtime.py"
    ).read_text(encoding="utf-8")
    for prohibited in ("exec(", "eval(", "compile(", "importlib", "runpy"):
        assert prohibited not in source


def test_review_runtime_image_lineage_is_complete() -> None:
    config = json.loads(
        (
            ROOT
            / "configs/argos_reproduction/task038c_review_inner_experiment.json"
        ).read_text(encoding="utf-8")
    )
    image = config["image"]
    assert image["pinned_from"].startswith("docker.io/library/python@sha256:")
    assert image["python_version"] == "3.11.9"
    assert image["numpy_version"] == "1.26.4"
