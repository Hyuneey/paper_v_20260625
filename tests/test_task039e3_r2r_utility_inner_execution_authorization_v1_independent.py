"""Independent adversarial audit of the INNER D1 authorization contract.

This suite uses only the synthetic custody-receipt factory.  It never calls
the real custody preflight, reads an environment locator, or opens any HAI or
label asset.  All invalid objects are independently rehashed before
validation so that a self-consistent digest cannot be mistaken for factory
issuance or current semantic authority.
"""

from __future__ import annotations

import copy
from dataclasses import fields, replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.v6 import (  # noqa: E402
    task039e3_r2r_utility_inner_execution_authorization_v1 as subject,
)


EXPECTED_SCOPE = "HAI_23_05_P1_TEST1_COMMON42_D1_RULE_ONLY_INNER_V1"
EXPECTED_DATASET_MANIFEST = (
    "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
)
EXPECTED_INNER_SPLIT = (
    "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
)
EXPECTED_FEATURE_SHA = (
    "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
)
EXPECTED_LABEL_SHA = (
    "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
)
EXPECTED_R3_IDENTITY = (
    "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"
)
EXPECTED_R3_AUDIT_RECEIPT = (
    "6f671aff17ea193ebf862af0739ee0bee22634f3f337944c14c90172acde34e0"
)
EXPECTED_MAIN_DESCRIPTOR = (
    "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
)
EXPECTED_MAIN_REGISTRY = (
    "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
)
EXPECTED_SUPPLEMENT_DESCRIPTOR = (
    "d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927"
)
EXPECTED_SUPPLEMENT_REGISTRY = (
    "12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf"
)
EXPECTED_COMBINED_CENSUS = (
    "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
)


def _independent_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _authorization_payload(
    authorization: subject.InnerExecutionAuthorizationV1,
) -> dict[str, object]:
    return {
        item.name: getattr(authorization, item.name)
        for item in fields(authorization)
        if not item.name.startswith("_") and item.name != "authorization_hash"
    }


def _receipt_payload(
    receipt: subject.InnerExecutionCustodyPreflightReceiptV1,
) -> dict[str, object]:
    return {
        item.name: getattr(receipt, item.name)
        for item in fields(receipt)
        if item.name != "custody_preflight_hash"
    }


def _rehash_authorization(
    authorization: subject.InnerExecutionAuthorizationV1,
) -> subject.InnerExecutionAuthorizationV1:
    return replace(
        authorization,
        authorization_hash=_independent_hash(_authorization_payload(authorization)),
    )


def _rehash_receipt(
    receipt: subject.InnerExecutionCustodyPreflightReceiptV1,
) -> subject.InnerExecutionCustodyPreflightReceiptV1:
    return replace(
        receipt,
        custody_preflight_hash=_independent_hash(_receipt_payload(receipt)),
    )


def _reconstruct(value: object) -> object:
    return type(value)(
        **{item.name: getattr(value, item.name) for item in fields(value)}
    )


