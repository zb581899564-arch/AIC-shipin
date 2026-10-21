"""First bounded CPU recovery of seven existing same-frame cache views."""
import inspect
from pathlib import Path
import numpy as np
import torch
from common import ROOT, checked, read, ref, write
from patch_inverse import pack, recover_uint8


def processor_contract():
    from transformers.models.qwen2_vl.image_processing_qwen2_vl_fast import Qwen2VLImageProcessorFast
    processor = Qwen2VLImageProcessorFast(patch_size=16, temporal_patch_size=2, merge_size=2)
    rgb = (np.arange(192 * 320 * 3).reshape(192, 320, 3) % 251).astype(np.uint8)
    result = processor(images=[rgb], do_resize=False, do_rescale=False, do_normalize=False, return_tensors='pt')
    grid = result['image_grid_thw'][0].tolist()
    assert grid == [1, 12, 20]
    frames = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0).repeat(2, 1, 1, 1)
    assert torch.equal(pack(frames, grid), result['pixel_values'])
    return dict(status='PASS_INDEPENDENT_INSTALLED_PROCESSOR_PACKING',
                module=ref(Path(inspect.getfile(Qwen2VLImageProcessorFast))), new_synthetic_processor_calls=1)


def recover_one(source, case):
    context = Path(case['context_path'])
    assert ref(context)['sha256'] == case['context_sha256']
    data = torch.load(context, map_location='cpu', weights_only=True)
    grids = data['image_grid_thw'].tolist()
    index = case['context_query_index']
    assert grids[index] == case['grid']
    lengths = [int(np.prod(g)) for g in grids]
    start = sum(lengths[:index])
    pixels = data['pixel_values'][start:start + lengths[index]]
    profile = read(checked(case['profile']))
    assert profile['processor_dict']['patch_size'] == 16
    assert profile['processor_dict']['temporal_patch_size'] == 2
    assert profile['processor_dict']['merge_size'] == 2
    rgb, quantization_error, normalize_error = recover_uint8(pixels, grids[index], profile['processor_dict'])
    target = ROOT / 'inverse_inputs11' / f'{source["sid"]}_{case["native_ordinal"]}.npy'
    np.save(target, rgb, allow_pickle=False)
    return dict(sid=source['sid'], ordinal=case['native_ordinal'], shape=list(rgb.shape),
          cached_view=ref(target), cached_context_sha256=case['context_sha256'],
          native_clock_identity_already_bound=True, integer_quantization_error=quantization_error,
          normalized_reconstruction_max_error=normalize_error,
          old_normalized_patch_permutation_bit_exact=True,
          original_full_resolution_RGB_recovered=False)


def main():
    inventory = read(ROOT / 'full_view_cache_inventory10.json')
    cases = [(source, source['chosen'][0]) for source in inventory['sources'] if source['chosen']]
    assert len(cases) == 7 and inventory['selected_frame_count'] == 56
    write(ROOT / 'input_inverse11_registration.json', dict(
          inventory=ref(ROOT / 'full_view_cache_inventory10.json'),
          scope='First hash-selected shared frame in each of7 available sources; inverse cached processor only',
          source_frames=[dict(sid=s['sid'], case=c) for s, c in cases],
          missing_source_not_nearest_matched='V05', new_real_processor_calls=0,
          new_synthetic_processor_calls=1, new_media_decode=0, new_models=0,
          no_labels_or_predictions_used=True, old_STOP_and40_47_unchanged=True))
    contract = processor_contract()
    (ROOT / 'inverse_inputs11').mkdir()
    rows = [recover_one(source, case) for source, case in cases]
    write(ROOT / 'input_inverse11_acceptance.json', dict(
          status='PASS7_FIRST_CACHED_VIEW_INVERSES', contract=contract, sources=rows,
          real_new_processor_calls=0, new_decode=0, new_model_calls=0,
          old_successful_encoding_repeated=0, old_frames_or_clock_changed=False,
          provenance='Existing native context path passes original RGB to image processor; normalized resized view only',
          omitted_important_content_or_quality_gain_proven=False, production_allowed=False))
    print(dict(status='PASS7_FIRST_CACHED_VIEW_INVERSES', sources=len(rows),
          max_quantization_error=max(r['integer_quantization_error'] for r in rows),
          max_normalization_error=max(r['normalized_reconstruction_max_error'] for r in rows)))


if __name__ == '__main__':
    main()
