"""Actual production functions with scoped CPU media/model boundaries mocked.

Synthetic weight/source/inference receipts here are never runtime admission.
The real original structural validator and independent subprocess run unchanged.
"""
import copy
from contextlib import ExitStack
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import boundary_ids as b
import teacher_label as t
import pilot
import visual_interface_probe as visual


OFFICIAL_WEIGHTS=[('Qwen3VL-32B-Instruct-Q4_K_M.gguf','5cf0136e721d6294718ec71fd8c93b17ab5dd4e2714d6079e83fa46571ad94c8'),
    ('mmproj-Qwen3VL-32B-Instruct-F16.gguf','8617824839df91f84b4840ad5084dcf50a1403a435a1f4cfc4d8c84ce6cac2fc')]


def window(split,index):
    identity=('t' if split=='train' else 'd')+str(index).zfill(3)
    return {'schema':'aic_complete_window_selection_v1','split':split,'window_id':identity,
        'source_group':identity,'youtube_id':identity,'source_path':'/home/inspur/aic_video_data/videos/cpu/'+identity+'.mp4',
        'source_sha256':'a'*64,'clock_sequence_sha256':'b'*64,'window_pts_start_sec':10.25,
        'window_pts_end_exclusive_sec':40.25,'window_duration_sec':30.0,
        'planned_actual_pts_sec':[10.25,25.25,40.0],'planned_source_frame_ordinals':[100,400,695],
        'first_eligible_pts_sec':10.25,'last_eligible_pts_sec':40.0,'structural_stratum':'source_beginning'}


