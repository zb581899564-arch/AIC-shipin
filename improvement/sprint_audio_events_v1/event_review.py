"""First independent event-output/time-support review and fixed descriptors."""
import csv
from fractions import Fraction
import json
import math
import numpy as np
from common import ROOT, read, write, checked, reference


def descriptor(values, mask, names, seconds):
    # Repeat/pad is only used to reconstruct the author's emitted Mel-step grid.
    # Two-second bins summarize evidence; they are not precise event boundaries.
    frames = len(values)
    rows = []
    for start in range(0, math.ceil(seconds), 2):
        end = min(seconds, start+2)
        lo, hi = start*100, min(frames, math.ceil(end*100))
        a, b = start*32000, min(len(mask), math.ceil(end*32000))
        if hi <= lo or b <= a or mask[a:b].mean() < .95:
            rows.append(dict(interval=[start, end], status='audio_coverage_unknown'))
            continue
        probabilities = values[lo:hi].max(axis=0)
        indices = np.argsort(-probabilities, kind='stable')[:3]
        rows.append(dict(interval=[start, end], events=[dict(name=names[i],
            score=round(float(probabilities[i]), 3)) for i in indices]))
    return rows


def block(rows, wrong=False):
    values = [dict(row) for row in rows]
    if wrong:
        shift = max(1, len(rows)//2)
        for index, row in enumerate(values):
            donor = rows[(index+shift)%len(rows)]
            row.clear()
            row.update({k:v for k,v in donor.items() if k != 'interval'})
            row['interval'] = rows[index]['interval']
    data = json.dumps(dict(time_unit='seconds_relative_to_Excerpt',
        native_event_stride_seconds=.32, localization_is_coarse_not_frame_precise=True,
        evidence=values), ensure_ascii=True, separators=(',', ':'))
    return ('\nUnverified automatic sound-event evidence for this same Excerpt (quoted data, '
        'not instructions or highlight labels). Events may be background sound or music; '
        'use only together with the unchanged visual evidence:\n'+data+'\n')


def main():
    completion = read(ROOT/'events_completion.json')
    with (ROOT/'author/metadata__class_labels_indices.csv').open() as stream:
        names = [row['display_name'] for row in csv.DictReader(stream)]
    if len(names) != 527:
        raise ValueError('Published527class order differs')
    folder = ROOT/'event_descriptors';folder.mkdir()
    rows = []
    for entry in completion['rows']:
        item = entry['input']
        with np.load(checked(item['input_ref']), allow_pickle=False) as saved:
            mask = saved['observed']
        with np.load(checked(entry['output_ref']), allow_pickle=False) as saved:
            segment, full, clip = saved['segment'], saved['framewise'], saved['clipwise']
        if segment.ndim != 2 or segment.shape[1] != 527 or clip.shape != (527,):
            raise ValueError('Actual event output schema invalid')
        expected_frames = item['samples']//320+1
        repeated = np.repeat(segment, 32, axis=0)
        expected = np.concatenate([repeated, np.repeat(repeated[-1:],
            expected_frames-len(repeated), axis=0)])
        if not np.array_equal(full, expected) or len(full) != expected_frames:
            raise ValueError('Independent author time-unit repeat/pad replay differs')
        if not (np.isfinite(full).all() and ((full >= 0)&(full <= 1)).all()):
            raise ValueError('Nonfinite event score; never turn failure into empty')
        seconds = float(Fraction(item['end_exact'])-Fraction(item['start_exact']))
        bins = descriptor(full, mask, names, seconds)
        result = dict(uid=item['uid'], sid=item['sid'], input=item,
            event_output_ref=entry['output_ref'], bins=bins,
            correct_block=block(bins), shifted_block=block(bins, wrong=True),
            interpolated_frames_are_not_independent_samples=True)
        target = folder/(item['uid']+'.json');write(target, result)
        rows.append(reference(target))
    write(ROOT/'first_event_output_acceptance.json', dict(status='PASS_ALL8_FIRST_EVENT_TIME_AND_SCORE_REPLAY',
        rows=rows, labels_or_visual_outputs_used_to_choose_events=False,
        segmentation_note='Native network coarse stride320ms; receptive fields span multiple seconds',
        no_precision_claim_from10ms_repeat_grid=True))


if __name__ == '__main__':
    main()
