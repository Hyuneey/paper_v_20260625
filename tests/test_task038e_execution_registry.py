import json
from collections import Counter
from pathlib import Path


def test_exact_outer_registry_is_complete_before_values() -> None:
    report = json.loads(
        Path("docs/task_reports/TASK-038E_OUTER_EXECUTION_REGISTRY.json").read_text()
    )
    assert report["status"] == "frozen_before_outer_value_access"
    assert report["logical_record_count"] == 249
    assert report["logical_branch_arm_count_after_composition"] == 320
    assert Counter(row["evidence_block"] for row in report["records"]) == {
        "branch_selected": 160,
        "review_transfer": 76,
        "repair_utility": 13,
    }
    assert not report["outer_values_accessed"]
    assert not report["outer_labels_accessed"]
