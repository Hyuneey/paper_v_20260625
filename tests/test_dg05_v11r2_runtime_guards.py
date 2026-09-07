from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, self_hashed
from paperworks.validation_v2.dg05_v11r2_execution_ledger import (
    DG05V11R2ExecutionLedgerError, append_contact_guard_v11r2, append_terminal_state_v11r2,
    execution_scope_id_v11r2, ledger_scope_status_v11r2, start_real_execution_v11r2,
)
from paperworks.validation_v2.dg05_v11r2_runtime_approval_guard import (
    DG05V11R2RuntimeApprovalError, verify_runtime_approval_v11r2,
)


H = "a" * 64
V5 = "ea16f4475de97a224af35627cada524bca1183285cda0ebeede26b54d1b42525"


class V11R2RuntimeGuardTests(unittest.TestCase):
    def _closure(self, root: Path, *, release: str = H, binding: str = "b" * 64) -> Path:
        path = root / "closure.json"
        doc = self_hashed({"schema": "dg05_v11r2_final_e2e_fresh_process_closure_receipt_v1", "status": "PASS",
                           "release_hash": release, "execution_binding_hash": binding,
                           "implementation_source_commit": "c" * 40, "v5_kernel_hash": V5,
                           "heldout_rows_parsed": 0, "heldout_predictions": 0, "heldout_metrics": 0,
                           "metric_pipeline_pass": True, "full_synthetic_route_pass": True})
        path.write_bytes(canonical_bytes(doc) + b"\n"); return path

    def test_closure_and_all_three_approved_roots_are_required(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); closure = self._closure(root)
            manifest = {"self_hash": H, "execution_binding_hash": "b" * 64, "implementation_source_commit": "c" * 40}
            receipt = verify_runtime_approval_v11r2(manifest=manifest, final_closure_path=closure,
                approved_release_hash=H, approved_final_closure_hash=self_hashed({"schema": "dg05_v11r2_final_e2e_fresh_process_closure_receipt_v1", "status": "PASS", "release_hash": H, "execution_binding_hash": "b" * 64, "implementation_source_commit": "c" * 40, "v5_kernel_hash": V5, "heldout_rows_parsed": 0, "heldout_predictions": 0, "heldout_metrics": 0, "metric_pipeline_pass": True, "full_synthetic_route_pass": True})["self_hash"], approved_execution_binding_hash="b" * 64)
            self.assertEqual(receipt["status"], "PASS")
            with self.assertRaises(DG05V11R2RuntimeApprovalError):
                verify_runtime_approval_v11r2(manifest=manifest, final_closure_path=closure, approved_release_hash=H,
                    approved_final_closure_hash="d" * 64, approved_execution_binding_hash="b" * 64)

    def test_scope_is_release_tuple_not_output_root_and_contact_consumes_it(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); start = start_real_execution_v11r2(ledger_root=root, release_hash=H,
                final_closure_hash="c" * 64, execution_binding_hash="b" * 64, preflight_receipt_hash="d" * 64,
                physical_custody_hash="e" * 64, output_namespace="first")
            self.assertEqual(start["execution_scope_id"], execution_scope_id_v11r2(release_hash=H, final_closure_hash="c" * 64, execution_binding_hash="b" * 64))
            append_contact_guard_v11r2(ledger_root=root, start_state=start)
            with self.assertRaises(DG05V11R2ExecutionLedgerError):
                start_real_execution_v11r2(ledger_root=root, release_hash=H, final_closure_hash="c" * 64,
                    execution_binding_hash="b" * 64, preflight_receipt_hash="d" * 64,
                    physical_custody_hash="e" * 64, output_namespace="different-output-root")

    def test_precontact_abort_and_contact_boundary_failure_are_both_nonretryable(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            started = start_real_execution_v11r2(ledger_root=root, release_hash=H, final_closure_hash="c" * 64,
                execution_binding_hash="b" * 64, preflight_receipt_hash="d" * 64, physical_custody_hash="e" * 64,
                output_namespace="before-contact")
            aborted = append_terminal_state_v11r2(ledger_root=root, predecessor=started, state_name="PRECONTACT_ABORTED")
            self.assertEqual(aborted["state"], "PRECONTACT_ABORTED")
            with self.assertRaises(DG05V11R2ExecutionLedgerError):
                start_real_execution_v11r2(ledger_root=root, release_hash=H, final_closure_hash="c" * 64,
                    execution_binding_hash="b" * 64, preflight_receipt_hash="d" * 64, physical_custody_hash="e" * 64,
                    output_namespace="retry")

    def test_ledger_rejects_retroactive_or_forged_transitions(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            start = start_real_execution_v11r2(ledger_root=root, release_hash=H, final_closure_hash="c" * 64,
                execution_binding_hash="b" * 64, preflight_receipt_hash="d" * 64, physical_custody_hash="e" * 64,
                output_namespace="one")
            self.assertEqual(ledger_scope_status_v11r2(ledger_root=root, release_hash=H, final_closure_hash="c" * 64,
                execution_binding_hash="b" * 64)["status"], "CONSUMED")
            with self.assertRaises(DG05V11R2ExecutionLedgerError):
                append_terminal_state_v11r2(ledger_root=root, predecessor=start, state_name="METRICS_FROZEN")
            forged = {**start, "execution_binding_hash": "f" * 64}
            with self.assertRaises(DG05V11R2ExecutionLedgerError):
                append_contact_guard_v11r2(ledger_root=root, start_state=forged)
            contact = append_contact_guard_v11r2(ledger_root=root, start_state=start)
            predictions = append_terminal_state_v11r2(ledger_root=root, predecessor=contact, state_name="PREDICTIONS_FROZEN")
            metrics = append_terminal_state_v11r2(ledger_root=root, predecessor=predictions, state_name="METRICS_FROZEN")
            terminal = append_terminal_state_v11r2(ledger_root=root, predecessor=metrics, state_name="TERMINAL_COMPLETE")
            self.assertEqual(terminal["execution_binding_hash"], "b" * 64)


if __name__ == "__main__": unittest.main()
