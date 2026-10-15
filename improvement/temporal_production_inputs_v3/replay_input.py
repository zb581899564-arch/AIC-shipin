"""First independent RGB -> ordinary processor replay, after natural GPU terminal.

This writes an INPUT-ONLY proof. It never invents output/weight verification,
accepts a consumer, releases RGB, decodes source media or calls a model.
"""
import argparse
from fractions import Fraction as F
import hashlib
import os
from pathlib import Path
import resource
import time

from consumer_api import load_consumer
import tp_io as io
from tp_contract import require


def first_input_replay(reg,consumer,resource_ref,ledger_ref):
    io.host();io.actual_permission(reg)
    loaded=load_consumer(reg,consumer);store=loaded['store'];meta=loaded['metadata']
    resource_receipt=io.read(store.checked_ref(resource_ref))
    ledger_path=store.checked_ref(ledger_ref)
    import json
    ledger=[json.loads(line) for line in ledger_path.read_text().splitlines() if line]
    require(resource_receipt['status']=='completed' and type(resource_receipt['exit_code']) is int and
        resource_receipt['exit_code']==0 and [row for row in ledger if row.get('name')==resource_receipt['name']]==[resource_receipt] and
        resource_receipt.get('validation_scope')!='PURE_SYNTHETIC_NOT_REAL_TERMINAL',
        'Input replay requires the unique actual naturally completed GPU resource/ledger')
    destination='permanent/proofs/'+consumer+'_first_input_replay.json'
    launch='permanent/proofs/'+consumer+'_first_input_replay_launch.json'
    require(not store.path(destination,'permanent').exists() and not store.path(launch,'permanent').exists(),
            'Successful or attempted first replay cannot rerun; explicit recovery required')
    proof=io.read(store.checked_ref(loaded['CPU_input_proof_ref']))
    require(proof['prepare_pid']!=os.getpid(),'Independent PID must differ from prepare PID')
    RGB_ref=proof['original_RGB_ref'];RGB_path=store.checked_ref(RGB_ref,'staging')
    require(str(RGB_path)==meta['frame_array_path'] and RGB_ref['sha256']==meta['frame_array_sha256'],
            'Still-present original RGB differs from canonical manifest')
    # Launch binds code, PID and terminal before the one new independent encode.
    code_sha=io.sha(__file__)
    require(reg['required_code_files'].get(str(Path(__file__).resolve()))==code_sha,'Replay code is not frozen')
    store.write_metadata(launch,dict(consumer=consumer,verifier_pid=os.getpid(),prepare_pid=proof['prepare_pid'],
        verifier_code_sha256=code_sha,resource_ref=resource_ref,ledger_ref=ledger_ref,original_RGB_ref=RGB_ref,
        new_model_calls=0,first_independent_input_replay=True))
    started=time.monotonic()
    try:
        import numpy as np
        with np.load(RGB_path,allow_pickle=False) as archive:arrays=archive['rgb']
        require(arrays.dtype==np.uint8 and arrays.shape==(64,meta['height'],meta['width'],3) and
            [hashlib.sha256(frame.tobytes()).hexdigest() for frame in arrays]==meta['pixel_sha256'],
            'Original RGB dtype/shape/frame-byte evidence changed')
        lib=io.libraries(reg,cpu=True)
        require(lib['runtime_identity']==proof['processor_runtime_identity'],'Original processor/runtime assets changed')
        encoded,evidence=lib['runtime'].encode(lib['processor'],meta,
            (arrays,meta['source_frame_ordinals'],meta['sample_exact_pts']),F(meta['window_start']),meta['prompt'])
        actual=lib['cache'].signature(dict(encoded))
        require(actual==loaded['manifest']['full_signature'] and lib['cache'].exact_equal(dict(encoded),loaded['encoded']),
                'Independent normal processor differs in complete bytes/dtypes/strides/aliases/tokens/grid')
        require(evidence==proof['input_evidence'],'Independent runtime input/token/native evidence differs')
        result=dict(status='PASS_FIRST_INDEPENDENT_INPUT_REPLAY_ONLY_NOT_LEASE_ACCEPTANCE',consumer=consumer,
            prepare_pid=proof['prepare_pid'],verifier_pid=os.getpid(),verifier_code_sha256=code_sha,CPU_only=True,
            first_independent_input_replay=True,normal_processor_from_original_RGB_verified=True,
            input_manifest_ref=loaded['input_manifest_ref'],CPU_input_proof_ref=loaded['CPU_input_proof_ref'],
            full_input_signature=actual,input_evidence=evidence,original_RGB_ref=RGB_ref,
            resource_ref=resource_ref,ledger_ref=ledger_ref,gpu_job_name=resource_receipt['name'],
            output_token_decode_grammar_parser_native_verified=False,actual_weight_identity_verified=False,
            consumer_accepted=False,RGB_released=False,new_model_calls=0,new_source_decodes=0,
            actual_first_independent_processor_encodes=1,wall_seconds=time.monotonic()-started,
            process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return store.write_metadata(destination,result)
    except BaseException as error:
        store.write_metadata('permanent/proofs/'+consumer+'_first_input_replay_failure.json',dict(
            status='FAILED_FIRST_INPUT_REPLAY_RETAIN_ALL',consumer=consumer,error_type=type(error).__name__,
            error=str(error),new_model_calls=0,no_RGB_or_canonical_deleted=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True,type=Path)
    parser.add_argument('--consumer',required=True);parser.add_argument('--resource-ref',required=True,type=Path)
    parser.add_argument('--ledger-ref',required=True,type=Path);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';io.host();reg=io.registration(args.registration)
    first_input_replay(reg,args.consumer,io.read(args.resource_ref),io.read(args.ledger_ref))
