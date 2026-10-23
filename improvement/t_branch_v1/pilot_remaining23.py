"""Explicit first remaining profile inputs; preserve failed21 and its frozen choices."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pathlib import Path
import traceback

from exact_decode23 import sequential_window
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'pilot_remaining23'


def main():
    prior = ROOT / 'pilot_profile21'
    if 'native64 decode missed a registered original PTS' not in read(prior / 'failure.json')['traceback']:
        raise ValueError('Expected actual first-seek failure missing')
    if list(prior.glob('*_W*.json')):
        raise ValueError('Unexpected completed profile inputs must be explicitly adopted, not redone')
    OUT.mkdir()
    original = read(prior / 'registration.json')
    save(OUT / 'registration.json', dict(original_registration=identity(prior / 'registration.json'),
        actual_first_seek_failure=identity(prior / 'failure.json'),
        unchanged_sources_windows_and_targets=True, only_first_unsuccessful_input_decode_replaced=True,
        new_decode='Sequential original ordinals; every traversed exactPTS equals accepted clock',
        no_repeated_successful_input_model_or_processor=True))
    import pilot_profile21 as first
    import time_control50_prepare as helper
    helper.decode_window = sequential_window
    first.OUT = OUT
    first.CACHE = Path('/dev/shm/aic_T_policy23_remaining_inputs')
    first.CACHE.mkdir()
    rt = first.legacy_runtime()
    from transformers import AutoProcessor
    config = read(first.RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    accepted = []
    for row in original['planned']:
        check(row['source']['media'])
        clock, points, _ = helper.source_windows(row['source'])
        accepted.append(first.prepare_one(rt, processor, row['source'], clock, points, row['first_cost_window']))
    save(OUT / 'completion.json', dict(state='FIRST_FOUR_POLICY_COST_INPUTS_REMAINING_COMPLETE',
        accepted=accepted, full_source_windows=original['full_source_windows'],
        model_calls=0, training_updates=0, original_failure_preserved=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_every_success=True))
        raise
