"""Record the explicit DG04 decision. No provider, credentials or data reads."""
from pathlib import Path
import json
from paperworks.validation_v2.final_method_lock_v1 import method_lock
from paperworks.validation_v2.exp03b_custody_v1 import publish

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / 'research_control_center/validation_v2'


def main():
    source = PUB / 'exp03b/execution_v2'
    result = json.loads((source / 'EXP03B_REVISED_RESULTS_V1.json').read_text())
    qa = json.loads((source / 'EXP03B_EXECUTION_INDEPENDENT_QA_V1.json').read_text())
    value = method_lock(result, qa)
    publish(PUB / 'dg04_xver_prep/FINAL_METHOD_LOCK_V1.json', value)
    print(json.dumps({'status': value['status'], 'decision_id': value['decision_id'],
                      'self_hash': value['self_hash'], 'provider_calls': 0, 'data_reads': 0}))


if __name__ == '__main__': main()
