from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperworks.data.hai_provenance_v1 import (
    HAIProvenanceError,
    assert_external_audit_roots,
    assert_public_artifact_has_no_sensitive_content,
    audit_label_custody_pair,
    inventory_graph_file,
)


class Task039ACustodyReferenceTests(unittest.TestCase):
    def test_label_alignment_domain_and_public_redaction(self) -> None:
        test_text = (
            "timestamp,P1_SYN_SOURCE\n"
            "2026-01-01 00:00:00,0\n"
            "2026-01-01 00:00:01,1\n"
            "2026-01-01 00:00:02,0\n"
            "2026-01-01 00:00:03,1\n"
            "2026-01-01 00:00:04,0\n"
        )
        label_text = (
            "timestamp,label\n"
            "2026-01-01 00:00:00,0\n"
            "2026-01-01 00:00:01,1\n"
            "2026-01-01 00:00:02,0\n"
            "2026-01-01 00:00:03,1\n"
            "2026-01-01 00:00:04,0\n"
        )
        summary_text = (
            "2026-01-01 00:00:01 synthetic private event\n"
            "2026-01-01 00:00:03 synthetic private event\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test = root / "test.csv"
            label = root / "label.csv"
            summary = root / "summary.txt"
            private = root / "private" / "custody.json"
            test.write_text(test_text, encoding="utf-8")
            label.write_text(label_text, encoding="utf-8")
            summary.write_text(summary_text, encoding="utf-8")
            record = audit_label_custody_pair(
                test_path=test,
                test_relative_path="hai-23.05/hai-test1.csv",
                label_path=label,
                label_relative_path="hai-23.05/label-test1.csv",
                summary_path=summary,
                summary_relative_path="hai-23.05/summary_label1.txt",
                expected_event_count=2,
                private_output_path=private,
            )
            private_document = json.loads(private.read_text(encoding="utf-8"))
        public = record.to_dict()
        self.assertEqual(record.custody_status, "verified")
        self.assertEqual(record.event_record_count, 2)
        self.assertNotIn("label_events", public)
        self.assertNotIn("summary_records", public)
        self.assertIn("label_events", private_document)
        assert_public_artifact_has_no_sensitive_content(public)

    def test_invalid_label_domain_and_alignment_fail_custody(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test = root / "test.csv"
            label = root / "label.csv"
            summary = root / "summary.txt"
            test.write_text(
                "timestamp,P1_SYN\n2026-01-01 00:00:00,0\n",
                encoding="utf-8",
            )
            label.write_text(
                "timestamp,label\n2026-01-01 00:00:01,unknown\n",
                encoding="utf-8",
            )
            summary.write_text("synthetic summary without event\n", encoding="utf-8")
            record = audit_label_custody_pair(
                test_path=test,
                test_relative_path="hai-23.05/hai-test2.csv",
                label_path=label,
                label_relative_path="hai-23.05/label-test2.csv",
                summary_path=summary,
                summary_relative_path="hai-23.05/summary_label2.txt",
                expected_event_count=1,
                private_output_path=root / "private.json",
            )
        self.assertEqual(record.custody_status, "failed")
        self.assertFalse(record.label_domain_valid)
        self.assertEqual(record.timestamp_alignment_status, "misaligned")

    def test_public_boundary_rejects_absolute_path_and_attack_detail(self) -> None:
        with self.assertRaises(HAIProvenanceError):
            assert_public_artifact_has_no_sensitive_content({"path": "C:\\private\\x"})
        with self.assertRaises(HAIProvenanceError):
            assert_public_artifact_has_no_sensitive_content({"attack_start": "hidden"})

    def test_external_roots_cannot_be_inside_paper_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paper = Path(directory) / "paper"
            paper.mkdir()
            with self.assertRaises(HAIProvenanceError):
                assert_external_audit_roots(
                    paper_repository_root=paper,
                    official_root=paper / "data",
                    private_root=Path(directory) / "private",
                )

    def test_graph_json_and_python_literal_classification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            strict = root / "strict.json"
            literal = root / "literal.txt"
            strict.write_text(
                json.dumps(
                    {
                        "directed": True,
                        "multigraph": False,
                        "nodes": [{"id": "P1_SYN_A"}, {"id": "P1_SYN_B"}],
                        "links": [{"source": "P1_SYN_A", "target": "P1_SYN_B"}],
                    }
                ),
                encoding="utf-8",
            )
            literal.write_text(
                "{'directed': False, 'nodes': ['P3_SYN_A'], 'edges': []}",
                encoding="utf-8",
            )
            strict_record = inventory_graph_file(
                strict,
                relative_path="graph/synthetic.json",
                git_blob_sha="1" * 40,
            )
            literal_record = inventory_graph_file(
                literal,
                relative_path="graph/synthetic.txt",
                git_blob_sha="2" * 40,
            )
        self.assertEqual(strict_record.strict_json_parse_status, "parsed")
        self.assertEqual(strict_record.node_count, 2)
        self.assertEqual(strict_record.edge_count, 1)
        self.assertEqual(literal_record.strict_json_parse_status, "invalid")
        self.assertEqual(literal_record.python_literal_parse_status, "parsed")


if __name__ == "__main__":
    unittest.main()
