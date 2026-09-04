"""Publish aggregate EXP03 reports only after completed independent QA.

No provider, private numeric, dataset, or scientific execution entrypoint.
"""
from __future__ import annotations
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RCC = ROOT / "research_control_center"
EXP = RCC / "validation_v2/exp03/execution_v1"
REF = "validation-v2-exp03-provider-exec-001"
SOURCE = "9e0c669d5efa03afcd13342fa1fc3dbc8ba8f3f4"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def json_write(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def table(name):
    path = RCC / "registry" / (name + ".csv")
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return path, reader.fieldnames, list(reader)


def save_table(path, headers, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write(path, stream.getvalue())


def main():
    from paperworks.validation_v2.exp03_live_contract_v1 import h
    result = read(EXP / "EXP03_NATURAL_RESULTS_V1.json")
    qa = read(EXP / "INDEPENDENT_RESULT_QA_V1.json")
    for document in (result, qa):
        assert document["self_hash"] == h({k: v for k, v in document.items() if k != "self_hash"})
    assert qa["status"] == "PASS" and qa["results_hash"] == result["self_hash"]
    assert qa["pilot_blobs_unchanged"] == 3021 and qa["frozen_execution_bindings_unchanged"] == 55
    assert qa["synthetic_fixture_count"] == 390 and qa["test_data_accesses"] == 0
    arms = {row["arm"]: row for row in result["arm_metrics"]}
    t2 = arms["T2"]
    # Reporting does not decide final contribution wording at DG-04.
    repair = (f"{t2['feedback_repair_success']}/{t2['feedback_repair_denominator']}" if t2['feedback_repair_denominator'] else "NOT_OBSERVED (denominator=0)")
    feedback = f"T2 feedback {t2['feedback_activated']}/{t2['scheduled']}; repair {repair}"
    limitation = ("자연 cohort에서 feedback이 발생하지 않아 Agentic feedback 이점을 관찰하지 못했다."
                  if t2["feedback_activated"] == 0 else
                  "feedback의 빈도와 성공을 관찰했지만 최종 기여 표현은 DG-04에서 비교 근거와 한계를 함께 검토해야 한다.")
    summary = "; ".join(f"{arm} {r['accepted']}/{r['scheduled']}" for arm, r in arms.items())
    next_task = "DG-04 — 최종 제목·Agentic 기여 표현 결정"
    report = "# EXP-03 고정 snapshot 규칙 구성 비교 결과\n\n"
    report += f"상태: COMPLETE_QA_PASS. 모델: `{result['model_snapshot']}`.\n\n"
    report += "| arm | 승인/예정 | 생성 호출 | feedback |\n|---|---:|---:|---:|\n"
    for arm, row in arms.items():
        report += f"| {arm} | {row['accepted']}/{row['scheduled']} | {row['calls']} | {row['feedback_activated']} |\n"
    report += f"\n{feedback}. {limitation}\n\n"
    report += "## 반복 및 실패 분류\n\n| arm | 반복 1 승인 | 반복 2 승인 | 반복 3 승인 |\n|---|---:|---:|---:|\n"
    for arm in ("T1", "T1-B", "T2"):
        report += "| " + arm + " | " + " | ".join(f"{r['accepted']}/{r['scheduled']}" for r in arms[arm]["by_repeat"]) + " |\n"
    report += "\n| arm | 최종 비승인 상태 |\n|---|---|\n"
    for arm, row in arms.items():
        nonaccepted = "; ".join(f"{k}: {v}" for k, v in row["terminal_counts"].items() if v and k != "ACCEPTED_PROPOSAL") or "없음"
        report += f"| {arm} | {nonaccepted} |\n"
    report += "\nPARSE_FAILURE는 고정된 strict envelope 검사 실패이며, 모두 JSON 문법 오류라는 뜻은 아니다. T1-B의 ALL_DRAWS_FAILED는 3개 원본 draw 실패를 보존한 terminal 요약이다. operational failure를 no_rule로 바꾸지 않았다.\n\n"
    report += (f"실제 호출 {result['actual_calls']}회; input {result['input_tokens']:,}, output {result['output_tokens']:,}, "
               f"total {result['total_tokens']:,} tokens. 표준요금 상한 계산 USD {result['standard_api_cost_upper_bound_usd']} "
               "(cache 할인 미반영, 청구서 확정액 아님). 상한 819회 / 5,031,936 tokens / USD10.07 이내.\n\n")
    report += ("## 해석 경계\n\n이미 확인된 39개 directional relation의 identity·방향·horizon·numeric reference를 "
               "고정된 Formal V4 표현으로 구성하는 제한된 과제다. 새 관계 발견이나 numeric 추론, 탐지 성능을 측정하지 않았다. "
               "동일 정답 reference가 입력에 있으므로 높은 승인율 자체는 LLM 또는 Agentic 필요성을 입증하지 않는다. "
               "T1-B는 항상 3회 독립 생성 후 최초 admissible 출력을 선택하며 T2는 ACCEPTED_PROPOSAL 직후 중단한다. "
               "세 반복은 같은 관계를 재사용하므로 독립 scientific sample 수로 합산하지 않는다. "
               "snapshot·temperature 0.7·top_p 1.0·reasoning none을 고정했지만 API 재호출의 byte-identical 출력을 보장하지 않는다. "
               "여기서 replay는 보관된 응답·판정의 무결성 재검증이다.\n\n"
               "synthetic stress 390 fixtures는 terminal/controller 계약 점검이며 provider 호출이 없는 별도 결과다. "
               "자연 cohort의 repair evidence와 합치지 않는다. no_rule appropriateness는 관찰된 계약 범위만 다루며 전문가 유용성을 뜻하지 않는다.\n\n"
               "## 보존과 다음 단계\n\nV2A 39-rule portfolio, EXP-02, EXP-04/05, detector/fusion, 향후 held-out 방법 집합은 변경하지 않았다. "
               "이번 task의 test1/test2/held-out/공격 label 접근은 0이다. PILOT V1 3,021개 보존 항목은 그대로다. "
               "DG-03은 고정 snapshot으로 승인·실행되었다. **DG-04에서 정지**하며 DG-05 공격 접근과 DG-06 제출은 승인되지 않았다.\n")
    write(EXP / "EXP03_RESULTS_REPORT_V1.md", report)
    write(ROOT / "docs/professor_experiment_update_v2/06_EXP03_AGENTIC_RESULTS.md", report)
    brief = ("# DG-04 — 최종 제목·기여 표현 결정안\n\n상태: USER_DECISION_REQUIRED. 자동 확정하지 않는다.\n\n"
             f"EXP-03: {summary}. {feedback}. {limitation}\n\n"
             "권고: GDN-Assisted는 LEARNED_GRAPH_SUPPORTING 범위의 비인과 보조 근거로 설명한다. "
             "Agentic feedback의 우월성이 입증되지 않은 경우 제목의 기여 주장에서는 제외하고 bounded feedback capability로 제한한다. "
             "META는 HYBRID_REVIEWED_METADATA이며 완전 자동 graph discovery라고 표현하지 않는다. "
             "두 fusion의 DEVELOPMENT_NOT_SUPPORTED 결과는 음성 비교 결과로 보존한다.\n\n"
             "필요한 결정: 최종 제목, Agentic 기여 포함 여부, construction-arm 표현, fusion의 음성 비교 위치. "
             "이 결정은 탐지 방법·portfolio·이미 소비된 test1 결과를 바꾸지 않는다. "
             "어떤 선택도 DG-05의 신규 공격 데이터 접근이나 DG-06 제출을 자동 승인하지 않는다.\n")
    write(EXP / "DG04_CONTRIBUTION_DECISION_BRIEF_V1.md", brief)
    state_path = RCC / "registry/current_state.yaml"
    state = read(state_path)
    state["current_phase_statement"] = f"EXP-03 고정 snapshot 비교와 독립 QA 완료. {limitation} V2 개발 결과는 보존하며 DG-04에서 제목·기여 표현 결정을 기다린다."
    state["exact_next_task"] = state["recommended_next_management_task"] = next_task
    state["last_completed_task"] = "EXP03-PROVIDER-EXEC-001 — 고정 snapshot 실행·독립 QA 완료"
    state["exp03_execution"] = {"status": "COMPLETE_QA_PASS", "model_snapshot": result["model_snapshot"],
        "calls": result["actual_calls"], "total_tokens": result["total_tokens"],
        "cost_upper_bound_usd": result["standard_api_cost_upper_bound_usd"], "arm_metrics": result["arm_metrics"],
        "results_hash": result["self_hash"], "qa_hash": qa["self_hash"], "next_gate": "DG-04",
        "scope": "REFERENCE_BOUND_CONSTRUCTION_NOT_DETECTION_OR_DISCOVERY"}
    program_view = state["validation_v2_program"]
    program_view["provider_gate"] = "DG-03 APPROVED_WITH_FIXED_SNAPSHOT; EXP-03 COMPLETE_QA_PASS; DG-04 pending."
    program_view["provider_calls"] = result["actual_calls"]
    program_view["exp03_status"] = "COMPLETE_QA_PASS"
    program_view["blocked_scope"] = "최종 제목·기여 DG-04; attack/heldout DG-05; 실제 제출 DG-06"
    for key, value in state.items():
        if isinstance(value, dict) and "experiment_gates" in value:
            value["experiment_gates"]["EXP-03"] = "COMPLETE"
    first = f"{next_task}: {limitation}"
    for key in ("top_priorities", "highest_priority_work", "top_user_todo"):
        state[key][0] = first
    for row in state["user_todo_items"]:
        if row["id"] == "USER-V2-003":
            row.update(status="COMPLETED", task="DG-03 고정 snapshot 승인·EXP-03 실행 완료", why=summary,
                       linked="research_control_center/validation_v2/exp03/execution_v1/EXP03_RESULTS_REPORT_V1.md")
        if row["id"] == "USER-V2-004":
            row.update(task=next_task, why=limitation, linked="research_control_center/validation_v2/exp03/execution_v1/DG04_CONTRIBUTION_DECISION_BRIEF_V1.md")
    json_write(state_path, state)
    program_path = RCC / "validation_v2/PROGRAM_STATE.json"
    program = read(program_path)
    program["decision_gates"]["DG-03"] = "APPROVED_WITH_FIXED_SNAPSHOT_EXECUTED_QA_PASS"
    program["decision_gates"]["DG-04"] = "USER_DECISION_REQUIRED"
    program["experiment_status"]["EXP-03"] = "COMPLETE_QA_PASS_REFERENCE_BOUND_CONSTRUCTION"
    program["exp03_execution"] = state["exp03_execution"]
    program["current_stage"] = "DG04_CONTRIBUTION_FRAMING"
    program["exact_next_task"] = next_task
    program["stage3_execution_readiness"]["next"] = next_task
    json_write(program_path, program)
    path, headers, rows = table("experiments")
    for row in rows:
        if row["experiment_id"] == "EXP-03":
            row.update(status="EXECUTED_AUDITED_DEVELOPMENT", dataset_scope="Frozen V2A 39 directional relations; redacted normal identity projection only",
                current_evidence=summary + "; " + feedback, result_scope="Reference-bound construction only; no dataset or detection evaluation",
                limitations=limitation + " Fixed confirmed inputs; synthetic stress is not natural repair evidence.", next_action=next_task,
                claim_impact="Bounded construction executed; Agentic superiority not established; DG-04 required",
                scientific_source_ref=REF, scientific_source_commit=SOURCE,
                artifact_refs="ART-EXP03-LIVE-RESULT;ART-CONSTRUCTION-ANALYSIS")
    save_table(path, headers, rows)
    path, headers, rows = table("artifacts")
    rows = [r for r in rows if r["artifact_id"] != "ART-EXP03-LIVE-RESULT"]
    rows.append(dict(zip(headers, ["ART-EXP03-LIVE-RESULT", "EXP-03 고정 snapshot 비교", "Public aggregate construction results", REF, SOURCE,
        "T2_AGENTIC_FEEDBACK", "RESULT_INTEGRITY", "PUBLIC_SAFE", "true", "true", "true", "false",
        "research_control_center/validation_v2/exp03/execution_v1/EXP03_NATURAL_RESULTS_V1.json"])))
    save_table(path, headers, rows)
    path, headers, rows = table("claims")
    for row in rows:
        if row["claim_id"] == "CLAIM-F":
            row.update(contradicting_evidence="experiment:EXP-03;artifact:ART-EXP03-LIVE-RESULT",
                allowed_wording="PILOT V1의 feedback 미관찰 결론은 그대로 보존한다. VALIDATION V2: " + limitation,
                validation_needed="DG-04 final contribution framing; do not infer benefit from synthetic fixtures or equal acceptance.",
                scientific_source_ref=REF, scientific_source_commit=SOURCE)
    save_table(path, headers, rows)
    path, headers, rows = table("decisions")
    prior = next((r for r in rows if r["decision_id"] == "DEC-023"), None)
    assert prior is None or prior["title"] == "DG03_FIXED_SNAPSHOT_PROVIDER_EXECUTION_APPROVED"
    rows = [r for r in rows if r["decision_id"] != "DEC-023"]
    row = {k: "NONE" for k in headers}
    row.update(decision_id="DEC-023", date="2026-09-04", date_precision="DAY", title="DG03_FIXED_SNAPSHOT_PROVIDER_EXECUTION_APPROVED", status="ACTIVE",
        context="Explicit research owner approval", alternatives_considered="Moving alias and fallback prohibited",
        decision="OpenAI gpt-5.4-mini-2026-03-17;819 calls;5031936 tokens;USD10.07;concurrency1",
        reason="Exact reproducible snapshot and bounded privacy-safe execution", consequence="EXP-03 only; immutable portfolio and detection results",
        current_relevance="Execution completed; DG-04 mandatory", source="USER_APPROVED_VALIDATION_V2_POLICY",
        source_ref="research_control_center/validation_v2/exp03/DG03_FIXED_SNAPSHOT_APPROVAL_V1.json",
        affected_components="T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY", user_approved="true", confidence="HIGH")
    rows.append(row)
    save_table(path, headers, rows)
    path, headers, rows = table("timeline")
    prior = next((r for r in rows if r["event_id"] == "EVENT-033"), None)
    assert prior is None or prior["title"] == "EXP-03 고정 snapshot 비교·독립 QA 완료"
    rows = [r for r in rows if r["event_id"] != "EVENT-033"]
    row = {k: "NONE" for k in headers}
    row.update(event_id="EVENT-033", date="2026-09-04", date_precision="DAY", event_type="RESULT_MILESTONE",
        title="EXP-03 고정 snapshot 비교·독립 QA 완료", summary=summary + "; " + feedback,
        source="V2_DEVELOPMENT_RESULT", source_ref="research_control_center/validation_v2/exp03/execution_v1/",
        source_commit=SOURCE, affected_components="T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY", decision_refs="DEC-023",
        status="ACTIVE_CONTEXT", notes="No test/heldout/data reads; no portfolio change; DG-04 stop")
    rows.append(row)
    save_table(path, headers, rows)
    professor = ROOT / "docs/professor_experiment_update_v2"
    replacements = {
        "01_ONE_PAGE_SUMMARY.md": ("다음은 DG-03 provider 실행 예산/허가 검토입니다.", "DG-03 승인 아래 EXP-03 실행·QA가 완료됐으며 다음은 DG-04 기여 표현 결정입니다."),
        "09_CLAIM_AND_LIMITATION_MATRIX.md": ("미지원/EXP-03 gated", "EXP-03 실행·QA 완료; Agentic 우월성 미입증"),
        "11_PROFESSOR_DECISION_AGENDA.md": ("DG-03: EXP-03 provider/model/exact call·token budget 승인 전 호출 금지.", "DG-03 고정 snapshot 실행 완료. EXP-03 결과를 바탕으로 DG-04 제목·기여 표현 결정."),
    }
    for filename, (old, new) in replacements.items():
        path = professor / filename
        text = path.read_text(encoding="utf-8")
        assert old in text or new in text
        text = text.replace(old, new)
        if filename == "01_ONE_PAGE_SUMMARY.md":
            text = text.replace("test2/held-out과 provider 호출은 0입니다.", f"test2/held-out 접근은 0입니다. EXP-04/05 당시 provider 호출은 0이었고, 이후 별도 DG-03 승인 EXP-03에서 {result['actual_calls']}회 호출했습니다. EXP-03은 test1을 다시 열지 않았습니다.")
        write(path, text)
    print("EXP03_PUBLICATION_GENERATED_REQUIRES_RCC_REFRESH_AND_FINAL_QA")


if __name__ == "__main__":
    main()
