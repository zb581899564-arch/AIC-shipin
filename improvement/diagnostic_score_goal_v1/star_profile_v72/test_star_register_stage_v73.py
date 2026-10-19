"""Pure synthetic single-scope registration; never start a process/model."""
import copy
import datetime as dt
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import star_register_stage_v73 as reg73


def r(name):
    return dict(path='/synthetic/'+str(name),sha256=hashlib.sha256(str(name).encode()).hexdigest())


class FakeArtifacts:
    root=Path('/synthetic/root')
    def __init__(self): self.docs={};self.read_log=[]
    def code(self,name): return r('code/'+name)
    def load(self,reference): return self.docs[reference['path']]
    def put(self,relative,value):
        reference=r(relative); self.docs[reference['path']]=value; return reference
    def file(self,relative):
        self.read_log.append(relative)
        reference=r(relative); return reference,self.docs[reference['path']]
    def reference(self,relative):
        reference=r(relative); self.docs[reference['path']]; return reference
    def add_terminal(self,phase,scope):
        prefix='star_'+phase+'_'+scope+'_72'
        names=['GPU','output_QA'] if phase=='GPU' else ['reference' if phase=='reference' else 'CPU']
        entries=[]
        for i,name in enumerate(names):
            entry=dict(stage=name,argv=['synthetic','--scope',scope],pid=i+1,start_ticks=str(100+i))
            entries.append(entry); self.put(prefix+'_'+name+'_launch.json',entry)
            self.put(prefix+'_'+name+'_exit.json',dict(entry=entry,actual_exit_code=0))
        self.put(prefix+'_terminal.json',dict(status='REGISTERED_STAR_SCOPE_NATURAL_COMPLETE_EXIT0',exit_code=0,
            phase=phase,scope=scope,entries=entries))


def fixture():
    io=FakeArtifacts()
    common={k:r(k) for k in ('adapter_weights','value_weights','training_completion','star_GPU69_registration','training_quality_admission')}
    common['adapter_weights']=r('adapter1300/adapter_model.safetensors')
    c69={k:r(k) for k in ('image_code','screen_prepared','screen_input_acceptance','policy_code','old_gain_state','old_geometry_control')}
    context=dict(common=common,c69=c69,c68=dict(geometry_code=r('geometry31')),c55=dict(review_code=r('review56')),
        cpu55=dict(old_catalog=r('originalcatalog'),original_targets=r('originaltargets'),old_case_plan=r('originalplan')),
        qa=r('QA70'),recovery_code=r('recovery34'),recovery_receipts=[r('successful35')])
    for scope,count in (('resized20',20),('resized19',19)):
        m='screen' if count==20 else 'confirm'
        for phase,s in (('reference',m),('CPU',scope),('GPU',scope)): io.add_terminal(phase,s)
        catalog=io.put('catalog_'+scope,dict(sources=[dict(source_id=scope+'_'+str(i)) for i in range(count)]))
        io.put('star_profile_reference_72/'+m+'/completion.json',dict(status='COMPLETE_STAR_PROFILE_REFERENCE_METADATA_V72',
            scope=m,sources=count,registration=r('star_reference_registration_72.json'),source_catalog=catalog,
            case_plan=r('plan_'+scope),CPU_targets=r('targets_'+scope)))
        cpu=io.put('star_profile_CPU_registration_72_'+scope+'.json',dict(synthetic=True))
        prep=io.put('star_profile_inputs_72/'+scope+'/prepared.json',dict(schema='STAR_PROFILE_PREPARED_V72',scope=scope,
            sources=count,inference_inputs=[dict(id='a'),dict(id='b')],**{k:common[k] for k in
                ('adapter_weights','value_weights','training_completion','star_GPU69_registration')}))
        io.put('star_profile_inputs_72/'+scope+'/input_acceptance.json',dict(status='PASS_STAR72_NEW_PROFILE_INPUTS_FIRST_CPU_QA',
            registration=cpu,prepared=prep))
        gpureg=io.put('star_GPU_registration_72_'+scope+'.json',dict(adapter_weights=common['adapter_weights'],value_weights=common['value_weights']))
        qa=io.put('star_review_72/'+scope+'/output_acceptance.json',dict(status='PASS_STAR72_FIRST_OUTPUT_QA',scope=scope,
            registration=gpureg,training_completion=common['training_completion']))
        io.put('star_review_72/'+scope+'/result.json',dict(status='PASS_STAR_RESIZED20_PROFILE_ONLY' if count==20 else 'PASS_STAR_RESIZED19_CONFIRM_ONLY',
            scope=scope,primary='UTILITY',quality=dict(admitted=True),fixed_final_checkpoint=True,
            registration=gpureg,output_acceptance=qa,**{k:common[k] for k in
                ('adapter_weights','value_weights','training_completion','star_GPU69_registration')}))
    io.put('star_reference_registration_72.json',{})
    io.put('roi_confirm_inputs_10/C00.json',dict(item_id='gnmc:test:006575.jpeg'))
    for name in ('roi_confirm_inputs_10/prepared.json','roi_confirm_inputs_10/input_acceptance.json',
            'roi_confirm_remaining19_output_acceptance_12.json','roi_confirm_remaining19_GPU_12/completion.json',
            'star_profile_reference_72/screen/native_qualification_binding.json','star_profile_reference_72/screen/old55_STOP_binding.json'):
        io.put(name,dict(synthetic=True))
    return io,context


