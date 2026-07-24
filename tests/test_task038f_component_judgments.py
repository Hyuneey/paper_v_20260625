import json
from pathlib import Path


def test_all_seven_component_judgments_are_frozen() -> None:
    payload = json.loads(
        Path("docs/task_reports/TASK-038F_COMPONENT_JUDGMENTS.json").read_text(
            encoding="utf-8"
        )
    )
    dimensions = payload["dimensions"]
    assert len(dimensions) == 7
    assert dimensions["V1_one_shot_generation_operability"]["support_label"] == (
        "partial_component_support"
    )
    assert dimensions["V2_repair_agent_operational_validity"]["support_label"] == (
        "strong_component_support"
    )
    assert dimensions["V3_repair_agent_detection_utility"]["support_label"] == (
        "partial_component_support"
    )
    assert dimensions["V4_review_agent_inner_effectiveness"]["support_label"] == (
        "strong_component_support"
    )
    outer = dimensions["V5_review_agent_outer_transfer"]
    assert outer["support_label"] == "strong_component_support"
    assert outer["evidence_status"] == "descriptive_previously_exposed_outer"
    assert dimensions["V6_end_to_end_agentic_aggregator_robustness"][
        "support_label"
    ] == "partial_component_support"
    assert dimensions["V7_safety_and_efficiency"]["support_label"] == (
        "partial_component_support"
    )


def test_fixed_component_label_enum_is_not_extended() -> None:
    payload = json.loads(
        Path("docs/task_reports/TASK-038F_COMPONENT_JUDGMENTS.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(payload["label_enum"]) == {
        "strong_component_support",
        "partial_component_support",
        "no_component_support",
        "unresolved",
    }
