"""External deterministic T0 phase capability; does not impersonate provider runs."""
from dataclasses import asdict
from pathlib import Path
from hashlib import sha256
import json
from .exp03b_contract_v1 import require, digest
from .exp03b_custody_v1 import replay, seal, publish
from .exp03b_execution_v2 import VerifiedAdmission
from .exp03b_binder_v2 import POLICY, FIXED_ALIAS, fixed_roles, validate_roles
from .exp03b_numeric_v1 import roles_from_summary, pooled_roles
from .exp03b_evaluation import GuardRuleInput
from .exp03b_semantic_v2 import parse_proposal, proposal_document

_ISSUER = object()


class ExternalT0ClosureV1:
    __slots__ = ('files', 'reference_hash', 'members', 'admission_hashes')
    def __init__(self, token, files, reference_hash, members, admission_hashes):
        require(token is _ISSUER, 'T0_CLOSURE_FACTORY_REQUIRED')
        self.files = tuple(files); self.reference_hash = reference_hash
        self.members = frozenset(members); self.admission_hashes = frozenset(admission_hashes)
    def replay(self):
        require(all(sha256(p.read_bytes()).hexdigest() == h for p, h in self.files), 'T0_CLOSURE_BYTES_CHANGED')


def authorize_t0_binding(directory: Path, *, version: str, candidate_ids: tuple[str, ...], execution_hash: str):
    """Every T0 slot plus hidden admissions/reference/evaluation must be durable."""
    require(version in ('22.04', '21.03') and candidate_ids and len(set(candidate_ids)) == len(candidate_ids), 'T0_COHORT')
    files = []
    def read(name):
        p = directory/name; raw = p.read_bytes(); d = json.loads(raw); replay(d)
        require(d['version'] == version and d['provider_calls'] == 0 and d['execution_hash'] == execution_hash, 'T0_PHASE_IDENTITY')
        files.append((p, sha256(raw).hexdigest())); return d
    out = read('T0_OUTPUTS_FROZEN.json'); adm = read('TRAIN2_ADMISSIONS_FROZEN.json')
    ref = read('NORMAL_REFERENCE_FROZEN.json'); ev = read('SEMANTIC_EVALUATION_FROZEN.json')
    for doc in (out, adm, ref, ev):
        require(tuple(r['candidate_id'] for r in doc['records']) == candidate_ids, 'T0_SLOT_CLOSURE')
    require(adm['outputs_hash'] == out['self_hash'] and ev['outputs_hash'] == out['self_hash'] and ev['admissions_hash'] == adm['self_hash'] and ev['reference_hash'] == ref['self_hash'], 'T0_PHASE_ORDER_BINDING')
    for o, a, r, e in zip(out['records'], adm['records'], ref['records'], ev['records']):
        proposal = parse_proposal(o['proposal'])
        require(o['proposal_hash'] == digest(proposal_document(proposal)), 'T0_PROPOSAL_HASH')
        accepted = a['status'] == 'ACCEPTED'
        require(accepted == (a['admission_hash'] is not None) == (a['admission_receipt'] is not None), 'T0_ADMISSION_STATE')
        if accepted:
            receipt = a['admission_receipt']; replay(receipt)
            require(receipt['self_hash'] == a['admission_hash'] and receipt['candidate_id'] == o['candidate_id'] and receipt['proposal_hash'] == o['proposal_hash'] and receipt['verifier_status'] == 'ACCEPTED' and receipt['config_hash'] == execution_hash and receipt['verifier_result_hash'] == digest(a['verifier']), 'T0_ADMISSION_CONTENT')
        require(a['verifier']['status'] == a['status'] and e['admitted'] == accepted, 'T0_VERIFIER_STATE')
        truth = tuple(sorted((x['source_direction'], x['target_direction'], x['horizon_seconds']) for x in r['relations']))
        prediction = tuple((s.source_direction, s.target_direction, s.horizon_seconds) for s in proposal.semantic_set())
        require(e['semantic_exact'] == (accepted and prediction == truth), 'T0_EVALUATION_CONTENT')
    members = ((p['candidate_id'], r['source_direction'], r['target_direction'], r['horizon_seconds']) for p in ref['records'] for r in p['relations'])
    hashes = [p['admission_hash'] for p in adm['records'] if p['admission_hash'] is not None]
    cap = ExternalT0ClosureV1(_ISSUER, files, ref['self_hash'], members, hashes); cap.replay()
    publish(directory/'NUMERIC_BINDING_STARTED.json', seal({'version': version, 'provider_calls': 0, 'policy': POLICY, 'outputs_hash': out['self_hash'], 'admissions_hash': adm['self_hash'], 'evaluation_hash': ev['self_hash'], 'provider_phase': 'NOT_AUTHORIZED_NO_PROVIDER_EXECUTION'}))
    return cap


def bind_t0_rule(cap, admission, index, *, pair, train1_summary, train2_summary):
    require(type(cap) is ExternalT0ClosureV1, 'POST_SEMANTIC_EVALUATION_REQUIRED'); cap.replay()
    require(type(admission) is VerifiedAdmission, 'VERIFIED_ADMISSION_REQUIRED'); admission.replay()
    require(admission.receipt['self_hash'] in cap.admission_hashes, 'T0_ADMISSION_CLOSURE')
    require(admission.candidate_id == 'EXP03B-CAND-'+digest({'source': pair[0], 'target': pair[1]})[:20], 'PAIR_BINDING')
    semantic = admission.proposal.rules[index].semantic
    require((admission.candidate_id, semantic.source_direction, semantic.target_direction, semantic.horizon_seconds) in cap.members, 'NORMAL_CONFIRMATION_REQUIRED')
    tables = []
    for source_summary, target_summary in (train1_summary, train2_summary):
        selected = fixed_roles(source_summary, target_summary, semantic.source_direction)
        common = roles_from_summary(source_summary, target_summary, semantic.source_direction, 'NUM-000')
        validate_roles(common); tables.append((selected, common))
    selected = pooled_roles(tables[0][0], tables[1][0], train2_status='ACCEPTED')
    common = pooled_roles(tables[0][1], tables[1][1], train2_status='ACCEPTED')
    return GuardRuleInput(admission.candidate_id, *pair, semantic, FIXED_ALIAS, tuple(sorted(selected.items())), tuple(sorted(common.items())), admission.receipt['self_hash'], cap.reference_hash, digest(tables[0]), digest(tables[1]))