class InnerExecutionAuthorizationV1IndependentAudit(unittest.TestCase):
    """Synthetic-only substitution, forgery, and escalation audit."""

    def setUp(self) -> None:
        self.receipt = (
            subject.build_synthetic_inner_execution_custody_preflight_receipt_v1()
        )
        self.authorization = subject.issue_inner_execution_authorization_v1(
            self.receipt
        )

    def _authorization_is_rejected(
        self,
        candidate: object,
        *,
        receipt: subject.InnerExecutionCustodyPreflightReceiptV1 | None = None,
    ) -> bool:
        try:
            subject.validate_inner_execution_authorization_v1(
                candidate,  # type: ignore[arg-type]
                self.receipt if receipt is None else receipt,
            )
        except subject.InnerExecutionAuthorizationV1Error:
            return True
        return False

    @staticmethod
    def _receipt_is_rejected(candidate: object) -> bool:
        try:
            subject.validate_inner_execution_custody_preflight_receipt_v1(
                candidate  # type: ignore[arg-type]
            )
        except subject.InnerExecutionAuthorizationV1Error:
            return True
        return False

    def test_positive_synthetic_contract_is_exact_and_non_authorizing(self) -> None:
        observed = subject.validate_inner_execution_authorization_v1(
            self.authorization,
            self.receipt,
        )
        self.assertEqual(observed, self.authorization.authorization_hash)
        self.assertEqual(
            self.authorization.authorization_hash,
            _independent_hash(_authorization_payload(self.authorization)),
        )
        self.assertEqual(
            self.receipt.custody_preflight_hash,
            _independent_hash(_receipt_payload(self.receipt)),
        )
        self.assertEqual(self.authorization.authorization_scope, EXPECTED_SCOPE)
        self.assertEqual(
            self.authorization.dataset_manifest_id, EXPECTED_DATASET_MANIFEST
        )
        self.assertEqual(self.authorization.inner_split_id, EXPECTED_INNER_SPLIT)
        self.assertEqual(self.authorization.feature_filename, "hai-test1.csv")
        self.assertEqual(self.authorization.feature_sha256, EXPECTED_FEATURE_SHA)
        self.assertEqual(self.authorization.label_filename, "label-test1.csv")
        self.assertEqual(self.authorization.label_sha256, EXPECTED_LABEL_SHA)
        self.assertEqual(
            self.authorization.r3_implementation_identity, EXPECTED_R3_IDENTITY
        )
        self.assertEqual(
            self.authorization.r3_independent_audit_receipt_hash,
            EXPECTED_R3_AUDIT_RECEIPT,
        )
        self.assertEqual(
            self.authorization.main_descriptor_hash, EXPECTED_MAIN_DESCRIPTOR
        )
        self.assertEqual(
            self.authorization.main_private_registry_expected_hash,
            EXPECTED_MAIN_REGISTRY,
        )
        self.assertEqual(
            self.authorization.supplement_descriptor_hash,
            EXPECTED_SUPPLEMENT_DESCRIPTOR,
        )
        self.assertEqual(
            self.authorization.supplement_private_registry_expected_hash,
            EXPECTED_SUPPLEMENT_REGISTRY,
        )
        self.assertEqual(
            self.authorization.combined_source_census_contract_hash,
            EXPECTED_COMBINED_CENSUS,
        )
        self.assertEqual(self.authorization.common_portfolio, "COMMON-42")
        self.assertEqual(self.authorization.common_relation_count, 42)
        self.assertEqual(self.authorization.experiment_arm, "D1")
        self.assertFalse(self.authorization.d0_authorized)
        self.assertFalse(self.authorization.d1_authorized)
        self.assertFalse(self.authorization.d2_authorized)
        self.assertFalse(self.authorization.t2_authorized)
        self.assertFalse(self.authorization.detector_authorized)
        self.assertFalse(self.authorization.outer_authorized)
        self.assertFalse(self.authorization.test2_authorized)
        self.assertFalse(self.authorization.fusion_authorized)
        self.assertFalse(self.authorization.threshold_recalibration_authorized)
        self.assertFalse(self.authorization.rule_regeneration_authorized)
        self.assertFalse(self.authorization.metric_modification_authorized)
        self.assertFalse(self.authorization.utility_inner_execution_authorized)
        self.assertFalse(
            self.authorization.utility_inner_d1_execution_authorization_issued
        )
        self.assertFalse(self.authorization.utility_inner_d1_executed)
        self.assertFalse(self.authorization.real_utility_execution_authorized)
        self.assertFalse(self.receipt.test2_touched)
        self.assertFalse(self.receipt.scientific_parsing_performed)
        self.assertEqual(self.receipt.real_utility_computations, 0)
        self.assertEqual(self.receipt.private_numeric_values_exposed, 0)
        self.assertEqual(self.receipt.private_paths_exposed, 0)

    def test_authorization_substitution_and_escalation_matrix_rejected(self) -> None:
        wrong = "0" * 64
        mutations: tuple[tuple[str, dict[str, object]], ...] = (
            ("scope", {"authorization_scope": "HAI_23_05_P1_TEST2"}),
            ("test2_feature", {"feature_filename": "hai-test2.csv"}),
            ("test2_label", {"label_filename": "label-test2.csv"}),
            ("test2_authority", {"test2_authorized": True}),
            ("outer", {"outer_authorized": True}),
            (
                "outer_ready",
                {"utility_outer_execution_authorization_ready": True},
            ),
            ("outer_issued", {"utility_outer_execution_authorized": True}),
            ("outer_split", {"inner_split_id": "OUTER"}),
            ("dataset", {"dataset_manifest_id": wrong}),
            ("d0_arm", {"experiment_arm": "D0"}),
            ("d0_grant", {"d0_authorized": True}),
            ("d2_arm", {"experiment_arm": "D2"}),
            ("d2_grant", {"d2_authorized": True}),
            ("t2_grant", {"t2_authorized": True}),
            ("d1_removed", {"experiment_arm": "NO_OP"}),
            ("detector", {"detector_authorized": True}),
            ("fusion", {"fusion_authorized": True}),
            (
                "recalibration",
                {"threshold_recalibration_authorized": True},
            ),
            ("rule_regeneration", {"rule_regeneration_authorized": True}),
            ("metric_change", {"metric_modification_authorized": True}),
            ("feature_hash", {"feature_sha256": wrong}),
            ("label_hash", {"label_sha256": wrong}),
            ("feature_asset", {"feature_filename": "hai-train1.csv"}),
            ("label_asset", {"label_filename": "label-train1.csv"}),
            ("r3_identity", {"r3_implementation_identity": wrong}),
            ("r3_audit", {"r3_independent_audit_receipt_hash": wrong}),
            ("r3_completion", {"r3_completion_audit_hash": wrong}),
            ("evaluator_bundle", {"evaluator_authority_bundle_hash": wrong}),
            ("v4", {"v4_authority_hash": wrong}),
            ("common_name", {"common_portfolio": "COMMON-41"}),
            ("common_count", {"common_relation_count": 41}),
            ("main_version", {"main_authority_version": "UNFROZEN"}),
            ("main_descriptor", {"main_descriptor_hash": wrong}),
            ("main_reference_set", {"main_reference_set_hash": wrong}),
            (
                "main_registry",
                {"main_private_registry_expected_hash": wrong},
            ),
            ("main_locator", {"main_locator_expected_hash": wrong}),
            (
                "supplement_version",
                {"supplement_authority_version": "UNFROZEN"},
            ),
            (
                "supplement_purpose",
                {"supplement_purpose": "RELATION_NUMERIC_AUTHORITY"},
            ),
            ("supplement_descriptor", {"supplement_descriptor_hash": wrong}),
            (
                "supplement_reference_set",
                {"supplement_reference_set_hash": wrong},
            ),
            (
                "supplement_registry",
                {"supplement_private_registry_expected_hash": wrong},
            ),
            ("supplement_locator", {"supplement_locator_expected_hash": wrong}),
            (
                "combined_census",
                {"combined_source_census_contract_hash": wrong},
            ),
            ("source_event_policy", {"source_census_event_policy_hash": wrong}),
            (
                "isolation_policy",
                {"cross_source_isolation_policy_hash": wrong},
            ),
            ("custody_receipt", {"custody_preflight_hash": wrong}),
            ("physical_range", {"expected_physical_range": (0, 54001)}),
            ("logical_range", {"expected_logical_range": (120, 54000)}),
            ("row_count", {"expected_physical_row_count": 53999}),
            ("purge", {"virtual_purge_seconds": 0}),
            ("utility_policy", {"utility_event_policy_hash": wrong}),
            ("metric_policy", {"metric_policy_hash": wrong}),
            (
                "real_mode",
                {"execution_mode": subject.FUTURE_INNER_D1_RULE_ONLY},
            ),
            ("pass_status", {"authorization_status": subject.PASS_STATUS}),
            (
                "inner_authorized",
                {"utility_inner_execution_authorized": True},
            ),
            (
                "inner_issued",
                {"utility_inner_d1_execution_authorization_issued": True},
            ),
            ("inner_executed", {"utility_inner_d1_executed": True}),
            ("real_utility", {"real_utility_execution_authorized": True}),
            (
                "audit_flag",
                {"utility_evaluator_v1_independently_audited": False},
            ),
            (
                "full_audit_flag",
                {"utility_evaluator_v1_full_independent_audit_completed": False},
            ),
        )
        accepted: list[str] = []
        for name, changes in mutations:
            with self.subTest(name=name):
                candidate = _rehash_authorization(
                    replace(self.authorization, **changes)
                )
                if not self._authorization_is_rejected(candidate):
                    accepted.append(name)
        self.assertEqual(len(mutations), 60)
        self.assertEqual(accepted, [], "accepted invalid authorization substitutions")

    def test_reconstructed_replaced_and_deepcopied_authorizations_rejected(self) -> None:
        candidates = {
            "exact_reconstruction": _reconstruct(self.authorization),
            "exact_replace": replace(self.authorization),
            "deepcopy": copy.deepcopy(self.authorization),
            "self_rehashed_reconstruction": _rehash_authorization(
                _reconstruct(self.authorization)  # type: ignore[arg-type]
            ),
        }
        accepted = [
            name
            for name, candidate in candidates.items()
            if not self._authorization_is_rejected(candidate)
        ]
        self.assertEqual(accepted, [], "accepted reconstructed authorization")

    def test_issued_authorization_tamper_and_self_rehash_rejected(self) -> None:
        receipt = (
            subject.build_synthetic_inner_execution_custody_preflight_receipt_v1()
        )
        authorization = subject.issue_inner_execution_authorization_v1(receipt)
        object.__setattr__(authorization, "detector_authorized", True)
        object.__setattr__(
            authorization,
            "authorization_hash",
            _independent_hash(_authorization_payload(authorization)),
        )
        self.assertTrue(
            self._authorization_is_rejected(authorization, receipt=receipt)
        )

    def test_forged_receipt_matrix_rejected_even_after_self_rehash(self) -> None:
        wrong = "0" * 64
        mutations: tuple[tuple[str, dict[str, object]], ...] = (
            ("scope", {"authorization_scope": "TEST2"}),
            ("mode", {"custody_mode": subject.REAL_CUSTODY_PREFLIGHT}),
            ("identity", {"sanitized_custody_identity": wrong}),
            ("main_locator_expected", {"main_locator_expected_hash": wrong}),
            ("main_locator_observed", {"main_locator_observed_hash": wrong}),
            ("main_locator_match", {"main_locator_hash_match": False}),
            ("main_registry_expected", {"main_registry_expected_hash": wrong}),
            ("main_registry_observed", {"main_registry_observed_hash": wrong}),
            ("main_registry_match", {"main_registry_hash_match": False}),
            (
                "supplement_locator_expected",
                {"supplement_locator_expected_hash": wrong},
            ),
            (
                "supplement_locator_observed",
                {"supplement_locator_observed_hash": wrong},
            ),
            (
                "supplement_locator_match",
                {"supplement_locator_hash_match": False},
            ),
            (
                "supplement_registry_expected",
                {"supplement_registry_expected_hash": wrong},
            ),
            (
                "supplement_registry_observed",
                {"supplement_registry_observed_hash": wrong},
            ),
            (
                "supplement_registry_match",
                {"supplement_registry_hash_match": False},
            ),
            ("feature_expected", {"test1_feature_expected_hash": wrong}),
            ("feature_observed", {"test1_feature_observed_hash": wrong}),
            ("feature_match", {"test1_feature_hash_match": False}),
            ("label_expected", {"test1_label_expected_hash": wrong}),
            ("label_observed", {"test1_label_observed_hash": wrong}),
            ("label_match", {"test1_label_hash_match": False}),
            ("main_locator_read", {"main_locator_reads": 1}),
            (
                "main_registry_read",
                {"main_registry_custody_validations": 1},
            ),
            ("supplement_locator_read", {"supplement_locator_reads": 1}),
            (
                "supplement_registry_read",
                {"supplement_registry_custody_validations": 1},
            ),
            ("feature_hash_pass", {"test1_feature_hash_passes": 1}),
            ("label_hash_pass", {"test1_label_hash_passes": 1}),
            ("test2", {"test2_touched": True}),
            ("parsing", {"scientific_parsing_performed": True}),
            ("feature_parse", {"scientific_feature_parse_count": 1}),
            ("label_parse", {"scientific_label_parse_count": 1}),
            ("attack_derivation", {"attack_event_derivation_count": 1}),
            ("rule_execution", {"rule_execution_count": 1}),
            ("metrics", {"metric_computation_count": 1}),
            ("detector", {"detector_execution_count": 1}),
            ("real_utility", {"real_utility_computations": 1}),
            ("private_value", {"private_numeric_values_exposed": 1}),
            ("private_path", {"private_paths_exposed": 1}),
        )
        accepted: list[str] = []
        for name, changes in mutations:
            with self.subTest(name=name):
                candidate = _rehash_receipt(replace(self.receipt, **changes))
                if not self._receipt_is_rejected(candidate):
                    accepted.append(name)
        self.assertEqual(len(mutations), 38)
        self.assertEqual(accepted, [], "accepted forged custody receipt")

    def test_reconstructed_replaced_deepcopied_and_swapped_receipts_rejected(self) -> None:
        candidates = {
            "exact_reconstruction": _reconstruct(self.receipt),
            "exact_replace": replace(self.receipt),
            "deepcopy": copy.deepcopy(self.receipt),
            "self_rehashed_reconstruction": _rehash_receipt(
                _reconstruct(self.receipt)  # type: ignore[arg-type]
            ),
        }
        accepted = [
            name
            for name, candidate in candidates.items()
            if not self._receipt_is_rejected(candidate)
        ]
        self.assertEqual(accepted, [], "accepted reconstructed custody receipt")

        other_receipt = (
            subject.build_synthetic_inner_execution_custody_preflight_receipt_v1()
        )
        self.assertTrue(
            self._authorization_is_rejected(
                self.authorization,
                receipt=other_receipt,
            )
        )

    def test_real_validation_rejects_synthetic_authorization(self) -> None:
        with self.assertRaises(subject.InnerExecutionAuthorizationV1Error):
            subject.validate_inner_execution_authorization_v1(
                self.authorization,
                self.receipt,
                require_real=True,
            )


if __name__ == "__main__":
    unittest.main()
