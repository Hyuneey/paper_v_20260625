"""Append a single-copy local execution custody manifest; public hashes only."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
from paperworks.validation_v2.exp03b_custody_v1 import publish, seal, replay
from paperworks.validation_v2.exp03b_contract_v1 import require
ROOT = Path(__file__).resolve().parents[1]


def main():
    common = Path(subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT, text=True).strip()).resolve()
    vault = common.parent.parent / 'paper_v_20260625_private_vault'
    require(vault.exists() and not vault.is_symlink(), 'EXISTING_VAULT_REQUIRED')
    prior = vault / 'exp03b-payload-reduce-001/TASK_PRIVATE_VAULT_MANIFEST.json'
    prior_raw = prior.read_bytes(); replay(json.loads(prior_raw))
    run = ROOT / 'artifacts/validation_v2/exp03b/private/provider_execution_v2'
    require((run / 'evaluation/FINAL_LOCAL_RESULTS.json').exists() and not (run / 'SINGLE_WRITER.lock').exists(), 'FINAL_RESULTS_REQUIRED')
    records = []
    for path in sorted(run.rglob('*.json')):
        require(not path.is_symlink(), 'SYMLINK'); raw = path.read_bytes()
        records.append({'path': str(path.resolve()), 'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)})
    manifest = seal({'task': 'EXP03B-PROVIDER-EXEC-001', 'records': records, 'prior_manifest_file_hash': sha256(prior_raw).hexdigest(), 'storage_policy': 'SINGLE_COPY_LOCAL_ONLY', 'second_copy_verified': False, 'next_gate': 'DG-04'})
    target = vault / 'exp03b-provider-exec-001/TASK_PRIVATE_VAULT_MANIFEST.json'; publish(target, manifest)
    restored = json.loads(target.read_text()); replay(restored); require(restored == manifest, 'RESTORE_READ_SMOKE')
    publish(ROOT / 'research_control_center/validation_v2/exp03b/execution_v2/EXP03B_EXECUTION_PRIVATE_INDEX_V1.json', seal({'private_manifest_hash': manifest['self_hash'], 'record_count': len(records), 'storage_policy': 'SINGLE_COPY_LOCAL_ONLY', 'second_copy_verified': False, 'restore_read_smoke': 'PASS', 'private_exposures': 0}))
    print(json.dumps({'status': 'PASS', 'record_count': len(records), 'restore_read_smoke': 'PASS', 'storage_policy': 'SINGLE_COPY_LOCAL_ONLY'}))


if __name__ == '__main__': main()
