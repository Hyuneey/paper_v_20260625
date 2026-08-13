from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_INVENTORY_HASH = "0dd0792e95066bbff3a5b28f69adec81307fe6b0a6b3a4d45bfbd837d9b9aa1b"
PRIVATE_INVENTORY_HASH = "56c1cb6fc14be6742d88ba681987398d7d0b02cb19759b6d7b4d572cfd0e011a"
PUBLIC_HASHES = {
    "TASK-039E3_R2R_CAPABILITY_REUSE_BINDING.json": "cc240a511bc701518f2208882b71456397b3864e0d6d3fc259960a2a4299334e",
    "TASK-039E3_R2R_PROVIDER_CUSTODY_BINDING.json": "3692354bfe41eacdb1475b10a013e10a6e08320033b880825abd71714bc06717",
    "TASK-039E3_R2R_PRIVATE_LEDGER_BINDINGS.json": "6caf7e285f6ba0da8859f44a280b961ac945319732b77ea08bc60037a99fe54f",
    "TASK-039E3_R2R_CONSTRUCTION_METRICS.json": "c3758bbdba4bd85799dc86d4cff1eeb395190d27317f7a857ee54b279f4848b8",
    "TASK-039E3_R2R_DIRECT_NUMBER_METRICS.json": "3848ed1650c67522b2acc47f9543b1545f0d39f74488eb58d82173d250da115e",
    "TASK-039E3_R2R_EXECUTION_SUMMARY.json": "af88ac3df00954d483d46d89c4fa2e9813ccf7138303a8bac913e7579dafc8e9",
    "TASK-039E3_R2R_DATA_ACCESS_AUDIT.json": "815b3fe1176d87c8277deb51a6a72d0110e0b41456e19be728dd201f560628cd",
    "TASK-039E3_R2R_EXECUTION_RECEIPT.json": "d164f00da3121e345907fe9076e62f4697493f26dde7448cc8527b895cbffa6e",
}
PRIVATE_HASHES = {
    "TASK039E3_R2R_SCIENTIFIC_PROVIDER_LEDGER.json": "dd63972ae1a49fb86ce3020e472b67ece54ca4aadc19dd9311c415fce0234664",
    "TASK039E3_R2R_PROPOSAL_VALIDITY_LEDGER.json": "1d573ae83a147edf4aacb2a806016d7cfaf23b90d17e11e4e7b3c885c30e0e93",
    "TASK039E3_R2R_CONSTRUCTION_OUTCOME_LEDGER.json": "991a289a6936b9b3a6c4481ac8f700da1fee7ca9267dc4e0c013ac4411094057",
    "TASK039E3_R2R_DIRECT_NUMBER_LEDGER.json": "e39a28c5199345471727648930ffbfe4cf96aac73e484cef9f208a306f2c002f",
}


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("JSON object required")
    return value


def _verify(document: dict[str, object], expected: str) -> None:
    self_hash = document.get("artifact_hash")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if self_hash != expected or stable_hash_v1(payload) != expected:
        raise AssertionError("artifact hash differs")


