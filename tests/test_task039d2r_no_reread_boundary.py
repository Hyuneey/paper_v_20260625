from __future__ import annotations

import ast
import unittest
from pathlib import Path

from paperworks.profiling.task039d2_result_recovery_v1 import build_recovery_data_access_audit_v1


ROOT = Path(__file__).resolve().parents[1]


class TASK039D2RNoRereadBoundaryTests(unittest.TestCase):
    def test_finalizer_has_no_hai_loader_or_dataset_root(self) -> None:
        path = ROOT / "scripts/finalize_task039d2_from_frozen_ledger.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
        } | {
            node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(any(name.endswith("task039d2_real_execution_v1") for name in imported_modules))
        self.assertFalse(any(name.endswith("task039d1_fit_v1") for name in imported_modules))
        for forbidden in ("HAI_DATA_ROOT", "load_authorized_train3_values_v1", "confirm_relations_one_way_v1"):
            self.assertNotIn(forbidden, source)

    def test_recovery_access_audit_distinguishes_original_and_recovery(self) -> None:
        audit = build_recovery_data_access_audit_v1()
        self.assertTrue(audit["original_scientific_run"]["train3_accessed"])
        self.assertFalse(audit["recovery_finalization"]["train3_accessed"])
        self.assertFalse(audit["recovery_finalization"]["train3_reread"])
        self.assertFalse(audit["recovery_finalization"]["hai_feature_values_accessed"])


if __name__ == "__main__":
    unittest.main()
