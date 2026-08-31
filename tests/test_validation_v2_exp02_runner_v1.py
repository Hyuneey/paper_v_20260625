from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.exp02_runner_v1 import (
    EXP02_REQUIRED_BINDING_IDS,
    Exp02RunnerError,
    atomic_persist_selected_policy_v1,
    build_cohort_projection_receipt_v1,
    build_frozen_scientific_binding_v1,
    close_exact_candidate_set_v1,
    execute_authorized_split_open_v1,
    frozen_scientific_binding_from_dict_v1,
    start_split_open_ledger_v1,
    validate_cohort_projection_receipt_v1,
    validate_scientific_binding_bundle_v1,
)
from paperworks.validation_v2.exp02_scientific_v1 import (
    Exp02OperationV1,
    build_private_summary_hash_receipt_v1,
    build_v2_confirmed_cohort_binding_v1,
)
from paperworks.validation_v2.numeric_policy_v1 import (
    ConfirmedRelationIdentityV1,
    build_confirmed_cohort_authority_v1,
)


COMMIT = "1" * 40


def h(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


class Exp02RunnerV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.bindings = tuple(
            build_frozen_scientific_binding_v1(
                binding_id=binding_id,
                contract_id=f"contract-{index}",
                specification_hash=h(f"spec-{index}"),
                implementation_hash=h(f"impl-{index}"),
                configuration_hash=h(f"config-{index}"),
                source_commit=COMMIT,
            )
            for index, binding_id in enumerate(EXP02_REQUIRED_BINDING_IDS, start=1)
        )
        self.expected_bindings = {item.binding_id: item.self_hash for item in self.bindings}
        self.bundle = validate_scientific_binding_bundle_v1(
            self.bindings, expected_binding_hashes=self.expected_bindings,
            source_commit=COMMIT,
        )
        relations = (
            ConfirmedRelationIdentityV1(
                "r1", "s1", "t1", "step_up", "increase", 5, h("r1")
            ),
            ConfirmedRelationIdentityV1(
                "r2", "s2", "t2", "step_down", "decrease", 10, h("r2")
            ),
        )
        self.cohort = build_confirmed_cohort_authority_v1(
            cohort_id="V2-EXP02-COHORT", source_commit=COMMIT,
            confirmation_artifact_hash=h("confirmation"), relations=relations,
        )
        self.cohort_binding = build_v2_confirmed_cohort_binding_v1(self.cohort)
        self.candidate_policy_hash = h("candidate-policy")
        self.projection = build_cohort_projection_receipt_v1(
            cohort=self.cohort, cohort_binding=self.cohort_binding,
            candidate_policy_hash=self.candidate_policy_hash,
            projection_artifact_hash=h("projection-artifact"),
        )
        self.summary_receipts = tuple(
            build_private_summary_hash_receipt_v1(
                split_id=split, cohort=self.cohort_binding,
                private_summary_bundle_hash=h(f"summary-{split}"),
            )
            for split in ("train1", "train2")
        )

    def test_binding_bundle_is_exact_and_public_safe(self) -> None:
        self.assertEqual(self.bundle.binding_count, 3)
        self.assertTrue(self.bundle.complete)
        self.assertTrue(self.bundle.data_io_authorized)
        self.assertFalse(self.bundle.labels_allowed)
        self.assertFalse(self.bundle.test1_allowed)
        self.assertFalse(self.bundle.test2_allowed)
        document = json.dumps(self.bundle.to_dict())
        self.assertNotIn("\\", document)
        self.assertNotIn("/Users/", document)
        replayed = tuple(frozen_scientific_binding_from_dict_v1(item.to_dict()) for item in self.bindings)
        self.assertEqual(replayed, self.bindings)

    def test_missing_stale_and_mutated_bindings_reject_before_any_io(self) -> None:
        opened = 0

        def opener():
            nonlocal opened
            opened += 1
            return object(), 1, h("payload")

        with self.assertRaisesRegex(Exp02RunnerError, "BINDING_SET_INCOMPLETE"):
            validate_scientific_binding_bundle_v1(
                self.bindings[:-1], expected_binding_hashes=self.expected_bindings,
                source_commit=COMMIT,
            )
        self.assertEqual(opened, 0)
        with self.assertRaisesRegex(Exp02RunnerError, "BINDING_STALE"):
            validate_scientific_binding_bundle_v1(
                self.bindings,
                expected_binding_hashes={
                    **self.expected_bindings,
                    EXP02_REQUIRED_BINDING_IDS[0]: h("stale"),
                },
                source_commit=COMMIT,
            )
        self.assertEqual(opened, 0)
        mutated = replace(self.bindings[0], implementation_hash=h("mutated"))
        with self.assertRaisesRegex(Exp02RunnerError, "BINDING_REPLAY_MISMATCH"):
            validate_scientific_binding_bundle_v1(
                (mutated, *self.bindings[1:]),
                expected_binding_hashes=self.expected_bindings,
                source_commit=COMMIT,
            )
        self.assertEqual(opened, 0)

    def test_prohibited_splits_reject_before_opener(self) -> None:
        for split in ("test1", "test2", "heldout", "future_heldout", "outer", "sealed"):
            opened = 0

            def opener():
                nonlocal opened
                opened += 1
                return object(), 1, h("payload")

            with self.subTest(split=split), self.assertRaisesRegex(
                Exp02RunnerError, "SPLIT_PROHIBITED"
            ):
                execute_authorized_split_open_v1(
                    binding_bundle=self.bundle,
                    ledger=start_split_open_ledger_v1(self.bundle),
                    split_id=split,
                    operation=Exp02OperationV1.SELECT_ON_NORMAL_TRAIN4,
                    purpose_id="synthetic-open", opener=opener,
                )
            self.assertEqual(opened, 0)

    def test_authorized_open_records_path_free_hash_ledger(self) -> None:
        private_value = object()

        returned, ledger = execute_authorized_split_open_v1(
            binding_bundle=self.bundle,
            ledger=start_split_open_ledger_v1(self.bundle),
            split_id="train4",
            operation=Exp02OperationV1.SELECT_ON_NORMAL_TRAIN4,
            purpose_id="selection-input",
            opener=lambda: (private_value, 123, h("train4-private-bytes")),
        )
        self.assertIs(returned, private_value)
        self.assertEqual(len(ledger.events), 1)
        self.assertEqual(ledger.events[0].split_id, "train4")
        self.assertEqual(ledger.test1_accesses, 0)
        self.assertEqual(ledger.test2_accesses, 0)
        self.assertEqual(ledger.label_accesses, 0)
        self.assertEqual(ledger.heldout_accesses, 0)
        self.assertNotIn("path", json.dumps(ledger.to_dict()).lower())

    def test_cohort_projection_requires_external_identity(self) -> None:
        self.assertEqual(
            validate_cohort_projection_receipt_v1(
                self.projection, cohort=self.cohort,
                cohort_binding=self.cohort_binding,
                candidate_policy_hash=self.candidate_policy_hash,
                expected_receipt_hash=self.projection.self_hash,
            ),
            self.projection.self_hash,
        )
        with self.assertRaisesRegex(Exp02RunnerError, "PROJECTION_STALE"):
            validate_cohort_projection_receipt_v1(
                self.projection, cohort=self.cohort,
                cohort_binding=self.cohort_binding,
                candidate_policy_hash=self.candidate_policy_hash,
                expected_receipt_hash=h("stale"),
            )

    def test_candidate_closure_is_exactly_one_plus_36(self) -> None:
        candidates, candidate_receipt, closure = close_exact_candidate_set_v1(
            binding_bundle=self.bundle, projection=self.projection,
            expected_projection_hash=self.projection.self_hash,
            cohort=self.cohort, cohort_binding=self.cohort_binding,
            candidate_policy_hash=self.candidate_policy_hash,
            normal_fit_input_hash=h("normal-fit-input"),
            summary_receipts=self.summary_receipts,
            expected_summary_receipt_hashes={
                item.split_id: item.self_hash for item in self.summary_receipts
            },
        )
        self.assertEqual(len(candidates), 37)
        self.assertEqual(candidate_receipt.candidate_count, 37)
        self.assertEqual(closure.common_candidate_count, 1)
        self.assertEqual(closure.relation_specific_candidate_count, 36)
        self.assertTrue(closure.closed_before_train4)
        self.assertEqual(closure.test1_accesses, 0)

    def test_atomic_persistence_writes_fsyncs_reopens_and_directory_syncs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory).resolve() / "selected-policy.private.json"
            directory_syncs: list[Path] = []
            evidence, receipt = atomic_persist_selected_policy_v1(
                artifact_id="V2-EXP02-SELECTED-POLICY", payload=b"private-policy",
                target_path=target,
                directory_fsync=lambda path: directory_syncs.append(path),
            )
            self.assertEqual(target.read_bytes(), b"private-policy")
            self.assertEqual(evidence.payload_bytes_sha256, h("private-policy"))
            self.assertEqual(directory_syncs, [target.parent])
            self.assertTrue(receipt.atomic_replace_completed)
            self.assertTrue(receipt.file_fsync_completed)
            self.assertTrue(receipt.close_completed)
            self.assertTrue(receipt.directory_fsync_completed)
            self.assertTrue(receipt.reopen_completed)
            self.assertFalse(receipt.contains_private_path)
            self.assertNotIn(str(target), json.dumps(receipt.to_dict()))

    def test_atomic_partial_write_reopen_mismatch_and_stale_target_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            partial = root / "partial.json"

            def partial_writer(handle, payload):
                handle.write(payload[:-1])
                return len(payload) - 1

            with self.assertRaisesRegex(Exp02RunnerError, "PARTIAL_WRITE"):
                atomic_persist_selected_policy_v1(
                    artifact_id="partial", payload=b"payload", target_path=partial,
                    write_payload=partial_writer, directory_fsync=lambda _: None,
                )
            self.assertFalse(partial.exists())

            mismatch = root / "mismatch.json"
            with self.assertRaisesRegex(Exp02RunnerError, "REOPEN_MISMATCH"):
                atomic_persist_selected_policy_v1(
                    artifact_id="mismatch", payload=b"payload", target_path=mismatch,
                    directory_fsync=lambda _: None,
                    reopen_reader=lambda _: b"different",
                )

            stale = root / "stale.json"
            stale.write_bytes(b"already-frozen")
            with self.assertRaisesRegex(Exp02RunnerError, "TARGET_EXISTS"):
                atomic_persist_selected_policy_v1(
                    artifact_id="stale", payload=b"payload", target_path=stale,
                    directory_fsync=lambda _: None,
                )
            self.assertEqual(stale.read_bytes(), b"already-frozen")

    def test_atomic_replace_and_directory_sync_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target = root / "replace-failure.json"

            def fail_replace(_source, _destination):
                raise OSError("synthetic replace failure")

            with self.assertRaisesRegex(Exp02RunnerError, "ATOMIC_PERSISTENCE_FAILED"):
                atomic_persist_selected_policy_v1(
                    artifact_id="replace-failure", payload=b"payload",
                    target_path=target, atomic_replace=fail_replace,
                    directory_fsync=lambda _: None,
                )
            self.assertFalse(target.exists())

            directory_target = root / "directory-failure.json"

            def fail_directory(_directory):
                raise OSError("synthetic directory sync failure")

            with self.assertRaisesRegex(Exp02RunnerError, "ATOMIC_PERSISTENCE_FAILED"):
                atomic_persist_selected_policy_v1(
                    artifact_id="directory-failure", payload=b"payload",
                    target_path=directory_target, directory_fsync=fail_directory,
                )


if __name__ == "__main__":
    unittest.main()
