"""First conditional human-text scores, shared frozen BASE versus original TIME."""
from contextlib import nullcontext
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import torch

from frozen_branch46 import RUN
from description_tokens64 import load_values
from joint_replay44 import forward
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'description_score67'
TEMP = Path('/dev/shm/aic_T_description_score67')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def actual_input(task, rt):
    pair = read(check(task['physical_pair']))
    values = load_values(pair['physical_inputs']['correct'])
    if task['pixel_condition'] == 'wrong':
        wrong = load_values(pair['physical_inputs']['wrong'])
        values['pixel_values_videos'] = wrong['pixel_values_videos']
    with np.load(check(task['tokens']), allow_pickle=False) as data:
        values.update(input_ids=torch.from_numpy(data['input_ids'].copy()),
                      attention_mask=torch.from_numpy(data['attention_mask'].copy()))
        targets = data['target_tokens'].tolist()
    if rt.tensor_signature(values) != task['actual_signature']:
        raise ValueError('Actual caption video/time/text/target input differs')
    return values, targets


def score(model, values, targets, key, role, index, CPU_manifest):
    from peft.tuners.tuners_utils import BaseTunerLayer
    model.set_adapter('default'); model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    context = model.disable_adapter() if role == 'BASE' else nullcontext()
    with context, torch.inference_mode():
        layers = [m for m in model.modules() if isinstance(m, BaseTunerLayer)]
        disabled = sum(bool(layer.disable_adapters) for layer in layers)
        if len(layers) != 144 or disabled != (144 if role == 'BASE' else 0):
            raise ValueError('Actual original BASE/TIME adapter role differs')
        started = time.monotonic()
        logits = forward(model, type('CaptionCase', (), dict(values=values))(), targets)
        target = torch.tensor(targets, device=logits.device, dtype=torch.long)
        logp = logits.float().log_softmax(-1).gather(1, target[:, None]).squeeze(1)
        normalizer = torch.logsumexp(logits.float(), dim=1)
        selected = logits[torch.arange(len(targets), device=logits.device), target].float()
        torch.cuda.synchronize()
        temporary = TEMP / ('%03d.activation.pt' % index)
        with temporary.open('xb') as stream:
            torch.save(dict(logits=logits.detach().cpu()), stream)
        raw = OUT / 'raw' / ('%03d_%s.pt' % (index, role))
        with raw.open('xb') as stream:
            torch.save(dict(input_key=key, model_role=role, targets=targets, CPU_manifest=CPU_manifest,
                shape=list(logits.shape), dtype=str(logits.dtype), target_logp=logp.cpu().tolist(),
                target_logits=selected.cpu().tolist(), log_normalizers=normalizer.cpu().tolist(),
                actual_disabled_adapter_modules=disabled, forward_seconds=time.monotonic() - started,
                temporary_full_logits=identity(temporary)), stream)
        del logits, logp, normalizer, selected
    command = [str(PY), '-B', str(Path(__file__).with_name('description_score67_cpu.py')), str(raw)]
    result = subprocess.run(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'),
        capture_output=True, text=True)
    if result.returncode:
        save(OUT / ('%03d_CPU_failure.json' % index), dict(command=command, exit_code=result.returncode,
            stdout=result.stdout, stderr=result.stderr, all_task_outputs_preserved=True))
        raise RuntimeError('First independent full-vocabulary CPU check failed')
    proof = raw.with_suffix('.CPU.json')
    check(read(raw.with_suffix('.retirement.json'))['first_CPU_proof'])
    print('DESCRIPTION67_FIRST_TF_AND_CPU_PASS', index, role, key, flush=True)
    return dict(raw=identity(raw), CPU=identity(proof), retirement=identity(raw.with_suffix('.retirement.json')))


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    cpu = read(check(lock['all_actual_CPU_inputs']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Actual original shared BASE/TIME parameter count differs')
    TEMP.mkdir(); (OUT / 'raw').mkdir()
    outputs, index = {}, 0
    for key, task in cpu['tasks'].items():
        values, targets = actual_input(task, rt); outputs[key] = {}
        for role in ['BASE', 'TIME']:
            index += 1
            outputs[key][role] = score(model, values, targets, key, role, index, lock['all_actual_CPU_inputs'])
        del values
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Protected original BASE or TIME changed')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_ALL_HUMAN_CONTENT_MODALITY_ROLE_SCORES_AND_CPU_PASS',
        outputs=outputs, actual_new_causal_TF_calls=index, no_generation_or_training=True,
        actual_GPU_model_parameters=8782459120, protected_pipeline_plus_ASR_parameters=8819742089,
        peak_torch_bytes=torch.cuda.max_memory_allocated(), all_original_weights_unchanged=True,
        permanent_raw_projections_and_first_full_vocabulary_CPU_proofs=True))


if __name__ == '__main__':
    main()
