"""Synthetic patches and a fake three-video processor only; no real model IO."""
import copy
from fractions import Fraction
from types import SimpleNamespace
import unittest

import torch

from context_video_input import (QUESTION, OVERVIEW_NOTE, build_context_pixels, build_context_text,
                                independent_context_pixel_check, independent_context_text_check)


def frames(count, h=2, w=2, offset=0):
    result = []
    for i in range(count):
        one = torch.arange(h*w*3*256, dtype=torch.float32).reshape(h*w, 3, 16, 16)+10000*i+offset
        result.append(torch.stack([one, one], dim=2).reshape(h*w, 1536))
    return result


def fixture(count=80, foreign=False):
    local = frames(count); points = [str(Fraction(i*i, 10)) for i in range(count)]
    ranges = [[8, 16], [24, 32]] if count >= 32 else [[0, 8], [0, 8]]
    overview = frames(90, offset=10000000) if foreign else local
    overview_points = [str(Fraction(i, 3)) for i in range(90)] if foreign else points
    args = (local, [2, 2], ranges, list(range(count)), points,
            overview, [2, 2], list(range(len(overview))), overview_points)
    kwargs = dict(local_owner=dict(source_id='local', source_sha256='a'*64),
                  overview_owner=dict(source_id='foreign', source_sha256='b'*64) if foreign else
                                 dict(source_id='local', source_sha256='a'*64), overview_is_foreign=foreign)
    return args, kwargs


class FakeTokenizer:
    special = {'<vs>':91, '<ve>':92, '<v>':93, '0':71, '1':72, '2':73}

    def encode(self, text, add_special_tokens=False):
        tokens = []; i = 0
        while i < len(text):
            marker = next((s for s in self.special if text.startswith(s, i)), None)
            if marker:
                tokens.append(self.special[marker]); i += len(marker)
            else:
                tokens.append(1000+ord(text[i])); i += 1
        return tokens

    def __call__(self, text, **kwargs):
        text = text[0] if isinstance(text, list) else text
        ids = torch.tensor([self.encode(text)], dtype=torch.int64)
        return dict(input_ids=ids, attention_mask=torch.ones_like(ids))

    def convert_tokens_to_ids(self, marker):
        return self.special[marker]


class ForbiddenVideoProcessor:
    merge_size = 2
    model_input_names = ['pixel_values_videos', 'video_grid_thw']

    def __call__(self, *args, **kwargs):
        raise AssertionError('Real video processing is forbidden in pure tests')