class Harness:
    def __init__(self,root):
        self.root=Path(root);self.calls=[];self.bad_answer=False;self.disagree=set();self.empty_ids={'d001'};self.whole=False
        for name in ('teacher_prompt.txt','review_prompt.txt'):
            (self.root/name).write_bytes((t.HERE/name).read_bytes())
        self.real_sha=t.sha;self.real_run=subprocess.run
        self.validator=t.validator_for(t.HERE.parent)
        self.train=[window('train',i) for i in range(128)];self.dev=[window('dev',i) for i in range(32)]
        self.selection=self.root/'selection';self.selection.mkdir()
        for split,values in (('train',self.train),('dev',self.dev)):
            t.save_rows(self.selection/f'selected_{split}.jsonl',values)
        receipt={'status':'PASS_CPU_SELECTION_UNLABELLED','confirm_opened':False,'contest_assets_opened':False,
            'files':{name:self.real_sha(self.selection/name) for name in ('selected_train.jsonl','selected_dev.jsonl')}}
        t.save(self.selection/'selection_receipt.json',receipt,fresh=True)
        weights=[]
        for name,digest in OFFICIAL_WEIGHTS:
            path=self.root/name;path.write_bytes(b'SYNTHETIC_CPU_WEIGHT_IO_FIXTURE_ONLY')
            weights.append({'path':path.as_posix(),'sha256':digest,'bytes':path.stat().st_size})
        self.admission={'status':'ADMITTED_PENDING_REAL_TEACHER_PROBE','base_model_id':t.BASE_ID,'model_id':t.TEACHER_ID,
            'model_revision':t.TEACHER_REVISION,'runtime_revision':t.RUNTIME_REVISION,'production_test_access':False,
            'job_source_lock_sha256':'e'*64,'weight_files':weights,'max_sequence_length':65536,'max_pixels_per_frame':786432,
            'image_min_tokens':1,'image_max_tokens':768,'server_url':'http://127.0.0.1:8080'}
        t.save(self.root/'teacher_admission.json',self.admission,fresh=True)
        small=self.root/'pilot_selection';small.mkdir()
        for split,values in (('train',self.train[:16]),('dev',self.dev[:8])):
            t.save_rows(small/f'selected_{split}.jsonl',values)
        tiny={**receipt,'files':{name:self.real_sha(small/name) for name in ('selected_train.jsonl','selected_dev.jsonl')}}
        t.save(small/'selection_receipt.json',tiny,fresh=True)
        t.save(small/'manifest.json',{'counts':{'train':16,'dev':8},'window_ids':[w['window_id'] for w in self.train[:16]+self.dev[:8]],
            'selection_receipt_sha256':self.real_sha(small/'selection_receipt.json'),'no_label_access':True},fresh=True)
        config={'selection_dir':str(self.selection),'ffprobe_path':'SYNTHETIC_FFPROBE_CPU_ONLY'}
        t.save(self.root/'config.json',config,fresh=True)
        t.save(self.root/'source_lock.json',{'files':{str(self.root/'config.json'):self.real_sha(self.root/'config.json')}},fresh=True)
        self.out=self.root/'teacher_01';self.out.mkdir()
        self.args=SimpleNamespace(run_dir=t.HERE.parent,out_dir=self.out,selected_train=self.selection/'selected_train.jsonl',
            selected_dev=self.selection/'selected_dev.jsonl',selection_receipt=self.selection/'selection_receipt.json',
            phase='probe',ffprobe=config['ffprobe_path'],request_timeout=20)

    def sha(self,path):
        normalized=Path(path).as_posix()
        if normalized.startswith('/home/inspur/aic_video_data/videos/'):return 'a'*64
        for weight in self.admission['weight_files']:
            if Path(path)==Path(weight['path']):return weight['sha256']
        return self.real_sha(path)

    def process(self,args,**kwargs):
        if args[0]=='SYNTHETIC_FFPROBE_CPU_ONLY':
            return SimpleNamespace(stdout=json.dumps({'streams':[{'width':32,'height':32}]}),returncode=0)
        return self.real_run(args,**kwargs)

    def decode(self,w,out,validator,**kwargs):
        from PIL import Image
        import numpy as np
        validator.validate_window(w)
        out=Path(out);(out/'frames').mkdir()
        files=[];pixels=[]
        for i,ordinal in enumerate(w['planned_source_frame_ordinals']):
            image=Image.new('RGB',(32,32),(i*40,60,80));path=out/'frames'/f'{ordinal}.png';image.save(path)
            pixel=hashlib.sha256(np.asarray(image).tobytes()).hexdigest();pixels.append(pixel)
            files.append({'path':str(path),'sha256':self.real_sha(path),'pixel_sha256':pixel,'source_frame_ordinal':ordinal})
        observation={**{k:w[k] for k in ('window_id','source_path','source_sha256','clock_sequence_sha256',
            'window_pts_start_sec','window_pts_end_exclusive_sec','window_duration_sec')},
            'decode_status':'PASS_REAL_SEQUENTIAL_DECODE','pixel_identity_status':'PASS','all_planned_frames_delivered':True,
            'source_frame_ordinals':w['planned_source_frame_ordinals'],'actual_pts_sec':w['planned_actual_pts_sec'],
            'frame_pixel_sha256':pixels,'max_frames':64,'frame_files':files,
            'teacher_modality':'SYNTHETIC_CPU_ONLY_NOT_REAL_VIDEO','source_total_frames':1000,
            'fps_num':20,'fps_den':1,'width':32,'height':32}
        t.save(out/'decode_receipt.json',observation,fresh=True)
        return observation

    def infer(self,server_url,prompt,observation,schema,admission,out,timeout):
        out=Path(out);self.calls.append((observation['window_id'],'review' if out.parent.name=='reviews' else 'label'))
        t.frame_content(observation) # Actual lossless pixel and file-SHA checks.
        identity=observation['window_id']
        unknown=identity=='t001'
        empty=identity in self.empty_ids
        value={'state':'UNKNOWN' if unknown else ('NO_HIGHLIGHT' if empty else 'KEEP'),
            'segments':[] if unknown or empty else [{'start_boundary_id':0,'end_boundary_id':3 if self.whole else 1}],
            'evidence_frame_ids':[0],'reason':'Synthetic CPU evidence only; not a real visual-quality result'}
        if identity in self.disagree and out.parent.name=='reviews':
            value.update(state='UNKNOWN',segments=[])
        if self.bad_answer:value['segments']=[{'start_boundary_id':2,'end_boundary_id':1}]
        answer=json.dumps(value,ensure_ascii=False)
        (out/'raw_answer.txt').write_text(answer,encoding='utf-8')
        t.save(out/'server_response.json',{'synthetic_cpu':True,'answer':answer},fresh=True)
        (out/'http').mkdir()
        t.save(out/'http/request.json',{'synthetic_cpu':True,'prompt':prompt},fresh=True)
        (out/'http/response.bin').write_bytes(answer.encode())
        t.save(out/'http/http_receipt.json',{'synthetic_cpu':True},fresh=True)
        t.save(out/'input_contract.json',{'synthetic_cpu':True,'pixels':observation['frame_pixel_sha256'],'prompt':prompt},fresh=True)
        generated,constraints,relation=t.generation_constraints(schema,observation)
        t.save(out/'generation_schema.json',generated,fresh=True)
        if relation is not None:
            t.save_exact_text(out/'generation_grammar.gbnf',constraints['grammar'])
            t.save(out/'generation_relation_contract.json',relation,fresh=True)
        t.save(out/'runtime_grammar_validation.json',{'synthetic_cpu':True},fresh=True)
        (out/'processor.log').write_text('SYNTHETIC_CPU_BOUNDARY_MOCK',encoding='utf-8')
        measured={'input_contract_sha256':self.real_sha(out/'input_contract.json'),
            'actual_processed_pixels_per_frame':[1024]*len(observation['actual_pts_sec']),
            'max_pixels_per_frame':786432,'max_sequence_length':65536,'input_sequence_length':2000,
            'processor_log_sha256':self.real_sha(out/'processor.log'),'server_response_sha256':self.real_sha(out/'server_response.json')}
        return answer,measured

    def mocks(self):
        stack=ExitStack()
        stack.enter_context(patch.object(t,'sha',side_effect=self.sha))
        stack.enter_context(patch.object(t,'decode_window',side_effect=self.decode))
        stack.enter_context(patch.object(t,'inference',side_effect=self.infer))
        stack.enter_context(patch.object(t.subprocess,'run',side_effect=self.process))
        stack.enter_context(patch.object(pilot.c,'HERE',self.root))
        stack.enter_context(patch.object(pilot.c,'RUN',t.HERE.parent))
        stack.enter_context(patch.object(pilot.socket,'gethostname',return_value='inspur-NP5570M5'))
        process=SimpleNamespace(pid=1234,returncode=0,poll=lambda:0)
        stack.enter_context(patch.object(t,'start_server',return_value=(process,self.admission)))
        return stack

    def phase(self,phase):
        self.args.phase=phase
        t.execute_phase(self.args,self.train,self.dev,self.validator,self.admission,self.admission['server_url'])


