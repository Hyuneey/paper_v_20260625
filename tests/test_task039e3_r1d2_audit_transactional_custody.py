from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    FAULT_STAGES,
    HEAD_AUTHORITY,
    HEAD_FILENAME,
    ORPHAN_CLASSIFICATION,
    PENDING_DIRECTORY,
    RECORDS_DIRECTORY,
    TASK039E3TransactionalCustodyV3Error,
    TransactionalCustodyAppendV3Error,
    TransactionalHashChainCustodyV3,
    reconstruct_transactional_ledger_v3,
)


LEDGER_KIND = "scientific_provider"


def _canonical_hash(document: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            document,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _rehash(document: dict[str, object], field: str) -> dict[str, object]:
    result = dict(document)
    result.pop(field, None)
    result[field] = _canonical_hash(result)
    return result


def _payload(index: int) -> dict[str, object]:
    return {
        "provider_contacted": True,
        "response_origin": "provider",
        "response_id": f"chatcmpl-audit-{index}",
        "transport_attempts": 1,
    }


class _FailOnce:
    def __init__(self, target: str) -> None:
        self.target = target
        self.raised = False

    def __call__(self, stage: str, _context: object) -> None:
        if stage == self.target and not self.raised:
            self.raised = True
            raise OSError(f"synthetic crash at {stage}")


def _ledger(root: Path, *, fault: _FailOnce | None = None) -> TransactionalHashChainCustodyV3:
    return TransactionalHashChainCustodyV3(
        root,
        ledger_kind=LEDGER_KIND,
        allowed_logical_call_kind="scientific",
        fault_injector=fault,
    )


class TransactionalCustodyIndependentAuditTests(unittest.TestCase):
    def test_independent_normal_chain_hash_and_restart_reconstruction(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = _ledger(root)
            first = ledger.append(logical_call_kind="scientific", slot_identity="T1:0", payload=_payload(0))
            second = ledger.append(logical_call_kind="scientific", slot_identity="T1:1", payload=_payload(1))
            for record in (first, second):
                unsigned = dict(record)
                observed = unsigned.pop("record_hash")
                self.assertEqual(observed, _canonical_hash(unsigned))
            self.assertIsNone(first["previous_record_hash"])
            self.assertEqual(second["previous_record_hash"], first["record_hash"])
            head = json.loads((root / HEAD_FILENAME).read_text("utf-8"))
            unsigned_head = dict(head)
            observed_head_hash = unsigned_head.pop("artifact_hash")
            self.assertEqual(observed_head_hash, _canonical_hash(unsigned_head))
            self.assertEqual(head["head_authority"], HEAD_AUTHORITY)
            self.assertEqual(head["head_record_hash"], second["record_hash"])
            restarted = _ledger(root)
            self.assertEqual(restarted.authoritative_head_hash, second["record_hash"])
            self.assertEqual(restarted.authoritative_record_count, 2)
            self.assertEqual(restarted.reconstruct().orphan_record_hashes, ())

    def test_every_fault_point_has_one_unambiguous_old_authoritative_head(self) -> None:
        stages_after_promotion = {
            "record_promotion",
            "records_directory_fsync",
            "head_temp_write",
            "head_temp_flush",
            "head_temp_fsync",
            "head_replace",
            "ledger_directory_fsync",
            "disk_verification",
        }
        self.assertEqual(
            set(FAULT_STAGES),
            {
                "candidate_write",
                "candidate_flush",
                "candidate_fsync",
                "record_promotion",
                "records_directory_fsync",
                "head_temp_write",
                "head_temp_flush",
                "head_temp_fsync",
                "head_replace",
                "ledger_directory_fsync",
                "disk_verification",
            },
        )
        for stage in FAULT_STAGES:
            with self.subTest(stage=stage), TemporaryDirectory() as raw:
                root = Path(raw) / "ledger"
                ledger = _ledger(root, fault=_FailOnce(stage))
                with self.assertRaises(TransactionalCustodyAppendV3Error) as caught:
                    ledger.append(logical_call_kind="scientific", slot_identity=f"T1:{stage}", payload=_payload(1))
                self.assertEqual(caught.exception.failed_stage, stage)
                self.assertIsNone(ledger.authoritative_head_hash)
                self.assertEqual(ledger.authoritative_record_count, 0)
                disk = reconstruct_transactional_ledger_v3(root, ledger_kind=LEDGER_KIND)
                self.assertIsNone(disk.head_record_hash)
                self.assertEqual(disk.authoritative_record_count, 0)
                self.assertEqual(disk.pending_files, ())
                self.assertEqual(len(disk.orphan_records), int(stage in stages_after_promotion))
                if disk.orphan_records:
                    self.assertEqual(caught.exception.candidate_classification, ORPHAN_CLASSIFICATION)
                restarted = _ledger(root)
                self.assertIsNone(restarted.authoritative_head_hash)

    def test_tamper_absent_reference_predecessor_duplicate_orphan_and_pending_are_deterministic(self) -> None:
        # Direct record and HEAD tampering is rejected by independent hashes.
        for target in ("record", "head"):
            with self.subTest(target=target), TemporaryDirectory() as raw:
                root = Path(raw) / "ledger"
                ledger = _ledger(root)
                ledger.append(logical_call_kind="scientific", slot_identity="T1:0", payload=_payload(0))
                path = next((root / RECORDS_DIRECTORY).glob("*.json")) if target == "record" else root / HEAD_FILENAME
                document = json.loads(path.read_text("utf-8"))
                document["record_count" if target == "head" else "sequence_index"] = 999
                path.write_text(json.dumps(document), "utf-8")
                with self.assertRaisesRegex(TASK039E3TransactionalCustodyV3Error, "hash differs"):
                    reconstruct_transactional_ledger_v3(root, ledger_kind=LEDGER_KIND)

        # A validly self-hashed HEAD pointing to an absent record still fails closed.
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            _ledger(root)
            head_path = root / HEAD_FILENAME
            head = json.loads(head_path.read_text("utf-8"))
            head.update({"head_record_hash": "a" * 64, "record_count": 1})
            head = _rehash(head, "artifact_hash")
            head_path.write_text(json.dumps(head), "utf-8")
            with self.assertRaisesRegex(TASK039E3TransactionalCustodyV3Error, "absent record"):
                reconstruct_transactional_ledger_v3(root, ledger_kind=LEDGER_KIND)

        # A duplicate complete record under another filename is never silently accepted.
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = _ledger(root)
            ledger.append(logical_call_kind="scientific", slot_identity="T1:0", payload=_payload(0))
            original = next((root / RECORDS_DIRECTORY).glob("*.json"))
            shutil.copyfile(original, root / RECORDS_DIRECTORY / ("duplicate-" + original.name))
            with self.assertRaisesRegex(TASK039E3TransactionalCustodyV3Error, "filename differs"):
                reconstruct_transactional_ledger_v3(root, ledger_kind=LEDGER_KIND)

        # Pending files are reported, while a promoted unreachable record is an orphan.
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = _ledger(root, fault=_FailOnce("record_promotion"))
            with self.assertRaises(TransactionalCustodyAppendV3Error):
                ledger.append(logical_call_kind="scientific", slot_identity="T1:orphan", payload=_payload(0))
            (root / PENDING_DIRECTORY / "synthetic.pending").write_text("non-authoritative", "utf-8")
            state = reconstruct_transactional_ledger_v3(root, ledger_kind=LEDGER_KIND)
            self.assertEqual(state.authoritative_record_count, 0)
            self.assertEqual(len(state.orphan_records), 1)
            self.assertEqual(state.pending_files, ("synthetic.pending",))
            self.assertEqual(state.to_dict()["orphan_records"][0]["classification"], ORPHAN_CLASSIFICATION)

    def test_predecessor_and_sequence_contract_cannot_be_reinterpreted(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = _ledger(root)
            ledger.append(logical_call_kind="scientific", slot_identity="T1:0", payload=_payload(0))
            ledger.append(logical_call_kind="scientific", slot_identity="T1:1", payload=_payload(1))
            second_path = sorted((root / RECORDS_DIRECTORY).glob("*.json"))[1]
            second = json.loads(second_path.read_text("utf-8"))
            second["previous_record_hash"] = None
            second = _rehash(second, "record_hash")
            replacement = root / RECORDS_DIRECTORY / f"00000001-{second['record_hash']}.json"
            second_path.unlink()
            replacement.write_text(json.dumps(second), "utf-8")
            head_path = root / HEAD_FILENAME
            head = json.loads(head_path.read_text("utf-8"))
            head["head_record_hash"] = second["record_hash"]
            head = _rehash(head, "artifact_hash")
            head_path.write_text(json.dumps(head), "utf-8")
            with self.assertRaisesRegex(TASK039E3TransactionalCustodyV3Error, "sequence differs|record count differs|ledger hash differs"):
                reconstruct_transactional_ledger_v3(root, ledger_kind=LEDGER_KIND)

    def test_crash_windows_restart_to_exactly_one_head_interpretation(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw) / "ledger"
            ledger = _ledger(root)
            first = ledger.append(logical_call_kind="scientific", slot_identity="T1:0", payload=_payload(0))
            old_head_bytes = (root / HEAD_FILENAME).read_bytes()
            second = ledger.append(logical_call_kind="scientific", slot_identity="T1:1", payload=_payload(1))

            # HEAD replaced and durable, process dies before in-memory update: restart follows new HEAD.
            restarted_new = _ledger(root)
            self.assertEqual(restarted_new.authoritative_head_hash, second["record_hash"])
            self.assertEqual(restarted_new.authoritative_record_count, 2)

            # Record promoted but HEAD replacement is lost: old HEAD is sole authority, second is orphan.
            (root / HEAD_FILENAME).write_bytes(old_head_bytes)
            restarted_old = _ledger(root)
            old_state = restarted_old.reconstruct()
            self.assertEqual(restarted_old.authoritative_head_hash, first["record_hash"])
            self.assertEqual(restarted_old.authoritative_record_count, 1)
            self.assertEqual(old_state.orphan_record_hashes, (second["record_hash"],))

            # The orphan persists across a further restart without competing with HEAD.
            restarted_again = _ledger(root)
            self.assertEqual(restarted_again.authoritative_head_hash, first["record_hash"])
            self.assertEqual(restarted_again.reconstruct().orphan_record_hashes, (second["record_hash"],))

    def test_existing_head_remains_disk_and_memory_authority_after_second_append_fault(self) -> None:
        for stage in FAULT_STAGES:
            with self.subTest(stage=stage), TemporaryDirectory() as raw:
                root = Path(raw) / "ledger"
                ledger = _ledger(root)
                first = ledger.append(logical_call_kind="scientific", slot_identity="T1:0", payload=_payload(0))
                ledger._fault_injector = _FailOnce(stage)  # audit-only fault seam
                with self.assertRaises(TransactionalCustodyAppendV3Error):
                    ledger.append(logical_call_kind="scientific", slot_identity="T1:1", payload=_payload(1))
                disk = reconstruct_transactional_ledger_v3(root, ledger_kind=LEDGER_KIND)
                self.assertEqual(disk.head_record_hash, first["record_hash"])
                self.assertEqual(disk.authoritative_record_count, 1)
                self.assertEqual(ledger.authoritative_head_hash, first["record_hash"])
                self.assertEqual(ledger.authoritative_record_count, 1)


if __name__ == "__main__":
    unittest.main()
