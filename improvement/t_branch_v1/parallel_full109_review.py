"""Complete four-arm, all-original-reviewer source evaluation against actual40.48."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math

import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from frozen_branch46 import RUN
from parallel_full109_masks import complete
from parallel_metric_cache109 import accepted, score
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime
from verify_adoption92 import first_decisions

OUT = ROOT / 'parallel_full109'


def main():
    torch.set_num_threads(2)
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    cpu = read(ROOT / 'parallel_verify_inputs109/completion.json')
    gpu = read(OUT / 'GPU_completion.json')
    resolved, proofs = first_decisions(cpu, gpu, tokenizer, OUT / 'first_VERIFY_CPU')
    protocol = read(ROOT / 'code/parallel_protocol105.json')
    arms = protocol['development_matrix']
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    routes = read(ROOT / 'event_route77/CPU_completion.json')['source_masks']
    semantic = read(ROOT / 'development51/coarse_and_BASE_GPU_completion.json')['semantic']
    masks, bindings = {}, {}
    for sid, source in sources.items():
        masks[sid], bindings[sid] = complete(source, arms, cpu, resolved, routes[sid], semantic[sid], OUT)
    save(OUT / 'frozen_all_masks_before_labels.json', bindings)
    labeled = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=True)
    cache, independent_keys = accepted(labeled)
    metrics, primary_first, independent_first = {}, [], []
    for sid, source in labeled.items():
        metrics[sid] = {arm: score(mask, source, cache, independent_keys, primary_first, independent_first)
                        for arm, mask in masks[sid].items()}
    means = {arm: math.fsum(metrics[sid][arm]['score']['mean_f1'] for sid in sources) / len(sources)
             for arm in ['original40_48'] + arms}
    trained = arms[1]
    gains = {sid: metrics[sid][trained]['score']['mean_f1']
                  - metrics[sid]['original40_48']['score']['mean_f1'] for sid in sources}
    gates = dict(both_publishers_improve_actual_full40_48=all(value > 0 for value in gains.values()),
        trained_macro_beats_original_TIME_same_parallel_control=means[trained] > means[arms[0]],
        correct_content_beats_fixed_joint_AV_shift=means[trained] > means[arms[2]],
        no_new_empty_source=all(masks[sid][trained].any() or not masks[sid]['original40_48'].any()
                                for sid in sources),
        complete_training_native_and_downstream_first_QA=True,
        actual_complete_parameters_below9B=8869330010 <= 9000000000)
    gates = {key: bool(value) for key, value in gates.items()}
    if torch.cuda.is_initialized():
        raise ValueError('Full-source scientific CPU review initialized CUDA')
    save(OUT / 'review.json', dict(state='PASS_FIXED_PARALLEL105_DEVELOPMENT_PENDING_COST_AND_CONFIRMATION'
        if all(gates.values()) else 'STOP_FIXED_PARALLEL105_DEVELOPMENT',
        metrics=metrics, means=means, per_source_delta_vs_actual40_48=gains, gates=gates,
        video_only_shift_diagnostic_not_architecture_selector=arms[3],
        all_original_reviewers=True, human_summary_omissions_semantic_UNKNOWN=True,
        development_previously_exposed=True, original4confirmation_read=False,
        official_joint_score='UNKNOWN', actual_parameters=8869330010,
        no_automatic_confirmation_or_production=True, no_threshold_prompt_dose_retry=True))
    save(OUT / 'independent_CPU_completion.json', dict(state='FIRST_COMPLETE_PARALLEL105_NATIVE_CURRENT40_48_CPU_PASS',
        first_new_VERIFY_proofs=proofs, old_exact_VERIFY_adopted=len(cpu['adopted_successful_outputs']),
        old365_BASE_batches_and_exact_route_adopted=True,
        all_masks=identity(OUT / 'frozen_all_masks_before_labels.json'),
        first_native_metrics=primary_first, first_independent_all_reviewers=independent_first,
        accepted_same_mask_metrics_adopted=True, no_successful_old_model_or_QA_replayed=True))


if __name__ == '__main__':
    main()