class RegisterStageTests(unittest.TestCase):
    def build(self,io,c,stage):
        with mock.patch.object(reg73,'bound',side_effect=lambda q:Path(q['path'])), \
             mock.patch.object(reg73,'ref',side_effect=lambda p:r(Path(p).as_posix())):
            return reg73.build_stage(io,c,stage,dict(planned_output_bytes=1000,capacity_reason='explicit measured allocation'))

    def test_first_six_generate_only_one_fixed_phase_and_correct_actual_fields(self):
        io,c=fixture()
        for stage in reg73.FIRST_SIX:
            with self.subTest(stage=stage):
                path,reg,argv=self.build(io,c,stage)
                phase,scope=stage.split('_',1)
                self.assertEqual(argv[argv.index('--phase')+1],phase)
                self.assertEqual(argv[argv.index('--scope')+1],scope)
                self.assertEqual(argv[argv.index('--registration')+1],str(path))
                self.assertEqual(reg['training_completion'],c['common']['training_completion'])
                if phase=='CPU':
                    self.assertEqual(reg['schema'],'STAR_CONDITIONAL_PROFILE_CPU_V72')
                    self.assertEqual(reg['input_code'],c['c69']['image_code'])
                    self.assertEqual(reg['quality_result70'],c['common']['training_quality_admission'])
                    self.assertEqual(reg['max_seconds'],600)
                    self.assertEqual(reg['native_prepared'] is None,scope=='resized19')
                if phase=='GPU':
                    self.assertEqual(reg['schema'],'STAR_FROZEN_PROFILE_INFERENCE_V72')
                    self.assertEqual(reg['model_role'],'UTILITY_STAR_'+scope)
                    self.assertEqual(reg['max_seconds'],900)
                    self.assertEqual(reg['expected_sources'],20 if scope=='resized20' else 19)
                    self.assertEqual(reg['old55_STOP_binding'],r('star_profile_reference_72/screen/old55_STOP_binding.json'))
                    self.assertEqual(len(reg['adopted_output_acceptances']),1 if scope=='resized20' else 2)

    def test_screen_registration_binds_but_does_not_parse_original19(self):
        io,c=fixture(); self.build(io,c,'reference_screen')
        self.assertFalse(any(name.startswith('roi_confirm') for name in io.read_log))

    def test_code_ref_uses_deployed_member_size_and_SHA_without_refreshing_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); file=root/reg73.CODEDIR/'star_identity_v72.py';file.parent.mkdir(parents=True)
            file.write_text('synthetic original',encoding='utf-8')
            deployment=dict(members={'star_profile_v72/star_identity_v72.py':dict(size=file.stat().st_size,sha256=reg73.sha(file))})
            io=reg73.Artifacts(root,deployment); original=io.code(file.name)
            self.assertEqual(original['sha256'],deployment['members']['star_profile_v72/'+file.name]['sha256'])
            file.write_text('synthetic mutation',encoding='utf-8')
            with self.assertRaises(ValueError): io.code(file.name)

    def test_no_confirm_after_STOP_or_incomplete_true_terminal(self):
        io,c=fixture()
        q=io.docs[r('star_review_72/resized20/result.json')['path']]
        q['status']='STOP_STAR_RESIZED20_REJECTED'
        for stage in ('reference_confirm','CPU_resized19','GPU_resized19'):
            with self.subTest(stage=stage), self.assertRaises(ValueError): self.build(io,c,stage)
        io,c=fixture(); t=io.docs[r('star_GPU_resized20_72_output_QA_exit.json')['path']]
        t['actual_exit_code']=1
        with self.assertRaises(ValueError): self.build(io,c,'reference_confirm')

    def test_old55_inputs_or_missing_source_cannot_be_adopted_as_new1300(self):
        for mode in ('model','gate','missing'):
            io,c=fixture()
            if mode=='model': io.docs[r('star_profile_inputs_72/resized20/prepared.json')['path']]['training_completion']=r('old55')
            elif mode=='gate': io.docs[r('star_profile_inputs_72/resized20/input_acceptance.json')['path']]['status']='OLD55_PASS'
            else: io.docs[r('catalog_resized19')['path']]['sources'][0]['source_id']='gnmc:test:006575.jpeg'
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                self.build(io,c,'CPU_resized19' if mode=='missing' else 'GPU_resized20')

    def test_admission_deadline_exact_code_scope_and_no_production_guessing(self):
        io,c=fixture(); now=dt.datetime(2026,10,18,0,0,tzinfo=dt.timezone.utc)
        deployment=dict(status='STAR72_CODE_READY_NO_REAL_SCOPE_ADMITTED',actual_test_exit_code=0,
            code_directory=str(io.root/reg73.CODEDIR))
        admission=dict(schema='STAR_SINGLE_SCOPE_LAUNCH_V73',stage='GPU_resized20',launch_approved=True,
            deadline_utc=reg73.DEADLINE,register_code=r('reg73'),planned_output_bytes=1000,capacity_reason='main current allocation')
        with mock.patch.object(reg73,'bound',return_value=Path(reg73.__file__).resolve()):
            self.assertEqual(reg73.validate_admission(io.root,'GPU_resized20',admission,deployment,now),900)
            for change in (dict(stage='GPU_resized19'),dict(deadline_utc='2099-01-01T00:00:00Z'),dict(launch_approved=False),dict(planned_output_bytes=0)):
                with self.assertRaises(ValueError): reg73.validate_admission(io.root,'GPU_resized20',dict(admission,**change),deployment,now)
            with self.assertRaises(ValueError): reg73.validate_admission(io.root,'GPU_resized20',admission,deployment,
                dt.datetime(2026,10,18,3,10,tzinfo=dt.timezone.utc))
        with mock.patch.object(reg73.subprocess,'Popen',side_effect=AssertionError('No launch in registration tests')):
            for stage in reg73.STAGES[6:]:
                with self.assertRaises(ValueError): self.build(io,c,stage)


if __name__=='__main__': unittest.main()
