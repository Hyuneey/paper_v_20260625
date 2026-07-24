from experiments.argos_reproduction.task038e_execution_dedup import (
    physical_key,
    physical_unit_id,
)


def test_full_lineage_controls_physical_deduplication() -> None:
    base = physical_key(
        rule_hash="r",
        detector_variant="LSTMADalpha",
        kpi_id="k",
        direction="FN",
        outer_input_hash="v",
        frozen_runtime_hash="x",
    )
    assert physical_unit_id(base) == physical_unit_id(dict(reversed(list(base.items()))))
    changed = dict(base, direction="FP")
    assert physical_unit_id(base) != physical_unit_id(changed)


def test_manifest_deduplicates_without_merging_logical_records() -> None:
    import json
    from pathlib import Path

    report = json.loads(
        Path("docs/task_reports/TASK-038E_PHYSICAL_EXECUTION_MANIFEST.json").read_text()
    )
    assert report["physical_execution_unit_count"] == 146
    assert report["new_execution_unit_count"] == 125
    assert report["exact_reuse_unit_count"] == 21
    assert not report["duplicate_physical_execution_performed"]
    assert len({row["physical_execution_unit_id"] for row in report["records"]}) == 146
