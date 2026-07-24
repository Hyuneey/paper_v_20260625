import json
from pathlib import Path

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json


REPORT_ROOT = Path("docs/task_reports")
EVIDENCE_MAP = REPORT_ROOT / "TASK-038F_EVIDENCE_SOURCE_MAP.json"


def _load(name: str) -> dict:
    return json.loads((REPORT_ROOT / name).read_text(encoding="utf-8"))


def test_every_evidence_source_exists_and_matches_its_committed_hash() -> None:
    payload = json.loads(EVIDENCE_MAP.read_text(encoding="utf-8"))
    assert payload["claim_count"] == len(payload["claims"]) == 25
    for claim in payload["claims"]:
        reports = [item.strip() for item in claim["source_report"].split(";")]
        hashes = [item.strip() for item in claim["source_report_hash"].split(";")]
        assert len(reports) == len(hashes)
        for report, expected_hash in zip(reports, hashes, strict=True):
            if expected_hash == "SELF_HASH_AFTER_FREEZE":
                continue
            source = json.loads(Path(report).read_text(encoding="utf-8"))
            observed_hash = source.pop("report_hash")
            assert observed_hash == expected_hash
            assert observed_hash == sha256_json(source)


def test_headline_values_equal_frozen_report_fields() -> None:
    repair = _load("TASK-038B_OPERABILITY_REPORT.json")
    assert repair["frozen_repair_population"] == 13
    assert repair["repaired_executable_count"] == 13

    review = _load("TASK-038C_EFFECT_REPORT.json")
    assert review["A2"]["reviewed_executable_and_inner_F1_improved"] == 34
    assert review["A2"]["reviewed_executable_and_inner_F1_equal"] == 1
    assert review["A2"]["invalid_or_nonexecutable_revision"] == 1
    assert review["A3"]["reviewed_executable_and_inner_F1_improved"] == 38
    assert review["A3"]["reviewed_executable_and_inner_F1_regressed"] == 3

    outer = _load("TASK-038E_BRANCH_OUTER_REPORT.json")
    arms = outer["per_branch_variant_arm"]
    assert arms["A0"]["LSTMADalpha"]["full_aggregator"]["macro"]["point_f1"] == (
        0.48835484765241866
    )
    assert arms["A2"]["LSTMADalpha"]["full_aggregator"]["macro"]["point_f1"] == (
        0.5046571805852699
    )
    assert arms["A0"]["LSTMADbeta"]["full_aggregator"]["macro"]["point_f1"] == (
        0.3880429715206822
    )
    assert arms["A2"]["LSTMADbeta"]["full_aggregator"]["macro"]["point_f1"] == (
        0.42152351510821406
    )
