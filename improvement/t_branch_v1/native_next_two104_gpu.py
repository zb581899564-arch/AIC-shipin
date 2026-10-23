"""Only fixed remaining micros2/3, adopting exact first successful gradient."""
from pathlib import Path
import time

import torch

from actor_roles33 import activate_actor
from frozen_branch46 import RUN
from joint_data44 import Case, Source
from joint_rollout47 import evaluation_mode
from native_actor98 import attach_native_actor
from native_generate104 import generate
from native_prepared103 import Prefetch, prepare, transfer
from native_recovery102 import restore_first
from native_sets import NativeTimeline
from native_state100 import fingerprint
from native_teacher104 import backward
from summary_recovery88 import gradient_state
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_next_two104'
TEMP = Path('/dev/shm/aic_T_native_next_two104')


def next_cases(data, first):
    publisher = data['schedule'][0]
    sid = data['publishers'][publisher][0]
    source = data['sources'][sid]
    if source['cases'][0] != first['target_binding'] or len(source['cases']) < 3:
        raise ValueError('Registered exact remaining cases2/3 are unavailable')
    timeline = NativeTimeline.from_clock(read(check(source['source']['clock'])))
    items = []
    for number, task in enumerate(source['cases'][1:3], 2):
        original = read(check(read(check(task['original_CPU']))['input']))
        case = Case(task['case'], task['original_CPU'], original, {}, {})
        items.append((number, task, case))
    return publisher, sid, source, Source(sid, [], timeline, [], {}), items


def main():
    torch.set_num_threads(2)
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    first = read(check(lock['first_micro']))
    data = read(check(lock['loss_bindings']))
    method = read(check(lock['protocol']))['training']
    code = read(ROOT / 'native_action_contract98/completion.json')['actual_token_codec']
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    trainable = attach_native_actor(model)
    count = sum(p.numel() for p in model.parameters()) + 98329 + 37184640 + 28043472 + 6209025
    if count != 8869330010:
        raise ValueError('Actual prepared native full parameter count differs')
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=method['lr'],
        betas=tuple(method['betas']), eps=method['epsilon'], weight_decay=0., foreach=False)
    checkpoint = restore_first(model, optimizer, trainable, first, loaded['base'])
    state = first['actual_actor_state']
    publisher, sid, item, source, cases = next_cases(data, first)
    TEMP.mkdir()
    rows = []
    (OUT / 'micro').mkdir()

    def loader(entry):
        started = time.monotonic()
        prepared = prepare(entry[2], entry[1]['actual_input_CPU'], processor.tokenizer, rt)
        return prepared, time.monotonic() - started

    with Prefetch(cases, loader) as prepared:
        for entry, (actual, load_seconds) in prepared:
            number, task, case = entry
            folder = OUT / 'micro' / ('M%03d' % number)
            folder.mkdir()
            started = time.monotonic()
            transfer_started = time.monotonic()
            gpu, signature, snapshot = transfer(actual, task['actual_input_CPU'], rt)
            transfer_seconds = time.monotonic() - transfer_started
            del actual
            evaluation_mode(model)
            activate_actor(model, 'actor')
            greedy, greedy_seconds = generate(model, processor.tokenizer, source, case,
                task['actual_input_CPU'], code, state, gpu, signature, snapshot, folder / 'greedy')
            teacher = backward(model, rt, task, greedy, item['publisher_source_weight'],
                                code, state, gpu, snapshot)
            if any(p.grad is not None for name, p in model.named_parameters()
                   if '.lora_A.actor.' not in name and '.lora_B.actor.' not in name):
                raise ValueError('Prepared native gradient reached a protected parameter')
            cursor = dict(publisher=publisher, source=sid, case=case.name,
                          completed_micro=number, optimizer_updates=0)
            gradient_started = time.monotonic()
            gradient = gradient_state(TEMP / ('micro%03d.pt' % number), trainable, cursor, checkpoint)
            persist_seconds = time.monotonic() - gradient_started
            save(folder / 'acceptance.json', dict(cursor=cursor, actual_teacher=teacher,
                actual_greedy=greedy, exact_recovery_gradient=gradient,
                bounded_CPU_load_seconds=load_seconds, actual_transfer_seconds=transfer_seconds,
                actual_greedy_seconds=greedy_seconds, actual_gradient_persistence_seconds=persist_seconds,
                actual_shared_GPU_micro_seconds=time.monotonic() - started,
                successful_first_micro101_adopted_without_repetition=True))
            rows.append(identity(folder / 'acceptance.json'))
            del gpu
            print('NATIVE104_REMAINING_MICRO', number, case.name, flush=True)
    if fingerprint(model, 'actor', loaded['base']) != state:
        raise ValueError('No complete publisher update allowed in remaining-micro cost probe')
    evaluation_mode(model)
    model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Protected BASE/TIME changed during exact input reuse')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_REMAINING_TWO_NATIVE_MICRO_COMPLETE_NEEDS_CPU_COST',
        adopted_first_micro=lock['first_micro'], actual_new_greedy=2, actual_new_teacher_backwards=2,
        actual_optimizer_updates=0, all_successful_training_micros_now=3,
        actual_complete_parameters=count, actual_model_state=state, micro=rows,
        final_exact_gradient=read(check(rows[-1]))['exact_recovery_gradient'],
        initial_actor_optimizer=checkpoint, original_BASE_TIME_unchanged=True,
        no_confirmation_or_production_admission=True, peak_torch_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
