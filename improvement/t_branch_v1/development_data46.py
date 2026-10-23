"""Original development windows and fixed half-group shift, no labels in inputs."""
from dataclasses import replace

import torch

import numpy as np
from coarse_call25 import load_case
from joint_data44 import Case, Source
from native_sets import NativeTimeline
from preference_reward import SummaryReview
from t_io import ROOT, check, read

ARMS = ('original_correct', 'trained_correct', 'original_shift', 'trained_shift')


def development_sources(rt, tokenizer, protocol, values=True, labels=False):
    wanted = set(protocol['development_sources'])
    plan = read(ROOT / protocol['source_cohort'])['planned']
    selected = {row['source']['sid']: row for row in plan if row['source']['sid'] in wanted}
    outputs = {read(check(ref))['case']: ref for ref in read(ROOT / 'pilot_control30/gpu_completion.json')['outputs']}
    cases = {sid: [] for sid in wanted}
    for ref in read(ROOT / 'pilot_input_qa29/completion.json')['accepted']:
        proof = read(check(ref)); meta = read(check(proof['input']))
        sid = meta['source_name']
        if sid not in wanted:
            continue
        cached = load_case(ref, rt, tokenizer)[2] if values else {}
        cases[sid].append(Case(meta['case_id'], ref, meta, cached, outputs[meta['case_id']]))
    result = {}
    for sid, row in selected.items():
        timeline = NativeTimeline.from_clock(read(check(row['source']['clock'])))
        reviews = []
        if labels:
            target = read(ROOT / 'summary_targets28' / (sid + '.json'))
            with np.load(check(target['tensor']), allow_pickle=False) as archive:
                reviews = [SummaryReview(name, mask.copy(), archive['summary_task_domain'].copy())
                    for name, mask in zip(target['all_original_reviewers'], archive['summary_selected'])]
        allowed = {case.name: timeline.intervals([(case.meta['window_start'], case.meta['window_end'])]) for case in cases[sid]}
        if len(cases[sid]) != len(row['windows']):
            raise ValueError('Development source incomplete')
        result[sid] = Source(sid, cases[sid], timeline, reviews, allowed)
    if set(result) != wanted:
        raise ValueError('Frozen development publisher set differs')
    return result


def shifted(case):
    value = case.values['pixel_values_videos']
    grid = case.values['video_grid_thw']
    if grid.shape != (1, 3):
        raise ValueError('Counterfactual requires a single measured native video grid')
    t, h, w = map(int, grid[0])
    if t != 32 or value.shape[0] != t * h * w:
        raise ValueError('Measured real token grid does not support the registered half shift')
    grouped = value.reshape(t, h * w, *value.shape[1:])
    swapped = torch.roll(grouped, t // 2, dims=0)
    if not torch.equal(torch.roll(swapped, -t // 2, dims=0), grouped):
        raise ValueError('Actual counterfactual does not invert bit-exactly')
    values = dict(case.values, pixel_values_videos=swapped.reshape_as(value))
    # This is deliberately incorrect content/timestamp correspondence. It is a
    # diagnostic view of the same native source, never new native evidence.
    return replace(case, values=values)
