"""Synthetic-only run receipt closure; no scientific artifacts are opened."""
import copy
import unittest
from unittest.mock import patch
import xver_result_integrity_v1 as integrity


class ResultIntegrityTests(unittest.TestCase):
    def records(self):
        return {(s,k):dict(version='22.04',split=s,seed=k,status='PASS',scope='SCIENTIFIC',authority_hash='a'*64,node_count=36,candidate_count=29,global_row_count=145,auxiliary_row_count=290,provider_calls=0,credential_reads=0,attack_accesses=0,raw_timestamp_overlap=0,excluded_label_values_parsed=False,global_auxiliary_fused=False,run_identity_hash=f'{s}-{k}') for s in ('train1','train2') for k in (11,23,37)}

    def replay(self, rows):
        def document(path):
            name=path.name
            if name=='GDN_EXECUTION_AUTHORITY_V2.json':return {'self_hash':'a'*64}
            if 'CONTEXT_MAPPING' in name:return {'context_count':36}
            if 'META_STAT' in name:return {'candidate_count':29}
            return copy.deepcopy(rows[next((s,k) for s,k in rows if s.upper() in name and f'SEED{k}_' in name)])
        with patch.object(integrity,'document',side_effect=document):return integrity.scientific_receipts('22.04')

    def test_all_exact_slots(self):self.assertEqual(len(self.replay(self.records())),6)

    def test_misfiled_duplicate_and_unsafe_receipts_rejected(self):
        for field,value in [('version','21.03'),('split','train2'),('seed',23),('authority_hash','b'*64),('node_count',30),('candidate_count',28),('global_row_count',144),('auxiliary_row_count',289),('provider_calls',1),('excluded_label_values_parsed',True),('global_auxiliary_fused',True),('run_identity_hash','train2-11')]:
            with self.subTest(field=field):
                rows=self.records();rows['train1',11][field]=value
                with self.assertRaises(ValueError):self.replay(rows)


if __name__=='__main__':unittest.main()
