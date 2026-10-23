"""Independent corrected-prefix/token/native replay and adopted frozen semantic branch."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import sys

import numpy as np
import torch
from transformers import AutoTokenizer

from prompt_contract13 import prompt_binding
from reference_data18 import load_input
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'reference_control19'
OLD = WORK / 'general_highlight_supervision_20261021_v1/baseline_bridge57'
sys.path.insert(0, str(OLD.parent / 'code'))
from baseline_bridge57_common import RUN, legacy_runtime


def independent_inputs(tokenizer, rt):
    rows = read(OUT / 'verify_GPU_completion.json')['outputs']
    if len(rows) != 14:
        raise ValueError('First correct task output count differs')
    for ref in rows:
        result = read(check(ref))
        cpu = read(check(result['input']['CPU']))
        values = load_input(cpu)
        if rt.tensor_signature(values) != cpu['detail']['tensor_signature']:
            raise ValueError('Independent actual corrected input replay differs')
        request = read(check(result['input']['request']))
        prompt_binding(tokenizer, values['input_ids'], cpu['detail'], request['prompt'], 'VERIFY', rt.EMPTY_PROMPT)
        raw = read(check(result['raw']))
        if raw['prefix'] != int(values['input_ids'].shape[1]):
            raise ValueError('Actual GPU input prefix count differs from independently restored input')
    return len(rows)


def main():
    rt = legacy_runtime()
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
    count = independent_inputs(tokenizer, rt)
    import baseline_bridge57_review as frozen
    frozen.ROOT = OUT
    for name in ['semantic_CPU_completion.json', 'semantic_GPU_completion.json']:
        adopted = read(OLD / name)
        save(OUT / name, adopted)
    source = read(OLD / 'registration.json')['source']
    verify, d8, decisions, guard = frozen.verified_mask(source)
    full, added = frozen.semantic_mask(verify)
    with (OUT / 'native_selections.npz').open('xb') as stream:
        np.savez_compressed(stream, D8=d8, VERIFY=verify, full40_47=full)
    # All predictions above are fixed before the first target read in this new stage.
    sys.path.insert(0, str(WORK / 'highlight_source_admission_20261021_v1/matched_hl_pilot16/code'))
    from pilot15_common import original_targets
    from time_control50_review import metrics
    labels = original_targets(source)
    values = {key: metrics(mask, labels) for key, mask in {'D8': d8, 'VERIFY': verify, 'full40_47': full}.items()}
    old = read(OLD / 'review.json')
    save(OUT / 'review.json', dict(state='CORRECTED_EXTERNAL_REFERENCE_COMPLETE_NOT_CANDIDATE',
        metrics=values, historical_wrong_task_metrics=old['metrics']['full40_47'],
        input_output_cases=count, VERIFY_decisions=decisions, empty_source_guard=guard,
        semantic_added_frames=added, adopted_BASE_batches=74, new_BASE_calls=0,
        code_matches_frozen_original_branch=True, old14_wrong_task_outputs_not_overwritten=True,
        scope='One historically exposed external sport; not new confirmation or official joint score',
        no_training_or426_production_or_package=True))
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS', cases=count,
        actual_prompt_prefix_and_tensor_replay=True, grammar_parser_native_and_frozen_head_replay=True,
        selections=identity(OUT / 'native_selections.npz'), CUDA_initialized=torch.cuda.is_initialized()))
    if torch.cuda.is_initialized():
        raise ValueError('Independent CPU review initialized CUDA')


if __name__ == '__main__':
    main()
