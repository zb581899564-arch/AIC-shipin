"""Finish only missing output QA and characterize unsupported native actions."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from dataclasses import replace
from pathlib import Path
import traceback

import numpy as np
import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from development_data46 import development_sources
from development_prepare55 import normalized_output
from joint_audit45 import trajectory
from preference_reward import summary_agreement
from speech_task60 import ARMS
from t_io import ROOT, check, identity, read, save
from t_runtime39 import grammar, runtime

OUT = ROOT / 'native_failure_audit62'
FAILED = ROOT / 'speech_development60'


def text_case(case, proof):
    row = read(check(proof))
    if row['original_CPU'] != case.CPU:
        raise ValueError('New actual speech CPU binding differs')
    with np.load(check(row['text']), allow_pickle=False) as data:
        prefix = {name: torch.from_numpy(data[name].copy()) for name in data.files}
    return replace(case, values=prefix)


def masks_and_first_QA(rt, tokenizer):
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    outputs = read(FAILED / 'coarse_GPU_completion.json')['outputs']
    inputs = read(ROOT / 'speech_inputs59/completion.json')['accepted']
    candidates = grammar().ascii_token_candidates(tokenizer)
    replay = OUT / 'remaining_replay'; replay.mkdir()
    predictions, accepted, adopted = {}, [], []
    existing = {p.name: p for p in (FAILED / 'coarse_replay').glob('*.json')}
    if len(existing) != 8 or 'candidate_request' not in (FAILED / 'speech_prepare60.log').read_text():
        raise ValueError('Expected precise eight-output successful prefix not established')
    for sid, source in sources.items():
        predictions[sid] = {}
        for arm in ARMS:
            mask = np.zeros(len(source.timeline.points), dtype=bool)
            for case in source.cases:
                ref = outputs[sid][arm][case.name]
                if arm == 'original_correct':
                    row = read(check(ref))
                else:
                    name = arm + '_' + case.name + '.json'
                    if name in existing:
                        normalized = identity(existing[name]); row = read(check(normalized))
                        if row['original_acceptance_adopted'] != ref:
                            raise ValueError('Prior successful partial output replay changed')
                        adopted.append(normalized)
                    else:
                        actual = text_case(case, inputs[sid][arm][case.name])
                        normalized = normalized_output(ref, actual, rt, tokenizer, candidates, replay / name)
                        row, _ = trajectory(normalized, actual, source, rt, tokenizer)
                        accepted.append(normalized)
                mask |= source.selection(case, row)
            predictions[sid][arm] = mask
    if len(accepted) != 92 or len(adopted) != 8:
        raise ValueError('Remaining-only first output QA count differs')
    return predictions, accepted, adopted


def main():
    OUT.mkdir()
    if read(FAILED / 'speech_prepare60_terminal.json')['exit_code'] != 1:
        raise ValueError('Actual before-VERIFY CPU failure absent')
    log = (FAILED / 'speech_prepare60.log').read_text()
    if 'Generated original candidate lacks registered native support' not in log:
        raise ValueError('Different failure needs its own recovery')
    boundary = read(ROOT / 'boundary_metadata61/completion.json')
    all_empty = all(row['candidate_indices'][0] == row['candidate_indices'][1] for row in boundary['violations'])
    save(OUT / 'registration.json', dict(actual_failure=identity(FAILED / 'failure.json'),
        native_boundary_diagnosis=identity(ROOT / 'boundary_metadata61/completion.json'),
        source_code=identity(Path(__file__)), first_QA_remaining92=True, successful8_QA_adopted=True,
        no_new_generation_decode_encoding_or_VERIFY=True,
        no_segment_dropped_clipped_expanded_or_replaced=True,
        scope='First native-set coarse diagnostic only, not full40.47 or candidate admission'))
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    predictions, first, adopted = masks_and_first_QA(rt, tokenizer)
    binding = {}
    for sid, arms in predictions.items():
        path = OUT / (sid + '_all_coarse_native.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, **arms)
        binding[sid] = identity(path)
    save(OUT / 'frozen_coarse_masks_before_diagnostic_labels.json', binding)
    labeled = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=True)
    metrics = {sid: {arm: summary_agreement(mask, labeled[sid].reviews, len(labeled[sid].reviews))
        for arm, mask in arms.items()} for sid, arms in predictions.items()}
    means = {arm: float(np.mean([metrics[sid][arm]['mean_f1'] for sid in labeled])) for arm in ARMS}
    save(OUT / 'completion.json', dict(state='STOP_FIXED60_NATIVE_UNREPRESENTABLE_ACTIONS',
        all_new_continuous_token_and_grammar_QA_passed=True, first92_output_QA=first, adopted8_output_QA=adopted,
        unsupported_segments=len(boundary['violations']), all_unsupported_have_zero_native_PTS=all_empty,
        unsupported_case_count=len({(row['case'], row['arm']) for row in boundary['violations']}),
        means_coarse_only=means, metrics_coarse_only=metrics, new_model_calls=0,
        no_native_frame_was_invented_or_segment_silently_discarded=True,
        full40_47_not_completed=True, candidate_or_production_admitted=False,
        old_engineering_failure_preserved=True, fresh_confirmation_read=False, new_packages=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
