from __future__ import annotations

import contextlib
import io
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from paperworks.v6 import task039e3_r2r_d2_execution_recovery_authorization_v1 as a
from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as c


INDEPENDENT_ATTACKS = 25


class D2RecoveryAuthorizationIndependentAuditV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        base = Path(cls.temp.name)
        cls.repo, cls.private = base / "repo", base / "private"
        cls.repo.mkdir(); cls.private.mkdir()
        cls.root = c._issue_synthetic_recovery_root_v1(cls.private, cls.repo)
        cls.preflight = c._build_synthetic_preflight_v1(cls.root)
        cls.authorization = a._issue_synthetic_recovery_authorization_v1(cls.preflight)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def _assert_mutation_rejected(self, **changes: object) -> None:
        forged = replace(self.authorization, **changes)
        forged = replace(forged, authorization_hash=c.stable_hash_v1(forged._payload()))
        with self.assertRaises(a.D2ExecutionRecoveryAuthorizationV1Error):
            a.validate_d2_execution_recovery_authorization_v1(forged, self.preflight)

    def test_twenty_one_semantic_authority_attacks_rejected(self) -> None:
        attacks = (
            {"original_d2_design_hash": "0" * 64},
            {"d0_prediction_hash": "0" * 64},
            {"d1_prediction_hash": "0" * 64},
            {"source_map_hash": "0" * 64},
            {"required_distinct_source_count": 1},
            {"same_second_policy": "TEMPORAL_WINDOW"},
            {"d0_preservation_policy": "D0_SUPPRESSION_ALLOWED"},
            {"d0_score_access_authorized": True},
            {"d0_rerun_authorized": True},
            {"d1_rerun_authorized": True},
            {"authorized_additional_recovery_attempts": 2},
            {"historical_total_execution_attempts": 0},
            {"historical_aborted_infrastructure_attempts": 0},
            {"historical_completed_scientific_executions": 1},
            {"maximum_future_completed_scientific_executions": 2},
            {"result_driven_retries_authorized": 1},
            {"result_driven_retry_authorized": True},
            {"test2_authorized": True},
            {"outer_authorized": True},
            {"fusion_change_authorized": True},
            {"label_before_combined_prediction_authorized": True},
        )
        self.assertEqual(21, len(attacks))
        for attack in attacks:
            with self.subTest(attack=tuple(attack)):
                self._assert_mutation_rejected(**attack)

    def test_root_inside_git_and_symlink_rejected(self) -> None:
        with self.assertRaises(c.D2RecoveryCustodyV1Error):
            c._issue_synthetic_recovery_root_v1(self.repo, self.repo)
        with mock.patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(c.D2RecoveryCustodyV1Error):
                c._issue_synthetic_recovery_root_v1(self.private, self.repo)

    def test_path_bearing_oserror_and_traceback_channels_redacted(self) -> None:
        path_token = "UNIQUE_PRIVATE_PATH_TOKEN_INDEPENDENT"
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("pathlib.Path.open", side_effect=OSError(path_token)):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(c.D2RecoveryCustodyV1Error) as caught:
                    c._atomic_write_bytes_v1(
                        self.root, ".independent-sentinel", b"x", allow_sentinel=True,
                    )
        public_channels = (
            str(caught.exception), repr(caught.exception),
            stdout.getvalue(), stderr.getvalue(), caught.exception.code,
        )
        self.assertEqual(0, sum(item.count(path_token) for item in public_channels))

    def test_original_fusion_source_not_imported_or_duplicated(self) -> None:
        custody_source = Path(c.__file__).read_text(encoding="utf-8")
        auth_source = Path(a.__file__).read_text(encoding="utf-8")
        forbidden = (
            "_build_fusion_evidence_v1", "fuse_point_v1(",
            "_parse_frozen_d0_prediction_v1", "_parse_frozen_d1_prediction_v1",
            "_load_label_custody_once_v1", "metric_computations +=",
        )
        for token in forbidden:
            self.assertNotIn(token, custody_source)
            self.assertNotIn(token, auth_source)


if __name__ == "__main__":
    unittest.main()
