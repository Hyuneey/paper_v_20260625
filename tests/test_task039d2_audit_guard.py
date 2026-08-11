from __future__ import annotations

import ast
import inspect
from pathlib import Path
import unittest
from unittest.mock import patch

from paperworks.profiling import task039d2_audit_accounting_v1 as accounting
from paperworks.profiling import task039d2_audit_reference_v1 as reference
from paperworks.profiling.task039d2_audit_reference_v1 import (
    TASK039D2AuditPreparationError,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCES,
    FROZEN_TARGETS,
)


ROOT = Path(__file__).resolve().parents[1]


class AuditPreparationDataGuardTests(unittest.TestCase):
    def test_all_real_authorities_and_scientific_outcomes_remain_false(self) -> None:
        self.assertFalse(reference.D2_AUDIT_REAL_EXECUTION_AUTHORIZED)
        self.assertFalse(reference.D1_PRIVATE_LEDGER_ACCESS_AUTHORIZED)
        self.assertFalse(reference.D2_RESULT_AUDITED)
        self.assertFalse(reference.RULE_V2_AUTHORIZED)

    def test_real_access_request_fails_closed(self) -> None:
        for request in (
            {"real_hai_access": True, "train3_access": False, "d1_private_ledger_access": False},
            {"real_hai_access": False, "train3_access": True, "d1_private_ledger_access": False},
            {"real_hai_access": False, "train3_access": False, "d1_private_ledger_access": True},
        ):
            with self.subTest(request=request):
                with self.assertRaisesRegex(
                    TASK039D2AuditPreparationError, "synthetic-only"
                ):
                    accounting.assert_audit_preparation_data_boundary_v1(**request)

    def test_d2_authorization_does_not_grant_audit_prep_execution(self) -> None:
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError,
            "never grants audit-preparation real execution",
        ):
            accounting.assert_audit_preparation_data_boundary_v1(
                real_hai_access=False,
                train3_access=False,
                d1_private_ledger_access=False,
                d2_authorization_supplied=object(),
            )

    def test_file_entrypoint_stops_before_opening_any_file(self) -> None:
        with patch("builtins.open") as mocked_open:
            with self.assertRaisesRegex(
                TASK039D2AuditPreparationError, "not authorized"
            ):
                accounting.audit_completed_d2_from_files_v1(
                    "hai-train3.csv", "private-d1-ledger.json"
                )
            mocked_open.assert_not_called()

    def test_task_modules_have_no_file_io_calls_or_production_engine_import(self) -> None:
        for module in (reference, accounting):
            tree = ast.parse(inspect.getsource(module))
            called_names = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            self.assertNotIn("open", called_names)
            self.assertNotIn("Path", called_names)
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            }
            self.assertFalse(
                any("task039d2_confirmation_v1" in name for name in imports)
            )
            self.assertFalse(any("runtime" in name for name in imports))
            self.assertFalse(any("agent" in name for name in imports))

    def test_synthetic_fixture_contract_rejects_unmarked_values(self) -> None:
        values = {
            name: [0.0] * 10 for name in (*FROZEN_SOURCES, *FROZEN_TARGETS)
        }
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "clearly marked synthetic"
        ):
            reference.SyntheticAuditValueMapV1(
                fixture_id="train3", values=values
            )
        with self.assertRaisesRegex(
            TASK039D2AuditPreparationError, "synthetic values only"
        ):
            reference.SyntheticAuditValueMapV1(
                fixture_id="synthetic_audit_rejected",
                values=values,
                synthetic_only=False,
            )

    def test_no_d2_audit_result_or_authority_artifact_is_created(self) -> None:
        forbidden = (
            "TASK-039D2_AUDIT_RESULT.json",
            "TASK-039D2_RULE_V2_AUTHORITY.json",
            "TASK-039D2_CONSTRUCTION_PRIMITIVES.json",
        )
        for name in forbidden:
            self.assertFalse((ROOT / "docs" / "task_reports" / name).exists())


if __name__ == "__main__":
    unittest.main()
