"""First CPU decomposition of the completed, rejected joint4 experiment."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import subprocess
import traceback

import numpy as np

from development_data46 import ARMS, development_sources
from preference_reward import summary_agreement
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'development_diagnosis57'
DEV = ROOT / 'development_remaining55'
STAGES = ('coarse', 'D8', 'VERIFY', 'full40_47')


def compact(mask, source):
    score = summary_agreement(mask, source.reviews, len(source.reviews))
    return {key: score[key] for key in ('mean_f1', 'mean_precision', 'mean_recall')} | {
        'selected_native_frames': int(mask.sum()), 'whole_source_frames': len(mask),
        'original_reviewers': len(source.reviews)}


def native_masks(source, coarse, binding):
    result = {}
    for arm in ARMS:
        mask = np.zeros(len(source.timeline.points), dtype=bool)
        for case in source.cases:
            row = read(check(coarse[source.sid][arm][case.name]))
            mask |= source.selection(case, row)
        with np.load(check(binding[source.sid][arm]['native']), allow_pickle=False) as archive:
            result[arm] = dict(coarse=mask, **{name: archive[name].copy() for name in STAGES[1:]})
    return result


def development():
    protocol = read(ROOT / 'code/joint_policy_protocol44.json')
    sources = development_sources(None, None, protocol, values=False, labels=True)
    coarse = read(ROOT / 'development51/coarse_GPU_completion.json')['outputs']
    binding = read(DEV / 'frozen_all_predictions_before_labels.json')
    per_source = {}
    for sid, source in sources.items():
        masks = native_masks(source, coarse, binding)
        scores = {arm: {stage: compact(mask, source) for stage, mask in stages.items()}
                  for arm, stages in masks.items()}
        differences = {}
        for stage in STAGES:
            old, new = masks['original_correct'][stage], masks['trained_correct'][stage]
            differences[stage] = dict(
                delta_f1=scores['trained_correct'][stage]['mean_f1'] - scores['original_correct'][stage]['mean_f1'],
                added=int((new & ~old).sum()), removed=int((old & ~new).sum()))
        per_source[sid] = dict(scores=scores, differences=differences)
    macro = {arm: {stage: float(np.mean([row['scores'][arm][stage]['mean_f1']
             for row in per_source.values()])) for stage in STAGES} for arm in ARMS}
    return dict(per_source=per_source, macro=macro,
        stage_delta={stage: macro['trained_correct'][stage] - macro['original_correct'][stage] for stage in STAGES})


def training():
    result = read(ROOT / 'joint_continue50/gpu_completion.json')
    rows = []
    for ref in result['episodes']:
        episode = read(check(ref)); reward = read(check(episode['reward']))
        advantages = [item['advantage'] for item in reward['per_window'].values()]
        rows.append(dict(episode=episode['index'], source=episode['source'],
            current_greedy_F1=reward['greedy_source']['mean_f1'],
            current_sample_F1=reward['sampled_source']['mean_f1'],
            windows=len(advantages), positive_advantages=sum(v > 0 for v in advantages),
            negative_advantages=sum(v < 0 for v in advantages), zero_advantages=sum(v == 0 for v in advantages),
            actual_optimizer_updates=episode['optimizer_updates']))
    return rows


def main():
    OUT.mkdir()
    terminal = read(DEV / 'completion.json')
    if terminal['state'] != 'STOP_FROZEN_JOINT4_DEVELOPMENT':
        raise ValueError('Only diagnose the completed rejected fixed profile, never a partial result')
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Protected CONTROL5 identity/state differs')
    save(OUT / 'registration.json', dict(completed_development=identity(DEV / 'completion.json'),
        source_code=identity(Path(__file__)), task='First saved-mask stage decomposition and accepted reward summary',
        new_model_calls=0, repeated_QA=0, training=0, confirmation_sources_read=0,
        no_parameter_or_prompt_or_threshold_selection=True,
        RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    values = development()
    save(OUT / 'completion.json', dict(state='FIRST_REJECTED_PROFILE_CPU_DECOMPOSITION_COMPLETE',
        **values, training_episodes=training(), new_model_calls=0,
        no_quality_gate_or_original_failure_modified=True,
        limitation='Exposed human-summary development, not dense generic ordinary labels or official joint score',
        confirmation_sources_read=0, new_packages=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
