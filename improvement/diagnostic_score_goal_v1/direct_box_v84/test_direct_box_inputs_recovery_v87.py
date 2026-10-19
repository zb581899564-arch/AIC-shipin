import copy
import math
from pathlib import Path
import struct
import unittest
from unittest import mock
import direct_box_inputs_recovery_v87 as recovery


class RecoveryTests(unittest.TestCase):
    def test_nine_roundoff_patterns_including_actual_examples_and_3k_scale(self):
        rows=[(1.0399999999999998,498.96000000000004,500),(5.42025,219.57975000000002,225)]
        for start,limit in ((.1,500),(1.04,3000),(123.456,3000),(5.42025,225),(.001,3072),(9.9,1080),(17.125,2160)):
            rows.append((start,math.nextafter(limit-start,math.inf),limit))
        self.assertEqual(len(rows),9)
        for start,size,limit in rows:
            certificate=recovery.bound_numeric(start,size,limit)
            self.assertLessEqual(certificate['overflow'],sum(certificate['ulp_terms']))
            self.assertTrue(certificate['original_values_unchanged'])

    def test_real_1e_minus10_and_point001_overflows_not_admitted(self):
        for limit in (225,500,3000,3072):
            for excess in (1e-10,.001):
                with self.assertRaises(ValueError):recovery.bound_numeric(1.,limit-1.+excess,limit)
        for terms in ((-1e-20,5.,10),(0.,0.,10),(0.,float('nan'),10)):
            with self.assertRaises(ValueError):recovery.bound_numeric(*terms)

    def test_original_xywh_float_bits_and_non16aspect_remain_unchanged(self):
        original=[1.0399999999999998,0.,498.96000000000004,200.125]
        before=b''.join(struct.pack('>d',v) for v in original)
        proof=recovery.native_reference_ulp_certificate(original,500,225)
        self.assertTrue(proof['x_endpoint']['rounding_only_overflow'])
        self.assertFalse(proof['fixed_epsilon_used']);self.assertFalse(proof['original_reference_modified'])
        self.assertEqual(before,b''.join(struct.pack('>d',v) for v in original))

    def test_failed_registration_cli_binding_and_no_existing_success_output(self):
        root=Path('/home/inspur/aic_video_work/synthetic87').resolve()
        def r(name):return dict(path=str(root/name),sha256='a'*64)
        oldref=r('direct_box_CPU_registration_84.json');exitref=r('direct_box_CPU_85_exit.json');code=r('direct_box_inputs_v84.py')
        diagnosis=r('direct_box_CPU_metadata_failure_diagnosis_87.json');diagnosis['sha256']='9789bddca6e3811e6b8d18052938739bfabd1f557e263028360b2d6ca1029256'
        old=dict(schema=recovery.CPU_SCHEMA,preparation_code=code,input_code=code,max_seconds=600)
        reg=dict(old,preparation_code=r('direct_box_inputs_recovery_v87.py'),input_code=r('direct_box_inputs_recovery_v87.py'),
            original_failed_registration=oldref,original_failed_exit=exitref,failure_diagnosis=diagnosis)
        entry=dict(CPU_child=True,argv=['python','-B','-u',code['path'],'--root',str(root)])
        execution=r('direct_box_execution_registration_CPU_85.json')
        objects={oldref['path']:old,exitref['path']:dict(actual_exit_code=1,entry=entry),
            str(root/'direct_box_CPU_85_failure.json'):dict(entry=entry,registration=execution),
            execution['path']:dict(science_registration=oldref,child_code=code)}
        def read(path):return objects[str(path)]
        with mock.patch.object(recovery,'bound',side_effect=lambda v:Path(v['path'])),mock.patch.object(recovery,'read',side_effect=read),mock.patch.object(Path,'exists',return_value=False):
            self.assertTrue(recovery.validate_failed84(root,reg)['old_failure_preserved'])
            bad=copy.deepcopy(reg);bad['max_seconds']=900
            with self.assertRaises(ValueError):recovery.validate_failed84(root,bad)
            with mock.patch.object(Path,'exists',return_value=True):
                with self.assertRaises(ValueError):recovery.validate_failed84(root,reg)


if __name__=='__main__':unittest.main()
