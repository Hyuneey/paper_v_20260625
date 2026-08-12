from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    FAULT_STAGES,
    HEAD_AUTHORITY,
    HEAD_FILENAME,
    LEDGER_FILENAME,
    ORPHAN_CLASSIFICATION,
    PENDING_DIRECTORY,
    RECORDS_DIRECTORY,
    TASK039E3TransactionalCustodyV3Error,
    TransactionalCustodyAppendV3Error,
    TransactionalHashChainCustodyV3,
    reconstruct_transactional_ledger_v3,
)


LEDGER_KIND = "scientific_provider"


def _payload(index: int) -> dict[str, object]:
    return {
        "provider_contacted": True,
        "response_origin": "provider",
        "response_id": f"chatcmpl-synthetic-{index}",
        "transport_attempts": 1,
    }


class _FailOnce:
    def __init__(self, target: str) -> None:
        self.target = target
        self.seen: list[str] = []
        self.raised = False

    def __call__(self, stage: str, context: object) -> None:
        del context
        self.seen.append(stage)
        if stage == self.target and not self.raised:
            self.raised = True
            raise OSError(f"synthetic fault after {stage}")


class _FailOnOccurrence:
    def __init__(self, target: str, occurrence: int) -> None:
        self.target = target
        self.occurrence = occurrence
        self.observed = 0

    def __call__(self, stage: str, context: object) -> None:
        del context
        if stage == self.target:
            self.observed += 1
            if self.observed == self.occurrence:
                raise OSError(f"synthetic fault after {stage}")


