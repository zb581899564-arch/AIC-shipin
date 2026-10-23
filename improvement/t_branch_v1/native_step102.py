"""Remaining prescribed native micros; durable successful gradients, no window renormalization."""
import time

import torch

from actor_roles33 import activate_actor
from joint_rollout47 import evaluation_mode
from native_codec98 import causal_history, preference_loss
from native_greedy100 import generate
from native_input99 import values
from native_training_data99 import coefficients
from summary_recovery88 import gradient_state
from t_io import check, identity, read, save


def training_mode(model):
    activate_actor(model, 'actor')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model.train()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Dropout) or name.endswith('.visual'):
            module.eval()


def teacher(model, rt, tokenizer, case, task, greedy, weight, code, state):
    actual = values(case, task['actual_input_CPU'], tokenizer, rt)
    emitted = read(check(read(check(greedy))['raw']))
    history = causal_history(actual['input_ids'], emitted['tokens'], code)
    signature = rt.tensor_signature({k: history[k] for k in ['input_ids', 'attention_mask']})
    actual.update({k: history[k] for k in ['input_ids', 'attention_mask']})
    positive, negative, scalar = coefficients(task, weight)
    training_mode(model)
    output = model(**{k: v.cuda() if torch.is_tensor(v) else v for k, v in actual.items()},
        logits_to_keep=history['logits_to_keep'], use_cache=False, return_dict=True)
    full = output.logits[0].float()
    if full.shape[0] != 32 or not torch.isfinite(full).all():
        raise ValueError('Actual native teacher output is incomplete or nonfinite')
    binary = full[:, [code['Yes'], code['No']]]
    loss, logp = preference_loss(binary, torch.from_numpy(positive).cuda(),
                                  torch.from_numpy(negative).cuda(), scalar)
    raw = dict(actual_greedy=greedy, target_binding=task, publisher_source_weight=weight,
        actual_causal_text_signature=signature, choice_logit_positions=history['logits_to_keep'],
        actual_model_state=state, binary_logits=binary.detach().cpu().tolist(),
        binary_logp=logp.detach().cpu().tolist(), weighted_preference_loss=float(loss.detach()),
        teacher_previous_tokens_are_actual_model_choices=True,
        first_full_vocabulary_implementation_proof='native_first_micro101/first_TF_independent_CPU.json')
    loss.backward()
    del output, full, binary, loss, actual
    return raw


def micro(model, processor, rt, source, case, task, weight, code, state,
          folder, temporary, trainable, cursor, checkpoint, cache):
    folder.mkdir()
    started = time.monotonic()
    evaluation_mode(model)
    activate_actor(model, 'actor')
    greedy = generate(model, processor.tokenizer, rt, source, case, task['actual_input_CPU'],
                       code, state, 'actor', folder / 'greedy', cache)
    raw = teacher(model, rt, processor.tokenizer, case, task, greedy, weight, code, state)
    if any(p.grad is not None for name, p in model.named_parameters()
           if '.lora_A.actor.' not in name and '.lora_B.actor.' not in name):
        raise ValueError('Native preference gradient reached protected model parameters')
    saved_gradient = gradient_state(temporary / ('micro%03d.pt' % cursor['completed_micro']),
                                      trainable, cursor, checkpoint)
    save(folder / 'acceptance.json', dict(cursor=cursor, actual_greedy=greedy,
        actual_teacher=raw, exact_recovery_gradient=saved_gradient,
        actual_micro_seconds=time.monotonic() - started,
        original_source_global_coefficients=True, no_window_or_blank_window_renormalization=True))
    print('NATIVE102_SUCCESSFUL_MICRO', cursor['completed_micro'], cursor['publisher'], case.name, flush=True)
    return identity(folder / 'acceptance.json')
