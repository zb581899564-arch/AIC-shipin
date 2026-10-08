"""Cross-stage regression cases for the failures found in the full audit."""
import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import train_student as s
import teacher_label as t
from cost_contract import teacher_remaining_cost, measured_spatial_cost

s.helper_paths(Path(__file__).resolve().parent.parent)
import contracts
import constrained_json as grammar
import engine
import training_target
from native_segment_contract import native_segment_ranges


class CrossStageContracts(unittest.TestCase):
    def test_original_bug_and_lossless_six_decimal_bridge(self):
        old = s.load(t.HERE.parent/'next_round_v1/contracts.py','audit_original_four_digit_contract')
        with self.assertRaisesRegex(ValueError,'four-decimal'):
            old.answer_string([[0,0.018292]],30)
        answer = contracts.answer_string([[0,0.018292]],30)
        self.assertEqual(json.loads(answer)['segments'],[[0,0.018292]])
        self.assertTrue(grammar.BoundedSegmentsGrammar(30).complete(answer))
        self.assertEqual(contracts.parse_segments(answer,30),([[0,0.018292]],[],[]))

    def test_lossless_tail_and_high_precision_values(self):
        for value in (18.666665999999992,8.928799999999995,19.889749999999992,
                      0.016666666666666666,0.000000000000000001):
            answer=contracts.answer_string([[0,value]],30)
            self.assertEqual(Fraction(str(json.loads(answer)['segments'][0][1])),Fraction(str(value)))
            g=grammar.BoundedSegmentsGrammar(30)
            self.assertTrue(g.complete(answer),answer)
            self.assertTrue(all(g.valid_prefix(answer[:i]) for i in range(len(answer)+1)),answer)
            self.assertEqual(contracts.parse_segments(answer,30)[0],[[0,value]])

    def test_grammar_cannot_complete_a_number_the_parser_rejects(self):
        text='{"segments":[[0,0.12345678901234567]]}'
        self.assertIsNone(contracts.parse_segments(text,30)[0])
        self.assertFalse(grammar.BoundedSegmentsGrammar(30).complete(text))

    def test_sorted_bounds_empty_and_malformed_remain_strict(self):
        g=grammar.BoundedSegmentsGrammar(1)
        self.assertTrue(g.complete('{"segments":[]}'))
        for text in ('{"segments":[[0,1.000001]]}','{"segments":[[0.3,0.2]]}',
                     '{"segments":[[0,.2]]}','{"segments":[[0,0.5],[0.4,0.8]]}',
                     '{"segments":[[0,0.5],]}','{"segments":[[0,1e-2]]}'):
            self.assertFalse(g.complete(text),text)

    def test_explicit_binding_survives_old_modules_and_path_reorder(self):
        for name in ('contracts','constrained_json','engine','training_target'):
            s.load(t.HERE.parent/'next_round_v1'/(name+'.py'),name)
        s.helper_paths(t.HERE.parent)
        for name in ('contracts','constrained_json','engine','training_target'):
            self.assertEqual(Path(sys.modules[name].__file__).resolve(),(t.HERE/'precision_helpers'/(name+'.py')).resolve())
        self.assertEqual(sys.modules['engine'].make_prefix_constraint.__module__,'constrained_json')
        self.assertEqual(sys.modules['training_target'].answer_string([[0,0.018292]],30),'{"segments":[[0,0.018292]]}')

    def test_native_frame_gap_reproduces_legal_numeric_but_unrealizable_interval(self):
        text='{"segments":[[0.0001,0.0002]]}'
        self.assertTrue(grammar.BoundedSegmentsGrammar(1).complete(text))
        self.assertIsNotNone(contracts.parse_segments(text,1)[0])
        with self.assertRaisesRegex(ValueError,'no actual source frame'):
            native_segment_ranges([[0.0001,0.0002]],[0,.034,.068,.102],0,1)

    def generation(self, segments, points):
        actual=sys.modules['engine'];original=actual.generate_window
        actual.generate_window=lambda *args,**kw:dict(output_valid=True,status='MODEL_OK' if segments else 'LEGAL_EMPTY',
            parsed_segments=copy.deepcopy(segments),parse_errors=[],parse_warnings=[],raw_output=json.dumps({'segments':segments}))
        try:
            return s.production_generate(None,None,{'window_pts_start_sec':0,'window_duration_sec':1},None,
                {'window_source_pts_sec':points},candidates=())
        finally:actual.generate_window=original

    def test_shared_generation_marks_failure_without_empty_conversion(self):
        result=self.generation([[.0001,.0002]],[0,.034,.068,.102])
        self.assertFalse(result['output_valid']);self.assertIsNone(result['parsed_segments'])
        self.assertEqual(result['rejected_parsed_segments'],[[.0001,.0002]])
        self.assertFalse(result['native_frame_realizability']['failure_converted_to_empty'])

    def test_realizability_uses_all_source_frames_and_preserves_legal_empty(self):
        self.assertTrue(self.generation([[.01,.025]],[0,.02,.03])['output_valid'])
        result=self.generation([],[0,.02,.03]);self.assertTrue(result['output_valid'])
        self.assertEqual(result['status'],'LEGAL_EMPTY');self.assertEqual(result['parsed_segments'],[])

    def test_incremental_cost_is_invariant_to_preexisting_pilot_payload_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for i in range(14):
                p=root/'windows'/str(i);(p/'http').mkdir(parents=True)
                (p/'done.json').write_text('{}');(p/'http/request.json').write_bytes(b'x'*100)
            before=teacher_remaining_cost(root,['0','1'],160)
            (root/'windows/2/large_pilot_payload').write_bytes(b'x'*100000)
            after=teacher_remaining_cost(root,['0','1'],160)
            self.assertEqual(before,after);self.assertEqual(after['remaining_label_windows'],146)
            self.assertFalse(after['already_stored_bytes_charged_again'])

    def test_valid_empty_measurement_never_becomes_none_in_spatial_arithmetic(self):
        empty={'status':'PASS_EMPTY_SPACE_NO_MODEL_CALL','invalid':0,'model_calls':0,'measured_seconds_per_anchor':None}
        good={'status':'PASS_STRICT_SOURCE_FIELD_SPATIAL','invalid':0,'model_calls':12,'measured_seconds_per_anchor':.6}
        self.assertEqual(measured_spatial_cost([('empty',empty),('real',good)]),('real',.6))
        with self.assertRaisesRegex(ValueError,'no actual successful'):
            measured_spatial_cost([('empty',empty)])

    def test_fresh_probe_cannot_silently_return_a_cached_annotation(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary);(out/'done.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'fresh real generation required'):
                t.annotate({},out,None,{},None,0,'ffprobe',allow_prior_reuse=False)

    def test_annotation_scope_true_is_structural_not_self_confirmation(self):
        schema=t.read(t.HERE/'supervision/teacher_response.schema.json')
        request=t.request_schema(schema,{'window_id':'fixture','window_pts_start_sec':0,'window_pts_end_exclusive_sec':1,
            'window_duration_sec':1,'actual_pts_sec':[0,.5]})
        self.assertTrue(all(b['properties']['observation_scope']['properties']['all_provided_frames_reviewed']=={'const':True}
                            for b in request['anyOf']))
        self.assertEqual(t.REVIEW_SCHEMA['properties']['observation_scope']['properties']['all_provided_frames_reviewed'],{'type':'boolean'})

    def test_review_coordinate_map_preserves_local_bounds_without_subtracting_origin(self):
        record={'window':{'window_id':'clock_fixture','window_pts_start_sec':120,'window_pts_end_exclusive_sec':150,'window_duration_sec':30},
            'actual_observation':{'actual_pts_sec':[120,136.16936666666666,149]},
            'retained_segments':[{'start_sec':16.16936666666666,'end_sec':19.0}], 'raw_answer':'ORIGINAL_UNCHANGED'}
        text=t.review_prompt(record)
        self.assertIn('"start_window_local_sec": 16.16936666666666',text)
        self.assertIn('"start_source_pts_sec": 136.16936666666666',text)
        self.assertIn('不要再次',text);self.assertTrue(text.endswith('ORIGINAL_UNCHANGED'))

    def test_new_calibration_decides_semantic_state_before_enumerating_segments(self):
        schema=t.read(t.HERE/'supervision/teacher_response.schema.json')
        request=t.request_schema(schema,{'window_id':'fixture','window_pts_start_sec':0,'window_pts_end_exclusive_sec':1,
            'window_duration_sec':1,'actual_pts_sec':[0,.5]})
        for branch in request['anyOf']:
            order=list(branch['properties'])
            self.assertLess(order.index('decision_reason'),order.index('retained_segments'))
            self.assertLess(order.index('explicit_no_highlight'),order.index('retained_segments'))
            self.assertEqual(set(branch['required']),set(schema['required']))
        self.assertEqual({(b['properties']['uncertain']['const'],b['properties']['explicit_no_highlight']['const']) for b in request['anyOf']},
            {(True,False),(False,True),(False,False)})

    def test_pilot_diagnostic_review_cannot_promote_rejections_to_training_success(self):
        import pilot
        records=[{'window_id':str(i),'sft_eligible':True,'status':'PASS_WEAK_COMPLETE_WINDOW_TARGET',
            'split':'train' if i<8 else 'dev','explicit_no_highlight':i==0,
            'retained_segments':[] if i==0 else [{'start_sec':1,'end_sec':2}],
            'window':{'window_duration_sec':3}} for i in range(12)]
        reviews=[{'window_id':str(i),'review_status':'PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW'} for i in range(12)]
        self.assertEqual(pilot.reviewed_gate(records,reviews),([],[]))
        reviews[0]['review_status']='STOP_WEAK_REVIEW_REJECTED_OR_UNCERTAIN'
        reasons,rejected=pilot.reviewed_gate(records,reviews)
        self.assertEqual(rejected,['0']);self.assertTrue(any('rejected' in r for r in reasons))
        self.assertTrue(any('exactly one' in r for r in pilot.reviewed_gate(records,reviews[1:])[0]))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CrossStageContracts))
    report={'status':'PASS_V7_CROSS_STAGE_CPU_AUDIT' if result.wasSuccessful() else 'STOP_V7_CROSS_STAGE_CPU_AUDIT',
        'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'GPU_started':False,
        'synthetic_fixtures_never_training_labels':True,'scientific_distribution_stop_not_waived':True}
    if result.wasSuccessful():t.save(t.HERE/'audit_cpu_acceptance.json',report,fresh=True)
    print(json.dumps(report));raise SystemExit(0 if result.wasSuccessful() else 1)
