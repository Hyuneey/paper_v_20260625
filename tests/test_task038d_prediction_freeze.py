import json
from pathlib import Path


def test_prediction_freeze_contains_no_paths_or_arrays() -> None:
    payload = json.loads(
        Path("docs/task_reports/TASK-038D_CANDIDATE_PREDICTION_MANIFEST.json").read_text()
    )
    text = json.dumps(payload)
    assert payload["status"] == "frozen_before_inner_label_access"
    assert "private_argos_reproduction" not in text
    assert "output_labels" not in text
    assert "prediction_values" not in text
