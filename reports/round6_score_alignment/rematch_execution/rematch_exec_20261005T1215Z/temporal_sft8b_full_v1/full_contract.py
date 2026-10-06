"""Stdlib-only admission and exact epoch batching for the new full B run."""
import hashlib
import json
import math
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
OLD = HERE.parent/'temporal_sft8b_v1'
sys.path.insert(0, str(OLD))
from sft_contract import (require, sha256, read_bound, verify_model_receipt,
    load_original_train, MODEL_ID, REVISION, ORIGINAL_TRAIN_SHA)
from row_contract import validate_training_rows

SCOPE = 'TEMPORAL_8B_INTERVAL_SFT_FULL_NONTEST'
REQUEST = '4b得分33.81，登记一下然后开始8B的训练'
FULL_SHA = '124801624736f960d15074ad65840d4e2850dcb7d8d5d3b16a2cb54e7eee4bc0'
REGISTRY_SHA = '71552f64ccdb125ca11a451baf5b8a22491d51d73db1a42e0ce1a545262d1cd4'
FIXED = dict(schema='aic_sft8b_full_config_v1', model_id=MODEL_ID, revision=REVISION,
    epochs=5, grad_accum=16, lr=5e-5, seed=20261006, max_sequence_length=8192,
    max_wall_seconds=36000, max_frames=64, max_pixels=131072, window_seconds=30,
    precision='bf16', attn_implementation='sdpa', lora_rank=16, lora_alpha=32,
    lora_dropout=.05, modules_to_save=None, gradient_checkpointing_use_reentrant=False,
    loss='ASSISTANT_INTERVAL_JSON_CE', optimizer='AdamW', weight_decay=0.0,
    grad_clip_norm=1.0, adamw_betas=[.9,.999], adamw_eps=1e-8,
    initialization='PINNED_BASE_NEW_LORA_NOT_SMOKE_ADAPTER', final_checkpoint_only=True,
    expected_parents=704, expected_groups=602, expected_windows=724,
    expected_effective_batches=3620, expected_optimizer_steps=227)
FIXED['source_endpoint_contract'] = 'R7_MILLISECOND_ROUNDING_ONLY_MAX_0_000500001_SEC'
BOUND_NAMES = ('model_receipt','train_manifest','r7_train_registry','temporal_common','r7_core')
EXTRA = {'model_dir','out_dir', *BOUND_NAMES}


def epoch_batches(n_rows, epochs, grad_accum, seed):
    """Every window exactly once per epoch, including the final partial batch."""
    require(all(type(v) is int and v > 0 for v in (n_rows,epochs,grad_accum,seed)),
            'invalid epoch batching specification')
    stream = []
    for epoch in range(epochs):
        order = list(range(n_rows))
        random.Random(seed+epoch).shuffle(order)
        stream.extend((epoch+1,index) for index in order)
    return [stream[i:i+grad_accum] for i in range(0,len(stream),grad_accum)]


def validate_config(config):
    require(set(config) == set(FIXED)|EXTRA, 'unknown/missing full-training recipe field')
    for key, value in FIXED.items():
        require(config[key] == value and type(config[key]) is type(value), 'full recipe changed: '+key)


def validate_authority(authority):
    require(authority.get('authorized') is True and authority.get('scope') == SCOPE and
            authority.get('route') == 'TEMPORAL_8B_INTERVAL_SFT' and
            authority.get('user_request_quote') == REQUEST and
            authority.get('authority_kind') == 'DIRECT_USER_FULL_8B_TRAINING_REQUEST_MAIN_B_PROTOCOL' and
            authority.get('full_training_admitted') is True and
            authority.get('formal_c_bce_admitted') is False and
            authority.get('authorization_inferred_from_nonresponse') is False,
            'direct full-training request/main B protocol missing; C STOP remains')


def validate_full_rows(registry, rows, original):
    sources = validate_training_rows(registry,rows,original)
    require(len(rows) == 724 and len(sources) == 704 and
            len({r['parent_sample_id'] for r in rows}) == 704 and
            len({r['youtube_id'] for r in rows}) == 602, 'full train population changed')
    registered = {w['window_id'] for parent in registry['records']
                  for w in parent['registered_windows'] if w['segments_clip_local']}
    require({row['window_id'] for row in rows} == registered, 'positive windows missing/added')
    return sources


def verify_lock(lock_path, expected):
    require(sha256(lock_path) == expected, 'new full-stage source lock changed')
    lock = json.loads(Path(lock_path).read_text())
    require(lock['scope'] == SCOPE and isinstance(lock.get('files'),dict) and lock['files'], 'invalid full lock')
    for path,digest in lock['files'].items():
        require(sha256(path) == digest, 'bound full-stage source/evidence changed: '+path)
    return lock


def admit(config_path, admission_path, lock_path, expected_lock):
    lock = verify_lock(lock_path,expected_lock)
    admission = json.loads(Path(admission_path).read_text())
    require(admission.get('scope') == SCOPE and admission.get('authorized') is True and
            admission.get('source_lock_sha256') == expected_lock and
            admission.get('config_sha256') == sha256(config_path) and
            all(admission.get(key) is True for key in
                ('resource_preflight_pass','shared_gpu_queue_approved','disk_peak_within_80gib')),
            'full B registration/source/resources missing')
    authority_path = read_bound(admission['authority'],'full training authority')
    validate_authority(json.loads(authority_path.read_text()))
    config = json.loads(Path(config_path).read_text())
    validate_config(config)
    bound = {name:read_bound(config[name],name) for name in BOUND_NAMES}
    require(config['train_manifest']['sha256'] == FULL_SHA and
            config['r7_train_registry']['sha256'] == REGISTRY_SHA, 'original full input identity changed')
    verify_model_receipt(Path(config['model_dir']), json.loads(bound['model_receipt'].read_text()))
    registry = json.loads(bound['r7_train_registry'].read_text())
    rows = [json.loads(line) for line in bound['train_manifest'].read_text().splitlines() if line.strip()]
    original = load_original_train(bound['r7_core'].parent.parent/'inputs/train_temporal.jsonl')
    sources = validate_full_rows(registry,rows,original)
    for path,digest in sources.items():
        require(sha256(path) == digest, 'current training source bytes changed: '+path)
    output = Path(config['out_dir']).resolve()
    require(HERE in output.parents and (not output.exists() or not any(output.iterdir())), 'unsafe/nonempty full output')
    batches = epoch_batches(len(rows),config['epochs'],config['grad_accum'],config['seed'])
    require(len(batches) == 227 and sum(map(len,batches)) == 3620 and len(batches[-1]) == 4,
            'exact five-epoch batch plan changed')
    return dict(config=config,admission=admission,rows=rows,sources=sources,bound=bound,
        batches=batches,lock=lock,lock_path=Path(lock_path),lock_sha256=expected_lock,
        config_sha256=sha256(config_path),admission_sha256=sha256(admission_path),
        origin_train_manifest_sha256=ORIGINAL_TRAIN_SHA)
