"""Read-only parent replay and public context freeze; no scientific execution."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
from paperworks.validation_v2.exp03b_custody_v1 import replay, seal, publish
from paperworks.validation_v2.exp03b_contract_v1 import require, digest
from paperworks.validation_v2.gdn_corr_contract_v1 import Exp01CConfigV1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER
from paperworks.validation_v2.exp01_scientific_v1 import SOURCE_VARIABLES, TARGET_VARIABLES
from paperworks.data.hai_xver_normal_v1 import sha256_file
from materialize_xver_normal_v1 import cache_root

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'research_control_center/validation_v2/dg04_xver_prep'
PUBLIC = ROOT/'research_control_center/validation_v2/xver_normal'
BASE = '3a410f5b6aa32ce7aa7547ddc445cf50c1aa347b'


def mapped_context(canonical: tuple, schemas: tuple) -> tuple:
    require(bool(canonical) and len(set(canonical)) == len(canonical), 'CANONICAL_IDENTITY')
    require(bool(schemas), 'SCHEMA_AUTHORITY_MISSING')
    require(all(len(set(s)) == len(s) for s in schemas), 'SCHEMA_DUPLICATE')
    require(all(all(n in s for s in schemas) or all(n not in s for s in schemas)
                for n in canonical), 'SCHEMA_AVAILABILITY_INCONSISTENT')
    return tuple(n for n in canonical if all(n in s for s in schemas))


def frozen(name: str) -> dict:
    path = PARENT/name
    require(path.read_bytes() == subprocess.check_output(
        ['git','show',BASE+':'+path.relative_to(ROOT).as_posix()], cwd=ROOT), 'PARENT_BYTES_CHANGED')
    value = json.loads(path.read_text()); replay(value)
    return value


def main() -> None:
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE,
            'INITIAL_PARENT_HEAD')
    configs = frozen('EXTERNAL_GDN_PREPARATION_PLAN_V2.json')
    for name, expected in configs['code_hashes'].items():
        require(sha256((ROOT/name).read_bytes()).hexdigest() == expected, 'GDN_CODE_CHANGED')
    config = Exp01CConfigV1()
    require(config.to_dict() == configs['architecture_family_config'], 'GDN_CONFIG_CHANGED')
    identities = {}
    for name in ('FINAL_METHOD_LOCK_V1.json','T0_HELDOUT_CANDIDATE_PORTFOLIO_V1.json',
                 'T2_HELDOUT_CANDIDATE_PORTFOLIO_V1.json','STAGE_B_RESUME_STATUS_V2.json'):
        identities[name] = frozen(name)['self_hash']
    canonical = tuple(P1_FEATURE_ORDER)
    authority = seal({'schema':'gdn_canonical_context_authority_v1', 'source_commit':BASE,
        'canonical_context':list(canonical), 'node_count':len(canonical),
        'source_roles':list(SOURCE_VARIABLES), 'target_roles':list(TARGET_VARIABLES),
        'context_only':[n for n in canonical if n not in SOURCE_VARIABLES+TARGET_VARIABLES],
        'order_hash':digest(canonical), 'configuration':config.to_dict(),
        'configuration_hash':config.config_hash, 'implementation_hashes':configs['code_hashes'],
        'role_unit_metadata_numerically_consumed':False,
        'P1_identity_authority':'FROZEN_EXP01C_P1_FEATURE_ORDER',
        'model_node_count':'CONSTRUCTOR_ARGUMENT_LEN_FEATURE_ORDER',
        'trained_weights_transfer_allowed':False, 'scientific_runs':0,
        'parent_authority_hashes':identities})
    publish(PUBLIC/'GDN_CANONICAL_CONTEXT_AUTHORITY_V1.json',authority)
    records = []
    for version in ('22','21'):
        custody = frozen(f'HAI{version}_NORMAL_PROJECTION_RECEIPT_V2.json')
        candidate = frozen(f'HAI{version}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
        schemas = []
        for row in custody['records']:
            replay(row)
            require(sha256_file(cache_root()/'projections_v2'/(row['source_file_identity']+'.csv'))
                    == row['projection_hash'], 'PROJECTION_BYTES_CHANGED')
            require(row['label_values_parsed'] is False and row['label_values_used'] is False
                    and row['label_values_validated'] is False, 'LABEL_CUSTODY')
            schemas.append(tuple(row['projected_feature_identities']+row['excluded_schema_identities']))
        context = mapped_context(canonical,tuple(schemas))
        rows = []
        for i,n in enumerate(canonical):
            role = 'SOURCE' if n in SOURCE_VARIABLES else 'TARGET' if n in TARGET_VARIABLES else 'CONTEXT_ONLY'
            rows.append({'canonical_identity':n,'canonical_order_index':i,
                'external_identity':n if n in context else None,
                'status':'MAPPED_EXACT' if n in context else 'ABSENT', 'role':role,
                'alias':None, 'process':'P1',
                'role_unit_requirement':'NOT_REQUIRED_FOR_CONTEXT_ONLY_GDN' if role=='CONTEXT_ONLY' else 'PARENT_STRICT_ROLE_MAPPING_REQUIRED',
                'datatype_status':'PENDING_CONTEXT_PROJECTION_FINITE_CHECK' if role=='CONTEXT_ONLY' and n in context else 'PARENT_ROLE_PROJECTION_OR_ABSENT',
                'sample_interval_seconds':1,
                'evidence':['FROZEN_EXP01C_P1_FEATURE_ORDER',custody['self_hash']]})
        doc = seal({'schema':'gdn_external_context_mapping_v1','version':custody['version'],
            'canonical_authority_hash':authority['self_hash'], 'source_commit':BASE,
            'parent_custody_hash':custody['self_hash'],'candidate_authority_hash':candidate['self_hash'],
            'context_order':list(context),'context_count':len(context),'feature_order_hash':digest(context),
            'selection_policy':'ORDERED_INTERSECTION_CANONICAL_WITH_EXACT_VERIFIED_SCHEMA',
            'context_status':'FULL_CONTEXT_REPLICATION' if context==canonical else 'SCHEMA_BOUND_PARTIAL_CONTEXT_REPLICATION',
            'rows':rows,'scientific_runs':0,'new_or_replacement_nodes':0,'guessed_aliases':0})
        publish(PUBLIC/f'HAI{version}_GDN_CONTEXT_MAPPING_V1.json',doc)
        records.append({'version':custody['version'],'context_hash':doc['self_hash'],
                        'features':list(context),'parent_projection_hash':custody['self_hash']})
    contract = seal({'schema':'xver_gdn_context_projection_contract_v1','source_commit':BASE,
        'task':'HAI-XVER-NORMAL-PREP-001','records':records,
        'splits':['train1','train2'], 'projection_policy':'TIMESTAMP_PLUS_APPROVED_FEATURE_ALLOWLIST',
        'implementation_hashes':{n:sha256((ROOT/n).read_bytes()).hexdigest() for n in (
            'src/paperworks/data/hai_normal_projection_v2.py','scripts/project_xver_gdn_context_v1.py')},
        'label_values_parsed':False,'label_values_validated':False,'label_values_used':False,
        'provider_calls_allowed':False,'training_authorized_by_this_artifact':False})
    publish(PUBLIC/'GDN_CONTEXT_PROJECTION_CONTRACT_V1.json',contract)
    print(json.dumps({'status':'PARENT_AND_CONTEXT_REPLAY_PASS','canonical':len(canonical),
                      'contexts':{r['version']:len(r['features']) for r in records},'scientific_runs':0}))


if __name__ == '__main__':
    main()
