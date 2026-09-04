"""Serial normal-only CPU follow-on; never starts GPU or provider execution."""
import json
import subprocess
import sys
import time
from xver_execution_common import ROOT, PUB
from xver_result_integrity_v1 import scientific_receipts


def main():
    for version in ('22.04','21.03'):
        paths=[PUB/'runs'/f'HAI{version[:2]}_{split.upper()}_SEED{seed}_RECEIPT_V1.json' for split in ('train1','train2') for seed in (11,23,37)]
        print(json.dumps({'phase':'WAIT_FOR_EXACT_SIX_GDN_RECEIPTS','version':version}),flush=True)
        while not all(p.is_file() for p in paths):time.sleep(5)
        scientific_receipts(version)
        commands=[['scripts/run_xver_semantic_execution_v1.py',phase,'--version',version] for phase in ('evidence','t0')]
        commands.append(['scripts/freeze_xver_provider_v1.py','--version',version])
        for args in commands:
            print(json.dumps({'phase':'CPU_NORMAL_STAGE_START','version':version,'stage':args[1] if args[0].endswith('semantic_execution_v1.py') else 'OFFLINE_PROVIDER_PROFILE'}),flush=True)
            status=subprocess.run([sys.executable,*args],cwd=ROOT).returncode
            if status:return status
    return 0


if __name__=='__main__':
    try:status=main()
    except Exception as error:
        print(json.dumps({'status':'CPU_NORMAL_CLOSURE_FAILURE','error_type':type(error).__name__}),flush=True)
        status=2
    raise SystemExit(status)
