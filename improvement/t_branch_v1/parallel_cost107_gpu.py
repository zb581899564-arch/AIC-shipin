"""First50 originalTIME query controls and one prescribed training micro, one load."""
from pathlib import Path
import time

import torch

from development_data46 import development_sources
from frozen_branch46 import RUN
from joint_checkpoint44 import recovery_checkpoint
from joint_data44 import Case, Source
from joint_rollout47 import evaluation_mode
from native_actor98 import attach_native_actor
from native_prepared103 import Prefetch, transfer
from native_sets import NativeTimeline
from native_state100 import fingerprint
from parallel_forward107 import infer
from parallel_input106 import values
from parallel_training107 import TEMP, first_backward
from summary_recovery88 import gradient_state, rng
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'parallel_cost107'


def controls(model, processor, rt, inputs, code, state, protocol):
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    items = [(sid, source, case, inputs['development'][sid][protocol['input_arm_keys'][0]][case.name])
             for sid, source in sources.items() for case in source.cases]
    def loader(item):
        started = time.monotonic()
        actual = values(item[2], item[3], processor.tokenizer, rt)
        return actual, time.monotonic() - started
    outputs, timings = {}, []
    folder = OUT / 'initial_controls'
    folder.mkdir()
    started = time.monotonic()
    with Prefetch(items, loader) as pending:
        for (sid, source, case, proof), (actual, cpu_seconds) in pending:
            before = time.monotonic()
            gpu, signature, _ = transfer(actual, proof, rt)
            transfer_seconds = time.monotonic() - before
            ref, seconds = infer(model, source, case, proof, code, state, 'default',
                                  gpu, signature, folder / case.name)
            outputs.setdefault(sid, {})[case.name] = ref
            timings.append(dict(case=case.name, CPU_load_seconds=cpu_seconds,
                actual_transfer_seconds=transfer_seconds, actual_forward_seconds=seconds,
                actual_consumer_seconds=time.monotonic() - before))
            del gpu, actual
            print('PARALLEL107_FIRST_CONTROL', case.name, flush=True)
    if sum(map(len, outputs.values())) != 50:
        raise ValueError('First50 originalTIME parallel controls incomplete')
    save(OUT / 'initial_controls_GPU.json', dict(outputs=outputs, actual_calls=50,
        timings=timings, actual_pipeline_seconds=time.monotonic() - started,
        model_state=state, model_role='default', no_actor_updates=True))


def first_micro(model, processor, rt, loaded, code, method, data):
    publisher = data['schedule'][0]
    sid = data['publishers'][publisher][0]
    item = data['sources'][sid]
    target = item['cases'][0]
    original = read(check(read(check(target['original_CPU']))['input']))
    case = Case(target['case'], target['original_CPU'], original, {}, {})
    source = Source(sid, [case], NativeTimeline.from_clock(read(check(item['source']['clock']))), [], {})
    torch.manual_seed(method['seed'])
    torch.cuda.manual_seed_all(method['seed'])
    trainable = attach_native_actor(model)
    state = fingerprint(model, 'actor', loaded['base'])
    if state != fingerprint(model, 'default', loaded['base']):
        raise ValueError('New query actor is not exact originalTIME before first gradient')
    count = sum(p.numel() for p in model.parameters()) + 98329 + 37184640 + 28043472 + 6209025
    if count != 8869330010 or sum(p.numel() for _, p in trainable) != 15335424:
        raise ValueError('Actual complete parallel query model budget differs')
    TEMP.mkdir()
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=method['lr'], betas=tuple(method['betas']),
                                  eps=method['epsilon'], weight_decay=0., foreach=False)
    optimizer.zero_grad(set_to_none=True)
    initial = recovery_checkpoint(TEMP / 'initial_actor_Adam.pt', model, optimizer, 0,
                                   dict(completed_micro=0, **rng()))
    data_started = time.monotonic()
    actual = values(case, target['actual_input_CPU'], processor.tokenizer, rt)
    cpu_seconds = time.monotonic() - data_started
    started = time.monotonic()
    gpu, signature, snapshot = transfer(actual, target['actual_input_CPU'], rt)
    transfer_seconds = time.monotonic() - started
    del actual
    result = first_backward(model, source, case, target, code, state, gpu, signature,
                            snapshot, item['publisher_source_weight'])
    if any(p.grad is not None for name, p in model.named_parameters()
           if '.lora_A.actor.' not in name and '.lora_B.actor.' not in name):
        raise ValueError('Parallel preference gradient reached protected parameters')
    cursor = dict(publisher=publisher, source=sid, case=case.name, completed_micro=1, optimizer_updates=0)
    before = time.monotonic()
    gradient = gradient_state(TEMP / 'first_successful_gradient.pt', trainable, cursor, initial)
    persist = time.monotonic() - before
    if fingerprint(model, 'actor', loaded['base']) != state:
        raise ValueError('First query micro changed weights before complete publisher update')
    return dict(**result, cursor=cursor, target_binding=target, initial_actor_optimizer=initial,
        exact_successful_gradient=gradient, actual_actor_state=state, actual_complete_parameters=count,
        actual_new_target_forwards=1, actual_optimizer_updates=0,
        CPU_load_seconds=cpu_seconds, actual_transfer_seconds=transfer_seconds,
        actual_gradient_persistence_seconds=persist,
        GPU_consumer_seconds_excluding_first_CPU=transfer_seconds
            + result['forward_and_backward_plus_first_CPU_seconds'] - result['one_off_CPU_seconds'] + persist)


def main():
    torch.set_num_threads(2)
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    protocol = read(check(lock['protocol']))
    inputs = read(check(lock['actual_inputs']))
    data = read(check(inputs['loss_bindings']))
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if set(model.peft_config) != {'default'} or sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Initial parallel controls must use protected originalBASE/TIME only')
    model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    model.eval()
    state = fingerprint(model, 'default', loaded['base'])
    controls(model, processor, rt, inputs, inputs['actual_query_code'], state, protocol)
    result = first_micro(model, processor, rt, loaded, inputs['actual_query_code'], protocol['training'], data)
    evaluation_mode(model)
    model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Original BASE/TIME changed during first query control/gradient job')
    save(OUT / 'GPU_completion.json', dict(state='FIRST50_PARALLEL_CONTROLS_AND_ONE_ACTUAL_GRADIENT_NEEDS_CPU',
        first_micro=result, initial_controls=identity(OUT / 'initial_controls_GPU.json'),
        actual_initial_control_calls=50, actual_new_target_forwards=1, actual_optimizer_updates=0,
        original_BASE_TIME_unchanged=True, original_loaded=loaded,
        actual_complete_parameters=8869330010, peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
