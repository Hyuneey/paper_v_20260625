"""Focused R1 tests for exact synthetic feature-pair canonicalization."""

from __future__ import annotations

from dataclasses import replace
import math
import unittest

from paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 import (
    build_evaluator_authority_bundle_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_input_v1 import (
    build_synthetic_feature_frame_v1,
    feature_series_v1,
    feature_value_v1,
    validate_synthetic_feature_frame_v1,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import UtilityEvaluatorV1Error
from test_task039e3_r2r_utility_evaluator_v1_independent_authority import (
    build_lower_v4_authority,
)


R1_INPUT_INVALID_CASES = 11


class _FeaturePairTupleSubclass(tuple):
    pass


class UtilityEvaluatorV1R1InputCanonicalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = build_evaluator_authority_bundle_v1(build_lower_v4_authority())
        cls.features = cls.bundle.v4_authority.feature_schema.union_features

    def frame(self):
        return build_synthetic_feature_frame_v1(
            self.bundle,
            source_file_identity="hai-test1.csv",
            start_physical_row_index=100,
            rows=(tuple(0.0 for _ in self.features),),
        )

    @staticmethod
    def replace_first_pair(frame, pair: object):
        row = frame.rows[0]
        feature_values = (pair,) + row.feature_values[1:]
        forged_row = replace(row, feature_values=feature_values)
        return replace(frame, rows=(forged_row,))

    def test_canonical_exact_tuple_pair_and_accessors_pass(self) -> None:
        frame = self.frame()
        first_feature = frame.ordered_features[0]
        self.assertEqual(validate_synthetic_feature_frame_v1(frame, self.bundle), frame.frame_hash)
        self.assertEqual(feature_series_v1(frame, self.bundle, first_feature), (0.0,))
        self.assertEqual(
            feature_value_v1(
                frame,
                self.bundle,
                physical_row_index=100,
                feature=first_feature,
            ),
            0.0,
        )

    def test_widened_or_malformed_inner_pairs_reject_before_hash_replay(self) -> None:
        frame = self.frame()
        canonical_pair = frame.rows[0].feature_values[0]
        name = canonical_pair[0]
        invalid_pairs = (
            [name, 0.0],
            _FeaturePairTupleSubclass((name, 0.0)),
            (item for item in (name, 0.0)),
            (name,),
            (name, 0.0, 1.0),
            (name, True),
            (name, 0),
            (name, "0.0"),
            (name, math.nan),
            (name, math.inf),
            (name, -math.inf),
        )
        for pair in invalid_pairs:
            candidate = self.replace_first_pair(frame, pair)
            with self.subTest(pair_type=type(pair), pair_repr=repr(pair)):
                with self.assertRaises(UtilityEvaluatorV1Error):
                    validate_synthetic_feature_frame_v1(candidate, self.bundle)

    def test_list_pair_rejects_with_preserved_or_recomputed_outer_hashes(self) -> None:
        frame = self.frame()
        canonical_pair = frame.rows[0].feature_values[0]
        candidate = self.replace_first_pair(frame, [canonical_pair[0], canonical_pair[1]])

        # Canonical JSON normalization historically made these hashes equal.
        self.assertEqual(candidate.rows[0].row_identity, frame.rows[0].row_identity)
        self.assertEqual(candidate.frame_hash, frame.frame_hash)
        for forged in (candidate, replace(candidate, frame_hash=frame.frame_hash)):
            with self.assertRaises(UtilityEvaluatorV1Error):
                validate_synthetic_feature_frame_v1(forged, self.bundle)

    def test_feature_access_paths_inherit_pair_validation(self) -> None:
        frame = self.frame()
        first_feature = frame.ordered_features[0]
        candidate = self.replace_first_pair(frame, [first_feature, 0.0])
        with self.assertRaises(UtilityEvaluatorV1Error):
            feature_series_v1(candidate, self.bundle, first_feature)
        with self.assertRaises(UtilityEvaluatorV1Error):
            feature_value_v1(
                candidate,
                self.bundle,
                physical_row_index=100,
                feature=first_feature,
            )


if __name__ == "__main__":
    unittest.main()
