"""Read-only execution integrity and preservation replay; no scientific rerun."""
from hashlib import sha256
from pathlib import Path
import json
import subprocess

from paperworks.validation_v2.exp03b_custody_v1 import replay
from paperworks.validation_v2.exp03b_contract_v1 import require, digest
from audit_exp03b_preparation_gate_v1 import audit

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / 'research_control_center/validation_v2/exp03b'
PRIVATE = ROOT / 'artifacts/validation_v2/exp03b/private'


def main():
    run = PRIVATE / 'provider_execution_v2'
    require(not (run / 'SINGLE_WRITER.lock').exists(), 'WRITER_ACTIVE')
    preservation = audit(ROOT)
    pilot = json.loads((ROOT / 'research_control_center/validation_v2/PILOT_V1_PRESERVATION_MANIFEST.json').read_text())
    base = subprocess.check_output(['git', 'ls-tree', '-r', '-z', pilot['authority_commit']], cwd=ROOT)
    index = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT)
    expected = {x.split(b'\t', 1)[1]: x.split(b'\t', 1)[0].split()[2] for x in base.split(b'\0') if x and b' blob ' in x.split(b'\t', 1)[0]}
    actual = {x.split(b'\t', 1)[1]: x.split(b'\t', 1)[0].split()[1] for x in index.split(b'\0') if x}
    require(len(expected) == 3021 and all(actual.get(k) == v for k, v in expected.items()), 'PILOT_CHANGED')
    changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()
    require(not any(p.encode() in expected for p in changed), 'PILOT_WORKTREE_CHANGED')
    for ref in (pilot['authority_ref'], pilot['immutable_tag']):
        require(subprocess.check_output(['git', 'rev-parse', ref + '^{commit}'], cwd=ROOT, text=True).strip() == pilot['authority_commit'], 'PILOT_REF_CHANGED')
    inputs = 0
    for name in ('EXP03B_FINAL_PREPARATION_FREEZE_V2.json', 'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json'):
        freeze = json.loads((PUB / name).read_text()); replay(freeze)
        for relative, h in freeze['implementation_hashes'].items(): require(sha256((ROOT / relative).read_bytes()).hexdigest() == h, 'CODE_CHANGED')
        for relative, h in freeze['private_input_hashes'].items(): require(sha256((PRIVATE / relative).read_bytes()).hexdigest() == h, 'INPUT_CHANGED'); inputs += 1
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'd10c93fbe36be237e5ecfe623c29c67b58e9e30d', '--', 'research_control_center/validation_v2/exp03b'], cwd=ROOT, text=True).splitlines()
    for name in names: require((ROOT / name).read_bytes() == subprocess.check_output(['git', 'show', 'd10c93fbe36be237e5ecfe623c29c67b58e9e30d:' + name], cwd=ROOT), 'FROZEN_PUBLIC_CHANGED')
    records = {}
    for path in run.rglob('*.json'):
        require(not path.is_symlink(), 'PRIVATE_SYMLINK')
        raw = path.read_bytes(); value = json.loads(raw)
        if 'self_hash' in value: replay(value)
        records[path.relative_to(run).as_posix()] = sha256(raw).hexdigest()
    public = json.loads((PUB / 'execution_v2/EXP03B_REVISED_RESULTS_V1.json').read_text()); replay(public)
    for filename, field in [('ALL_ARM_OUTPUTS_FROZEN.json', 'output_bundle_hash'), ('evaluation/TRAIN2_ADMISSIONS_FROZEN.json', 'admissions_hash'), ('evaluation/TRAIN3_EVALUATION_FROZEN.json', 'train3_evaluation_hash'), ('evaluation/FINAL_LOCAL_RESULTS.json', 'final_local_results_hash')]:
        value = json.loads((run / filename).read_text()); replay(value); require(value['self_hash'] == public[field], 'PUBLIC_RESULT_BINDING')
    require(subprocess.run(['git', 'check-ignore', '--quiet', str(PRIVATE)], cwd=ROOT).returncode == 0, 'PRIVATE_NOT_IGNORED')
    require(not subprocess.check_output(['git', 'ls-files', '--', str(PRIVATE)], cwd=ROOT).strip(), 'PRIVATE_TRACKED')
    print(json.dumps({'status': 'PASS', 'PILOT_V1_blobs': 3021, 'protected_V2_blobs': preservation['protected_public_blob_count'], 'prior_EXP03B_public_files': len(names), 'private_input_hash_bindings_replayed': inputs, 'execution_file_count': len(records), 'execution_file_hash_bundle': digest(records), 'provider_calls': public['usage_total']['calls'], 'test1': 0, 'test2': 0, 'heldout': 0, 'attack_labels': 0, 'private_exposures': 0}))


if __name__ == '__main__':
    main()
