"""Record the explicit DG-03B_REVISED user decision; no credential or transport."""
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess

from paperworks.validation_v2.exp03b_contract_v1 import digest, require
from paperworks.validation_v2.exp03b_custody_v1 import seal, publish, replay
from paperworks.validation_v2.exp03b_provider_gate_v2 import ProviderCallGate

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / 'research_control_center/validation_v2/exp03b'
PRIVATE = ROOT / 'artifacts/validation_v2/exp03b/private'
BASELINE = 'd10c93fbe36be237e5ecfe623c29c67b58e9e30d'


def main():
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASELINE, 'APPROVAL_BASELINE')
    budget = json.loads((PUB / 'EXP03B_PROVIDER_BUDGET_V2.json').read_text()); replay(budget)
    freeze = json.loads((PUB / 'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json').read_text()); replay(freeze)
    require(budget['self_hash'] == 'e6731a2fcfc1969287f74217b6cccb05f970673b5684a20493dec535b0ad28b6', 'APPROVED_BUDGET')
    require(freeze['self_hash'] == 'bacfd22859bb7014f3604abf4ad81b63586e1a98f21ddb0206b4a8e892f8ab8c', 'APPROVED_FREEZE')
    approval = seal({
        'schema': 'exp03b_revised_user_approval_v1', 'gate': 'DG-03B_REVISED',
        'status': 'APPROVED', 'decision_source': 'EXPLICIT_RESEARCH_OWNER_MESSAGE',
        'integration_baseline': BASELINE,
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'budget_hash': budget['self_hash'], 'execution_freeze_hash': freeze['self_hash'],
        'implementation_commit': freeze['implementation_commit'],
        'provider_config_hash': budget['config_hash'],
        'provider_input_hashes_digest': digest(freeze['provider_input_hashes']),
        'model': 'gpt-5.4-mini-2026-03-17', 'endpoint': 'https://api.openai.com/v1/responses',
        'N': 29, 'R': 3, 'maximum_calls': {'T1': 87, 'T1-B': 261, 'T2': 261, 'total': 609},
        'maximum_input_tokens': 7216128, 'maximum_output_tokens': 1247232,
        'maximum_total_tokens': 8463360, 'standard_api_cost_ceiling_usd': '11.03',
        'concurrency': 1, 'retry': 0, 'reasoning': 'none', 'temperature': 0.7,
        'top_p': 1.0, 'store': False, 'tools_allowed': False, 'fallback_allowed': False,
        'semantic_only': True, 'numeric_policy_provider_visible': False,
        'T2_early_stop_on_accepted': True, 'T2_maximum_calls_per_pair_repeat': 3,
        'first_scientific_call_is_probe': True, 'additional_probe_calls_allowed': False,
        'post_induction_order': ['ALL_OUTPUTS_FROZEN', 'TRAIN2_ADMISSIONS_FROZEN', 'TRAIN3_SEMANTIC_EVALUATION_FROZEN', 'SCI02B_FIXED_NUMERIC_BINDING', 'FORMAL_V4', 'TRAIN4_ONE_WAY_GUARD'],
        'portfolio_repeat': 1, 'next_gate': 'DG-04',
        'test1_allowed': False, 'test2_allowed': False, 'heldout_allowed': False,
        'external_attack_allowed': False, 'attack_labels_allowed': False,
        'frozen_result_changes_allowed': False,
    })
    ProviderCallGate(budget, approval, freeze['self_hash'])
    publish(PRIVATE / 'approvals/DG03B_REVISED_APPROVED_V1.json', approval)
    publish(PUB / 'execution_v2/DG03B_REVISED_USER_APPROVAL_V1.json', approval)
    print(json.dumps({'status': 'APPROVAL_RECORDED', 'self_hash': approval['self_hash'], 'provider_calls': 0, 'credential_reads': 0}))


if __name__ == '__main__':
    main()
