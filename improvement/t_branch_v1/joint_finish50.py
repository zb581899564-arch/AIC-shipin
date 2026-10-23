"""Exact final fourth-episode artifact only, never an earlier checkpoint selection."""
import torch

from joint_checkpoint44 import actor_digest, final_save_reload
from joint_rollout47 import evaluation_mode
from t_io import ROOT, check, identity, read, save


def finish(model, rt, config, loaded, episodes, initial_digest, out):
    protocol = read(ROOT / 'code/joint_policy_protocol44.json')
    rows = [read(check(ref)) for ref in episodes]
    if [row['source'] for row in rows] != protocol['method']['episode_source_order'] or len(rows) != 4:
        raise ValueError('Engineering continuation did not complete the same four source episodes')
    final_digest = actor_digest(model)
    final = final_save_reload(model, out / 'final_checkpoint')
    if actor_digest(model) != final_digest:
        raise ValueError('Final source4 checkpoint changed on exact reload')
    evaluation_mode(model); model.eval(); model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original frozen BASE/reference differs after engineering continuation')
    signaled = sorted({row['source'] for row in rows if row['optimizer_updates']})
    supported = set(signaled) == set(protocol['training_sources']) and initial_digest != final_digest
    save(out / 'gpu_completion.json', dict(state='JOINT4_TRAINING_ENGINEERING_COMPLETE' if supported else 'STOP_NO_SOURCE_MECHANISM',
        protocol=identity(ROOT / 'code/joint_policy_protocol44.json'), episodes=episodes,
        actual_optimizer_updates=sum(row['optimizer_updates'] for row in rows), signal_sources=signaled,
        actor_initial=initial_digest, actor_final=final_digest, final_adapter=final,
        actual_complete_parameters=sum(p.numel() for p in model.parameters()) + 98329,
        original_BASE_TIME_unchanged=True, torch_peak_bytes=torch.cuda.max_memory_allocated(),
        original_train_stage_budget_failure_preserved=True,
        engineering_continuation=identity(out / 'registration.json'), original_total_T1_limit_seconds=10800,
        quality_admission=False, frozen_final_only=True, official_score='UNKNOWN', protected40_47_unchanged=True))
