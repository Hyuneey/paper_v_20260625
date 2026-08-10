from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.candidates.gdn_candidate_discovery_v1 import (
    GDNSeedGraphRecordV1,
    aggregate_and_rank_gdn_candidates_v1,
)
from paperworks.gdn.gdn_remediation_environment_v1 import verify_self_hash_v1
from paperworks.gdn.pyg_softmax_compatibility_v1 import FROZEN_HYPERPARAMETER_HASH
from scripts.run_task039c_gdn_compat import (
    _build_access_audit,
    _build_execution_receipt,
    _build_passing_result,
    _build_report,
)


ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = "2026-08-10T11:00:00+00:00"
COMPATIBILITY_HASH = "a" * 64
EXECUTION_COMMIT = "b" * 40


def _universe() -> tuple[tuple[str, str], ...]:
    bundle = json.loads(
        (ROOT / "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json").read_text(
            encoding="utf-8"
        )
    )
    policy = bundle["universe_policy"]
    return tuple(
        (source, target)
        for source in policy["source_variables"]
        for target in policy["target_variables"]
    )


def _seed_records() -> tuple[GDNSeedGraphRecordV1, ...]:
    universe = _universe()
    records = []
    for seed, count, offset in ((11, 50, 0.001), (23, 40, 0.002), (37, 30, 0.003)):
        records.append(
            GDNSeedGraphRecordV1(
                seed=seed,
                successful=True,
                selected_edges=tuple(universe[:count]),
                candidate_similarities={
                    pair: (index + 1) / 200.0 + offset
                    for index, pair in enumerate(universe)
                },
                hyperparameter_hash=FROZEN_HYPERPARAMETER_HASH,
                epoch_count=4,
                best_validation_loss=0.25 + offset,
            )
        )
    return tuple(records)


