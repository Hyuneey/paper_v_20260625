from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, self_hashed
from paperworks.validation_v2.dg05_production_chain_v11r2r1 import (
    DG05ProductionChainV11R2R1Error, FINAL_CLOSURE_SCHEMA_V11R2R3,
    verify_runtime_approval_v11r2r1,
)


class ApprovalSchemaTests(unittest.TestCase):
    def test_exact_successor_closure_schema_replays_and_predecessor_schema_rejects(self):
        manifest = {"self_hash": "a" * 64, "execution_binding_hash": "b" * 64,
                    "implementation_source_commit": "c" * 40}
        body = {"schema": FINAL_CLOSURE_SCHEMA_V11R2R3, "status": "PASS",
                "release_hash": manifest["self_hash"], "execution_binding_hash": manifest["execution_binding_hash"],
                "implementation_source_commit": manifest["implementation_source_commit"],
                "v5_kernel_hash": "ea16f4475de97a224af35627cada524bca1183285cda0ebeede26b54d1b42525",
                "heldout_rows_parsed": 0, "heldout_predictions": 0, "heldout_metrics": 0,
                "metric_pipeline_pass": True, "full_synthetic_route_pass": True}
        closure = self_hashed(body)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "closure.json"; path.write_bytes(canonical_bytes(closure) + b"\n")
            self.assertEqual(verify_runtime_approval_v11r2r1(manifest=manifest, final_closure_path=path,
                approved_release_hash=manifest["self_hash"], approved_final_closure_hash=closure["self_hash"],
                approved_execution_binding_hash=manifest["execution_binding_hash"])["status"], "PASS")
            wrong = self_hashed({**{k:v for k,v in body.items() if k != "schema"}, "schema": "dg05_v11r2r2_final_e2e_fresh_process_closure_receipt_v1"})
            path.write_bytes(canonical_bytes(wrong) + b"\n")
            with self.assertRaises(DG05ProductionChainV11R2R1Error):
                verify_runtime_approval_v11r2r1(manifest=manifest, final_closure_path=path,
                    approved_release_hash=manifest["self_hash"], approved_final_closure_hash=wrong["self_hash"],
                    approved_execution_binding_hash=manifest["execution_binding_hash"])
