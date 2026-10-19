"""Synthetic RGB/patches and fake template/tokenizer only; no real processor."""
import copy
import unittest

import numpy as np
from PIL import Image
import torch

import crop_image_input_v31 as inputs


def image_pixels(h, w, offset):
    one = torch.arange(h*w*3*16*16, dtype=torch.float32).reshape(h*w, 3, 16, 16)+offset
    return torch.stack((one, one), dim=2).reshape(h*w, 1536)


class FakeTokenizer:
    def __init__(self):
        self.special = {'<vs>': 91, '<ve>': 92, '<i>': 93, '0': 71, '1': 72, '2': 73}

    def encode(self, text, **kwargs):
        result, index = [], 0
        while index < len(text):
            token = next((v for v in self.special if text.startswith(v, index)), None)
            if token is None:
                result.append(1000+ord(text[index])); index += 1
            else:
                result.append(self.special[token]); index += len(token)
        return result

    def __call__(self, text, **kwargs):
        ids = torch.tensor([self.encode(text[0] if isinstance(text, list) else text)], dtype=torch.int64)
        return dict(input_ids=ids, attention_mask=torch.ones_like(ids))

    def convert_tokens_to_ids(self, token):
        return self.special[token]


class ForbiddenImageProcessor:
    merge_size = 2
    model_input_names = ['pixel_values', 'image_grid_thw']

    def __call__(self, *args, **kwargs):
        raise AssertionError('Real image processor must never be invoked in pure tests')