class TransactionalCustodyV3Tests(unittest.TestCase):
    def test_initial_layout_declares_head_as_sole_authority(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = TransactionalHashChainCustodyV3(
                root,
                ledger_kind=LEDGER_KIND,
                allowed_logical_call_kind="scientific",
            )
            self.assertTrue((root / RECORDS_DIRECTORY).is_dir())
            self.assertTrue((root / PENDING_DIRECTORY).is_dir())
            metadata = json.loads((root / LEDGER_FILENAME).read_text("utf-8"))
            head = json.loads((root / HEAD_FILENAME).read_text("utf-8"))
            self.assertEqual(metadata["head_authority"], HEAD_AUTHORITY)
            self.assertTrue(metadata["single_authoritative_writer"])
            self.assertEqual(
                metadata["unreachable_record_classification"],
                ORPHAN_CLASSIFICATION,
            )
            self.assertEqual(head["head_authority"], HEAD_AUTHORITY)
            self.assertIsNone(head["head_record_hash"])
            self.assertEqual(head["record_count"], 0)
            self.assertEqual(ledger.authoritative_record_count, 0)

    def test_two_commits_reconstruct_exact_hash_chain_and_reopen(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = TransactionalHashChainCustodyV3(
                root,
                ledger_kind=LEDGER_KIND,
                allowed_logical_call_kind="scientific",
            )
            first = ledger.append(
                logical_call_kind="scientific",
                slot_identity="T1:000:1",
                payload=_payload(1),
            )
            second = ledger.append(
                logical_call_kind="scientific",
                slot_identity="T1:001:1",
                payload=_payload(2),
            )
            observed = reconstruct_transactional_ledger_v3(
                root, ledger_kind=LEDGER_KIND
            )
            self.assertEqual(observed.authoritative_record_count, 2)
            self.assertEqual(observed.head_record_hash, second["record_hash"])
            self.assertEqual(second["previous_record_hash"], first["record_hash"])
            self.assertEqual(observed.orphan_record_hashes, ())
            self.assertEqual(observed.pending_files, ())
            self.assertEqual(observed.ledger_hash, ledger.ledger_hash)

            reopened = TransactionalHashChainCustodyV3(
                root,
                ledger_kind=LEDGER_KIND,
                allowed_logical_call_kind="scientific",
            )
            self.assertEqual(reopened.authoritative_record_count, 2)
            self.assertEqual(reopened.authoritative_head_hash, second["record_hash"])
            self.assertEqual(reopened.ledger_hash, ledger.ledger_hash)

    def test_every_fault_stage_preserves_previous_authoritative_head(self) -> None:
        promoted_stages = {
            "record_promotion",
            "records_directory_fsync",
            "head_temp_write",
            "head_temp_flush",
            "head_temp_fsync",
            "head_replace",
            "ledger_directory_fsync",
            "disk_verification",
        }
        for stage in FAULT_STAGES:
            with self.subTest(stage=stage), TemporaryDirectory() as raw:
                root = Path(raw) / "ledger"
                fault = _FailOnce(stage)
                ledger = TransactionalHashChainCustodyV3(
                    root,
                    ledger_kind=LEDGER_KIND,
                    allowed_logical_call_kind="scientific",
                    fault_injector=fault,
                )
                with self.assertRaises(TransactionalCustodyAppendV3Error) as caught:
                    ledger.append(
                        logical_call_kind="scientific",
                        slot_identity=f"T1:fault:{stage}",
                        payload=_payload(1),
                    )
                self.assertEqual(caught.exception.failed_stage, stage)
                self.assertIsNone(caught.exception.authoritative_head_hash)
                self.assertEqual(ledger.authoritative_record_count, 0)
                self.assertIsNone(ledger.authoritative_head_hash)
                observed = reconstruct_transactional_ledger_v3(
                    root, ledger_kind=LEDGER_KIND
                )
                self.assertEqual(observed.authoritative_record_count, 0)
                self.assertIsNone(observed.head_record_hash)
                self.assertEqual(observed.pending_files, ())
                expected_orphans = 1 if stage in promoted_stages else 0
                self.assertEqual(len(observed.orphan_records), expected_orphans)
                if expected_orphans:
                    self.assertEqual(
                        caught.exception.candidate_classification,
                        ORPHAN_CLASSIFICATION,
                    )
                    self.assertEqual(
                        observed.orphan_record_hashes,
                        (caught.exception.candidate_record_hash,),
                    )
                else:
                    self.assertEqual(
                        caught.exception.candidate_classification,
                        "candidate_not_committed",
                    )

    def test_failed_second_append_retains_prior_disk_and_memory_head(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = TransactionalHashChainCustodyV3(
                root,
                ledger_kind=LEDGER_KIND,
                allowed_logical_call_kind="scientific",
                fault_injector=_FailOnOccurrence("ledger_directory_fsync", 2),
            )
            first = ledger.append(
                logical_call_kind="scientific",
                slot_identity="T1:000:1",
                payload=_payload(1),
            )
            with self.assertRaises(TransactionalCustodyAppendV3Error) as caught:
                ledger.append(
                    logical_call_kind="scientific",
                    slot_identity="T1:001:1",
                    payload=_payload(2),
                )
            self.assertEqual(
                caught.exception.authoritative_head_hash,
                first["record_hash"],
            )
            self.assertEqual(ledger.authoritative_record_count, 1)
            self.assertEqual(ledger.authoritative_head_hash, first["record_hash"])
            observed = ledger.reconstruct()
            self.assertEqual(observed.authoritative_record_count, 1)
            self.assertEqual(observed.head_record_hash, first["record_hash"])
            self.assertEqual(len(observed.orphan_records), 1)

    def test_unreachable_complete_record_is_never_authoritative(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = TransactionalHashChainCustodyV3(
                root,
                ledger_kind=LEDGER_KIND,
                fault_injector=_FailOnce("record_promotion"),
            )
            with self.assertRaises(TransactionalCustodyAppendV3Error):
                ledger.append(
                    logical_call_kind="scientific",
                    slot_identity="T1:orphan",
                    payload=_payload(1),
                )
            record_files = tuple((root / RECORDS_DIRECTORY).glob("*.json"))
            self.assertEqual(len(record_files), 1)
            complete_looking = json.loads(record_files[0].read_text("utf-8"))
            self.assertIn("record_hash", complete_looking)
            observed = ledger.reconstruct()
            self.assertEqual(observed.authoritative_record_count, 0)
            self.assertEqual(len(observed.orphan_records), 1)
            self.assertEqual(
                observed.to_dict()["orphan_records"][0]["classification"],
                ORPHAN_CLASSIFICATION,
            )

    def test_logical_call_kind_and_slot_uniqueness_are_fail_closed(self) -> None:
        with TemporaryDirectory() as raw:
            ledger = TransactionalHashChainCustodyV3(
                Path(raw) / "ledger",
                ledger_kind="capability_provider",
                allowed_logical_call_kind="recovery_capability",
            )
            with self.assertRaisesRegex(
                TASK039E3TransactionalCustodyV3Error, "logical-call kind"
            ):
                ledger.append(
                    logical_call_kind="scientific",
                    slot_identity="wrong-kind",
                    payload=_payload(1),
                )
            ledger.append(
                logical_call_kind="recovery_capability",
                slot_identity="recovery-capability:1",
                payload=_payload(1),
            )
            with self.assertRaisesRegex(
                TASK039E3TransactionalCustodyV3Error, "already committed"
            ):
                ledger.append(
                    logical_call_kind="recovery_capability",
                    slot_identity="recovery-capability:1",
                    payload=_payload(2),
                )

    def test_tampered_record_or_head_cannot_reconstruct(self) -> None:
        for target in ("record", "head"):
            with self.subTest(target=target), TemporaryDirectory() as raw:
                root = Path(raw) / "ledger"
                ledger = TransactionalHashChainCustodyV3(
                    root, ledger_kind=LEDGER_KIND
                )
                ledger.append(
                    logical_call_kind="scientific",
                    slot_identity="T1:000:1",
                    payload=_payload(1),
                )
                if target == "record":
                    path = next((root / RECORDS_DIRECTORY).glob("*.json"))
                    document = json.loads(path.read_text("utf-8"))
                    document["payload"]["transport_attempts"] = 3
                else:
                    path = root / HEAD_FILENAME
                    document = json.loads(path.read_text("utf-8"))
                    document["record_count"] = 999
                path.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaisesRegex(
                    TASK039E3TransactionalCustodyV3Error,
                    "hash differs",
                ):
                    reconstruct_transactional_ledger_v3(
                        root, ledger_kind=LEDGER_KIND
                    )

    def test_non_json_payload_is_rejected_before_any_candidate_file(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = TransactionalHashChainCustodyV3(root, ledger_kind=LEDGER_KIND)
            with self.assertRaises(Exception):
                ledger.append(
                    logical_call_kind="scientific",
                    slot_identity="T1:invalid",
                    payload={"unsupported": object()},
                )
            self.assertEqual(tuple((root / PENDING_DIRECTORY).iterdir()), ())
            self.assertEqual(tuple((root / RECORDS_DIRECTORY).iterdir()), ())
            self.assertEqual(ledger.authoritative_record_count, 0)


if __name__ == "__main__":
    unittest.main()
