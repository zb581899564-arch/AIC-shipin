"""Fixed10 publisher updates on selected content, no original temporal adapter training."""
from pathlib import Path

import torch

from frozen_branch46 import RUN
from summary_actor88 import add_fresh_summary, digest, final_save_reload
from summary_data88 import load_inputs
from summary_recovery88 import publisher_checkpoint
from summary_step88 import one_publisher, TEMP
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_train88'


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    protocol = read(check(lock['protocol'])); method = protocol['summary_training']
    torch.manual_seed(method['seed']); torch.cuda.manual_seed_all(method['seed'])
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    if sum(p.numel() for p in model.parameters()) != 8782459120:
        raise ValueError('Actual original BASE/TIME count differs before adding any new adapter')
    for p in model.parameters():
        p.requires_grad_(False)
    torch.manual_seed(method['seed']); torch.cuda.manual_seed_all(method['seed'])
    trainable = add_fresh_summary(model, method)
    actual = sum(p.numel() for p in model.parameters()) + 98329 + 37184640 + 28043472 + 6209025
    if actual != 8869330010 or actual > 9000000000:
        raise ValueError('Actual complete all-model/two-adapter parameter budget differs')
    data, publishers, prefixes, schedule = load_inputs(rt)
    save(OUT / 'model_acceptance.json', dict(actual_complete_pipeline_parameters=actual,
        actual_new_adapter_parameters=sum(p.numel() for _, p in trainable), new_tensor_count=len(trainable),
        original_loaded=loaded, publisher_schedule=schedule, zero_B_initialization_checked=True,
        training_scope='Only fresh summary language adapter; BASE/TIME/vision frozen'))
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=method['learning_rate'],
        betas=tuple(method['betas']), eps=method['epsilon'], weight_decay=method['weight_decay'], foreach=False)
    TEMP.mkdir(); (OUT / 'micro').mkdir(); (OUT / 'publisher').mkdir()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads(); model.train()
    initial = digest(model)
    checkpoint = publisher_checkpoint(TEMP / 'initial.pt', model, optimizer, 0, dict(completed_micro=0))
    micro = 0; updates = []
    for episode, publisher in enumerate(schedule, 1):
        result, checkpoint, micro = one_publisher(model, rt, data, prefixes, publishers[publisher],
            publisher, episode, micro, optimizer, trainable, checkpoint)
        updates.append(result)
    if len(updates) != 10 or micro != 172 or initial == digest(model):
        raise ValueError('Actual fixed10 updates/172 complete original reviews not reached')
    final_digest = digest(model)
    model.gradient_checkpointing_disable(); model.disable_input_require_grads(); model.eval()
    final = final_save_reload(model, OUT / 'final_checkpoint')
    if digest(model) != final_digest:
        raise ValueError('Final summary digest changed on lossless save/reload')
    model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Protected BASE/TIME bytes changed during content-only training')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_FIXED10_CONTENT_UPDATES_ENGINEERING_PASS_NOT_TIME_QUALITY',
        actual_optimizer_updates=10, actual_target_forwards=172, first_full_vocab_TF_CPU=identity(OUT / 'first_TF_independent_CPU.json'),
        actual_original_reviewers_per_epoch=86, publisher_updates=updates,
        actor_initial=initial, actor_final=final_digest, final_adapter=final,
        exact_final_reload=True, actual_complete_pipeline_parameters=actual,
        protected_original_BASE_TIME_unchanged=True, final_only=True,
        recovery_checkpoints_retained_in_tmpfs=True, peak_torch_bytes=torch.cuda.max_memory_allocated(),
        no_development_confirmation_or_package_admission=True))


if __name__ == '__main__':
    main()
