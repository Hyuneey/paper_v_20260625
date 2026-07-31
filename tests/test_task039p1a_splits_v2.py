from __future__ import annotations

import unittest

from paperworks.data.contracts_v2 import (
    DataContractV2Error,
    RawRangeV2,
    SplitRoleV2,
)
from paperworks.data.splits_v2 import (
    DataOperationV2,
    OPERATION_PERMISSIONS_V2,
    SplitPermissionV2Error,
    SplitPolicyV2Error,
    assert_operation_permitted_v2,
    generate_split_windows_v2,
    required_purge_gap_v2,
    validate_split_collection_v2,
)
from tests.task039p1a_support import split_manifest_v2


class Task039P1ASplitsV2Tests(unittest.TestCase):
    def test_complete_operation_permission_matrix(self) -> None:
        for role in SplitRoleV2:
            split = split_manifest_v2(
                role,
                sealed_approved=role is SplitRoleV2.SEALED_EVALUATION,
            )
            for operation in DataOperationV2:
                permitted = role in OPERATION_PERMISSIONS_V2[operation]
                with self.subTest(role=role.value, operation=operation.value):
                    if permitted:
                        assert_operation_permitted_v2(split, operation)
                    else:
                        with self.assertRaises(SplitPermissionV2Error):
                            assert_operation_permitted_v2(split, operation)

    def test_required_negative_role_cases_fail_closed(self) -> None:
        outer = split_manifest_v2(SplitRoleV2.OUTER_VALIDATION)
        sealed = split_manifest_v2(
            SplitRoleV2.SEALED_EVALUATION, sealed_approved=True
        )
        development = split_manifest_v2(SplitRoleV2.DEVELOPMENT)
        inner = split_manifest_v2(SplitRoleV2.INNER_UTILITY)
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(
                outer, DataOperationV2.REVISE_RULE_WITH_FEEDBACK
            )
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(outer, "select_detector_threshold")
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(
                sealed, DataOperationV2.CALIBRATE_RELATION_PARAMETERS
            )
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(
                development, DataOperationV2.RUN_SEALED_EVALUATION
            )
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(
                inner, DataOperationV2.PROFILE_NORMAL_RELATION
            )

    def test_sealed_evaluation_requires_approval(self) -> None:
        split = split_manifest_v2(SplitRoleV2.SEALED_EVALUATION)
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(
                split, DataOperationV2.RUN_SEALED_EVALUATION
            )

    def test_unknown_operation_fails_closed(self) -> None:
        with self.assertRaises(SplitPermissionV2Error):
            assert_operation_permitted_v2(
                split_manifest_v2(SplitRoleV2.DEVELOPMENT),
                "unknown_operation",
            )

    def test_raw_ranges_reject_overlap_and_wrong_order(self) -> None:
        with self.assertRaises(DataContractV2Error):
            split_manifest_v2(
                SplitRoleV2.NORMAL_GUARD,
                ranges=(RawRangeV2(10, 20), RawRangeV2(0, 5)),
            )
        with self.assertRaises(DataContractV2Error):
            split_manifest_v2(
                SplitRoleV2.NORMAL_GUARD,
                ranges=(RawRangeV2(0, 10), RawRangeV2(9, 20)),
            )

    def test_purge_gap_formula_and_insufficient_gap(self) -> None:
        self.assertEqual(required_purge_gap_v2(4, 2), 5)
        split = split_manifest_v2(
            SplitRoleV2.NORMAL_CANDIDATE_FIT, purge_gap_samples=4
        )
        with self.assertRaises(SplitPolicyV2Error):
            generate_split_windows_v2(
                split, window_size=4, maximum_required_lag=2
            )

    def test_windows_are_independent_and_do_not_cross_ranges(self) -> None:
        split = split_manifest_v2(
            SplitRoleV2.NORMAL_RELATION_CALIBRATION,
            ranges=(RawRangeV2(0, 12), RawRangeV2(20, 32)),
        )
        windows = generate_split_windows_v2(
            split,
            window_size=4,
            maximum_required_lag=2,
            step=2,
        )
        self.assertTrue(windows)
        for window in windows:
            owning_range = split.raw_ranges[window.range_index]
            self.assertGreaterEqual(window.context_start, owning_range.start)
            self.assertLess(window.target_index, owning_range.end)
        self.assertFalse(
            any(window.context_start < 12 < window.target_index for window in windows)
        )

    def test_collection_checks_physical_boundary_purge(self) -> None:
        first = split_manifest_v2(
            SplitRoleV2.NORMAL_CANDIDATE_FIT,
            ranges=(RawRangeV2(0, 20),),
        )
        second = split_manifest_v2(
            SplitRoleV2.NORMAL_RELATION_CALIBRATION,
            ranges=(RawRangeV2(24, 40),),
        )
        with self.assertRaises(SplitPolicyV2Error):
            validate_split_collection_v2(
                (first, second),
                window_size=4,
                maximum_required_lag=2,
            )


if __name__ == "__main__":
    unittest.main()
