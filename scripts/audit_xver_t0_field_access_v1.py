"""Synthetic instrumentation of the unchanged HAI23 T0 field-access contract."""
from dataclasses import asdict
from unittest.mock import patch
from xver_execution_common import ROOT, PUB, document, publish, seal, digest, sha256_file, require, head
from paperworks.validation_v2.exp03b_semantic_v2 import t0, Train1SemanticEvidenceV2
from paperworks.validation_v2.exp03b_contract_v1 import SemanticTupleV1, StructuralTupleEvidenceV1


def main():
    authority=document(PUB/'SEMANTIC_EXECUTION_AUTHORITY_V1.json')
    hashes={p:sha256_file(ROOT/p) for p in ('src/paperworks/validation_v2/exp03b_semantic_v2.py','src/paperworks/validation_v2/exp03b_contract_v1.py')}
    require(all(authority['implementation_hashes'][p]==h for p,h in hashes.items()),'EXACT_FROZEN_T0')
    accesses={cls.__name__:set() for cls in (Train1SemanticEvidenceV2,StructuralTupleEvidenceV1,SemanticTupleV1)}
    outcomes=[]
    for supported in ((),('step_up',),('step_up','step_down')):
        rows=[]
        for sd in ('step_up','step_down'):
            for td in ('increase','decrease'):
                for h in (1,5,10,30,60):
                    semantic=SemanticTupleV1(sd,td,h);good=sd in supported and td=='increase'
                    rows.append(StructuralTupleEvidenceV1(semantic,10 if good else 0,.9 if good else 0.,0.,3.,'EV-'+digest(asdict(semantic))[:24]))
        source,target='SYNTHETIC_SOURCE','SYNTHETIC_TARGET'
        evidence=Train1SemanticEvidenceV2('EXP03B-CAND-'+digest({'source':source,'target':target})[:20],source,target,'a'*64,tuple(rows))
        def getter(cls):
            original=cls.__getattribute__
            def get(obj,name):
                if not name.startswith('__'):accesses[cls.__name__].add(name)
                return original(obj,name)
            return get
        with patch.object(Train1SemanticEvidenceV2,'__getattribute__',getter(Train1SemanticEvidenceV2)),patch.object(StructuralTupleEvidenceV1,'__getattribute__',getter(StructuralTupleEvidenceV1)),patch.object(SemanticTupleV1,'__getattribute__',getter(SemanticTupleV1)):
            proposal=t0(evidence)
        require(len(proposal.rules)==len(supported),'T0_SYNTHETIC_SEMANTICS')
        outcomes.append({'decision':proposal.decision,'rule_count':len(proposal.rules)})
    require(accesses['Train1SemanticEvidenceV2']=={'rows'},'T0_INPUT_FIELD_SET')
    require(accesses['StructuralTupleEvidenceV1']=={'semantic','support','consistency','opposite_consistency','effect','evidence_slice_id','passes','rank'},'T0_STRUCTURAL_FIELD_SET')
    require(accesses['SemanticTupleV1']=={'source_direction','horizon_seconds'},'T0_DIRECT_SEMANTIC_FIELD_SET')
    receipt=seal({'schema':'xver_T0_field_access_receipt_v1','status':'PASS','scope':'SYNTHETIC_INSTRUMENTATION_NOT_SCIENTIFIC_EXECUTION','source_commit':head(),'frozen_implementation_hashes':hashes,'observed_fields':{k:sorted(v) for k,v in accesses.items()},'target_direction':'COPIED_WITH_SELECTED_SEMANTIC_TUPLE_NOT_ADDITIONAL_SCORING','cases':outcomes,'T0_scientific_executions':0,'STAT_consumed':False,'GLOBAL_GDN_consumed':False,'EVENT_GDN_consumed':False,'hidden_authority_consumed':False,'provider_calls':0,'attack_accesses':0})
    publish(PUB/'T0_FIELD_ACCESS_RECEIPT_V1.json',receipt)
    print('T0_FIELD_ACCESS_RECEIPT_PASS')


if __name__=='__main__':main()
