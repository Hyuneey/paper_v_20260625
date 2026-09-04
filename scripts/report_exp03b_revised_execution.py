"""Public-safe post-execution projection; never calls a provider or reads raw data."""
from collections import Counter
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from statistics import median
import json
import subprocess

from paperworks.validation_v2.exp03b_contract_v1 import require, digest
from paperworks.validation_v2.exp03b_custody_v1 import replay, seal, publish

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'research_control_center/validation_v2/exp03b'
RUN = ROOT / 'artifacts/validation_v2/exp03b/private/provider_execution_v2'


def read(path):
    value = json.loads(path.read_text()); replay(value); return value


def metric(value):
    n, d = value['numerator'], value['denominator']
    return f'{n}/{d} ({n/d:.4f})' if d else 'UNDEFINED'


def write_report(result):
    rows = []
    for arm, item in result['reports'].items():
        s = item['strict']; c = item['raw_and_admitted_coverage']
        rows.append(f"| {arm} | {metric(s['precision'])} / {metric(s['recall'])} / {metric(s['F1'])} | {metric(s['directional_precision'])} / {metric(s['directional_recall'])} / {metric(s['directional_F1'])} | {s['semantic_exact_match_count']}/{result['N']} | {metric(item['exact_horizon_accuracy']['value'])} | {c['selected_raw_parsed']}/{c['observations']} | {c['admitted']}/{c['observations']} |")
    guard_rows = []
    for arm in ('T0', 'T1', 'T1-B', 'T2'):
        g = result['post_induction'][arm + '.R1']; c = g['portfolio_census']
        burden = ' / '.join(metric(v) if v is not None else 'UNDEFINED' for v in c['burden'])
        guard_rows.append(f"| {arm} Repeat 1 | {g['numeric_binding_count']}/{g['train3_confirmed_binding_eligible_count']} | {g['formal_conversion_count']}/{g['admitted_rule_count']} | {g['retained_rule_count']} | {burden} | {json.dumps(g['guard_states'], ensure_ascii=False)} |")
    costs = []
    for arm, c in result['usage_by_arm'].items():
        costs.append(f"| {arm} | {c['calls']} | {c['input_tokens']:,} | {c['output_tokens']:,} | {c['latency_sum_seconds']:.3f} / {c['latency_median_seconds']:.3f} | {c['standard_uncached_cost_upper_usd']} |")
    total = result['usage_total']; pairs = result['repair_distinct_pairs']; paired = result['paired_exact_match_table']
    text = f'''# EXP-03B 의미적 evidence-to-rule induction 실행 결과

판정: **{result['disposition']}**. 다음 사용자 결정은 **DG-04**입니다. 이 문서는 동결된 정상-only 개발 비교 결과이며, 인과적 진실·공격 탐지 성능·held-out 일반화를 입증하지 않습니다. 독립 QA 판정은 별도 `EXP03B_EXECUTION_INDEPENDENT_QA_V1.json`에 결속합니다.

## 고정 설계와 strict 결과

29-pair cohort, stochastic R=3. T0는 한 번만 실행하고 반복표에서는 동일 artifact를 참조했습니다. 반복은 독립 과학 표본이 아닙니다. Primary는 train2-admitted 출력의 semantic majority이며, 실패/no-majority는 고정 cohort 분모에서 오답으로 유지합니다. RAW parsed proposal과 admitted output은 다릅니다. Numeric policy는 provider에 공개하지 않았습니다.

| arm | strict pair P / R / F1 | directional P / R / F1 | exact semantic set | horizon accuracy | selected raw parse | admitted observations |
|---|---|---|---|---|---|---|
{chr(10).join(rows)}

Horizon accuracy는 frozen reference directional relation 분모입니다. Selected raw/admitted는 T0 29 또는 stochastic 87 observation 분모이고, majority valid-output coverage는 JSON의 `strict.valid_output_coverage`에 별도로 기록했습니다. T1-B 전체 draw parse 수와 실패 taxonomy도 JSON에 보존합니다. Conditional metrics는 disposition 판정에 사용하지 않습니다.

## Feedback와 paired 비교

- Initial NEEDS_REPAIR observations: {result['initial_needs_repair_observations']}
- Feedback actions: {result['feedback_actions']}; distinct pairs: {pairs['feedback_pairs']}
- Verifier repair success observations: {result['verifier_repair_success_observations']}; distinct pairs: {pairs['verifier_repair_pairs']}
- Train3-confirmed exact semantic repair distinct pairs: {pairs['train3_confirmed_exact_repair_pairs']}
- Pair-decision repair distinct pairs: {pairs['pair_decision_repair_pairs']}
- Paired semantic exact table: T2-only {paired.get('T2_only_exact', 0)}, T1-B-only {paired.get('T1B_only_exact', 0)}, both {paired.get('both_exact', 0)}, neither {paired.get('neither_exact', 0)}.
- Frozen limitation: {result['limitation']}

Train3 reference는 `FROZEN_NORMAL_CONFIRMED_RELATION_REFERENCE`입니다. 독립 held-out ground truth가 아닙니다. Formatting repair를 semantic exact repair로 바꾸지 않았습니다.

## Post-induction SCI02B / Formal V4 / train4

모든 provider outputs → train2 admissions → train3 semantic evaluation을 먼저 동결했습니다. 이후 고정 `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05`와 기존 train1/train2 수식·max pooling으로 결속했습니다. Train4는 one-way guard이며 provider 호출이나 proposal 변경으로 돌아가지 않았습니다.

| arm | numeric binding / confirmed eligible | Formal V4 / admitted Rules | retained Rules | false seconds/hour / false episodes/hour / abstain | guard states |
|---|---|---|---|---|---|
{chr(10).join(guard_rows)}

이 표는 사전 지정 Repeat 1이며 최선 반복 선택이 아닙니다. 나머지 반복도 JSON에 보존했습니다. Formal V4 conversion의 분모는 frozen evaluator와 동일하게 전체 admitted Rule 수이며, numeric binding 분모는 train3-confirmed eligible 수로 구분했습니다. Opportunity-relation coverage는 frozen aggregate가 보존하지 않아 `NOT_RETAINED_IN_FROZEN_AGGREGATE`입니다. PASS/FAIL/ABSTAIN·unique false seconds·episodes·normal exposure는 JSON portfolio census에 있습니다. Guard 후 빈 portfolio를 provider-proposed NO_RULE로 해석하지 않습니다. Production/held-out Agentic portfolio는 생성하지 않았습니다.

## 호출·token·latency·비용

고정 snapshot `{result['model']}`, Responses/default, concurrency1, retry0, T2 ACCEPTED early-stop, 최대3. 첫 과학 호출이 receipt-first probe였으며 추가 probe를 만들지 않았습니다.

| arm | calls | input | output | latency sum / median seconds | uncached standard USD upper |
|---|---|---|---|---|---|
{chr(10).join(costs)}

총 {total['calls']} calls, input {total['input_tokens']:,}, output {total['output_tokens']:,}, total {total['total_tokens']:,}. 표준 uncached 요금 산식 상한 USD {total['standard_uncached_cost_upper_usd']}; cached usage 반영 추정 USD {total['standard_cache_adjusted_estimate_usd']}. 청구서가 아닌 token-price estimate입니다. [공식 모델 요금](https://developers.openai.com/api/docs/models/gpt-5.4-mini)을 사용했습니다. 승인 hard cap 609 calls / 8,463,360 total tokens / USD11.03을 초과하지 않았습니다.

## 보존과 다음 결정

PILOT V1·EXP-03 V1·V2A39·EXP02·EXP04/05·GDN은 변경하지 않았습니다. Test1 재개봉, test2, held-out, 외부공격, 공격 labels, GDN retraining, post-result tuning, private exposure는 0입니다. Credential은 승인 후 frozen transport에서만 사용했고 값은 기록·공개하지 않았습니다.

DG-04에서 제목·Agentic 기여 범위·construction-arm 표현을 결정합니다. 추가 Agentic rescue는 자동 진행하지 않습니다. DG-05 공격 접근과 DG-06 실제 교수님 제출은 별도 승인입니다. 교수님에게 제출하지 않았습니다.

Result hash: `{result['self_hash']}`. Execution source commit: `{result['execution_source_commit']}`.
'''
    path = PUBLIC / 'execution_v2/EXP03B_RESULTS_REPORT_V1.md'
    require(not path.exists() or path.read_text(encoding='utf-8') == text, 'REPORT_ALREADY_FROZEN')
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    require(not (RUN / 'SINGLE_WRITER.lock').exists(), 'PROVIDER_WRITER_ACTIVE')
    outputs = read(RUN / 'ALL_ARM_OUTPUTS_FROZEN.json')
    admissions = read(RUN / 'evaluation/TRAIN2_ADMISSIONS_FROZEN.json')
    evaluation = read(RUN / 'evaluation/TRAIN3_EVALUATION_FROZEN.json')
    final = read(RUN / 'evaluation/FINAL_LOCAL_RESULTS.json')
    freeze = read(PUBLIC / 'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json')
    budget = read(PUBLIC / 'EXP03B_PROVIDER_BUDGET_V2.json')
    require(evaluation['output_bundle_hash'] == admissions['output_bundle_hash'] == outputs['self_hash'], 'OUTPUT_BINDING')
    require(evaluation['admissions_hash'] == admissions['self_hash'], 'ADMISSION_BINDING')
    require(final['next_gate'] == 'DG-04' and not final['production_portfolio_created'], 'FINAL_BOUNDARY')
    costs = {arm: {'calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'cached_input_tokens': 0, 'latencies': []} for arm in ('T1', 'T1-B', 'T2')}
    receipt_hashes = []
    for index in range(1, outputs['calls'] + 1):
        receipt = read(RUN / 'calls' / f'{index:04d}.receipt.json')
        response = read(RUN / 'calls' / f'{index:04d}.response.json')
        request = read(RUN / 'calls' / f'{index:04d}.request.json')
        require(receipt['response_hash'] == digest(response['response']), 'RESPONSE_BINDING')
        require(response['response']['model'] == budget['model'], 'SNAPSHOT_CHANGED')
        require(response['response'].get('service_tier') == 'default', 'SERVICE_TIER_CHANGED')
        usage = response['usage']
        require(usage == response['response']['usage'], 'USAGE_RESPONSE_BINDING')
        require(receipt['request_hash'] == response['request_hash'] == digest(request['request']) and receipt['slot'] == request['slot'], 'RECEIPT_REQUEST_BINDING')
        require((receipt['input_tokens'], receipt['output_tokens']) == (usage['input_tokens'], usage['output_tokens']), 'RECEIPT_USAGE_BINDING')
        require(usage['total_tokens'] == usage['input_tokens'] + usage['output_tokens'], 'USAGE_TOTAL')
        arm = receipt['slot'].split('.')[1]; item = costs[arm]
        item['calls'] += 1; item['input_tokens'] += usage['input_tokens']; item['output_tokens'] += usage['output_tokens']
        item['cached_input_tokens'] += usage.get('input_tokens_details', {}).get('cached_tokens', 0)
        item['latencies'].append(receipt['latency_seconds']); receipt_hashes.append(receipt['self_hash'])
        require(request['request']['store'] is False and not request['request'].get('tools'), 'REQUEST_PRIVACY')
    for item in costs.values():
        timings = item.pop('latencies')
        item['latency_sum_seconds'] = sum(timings); item['latency_median_seconds'] = median(timings)
        item['standard_uncached_cost_upper_usd'] = str((Decimal(item['input_tokens']) * Decimal('.75') + Decimal(item['output_tokens']) * Decimal('4.5')) / 1000000)
        item['standard_cache_adjusted_estimate_usd'] = str((Decimal(item['input_tokens'] - item['cached_input_tokens']) * Decimal('.75') + Decimal(item['cached_input_tokens']) * Decimal('.075') + Decimal(item['output_tokens']) * Decimal('4.5')) / 1000000)
    total = {key: sum(v[key] for v in costs.values()) for key in ('calls', 'input_tokens', 'output_tokens', 'cached_input_tokens', 'latency_sum_seconds')}
    total['total_tokens'] = total['input_tokens'] + total['output_tokens']
    for key in ('standard_uncached_cost_upper_usd', 'standard_cache_adjusted_estimate_usd'):
        total[key] = str(sum(Decimal(v[key]) for v in costs.values()))
    require(total['calls'] <= budget['maximum_calls'] and total['input_tokens'] <= budget['maximum_input_tokens'] and total['output_tokens'] <= budget['maximum_output_tokens'], 'APPROVED_CAP_EXCEEDED')
    require(Decimal(total['standard_uncached_cost_upper_usd']) <= Decimal(budget['standard_api_cost_ceiling_usd']), 'COST_EXCEEDED')
    coverage = {a: {'selected_raw_parsed': 0, 'raw_draws_parsed': 0, 'raw_draws': 0, 'admitted': 0, 'observations': 0, 'terminals': Counter()} for a in ('T0', 'T1', 'T1-B', 'T2')}
    t2_actions = 0; t2_initial_repair = 0; t2_repaired = 0
    for item in admissions['records']:
        arm = item['arm']; c = coverage[arm]; c['observations'] += 1; c['admitted'] += int(item['admission_hash'] is not None)
        if arm == 'T0':
            c['selected_raw_parsed'] += 1; c['raw_draws_parsed'] += 1; c['raw_draws'] += 1
            c['terminals']['ADMITTED' if item['admission_hash'] else 'VERIFIER_REJECTION'] += 1
            continue
        row = read(RUN / 'outputs' / f"{item['candidate_id']}.{arm}.R{item['repeat']}.json")
        c['selected_raw_parsed'] += int(row['raw'][row['selected_draw'] - 1] is not None)
        c['raw_draws_parsed'] += sum(r is not None for r in row['raw']); c['raw_draws'] += len(row['raw']); c['terminals'][row['terminal']] += 1
        if arm == 'T2':
            t2_actions += len(row['feedback']); initial = row['verifier_results'][0]['status'] == 'NEEDS_REPAIR'
            t2_initial_repair += int(initial); t2_repaired += int(initial and item['admission_hash'] is not None)
    reports = {}
    for arm, report in evaluation['reports'].items():
        reports[arm] = {k: report[k] for k in ('strict', 'conditional', 'conditional_denominator', 'source_direction_accuracy', 'target_direction_accuracy', 'exact_horizon_accuracy', 'structure_reference_rule_denominator')}
        reports[arm]['raw_and_admitted_coverage'] = coverage[arm]
    guards = {}
    for key, item in final['guard'].items():
        guards[key] = {k: item[k] for k in ('numeric_binding_count', 'formal_conversion_count', 'admitted_rule_count', 'deployment_authorized')}
        guards[key]['binding_failure_count'] = len(item['numeric_binding_failures'])
        guards[key]['train3_confirmed_binding_eligible_count'] = item['numeric_binding_count'] + len(item['numeric_binding_failures'])
        guards[key]['opportunity_relation_coverage'] = 'NOT_RETAINED_IN_FROZEN_AGGREGATE'
        require(all(isinstance(row, list) and len(row) == 3 and isinstance(row[2], str) for row in item['states']), 'GUARD_STATE_SHAPE')
        guards[key]['guard_states'] = dict(Counter(row[2] for row in item['states']))
        guards[key]['retained_rule_count'] = sum(row[2] == 'RETAINED' for row in item['states'])
        guards[key]['portfolio_census'] = item['census']
    paired = Counter(('both_exact' if r['left_exact'] and r['right_exact'] else 'T2_only_exact' if r['left_exact'] else 'T1B_only_exact' if r['right_exact'] else 'neither_exact') for r in final['paired'])
    result = seal({
        'schema': 'exp03b_revised_public_results_v1', 'status': 'COMPLETE_PENDING_INDEPENDENT_QA',
        'model': budget['model'], 'N': budget['N'], 'R': budget['R'],
        'execution_source_commit': subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', 'research_control_center/validation_v2/exp03b/execution_v2/DG03B_REVISED_USER_APPROVAL_V1.json'], cwd=ROOT, text=True).strip(),
        'execution_freeze_hash': freeze['self_hash'], 'budget_hash': budget['self_hash'],
        'output_bundle_hash': outputs['self_hash'], 'admissions_hash': admissions['self_hash'],
        'train3_evaluation_hash': evaluation['self_hash'], 'final_local_results_hash': final['self_hash'],
        'call_receipt_bundle_hash': digest(receipt_hashes), 'reports': reports,
        'feedback_actions': t2_actions, 'initial_needs_repair_observations': t2_initial_repair,
        'verifier_repair_success_observations': t2_repaired,
        'repair_distinct_pairs': {k: len(v) for k, v in final['repairs'].items()},
        'paired_exact_match_table': dict(paired), 'post_induction': guards,
        'usage_by_arm': costs, 'usage_total': total, 'cost_boundary': 'TOKEN_PRICE_ESTIMATE_NOT_ACCOUNT_INVOICE',
        'disposition': final['disposition'], 'limitation': final['limitation'], 'next_gate': 'DG-04',
        'repeat_policy': 'T0_ONCE;STOCHASTIC_R3_NOT_IID;PORTFOLIO_REPEAT_1_ONLY',
        'production_portfolio_created': False,
        'test1': 0, 'test2': 0, 'heldout': 0, 'external_attack': 0, 'attack_label': 0,
        'GDN_retraining': 0, 'frozen_result_changes': 0, 'post_result_tuning': 0, 'private_exposures': 0,
    })
    publish(PUBLIC / 'execution_v2/EXP03B_REVISED_RESULTS_V1.json', result)
    write_report(result)
    print(json.dumps({'status': 'PUBLIC_SAFE_RESULT_PUBLISHED', 'calls': total['calls'], 'disposition': result['disposition'], 'self_hash': result['self_hash']}))


if __name__ == '__main__':
    main()
