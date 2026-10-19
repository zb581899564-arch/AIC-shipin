"""Synthetic production registration/ownership/domain tests; no real launch."""
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import star_register_production_v74 as reg74
from test_star_register_stage_v73 import fixture as external_fixture,r


def fixture():
    io,c=external_fixture()
    pref,p=io.file('star_profile_inputs_72/resized20/prepared.json');p['class_token_ids']=[15,16,17]
    gref,_=io.file('star_profile_inputs_72/resized20/input_acceptance.json')
    _,gpu=io.file('star_GPU_registration_72_resized20.json');gpu.update(prepared=pref,input_acceptance=gref)
    original=dict(c['common'],schema='STAR_PRODUCTION_OBSERVATION_CPU_V72',selection=reg74.SELECTION,protected_baseline=reg74.BASELINE,
        preparation_code=io.code('star_production_prepare_v72.py'),image_code=c['c69']['image_code'])
    origref=io.put('star_production_CPU_registration_72.json',original)
    selected=[dict(source_id='official:0:native:'+str(i),source_sha256='a'*64,observation_index=i*2,native_ordinal=i*3) for i in range(34)]
    ids=[s['source_id'] for s in selected]
    domain=dict(selection=reg74.SELECTION,official_source_count=426,affected_video_count=1,selected_D=selected,
        all_D=[dict(owner=s['source_id']) for s in selected],selected_D_count=34,pilot_source_ids=ids[:32],
        remaining_source_ids=ids[32:],selected_D_sha256=reg74.digest(selected),protected_baseline_sha256=reg74.BASELINE['sha256'])
    domain['all_D_sha256']=reg74.digest(domain['all_D'])
    dref=io.put('star_production_inputs_72/domain.json',domain)
    catalog=io.put('star_production_inputs_72/source_catalog.json',dict(sources=selected))
    plan=io.put('star_production_inputs_72/case_plan.json',dict(GT_used_for_input_or_pair_choice=False))
    proofs=[io.put('proof_'+str(i),dict(status='PASS_STAR72_OBSERVATION_FIRST_CPU_INPUT_QA',source_id=s['source_id'],
        source_metadata_sha256=reg74.digest(s))) for i,s in enumerate(selected[:32])]
    pilot=io.put('star_production_inputs_72/pilot_acceptance.json',dict(status='PASS_STAR72_CPU_CAPACITY_PILOT32_ONLY',
        registration=origref,capacity_only=True,observations=32,production_admitted=False,domain=dref,source_catalog=catalog,
        case_plan=plan,selected_D_sha256=domain['selected_D_sha256'],observation_acceptances=proofs))
    for phase in ('pilot32','remaining'):
        entry=dict(argv=['synthetic','--phase',phase],pid=20,start_ticks='123',CPU_child=True)
        prefix='star_production_'+phase+'_72'
        io.put(prefix+'_terminal.json',dict(status='EXPLICIT_STAR_CPU_NATURAL_COMPLETE_EXIT0',exit_code=0,entry=entry))
        io.put(prefix+'_launch.json',entry);io.put(prefix+'_exit.json',dict(actual_exit_code=0,entry=entry))
    q20=r('star_review_72/resized20/result.json');q19=r('star_review_72/resized19/result.json')
    spatial=reg74.production_admission(c,q20,q19,pilot=False,domain=domain)
    spatialref=io.put('star_production_spatial_admission_74.json',spatial)
    io.put('star_production_remaining_admission_72.json',dict(original_registration=origref,pilot_acceptance=pilot,domain=dref,
        production_admission=spatialref))
    entries=[dict(id=str(i),source_id=selected[i%34]['source_id']) for i in range(68)]
    prep=io.put('star_production_inputs_72/prepared.json',dict(c['common'],schema='STAR_PRODUCTION_PREPARED_V72',scope='production',
        sources=34,official_source_count=426,affected_video_count=1,selection=reg74.SELECTION,source_catalog=catalog,
        case_plan=plan,selected_D_sha256=domain['selected_D_sha256'],CPU_targets=None,inference_inputs=entries,
        execution_entries=entries,adopted_success={},profile='RESIZED_OBSERVATION_PLANE',native_RGB_recovered=False))
    gate=io.put('star_production_inputs_72/input_acceptance.json',dict(status='PASS_STAR72_ALL_SELECTED_OBSERVATIONS_FIRST_CPU_QA',
        prepared=prep,registration=origref,sources=34,scope='production',inference_inputs=68,execution_inputs=68,adopted_successes=0,
        first_independent_crop_processor_QA=True,first_compressed_save_and_reader_roundtrip=True,native_RGB_recovered=False,
        official_source_count=426,affected_video_count=1))
    gpuref=io.put('star_GPU_registration_72_production.json',dict(production_admission=spatialref,profile_quality_admission=q20,
        confirm_quality_admission=q19))
    top=io.put('star_inference_72/production/completion.json',dict(c['common'],status='COMPLETE_STAR_V72_READONLY_SCOPE_NOT_QUALITY',
        GPU_registration=gpuref,prepared=prep,input_acceptance=gate,inventory=dict(pipeline=8790229268),new_optimizer_updates=0))
    qa=io.put('star_review_72/production/output_acceptance.json',dict(c['common'],status='PASS_STAR72_FIRST_OUTPUT_QA',scope='production',
        registration=gpuref,top_completion=top))
    io.put('star_review_72/production/policy.json',dict(output_acceptance=qa,GT_read=False))
    io.add_terminal('GPU','production')
    rules=io.put('new_current_rules',dict(status='PASS_CURRENT_STAR_PACKAGE_RULE_SCOPE'))
    admission=dict(max_seconds=850,max_additional_bytes=1234567,planned_output_bytes=7654321,capacity_reason='main measured after32',
        official_rule_check=rules,historical_canonical_sha256=['b'*64],pilot_acceptance=pilot,domain=dref,
        prepared=prep,input_acceptance=gate,production_output_acceptance=qa)
    return io,c,admission


