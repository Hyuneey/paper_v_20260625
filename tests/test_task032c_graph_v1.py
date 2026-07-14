from __future__ import annotations

import copy
import dataclasses
import json
import math
import unittest
from pathlib import Path

from paperworks.contracts import (
    ContractArtifactHashError,
    GraphV1ModelError,
    canonical_candidate_graph_sha256,
    canonical_contract_artifact_sha256,
    candidate_graph_to_dict,
    load_candidate_graph,
    parse_candidate_graph,
    verify_contract_artifact_hash,
    with_computed_artifact_hash,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/task032c/graph_delayed_response.json"


def graph_document() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def rehash(document: dict) -> dict:
    return with_computed_artifact_hash(document)


class Task032CGraphV1Tests(unittest.TestCase):
    def test_shared_self_hash_excludes_only_top_level_and_is_deterministic(self) -> None:
        document = graph_document()
        before = copy.deepcopy(document)
        first = canonical_contract_artifact_sha256(document)
        changed_self = copy.deepcopy(document)
        changed_self["artifact_hash"] = "f" * 64
        self.assertEqual(canonical_contract_artifact_sha256(changed_self), first)
        changed_nested = copy.deepcopy(document)
        changed_nested["nodes"][0]["metadata_provenance"]["artifact_hash"] = "e" * 64
        self.assertNotEqual(canonical_contract_artifact_sha256(changed_nested), first)
        self.assertEqual(document, before)
        self.assertEqual(verify_contract_artifact_hash(document), document["artifact_hash"])

    def test_hash_mismatch_and_nonfinite_values_fail(self) -> None:
        document = graph_document()
        document["dataset_version"] = "changed"
        with self.assertRaisesRegex(ContractArtifactHashError, "CONTRACT_ARTIFACT_HASH_MISMATCH"):
            verify_contract_artifact_hash(document)
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaisesRegex(ContractArtifactHashError, "CONTRACT_ARTIFACT_NONFINITE_VALUE"):
                canonical_contract_artifact_sha256({"value": value, "artifact_hash": "0" * 64})

    def test_valid_graph_is_typed_immutable_and_round_trips(self) -> None:
        before = FIXTURE.read_bytes()
        graph = load_candidate_graph(FIXTURE)
        self.assertEqual(candidate_graph_to_dict(graph), graph_document())
        self.assertEqual(canonical_candidate_graph_sha256(graph), graph.artifact_hash)
        self.assertFalse(graph.runtime_authorized)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            graph.graph_id = "GRAPH-OTHER"  # type: ignore[misc]
        self.assertEqual(FIXTURE.read_bytes(), before)

    def test_duplicate_identifiers_fail(self) -> None:
        cases = []
        duplicate_node = graph_document()
        duplicate_node["nodes"][1]["node_id"] = duplicate_node["nodes"][0]["node_id"]
        cases.append((duplicate_node, "GRAPH_V1_DUPLICATE_NODE_ID"))
        duplicate_variable = graph_document()
        duplicate_variable["nodes"][1]["variable_name"] = duplicate_variable["nodes"][0]["variable_name"]
        cases.append((duplicate_variable, "GRAPH_V1_DUPLICATE_VARIABLE"))
        duplicate_edge = graph_document()
        duplicate_edge["edges"].append(copy.deepcopy(duplicate_edge["edges"][0]))
        duplicate_edge["edges"][1]["source_node"], duplicate_edge["edges"][1]["target_node"] = duplicate_edge["edges"][1]["target_node"], duplicate_edge["edges"][1]["source_node"]
        cases.append((duplicate_edge, "GRAPH_V1_DUPLICATE_EDGE_ID"))
        for document, code in cases:
            with self.subTest(code=code), self.assertRaises(GraphV1ModelError) as caught:
                parse_candidate_graph(rehash(document))
            self.assertEqual(caught.exception.issue_code, code)

    def test_endpoint_self_edge_and_ranges_fail(self) -> None:
        cases = []
        endpoint = graph_document(); endpoint["edges"][0]["target_node"] = "NODE-UNKNOWN-032C"
        cases.append((endpoint, "GRAPH_V1_UNKNOWN_ENDPOINT"))
        self_edge = graph_document(); self_edge["edges"][0]["target_node"] = self_edge["edges"][0]["source_node"]
        cases.append((self_edge, "GRAPH_V1_SELF_EDGE"))
        lag = graph_document(); lag["edges"][0]["lag_candidate_range"].update(minimum=6, maximum=5)
        cases.append((lag, "GRAPH_V1_LAG_ORDER"))
        uncertainty = graph_document(); uncertainty["edges"][0]["uncertainty"].update(lower=0.9, upper=0.8)
        cases.append((uncertainty, "GRAPH_V1_UNCERTAINTY_ORDER"))
        for document, code in cases:
            with self.subTest(code=code), self.assertRaises(GraphV1ModelError) as caught:
                parse_candidate_graph(rehash(document))
            self.assertEqual(caught.exception.issue_code, code)

    def test_causal_claim_is_rejected_structurally(self) -> None:
        document = graph_document(); document["edges"][0]["causal_claim_allowed"] = True
        with self.assertRaises(GraphV1ModelError) as caught:
            parse_candidate_graph(rehash(document))
        self.assertEqual(caught.exception.issue_code, "GRAPH_V1_STRUCTURAL_INVALID")


if __name__ == "__main__":
    unittest.main()
