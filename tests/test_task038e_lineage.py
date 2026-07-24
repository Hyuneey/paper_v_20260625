import json
from pathlib import Path

from experiments.argos_reproduction.review_parent_registry import verify_hashed_report


def test_task038e_lineage_and_selection_hashes_match() -> None:
    config = json.loads(
        Path("configs/argos_reproduction/task038e_outer_branch_comparison.json").read_text()
    )
    for key, path in config["sources"].items():
        report = verify_hashed_report(Path(path), config["source_hashes"][key])
        assert report["task_id"].startswith("TASK-03")
    assert set(config["decision"]["branches"]) == {"A0", "A1", "A2", "A3"}
    assert config["decision"]["sealed_test_access"] is False
