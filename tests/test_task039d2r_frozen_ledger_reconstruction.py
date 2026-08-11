from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from paperworks.profiling.task039d2_result_recovery_v1 import (
    PRIVATE_D2_LEDGER_HASH,
    PRIVATE_D2_LEDGER_NAME,
    assert_reconstruction_invariance_v1,
    build_arm_summary_from_frozen_ledger_v1,
    build_directional_summary_from_frozen_ledger_v1,
    build_pair_summary_from_frozen_ledger_v1,
    load_d1_private_inputs_for_recovery_v1,
    validate_frozen_d2_ledger_v1,
    verify_recovery_self_hash_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import CandidateProvenanceAnalysisViewV1


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("TASK039D_PRIVATE_ROOT") and os.environ.get("TASK039D2_PRIVATE_ROOT"), "external frozen D1/D2 ledgers are not configured")
class TASK039D2RFrozenLedgerReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.d1_root = Path(os.environ["TASK039D_PRIVATE_ROOT"])
        cls.d2_root = Path(os.environ["TASK039D2_PRIVATE_ROOT"])

    def test_exact_private_ledger_and_aggregate_reconstruction(self) -> None:
        inputs = load_d1_private_inputs_for_recovery_v1(self.d1_root)
        ledger = json.loads((self.d2_root / PRIVATE_D2_LEDGER_NAME).read_text(encoding="utf-8"))
        validation = validate_frozen_d2_ledger_v1(ledger, expected_d1_relations=inputs.relations)
        self.assertEqual(ledger["artifact_hash"], PRIVATE_D2_LEDGER_HASH)
        self.assertEqual((validation.confirmed_count, validation.conflict_count), (42, 3))
        directional = build_directional_summary_from_frozen_ledger_v1(ledger)
        d1_pair = json.loads((ROOT / "docs/task_reports/TASK-039D1_PAIR_FIT_SUMMARY.json").read_text())
        pair = build_pair_summary_from_frozen_ledger_v1(d1_pair_summary=d1_pair, directional_summary=directional)
        provenance = json.loads((ROOT / "docs/task_reports/TASK-039D0_PROVENANCE_ANALYSIS_VIEW.json").read_text())
        CandidateProvenanceAnalysisViewV1.from_dict(provenance)
        d1_arm = json.loads((ROOT / "docs/task_reports/TASK-039D1_ARM_FIT_SUMMARY.json").read_text())
        arm = build_arm_summary_from_frozen_ledger_v1(
            d1_arm_summary=d1_arm, pair_summary=pair, directional_summary=directional, provenance=provenance,
        )
        assert_reconstruction_invariance_v1(directional=directional, pair=pair, arm=arm)
        self.assertEqual(directional["artifact_hash"], "4f5057380c4b1b995bd0d5a714d307df556ce05094223fa909b6e2ed7dfec666")
        self.assertEqual(pair["artifact_hash"], "3929e84c680422a75069d59e1bef756f054a476ecc95f3e4e9573c7dfe368ad5")
        self.assertEqual(arm["artifact_hash"], "afc9ea42cf4c925667888e6223e414769c97fe326e0eb4c7c55f6ef9155c42e7")

    def test_failed_run_custody_is_self_hashed(self) -> None:
        custody = json.loads((ROOT / "docs/task_reports/TASK-039D2_FAILED_RUN_CUSTODY.json").read_text())
        verify_recovery_self_hash_v1(custody)
        self.assertEqual(custody["private_ledger_hash"], PRIVATE_D2_LEDGER_HASH)
        self.assertTrue(custody["private_scientific_ledger_authoritative_custody_candidate"])
        self.assertFalse(custody["original_public_outputs_authoritative"])


if __name__ == "__main__":
    unittest.main()
