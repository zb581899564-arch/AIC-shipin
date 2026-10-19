import copy
from pathlib import Path
import unittest
import direct_box_scope_inputs_v95 as scope


def fixture():
    identity=dict(training_completion={'path':'/93/completion','sha256':'a'*64},adapter_weights={'path':'/93/adapter','sha256':'b'*64},head_weights={'path':'/93/head','sha256':'c'*64})
    native={'path':'/93/quality','sha256':'d'*64};confirm={'path':'/95/confirm','sha256':'e'*64}
    reg=dict(identity,admitted_arm_names=['DIRECT'],native20_quality_result=native,confirm19_quality_result=confirm)
    q=dict(identity,status='PASS_DIRECT_BOX93_NATIVE20_QUALIFIED_ARMS',admitted_arm_names=['DIRECT','ANCHORED_HALF'],result=native)
    return reg,q


class IdentityTests(unittest.TestCase):
    def test_only_actual_new93_native_summary_and_exact_model_can_qualify(self):
        reg,q=fixture();scope.validate_native93_summary(reg,q)
        for status in ('PASS_DIRECT_BOX84_NATIVE20_QUALIFIED_ARMS','PASS_STAR_NATIVE20_ONLY','STOP_DIRECT_BOX93_NATIVE20_QUALIFIED_ARMS'):
            bad=copy.deepcopy(q);bad['status']=status
            with self.assertRaises(ValueError):scope.validate_native93_summary(reg,bad)
        bad=copy.deepcopy(q);bad['head_weights']['sha256']='0'*64
        with self.assertRaises(ValueError):scope.validate_native93_summary(reg,bad)

    def test_only_new95_confirm_summary_and_exact_rich_result(self):
        reg,q=fixture();q.update(status='PASS_DIRECT_BOX95_CONFIRM19_QUALIFIED_ARMS',result=reg['confirm19_quality_result'])
        scope.validate_confirm95_summary(reg,q)
        q['status']='PASS_DIRECT_BOX89_CONFIRM19_QUALIFIED_ARMS'
        with self.assertRaises(ValueError):scope.validate_confirm95_summary(reg,q)
        q.update(status='PASS_DIRECT_BOX95_CONFIRM19_QUALIFIED_ARMS',result=reg['native20_quality_result'])
        with self.assertRaises(ValueError):scope.validate_confirm95_summary(reg,q)

    def test_new_scope_namespaces_cannot_resolve_old86_outputs(self):
        root=Path('/explicit/root')
        for phase in ('confirm19','formal'):
            paths=scope.scope_paths(root,phase)
            self.assertEqual(paths['registration'],root/('direct_box_scope_CPU_registration_95_'+phase+'.json'))
            self.assertEqual(paths['output'],root/'direct_box_scope_inputs_95'/phase)
            self.assertEqual(paths['remaining'],root/'direct_box_scope_remaining_admission_95_formal.json')
        self.assertEqual(scope.SCHEMA,'DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V95')
        self.assertEqual(scope.GATE,'PASS_DIRECT_BOX95_SOURCE_ONLY_FIRST_CPU_QA')
        with self.assertRaises(ValueError):scope.scope_paths(root,'screen20')

    def test_arm_subset_has_no_new_unqualified_arm(self):
        reg,q=fixture();scope.validate_native93_summary(reg,q)
        reg['admitted_arm_names']=['UNREGISTERED']
        with self.assertRaises(ValueError):scope.validate_native93_summary(reg,q)


if __name__=='__main__':unittest.main()
