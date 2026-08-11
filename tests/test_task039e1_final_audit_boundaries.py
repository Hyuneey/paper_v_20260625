from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperworks.v6.task039e1_final_audit_v1 import (
    TASK039E1FinalAuditError,
    assert_public_safe_v1,
    validate_external_roots_v1,
)


class FinalAuditBoundaryTests(unittest.TestCase):
    def test_four_distinct_outside_roots_are_required_and_audit_is_fresh(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            d1, d2, e1 = (base / name for name in ("d1", "d2", "e1"))
            for path in (d1, d2, e1):
                path.mkdir()
            audit = base / "audit"
            roots = validate_external_roots_v1(
                repository_root=repository,
                d1_private_value=str(d1),
                d2_private_value=str(d2),
                e1_private_value=str(e1),
                audit_private_value=str(audit),
            )
            self.assertEqual(4, len(set(roots)))
            self.assertTrue(audit.is_dir())
            with self.assertRaises(TASK039E1FinalAuditError):
                validate_external_roots_v1(
                    repository_root=repository,
                    d1_private_value=str(d1),
                    d2_private_value=str(d2),
                    e1_private_value=str(e1),
                    audit_private_value=str(audit),
                )

    def test_repository_containment_is_rejected(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            d2, e1 = base / "d2", base / "e1"
            d2.mkdir()
            e1.mkdir()
            inside = repository / ".task039e1-audit-boundary-test"
            inside.mkdir(exist_ok=False)
            try:
                with self.assertRaises(TASK039E1FinalAuditError):
                    validate_external_roots_v1(
                        repository_root=repository,
                        d1_private_value=str(inside),
                        d2_private_value=str(d2),
                        e1_private_value=str(e1),
                        audit_private_value=str(base / "audit"),
                    )
            finally:
                inside.rmdir()

    def test_public_scan_rejects_private_values_and_absolute_paths(self) -> None:
        assert_public_safe_v1(
            {"role_frequencies": {"source_step_threshold": 42}}
        )
        with self.assertRaises(TASK039E1FinalAuditError):
            assert_public_safe_v1({"numeric_value": 3.0})
        with self.assertRaises(TASK039E1FinalAuditError):
            assert_public_safe_v1({"path": "C:\\private\\ledger.json"})


if __name__ == "__main__":
    unittest.main()
