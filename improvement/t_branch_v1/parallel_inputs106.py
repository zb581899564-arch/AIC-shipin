"""New text-only input bindings and exact adoption of all original source loss contracts."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from copy import deepcopy
from pathlib import Path
import shutil
import traceback

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from parallel_input106 import prepare
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'parallel_inputs106'


def inputs(rt, tokenizer, code, old):
    folder = OUT / 'prefixes'
    folder.mkdir()
    mapped, owners = {}, {}
    def transform(ref):
        key = ref['sha256']
        if key not in mapped:
            mapped[key] = prepare(ref, tokenizer, rt, code, folder / ('I%03d' % len(mapped)), owners)
        return mapped[key]
    fit = {sid: {name: transform(ref) for name, ref in rows.items()} for sid, rows in old['fit'].items()}
    development = {sid: {arm: {name: transform(ref) for name, ref in rows.items()}
                        for arm, rows in arms.items()} for sid, arms in old['development'].items()}
    if (sum(map(len, fit.values())) != 217
            or sum(len(rows) for arms in development.values() for rows in arms.values()) != 200
            or len(owners) != 367):
        raise ValueError('Complete417 logical/367 physical native query source domain differs')
    return dict(fit=fit, development=development, original_fit_sources=old['original_fit_sources'],
        development_provenance=old['development_provenance'], physical_owners=owners,
        logical_fit=217, logical_development=200, unique_physical_input_signatures=len(owners))


def loss_bindings(actual):
    original = read(ROOT / 'native_action_loss99/completion.json')
    sources = deepcopy(original['sources'])
    for sid, source in sources.items():
        if set(actual['fit'][sid]) != {row['case'] for row in source['cases']}:
            raise ValueError('Adopted original all-reviewer source loss case domain changed')
        for row in source['cases']:
            current = actual['fit'][sid][row['case']]
            proof = read(check(current))
            if (proof['source_native_cells'] != row['native_cells']
                    or proof['original_CPU'] != row['original_CPU']
                    or proof['prior_native_input'] != row['actual_input_CPU']):
                raise ValueError('Adopted exact original label partition differs from new query input')
            row['adopted_previous_input_CPU'] = row['actual_input_CPU']
            row['actual_input_CPU'] = current
    return dict(sources=sources, publishers=original['publishers'], schedule=original['schedule'],
        original_successful_loss_bindings=identity(ROOT / 'native_action_loss99/completion.json'),
        same_all86_reviewers_and_source_coefficients=True, source_reference_recalculation=0,
        no_labels_in_new_query_text=True)


def main():
    OUT.mkdir()
    torch.set_num_threads(2)
    contract = read(ROOT / 'parallel_contract105/completion.json')
    if contract['state'] != 'FIRST_PARALLEL_NATIVE_QUERY_POSITION_CAUSAL_GRADIENT_CPU_PASS':
        raise ValueError('Actual parallel query causal/gradient contract incomplete')
    required = 367 * (2 * 16384 * 8 + 8192)
    if shutil.disk_usage(ROOT).free < required:
        raise RuntimeError('Specific367 text/first-proof files do not fit current capacity')
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    old = read(ROOT / 'native_action_inputs99/completion.json')
    save(OUT / 'registration.json', dict(actual_CPU_contract=identity(ROOT / 'parallel_contract105/completion.json'),
        adopted_native_inputs=identity(ROOT / 'native_action_inputs99/completion.json'),
        original_loss=identity(ROOT / 'native_action_loss99/completion.json'),
        current_specific_capacity_bytes=required, no_old_visual_CPU_QA_repeated=True,
        no_confirmation_labels_read=True,
        code={n: identity(Path(__file__).with_name(n)) for n in
              ['parallel_inputs106.py', 'parallel_input106.py', 'parallel_query105.py']}))
    actual = inputs(rt, tokenizer, contract['actual_query_code'], old)
    save(OUT / 'loss_bindings.json', loss_bindings(actual))
    if torch.cuda.is_initialized():
        raise ValueError('Text-only input and loss adoption initialized CUDA')
    save(OUT / 'completion.json', dict(state='FIRST_ALL417_PARALLEL_QUERY_TEXT_AND_LOSS_ADOPTION_CPU_PASS',
        **actual, actual_query_code=contract['actual_query_code'],
        loss_bindings=identity(OUT / 'loss_bindings.json'),
        no_old_decode_processor_ASR_or_model_repeated=True, no_confirmation_read=True,
        no_actual_model_training_or_quality_admission=True,
        next='One fixed new protocol/all-source input/model/budget lock and actual first forward/backward cost before any full training.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successful_prefixes=True))
        raise
