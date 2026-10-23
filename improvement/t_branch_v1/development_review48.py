"""First exact frozen downstream source masks, then paired all-reviewer dev metrics."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from fractions import Fraction

import numpy as np
import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN, semantic_prediction, verify_modules
from development_data46 import ARMS, development_sources
from preference_reward import summary_agreement
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'development48'


def decisions(tokenizer):
    contract, grammar, _ = verify_modules()
    candidates = grammar.candidate_tokens(tokenizer, contract.responses())
    cpu = read(OUT / 'verify_CPU_completion.json')
    gpu = read(OUT / 'verify_GPU_completion.json')
    if set(gpu['outputs']) != set(cpu['tasks']):
        raise ValueError('Downstream VERIFY source/task set incomplete')
    accepted = {}
    for key, ref in gpu['outputs'].items():
        row = read(check(ref)); raw = read(check(row['raw']))
        request = read(check(cpu['tasks'][key]['request']))
        rule = grammar.VerifyConstraint(tokenizer, raw['prefix'], request, raw['eos'], candidates)
        rule.assert_complete(torch.tensor(raw['tokens'], dtype=torch.long))
        text = tokenizer.decode(raw['tokens'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
        actual = contract.resolve(text, request, execution_status='MODEL_OK')
        if actual != row['decision'] or row['input'] != cpu['tasks'][key]:
            raise ValueError('First independent downstream token/grammar/parser/task replay differs')
        accepted[key] = actual['decision']
    return cpu, accepted


def retained(source, keys, tasks, resolved):
    count = len(source.timeline.points)
    d8, kept = np.zeros(count, dtype=bool), np.zeros(count, dtype=bool)
    for key in keys:
        event = tasks[key]['event']
        start, end = map(Fraction, event['original_interval_exact'])
        lo, hi = map(Fraction, event['original_window_exact'])
        mask = source.timeline.intervals([(max(lo, start - Fraction(3, 4)),
            min(hi, end + Fraction(1, 2) + (Fraction(1, 4) if end - start >= 8 else 0)))])
        d8 |= mask
        if resolved[key] != 'DROP':
            kept |= mask
    guard = not kept.any() and d8.any()
    if guard:
        kept = d8.copy()
    return d8, kept, bool(guard)


def main():
    runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    cpu, resolved = decisions(tokenizer)
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    model = read(OUT / 'coarse_and_BASE_GPU_completion.json')
    predictions, binding = {}, {}
    for sid, source in sources.items():
        native = read(ROOT / 'development_semantic46' / sid / 'semantic_CPU_completion.json')
        features = read(check(model['semantic'][sid]))['outputs']
        predictions[sid] = {}; binding[sid] = {}
        for arm in ARMS:
            d8, verified, guard = retained(source, cpu['source_policies'][sid][arm], cpu['tasks'], resolved)
            full, residual = semantic_prediction(verified, native, features)
            predictions[sid][arm] = full
            path = OUT / (sid + '_' + arm + '_native.npz')
            with path.open('xb') as stream:
                np.savez_compressed(stream, D8=d8, VERIFY=verified, full40_47=full, residual=residual)
            binding[sid][arm] = dict(native=identity(path), empty_source_guard=guard,
                semantic_new_frames=int((full & ~verified).sum()), occupancy_recomputed=True)
    save(OUT / 'frozen_all_predictions_before_labels.json', binding)
    labeled = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=True)
    metrics = {sid: {arm: summary_agreement(mask, labeled[sid].reviews, len(labeled[sid].reviews))
        for arm, mask in arms.items()} for sid, arms in predictions.items()}
    controls = {sid: read(ROOT / 'pilot_control30' / (sid + '_control.json'))['score']['mean_f1'] for sid in sources}
    means = {arm: float(np.mean([metrics[sid][arm]['mean_f1'] for sid in sources])) for arm in ARMS}
    differences = {sid: metrics[sid]['trained_correct']['mean_f1'] - metrics[sid]['original_correct']['mean_f1'] for sid in sources}
    ordinary_gain = means['trained_correct'] - means['original_correct']
    shifted_gain = means['trained_shift'] - means['original_shift']
    gates = dict(mean_beats_original_coarse=means['trained_correct'] > np.mean(list(controls.values())),
        mean_beats_complete40_47=ordinary_gain > 0,
        both_development_publishers_improve=all(value > 0 for value in differences.values()),
        correct_content_beats_shift=means['trained_correct'] > means['trained_shift'],
        correct_gain_exceeds_shift_gain=ordinary_gain > shifted_gain,
        no_new_empty_whole_source=all(predictions[sid]['trained_correct'].any() or not predictions[sid]['original_correct'].any() for sid in sources))
    gates = {key: bool(value) for key, value in gates.items()}
    save(OUT / 'review.json', dict(state='PASS_FROZEN_JOINT4_DEVELOPMENT' if all(gates.values()) else 'STOP_FROZEN_JOINT4_DEVELOPMENT',
        metrics=metrics, means=means, original_coarse_controls=controls, per_source_delta=differences,
        correct_content_gain=ordinary_gain, shifted_content_gain=shifted_gain, gates=gates,
        exact_complete40_47_external_algorithm=True, historical_exposure='Not new blind; fixed two development publishers',
        human_summary_preference_not_generic_NHL=True, official_joint_score='UNKNOWN',
        no_parameter_threshold_prompt_or_dose_retry=True))
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS_FIRST_DEV_OUTPUT_AND_FROZEN_DOWNSTREAM_NATIVE_REPLAY',
        unique_VERIFY_tasks=len(resolved), sources=2, policies_per_source=4,
        input_SHIFT_first_QA=identity(OUT / 'coarse_CPU_completion.json'), all_masks=identity(OUT / 'frozen_all_predictions_before_labels.json'),
        all_original_reviewers=True, protected40_47_unchanged=True, no_quality_admission_without_frozen_gates=True))


if __name__ == '__main__':
    main()
