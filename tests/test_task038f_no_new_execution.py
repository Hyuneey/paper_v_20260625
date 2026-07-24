import json
from pathlib import Path


def test_task038f_has_no_execution_module_or_config() -> None:
    assert not list(Path("experiments/argos_reproduction").glob("*task038f*.py"))
    assert not list(Path("configs/argos_reproduction").glob("*task038f*.json"))


def test_structured_outcome_records_zero_execution_and_access() -> None:
    payload = json.loads(
        Path("docs/task_reports/TASK-038F_OVERALL_VALIDITY.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["provider_calls"] == 0
    assert payload["new_experiments"] == 0
    assert payload["outer_access"] is False
    assert payload["sealed_test_access"] is False
    assert payload["private_artifact_access"] is False


def test_task038f_files_do_not_reference_raw_or_private_artifacts() -> None:
    paths = [
        *Path("docs/argos_reproduction").glob("*ARGOS*VALID*.md"),
        *Path("docs/task_reports").glob("TASK-038F*"),
        Path("TASKS/TASK-038F_ARGOS_METHOD_VALIDITY_SYNTHESIS.md"),
    ]
    forbidden = (
        "private_argos_reproduction",
        "outer_values.npy",
        "outer_labels.npy",
        "test_values.npy",
        "test_labels.npy",
        "def inference(",
        "prompt_text",
        "response_text",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
