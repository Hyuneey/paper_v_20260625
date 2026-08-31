from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import paperworks.validation_v2.evaluation_custody_v1 as custody

from paperworks.validation_v2.evaluation_custody_v1 import (
    DenseBooleanPredictionArtifactV1,
    DenseBooleanPredictionRecordV1,
    EvaluationCustodyError,
    EvaluationCustodyStateV1,
    EvaluationLabelAccessCapabilityV1,
    HashOnlyEvaluationBundleFreezeReceiptV1,
    PredictionFreezeReferenceV1,
    authorize_evaluation_label_access_v1,
    consume_evaluation_label_access_v1,
    freeze_multi_method_evaluation_bundle_v1,
    persist_dense_prediction_before_label_v1,
    verify_evaluation_inputs_unchanged_v1,
)


H_A = "a" * 64
H_B = "b" * 64
H_C = "c" * 64
H_D = "d" * 64
COMMIT = "e" * 40
METHODS = ("VALIDATION-V2-D0", "VALIDATION-V2-D2-V1")
BUNDLE = "bundle/evaluation.json"
BUNDLE_RECEIPT = "bundle/evaluation.freeze.json"


def artifact(method_id: str, *, policy_hash: str = H_B) -> DenseBooleanPredictionArtifactV1:
    return DenseBooleanPredictionArtifactV1(
        artifact_id=f"{method_id}-PREDICTION",
        method_id=method_id,
        config_id=f"{method_id}-CONFIG",
        experiment_id="EXP-04-DEVELOPMENT",
        dataset_id="HAI-P1-DEVELOPMENT",
        split_role="DEVELOPMENT_TEST1",
        authority_hash=H_A,
        evaluation_policy_hash=policy_hash,
        metric_contract_hash=H_C,
        file_contract_hash=H_D,
        source_commit=COMMIT,
        records=(
            DenseBooleanPredictionRecordV1("test1-part-a", H_C, 0, False),
            DenseBooleanPredictionRecordV1("test1-part-a", H_C, 1, method_id.endswith("V1")),
            DenseBooleanPredictionRecordV1("test1-part-b", H_D, 0, True),
        ),
    )


class MultiMethodEvaluationCustodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def freeze_method(self, method_id: str, *, policy_hash: str = H_B) -> PredictionFreezeReferenceV1:
        prediction = f"methods/{method_id}/prediction.json"
        receipt_path = f"methods/{method_id}/prediction.freeze.json"
        receipt = persist_dense_prediction_before_label_v1(
            artifact(method_id, policy_hash=policy_hash),
            artifact_root=self.root,
            prediction_relative_path=prediction,
            receipt_relative_path=receipt_path,
        )
        return PredictionFreezeReferenceV1(method_id, prediction, receipt_path, receipt)

    def freeze_methods(self) -> tuple[PredictionFreezeReferenceV1, ...]:
        return tuple(self.freeze_method(method_id) for method_id in METHODS)

    def freeze_bundle(self, references: tuple[PredictionFreezeReferenceV1, ...]):
        return freeze_multi_method_evaluation_bundle_v1(
            artifact_root=self.root,
            bundle_id="EXP-04-EXACT-METHOD-BUNDLE",
            exact_method_ids=METHODS,
            prediction_references=references,
            evaluation_policy_hash=H_B,
            metric_contract_hash=H_C,
            source_commit=COMMIT,
            bundle_relative_path=BUNDLE,
            bundle_receipt_relative_path=BUNDLE_RECEIPT,
        )

    def authorize(self, references, bundle_receipt):
        return authorize_evaluation_label_access_v1(
            artifact_root=self.root,
            exact_method_ids=METHODS,
            prediction_references=references,
            evaluation_policy_hash=H_B,
            metric_contract_hash=H_C,
            source_commit=COMMIT,
            bundle_relative_path=BUNDLE,
            bundle_receipt_relative_path=BUNDLE_RECEIPT,
            expected_bundle_receipt=bundle_receipt,
        )

    def test_complete_roundtrip_is_one_shot_and_post_label_verified(self) -> None:
        references = self.freeze_methods()
        bundle_receipt = self.freeze_bundle(references)
        capability = self.authorize(references, bundle_receipt)
        reads: list[str] = []
        result = consume_evaluation_label_access_v1(capability, lambda: reads.append("labels") or 14)
        self.assertEqual(result, 14)
        self.assertEqual(reads, ["labels"])
        self.assertEqual(len(verify_evaluation_inputs_unchanged_v1(capability)), 7)
        with self.assertRaisesRegex(EvaluationCustodyError, "ALREADY_CONSUMED"):
            consume_evaluation_label_access_v1(capability, lambda: None)

    def test_prediction_is_dense_file_local_boolean_and_label_blind(self) -> None:
        document = artifact(METHODS[0]).to_document()
        self.assertTrue(document["label_blind"])
        self.assertEqual(document["sample_period_seconds"], 1)
        self.assertNotIn("label", document)
        self.assertTrue(all("label" not in record for record in document["records"]))
        with self.assertRaisesRegex(EvaluationCustodyError, "DENSE_FILE_LOCAL"):
            replace(
                artifact(METHODS[0]),
                records=(DenseBooleanPredictionRecordV1("file-a", H_A, 1, False),),
            )
        with self.assertRaisesRegex(EvaluationCustodyError, "INVALID_ALARM"):
            DenseBooleanPredictionRecordV1("file-a", H_A, 0, 1)  # type: ignore[arg-type]

    def test_public_receipts_are_hash_only_and_path_free(self) -> None:
        references = self.freeze_methods()
        bundle_receipt = self.freeze_bundle(references)
        documents = [reference.receipt.to_document() for reference in references]
        documents.append(bundle_receipt.to_document())
        for document in documents:
            serialized = json.dumps(document, sort_keys=True)
            self.assertNotIn("relative_path", serialized)
            self.assertNotIn(str(self.root), serialized)
            self.assertNotIn("methods/", serialized)
            self.assertNotIn("records", document)

        for private_shape in ("C:/private/prediction", "./prediction", "folder/prediction"):
            with self.subTest(private_shape=private_shape), self.assertRaises(EvaluationCustodyError):
                replace(artifact(METHODS[0]), artifact_id=private_shape)

    def test_no_overwrite_and_partial_temporary_files_fail_closed(self) -> None:
        reference = self.freeze_method(METHODS[0])
        before = (self.root / reference.prediction_relative_path).read_bytes()
        with self.assertRaisesRegex(EvaluationCustodyError, "STALE_DESTINATION"):
            persist_dense_prediction_before_label_v1(
                artifact(METHODS[0]), artifact_root=self.root,
                prediction_relative_path=reference.prediction_relative_path,
                receipt_relative_path="new-receipt.json",
            )
        self.assertEqual((self.root / reference.prediction_relative_path).read_bytes(), before)

        partial = self.root / "partial/prediction.json.tmp"
        partial.parent.mkdir()
        partial.write_bytes(b"partial")
        with self.assertRaisesRegex(EvaluationCustodyError, "STALE_TEMPORARY"):
            persist_dense_prediction_before_label_v1(
                artifact("OTHER"), artifact_root=self.root,
                prediction_relative_path="partial/prediction.json",
                receipt_relative_path="partial/receipt.json",
            )
        self.assertEqual(partial.read_bytes(), b"partial")

    def test_bundle_requires_exact_sorted_method_set_and_references(self) -> None:
        references = self.freeze_methods()
        with self.assertRaisesRegex(EvaluationCustodyError, "MISSING_OR_EXTRA"):
            freeze_multi_method_evaluation_bundle_v1(
                artifact_root=self.root, bundle_id="B", exact_method_ids=METHODS,
                prediction_references=references[:1], evaluation_policy_hash=H_B,
                metric_contract_hash=H_C, source_commit=COMMIT,
                bundle_relative_path=BUNDLE, bundle_receipt_relative_path=BUNDLE_RECEIPT,
            )
        with self.assertRaisesRegex(EvaluationCustodyError, "DUPLICATE_METHOD_REFERENCE"):
            freeze_multi_method_evaluation_bundle_v1(
                artifact_root=self.root, bundle_id="B", exact_method_ids=METHODS,
                prediction_references=(references[0], references[0]), evaluation_policy_hash=H_B,
                metric_contract_hash=H_C, source_commit=COMMIT,
                bundle_relative_path=BUNDLE, bundle_receipt_relative_path=BUNDLE_RECEIPT,
            )
        with self.assertRaisesRegex(EvaluationCustodyError, "SORTED_UNIQUE"):
            freeze_multi_method_evaluation_bundle_v1(
                artifact_root=self.root, bundle_id="B", exact_method_ids=tuple(reversed(METHODS)),
                prediction_references=references, evaluation_policy_hash=H_B,
                metric_contract_hash=H_C, source_commit=COMMIT,
                bundle_relative_path=BUNDLE, bundle_receipt_relative_path=BUNDLE_RECEIPT,
            )

    def test_wrong_policy_reference_rejected(self) -> None:
        references = (self.freeze_method(METHODS[0]), self.freeze_method(METHODS[1], policy_hash=H_D))
        with self.assertRaisesRegex(EvaluationCustodyError, "WRONG_EVALUATION_POLICY"):
            self.freeze_bundle(references)

    def test_stale_or_mutated_prediction_rejected_before_bundle_freeze(self) -> None:
        references = self.freeze_methods()
        target = self.root / references[0].prediction_relative_path
        target.write_bytes(b"mutated")
        with self.assertRaises(EvaluationCustodyError):
            self.freeze_bundle(references)

    def test_stale_receipt_object_reference_rejected(self) -> None:
        references = self.freeze_methods()
        forged = replace(references[0].receipt, alarm_count=references[0].receipt.alarm_count + 1)
        stale = PredictionFreezeReferenceV1(
            references[0].method_id, references[0].prediction_relative_path,
            references[0].receipt_relative_path, forged,
        )
        with self.assertRaisesRegex(EvaluationCustodyError, "STALE_OR_WRONG"):
            self.freeze_bundle((stale, references[1]))

    def test_self_consistent_false_prediction_receipt_is_rejected(self) -> None:
        reference = self.freeze_method(METHODS[0])
        document = reference.receipt.to_document()
        document.update({"publication_method": "NONE", "file_fsync": False, "state": "BUNDLE_FROZEN"})
        document["self_hash"] = custody._self_hash(document)
        with self.assertRaisesRegex(EvaluationCustodyError, "CUSTODY_STATE_INVALID"):
            custody._validate_prediction_receipt_document(document)

    def test_label_access_before_bundle_freeze_rejected(self) -> None:
        references = self.freeze_methods()
        (self.root / "bundle").mkdir()
        fake = HashOnlyEvaluationBundleFreezeReceiptV1(
            bundle_id="NOT-FROZEN", exact_method_ids=METHODS, bundle_bytes_sha256=H_A,
            bundle_self_hash=H_A, evaluation_policy_hash=H_B, metric_contract_hash=H_C,
            source_commit=COMMIT, prediction_receipt_hashes=(H_A, H_B),
            publication_method="NONE", file_fsync=False, directory_fsync="NONE",
            state=EvaluationCustodyStateV1.BUNDLE_FROZEN, self_hash=H_A,
        )
        with self.assertRaisesRegex(EvaluationCustodyError, "ARTIFACT_MISSING"):
            self.authorize(references, fake)

    def test_self_consistent_false_bundle_receipt_is_rejected(self) -> None:
        references = self.freeze_methods()
        receipt = self.freeze_bundle(references)
        document = receipt.to_document()
        document.update({"publication_method": "NONE", "file_fsync": False, "state": "REOPENED_AND_REPLAYED"})
        document["self_hash"] = custody._self_hash(document)
        with self.assertRaisesRegex(EvaluationCustodyError, "CUSTODY_STATE_INVALID"):
            custody._validate_bundle_receipt_document(document)

    def test_prediction_mutation_after_authorization_blocks_label_reader(self) -> None:
        references = self.freeze_methods()
        capability = self.authorize(references, self.freeze_bundle(references))
        (self.root / references[0].prediction_relative_path).write_bytes(b"mutated")
        reads: list[str] = []
        with self.assertRaisesRegex(EvaluationCustodyError, "PREDICTION_MUTATED"):
            consume_evaluation_label_access_v1(capability, lambda: reads.append("read"))
        self.assertEqual(reads, [])

    def test_bundle_mutation_after_label_is_detected(self) -> None:
        references = self.freeze_methods()
        capability = self.authorize(references, self.freeze_bundle(references))
        consume_evaluation_label_access_v1(capability, lambda: "labels")
        (self.root / BUNDLE).write_bytes(b"mutated")
        with self.assertRaisesRegex(EvaluationCustodyError, "BUNDLE_MUTATED"):
            verify_evaluation_inputs_unchanged_v1(capability)

    def test_label_reader_mutation_is_detected_in_finally(self) -> None:
        references = self.freeze_methods()
        capability = self.authorize(references, self.freeze_bundle(references))

        def mutating_reader() -> str:
            (self.root / BUNDLE_RECEIPT).write_bytes(b"mutated")
            return "labels"

        with self.assertRaisesRegex(EvaluationCustodyError, "BUNDLE_RECEIPT_MUTATED"):
            consume_evaluation_label_access_v1(capability, mutating_reader)

    def test_forged_capability_rejected(self) -> None:
        with self.assertRaisesRegex(EvaluationCustodyError, "FORGED_LABEL_CAPABILITY"):
            EvaluationLabelAccessCapabilityV1(object(), "forged")
        with self.assertRaisesRegex(EvaluationCustodyError, "FORGED_LABEL_CAPABILITY"):
            consume_evaluation_label_access_v1(object(), lambda: None)  # type: ignore[arg-type]

    def test_source_commit_and_authority_hashes_are_exact(self) -> None:
        with self.assertRaisesRegex(EvaluationCustodyError, "INVALID_SOURCE_COMMIT"):
            replace(artifact(METHODS[0]), source_commit="e" * 39)
        with self.assertRaisesRegex(EvaluationCustodyError, "INVALID_AUTHORITY_HASH"):
            replace(artifact(METHODS[0]), authority_hash="a" * 63)
        with self.assertRaisesRegex(EvaluationCustodyError, "INVALID_AUTHORITY_HASH"):
            replace(artifact(METHODS[0]), authority_hash="A" * 64)

    def test_path_escape_windows_paths_and_git_roots_are_rejected(self) -> None:
        for path in ("../prediction.json", "./prediction.json", "C:/prediction.json", "private\\prediction.json"):
            with self.subTest(path=path), self.assertRaises(EvaluationCustodyError):
                persist_dense_prediction_before_label_v1(
                    artifact(METHODS[0]), artifact_root=self.root,
                    prediction_relative_path=path, receipt_relative_path="receipt.json",
                )
        repository_root = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(EvaluationCustodyError, "GIT_INTERNAL_CUSTODY_ROOT"):
            persist_dense_prediction_before_label_v1(
                artifact(METHODS[0]), artifact_root=repository_root,
                prediction_relative_path="private/prediction.json", receipt_relative_path="private/receipt.json",
            )

    def test_symlink_parent_rejected_when_supported(self) -> None:
        external = self.root / "external"
        external.mkdir()
        link = self.root / "linked"
        try:
            link.symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(EvaluationCustodyError, "SYMLINK_PATH"):
            persist_dense_prediction_before_label_v1(
                artifact(METHODS[0]), artifact_root=self.root,
                prediction_relative_path="linked/prediction.json", receipt_relative_path="receipt.json",
            )

    def test_windows_junction_parent_is_rejected_before_resolution(self) -> None:
        linked = self.root / "linked"
        linked.mkdir()
        original = getattr(Path, "is_junction", None)
        if original is None:
            self.skipTest("Path.is_junction is unavailable")

        def fake_is_junction(path: Path) -> bool:
            return path.name == "linked"

        with mock.patch.object(Path, "is_junction", fake_is_junction):
            with self.assertRaisesRegex(EvaluationCustodyError, "LINKED_PARENT"):
                persist_dense_prediction_before_label_v1(
                    artifact(METHODS[0]), artifact_root=self.root,
                    prediction_relative_path="linked/prediction.json", receipt_relative_path="receipt.json",
                )

    def test_unsupported_atomic_publish_fails_closed(self) -> None:
        with mock.patch(
            "paperworks.validation_v2.evaluation_custody_v1.os.link",
            side_effect=OSError("synthetic unsupported"),
        ):
            with self.assertRaisesRegex(EvaluationCustodyError, "ATOMIC_PUBLISH_FAILED"):
                self.freeze_method(METHODS[0])
        self.assertFalse((self.root / f"methods/{METHODS[0]}/prediction.json").exists())


if __name__ == "__main__":
    unittest.main()
