"""First new VERIFY replay and frozen complete-source audiovisual comparison."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import numpy as np
import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN, semantic_prediction, verify_modules
from development_data46 import development_sources
from development_review48 import retained
from preference_reward import summary_agreement
from speech_task60 import ARMS, OUT
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime


def decisions(tokenizer, cpu, gpu):
    contract, grammar, _ = verify_modules()
    candidates = grammar.candidate_tokens(tokenizer, contract.responses())
    if set(cpu['tasks']) != set(gpu['outputs']):
        raise ValueError('Incomplete unique VERIFY result set')
    resolved = {}
    for key, ref in gpu['outputs'].items():
        row = read(check(ref))
        if key in cpu['adopted_VERIFY_outputs']:
            if ref != cpu['adopted_VERIFY_outputs'][key] or row['input'] != cpu['tasks'][key]:
                raise ValueError('Successful old VERIFY adoption changed task/input')
        else:
            raw = read(check(row['raw'])); request = read(check(cpu['tasks'][key]['request']))
            rule = grammar.VerifyConstraint(tokenizer, raw['prefix'], request, raw['eos'], candidates)
            rule.assert_complete(torch.tensor(raw['tokens'], dtype=torch.long))
            text = tokenizer.decode(raw['tokens'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
            if contract.resolve(text, request, execution_status='MODEL_OK') != row['decision'] or row['input'] != cpu['tasks'][key]:
                raise ValueError('First new VERIFY token/grammar/native task replay differs')
        resolved[key] = row['decision']['decision']
    return resolved


def main():
    runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    cpu, gpu = read(OUT / 'verify_CPU_completion.json'), read(OUT / 'verify_GPU_completion.json')
    resolved = decisions(tokenizer, cpu, gpu)
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    semantic = read(OUT / 'coarse_GPU_completion.json')['semantic']
    old = read(ROOT / 'development_remaining55/frozen_all_predictions_before_labels.json')
    predictions, bindings = {}, {}
    for sid, source in sources.items():
        native = read(ROOT / 'development_semantic46' / sid / 'semantic_CPU_completion.json')
        features = read(check(semantic[sid]))['outputs']
        predictions[sid], bindings[sid] = {}, {}
        for arm in ARMS:
            if arm == 'original_correct':
                with np.load(check(old[sid][arm]['native']), allow_pickle=False) as archive:
                    predictions[sid][arm] = archive['full40_47'].copy()
                bindings[sid][arm] = dict(adopted_successful_native=old[sid][arm]['native'], repeated_original_pipeline=0)
            else:
                d8, verified, guard = retained(source, cpu['source_policies'][sid][arm], cpu['tasks'], resolved)
                full, residual = semantic_prediction(verified, native, features)
                predictions[sid][arm] = full
                path = OUT / (sid + '_' + arm + '_native.npz')
                with path.open('xb') as stream:
                    np.savez_compressed(stream, D8=d8, VERIFY=verified, full40_47=full, residual=residual)
                bindings[sid][arm] = dict(native=identity(path), empty_source_guard=guard, occupancy_recomputed=True)
    save(OUT / 'frozen_predictions_before_labels.json', bindings)
    labeled = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=True)
    metrics = {sid: {arm: summary_agreement(mask, labeled[sid].reviews, len(labeled[sid].reviews))
        for arm, mask in arms.items()} for sid, arms in predictions.items()}
    means = {arm: float(np.mean([metrics[sid][arm]['mean_f1'] for sid in sources])) for arm in ARMS}
    changes = {sid: dict(delta_f1=metrics[sid]['speech_correct']['mean_f1'] - metrics[sid]['original_correct']['mean_f1'],
        added=int((predictions[sid]['speech_correct'] & ~predictions[sid]['original_correct']).sum()),
        removed=int((predictions[sid]['original_correct'] & ~predictions[sid]['speech_correct']).sum())) for sid in sources}
    coarse = read(ROOT / 'development_remaining55/review.json')['original_coarse_controls']
    gates = dict(mean_beats_complete40_47=means['speech_correct'] > means['original_correct'],
        mean_beats_original_TIME=means['speech_correct'] > float(np.mean(list(coarse.values()))),
        both_development_publishers_improve=all(row['delta_f1'] > 0 for row in changes.values()),
        aligned_speech_beats_shifted=means['speech_correct'] > means['speech_shift'],
        no_new_empty_source=all(predictions[sid]['speech_correct'].any() or not predictions[sid]['original_correct'].any() for sid in sources))
    gates = {key: bool(value) for key, value in gates.items()}
    save(OUT / 'review.json', dict(state='PASS_FIXED_WHOLE_SPEECH_VISUAL_DEV' if all(gates.values()) else 'STOP_FIXED_WHOLE_SPEECH_VISUAL_DEV',
        means=means, metrics=metrics, changes=changes, gates=gates, original_coarse_controls=coarse,
        all_original_reviewers=True, historical_exposure='Development already exposed, not blind',
        official_joint_score='UNKNOWN', no_threshold_or_prompt_or_training_retry=True))
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS_FIRST_NEW_AV_OUTPUT_AND_COMPLETE_NATIVE_PIPELINE',
        first100_coarse_QA=cpu['first100_output_QA'], new_VERIFY_replayed=gpu['actual_calls'],
        successful_old_VERIFY_adopted=gpu['adopted_calls'], original_complete40_47_adopted=True,
        all_new_predictions_before_reference=identity(OUT / 'frozen_predictions_before_labels.json')))


if __name__ == '__main__':
    main()
