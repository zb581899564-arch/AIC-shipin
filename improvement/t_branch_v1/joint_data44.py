"""Pinned fitting-source inputs, original controls and unmodified summary references."""
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from coarse_call25 import load_case
from native_sets import NativeTimeline, accepted_selection
from preference_reward import SummaryReview
from t_io import ROOT, check, read


@dataclass
class Case:
    name: str
    CPU: dict
    meta: dict
    values: dict
    original: dict


@dataclass
class Source:
    sid: str
    cases: list
    timeline: NativeTimeline
    reviews: list
    allowed: dict

    def selection(self, case, result):
        lo = Fraction(case.meta['window_start'])
        spans = [(lo + Fraction(str(a)), lo + Fraction(str(b))) for a, b in result['segments']]
        mask = self.timeline.intervals(spans)
        return accepted_selection(result['status'], mask, len(self.timeline.points))


def load_sources(rt, tokenizer, protocol, load_values=True):
    plan = read(ROOT / protocol['source_cohort'])['planned']
    requested = set(protocol['training_sources'])
    rows = {row['source']['sid']: row['source'] for row in plan if row['source']['sid'] in requested}
    controls = {read(check(ref))['case']: ref for ref in read(ROOT / 'pilot_control30/gpu_completion.json')['outputs']}
    cases = {sid: [] for sid in rows}
    for cpu_ref in read(ROOT / 'pilot_input_qa29/completion.json')['accepted']:
        proof = read(check(cpu_ref))
        meta = read(check(proof['input']))
        if meta['source_name'] not in rows:
            continue
        values = {}
        if load_values:
            _, meta, values, _ = load_case(cpu_ref, rt, tokenizer)
        cases[meta['source_name']].append(Case(meta['case_id'], cpu_ref, meta, values,
                                              controls[meta['case_id']]))
    result = {}
    for sid, source in rows.items():
        timeline = NativeTimeline.from_clock(read(check(source['clock'])))
        target = read(ROOT / 'summary_targets28' / (sid + '.json'))
        with np.load(check(target['tensor']), allow_pickle=False) as archive:
            observed = archive['summary_task_domain'].copy()
            masks = archive['summary_selected'].copy()
        reviews = [SummaryReview(name, mask, observed) for name, mask in zip(target['all_original_reviewers'], masks)]
        if len(reviews) != source['independent_reviewers']:
            raise ValueError('Fitting-source all-reviewer denominator differs')
        allowed = {case.name: timeline.intervals([(case.meta['window_start'], case.meta['window_end'])]) for case in cases[sid]}
        expected = next(row['windows'] for row in plan if row['source']['sid'] == sid)
        if len(cases[sid]) != len(expected):
            raise ValueError('Fitting source is missing a frozen original window')
        result[sid] = Source(sid, cases[sid], timeline, reviews, allowed)
    if set(result) != requested:
        raise ValueError('Fixed fitting-source set differs')
    return result
