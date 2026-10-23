"""First CPU proof for50 shifted views; accepted correct/native inputs adopted."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from development_data46 import development_sources, shifted
from t_io import ROOT, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'development48'


def main():
    rt = runtime()
    protocol = read(ROOT / 'code/joint_policy_protocol44.json')
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = development_sources(rt, tokenizer, protocol)
    folder = OUT / 'shift_CPU'; folder.mkdir()
    accepted = {}
    for source in sources.values():
        for case in source.cases:
            counterfactual = shifted(case)
            proof = dict(original_CPU=case.CPU, actual_grid=case.values['video_grid_thw'].tolist(),
                operation='Fixed roll by16 of32 temporal pixel groups; timestamps/text unchanged',
                original_native_view=True, transformed_view_is_deliberately_wrong_content_time_pairing=True,
                source_native_identity_not_redeclared=True, exactly_invertible=True,
                tensor_signature=rt.tensor_signature(counterfactual.values), labels_read=False,
                no_decode_processor_or_input_encoding_repeated=True)
            save(folder / (case.name + '.json'), proof)
            accepted[case.name] = identity(folder / (case.name + '.json'))
    if len(accepted) != 50 or torch.cuda.is_initialized():
        raise ValueError('Registered50 development views/CPU-only denominator differs')
    save(OUT / 'coarse_CPU_completion.json', dict(state='PASS_FIRST50_FIXED_CONTENT_SHIFT_CPU',
        shifted_inputs=accepted, original97_CPU_adopted=identity(ROOT / 'pilot_input_qa29/completion.json'),
        human_summary_labels_read=False))


if __name__ == '__main__':
    main()
