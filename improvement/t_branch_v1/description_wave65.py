"""Same annotation clips' real audio, adopting previously successful full waveforms."""
from fractions import Fraction

import numpy as np

from speech_native58 import chunk_mapping
from speech_scope58 import GENERAL, original_helpers
from t_io import ROOT, check, identity, read, save


def existing_sources():
    result = {}
    for ref in read(GENERAL / 'speech36/input_acceptance.json')['accepted']:
        row = read(check(ref)); result[row['sid']] = (row['media'], row['original_audio_frames'], ref)
    for ref in read(ROOT / 'speech_information58/native_completion.json')['accepted']:
        row = read(check(ref)); result[row['sid']] = (row['source']['media'], row['original_audio_frames'], ref)
    return result


def prepare(examples, cache, out):
    module, helpers, helper_ref = original_helpers()
    prior = existing_sources(); by_source = {}
    for example in examples:
        by_source.setdefault(example['source']['sid'], []).append(example)
    accepted, first, adopted = {}, [], []
    for sid, rows in by_source.items():
        source = rows[0]['source']; folder = cache / sid; folder.mkdir()
        clock = read(check(source['clock']))
        if sid in prior:
            media, full, receipt = prior[sid]
            if media['sha256'] != source['media']['sha256']:
                raise ValueError('Old complete native audio belongs to a different source')
            with np.load(check(full), allow_pickle=False) as data:
                values, offsets = data['values'].copy(), data['offsets'].copy()
                starts = list(map(Fraction, data['starts_exact'].tolist()))
            adopted.append(dict(sid=sid, original_native_receipt=receipt, full_audio=full))
        else:
            check(source['media'])
            values, offsets, starts, full = module.audio_frames(source['media'], Fraction(clock['first_PTS_exact']), folder)
            first.append(dict(sid=sid, original_clock=source['clock'], full_audio=full))
        if offsets[0] != 0 or offsets[-1] != len(values) or len(offsets) != len(starts) + 1:
            raise ValueError('Native original sample-frame structure differs')
        for row in rows:
            for kind, key in [('correct', 'correct_view'), ('wrong', 'wrong_native_view')]:
                view = row[key]; target = folder / (row['example_id'] + '_' + kind); target.mkdir()
                chunk = chunk_mapping(helpers, values, offsets, starts,
                    Fraction(view['start_exact']), Fraction(view['end_exact']), target, 0)
                name = row['example_id'] + '_' + kind
                receipt = dict(example_id=row['example_id'], condition=kind, source=sid,
                    actual_native_interval_exact=[view['start_exact'], view['end_exact']],
                    original_media=source['media'], original_clock=source['clock'], original_audio_frames=full,
                    chunk=chunk, no_human_description_given_to_ASR=True,
                    selected_human_interval_is_supervised_input_not_test_data=True)
                save(target / 'CPU_acceptance.json', receipt)
                accepted[name] = identity(target / 'CPU_acceptance.json')
                print('DESCRIPTION65_FIRST_CLIP_AUDIO', name, flush=True)
        del values, offsets, starts
    save(out / 'native_completion.json', dict(state='FIRST48_MATCHED_CONTROL_CLIP_AUDIO_PASS',
        accepted=accepted, original_helpers=helper_ref, adopted_complete_sources=adopted,
        first_audio_sources=first, no_successful_prior_audio_decode_repeated=True,
        all_first_clip_sample_native_mapping_QA=True, new_model_calls=0))
    return accepted
