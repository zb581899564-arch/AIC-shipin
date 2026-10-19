"""Synthetic tensors/fake tokenizer only; no real processor, model or data."""
import copy
from fractions import Fraction
from types import SimpleNamespace
import unittest

import torch

from pair_video_input import (QUESTION, build_text_input, independent_pixel_check,
                             independent_text_check, pair_video_pixels)


def frames(count=20, h=2, w=2):
    result = []
    for index in range(count):
        value = torch.arange(h*w*3*16*16, dtype=torch.float32).reshape(h*w, 3, 16, 16)+index*100000
        result.append(torch.stack((value, value), dim=2).reshape(h*w, 1536))
    return result


def inputs():
    return frames(), [2, 2], [[0, 8], [12, 20]], list(range(20)), [str(Fraction(i*i, 10)) for i in range(20)]


class FakeTokenizer:
    special = {'<vs>': 91, '<ve>': 92, '<v>': 93, '0': 71, '1': 72, '2': 73}

    def encode(self, text, add_special_tokens=False):
        ids = []; index = 0
        while index < len(text):
            token = next((s for s in self.special if text.startswith(s, index)), None)
            if token is not None:
                ids.append(self.special[token]); index += len(token)
            else:
                ids.append(1000+ord(text[index])); index += 1
        return ids

    def __call__(self, text, **kwargs):
        value = text[0] if isinstance(text, list) else text
        ids = torch.tensor([self.encode(value)], dtype=torch.int64)
        return dict(input_ids=ids, attention_mask=torch.ones_like(ids))

    def convert_tokens_to_ids(self, token):
        return self.special[token]


class ForbiddenVideoProcessor:
    merge_size = 2
    model_input_names = ['pixel_values_videos', 'video_grid_thw']

    def __call__(self, *args, **kwargs):
        raise AssertionError('A real video processor must never run in these tests')


