"""One fixed complete training trajectory then150 final development outputs."""
from pathlib import Path

import torch

from frozen_branch46 import RUN
from joint_checkpoint44 import final_save_reload
from joint_rollout47 import evaluation_mode
from native_actor98 import attach_native_actor
from native_state100 import fingerprint
from parallel_dev108 import development
from parallel_train108 import train
from t_io import ROOT, check, read, save
from t_runtime39 import runtime

OUT = ROOT / 'parallel_remaining108'
TEMP = Path('/dev/shm/aic_T_parallel_remaining108')


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
    method = protocol['training']
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    trainable = attach_native_actor(model)
    actual = sum(p.numel() for p in model.parameters()) + sum(
        protocol['components'][key] for key in ['fixed_semantic_head', 'local_Whisper_tiny', 'fixed_I3D', 'fixed_UMT'])
    if actual != protocol['expected_full_method_parameters'] or actual > 9000000000:
        raise ValueError('Actual complete parallel-model shared parameter budget differs')
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=method['lr'], betas=tuple(method['betas']),
                                  eps=method['epsilon'], weight_decay=0., foreach=False)
    TEMP.mkdir()
    training = train(model, processor, rt, loaded, optimizer, trainable, data,
                     inputs['actual_query_code'], OUT, TEMP)
    evaluation_mode(model)
    model.eval()
    del optimizer, trainable
    final = final_save_reload(model, OUT / 'final_checkpoint')
    state = fingerprint(model, 'actor', loaded['base'])
    if state != training['actor_final'] or state == training['actor_initial']:
        raise ValueError('Actual final trained query checkpoint did not survive exact FP32 reload')
    model.set_adapter('actor')
    for p in model.parameters():
        p.requires_grad_(False)
    model.eval()
    outputs = development(model, processor, rt, inputs, protocol, inputs['actual_query_code'], state, OUT)
    model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    if (rt.b_engine.frozen_identity(model, config) != loaded['base']
            or rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('OriginalBASE/TIME changed during actual query training/development')
    save(OUT / 'GPU_completion.json', dict(state='COMPLETE217_QUERY_TRAINING_AND150_FINAL_DEV_NEEDS_CPU',
        training=training, final_adapter=final, development=outputs,
        actual_new_training_forwards=216, first107_training_micro_adopted=True,
        actual_optimizer_updates=5, actual_new_development_forwards=150,
        actual_complete_parameters=actual, final_checkpoint_only=True,
        original_BASE_TIME_unchanged=True, actual_loaded=loaded,
        peak_torch_bytes=torch.cuda.max_memory_allocated(),
        quality_confirmation_or_production_admitted=False))


if __name__ == '__main__':
    main()
