"""First prescribed native-action micro only; persist exact remaining recovery."""
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import torch

from actor_roles33 import activate_actor
from frozen_branch46 import RUN
from joint_checkpoint44 import recovery_checkpoint
from joint_data44 import Case, Source
from joint_rollout47 import evaluation_mode
from native_actor98 import attach_native_actor
from native_codec98 import causal_history, preference_loss
from native_greedy100 import generate
from native_input99 import values
from native_sets import NativeTimeline
from native_state100 import fingerprint
from native_training_data99 import coefficients
from summary_recovery88 import gradient_state, rng
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_first_micro101'
TEMP = Path('/dev/shm/aic_T_native_action100_first')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def teacher(model, rt, tokenizer, case, target, greedy, weight, code, state):
    actual = values(case, target['actual_input_CPU'], tokenizer, rt)
    emitted = read(check(read(check(greedy))['raw']))
    history = causal_history(actual['input_ids'], emitted['tokens'], code)
    text_signature = rt.tensor_signature({k: history[k] for k in ['input_ids', 'attention_mask']})
    actual.update({k: history[k] for k in ['input_ids', 'attention_mask']})
    a, b, scalar_weight = coefficients(target, weight)
    activate_actor(model, 'actor')
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads(); model.train()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Dropout) or name.endswith('.visual'):
            module.eval()
    started = time.monotonic()
    output = model(**{k: v.cuda() if torch.is_tensor(v) else v for k, v in actual.items()},
        logits_to_keep=history['logits_to_keep'], use_cache=False, return_dict=True)
    full = output.logits[0].float()
    if full.shape[0] != 32 or not torch.isfinite(full).all():
        raise ValueError('Actual first native teacher full vocabulary activation invalid')
    z = full[:, [code['Yes'], code['No']]]
    loss, logp = preference_loss(z, torch.from_numpy(a).cuda(), torch.from_numpy(b).cuda(), scalar_weight)
    activation = TEMP / 'first_native_TF_full_logits.pt'
    with activation.open('xb') as stream:
        torch.save(dict(logits=full.detach().cpu()), stream)
    save(OUT / 'first_TF_raw.json', dict(target_binding=target, actual_greedy=greedy,
        actual_causal_text_signature=text_signature, choice_logit_positions=history['logits_to_keep'],
        actual_model_state=state, publisher_source_weight=weight,
        binary_logp=logp.detach().cpu().tolist(), weighted_preference_loss=float(loss.detach()),
        temporary_full_logits=identity(activation), teacher_previous_tokens_are_actual_model_choices=True))
    before_cpu = time.monotonic()
    child = subprocess.run([str(PY), '-B', str(Path(__file__).with_name('native_teacher101_cpu.py'))],
        capture_output=True, text=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
                                               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'))
    cpu_seconds = time.monotonic() - before_cpu
    if child.returncode:
        save(OUT / 'first_TF_CPU_failure.json', dict(exit_code=child.returncode,
            stdout=child.stdout, stderr=child.stderr, no_backward_or_optimizer_yet=True))
        raise RuntimeError('Actual native teacher first independent CPU failed')
    loss.backward()
    return dict(forward_backward_and_first_CPU_seconds=time.monotonic() - started,
                one_off_CPU_seconds=cpu_seconds, preference_loss=float(loss.detach()))


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    data = read(check(lock['loss_bindings'])); method = read(check(lock['protocol']))['training']
    publisher = data['schedule'][0]; sid = data['publishers'][publisher][0]
    item = data['sources'][sid]; target = item['cases'][0]
    original = read(check(read(check(target['original_CPU']))['input']))
    case = Case(target['case'], target['original_CPU'], original, {}, {})
    timeline = NativeTimeline.from_clock(read(check(item['source']['clock'])))
    source = Source(sid, [case], timeline, [], {})
    torch.manual_seed(method['seed']); torch.cuda.manual_seed_all(method['seed'])
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    original_state = fingerprint(model, 'default', loaded['base'])
    trainable = attach_native_actor(model)
    state = fingerprint(model, 'actor', loaded['base'])
    count = sum(p.numel() for p in model.parameters()) + 98329 + 37184640 + 28043472 + 6209025
    if original_state != state or count != 8869330010 or sum(p.numel() for _, p in trainable) != 15335424:
        raise ValueError('Actual originalTIME clone/value/parameter acceptance differs')
    TEMP.mkdir(); code = read(ROOT / 'native_action_contract98/completion.json')['actual_token_codec']
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=method['lr'], betas=tuple(method['betas']),
        eps=method['epsilon'], weight_decay=0., foreach=False)
    optimizer.zero_grad(set_to_none=True)
    initial = recovery_checkpoint(TEMP / 'initial_actor_and_optimizer.pt', model, optimizer, 0,
                                   dict(completed_micro=0, **rng()))
    evaluation_mode(model); activate_actor(model, 'actor')
    started = time.monotonic()
    greedy = generate(model, processor.tokenizer, rt, source, case, target['actual_input_CPU'],
        code, state, 'actor', OUT / 'first_greedy', {})
    greedy_seconds = time.monotonic() - started
    teacher_started = time.monotonic()
    stats = teacher(model, rt, processor.tokenizer, case, target, greedy,
                    item['publisher_source_weight'], code, state)
    stats['whole_teacher_seconds_including_data_and_first_CPU'] = time.monotonic() - teacher_started
    if any(p.grad is not None for name, p in model.named_parameters()
           if '.lora_A.actor.' not in name and '.lora_B.actor.' not in name):
        raise ValueError('Native action gradient reached protected BASE/TIME/vision parameters')
    cursor = dict(publisher=publisher, source=sid, case=case.name, completed_micro=1, optimizer_updates=0)
    gradient_started = time.monotonic()
    gradient = gradient_state(TEMP / 'first_accumulated_gradient.pt', trainable, cursor, initial)
    persistence_seconds = time.monotonic() - gradient_started
    if fingerprint(model, 'actor', loaded['base']) != state:
        raise ValueError('First gradient-only micro changed actor weights before any complete publisher')
    evaluation_mode(model); model.set_adapter('default'); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Protected originalBASE/TIME bytes changed during first native micro')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_NATIVE_GREEDY_TEACHER_BACKWARD_COMPLETE_NEEDS_CPU_COST',
        original_loaded=loaded, actual_complete_parameters=count, new_actor_parameters=15335424,
        actual_new_greedy_calls=1, actual_new_teacher_backwards=1, optimizer_updates=0,
        target_binding=target, cursor=cursor, initial_actor_optimizer=initial,
        exact_successful_gradient=gradient, actual_greedy=greedy,
        actual_first_TF=identity(OUT / 'first_TF_raw.json'),
        first_independent_TF_CPU=identity(OUT / 'first_TF_independent_CPU.json'),
        actual_actor_state=state, publisher_source_weight=item['publisher_source_weight'],
        greedy_wall_seconds=greedy_seconds, gradient_persistence_seconds=persistence_seconds,
        timing=stats, first_micro_seconds_excluding_one_off_CPU=greedy_seconds
        + stats['whole_teacher_seconds_including_data_and_first_CPU'] - stats['one_off_CPU_seconds']
        + persistence_seconds,
        original_BASE_TIME_unchanged=True, no_new_dose_or_quality_claim=True,
        next='Adopt this exact first greedy/teacher/gradient and initial actor/Adam/RNG once; cost gate complete remaining216micro/five publisher updates and150dev before explicit remaining-only recovery. Never repeat this successful micro.',
        peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
