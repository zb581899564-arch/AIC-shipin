"""First150 output audits using the proven native checker, without scoring labels."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import numpy as np
import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from event_native71 import bindings
from event_select72_cpu import replay
from frozen_branch46 import RUN
from summary_context90 import ARMS
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_selection91'


def main():
    torch.set_num_threads(2); rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    cpu = read(ROOT / 'summary_context90/completion.json'); gpu = read(OUT / 'GPU_completion.json')
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    _, grammar = bindings(); candidates = grammar.ascii_token_candidates(tokenizer)
    folder = OUT / 'first_CPU'; folder.mkdir(); proofs = []; frozen = {}
    for sid in sorted(sources):
        source = sources[sid]; masks = {}
        for arm in ARMS:
            if set(gpu['outputs'][sid][arm]) != {c.name for c in source.cases}:
                raise ValueError('Actual complete native source/arm lacks an output')
            mask = np.zeros(len(source.timeline.points), dtype=bool)
            for case in source.cases:
                selected, proof = replay(gpu['outputs'][sid][arm][case.name], case, source,
                    cpu['inputs'][sid][arm][case.name], arm, tokenizer, rt, candidates, folder)
                mask |= selected; proofs.append(proof)
            masks[arm] = mask
        path = OUT / (sid + '_native_coarse.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, **masks)
        frozen[sid] = identity(path)
    if len(proofs) != 150 or torch.cuda.is_initialized():
        raise ValueError('Actual first150 independent native output checks incomplete')
    save(OUT / 'frozen_coarse_masks_before_labels.json', frozen)
    save(OUT / 'CPU_completion.json', dict(state='PASS_FIRST_ALL150_CONTENT_GOAL_NATIVE_OUTPUTS_NOT_FULL40_48_QUALITY',
        actual_first_output_proofs=proofs, frozen_masks=identity(OUT / 'frozen_coarse_masks_before_labels.json'),
        original_label_or_confirmation_quality_read=False, no_actual_output_repaired_or_dropped=True,
        same_old_native_checker_new_outputs_only=True, new8B_calls=0,
        next='First missing originalVERIFY tasks only, adopt oldBASE/semantic/route and identical successful VERIFY; full40.48/all-reviewer masks before quality decision.'))


if __name__ == '__main__':
    main()
