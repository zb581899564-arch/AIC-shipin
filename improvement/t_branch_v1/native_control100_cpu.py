"""First50 initial native-codec output QA/masks, no human quality or training."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import numpy as np
import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from frozen_branch46 import RUN
from native_audit100 import audit
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_action_control100'


def main():
    torch.set_num_threads(2); rt = runtime()
    inputs = read(ROOT / 'native_action_inputs99/completion.json')
    result = read(OUT / 'GPU_completion.json')
    code = read(ROOT / 'native_action_contract98/completion.json')['actual_token_codec']
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    arm = read(ROOT / 'code/native_action_protocol98.json')['development_matrix'][0]
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    folder = OUT / 'first_CPU'; folder.mkdir(); proofs, token_proofs, frozen = [], {}, {}
    for sid, source in sources.items():
        if set(result['outputs'][sid]) != {case.name for case in source.cases}:
            raise ValueError('Complete originalTIME native-codec source denominator differs')
        mask = np.zeros(len(source.timeline.points), dtype=bool)
        for case in source.cases:
            selected, proof = audit(result['outputs'][sid][case.name], source, case,
                inputs['development'][sid][arm][case.name], code, tokenizer, folder, token_proofs)
            mask |= selected; proofs.append(proof)
        path = OUT / (sid + '_coarse.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, coarse=mask)
        frozen[sid] = identity(path)
    if len(proofs) != 50 or len(token_proofs) != result['first_physical_calls'] or torch.cuda.is_initialized():
        raise ValueError('First native-codec control output QA incomplete or initialized CUDA')
    save(OUT / 'CPU_completion.json', dict(state='FIRST50_ORIGINAL_TIME_NATIVE_CODEC_CPU_PASS_NOT_QUALITY',
        first_geometry_proofs=proofs, first_physical_token_proofs=token_proofs,
        frozen_source_masks=frozen, human_reference_or_quality_read=False,
        original_TIME_codec_control_adopt_for_later_once=True, no_actual_training_or_package=True))


if __name__ == '__main__':
    main()
