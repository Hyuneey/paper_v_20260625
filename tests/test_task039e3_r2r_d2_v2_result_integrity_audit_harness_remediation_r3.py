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
    "d2_v2_r3_harness",
    ROOT / "scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r3.py",
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


def synthetic_result() -> subject.FrozenR3AuditResult:
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
        "authorization_footer_separator_lf_count_excluded": 1,
        "authorization_canonical_body_extraction_pass": True,
        "authorization_report_body_self_hash_match": True,
        "authorization_footer_bundle_binding_match": True,
        "authorization_footer_receipt_binding_match": True,
        "authorization_computed_body_hash": "c" * 64,
        "r3_authorization_artifact_semantic_parses": 1,
    }
    return subject.FrozenR3AuditResult(
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


class D2V2R3SinglePassHarnessTests(unittest.TestCase):
    BUNDLE = "b" * 64
    RECEIPT = "c" * 64

    def markdown(self, body: bytes) -> tuple[bytes, str]:
        return subject.render_markdown_provenance_raw_v1(
            body, subject.AUTH_BEGIN, subject.AUTH_END, self.BUNDLE, self.RECEIPT)

    def test_raw_body_without_terminal_lf(self) -> None:
        raw, digest = self.markdown(b"body")
        result = subject.validate_markdown_provenance_raw_v1(
            raw, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)
        self.assertEqual(result["computed_body_hash"], sha256(b"body").hexdigest())

    def test_raw_body_one_terminal_lf_preserved(self) -> None:
        body = b"body\n"
        raw, digest = self.markdown(body)
        self.assertEqual(subject.validate_markdown_provenance_raw_v1(
            raw, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)["computed_body_hash"],
            sha256(body).hexdigest())

    def test_raw_body_two_terminal_lfs_preserved(self) -> None:
        body = b"body\n\n"
        raw, digest = self.markdown(body)
        self.assertEqual(subject.validate_markdown_provenance_raw_v1(
            raw, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)["computed_body_hash"],
            sha256(body).hexdigest())

    def test_missing_separator_lf_rejected(self) -> None:
        raw, digest = self.markdown(b"body")
        raw = raw.replace(b"body\n" + subject.AUTH_BEGIN, b"body" + subject.AUTH_BEGIN, 1)
        with self.assertRaisesRegex(subject.AuditR3Error, "SEPARATOR_NOT_CANONICAL"):
            subject.validate_markdown_provenance_raw_v1(
                raw, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)

    def test_duplicate_begin_and_end_markers_rejected(self) -> None:
        raw, digest = self.markdown(b"body")
        for mutated in (raw + subject.AUTH_BEGIN, raw + subject.AUTH_END):
            with self.subTest(mutated=mutated[-20:]):
                with self.assertRaises(subject.AuditR3Error):
                    subject.validate_markdown_provenance_raw_v1(
                        mutated, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)

    def test_unknown_scheme_rejected(self) -> None:
        raw, digest = self.markdown(b"body")
        raw = raw.replace(subject.MARKDOWN_SCHEME.encode("ascii"), b"UNKNOWN_SCHEME")
        with self.assertRaisesRegex(subject.AuditR3Error, "FOOTER_BINDING_REJECTED"):
            subject.validate_markdown_provenance_raw_v1(
                raw, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)

    def test_crlf_separator_rejected(self) -> None:
        raw, digest = self.markdown(b"body")
        raw = raw.replace(b"body\n" + subject.AUTH_BEGIN, b"body\r\n" + subject.AUTH_BEGIN, 1)
        with self.assertRaisesRegex(subject.AuditR3Error, "SEPARATOR_NOT_CANONICAL"):
            subject.validate_markdown_provenance_raw_v1(
                raw, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)

    def test_body_whitespace_mutation_rejected(self) -> None:
        raw, digest = self.markdown(b"body")
        with self.assertRaisesRegex(subject.AuditR3Error, "BODY_HASH_REJECTED"):
            subject.validate_markdown_provenance_raw_v1(
                b"body " + raw[len(b"body"):], subject.AUTH_BEGIN, subject.AUTH_END,
                digest, self.BUNDLE, self.RECEIPT)

    def test_footer_bundle_and_receipt_mutations_rejected(self) -> None:
        raw, digest = self.markdown(b"body")
        mutations = (
            raw.replace(b"Report-Self-Hash: " + digest.encode(), b"Report-Self-Hash: " + b"0" * 64),
            raw.replace(b"Bundle-Hash: " + self.BUNDLE.encode(), b"Bundle-Hash: " + b"0" * 64),
            raw.replace(b"Receipt-Hash: " + self.RECEIPT.encode(), b"Receipt-Hash: " + b"0" * 64),
        )
        for mutated in mutations:
            with self.subTest(field=mutated[-100:]):
                with self.assertRaisesRegex(subject.AuditR3Error, "FOOTER_BINDING_REJECTED"):
                    subject.validate_markdown_provenance_raw_v1(
                        mutated, subject.AUTH_BEGIN, subject.AUTH_END, digest, self.BUNDLE, self.RECEIPT)

    def test_rstrip_equivalent_overtrim_is_wrong(self) -> None:
        body = b"body\n\n"
        raw, digest = self.markdown(body)
        prefix = raw[:raw.index(subject.AUTH_BEGIN)]
        self.assertEqual(prefix[:-1], body)
        self.assertNotEqual(sha256(prefix.rstrip(b"\n")).hexdigest(), digest)

    def test_artifact_self_hash_is_identity_without_redundant_field(self) -> None:
        document = synthetic_authorization()
        self.assertNotIn("authorization_hash", document)
        self.assertEqual(subject.validate_authorization_document(document, document["artifact_hash"]), document)

    def test_wrong_authorization_artifact_self_hash_rejected(self) -> None:
        document = synthetic_authorization()
        document["artifact_hash"] = "0" * 64
        with self.assertRaises(subject.AuditR3Error):
            subject.validate_authorization_document(document, "0" * 64)

    def test_unknown_redundant_authorization_hash_rejected(self) -> None:
        document = synthetic_authorization()
        document["authorization_hash"] = document["artifact_hash"]
        with self.assertRaisesRegex(subject.AuditR3Error, "D2_V2_R3_AUTHORIZATION_SCHEMA_REJECTED"):
            subject.validate_authorization_document(document, document["artifact_hash"])

    def test_wrong_scope_design_and_input_bindings_rejected(self) -> None:
        for key in ("authorization_scope", "design_hash", "d0_prediction_hash", "d1_prediction_hash",
                    "source_map_hash", "native_horizon_map_hash"):
            with self.subTest(key=key):
                document = synthetic_authorization()
                document[key] = "MUTATED"
                payload = {k: v for k, v in document.items() if k != "artifact_hash"}
                document["artifact_hash"] = subject.stable(payload)
                with self.assertRaises(subject.AuditR3Error):
                    subject.validate_authorization_document(document, document["artifact_hash"])

    def test_authorization_duplicate_parse_rejected(self) -> None:
        guard = subject.AuditSingleParseGuardR3.create()
        guard.claim_semantic_parse(subject.AUTH_IDENTITY)
        with self.assertRaisesRegex(subject.AuditR3Error, "D2_V2_R3_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
            guard.claim_semantic_parse(subject.AUTH_IDENTITY)

    def test_duplicate_parse_guards_for_all_real_authorities(self) -> None:
        for identity in subject.REAL_IDENTITIES:
            with self.subTest(identity=identity):
                guard = subject.AuditSingleParseGuardR3.create()
                guard.claim_semantic_parse(identity)
                with self.assertRaisesRegex(subject.AuditR3Error, "D2_V2_R3_AUDIT_DUPLICATE_REAL_INPUT_PARSE"):
                    guard.claim_semantic_parse(identity)

    def test_hash_only_read_is_not_semantic_parse(self) -> None:
        guard = subject.AuditSingleParseGuardR3.create()
        class SyntheticBytes:
            def read_bytes(self) -> bytes:
                return b"synthetic hash-only bytes"
        subject.hash_only_bytes(SyntheticBytes(), "SYNTHETIC", guard)
        self.assertEqual(guard.byte_hash_reads, {"SYNTHETIC": 1})
        self.assertEqual(guard.semantic_parses, {})

    def test_corrected_public_horizon_parser_uses_map_hash(self) -> None:
        document, outer_hash, map_hash = synthetic_horizon([
            {"relation_binding_hash": "r1", "native_horizon_seconds": 2},
            {"relation_binding_hash": "r3", "native_horizon_seconds": 0},
        ])
        self.assertEqual(subject.parse_horizon_r3(document, outer_hash, map_hash, 2), {"r1": 2, "r3": 0})
        self.assertNotIn("artifact_hash", document["native_horizon_map"])

    def test_horizon_value_mutation_is_rejected(self) -> None:
        document, outer_hash, map_hash = synthetic_horizon([
            {"relation_binding_hash": "r3", "native_horizon_seconds": 2}
        ])
        document["native_horizon_map"]["entries"][0]["native_horizon_seconds"] = 3
        with self.assertRaises(subject.AuditR3Error):
            subject.parse_horizon_r3(document, outer_hash, map_hash, 1)

    def test_negative_and_noninteger_horizons_are_rejected(self) -> None:
        for bad in (-1, 1.5, True):
            with self.subTest(bad=bad):
                document, outer_hash, map_hash = synthetic_horizon([
                    {"relation_binding_hash": "r", "native_horizon_seconds": bad}
                ])
                with self.assertRaises(subject.AuditR3Error):
                    subject.parse_horizon_r3(document, outer_hash, map_hash, 1)

    def test_snapshot_is_immutable(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR3(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        with self.assertRaises(FrozenInstanceError):
            snapshot.snapshot_identity = "changed"  # type: ignore[misc]

    def test_snapshot_extension_preserves_identity(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR3(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        extension = subject.FrozenD2V2AuditSnapshotWithLabelR3(snapshot, (0,), "label")
        self.assertIs(extension.prelabel, snapshot)

    def test_ordering_must_pass_before_label_parse(self) -> None:
        snapshot = subject.FrozenD2V2AuditSnapshotR3(
            "id", (False,), tuple(), tuple(), tuple(), tuple(), (tuple(),),
            (False,), (False,), ("NONE",), ((0, False, "NONE", "x"),), "f", "c")
        guard = subject.AuditSingleParseGuardR3.create()
        with self.assertRaisesRegex(subject.AuditR3Error, "D2_V2_R3_LABEL_BEFORE_ORDERING_REJECTED"):
            subject.extend_snapshot_after_ordering(snapshot, Path("never-opened"), guard, False)
        self.assertNotIn("LABEL_TEST1", guard.semantic_parses)

    def test_report_rendering_does_not_change_parse_ledger(self) -> None:
        result = synthetic_result()
        before = result.parse_counts
        reports, markdown = subject.build_reports(result)
        self.assertEqual(result.parse_counts, before)
        self.assertEqual(len(reports), 18)
        self.assertEqual(markdown.count(subject.R3_BEGIN), 1)
        receipt = reports["RECEIPT"]
        subject.validate_markdown_provenance_raw_v1(
            markdown, subject.R3_BEGIN, subject.R3_END, receipt["report_self_hash"],
            reports["BUNDLE"]["artifact_hash"], receipt["artifact_hash"])

    def test_result_hash_mutation_is_rejected(self) -> None:
        document = subject.self_hash({"value": 1})
        expected = document["artifact_hash"]
        subject.validate_hash(document, expected)
        document["value"] = 2
        with self.assertRaises(subject.AuditR3Error):
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
