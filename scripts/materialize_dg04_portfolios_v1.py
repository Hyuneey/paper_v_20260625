"""Materialize candidate membership only from frozen EXP03B; no scientific rerun."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import csv
import io
import json
import subprocess
from paperworks.validation_v2.exp03b_contract_v1 import require, digest
from paperworks.validation_v2.exp03b_custody_v1 import publish, replay, seal
from paperworks.validation_v2.final_method_lock_v1 import BASELINE, NUMERIC_POLICY
from paperworks.validation_v2.final_method_lock_v1 import RESULT_HASH, QA_HASH
from paperworks.validation_v2.exp03b_semantic_v2 import parse_proposal, proposal_document
from paperworks.validation_v2.exp03b_codec_v2 import structural
from paperworks.validation_v2.exp03b_hidden_v2 import Train2HiddenVerifierAuthorityV2, verify, retrieval, feedback
from paperworks.validation_v2.exp03b_execution_v2 import admit
from paperworks.validation_v2.heldout_candidate_portfolio_v1 import retained_descriptors, candidate_manifest, census, compare
from paperworks.validation_v2.formal_v4_authority_v1 import (
    FormalV4RuleDescriptorV1, NumericReferenceBindingV1, FormalV4ArtifactBindingV1,
    V4_NUMERIC_ROLES, _validate_descriptor_materialization_v1, load_formal_v4_numeric_values_v1)

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / 'research_control_center/validation_v2'
DEST = PUB / 'dg04_xver_prep'
PRIVATE = ROOT / 'artifacts/validation_v2/exp03b/private'
RUN = PRIVATE / 'provider_execution_v2'


def read(path: Path, sealed: bool = True) -> dict:
    require(not path.is_symlink(), 'SYMLINK_REJECTED')
    value = json.loads(path.read_bytes())
    if sealed: replay(value)
    return value


def filehash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write_text_new(path: Path, text: str) -> None:
    payload = text.encode('utf-8')
    if path.exists(): require(path.read_bytes() == payload, 'APPEND_ONLY_REPORT_CONFLICT')
    else:
        with path.open('xb') as out: out.write(payload)


def main():
    require(not (RUN / 'SINGLE_WRITER.lock').exists(), 'WRITER_ACTIVE')
    lock = read(DEST / 'FINAL_METHOD_LOCK_V1.json')
    freeze = read(PUB / 'exp03b/EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json')
    cohort = read(PUB / 'exp03b/EXP03B_COHORT_AUTHORITY_V1.json')
    cohort_relative = 'research_control_center/validation_v2/exp03b/EXP03B_COHORT_AUTHORITY_V1.json'
    require((ROOT / cohort_relative).read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + cohort_relative], cwd=ROOT), 'COHORT_BASELINE_ANCHOR')
    result = read(PUB / 'exp03b/execution_v2/EXP03B_REVISED_RESULTS_V1.json')
    require(lock['result_hash'] == result['self_hash'] == RESULT_HASH and lock['independent_qa_hash'] == QA_HASH,
            'LOCK_RESULT_ANCHOR')
    require(freeze['self_hash'] == result['execution_freeze_hash'], 'EXECUTION_FREEZE_ANCHOR')
    for relative,h in freeze['private_input_hashes'].items():
        require(filehash(PRIVATE / relative) == h, 'FROZEN_PRIVATE_INPUT_CHANGED')
    for relative,h in freeze['implementation_hashes'].items():
        require(filehash(ROOT / relative) == h, 'FROZEN_IMPLEMENTATION_CHANGED')
    hidden = read(PRIVATE / 'train3/reference.json')
    final = read(RUN / 'evaluation/FINAL_LOCAL_RESULTS.json')
    outputs = read(RUN / 'ALL_ARM_OUTPUTS_FROZEN.json')
    admissions = read(RUN / 'evaluation/TRAIN2_ADMISSIONS_FROZEN.json')
    train3 = read(RUN / 'evaluation/TRAIN3_EVALUATION_FROZEN.json')
    require(hidden['self_hash'] == train3['reference_hash'] == freeze['private_reference_hash'], 'REFERENCE_BINDING')
    reference = {p['candidate_id']: p['relations'] for p in hidden['pairs']}
    numeric = read(RUN / 'evaluation/NUMERIC_BINDING_STARTED.json')
    closed = read(RUN / 'PROVIDER_PHASE_CLOSED.json')
    require(closed['provider_calls_allowed'] is False, 'PROVIDER_NOT_CLOSED')
    require(closed['output_bundle_hash'] == outputs['self_hash'] and closed['execution_freeze_hash'] == freeze['self_hash'], 'CLOSED_PHASE_BINDING')
    require(final['self_hash'] == result['final_local_results_hash'] and
            outputs['self_hash'] == result['output_bundle_hash'] and
            admissions['self_hash'] == result['admissions_hash'] and
            train3['self_hash'] == result['train3_evaluation_hash'], 'PHASE_HASH_MISMATCH')
    require(numeric['policy'] == NUMERIC_POLICY and numeric['provider_calls_allowed'] is False and
            numeric['output_bundle_hash'] == outputs['self_hash'] and
            numeric['admissions_hash'] == admissions['self_hash'] and
            numeric['train3_evaluation_hash'] == train3['self_hash'], 'NUMERIC_PHASE_MISMATCH')
    pairs = {p['candidate_id']: (p['source'], p['target']) for p in cohort['pairs']}
    require(len(pairs) == cohort['count'], 'COHORT_REPLAY')
    call_index = {}; call_repairs = {}
    for i in range(1, outputs['calls'] + 1):
        req = read(RUN / 'calls' / f'{i:04d}.request.json')
        if '.T2.R1.' not in req['slot']: continue
        res = read(RUN / 'calls' / f'{i:04d}.response.json')
        receipt = read(RUN / 'calls' / f'{i:04d}.receipt.json')
        require(req['reservation']['request_hash'] == res['request_hash'] == digest(req['request']), 'REQUEST_RESPONSE_HASH')
        require(receipt['request_hash'] == res['request_hash'] and receipt['response_hash'] == digest(res['response'])
                and receipt['slot'] == req['slot'], 'CALL_RECEIPT_BINDING')
        body = json.loads(req['request']['input'])
        repair = body.get('repair')
        call_repairs[req['slot']] = repair
        call_index[req['slot']] = {'request_hash': req['self_hash'], 'response_hash': res['self_hash'],
            'receipt_hash': receipt['self_hash'], 'repair_projection_hash': digest(repair) if repair else None,
            'retrieval_hash': repair['retrieval']['retrieval_hash'] if repair else None}
    source_commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--',
        'research_control_center/validation_v2/dg04_xver_prep/FINAL_METHOD_LOCK_V1.json'], cwd=ROOT, text=True).strip()
    require(len(source_commit) == 40 and subprocess.run(['git', 'merge-base', '--is-ancestor', source_commit, 'HEAD'], cwd=ROOT).returncode == 0, 'SOURCE_COMMIT_ANCESTRY')
    views = {}; manifests = {}
    for arm in ('T0', 'T2'):
        group = arm + '.R1'; directory = RUN / 'evaluation/conversion' / group
        conversion = read(directory / 'CONVERSION_RECEIPT.json')
        rel = read(directory / 'relations.json', False); num = read(directory / 'numeric.json', False)
        rh, nh = filehash(directory / 'relations.json'), filehash(directory / 'numeric.json')
        require((rh, nh) == (conversion['relation_authority_hash'], conversion['numeric_authority_hash']), 'CONVERSION_INPUT_HASH')
        descriptors = []
        for row in rel['relations']:
            refs = [x for x in num['bindings'] if x['relation_id'] == row['relation_id']]
            refs.sort(key=lambda r: V4_NUMERIC_ROLES.index(r['numeric_role']))
            descriptors.append(FormalV4RuleDescriptorV1(**row, numeric_authority_hash=nh,
                numeric_reference_bindings=tuple(NumericReferenceBindingV1(x['numeric_role'], x['reference_id'], x['reference_hash']) for x in refs)))
        require([x.descriptor_hash for x in descriptors] == conversion['descriptor_hashes'], 'DESCRIPTOR_HASH_SEQUENCE')
        rb = FormalV4ArtifactBindingV1('EXP03B-RELATION', (directory / 'relations.json').relative_to(ROOT).as_posix(), rh)
        nb = FormalV4ArtifactBindingV1('EXP03B-NUMERIC', (directory / 'numeric.json').relative_to(ROOT).as_posix(), nh)
        _validate_descriptor_materialization_v1(tuple(descriptors), relation_authority_binding=rb, numeric_authority_binding=nb, repository_root=ROOT)
        for d in descriptors: load_formal_v4_numeric_values_v1(descriptor=d, numeric_authority_binding=nb, repository_root=ROOT)
        selected = retained_descriptors([x.to_dict() for x in descriptors], final['guard'][group]['states'], pairs)
        lineage = {}
        for d in selected:
            cid = next(cid for cid, pair in pairs.items() if pair == (d['source'], d['target']))
            admission = next(x['admission_hash'] for x in admissions['records'] if (x['arm'], x['repeat'], x['candidate_id']) == (arm, 1, cid))
            require(admission is not None, 'ADMISSION_MISSING')
            semantic = {'source_direction': d['source_direction'], 'target_direction': d['target_direction'], 'horizon_seconds': d['selected_horizon_seconds']}
            require(semantic in reference[cid], 'TRAIN3_MEMBERSHIP')
            pack = read(PRIVATE / f'semantic_v2/train1/provider/{cid}.json', False)
            auth = Train2HiddenVerifierAuthorityV2(structural(read(PRIVATE / f'semantic_v2/train2/structural/{cid}.json', False), 'train2'), frozenset(r[7] for r in pack['structural_rows']))
            retrieval_ids = frozenset()
            if arm == 'T0':
                name = f'semantic_v2/train1/t0/{cid}.json'
                ph = filehash(PRIVATE / name)
                require(ph == freeze['private_input_hashes'][name], 'T0_PROPOSAL_HASH')
                proposal = parse_proposal(read(PRIVATE / name, False))
                origin = {'proposal_file_hash': ph, 'calls': [], 'repeat_policy': 'DETERMINISTIC_SINGLE_RUN_REFERENCE'}
            else:
                terminal = read(RUN / 'outputs' / f'{cid}.T2.R1.json')
                require(terminal['self_hash'] in outputs['terminal_hashes'] and terminal['repeat'] == 1 and terminal['arm'] == arm and terminal['candidate_id'] == cid, 'REPEAT_OUTPUT_HASH')
                calls = [call_index[f'{cid}.T2.R1.C{i}'] for i in range(1, terminal['selected_draw'] + 1)]
                require(1 <= len(calls) <= 3, 'CALL_CARDINALITY')
                require(terminal['selected_draw'] == len(terminal['raw']), 'FINAL_DRAW_REQUIRED')
                expected_feedback = []
                for i, raw in enumerate(terminal['raw'][:-1], 1):
                    p = parse_proposal(raw); verdict = verify(p, auth, retrieval_ids=retrieval_ids)
                    require(verdict.status == 'NEEDS_REPAIR', 'T2_EARLY_STOP')
                    f = feedback(p, verdict, i); q = retrieval(auth, p, verdict)
                    expected_feedback.append(f)
                    require(call_repairs[f'{cid}.T2.R1.C{i+1}'] == {'previous_proposal': proposal_document(p), 'feedback': f, 'retrieval': q}, 'REPAIR_PAYLOAD_BINDING')
                    retrieval_ids |= frozenset(x['evidence_slice_id'] for x in q['alternatives'])
                require(expected_feedback == terminal['feedback'], 'FEEDBACK_REPLAY')
                proposal = parse_proposal(terminal['raw'][-1])
                require(terminal['admission_receipt']['self_hash'] == admission, 'TERMINAL_ADMISSION')
                origin = {'terminal_output_hash': terminal['self_hash'], 'feedback_hash': digest(terminal['feedback']), 'calls': calls, 'repeat_policy': 'PREASSIGNED_REPEAT_1'}
            accepted = admit(proposal, auth, implementation_hash=freeze['implementation_bundle_hash'], config_hash=freeze['provider_config_hash'], retrieval_ids=retrieval_ids)
            require(accepted.receipt['self_hash'] == admission, 'ADMISSION_REPLAY')
            require(any(r.semantic.__dict__ == semantic for r in proposal.rules), 'PROPOSAL_SEMANTIC_BINDING')
            lineage[d['relation_id']] = {'candidate_id': cid, **origin, 'train2_admission_hash': admission,
                'train2_admissions_bundle_hash': admissions['self_hash'], 'train3_evaluation_hash': train3['self_hash'],
                'train3_reference_hash': train3['reference_hash'], 'numeric_binding_phase_hash': numeric['self_hash'],
                'numeric_source_hashes': {s: freeze['private_input_hashes'][s + '/numeric_roles.json'] for s in ('train1', 'train2')},
                'conversion_receipt_hash': conversion['self_hash'], 'guard_result_hash': final['self_hash'],
                'guard_group': group, 'guard_status': 'RETAINED'}
        stats = result['post_induction'][group]
        manifest = candidate_manifest(arm=arm, repeat=1, descriptors=selected, lineage=lineage,
            method_lock_hash=lock['self_hash'], source_commit=source_commit,
            guard_census=final['guard'][group]['census'],
            stage_counts={k: stats[k] for k in ('admitted_rule_count', 'numeric_binding_count', 'formal_conversion_count', 'retained_rule_count')})
        private_binding = seal({'portfolio_hash': manifest['self_hash'], 'source_commit': source_commit,
            'relation_binding': rb.to_dict(), 'numeric_binding': nb.to_dict(),
            'descriptors': selected, 'attack_access_authorized': False, 'production_authorized': False})
        target = ROOT / 'artifacts/validation_v2/dg04_xver_prep/private' / (arm + '_PORTFOLIO_BINDING.json')
        publish(target, private_binding)
        require(subprocess.run(['git', 'check-ignore', '--quiet', str(target)], cwd=ROOT).returncode == 0, 'PRIVATE_NOT_IGNORED')
        publish(DEST / (arm + '_HELDOUT_CANDIDATE_PORTFOLIO_V1.json'), manifest)
        views[arm] = selected; manifests[arm] = manifest
    v2a_path = PUB / 'core_v2a/authorities/V2A_FORMAL_V4_PORTFOLIO_AUTHORITY.json'
    require(v2a_path.read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + v2a_path.relative_to(ROOT).as_posix()], cwd=ROOT), 'V2A_CHANGED')
    v2a = read(v2a_path, False); views['V2A'] = v2a['descriptors']
    comparisons = {a + '_vs_' + b: compare(views[a], views[b]) for a, b in (('T0','T2'),('V2A','T0'),('V2A','T2'))}
    report = seal({'schema': 'final_portfolio_comparison_v1', 'comparisons': comparisons,
        'census': {k: census(v) for k,v in views.items()},
        'portfolio_hashes': {**{a:m['self_hash'] for a,m in manifests.items()}, 'V2A': v2a['authority_hash']},
        'V2A_train4_comparability': 'NOT_RETAINED_IN_EXP03B_SAME_CONTEXT_NO_RERUN',
        'selection_performed': False, 'scientific_reruns': 0, 'test_accesses': 0, 'provider_calls': 0})
    publish(DEST / 'FINAL_PORTFOLIO_COMPARISON_V1.json', report)
    text = '# 정상-only 포트폴리오 비교\n\n포트폴리오 선택은 하지 않았습니다. V2A는 기존 reference, T0/T2는 별도 HELDOUT_CANDIDATE입니다. 공격·production 권한은 없습니다. T2는 Repeat 1만 사용했습니다.\n\n'
    text += '| portfolio | pairs | retained Rules | sources | targets |\n|---|---:|---:|---:|---:|\n'
    for a,c in report['census'].items(): text += f"| {a} | {c['pair_count']} | {c['rule_count']} | {c['source_count']} | {c['target_count']} |\n"
    text += '\nT0/T2 비교: ' + json.dumps(comparisons['T0_vs_T2'], ensure_ascii=False) + '\n\n'
    text += 'Train4 census는 기존 arm-group cross-source isolation context에 결속되며 retained-only universe를 재평가한 결과가 아닙니다. V2A의 동일-context train4 비교와 per-rule opportunity coverage는 보존 artifact에 없으므로 미제공입니다. 수치값·private 경로는 공개하지 않습니다.\n'
    write_text_new(DEST / 'FINAL_PORTFOLIO_COMPARISON_V1.md', text)
    out = io.StringIO(); writer = csv.DictWriter(out, fieldnames=['comparison', *next(iter(comparisons.values())).keys()]); writer.writeheader()
    for key,row in comparisons.items(): writer.writerow({'comparison': key, **row})
    write_text_new(DEST / 'FINAL_PORTFOLIO_COMPARISON_V1.csv', out.getvalue())
    print(json.dumps({'status': 'CANDIDATES_MATERIALIZED', 'census': report['census'], 'portfolio_hashes': report['portfolio_hashes']}))


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(json.dumps({'status': 'FAIL_CLOSED', 'error_type': type(error).__name__})); raise SystemExit(2)