class FakeProcessor:
    vision_start_token = '<vs>'; video_token = '<v>'; vision_end_token = '<ve>'

    def __init__(self):
        self.tokenizer = FakeTokenizer(); self.video_processor = ForbiddenVideoProcessor()

    def apply_chat_template(self, messages, add_generation_prompt, **kwargs):
        raw = '<user>'+''.join(c['text'] if c['type'] == 'text' else '<vs><v><ve>'
                               for c in messages[0]['content'])+'</user>'
        return raw+('<assistant>' if add_generation_prompt else '')

    def _calculate_timestamps(self, *args):
        raise AssertionError('Each exact video timestamp list must be supplied by the QA stub')

    def __call__(self, text, videos, **kwargs):
        if len(videos) != 3: raise AssertionError('Exactly three independent videos required')
        result = self.video_processor(videos=videos)
        pieces = text[0].split('<vs><v><ve>'); expanded = pieces[0]
        for index, (grid, meta) in enumerate(zip(result['video_grid_thw'].tolist(), result['video_metadata'])):
            times = self._calculate_timestamps(meta.frames_indices, meta.fps, self.video_processor.merge_size)
            expanded += ''.join(f'<{t:.1f} seconds><vs>'+('<v>'*(grid[1]*grid[2]//4))+'<ve>' for t in times)+pieces[index+1]
        return dict(**self.tokenizer(expanded), pixel_values_videos=result['pixel_values_videos'], video_grid_thw=result['video_grid_thw'])


class ContextInputTests(unittest.TestCase):
    def test_true_overview64_includes_endpoints_and_has_three_grids_without_mutation(self):
        args, kwargs = fixture(); saved = [x.clone() for x in args[0]]
        value = build_context_pixels(*args, **kwargs)
        self.assertEqual(value['video_grid_thw'].tolist(), [[32, 2, 2], [4, 2, 2], [4, 2, 2]])
        self.assertEqual(value['pixel_values_videos'].shape, (160, 1536))
        overview = value['video_metadata'][0]
        self.assertEqual(overview['source_cell_indices'], [i*79//63 for i in range(64)])
        self.assertEqual(overview['source_cell_indices'][0], 0); self.assertEqual(overview['source_cell_indices'][-1], 79)
        self.assertEqual(value['observation_appearances'], 80)
        self.assertFalse(value['old_two_video_QA_adopted']); self.assertFalse(value['input_admitted'])
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(saved, args[0])))
        self.assertTrue(independent_context_pixel_check(*args, context=value, **kwargs)['status'].startswith('PASS'))

    def test_odd_small_overview_takes_largest_even_with_real_endpoints_no_padding(self):
        args, kwargs = fixture(9); value = build_context_pixels(*args, **kwargs)
        overview = value['video_metadata'][0]
        self.assertEqual(overview['observations'], 8)
        self.assertEqual(overview['source_cell_indices'], [i*8//7 for i in range(8)])
        self.assertEqual(overview['padded_observations'], 0)
        self.assertEqual(value['video_grid_thw'].tolist(), [[4, 2, 2]]*3)

    def test_foreign_control_uses_own_actual_owner_clock_and64_observations(self):
        args, kwargs = fixture(foreign=True); value = build_context_pixels(*args, **kwargs)
        overview, a, b = value['video_metadata']
        self.assertEqual(overview['owner']['source_id'], 'foreign')
        self.assertEqual(a['owner']['source_id'], b['owner']['source_id']); self.assertEqual(a['owner']['source_id'], 'local')
        self.assertEqual(overview['timestamps_exact'][0], '1/6')
        self.assertTrue(all(row['owner'] == kwargs['overview_owner'] for row in value['sample_bindings'][:64]))
        self.assertTrue(all(row['owner'] == kwargs['local_owner'] for row in value['sample_bindings'][64:]))
        independent_context_pixel_check(*args, context=value, **kwargs)

    def test_overview_global_times_and_local_clip_times_remain_separate(self):
        args, kwargs = fixture(); value = build_context_pixels(*args, **kwargs)
        overview, a, b = value['video_metadata']
        self.assertEqual(overview['timestamp_scope'], 'OWN_SOURCE_GLOBAL_NORMALIZED_PTS')
        self.assertEqual(a['timestamp_scope'], 'OWN_CLIP_LOCAL_NORMALIZED_PTS')
        self.assertEqual(a['origin_exact'], '32/5')
        self.assertEqual(a['timestamps_exact'][0], '17/20')
        self.assertEqual(b['origin_exact'], '288/5')
        self.assertEqual(b['timestamps_exact'][0], '49/20')

    def test_false_foreign_identity_wrong_grid_or_wrong_true_clock_fail(self):
        args, kwargs = fixture(foreign=True)
        for change in (dict(overview_is_foreign=False), dict(overview_owner=kwargs['local_owner'])):
            with self.assertRaises(ValueError): build_context_pixels(*args, **dict(kwargs, **change))
        bad = list(args); bad[6] = [2, 4]
        with self.assertRaises(ValueError): build_context_pixels(*bad, **kwargs)
        args, kwargs = fixture(); bad = list(args); bad[-1] = [str(Fraction(i, 2)) for i in range(80)]
        with self.assertRaises(ValueError): build_context_pixels(*bad, **kwargs)

    def test_flat_pixel_qa_and_owner_bindings_reject_corruption(self):
        args, kwargs = fixture(); value = build_context_pixels(*args, **kwargs)
        value['pixel_values_videos'][0, 256] += 1
        with self.assertRaises(ValueError): independent_context_pixel_check(*args, context=value, **kwargs)
        value = build_context_pixels(*args, **kwargs); value['sample_bindings'][0]['owner']['source_sha256'] = 'c'*64
        with self.assertRaises(ValueError): independent_context_pixel_check(*args, context=value, **kwargs)

    def test_image_temporal_slices_require_bit_identity_and_sufficient_real_observations(self):
        args, kwargs = fixture(); args[0][0][0, 0] = -0.0
        with self.assertRaises(ValueError): build_context_pixels(*args, **kwargs)
        args, kwargs = fixture(); bad = list(args); bad[5] = bad[5][:1]; bad[7] = [0]
        with self.assertRaises(ValueError): build_context_pixels(*bad, **kwargs)
        args, kwargs = fixture(foreign=True); bad = list(args); bad[5] = bad[5][:32]; bad[7] = list(range(32))
        with self.assertRaises(ValueError): build_context_pixels(*bad, **kwargs)

    def test_fixed_question_three_markers_class_ids_and_final_position(self):
        args, kwargs = fixture(); context = build_context_pixels(*args, **kwargs)
        encoded, meta = build_context_text(FakeProcessor(), context)
        self.assertEqual(meta['question'], QUESTION); self.assertEqual(meta['overview_note'], OVERVIEW_NOTE)
        self.assertEqual(meta['raw_template'].count('<vs><v><ve>'), 3)
        self.assertEqual(meta['class_token_ids'], [71, 72, 73])
        self.assertEqual(meta['next_token_prediction_position'], encoded['input_ids'].shape[1]-1)
        self.assertTrue(meta['expanded_text'].endswith('<assistant>'))
        self.assertEqual(meta['video_token_count'], 40)
        self.assertEqual([len(v['group_token_positions']) for v in meta['video_positions']], [32, 4, 4])
        self.assertLess(encoded['input_ids'].shape[1], 4096)

    def test_first_three_video_text_stub_consumes_three_own_timestamp_lists(self):
        args, kwargs = fixture(foreign=True); context = build_context_pixels(*args, **kwargs)
        processor = FakeProcessor(); original = processor.video_processor
        encoded, meta = build_context_text(processor, context)
        evidence = independent_context_text_check(processor, context, encoded, meta)
        self.assertEqual(evidence['timestamp_sequences'], 3)
        self.assertEqual(evidence['real_video_processor_calls'], 0)
        self.assertIs(processor.video_processor, original)
        self.assertFalse(evidence['old_two_video_QA_adopted'])

    def test_token_budget_duplicate_or_multitoken_classes_fail(self):
        args, kwargs = fixture(); context = build_context_pixels(*args, **kwargs)
        large = copy.deepcopy(context); large['video_grid_thw'][:, 1:] = 32
        with self.assertRaises(ValueError): build_context_text(FakeProcessor(), large)
        processor = FakeProcessor(); processor.tokenizer.special = dict(processor.tokenizer.special, **{'2':72})
        with self.assertRaises(ValueError): build_context_text(processor, context)
        processor = FakeProcessor(); encode = processor.tokenizer.encode
        processor.tokenizer.encode = lambda text, **options: [73, 74] if text == '2' else encode(text, **options)
        with self.assertRaises(ValueError): build_context_text(processor, context)

    def test_independent_text_qa_rejects_changed_class_evidence(self):
        args, kwargs = fixture(); context = build_context_pixels(*args, **kwargs); processor = FakeProcessor()
        encoded, meta = build_context_text(processor, context); meta['class_token_ids'] = [72, 71, 73]
        with self.assertRaises(ValueError): independent_context_text_check(processor, context, encoded, meta)

    def test_optional_refs_are_carried_without_file_reads(self):
        args, kwargs = fixture(); references = dict(local_ref=dict(path='/bound/local.json', sha256='c'*64),
            overview_ref=dict(path='/bound/local.json', sha256='c'*64),
            pairing_proof_ref=dict(path='/bound/old-proof.json', sha256='d'*64))
        context = build_context_pixels(*args, **kwargs, **references)
        self.assertEqual(context['source_refs']['local'], references['local_ref'])
        self.assertEqual(context['video_metadata'][0]['source_ref'], references['overview_ref'])
        self.assertEqual(context['old_synthetic_pairing_proof'], references['pairing_proof_ref'])


if __name__ == '__main__':
    unittest.main()
