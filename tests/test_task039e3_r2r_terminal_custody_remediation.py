from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeLedgerV1,
    ConstructionProposalLedgerV1,
    T0_TEMPLATE_HASH,
    run_t0_v1,
    wrap_and_verify_core_v1,
)
from paperworks.v6.task039e3_r2r_proposal_custody_v2 import (
    TASK039E3ProposalCustodyError,
    proposal_record_hash_preimage_v1,
    serialize_construction_proposal_custody_record_v2,
    verify_serialized_construction_proposal_custody_record_v2,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    DurableConstructionProposalLedgerV1,
)
from paperworks.v6.task039e3_r2r_result_finalizer_v1 import (
    PRIVATE_ARTIFACT_NAMES_R2R_V1,
    TASK039E3R2RResultFinalizationError,
    _proposal_custody_record_v2,
    finalize_successful_r2r_scientific_result_v1,
)
from tests.test_task039e3_r2r_finalization_v1 import _arguments
from task039e3_support import make_evidence, valid_core


ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT_HASH = "54d71edb6357e8c4d4a5479a9f0b130ca0f89f10ed4ff04ad9ba90122f3ff7c2"
PUBLIC_INVENTORY_HASH = "0dd0792e95066bbff3a5b28f69adec81307fe6b0a6b3a4d45bfbd837d9b9aa1b"
PRIVATE_INVENTORY_HASH = "56c1cb6fc14be6742d88ba681987398d7d0b02cb19759b6d7b4d572cfd0e011a"
SUCCESS_RECEIPT_BYTE_HASH = "fd6fb116004567fad8acccaafff098d8738ecde1ad80f490bf032b7cbe46358f"
PROPOSAL_LEDGER_BYTE_HASH = "22593dcbb195f7094f5185c2b8a08ee9236e982e867f0fa10d55d60fab0cf15c"
WORKING_PROPOSAL_BYTE_HASH = "d06f74139cc1a81c455cf7d933b7ee02c5a2df074c55ebd498bd6d2bd8eed7ec"


def _record(index: int = 1):
    evidence = make_evidence(index)
    return wrap_and_verify_core_v1(
        core=valid_core(evidence), evidence=evidence, arm="T0",
        call_number=0, prompt_hash=T0_TEMPLATE_HASH,
    )


