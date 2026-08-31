from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.validation_v2 import exp05_custody_v1 as custody
from paperworks.validation_v2 import exp05_runner_v1 as runner
from paperworks.validation_v2.runtime_v1 import FormalV4ObservationWindowV1
from paperworks.validation_v2.schema_registry_v1 import validate_validation_v2_document_v1
from tests.test_validation_v2_formal_v4_authority_v1 import V2Fixture


def h(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class Exp05CustodyV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = V2Fixture()
        descriptor = self.fx.descriptors[0]
        self.authorization = runner.authorize_exp05_execution_v1(
            execution_scope="SYNTHETIC_CONFORMANCE",
            preregistration_hash=h("exp05-preregistration"),
            source_commit=self.fx.commit,
            bundle=self.fx.bundle,
        )
        first = FormalV4ObservationWindowV1(
            opportunity_id="OP-EXP05-001", relation_id=descriptor.relation_id,
            feature_contract_hash=self.fx.feature_binding.content_sha256,
            file_contract_hash=self.fx.file_binding.content_sha256,
            sampling_contract_hash=self.fx.sampling_binding.content_sha256,
            event_index=100, target_response_start_index=105,
            source_pre_values=(0.0, 0.0), source_post_values=(2.0, 2.0),
            target_baseline_values=(10.0, 10.0), target_response_values=(11.0, 11.0),
            seconds_since_previous_source_trigger=None,
            seconds_to_nearest_other_source_trigger=None,
            future_window_complete=True,
        )
        second = replace(
            first, opportunity_id="OP-EXP05-002", event_index=200,
            target_response_start_index=205, target_response_values=(9.0, 9.0),
        )
        self.units = tuple(
            runner.execute_and_materialize_formal_v4_rule_v1(
                self.fx.bundle, authorization=self.authorization,
                execution_context=self.fx.context, repository_root=self.fx.root, window=window,
            )
            for window in (first, second)
        )
        self.manifest = custody.build_exp05_opportunity_manifest_v1(tuple(
            custody.Exp05OpportunityManifestEntryV1(
                unit.materialized_trace.opportunity_id, unit.materialized_trace.relation_id,
            )
            for unit in self.units
        ))
        self.unit_directory = TemporaryDirectory()
        self.unit_root = Path(self.unit_directory.name).resolve()
        self.full_receipts = tuple(
            custody.persist_exp05_full_evaluated_unit_v1(
                unit,
                artifact_path=self.unit_root / f"unit-{index}.private.json",
                receipt_path=self.unit_root / f"unit-{index}.receipt.json",
            )
            for index, unit in enumerate(self.units)
        )

    def tearDown(self) -> None:
        self.unit_directory.cleanup()
        self.fx.close()

    def bundle(self):
        return custody.build_exp05_evaluated_cohort_bundle_v1(
            cohort_id="EXP05-SYNTHETIC-COHORT",
            preregistration_hash=self.authorization.preregistration_hash,
            opportunity_manifest=self.manifest,
            d1_native_outcome_binding_hash=h("d1-native-outcomes"),
            units=self.units, full_unit_receipts=self.full_receipts,
        )

    def test_exact_manifest_requires_every_unit_once_in_stable_order(self) -> None:
        bundle = self.bundle()
        validate_validation_v2_document_v1(
            "exp05_evaluated_cohort_bundle_v1.schema.json", bundle.to_dict(),
        )
        self.assertEqual(2, bundle.opportunity_count)
        self.assertEqual(
            ("OP-EXP05-001", "OP-EXP05-002"),
            tuple(item.opportunity_id for item in bundle.evaluated_units),
        )
        with self.assertRaisesRegex(custody.Exp05CustodyError, "INCOMPLETE_OR_ORPHANED"):
            custody.build_exp05_evaluated_cohort_bundle_v1(
                cohort_id="EXP05-SYNTHETIC-COHORT",
                preregistration_hash=self.authorization.preregistration_hash,
                opportunity_manifest=self.manifest,
                d1_native_outcome_binding_hash=h("d1-native-outcomes"), units=self.units[:1],
                full_unit_receipts=self.full_receipts[:1],
            )
        with self.assertRaises(custody.Exp05CustodyError):
            custody.build_exp05_evaluated_cohort_bundle_v1(
                cohort_id="EXP05-SYNTHETIC-COHORT",
                preregistration_hash=self.authorization.preregistration_hash,
                opportunity_manifest=self.manifest,
                d1_native_outcome_binding_hash=h("d1-native-outcomes"), units=self.units[::-1],
                full_unit_receipts=self.full_receipts,
            )
        with self.assertRaises(custody.Exp05CustodyError):
            custody.build_exp05_evaluated_cohort_bundle_v1(
                cohort_id="EXP05-SYNTHETIC-COHORT",
                preregistration_hash=self.authorization.preregistration_hash,
                opportunity_manifest=self.manifest,
                d1_native_outcome_binding_hash=h("d1-native-outcomes"), units=(self.units[0], self.units[0]),
                full_unit_receipts=self.full_receipts,
            )

    def test_cross_trace_substitution_is_rejected(self) -> None:
        forged = replace(
            self.units[0],
            explanation=replace(
                self.units[0].explanation,
                materialized_trace_hash=self.units[1].materialized_trace.self_hash,
            ),
        )
        with self.assertRaises(runner.Exp05RunnerError):
            custody.build_exp05_evaluated_cohort_bundle_v1(
                cohort_id="EXP05-SYNTHETIC-COHORT",
                preregistration_hash=self.authorization.preregistration_hash,
                opportunity_manifest=self.manifest,
                d1_native_outcome_binding_hash=h("d1-native-outcomes"),
                units=(forged, self.units[1]),
                full_unit_receipts=self.full_receipts,
            )

    def test_forged_label_access_cannot_be_hidden_by_cohort_safety_fields(self) -> None:
        original = self.units[0]
        changed = replace(
            original.materialization_receipt,
            labels_accessed=True,
            receipt_hash="0" * 64,
        )
        changed = replace(changed, receipt_hash=runner.canonical_document_hash_v1(changed.payload()))
        forged = replace(original, materialization_receipt=changed, unit_hash="0" * 64)
        forged = replace(forged, unit_hash=runner.canonical_document_hash_v1(forged.payload()))
        with self.assertRaisesRegex(runner.Exp05RunnerError, "RECEIPT_BINDING_MISMATCH"):
            custody.build_exp05_evaluated_cohort_bundle_v1(
                cohort_id="EXP05-SYNTHETIC-COHORT",
                preregistration_hash=self.authorization.preregistration_hash,
                opportunity_manifest=self.manifest,
                d1_native_outcome_binding_hash=h("d1-native-outcomes"),
                units=(forged, self.units[1]),
                full_unit_receipts=self.full_receipts,
            )

    def test_persist_reopen_replay_is_path_free_and_public_safe(self) -> None:
        bundle = self.bundle()
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            bundle_path = root / "cohort.private.json"
            receipt_path = root / "cohort.receipt.json"
            receipt = custody.persist_exp05_evaluated_bundle_v1(
                bundle, bundle_path=bundle_path, receipt_path=receipt_path,
            )
            replay = custody.replay_exp05_evaluated_bundle_v1(
                bundle_path=bundle_path, receipt_path=receipt_path, expected_receipt=receipt,
            )
            self.assertEqual(bundle, replay)
            public = receipt_path.read_text(encoding="utf-8")
            private = bundle_path.read_text(encoding="utf-8")
            self.assertNotIn(str(root), public)
            self.assertNotIn("source_pre_values", private)
            self.assertNotIn("target_response_values", private)
            self.assertNotIn("explanation_text", private)

    def test_full_unit_persist_reopen_replays_the_actual_artifacts(self) -> None:
        unit = self.units[0]
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            artifact_path = root / "unit.private.json"
            receipt_path = root / "unit.receipt.json"
            receipt = custody.persist_exp05_full_evaluated_unit_v1(
                unit, artifact_path=artifact_path, receipt_path=receipt_path,
            )
            replay = custody.replay_exp05_full_evaluated_unit_v1(
                artifact_path=artifact_path, receipt_path=receipt_path,
                expected_receipt=receipt,
            )
            self.assertEqual(unit, replay)
            private = artifact_path.read_text(encoding="utf-8")
            private_document = json.loads(private)
            public = receipt_path.read_text(encoding="utf-8")
            validate_validation_v2_document_v1(
                "exp05_full_evaluated_unit_v1.schema.json", private_document,
            )
            validate_validation_v2_document_v1(
                "exp05_full_unit_freeze_receipt_v1.schema.json", receipt.to_dict(),
            )
            self.assertEqual(
                unit.explanation.natural_language_text,
                private_document["explanation"]["natural_language_text"],
            )
            self.assertNotIn("source_pre_values", private)
            self.assertNotIn("target_response_values", private)
            self.assertNotIn(str(root), public)

    def test_closed_cohort_schema_rejects_malformed_nested_references_and_strata(self) -> None:
        document = self.bundle().to_dict()
        document["evaluated_units"][0]["foreign_field"] = "not-authorized"
        with self.assertRaisesRegex(Exception, "extra fields"):
            validate_validation_v2_document_v1(
                "exp05_evaluated_cohort_bundle_v1.schema.json", document,
            )
        document = self.bundle().to_dict()
        document["outcome_reason_strata"] = {"UNKNOWN:reason": 1}
        with self.assertRaisesRegex(Exception, "pattern differs"):
            validate_validation_v2_document_v1(
                "exp05_evaluated_cohort_bundle_v1.schema.json", document,
            )
        document = self.bundle().to_dict()
        document["outcome_reason_strata"] = {"PASS:reason": 0}
        with self.assertRaisesRegex(Exception, "below minimum"):
            validate_validation_v2_document_v1(
                "exp05_evaluated_cohort_bundle_v1.schema.json", document,
            )

    def test_verified_replay_repopulates_custody_proof_after_process_restart(self) -> None:
        custody._PUBLISHED_FULL_UNITS.clear()
        with self.assertRaisesRegex(custody.Exp05CustodyError, "NOT_PERSISTED"):
            self.bundle()
        for index, (unit, receipt) in enumerate(zip(self.units, self.full_receipts, strict=True)):
            replayed = custody.replay_exp05_full_evaluated_unit_v1(
                artifact_path=self.unit_root / f"unit-{index}.private.json",
                receipt_path=self.unit_root / f"unit-{index}.receipt.json",
                expected_receipt=receipt,
            )
            self.assertEqual(unit, replayed)
        self.assertEqual(2, self.bundle().opportunity_count)

    def test_full_unit_nested_mutation_partial_write_and_overwrite_fail_closed(self) -> None:
        unit = self.units[0]
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            artifact_path = root / "unit.private.json"
            receipt_path = root / "unit.receipt.json"
            receipt = custody.persist_exp05_full_evaluated_unit_v1(
                unit, artifact_path=artifact_path, receipt_path=receipt_path,
            )
            with self.assertRaises(custody.Exp05CustodyError):
                custody.persist_exp05_full_evaluated_unit_v1(
                    unit, artifact_path=artifact_path, receipt_path=receipt_path,
                )
            document = json.loads(artifact_path.read_text(encoding="utf-8"))
            document["explanation"]["natural_language_text"] += " altered"
            artifact_path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises((custody.Exp05CustodyError, runner.Exp05RunnerError)):
                custody.replay_exp05_full_evaluated_unit_v1(
                    artifact_path=artifact_path, receipt_path=receipt_path,
                    expected_receipt=receipt,
                )
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            artifact_path = root / "partial.private.json"
            receipt_path = root / "partial.receipt.json"
            artifact_path.write_bytes(b'{"partial":true}')
            receipt_path.write_bytes(b'{"partial":true}')
            with self.assertRaises(custody.Exp05CustodyError):
                custody.replay_exp05_full_evaluated_unit_v1(
                    artifact_path=artifact_path, receipt_path=receipt_path,
                    expected_receipt=replace(
                        custody.FullExp05UnitFreezeReceiptV1(
                            opportunity_id="x", relation_id="r", unit_hash=h("u"),
                            artifact_file_sha256=h("a"), byte_count=1,
                            publication_method="NO_OVERWRITE_LINK_PUBLISH", file_fsync=True,
                            directory_fsync="UNSUPPORTED_WINDOWS", reopened_bytes_match=True,
                        ), receipt_hash=h("receipt"),
                    ),
                )

    def test_overwrite_partial_and_post_freeze_mutation_fail_closed(self) -> None:
        bundle = self.bundle()
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            bundle_path = root / "cohort.private.json"
            receipt_path = root / "cohort.receipt.json"
            receipt = custody.persist_exp05_evaluated_bundle_v1(
                bundle, bundle_path=bundle_path, receipt_path=receipt_path,
            )
            with self.assertRaises(custody.Exp05CustodyError):
                custody.persist_exp05_evaluated_bundle_v1(
                    bundle, bundle_path=bundle_path, receipt_path=receipt_path,
                )
            document = json.loads(bundle_path.read_text(encoding="utf-8"))
            document["opportunity_count"] = 1
            bundle_path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(custody.Exp05CustodyError):
                custody.replay_exp05_evaluated_bundle_v1(
                    bundle_path=bundle_path, receipt_path=receipt_path, expected_receipt=receipt,
                )
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            bundle_path = root / "partial.private.json"
            receipt_path = root / "partial.receipt.json"
            bundle_path.write_bytes(b"{\"partial\":true}")
            receipt_path.write_bytes(b"{\"partial\":true}")
            with self.assertRaises(custody.Exp05CustodyError):
                custody.replay_exp05_evaluated_bundle_v1(
                    bundle_path=bundle_path, receipt_path=receipt_path,
                    expected_receipt=replace(
                        custody.HashOnlyExp05BundleFreezeReceiptV1(
                            cohort_id="x", bundle_hash=h("b"), bundle_file_sha256=h("f"),
                            opportunity_manifest_hash=h("m"), d1_native_outcome_binding_hash=h("d"),
                            unit_count=1, byte_count=1, publication_method="NO_OVERWRITE_LINK_PUBLISH",
                            file_fsync=True, directory_fsync="UNSUPPORTED_WINDOWS", reopened_bytes_match=True,
                        ), receipt_hash=h("receipt"),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