class ProductionRegistrationTests(unittest.TestCase):
    def build(self,io,c,stage,a):
        with mock.patch.object(reg74,'bound',side_effect=lambda q:Path(q['path'])), \
             mock.patch.object(reg74,'ref',side_effect=lambda p:r(Path(p).as_posix())):
            return reg74.build_stage(io,c,stage,a)

    def test_four_explicit_stages_have_exact_scopes_counts_and_no_auto_remaining(self):
        io,c,a=fixture()
        for stage in reg74.STAGES:
            with self.subTest(stage=stage):
                writes,argv=self.build(io,c,stage,a);reg=writes[-1][1]
                self.assertEqual(len(writes),2 if stage.startswith('CPU_') else 1)
                self.assertEqual(argv.count('--phase'),1)
                if stage=='CPU_pilot32':
                    adm=writes[0][1]
                    self.assertFalse(adm['production_admitted']);self.assertNotIn('expected_sources',adm)
                    self.assertEqual(reg['class_token_ids'],[15,16,17]);self.assertEqual(reg['max_seconds'],600)
                    self.assertEqual(reg['selection'],'OBS_INDEX_EVEN');self.assertEqual(reg['protected_baseline'],reg74.BASELINE)
                elif stage=='CPU_remaining':
                    self.assertEqual(reg['expected_sources'],34);self.assertEqual(reg['official_source_count'],426)
                    self.assertEqual(len(reg['remaining_source_ids']),2)
                    self.assertEqual(reg['max_additional_bytes'],a['max_additional_bytes'])
                    self.assertTrue(writes[0][1]['production_admitted'])
                elif stage=='GPU_production':
                    self.assertEqual(reg['reader_class'],'ProductionInputs');self.assertEqual(reg['expected_sources'],34)
                    self.assertEqual(reg['official_source_count'],426);self.assertEqual(reg['expected_inputs'],68)
                    self.assertEqual(reg['max_seconds'],a['max_seconds']);self.assertEqual(len(reg['adopted_output_acceptances']),3)
                    self.assertEqual(argv[argv.index('--scope')+1],'production')
                else:
                    self.assertEqual(reg['schema'],'STAR_EXACT_OBSERVATION_PACKAGE_V72')
                    self.assertEqual(reg['official_rule_check'],a['official_rule_check'])
                    self.assertEqual(reg['historical_canonical_sha256'],a['historical_canonical_sha256'])

    def test_any_external_scope_STOP_rejects_all_production_before_registration(self):
        for scope in ('resized20','resized19'):
            io,c,a=fixture();io.docs[r('star_review_72/'+scope+'/result.json')['path']]['quality']['admitted']=False
            for stage in reg74.STAGES:
                with self.subTest(scope=scope,stage=stage),self.assertRaises(ValueError):self.build(io,c,stage,a)

    def test_remaining_adopts_exact32_and_does_not_guess_domain_or_repeat_it(self):
        for mode in ('hash','order','proof','exit'):
            io,c,a=fixture()
            if mode=='hash':io.docs[r('star_production_inputs_72/domain.json')['path']]['selected_D_count']=426
            elif mode=='order':io.docs[r('star_production_inputs_72/domain.json')['path']]['remaining_source_ids'].reverse()
            elif mode=='proof':io.docs[r('proof_0')['path']]['source_metadata_sha256']='f'*64
            else:io.docs[r('star_production_pilot32_72_exit.json')['path']]['actual_exit_code']=1
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.build(io,c,'CPU_remaining',a)

    def test_gpu_needs_real_full_input_gate_and_package_needs_new_rules(self):
        io,c,a=fixture();io.docs[r('star_production_inputs_72/input_acceptance.json')['path']]['status']='PASS_STAR72_CPU_CAPACITY_PILOT32_ONLY'
        with self.assertRaises(ValueError):self.build(io,c,'GPU_production',a)
        io,c,a=fixture();io.docs[a['official_rule_check']['path']]['status']='OLD_RULE_PASS'
        with self.assertRaises(ValueError):self.build(io,c,'package',a)
        io,c,a=fixture();io.docs[r('star_inference_72/production/completion.json')['path']]['training_completion']=r('old55')
        with self.assertRaises(ValueError):self.build(io,c,'package',a)

    def test_future_refs_equal_actual_exclusive_saved_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'reference.json';value=dict(status='中文',bool_value=True,nested=dict(a=1))
            expected=reg74.future_ref(path,value);reg74.save(path,value)
            self.assertEqual(expected,reg74.ref(path))

    def test_admission_costs_and_code_identity_are_explicit_and_deadline_fixed(self):
        io,c,a=fixture();now=dt.datetime(2026,10,18,0,0,tzinfo=dt.timezone.utc)
        deployment=dict(status='STAR72_CODE_READY_NO_REAL_SCOPE_ADMITTED',actual_test_exit_code=0,code_directory=str(io.root/reg74.stage73.CODEDIR))
        base=dict(a,schema='STAR_SINGLE_PRODUCTION_STAGE_LAUNCH_V74',launch_approved=True,deadline_utc=reg74.stage73.DEADLINE,
            register_code=r('74'),stage73_code=r('73'))
        def bound(q):return Path(reg74.__file__).resolve() if q==base['register_code'] else Path(reg74.stage73.__file__).resolve()
        with mock.patch.object(reg74,'bound',side_effect=bound):
            for stage in reg74.STAGES:
                self.assertEqual(reg74.validate_admission(io.root,stage,dict(base,stage=stage),deployment,now),600 if stage=='CPU_pilot32' else 850)
            for stage,change in (('CPU_remaining',dict(max_additional_bytes=0)),('GPU_production',dict(planned_output_bytes=0)),
                    ('package',dict(historical_canonical_sha256=['bad'])),('CPU_pilot32',dict(launch_approved=False))):
                with self.subTest(stage=stage),self.assertRaises(ValueError):
                    reg74.validate_admission(io.root,stage,dict(base,stage=stage,**change),deployment,now)


if __name__=='__main__':unittest.main()
