"""First CPU-only development interface audit, no model, label or tensor replay."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
from types import SimpleNamespace
import traceback

import torch

from frozen_branch46 import verify_modules, semantic_modules
from development_data46 import development_sources, shifted
from development_verify46 import candidate_request
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'development_contract49'


def synthetic_shift():
    pixels = torch.arange(32 * 6 * 3).reshape(32 * 6, 3)
    case = SimpleNamespace(values=dict(pixel_values_videos=pixels, video_grid_thw=torch.tensor([[32, 2, 3]])))
    from joint_data44 import Case
    actual = Case('synthetic', {}, {}, case.values, {})
    transformed = shifted(actual)
    expected = torch.cat((pixels[16 * 6:], pixels[:16 * 6]))
    if not torch.equal(expected, transformed.values['pixel_values_videos']) or not torch.equal(pixels, case.values['pixel_values_videos']):
        raise ValueError('Fixed half temporal-group shift changed original or ordering')


def main():
    OUT.mkdir()
    rt = runtime()
    contract, grammar, protocol_module = verify_modules()
    semantic_modules()
    synthetic_shift()
    protocol = read(ROOT / 'code/joint_policy_protocol44.json')
    sources = development_sources(None, None, protocol, values=False, labels=False)
    planned = []
    for sid, source in sources.items():
        if source.reviews or any(case.values for case in source.cases):
            raise ValueError('Metadata-only dev planning read labels or tensors')
        events = []
        for case in source.cases:
            output = read(check(case.original))
            for index, segment in enumerate(output['segments']):
                event, request = candidate_request(case, source, segment, index)
                if request['prompt'] != protocol_module.verify_prompt(request, contract) or request['prompt'] == rt.EMPTY_PROMPT:
                    raise ValueError('Actual dev request uses wrong task prompt')
                lo, hi = map(Fraction, event['original_window_exact'])
                start, end = map(Fraction, event['original_interval_exact'])
                if not lo <= start < end <= hi:
                    raise ValueError('Existing native candidate leaves its frozen window')
                events.append(request['request_id'])
        planned.append(dict(source=sid, original_windows=len(source.cases), first_native_request_contracts=len(events), request_ids=events))
    if torch.cuda.is_initialized():
        raise ValueError('CPU dev interface audit initialized CUDA')
    save(OUT / 'completion.json', dict(state='PASS_NEW_DEV_IMPORT_SHIFT_AND_NATIVE_REQUEST_INTERFACES',
        sources=planned, synthetic_half_group_order=True, labels_read=False, tensor_cache_read=False,
        actual_model_calls=0, new_GPU_calls=0, no_quality_or_training_admission=True,
        original97_control_output_QA_adopted=identity(ROOT / 'pilot_review37/completion.json')))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
