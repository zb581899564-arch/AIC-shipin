"""Three first greedy views per dev window, original-correct adopted; shared BASE."""
import torch

from frozen_branch46 import RUN, final_actor
from development_call46 import generate
from development_data46 import ARMS, development_sources, shifted
from joint_checkpoint44 import actor_digest
from joint_rollout44 import original_greedy
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'development48'


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    final_actor(model, ROOT / 'joint_remaining47/completion.json')
    before = actor_digest(model)
    if sum(p.numel() for p in model.parameters()) + 98329 != 8797892873:
        raise ValueError('Integrated final twoTIME and head parameter total differs')
    sources = development_sources(rt, processor.tokenizer, read(ROOT / 'code/joint_policy_protocol44.json'))
    accepted = read(OUT / 'coarse_CPU_completion.json')['shifted_inputs']
    folder = OUT / 'coarse'; folder.mkdir()
    records = {}
    for sid, source in sources.items():
        records[sid] = {arm: {} for arm in ARMS}
        for arm in ARMS:
            target = folder / (sid + '_' + arm); target.mkdir()
            for case in source.cases:
                if arm == 'original_correct':
                    _, ref = original_greedy(case, target / case.name)
                else:
                    chosen = shifted(case) if arm.endswith('_shift') else case
                    proof = accepted[case.name] if arm.endswith('_shift') else case.CPU
                    if arm.endswith('_shift') and rt.tensor_signature(chosen.values) != read(check(proof))['tensor_signature']:
                        raise ValueError('Actual shifted tensor differs from first independent CPU proof')
                    _, ref = generate(model, processor, rt, chosen, target / case.name,
                        'default' if arm.startswith('original_') else 'actor', proof)
                records[sid][arm][case.name] = ref
                print('DEV48_COARSE', sid, arm, case.name, flush=True)
    save(OUT / 'coarse_GPU_completion.json', dict(state='PASS_FIRST150_GREEDY_AND50_ADOPTED', outputs=records,
        first_generations=150, adopted_original_generations=50, labels_read=False))
    # Exact unadapted BASE semantic image/query forward recipe. Native inputs
    # are shared across arms; only downstream occupancy transform is repeated.
    import baseline_bridge57_gpu as frozen
    semantic = {}
    model.set_adapter('default')
    for ref in read(ROOT / 'development_semantic46/completion.json')['sources']:
        cpu = read(check(ref)); sid = cpu['source']['sid']
        frozen.ROOT = ROOT / 'development_semantic46' / sid
        frozen.semantic(model)
        semantic[sid] = identity(frozen.ROOT / 'semantic_GPU_completion.json')
    for p in model.parameters():
        p.requires_grad_(False)
    model.set_adapter('default')
    for p in model.parameters():
        p.requires_grad_(False)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter'] or actor_digest(model) != before:
        raise ValueError('Frozen original or final trained values changed during development')
    save(OUT / 'coarse_and_BASE_GPU_completion.json', dict(state='PASS_ALL_FIRST_DEV_GREEDY_AND_BASE_FEATURES',
        coarse=identity(OUT / 'coarse_GPU_completion.json'), semantic=semantic,
        actual_complete_parameters=8797892873, final_actor_frozen=True,
        torch_peak_bytes=torch.cuda.max_memory_allocated(), no_quality_claim=True))


if __name__ == '__main__':
    main()
