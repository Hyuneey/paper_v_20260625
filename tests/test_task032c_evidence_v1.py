from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path

from paperworks.contracts import (
    EvidenceV1ModelError,
    canonical_evidence_package_sha256,
    evidence_package_to_dict,
    load_evidence_package,
    parse_evidence_package,
    with_computed_artifact_hash,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/task032c/evidence_delayed_response.json"


def evidence_document() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class Task032CEvidenceV1Tests(unittest.TestCase):
    def test_valid_evidence_is_typed_immutable_and_round_trips(self) -> None:
        evidence = load_evidence_package(FIXTURE)
        self.assertEqual(evidence_package_to_dict(evidence), evidence_document())
        self.assertEqual(canonical_evidence_package_sha256(evidence), evidence.artifact_hash)
        self.assertFalse(evidence.runtime_authorized)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            evidence.evidence_id = "EVID-OTHER"  # type: ignore[misc]

    def test_window_and_lag_order_fail(self) -> None:
        cases = []
        window = evidence_document(); window["event_window"].update(start_offset=21, end_offset=20)
        cases.append((window, "EVIDENCE_V1_WINDOW_ORDER"))
        lag = evidence_document(); lag["candidate_lag_range"].update(minimum=6, maximum=5)
        cases.append((lag, "EVIDENCE_V1_LAG_ORDER"))
        for document, code in cases:
            with self.subTest(code=code), self.assertRaises(EvidenceV1ModelError) as caught:
                parse_evidence_package(with_computed_artifact_hash(document))
            self.assertEqual(caught.exception.issue_code, code)

    def test_source_target_overlap_fails(self) -> None:
        document = evidence_document(); document["target_variables"] = [document["source_variables"][0]]
        with self.assertRaises(EvidenceV1ModelError) as caught:
            parse_evidence_package(with_computed_artifact_hash(document))
        self.assertEqual(caught.exception.issue_code, "EVIDENCE_V1_VARIABLE_OVERLAP")

    def test_raw_values_and_missing_claim_boundary_fail_structurally(self) -> None:
        raw = evidence_document(); raw["raw_values_included"] = True
        missing = evidence_document(); missing["prohibited_claims"].remove("root_cause")
        for document in (raw, missing):
            with self.assertRaises(EvidenceV1ModelError) as caught:
                parse_evidence_package(with_computed_artifact_hash(document))
            self.assertEqual(caught.exception.issue_code, "EVIDENCE_V1_STRUCTURAL_INVALID")

    def test_exact_regime_normal_reference_must_match(self) -> None:
        document = evidence_document(); document["matched_normal_reference"]["operating_regime"] = "REGIME-OTHER-032C"
        with self.assertRaises(EvidenceV1ModelError) as caught:
            parse_evidence_package(with_computed_artifact_hash(document))
        self.assertEqual(caught.exception.issue_code, "EVIDENCE_V1_REGIME_MISMATCH")


if __name__ == "__main__":
    unittest.main()
