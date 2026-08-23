from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d2_v2_r4_harness",
    ROOT / "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r4.py",
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


def synthetic_result() -> subject.FrozenR4AuditResult:
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
    authority = {
        "authorization_identity_scheme": subject.AUTH_IDENTITY_SCHEME,
        "expected_authorization_artifact_self_hash": subject.AUTH,
        "computed_authorization_artifact_self_hash": subject.AUTH,
        "authorization_artifact_self_hash_match": True,
        "redundant_authorization_hash_required": False,
        "redundant_authorization_hash_absence_accepted": True,
        "authorization_scope_match": True,
        "authorization_design_binding_match": True,
        "authorization_d0_binding_match": True,
        "authorization_d1_binding_match": True,
        "authorization_source_map_binding_match": True,
        "authorization_horizon_map_binding_match": True,
        "authorization_chain_cross_bindings_pass": True,
        "authorization_markdown_hash_scheme": subject.MARKDOWN_SCHEME,
        "authorization_begin_marker_count": 1,
        "authorization_end_marker_count": 1,
        "authorization_raw_line_ending_profile": "CRLF",
        "authorization_raw_separator_type": "CRLF",
        "authorization_hash_domain_newline_representation": "CANONICAL_LF_UTF8_EXPLICIT_NORMALIZATION",
        "authorization_in_memory_canonicalization_used": True,
        "authorization_frozen_file_normalization_performed": False,
        "authorization_report_body_self_hash_match": True,
        "authorization_footer_bundle_binding_match": True,
        "authorization_footer_receipt_binding_match": True,
        "authorization_markdown_provenance_pass": True,
        "authorization_markdown_raw_file_changed": False,
        "authorization_markdown_raw_reads": 1,
        "authorization_footer_logical_parses": 1,
        "authorization_computed_body_hash": "c" * 64,
        "producer_classification": subject.PRODUCER_CLASSIFICATION,
        "producer_semantics_proven": True,
        "producer_authority_source_sha256": subject.PRODUCER_AUTHORITY_SHA256,
        "producer_authority_source_blob": subject.PRODUCER_AUTHORITY_BLOB,
        "producer_source_static_reads": 1,
        "producer_separator_hash_domain": "FOOTER_SERIALIZATION_ONLY",
        "r4_authorization_artifact_semantic_parses": 1,
    }
    return subject.FrozenR4AuditResult(
        "a" * 40,
        "b" * 64,
        tuple(sorted(authority.items())),
        tuple(sorted({"result_freeze_commit_verified": True,
                      "post_result_freeze_mutations": 0,
                      "historical_blocked_audits_preserved": True,
                      "result_driven_changes": False}.items())),
        tuple(sorted({"fusion_before_combined": True, "combined_before_label": True,
                      "state_machine_guard_valid": True, "prediction_before_label_pass": True}.items())),
        tuple(sorted(metric.items())),
        parses,
        tuple(sorted({"private_path_exposures": 0, "tracked_private_path_occurrences": 0,
                      "private_source_set_exposures": 0, "scientific_private_value_leaks": 0}.items())),
        30,
        0,
    )


def synthetic_authorization() -> dict[str, object]:
    payload = {key: False for key in subject.AUTHORIZATION_KEYS if key != "artifact_hash"}
    payload.update({
        "artifact_type": "D2V2InnerExecutionAuthorizationV1",
        "schema_version": "1.0.0",
        "authorization_version": subject.AUTH_VERSION,
        "authorization_scope": subject.AUTH_SCOPE,
        "design_hash": subject.DESIGN,
        "d0_prediction_hash": subject.D0_HASH,
        "d1_prediction_hash": subject.D1_HASH,
        "source_map_hash": subject.SOURCE_HASH,
        "native_horizon_map_hash": subject.HORIZON_HASH,
        "custody_preflight_hash": subject.AUTH_AUTHORITIES["CUSTODY_PREFLIGHT"][0],
        "required_distinct_source_count": 2,
        "fixed_global_temporal_window": None,
        "d2_v2_inner_execution_authorized": True,
    })
    return subject.self_hash(payload)


