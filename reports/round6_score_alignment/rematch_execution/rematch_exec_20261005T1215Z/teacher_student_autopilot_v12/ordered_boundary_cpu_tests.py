"""Pinned C++ parser acceptance of the registered ordered boundary grammar.

Read the actual predecessor response on Linux; no real answer or media enters
source fixtures. Enumeration cases are explicitly synthetic CPU structures.
"""
import ast
from fractions import Fraction
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor,as_completed

import autopilot_common as c
import boundary_ids as b
import teacher_label as t

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'teacher_student_autopilot_v9'
FAILURE=OLD/'teacher_01/windows/complete_087af79e4b421be308d6cf6f'
BENCHMARKS=[]
DOMAIN_COUNTS={}


DEFAULT_OBSERVATION=None


def legacy_decision(segments,state='KEEP',frame_count=64):
    return {'state':state,'segments':[{'start_boundary_id':a,'end_boundary_id':e} for a,e in segments],
        'evidence_frame_ids':list(range(frame_count)),'reason':'SYNTHETIC_CPU_RELATION_STRUCTURE_ONLY'}


def decision(segments,state='KEEP',frame_count=64,observation=None):
    obs=DEFAULT_OBSERVATION if observation is None else observation
    items=[]
    for a,e in segments:
        try:frames=b.physical_evidence_domain(obs,a,e) if 0<=a<e<len(b.tables(obs)['boundary_ids']) else []
        except (IndexError,ValueError):frames=[]
        items.append({'start_boundary_id':'B'+str(a),'end_boundary_id':'B'+str(e),
            'evidence_frame_ids':['F'+str(i) for i in (frames or [0])]})
    return {'state':state,'segments':items,'evidence_frame_ids':[] if state=='KEEP' else ['F'+str(i) for i in range(frame_count)],
        'reason':'SYNTHETIC_CPU_RELATION_STRUCTURE_ONLY'}


def encoded(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def check(grammar,examples,label,root='root'):
    started=time.monotonic()
    # The fixed binary reparses the same grammar for every independent example.
    # Batching changes CPU scheduling only; every original text/expectation is
    # delivered unchanged, and returned checks retain original global indices.
    chunks=[examples[index:index+256] for index in range(0,len(examples),256)]
    affinity=sorted(os.sched_getaffinity(0));load=os.getloadavg()
    runnable=int(Path('/proc/loadavg').read_text().split()[3].split('/')[0])
    available_memory=next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
        if line.startswith('MemAvailable:'))
    observed_peak=int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)*1024
    largest_input=max(len(json.dumps({'grammar':grammar,'root':root,'examples':chunk},ensure_ascii=False).encode())
        for chunk in chunks)
    child_memory=max(observed_peak,len(grammar.encode())+largest_input)
    spare_cpu=max(1,len(affinity)-math.ceil(max(load[0],load[1],runnable-1)))
    memory_workers=available_memory//child_memory
    if memory_workers<1:raise RuntimeError('actual available memory cannot cover observed pinned checker child peak')
    workers=min(len(chunks),spare_cpu,memory_workers)
    capacity={'cpu_affinity':affinity,'load_average':list(load),'runnable_tasks':runnable,
        'available_memory_bytes':available_memory,'observed_child_peak_rss_bytes':observed_peak,
        'largest_batch_request_bytes':largest_input,'estimated_child_memory_bytes':child_memory,
        'spare_cpu_from_current_conflicts':spare_cpu,'memory_capacity_workers':memory_workers}
    print(f'{label}: {len(examples)} unchanged examples, {len(chunks)} batches, {workers} workers; capacity={json.dumps(capacity)}',
        file=sys.stderr,flush=True)
    def batch(index,chunk):
        batch_started=time.monotonic()
        process=subprocess.run([str(HERE/'runtime_schema_check')],
            input=json.dumps({'grammar':grammar,'root':root,'examples':chunk},ensure_ascii=False),
            capture_output=True,text=True,timeout=600)
        try:report=json.loads(process.stdout)
        except json.JSONDecodeError:raise AssertionError(process.stderr[-1000:])
        if len(report.get('checks',[]))!=len(chunk):raise AssertionError('fixed parser did not return every batch example')
        elapsed=time.monotonic()-batch_started
        print(f'{label}: batch {index+1}/{len(chunks)} complete; original indices {index*256}..{index*256+len(chunk)-1}; '
            f'wall={elapsed:.3f}s; returncode={process.returncode}; matches={report.get("all_examples_match_expectations")}',
            file=sys.stderr,flush=True)
        return index,report,{'batch_index':index,'first_case_index':index*256,'examples':len(chunk),
            'wall_sec':elapsed,'returncode':process.returncode,'all_examples_match_expectations':report.get('all_examples_match_expectations')}
    reports={};batches=[]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending=[executor.submit(batch,index,chunk) for index,chunk in enumerate(chunks)]
        for future in as_completed(pending):
            index,report,measurement=future.result();reports[index]=report;batches.append(measurement)
    checks=[item for index in range(len(chunks)) for item in reports[index]['checks']]
    all_match=all(item['accepted']==item['expected'] for item in checks)
    returncode=next((item['returncode'] for item in batches if item['returncode']),0)
    report={'all_examples_match_expectations':all_match,'checks':checks,'grammar':grammar}
    BENCHMARKS.append({'label':label,'examples':len(examples),'checker_wall_sec':time.monotonic()-started,
        'returncode':returncode,'all_examples_match_expectations':all_match,'batch_count':len(chunks),'workers':workers,
        'maximum_examples_per_batch':256,'per_batch_timeout_sec':600,'case_index_order_preserved':True,
        'resource_selection':capacity,'batches':sorted(batches,key=lambda item:item['batch_index']),
        'original_pinned_binary_and_all_examples_unchanged':True})
    if returncode or not all_match:
        mismatches=[i for i,item in enumerate(checks) if item['accepted']!=item['expected']]
        raise AssertionError(f'pinned parser mismatch case indices={mismatches[:20]}')
    return report


class OrderedBoundaryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert socket.gethostname()=='inspur-NP5570M5','actual ordered grammar verification is Linux-only'
        assert t.sha(HERE/'runtime_schema_check')==t.sha(OLD/'runtime_schema_check'),'keep original pinned checker bytes'
        cls.old_lock_sha=t.sha(OLD/'source_lock.json')
        cls.old_raw_sha=t.sha(FAILURE/'raw_answer.txt')
        cls.observation=c.read(FAILURE/'decode_receipt.json')
        global DEFAULT_OBSERVATION
        DEFAULT_OBSERVATION=cls.observation
        cls.raw=c.read(FAILURE/'server_response.json')['choices'][0]['message']['content']
        assert cls.raw.encode()==(FAILURE/'raw_answer.txt').read_bytes(),'actual original response alias changed'
        cls.grammar=b.ordered_grammar(cls.observation)
        cls.old_grammar=c.read(FAILURE/'server_response.json')['__verbose']['generation_settings']['grammar']
        assert len(cls.observation['actual_pts_sec'])==64
        assert len(b.tables(cls.observation)['boundary_ids'])==66
        spec=importlib.util.spec_from_file_location('old_v9_boundary_reference',OLD/'boundary_ids.py')
        cls.reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.reference)

    def test_01_actual_schema_grammar_accepted_overlap_but_original_validator_rejects(self):
        check(self.old_grammar,[{'text':self.raw,'expected':True}],'ACTUAL_V9_SCHEMA_GRAMMAR',root='response-format')
        with self.assertRaisesRegex(ValueError,'unordered or overlapping'):
            self.reference.validate_decision(json.loads(self.raw),self.observation)

    def test_02_actual_original_raw_rejected_without_rewriting(self):
        check(self.grammar,[{'text':self.raw,'expected':False}],'ACTUAL_OLD_RAW_RELATION_REJECTION')
        self.assertEqual(t.sha(FAILURE/'raw_answer.txt'),self.old_raw_sha)
        self.assertEqual(t.sha(OLD/'source_lock.json'),self.old_lock_sha)

    def test_03_exhaustive_actual66_single_pair_domain(self):
        count=len(b.tables(self.observation)['boundary_ids'])
        examples=[];legal=0;illegal=0
        for a in range(count):
            for e in range(count):
                value=decision([(a,e)])
                try:self.reference.validate_decision(legacy_decision([(a,e)]),self.observation);expected=True
                except ValueError:expected=False
                legal+=int(expected);illegal+=int(not expected)
                examples.append({'text':encoded(value),'expected':expected})
        self.assertEqual(legal,len(b.native_pair_domain(self.observation)))
        self.assertEqual(legal,2144)
        DOMAIN_COUNTS.update(actual_boundary_count=count,actual_frame_count=64,
            exhaustive_pair_instances=len(examples),legal_pair_instances=legal,illegal_pair_instances=illegal)
        check(self.grammar,examples,'ALL_ACTUAL_66_BY_66_SINGLE_PAIRS')

    def test_04_exhaustive_small_domain_all_legal1_to5_sequences(self):
        obs={'window_id':'synthetic_cpu_complete_sequence_domain','window_pts_start_sec':0.0,
            'window_pts_end_exclusive_sec':5.0,'window_duration_sec':5.0,
            'actual_pts_sec':[0.1,1.0,2.0,3.0,4.0],'source_frame_ordinals':list(range(5))}
        table=b.tables(obs);positions=[Fraction(p['local_seconds_fraction']) for p in table['boundary_ids']]
        points=[Fraction(str(p)) for p in obs['actual_pts_sec']]
        pairs=[(a,e) for a in range(len(positions)) for e in range(a+1,len(positions))
            if any(positions[a]<=point<positions[e] for point in points)]
        examples=[];counts={str(k):0 for k in range(1,6)}
        def enumerate_all(sequence,minimum):
            if sequence:
                value=decision(sequence,frame_count=5,observation=obs)
                self.reference.validate_decision(legacy_decision(sequence,frame_count=5),obs)
                examples.append({'text':encoded(value),'expected':True});counts[str(len(sequence))]+=1
            if len(sequence)==5:return
            for a,e in pairs:
                if a>=minimum:enumerate_all([*sequence,(a,e)],e)
        enumerate_all([],0)
        self.assertTrue(all(counts[str(k)]>0 for k in range(1,6)))
        DOMAIN_COUNTS.update(small_domain_exhaustive_legal_sequences_by_count=counts,
            small_domain_exhaustive_sequence_instances=len(examples))
        check(b.ordered_grammar(obs),examples,'ALL_SMALL_DOMAIN_LEGAL_1_TO_5_SEQUENCES')

    def test_05_actual66_touching_gap_nested_overlap_order_reversal_and_maxcount(self):
        cases=[([(0,2),(2,4)],True),([(1,3),(4,8),(9,11),(12,14),(15,18)],True),
            ([(0,65)],True),([(4,8),(0,2)],False),([(0,8),(2,6)],False),
            ([(0,8),(5,12)],False),([(3,3)],False),([(4,3)],False),
            ([(0,2),(2,4),(4,6),(6,8),(8,10),(10,12)],False),
            ([(0,66)],False),([(-1,3)],False),([(0,1)],False)]
        check(self.grammar,[{'text':encoded(decision(pair)),'expected':expected} for pair,expected in cases],
            'ACTUAL66_MULTI_SEGMENT_VALID_AND_INVALID_RELATIONS')

    def test_06_keep_no_unknown_states_and_separate_terminal_evidence(self):
        examples=[]
        for state in ('NO_HIGHLIGHT','UNKNOWN'):
            value=decision([],state=state)
            examples.append({'text':encoded(value),'expected':True})
            canonical=b.canonical_response(value,self.observation)
            self.assertEqual(canonical['explicit_no_highlight'],state=='NO_HIGHLIGHT')
            self.assertEqual(canonical['uncertain'],state=='UNKNOWN')
            examples.append({'text':encoded(decision([(0,2)],state=state)),'expected':False})
        examples.append({'text':encoded(decision([])),'expected':False})
        value=decision([(0,65)]);value['segments'][0]['evidence_frame_ids']=['F65']
        examples.append({'text':encoded(value),'expected':False})
        value=decision([(0,65)]);value['reason']=''
        examples.append({'text':encoded(value),'expected':False})
        check(self.grammar,examples,'KEEP_NO_UNKNOWN_UNCHANGED_STRUCTURAL_STATES')

    def test_07_payload_only_adds_relation_constraint_schema_prompt_validator_unchanged(self):
        generated,fields,contract=t.generation_constraints(None,self.observation)
        self.assertNotEqual(generated,c.read(FAILURE/'generation_schema.json'))
        self.assertEqual(generated,b.schema(self.observation))
        self.assertEqual(generated['anyOf'][0]['properties']['segments']['items']['properties']['start_boundary_id']['type'],'string')
        self.assertEqual(set(fields),{'grammar'})
        self.assertEqual(contract['all_legal_segment_counts'],[1,2,3,4,5])
        self.assertEqual(contract['physical_pair_count'],2144)
        for name in ('teacher_prompt.txt','review_prompt.txt','supervision/validate_teacher.py'):
            self.assertEqual(t.sha(HERE/name),t.sha(OLD/name))
        new_ast=ast.parse((HERE/'boundary_ids.py').read_text());old_ast=ast.parse((OLD/'boundary_ids.py').read_text())
        for name in ('tables',):
            new=next(node for node in new_ast.body if isinstance(node,ast.FunctionDef) and node.name==name)
            old=next(node for node in old_ast.body if isinstance(node,ast.FunctionDef) and node.name==name)
            self.assertEqual(ast.dump(new),ast.dump(old))
        visual={'type':'object','additionalProperties':False,'required':['red_square_frame_ids'],
            'properties':{'red_square_frame_ids':{'type':'array','items':{'type':'integer','enum':list(range(64))}}}}
        generated,fields,contract=t.generation_constraints(visual,self.observation)
        self.assertEqual(generated,visual);self.assertEqual(set(fields),{'response_format'});self.assertIsNone(contract)

    def test_08_production_runtime_verifier_requires_exact_applied_grammar(self):
        generated=b.schema(self.observation);value=encoded(decision([(0,65)]))
        result={'__verbose':{'generation_settings':{'grammar':self.grammar,'grammar_lazy':False}}}
        with tempfile.TemporaryDirectory(prefix='ordered_runtime_cpu_',dir=HERE) as folder:
            t.verify_runtime_grammar(result,generated,value,Path(folder),expected_grammar=self.grammar,observation=self.observation)
            receipt=c.read(Path(folder)/'runtime_grammar_validation.json')
            self.assertTrue(receipt['ordered_native_boundary_grammar'])
            self.assertTrue(receipt['direct_request_grammar_exactly_matches_actual_runtime'])
        result['__verbose']['generation_settings']['grammar']=self.old_grammar
        with tempfile.TemporaryDirectory(prefix='ordered_mismatch_cpu_',dir=HERE) as folder:
            with self.assertRaisesRegex(ValueError,'did not retain'):
                t.verify_runtime_grammar(result,generated,value,Path(folder),expected_grammar=self.grammar,observation=self.observation)


