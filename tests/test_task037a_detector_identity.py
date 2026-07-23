import json
from pathlib import Path

from experiments.argos_reproduction.lstm_variant_resolver import resolve_lstm_variant


ROOT = Path(__file__).resolve().parents[1]


def test_generic_argos_name_preserves_dual_variant_ambiguity():
    result = resolve_lstm_variant(
        argos_names=["LSTMAD"],
        easytsad_variants={"LSTMADalpha": True, "LSTMADbeta": True},
    )
    assert result.identity_status == "detector_family_recovered_variant_ambiguous"
    assert result.retained_variants == ("LSTMADalpha", "LSTMADbeta")
    assert result.selection_between_variants == "prohibited"


def test_committed_identity_report_does_not_claim_exact_reproduction():
    report = json.loads((ROOT / "docs/task_reports/TASK-037A_DETECTOR_IDENTITY_REPORT.json").read_text())
    assert report["argos_exact_variant_identified"] is False
    assert report["argos_exact_config_identified"] is False
    assert report["performance_metrics_computed"] is False
