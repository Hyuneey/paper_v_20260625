"""Independent R1 authority and process-local custody attacks.

The expected values below are frozen lower-authority oracles.  The tests do
not use implementation or remediation tests as an oracle and never resolve a
private locator or registry.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import gc
import json
from pathlib import Path
import pickle
import unittest
import weakref

import paperworks.v6.task039e3_r2r_utility_evaluator_authority_v1 as authority_module
import paperworks.v6.task039e3_r2r_utility_evaluator_v1 as evaluator_module
from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    UtilityEvaluatorV1Error,
    dataclass_payload_v1,
    stable_hash_v1,
)
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4


EXPECTED_V4_R1_AUTHORITY = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
EXPECTED_AUTHORITY_BUNDLE = "0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9"
EXPECTED_R1_IMPLEMENTATION = "64a6e7f0d210dc074bc85b0f389e61b45aaa512091532cf8f4d275ccaa35746a"
ORIGINAL_IMPLEMENTATION = "332e367cdc0da21b281c5de43f6a735d7dc68bc87efafe90976d89d7f9dc3330"
EXPECTED_MAIN_DESCRIPTOR = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
EXPECTED_MAIN_REFERENCE_SET = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
EXPECTED_SUPPLEMENT_DESCRIPTOR = "d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927"
EXPECTED_SUPPLEMENT_REFERENCE_SET = "5139cae6e454318f0ca4317f3f5eaa5f775bd4f75261c4110ea610815929b580"
EXPECTED_COMBINED_CENSUS = "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
EXPECTED_SOURCE_EVENT_POLICY = "3fb20068feff44632be3e4e6917183d52fea5616feec68ede5e9b62f95ecb390"
EXPECTED_ISOLATION_POLICY = "f62075523632a7573d28e95ca7f0402d87e62977f4a2f14f4eaf2b9a58f0e280"
EXPECTED_UTILITY_EVENT_POLICY = "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4"
EXPECTED_METRIC_POLICY = "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a"

# Audit-report metadata.  Positive factory and cleanup checks are not counted
# as invalid attacks.  Each class is a distinct authority/custody mechanism.
UNIQUE_SEMANTIC_ATTACK_CLASSES = 18
RAW_ADVERSARIAL_CASES = 18

_PUBLIC_INPUTS = {
    "executable_equivalence": "docs/task_reports/TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json",
    "evidence_manifest": "docs/task_reports/TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
    "dataset_manifest": "docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json",
    "csv_structure_report": "docs/task_reports/TASK-039A_CSV_STRUCTURE_REPORT.json",
    "c0_config": "configs/v6/task039c0_candidate_discovery_protocol.json",
    "br2_config": "configs/v6/task039br2_hai_continuous_step_feasibility.json",
    "materialized_audit_receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json",
}


def _load_current_v4_authority() -> v4.UtilityProtocolV4CanonicalAuthority:
    root = Path(__file__).resolve().parents[1]
    documents = {
        name: json.loads((root / relative).read_text(encoding="utf-8"))
        for name, relative in _PUBLIC_INPUTS.items()
    }
    result = v4.build_utility_protocol_v4_canonical_authority(**documents)
    if result.authority_hash != EXPECTED_V4_R1_AUTHORITY:
        raise AssertionError("lower public authorities did not replay V4 R1")
    return result


def _reconstruct(value: object) -> object:
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


class UtilityEvaluatorV1R1IndependentAuthorityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4_authority = _load_current_v4_authority()

    def _bundle(self) -> authority_module.EvaluatorAuthorityBundleV1:
        return authority_module.build_evaluator_authority_bundle_v1(self.v4_authority)

    def _implementation(
        self, bundle: authority_module.EvaluatorAuthorityBundleV1
    ) -> evaluator_module.EvaluatorImplementationAuthorityV1:
        return evaluator_module.build_evaluator_implementation_authority_v1(bundle)

    def assertBundleRejected(self, candidate: object) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            authority_module.validate_evaluator_authority_bundle_v1(candidate)  # type: ignore[arg-type]

    def assertImplementationRejected(
        self,
        candidate: object,
        bundle: authority_module.EvaluatorAuthorityBundleV1,
    ) -> None:  # noqa: N802
        with self.assertRaises(UtilityEvaluatorV1Error):
            evaluator_module.validate_evaluator_implementation_authority_v1(  # type: ignore[arg-type]
                candidate, bundle
            )

    def test_lower_authority_replay_and_factory_issuance(self) -> None:
        bundle = self._bundle()
        self.assertEqual(EXPECTED_AUTHORITY_BUNDLE, bundle.bundle_hash)
        self.assertEqual(EXPECTED_V4_R1_AUTHORITY, bundle.v4_authority_hash)
        self.assertEqual("COMMON-42", bundle.common_portfolio)
        self.assertEqual(42, bundle.common_relation_count)
        self.assertIs(bundle.t2_utility_authorized, False)
        self.assertEqual(EXPECTED_MAIN_DESCRIPTOR, bundle.main_descriptor_hash)
        self.assertEqual(EXPECTED_MAIN_REFERENCE_SET, bundle.main_reference_set_hash)
        self.assertEqual(EXPECTED_SUPPLEMENT_DESCRIPTOR, bundle.supplement_descriptor_hash)
        self.assertEqual(EXPECTED_SUPPLEMENT_REFERENCE_SET, bundle.supplement_reference_set_hash)
        self.assertEqual(EXPECTED_COMBINED_CENSUS, bundle.combined_source_census_contract_hash)
        self.assertEqual(EXPECTED_SOURCE_EVENT_POLICY, bundle.source_census_event_policy_hash)
        self.assertEqual(EXPECTED_ISOLATION_POLICY, bundle.cross_source_isolation_policy_hash)
        self.assertEqual(EXPECTED_UTILITY_EVENT_POLICY, bundle.utility_event_aggregation_policy_hash)
        self.assertEqual(EXPECTED_METRIC_POLICY, bundle.metric_policy_hash)
        self.assertEqual((9, 3, 12), (len(bundle.main_sources), len(bundle.supplement_sources), len(bundle.evaluator_source_census)))
        self.assertEqual(EXPECTED_AUTHORITY_BUNDLE, authority_module.validate_evaluator_authority_bundle_v1(bundle))

        implementation = self._implementation(bundle)
        self.assertEqual("R1", implementation.control_revision)
        self.assertEqual(EXPECTED_R1_IMPLEMENTATION, implementation.implementation_identity)
        self.assertNotEqual(ORIGINAL_IMPLEMENTATION, implementation.implementation_identity)
        self.assertEqual(
            EXPECTED_R1_IMPLEMENTATION,
            evaluator_module.validate_evaluator_implementation_authority_v1(
                implementation, bundle
            ),
        )

    def test_multiple_independent_factory_issuances_are_each_authentic(self) -> None:
        first_bundle = self._bundle()
        second_bundle = self._bundle()
        self.assertIsNot(first_bundle, second_bundle)
        self.assertEqual(first_bundle, second_bundle)
        self.assertEqual(EXPECTED_AUTHORITY_BUNDLE, authority_module.validate_evaluator_authority_bundle_v1(first_bundle))
        self.assertEqual(EXPECTED_AUTHORITY_BUNDLE, authority_module.validate_evaluator_authority_bundle_v1(second_bundle))

        first_implementation = self._implementation(first_bundle)
        second_implementation = self._implementation(second_bundle)
        self.assertIsNot(first_implementation, second_implementation)
        self.assertEqual(first_implementation, second_implementation)
        self.assertEqual(EXPECTED_R1_IMPLEMENTATION, evaluator_module.validate_evaluator_implementation_authority_v1(first_implementation, first_bundle))
        self.assertEqual(EXPECTED_R1_IMPLEMENTATION, evaluator_module.validate_evaluator_implementation_authority_v1(second_implementation, second_bundle))

    def test_bundle_caller_reconstruction_mechanisms_reject(self) -> None:
        issued = self._bundle()
        candidates = {
            "direct_exact_reconstruction": _reconstruct(issued),
            "deepcopy": deepcopy(issued),
            "no_op_replace": replace(issued),
            "modified_replace": replace(issued, main_descriptor_hash="0" * 64),
            "serialized_round_trip": pickle.loads(pickle.dumps(issued)),
        }
        for name, candidate in candidates.items():
            with self.subTest(name=name):
                self.assertBundleRejected(candidate)

    def test_bundle_registry_requires_exact_object_hash_and_semantics(self) -> None:
        issued = self._bundle()

        # A registry entry referring to a different authentic object is not
        # custody for a value-identical reconstruction.
        reconstructed = _reconstruct(issued)
        reconstructed_key = id(reconstructed)
        authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[reconstructed_key] = (  # type: ignore[attr-defined]
            weakref.ref(issued),
            reconstructed.bundle_hash,
        )
        try:
            self.assertBundleRejected(reconstructed)
        finally:
            authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(reconstructed_key, None)  # type: ignore[attr-defined]

        # The issuance-time hash remains part of custody.
        issued_key = id(issued)
        saved = authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[issued_key]  # type: ignore[attr-defined]
        authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[issued_key] = (saved[0], "f" * 64)  # type: ignore[attr-defined]
        try:
            self.assertBundleRejected(issued)
        finally:
            authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[issued_key] = saved  # type: ignore[attr-defined]

        # Even a forged exact-object issuance entry cannot override lower
        # semantic replay.
        mutated = replace(issued, metric_policy_hash="e" * 64)
        mutated_key = id(mutated)
        authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES[mutated_key] = (  # type: ignore[attr-defined]
            weakref.ref(mutated),
            mutated.bundle_hash,
        )
        try:
            self.assertBundleRejected(mutated)
        finally:
            authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(mutated_key, None)  # type: ignore[attr-defined]

    def test_bundle_weakref_cleanup_removes_stale_issuance(self) -> None:
        issued = self._bundle()
        issued_key = id(issued)
        issued_ref = weakref.ref(issued)
        self.assertIn(issued_key, authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)  # type: ignore[attr-defined]
        del issued
        gc.collect()
        self.assertIsNone(issued_ref())
        self.assertNotIn(issued_key, authority_module._ISSUED_EVALUATOR_AUTHORITY_BUNDLES)  # type: ignore[attr-defined]

    def test_implementation_caller_reconstruction_and_old_identity_reject(self) -> None:
        bundle = self._bundle()
        issued = self._implementation(bundle)

        wrong_revision = replace(issued, control_revision="R0", implementation_identity="")
        wrong_revision = replace(
            wrong_revision,
            implementation_identity=stable_hash_v1(
                dataclass_payload_v1(wrong_revision, exclude=("implementation_identity",))
            ),
        )
        candidates = {
            "direct_exact_reconstruction": _reconstruct(issued),
            "deepcopy": deepcopy(issued),
            "no_op_replace": replace(issued),
            "serialized_round_trip": pickle.loads(pickle.dumps(issued)),
            "old_implementation_identity": replace(
                issued, implementation_identity=ORIGINAL_IMPLEMENTATION
            ),
            "wrong_revision_self_rehash": wrong_revision,
        }
        for name, candidate in candidates.items():
            with self.subTest(name=name):
                self.assertImplementationRejected(candidate, bundle)

    def test_implementation_registry_requires_exact_object_hash_and_semantics(self) -> None:
        bundle = self._bundle()
        issued = self._implementation(bundle)

        reconstructed = _reconstruct(issued)
        reconstructed_key = id(reconstructed)
        evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[  # type: ignore[attr-defined]
            reconstructed_key
        ] = (
            weakref.ref(issued),
            reconstructed.implementation_identity,
            reconstructed.evaluator_authority_bundle_hash,
        )
        try:
            self.assertImplementationRejected(reconstructed, bundle)
        finally:
            evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES.pop(  # type: ignore[attr-defined]
                reconstructed_key, None
            )

        issued_key = id(issued)
        saved = evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[issued_key]  # type: ignore[attr-defined]
        evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[issued_key] = (  # type: ignore[attr-defined]
            saved[0], "f" * 64, saved[2]
        )
        try:
            self.assertImplementationRejected(issued, bundle)
        finally:
            evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[issued_key] = saved  # type: ignore[attr-defined]

        mutated = replace(issued, control_revision="RX", implementation_identity="")
        mutated = replace(
            mutated,
            implementation_identity=stable_hash_v1(
                dataclass_payload_v1(mutated, exclude=("implementation_identity",))
            ),
        )
        mutated_key = id(mutated)
        evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES[mutated_key] = (  # type: ignore[attr-defined]
            weakref.ref(mutated),
            mutated.implementation_identity,
            mutated.evaluator_authority_bundle_hash,
        )
        try:
            self.assertImplementationRejected(mutated, bundle)
        finally:
            evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES.pop(  # type: ignore[attr-defined]
                mutated_key, None
            )

    def test_implementation_weakref_cleanup_and_stale_bundle_reject(self) -> None:
        bundle = self._bundle()
        issued = self._implementation(bundle)
        issued_key = id(issued)
        issued_ref = weakref.ref(issued)
        self.assertIn(issued_key, evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES)  # type: ignore[attr-defined]
        del issued
        gc.collect()
        self.assertIsNone(issued_ref())
        self.assertNotIn(issued_key, evaluator_module._ISSUED_EVALUATOR_IMPLEMENTATION_AUTHORITIES)  # type: ignore[attr-defined]

        current = self._implementation(bundle)
        caller_bundle = _reconstruct(bundle)
        self.assertImplementationRejected(current, caller_bundle)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
