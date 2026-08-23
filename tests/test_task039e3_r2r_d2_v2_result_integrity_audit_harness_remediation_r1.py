from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d2_v2_r1_harness",
    ROOT / "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r1.py",
)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


def synthetic_horizon(entries: list[dict[str, object]]) -> tuple[dict[str, object], str, str]:
    inner = {
        "artifact_type": "synthetic_native_horizon_map",
        "entries": entries,
    }
    map_hash = subject.stable(inner)
    inner["map_hash"] = map_hash
    outer = {
        "artifact_type": "synthetic_horizon_wrapper",
        "native_horizon_map": inner,
        "missing_horizon_count": 0,
        "ambiguous_horizon_count": 0,
        "label_derived_horizon_count": 0,
        "test1_derived_horizon_count": 0,
        "foreign_relation_count": 0,
    }
    outer_hash = subject.stable(outer)
    outer["artifact_hash"] = outer_hash
    return outer, outer_hash, map_hash


def synthetic_result() -> subject.FrozenR1AuditResult:
    metric = {
        "d2_detected": 11,
        "d2_false": 98,
        "normal_seconds": 51019,
        "d0_detected": 11,
        "d0_false": 7,
        "d0_missed": 3,
        "recovered": 0,
        "recovery_false": 92,
        "d0_recall": 0.7857142857142857,
        "d0_far": 0.4939336325682589,
        "values": {
            "d2_v2_recall": 0.7857142857142857,
            "d2_v2_far": 6.915070855955625,
            "d0_missed_recovery": 0.0,
            "incremental_recall": 0.0,
            "added_recovery_far": 6.4916991708971175,
            "incremental_far": 6.421137223387365,
        },
    }
    parses = tuple((identity, 1) for identity in subject.REAL_IDENTITIES)
    return subject.FrozenR1AuditResult(
        "a" * 40,
        "b" * 64,
        tuple(sorted({"result_freeze_commit_verified": True,
                      "post_result_freeze_mutations": 0,
                      "historical_blocked_audit_preserved": True,
                      "result_driven_changes": False}.items())),
        tuple(sorted({"fusion_before_combined": True, "combined_before_label": True,
                      "state_machine_guard_valid": True, "prediction_before_label_pass": True}.items())),
        tuple(sorted(metric.items())),
        parses,
        tuple(sorted({"private_path_exposures": 0, "tracked_private_path_occurrences": 0,
                      "private_source_set_exposures": 0, "scientific_private_value_leaks": 0}.items())),
        24,
        0,
    )


class D2V2R1SinglePassHarnessTests(unittest.TestCase):
    def test_duplicate_parse_guards_for_all_real_authorities(self) -> None:
        for identity in subject.REAL_IDENTITIES:
            with self.subTest(identity=identity):
                guard = subject.AuditSingleParseGuardR1.create()
                guard.claim_semantic_parse(identity)
                with self.assertRaisesRegex(subject.AuditR1Error, "D2_V2_R1_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
                    guard.claim_semantic_parse(identity)

    def test_hash_only_read_is_not_semantic_parse(self) -> None:
        guard = subject.AuditSingleParseGuardR1.create()
        class SyntheticBytes:
            def read_bytes(self) -> bytes:
                return b"synthetic hash-only bytes"
        subject.hash_only_bytes(SyntheticBytes(), "SYNTHETIC", guard)
        self.assertEqual(guard.byte_hash_reads, {"SYNTHETIC": 1})
        self.assertEqual(guard.semantic_parses, {})

    def test_corrected_public_horizon_parser_uses_map_hash(self) -> None:
        document, outer_hash, map_hash = synthetic_horizon([
            {"relation_binding_hash": "r1", "native_horizon_seconds": 2},
            {"relation_binding_hash": "r2", "native_horizon_seconds": 0},
        ])
        self.assertEqual(subject.parse_horizon_r1(document, outer_hash, map_hash, 2), {"r1": 2, "r2": 0})
        self.assertNotIn("artifact_hash", document["native_horizon_map"])

    def test_horizon_value_mutation_is_rejected(self) -> None:
        document, outer_hash, map_hash = synthetic_horizon([
            {"relation_binding_hash": "r1", "native_horizon_seconds": 2}
        ])
        document["native_horizon_map"]["entries"][0]["native_horizon_seconds"] = 3
        with self.assertRaises(subject.AuditR1Error):
            subject.parse_horizon_r1(document, outer_hash, map_hash, 1)

    def test_negative_and_noninteger_horizons_are_rejected(self) -> None:
        for bad in (-1, 1.5, True):
            with self.subTest(bad=bad):
                document, outer_hash, map_hash = synthetic_horizon([
                    {"relation_binding_hash": "r", "native_horizon_seconds": bad}
                ])
                with self.assertRaises(subject.AuditR1Error):
                    subject.parse_horizon_r1(document, outer_hash, map_hash, 1)

    def test_snapshot_is_immutable(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR1(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        with self.assertRaises(FrozenInstanceError):
            snapshot.snapshot_identity = "changed"  # type: ignore[misc]

    def test_snapshot_extension_preserves_identity(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR1(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        extension = subject.FrozenD2V2AuditSnapshotWithLabelR1(snapshot, (0,), "label")
        self.assertIs(extension.prelabel, snapshot)

    def test_ordering_must_pass_before_label_parse(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR1(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        guard = subject.AuditSingleParseGuardR1.create()
        with self.assertRaisesRegex(subject.AuditR1Error, "D2_V2_R1_LABEL_BEFORE_ORDERING_REJECTED"):
            subject.extend_snapshot_after_ordering(snapshot, Path("never-opened"), guard, False)
        self.assertNotIn("LABEL_TEST1", guard.semantic_parses)

    def test_report_rendering_does_not_change_parse_ledger(self) -> None:
        result = synthetic_result()
        before = result.parse_counts
        reports, markdown = subject.build_reports(result)
        self.assertEqual(result.parse_counts, before)
        self.assertEqual(len(reports), 16)
        self.assertEqual(markdown.count("BEGIN D2 V2 RESULT INTEGRITY R1 REPORT PROVENANCE V1"), 1)

    def test_result_hash_mutation_is_rejected(self) -> None:
        document = subject.self_hash({"value": 1})
        expected = document["artifact_hash"]
        subject.validate_hash(document, expected)
        document["value"] = 2
        with self.assertRaises(subject.AuditR1Error):
            subject.validate_hash(document, expected)

    def test_root_cause_is_audit_only(self) -> None:
        root = subject.root_cause()
        self.assertFalse(root["root_cause_scientific"])
        self.assertFalse(root["root_cause_result_driven"])
        self.assertFalse(root["native_horizon_public_map_bytes_changed"])
        self.assertFalse(root["native_horizon_values_changed"])

    def test_adversarial_matrix(self) -> None:
        self.assertEqual(subject.adversarial(), (24, 0))

    def test_exact_next_task(self) -> None:
        self.assertEqual(subject.NEXT_TASK, "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1")

    def test_no_test1_feature_or_test2_path(self) -> None:
        source = (ROOT / subject.SCRIPT_PATH).read_text(encoding="utf-8")
        self.assertNotIn("hai-test1.csv", source)
        self.assertNotIn("label-test2.csv", source)


if __name__ == "__main__":
    unittest.main()
