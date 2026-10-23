"""Adopt three completed profile inputs; first sequential decode only for the fourth."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pathlib import Path
import traceback

from exact_decode23 import sequential_window
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'pilot_remaining24'


def adopted_inputs(prior, planned):
    accepted, remaining = [], []
    for row in planned:
        case = row['source']['sid'] + '_W' + str(row['first_cost_window']['index']).zfill(3)
        path = prior / (case + '.json')
        if not path.exists():
            remaining.append(row)
            continue
        record = read(path)
        cpu = read(check(record['original_CPU']))
        meta = read(check(cpu['input']))
        if (record['case_id'] != case or meta['source_sha256'] != row['source']['media']['sha256'] or
                meta['source_frame_ordinals'] != row['first_cost_window']['source_frame_ordinals'] or
                not record['actual_prompt']['complete_task_in_actual_tokens']):
            raise ValueError('Existing completed profile does not bind frozen source/window/task')
        accepted.append(identity(path))
    if len(accepted) != 3 or len(remaining) != 1:
        raise ValueError('Expected three completed inputs and exactly one remaining failed seek')
    return accepted, remaining


def main():
    prior = ROOT / 'pilot_profile21'
    if 'native64 decode missed a registered original PTS' not in read(prior / 'failure.json')['traceback']:
        raise ValueError('Expected actual original decode failure missing')
    original = read(prior / 'registration.json')
    accepted, remaining = adopted_inputs(prior, original['planned'])
    OUT.mkdir()
    save(OUT / 'registration.json', dict(original_registration=identity(prior / 'registration.json'),
        original_failure=identity(prior / 'failure.json'),
        guard23_log=identity(ROOT / 'pilot_remaining23.log'),
        adopted_successful_inputs=accepted, remaining_source=remaining[0]['source']['sid'],
        unchanged_source_window_and_nativePTS=True,
        only_one_first_remaining_sequential_decode=True, model_calls=0))
    import pilot_profile21 as first
    import time_control50_prepare as helper
    helper.decode_window = sequential_window
    first.OUT = OUT
    first.CACHE = Path('/dev/shm/aic_T_policy24_remaining_input')
    first.CACHE.mkdir()
    rt = first.legacy_runtime()
    from transformers import AutoProcessor
    config = read(first.RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    row = remaining[0]
    check(row['source']['media'])
    clock, points, _ = helper.source_windows(row['source'])
    accepted.append(first.prepare_one(rt, processor, row['source'], clock, points, row['first_cost_window']))
    records = [read(check(ref)) for ref in accepted]
    save(OUT / 'completion.json', dict(state='FIRST_FOUR_POLICY_COST_INPUTS_COMPLETE',
        accepted=accepted, adopted_inputs=3, new_inputs=1,
        full_source_windows=original['full_source_windows'],
        actual_CPU_seconds=sum(row['seconds'] for row in records),
        accepted_cache_bytes=sum(row['cache_bytes'] for row in records),
        model_calls=0, training_updates=0, all_old_failures_preserved=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_every_success=True))
        raise