class Task039CGDNCExecutionContractTests(unittest.TestCase):
    def test_access_audit_is_self_hashed_and_rejects_all_prohibited_inputs(self) -> None:
        audit = _build_access_audit(
            status="failed_gdn_final_attempt",
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            train1_accessed=True,
            train2_accessed=True,
            feature_count=37,
            created_at=CREATED_AT,
        )
        self.assertEqual(verify_self_hash_v1(audit), audit["artifact_hash"])
        self.assertTrue(audit["train1_accessed"])
        self.assertTrue(audit["train2_accessed"])
        for field in (
            "train3_accessed",
            "train4_accessed",
            "test_accessed",
            "labels_accessed",
            "attacks_accessed",
            "br2_pair_supervision_used",
            "meta_output_used",
            "stat_output_used",
            "partial_gdnr_state_reused",
        ):
            self.assertFalse(audit[field])

    def test_synthetic_three_seed_result_uses_one_denominator_three_ranking(self) -> None:
        records = _seed_records()
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=_universe(),
            seed_records=records,
        )
        result = _build_passing_result(
            execution_commit=EXECUTION_COMMIT,
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            environment={"dependency_environment_fingerprint": "c" * 64},
            ranking=ranking,
            seed_records=records,
            ledger_hashes=(
                {"seed": 11, "ledger_hash": "1" * 64},
                {"seed": 23, "ledger_hash": "2" * 64},
                {"seed": 37, "ledger_hash": "3" * 64},
            ),
            created_at=CREATED_AT,
        )
        self.assertEqual(result["seeds_attempted"], [11, 23, 37])
        self.assertEqual(result["seeds_completed"], [11, 23, 37])
        self.assertEqual(result["evaluated_candidate_count"], 144)
        self.assertEqual(result["supported_candidate_count"], 50)
        self.assertEqual(len(result["top10"]), 10)
        self.assertEqual(len(result["top20"]), 20)
        self.assertEqual(len(result["top40"]), 40)
        self.assertEqual(result["candidate_shortfall"], {"10": 0, "20": 0, "40": 0})
        self.assertTrue(
            all(
                item["edge_selection_frequency"]
                == item["selected_seed_count"] / 3.0
                for item in result["ranking"]
            )
        )
        self.assertEqual(
            [(item["source"], item["target"]) for item in result["top20"]],
            [
                (item["source"], item["target"])
                for item in result["ranking"][:20]
            ],
        )
        self.assertEqual(verify_self_hash_v1(result), result["artifact_hash"])

    def test_passing_result_hash_is_deterministic(self) -> None:
        records = _seed_records()
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=_universe(), seed_records=records
        )
        kwargs = {
            "execution_commit": EXECUTION_COMMIT,
            "compatibility_receipt_hash": COMPATIBILITY_HASH,
            "environment": {"dependency_environment_fingerprint": "c" * 64},
            "ranking": ranking,
            "seed_records": records,
            "ledger_hashes": (
                {"seed": 11, "ledger_hash": "1" * 64},
                {"seed": 23, "ledger_hash": "2" * 64},
                {"seed": 37, "ledger_hash": "3" * 64},
            ),
            "created_at": CREATED_AT,
        }
        self.assertEqual(
            _build_passing_result(**kwargs)["artifact_hash"],
            _build_passing_result(**kwargs)["artifact_hash"],
        )

    def test_final_failure_receipt_produces_no_ranking_and_zero_retries(self) -> None:
        access = _build_access_audit(
            status="failed_gdn_final_attempt",
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            train1_accessed=True,
            train2_accessed=True,
            feature_count=37,
            created_at=CREATED_AT,
        )
        preserved_result = json.loads(
            (ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json").read_text(
                encoding="utf-8"
            )
        )
        receipt = _build_execution_receipt(
            status="failed_gdn_final_attempt",
            execution_commit=EXECUTION_COMMIT,
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            scientific_hashes={"source.py": "d" * 64},
            access=access,
            result=preserved_result,
            seeds_attempted=(11,),
            seeds_completed=(),
            ledger_hashes=(),
            failure_stage="training_seed_11",
            failure_type="RuntimeError",
            created_at=CREATED_AT,
        )
        self.assertEqual(receipt["status"], "failed_gdn_final_attempt")
        self.assertEqual(receipt["seed_retry_count"], 0)
        self.assertFalse(receipt["ranking_produced"])
        self.assertIsNone(receipt["ranking_hash"])
        self.assertEqual(receipt["top10_count"], 0)
        self.assertEqual(receipt["top20_count"], 0)
        self.assertEqual(receipt["top40_count"], 0)
        self.assertIsNone(receipt["candidate_shortfall"])
        self.assertEqual(
            receipt["gdn_result_artifact_hash"], preserved_result["artifact_hash"]
        )
        self.assertEqual(
            receipt["recommendation"],
            "PROCEED_WITH_META_STAT_INTEGRATION_GDN_UNAVAILABLE",
        )
        self.assertEqual(verify_self_hash_v1(receipt), receipt["artifact_hash"])

    def test_passing_execution_receipt_reuses_the_single_ranking_views(self) -> None:
        records = _seed_records()
        ranking = aggregate_and_rank_gdn_candidates_v1(
            universe_pairs=_universe(), seed_records=records
        )
        result = _build_passing_result(
            execution_commit=EXECUTION_COMMIT,
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            environment={"dependency_environment_fingerprint": "c" * 64},
            ranking=ranking,
            seed_records=records,
            ledger_hashes=(
                {"seed": 11, "ledger_hash": "1" * 64},
                {"seed": 23, "ledger_hash": "2" * 64},
                {"seed": 37, "ledger_hash": "3" * 64},
            ),
            created_at=CREATED_AT,
        )
        access = _build_access_audit(
            status=result["status"],
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            train1_accessed=True,
            train2_accessed=True,
            feature_count=37,
            created_at=CREATED_AT,
        )
        receipt = _build_execution_receipt(
            status=result["status"],
            execution_commit=EXECUTION_COMMIT,
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            scientific_hashes={"source.py": "d" * 64},
            access=access,
            result=result,
            seeds_attempted=(11, 23, 37),
            seeds_completed=(11, 23, 37),
            ledger_hashes=(
                {"seed": 11, "ledger_hash": "1" * 64},
                {"seed": 23, "ledger_hash": "2" * 64},
                {"seed": 37, "ledger_hash": "3" * 64},
            ),
            failure_stage=None,
            failure_type=None,
            created_at=CREATED_AT,
        )
        self.assertTrue(receipt["ranking_produced"])
        self.assertEqual(receipt["ranking_hash"], result["ranking_hash"])
        self.assertEqual(receipt["top10_count"], len(result["top10"]))
        self.assertEqual(receipt["top20_count"], len(result["top20"]))
        self.assertEqual(receipt["top40_count"], len(result["top40"]))
        self.assertEqual(receipt["recommendation"], "PROCEED_WITH_THREE_ARM_INTEGRATION")
        self.assertEqual(receipt["seed_retry_count"], 0)

    def test_report_retains_all_three_lineage_stages(self) -> None:
        access = _build_access_audit(
            status="failed_gdn_final_attempt",
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            train1_accessed=True,
            train2_accessed=True,
            feature_count=37,
            created_at=CREATED_AT,
        )
        preserved_result = json.loads(
            (ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json").read_text(
                encoding="utf-8"
            )
        )
        execution = _build_execution_receipt(
            status="failed_gdn_final_attempt",
            execution_commit=EXECUTION_COMMIT,
            compatibility_receipt_hash=COMPATIBILITY_HASH,
            scientific_hashes={"source.py": "d" * 64},
            access=access,
            result=preserved_result,
            seeds_attempted=(11,),
            seeds_completed=(),
            ledger_hashes=(),
            failure_stage="training_seed_11",
            failure_type="RuntimeError",
            created_at=CREATED_AT,
        )
        report = _build_report(
            status="failed_gdn_final_attempt",
            compatibility={"artifact_hash": COMPATIBILITY_HASH},
            access=access,
            execution=execution,
            result=preserved_result,
        )
        self.assertIn("Initial GDN", report)
        self.assertIn("GDNR", report)
        self.assertIn("GDNC", report)
        self.assertIn("PROCEED_WITH_META_STAT_INTEGRATION_GDN_UNAVAILABLE", report)


if __name__ == "__main__":
    unittest.main()
