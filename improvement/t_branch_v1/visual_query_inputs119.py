"""All25 new shared contexts before first2 engineering; no new images or ASR."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import shutil
import traceback

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from parallel_train108 import cases
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime
from visual_query_prefix119 import prepare

OUT = ROOT / 'visual_query_inputs119'


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    if read(ROOT / 'shared_visual_query118_CPU/completion.json')['state'] != (
            'FIRST_SHARED_PREFIX_VISUAL_QUERY_CPU_FEASIBILITY_PASS_NOT8B'):
        raise ValueError('Actual installed-HF CPU/cache/gradient/DeepStack prototype required')
    protocol = read(ROOT / 'code/visual_query_protocol119.json')
    if shutil.disk_usage(ROOT).free < protocol['root_artifact_upper_bytes']:
        raise RuntimeError('Specific25 new prefixes and first native/CPU proofs do not fit actual capacity')
    prior = read(ROOT / 'parallel_inputs106/completion.json'); data = read(check(prior['loss_bindings']))
    sid = data['publishers'][data['schedule'][0]][0]
    if sid != 'L7ddd6bf6c93a' or len(data['sources'][sid]['cases']) != 25:
        raise ValueError('Original first complete publisher differs')
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model_config = Path(config['model_dir']) / 'config.json'
    actual = read(model_config); merge = int(actual['vision_config']['spatial_merge_size'])
    tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
    rt = runtime(); source = cases(data)[sid]; accepted = {}
    for case in source.cases:
        accepted[case.name] = prepare(case, prior['fit'][sid][case.name], tokenizer, rt, merge, OUT / case.name)
    if len(accepted) != 25 or torch.cuda.is_initialized():
        raise ValueError('All25 shared-prefix CPU context scope or CPU-only role differs')
    save(OUT / 'completion.json', dict(state='FIRST_ALL25_LOCAL_VISUAL_SHARED_PREFIX_CPU_INPUTS_PASS',
        source=sid, inputs=accepted, first_engineering_cases=[case.name for case in source.cases[:2]],
        actual_model_config=identity(model_config), actual_spatial_merge_size=merge,
        actual_query_code=prior['actual_query_code'],
        first_CPU118_adopted=identity(ROOT / 'shared_visual_query118_CPU/completion.json'),
        native64_and_visual_signatures_adopted=True, no_source_or_confirmation_labels_read=True,
        real8B_mapping_and_cost_still_unmeasured=True, no_training_or_quality_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_successes=True))
        raise
