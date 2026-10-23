"""One prescribed full-query forward/backward and durable exact recovery state."""
import time

import torch

from native_prepared103 import transfer, unchanged
from native_codec98 import preference_loss
from native_training_data99 import coefficients
from parallel_forward107 import accepted, forward
from summary_recovery88 import gradient_state
from t_io import identity, save


def step(model, source, case, task, weight, code, state, actual, rt,
         folder, temporary, trainable, cursor, checkpoint, cpu_seconds):
    folder.mkdir()
    started = time.monotonic()
    gpu, signature, snapshot = transfer(actual, task['actual_input_CPU'], rt)
    before = time.monotonic()
    full, binary = forward(model, gpu, task['actual_input_CPU'], code)
    forward_seconds = time.monotonic() - before
    output = folder / 'selection'
    output.mkdir()
    result = accepted(source, case, task['actual_input_CPU'], code, state, 'actor',
                      binary, signature, forward_seconds, output)
    positive, negative, scalar = coefficients(task, weight)
    loss, logp = preference_loss(binary,
        torch.from_numpy(positive).cuda(), torch.from_numpy(negative).cuda(), scalar)
    projected = dict(target_binding=task, publisher_source_weight=weight,
        actual_model_state=state, actual_selection=result,
        binary_logits=binary.detach().float().cpu().tolist(),
        binary_logp=logp.detach().cpu().tolist(), weighted_preference_loss=float(loss.detach()),
        no_previous_human_or_generated_choice_tokens=True)
    loss.backward()
    unchanged(gpu, snapshot)
    if any(p.grad is not None for name, p in model.named_parameters()
           if '.lora_A.actor.' not in name and '.lora_B.actor.' not in name):
        raise ValueError('Parallel source preference gradient reached protected parameters')
    gradient = gradient_state(temporary / ('micro%03d.pt' % cursor['completed_micro']),
                              trainable, cursor, checkpoint)
    save(folder / 'acceptance.json', dict(cursor=cursor, actual_teacher=projected,
        exact_recovery_gradient=gradient, actual_selection=result,
        source_global_weights_not_window_renormalized=True,
        CPU_load_seconds=cpu_seconds, actual_consumer_seconds=time.monotonic() - started))
    print('PARALLEL108_FIRST_REMAINING_BACKWARD', cursor['completed_micro'], source.sid, case.name, flush=True)
    return identity(folder / 'acceptance.json')
