"""Fixed-runtime structural evidence interface tests; synthetic never labels.

The actual predecessor failure is read only on Linux and never embedded here.
CPU request comparison scopes only the HTTP/model boundary; production inference,
lossless frame identity, processor-log parsing and contract construction run.
"""
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import socket
import tempfile
import time
import unittest
from unittest.mock import patch
import autopilot_common as c
import boundary_ids as b
import teacher_label as t
import visual_interface_probe as visual
from ordered_boundary_cpu_tests import check,BENCHMARKS,decision,encoded

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'teacher_student_autopilot_v10'
COUNTS={}
FAILURE_ID='complete_45666feb9bbc3d854e9d05c1'
EXPECTED_RAW_SHA='9977638522f91aa2661fd70b5179a7aed557ea816d5f451f6f50b010114f65fa'


def subsets(values):
    return [list(items) for n in range(1,len(values)+1) for items in itertools.combinations(values,n)]


class EvidenceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert socket.gethostname()=='inspur-NP5570M5','fixed runtime acceptance is Linux CPU only'
        assert t.sha(HERE/'runtime_schema_check')==t.sha(OLD/'runtime_schema_check')
        candidates=[OLD/folder/FAILURE_ID for folder in ('teacher_01/windows','pilot_01/windows')]
        cls.failure=next(path for path in candidates if (path/'server_response.json').is_file())
        cls.actual_raw=c.read(cls.failure/'server_response.json')['choices'][0]['message']['content']
        assert cls.actual_raw.encode()==(cls.failure/'raw_answer.txt').read_bytes()
        assert t.sha(cls.failure/'raw_answer.txt')==EXPECTED_RAW_SHA
        cls.failed_observation=c.read(cls.failure/'decode_receipt.json')
        cls.observation=c.read(HERE.parent/'teacher_student_autopilot_v9/teacher_01/windows/complete_087af79e4b421be308d6cf6f/decode_receipt.json')
        cls.grammar=b.ordered_grammar(cls.observation)
        for name,file in (('old_v10_boundary',OLD/'boundary_ids.py'),('old_v10_inference',OLD/'teacher_label.py')):
            spec=importlib.util.spec_from_file_location(name,file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            if name=='old_v10_boundary':cls.old_boundary=module
            else:cls.old_teacher=module
        cls.old_lock_sha=t.sha(OLD/'source_lock.json')

    def test_01_actual_old_raw_was_grammar_accepted_but_original_evidence_validator_rejected(self):
        grammar=c.read(self.failure/'server_response.json')['__verbose']['generation_settings']['grammar']
        check(grammar,[{'text':self.actual_raw,'expected':True}],'ACTUAL_V10_DETACHED_EVIDENCE_GRAMMAR')
        with self.assertRaisesRegex(ValueError,'every KEEP segment needs a selected physical evidence frame'):
            self.old_boundary.validate_decision(json.loads(self.actual_raw),self.failed_observation)

    def test_02_actual_old_raw_rejected_and_frozen_bytes_unchanged(self):
        check(b.ordered_grammar(self.failed_observation),[{'text':self.actual_raw,'expected':False}],
            'ACTUAL_V10_DETACHED_EVIDENCE_RAW_REJECTED')
        self.assertEqual(t.sha(self.failure/'raw_answer.txt'),EXPECTED_RAW_SHA)
        self.assertEqual(t.sha(OLD/'source_lock.json'),self.old_lock_sha)

    def test_03_every_real_pair_evidence_domain_and_every_finite_subset_transition(self):
        table=b.tables(self.observation);rules=b.grammar_rules(self.observation)
        points=[Fraction(f['local_seconds_fraction']) for f in table['evidence_frames']]
        positions=[Fraction(f['local_seconds_fraction']) for f in table['boundary_ids']]
        token=lambda value:json.dumps(json.dumps(value))
        pairs=b.native_pair_domain(self.observation);memberships=0;legal_memberships=0;states=set()
        for a,e in pairs:
            domain=b.physical_evidence_domain(self.observation,a,e)
            self.assertIn('ev-'+str(domain[0])+'-'+str(domain[-1]),rules['pair-'+str(a)+'-'+str(e)])
            for f,point in enumerate(points):
                self.assertEqual(f in domain,positions[a]<=point<positions[e])
                memberships+=1;legal_memberships+=int(f in domain)
            for lo in range(domain[0],domain[-1]+1):
                hi=domain[-1];name=f'ev-{lo}-{hi}';first=token('F'+str(lo))+' space'
                rest=f'ev-{lo+1}-{hi}' if lo<hi else None
                self.assertEqual(rules[name],first+(' ("," space '+rest+')? | '+rest if rest else ''))
                states.add(name)
        COUNTS.update(actual_boundary_count=len(positions),actual_frame_count=len(points),all_legal_pair_domains=len(pairs),
            exhaustive_pair_frame_membership_instances=memberships,legal_pair_frame_membership_instances=legal_memberships,
            finite_evidence_subset_states_verified=len(states))
        examples=[];last=len(positions)-1
        for f in range(len(points)):
            value=decision([(0,last)],observation=self.observation)
            value['segments'][0]['evidence_frame_ids']=['F'+str(f)]
            b.validate_decision(value,self.observation);examples.append({'text':encoded(value),'expected':True})
        for frame_list in (list(range(0,64,2)),list(range(1,64,2)),[0,63],list(range(64))):
            value=decision([(0,last)],observation=self.observation)
            value['segments'][0]['evidence_frame_ids']=['F'+str(f) for f in frame_list]
            examples.append({'text':encoded(value),'expected':True})
        check(self.grammar,examples,'ALL_REAL64_SINGLETON_CHOICES_AND_MULTIPLE_NONEMPTY_SUBSETS')
        COUNTS['actual_runtime_evidence_choice_examples']=len(examples)

    def test_04_small_domain_all_legal1_to5_and_all_nonempty_local_witness_subsets(self):
        obs={'window_id':'synthetic_all_local_evidence_subsets','window_pts_start_sec':0.0,
            'window_pts_end_exclusive_sec':5.0,'window_duration_sec':5.0,
            'actual_pts_sec':[0.1,1.0,2.0,3.0,4.0],'source_frame_ordinals':list(range(5))}
        pairs=b.native_pair_domain(obs);examples=[];counts={str(k):0 for k in range(1,6)}
        def visit(sequence,minimum):
            if sequence:
                value=decision([(a,e) for a,e,_ in sequence],observation=obs,frame_count=5)
                for segment,(_,_,frames) in zip(value['segments'],sequence):segment['evidence_frame_ids']=['F'+str(f) for f in frames]
                b.validate_decision(value,obs);examples.append({'text':encoded(value),'expected':True});counts[str(len(sequence))]+=1
            if len(sequence)==5:return
            for a,e in pairs:
                if a<minimum:continue
                for frames in subsets(b.physical_evidence_domain(obs,a,e)):visit([*sequence,(a,e,frames)],e)
        visit([],0);self.assertTrue(all(counts[str(k)] for k in range(1,6)))
        check(b.ordered_grammar(obs),examples,'ALL_SMALL_LEGAL_SEQUENCES_AND_LOCAL_EVIDENCE_SUBSETS')
        COUNTS.update(small_exhaustive_local_evidence_sequences=len(examples),small_sequences_by_count=counts)

    def test_05_outside_borrowed_empty_duplicate_reverse_terminal_and_namespace_evidence_rejected(self):
        examples=[]
        for evidence in (['F64'],['B0'],['F01'],[],['F2','F1'],['F0','F0'],[0]):
            value=decision([(0,3)],observation=self.observation);value['segments'][0]['evidence_frame_ids']=evidence
            with self.assertRaises(ValueError):b.validate_decision(value,self.observation)
            examples.append({'text':encoded(value),'expected':False})
        value=decision([(0,3),(4,8)],observation=self.observation)
        value['segments'][1]['evidence_frame_ids']=['F0']
        with self.assertRaises(ValueError):b.validate_decision(value,self.observation)
        examples.append({'text':encoded(value),'expected':False})
        value=decision([(0,3)],observation=self.observation);value['evidence_frame_ids']=['F0']
        examples.append({'text':encoded(value),'expected':False})
        value=decision([(0,3)],observation=self.observation);value['segments'][0]['start_boundary_id']='F0'
        examples.append({'text':encoded(value),'expected':False})
        check(self.grammar,examples,'INVALID_LOCAL_WITNESS_AND_EXPLICIT_NAMESPACES')

    def test_06_projection_uses_only_model_selected_witnesses_and_different_legal_choices_compare(self):
        first=decision([(0,3)],observation=self.observation);first['segments'][0]['evidence_frame_ids']=['F0','F1']
        second=decision([(0,3)],observation=self.observation);second['segments'][0]['evidence_frame_ids']=['F1']
        projected=b.canonical_response(first,self.observation)
        self.assertIn('physical evidence IDs=[0, 1]',projected['boundary_notes'][0])
        self.assertEqual(b.normalized_decision(first,self.observation)['evidence_frame_ids'],[0,1])
        self.assertTrue(t.compare_selections(first,second,self.observation)['supported'])
        second['segments'][0]['evidence_frame_ids']=['F0']
        self.assertTrue(t.compare_selections(first,second,self.observation)['supported'])
        legacy={'state':'KEEP','segments':[{'start_boundary_id':0,'end_boundary_id':3}],
            'evidence_frame_ids':[1],'reason':'SYNTHETIC_LEGACY_COMPARISON_ONLY'}
        with self.assertRaisesRegex(ValueError,'exact approved'):t.compare_selections(legacy,second,self.observation)
        self.assertTrue(t.compare_selections(legacy,first,self.observation,approved_legacy_first=True)['supported'])

    def test_07_template_semantics_original_validator_and_new_runtime_application(self):
        for name in ('teacher_prompt.txt','review_prompt.txt','supervision/validate_teacher.py'):
            self.assertEqual(t.sha(HERE/name),t.sha(OLD/name))
        template=(HERE/'teacher_prompt.txt').read_text(encoding='utf-8');new=b.prompt(template,self.observation)
        self.assertIn('aic_B_boundary_F_segment_local_evidence_v11',new)
        self.assertIn('真正显示相关事件',new)
        for semantic in ('普通连续活动本身不自动值得保留','不能确定关键价值、事件身份或边界时选择UNKNOWN','图片间未观测区间不能被证明为负'):
            self.assertIn(semantic,new)
        value=decision([(0,65)],observation=self.observation)
        result={'__verbose':{'generation_settings':{'grammar':self.grammar,'grammar_lazy':False}}}
        with tempfile.TemporaryDirectory(prefix='bf_actual_runtime_',dir=HERE) as folder:
            t.verify_runtime_grammar(result,b.schema(self.observation),encoded(value),Path(folder),expected_grammar=self.grammar,observation=self.observation)
            self.assertTrue(c.read(Path(folder)/'runtime_grammar_validation.json')['direct_request_grammar_exactly_matches_actual_runtime'])

    def test_08_actual_inference_visual8_http_payloads_equal_original_v10(self):
        equal=0;request_hashes=[]
        with tempfile.TemporaryDirectory(prefix='bf_visual_payload_cpu_',dir=HERE) as folder:
            root=Path(folder)
            for i,plan in enumerate(visual.case_plan()):
                observation,expected=visual.make_case(plan,root/('frames_'+str(i)))
                count=len(observation['actual_pts_sec'])
                prompt=(f'按给出的图片顺序查看全部{count}张图片。只找绿色背景上明显可见的红色方块。'
                    '用图片标注的evidence_frame_id回答，按升序列出所有有红色方块的图片编号。'
                    '若所有图片都没有红色方块则输出空列表。只输出JSON，字段恰好red_square_frame_ids。')
                generated_schema={'type':'object','additionalProperties':False,'required':['red_square_frame_ids'],
                    'properties':{'red_square_frame_ids':{'type':'array','maxItems':count,
                        'items':{'type':'integer','enum':list(range(count))}}}}
                requests=[]
                for j,module in enumerate((self.old_teacher,t)):
                    out=root/f'case_{i}_{j}';out.mkdir();log=out/'server.log';log.write_bytes(b'')
                    admission={**c.read(OLD/'teacher_admission.json'),'server_log':str(log),
                        'server_parallel':1,'server_log_verbosity':5}
                    def http(url,payload,receipt_dir,timeout):
                        data=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode();requests.append(data)
                        receipt_dir.mkdir();(receipt_dir/'request.json').write_bytes(data)
                        with log.open('ab') as stream:
                            for _ in observation['actual_pts_sec']:
                                stream.write(b'copying image 1/2 to input buffer (nx=256, ny=256)\ncopying image 2/2 to input buffer (nx=256, ny=256)\n')
                        return {'choices':[{'message':{'content':json.dumps({'red_square_frame_ids':expected})},'finish_reason':'stop'}],
                            'usage':{'prompt_tokens':1000},'__verbose':{'generation_settings':{'grammar':'SYNTHETIC_HTTP_ONLY','grammar_lazy':False}}}
                    with patch.object(module,'http_json',side_effect=http),patch.object(module,'verify_runtime_grammar',return_value=None):
                        module.inference('http://127.0.0.1:8080',prompt,observation,generated_schema,admission,out,30)
                self.assertEqual(requests[0],requests[1])
                self.assertEqual(requests[0],(OLD/'visual_probe_01/cases'/plan['case_id']/'http/request.json').read_bytes())
                equal+=1
                request_hashes.append(hashlib.sha256(requests[0]).hexdigest())
        self.assertEqual(equal,8);COUNTS.update(legacy_visual_requests_equal_actual_count=equal,
            legacy_visual_request_sha256=request_hashes,visual_http_and_model_boundary_scoped_mock=True,
            production_frame_pixels_processor_parse_and_inference_executed=True)


if __name__=='__main__':
    started=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceContracts))
    passed=result.wasSuccessful() and result.testsRun==8
    report={'status':'PASS_FIXED_RUNTIME_BF_PER_SEGMENT_EVIDENCE_CPU' if passed else 'STOP_FIXED_RUNTIME_BF_PER_SEGMENT_EVIDENCE_CPU',
        'GPU_started':False,'real_teacher_generation_performed':False,'synthetic_never_training_labels':True,
        'old_raw_rejected':passed,'old_raw_sha256':EXPECTED_RAW_SHA,'old_source_lock_sha256':t.sha(OLD/'source_lock.json'),
        'old_teacher_sha256':t.sha(OLD/'teacher_label.py'),'production_teacher_sha256':t.sha(HERE/'teacher_label.py'),
        'production_boundary_sha256':t.sha(HERE/'boundary_ids.py'),'pinned_checker_sha256':t.sha(HERE/'runtime_schema_check'),
        'new_evidence_contract_tests':result.testsRun,'total_contract_tests':64+8+result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'benchmarks':BENCHMARKS,
        'checker_benchmark_wall_sec':sum(item['checker_wall_sec'] for item in BENCHMARKS),
        'total_wall_sec':time.monotonic()-started,'domain_instances_are_not_independent_contract_tests':True,**COUNTS}
    c.write(HERE/'evidence_boundary_cpu_acceptance.json',report,fresh=True)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    raise SystemExit(0 if passed else 1)
