import json
from pathlib import Path

from experiments.argos_reproduction.detector_error_support_audit import (
    audit_support,
    load_generation_cells,
)
from experiments.argos_reproduction.expanded_kpi_cohort import read_json


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/argos_reproduction/task037d_error_conditioned_rules.json"


def test_frozen_generation_lineage_has_both_variants_and_ten_kpis() -> None:
    config = read_json(CONFIG)
    cells = load_generation_cells(config)
    assert len(cells) == 20
    assert {cell.variant for cell in cells} == {"LSTMADalpha", "LSTMADbeta"}
    assert len({cell.kpi_id for cell in cells}) == 10
    assert all(len(cell.values) == len(cell.labels) == len(cell.predictions) for cell in cells)


def test_support_audit_has_all_forty_cells_and_no_later_split_access(
    tmp_path: Path,
) -> None:
    config = read_json(CONFIG)
    config["reports"]["support"] = str(tmp_path / "support.json")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    report = audit_support(config_path)
    assert report["potential_cell_count"] == 40
    assert report["inner_accessed"] is False
    assert report["outer_accessed"] is False
    assert report["test_accessed"] is False
    assert {row["direction"] for row in report["cells"]} == {"FN", "FP"}
