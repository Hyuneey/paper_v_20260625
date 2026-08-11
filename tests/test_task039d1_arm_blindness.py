from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperworks.profiling.task039d1_fit_v1 import (
    PROFILING_IDENTITY_VIEW_HASH,
    TASK039D1Error,
    build_arm_fit_summary_v1,
    load_provenance_after_outcomes_frozen_v1,
    verify_d1_self_hash_v1,
    write_json_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    assert_arm_blind_identity_record_v1,
    profiling_identity_from_candidate_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/task_reports"


class Task039D1ArmBlindnessTests(unittest.TestCase):
    def test_identity_view_is_exact_and_contains_no_arm_fields(self) -> None:
        view = json.loads((REPORTS / "TASK-039D0_PROFILING_IDENTITY_VIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(view["artifact_hash"], PROFILING_IDENTITY_VIEW_HASH)
        self.assertEqual(len(view["candidates"]), 47)
        for record in view["candidates"]:
            assert_arm_blind_identity_record_v1(record)
            self.assertEqual(
                set(record),
                {"source", "target", "process", "relation_family", "candidate_cohort_hash"},
            )

    def test_all_arm_evidence_fields_are_rejected(self) -> None:
        view = json.loads((REPORTS / "TASK-039D0_PROFILING_IDENTITY_VIEW.json").read_text(encoding="utf-8"))
        record = view["candidates"][0]
        fields = {
            "origin_arms": ["META"], "META": {}, "STAT": {}, "GDN": {},
            "meta_rank": 1, "meta_tier": "M1", "evidence_tier": "M1",
            "stat_correlation": 0.2, "selected_horizon_seconds": 5,
            "stability_strength": 0.2, "gdn_rank": 1, "gdn_frequency": 1.0,
            "gdn_similarity": 0.3, "overlap_category": "shared", "origin_arm_count": 2,
        }
        for name, value in fields.items():
            with self.subTest(name=name), self.assertRaises(Exception):
                assert_arm_blind_identity_record_v1({**record, name: value})

    def test_same_pair_projects_identically_under_fake_provenance(self) -> None:
        a = {"source": "P1_FCV01D", "target": "P1_FT01", "origin_arms": ["META"], "META": {"rank": 1}}
        b = {"source": "P1_FCV01D", "target": "P1_FT01", "origin_arms": ["GDN"], "GDN": {"rank": 20}}
        self.assertEqual(profiling_identity_from_candidate_v1(a), profiling_identity_from_candidate_v1(b))

    def test_provenance_cannot_load_before_pair_summary_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing.json"
            with self.assertRaises(TASK039D1Error):
                load_provenance_after_outcomes_frozen_v1(
                    provenance_path=REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json",
                    frozen_pair_summary_path=missing,
                    expected_pair_summary_hash="0" * 64,
                )

    def test_arm_summary_reuses_one_frozen_pair_outcome(self) -> None:
        provenance = json.loads((REPORTS / "TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json").read_text(encoding="utf-8"))
        pairs = []
        for item in provenance["candidates"]:
            pairs.append({
                "source": item["source"], "target": item["target"],
                "step_up_status": "fit_supported", "step_down_status": "fit_unsupported",
                "pair_fit_status": "fit_supported_pair",
            })
        from paperworks.profiling.task039d1_fit_v1 import TASK039D1PairFitSummaryV1, D0_PROTOCOL_BUNDLE_HASH
        pair = TASK039D1PairFitSummaryV1({
            "task_id": "TASK-039D1", "status": "frozen_task039d1_pair_fit_outcomes",
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "candidate_cohort_hash": provenance["cohort_hash"],
            "profiling_identity_view_hash": PROFILING_IDENTITY_VIEW_HASH,
            "candidate_count": 47, "directional_opportunity_count": 94,
            "pair_fit_supported_count": 47, "pair_fit_unsupported_count": 0,
            "directional_status_counts": {"fit_supported": 47, "direction_unstable": 0, "fit_unsupported": 47},
            "pair_outcomes": pairs, "lower_ranked_fallback_used": False,
            "candidate_arm_evidence_visible_to_profiler": False,
        }).to_dict()
        summary = build_arm_fit_summary_v1(pair_summary_document=pair, provenance_document=provenance).to_dict()
        self.assertTrue(summary["same_pair_same_d1_outcome_across_all_origin_arms"])
        self.assertEqual([item["pair_fit_supported_count"] for item in summary["arms"]], [20, 20, 20])
        self.assertFalse(summary["winner_selected"])


if __name__ == "__main__":
    unittest.main()