def _inventory_hash(root: Path) -> str:
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries.append({"path": relative, "kind": "link"})
        elif path.is_dir():
            entries.append({"path": relative, "kind": "directory"})
        elif path.is_file():
            payload = path.read_bytes()
            entries.append({
                "path": relative, "kind": "file", "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            })
        else:
            entries.append({"path": relative, "kind": "other"})
    return stable_hash_v1({"entries": entries})


class TerminalCustodyFutureSerializationTests(unittest.TestCase):
    def test_serialized_only_roundtrip_closes_all_three_hashes(self) -> None:
        record = _record()
        encoded = json.dumps(
            serialize_construction_proposal_custody_record_v2(record),
            sort_keys=True, separators=(",", ":"),
        )
        document = json.loads(encoded)
        verified = verify_serialized_construction_proposal_custody_record_v2(
            document
        )
        self.assertEqual(verified["proposal_hash"], record.proposal_hash)
        self.assertEqual(verified["validity_hash"], record.validity_hash)
        self.assertEqual(verified["record_hash"], record.record_hash)
        self.assertEqual(
            stable_hash_v1(proposal_record_hash_preimage_v1(verified)),
            record.record_hash,
        )

    def test_working_jsonl_survives_failure_and_is_self_sufficient(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "proposals_working.jsonl"
            ledger = DurableConstructionProposalLedgerV1(path)
            record = _record()
            ledger.append(record)
            ledger.close()
            self.assertFalse((Path(temporary) / "final_authoritative_r2r_v1").exists())
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                verify_serialized_construction_proposal_custody_record_v2(
                    persisted
                )["record_hash"],
                record.record_hash,
            )

    def test_final_snapshot_equals_canonical_working_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()
            arguments = _arguments(private, public)
            expected = list(arguments["proposal_records"])
            finalize_successful_r2r_scientific_result_v1(**arguments)
            final = json.loads((
                private / "final_authoritative_r2r_v1"
                / PRIVATE_ARTIFACT_NAMES_R2R_V1["proposal_validity"]
            ).read_text(encoding="utf-8"))
            self.assertEqual(final["records"], expected)
            for document in final["records"]:
                verify_serialized_construction_proposal_custody_record_v2(
                    document
                )

    def test_legacy_or_tampered_custody_fails_closed(self) -> None:
        complete = serialize_construction_proposal_custody_record_v2(_record())
        legacy = copy.deepcopy(complete)
        del legacy["proposal_envelope"]
        with self.assertRaises(TASK039E3ProposalCustodyError):
            verify_serialized_construction_proposal_custody_record_v2(legacy)
        with self.assertRaises(TASK039E3R2RResultFinalizationError):
            _proposal_custody_record_v2(legacy)
        for path in (
            ("proposal_envelope", "prompt_hash"),
            ("proposal_envelope", "proposal_core", "relation_identity"),
            ("project_proposal", "source"),
            ("validity_result", "artifact_hash"),
        ):
            altered = copy.deepcopy(complete)
            target = altered
            for field in path[:-1]:
                target = target[field]
            target[path[-1]] = "0" * 64 if "hash" in path[-1] else "ALTERED"
            with self.subTest(path=path):
                with self.assertRaises(TASK039E3ProposalCustodyError):
                    verify_serialized_construction_proposal_custody_record_v2(
                        altered
                    )


@unittest.skipUnless(
    os.environ.get("TASK039E3_CUSTODY_SUPPLEMENT"),
    "task-local private custody paths are intentionally external",
)
class TerminalCustodyHistoricalReconstructionTests(unittest.TestCase):
    def test_exact_historical_reconstruction_matches_private_supplement(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(
            Path(environment["TASK039E3_HISTORICAL_REPOSITORY"]) / "src"
        )
        command = [
            sys.executable, "-B",
            str(ROOT / "scripts/reconstruct_task039e3_r2r_terminal_custody_v1.py"),
            "--historical-repository-root", environment["TASK039E3_HISTORICAL_REPOSITORY"],
            "--e1-private-ledger", environment["TASK039E3_E1_LEDGER"],
            "--original-proposal-ledger", environment["TASK039E3_ORIGINAL_PROPOSAL_LEDGER"],
            "--original-provider-ledger", environment["TASK039E3_ORIGINAL_PROVIDER_LEDGER"],
            "--success-receipt", environment["TASK039E3_SUCCESS_RECEIPT"],
            "--verify-existing-supplement", environment["TASK039E3_CUSTODY_SUPPLEMENT"],
        ]
        completed = subprocess.run(
            command, check=True, capture_output=True, text=True,
            env=environment,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["artifact_hash"], SUPPLEMENT_HASH)
        self.assertEqual((result["records"], result["exact_matches"], result["mismatches"]), (251, 251, 0))

    def test_supplement_is_private_closed_and_self_hashed(self) -> None:
        document = json.loads(
            Path(os.environ["TASK039E3_CUSTODY_SUPPLEMENT"]).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(document["artifact_hash"], SUPPLEMENT_HASH)
        self.assertEqual(
            stable_hash_v1({k: v for k, v in document.items() if k != "artifact_hash"}),
            SUPPLEMENT_HASH,
        )
        self.assertEqual(len(document["records"]), 251)
        self.assertEqual(document["proposal_arm_counts"], {"T0": 42, "T1": 42, "T1-B": 125, "T2": 42})
        self.assertFalse(document["missing_schema_failure_proposal_materialized"])
        for record in document["records"]:
            self.assertEqual(record["original_record_hash"], record["recomputed_record_hash"])
            self.assertEqual(
                stable_hash_v1({k: v for k, v in record.items() if k != "supplement_record_hash"}),
                record["supplement_record_hash"],
            )

    def test_original_success_roots_are_byte_identical(self) -> None:
        public = Path(os.environ["TASK039E3_SUCCESS_PUBLIC_ROOT"])
        private = Path(os.environ["TASK039E3_SUCCESS_PRIVATE_ROOT"])
        self.assertEqual(
            _inventory_hash(public),
            PUBLIC_INVENTORY_HASH,
        )
        self.assertEqual(
            _inventory_hash(private),
            PRIVATE_INVENTORY_HASH,
        )
        self.assertEqual(
            hashlib.sha256((public / "TASK-039E3_R2R_EXECUTION_RECEIPT.json").read_bytes()).hexdigest(),
            SUCCESS_RECEIPT_BYTE_HASH,
        )
        self.assertEqual(
            hashlib.sha256((private / "final_authoritative_r2r_v1" / "TASK039E3_R2R_PROPOSAL_VALIDITY_LEDGER.json").read_bytes()).hexdigest(),
            PROPOSAL_LEDGER_BYTE_HASH,
        )
        self.assertEqual(
            hashlib.sha256((private / "scientific_r2r_v1" / "proposals_working.jsonl").read_bytes()).hexdigest(),
            WORKING_PROPOSAL_BYTE_HASH,
        )


if __name__ == "__main__":
    unittest.main()
