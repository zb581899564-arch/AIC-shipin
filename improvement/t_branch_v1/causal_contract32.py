"""First real-prefix/grammar-to-policy bridge on four already accepted control answers."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from fractions import Fraction
from pathlib import Path
import sys
import traceback

import numpy as np
import torch
from transformers import AutoTokenizer

from causal_policy32 import actual_allowed_states, causal_suffix
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'causal_contract32'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime


def one_case(result, tokenizer, candidates, make_grammar):
    cpu = read(check(result['CPU']))
    raw = read(check(result['raw']))
    with np.load(check(cpu['encoded']), allow_pickle=False) as archive:
        prefix = torch.from_numpy(archive['input_ids'].copy())
    if prefix.shape[1] != raw['prefix']:
        raise ValueError('Actual accepted prefix and generated suffix boundary differ')
    inputs = causal_suffix(prefix, raw['token_ids'])
    grammar = make_grammar(tokenizer, raw['prefix'], Fraction(result['source_end']) - Fraction(result['source_start']),
        candidate_token_ids=candidates, eos_token_ids=raw['eos'], allow_empty=True)
    allowed = actual_allowed_states(prefix, raw['token_ids'], grammar)
    if inputs['causal_positions'][0] != raw['prefix'] - 1 or inputs['logits_to_keep'] != len(raw['token_ids']):
        raise ValueError('Actual model causal logit slice does not include first action and finalEOS')
    path = OUT / (result['case'] + '_text.npz')
    with path.open('xb') as stream:
        np.savez_compressed(stream, input_ids=inputs['input_ids'].numpy(),
                            attention_mask=inputs['attention_mask'].numpy(), targets=inputs['targets'].numpy())
    save(OUT / (result['case'] + '.json'), dict(case=result['case'], original_CPU=result['CPU'],
        original_raw=result['raw'], causal_text=identity(path),
        prefix_tokens=raw['prefix'], suffix_tokens=len(raw['token_ids']),
        logits_to_keep=inputs['logits_to_keep'], actual_causal_positions=inputs['causal_positions'],
        actual_allowed_tokens=allowed, forced_states=sum(len(row) == 1 for row in allowed),
        branching_states=sum(len(row) > 1 for row in allowed),
        payload_tensors_adopt_original_CPU=True, no_human_JSON_or_labels_in_sequence=True,
        future_probe_only_not_optimizer_training_admission=True))
    print('ACTUAL_CAUSAL_CONTRACT32', result['case'], len(allowed), flush=True)
    return identity(OUT / (result['case'] + '.json'))


def main():
    OUT.mkdir()
    legacy_runtime()
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    candidates = ascii_token_candidates(tokenizer)
    outputs = read(ROOT / 'pilot_cost25/gpu_completion.json')['outputs']
    save(OUT / 'registration.json', dict(actual_first4_outputs=identity(ROOT / 'pilot_cost25/gpu_completion.json'),
        source_code=identity(Path(__file__).with_name('causal_policy32.py')),
        original_task='Constrained originalTIME native64 greedy, no new generation or optimizer',
        complete_grammar_allowed_actions_not_full_vocabulary_normalizer=True,
        model_actual_logit_or_gradient_not_yet_tested=True))
    accepted = [one_case(read(check(ref)), tokenizer, candidates, make_prefix_constraint) for ref in outputs]
    save(OUT / 'completion.json', dict(state='PASS_REAL4_CAUSAL_PREFIX_GRAMMAR_POLICY_CONTRACT',
        accepted=accepted, model_calls=0, optimizer_updates=0,
        remaining='Actual Qwen conditional-logit replay, cloned actor/reference identity, real gradient and budget'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
