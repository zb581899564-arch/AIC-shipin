"""Resume committed source state and only missing work after an actual time limit."""
import torch

from actor_copy41 import exact_actor_copy
from joint_checkpoint44 import actor_digest
from joint_data44 import load_sources
from joint_finish50 import finish
from joint_replay44 import ReferenceCache
from resume_episode50 import episode
from resume_rng50 import kernel_contract
from resume_state50 import restore_checkpoint
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'joint_continue50'
OLD = ROOT / 'joint_remaining47'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def adopt_reference_cache(cache):
    for path in sorted((OLD / 'reference_cache').glob('*.pt')):
        payload = torch.load(path, map_location='cpu', weights_only=True)
        key = cache.key(payload['CPU'], payload['targets'], payload['allowed_tokens'])
        if path.stem != key:
            raise ValueError('Actual old frozen-reference cache key differs')
        cache.entries[key] = (payload['allowed_logits'], identity(path))


def main():
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    lock = read(OUT / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    protocol = read(check(lock['protocol']))
    completed = read(OUT / 'registration.json')['completed_episodes_adopted']
    rows = [read(check(ref)) for ref in completed]
    if not rows or [row['index'] for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError('Actual committed episode prefix missing or unordered')
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    trainable, copying = exact_actor_copy(model, config['b_adapter'])
    if sum(p.numel() for p in model.parameters()) + 98329 != 8797892873:
        raise ValueError('Actual continuation parameter budget differs')
    method = protocol['method']
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=method['learning_rate'],
        betas=tuple(method['betas']), eps=method['epsilon'], weight_decay=method['weight_decay'], foreach=False)
    proof = kernel_contract(model.get_base_model().lm_head.weight.shape[0])
    restored = restore_checkpoint(model, optimizer, rows[-1])
    save(OUT / 'restored_state.json', dict(exact_copy=copying, committed_state=restored,
        actual_CUDA_RNG_kernel=proof, old_accepted_updates_repeated=0))
    cache = ReferenceCache(OUT / 'reference_cache'); adopt_reference_cache(cache)
    remaining_sids = method['episode_source_order'][len(rows):]
    subset = dict(protocol, training_sources=sorted(set(remaining_sids)))
    sources = load_sources(rt, processor.tokenizer, subset) if remaining_sids else {}
    for index in range(len(rows) + 1, 5):
        sid = method['episode_source_order'][index - 1]
        ref = episode(model, processor, rt, sources[sid], index, method, optimizer, trainable, cache,
            OLD / ('episode_%02d' % index), OUT / ('episode_%02d' % index))
        completed.append(ref)
    finish(model, rt, config, loaded, completed, rows[0]['actor_before'], OUT)


if __name__ == '__main__':
    main()
