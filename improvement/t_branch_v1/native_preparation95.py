"""Remaining-only native input preparation with explicit new evidence/cache roots.

This is a reusable CPU implementation, not admission of confirmation or production.
Callers must bind the complete original source plan and actual artifact capacity.
"""
from collections import Counter
import json
import time

from coarse_call25 import load_case
from pilot_input_qa29 import native_case
from pilot_inputs27 import source_pixels, window_meta
from summary_inputs82 import case_name
from t_io import check, identity, save


def prepare_source(row, known_pixels, accepted_exact, rt, processor, cache_root,
                   first_proof_root, journal, deadline, expected_geometry=None):
    """Decode/encode only missing native windows, with a first independent QA."""
    from time_control50_prepare import encode_case, source_windows
    source = row['source']; check(source['media'])
    clock, points, windows = source_windows(source)
    if windows != row['windows']:
        raise ValueError('Complete original native plan differs; never shorten it to fit')
    todo = [w for w in windows if case_name(source, w) not in accepted_exact]
    if not todo:
        return [accepted_exact[case_name(source, w)] for w in windows], []
    pictures = source_pixels(source, clock, points, todo, known_pixels)
    uses = Counter(i for w in todo for i in w['source_frame_ordinals'])
    result, proofs = [], []
    for window in windows:
        name = case_name(source, window)
        if name in accepted_exact:
            check(accepted_exact[name]); result.append(accepted_exact[name]); continue
        if time.monotonic() > deadline:
            raise TimeoutError('First input budget expired; retain every accepted journal entry')
        folder = cache_root / name; folder.mkdir()
        meta = window_meta(source, clock, points, window, pictures, folder)
        ref = encode_case(rt, processor, meta, folder)
        journal.write(json.dumps(dict(case=name, CPU=ref)) + '\n'); journal.flush()
        cpu, independent = native_case(ref, {name: (source, window)})
        _, _, values, _ = load_case(ref, rt, processor.tokenizer)
        grid = values['video_grid_thw']
        if tuple(grid.shape) != (1, 3) or int(grid[0, 0]) * 2 != 64 or independent != meta:
            raise ValueError('First independent native64 grid or exact metadata differs')
        pixel = cpu['detail']['tensor_signature']['pixel_values_videos']
        if expected_geometry is not None and dict(shape=pixel['shape'], dtype=pixel['dtype']) != expected_geometry:
            raise ValueError('First actual pixel geometry differs from declared capacity profile')
        del values
        path = first_proof_root / (name + '.json')
        save(path, dict(state='PASS_FIRST_NEW_NATIVE64_INPUT_AND_TOKEN_CPU', actual_CPU=ref,
            source_media=source['media'], source_clock=source['clock'],
            no_human_labels_in_input=True, no_old_processor_or_QA_repeated=True))
        proofs.append(identity(path)); result.append(ref)
        print('FIRST_NATIVE95_INPUT_QA', name, flush=True)
        for ordinal in window['source_frame_ordinals']:
            uses[ordinal] -= 1
            if not uses[ordinal]:
                del pictures[ordinal]
    return result, proofs
