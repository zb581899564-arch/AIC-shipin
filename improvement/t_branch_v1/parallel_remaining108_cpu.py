"""First full training and150 final outputs review; no proxy or production admission."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import torch
from safetensors.torch import load_file

from development_data46 import development_sources
from parallel_audit107 import audit
from parallel_train108 import cases
from parallel_training_audit108 import state_digest, training
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'parallel_remaining108'


def main():
    torch.set_num_threads(2)
    result = read(OUT / 'GPU_completion.json')
    inputs = read(ROOT / 'parallel_inputs106/completion.json')
    protocol = read(ROOT / 'code/parallel_protocol105.json')
    data = read(check(inputs['loss_bindings']))
    reviewed = training(result, data)
    save(OUT / 'training_CPU.json', reviewed)
    weights = load_file(str(check(result['final_adapter']['weights'])), device='cpu')
    if (len(weights) != 288 or sum(v.numel() for v in weights.values()) != 15335424
            or any(v.dtype != torch.float32 or not torch.isfinite(v).all() for v in weights.values())
            or state_digest(weights, result['actual_loaded']['base']) != reviewed['actual_final_actor_state']):
        raise ValueError('Final FP32 native-query checkpoint differs from actual final training state')
    fit = cases(data)
    folder = OUT / 'first_training_output_CPU'
    folder.mkdir()
    new_training_output_proofs = []
    for update_ref in result['training']['publisher_updates']:
        for ref in read(check(update_ref))['all_prescribed_micro']:
            row = read(check(ref))
            if row.get('adopted_first_CPU'):
                continue
            sid = row['cursor']['source']
            name = row['cursor']['case']
            source = fit[sid]
            case = next(c for c in source.cases if c.name == name)
            _, proof = audit(row['actual_selection'], source, case,
                row['actual_teacher']['target_binding']['actual_input_CPU'], inputs['actual_query_code'], folder)
            new_training_output_proofs.append(proof)
    dev_sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                      values=False, labels=False)
    output = read(check(result['development']))
    folder = OUT / 'first_dev_CPU'
    folder.mkdir()
    dev_proofs = {}
    for index, arm in enumerate(protocol['development_matrix'][1:], 1):
        (folder / arm).mkdir()
        dev_proofs[arm] = {}
        for sid, source in dev_sources.items():
            if set(output['outputs'][arm][sid]) != {case.name for case in source.cases}:
                raise ValueError('Final parallel development source/window domain incomplete')
            for case in source.cases:
                ref = output['outputs'][arm][sid][case.name]
                if read(check(ref))['actual_model_state'] != reviewed['actual_final_actor_state']:
                    raise ValueError('Development used another checkpoint than the fixed final actor')
                _, proof = audit(ref, source, case,
                    inputs['development'][sid][protocol['input_arm_keys'][index]][case.name],
                    inputs['actual_query_code'], folder / arm)
                dev_proofs[arm][case.name] = proof
    if (len(new_training_output_proofs) != 216 or sum(map(len, dev_proofs.values())) != 150
            or torch.cuda.is_initialized()):
        raise ValueError('Actual complete first training/development QA denominator differs')
    save(OUT / 'CPU_completion.json', dict(state='COMPLETE217_TRAINING_AND150_DEV_FIRST_CPU_PASS_NOT_QUALITY',
        actual_optimizer_updates=5, actual_new_target_forwards=216, adopted_first_training_micro=1,
        complete_native_training_windows=217, all_original_reviewers=86,
        independent_training=identity(OUT / 'training_CPU.json'),
        new_training_output_proofs=new_training_output_proofs, new150dev_proofs=dev_proofs,
        original50control_CPU_adopted=identity(ROOT / 'parallel_cost107/CPU_completion.json'),
        final_FP32_adapter=result['final_adapter'], actual_parameters=8869330010,
        no_quality_confirmation_or_production_admission=True,
        next='First complete native-source downstream D8/VERIFY/current40.48 comparison, adopting all originalBASE/head/route and identical accepted VERIFY. No new confirm labels before frozen development quality gates.'))


if __name__ == '__main__':
    main()
