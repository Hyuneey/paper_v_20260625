from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_orchestration_v1 import (
    T0_TEMPLATE_HASH,
    wrap_and_verify_core_v1,
)
import paperworks.v6.task039e3_r2r_proposal_custody_v2 as custody
import paperworks.v6.task039e3_r2r_result_finalizer_v1 as finalizer
import paperworks.v6.task039e3_scientific_execution_v1 as execution
from task039e3_support import make_evidence, valid_core


ROOT = Path(__file__).resolve().parents[1]
BASE = "2be5426ff1ae3b8d2ffb1d935b180ec5eafa4226"
REMEDIATION_A = "77de8992f010e4331d6f4c024be4f6b8fa38517d"
REMEDIATION_B = "870e20db2515bd6a54dbf6a306fea05055ec0afd"
SOURCE_FREEZE_HASH = "47b014e9ffbd95c1a36f8579375f61a65fa344404c4a9aa5e77d056117dbfb73"
EXPECTED_SOURCE_PATHS = {
    "scripts/reconstruct_task039e3_r2r_terminal_custody_v1.py",
    "src/paperworks/v6/task039e3_r2r_proposal_custody_v2.py",
    "src/paperworks/v6/task039e3_r2r_result_finalizer_v1.py",
    "src/paperworks/v6/task039e3_scientific_execution_v1.py",
}
FROZEN_SCIENTIFIC_PATHS = (
    "src/paperworks/v6/task039e0_rule_construction_prep_v1.py",
    "src/paperworks/v6/task039e0_validity_v2.py",
    "src/paperworks/v6/task039e2_execution_configuration_v1.py",
    "src/paperworks/v6/task039e3_execution_prep_v1.py",
    "src/paperworks/v6/task039e3_orchestration_v1.py",
    "src/paperworks/v6/task039e3_r2r_request_contract_v1.py",
)


def _record():
    evidence = make_evidence(404)
    return wrap_and_verify_core_v1(
        core=valid_core(evidence),
        evidence=evidence,
        arm="T0",
        call_number=0,
        prompt_hash=T0_TEMPLATE_HASH,
    )


def _git(*arguments: str, binary: bool = False):
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


class IndependentFutureSerializerAuditTests(unittest.TestCase):
    def test_serialized_only_roundtrip_and_fail_closed_mutations(self) -> None:
        record = _record()
        serialized = json.loads(json.dumps(
            custody.serialize_construction_proposal_custody_record_v2(record),
            sort_keys=True,
            separators=(",", ":"),
        ))
        verified = custody.verify_serialized_construction_proposal_custody_record_v2(
            serialized
        )
        self.assertEqual(verified["proposal_hash"], record.proposal_hash)
        self.assertEqual(verified["validity_hash"], record.validity_hash)
        self.assertEqual(verified["record_hash"], record.record_hash)
        self.assertEqual(
            stable_hash_v1(custody.proposal_record_hash_preimage_v1(verified)),
            record.record_hash,
        )

        mutations = {
            "missing-envelope": lambda value: value.pop("proposal_envelope"),
            "evidence-hash": lambda value: value["proposal_envelope"].__setitem__("evidence_hash", "0" * 64),
            "prompt-hash": lambda value: value["proposal_envelope"].__setitem__("prompt_hash", "0" * 64),
            "proposal-core": lambda value: value["proposal_envelope"]["proposal_core"].__setitem__("source", "ALTERED"),
            "proposal-hash": lambda value: value.__setitem__("proposal_hash", "0" * 64),
            "validity-hash": lambda value: value.__setitem__("validity_hash", "0" * 64),
            "record-hash": lambda value: value.__setitem__("record_hash", "0" * 64),
            "arm-mismatch": lambda value: value.__setitem__("arm", "T1"),
            "call-mismatch": lambda value: value.__setitem__("call_number", 1),
        }
        for label, mutate in mutations.items():
            altered = copy.deepcopy(serialized)
            mutate(altered)
            with self.subTest(label=label):
                with self.assertRaises(custody.TASK039E3ProposalCustodyError):
                    custody.verify_serialized_construction_proposal_custody_record_v2(
                        altered
                    )

    def test_working_and_final_paths_share_one_canonical_serializer(self) -> None:
        canonical = custody.serialize_construction_proposal_custody_record_v2
        self.assertIs(
            execution.DurableConstructionProposalLedgerV1.append.__globals__[
                "serialize_construction_proposal_custody_record_v2"
            ],
            canonical,
        )
        self.assertIs(
            finalizer._proposal_custody_record_v2.__globals__[
                "serialize_construction_proposal_custody_record_v2"
            ],
            canonical,
        )
        record = _record()
        expected = canonical(record)
        self.assertEqual(finalizer._proposal_custody_record_v2(record), expected)

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "proposals_working.jsonl"
            ledger = execution.DurableConstructionProposalLedgerV1(path)
            ledger.append(record)
            ledger.close()
            del record
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted, expected)
            custody.verify_serialized_construction_proposal_custody_record_v2(
                persisted
            )
            self.assertEqual(finalizer._proposal_custody_record_v2(persisted), expected)

    def test_source_delta_is_custody_only_and_formulas_are_frozen(self) -> None:
        changed = set(_git("diff", "--name-only", BASE, REMEDIATION_A).splitlines())
        changed_source = {path for path in changed if not path.startswith("tests/")}
        self.assertEqual(changed_source, EXPECTED_SOURCE_PATHS)
        self.assertEqual(
            _git("diff", "--name-only", REMEDIATION_A, REMEDIATION_B, "--", "src", "scripts"),
            "",
        )
        for path in FROZEN_SCIENTIFIC_PATHS:
            self.assertEqual(
                _git("rev-parse", f"{BASE}:{path}").strip(),
                _git("rev-parse", f"{REMEDIATION_A}:{path}").strip(),
                path,
            )

    def test_source_freeze_self_hash_and_exact_git_bytes(self) -> None:
        path = ROOT / "docs/task_reports/TASK-039E3_R2R_TERMINAL_CUSTODY_REMEDIATION_SOURCE_FREEZE.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(document["artifact_hash"], SOURCE_FREEZE_HASH)
        self.assertEqual(
            stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"}),
            SOURCE_FREEZE_HASH,
        )
        self.assertEqual(len(document["source_records"]), 4)
        self.assertEqual(
            {item["path"] for item in document["source_records"]},
            EXPECTED_SOURCE_PATHS,
        )
        for item in document["source_records"]:
            blob = _git("cat-file", "blob", item["git_blob_sha"], binary=True)
            self.assertEqual(hashlib.sha256(blob).hexdigest(), item["byte_sha256"])
            self.assertEqual(
                _git("rev-parse", f"{REMEDIATION_A}:{item['path']}").strip(),
                item["git_blob_sha"],
            )
            self.assertEqual((ROOT / item["path"]).read_bytes(), blob)
        self.assertFalse(document["record_hash_formula_changed"])
        self.assertFalse(document["scientific_semantics_changed"])
        self.assertTrue(document["custody_serialization_changed"])


if __name__ == "__main__":
    unittest.main()
