from __future__ import annotations

import json
from pathlib import Path
import unittest

from paperworks.validation_v2.core_v2a_authority_v1 import (
    CoreV2AAuthorityError,
    build_meta_stat_candidate_union_authority_v1,
    build_v2a_confirmed_cohort_v1,
    validate_meta_stat_candidate_union_authority_v1,
)


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "7" * 40


def _load(name: str) -> dict:
    return json.loads((ROOT / "docs" / "task_reports" / name).read_text(encoding="utf-8"))


class CoreV2AAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.meta = _load("TASK-039C_META_RESULT.json")
        self.stat = _load("TASK-039C_STAT_RESULT.json")
        self.directional = _load("TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json")

    def test_meta_stat_union_and_directional_subset_replay(self) -> None:
        authority = build_meta_stat_candidate_union_authority_v1(
            meta_document=self.meta, stat_document=self.stat, source_commit=COMMIT,
        )
        self.assertEqual(29, len(authority.candidates))
        self.assertEqual(11, sum(item.provenance == ("META", "STAT") for item in authority.candidates))
        self.assertEqual(authority.authority_hash, validate_meta_stat_candidate_union_authority_v1(
            authority, meta_document=self.meta, stat_document=self.stat,
        ))
        cohort, binding = build_v2a_confirmed_cohort_v1(
            candidate_authority=authority,
            directional_confirmation_document=self.directional,
            source_commit=COMMIT,
        )
        self.assertEqual(21, binding.confirmed_pair_count)
        self.assertEqual(39, binding.confirmed_directional_relation_count)
        self.assertEqual(39, len(cohort.relations))
        self.assertFalse(binding.pilot_v1_authority_aliased)
        self.assertFalse(binding.test1_accessed)
        self.assertFalse(binding.test2_accessed)
        self.assertFalse(binding.labels_accessed)

    def test_wrong_upstream_identity_fails_closed(self) -> None:
        mutated = dict(self.meta)
        mutated["artifact_hash"] = "0" * 64
        with self.assertRaises(CoreV2AAuthorityError):
            build_meta_stat_candidate_union_authority_v1(
                meta_document=mutated, stat_document=self.stat, source_commit=COMMIT,
            )

    def test_unconfirmed_direction_is_not_admitted(self) -> None:
        authority = build_meta_stat_candidate_union_authority_v1(
            meta_document=self.meta, stat_document=self.stat, source_commit=COMMIT,
        )
        cohort, _ = build_v2a_confirmed_cohort_v1(
            candidate_authority=authority,
            directional_confirmation_document=self.directional,
            source_commit=COMMIT,
        )
        admitted = {(x.source, x.target, x.source_direction, x.target_direction) for x in cohort.relations}
        conflicts = {
            (x["source"], x["target"], x["source_step_direction"], x["target_response_direction"])
            for x in self.directional["relations"]
            if x["confirmation_status"] == "calibration_conflict"
        }
        self.assertFalse(admitted & conflicts)


if __name__ == "__main__":
    unittest.main()
