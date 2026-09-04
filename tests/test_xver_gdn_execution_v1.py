import ast
import inspect
from pathlib import Path
import unittest
import numpy as np
from paperworks.validation_v2 import exp03b_gdn_v1 as frozen
from paperworks.validation_v2 import xver_gdn_execution_v1 as adapter
from paperworks.validation_v2.exp03b_contract_v1 import digest
from paperworks.validation_v2.gdn_corr_contract_v1 import Exp01CConfigV1


class ExecutionAdapterTests(unittest.TestCase):
    def test_entire_global_kernel_ast_exact_except_two_replaced_custody_guards(self):
        old=ast.parse(inspect.getsource(frozen.infer)).body[0]
        new=ast.parse(inspect.getsource(adapter._global_core)).body[0]
        filtered=[]
        removed=[]
        for statement in old.body:
            constants={n.value for n in ast.walk(statement) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
            if constants & {'GDN_FEATURE_ORDER','GDN_SPLIT_LENGTH_AUTHORITY'}:
                removed.append(statement)
            else:filtered.append(statement)
        self.assertEqual(len(removed),2)
        self.assertEqual([ast.dump(x) for x in filtered],[ast.dump(x) for x in new.body])

    def test_training_kernel_is_imported_unchanged(self):
        from paperworks.validation_v2.exp01c_backend_v1 import train_exp01c_seed_v1
        self.assertIs(adapter.train_exp01c_seed_v1,train_exp01c_seed_v1)

    def test_run_identity_mutation_fails_before_backend(self):
        expected={'version':'22.04','seed':11}
        for field,value in [('version','21.03'),('seed',23),('projection_hash','b'*64),('source_commit','c'*40)]:
            mutated={**expected,field:value}
            with self.assertRaisesRegex(ValueError,'RUN_IDENTITY'):
                adapter.validate_checkpoint(checkpoint={'run_identity':mutated},identity=expected,matrix=None,feature_order=(),pairs=())

    def test_new_numeric_policy_or_device_rejected(self):
        config=Exp01CConfigV1()
        identity=dict(version='22.04',split='train1',config_hash=config.config_hash,device='cuda',dtype='float32',scaler_policy='TRAIN_ONLY_ROBUST_MEDIAN_IQR')
        for field,value in [('device','cpu'),('dtype','float64'),('scaler_policy','RAW_CURRENT')]:
            bad={**identity,field:value}
            with self.assertRaises(ValueError):
                adapter.validate_checkpoint(checkpoint={'run_identity':bad,'config_hash':config.config_hash},identity=bad,matrix=None,feature_order=(),pairs=())

    def test_aux_source_universe_bound_before_backend(self):
        with self.assertRaisesRegex(ValueError,'AUX_SOURCE_UNIVERSE'):
            adapter.auxiliary_events(identity={'split':'train1','source_universe_hash':digest(('S','OTHER'))},
                checkpoint={},matrix=np.zeros((100,2)),feature_order=('S','OTHER'),pairs=(('S','OTHER'),),sources=('S',))

    def test_aux_cannot_call_numeric_or_hidden_authority(self):
        source=inspect.getsource(adapter.auxiliary_events)
        tree=ast.parse(source)
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertIn('derive_source_screening_parameters_v1',calls)
        self.assertIn('event_validation_starts',calls)
        self.assertFalse(calls & {'roles_from_summary','fixed_roles','pooled_roles','verify','t0','convert','project'})
        self.assertNotIn('train3',source);self.assertNotIn('train4',source)

    def test_no_provider_import_or_old_weight_loader(self):
        source=Path(adapter.__file__).read_text()
        for token in ('openai','load_checkpoint','normal_capability','fit_and_confirm_arbitrary_union','train3','train4'):
            self.assertNotIn(token,source)


if __name__=='__main__':unittest.main()
