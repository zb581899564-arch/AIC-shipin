"""Mac scope, pinned bytes, positive-only supervision and exact epoch coverage."""
import hashlib
import json
import math
import os
from pathlib import Path
import random

from sft_contract import (require,sha256,read_bound,verify_model_receipt,load_original_train,
                         ORIGINAL_TRAIN_SHA,MODEL_ID,REVISION)
from row_contract import validate_training_rows

HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/choubk/codex-workspace')
SCOPE='MAC_8B_64_LOWRES_INTERVAL_SFT_NONTEST'
ASSET_ROOT=Path('/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z')

def verify_lock(path,expected):
    require(sha256(path)==expected,'Mac source lock changed')
    lock=json.loads(Path(path).read_text())
    for name,digest in lock['files'].items():require(sha256(HERE/name)==digest,'Mac bound input/code changed: '+name)
    return lock

def epoch_batches(rows,epochs,accum,seed,total=None):
    stream=[];epoch=0
    while len(stream)<(total if total is not None else rows*epochs):
        order=list(range(rows));random.Random(seed+epoch).shuffle(order)
        stream.extend((epoch+1,index) for index in order);epoch+=1
    if total is not None:stream=stream[:total]
    return [stream[i:i+accum] for i in range(0,len(stream),accum)]

def verify_live_gpu_reservation():
    active=json.loads((HERE/'controller/active_training.json').read_text())
    require(active['child_pid']==os.getpid() and active['scope']==SCOPE,'Mac training reservation belongs to another process')

def admit(config_path,admission_path,lock_path,expected_lock,phase):
    require(phase in ('probe','full'),'unknown Mac phase')
    verify_lock(lock_path,expected_lock)
    require(ROOT in HERE.resolve().parents,'Mac task escaped approved workspace')
    config=json.loads(Path(config_path).read_text());admission=json.loads(Path(admission_path).read_text())
    authority=json.loads((HERE/'authorization.json').read_text())
    require(authority['authorized'] is True and authority['scope']==SCOPE and
            authority['user_request_quote']=='去修复内存问题，如果mac支撑不起128帧，那你就换个微调方向' and
            authority['formal_C_BCE_admitted'] is False,'Mac request/main independent-version authority missing')
    require(admission['scope']==SCOPE and admission['phase']==phase and admission['authorized'] is True and
            admission['source_lock_sha256']==expected_lock and admission['config_sha256']==sha256(config_path),
            'Mac phase not registered')
    require(config['max_frames']==64 and config['max_pixels']==32768 and config['max_sequence_length']==6144 and
            config['epochs']==5 and config['grad_accum']==16 and config['lr']==5e-5 and config['seed']==20261006 and
            config['model_id']==MODEL_ID and config['revision']==REVISION,'frozen 128-frame recipe changed')
    asset_path=ASSET_ROOT/'controller/asset_http_completion.json'
    if not asset_path.exists():asset_path=ASSET_ROOT/'controller/asset_completion.json'
    asset=json.loads(asset_path.read_text())
    env=json.loads((ASSET_ROOT/'controller/environment_completion.json').read_text())
    require(asset['status']=='PASS_MAC_PINNED_MODEL_AND_704_TRAIN_MEDIA_TRANSFER' and asset['all_sizes_and_sha256_match'] and
            env['status']=='PASS_TASK_SCOPED_MPS_ENVIRONMENT','Mac media/model/environment preparation incomplete')
    verify_model_receipt(ASSET_ROOT/'models/Qwen3-VL-8B-Instruct',json.loads((HERE/'model_receipt.json').read_text()))
    original=load_original_train(HERE/'original_train.jsonl')
    registry=json.loads((HERE/'r7_train_registry.json').read_text())
    full=[json.loads(line) for line in (HERE/'full_train.jsonl').read_text().splitlines() if line.strip()]
    sources=validate_training_rows(registry,full,original)
    require(len(full)==724 and len(sources)==704 and len({row['youtube_id'] for row in full})==602,'Mac full population changed')
    mapping=json.loads((HERE/'source_map.json').read_text());require(set(mapping)==set(sources),'Mac source map missing/extra')
    for original_path,digest in sources.items():
        actual=Path(mapping[original_path]);require(ROOT in actual.resolve().parents and not actual.is_symlink() and
            sha256(actual)==digest,'Mac source bytes/path changed')
    rows=full if phase=='full' else [json.loads(line) for line in (HERE/'probe_train.jsonl').read_text().splitlines() if line.strip()]
    validate_training_rows(registry,rows,original)
    batches=epoch_batches(len(rows),5,16,20261006,48 if phase=='probe' else None)
    expected_batches=48 if phase=='probe' else 3620;expected_steps=3 if phase=='probe' else 227
    require(sum(map(len,batches))==expected_batches and len(batches)==expected_steps,'Mac exposure plan changed')
    output=HERE/('probe_01' if phase=='probe' else 'full_01')
    require(not output.exists() or not any(output.iterdir()),'preserve existing Mac run; no duplicate')
    config.update(phase=phase,train_manifest=dict(sha256=sha256(HERE/('full_train.jsonl' if phase=='full' else 'probe_train.jsonl'))),
                  out_dir=str(output),model_dir=str(ASSET_ROOT/'models/Qwen3-VL-8B-Instruct'),
                  max_wall_seconds=admission['max_seconds'],expected_effective_batches=expected_batches,expected_optimizer_steps=expected_steps)
    return dict(config=config,admission=admission,rows=rows,sources={mapping[path]:digest for path,digest in sources.items()},
        bound=dict(temporal_common=HERE/'temporal_common.py'),batches=batches,lock_path=Path(lock_path),lock_sha256=expected_lock,
        source_map=mapping,config_sha256=sha256(config_path),admission_sha256=sha256(admission_path))
