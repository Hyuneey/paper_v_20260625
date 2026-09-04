"""Freeze serializer/settings before profiling or any prospective provider use."""
from xver_execution_common import ROOT, PUB, committed, head, publish, seal, digest, sha256_file
from paperworks.validation_v2.xver_prompt_v1 import execution_config
from paperworks.validation_v2.exp03b_prompt_v2 import SYSTEM_PROMPT, output_schema


if __name__=='__main__':
    files=('src/paperworks/validation_v2/xver_prompt_v1.py','scripts/freeze_xver_provider_v1.py','scripts/freeze_xver_prompt_contract_v1.py','tests/test_xver_prompt_v1.py')
    for name in files:committed(ROOT/name)
    value=seal({'schema':'xver_provider_serializer_freeze_v1','source_commit':head(),'implementation_hashes':{p:sha256_file(ROOT/p) for p in files},'system_prompt_hash':digest(SYSTEM_PROMPT),'schema_hash':digest(output_schema()),'configuration':execution_config(),'configuration_hash':digest(execution_config()),'version_and_candidate_and_pack_hash_required':True,'global_only_retrieval':True,'event_exposure':False,'provider_calls_authorized':False})
    publish(PUB/'XVER_PROVIDER_SERIALIZER_FREEZE_V1.json',value)
    print('OFFLINE_PROVIDER_SERIALIZER_FROZEN_NO_CALL_AUTHORITY')
