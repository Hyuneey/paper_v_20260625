import json
from pathlib import Path


def test_overall_classification_and_boundaries_are_exact() -> None:
    payload = json.loads(
        Path("docs/task_reports/TASK-038F_OVERALL_VALIDITY.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["classification"] == "partial_methodological_support"
    assert payload["evidence_status"] == (
        "descriptive_previously_exposed_outer_pending_sealed_confirmation"
    )
    assert payload["exact_ARGOS_reproduction"] is False
    assert payload["sealed_test_access"] is False
    assert payload["proposed_method_validated"] is False
    assert payload["reference_track_recommendation"] == (
        "freeze_ARGOS_reference_track"
    )


def test_strong_support_gate_fails_without_variant_robust_A3_and_sealed_test() -> None:
    payload = json.loads(
        Path("docs/task_reports/TASK-038F_OVERALL_VALIDITY.json").read_text(
            encoding="utf-8"
        )
    )
    gate = payload["strong_methodological_support_gate"]
    assert gate["Repair_operationally_effective"] is True
    assert gate["Review_improves_outer_performance"] is True
    assert gate["A3_improves_over_A0_for_both_variants"] is False
    assert gate["effect_survives_sealed_test_confirmation"] is False
    assert gate["gate_passed"] is False
    assert payload["classification"] != "strong_methodological_support"