class FakeProcessor:
    vision_start_token = '<vs>'
    video_token = '<v>'
    vision_end_token = '<ve>'

    def __init__(self):
        self.tokenizer = FakeTokenizer(); self.video_processor = ForbiddenVideoProcessor()

    def apply_chat_template(self, messages, add_generation_prompt, **kwargs):
        value = '<user>'+''.join(c['text'] if c['type'] == 'text' else '<vs><v><ve>' for c in messages[0]['content'])+'</user>'
        return value+('<assistant>' if add_generation_prompt else '')

    def _calculate_timestamps(self, *args):
        raise AssertionError('Independent QA must supply each exact clip timestamp list')

    def __call__(self, text, videos, **kwargs):
        value = self.video_processor(videos=videos)
        marker = '<vs><v><ve>'; pieces = text[0].split(marker); expanded = []
        for grid, meta in zip(value['video_grid_thw'].tolist(), value['video_metadata']):
            times = self._calculate_timestamps(meta.frames_indices, meta.fps, self.video_processor.merge_size)
            expanded.append(''.join(f'<{t:.1f} seconds><vs>'+('<v>'*(grid[1]*grid[2]//4))+'<ve>' for t in times))
        tokens = self.tokenizer(pieces[0]+expanded[0]+pieces[1]+expanded[1]+pieces[2])
        return dict(**tokens, pixel_values_videos=value['pixel_values_videos'], video_grid_thw=value['video_grid_thw'])


class PairVideoInputTests(unittest.TestCase):
    def test_two_grids_exact_pixels_source_bindings_and_no_mutation(self):
        args = inputs(); saved = [x.clone() for x in args[0]]
        pair = pair_video_pixels(*args)
        self.assertEqual(pair['video_grid_thw'].tolist(), [[4, 2, 2], [4, 2, 2]])
        self.assertEqual(tuple(pair['pixel_values_videos'].shape), (32, 1536))
        self.assertEqual(pair['sample_bindings'][8]['source_cell'], 12)
        self.assertEqual(pair['sample_bindings'][8]['clip'], 'B')
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(args[0], saved)))
        self.assertTrue(independent_pixel_check(*args, pair)['status'].startswith('PASS'))
        self.assertFalse(pair['input_admitted'])

    def test_vfr_centers_reset_independently_per_clip(self):
        pair = pair_video_pixels(*inputs())
        a, b = pair['clip_metadata']
        self.assertEqual(a['relative_group_centers_exact'][0], '1/20')
        self.assertEqual(b['origin_exact'], '72/5')
        self.assertEqual(b['relative_group_centers_exact'][0], '5/4')
        self.assertNotEqual(a['relative_group_centers_exact'], b['relative_group_centers_exact'])

    def test_no_short_tail_or_unaligned_group_or_out_of_bounds(self):
        args = inputs()
        for ranges in ([[0, 7], [12, 20]], [[1, 9], [12, 20]], [[0, 8], [14, 22]]):
            with self.assertRaises(ValueError): pair_video_pixels(args[0], args[1], ranges, args[3], args[4])

    def test_overlap_is_explicit_and_does_not_invent_independent_samples(self):
        args = inputs(); args = (*args[:2], [[0, 8], [4, 12]], *args[3:])
        pair = pair_video_pixels(*args)
        self.assertEqual(pair['shared_native_ordinals'], [4, 5, 6, 7])
        self.assertEqual(pair['observation_appearances'], 16)
        self.assertEqual(pair['distinct_native_observations'], 12)

    def test_nonfinite_wrong_grid_and_nonidentical_temporal_bits_fail(self):
        for mode in ('nan', 'bits', 'shape'):
            args = inputs()
            if mode == 'nan': args[0][0][0, 0] = float('nan')
            elif mode == 'bits': args[0][0][0, 256] = -0.0
            else: args[0][0] = args[0][0][:, :-1]
            with self.assertRaises(ValueError): pair_video_pixels(*args)

    def test_bad_clock_duplicate_ordinals_and_gt_argument_rejected(self):
        args = inputs()
        bad = list(args[4]); bad[1] = .1
        with self.assertRaises(ValueError): pair_video_pixels(*args[:4], bad)
        bad_ids = list(args[3]); bad_ids[1] = 0
        with self.assertRaises(ValueError): pair_video_pixels(*args[:3], bad_ids, args[4])
        with self.assertRaises(TypeError): pair_video_pixels(*args, targets=[0, 1])

    def test_two_original_markers_each_expand_once_when_one_token_per_group(self):
        pair = pair_video_pixels(*inputs()); encoded, meta = build_text_input(FakeProcessor(), pair)
        self.assertEqual(meta['expanded_text'].count('<vs>'), 8)
        self.assertIn(QUESTION+'A:', meta['raw_template']); self.assertIn('B:', meta['raw_template'])
        self.assertEqual(len(meta['clip_positions']), 2)
        self.assertEqual(sum(len(g) for c in meta['clip_positions'] for g in c['group_token_positions']), 8)
        self.assertEqual(meta['class_token_ids'], [71, 72, 73])
        self.assertEqual(meta['class_tokens_by_digit'], {'0': 71, '1': 72, '2': 73})
        self.assertEqual(meta['next_token_prediction_position'], encoded['input_ids'].shape[1]-1)

    def test_final_assistant_prefix_has_no_answer_and_digits_are_next_tokens(self):
        pair = pair_video_pixels(*inputs()); proc = FakeProcessor(); encoded, meta = build_text_input(proc, pair)
        self.assertTrue(meta['expanded_text'].endswith('<assistant>'))
        for digit, token in meta['class_tokens_by_digit'].items():
            full = proc.tokenizer(meta['expanded_text']+digit)['input_ids']
            self.assertTrue(torch.equal(full[:, :-1], encoded['input_ids']))
            self.assertEqual(int(full[0, -1]), token)

    def test_nonunique_multitoken_or_context_merged_digit_fails(self):
        pair = pair_video_pixels(*inputs())
        for mode in ('duplicate', 'multi', 'merge'):
            proc = FakeProcessor(); proc.tokenizer.special = dict(FakeTokenizer.special)
            if mode == 'duplicate': proc.tokenizer.special['2'] = proc.tokenizer.special['1']
            elif mode == 'multi':
                original = proc.tokenizer.encode
                proc.tokenizer.encode = lambda text, **kw: [8, 9] if text == '2' else original(text, **kw)
            else: proc.tokenizer.special['<assistant>0'] = 999
            with self.assertRaises(ValueError): build_text_input(proc, pair)

    def test_input_plus_next_digit_budget_is_checked_without_truncation(self):
        pair = pair_video_pixels(*inputs()); proc = FakeProcessor(); original = proc.apply_chat_template
        proc.apply_chat_template = lambda *args, **kw: 'x'*4096+original(*args, **kw)
        with self.assertRaises(ValueError): build_text_input(proc, pair)

    def test_independent_pixel_qa_detects_corrupted_boundary(self):
        args = inputs(); pair = pair_video_pixels(*args)
        pair['pixel_values_videos'][16, 0] += 1
        with self.assertRaises(ValueError): independent_pixel_check(*args, pair)

    def test_independent_text_qa_uses_two_timestamp_sequences_and_restores_stub(self):
        pair = pair_video_pixels(*inputs()); proc = FakeProcessor(); encoded, meta = build_text_input(proc, pair)
        original = proc.video_processor
        report = independent_text_check(proc, pair, encoded, meta)
        self.assertIs(proc.video_processor, original)
        self.assertEqual(report['timestamp_sequences'], 2); self.assertEqual(report['real_video_processor_calls'], 0)
        wrong = copy.deepcopy(meta); wrong['class_token_ids'][0] = 123
        wrong['class_tokens_by_digit']['0'] = 123
        with self.assertRaises(ValueError): independent_text_check(proc, pair, encoded, wrong)
        changed = copy.deepcopy(pair)
        changed['clip_metadata'][1]['relative_group_centers_exact'] = changed['clip_metadata'][0]['relative_group_centers_exact']
        with self.assertRaises(ValueError): independent_text_check(proc, changed, encoded, meta)


if __name__ == '__main__':
    unittest.main()
