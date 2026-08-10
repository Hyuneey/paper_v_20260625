from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.candidates.metadata_candidate_discovery_v1 import (
    OFFICIAL_GRAPH_CLAIM_BOUNDARY,
    OFFICIAL_GRAPH_GIT_BLOB,
    OFFICIAL_GRAPH_SHA256,
    OFFICIAL_MANUAL_GIT_BLOB,
    OFFICIAL_MANUAL_SHA256,
    FrozenUniverseBindingV1,
    MetadataCandidateDiscoveryError,
    MetadataPairEvidenceRecordV1,
    OfficialPhysicalGraphV1,
    ReviewedMetadataEvidenceInputV1,
    assert_public_metadata_payload_v1,
    authorize_metadata_reference_path_v1,
    build_metadata_candidate_result_v1,
    discover_metadata_pair_records_v1,
    load_frozen_c0_universe_v1,
    rank_supported_metadata_records_v1,
    validate_evidence_against_universe_v1,
    validate_metadata_candidate_result_v1,
)
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/v6/task039c0_candidate_discovery_protocol.json"
BUNDLE_PATH = ROOT / "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json"
SCHEMA_PATH = ROOT / "schemas/v6/metadata_candidate_result_v1_schema.json"
PUBLIC_RESULT_PATH = ROOT / "docs/task_reports/TASK-039C_META_RESULT.json"
PUBLIC_AUDIT_PATH = ROOT / "docs/task_reports/TASK-039C_META_DATA_ACCESS_AUDIT.json"
PUBLIC_REPORT_PATH = ROOT / "docs/task_reports/TASK-039C_META_REPORT.md"
PRIVATE_LEDGER_PATH = ROOT / "artifacts/task039c_meta/TASK-039C_META_EVIDENCE_LEDGER.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reference(
    reference_id: str, source_id: str, locator: str
) -> dict[str, str]:
    if source_id == "official_HAI_technical_manual":
        content_hash, blob = OFFICIAL_MANUAL_SHA256, OFFICIAL_MANUAL_GIT_BLOB
    else:
        content_hash, blob = OFFICIAL_GRAPH_SHA256, OFFICIAL_GRAPH_GIT_BLOB
    return {
        "content_sha256": content_hash,
        "git_blob_sha": blob,
        "independent_source_id": source_id,
        "locator": locator,
        "reference_id": reference_id,
    }


def _synthetic_evidence_payload(universe: FrozenUniverseBindingV1) -> dict:
    sources = universe.source_variables
    targets = universe.target_variables
    source_nodes = {variable: f"S{index:02d}" for index, variable in enumerate(sources)}
    target_nodes = {variable: f"T{index:02d}" for index, variable in enumerate(targets)}
    subsystem_source = sources[2]
    subsystem_target = targets[2]
    payload = {
        "artifact_type": "task039c_meta_reviewed_metadata_evidence_input_v1",
        "graph_reference_id": "META_FIXTURE_GRAPH",
        "manual_explicit_pairs": [
            {
                "reference_ids": ["META_FIXTURE_MANUAL_EXPLICIT"],
                "source_identity": sources[0],
                "target_identity": targets[0],
            }
        ],
        "reference_catalog": [
            _reference(
                "META_FIXTURE_GRAPH",
                "official_P1_process_physical_graph",
                "graph:synthetic_fixture",
            ),
            _reference(
                "META_FIXTURE_MANUAL_EXPLICIT",
                "official_HAI_technical_manual",
                "manual:synthetic_explicit",
            ),
            _reference(
                "META_FIXTURE_MANUAL_MAPPING",
                "official_HAI_technical_manual",
                "manual:synthetic_mapping",
            ),
            _reference(
                "META_FIXTURE_MANUAL_SUBSYSTEM",
                "official_HAI_technical_manual",
                "manual:synthetic_subsystem",
            ),
        ],
        "schema_version": "1.0.0",
        "snapshot_commit": "2a814cebc9a66b06c9e5cd545e2d72e65d383737",
        "source_graph_bindings": [
            {
                "graph_node_id": source_nodes[variable],
                "reference_ids": ["META_FIXTURE_MANUAL_MAPPING"],
                "variable": variable,
            }
            for variable in sources
        ],
        "source_subsystem_bindings": [
            {
                "reference_ids": (
                    ["META_FIXTURE_MANUAL_SUBSYSTEM"]
                    if variable == subsystem_source
                    else []
                ),
                "subsystem_ids": ["SYNTHETIC_LOOP"] if variable == subsystem_source else [],
                "variable": variable,
            }
            for variable in sources
        ],
        "target_graph_bindings": [
            {
                "graph_node_id": target_nodes[variable],
                "reference_ids": ["META_FIXTURE_MANUAL_MAPPING"],
                "variable": variable,
            }
            for variable in targets
        ],
        "target_subsystem_bindings": [
            {
                "reference_ids": (
                    ["META_FIXTURE_MANUAL_SUBSYSTEM"]
                    if variable == subsystem_target
                    else []
                ),
                "subsystem_ids": ["SYNTHETIC_LOOP"] if variable == subsystem_target else [],
                "variable": variable,
            }
            for variable in targets
        ],
        "task_id": "TASK-039C-META",
    }
    payload["evidence_input_hash"] = stable_hash_v1(payload)
    return payload


