from __future__ import annotations

import html
import sys
import tempfile
import unittest
from pathlib import Path


RCC_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = RCC_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_dashboard import (  # noqa: E402
    AUTHORITY_COMMIT,
    build_dashboard,
    generate_summaries,
    load_registry,
    registry_digest,
    render_dashboard,
    render_gpt_brief,
)
import validate_registry as validator  # noqa: E402


class DashboardGenerationTests(unittest.TestCase):
    def test_dashboard_is_registry_derived(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        for component in data["components"]:
            self.assertIn(component["name"], rendered)
            self.assertIn(component["status"], rendered)
        for user_task in data["state"]["top_user_todo"]:
            self.assertIn(html.escape(user_task), rendered)

    def test_required_sections_and_authority_warning_render(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        for heading in (
            "CURRENT STATE", "MY TASKS", "DECISION INBOX", "ARCHITECTURE OVERVIEW",
            "COMPONENT STATUS", "EXPERIMENT STATUS", "CLAIM &amp; EVIDENCE", "RISKS",
            "RESEARCH HISTORY", "SOURCE AUTHORITY", "RECENT CHANGE / NEXT TASK",
        ):
            self.assertIn(heading, rendered)
        self.assertIn(AUTHORITY_COMMIT, rendered)
        self.assertIn("NOT AUTHORITATIVE", rendered)

    def test_dashboard_uses_only_local_assets(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        self.assertNotIn("https://", rendered)
        self.assertNotIn("http://", rendered)
        self.assertIn('href="assets/rcc.css"', rendered)
        self.assertIn('src="assets/rcc.js"', rendered)

    def test_search_and_status_filter_controls_exist(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        self.assertIn('id="registry-search"', rendered)
        self.assertIn('id="status-filter"', rendered)
        script = (RCC_ROOT / "dashboard" / "assets" / "rcc.js").read_text(encoding="utf-8")
        self.assertIn("applyFilters", script)
        self.assertIn('value="CRITICAL"', rendered)

    def test_gpt_brief_has_required_recovery_boundary_and_word_budget(self) -> None:
        brief = render_gpt_brief(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        self.assertIn("Chat memory must not override the scientific authority or RCC registry.", brief)
        self.assertIn("14 attack events are pilot evidence only", brief)
        self.assertIn("Graph-Guided and Agentic remain provisional contribution labels.", brief)
        self.assertIn("## Research objective", brief)
        self.assertIn("## Claim boundaries", brief)
        self.assertIn("## How we got here", brief)
        self.assertIn("History explains this lineage but cannot override", brief)
        self.assertIn("## Exact next task", brief)
        self.assertGreaterEqual(len(brief.split()), 800)
        self.assertLessEqual(len(brief.split()), 1500)

    def test_builders_write_all_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "research_control_center"
            (root / "registry").mkdir(parents=True)
            for source in (RCC_ROOT / "registry").iterdir():
                if source.is_file():
                    (root / "registry" / source.name).write_bytes(source.read_bytes())
            dashboard = build_dashboard(root)
            summaries = generate_summaries(root)
            self.assertTrue(dashboard.is_file())
            self.assertEqual(36, len(summaries))
            self.assertTrue(all(path.is_file() for path in summaries))
            self.assertTrue((root / "history" / "PROJECT_TIMELINE.md").is_file())
            self.assertTrue((root / "generated" / "RCC_003_HISTORY_SUMMARY.md").is_file())

    def test_dashboard_has_population_counts_and_architecture_nodes(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        for label in ("Implemented", "Executed", "Evidence-reviewed", "Independently reproduced"):
            self.assertIn(label, rendered)
        self.assertNotIn("Claim-ready", rendered)
        for component_id in ("DATA_PROVENANCE", "GDN_DISCOVERY", "D0_PCA_SPE", "D1_RULE_ONLY"):
            name = next(row["name"] for row in load_registry(RCC_ROOT)["components"] if row["component_id"] == component_id)
            self.assertIn(name, rendered)

    def test_arch000_dashboard_exposes_clickable_contracts(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        for section in ("DATA", "DISCOVERY", "RELATION", "RULE", "VERIFIER", "RUNTIME", "D0", "D1", "D2", "METRICS", "REPRODUCIBILITY"):
            self.assertIn(f'id="arch-{section.lower()}"', rendered)
        for label in ("ROLE", "INPUT", "OUTPUT", "CODE", "EXECUTED?", "FROZEN RESULT USED?", "VALIDATION STATE", "NEXT DEEP REVIEW"):
            self.assertIn(label, rendered)

    def test_status_semantics_are_non_linear_and_claim_registry_authoritative(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        self.assertIn("These counts are not a single completion percentage.", rendered)
        self.assertIn(
            "Code existence, execution, evidence review, independent reproduction, and scientific validation are separate states.",
            rendered,
        )
        self.assertIn("source or evidence status was reviewed", rendered)
        self.assertIn("explicit scientific result-integrity audits are shown separately", rendered)
        self.assertIn("claims.csv", rendered)
        self.assertNotRegex(rendered, r"\b\d+(?:\.\d+)?\s*%")
        self.assertGreater(
            sum(row["audited"] == "true" for row in data["components"]),
            sum(row["executed"] == "true" for row in data["components"]),
        )

    def test_claim_headline_counts_derive_from_claims_registry(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        expected = {
            "Supported implementation": "SUPPORTED_IMPLEMENTATION",
            "Pilot only": "PILOT_ONLY",
            "Unvalidated": "UNVALIDATED",
            "Not supported": "NOT_SUPPORTED",
            "Conditional": "CONDITIONAL",
        }
        for label, status in expected.items():
            count = sum(row["status"] == status for row in data["claims"])
            self.assertIn(f"<dt>{label}</dt><dd>{count}</dd>", rendered)

    def test_user_summary_and_context_preserve_pilot_boundaries(self) -> None:
        generated = generate_summaries(RCC_ROOT)
        self.assertEqual(36, len(generated))
        user_summary = (RCC_ROOT / "generated" / "RCC_002_USER_SUMMARY.md").read_text(encoding="utf-8")
        context = (RCC_ROOT / "CURRENT_CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("14", user_summary)
        self.assertIn("예비", user_summary)
        for heading in ("WHAT EXISTS", "WHAT WAS EXECUTED", "WHAT WAS OBSERVED", "WHAT IS VALIDATED", "WHAT REMAINS UNKNOWN"):
            self.assertIn(heading, context)

    def test_history_dashboard_is_curated_and_registry_derived(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        self.assertEqual(12, len(data["history"]["dashboard_event_ids"]))
        self.assertIn("EVENT-013", data["history"]["dashboard_event_ids"])
        self.assertIn("RESEARCH HISTORY", rendered)
        self.assertIn("USER_CONTEXT entries preserve uncertainty", rendered)
        for event_id in data["history"]["dashboard_event_ids"]:
            event = next(row for row in data["timeline"] if row["event_id"] == event_id)
            self.assertIn(event["title"], rendered)

    def test_generated_history_preserves_temporal_corrections(self) -> None:
        generate_summaries(RCC_ROOT)
        lineage = (RCC_ROOT / "history" / "PROFESSOR_FEEDBACK_LINEAGE.md").read_text(encoding="utf-8")
        summary = (RCC_ROOT / "generated" / "RCC_003_HISTORY_SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("2026-08-18", lineage)
        self.assertIn("not professor feedback", lineage)
        self.assertIn("2026-08-26", lineage)
        self.assertIn("8월 3일 고정", summary)
        self.assertIn("pilot evidence", summary)
        self.assertIn("구조적 한계를 명시적인 계약", summary)
        self.assertNotIn("Only a possible lesson", summary)

    def test_generated_outputs_match_current_registry_digest(self) -> None:
        result = validator.validate_registry(RCC_ROOT, check_git=True, check_outputs=True)
        self.assertEqual([], result.errors)


if __name__ == "__main__":
    unittest.main()