if __name__=='__main__':
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OrderedBoundaryContracts))
    passed=result.wasSuccessful() and result.testsRun==8
    observation=c.read(FAILURE/'decode_receipt.json')
    grammar=b.ordered_grammar(observation)
    report={'status':'PASS_FIXED_RUNTIME_ORDERED_BOUNDARY_CPU' if passed else 'STOP_FIXED_RUNTIME_ORDERED_BOUNDARY_CPU',
        'GPU_started':False,'real_teacher_generation_performed':False,'synthetic_never_training_labels':True,
        'old_raw_rejected':passed,'old_source_lock_sha256':t.sha(OLD/'source_lock.json'),
        'old_raw_sha256':t.sha(FAILURE/'raw_answer.txt'),'old_raw_not_rewritten':True,
        'production_boundary_sha256':t.sha(HERE/'boundary_ids.py'),'production_teacher_sha256':t.sha(HERE/'teacher_label.py'),
        'runtime_revision':t.RUNTIME_REVISION,'pinned_checker_sha256':t.sha(HERE/'runtime_schema_check'),
        'grammar_sha256':t.text_sha(grammar),'grammar_bytes':len(grammar.encode()),'grammar_rule_count':len(grammar.splitlines()),
        'new_relation_contract_tests':result.testsRun,'total_contract_tests':64+result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'benchmarks':BENCHMARKS,
        'checker_total_wall_sec':sum(item['checker_wall_sec'] for item in BENCHMARKS),
        'total_wall_sec':time.monotonic()-started,'domain_instance_counts_are_not_independent_tests':True,
        **DOMAIN_COUNTS}
    c.write(HERE/'ordered_boundary_cpu_acceptance.json',report,fresh=True)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    raise SystemExit(0 if passed else 1)
