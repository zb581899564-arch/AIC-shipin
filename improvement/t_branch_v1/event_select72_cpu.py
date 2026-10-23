"""First full native action/token audit; source masks frozen before diagnostic labels."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction

import numpy as np
import torch
from transformers import AutoTokenizer

from causal_policy32 import actual_allowed_states
from development_data46 import development_sources
from event_native71 import bindings, constraint
from event_select72_common import ARMS, CPU, OUT, prefix_ids
from frozen_branch46 import RUN
from preference_reward import summary_agreement
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime


def replay(ref, case, source, task, arm, tokenizer, rt, candidates, folder):
    row = read(check(ref)); raw = read(check(row['raw']))
    payload = torch.load(check(row['allowed_scores']), map_location='cpu', weights_only=True)
    ids = prefix_ids(case, task)
    if (row['case'] != case.name or row['arm'] != arm or row['original_CPU'] != case.CPU
            or row['actual_input_proof'] != task or raw['prefix'] != ids.shape[1]
            or row['tokens'] != raw['tokens'] or raw['tokens'] != payload['tokens']):
        raise ValueError('First actual native selector task/token binding differs')
    rule = constraint(tokenizer, ids.shape[1], case, source, raw['eos'], candidates)
    rule.assert_complete(torch.tensor(raw['tokens'], dtype=torch.long))
    allowed = actual_allowed_states(ids, raw['tokens'], rule)
    if allowed != payload['allowed'] or len(allowed) != len(payload['scores']):
        raise ValueError('First independent native feasible-action replay differs')
    for token, domain, logits in zip(raw['tokens'], allowed, payload['scores']):
        scores = logits.numpy().astype(np.float64)
        if scores.shape != (len(domain),) or not np.isfinite(scores).all():
            raise ValueError('Actual greedy choice differs from native constrained scores')
        first_max_token = min(value for value, score in zip(domain, scores) if score == scores.max())
        if first_max_token != token:
            raise ValueError('Actual greedy tie break differs from full-vocabulary argmax')
    text = tokenizer.decode(raw['tokens'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
    parsed, errors, warnings = rt.parse_segments(text,
        Fraction(case.meta['window_end']) - Fraction(case.meta['window_start']), allow_empty=True)
    if (text != raw['text'] or parsed is None or parsed != row['segments'] or errors
            or warnings != row['warnings'] or row['status'] != ('MODEL_OK' if parsed else 'LEGAL_EMPTY')):
        raise ValueError('First original parser/text replay differs')
    start = Fraction(case.meta['window_start'])
    mask = np.zeros(len(source.timeline.points), dtype=bool)
    for first, last in parsed:
        selected = source.timeline.intervals([(start + Fraction(str(first)), start + Fraction(str(last)))])
        if not selected.any():
            raise ValueError('A generated segment has zero native PTS; never repair or drop it')
        mask |= selected
    path = folder / (arm + '_' + case.name + '.json')
    save(path, dict(state='PASS_FIRST_NATIVE_GREEDY_TOKEN_GRAMMAR_AND_ACTUAL_PTS',
        actual_output=ref, source=source.sid, case=case.name, arm=arm,
        native_frames=int(mask.sum()), successful_empty=(not parsed), new_model_calls=0))
    return mask, identity(path)


def main():
    torch.set_num_threads(2); rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    cpu = read(CPU / 'completion.json'); gpu = read(OUT / 'GPU_completion.json')
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    _, grammar = bindings(); candidates = grammar.ascii_token_candidates(tokenizer)
    folder = OUT / 'first_CPU'; folder.mkdir(); masks, proofs, frozen = {}, [], {}
    for sid, source in sources.items():
        masks[sid] = {}
        for arm in ARMS:
            if set(gpu['outputs'][sid][arm]) != {case.name for case in source.cases}:
                raise ValueError('Complete native source lacks an actual window output')
            mask = np.zeros(len(source.timeline.points), dtype=bool)
            for case in source.cases:
                selected, proof = replay(gpu['outputs'][sid][arm][case.name], case, source,
                    cpu['inputs'][sid][arm][case.name], arm, tokenizer, rt, candidates, folder)
                mask |= selected; proofs.append(proof)
            masks[sid][arm] = mask
        path = OUT / (sid + '_coarse_native.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, **masks[sid])
        frozen[sid] = identity(path)
    save(OUT / 'frozen_coarse_masks_before_labels.json', frozen)
    labeled = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=True)
    metrics = {sid: {arm: summary_agreement(mask, labeled[sid].reviews, len(labeled[sid].reviews))
        for arm, mask in arms.items()} for sid, arms in masks.items()}
    if len(proofs) != 150 or torch.cuda.is_initialized():
        raise ValueError('All150 first native output proofs must complete without CUDA')
    save(OUT / 'CPU_completion.json', dict(state='PASS_FIRST_ALL150_NATIVE_MEMORY_OUTPUTS_NOT_FULL40_48_QUALITY',
        first150_independent_proofs=proofs, frozen_masks=identity(OUT / 'frozen_coarse_masks_before_labels.json'),
        coarse_only_metrics=metrics, no_original_action_repaired_or_discarded=True,
        all_original_reviewers=True, fresh_confirmation_read=False, new_models=0,
        next='Only separately bound exact VERIFY/semantic/current40.48 route full source comparison can qualify this candidate; no coarse proxy hard gate or F1 claim'))


if __name__ == '__main__':
    main()