class BoundaryContracts(unittest.TestCase):
    def observation(self):
        return {'window_id':'precision','window_pts_start_sec':139.514375,'window_duration_sec':30.0,
            'window_pts_end_exclusive_sec':169.514375,'actual_pts_sec':[139.514375,151.37783333333334,169.499],
            'source_frame_ordinals':[0,237,599]}

    def test_precision_is_program_owned_and_terminal_has_no_frame(self):
        observation=self.observation();table=b.tables(observation)
        self.assertEqual(Fraction(table['boundary_ids'][1]['local_seconds_fraction']),
            Fraction(str(observation['actual_pts_sec'][1]))-Fraction(str(observation['window_pts_start_sec'])))
        self.assertTrue(table['boundary_ids'][-1]['terminal_without_frame'])
        self.assertEqual(table['boundary_ids'][-1]['evidence_frame_ids'],[])
        value={'state':'KEEP','segments':[{'start_boundary_id':2,'end_boundary_id':3}],
            'evidence_frame_ids':[2],'reason':'CPU terminal interval'}
        canonical=b.canonical_response(value,observation)
        self.assertEqual(canonical['retained_segments'][0]['end_sec'],30.0)
        value['evidence_frame_ids']=[3]
        with self.assertRaisesRegex(ValueError,'physical evidence'):b.validate_decision(value,observation)

    def test_unknown_never_projects_to_a_negative(self):
        canonical=b.canonical_response({'state':'UNKNOWN','segments':[],'evidence_frame_ids':[1],'reason':'cannot tell'},self.observation())
        self.assertTrue(canonical['uncertain']);self.assertFalse(canonical['explicit_no_highlight'])
        empty=b.canonical_response({'state':'NO_HIGHLIGHT','segments':[],'evidence_frame_ids':[0,1,2],
            'reason':'explicit sampled-window ordinary background'},self.observation())
        self.assertTrue(empty['explicit_no_highlight']);self.assertFalse(empty['uncertain'])

    def test_exact_raw_text_crlf_and_duplicate_write_preserved(self):
        with tempfile.TemporaryDirectory(prefix='aic_exact_raw_cpu_') as folder:
            path=Path(folder)/'raw.txt';raw='line1\r\nline2\n'
            t.save_exact_text(path,raw)
            self.assertEqual(path.read_bytes(),raw.encode('utf-8'))
            with self.assertRaises(FileExistsError):t.save_exact_text(path,'replacement')
            self.assertEqual(path.read_bytes(),raw.encode('utf-8'))

    def test_order_overlap_missing_evidence_and_float_ids_reject(self):
        base={'state':'KEEP','segments':[{'start_boundary_id':0,'end_boundary_id':1}],
            'evidence_frame_ids':[0],'reason':'synthetic'}
        for change in ({'segments':[{'start_boundary_id':1,'end_boundary_id':0}]},
            {'evidence_frame_ids':[2]},{'segments':[{'start_boundary_id':0.0,'end_boundary_id':1}]},
            {'segments':[{'start_boundary_id':0,'end_boundary_id':2},{'start_boundary_id':1,'end_boundary_id':3}]}):
            with self.assertRaises(ValueError):b.validate_decision({**base,**change},self.observation())

    def test_visual64_images_change_order_without_training_labels(self):
        from PIL import Image
        with tempfile.TemporaryDirectory(prefix='aic_visual_cpu_') as folder:
            plans=visual.case_plan()[-2:]
            first,expected=visual.make_case(plans[0],Path(folder)/'forward')
            second,reversed_expected=visual.make_case(plans[1],Path(folder)/'reverse')
            self.assertEqual(expected,[63]);self.assertEqual(reversed_expected,[0])
            self.assertEqual(first['frame_pixel_sha256'],list(reversed(second['frame_pixel_sha256'])))
            self.assertEqual(len(first['actual_pts_sec']),64)
            self.assertTrue(second['synthetic_never_training_labels'])
            self.assertEqual(Image.open(second['frame_files'][0]['path']).getpixel((128,128)),(240,10,10))

    def test_actual_probe_pilot24_all_review_chain_counts_and_immutable_bytes(self):
        with tempfile.TemporaryDirectory(prefix='aic_teacher_chain_cpu_') as folder:
            h=Harness(folder);h.disagree={'t002'};h.empty_ids=set()
            with h.mocks():
                h.phase('probe');self.assertEqual(len(h.calls),2)
                probe_bytes={str(path):path.read_bytes() for identity in ('t000','d000') for path in (h.out/'windows'/identity).rglob('*') if path.is_file()}
                pilot.run()
                completion=t.read(h.root/'pilot_01/completion.json')
                self.assertEqual(completion['selected_denominator'],24)
                self.assertEqual(completion['fresh_model_calls'],22)
                self.assertEqual(completion['verified_probe_reused_windows'],2)
                self.assertGreater(len(completion['unknown_window_ids']),0)
                self.assertEqual(completion['status'],'PASS_REAL_PILOT_READY_FOR_FULL_RELABEL')
                self.assertEqual(completion['explicit_empty_by_split'],{'train':0,'dev':0})
                self.assertTrue(completion['positive_only_capability_limit'])
                self.assertEqual(len(h.calls),48)
                h.phase('all')
                self.assertEqual(len(h.calls),320) # 160 annotations + 160 blind decisions; none duplicated.
                before={str(path):path.read_bytes() for path in (h.out/'validated').rglob('*') if path.is_file()}
                h.phase('review');self.assertEqual(len(h.calls),320)
                self.assertEqual(before,{str(path):path.read_bytes() for path in (h.out/'validated').rglob('*') if path.is_file()})
                self.assertEqual(probe_bytes,{name:Path(name).read_bytes() for name in probe_bytes})
                receipt=t.read(h.out/'semantic_review.json')
                self.assertEqual(receipt['selected_denominator'],160)
                self.assertEqual(len(receipt['reviewed_teacher_record_sha256']),160)
                self.assertEqual(receipt['unknown_count'],2)
                records=t.rows(h.out/'validated/validated_records.jsonl')
                unknown=next(r for r in records if r['window_id']=='t001')
                self.assertEqual(unknown['status'],'EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET')
                self.assertIsNone(unknown['target_json'])
                rawrows=t.rows(h.out/'raw_semantic_review_receipts.jsonl')
                unknown_review=next(r for r in rawrows if r['window_id']=='t002')
                self.assertEqual(unknown_review['support_class'],'UNKNOWN')
                self.assertNotIn(unknown_review['teacher_record_sha256'],receipt['supported_teacher_record_sha256'])
                for review in rawrows:
                    original=next(r for r in records if r['window_id']==review['window_id'])
                    t.verify_blind_review_projection(review,original,h.validator)

    def test_probe_fresh_guard_and_changed_cache_sha_model_prompt_fail(self):
        with tempfile.TemporaryDirectory(prefix='aic_teacher_cache_cpu_') as folder:
            h=Harness(folder)
            with h.mocks():
                h.phase('probe')
                with self.assertRaisesRegex(ValueError,'fresh real generation'):h.phase('probe')
                self.assertEqual(len(h.calls),2)
                path=h.out/'windows/t000';w=h.train[0]
                changed=copy.deepcopy(h.admission);changed['job_source_lock_sha256']='f'*64
                with self.assertRaisesRegex(ValueError,'model/weights/runtime/source-lock'):
                    t.annotate(w,path,h.validator,changed,changed['server_url'],20,h.args.ffprobe)
                raw_before=(path/'raw_answer.txt').read_bytes()
                (path/'prompt.txt').write_text('tampered',encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'cached annotation identity'):
                    t.annotate(w,path,h.validator,h.admission,h.admission['server_url'],20,h.args.ffprobe)
                self.assertEqual((path/'raw_answer.txt').read_bytes(),raw_before)

    def test_actual_pilot_whole_window_collapse_routes_without_fabrication(self):
        with tempfile.TemporaryDirectory(prefix='aic_teacher_collapse_cpu_') as folder:
            h=Harness(folder);h.whole=True;h.empty_ids=set()
            with h.mocks():
                h.phase('probe');pilot.run()
                receipt=t.read(h.root/'pilot_01/completion.json')
                self.assertEqual(receipt['status'],'PASS_REAL_PILOT_ROUTE_DECISION_REQUIRED')
                self.assertTrue(receipt['systematic_near_whole_window_collapse'])
                self.assertEqual(len(receipt['near_whole_window_ids']),23)
                self.assertEqual(receipt['route_decision'],'ROUTE_C_STOP_TEACHER')
                self.assertEqual(receipt['selected_denominator'],24)
                self.assertEqual(len(t.rows(h.root/'pilot_01/validated/validated_records.jsonl')),24)
                self.assertEqual(receipt['optimizer_steps'],0)

    def test_failed_raw_is_preserved_not_cached_or_turned_empty(self):
        with tempfile.TemporaryDirectory(prefix='aic_teacher_failure_cpu_') as folder:
            h=Harness(folder);h.bad_answer=True
            directory=h.out/'windows/t003'
            with h.mocks():
                with self.assertRaises(ValueError):t.annotate(h.train[3],directory,h.validator,h.admission,h.admission['server_url'],20,h.args.ffprobe)
                original=(directory/'raw_answer.txt').read_bytes()
                self.assertTrue((directory/'failure.json').is_file());self.assertFalse((directory/'done.json').exists())
                h.bad_answer=False
                with self.assertRaisesRegex(ValueError,'incomplete/failed'):t.annotate(h.train[3],directory,h.validator,h.admission,h.admission['server_url'],20,h.args.ffprobe)
                self.assertEqual(len(h.calls),1);self.assertEqual((directory/'raw_answer.txt').read_bytes(),original)

    def test_top_level_decision_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='aic_teacher_projection_cpu_') as folder:
            h=Harness(folder)
            with h.mocks():
                h.phase('probe')
                record=t.read(h.out/'windows/t000/validated_record.json')
                record['model_decision']['reason']='forged top-level reason'
                with self.assertRaisesRegex(ValueError,'projection differs'):t.verify_model_decision_projection(record)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryContracts))
    print(json.dumps({'status':'PASS_V8_CPU_BOUNDARY_PHASE_CHAIN' if result.wasSuccessful() else 'STOP_V8_CPU_BOUNDARY_PHASE_CHAIN',
        'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'gpu_used':False,'real_teacher_quality_tested':False,'synthetic_never_training_admission':True}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
