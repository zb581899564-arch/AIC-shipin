"""First remaining23 real CPU proofs, whole25 fit diagnosis, old first2 adopted."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path

import torch

from parallel_train108 import cases
from t_io import ROOT, check, identity, read, save
from visual_query_metrics120 import evaluate
from visual_query_review120 import check_case

OUT = ROOT / 'visual_query_fit120'
TEMP = Path('/dev/shm/aic_T_visual_query120_remaining')


def main():
    torch.set_num_threads(2)
    result = read(OUT / 'GPU_completion.json'); inputs = read(ROOT / 'visual_query_inputs119/completion.json')
    old = read(ROOT / 'parallel_inputs106/completion.json'); data = read(check(old['loss_bindings']))
    source = cases(data)[inputs['source']]; names = {case.name: case for case in source.cases}
    if (set(result['first_new_cases']) != set(names) - set(inputs['first_engineering_cases'])
            or len(result['first_new_cases']) != 23):
        raise ValueError('Only exact23 remaining first outputs may enter this CPU scope')
    (OUT / 'first_CPU').mkdir(); proofs, temporary = [], []
    for name in result['first_new_cases']:
        proof, retire = check_case(source, names[name], inputs['inputs'][name],
            result['outputs'][name], inputs['actual_query_code'], OUT / 'first_CPU')
        proofs.append(proof); temporary.extend(retire)
    save(OUT / 'first23_CPU_completion.json', dict(state='FIRST_ALL_REMAINING23_REAL_VISUAL_QA_PASS',
        first_new_proofs=proofs, first2_actual_CPU_adopted=identity(ROOT / 'visual_query_engine119/CPU_completion.json'),
        no_old_model_input_or_QA_repeated=True))
    diagnosis = evaluate(source, result['outputs'], inputs, OUT)
    if torch.cuda.is_initialized():
        raise ValueError('Whole fitting diagnosis initialized CUDA')
    cpu = OUT / 'CPU_completion.json'
    save(cpu, dict(state='FIRST_COMPLETE25_SHARED_VISUAL_FIT_DIAGNOSIS_AND_ALL_CPU_PASS',
        source=source.sid, actual_native_windows=25, first_new_native_windows=23,
        first23_CPU=identity(OUT / 'first23_CPU_completion.json'), **diagnosis,
        new_training_updates=0, confirmation_sources_read=0, old105_STOP_unchanged=True,
        no_automatic_training_confirmation_or_production_admission=True))
    retired = []
    for ref in temporary:
        path = check(ref)
        if path.is_symlink() or path.parent != TEMP.resolve(strict=True):
            raise ValueError('New full activation outside exact remaining120 root; do not retire')
        path.unlink(); retired.append(ref)
    save(OUT / 'activation_retirement.json', dict(first_CPU=identity(cpu),
        only_new_full_activations_retired=retired, permanent_projected_model_raw_and_proofs_preserved=True,
        no_old_successful_artifacts_deleted=True))


if __name__ == '__main__':
    main()
