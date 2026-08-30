from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


RCC = Path(__file__).resolve().parents[1]
SCRIPTS = RCC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_dashboard import load_registry, registry_digest, render_dashboard  # noqa: E402
from dashboard_v2 import build_dashboard_view_model, load_dashboard_config  # noqa: E402


class DashboardV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_registry(RCC)
        cls.html = render_dashboard(cls.data, registry_digest(RCC), RCC)
        cls.vm = build_dashboard_view_model(cls.data, registry_digest(RCC), RCC)
        cls.css = (RCC / "dashboard" / "assets" / "rcc.css").read_text(encoding="utf-8")
        cls.js = (RCC / "dashboard" / "assets" / "rcc.js").read_text(encoding="utf-8")

    def test_exactly_five_primary_navigation_items(self) -> None:
        self.assertEqual(5, self.html.count('class="primary-nav-item'))
        self.assertEqual(["개요", "아키텍처", "실험·결과", "준비도·위험", "이력·근거"], [row["label_ko"] for row in self.vm["navigation"]])
        self.assertNotIn("section-nav", self.html)

    def test_architecture_nodes_and_edges_are_valid(self) -> None:
        node_ids = [node["node_id"] for node in self.vm["nodes"]]
        self.assertEqual(14, len(node_ids))
        self.assertEqual(len(node_ids), len(set(node_ids)))
        valid = set(node_ids)
        self.assertTrue(all(edge["source_node_id"] in valid and edge["target_node_id"] in valid for edge in self.vm["edges"]))
        self.assertEqual(len(self.vm["edges"]), len({edge["edge_id"] for edge in self.vm["edges"]}))

    def test_document_ids_are_unique(self) -> None:
        ids = re.findall(r'(?<![\w-])id="([^"]+)"', self.html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_top_level_node_supports_drawer_interaction(self) -> None:
        for node in self.vm["nodes"]:
            self.assertIn(f'data-node-id="{node["node_id"]}"', self.html)
        self.assertIn('id="detail-drawer"', self.html)
        self.assertIn("selectNode", self.js)
        self.assertIn("renderNodeDrawer", self.js)

    def test_easy_and_technical_drawer_modes_exist(self) -> None:
        self.assertIn('data-drawer-mode="easy"', self.html)
        self.assertIn('data-drawer-mode="technical"', self.html)
        self.assertIn("Input", self.js)
        self.assertIn("process", self.js)
        self.assertIn("Output", self.js)

    def test_frozen_pilot_values_and_overlap_are_single_source_asserted(self) -> None:
        expected = {
            "D0": (11, 14, 0.4939336325682589),
            "D1": (13, 14, 40.50255787059723),
            "D2 V1": (11, 14, 0.7056194750975128),
            "D2 V2": (11, 14, 6.915070855955625),
        }
        actual = {row["method"]: (row["detected"], row["total"], row["far"]) for row in self.vm["pilot_results"]}
        self.assertEqual(expected, actual)
        self.assertEqual({"both": 10, "d0_only": 1, "d1_only": 3, "neither": 0}, self.vm["overlap"])

    def test_candidate_and_construction_values_are_asserted(self) -> None:
        self.assertEqual({"universe": 144, "META": 20, "STAT": 20, "GDN": 20, "union": 47, "confirmed": 42}, self.vm["candidate_path"])
        self.assertEqual({"T0": "42/42", "T1": "42/42", "T1-B": "42/42", "T2": "39/42", "feedback_actions": 0}, self.vm["construction"])

    def test_experiment_gates_match_gap_registry(self) -> None:
        gates = {row["experiment_id"]: row["gate"]["ready_now"] for row in self.vm["experiments"]}
        self.assertEqual("BLOCKED", gates["EXP-01"])
        self.assertEqual("READY_WITH_CONDITIONS", gates["EXP-02"])
        self.assertEqual("NOT_REQUIRED", gates["EXP-06"])

    def test_korean_primary_labels_preserve_scientific_identifiers(self) -> None:
        for label in ("현재 연구 단계", "정확한 다음 작업", "전체 연구 시스템 지도", "결과 무결성 확인", "과학적 검증"):
            self.assertIn(label, self.html)
        for identifier in ("D0", "D1", "D2", "META", "STAT", "GDN", "COMMON-42", "PASS", "FAIL", "ABSTAIN"):
            self.assertIn(identifier, self.html)

    def test_no_external_runtime_dependency(self) -> None:
        self.assertIsNone(re.search(r'<(?:script|link)[^>]+(?:https?:)?//', self.html))
        self.assertNotIn("fetch(", self.js)
        self.assertNotIn("XMLHttpRequest", self.js)

    def test_local_links_resolve(self) -> None:
        refs = re.findall(r'(?:href|src)="([^"]+)"', self.html)
        for ref in refs:
            if ref.startswith("#"):
                continue
            target = (RCC / "dashboard" / ref).resolve()
            self.assertTrue(target.is_file(), ref)

    def test_mobile_and_reduced_motion_contracts_exist(self) -> None:
        self.assertIn('id="mobile-nav-toggle"', self.html)
        self.assertIn("@media (max-width:680px)", self.css)
        self.assertIn("prefers-reduced-motion:reduce", self.css)
        self.assertIn("detail-drawer", self.css)

    def test_accessibility_contracts_exist(self) -> None:
        self.assertIn('class="skip-link"', self.html)
        self.assertIn('role="button" tabindex="0"', self.html)
        self.assertIn('aria-label="연구 아키텍처 지도"', self.html)
        self.assertIn('class="table-wrap accessible-data"', self.html)
        self.assertIn("focus-visible", self.css)

    def test_legacy_snapshot_and_config_exist(self) -> None:
        self.assertTrue((RCC / "dashboard" / "legacy" / "dashboard_v1_before_visual_redesign.html").is_file())
        config = load_dashboard_config(RCC)
        self.assertEqual(14, len(config["nodes"]))
        for name in ("architecture_nodes.csv", "architecture_edges.csv", "architecture_groups.json", "dashboard_layout.json", "display_labels_ko.json", "visual_tokens.json"):
            self.assertTrue((RCC / "dashboard_config" / name).is_file())

    def test_registry_digest_is_embedded_without_state_override(self) -> None:
        digest = registry_digest(RCC)
        self.assertEqual(digest, self.vm["registry_digest"])
        self.assertIn(digest, self.html)
        self.assertEqual(0, self.vm["safety"]["private_exposures"])


if __name__ == "__main__":
    unittest.main()
