"""Same on-policy loss/backward from unmodified shared visual inputs."""
import time

import numpy as np
import torch

from actor_roles33 import activate_actor
from native_codec98 import causal_history, preference_loss
from native_prepared103 import causal_values, unchanged
from native_training_data99 import coefficients
from t_io import check, read


def backward(model, rt, task, greedy, weight, code, state, gpu, snapshot):
    unchanged(gpu, snapshot)
    emitted = read(check(read(check(greedy))['raw']))
    history = causal_history(gpu['input_ids'].cpu(), emitted['tokens'], code)
    signature = rt.tensor_signature({k: history[k] for k in ['input_ids', 'attention_mask']})
    actual = causal_values(gpu, history)
    positive, negative, scalar = coefficients(task, weight)
    activate_actor(model, 'actor')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model.train()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Dropout) or name.endswith('.visual'):
            module.eval()
    started = time.monotonic()
    output = model(**actual, logits_to_keep=history['logits_to_keep'], use_cache=False, return_dict=True)
    full = output.logits[0].float()
    if full.shape[0] != 32 or not torch.isfinite(full).all():
        raise ValueError('Prepared native teacher full vocabulary output differs')
    binary = full[:, [code['Yes'], code['No']]]
    loss, logp = preference_loss(binary, torch.from_numpy(positive).cuda(),
                                  torch.from_numpy(negative).cuda(), scalar)
    raw = dict(target_binding=task, actual_greedy=greedy, publisher_source_weight=weight,
        actual_causal_text_signature=signature, choice_logit_positions=history['logits_to_keep'],
        actual_model_state=state, binary_logits=binary.detach().cpu().tolist(),
        binary_logp=logp.detach().cpu().tolist(), weighted_preference_loss=float(loss.detach()),
        teacher_previous_tokens_are_actual_model_choices=True,
        no_second_visual_input_load_or_transfer=True,
        first_full_vocabulary_CPU='native_first_micro101/first_TF_independent_CPU.json')
    loss.backward()
    raw['actual_forward_backward_seconds'] = time.monotonic() - started
    unchanged(gpu, snapshot)
    return raw
