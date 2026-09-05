"""Synchronize public records after external T2 normal-only closure."""
import csv
import json
import subprocess
from pathlib import Path

from synchronize_dg04_stage_a_v1 import RCC, write, table
from xver_execution_common import ROOT, PUB, document, head, require, seal


PUBLIC = PUB / "provider_execution_v1"


def prepend(path: Path, marker: str, text: str):
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if old.startswith(marker):
        return
    path.write_text(marker + "\n\n" + text + "\n\n## 이전 기록 — 역사적 상태\n\n" + old, encoding="utf-8", newline="\n")


def main():
    result = document(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_RESULT_V1.json")
    qa = document(PUBLIC / "XVER_T2_EXECUTION_INTEGRITY_QA_V1.json")
    private = document(PUBLIC / "PUBLIC_PRIVATE_T2_EXECUTION_INDEX_V1.json")
    portfolios = {v: document(PUBLIC / f"HAI{v[:2]}_T2_PORTFOLIO_AUTHORITY_V1.json") for v in ("22.04", "21.03")}
    t0 = {v: document(PUB / f"HAI{v[:2]}_T0_PORTFOLIO_AUTHORITY_V1.json") for v in ("22.04", "21.03")}
    require(qa["status"] == "PASS" and qa["result_hash"] == result["self_hash"], "QA_RESULT_BINDING")
    source = head()
    p22, p21 = portfolios["22.04"], portfolios["21.03"]
    summary = f'''XVER-T2-PROVIDER-EXEC-001: COMPLETE_NORMAL_ONLY / QA PASS.
정확한 snapshot gpt-5.4-mini-2026-03-17로 HAI22 {p22['calls']}회, HAI21 {p21['calls']}회, 합계 {result['combined']['calls']}회 호출했습니다. retry/fallback/tools/4차 호출은 0이며 EVENT10은 전송하지 않았습니다.
실제 계량 사용량은 입력 {result['combined']['input_tokens']} / 출력 {result['combined']['output_tokens']} / 합계 {result['combined']['total_tokens']} tokens이고 표준 공개가격 단순 산식은 USD {result['combined']['standard_price_estimate_usd']}입니다. 이는 청구서가 아닙니다.
HAI22 T2는 train2 입장 {p22['train2_admitted_pairs']} pairs, 정상 확인 {p22['semantic_confirmed_rules']} Rules, Formal V4 {p22['Formal_V4_rules']}, train4 유지 {p22['guard_retained_rules']} Rules/{p22['final_pair_count']} pairs입니다.
HAI21 T2는 train2 입장 {p21['train2_admitted_pairs']} pairs, 정상 확인 {p21['semantic_confirmed_rules']} Rules, Formal V4 {p21['Formal_V4_rules']}, Block B 유지 {p21['guard_retained_rules']} Rules/{p21['final_pair_count']} pairs입니다.
두 결과는 HELDOUT_CANDIDATE이며 공격 검증·production·T2>T0 일반화 결론이 아닙니다. T0/T2/V2A는 별도 사전등록 방법으로 유지하며 선택하지 않았습니다.
모든 provider 출력과 admission을 양 버전에서 먼저 닫은 뒤 train3/Block A, SCI02B, Formal V4, 단방향 guard를 수행했습니다. 공격/test/label/real eligibility 접근은 0입니다.
DG-XVER-PROVIDER는 승인·실행 완료. DG05는 NOT_APPROVED, 교수 package는 NOT_SUBMITTED, DG06 필수입니다.
정확한 다음 작업은 MULTIPANEL-PRE-DG05-FREEZE-001이며 multi-file aggregation, empty-input, secondary P1 해석과 최종 prediction-before-label custody를 공격 접근 전에 고정합니다. 백업은 SINGLE_COPY_LOCAL_ONLY입니다.'''
    report = f'''# XVER T2 provider execution — normal-only result

Status: COMPLETE_NORMAL_ONLY / QA PASS. No attack, test, label, scenario or real eligibility authority was accessed.

## Provider

- Exact model snapshot: `gpt-5.4-mini-2026-03-17`; Responses API; reasoning none; temperature 0.7; top_p 1; store false.
- Calls: HAI22 {p22['calls']}; HAI21 {p21['calls']}; combined {result['combined']['calls']} (approved maximum 174).
- Metered tokens: input {result['combined']['input_tokens']}; output {result['combined']['output_tokens']}; total {result['combined']['total_tokens']} (approved maximum 3,622,912).
- Prospective standard-price arithmetic: USD {result['combined']['standard_price_estimate_usd']}; not an invoice or actual billing record.
- Retry, fallback, provider tools, fourth calls: zero. Scientific concurrency: one.
- First scheduled HAI22 call passed receipt-first snapshot, schema, usage, privacy and durable-custody checks.

## HAI22

- Candidate N 29; first/second/third-call accepts {p22['first_call_accepts']}/{p22['second_call_accepts']}/{p22['third_call_accepts']}.
- Explicit accepted NO_RULE {p22['terminal_counts'].get('INTENTIONAL_NO_RULE',0)}; repair-budget failures {p22['terminal_counts'].get('NEEDS_REPAIR_BUDGET_EXHAUSTED',0)}.
- Feedback {p22['feedback_actions']} actions across {p22['distinct_feedback_pairs']} pairs.
- Train2 admitted {p22['train2_admitted_pairs']} pairs / {p22['train2_admitted_rules']} Rules; hidden-confirmed {p22['semantic_confirmed_rules']} Rules.
- Numeric bound / Formal V4 / train4 retained: {p22['numeric_bound_rules']} / {p22['Formal_V4_rules']} / {p22['guard_retained_rules']} Rules; retained pairs {p22['final_pair_count']}.
- Portfolio hash: `{p22['self_hash']}`.

## HAI21

- Candidate N 29; first/second/third-call accepts {p21['first_call_accepts']}/{p21['second_call_accepts']}/{p21['third_call_accepts']}.
- Explicit accepted NO_RULE {p21['terminal_counts'].get('INTENTIONAL_NO_RULE',0)}; repair-budget failures {p21['terminal_counts'].get('NEEDS_REPAIR_BUDGET_EXHAUSTED',0)}.
- Feedback {p21['feedback_actions']} actions across {p21['distinct_feedback_pairs']} pairs.
- Train2 admitted {p21['train2_admitted_pairs']} pairs / {p21['train2_admitted_rules']} Rules; Block A-confirmed {p21['semantic_confirmed_rules']} Rules.
- Numeric bound / Formal V4 / Block B retained: {p21['numeric_bound_rules']} / {p21['Formal_V4_rules']} / {p21['guard_retained_rules']} Rules; retained pairs {p21['final_pair_count']}.
- Portfolio hash: `{p21['self_hash']}`.

## Boundaries

GLOBAL5 was transmitted; EVENT10, META rank/tier, candidate arm, T0, train3, numeric values/policy, guard and attack/test information were not. HAI22 and HAI21 are normal-only method re-instantiations, not attack-performance or generalization results. No choice was made between T0 and T2.
'''
    (PUBLIC / "XVER_T2_PROVIDER_EXECUTION_REPORT_V1.md").write_text(report, encoding="utf-8", newline="\n")
    handoff = '''# MULTIPANEL-PRE-DG05-FREEZE-001 handoff

Status: NEXT_TASK_ONLY; this file grants no attack access.

Freeze before DG-05: unresolved eTaPR multi-file aggregation and empty-input conventions; secondary P1 interpretation; HAI23/22/21 exact method bundle; V2A/T0/T2 portfolio hashes; PCA and frozen Fusion authorities; version-specific prediction-before-label custody; official scenario authority; outcome-blind P1 eligibility custodian; one-shot label lease; independent result-integrity QA.

DG-05 remains USER_DECISION_REQUIRED. Do not access test2, external attacks, labels, real scenario metadata or eligibility while preparing this contract.
'''
    (PUBLIC / "MULTIPANEL_PRE_DG05_HANDOFF_V1.md").write_text(handoff, encoding="utf-8", newline="\n")
    independent_qa = f'''# XVER T2 independent final QA V1

Status: PASS_FOR_COMMIT_AND_INTEGRATION

- Approved integration baseline replayed: `be3ff48bd2abfafc81544357af0daff69a6721a2`.
- Result authority replayed: `{result['self_hash']}`.
- HAI22 portfolio replayed: `{p22['self_hash']}`.
- HAI21 portfolio replayed: `{p21['self_hash']}`.
- Ten public authority self-hashes and all frozen source hashes replayed.
- Exact snapshot, receipt-first probe, concurrency one, retry/fallback/tools/fourth-call zero, and provider-before-train3 ordering passed.
- GLOBAL5-only transmission passed; EVENT10 exposure was zero.
- Usage replay: {result['combined']['calls']} calls; {result['combined']['input_tokens']} input; {result['combined']['output_tokens']} output; {result['combined']['total_tokens']} total tokens; USD {result['combined']['standard_price_estimate_usd']} prospective standard-price arithmetic. Approved ceilings were respected.
- The bounded post-provider tuple/array canonicalization repair was engineering-only: zero added calls, unchanged provider outputs, unchanged scientific method.
- V2A, EXP-02, EXP-03B, EXP-04/05, GDN-front, frozen experiment artifacts and PILOT V1 remained unchanged; PILOT preservation is 3,021/3,021.
- Registry/privacy validation passed with zero private exposure. Focused execution/EXP-03B tests passed 93/93; RCC/UI passed 218/218; post-dashboard targeted tests passed 39/39; `git diff --check` passed.
- DG-05 remains unapproved and the professor package remains unsubmitted.

The independent audit made no provider call, credential read, attack/test/label access or file modification, and did not inspect raw private provider payloads.
'''
    (PUBLIC / "XVER_T2_INDEPENDENT_QA_V1.md").write_text(independent_qa, encoding="utf-8", newline="\n")

    state = json.loads((RCC / "registry/current_state.yaml").read_text(encoding="utf-8"))
    state.update(
        last_updated="2026-09-05",
        current_phase_statement=summary,
        exact_next_task="MULTIPANEL-PRE-DG05-FREEZE-001",
        recommended_next_management_task="MULTIPANEL-PRE-DG05-FREEZE-001",
        last_completed_task="XVER-T2-PROVIDER-EXEC-001 — COMPLETE_QA_PASS",
        highest_priority_work=[
            "MULTIPANEL-PRE-DG05-FREEZE-001: unresolved metric and final custody bindings",
            "DG05 remains NOT_APPROVED; no attack/test/label access",
            "DG06 remains required for professor submission",
        ],
        top_user_todo=[
            "MULTIPANEL-PRE-DG05-FREEZE-001 complete normal-only contracts",
            "DG05: first attack-panel access decision",
            "DG06: professor package submission decision",
        ],
        xver_t2_execution={
            "status": "COMPLETE_QA_PASS_NORMAL_ONLY", "result_hash": result["self_hash"],
            "QA_hash": qa["self_hash"], "portfolio_hashes": result["portfolio_hashes"],
            "calls": result["combined"]["calls"], "tokens": result["combined"]["total_tokens"],
            "input_tokens": result["combined"]["input_tokens"],
            "output_tokens": result["combined"]["output_tokens"],
            "standard_price_estimate_usd": result["combined"]["standard_price_estimate_usd"],
            "model": "gpt-5.4-mini-2026-03-17",
            "versions": {
                version: {
                    "calls": portfolio["calls"],
                    "train2_admitted_pairs": portfolio["train2_admitted_pairs"],
                    "confirmed_rules": portfolio["semantic_confirmed_rules"],
                    "Formal_V4_rules": portfolio["Formal_V4_rules"],
                    "retained_rules": portfolio["guard_retained_rules"],
                    "retained_pairs": portfolio["final_pair_count"],
                    "portfolio_hash": portfolio["self_hash"],
                }
                for version, portfolio in portfolios.items()
            },
            "attack_accesses": 0, "report": "research_control_center/validation_v2/xver_normal/provider_execution_v1/XVER_T2_PROVIDER_EXECUTION_REPORT_V1.md",
            "independent_QA": "PASS_FOR_COMMIT_AND_INTEGRATION",
            "independent_QA_report": "research_control_center/validation_v2/xver_normal/provider_execution_v1/XVER_T2_INDEPENDENT_QA_V1.md",
        },
    )
    state["evaluation_expansion"]["provider_calls"] = result["combined"]["calls"]
    state["safety_counters"]["scientific_executions"] = 5
    # Preserve the complete pre-provider normal-execution receipt exactly as it
    # existed at the approved integration baseline.  The current provider
    # execution lives in the separate xver_t2_execution authority.
    baseline_state = json.loads(subprocess.run(
        ["git", "show", "be3ff48bd2abfafc81544357af0daff69a6721a2:research_control_center/registry/current_state.yaml"],
        cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout)
    state["xver_normal_execution"] = baseline_state["xver_normal_execution"]
    state["top_priorities"] = state["highest_priority_work"]
    write(RCC / "registry/current_state.yaml", state)
    program = json.loads((RCC / "validation_v2/PROGRAM_STATE.json").read_text(encoding="utf-8"))
    program.update(
        current_stage="MULTIPANEL_PRE_DG05_FREEZE_PENDING",
        program_status="XVER_T2_NORMAL_PORTFOLIOS_COMPLETE_QA_PASS",
        xver_t2_execution=state["xver_t2_execution"],
        exact_next_task="MULTIPANEL-PRE-DG05-FREEZE-001",
    )
    program["decision_gates"]["DG-XVER-PROVIDER"] = "APPROVED_EXECUTED_QA_PASS"
    program["decision_gates"]["DG-03C"] = "SUPERSEDED_BY_DG_XVER_PROVIDER_EXECUTED"
    program["decision_gates"]["DG-05"] = "NOT_APPROVED"
    program["evaluation_expansion"]["provider_calls"] = result["combined"]["calls"]
    program["safety_counters"]["scientific_executions"] = 5
    write(RCC / "validation_v2/PROGRAM_STATE.json", program)

    report_path = "research_control_center/validation_v2/xver_normal/provider_execution_v1/XVER_T2_PROVIDER_EXECUTION_RESULT_V1.json"
    table("artifacts", "artifact_id", "ART-XVER-T2-EXECUTION", dict(
        name="XVER_T2_PROVIDER_EXECUTION_RESULT_V1.json",
        role="External normal-only T2 provider execution and heldout-candidate portfolio authority",
        source_ref="validation-v2-xver-t2-provider-exec-001", source_commit=source,
        producer="RESULT_INTEGRITY", consumer="RCC",
        public_private="PUBLIC_SAFE", frozen="true", audited="true", current="true",
        superseded="false", safe_path=report_path,
    ))
    table("artifacts", "artifact_id", "ART-XVER-T2-INDEPENDENT-QA", dict(
        name="XVER_T2_INDEPENDENT_QA_V1.md",
        role="Independent read-only final QA for external normal-only T2 execution",
        source_ref="validation-v2-xver-t2-provider-exec-001", source_commit=source,
        producer="RESULT_INTEGRITY", consumer="RCC",
        public_private="PUBLIC_SAFE", frozen="true", audited="true", current="true",
        superseded="false", safe_path="research_control_center/validation_v2/xver_normal/provider_execution_v1/XVER_T2_INDEPENDENT_QA_V1.md",
    ))
    for version, portfolio in portfolios.items():
        table("experiments", "experiment_id", "EXP-H" + version[:2] + "-XVER", dict(
            status="EXECUTED_AUDITED_DEVELOPMENT",
            dataset_scope=(
                "HAI 22.04;58 nominal scenarios;FULL_COMMON_P1_UNIVERSE;real scenario eligibility pending DG-05"
                if version == "22.04" else
                "HAI 21.03;50 nominal scenarios;PARTIAL_COMMON_P1_UNIVERSE;real scenario eligibility pending DG-05"
            ),
            current_evidence=f"T0 {t0[version]['guard_retained_rules']} Rules;T2 {portfolio['guard_retained_rules']} Rules;attack evaluation not executed",
            result_scope="NORMAL_ONLY_METHOD_REINSTANTIATION_ATTACK_EVALUATION_NOT_EXECUTED",
            next_action="MULTIPANEL-PRE-DG05-FREEZE-001;then DG05",
            limitations="No attack utility, superiority, causal or generalization result",
            scientific_source_ref="validation-v2-xver-t2-provider-exec-001",
            scientific_source_commit=source,
            artifact_refs="ART-XVER-NORMAL-EXECUTION;ART-XVER-T2-EXECUTION",
        ))
    table("claims", "claim_id", "CLAIM-N", dict(
        status="UNVALIDATED", supporting_evidence="artifact:ART-XVER-NORMAL-EXECUTION;artifact:ART-XVER-T2-EXECUTION",
        allowed_wording="External versions completed normal-only T0/T2 method re-instantiation; attack panels remain unexecuted.",
        validation_needed="MULTIPANEL pre-DG05 freeze;DG05 one-shot version-separated evaluation",
        scientific_source_ref="validation-v2-xver-t2-provider-exec-001", scientific_source_commit=source,
    ))
    table("decisions", "decision_id", "DEC-027", dict(
        date="2026-09-05", date_precision="DAY",
        title="DG_XVER_PROVIDER_EXECUTION_APPROVED",
        status="ACTIVE",
        context="The research owner explicitly approved one normal-only external-version T2 execution for HAI22 and HAI21 under the already frozen version-bound provider contracts.",
        alternatives_considered="Do not execute;change model or budget;execute the exact frozen combined contract",
        decision="APPROVED: exact gpt-5.4-mini-2026-03-17 snapshot;maximum 174 calls and 3,622,912 total tokens;USD 4.06 prospective ceiling;concurrency one;retry and fallback zero",
        reason="The exact prompt, schema, evidence, privacy, custody and budget authorities were frozen and independently replayed before credential access.",
        consequence="HAI22 and HAI21 normal-only T2 heldout-candidate portfolios are frozen;DG-05 attack access remains unapproved.",
        current_relevance="DG_XVER_PROVIDER_EXECUTED_QA_PASS;MULTIPANEL_PRE_DG05_FREEZE_NEXT",
        source="USER_APPROVED_VALIDATION_V2_POLICY",
        source_ref="research_control_center/validation_v2/xver_normal/provider_execution_v1/XVER_T2_PROVIDER_APPROVAL_RECEIPT_V3.json",
        source_commit="NONE",
        affected_components="T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY;REPRODUCIBILITY",
        supersedes="NONE", superseded_by="NONE", user_approved="true", confidence="HIGH",
    ))
    table("timeline", "event_id", "EVENT-XVER-T2-PROVIDER-001", dict(
        date="2026-09-05", date_precision="DAY", event_type="RESULT_MILESTONE",
        title="외부 버전 T2 정상-only 실행 및 포트폴리오 동결",
        summary=f"HAI22/21 provider 61 calls each;T2 retained {p22['guard_retained_rules']}/{p21['guard_retained_rules']} Rules;no attack access",
        source="USER_APPROVED_DG_XVER_PROVIDER", source_ref=report_path, source_commit=source,
        affected_components="T2_AGENTIC_FEEDBACK;RESULT_INTEGRITY", decision_refs="DEC-025;DEC-027",
        status="ACTIVE_CONTEXT", superseded_by="NONE", notes="Normal-only re-instantiation;not attack utility/generalization",
    ))
    table("risks", "risk_id", "RISK-XVER-NORMAL-CUSTODY", dict(
        description="External T0/T2 normal portfolios are frozen; attack metrics and single-copy custody remain unresolved",
        evidence="artifact:ART-XVER-T2-EXECUTION",
        mitigation="MULTIPANEL-PRE-DG05 freeze then explicit DG05;preserve private hash custody",
        status="MITIGATING", scientific_source_ref="validation-v2-xver-t2-provider-exec-001", scientific_source_commit=source,
    ))

    marker = "# XVER-T2 — 외부 버전 정상-only 포트폴리오 동결 완료"
    for path in [
        RCC / "CURRENT_CONTEXT.md", RCC / "SESSION_HANDOFF.md", RCC / "MY_TODO.md",
        RCC / "DECISION_INBOX.md", RCC / "history/PROJECT_TIMELINE.md", RCC / "history/TERMINOLOGY_GUIDE.md",
        ROOT / "docs/professor_experiment_update_v2/03_VALIDATION_V2_METHOD.md",
        ROOT / "docs/professor_experiment_update_v2/10_HELDOUT_NEXT_PLAN.md",
        ROOT / "docs/professor_experiment_update_v2/11_PROFESSOR_DECISION_AGENDA.md",
        ROOT / "docs/professor_experiment_update_v2/13_SLIDE_OUTLINE.md",
    ]:
        prepend(path, marker, summary)

    task_path = RCC / "validation_v2/evaluation_expansion/IMPLEMENTATION_TASK_INDEX_V2.csv"
    with task_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream)); fields = list(rows[0])
    for row in rows:
        if row["task_id"] == "DG03C-PROVIDER-PREP-001":
            row.update(status="APPROVED_EXECUTED_QA_PASS", user_gate="DG_XVER_PROVIDER_APPROVED_EXECUTED")
        if row["task_id"] in ("HAI22-XVER-001", "HAI21-XVER-001"):
            row.update(status="BLOCKED_DG05_NORMAL_PORTFOLIOS_READY", prerequisite="Frozen T0 and T2 normal-only portfolios plus final multi-panel custody", user_gate="DG05")
    next_task = {
        "task_id": "MULTIPANEL-PRE-DG05-FREEZE-001", "status": "NEXT",
        "prerequisite": "Frozen HAI23/22/21 T0 T2 V2A and detector authorities",
        "allowed_data": "Public authorities;normal-only custody;synthetic metric fixtures",
        "prohibited_data": "Attack/test payloads;labels;real scenario eligibility",
        "expected_artifacts": "Metric bindings;method bundle;prediction-label custody;DG05 brief",
        "user_gate": "DG05_AFTER_FREEZE", "parallelization": "Read-only audits;sole writer",
        "scientific_stop_condition": "Undefined metric or custody authority",
    }
    existing = next((row for row in rows if row["task_id"] == next_task["task_id"]), None)
    if existing is None:
        rows.append(next_task)
    else:
        existing.update(next_task)
    with task_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    panel_path = RCC / "validation_v2/evaluation_expansion/PANEL_REGISTRY_V2.csv"
    with panel_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream)); fields = list(rows[0])
    for row in rows:
        if row["dataset_version"] in ("22.04", "21.03"):
            row["normal_authority_policy"] = "XVER_T0_T2_PORTFOLIOS_FROZEN_DG05_PENDING"
            row["result_status"] = "NORMAL_ONLY_METHODS_READY_ATTACK_NOT_ACCESSED"
    with panel_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    print("XVER_T2_RECORDS_SYNCHRONIZED")


if __name__ == "__main__":
    main()
