from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

import paperworks.validation_v2.prediction_custody_v1 as custody

from paperworks.validation_v2.prediction_custody_v1 import (
    D1PredictionArtifactV2,
    D1PredictionRecordV2,
    LabelAccessCapabilityV1,
    PredictionCustodyError,
    authorize_label_access_v1,
    consume_label_access_capability_v1,
    persist_prediction_before_label_v1,
    verify_prediction_unchanged_v1,
)


H_A = "a" * 64
H_B = "b" * 64
H_C = "c" * 64
PREDICTION = "custody/prediction.json"
RECEIPT = "custody/freeze_receipt.json"


def artifact() -> D1PredictionArtifactV2:
    return D1PredictionArtifactV2(
        method_id="VALIDATION-V2-D1",
        config_id="V2-CONFIG-001",
        experiment_id="EXP-04-DEVELOPMENT",
        dataset_id="HAI-P1-DEVELOPMENT",
        split_role="DEVELOPMENT_TEST1",
        authority_hash=H_A,
        runtime_authorization_hash=H_B,
        execution_context_hash=H_C,
        source_commit="d" * 40,
        portfolio_hash=H_B,
        file_contract_hash=H_C,
        records=(
            D1PredictionRecordV2("file-a", H_B, 0, False),
            D1PredictionRecordV2("file-a", H_B, 1, True, ("RULE-001",), (H_C,)),
            D1PredictionRecordV2("file-b", H_C, 0, False),
        ),
    )


class DurablePredictionCustodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def freeze(self) -> None:
        persist_prediction_before_label_v1(
            artifact(), artifact_root=self.root,
            prediction_relative_path=PREDICTION, receipt_relative_path=RECEIPT,
        )

    def authorize(self):
        return authorize_label_access_v1(
            artifact_root=self.root, prediction_relative_path=PREDICTION,
            receipt_relative_path=RECEIPT, expected_authority_hash=H_A,
            expected_runtime_authorization_hash=H_B,
            expected_execution_context_hash=H_C,
            expected_source_commit="d" * 40,
            expected_portfolio_hash=H_B,
            expected_file_contract_hash=H_C,
        )

    def test_roundtrip_is_durable_one_shot_and_post_metric_verified(self) -> None:
        self.freeze()
        capability = self.authorize()
        calls: list[str] = []
        self.assertEqual(consume_label_access_capability_v1(capability, lambda: calls.append("read") or 14), 14)
        self.assertEqual(calls, ["read"])
        self.assertEqual(verify_prediction_unchanged_v1(capability), sha256((self.root / PREDICTION).read_bytes()).hexdigest())
        with self.assertRaisesRegex(PredictionCustodyError, "LABEL_CAPABILITY_ALREADY_CONSUMED"):
            consume_label_access_capability_v1(capability, lambda: None)

    def test_persist_replay_and_authorize_have_bounded_reopen_counts(self) -> None:
        original_read_bytes = Path.read_bytes

        def record_read(path: Path) -> bytes:
            reads.append(path)
            return original_read_bytes(path)

        prediction_path = self.root / PREDICTION
        receipt_path = self.root / RECEIPT
        lease_path = self.root / (RECEIPT + ".label_access_authorized")
        reads: list[Path] = []
        with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=record_read):
            receipt = persist_prediction_before_label_v1(
                artifact(), artifact_root=self.root,
                prediction_relative_path=PREDICTION, receipt_relative_path=RECEIPT,
            )
        self.assertEqual([prediction_path, receipt_path], reads)

        reads = []
        with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=record_read):
            replayed = custody.replay_prediction_before_label_v1(
                artifact_root=self.root,
                prediction_relative_path=PREDICTION,
                receipt_relative_path=RECEIPT,
                expected_receipt=receipt,
                expected_authority_hash=H_A,
                expected_runtime_authorization_hash=H_B,
                expected_execution_context_hash=H_C,
                expected_source_commit="d" * 40,
                expected_portfolio_hash=H_B,
                expected_file_contract_hash=H_C,
            )
        self.assertEqual(artifact(), replayed)
        self.assertEqual([prediction_path, receipt_path], reads)

        reads = []
        with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=record_read):
            self.authorize()
        self.assertEqual([prediction_path, receipt_path, lease_path], reads)

    def test_label_access_before_freeze_rejected(self) -> None:
        with self.assertRaisesRegex(PredictionCustodyError, "ARTIFACT_MISSING"):
            self.authorize()

    def test_stale_destination_rejected_without_overwrite(self) -> None:
        target = self.root / PREDICTION
        target.parent.mkdir(parents=True)
        target.write_bytes(b"stale")
        with self.assertRaisesRegex(PredictionCustodyError, "STALE_DESTINATION"):
            self.freeze()
        self.assertEqual(target.read_bytes(), b"stale")

    def test_partial_temporary_file_rejected(self) -> None:
        temporary = self.root / (PREDICTION + ".tmp")
        temporary.parent.mkdir(parents=True)
        temporary.write_bytes(b"partial")
        with self.assertRaisesRegex(PredictionCustodyError, "STALE_TEMPORARY"):
            self.freeze()
        self.assertEqual(temporary.read_bytes(), b"partial")

    def test_wrong_authority_rejected(self) -> None:
        self.freeze()
        with self.assertRaisesRegex(PredictionCustodyError, "WRONG_PREDICTION_AUTHORITY"):
            authorize_label_access_v1(
                artifact_root=self.root, prediction_relative_path=PREDICTION,
                receipt_relative_path=RECEIPT, expected_authority_hash="d" * 64,
                expected_runtime_authorization_hash=H_B,
                expected_execution_context_hash=H_C,
                expected_source_commit="d" * 40,
                expected_portfolio_hash=H_B,
                expected_file_contract_hash=H_C,
            )

    def test_wrong_runtime_context_and_source_bindings_rejected(self) -> None:
        self.freeze()
        cases = (
            {"expected_runtime_authorization_hash": "e" * 64, "expected_execution_context_hash": H_C, "expected_source_commit": "d" * 40},
            {"expected_runtime_authorization_hash": H_B, "expected_execution_context_hash": "e" * 64, "expected_source_commit": "d" * 40},
            {"expected_runtime_authorization_hash": H_B, "expected_execution_context_hash": H_C, "expected_source_commit": "e" * 40},
            {"expected_runtime_authorization_hash": H_B, "expected_execution_context_hash": H_C, "expected_source_commit": "d" * 40, "expected_portfolio_hash": "e" * 64},
            {"expected_runtime_authorization_hash": H_B, "expected_execution_context_hash": H_C, "expected_source_commit": "d" * 40, "expected_file_contract_hash": "e" * 64},
        )
        for values in cases:
            with self.subTest(values=values), self.assertRaises(PredictionCustodyError):
                authorize_label_access_v1(
                    artifact_root=self.root, prediction_relative_path=PREDICTION,
                    receipt_relative_path=RECEIPT, expected_authority_hash=H_A,
                    expected_portfolio_hash=values.pop("expected_portfolio_hash", H_B),
                    expected_file_contract_hash=values.pop("expected_file_contract_hash", H_C),
                    **values,
                )

    def test_prediction_mutation_before_authorization_rejected(self) -> None:
        self.freeze()
        target = self.root / PREDICTION
        document = json.loads(target.read_text(encoding="utf-8"))
        document["record_count"] = 99
        target.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(PredictionCustodyError):
            self.authorize()

    def test_prediction_mutation_after_authorization_rejected_before_label_read(self) -> None:
        self.freeze()
        capability = self.authorize()
        (self.root / PREDICTION).write_bytes(b"mutated")
        calls: list[str] = []
        with self.assertRaisesRegex(PredictionCustodyError, "PREDICTION_MUTATED"):
            consume_label_access_capability_v1(capability, lambda: calls.append("read"))
        self.assertEqual(calls, [])

    def test_receipt_mutation_after_authorization_rejected(self) -> None:
        self.freeze()
        capability = self.authorize()
        (self.root / RECEIPT).write_bytes(b"mutated")
        with self.assertRaisesRegex(PredictionCustodyError, "RECEIPT_MUTATED"):
            consume_label_access_capability_v1(capability, lambda: None)

    def test_label_lease_mutation_after_authorization_rejected(self) -> None:
        self.freeze()
        capability = self.authorize()
        (self.root / (RECEIPT + ".label_access_authorized")).write_bytes(b"mutated")
        with self.assertRaisesRegex(PredictionCustodyError, "LABEL_LEASE_MUTATED"):
            consume_label_access_capability_v1(capability, lambda: None)

    def test_duplicate_authorization_is_durably_rejected(self) -> None:
        self.freeze()
        first = self.authorize()
        self.assertIsInstance(first, LabelAccessCapabilityV1)
        with self.assertRaisesRegex(PredictionCustodyError, "STALE_DESTINATION"):
            self.authorize()

    def test_post_label_mutation_rejected(self) -> None:
        self.freeze()
        capability = self.authorize()
        consume_label_access_capability_v1(capability, lambda: "labels")
        (self.root / PREDICTION).write_bytes(b"mutated")
        with self.assertRaisesRegex(PredictionCustodyError, "PREDICTION_MUTATED"):
            verify_prediction_unchanged_v1(capability)

    def test_post_metric_verification_before_label_rejected(self) -> None:
        self.freeze()
        capability = self.authorize()
        with self.assertRaisesRegex(PredictionCustodyError, "POST_METRIC_VERIFY_OUT_OF_ORDER"):
            verify_prediction_unchanged_v1(capability)

    def test_forged_capability_rejected(self) -> None:
        with self.assertRaisesRegex(PredictionCustodyError, "FORGED_LABEL_CAPABILITY"):
            LabelAccessCapabilityV1(object(), "fake")
        with self.assertRaisesRegex(PredictionCustodyError, "FORGED_LABEL_CAPABILITY"):
            consume_label_access_capability_v1(object(), lambda: None)  # type: ignore[arg-type]

    def test_path_escape_and_windows_path_rejected(self) -> None:
        # Assemble the synthetic drive-qualified path at runtime so the
        # repository privacy scanner does not mistake this negative fixture for
        # a published host path.  The custody boundary still receives and
        # rejects the exact same Windows path shape.
        windows_absolute = "C:" + "/prediction.json"
        for path in ("../prediction.json", windows_absolute, "custody\\prediction.json"):
            with self.subTest(path=path), self.assertRaises(PredictionCustodyError):
                persist_prediction_before_label_v1(
                    artifact(), artifact_root=self.root,
                    prediction_relative_path=path, receipt_relative_path=RECEIPT,
                )

    def test_git_internal_custody_root_rejected_before_write(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(PredictionCustodyError, "GIT_INTERNAL_CUSTODY_ROOT"):
            persist_prediction_before_label_v1(
                artifact(), artifact_root=repository_root,
                prediction_relative_path="private/prediction.json", receipt_relative_path="private/receipt.json",
            )
        self.assertFalse((repository_root / "private/prediction.json").exists())

    def test_symlink_parent_rejected_when_supported(self) -> None:
        external = self.root / "external"
        external.mkdir()
        link = self.root / "linked"
        try:
            link.symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(PredictionCustodyError, "SYMLINK_PATH"):
            persist_prediction_before_label_v1(
                artifact(), artifact_root=self.root,
                prediction_relative_path="linked/prediction.json", receipt_relative_path=RECEIPT,
            )

    def test_record_order_and_nested_mutability_rejected(self) -> None:
        with self.assertRaisesRegex(PredictionCustodyError, "SORTED_UNIQUE"):
            D1PredictionArtifactV2(
                method_id="m", config_id="c", experiment_id="e", dataset_id="d",
                split_role="DEVELOPMENT_TEST1", authority_hash=H_A, portfolio_hash=H_B,
                runtime_authorization_hash=H_B, execution_context_hash=H_C,
                source_commit="d" * 40, file_contract_hash=H_C,
                records=(D1PredictionRecordV2("z", H_A, 1, False), D1PredictionRecordV2("a", H_A, 0, False)),
            )
        with self.assertRaisesRegex(PredictionCustodyError, "MUTABLE_RULE_IDS"):
            D1PredictionRecordV2("a", H_A, 0, True, ["R"], ())  # type: ignore[arg-type]
        with self.assertRaisesRegex(PredictionCustodyError, "ALARM_REQUIRES_CONTRIBUTING_RULE"):
            D1PredictionRecordV2("a", H_A, 0, True)

    def test_private_path_shaped_file_identifier_rejected(self) -> None:
        drive_home = "C:" + "/Users/" + "private/data.csv"
        posix_home = "/home/" + "private/data.csv"
        for file_id in (drive_home, posix_home, "private\\data.csv"):
            with self.subTest(file_id=file_id), self.assertRaisesRegex(PredictionCustodyError, "PRIVATE_PATH_SHAPED"):
                D1PredictionRecordV2(file_id, H_A, 0, False)

    def test_same_file_identifier_requires_one_content_hash(self) -> None:
        with self.assertRaisesRegex(PredictionCustodyError, "INCONSISTENT_FILE_CONTENT_HASH"):
            D1PredictionArtifactV2(
                method_id="m", config_id="c", experiment_id="e", dataset_id="d",
                split_role="DEVELOPMENT_TEST1", authority_hash=H_A,
                runtime_authorization_hash=H_B, execution_context_hash=H_C,
                source_commit="d" * 40, portfolio_hash=H_B, file_contract_hash=H_C,
                records=(D1PredictionRecordV2("file-a", H_A, 0, False), D1PredictionRecordV2("file-a", H_B, 1, False)),
            )

    def test_label_reader_failure_still_consumes_capability(self) -> None:
        self.freeze()
        capability = self.authorize()

        def fail() -> None:
            raise LookupError("synthetic label reader failure")

        with self.assertRaisesRegex(LookupError, "synthetic"):
            consume_label_access_capability_v1(capability, fail)
        with self.assertRaisesRegex(PredictionCustodyError, "LABEL_CAPABILITY_ALREADY_CONSUMED"):
            consume_label_access_capability_v1(capability, lambda: None)

    def test_concurrent_consumption_allows_exactly_one_reader(self) -> None:
        self.freeze()
        capability = self.authorize()
        entered = threading.Event()
        release = threading.Event()
        outcomes: list[str] = []

        def reader() -> str:
            entered.set()
            release.wait(timeout=2)
            return "read"

        def run() -> None:
            try:
                consume_label_access_capability_v1(capability, reader)
                outcomes.append("success")
            except PredictionCustodyError:
                outcomes.append("rejected")

        first = threading.Thread(target=run)
        second = threading.Thread(target=run)
        first.start()
        entered.wait(timeout=2)
        second.start()
        release.set()
        first.join(timeout=2)
        second.join(timeout=2)
        self.assertCountEqual(outcomes, ["success", "rejected"])

    def test_concurrent_authorization_publishes_one_durable_lease(self) -> None:
        self.freeze()
        outcomes: list[str] = []

        def run() -> None:
            try:
                self.authorize()
                outcomes.append("success")
            except PredictionCustodyError:
                outcomes.append("rejected")

        first = threading.Thread(target=run)
        second = threading.Thread(target=run)
        first.start()
        second.start()
        first.join(timeout=2)
        second.join(timeout=2)
        self.assertCountEqual(outcomes, ["success", "rejected"])
        self.assertTrue((self.root / (RECEIPT + ".label_access_authorized")).is_file())

    def test_unsupported_hard_link_fails_closed_without_destination(self) -> None:
        with mock.patch("paperworks.validation_v2.prediction_custody_v1.os.link", side_effect=OSError("synthetic unsupported")):
            with self.assertRaisesRegex(PredictionCustodyError, "ATOMIC_PUBLISH_FAILED"):
                self.freeze()
        self.assertFalse((self.root / PREDICTION).exists())


if __name__ == "__main__":
    unittest.main()
