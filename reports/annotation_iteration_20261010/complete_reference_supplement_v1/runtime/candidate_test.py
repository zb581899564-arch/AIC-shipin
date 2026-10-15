"""Pure CPU contract tests: no torch, model, processor or media decoder."""
from fractions import Fraction as F
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os
import sys
from types import SimpleNamespace

import candidate_support as cs
from candidate_engine import estimate_output_bytes
from candidate_package import selected_frames, STRICT_CHECKS
import candidate_static_preflight as static
from common import load, read, save, sha

RUN = Path(__file__).resolve().parents[3]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


class CandidateLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load(RUN/'balanced_two_window_risk_v3/bw_common.py', 'bw_common')
        cls.native = load(RUN/'balanced_two_window_risk_v3/bw_native.py', 'candidate_test_original_native')
        load(RUN/'teacher_student_autopilot_v14/precision_helpers/contracts.py', 'contracts')
        load(RUN/'teacher_student_autopilot_v14/native_segment_contract.py', 'native_segment_contract')

    def test_balanced_exact_midpoint_and_boundaries(self):
        self.assertEqual(self.native.balanced_schedule([(0, 30), (30, 45.5)]), [(F(0), F('22.75')), (F('22.75'), F('45.5'))])
        for total in (30, 60):
            original = [(0, 20), (20, total)]
            self.assertEqual(self.native.balanced_schedule(original), [(F(a), F(b)) for a, b in original])

    def test_no_balancing_single_or_three_windows(self):
        self.assertEqual(self.native.balanced_schedule([(0, 35)]), [(F(0), F(35))])
        original = [(0, 10), (10, 20), (20, 35)]
        self.assertEqual(self.native.balanced_schedule(original), [(F(a), F(b)) for a, b in original])

    def test_noncontiguous_two_domain_rejected(self):
        with self.assertRaises(ValueError):
            self.native.balanced_schedule([(0, 20), (21, 40)])

    def test_floor64_has_real_endpoints(self):
        for first, stop in ((10, 11), (10, 74), (10, 75), (400, 2200)):
            ids = self.native.floor_indices(first, stop)
            self.assertEqual(ids[0], first); self.assertEqual(ids[-1], stop-1)
            self.assertEqual(len(ids), min(64, stop-first)); self.assertEqual(ids, sorted(set(ids)))

    def test_exact_native_half_open_raw_parser(self):
        a = dict(raw_start='0', raw_end='1', eligible_points=['0', '1/10', '1/5', '3/10'],
                 window=dict(window_pts_start_sec=0))
        evidence = dict(window_source_pts_sec=[0., .1, .2, .3])
        value = cs.result('{"segments":[[0.1,0.3]]}', a, evidence)
        self.assertEqual(value['native_frame_ranges'], [[1, 3]])
        self.assertEqual(value['parsed_segments'], [['1/10', '3/10']])

    def test_actual_legal_empty_is_preserved(self):
        a = dict(raw_start='0', raw_end='1', eligible_points=['0', '1/10'], window=dict(window_pts_start_sec=0))
        value = cs.result('{"segments":[]}', a, dict(window_source_pts_sec=[0., .1]))
        self.assertEqual(value['status'], 'LEGAL_EMPTY'); self.assertEqual(value['native_frame_ranges'], [])

    def test_positive_without_physical_source_frame_rejected(self):
        a = dict(raw_start='0', raw_end='1', eligible_points=['0', '1/2'], window=dict(window_pts_start_sec=0))
        with self.assertRaises(ValueError):
            cs.result('{"segments":[[0.1,0.2]]}', a, dict(window_source_pts_sec=[0., .5]))

    def test_malformed_raw_does_not_become_empty(self):
        a = dict(raw_start='0', raw_end='1', eligible_points=['0', '1/2'], window=dict(window_pts_start_sec=0))
        for raw in ('bad', '{"segments":[[0.5,0.1]]}', '{"segments":[[0,2]]}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                cs.result(raw, a, dict(window_source_pts_sec=[0., .5]))

    def test_float_exact_native_membership_disagreement_rejected(self):
        a = dict(raw_start='0', raw_end='1', eligible_points=['0', '1/10', '1/5'], window=dict(window_pts_start_sec=0))
        with self.assertRaises(ValueError):
            cs.result('{"segments":[[0.1,0.2]]}', a, dict(window_source_pts_sec=[0., .09, .21]))

    def test_selected_frames_use_source_ordinals(self):
        metadata = dict(video_id='v', source_path='/source.mp4', width=1920, height=1080,
                        n_frames=200, fps_num=30, fps_den=1, targetRatioWH=[9, 16])
        a = dict(video_id='v', first_ordinal=100, raw_start='10', raw_end='11',
                 eligible_points=['10', '101/10', '51/5', '103/10'])
        p = dict(manifest=dict(records=[metadata]), attempts=[a])
        r = dict(attempts=[dict(result=dict(parsed_segments=[['1/10', '3/10']], native_frame_ranges=[[1, 3]], status='MODEL_OK'))])
        self.assertEqual([x['source_frame'] for x in selected_frames(p, r)], [101, 102])

    def test_selection_saved_range_tamper_rejected(self):
        a = dict(video_id='v', first_ordinal=100, raw_start='10', raw_end='11', eligible_points=['10', '101/10'])
        p = dict(manifest=dict(records=[]), attempts=[a])
        r = dict(attempts=[dict(result=dict(parsed_segments=[['0', '1/10']], native_frame_ranges=[[0, 2]], status='MODEL_OK'))])
        with self.assertRaises(ValueError):
            selected_frames(p, r)

    def test_empty_selected_list_retains_empty_semantics(self):
        a = dict(video_id='v', first_ordinal=0, raw_start='0', raw_end='1', eligible_points=['0'])
        p = dict(manifest=dict(records=[]), attempts=[a])
        r = dict(attempts=[dict(result=dict(parsed_segments=[], native_frame_ranges=[], status='LEGAL_EMPTY'))])
        self.assertEqual(selected_frames(p, r), [])

    def test_exclusive_receipt_and_sha_tamper(self):
        with tempfile.TemporaryDirectory(prefix='candidate_logic_') as temp:
            path = Path(temp)/'receipt.json'; save(path, dict(status='synthetic'))
            reference = cs.ref(path)
            with self.assertRaises(FileExistsError):
                save(path, dict(status='changed'))
            path.write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError):
                cs.bound(reference)

    def test_foreign_binding_rejected(self):
        with self.assertRaises(ValueError):
            cs.same_binding(dict(binding=dict(final_adapter_sha256='old')), dict(binding=dict(final_adapter_sha256='new')))

    def test_estimate_uses_measured_source_and_eval_sizes(self):
        with tempfile.TemporaryDirectory(prefix='candidate_estimate_') as temp:
            root = Path(temp); lock = {}; refs = {}
            def file(name, value):
                path = root/name; save(path, value); lock[str(path.resolve())] = sha(path); return cs.ref(path)
            plan = file('plan.json', dict(records=426, windows=521, jobs=[dict(windows=[
                dict(window=dict(planned_source_frame_ordinals=list(range(64)))) for unused in range(521)])]))
            evidence = file('proofs.json', dict(proofs=['pure input evidence']*116))
            for key in ('field_frames', 'field_shots', 'anchor_requests', 'anchor_output'):
                refs[key] = file(key+'.json', dict(actual_measured_source_bytes='x'*100))
            spec = file('contract.json', dict(plan=plan, changed_cpu_acceptance=evidence, space=refs))
            for arm in ('original_B', 'new_final'):
                folder = root/arm; folder.mkdir()
                for i in range(12):
                    for kind in ('raw', 'done'):
                        save(folder/('%02d.%s.json'%(i, kind)), dict(actual='x'*200))
            contract = dict(config=dict(candidate_contract=spec, evaluate_output_dir=str(root)), lock=dict(files=lock))
            small = estimate_output_bytes(contract)
            bigger = root/'field_frames.json'; bigger.write_text(json.dumps(dict(actual='x'*10000)), encoding='utf-8')
            refs['field_frames'] = cs.ref(bigger); lock[str(bigger.resolve())] = sha(bigger)
            spec_path = root/'contract.json'; spec_path.write_text(json.dumps(dict(plan=plan, changed_cpu_acceptance=evidence, space=refs)), encoding='utf-8')
            contract['config']['candidate_contract'] = cs.ref(spec_path); lock[str(spec_path.resolve())] = sha(spec_path)
            self.assertGreater(estimate_output_bytes(contract), small)

    def test_estimate_requires_actual24_eval_size_evidence(self):
        with tempfile.TemporaryDirectory(prefix='candidate_estimate_') as temp:
            root = Path(temp); lock = {}
            def file(name, value):
                path = root/name; save(path, value); lock[str(path.resolve())] = sha(path); return cs.ref(path)
            plan = file('plan.json', dict(records=426, windows=521, jobs=[dict(windows=[
                dict(window=dict(planned_source_frame_ordinals=[0])) for unused in range(521)])]))
            proof = file('proof.json', {})
            spec = file('contract.json', dict(plan=plan, changed_cpu_acceptance=proof,
                space={k: proof for k in ('field_frames', 'field_shots', 'anchor_requests', 'anchor_output')}))
            with self.assertRaises(ValueError):
                estimate_output_bytes(dict(config=dict(candidate_contract=spec, evaluate_output_dir=str(root)), lock=dict(files=lock)))

    def test_all11_strict_checks_are_required(self):
        self.assertEqual(len(STRICT_CHECKS), 11)

    def test_unchanged_retains_original_float_duration(self):
        original = 31.26-30.0
        a = dict(changed=False, raw_start='30', raw_end='31.26', window=dict(window_duration_sec=original))
        self.assertIs(type(cs.duration(a)), float)
        self.assertEqual(cs.duration(a), original)
        self.assertNotEqual(F(str(cs.duration(a))), F('1.26'))

    def test_changed_retains_fraction_duration(self):
        a = dict(changed=True, raw_start='23/500', raw_end='7873/500', window=dict(window_duration_sec=15.7))
        self.assertIs(type(cs.duration(a)), F); self.assertEqual(cs.duration(a), F('15.7'))

    def test_actual_video388_tail_duration_regression(self):
        # Root's current read-only Linux excerpt: video388/index2 unchanged.
        a = dict(changed=False, raw_start='60', raw_end='66.72',
                 window=dict(window_duration_sec=6.719999999999999))
        self.assertEqual(cs.duration(a), 66.72-60.0)
        self.assertNotEqual(F(str(cs.duration(a))), F('6.72'))

    def test_unchanged_keeps_original_float_native_authority(self):
        a = dict(changed=False, raw_start='0', raw_end='1', eligible_points=['0', '5/6'],
                 window=dict(window_pts_start_sec=0., window_duration_sec=1.))
        # Exact5/6 is slightly below the registered float rendering. The
        # original float comparison includes this real source frame.
        value = cs.result('{"segments":[[0.8333333333333334,1]]}', a,
                          dict(window_source_pts_sec=[0., float(F('5/6'))]))
        self.assertEqual(value['native_frame_ranges'], [[1, 2]])

    def test_unchanged_package_keeps_same_float_membership(self):
        metadata = dict(video_id='v', source_path='/source.mp4', width=1920, height=1080,
                        n_frames=2, fps_num=30, fps_den=1, targetRatioWH=[9, 16])
        a = dict(changed=False, video_id='v', first_ordinal=0, raw_start='0', raw_end='1',
                 eligible_points=['0', '5/6'], window=dict(window_pts_start_sec=0., window_duration_sec=1.))
        r = cs.result('{"segments":[[0.8333333333333334,1]]}', a,
                      dict(window_source_pts_sec=[0., float(F('5/6'))]))
        self.assertEqual([x['source_frame'] for x in selected_frames(dict(manifest=dict(records=[metadata]), attempts=[a]),
            dict(attempts=[dict(result=r)]))], [1])

    def test_actual_static_helper_import_has_no_decoder_or_model_effect(self):
        helpers = cs.scientific_modules(dict(config=dict(historical_run_root=str(RUN))))
        self.assertEqual(len(helpers), 9)
        self.assertFalse(any(name in sys.modules for name in static.DEFERRED_LIBRARIES))

    def test_static_preflight_requires_no_final_or_quality_and_ignores_cuda_env(self):
        with tempfile.TemporaryDirectory(prefix='candidate_static_') as temp:
            root = Path(temp); output = root/'static.json'; candidate = root/'candidate'
            contract = dict(config=dict(candidate_output_dir=str(candidate)), config_sha='synthetic',
                            lock_sha='synthetic', lock_path='synthetic')
            attempts = [dict(video_id='v%d'%(i if i < 426 else i-426), changed=i < 116) for i in range(521)]
            spec = {k:dict(path='synthetic_'+k, sha256='synthetic') for k in ('plan', 'manifest', 'clock_registry', 'changed_cpu_acceptance')}
            spec.update(space={}, strict_loader_root='synthetic')
            fixture = dict(attempts=attempts, clocks={i:{} for i in range(426)}, spec=spec,
                           spec_ref=dict(path='synthetic', sha256='synthetic'), space_stage=dict(rows=31295))
            with patch.object(cs, 'prepare', return_value=fixture), patch.object(static, 'verify_lock'), \
                    patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES':'0'}):
                result = static.execute(contract, output)
            self.assertFalse(candidate.exists()); self.assertTrue(output.is_file())
            self.assertFalse(result['model_loaded']); self.assertFalse(result['processor_loaded'])
            self.assertFalse(result['native_decoder_called']); self.assertFalse(result['final_adapter_or_quality_receipt_required'])
            self.assertEqual(result['planned_temporal_calls'], 521)
            with self.assertRaises(ValueError):
                static.execute(contract, output)

    def test_static_binding_failure_creates_no_candidate_or_success_receipt(self):
        with tempfile.TemporaryDirectory(prefix='candidate_static_') as temp:
            root = Path(temp); output = root/'static.json'; candidate = root/'candidate'
            with patch.object(cs, 'prepare', side_effect=ValueError('synthetic wrong binding')):
                with self.assertRaises(ValueError):
                    static.execute(dict(config=dict(candidate_output_dir=str(candidate))), output)
            self.assertFalse(output.exists()); self.assertFalse(candidate.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
