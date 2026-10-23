"""First full-prefill native action gradient; targets enter only after actual forward."""
import os
from pathlib import Path
import subprocess
import time

import torch

from actor_roles33 import activate_actor
from native_codec98 import preference_loss
from native_prepared103 import unchanged
from native_training_data99 import coefficients
from parallel_forward107 import accepted, forward
from t_io import ROOT, WORK, identity, save

OUT = ROOT / 'parallel_cost107'
TEMP = Path('/dev/shm/aic_T_parallel_first107')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def training_mode(model):
    activate_actor(model, 'actor')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model.train()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Dropout) or name.endswith('.visual'):
            module.eval()


def first_backward(model, source, case, target, code, state, gpu, signature, snapshot, weight):
    training_mode(model)
    started = time.monotonic()
    full, binary = forward(model, gpu, target['actual_input_CPU'], code)
    forward_seconds = time.monotonic() - started
    selection = OUT / 'first_training_selection'
    selection.mkdir()
    output = accepted(source, case, target['actual_input_CPU'], code, state, 'actor',
                      binary, signature, forward_seconds, selection)
    a, b, scalar = coefficients(target, weight)
    loss, logp = preference_loss(binary, torch.from_numpy(a).cuda(), torch.from_numpy(b).cuda(), scalar)
    activation = TEMP / 'first_full_query_logits.pt'
    with activation.open('xb') as stream:
        torch.save(dict(logits=full.detach().cpu()), stream)
    save(OUT / 'first_TF_raw.json', dict(actual_input_CPU=target['actual_input_CPU'],
        target_binding=target, actual_selection=output, actual_model_state=state,
        query_positions=list(range(gpu['input_ids'].shape[1] - 63, gpu['input_ids'].shape[1], 2)),
        binary_logp=logp.detach().cpu().tolist(), weighted_preference_loss=float(loss.detach()),
        publisher_source_weight=weight, temporary_full_logits=identity(activation),
        no_previous_human_or_model_answers_in_input=True))
    before_cpu = time.monotonic()
    child = subprocess.run([str(PY), '-B', str(Path(__file__).with_name('parallel_teacher107_cpu.py'))],
        capture_output=True, text=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
                                               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'))
    cpu_seconds = time.monotonic() - before_cpu
    if child.returncode:
        save(OUT / 'first_TF_CPU_failure.json', dict(exit_code=child.returncode,
            stdout=child.stdout, stderr=child.stderr, no_backward_or_update_yet=True))
        raise RuntimeError('First parallel query independent full-vocabulary CPU failed')
    loss.backward()
    unchanged(gpu, snapshot)
    return dict(actual_selection=output, actual_TF=identity(OUT / 'first_TF_raw.json'),
        actual_first_CPU=identity(OUT / 'first_TF_CPU.json'),
        forward_and_backward_plus_first_CPU_seconds=time.monotonic() - started,
        actual_forward_seconds=forward_seconds, one_off_CPU_seconds=cpu_seconds,
        weighted_source_preference_loss=float(loss.detach()))