class FakeProcessor:
    vision_start_token, image_token, vision_end_token = '<vs>', '<i>', '<ve>'

    def __init__(self):
        self.tokenizer = FakeTokenizer()
        self.image_processor = ForbiddenImageProcessor()

    def apply_chat_template(self, messages, add_generation_prompt, **kwargs):
        content = messages[0]['content']
        text = '<user>'+''.join(c['text'] if c['type'] == 'text' else '<vs><i><ve>' for c in content)+'</user>'
        return text+('<assistant>' if add_generation_prompt else '')

    def __call__(self, text, images, **kwargs):
        adopted = self.image_processor(images=images)
        pieces = text[0].split('<vs><i><ve>')
        expanded = pieces[0]
        for row, tail in zip(adopted['image_grid_thw'].tolist(), pieces[1:]):
            expanded += '<vs>'+'<i>'*(row[0]*row[1]*row[2]//4)+'<ve>'+tail
        return dict(**self.tokenizer(expanded), **adopted)


class CropImageTests(unittest.TestCase):
    def test_physical_fractional_crop_and_independent_rgb_geometry_check(self):
        y, x = np.indices((40, 80))
        rgb = np.stack((x, y, (x+3*y) % 256), axis=-1).astype(np.uint8)
        original = rgb.copy()
        box = [1, 2, 33]
        actual, meta = inputs.render_crop(rgb, box)
        self.assertEqual(actual.shape, (180, 320, 3))
        self.assertEqual(meta['extent_xyxy'], [1, 2, 34, 20.5625])
        expected = np.asarray(Image.fromarray(rgb).transform((320, 180), Image.Transform.EXTENT,
            (1, 2, 34, 20.5625), resample=Image.Resampling.BICUBIC))
        self.assertTrue(np.array_equal(actual, expected))
        self.assertTrue(np.array_equal(rgb, original))
        self.assertTrue(inputs.independent_render_check(rgb, box, actual, meta)['status'].startswith('PASS'))

    def test_render_check_rejects_changed_pixels_extent_source_and_illegal_box(self):
        rgb = np.arange(40*80*3, dtype=np.uint8).reshape(40, 80, 3)
        actual, meta = inputs.render_crop(rgb, [1, 2, 33])
        bad = actual.copy(); bad[0, 0, 0] ^= 1
        with self.assertRaises(ValueError): inputs.independent_render_check(rgb, [1, 2, 33], bad, meta)
        wrong = copy.deepcopy(meta); wrong['extent_xyxy'][3] = 20
        with self.assertRaises(ValueError): inputs.independent_render_check(rgb, [1, 2, 33], actual, wrong)
        changed = rgb.copy(); changed[-1, -1, -1] ^= 1
        with self.assertRaises(ValueError): inputs.independent_render_check(changed, [1, 2, 33], actual, meta)
        with self.assertRaises(ValueError): inputs.render_crop(rgb, [0, 30, 33])
        with self.assertRaises(ValueError): inputs.render_crop(rgb.astype(np.float32), [0, 0, 16])

    def test_adopted_source_new_crops_keep_flat_order_and_grid_without_mutation(self):
        grid = torch.tensor([[1, 2, 4], [1, 4, 2], [1, 2, 2]], dtype=torch.int64)
        pixels = [image_pixels(2, 4, 0), image_pixels(4, 2, 100000), image_pixels(2, 2, 200000)]
        original = [v.clone() for v in pixels]
        packed = inputs.pack_image_pixels(pixels, grid)
        self.assertEqual(list(packed['pixel_values'].shape), [20, 1536])
        self.assertTrue(inputs.independent_pixel_check(pixels, grid, packed)['status'].startswith('PASS'))
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(original, pixels)))
        packed['pixel_values'][8, 0] += 1
        with self.assertRaises(ValueError): inputs.independent_pixel_check(pixels, grid, packed)

    def test_bad_static_slices_nonfinite_grid_and_count_fail(self):
        for mode in ('bits', 'nan', 'grid', 'count'):
            pixels = [image_pixels(2, 2, i*100000) for i in range(3)]
            grid = [[1, 2, 2]]*3
            if mode == 'bits': pixels[0][0, 256] = -0.0
            elif mode == 'nan': pixels[1][0, 0] = float('nan')
            elif mode == 'grid': grid = [[1, 3, 2]]*3
            else: pixels.pop()
            with self.assertRaises(ValueError): inputs.pack_image_pixels(pixels, grid)

    def test_three_image_text_actual_class_ids_and_independent_stub_qa(self):
        grid = torch.tensor([[1, 2, 2]]*3, dtype=torch.int64)
        proc = FakeProcessor(); original = proc.image_processor
        packed = inputs.pack_image_pixels([image_pixels(2, 2, i*100000) for i in range(3)], grid)
        encoded, meta = inputs.build_text_input(proc, grid)
        self.assertEqual(meta['class_token_ids'], [71, 72, 73])
        self.assertEqual(meta['image_tokens_per_image'], [1, 1, 1])
        self.assertEqual(meta['expanded_text'].count('<vs>'), 3)
        self.assertEqual([v['role'] for v in meta['image_positions']], ['Source', 'A', 'B'])
        self.assertTrue(meta['expanded_text'].endswith('<assistant>'))
        self.assertEqual(meta['next_token_prediction_position'], encoded['input_ids'].shape[1]-1)
        self.assertTrue(inputs.independent_text_check(proc, packed, encoded, meta)['status'].startswith('PASS'))
        self.assertIs(proc.image_processor, original)
        wrong = copy.deepcopy(meta); wrong['class_token_ids'][0] = 999
        with self.assertRaises(ValueError): inputs.independent_text_check(proc, packed, encoded, wrong)

    def test_class_collision_multitoken_context_merge_and_full_budget_fail(self):
        for mode in ('collision', 'multi', 'merge', 'budget'):
            proc = FakeProcessor()
            if mode == 'collision': proc.tokenizer.special['2'] = 72
            elif mode == 'multi':
                original = proc.tokenizer.encode
                proc.tokenizer.encode = lambda text, **kw: [8, 9] if text == '2' else original(text, **kw)
            elif mode == 'merge':
                # Put the longer combined token first, independently of normal special tokens.
                proc.tokenizer.special = {'<assistant>0': 99, **proc.tokenizer.special}
            else:
                template = proc.apply_chat_template
                proc.apply_chat_template = lambda *a, **kw: 'x'*4096+template(*a, **kw)
            with self.assertRaises(ValueError): inputs.build_text_input(proc, [[1, 2, 2]]*3)
        with self.assertRaises(TypeError): inputs.build_text_input(FakeProcessor(), [[1, 2, 2]]*3, labels=[0])


if __name__ == '__main__':
    unittest.main()
