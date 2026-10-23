"""First four real TIME inputs, with whole-source cohort and cost fixed beforehand."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from collections import defaultdict
import hashlib
from pathlib import Path
import sys
import time
import traceback

from prompt_contract13 import prompt_binding
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'pilot_profile21'
CACHE = Path('/dev/shm/aic_T_policy21_first_inputs')
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime


def choose_sources():
    registry = read(ROOT / 'source_registry09/registration.json')
    groups = defaultdict(list)
    for source in registry['sources']:
        if source['role'] == 'fit':
            groups[source['publisher']].append(source)
    rank = lambda value: hashlib.sha256(('T-policy21-fixed-source/' + value).encode()).hexdigest()
    publishers = sorted(groups, key=rank)[:2]
    fit = [min(groups[host], key=lambda row: rank(row['sid'])) for host in publishers]
    dev = [row for row in registry['sources'] if row['role'] == 'development']
    if len(fit) != 2 or len(dev) != 2 or len(set(row['publisher'] for row in fit + dev)) != 4:
        raise ValueError('Two fit and two fixed development publishers required')
    return fit + dev


def prepare_one(rt, processor, source, clock, points, window):
    from time_control50_prepare import decode_window, encode_case
    case_id = source['sid'] + '_W' + str(window['index']).zfill(3)
    folder = CACHE / case_id
    folder.mkdir()
    adapted = dict(source, source=source['sid'])
    start = time.monotonic()
    meta = decode_window(adapted, clock, points, window, folder)
    cpu_ref = encode_case(rt, processor, meta, folder)
    cpu = read(check(cpu_ref))
    import numpy as np
    import torch
    with np.load(check(cpu['encoded']), allow_pickle=False) as archive:
        ids = torch.from_numpy(archive['input_ids'].copy())
    proof = prompt_binding(processor.tokenizer, ids, cpu['detail'], rt.EMPTY_PROMPT, 'COARSE')
    record = dict(case_id=case_id, role=source['role'], source_id=source['sid'],
                  original_CPU=cpu_ref, actual_prompt=proof,
                  seconds=time.monotonic() - start,
                  cache_bytes=sum(path.stat().st_size for path in folder.iterdir()),
                  new_native64_inputs=1, no_model_call=True,
                  future_remaining_preparation_must_adopt_this_input=True)
    save(OUT / (case_id + '.json'), record)
    print('FIRST_POLICY_INPUT21', case_id, record['seconds'], record['cache_bytes'], flush=True)
    return identity(OUT / (case_id + '.json'))


def main():
    OUT.mkdir()
    CACHE.mkdir()
    rt = legacy_runtime()
    from time_control50_prepare import source_windows
    from transformers import AutoProcessor
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    planned = []
    for source in choose_sources():
        check(source['media'])
        clock, points, windows = source_windows(source)
        chosen = min(windows, key=lambda row: hashlib.sha256(
            ('T-policy21-first-cost/' + source['sid'] + '/' + str(row['index'])).encode()).hexdigest())
        planned.append(dict(source=source, windows=windows, first_cost_window=chosen))
    save(OUT / 'registration.json', dict(
        state='WHOLE_SOURCE_PILOT_COHORT_AND_FIRST_COST_INPUTS_FROZEN', planned=planned,
        fitting_sources=2, development_sources=2,
        full_source_windows=sum(len(row['windows']) for row in planned),
        first_cost_inputs=4, cache_root=str(CACHE),
        supervision='Original whole-source all-rater summary preference, not generic dense NHL',
        proposal='Source-marginal sequence policy gradient; no human-JSON teacher forcing',
        no_training_admission_until_budget_and_mechanism_registration=True,
        original_four_new_confirmation_sources_remain_untouched=True,
        no_old_successful_decode_or_input_repeated=True,
        fitting_publishers_fixed_before_quality=True))
    accepted = []
    for row in planned:
        clock, points, _ = source_windows(row['source'])
        accepted.append(prepare_one(rt, processor, row['source'], clock, points, row['first_cost_window']))
    save(OUT / 'completion.json', dict(state='FIRST_FOUR_POLICY_COST_INPUTS_COMPLETE', accepted=accepted,
        total_planned_whole_source_windows=sum(len(row['windows']) for row in planned),
        model_calls=0, training_updates=0, training_admitted=False))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), keep_every_success=True))
        raise
