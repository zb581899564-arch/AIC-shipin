"""All25 first real masked QA, then source diagnosis; no old QA repeated."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import torch

from localized_query_metrics122 import evaluate
from localized_query_review122 import check_case
from parallel_train108 import cases
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'localized_query122'
TEMP = Path('/dev/shm/aic_T_localized_query122')


def main():
    torch.set_num_threads(2)
    result = read(OUT / 'GPU_completion.json'); lock = read(OUT / 'source_input_lock.json')
    inputs = read(check(lock['actual_inputs'])); accepted = read(check(lock['accepted_masks']))
    protocol = read(check(lock['protocol']))
    data = read(check(read(ROOT / 'parallel_inputs106/completion.json')['loss_bindings']))
    source = cases(data)[inputs['source']]
    if set(result['outputs']) != {case.name for case in source.cases} or len(source.cases) != 25:
        raise ValueError('Entire fixed25 output set differs')
    (OUT / 'first_CPU').mkdir(); proofs = []; temporary = []
    for case in source.cases:
        proof, retire = check_case(source, case, inputs['inputs'][case.name], result['outputs'][case.name],
            inputs['actual_query_code'], accepted['masks'][case.name]['mask'], OUT / 'first_CPU')
        proofs.append(proof); temporary.extend(retire)
    save(OUT / 'first25_CPU_completion.json', dict(state='ALL25_FIRST_REAL_MASKED_INPUT_OUTPUT_QA_PASS',
        first_proofs=proofs, original_input_and_mask_QA_adopted=True, no_old_QA_repeated=True))
    diagnosis = evaluate(source, result['outputs'], inputs, OUT, protocol['local_information_gate'])
    if torch.cuda.is_initialized():
        raise ValueError('Independent first CPU initialized CUDA')
    save(OUT / 'CPU_completion.json', dict(state='COMPLETE25_REAL_LOCAL_VISIBILITY_CPU_AND_DIAGNOSIS_PASS',
        first_CPU=identity(OUT / 'first25_CPU_completion.json'), **diagnosis,
        confirmation_sources_read=0, new_training_updates=0, new_T_ZIPs=0))
    retired = []
    for ref in temporary:
        path = check(ref)
        if path.is_symlink() or path.parent != TEMP.resolve(strict=True):
            raise ValueError('Unregistered temporary activation retirement denied')
        path.unlink(); retired.append(ref)
    save(OUT / 'activation_retirement.json', dict(first_CPU=identity(OUT / 'CPU_completion.json'),
        only_new_full_activations_retired=retired, permanent_raw_projected_witnesses_and_old_evidence_retained=True))


if __name__ == '__main__':
    main()
