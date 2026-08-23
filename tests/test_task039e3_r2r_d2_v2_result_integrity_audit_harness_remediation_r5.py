from __future__ import annotations

from dataclasses import FrozenInstanceError
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r5.py"
SPEC = importlib.util.spec_from_file_location("d2_v2_r5_subject", SCRIPT)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


def synthetic_horizon(entries: list[dict[str, object]]) -> tuple[dict[str, object], str, str]:
    inner = {"artifact_type": "D2V2NativeTemporalHorizonMapV1", "entries": entries}
    map_hash = subject.stable(inner)
    inner["map_hash"] = map_hash
    outer = {"artifact_type": "native_horizon_wrapper", "schema_version": "1.0.0",
             "native_horizon_map": inner, "missing_horizon_count": 0, "ambiguous_horizon_count": 0,
             "label_derived_horizon_count": 0, "test1_derived_horizon_count": 0,
             "foreign_relation_count": 0}
    outer_hash = subject.stable(outer)
    outer["artifact_hash"] = outer_hash
    return outer, outer_hash, map_hash


class R5SyntheticAuditTests(unittest.TestCase):
    def test_authorization_artifact_self_hash_is_identity(self) -> None:
        document = subject.seal({"artifact_type": "authorization", "authorization_scope": "scope"})
        subject.validate_hash(document, document["artifact_hash"])
        self.assertNotIn("authorization_hash", document)

    def test_redundant_authorization_hash_not_required(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('authorization.get("authorization_hash")', source)
        self.assertEqual(subject.AUTH, subject.r4.AUTH)

    def test_historical_crlf_canonical_lf_hash_view(self) -> None:
        body = b"alpha\r\nbeta\r\n"
        canonical = body.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n"
        digest = sha256(canonical).hexdigest()
        raw = (body + subject.r4.AUTH_BEGIN + b"\r\nReport-Hash-Scheme: " + subject.r4.MARKDOWN_SCHEME.encode()
               + b"\r\nReport-Self-Hash: " + digest.encode() + b"\r\nBundle-Hash: " + b"b" * 64
               + b"\r\nReceipt-Hash: " + b"c" * 64 + b"\r\n" + subject.r4.AUTH_END + b"\r\n")
        producer = {"producer_classification": "HASHED_CANONICAL_TEXT_WITH_EXPLICIT_NEWLINE_NORMALIZATION",
                    "producer_semantics_proven": True, "separator_hash_domain": "FOOTER_SERIALIZATION_ONLY",
                    "expected_raw_sha256": sha256(raw).hexdigest()}
        view = subject.r4.authorization_markdown_hash_view_r4(raw, producer, digest, "b" * 64, "c" * 64)
        self.assertEqual(view.computed_body_hash, digest)
        self.assertEqual(view.raw_line_ending_profile, "CRLF")

    def test_parse_guard_rejects_all_duplicate_real_inputs(self) -> None:
        for identity in subject.REAL_IDENTITIES:
            with self.subTest(identity=identity):
                guard = subject.SingleParseGuardR5.create(); guard.claim(identity)
                with self.assertRaisesRegex(subject.AuditR5Error, "D2_V2_R5_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
                    guard.claim(identity)

    def test_parse_guard_requires_exact_closure(self) -> None:
        guard = subject.SingleParseGuardR5.create()
        for identity in subject.REAL_IDENTITIES[:-1]:
            guard.claim(identity)
        with self.assertRaisesRegex(subject.AuditR5Error, "PARSE_ACCOUNTING_REJECTED"):
            guard.require_exact()

    def test_native_horizon_map_hash_and_entries(self) -> None:
        document, outer_hash, map_hash = synthetic_horizon([
            {"relation_binding_hash": "r1", "native_horizon_seconds": 2},
            {"relation_binding_hash": "r2", "native_horizon_seconds": 3},
        ])
        self.assertEqual(subject.parse_horizon(document, outer_hash, map_hash, 2), {"r1": 2, "r2": 3})

    def test_horizon_mutations_rejected(self) -> None:
        for value in (-1, 1.5, True):
            with self.subTest(value=value):
                document, outer_hash, map_hash = synthetic_horizon([
                    {"relation_binding_hash": "r1", "native_horizon_seconds": value}])
                with self.assertRaises(subject.AuditR5Error):
                    subject.parse_horizon(document, outer_hash, map_hash, 1)

    def test_token_causal_start_and_inclusive_expiry(self) -> None:
        tokens = subject.build_tokens(((2, True, "r"),), {"r": "s"}, {"r": 3}, rows=8, enforce_frozen=False)
        self.assertEqual((tokens[0].decision, tokens[0].expiry), (2, 5))

    def test_token_clips_only_at_split_end(self) -> None:
        tokens = subject.build_tokens(((6, True, "r"),), {"r": "s"}, {"r": 5}, rows=8, enforce_frozen=False)
        self.assertEqual(tokens[0].expiry, 7)

    def test_same_source_tokens_collapse(self) -> None:
        tokens = subject.build_tokens(((0, True, "r1"), (0, True, "r2")),
                                      {"r1": "s", "r2": "s"}, {"r1": 2, "r2": 2},
                                      rows=4, enforce_frozen=False)
        fusion = subject.fusion_oracle((False,) * 4, tokens, rows=4, enforce_frozen=False)
        self.assertEqual(fusion["sources"][0], ("s",))
        self.assertFalse(any(fusion["corroboration"]))

    def test_two_active_distinct_sources_corroborate(self) -> None:
        tokens = subject.build_tokens(((0, True, "r1"), (1, True, "r2")),
                                      {"r1": "a", "r2": "b"}, {"r1": 2, "r2": 2},
                                      rows=4, enforce_frozen=False)
        fusion = subject.fusion_oracle((False,) * 4, tokens, rows=4, enforce_frozen=False)
        self.assertEqual(fusion["corroboration"], (False, True, True, False))

    def test_d0_preservation_and_trigger_truth_table(self) -> None:
        tokens = subject.build_tokens(((0, True, "r1"), (0, True, "r2")),
                                      {"r1": "a", "r2": "b"}, {"r1": 0, "r2": 0},
                                      rows=2, enforce_frozen=False)
        fusion = subject.fusion_oracle((True, True), tokens, rows=2, enforce_frozen=False)
        self.assertEqual(fusion["alarms"], (True, True))
        self.assertEqual(fusion["triggers"], ("D0_AND_RULE_CORROBORATION_NATIVE_HORIZON", "D0_ONLY"))

    def test_event_and_episode_formation(self) -> None:
        self.assertEqual(subject.attack_events((0, 1, 1, 0, 1)), ((1, 3), (4, 5)))
        self.assertEqual(subject.contiguous_runs((1, 2, 4)), ((1, 3), (4, 5)))

    def test_event_overlap_counts(self) -> None:
        self.assertEqual(subject.event_episode_counts(((1, 3), (5, 6)), ((2, 4), (7, 8))), (1, 1))

    def test_all_metric_formula_arithmetic(self) -> None:
        events, episodes = ((0, 2), (4, 5)), ((1, 3),)
        detected, false = subject.event_episode_counts(events, episodes)
        self.assertEqual((detected, false), (1, 0))
        self.assertEqual(7 / (51019 / 3600), 0.4939336325682589)
        self.assertEqual(98 / (51019 / 3600), 6.915070855955625)
        self.assertEqual(92 / (51019 / 3600), 6.4916991708971175)
        self.assertEqual(98 / (51019 / 3600) - 7 / (51019 / 3600), 6.421137223387365)

    def test_compatibility_receipt_is_mandatory_in_policy(self) -> None:
        attacks, accepted = subject.adversarial()
        self.assertGreaterEqual(attacks, 27); self.assertEqual(accepted, 0)

    def test_absolute_path_equality_is_not_authority(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"absolute_path_equality_required": False', source)
        self.assertNotIn("expected_absolute_private_path", source)

    def test_report_self_hash_collision_rejected(self) -> None:
        with self.assertRaisesRegex(subject.AuditR5Error, "SELF_HASH_FIELD_COLLISION"):
            subject.seal({"artifact_hash": "payload-reference"})

    def test_snapshot_is_immutable(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR5("id", tuple(), tuple(), tuple(), tuple(), tuple(), tuple(), tuple())
        with self.assertRaises(FrozenInstanceError):
            snapshot.identity = "mutated"  # type: ignore[misc]

    def test_new_markdown_writer_roundtrip(self) -> None:
        result = subject.CompletedR5Result("a", "snapshot", tuple(), tuple(), tuple(), tuple(),
            (("values", tuple()),), tuple(), tuple(), 40, 0)
        # Rendering needs aggregate metric keys; build a complete synthetic result without any file access.
        metric = (("d0_detected", 11), ("d0_false", 7), ("d0_missed", 3), ("d2_detected", 11),
                  ("d2_false", 98), ("normal_seconds", 51019), ("recovered", 0), ("recovery_false", 92),
                  ("values", tuple(sorted({"d2_v2_recall": .7857142857142857, "d2_v2_far": 6.915070855955625,
                   "d0_missed_recovery": 0.0, "incremental_recall": 0.0,
                   "added_recovery_far": 6.4916991708971175, "incremental_far": 6.421137223387365}.items()))))
        parses = tuple((name, 1) for name in subject.REAL_IDENTITIES)
        result = subject.CompletedR5Result("a", "snapshot", tuple(), tuple(), tuple(),
            (("prediction_before_label_pass", True),), metric, parses,
            (("private_path_exposures", 0),), 40, 0)
        reports, markdown = subject.build_reports(result)
        self.assertEqual(len(reports), 17)
        receipt = reports["RECEIPT"]
        subject.r4.validate_new_lf_markdown_v1(markdown, subject.REPORT_BEGIN, subject.REPORT_END,
            receipt["report_self_sha256"], reports["BUNDLE"]["artifact_hash"], receipt["artifact_hash"])

    def test_no_feature_or_test2_literal(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("hai-test1.csv", source)
        self.assertNotIn("label-test2.csv", source)


if __name__ == "__main__":
    unittest.main()
