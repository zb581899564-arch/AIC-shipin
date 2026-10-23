"""First50 label-free query permutation CPU inputs; accepted pixels stay referenced."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import shutil
import traceback

import numpy as np
import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from parallel_train108 import cases
from query_binding117_common import layout, prepare, remap
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'query_binding_inputs117'


def contracts(code, tokenizer, arms):
    for j, token in enumerate(code['anchors']):
        if tokenizer.encode(tokenizer.decode([token]), add_special_tokens=False) != [token]:
            raise ValueError('Actual reused query anchor token is not exact')
    native = np.arange(64, dtype=np.float64).reshape(32, 2)
    for arm in arms:
        cells, labels = layout(arm)
        query = native[cells]
        restored = remap(query, cells)
        independently = np.stack([query[cells.index(j)] for j in range(32)])
        if not np.array_equal(restored, native) or not np.array_equal(restored, independently):
            raise ValueError('Independent32-cell inverse scatter failed')
        if sorted(labels) != list(range(32)):
            raise ValueError('Counterfactual anchor labels are not a complete bijection')
    return dict(actual_tokenizer_and_two_inverse_bijections=True,
        all32_native_cells_retained=True, previous_answers_or_labels_in_suffix=False,
        causal_position_implementation_adopted=identity(ROOT / 'parallel_contract105/completion.json'),
        synthetic_remap_is_not_an8B_result=True)


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    protocol = read(ROOT / 'code/query_binding_protocol117.json')
    prior = read(ROOT / 'parallel_fit115/completion.json')
    if (prior['state'] != 'FIRST_FINAL_FIT25_ALL_NATIVE_CPU_AND_METRICS_PASS'
            or prior['all_goal_GPU_seconds'] != protocol['Goal_GPU_seconds_before']):
        raise ValueError('Exact completed115 evidence or original Goal budget differs')
    if shutil.disk_usage(ROOT).free < protocol['specific_artifact_upper_bytes']:
        raise RuntimeError('Specific complete50 text/raw/proof artifacts do not fit current capacity')
    old = read(ROOT / 'parallel_inputs106/completion.json')
    data = read(check(old['loss_bindings'])); sid = data['publishers'][data['schedule'][0]][0]
    if sid != 'L7ddd6bf6c93a' or len(data['sources'][sid]['cases']) != 25:
        raise ValueError('Entire preregistered first fitting publisher differs')
    rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    checks = contracts(old['actual_query_code'], tokenizer, protocol['arms'])
    source = cases(data)[sid]; result = {}
    save(OUT / 'registration.json', dict(protocol=identity(ROOT / 'code/query_binding_protocol117.json'),
        original25fit_CPU=identity(ROOT / 'parallel_fit115/CPU_completion.json'),
        prior_all_inputs=identity(ROOT / 'parallel_inputs106/completion.json'), CPU_contracts=checks,
        no_old_media_processor_ASR_QA_or_model_repeated=True))
    for arm in protocol['arms']:
        folder = OUT / arm; folder.mkdir(); result[arm] = {}
        for case in source.cases:
            result[arm][case.name] = prepare(case, source, old['fit'][sid][case.name],
                tokenizer, rt, old['actual_query_code'], arm, folder / case.name)
    if sum(map(len, result.values())) != 50 or torch.cuda.is_initialized():
        raise ValueError('Complete50 first CPU input scope or CPU-only role differs')
    save(OUT / 'completion.json', dict(state='FIRST_ALL50_QUERY_BINDING_TRANSFORM_CPU_INPUTS_PASS',
        source=sid, inputs=result, actual_query_code=old['actual_query_code'], CPU_contracts=checks,
        all50_first_text_roundtrips=True, accepted_visual_signatures_adopted=True,
        no_model_training_or_quality_admission=True, no_human_labels_read=True,
        actual_code={name: identity(ROOT / 'code' / name) for name in
                    ['query_binding_inputs117.py', 'query_binding117_common.py', 'query_binding_protocol117.json']}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_successes=True))
        raise
