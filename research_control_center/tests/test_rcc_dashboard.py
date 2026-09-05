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
    STATUS_DISPLAY_LABELS,
    _ko_text,
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
            self.assertIn(component["component_id"], rendered)
            self.assertIn(component["name"], rendered)
        self.assertIn(html.escape(data["state"]["exact_next_task"]), rendered)
        self.assertIn('id="rcc-view-model"', rendered)
        if data["state"].get("exp03b_execution"):
            self.assertNotIn('"decision_id":"DG-03B_REVISED"', rendered)

    def test_required_sections_and_authority_warning_render(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        for heading in ("현재 연구 단계", "전체 연구 시스템 지도", "실험·결과", "준비도·위험", "이력·근거"):
            self.assertIn(heading, rendered)
        self.assertIn(AUTHORITY_COMMIT, rendered)
        self.assertIn("과학 기준", rendered)

    def test_dashboard_uses_only_local_assets(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        self.assertIn('href="assets/rcc.css"', rendered)
        self.assertIn('src="assets/rcc.js"', rendered)
        self.assertNotIn("cdn.jsdelivr", rendered)
        self.assertNotIn("unpkg.com", rendered)

    def test_search_and_status_filter_controls_exist(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        self.assertIn('id="node-search"', rendered)
        self.assertIn('id="catalog-search"', rendered)
        self.assertIn('id="gap-priority"', rendered)
        script = (RCC_ROOT / "dashboard" / "assets" / "rcc.js").read_text(encoding="utf-8")
        self.assertIn("applyMapFilters", script)
        self.assertIn("applyCatalogFilters", script)
        self.assertIn('option>HIGH</option>', rendered)

    def test_gpt_brief_has_required_recovery_boundary_and_word_budget(self) -> None:
        brief = render_gpt_brief(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        self.assertIn("Chat memory must not override the scientific authority or RCC registry.", brief)
        self.assertIn("14 contiguous attack-event units", brief)
        self.assertIn("statistical independence is", brief)
        self.assertIn("Graph-Guided and Agentic remain provisional contribution labels.", brief)
        self.assertIn("## Research objective", brief)
        self.assertIn("## Claim boundaries", brief)
        self.assertIn("## How we got here", brief)
        self.assertIn("History cannot override current state", brief)
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
            for reference in ("result_ref", "trace_ref"):
                relative = load_registry(RCC_ROOT)["state"]["front_execution"][reference]
                destination = root.parent / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((RCC_ROOT.parent / relative).read_bytes())
            dashboard = build_dashboard(root)
            summaries = generate_summaries(root)
            self.assertTrue(dashboard.is_file())
            self.assertEqual(53, len(summaries))  # DEC-028 records the final pre-DG05 freeze.
            self.assertTrue(all(path.is_file() for path in summaries))
            self.assertTrue((root / "history" / "PROJECT_TIMELINE.md").is_file())
            self.assertTrue((root / "generated" / "RCC_003_HISTORY_SUMMARY.md").is_file())

    def test_dashboard_has_population_counts_and_architecture_nodes(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        for label in ("구현 완료", "실제 실행 완료", "근거 점검 완료", "독립 재현 완료"):
            self.assertIn(label, rendered)
        self.assertNotIn("Claim-ready", rendered)
        for component_id in ("DATA_PROVENANCE", "GDN_DISCOVERY", "D0_PCA_SPE", "D1_RULE_ONLY"):
            name = next(row["name"] for row in load_registry(RCC_ROOT)["components"] if row["component_id"] == component_id)
            self.assertIn(name, rendered)

    def test_arch000_dashboard_exposes_clickable_contracts(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        self.assertEqual(14, rendered.count('id="map-svg-NODE_'))
        for node_id in ("NODE_HAI_P1", "NODE_RULE_CONSTRUCTION", "NODE_D0", "NODE_D1", "NODE_D2", "NODE_OUTER_REPRO"):
            self.assertIn(f'data-node-id="{node_id}"', rendered)
        for label in ("Input", "Output", "코드", "실행", "근거", "무결성", "과학 검증"):
            self.assertIn(label, rendered)
        self.assertIn('id="detail-drawer"', rendered)

    def test_status_semantics_are_non_linear_and_claim_registry_authoritative(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        self.assertIn(
            "구현 완료, 실행 완료, 결과 무결성 확인, 과학적 검증, 재현성, 일반화는 서로 다른 상태입니다.",
            rendered,
        )
        self.assertIn("결과 무결성 확인은 과학적 검증이 아닙니다.", rendered)
        self.assertIn("claims.csv", rendered)
        self.assertNotIn("전체 연구 완료율", rendered)
        self.assertGreater(
            sum(row["audited"] == "true" for row in data["components"]),
            sum(row["executed"] == "true" for row in data["components"]),
        )

    def test_claim_headline_counts_derive_from_claims_registry(self) -> None:
        data = load_registry(RCC_ROOT)
        rendered = render_dashboard(data, registry_digest(RCC_ROOT))
        for row in data["claims"]:
            self.assertIn(row["claim_id"], rendered)
            self.assertIn(row["status"], rendered)

    def test_user_summary_and_context_preserve_pilot_boundaries(self) -> None:
        generated = generate_summaries(RCC_ROOT)
        self.assertEqual(53, len(generated))
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
        self.assertIn("연구 주요 단계", rendered)
        self.assertIn("History · Decision · Evidence", rendered)
        for event in data["timeline"][-10:]:
            self.assertIn(event["title"], rendered)

    def test_korean_first_ui_preserves_status_codes_and_pilot_numbers(self) -> None:
        rendered = render_dashboard(load_registry(RCC_ROOT), registry_digest(RCC_ROOT))
        self.assertIn('<html lang="ko">', rendered)
        self.assertIn(
            "구현 완료, 실행 완료, 결과 무결성 확인, 과학적 검증, 재현성, 일반화는 서로 다른 상태입니다.",
            rendered,
        )
        self.assertIn("test1의 14개 연속 공격 구간 단위(contiguous attack-event units)", rendered)
        for code, label in {
            "CODE_IMPLEMENTED": "구현 완료",
            "EXECUTED": "실제 실행 완료",
            "EVIDENCE_REVIEWED": "근거 점검 완료",
            "RESULT_INTEGRITY": "결과 무결성 확인",
            "REPRODUCED": "독립 재현 완료",
            "UNVALIDATED": "미검증",
            "PILOT_ONLY": "예비 실험 수준",
            "UNCONFIRMED": "미확인",
            "BLOCKED": "진행 전 해결 필요",
            "CONDITIONAL": "조건부",
        }.items():
            self.assertIn(label, STATUS_DISPLAY_LABELS[code])
        for identifier in ("D0", "D1", "D2", "META", "STAT", "GDN", "COMMON-42"):
            self.assertIn(identifier, rendered)
        for value in ("11/14", "13/14", "0.4939336325682589", "40.50255787059723"):
            self.assertIn(value, rendered)
        for old_heading in ("CURRENT STATE", "MY TASKS", "DECISION INBOX", "COMPONENT STATUS"):
            self.assertNotIn(f"<h2>{old_heading}</h2>", rendered)
        for label in (
            "Deterministic Verifier", "Metrics·Result Integrity", "실행 권한 (Runtime Authorization)",
            "근거 출처 추적 (Provenance)", "새 환경 독립 재현 (Fresh-machine Reproduction)",
        ):
            self.assertIn(label, rendered)
        for english_only in (
            ">Verifier</a>",
            ">Runtime·Trace</a>",
            ">Metric</a>",
            "<dt>AUTHORITY</dt>",
            "<dt>TRIGGER</dt>",
            "<dt>POLICY</dt>",
            "<dt>FIT</dt>",
            "<dt>RECALL</dt>",
            "<dt>FAR/HOUR</dt>",
            "42/42 proposal accepted",
            "39/42 accepted; 3 no_rule",
        ):
            self.assertNotIn(english_only, rendered)

        current_status = (RCC_ROOT / "generated" / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        my_todo = (RCC_ROOT / "MY_TODO.md").read_text(encoding="utf-8")
        decision_inbox = (RCC_ROOT / "DECISION_INBOX.md").read_text(encoding="utf-8")
        self.assertIn("| 구성요소 |", current_status)
        self.assertIn("| 실험 |", current_status)
        self.assertIn("**우선순위:** 높음 (HIGH)", my_todo)
        self.assertNotIn("현재 미결정 사용자 항목은 없다", decision_inbox)
        self.assertIn("DG-03B",decision_inbox)
        self.assertIn("USER_DECISION_REQUIRED",decision_inbox)
        self.assertNotIn("**필요한 이유:** The choice", decision_inbox)

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