def _pair_record(
    source: str,
    target: str,
    tier: str,
    reference_count: int,
) -> MetadataPairEvidenceRecordV1:
    if tier == "M1_EXPLICIT":
        summary = "manual_explicit_control_chain"
        graph, subsystem, manual, supported = False, False, True, True
    elif tier == "M2_GRAPH_ADJACENT":
        summary = "graph_adjacent_with_reviewed_semantic_mapping"
        graph, subsystem, manual, supported = True, False, True, True
    elif tier == "M3_SUBSYSTEM_SUPPORTED":
        summary = "reviewed_same_control_subsystem_no_direct_graph_edge"
        graph, subsystem, manual, supported = False, True, True, True
    else:
        summary = "no_approved_prioritization_evidence"
        graph, subsystem, manual, supported = False, False, False, False
    return MetadataPairEvidenceRecordV1(
        source_identity=source,
        target_identity=target,
        evidence_tier=tier,
        independent_official_reference_count=reference_count,
        reference_identifiers=(f"REF_{source}_{target}",) if supported else (),
        graph_evidence_present=graph,
        subsystem_evidence_present=subsystem,
        manual_semantic_evidence_present=manual,
        evidence_summary=summary,
        supported_status=supported,
    )


class Task039CMetaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.universe = load_frozen_c0_universe_v1(
            config_payload=_load(CONFIG_PATH), bundle_payload=_load(BUNDLE_PATH)
        )
        cls.evidence_payload = _synthetic_evidence_payload(cls.universe)
        cls.evidence = ReviewedMetadataEvidenceInputV1.from_dict(cls.evidence_payload)
        source_nodes = {
            item.variable: item.graph_node_id for item in cls.evidence.source_graph_bindings
        }
        target_nodes = {
            item.variable: item.graph_node_id for item in cls.evidence.target_graph_bindings
        }
        cls.graph = OfficialPhysicalGraphV1(
            node_ids=frozenset((*source_nodes.values(), *target_nodes.values())),
            directed_edges=frozenset(
                {
                    (
                        source_nodes[cls.universe.source_variables[1]],
                        target_nodes[cls.universe.target_variables[1]],
                    )
                }
            ),
        )
        cls.records = discover_metadata_pair_records_v1(
            universe=cls.universe, evidence=cls.evidence, graph=cls.graph
        )
        cls.result = build_metadata_candidate_result_v1(
            records=cls.records,
            code_commit="a" * 40,
            created_at="2026-08-10T00:00:00+09:00",
            evidence_ledger_hash="b" * 64,
            data_access_audit_ref="c" * 64,
        )

    def _record(self, source_index: int, target_index: int) -> MetadataPairEvidenceRecordV1:
        identity = (
            self.universe.source_variables[source_index],
            self.universe.target_variables[target_index],
        )
        return next(record for record in self.records if record.identity == identity)

    def test_exact_144_pair_universe_binding(self) -> None:
        self.assertEqual(len(self.universe.source_variables), 12)
        self.assertEqual(len(self.universe.target_variables), 12)
        self.assertEqual(len(self.universe.pairs), 144)
        self.assertEqual(len(self.records), 144)

    def test_out_of_universe_rejection(self) -> None:
        payload = deepcopy(self.evidence_payload)
        payload["manual_explicit_pairs"][0]["source_identity"] = "P1_UNKNOWN"
        payload.pop("evidence_input_hash")
        payload["evidence_input_hash"] = stable_hash_v1(payload)
        evidence = ReviewedMetadataEvidenceInputV1.from_dict(payload)
        with self.assertRaises(MetadataCandidateDiscoveryError):
            validate_evidence_against_universe_v1(self.universe, evidence)

    def test_feature_value_access_prohibition(self) -> None:
        with self.assertRaises(MetadataCandidateDiscoveryError):
            authorize_metadata_reference_path_v1(
                Path("hai-train1.csv"), "technical_manual"
            )

    def test_br2_pair_result_rejection(self) -> None:
        with self.assertRaises(MetadataCandidateDiscoveryError):
            authorize_metadata_reference_path_v1(
                Path("BR2_directional_fit_records.json"), "physical_graph"
            )

    def test_m1_classification(self) -> None:
        self.assertEqual(self._record(0, 0).evidence_tier, "M1_EXPLICIT")

    def test_m2_classification(self) -> None:
        self.assertEqual(self._record(1, 1).evidence_tier, "M2_GRAPH_ADJACENT")

    def test_m3_classification(self) -> None:
        self.assertEqual(self._record(2, 2).evidence_tier, "M3_SUBSYSTEM_SUPPORTED")

    def test_unsupported_classification(self) -> None:
        self.assertEqual(self._record(3, 3).evidence_tier, "UNSUPPORTED")

    def test_reference_count_ranking(self) -> None:
        entries = (
            _pair_record("S2", "T2", "M1_EXPLICIT", 1),
            _pair_record("S1", "T1", "M1_EXPLICIT", 2),
        )
        ranked = rank_supported_metadata_records_v1(entries)
        self.assertEqual(ranked[0].source_identity, "S1")

    def test_canonical_tie_break(self) -> None:
        entries = (
            _pair_record("S2", "T1", "M2_GRAPH_ADJACENT", 2),
            _pair_record("S1", "T2", "M2_GRAPH_ADJACENT", 2),
            _pair_record("S1", "T1", "M2_GRAPH_ADJACENT", 2),
        )
        ranked = rank_supported_metadata_records_v1(entries)
        self.assertEqual(
            [item.identity for item in ranked],
            [("S1", "T1"), ("S1", "T2"), ("S2", "T1")],
        )

    def test_unsupported_not_used_for_padding(self) -> None:
        self.assertEqual(self.result["supported_count"], 3)
        self.assertEqual(len(self.result["top40_identities"]), 3)
        self.assertNotIn(
            self._record(3, 3).identity,
            {
                (item["source_identity"], item["target_identity"])
                for item in self.result["top40_identities"]
            },
        )

    def test_top10_20_40_are_same_ranking_prefix(self) -> None:
        top10 = self.result["top10_identities"]
        top20 = self.result["top20_identities"]
        top40 = self.result["top40_identities"]
        self.assertEqual(top10, top20[:10])
        self.assertEqual(top20, top40[:20])

    def test_candidate_shortfall(self) -> None:
        self.assertTrue(self.result["candidate_shortfall"]["top10"]["candidate_shortfall"])
        self.assertEqual(self.result["candidate_shortfall"]["top10"]["shortfall_count"], 7)

    def test_no_numerical_weighted_score(self) -> None:
        self.assertFalse(self.result["numerical_weighting_used"])
        self.assertNotIn("weighted_score", json.dumps(self.result, sort_keys=True))

    def test_official_graph_not_causal_truth(self) -> None:
        self.assertEqual(
            self.result["official_graph_claim_boundary"],
            OFFICIAL_GRAPH_CLAIM_BOUNDARY,
        )

    def test_deterministic_serialization(self) -> None:
        repeated = build_metadata_candidate_result_v1(
            records=self.records,
            code_commit="a" * 40,
            created_at="2026-08-10T00:00:00+09:00",
            evidence_ledger_hash="b" * 64,
            data_access_audit_ref="c" * 64,
        )
        self.assertEqual(repeated, self.result)
        self.assertEqual(
            json.dumps(repeated, sort_keys=True, separators=(",", ":")),
            json.dumps(self.result, sort_keys=True, separators=(",", ":")),
        )

    def test_self_hash(self) -> None:
        validate_metadata_candidate_result_v1(self.result)
        changed = deepcopy(self.result)
        changed["artifact_hash"] = "0" * 64
        with self.assertRaises(MetadataCandidateDiscoveryError):
            validate_metadata_candidate_result_v1(changed)

    def test_unknown_field_rejection(self) -> None:
        changed = deepcopy(self.result)
        changed["numerical_score"] = 1
        with self.assertRaises(ValueError):
            validate_metadata_candidate_result_v1(changed)

    def test_public_leak_boundary(self) -> None:
        assert_public_metadata_payload_v1(self.result)
        changed = deepcopy(self.result)
        changed["creation_metadata"]["private_path"] = "C:/Users/research/private"
        with self.assertRaises(MetadataCandidateDiscoveryError):
            assert_public_metadata_payload_v1(changed)

    def test_result_schema_is_closed_and_validates(self) -> None:
        schema = _load(SCHEMA_PATH)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.result)
        self.assertFalse(schema["additionalProperties"])

    def test_evidence_input_unknown_field_rejection(self) -> None:
        changed = deepcopy(self.evidence_payload)
        changed["feature_values"] = []
        with self.assertRaises(ValueError):
            ReviewedMetadataEvidenceInputV1.from_dict(changed)

    def test_executed_public_result_when_present(self) -> None:
        if not PUBLIC_RESULT_PATH.is_file():
            self.skipTest("scientific META result is not created until clean Commit A")
        result = _load(PUBLIC_RESULT_PATH)
        validate_metadata_candidate_result_v1(result)
        Draft202012Validator(_load(SCHEMA_PATH)).validate(result)

    def test_executed_audit_and_ledger_self_hashes_when_present(self) -> None:
        if not PUBLIC_AUDIT_PATH.is_file() or not PRIVATE_LEDGER_PATH.is_file():
            self.skipTest("execution artifacts are not created until clean Commit A")
        audit = _load(PUBLIC_AUDIT_PATH)
        ledger = _load(PRIVATE_LEDGER_PATH)
        for payload in (audit, ledger):
            observed = payload.pop("artifact_hash")
            self.assertEqual(stable_hash_v1(payload), observed)
        self.assertFalse(audit["real_hai_feature_values_accessed"])
        self.assertFalse(audit["br2_pair_supervision_used"])
        self.assertEqual(ledger["evaluated_pair_count"], 144)

    def test_executed_public_report_boundary_when_present(self) -> None:
        if not PUBLIC_REPORT_PATH.is_file():
            self.skipTest("scientific META report is not created until clean Commit A")
        text = PUBLIC_REPORT_PATH.read_text(encoding="utf-8").lower()
        self.assertNotRegex(text, r"[a-z]:[\\/](?:users|documents|desktop)[\\/]")
        for token in ("hai-train", "hai-test", "label-test", "br2_private"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
