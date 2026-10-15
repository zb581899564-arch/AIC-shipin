"""New prompt binding, real output owner regression and unchanged science gates."""
import copy
import json
from pathlib import Path
import sys
import unittest

import teacher_label as t
import train_student as s
import pilot
from teacher_cpu_tests import fixture, VALIDATOR


class RecipeContracts(unittest.TestCase):
    def test_validation_rules_schema_and_identity_are_byte_identical(self):
        for name in ('validate_teacher.py','select_windows.py','teacher_metadata_20261007.json','teacher_response.schema.json'):
            self.assertEqual(t.sha(t.HERE/'supervision'/name),t.sha(t.HERE.parent/'next_round_v1/supervision'/name))

    def test_new_prompt_binding_survives_preloaded_old_selector(self):
        import select_windows
        original=select_windows.HERE
        try:
            select_windows.HERE=t.HERE.parent/'next_round_v1/supervision'
            validator=t.validator_for(t.HERE.parent)
            self.assertEqual(validator.HERE,t.HERE/'supervision')
            w,o,teacher,r=fixture()
            self.assertIn('保留价值',validator.prompt_for(w,o))
            self.assertEqual(t.sha(t.HERE/'teacher_prompt.txt'),t.sha(validator.HERE/'teacher_prompt.txt'))
            self.assertTrue(validator.make_record(w,o,teacher,json.dumps(r))['sft_eligible'])
        finally:select_windows.HERE=original

    def test_old_prompt_teacher_receipt_cannot_enter_new_recipe(self):
        w,o,teacher,r=fixture()
        old=Path(t.HERE.parent/'next_round_v1/supervision/teacher_prompt.txt').read_text(encoding='utf-8')
        new=VALIDATOR.prompt_for(w,o)
        self.assertNotEqual(old,new)
        teacher['prompt_sha256']=t.text_sha(old)
        self.assertFalse(VALIDATOR.make_record(w,o,teacher,json.dumps(r))['sft_eligible'])

    def test_student_owner_accepts_v5_and_rejects_old_or_external_output(self):
        run=t.HERE.parent
        for path in (t.HERE/'student_01',t.HERE/'student_01/prefix_adapter'):
            self.assertTrue(s.owns(path,run))
        for path in (run/'teacher_student_autopilot_v1/student_01',run/'teacher_student_autopilot_v4/student_01',run/'external/student_01',t.HERE):
            self.assertFalse(s.owns(path,run))
        source=Path(s.__file__).read_text(encoding='utf-8')
        self.assertNotIn('teacher_student_autopilot_v1',source)
        self.assertIn('owns(adapter, run)',source)
        self.assertIn('owns(out, run)',source)

    def test_pilot_selection_is_order_and_label_independent(self):
        train=[{'window_id':f'train{i}','old_label':'positive'} for i in range(128)]
        dev=[{'window_id':f'dev{i}','old_label':'positive'} for i in range(32)]
        chosen=pilot.choose(train,dev)
        self.assertEqual(tuple(map(len,chosen)),(8,4))
        selected=[[r['window_id'] for r in pop] for pop in chosen]
        for r in train+dev:r['old_label']='empty'
        again=pilot.choose(list(reversed(train)),list(reversed(dev)))
        self.assertEqual(selected,[[r['window_id'] for r in pop] for pop in again])

    def records(self):
        result=[]
        for i in range(12):
            w,o,teacher,response=fixture('train' if i<8 else 'dev',f'synthetic_pilot_{i}')
            result.append(VALIDATOR.make_record(w,o,teacher,json.dumps(response)))
        return result

    def test_all_positive_all_empty_invalid_and_whole_window_pilots_stop(self):
        records=self.records()
        self.assertTrue(any('empty' in reason for reason in pilot.gate(records)))
        empty=copy.deepcopy(records)
        for r in empty:r.update(retained_segments=[],explicit_no_highlight=True)
        self.assertTrue(any('positive' in reason for reason in pilot.gate(empty)))
        invalid=copy.deepcopy(records);invalid[0]['status']='INVALID_TEACHER_OR_INPUT_RECEIPT'
        self.assertTrue(any('invalid' in reason for reason in pilot.gate(invalid)))
        whole=copy.deepcopy(records)
        for r in whole:r['retained_segments']=[{'start_sec':0,'end_sec':r['window']['window_duration_sec']}]
        self.assertTrue(any('whole window' in reason for reason in pilot.gate(whole)))

    def test_diverse_pilot_is_not_full_student_admission(self):
        records=self.records()
        records[0].update(retained_segments=[],explicit_no_highlight=True)
        self.assertEqual(pilot.gate(records),[])
        reasons,_=t.semantic_audit(records,VALIDATOR.summarize(records))
        self.assertTrue(any('dev lacks real justified explicit-empty' in r for r in reasons))
        self.assertTrue(any('20-update' in r for r in reasons))

    def test_new_review_prompt_can_reject_and_does_not_require_every_action(self):
        record=self.records()[0]
        prompt=t.review_prompt(record)
        self.assertIn('能描述活动不等于有保留价值',prompt)
        self.assertIn('uncertain=true',prompt)
        review={'window_id':record['window_id'],'observation_scope':record['parsed_answer']['observation_scope'],
            'semantics_consistent':False,'uncertain':True,'reason':'Synthetic rejection only','issues':['Unsupported value']}
        with self.assertRaises(ValueError):t.review_response(json.dumps(review),record,VALIDATOR)

    def test_cross_recipe_resume_manifest_is_empty(self):
        self.assertEqual(t.read(t.HERE/'accepted_resume_manifest.json')['accepted'],{})
        self.assertNotIn('cached = reuse_accepted',Path(t.__file__).read_text(encoding='utf-8'))


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(RecipeContracts)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'PASS_V5_RECIPE_CPU_CONTRACTS' if result.wasSuccessful() else 'STOP_V5_RECIPE_CPU_CONTRACTS',
        'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'GPU_used':False,'synthetic_fixtures_never_training_labels':True,'real_semantic_quality_pending':True}
    if result.wasSuccessful():t.save(t.HERE/'recipe_cpu_acceptance.json',report,fresh=True)
    print(json.dumps(report));raise SystemExit(0 if result.wasSuccessful() else 1)
