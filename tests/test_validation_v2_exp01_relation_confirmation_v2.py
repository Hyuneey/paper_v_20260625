from __future__ import annotations

import unittest

import numpy as np

from paperworks.validation_v2.exp01_relation_confirmation_v2 import (
    ArmBlindConfirmationOutcomeV2,
    Exp01ConfirmationAdapterError,
    fit_and_confirm_arbitrary_union_v2,
)
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


class Exp01ConfirmationAdapterV2Tests(unittest.TestCase):
    def test_normal_only_access_counters_are_exact(self) -> None:
        outcome = ArmBlindConfirmationOutcomeV2(
            pair_decisions=(("S", "T", True),),
            private_decision_ledger_hash="a" * 64,
            train3_read_receipt_hash="b" * 64,
        )
        self.assertEqual(outcome.train3_open_count, 1)
        with self.assertRaises(Exp01ConfirmationAdapterError):
            ArmBlindConfirmationOutcomeV2(
                pair_decisions=(("S", "T", True),),
                private_decision_ledger_hash="a" * 64,
                train3_read_receipt_hash="b" * 64,
                labels_accessed=True,
            )

    def test_arbitrary_union_fit_then_actual_train3_confirmation(self) -> None:
        order = tuple(P1_FEATURE_ORDER)
        source = "P1_FCV01D"
        target = "P1_FT01"

        def frame(rows: int) -> np.ndarray:
            matrix = np.zeros((rows, len(order)), dtype=np.float64)
            source_values = np.asarray([(index // 20) % 2 for index in range(rows)], dtype=np.float64)
            target_values = np.concatenate(([source_values[0]], source_values[:-1]))
            matrix[:, order.index(source)] = source_values
            matrix[:, order.index(target)] = target_values
            return matrix

        result = fit_and_confirm_arbitrary_union_v2(
            candidate_pairs=((source, target),),
            train1_matrix=frame(700), train2_matrix=frame(700), train3_matrix=frame(700),
            feature_order=order,
            train1_read_receipt_hash="1" * 64,
            train2_read_receipt_hash="2" * 64,
            train3_read_receipt_hash="3" * 64,
        )
        self.assertEqual(result.outcome.train3_open_count, 1)
        self.assertEqual(tuple(row[:2] for row in result.outcome.pair_decisions), ((source, target),))
        self.assertFalse(result.outcome.labels_accessed)
        self.assertEqual(result.private_ledger["arm_identity_exposed"], False)


if __name__ == "__main__":
    unittest.main()
