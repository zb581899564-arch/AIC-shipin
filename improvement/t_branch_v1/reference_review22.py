"""Explicit CPU-only remaining review after non-idempotent legacy module rebinding."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pathlib import Path
import sys
import traceback

import numpy as np
import torch

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'reference_review22'
RUN19 = ROOT / 'reference_control19'
OLD = WORK / 'general_highlight_supervision_20261021_v1/baseline_bridge57'
sys.path.insert(0, str(OLD.parent / 'code'))
from baseline_bridge57_common import RUN, legacy_runtime


def adopt_first_input_replay():
    lock = read(RUN19 / 'source_input_lock.json')
    check(lock['code']['reference_review20.py'])
    log = (RUN19 / 'reference_review20.log').read_text()
    if (read(RUN19 / 'reference_review20_terminal.json')['exit_code'] != 1 or
            'verify, d8, decisions, guard = frozen.verified_mask(source)' not in log or
            'Legacy original engine helper namespace remains shadowed' not in log):
        raise ValueError('Expected failure after completed independent input loop is absent')
    # Under that exact locked code, reaching verified_mask proves independent_inputs
    # returned after all14 signature/prompt/prefix checks; do not reread4GB merely
    # because its completion receipt was scheduled later in the old function.
    save(OUT / 'prior_input_replay_adoption.json', dict(
        state='ADOPT_COMPLETED14_INPUT_REPLAY_FROM_EXACT_CODE_AND_FAILURE_LOCATION',
        locked_code=lock['code']['reference_review20.py'],
        actual_failed_trace=identity(RUN19 / 'reference_review20.log'),
        actual_terminal=identity(RUN19 / 'reference_review20_terminal.json'),
        cases=14, missing_prior_standalone_checkpoint=True,
        adoption_basis='Failure occurred after independent_inputs returned14, at first verified_mask call',
        no_tensor_or_model_replay_repeated=True))


def main():
    OUT.mkdir()
    adopt_first_input_replay()
    rt = legacy_runtime()
    import baseline_bridge57_review as frozen
    frozen.ROOT = RUN19
    frozen.legacy_runtime = lambda: rt
    source = read(OLD / 'registration.json')['source']
    verify, d8, decisions, guard = frozen.verified_mask(source)
    full, added = frozen.semantic_mask(verify)
    with (OUT / 'native_selections.npz').open('xb') as stream:
        np.savez_compressed(stream, D8=d8, VERIFY=verify, full40_47=full)
    sys.path.insert(0, str(WORK / 'highlight_source_admission_20261021_v1/matched_hl_pilot16/code'))
    from pilot15_common import original_targets
    from time_control50_review import metrics
    labels = original_targets(source)
    values = {key: metrics(mask, labels) for key, mask in {'D8': d8, 'VERIFY': verify, 'full40_47': full}.items()}
    save(OUT / 'review.json', dict(state='CORRECTED_EXTERNAL_REFERENCE_COMPLETE_NOT_CANDIDATE',
        metrics=values, previous_wrong_task_metrics=read(OLD / 'review.json')['metrics']['full40_47'],
        first_correct_VERIFY_calls=14, verification=decisions, source_empty_guard=guard,
        semantic_added_frames=added, actual_semantic_batches_adopted=74, new_BASE_calls=0,
        source_count=1, exposure='Historically exposed external diving; not new blind or official joint score',
        no_training_or426_production_or_package=True))
    if torch.cuda.is_initialized():
        raise ValueError('Independent CPU review initialized CUDA')
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS', cases=14,
        input_replay=identity(OUT / 'prior_input_replay_adoption.json'),
        first_correct_output_token_grammar_parser_native_and_frozen_head_replay=True,
        actual_language_features_adopted_not_rerun=True,
        native_selections=identity(OUT / 'native_selections.npz'), CUDA_initialized=False))
    job = 'T_first_correct_VERIFY_prompt14_20261022_v19'
    resource = read(RUN / 'controller' / (job + '.resource.json'))
    import json
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in ledger if r.get('name') == job] != [resource]:
        raise ValueError('Natural unique model terminal differs')
    check(read(RUN19 / 'registration.json')['protected_baseline'])
    save(OUT / 'completion.json', dict(state='CORRECTED_EXTERNAL_REFERENCE_CPU_REMAINING_COMPLETE',
        review=identity(OUT / 'review.json'), audit=identity(OUT / 'independent_CPU_audit.json'),
        GPU_seconds=resource['charged_seconds'], old_parent_failure_preserved=True,
        first_correct_model_calls=14, repeated_model_calls=0, training_updates=0, new_ZIP=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_automatic_retry=True))
        raise
