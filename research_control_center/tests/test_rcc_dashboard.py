from __future__ import annotations

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
            self.assertIn(user_task, rendered)

    def test_required_sections_and_authority_warning_render(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        for heading in (
            "CURRENT STATE", "MY TASKS", "DECISION INBOX", "ARCHITECTURE OVERVIEW",
            "COMPONENT STATUS", "EXPERIMENT STATUS", "CLAIM &amp; EVIDENCE", "RISKS",
            "SOURCE AUTHORITY", "RECENT CHANGE / NEXT TASK",
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
            self.assertEqual(7, len(summaries))
            self.assertTrue(all(path.is_file() for path in summaries))

    def test_dashboard_has_population_counts_and_architecture_nodes(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        for label in ("Implemented", "Executed", "Audited", "Reproduced", "Claim-ready"):
            self.assertIn(label, rendered)
        for component_id in ("DATA_PROVENANCE", "GDN_DISCOVERY", "D0_PCA_SPE", "D1_RULE_ONLY"):
            name = next(row["name"] for row in load_registry(RCC_ROOT)["components"] if row["component_id"] == component_id)
            self.assertIn(name, rendered)

    def test_user_summary_and_context_preserve_pilot_boundaries(self) -> None:
        generated = generate_summaries(RCC_ROOT)
        self.assertEqual(7, len(generated))
        user_summary = (RCC_ROOT / "generated" / "RCC_002_USER_SUMMARY.md").read_text(encoding="utf-8")
        context = (RCC_ROOT / "CURRENT_CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("14", user_summary)
        self.assertIn("예비", user_summary)
        for heading in ("WHAT EXISTS", "WHAT WAS EXECUTED", "WHAT WAS OBSERVED", "WHAT IS VALIDATED", "WHAT REMAINS UNKNOWN"):
            self.assertIn(heading, context)

    def test_generated_outputs_match_current_registry_digest(self) -> None:
        result = validator.validate_registry(RCC_ROOT, check_git=True, check_outputs=True)
        self.assertEqual([], result.errors)


if __name__ == "__main__":
    unittest.main()
