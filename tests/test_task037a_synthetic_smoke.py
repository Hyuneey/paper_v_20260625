import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_both_variants_pass_synthetic_replay_contract():
    report = json.loads((ROOT / "docs/task_reports/TASK-037A_SYNTHETIC_SMOKE_REPORT.json").read_text())
    assert report["status"] == "passed"
    assert report["execution_scope"] == "synthetic_only"
    assert report["performance_metrics_computed"] is False
    assert [item["variant"] for item in report["variants"]] == ["LSTMADalpha", "LSTMADbeta"]
    for variant in report["variants"]:
        assert variant["fit_repeats"] == 2
        assert variant["checkpoint_created"] is True
        assert variant["model_state_hash_stable"] is True
        assert variant["score_and_prediction_hashes_stable"] is True
        assert len(variant["runs"][0]["scenarios"]) == 6
        for scenario in variant["runs"][0]["scenarios"]:
            assert scenario["aligned_score_count"] == scenario["input_count"]
            assert scenario["scores_finite"] is True
            assert scenario["prediction_binary"] is True


def test_isolation_preflight_has_no_research_mounts():
    report = json.loads((ROOT / "docs/task_reports/TASK-037A_ENVIRONMENT_PREFLIGHT_REPORT.json").read_text())
    assert report["status"] == "passed"
    assert report["isolation"]["status"] == "passed"
    assert report["isolation"]["network_none"] is True
    assert report["isolation"]["host_mounts"] == []
    assert report["kpi_mounted"] is False
    assert report["rule_artifacts_mounted"] is False
