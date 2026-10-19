import copy
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

import crop_policy_v33 as policy
import utility_star_review_v70 as qa
import utility_star_math_v68 as math68
from test_utility_star_gpu_v69 import r, run_synthetic_screen


def complete_state():
    matrices = {}
    for layer in range(36):
        for projection in ('q_proj', 'k_proj', 'v_proj', 'o_proj'):
            for kind, shape in (('A', (8, 4096)), ('B', ((4096 if projection in ('q_proj', 'o_proj') else 1024), 8))):
                matrices[f'base_model.model.model.language_model.layers.{layer}.self_attn.{projection}.lora_{kind}.weight'] = torch.zeros(shape)
    head, beta = torch.ones((1, 4096))*.001, torch.zeros(11)
    values = list(matrices.values())+[head, beta]
    names = [list(matrices), ['head.weight'], ['geometry_beta']]
    n = np.random.RandomState(0).get_state()
    return dict(schema='UTILITY_STAR_COMPLETE_UPDATE_PROGRESS_V69', step=504, micro=2016, logical_training_forwards=4032,
        new_updates=4, new_micro=16, new_training_forwards=32, inherited_updates=500, inherited_micro=2000,
        inherited_training_forwards=4000, inherited_progress=r('old500'), schedule_sha256='schedule',
        train_schedule_reference=r('prepared'), recipe=qa.RECIPE, train_target_RMS=math68.TARGET_RMS,
        adapter_state_dict=matrices, head_state_dict=dict(weight=head), geometry_beta=beta,
        optimizer_parameter_names_by_group=names, optimizer_parameter_names_sha256=math68.digest(names),
        optimizer_state_dict=dict(state={i:dict(step=torch.tensor(504.), exp_avg=torch.zeros_like(v), exp_avg_sq=torch.zeros_like(v)) for i, v in enumerate(values)},
            param_groups=[dict(params=list(range(288)), lr=5e-5, weight_decay=0.),
                dict(params=[288], lr=.001, weight_decay=0.), dict(params=[289], lr=.001, weight_decay=0.)]),
        torch_rng_state=torch.Generator().get_state(), torch_cuda_rng_state_all=[torch.zeros(16, dtype=torch.uint8)],
        numpy_rng_state=dict(name=n[0], keys=torch.tensor(n[1].astype(np.int64)), position=n[2], has_gauss=n[3], cached_gaussian=n[4]),
        python_rng_state=random.Random(0).getstate(), original_TIME_loaded=False, old_PAIR_loaded=False,
        old_CROP_loaded=False, no_base_tensors_saved=True)


def evaluation_fixture(improved=20):
    sources, pairs, lookup, targets = [], [], {}, {}
    for i in range(20):
        sid = 'source'+str(i); digest = f'{i:064x}'
        sources.append(dict(source_id=sid, source_sha256=digest, role='screen', width=20, height=20, pool=[[0, 0, 16], [2, 2, 8]]))
        own, first, reverse = sid+'self', sid+'f', sid+'r'
        for identifier, value in ((own, 0.), (first, 2. if i < improved else 0.), (reverse, 0.)):
            h = np.zeros(4096); h[0] = value
            lookup[identifier] = dict(source_id=sid, source_sha256=digest, hidden4096=h)
        pairs.extend([dict(source_id=sid, candidate_index=0, first_id=own, reverse_id=own, same_crop=True),
            dict(source_id=sid, candidate_index=1, first_id=first, reverse_id=reverse, same_crop=False)])
        targets[sid] = [.4, .8]
    weight = torch.zeros((1, 4096)); weight[0, 0] = 1.
    return sources, pairs, lookup, targets, dict(weight=weight, geometry_beta=torch.zeros(11)), dict(RMS=np.ones(14), GEOM11_beta=np.zeros(11)), np.zeros(13), policy


class StarReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): torch.set_num_threads(2)

    def test_complete504_adam_global_counts_and_stale500_rejected(self):
        state = complete_state()
        result = qa.validate_progress(state, 504, 'schedule', r('prepared'), qa.RECIPE, math68.TARGET_RMS)
        self.assertEqual(result['adam_states'], 290)
        self.assertEqual(result['micro'], 2016)
        for field in ('adam', 'new_count', 'old_schema', 'RMS'):
            bad = copy.deepcopy(state)
            if field == 'adam': bad['optimizer_state_dict']['state'][289]['step'] = torch.tensor(500.)
            if field == 'new_count': bad['new_updates'] = 504
            if field == 'old_schema': bad['schema'] = 'UTILITY_R8_COMPLETE_UPDATE_PROGRESS_V55'
            if field == 'RMS': bad['train_target_RMS'] = .2
            with self.assertRaises(ValueError): qa.validate_progress(bad, 504, 'schedule', r('prepared'), qa.RECIPE, math68.TARGET_RMS)

    def test_global_micro_replays_new_schedule_row0_without_replay_old2000(self):
        schedule = [dict(id='S'+str(i), source_id='s', target=-.2, draw_weight=1.25,
            forward=dict(id='f'+str(i)), reverse=dict(id='r'+str(i))) for i in range(3200)]
        events = []
        for index in range(16):
            micro = index+2000; row = schedule[index]
            common = dict(step=micro//4+1, micro=micro, id=row['id'])
            owner = dict(source_id='s', forward_id=row['forward']['id'], reverse_id=row['reverse']['id'])
            loss = 1.25*((.3+.2)/math68.TARGET_RMS)**2
            events.extend([dict(common, **owner, event='BEGIN_TRAIN_MICRO'),
                dict(common, **owner, event='TRAIN_RAW_LOSS', target=-.2, draw_weight=1.25, target_RMS=math68.TARGET_RMS, prediction=.3, loss=loss),
                dict(common, event='TRAIN_BACKWARD_COMPLETE')])
        report = qa.validate_micro_logs(events, schedule, 501, 504, math68.TARGET_RMS)
        self.assertEqual(report['actual_dual_training_forwards'], 32)
        bad = copy.deepcopy(events); bad[1]['target'] = .2
        with self.assertRaises(ValueError): qa.validate_micro_logs(bad, schedule, 501, 504, math68.TARGET_RMS)

    def test_real69_receipts_aliases_cpu_dot_and_raw_first70(self):
        with tempfile.TemporaryDirectory() as temp:
            completion, expected, values, _ = run_synthetic_screen(temp)
            with mock.patch.object(qa, 'bound', side_effect=lambda ref:Path(ref['path'])):
                lookup, predictions, engineering = qa.review_screen(completion, expected, [15, 16, 17], r('adapter'), r('value'), values, registration_ref=r('reg'))
                self.assertEqual(len(lookup), 240)
                self.assertEqual((engineering['actual_new_forwards'], engineering['aliases']), (1, 239))
                self.assertEqual(len(predictions), 240)
                receipt_path = Path(qa.read(completion['path'])['entries'][0]['receipt']['path'])
                receipt = qa.read(receipt_path); receipt['head_value'] += .1
                receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
                with self.assertRaises(ValueError):
                    qa.review_screen(completion, expected, [15, 16, 17], r('adapter'), r('value'), values, registration_ref=r('reg'))

    def test_original20_quality_gate_and_controls_unchanged(self):
        admitted = qa.evaluate_scope(*evaluation_fixture())
        self.assertTrue(admitted['quality']['admitted'])
        self.assertEqual(admitted['self_gain_exact_zero'], 20)
        stopped = qa.evaluate_scope(*evaluation_fixture(improved=2))
        self.assertGreater(stopped['summaries']['UTILITY']['mean_gain'], .01)
        self.assertFalse(stopped['quality']['checks']['improved_sources'])
        self.assertFalse(stopped['quality']['admitted'])
        self.assertEqual(qa.choose([0., 0., -.1]), 0)
        self.assertEqual(qa.choose([0., .1, .1]), 1)


if __name__ == '__main__': unittest.main()
