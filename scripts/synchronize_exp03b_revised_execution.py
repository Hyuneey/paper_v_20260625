"""Publish reviewed execution status without changing any scientific authority."""
from pathlib import Path
import csv
import json

from paperworks.validation_v2.exp03b_custody_v1 import replay
from paperworks.validation_v2.exp03b_contract_v1 import require

ROOT = Path(__file__).resolve().parents[1]
RCC = ROOT / 'research_control_center'
PUB = RCC / 'validation_v2/exp03b/execution_v2'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def table(name, key, identity, fields):
    path = RCC / 'registry' / (name + '.csv')
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f); columns = reader.fieldnames; rows = list(reader)
    row = next(r for r in rows if r[key] == identity); row.update(fields)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator='\n'); writer.writeheader(); writer.writerows(rows)


def prepend(path, text):
    marker = '# EXP03B-PROVIDER-EXEC-001 — 현재 실행 결과'
    previous = path.read_text(encoding='utf-8')
    require(not previous.startswith(marker), 'EXECUTION_REPORT_ALREADY_SYNCHRONIZED')
    path.write_text(marker + '\n\n' + text + '\n\n## 이전 준비·실행 기록 — 역사적 보존\n\n' + previous, encoding='utf-8', newline='\n')


def main():
    result = json.loads((PUB / 'EXP03B_REVISED_RESULTS_V1.json').read_text()); replay(result)
    qa = json.loads((PUB / 'EXP03B_EXECUTION_INDEPENDENT_QA_V1.json').read_text()); replay(qa)
    require(qa['status'] == 'PASS' and qa['result_hash'] == result['self_hash'], 'INDEPENDENT_QA_REQUIRED')
    source_commit = result['execution_source_commit']
    summary = {
        'status': 'COMPLETE_QA_PASS', 'classification': 'SEMANTIC_RELATIONAL_RULE_INDUCTION',
        'calls': result['usage_total']['calls'], 'model_snapshot': result['model'],
        'input_tokens': result['usage_total']['input_tokens'], 'output_tokens': result['usage_total']['output_tokens'],
        'total_tokens': result['usage_total']['total_tokens'],
        'cost_upper_bound_usd': result['usage_total']['standard_uncached_cost_upper_usd'],
        'disposition': result['disposition'], 'feedback_actions': result['feedback_actions'],
        'feedback_distinct_pairs': result['repair_distinct_pairs']['feedback_pairs'],
        'exact_repair_distinct_pairs': result['repair_distinct_pairs']['train3_confirmed_exact_repair_pairs'],
        'result_hash': result['self_hash'], 'qa_hash': qa['self_hash'], 'source_commit': source_commit,
        'next_gate': 'DG-04', 'numeric_provider_visible': False,
        'report': 'research_control_center/validation_v2/exp03b/execution_v2/EXP03B_RESULTS_REPORT_V1.md',
        'reports': result['reports'],
    }
    text = f"EXP-03B 의미적 Rule induction 실행·독립 QA 완료. 판정 `{result['disposition']}`. {summary['calls']} calls, {summary['total_tokens']:,} tokens, 표준 uncached 요금 기준 상한 USD {summary['cost_upper_bound_usd']} (청구서가 아닌 token-price 산식). Feedback {summary['feedback_actions']}회/{summary['feedback_distinct_pairs']} pair, train3-confirmed exact repair {summary['exact_repair_distinct_pairs']} pair. Numeric policy는 provider에 공개하지 않고 모든 output/admission/train3 freeze 뒤 SCI02B로 결속했습니다.\n\nDG-03B_REVISED는 사용자 승인 후 실행 완료했습니다. 다음은 DG-04 최종 제목·Agentic 기여 결정입니다. 정상 확인 reference에 대한 개발 비교이며 causal truth·held-out generalization을 입증하지 않습니다. EXP-03 V1·V2A39·EXP02·EXP04/05·GDN·PILOT는 보존. test1/test2/heldout/외부공격/공격 label 접근0. 교수님에게 제출하지 않았습니다."
    state = json.loads((RCC / 'registry/current_state.yaml').read_text(encoding='utf-8'))
    state['exp03b_execution'] = summary
    state['current_phase_statement'] = text
    state['last_completed_task'] = 'EXP03B-PROVIDER-EXEC-001 — 의미적 induction 실행·독립 QA 완료'
    state['exact_next_task'] = 'DG-04 — EXP-03B 이후 최종 제목·Agentic 기여 결정'
    state['recommended_next_management_task'] = state['exact_next_task']
    state['top_user_todo'] = ['DG-04: EXP-03B 결과 기반 제목·Agentic 기여 범위 결정', 'DG-05: 다중 HAI 공격 접근 별도 승인; 현재 접근 금지', 'DG-06: 교수님 package 실제 제출 전 검토']
    state['highest_priority_work'] = ['DG-04: EXP-03B의 T2 대 T1-B 이점과 T0 대비 한계를 구분해 기여 표현을 결정한다.', 'HAI 22.04/21.03 호환성은 별도 normal-only/public metadata 작업이며 공격 접근은 DG-05 전 금지한다.', 'DG-03B_REVISED는 승인 실행 완료; 추가 Agentic rescue·provider 호출·교수님 자동 제출 금지.']
    state['top_priorities'] = list(state['highest_priority_work'])
    todo = next(x for x in state['user_todo_items'] if x['id'] == 'USER-V2-004')
    todo.update(task='DG-04 — EXP-03B 이후 제목·Agentic 기여 결정', why='DG-03B_REVISED 승인 실행 완료. Frozen T2 대 T1-B 기준과 T0 비교 한계를 검토한다.', linked='research_control_center/validation_v2/exp03b/execution_v2/DG04_EXP03B_DECISION_BRIEF_V1.md', status='OPEN')
    write(RCC / 'registry/current_state.yaml', state)
    program = json.loads((RCC / 'validation_v2/PROGRAM_STATE.json').read_text(encoding='utf-8'))
    program.update(current_stage='EXP03B_COMPLETE_DG04_PENDING', program_status='COMPLETE_CURRENT_AUTHORIZED_WORK_DG04_PENDING', exp03b_execution=summary, exact_next_task=state['exact_next_task'])
    program['experiment_status']['EXP-03B'] = 'COMPLETE_QA_PASS'
    program['decision_gates']['DG-03B_REVISED'] = 'APPROVED_EXECUTED'
    program['decision_gates']['DG-04'] = 'USER_DECISION_REQUIRED'
    write(RCC / 'validation_v2/PROGRAM_STATE.json', program)
    source = {'scientific_source_ref': 'codex/exp03b-provider-exec-001', 'scientific_source_commit': source_commit}
    table('experiments', 'experiment_id', 'EXP-03B', dict(status='EXECUTED_AUDITED_DEVELOPMENT', current_evidence=f"{result['disposition']};정상 semantic induction;독립 QA PASS;test/attack0", result_scope='정상 확인 reference 기반 DEVELOPMENT_ONLY;T2 대 T1-B 사전등록 비교', limitations='T0가 T2보다 주요 의미 지표 우수;T2 abstain 증가;held-out 미확인;single-copy custody', claim_impact='DG-04에서 bounded Agentic 기여 표현 결정;전체 방법 우월성 주장 금지', next_action='DG-04', **source))
    table('claims', 'claim_id', 'CLAIM-EXP03B-PREP', dict(claim_text=f"EXP-03B 실행 판정 {result['disposition']};최종 기여 표현 DG-04 대기", status='DEVELOPMENT_SUPPORTED', allowed_wording='정상 확인 reference에서 T2 대 T1-B 사전등록 기준 충족;T0 대비 우월성 아님', forbidden_wording='모든 arm보다 우월;인과적 진실;held-out 일반화 입증', validation_needed='DG-04 최종 표현 결정;DG-05 이후 별도 held-out 평가', **source))
    table('risks', 'risk_id', 'RISK-EXP03B-FIREWALL', dict(mitigation='freeze/receipt replay 및 독립 QA PASS;최종 표현 DG-04;공격 접근 DG-05;추가 rescue 금지', **source))
    table('decisions', 'decision_id', 'DEC-024', dict(current_relevance='DG03B_REVISED_APPROVED_EXECUTED;DG04_USER_DECISION_REQUIRED', source_ref='research_control_center/validation_v2/exp03b/execution_v2/DG03B_REVISED_USER_APPROVAL_V1.json'))
    table('artifacts', 'artifact_id', 'ART-EXP03B-PREP', dict(name='EXP-03B 의미적 induction 실행 결과 및 QA', source_ref=source['scientific_source_ref'], source_commit=source_commit, safe_path='research_control_center/validation_v2/exp03b/execution_v2/EXP03B_REVISED_RESULTS_V1.json'))
    table('timeline', 'event_id', 'EVENT-034', dict(notes='원 준비 기록 보존. 이후 PAYLOAD-REDUCE 및 사용자 DG03B_REVISED 승인에 따라 semantic induction 실행·QA 완료. 최종 기여 DG-04 대기.'))
    prepend(RCC / 'SESSION_HANDOFF.md', text)
    for name in ('06_EXP03_AGENTIC_RESULTS.md', '11_PROFESSOR_DECISION_AGENDA.md', '13_SLIDE_OUTLINE.md'):
        prepend(ROOT / 'docs/professor_experiment_update_v2' / name, text)
    print(json.dumps({'status': 'EXECUTION_RECORDS_SYNCHRONIZED', 'next_gate': 'DG-04'}))


if __name__ == '__main__':
    main()
