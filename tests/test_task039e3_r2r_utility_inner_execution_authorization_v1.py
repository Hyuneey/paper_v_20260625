from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.v6.common import stable_hash_v1
from paperworks.v6 import (
    task039e3_r2r_utility_inner_execution_authorization_v1 as subject,
)


class TestInnerExecutionAuthorizationV1(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = (
            subject.build_synthetic_inner_execution_custody_preflight_receipt_v1()
        )
        self.authorization = subject.issue_inner_execution_authorization_v1(
            self.receipt
        )

    def _assert_authorization_rejected(self, candidate: object) -> None:
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            subject.validate_inner_execution_authorization_v1(
                candidate, self.receipt  # type: ignore[arg-type]
            )

    @staticmethod
    def _self_rehash(
        candidate: subject.InnerExecutionAuthorizationV1,
    ) -> subject.InnerExecutionAuthorizationV1:
        return replace(
            candidate,
            authorization_hash=stable_hash_v1(candidate._payload()),
        )

    def test_public_r3_authority_replay(self) -> None:
        replay = subject.replay_required_evaluator_audit_authority_v1()
        self.assertEqual(replay.implementation_identity, subject.R3_IMPLEMENTATION_IDENTITY)
        self.assertEqual(
            replay.independent_audit_receipt_hash,
            subject.R3_INDEPENDENT_AUDIT_RECEIPT_HASH,
        )
        self.assertTrue(replay.independently_audited)
        self.assertTrue(replay.full_independent_audit_completed)
        self.assertTrue(replay.inner_execution_authorization_ready)

    def test_exact_canonical_synthetic_contract_builds(self) -> None:
        observed = subject.validate_inner_execution_authorization_v1(
            self.authorization, self.receipt
        )
        self.assertEqual(observed, self.authorization.authorization_hash)
        self.assertEqual(self.authorization.authorization_scope, subject.AUTHORIZATION_SCOPE)
        self.assertEqual(self.authorization.experiment_arm, "D1")
        self.assertEqual(self.authorization.feature_filename, "hai-test1.csv")
        self.assertEqual(self.authorization.label_filename, "label-test1.csv")
        self.assertFalse(self.authorization.detector_authorized)
        self.assertFalse(self.authorization.outer_authorized)
        self.assertFalse(self.authorization.real_utility_execution_authorized)

    def test_synthetic_receipt_has_zero_real_reads(self) -> None:
        subject.validate_inner_execution_custody_preflight_receipt_v1(self.receipt)
        self.assertEqual(self.receipt.main_locator_reads, 0)
        self.assertEqual(self.receipt.main_registry_custody_validations, 0)
        self.assertEqual(self.receipt.supplement_locator_reads, 0)
        self.assertEqual(self.receipt.supplement_registry_custody_validations, 0)
        self.assertEqual(self.receipt.test1_feature_hash_passes, 0)
        self.assertEqual(self.receipt.test1_label_hash_passes, 0)
        self.assertFalse(self.receipt.test2_touched)
        self.assertFalse(self.receipt.scientific_parsing_performed)

    def test_real_validation_rejects_synthetic_contract(self) -> None:
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            subject.validate_inner_execution_authorization_v1(
                self.authorization, self.receipt, require_real=True
            )

    def test_test2_feature_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, feature_filename="hai-test2.csv"))
        )

    def test_outer_split_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, inner_split_id="OUTER"))
        )

    def test_test2_label_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, label_filename="label-test2.csv"))
        )

    def test_relation_count_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, common_relation_count=41))
        )

    def test_t2_escalation_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, t2_authorized=True))
        )

    def test_common_name_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, common_portfolio="COMMON-41"))
        )

    def test_main_descriptor_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, main_descriptor_hash="0" * 64))
        )

    def test_main_registry_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(
                replace(self.authorization, main_private_registry_expected_hash="0" * 64)
            )
        )

    def test_supplement_descriptor_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(
                replace(self.authorization, supplement_descriptor_hash="0" * 64)
            )
        )

    def test_supplement_purpose_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, supplement_purpose="RELATION_AUTHORITY"))
        )

    def test_combined_census_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(
                replace(self.authorization, combined_source_census_contract_hash="0" * 64)
            )
        )

    def test_r3_implementation_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, r3_implementation_identity="0" * 64))
        )

    def test_r3_audit_receipt_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(
                replace(self.authorization, r3_independent_audit_receipt_hash="0" * 64)
            )
        )

    def test_detector_escalation_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, detector_authorized=True))
        )

    def test_d0_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, experiment_arm="D0"))
        )

    def test_d2_substitution_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, experiment_arm="D2"))
        )

    def test_fusion_escalation_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, fusion_authorized=True))
        )

    def test_recalibration_escalation_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(
                replace(self.authorization, threshold_recalibration_authorized=True)
            )
        )

    def test_wrong_feature_hash_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, feature_sha256="0" * 64))
        )

    def test_wrong_label_hash_rejected(self) -> None:
        self._assert_authorization_rejected(
            self._self_rehash(replace(self.authorization, label_sha256="0" * 64))
        )

    def test_caller_reconstruction_rejected(self) -> None:
        self._assert_authorization_rejected(replace(self.authorization))

    def test_deepcopy_rejected(self) -> None:
        self._assert_authorization_rejected(copy.deepcopy(self.authorization))

    def test_replace_rejected(self) -> None:
        self._assert_authorization_rejected(
            replace(self.authorization, metric_modification_authorized=True)
        )

    def test_self_rehash_does_not_create_authority(self) -> None:
        forged = replace(self.authorization, detector_authorized=True)
        self._assert_authorization_rejected(self._self_rehash(forged))

    def test_reconstructed_receipt_rejected(self) -> None:
        forged_receipt = replace(self.receipt)
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            subject.validate_inner_execution_custody_preflight_receipt_v1(forged_receipt)

    def test_receipt_self_rehash_rejected(self) -> None:
        forged = replace(self.receipt, private_paths_exposed=1)
        forged = replace(
            forged,
            custody_preflight_hash=stable_hash_v1(forged._payload()),
        )
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            subject.validate_inner_execution_custody_preflight_receipt_v1(forged)


if __name__ == "__main__":
    unittest.main()
