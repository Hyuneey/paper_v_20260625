from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.candidates.gdn_candidate_discovery_v1 import (
    GDNCandidateDiscoveryError,
    GDNSeedGraphRecordV1,
    aggregate_and_rank_gdn_candidates_v1,
    assert_supplementary_method_boundaries_v1,
    build_blocked_gdn_result_v1,
    project_seed_record_to_universe_v1,
)
from paperworks.v6.candidate_discovery_protocol_v1 import derive_candidate_budget_views_v1
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json"
ACCESS = ROOT / "docs/task_reports/TASK-039C_GDN_DATA_ACCESS_AUDIT.json"
REPORT = ROOT / "docs/task_reports/TASK-039C_GDN_REPORT.md"
SCHEMA = ROOT / "schemas/v6/gdn_candidate_result_v1_schema.json"
HASH = "a" * 64


def universe():
    return tuple((f"S{source:02d}", f"T{target:02d}") for source in range(12) for target in range(12))


def seed_record(seed: int, selected, similarities=None):
    pairs = universe()
    values = {pair: 0.1 for pair in pairs}
    if similarities:
        values.update(similarities)
    return GDNSeedGraphRecordV1(
        seed=seed,
        successful=True,
        selected_edges=tuple(selected),
        candidate_similarities=values,
        hyperparameter_hash=HASH,
        epoch_count=2,
        best_validation_loss=0.2,
    )


class Task039CGDNCandidateTests(unittest.TestCase):
    def test_common_universe_projection_preserves_semantic_direction(self) -> None:
        pairs = universe()
        projected = project_seed_record_to_universe_v1(
            seed=11,
            selected_model_edges=(("S00", "T00"), ("T00", "S00"), ("OTHER", "T00")),
            model_similarities={pair: 0.2 for pair in pairs},
            universe_pairs=pairs,
            hyperparameter_hash=HASH,
            epoch_count=1,
            best_validation_loss=0.1,
        )
        self.assertEqual(projected.selected_edges, (("S00", "T00"),))
        self.assertNotIn(("T00", "S00"), projected.selected_edges)

    def test_frequency_denominator_remains_three_and_ranks_before_similarity(self) -> None:
        high_frequency = ("S11", "T11")
        high_similarity = ("S00", "T00")
        records = (
            seed_record(11, (high_frequency, high_similarity), {high_similarity: 0.99, high_frequency: 0.01}),
            seed_record(23, (high_frequency,), {high_similarity: 0.99, high_frequency: 0.01}),
            seed_record(37, (), {high_similarity: 0.99, high_frequency: 0.01}),
        )
        ranked = aggregate_and_rank_gdn_candidates_v1(universe_pairs=universe(), seed_records=records)
        self.assertEqual((ranked[0].source, ranked[0].target), high_frequency)
        self.assertEqual(ranked[0].edge_selection_frequency, 2.0 / 3.0)
        self.assertEqual(ranked[1].edge_selection_frequency, 1.0 / 3.0)

    def test_similarity_then_lexicographic_ties(self) -> None:
        first = ("S00", "T01")
        second = ("S00", "T02")
        third = ("S01", "T00")
        records = tuple(
            seed_record(seed, (first, second, third), {first: 0.4, second: 0.4, third: 0.2})
            for seed in (11, 23, 37)
        )
        ranked = aggregate_and_rank_gdn_candidates_v1(universe_pairs=universe(), seed_records=records)
        self.assertEqual([(item.source, item.target) for item in ranked], [first, second, third])

    def test_failed_seed_is_retained_and_frequency_fails_closed(self) -> None:
        failed = GDNSeedGraphRecordV1(
            seed=37,
            successful=False,
            selected_edges=(),
            candidate_similarities={},
            hyperparameter_hash=HASH,
            failure_reason="synthetic training failure",
        )
        with self.assertRaisesRegex(GDNCandidateDiscoveryError, "fail closed"):
            aggregate_and_rank_gdn_candidates_v1(
                universe_pairs=universe(),
                seed_records=(seed_record(11, ()), seed_record(23, ()), failed),
            )

    def test_attention_supplementary_only_and_xai_primary_prohibited(self) -> None:
        with self.assertRaisesRegex(GDNCandidateDiscoveryError, "supplementary"):
            assert_supplementary_method_boundaries_v1(
                attention_used_for_primary_ranking=True,
                posthoc_xai_used=False,
            )
        with self.assertRaisesRegex(GDNCandidateDiscoveryError, "XAI"):
            assert_supplementary_method_boundaries_v1(
                attention_used_for_primary_ranking=False,
                posthoc_xai_used=True,
            )

    def test_no_candidate_padding(self) -> None:
        pair = ("S00", "T00")
        records = tuple(seed_record(seed, (pair,)) for seed in (11, 23, 37))
        ranked = aggregate_and_rank_gdn_candidates_v1(universe_pairs=universe(), seed_records=records)
        views = derive_candidate_budget_views_v1(tuple((item.source, item.target) for item in ranked))
        self.assertEqual(len(views.top10), 1)
        self.assertEqual(dict(views.candidate_shortfall), {10: 9, 20: 19, 40: 39})

    def test_blocked_result_has_deterministic_hash_and_no_candidates(self) -> None:
        result = build_blocked_gdn_result_v1(
            status="blocked_optional_dependency",
            phase_a_commit="b" * 40,
            fidelity_receipt_hash="c" * 64,
            dependency_environment_fingerprint="d" * 64,
            backend_classification="upstream_aligned_validated",
            blocking_reason="exact dependency unavailable",
            created_at="2026-08-10T00:00:00+00:00",
        )
        first = result.to_dict()
        second = result.to_dict()
        self.assertEqual(first, second)
        self.assertNotIn("ranking", first)
        self.assertNotIn("top10", first)
        observed = first.pop("artifact_hash")
        self.assertEqual(stable_hash_v1(first), observed)

    def test_final_blocked_artifacts_validate_and_disclose_no_access(self) -> None:
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(result)
        observed = result.pop("artifact_hash")
        self.assertEqual(stable_hash_v1(result), observed)
        self.assertEqual(result["status"], "blocked_optional_dependency")
        self.assertFalse(result["real_hai_feature_access"])
        self.assertNotIn("ranking", result)
        audit = json.loads(ACCESS.read_text(encoding="utf-8"))
        audit_hash = audit.pop("artifact_hash")
        self.assertEqual(stable_hash_v1(audit), audit_hash)
        self.assertEqual(audit["files_accessed"], [])

    def test_public_raw_value_checkpoint_path_and_private_path_leak_scan(self) -> None:
        for path in (RESULT, ACCESS, REPORT):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(
                re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", text), path.name
            )
            self.assertNotIn("checkpoint_path", text.lower(), path.name)
            self.assertNotIn("raw_feature_values", text.lower(), path.name)


if __name__ == "__main__":
    unittest.main()
