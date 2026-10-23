"""Four frozen whole-source episodes; one update only after every window replay."""
import random

import numpy as np
import torch

from actor_copy41 import exact_actor_copy
from actor_roles33 import activate_actor, adapter_equal
from joint_checkpoint44 import actor_digest, final_save_reload, gradient_snapshot, recovery_checkpoint
from joint_data44 import load_sources
from joint_replay44 import ReferenceCache, backward_window
from joint_reward43 import source_counterfactuals
from joint_rollout44 import original_greedy, run_case
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'joint_train44'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def rollout(model, processor, rt, source, folder, sampling):
    folder.mkdir()
    greedy, sampled, receipts = {}, {}, {}
    model.gradient_checkpointing_disable()
    model.disable_input_require_grads()
    activate_actor(model, 'actor')
    unchanged = adapter_equal(model)
    for case in source.cases:
        gdir = folder / (case.name + '_greedy')
        if unchanged:
            g, gr = original_greedy(case, gdir)
        else:
            g, gr = run_case(model, processor, rt, case, gdir, None)
        s, sr = run_case(model, processor, rt, case, folder / (case.name + '_sample'), sampling)
        greedy[case.name], sampled[case.name] = source.selection(case, g), source.selection(case, s)
        receipts[case.name] = dict(greedy=gr, sampled=sr)
        print('JOINT44_TRAJECTORY', source.sid, case.name, s['status'], flush=True)
    return greedy, sampled, receipts


def one_episode(model, processor, rt, source, index, method, optimizer, trainable, cache):
    folder = OUT / ('episode_%02d' % index)
    folder.mkdir()
    before = actor_digest(model)
    greedy, sampled, trajectories = rollout(model, processor, rt, source, folder / 'rollout', method['sampling'])
    if actor_digest(model) != before:
        raise ValueError('Actor changed during complete-source rollout')
    reward = source_counterfactuals(sampled, greedy, source.allowed, source.reviews, len(source.reviews))
    save(folder / 'reward.json', reward)
    save(folder / 'trajectories.json', trajectories)
    signal = any(row['advantage'] != 0 for row in reward['per_window'].values())
    optimizer.zero_grad(set_to_none=True)
    replays, gradients = [], []
    if signal:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
        for case in source.cases:
            result = read(check(trajectories[case.name]['sampled']))
            replays.append(backward_window(model, case, result,
                reward['per_window'][case.name]['advantage'], .02 / len(source.cases), cache,
                folder / (case.name + '_replay')))
            gradients.append(gradient_snapshot(folder / (case.name + '_cumulative_grad.npz'), trainable))
            save(folder / (case.name + '_gradient_acceptance.json'), gradients[-1])
            print('JOINT44_BACKWARD', index, case.name, gradients[-1]['norm_float64'], flush=True)
        if actor_digest(model) != before:
            raise ValueError('Actor changed before all source gradients accumulated')
        norm = float(torch.nn.utils.clip_grad_norm_([p for _, p in trainable], method['global_gradient_clip'], error_if_nonfinite=True))
        clipped = gradient_snapshot(folder / 'clipped_gradient.npz', trainable)
        if not np.isfinite(norm) or norm == 0:
            raise ValueError('Nonzero source reward yielded no finite actor gradient')
        optimizer.step()
    else:
        norm, clipped = 0.0, None
    after = actor_digest(model)
    if signal and after == before:
        raise ValueError('Real optimizer step did not change actual actor values')
    rng = dict(python=random.getstate(), numpy=np.random.get_state(),
               torch=torch.get_rng_state(), CUDA=torch.cuda.get_rng_state_all())
    checkpoint = recovery_checkpoint(folder / 'recovery_only.pt', model, optimizer, index, rng)
    result = dict(index=index, source=source.sid, actor_before=before, actor_after=after,
        trajectories=identity(folder / 'trajectories.json'), reward=identity(folder / 'reward.json'),
        state='SOURCE_UPDATE' if signal else 'NO_SOURCE_SIGNAL', optimizer_updates=int(signal),
        replays=replays, gradients=gradients, norm_before_clip=norm, clipped_gradient=clipped,
        recovery_checkpoint=checkpoint, intermediate_checkpoint_selection=False)
    save(folder / 'completion.json', result)
    print('JOINT44_EPISODE_COMPLETE', index, source.sid, result['state'], flush=True)
    return identity(folder / 'completion.json')


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    protocol = read(check(read(OUT / 'source_input_lock.json')['protocol']))
    method = protocol['method']
    random.seed(method['seed']); np.random.seed(method['seed']); torch.manual_seed(method['seed'])
    torch.cuda.manual_seed_all(method['seed'])
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    trainable, copying = exact_actor_copy(model, config['b_adapter'])
    resident = sum(p.numel() for p in model.parameters()) + 98329
    if resident != 8797892873 or resident > 9000000000:
        raise ValueError('Actual shared BASE/twoTIME/head parameter budget differs')
    save(OUT / 'model_acceptance.json', dict(actual_complete_parameters=resident,
        actor_parameters=sum(p.numel() for _, p in trainable), exact_copy=copying, loaded=loaded))
    sources = load_sources(rt, processor.tokenizer, protocol)
    cache = ReferenceCache(OUT / 'reference_cache')
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=method['learning_rate'],
        betas=tuple(method['betas']), eps=method['epsilon'], weight_decay=method['weight_decay'], foreach=False)
    initial, episodes = actor_digest(model), []
    for index, sid in enumerate(method['episode_source_order'], 1):
        episodes.append(one_episode(model, processor, rt, sources[sid], index, method, optimizer, trainable, cache))
    final_digest = actor_digest(model)
    final = final_save_reload(model, OUT / 'final_checkpoint')
    if actor_digest(model) != final_digest:
        raise ValueError('Final trained actor digest changed on exact reload')
    model.gradient_checkpointing_disable(); model.disable_input_require_grads(); model.eval()
    model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original BASE/TIME bytes changed during actual training')
    rows = [read(check(ref)) for ref in episodes]
    signal_sources = sorted({row['source'] for row in rows if row['optimizer_updates']})
    supported = set(signal_sources) == set(protocol['training_sources']) and initial != final_digest
    save(OUT / 'gpu_completion.json', dict(state='JOINT4_TRAINING_ENGINEERING_COMPLETE' if supported else 'STOP_NO_SOURCE_MECHANISM',
        protocol=identity(ROOT / 'code/joint_policy_protocol44.json'), episodes=episodes,
        actual_optimizer_updates=sum(row['optimizer_updates'] for row in rows), signal_sources=signal_sources,
        actor_initial=initial, actor_final=final_digest, final_adapter=final,
        actual_complete_parameters=resident, original_BASE_TIME_unchanged=True,
        torch_peak_bytes=torch.cuda.max_memory_allocated(), quality_admission=False,
        frozen_final_only=True, official_score='UNKNOWN', protected40_47_unchanged=True))


if __name__ == '__main__':
    main()
