"""Scope historical claims separately from the completed EXP03B evidence."""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
RCC = ROOT / 'research_control_center'


def main():
    path = RCC / 'registry/current_state.yaml'
    state = json.loads(path.read_text(encoding='utf-8'))
    assert state['exp03b_execution']['status'] == 'COMPLETE_QA_PASS'
    state['recommended_next_architecture_task'] = 'DG-04 최종 제목·기여 결정; 추가 provider/Agentic rescue 실행 금지'
    for field in ('current_unvalidated', 'not_established'):
        state[field] = ['Agentic의 T0 대비 우월성·고정 cohort 밖 전이·held-out utility' if s == 'Agentic verifier-feedback advantage' else s for s in state[field]]
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    path = RCC / 'registry/claims.csv'
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f); columns = reader.fieldnames; rows = list(reader)
    old = next(r for r in rows if r['claim_id'] == 'CLAIM-F')
    old['claim_text'] = 'PILOT V1 / EXP-03 V1: Agentic verifier-feedback benefit was not observed.'
    old['allowed_wording'] = 'PILOT V1 및 EXP-03 V1 constrained materialization의 feedback 미관찰 결론은 그대로 보존. EXP-03B 의미적 induction 결과는 별도 authority로 보고한다.'
    old['forbidden_wording'] = 'EXP-03 V1에서 Agentic feedback으로 rule quality가 개선되었다.'
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    note = '현재 결과의 필수 한계: T0는 T2보다 strict pair/directional F1 및 exact set에서 높았습니다. T2의 abstain은 T1-B보다 높았고, 동결 train4 burden 기준은 lexicographic입니다. 따라서 T2 대 T1-B의 사전등록 이점이며 전체 방법 우월성이 아닙니다. [동결 결과](../../research_control_center/validation_v2/exp03b/execution_v2/EXP03B_RESULTS_REPORT_V1.md) · [DG-04 결정안](../../research_control_center/validation_v2/exp03b/execution_v2/DG04_EXP03B_DECISION_BRIEF_V1.md).\n\n'
    for name in ('06_EXP03_AGENTIC_RESULTS.md', '11_PROFESSOR_DECISION_AGENDA.md', '13_SLIDE_OUTLINE.md'):
        path = ROOT / 'docs/professor_experiment_update_v2' / name
        content = path.read_text(encoding='utf-8')
        if note not in content:
            heading, rest = content.split('\n\n', 1)
            path.write_text(heading + '\n\n' + note + rest, encoding='utf-8', newline='\n')
    print('HISTORICAL_SCOPE_AND_CURRENT_LIMITATIONS_SYNCHRONIZED')


if __name__ == '__main__': main()
