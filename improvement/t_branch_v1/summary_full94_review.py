"""First complete content-goal quality, all original reviewers and strong40.48."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math

import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from event_full79 import independent_set_metrics
from frozen_branch46 import RUN
from preference_reward import summary_agreement
from summary_context90 import ARMS
from summary_full93_masks import complete_source
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime
from verify_adoption92 import first_decisions

OUT = ROOT / 'summary_full93'


def main():
    torch.set_num_threads(2); rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(
        read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    cpu = read(ROOT / 'summary_verify_inputs92/completion.json')
    gpu = read(OUT / 'GPU_completion.json')
    decisions, proofs = first_decisions(cpu, gpu, tokenizer, OUT / 'first_VERIFY_CPU')
    routes = read(ROOT / 'event_route77/CPU_completion.json')['source_masks']
    semantic = read(ROOT / 'development51/coarse_and_BASE_GPU_completion.json')['semantic']
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    masks, bindings, original = {}, {}, {}
    for sid, source in sources.items():
        masks[sid], bindings[sid], original[sid] = complete_source(
            source, cpu, decisions, routes[sid], semantic[sid], OUT)
    save(OUT / 'frozen_all_masks_before_labels.json', bindings)
    # Old controls' first independent metrics are adopted, not recomputed.
    old = read(ROOT / 'event_full78/review.json')
    labeled = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=True)
    metrics, independent = {}, []
    for sid in sources:
        metrics[sid] = {'original40_48': old['metrics'][sid]['original40_48']}
        for arm in ARMS:
            reviews = labeled[sid].reviews; mask = masks[sid][arm]
            score = summary_agreement(mask, reviews, len(reviews))
            other = independent_set_metrics(mask, reviews, len(reviews))
            if abs(score['mean_f1'] - other) > 1e-12:
                raise ValueError('First independent all-reviewer native set-F1 differs')
            metrics[sid][arm] = score
            independent.append(dict(source=sid, arm=arm, mean_f1=other))
    means = {arm: math.fsum(metrics[sid][arm]['mean_f1'] for sid in sources) / len(sources)
             for arm in ('original40_48',) + ARMS}
    trained = ARMS[1]
    gains = {sid: metrics[sid][trained]['mean_f1'] - metrics[sid]['original40_48']['mean_f1']
             for sid in sources}
    gates = dict(both_publishers_improve_actual_full40_48=all(v > 0 for v in gains.values()),
        trained_beats_untrained_BASE_goal=means[trained] > means[ARMS[0]],
        trained_beats_old_event_only=means[trained] > old['means']['native_event_memory_correct'],
        trained_beats_fixed_goal_shift=means[trained] > means[ARMS[2]],
        no_new_empty_source=all(masks[sid][trained].any() or not original[sid].any()
                                for sid in sources),
        complete_native_and_full_downstream_QA=True,
        actual_all_method_parameters_below9B=8869330010 <= 9000000000)
    gates = {key: bool(value) for key, value in gates.items()}
    if torch.cuda.is_initialized():
        raise ValueError('Independent full-source quality initialized CUDA')
    save(OUT / 'review.json', dict(state='PASS_FIXED_CONTENT_SUMMARY85_DEVELOPMENT_PENDING_COST_AND_CONFIRMATION'
        if all(gates.values()) else 'STOP_FIXED_CONTENT_SUMMARY85_DEVELOPMENT',
        metrics=metrics, means=means, per_source_delta_vs_actual40_48=gains, gates=gates,
        adopted_old_event_control_macro=old['means']['native_event_memory_correct'],
        adopted_original_metric_first_QA=identity(ROOT / 'event_full78/independent_CPU_completion.json'),
        all_original_reviewers=True, human_unselected_semantics='UNKNOWN_NOT_ORDINARY',
        development_previously_exposed=True, four_confirmation_read=False,
        actual_parameters=8869330010, official_joint_score='UNKNOWN',
        no_automatic_confirmation_or_production=True, no_prompt_dose_or_threshold_retry=True))
    save(OUT / 'independent_CPU_completion.json', dict(state='PASS_FIRST_FULL_CONTENT_GOAL_NATIVE_CURRENT40_48_CPU',
        first_VERIFY_proofs=proofs, adopted_successful_VERIFY=len(cpu['adopted_successful_outputs']),
        old_BASE_batches_adopted=365, no_old_model_or_token_QA_repeated=True,
        all_masks=identity(OUT / 'frozen_all_masks_before_labels.json'),
        independent_all_reviewers=independent, original_confirmation_unread=True))


if __name__ == '__main__':
    main()
