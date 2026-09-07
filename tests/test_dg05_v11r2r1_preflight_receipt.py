from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, self_hashed
from paperworks.validation_v2.dg05_v11r2r1_preflight_receipt import (
    DG05V11R2R1PreflightReceiptError,
    build_real_preflight_receipt_v11r2r1,
    persist_real_preflight_receipt_v11r2r1,
    verify_real_preflight_receipt_v11r2r1,
)


def h(letter: str) -> str:
    return letter * 64


class V11R2R1PreflightReceiptTests(unittest.TestCase):
    def _manifest(self) -> dict[str, str]:
        return {
            "self_hash": h("a"), "execution_binding_hash": h("b"),
            "implementation_source_commit": "c" * 40,
            "scenario_authority_hash": h("d"), "p1_authority_hash": h("e"),
            "source_file_crosswalk_hash": h("f"),
        }

    def _approval(self) -> dict[str, str]:
        return self_hashed({"schema": "synthetic_runtime_approval_replay_v1", "status": "PASS",
                            "release_hash": h("a"), "final_closure_hash": h("1"),
                            "execution_binding_hash": h("b")})

    def _bundle(self, **overrides: object) -> dict[str, object]:
        fields: dict[str, object] = {
            "schema": "dg05_v11r2r1_complete_real_preflight_authority_replay_v1", "status": "PASS",
            "implementation_replay_hash": h("2"), "execution_binding_hash": h("b"),
            "execution_binding_replay_hash": h("c"),
            "v5_kernel_hash": h("3"), "legacy_hash": h("4"), "v4_hash": h("5"),
            "v4_closure_hash": h("6"), "v1_hash": h("7"), "legacy_predecessor_replay_hash": h("8"), "physical_hash": h("8"),
            "framing_hash": h("9"), "production_executor_hash": h("0"), "normal_authority_hash": h("a"),
            "scenario_hash": h("d"), "p1_hash": h("e"), "crosswalk_hash": h("f"),
            "crosswalk_replay_hash": h("1"), "execution_scope_id": h("2"),
            "ledger_status_hash": h("3"),
            "heldout_rows_parsed": 0, "heldout_predictions": 0, "heldout_metrics": 0,
        }
        fields.update(overrides)
        return self_hashed(fields)

    def _ledger(self) -> dict[str, object]:
        return self_hashed({"schema": "dg05_v11r2_execution_ledger_scope_status_v1",
                            "status": "UNUSED", "execution_scope_id": h("2"), "state_hashes": {}})

    def test_receipt_is_only_constructed_from_self_hashed_actual_replay(self):
        receipt = build_real_preflight_receipt_v11r2r1(
            manifest=self._manifest(), approval_replay=self._approval(),
            replay_bundle=self._bundle(), ledger_status=self._ledger(),
        )
        self.assertEqual(receipt["status"], "REAL_PREFLIGHT_PASS_NO_FEATURE_ACCESS")
        self.assertNotIn("production_asset_census", receipt)
        self.assertEqual(receipt["execution_consumed"], False)
        self.assertEqual(receipt["heldout_rows_parsed"], 0)

    def test_receipt_lies_and_bad_roots_are_rejected_before_persistence(self):
        for mutated in (
            self._bundle(production_executor_hash="not-a-hash"),
            self._bundle(normal_authority_hash="not-a-hash"),
            self._bundle(scenario_hash=h("c")),
            self._bundle(p1_hash=h("c")),
            self._bundle(crosswalk_hash=h("c")),
            self._bundle(heldout_predictions=1),
        ):
            with self.assertRaises(DG05V11R2R1PreflightReceiptError):
                build_real_preflight_receipt_v11r2r1(
                    manifest=self._manifest(), approval_replay=self._approval(),
                    replay_bundle=mutated, ledger_status=self._ledger(),
                )

    def test_stored_receipt_requires_identical_fresh_immutable_replay(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "receipt.json"
            receipt = build_real_preflight_receipt_v11r2r1(
                manifest=self._manifest(), approval_replay=self._approval(),
                replay_bundle=self._bundle(), ledger_status=self._ledger(),
            )
            persist_real_preflight_receipt_v11r2r1(path=path, receipt=receipt)
            self.assertEqual(verify_real_preflight_receipt_v11r2r1(
                receipt_path=path, manifest=self._manifest(), approval_replay=self._approval(),
                fresh_replay_bundle=self._bundle(), ledger_status=self._ledger(),
            )["self_hash"], receipt["self_hash"])
            with self.assertRaises(DG05V11R2R1PreflightReceiptError):
                verify_real_preflight_receipt_v11r2r1(
                    receipt_path=path, manifest=self._manifest(), approval_replay=self._approval(),
                    fresh_replay_bundle=self._bundle(normal_authority_hash=h("c")), ledger_status=self._ledger(),
                )

    def test_persist_is_append_only(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "receipt.json"
            receipt = build_real_preflight_receipt_v11r2r1(
                manifest=self._manifest(), approval_replay=self._approval(),
                replay_bundle=self._bundle(), ledger_status=self._ledger(),
            )
            persist_real_preflight_receipt_v11r2r1(path=path, receipt=receipt)
            with self.assertRaises(DG05V11R2R1PreflightReceiptError):
                persist_real_preflight_receipt_v11r2r1(path=path, receipt=receipt)


if __name__ == "__main__":
    unittest.main()
