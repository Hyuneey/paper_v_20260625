from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
REPO = RCC.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperworks.v6.common import stable_hash_v1  # noqa: E402


class MetaLineageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = RCC / "validation_v2" / "meta_lineage"
        cls.classification = json.loads(
            (cls.base / "META_LINEAGE_CLASSIFICATION_V1.json").read_text(encoding="utf-8")
        )
        cls.graph = json.loads(
            (cls.base / "META_PROVENANCE_GRAPH_V1.json").read_text(encoding="utf-8")
        )
        cls.result_path = REPO / "docs" / "task_reports" / "TASK-039C_META_RESULT.json"
        cls.result = json.loads(cls.result_path.read_text(encoding="utf-8"))
        cls.access_audit_path = (
            REPO / "docs" / "task_reports" / "TASK-039C_META_DATA_ACCESS_AUDIT.json"
        )
        cls.access_audit = json.loads(cls.access_audit_path.read_text(encoding="utf-8"))

    def test_public_artifacts_self_hash(self) -> None:
        for document in (self.classification, self.graph):
            content = {key: value for key, value in document.items() if key != "artifact_hash"}
            self.assertEqual(document["artifact_hash"], stable_hash_v1(content))

    def test_classification_and_reproducibility_are_conservative(self) -> None:
        self.assertEqual(
            self.classification["primary_provenance_class"], "HYBRID_REVIEWED_METADATA"
        )
        self.assertEqual(
            self.classification["authorship_qualifier"], "AI_ASSISTED_METADATA_EXTRACTION"
        )
        self.assertEqual(
            self.classification["human_intervention_level"], "HUMAN_INTERVENTION_LEVEL_1"
        )
        self.assertEqual(
            self.classification["public_reproducibility"],
            "PARTIALLY_REPRODUCIBLE_PRIVATE_REVIEWED_INPUT_REQUIRED",
        )

    def test_frozen_meta_result_and_top20_identity(self) -> None:
        result_content = {key: value for key, value in self.result.items() if key != "artifact_hash"}
        self.assertEqual(self.result["artifact_hash"], stable_hash_v1(result_content))
        self.assertEqual(
            self.result["artifact_hash"],
            "0e3b055df911c74bd0e0993b7b3bb122860b265192ad0cf91d54edc1e74635bf",
        )
        self.assertEqual(
            hashlib.sha256(self.result_path.read_bytes()).hexdigest(),
            "7af95ab723a9fd3ea1ab0e2dae5be5a5796e0e58dbd14563652dfb0c6e65e688",
        )
        top20 = self.result["top20_identities"]
        self.assertEqual(
            stable_hash_v1({"top20_identities": top20}),
            "6a46d85891dd3d4f95f2b4c859bf91cbbdeb4582be3d2b72c6396737431d7286",
        )
        self.assertEqual(self.result["evaluated_pair_count"], 144)
        self.assertEqual(len(top20), 20)

    def test_public_data_boundary_and_official_reference_identities_replay(self) -> None:
        audit_content = {
            key: value for key, value in self.access_audit.items() if key != "artifact_hash"
        }
        self.assertEqual(self.access_audit["artifact_hash"], stable_hash_v1(audit_content))
        references = {
            row["reference_kind"]: (row["content_sha256"], row["git_blob_sha"])
            for row in self.access_audit["official_reference_files"]
        }
        self.assertEqual(
            references,
            {
                "official_HAI_technical_manual": (
                    "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556",
                    "18cb88514176e1c641f584cf24ac8e9559432b38",
                ),
                "official_P1_process_physical_graph": (
                    "eca648d73c0444a35294608c2a1067256d7b32547257153226fece2de3febd07",
                    "c47dc78fdef88ec1f5973280e179707cca36231b",
                ),
            },
        )
        self.assertEqual(self.access_audit["feature_value_file_access_count"], 0)
        self.assertEqual(self.access_audit["prohibited_input_access_count"], 0)

    def test_graph_references_are_closed_and_transformations_explicit(self) -> None:
        node_ids = {row["node_id"] for row in self.graph["nodes"]}
        self.assertEqual(len(node_ids), len(self.graph["nodes"]))
        for edge in self.graph["edges"]:
            self.assertIn(edge["source"], node_ids)
            self.assertIn(edge["target"], node_ids)
            self.assertIn(
                edge["transformation"],
                {
                    "AI_ASSISTED_EXTRACTION",
                    "AUTOMATIC_CODE_TRANSFORMATION",
                    "STATIC_DECLARATION",
                },
            )

    def test_private_input_is_not_embedded_in_public_outputs(self) -> None:
        combined = "\n".join(path.read_text(encoding="utf-8") for path in self.base.iterdir())
        self.assertNotRegex(combined, r"[A-Za-z]:[\\/](?:Users|Desktop|Documents)[\\/]")
        self.assertNotIn("private reviewed-evidence file contents", combined.lower())
        self.assertEqual(self.classification["safety"]["private_exposures"], 0)

    def test_meta_scientific_outputs_remain_outside_audit_namespace(self) -> None:
        allowed = {
            "META_LINEAGE_AUDIT_V1.md",
            "META_LINEAGE_CLASSIFICATION_V1.json",
            "META_PROVENANCE_GRAPH_V1.json",
            "META_THESIS_WORDING_V1.md",
        }
        self.assertEqual({path.name for path in self.base.iterdir()}, allowed)


if __name__ == "__main__":
    unittest.main()