class D2V2R4SinglePassHarnessTests(unittest.TestCase):
    BUNDLE = "b" * 64
    RECEIPT = "c" * 64

    def producer(self, classification: str = subject.PRODUCER_CLASSIFICATION,
                 domain: str = "FOOTER_SERIALIZATION_ONLY") -> dict[str, object]:
        return {"producer_classification": classification, "producer_semantics_proven": True,
                "separator_hash_domain": domain}

    def authorization_report(self, newline: bytes = b"\n", body: bytes = b"body\n",
                             classification: str = subject.PRODUCER_CLASSIFICATION) -> tuple[bytes, str, dict[str, object]]:
        prefix = (body + b"\n").replace(b"\n", newline)
        canonical = prefix.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n"
        producer = self.producer(classification,
            "BODY_HASH_DOMAIN" if classification == "HASHED_RAW_WRITTEN_BODY_BYTES" else "FOOTER_SERIALIZATION_ONLY")
        digest = sha256(prefix if classification == "HASHED_RAW_WRITTEN_BODY_BYTES" else canonical).hexdigest()
        footer_lines = (
            subject.AUTH_BEGIN, b"Report-Hash-Scheme: " + subject.MARKDOWN_SCHEME.encode(),
            b"Report-Self-Hash: " + digest.encode(), b"Bundle-Hash: " + self.BUNDLE.encode(),
            b"Receipt-Hash: " + self.RECEIPT.encode(), subject.AUTH_END, b"")
        return prefix + newline.join(footer_lines), digest, producer

    def validate_authorization_report(self, raw: bytes, digest: str, producer: dict[str, object]):
        return subject.authorization_markdown_hash_view_r4(
            raw, producer, digest, self.BUNDLE, self.RECEIPT)

    def test_lf_and_crlf_raw_report_fixtures(self) -> None:
        for newline, profile in ((b"\n", "LF"), (b"\r\n", "CRLF")):
            with self.subTest(profile=profile):
                raw, digest, producer = self.authorization_report(newline)
                view = self.validate_authorization_report(raw, digest, producer)
                self.assertEqual(view.raw_line_ending_profile, profile)
                self.assertEqual(view.computed_body_hash, digest)

    def test_producer_hashes_raw_bytes_fixture(self) -> None:
        raw, digest, producer = self.authorization_report(
            b"\n", classification="HASHED_RAW_WRITTEN_BODY_BYTES")
        view = self.validate_authorization_report(raw, digest, producer)
        self.assertEqual(view.matching_fixed_representation, "RAW_BODY")

    def test_valid_crlf_transport_uses_canonical_lf_hash(self) -> None:
        raw, digest, producer = self.authorization_report(b"\r\n")
        view = self.validate_authorization_report(raw, digest, producer)
        self.assertEqual(view.raw_separator_type, "CRLF")
        self.assertEqual(view.hash_domain_newline_representation, "CANONICAL_LF_UTF8_EXPLICIT_NORMALIZATION")

    def test_mixed_line_endings_rejected(self) -> None:
        raw, digest, producer = self.authorization_report(b"\r\n")
        raw = raw.replace(b"body\r\n", b"body\n", 1)
        with self.assertRaisesRegex(subject.AuditR4Error, "MIXED_LINE_ENDINGS"):
            self.validate_authorization_report(raw, digest, producer)

    def test_duplicate_begin_and_end_markers_rejected(self) -> None:
        raw, digest, producer = self.authorization_report()
        for mutated in (raw + subject.AUTH_BEGIN, raw + subject.AUTH_END):
            with self.subTest(mutated=mutated[-20:]):
                with self.assertRaises(subject.AuditR4Error):
                    self.validate_authorization_report(mutated, digest, producer)

    def test_missing_begin_and_end_markers_rejected(self) -> None:
        raw, digest, producer = self.authorization_report()
        for mutated in (raw.replace(subject.AUTH_BEGIN, b""), raw.replace(subject.AUTH_END, b"")):
            with self.subTest(size=len(mutated)):
                with self.assertRaises(subject.AuditR4Error):
                    self.validate_authorization_report(mutated, digest, producer)

    def test_unknown_scheme_rejected(self) -> None:
        raw, digest, producer = self.authorization_report()
        raw = raw.replace(subject.MARKDOWN_SCHEME.encode("ascii"), b"UNKNOWN_SCHEME")
        with self.assertRaisesRegex(subject.AuditR4Error, "FOOTER_BINDING_REJECTED"):
            self.validate_authorization_report(raw, digest, producer)

    def test_body_whitespace_mutation_rejected(self) -> None:
        raw, digest, producer = self.authorization_report()
        with self.assertRaisesRegex(subject.AuditR4Error, "BODY_HASH_REJECTED"):
            self.validate_authorization_report(b"body " + raw[len(b"body"):], digest, producer)

    def test_footer_bundle_and_receipt_mutations_rejected(self) -> None:
        raw, digest, producer = self.authorization_report()
        mutations = (
            raw.replace(b"Report-Self-Hash: " + digest.encode(), b"Report-Self-Hash: " + b"0" * 64),
            raw.replace(b"Bundle-Hash: " + self.BUNDLE.encode(), b"Bundle-Hash: " + b"0" * 64),
            raw.replace(b"Receipt-Hash: " + self.RECEIPT.encode(), b"Receipt-Hash: " + b"0" * 64),
        )
        for mutated in mutations:
            with self.subTest(field=mutated[-100:]):
                with self.assertRaisesRegex(subject.AuditR4Error, "FOOTER_BINDING_REJECTED"):
                    self.validate_authorization_report(mutated, digest, producer)

    def test_unknown_producer_semantics_rejected(self) -> None:
        raw, digest, producer = self.authorization_report()
        producer["producer_classification"] = "UNKNOWN_FAIL_CLOSED"
        with self.assertRaisesRegex(subject.AuditR4Error, "PRODUCER_SEMANTICS_UNKNOWN"):
            self.validate_authorization_report(raw, digest, producer)

    def test_frozen_report_modification_rejected(self) -> None:
        raw, digest, producer = self.authorization_report()
        producer["expected_raw_sha256"] = sha256(raw).hexdigest()
        self.validate_authorization_report(raw, digest, producer)
        with self.assertRaisesRegex(subject.AuditR4Error, "RAW_BYTES_CHANGED"):
            self.validate_authorization_report(raw + b"x", digest, producer)

    def test_artifact_self_hash_is_identity_without_redundant_field(self) -> None:
        document = synthetic_authorization()
        self.assertNotIn("authorization_hash", document)
        self.assertEqual(subject.validate_authorization_document(document, document["artifact_hash"]), document)

    def test_wrong_authorization_artifact_self_hash_rejected(self) -> None:
        document = synthetic_authorization()
        document["artifact_hash"] = "0" * 64
        with self.assertRaises(subject.AuditR4Error):
            subject.validate_authorization_document(document, "0" * 64)

    def test_unknown_redundant_authorization_hash_rejected(self) -> None:
        document = synthetic_authorization()
        document["authorization_hash"] = document["artifact_hash"]
        with self.assertRaisesRegex(subject.AuditR4Error, "D2_V2_R4_AUTHORIZATION_SCHEMA_REJECTED"):
            subject.validate_authorization_document(document, document["artifact_hash"])

    def test_wrong_scope_design_and_input_bindings_rejected(self) -> None:
        for key in ("authorization_scope", "design_hash", "d0_prediction_hash", "d1_prediction_hash",
                    "source_map_hash", "native_horizon_map_hash"):
            with self.subTest(key=key):
                document = synthetic_authorization()
                document[key] = "MUTATED"
                payload = {k: v for k, v in document.items() if k != "artifact_hash"}
                document["artifact_hash"] = subject.stable(payload)
                with self.assertRaises(subject.AuditR4Error):
                    subject.validate_authorization_document(document, document["artifact_hash"])

    def test_authorization_duplicate_parse_rejected(self) -> None:
        guard = subject.AuditSingleParseGuardR4.create()
        guard.claim_semantic_parse(subject.AUTH_IDENTITY)
        with self.assertRaisesRegex(subject.AuditR4Error, "D2_V2_R4_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
            guard.claim_semantic_parse(subject.AUTH_IDENTITY)

    def test_authorization_markdown_and_footer_duplicate_reads_rejected(self) -> None:
        guard = subject.AuditSingleParseGuardR4.create()
        guard.claim_authorization_markdown_raw_read()
        guard.claim_authorization_footer_logical_parse()
        with self.assertRaisesRegex(subject.AuditR4Error, "AUTHORIZATION_MARKDOWN_DUPLICATE_READ"):
            guard.claim_authorization_markdown_raw_read()
        with self.assertRaisesRegex(subject.AuditR4Error, "AUTHORIZATION_FOOTER_DUPLICATE_PARSE"):
            guard.claim_authorization_footer_logical_parse()

    def test_duplicate_parse_guards_for_all_real_authorities(self) -> None:
        for identity in subject.REAL_IDENTITIES:
            with self.subTest(identity=identity):
                guard = subject.AuditSingleParseGuardR4.create()
                guard.claim_semantic_parse(identity)
                with self.assertRaisesRegex(subject.AuditR4Error, "D2_V2_R4_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
                    guard.claim_semantic_parse(identity)

    def test_hash_only_read_is_not_semantic_parse(self) -> None:
        guard = subject.AuditSingleParseGuardR4.create()
        class SyntheticBytes:
            def read_bytes(self) -> bytes:
                return b"synthetic hash-only bytes"
        subject.hash_only_bytes(SyntheticBytes(), "SYNTHETIC", guard)
        self.assertEqual(guard.byte_hash_reads, {"SYNTHETIC": 1})
        self.assertEqual(guard.semantic_parses, {})

    def test_corrected_public_horizon_parser_uses_map_hash(self) -> None:
        document, outer_hash, map_hash = synthetic_horizon([
            {"relation_binding_hash": "r1", "native_horizon_seconds": 2},
            {"relation_binding_hash": "r4", "native_horizon_seconds": 0},
        ])
        self.assertEqual(subject.parse_horizon_r4(document, outer_hash, map_hash, 2), {"r1": 2, "r4": 0})
        self.assertNotIn("artifact_hash", document["native_horizon_map"])

    def test_horizon_value_mutation_is_rejected(self) -> None:
        document, outer_hash, map_hash = synthetic_horizon([
            {"relation_binding_hash": "r4", "native_horizon_seconds": 2}
        ])
        document["native_horizon_map"]["entries"][0]["native_horizon_seconds"] = 3
        with self.assertRaises(subject.AuditR4Error):
            subject.parse_horizon_r4(document, outer_hash, map_hash, 1)

    def test_negative_and_noninteger_horizons_are_rejected(self) -> None:
        for bad in (-1, 1.5, True):
            with self.subTest(bad=bad):
                document, outer_hash, map_hash = synthetic_horizon([
                    {"relation_binding_hash": "r", "native_horizon_seconds": bad}
                ])
                with self.assertRaises(subject.AuditR4Error):
                    subject.parse_horizon_r4(document, outer_hash, map_hash, 1)

    def test_snapshot_is_immutable(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR4(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        with self.assertRaises(FrozenInstanceError):
            snapshot.snapshot_identity = "changed"  # type: ignore[misc]

    def test_snapshot_extension_preserves_identity(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR4(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        extension = subject.FrozenD2V2AuditSnapshotWithLabelR4(snapshot, (0,), "label")
        self.assertIs(extension.prelabel, snapshot)

    def test_ordering_must_pass_before_label_parse(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR4(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        guard = subject.AuditSingleParseGuardR4.create()
        with self.assertRaisesRegex(subject.AuditR4Error, "D2_V2_R4_LABEL_BEFORE_ORDERING_REJECTED"):
            subject.extend_snapshot_after_ordering(snapshot, Path("never-opened"), guard, False)
        self.assertNotIn("LABEL_TEST1", guard.semantic_parses)

    def test_report_rendering_does_not_change_parse_ledger(self) -> None:
        result = synthetic_result()
        before = result.parse_counts
        reports, markdown = subject.build_reports(result)
        self.assertEqual(result.parse_counts, before)
        self.assertEqual(len(reports), 18)
        self.assertEqual(markdown.count(subject.R4_BEGIN), 1)
        self.assertIn(b"Historical-R3-Blocker-Hash: " + subject.HISTORICAL_R3_BLOCKER_HASH.encode(), markdown)
        receipt = reports["RECEIPT"]
        subject.validate_new_lf_markdown_v1(
            markdown, subject.R4_BEGIN, subject.R4_END, receipt["report_self_hash"],
            reports["BUNDLE"]["artifact_hash"], receipt["artifact_hash"])

    def test_result_hash_mutation_is_rejected(self) -> None:
        document = subject.self_hash({"value": 1})
        expected = document["artifact_hash"]
        subject.validate_hash(document, expected)
        document["value"] = 2
        with self.assertRaises(subject.AuditR4Error):
            subject.validate_hash(document, expected)

    def test_root_cause_is_audit_only(self) -> None:
        root = subject.root_cause()
        self.assertFalse(root["root_cause_scientific"])
        self.assertFalse(root["root_cause_result_driven"])
        self.assertFalse(root["native_horizon_public_map_bytes_changed"])
        self.assertFalse(root["native_horizon_values_changed"])

    def test_adversarial_matrix(self) -> None:
        attacks, accepted = subject.adversarial()
        self.assertGreaterEqual(attacks, 30)
        self.assertEqual(accepted, 0)

    def test_exact_next_task(self) -> None:
        self.assertEqual(subject.NEXT_TASK, "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1")

    def test_no_test1_feature_or_test2_path(self) -> None:
        source = (ROOT / subject.SCRIPT_PATH).read_text(encoding="utf-8")
        self.assertNotIn("hai-test1.csv", source)
        self.assertNotIn("label-test2.csv", source)


if __name__ == "__main__":
    unittest.main()
