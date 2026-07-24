from __future__ import annotations

from experiments.argos_reproduction.repair_semantic_drift import structural_summary


def test_structural_drift_exposes_counts_not_literal_values() -> None:
    before = structural_summary("def inference(sample):\n    return sample > 1.0\n")
    after = structural_summary("def inference(sample):\n    return sample > 2.0\n")
    assert len(before["numeric_literals"]) == 1
    assert before["numeric_literals"] != after["numeric_literals"]
    assert after["function_signature_preserved"] is True


def test_structural_summary_tracks_import_and_control_flow() -> None:
    summary = structural_summary(
        "import numpy as np\n"
        "def inference(sample):\n"
        "    if len(sample):\n"
        "        return np.zeros(len(sample))\n"
        "    return np.array([])\n"
    )
    assert summary["import_set"] == ("numpy",)
    assert summary["control_flow_node_count"] == 1
