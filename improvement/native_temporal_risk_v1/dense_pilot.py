"""Prepare six dense128 CPU inputs, or run exactly six prospective B calls."""
import sys
from pathlib import Path
import dense_runtime as r

PREP = r.HERE/'pilot_01/prepare_01'
GPU = r.HERE/'pilot_01/gpu_01'


def prepare():
    import numpy as np
    import torch
    r.registration('pilot')
    PREP.mkdir(parents=True,exist_ok=False)
    try:
        processor=r.processor_cpu(); windows=r.dev_windows(); entries=[]
        for window in windows:
            case=window['source_id']; folder=PREP/case; folder.mkdir()
            r.save(folder/'request.json',window)
            decoded=r.decode_window(window)
            encoded,evidence=r.encode_window(processor,window,decoded)
            cache=folder/'native_rgb.npz'
            with cache.open('xb') as stream:
                np.savez_compressed(stream,rgb=decoded[0])
            proof=dict(case_id=case,window=window,input_evidence=evidence,
                native_rgb_cache=str(cache),native_rgb_cache_sha256=r.sha(cache),native_rgb_cache_bytes=cache.stat().st_size,
                processor_weights_loaded=False,CUDA_initialized=False,new_model_calls=0)
            r.save(folder/'proof.json',proof)
            entries.append(dict(case_id=case,request_path=str(folder/'request.json'),request_sha256=r.sha(folder/'request.json'),
                proof_path=str(folder/'proof.json'),proof_sha256=r.sha(folder/'proof.json'),
                native_rgb_cache=str(cache),native_rgb_cache_sha256=r.sha(cache)))
            del encoded,decoded
            print(__import__('json').dumps(dict(stage='DENSE128_PILOT_CPU',case_id=case,input_tokens=evidence['input_tokens'],
                physical_frames=evidence['physical_frames'],actual_pixels_per_frame=evidence['actual_pixels_per_frame'])),flush=True)
        r.require(not torch.cuda.is_initialized(),'CPU preparation unexpectedly initialized CUDA')
        r.save(PREP/'acceptance.json',dict(status='PASS_SIX_DENSE128_REAL_NATIVE_CPU_INPUTS',utc=r.utc(),
            recipe=r.RECIPE,entries=entries,sources=6,frames=sum(len(w['source_frame_ordinals']) for w in windows),
            new_model_calls=0,new_optimizer_updates=0,CPU_only=True,CUDA_initialized=False,
            labels_read=False,formal_quality_reference='FAILED_PRESERVED',production_admitted=False,
            estimated_new_output_bytes=536870912,rematch_rgb_cache=False))
    except Exception as exc:
        r.failure(PREP,exc); raise


def prepared():
    path=PREP/'acceptance.json'; value=r.read(path)
    r.require(value['status']=='PASS_SIX_DENSE128_REAL_NATIVE_CPU_INPUTS' and value['sources']==6 and
        value['new_model_calls']==0 and value['CUDA_initialized'] is False and len(value['entries'])==6,
        'six actual CPU inputs are not accepted')
    current={w['source_id']:w for w in r.dev_windows()}; extra=[path]
    for entry in value['entries']:
        q,p=Path(entry['request_path']),Path(entry['proof_path'])
        r.require(r.sha(q)==entry['request_sha256'] and r.sha(p)==entry['proof_sha256'] and
            r.sha(entry['native_rgb_cache'])==entry['native_rgb_cache_sha256'],'accepted dense128 preparation bytes differ')
        proof=r.read(p)
        r.require(proof['window']==r.read(q)==current[entry['case_id']],'six-source prospective window differs')
        extra += [q,p,Path(entry['native_rgb_cache']),Path(proof['window']['source_metadata_path']),Path(proof['window']['source_path'])]
    r.require({e['case_id'] for e in value['entries']}==set(current),'six-source IDs differ')
    return value,extra


def run():
    # All source/proof bytes must be frozen before the model is loaded.
    acceptance,extra=prepared(); lock=r.verify_lock('pilot',extra)
    GPU.mkdir(parents=True,exist_ok=False); attempts=GPU/'attempts.jsonl'
    try:
        with attempts.open('x',encoding='utf-8'): pass
        model,processor,identity,config=r.loaded_model()
        r.save(GPU/'model_identity.json',dict(identity=identity,selected_time_adapter_enabled=True,new_optimizer_updates=0))
        from original_grammar import ascii_token_candidates
        candidates=ascii_token_candidates(processor.tokenizer); entries=[]
        for entry in acceptance['entries']:
            proof=r.read(entry['proof_path']); window=proof['window']; folder=GPU/entry['case_id']; folder.mkdir()
            encoded,evidence=r.encode_window(processor,window)
            r.require(evidence==proof['input_evidence'],'actual dense128 GPU request differs from accepted CPU proof')
            done=r.generate(model,processor,encoded,evidence,window,folder,attempts,6,candidates)
            entries.append(dict(case_id=entry['case_id'],done_path=str(folder/'done.json'),done_sha256=r.sha(folder/'done.json'),
                parsed_segments=done['parsed_segments'],native_ranges=done['native_frame_realizability']['ranges']))
            del encoded
            print(__import__('json').dumps(dict(stage='DENSE128_PILOT_REAL_CALL_ACCEPTED',case_id=entry['case_id'],
                calls=len(entries),segments=done['parsed_segments'])),flush=True)
        engine,_,_,_,_=r.dependencies()
        r.require(engine.frozen_identity(model,config)==identity['base'] and engine.adapter_identity(model,config)==identity['adapter'],
            'original frozen B weights changed during prospective inference')
        events=r.rows(attempts)
        r.require(sum(e['event']=='BEGIN_MODEL_CALL' for e in events)==sum(e['event']=='ACCEPTED_MODEL_CALL' for e in events)==6,
            'six actual-call terminal denominator differs')
        r.save(GPU/'completion.json',dict(status='PASS_SIX_DENSE128_ENGINEERING_CALLS_NOT_QUALITY',utc=r.utc(),
            entries=entries,actual_model_calls=6,new_optimizer_updates=0,source_lock_sha256=lock['sha256'],
            cpu_acceptance_sha256=r.sha(PREP/'acceptance.json'),attempts_sha256=r.sha(attempts),
            model_identity_sha256=r.sha(GPU/'model_identity.json'),reference_labels_read=False,
            formal_quality_reference='FAILED_PRESERVED',official_score=None,production_admitted=False))
    except Exception as exc:
        r.failure(GPU,exc,attempts); raise


if __name__=='__main__':
    r.require(len(sys.argv)==2 and sys.argv[1] in ('prepare','run'),'usage: dense_pilot.py prepare|run')
    {'prepare':prepare,'run':run}[sys.argv[1]]()
