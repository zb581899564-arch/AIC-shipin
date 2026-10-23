"""Exact unchanged candidate-specific VERIFY, with cross-arm identical-task adoption."""
from bisect import bisect_left
from fractions import Fraction
import hashlib
import numpy as np

import torch

from frozen_branch46 import verify_modules
from prompt_contract13 import prompt_binding
from t_io import identity, save


def candidate_request(case, source, segment, index):
    contract, _, protocol = verify_modules()
    lo, hi = Fraction(case.meta['window_start']), Fraction(case.meta['window_end'])
    first, last = (lo + Fraction(str(value)) for value in segment)
    pts = source.timeline.points
    start, stop = bisect_left(pts, first), bisect_left(pts, last)
    ordinals = case.meta['source_frame_ordinals']
    if not ordinals[0] <= start < stop <= ordinals[-1] + 1:
        raise ValueError('Generated original candidate lacks registered native support')
    cut_end = pts[stop] if stop < len(pts) else source.timeline.end
    stamp = hashlib.sha256((str(first) + '/' + str(last)).encode()).hexdigest()[:10]
    event = dict(event_id=case.name + '_E%02d_' % index + stamp, original_segment_index=index,
        original_interval_exact=[str(first), str(last)], original_window_exact=[str(lo), str(hi)],
        original_native_cut_interval_exact=[str(pts[start]), str(cut_end)])
    meta = dict(case.meta, window_start=str(pts[ordinals[0]]),
        window_end=str(pts[ordinals[-1] + 1] if ordinals[-1] + 1 < len(pts) else source.timeline.end))
    req = contract.request(dict(event, original_interval_exact=event['original_native_cut_interval_exact']), meta)
    req['prompt'] = protocol.verify_prompt(req, contract)
    return event, req


def task_values(case, tokenizer, request, rt):
    original = case.values['input_ids'][0].tolist()
    decoded = tokenizer.decode(original, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if tokenizer.encode(decoded, add_special_tokens=False) != original or decoded.count(rt.EMPTY_PROMPT) != 1:
        raise ValueError('Actual original prefix does not permit exact single-task substitution')
    replacement = tokenizer.encode(decoded.replace(rt.EMPTY_PROMPT, request['prompt']), add_special_tokens=False)
    image = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    end = max(i for i, token in enumerate(original) if token == image) + 1
    if replacement[:end] != original[:end] or len(replacement) > 16384:
        raise ValueError('VERIFY rewrite changed visual/timestamp prefix or exceeds original budget')
    values = dict(case.values, input_ids=torch.tensor([replacement], dtype=torch.long))
    values['attention_mask'] = torch.ones_like(values['input_ids'])
    binding = prompt_binding(tokenizer, values['input_ids'],
        dict(prompt_sha256=hashlib.sha256(request['prompt'].encode()).hexdigest()), request['prompt'], 'VERIFY', rt.EMPTY_PROMPT)
    return values, binding


def prepare(case, event, request, folder, tokenizer, rt):
    folder.mkdir()
    values, binding = task_values(case, tokenizer, request, rt)
    encoded = folder / 'text.npz'
    with encoded.open('xb') as stream:
        np.savez_compressed(stream, input_ids=values['input_ids'].numpy(), attention_mask=values['attention_mask'].numpy())
    # First independent text serialization replay, original accepted video
    # tensors stay referenced; no processor or native RGB is repeated.
    with np.load(encoded, allow_pickle=False) as archive:
        if any(not np.array_equal(archive[key], values[key].numpy()) for key in archive.files):
            raise ValueError('First VERIFY text cache roundtrip differs')
    from t_io import check, read
    old = read(check(case.CPU))
    detail = dict(old['detail'], input_tokens=values['input_ids'].shape[1],
        prompt_sha256=binding['expected_prompt_sha256'], tensor_signature=rt.tensor_signature(values))
    save(folder / 'request.json', request)
    save(folder / 'CPU_acceptance.json', dict(input=old['input'], adopted_multimodal=old['encoded'],
        encoded_text=identity(encoded), detail=detail, non_tensor_inputs=old['non_tensor_inputs'],
        original_CPU=case.CPU, prompt_binding=binding,
        actual_video_and_timestamp_prefix_unchanged=True, no_processor_or_decode_repeated=True,
        downstream_uses_original_correct_native_content_even_for_shifted_coarse=True))
    return dict(event=event, request=identity(folder / 'request.json'), CPU=identity(folder / 'CPU_acceptance.json'))
