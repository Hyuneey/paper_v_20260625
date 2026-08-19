"""Independent strict-container attack for evaluator input/census custody."""

from __future__ import annotations

from dataclasses import replace
import unittest

from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    build_evaluator_authority_bundle_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error
from test_task039e3_r2r_utility_evaluator_v1_independent_authority import (
    build_lower_v4_authority,
)


INDEPENDENT_SEMANTIC_ATTACK_CLASSES = 1
RAW_INPUT_SCHEMA_ATTACKS = 1
EXPECTED_ACCEPTED_INVALID_CASES = 0


class IndependentInputContainerAudit(unittest.TestCase):
    def test_self_hashed_inner_feature_pair_list_widening_must_reject(self) -> None:
        bundle = build_evaluator_authority_bundle_v1(build_lower_v4_authority())
        row_values = tuple(0.0 for _ in bundle.v4_authority.feature_schema.union_features)
        canonical = build_synthetic_feature_frame_v1(
            bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=0,
            rows=(row_values,),
        )
        row = canonical.rows[0]
        widened_values = list(row.feature_values)
        widened_values[0] = [widened_values[0][0], widened_values[0][1]]  # type: ignore[list-item]
        widened_row = replace(row, feature_values=tuple(widened_values))
        forged = replace(canonical, rows=(widened_row,))

        # Tuple/list normalization leaves both self-hashes unchanged.  The
        # validator must therefore enforce the raw exact inner pair type.
        self.assertEqual(widened_row.row_identity, row.row_identity)
        self.assertEqual(forged.frame_hash, canonical.frame_hash)
        with self.assertRaises(UtilityEvaluatorV1Error):
            validate_synthetic_feature_frame_v1(forged, bundle)


if __name__ == "__main__":
    unittest.main()
