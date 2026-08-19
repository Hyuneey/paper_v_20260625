"""Independent public-only attacks for Utility Protocol V4.

The oracle rebuilds lower authorities without opening the private numeric
registry or any HAI file.  Production V4 validators are attack subjects, not
the source of the expected COMMON, reference, schema, or regression values.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "audit_task039e3_r2r_utility_protocol_v4.py"
SPEC = importlib.util.spec_from_file_location("task039e3_v4_independent_oracle", HELPER)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import bootstrap
    raise RuntimeError("AUDIT_HELPER_IMPORT")
ORACLE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ORACLE
SPEC.loader.exec_module(ORACLE)


class UtilityProtocolV4IndependentAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = ORACLE.audit_summary(ROOT)

    def assert_no_invalid_acceptance(self, *categories: str) -> None:
        accepted = {
            name: self.summary["attacks"][name]["accepted_case_ids"]
            for name in categories
            if self.summary["attacks"][name]["accepted"]
        }
        self.assertEqual(accepted, {}, f"AUDIT_ACCEPTED_INVALID_CASES:{accepted}")

    def test_lower_authority_replay(self) -> None:
        self.assertEqual(self.summary["common"], {
            "relations": 42,
            "references": 420,
            "sources": 9,
            "targets": 10,
        })
        self.assertEqual(
            self.summary["numeric_descriptor_hash"],
            "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928",
        )
        self.assertEqual(
            self.summary["reference_set_hash"],
            "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae",
        )

    def test_numeric_common_and_rule_attacks(self) -> None:
        self.assertGreaterEqual(self.summary["attacks"]["t2"]["cases"], 3)
        self.assertGreaterEqual(
            self.summary["attacks"]["numeric"]["cases"]
            + self.summary["attacks"]["references"]["cases"],
            10,
        )
        self.assertGreaterEqual(self.summary["attacks"]["rules"]["cases"], 7)
        self.assert_no_invalid_acceptance("t2", "numeric", "references", "rules")

    def test_opportunity_and_census_attacks(self) -> None:
        self.assertGreaterEqual(self.summary["attacks"]["opportunity"]["cases"], 17)
        self.assertGreaterEqual(self.summary["attacks"]["census"]["cases"], 7)
        self.assert_no_invalid_acceptance("opportunity", "census")

    def test_feature_and_scalar_attacks(self) -> None:
        feature = self.summary["feature"]
        self.assertEqual(
            (feature["evaluator_sources"], feature["evaluator_targets"], feature["evaluator_union"]),
            (12, 10, 22),
        )
        self.assertEqual(
            (feature["common_sources"], feature["common_targets"], feature["common_union"]),
            (9, 10, 19),
        )
        self.assertGreaterEqual(self.summary["attacks"]["feature"]["cases"], 8)
        self.assertGreaterEqual(self.summary["attacks"]["scalar"]["cases"], 12)
        self.assert_no_invalid_acceptance("feature", "scalar")

    def test_terminal_provenance_attacks(self) -> None:
        self.assertGreaterEqual(self.summary["attacks"]["terminal"]["cases"], 10)
        self.assert_no_invalid_acceptance("terminal")

    def test_regression_authorities(self) -> None:
        self.assertEqual(
            tuple(self.summary["regression_hashes"]),
            ORACLE.CORRECTED_REGRESSION_HASHES,
        )
        self.assert_no_invalid_acceptance("regression")

    def test_total_independent_attack_coverage(self) -> None:
        self.assertGreaterEqual(self.summary["totals"]["cases"], 77)


if __name__ == "__main__":
    unittest.main()
