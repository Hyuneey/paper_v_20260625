from __future__ import annotations

import json
from pathlib import Path
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import FROZEN_SOURCES, SOURCE_IDENTITY_HASH
from paperworks.v6.task039e3_r2r_utility_protocol_v1 import UtilityProtocolError, is_synthetic_event_isolated_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


def _document(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


class IndependentReferenceAndEquivalenceAuditTests(unittest.TestCase):
    def test_historical_source_universe_is_unique(self) -> None:
        self.assertEqual(len(FROZEN_SOURCES), 12)
        self.assertEqual(len(set(FROZEN_SOURCES)), 12)
        self.assertEqual(
            SOURCE_IDENTITY_HASH,
            "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234",
        )

    def test_protocol_fails_to_bind_historical_source_universe(self) -> None:
        interpreter = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_INTERPRETER_POLICY.json")
        authority = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_AUTHORITY_POLICY.json")
        self.assertEqual(interpreter["source_event"]["source_stream_scope"], "all_12_frozen_P1_source_streams")
        serialized = json.dumps({"interpreter": interpreter, "authority": authority}, sort_keys=True)
        self.assertNotIn(SOURCE_IDENTITY_HASH, serialized)
        self.assertNotIn("relation_profiling_protocol_v1.py", serialized)

    def test_synthetic_isolation_accepts_an_arbitrary_subset_as_authority(self) -> None:
        supplied = ("one", "two")
        self.assertTrue(
            is_synthetic_event_isolated_v1(
                source="one",
                event_index=10,
                retained_events_by_source={"one": (10,), "two": (13,)},
                required_sources=supplied,
            )
        )
        with self.assertRaises(UtilityProtocolError):
            is_synthetic_event_isolated_v1(
                source="one",
                event_index=10,
                retained_events_by_source={"one": (10,)},
                required_sources=supplied,
            )

    def test_public_equivalence_artifact_has_closed_counts(self) -> None:
        value = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        observed = value["artifact_hash"]
        self.assertEqual(observed, stable_hash_v1({k: v for k, v in value.items() if k != "artifact_hash"}))
        self.assertEqual(value["T0_T1_T1B_equivalent_relation_count"], 42)
        self.assertEqual(value["T2_accepted_equivalent_count"], 39)
        self.assertEqual(value["T2_no_rule_count"], 3)
        self.assertFalse(value["identical_projections_treated_as_independent_predictions"])
        self.assertEqual(len(value["relation_records"]), 42)

    def test_numeric_reference_identifiers_are_closed_but_private_values_are_not_a_public_authority(self) -> None:
        value = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json")
        references: set[str] = set()
        for record in value["relation_records"]:
            signature = record["executable_signature"]
            references.update(
                (
                    signature["source_threshold_reference"],
                    signature["source_stability_reference"],
                    signature["target_scale_reference"],
                )
            )
            references.update(signature["window_constant_references"].values())
        self.assertEqual(len(references), 420)
        interpreter = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_INTERPRETER_POLICY.json")
        self.assertEqual(interpreter["parameter_policy"]["missing_or_mismatched_reference"], "FAIL_CLOSED")
        self.assertNotIn("authoritative_private_ledger_hash", interpreter["parameter_policy"])


if __name__ == "__main__":
    unittest.main()
