"""Official hypothetical + local synthetic conformance; no real data reader."""
from pathlib import Path
from hashlib import sha256
import importlib.metadata
import json
import platform
import random
import sys
import time
from paperworks.validation_v2.etapr_exchange_v1 import PIN, OfficialEtaprV1, EtaprFileExchangeV1
from paperworks.validation_v2.evaluation_expansion_v1 import binary_stream_to_closed_ranges_v1
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/dg04_xver_prep'


def main():
    source=ROOT/'artifacts/validation_v2/dg04_xver_prep/metric_source'/PIN
    dependencies=ROOT/'artifacts/validation_v2/dg04_xver_prep/metric_dependencies'
    source_receipt=json.loads((PUB/'ETAPR_SOURCE_RECEIPT_V1.json').read_text());replay(source_receipt)
    for record in source_receipt['files']:
        if sha256((source/record['path']).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('SOURCE_OR_HYPOTHETICAL_FIXTURE_MISMATCH')
    sys.path[:0]=[str(source),str(dependencies)]
    wrapper=OfficialEtaprV1(source)
    from eTaPR_pkg import etapr
    from eTaPR_pkg.DataManage import File_IO,Range
    import cv2,numpy,pandas
    rows=[]

    def compare(identity, count, reference, prediction):
        exchange=EtaprFileExchangeV1(identity,count,tuple(reference),tuple(prediction))
        before=time.perf_counter()
        actual=wrapper.score_file(exchange)
        elapsed=time.perf_counter()-before
        official=etapr.evaluate_w_ranges([Range.Range(a,b,str(i)) for i,(a,b) in enumerate(reference)],
                                        [Range.Range(a,b,str(i)) for i,(a,b) in enumerate(prediction)],
                                        theta_p=.5,theta_r=.1,delta=0.0)
        expected=(float(official['eTaP']),float(official['eTaR']),float(official['f1']))
        if (actual['eTaP'],actual['eTaR'],actual['F1'])!=expected or wrapper.score_file(exchange)!=actual:
            raise ValueError('OFFICIAL_WRAPPER_OR_REPLAY_MISMATCH')
        rows.append({'fixture':identity,'reference_range_count':len(reference),'prediction_range_count':len(prediction),
                     'exact_equality':True,'deterministic_replay':True,'wrapper_seconds':elapsed})

    hypothetical=source/'Sample_Data/Hypothetical_Data'
    # Official stream loader freezes normal=1, anomaly=-1 for these fixtures.
    reference=File_IO.load_file(str(hypothetical/'hyp1_anomalies.csv'),'stream')
    reference=[tuple(r.get_time()) for r in reference]
    for suffix in ('25K','50K','75K','100K'):
        predictions=File_IO.load_file(str(hypothetical/f'hyp_predictions_alpha_{suffix}.csv'),'stream')
        predictions=[tuple(r.get_time()) for r in predictions]
        compare('OFFICIAL_HYPOTHETICAL_'+suffix,max(reference[-1][1],predictions[-1][1])+1,reference,predictions)
    for identity,reference,prediction in (
        ('PERFECT',((0,0),(2,4)),((0,0),(2,4))),
        ('MISS',((0,1),),((4,5),)),
        ('CLOSED_ENDPOINT',((2,4),),((4,4),)),
        ('PARTIAL',((2,8),),((1,4),(7,9))),
        ('MULTIPLE',((1,3),(5,8)),((0,2),(4,7)))):
        compare('LOCAL_'+identity,10,reference,prediction)
    rng=random.Random(11)
    for index in range(100):
        streams=[[rng.random()<.25 for _ in range(200)] for _ in range(2)]
        ranges=[tuple((a,b) for a,b,_ in binary_stream_to_closed_ranges_v1(s,file_id='SYNTHETIC')) for s in streams]
        compare(f'LOCAL_RANDOM_{index}',200,*ranges)
    empty=wrapper.score_file(EtaprFileExchangeV1('EMPTY_SYNTHETIC',10,(),()))
    assert empty['status']=='UNDEFINED_EMPTY_RANGE_INPUT' and empty['F1'] is None
    batch=wrapper.score_files([EtaprFileExchangeV1('A',3,((0,0),),((2,2),)),
                               EtaprFileExchangeV1('B',3,((2,2),),((0,0),))])
    assert all(f['F1']==0 for f in batch['files']) and batch['pooled_metric'] is None
    environment={'python':platform.python_version(),'numpy':numpy.__version__,'pandas':pandas.__version__,
                 'opencv':cv2.__version__,'opencv_distribution':importlib.metadata.version('opencv-python-headless'),
                 'installation':'SEPARATE_METRIC_DEPENDENCY_TARGET_FROZEN_SCIENTIFIC_ENV_UNCHANGED'}
    receipt=seal({'schema':'etapr_per_file_conformance_receipt_v1','status':'PER_FILE_CONFORMANCE_PASS',
        'source_receipt_hash':source_receipt['self_hash'],'source_commit':PIN,'environment':environment,
        'wrapper_sha256':sha256((ROOT/'src/paperworks/validation_v2/etapr_exchange_v1.py').read_bytes()).hexdigest(),
        'test_script_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'parameters':{'theta_p':.5,'theta_r':.1,'delta':0.0},
        'official_hypothetical_cases':4,'local_nonempty_cases':105,'cases':rows,
        'empty_policy':'EXPLICITLY_UNDEFINED_PENDING_SCIENTIFIC_CONTRACT','file_isolation':'PASS',
        'interval_inclusivity':'CLOSED','point_adjustment_used':False,
        'upstream_test_oracle_note':'Official helper also calculates ancillary point-adjust outputs; these are neither selected nor reported. Wrapper calls eTaP/eTaR only.',
        'multi_file_aggregation':'UNRESOLVED_NOT_EXECUTED','P1_secondary_range_scope':'UNRESOLVED',
        'real_attack_or_label_files_accessed':0,'provider_calls':0})
    publish(PUB/'ETAPR_CONFORMANCE_RECEIPT_V2.json',receipt)
    print(json.dumps({'status':receipt['status'],'exact_cases':len(rows),'file_isolation':'PASS','hash':receipt['self_hash']}))


if __name__=='__main__':main()