def _inventory(root: Path) -> tuple[str, int]:
    entries: list[dict[str, object]] = []
    file_count = 0
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries.append({"path": relative, "kind": "link"})
        elif path.is_dir():
            entries.append({"path": relative, "kind": "directory"})
        elif path.is_file():
            payload = path.read_bytes()
            file_count += 1
            entries.append(
                {
                    "path": relative,
                    "kind": "file",
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        else:
            entries.append({"path": relative, "kind": "other"})
    return stable_hash_v1({"entries": entries}), file_count


def _nested(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
    except ValueError:
        return False
    return True


@unittest.skipUnless(
    all(
        os.environ.get(name)
        for name in (
            "TASK039E3_SUCCESS_PUBLIC_ROOT",
            "TASK039E3_SUCCESS_PRIVATE_ROOT",
            "TASK039E3_CUSTODY_SUPPLEMENT",
            "TASK039E3_E1_LEDGER",
        )
    ),
    "task-local original custody paths are intentionally external",
)
class IndependentOriginalImmutabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.public = Path(os.environ["TASK039E3_SUCCESS_PUBLIC_ROOT"]).resolve(strict=True)
        self.private = Path(os.environ["TASK039E3_SUCCESS_PRIVATE_ROOT"]).resolve(strict=True)
        self.supplement = Path(os.environ["TASK039E3_CUSTODY_SUPPLEMENT"]).resolve(strict=True)
        self.e1 = Path(os.environ["TASK039E3_E1_LEDGER"]).resolve(strict=True).parent

    def test_original_terminal_artifacts_and_full_inventories_unchanged(self) -> None:
        public_inventory, public_files = _inventory(self.public)
        private_inventory, private_files = _inventory(self.private)
        self.assertEqual((public_inventory, public_files), (PUBLIC_INVENTORY_HASH, 8))
        self.assertEqual((private_inventory, private_files), (PRIVATE_INVENTORY_HASH, 263))
        self.assertEqual({path.name for path in self.public.iterdir()}, set(PUBLIC_HASHES))
        for name, expected in PUBLIC_HASHES.items():
            _verify(_read(self.public / name), expected)
        final = self.private / "final_authoritative_r2r_v1"
        self.assertEqual({path.name for path in final.iterdir()}, set(PRIVATE_HASHES))
        for name, expected in PRIVATE_HASHES.items():
            _verify(_read(final / name), expected)

    def test_supplement_is_distinct_outside_and_unnested(self) -> None:
        supplement_root = self.supplement.parent
        self.assertTrue(self.supplement.is_file())
        self.assertFalse(self.supplement.is_symlink())
        for protected in (self.public, self.private, self.e1):
            self.assertNotEqual(supplement_root, protected)
            self.assertFalse(_nested(supplement_root, protected))
            self.assertFalse(_nested(protected, supplement_root))

    def test_prior_terminal_audit_has_exactly_one_carried_blocker(self) -> None:
        receipt = _read(
            ROOT / "docs/task_reports/TASK-039E3_R2R_TERMINAL_AUDIT_RECEIPT.json"
        )
        _verify(
            receipt,
            "6a2f3bd18e2df370eaee5bb5da95bc12c7f3da72eff11b82fd06b3775191614b",
        )
        self.assertEqual(receipt["blocking_finding_count"], 1)
        self.assertEqual(
            receipt["execution_receipt_hash"],
            PUBLIC_HASHES["TASK-039E3_R2R_EXECUTION_RECEIPT.json"],
        )
        evaluability = _read(
            ROOT / "docs/task_reports/TASK-039E3_R2R_TERMINAL_AUDIT_EVALUABILITY.json"
        )
        _verify(
            evaluability,
            "e39801cd1c6830d2f5032081c42dad8112e4363cc404bb7512192a99a40fb8a5",
        )
        self.assertEqual(evaluability["blocking_finding_count"], 1)
        self.assertEqual(len(evaluability["blocking_findings"]), 1)
        self.assertEqual(
            evaluability["blocking_findings"][0]["classification"],
            "BLOCKER_RESULT_CUSTODY_PROPOSAL_RECORD_HASH_PREIMAGE_OMITTED",
        )
        self.assertEqual(
            receipt["component_audit_hashes"],
            {
                "accounting": "6ce9557f502546f318205f203fb14a129de904f02fa74f89c98d9b1af7592f83",
                "custody": "637d0e5f346895fb73a1049aaab9833db2af2bb14bcafdb664d5f991be4e0335",
                "evaluability": "e39801cd1c6830d2f5032081c42dad8112e4363cc404bb7512192a99a40fb8a5",
                "metrics": "2bcc1cd01adb1bd6ce0f89ca587dbb9cfc9e4ba4e51d3c00788fcda567d4a56e",
                "private": "b3cc3b7a3d20ed513893109be07623930cdcad6fdc808c5dbd579e9caefaac71",
                "public": "e21ed242d8bbf13e565e5f5da61aa7229ab61ea2067dc7f5db13ed6bf6410456",
                "test_report": "6e5e9bd68d240cab2098c61fb2b41d881f5cbdad1f9c1f5c2389da0f587042ce",
            },
        )


if __name__ == "__main__":
    unittest.main()
