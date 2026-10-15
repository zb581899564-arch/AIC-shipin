"""Independent native decode/processor/token/parser replay; no GPU or weights."""
import math
import sys
from pathlib import Path
import dense_runtime as r


def replay_one(processor,proof,done_path):
    from native_grammar import make_native_constraint
    from original_grammar import ascii_token_candidates
    done_path=Path(done_path); done=r.read(done_path); window=proof['window']
    raw_path=Path(done['raw_path']); raw=r.read(raw_path)
    r.require(done['output_valid'] is True and done['parse_errors']==[] and done['source_window']==window and
        done['raw_sha256']==r.sha(raw_path) and raw['request_window_digest']==r.digest(window) and
        raw['actual_model_call'] is True and raw['raw_output']==done['raw_output'],'actual raw/done identity differs')
    encoded,evidence=r.encode_window(processor,window)  # Fresh source decode, never cached input tensors.
    r.require(evidence==proof['input_evidence']==raw['input_evidence']==done['input_evidence'],
        'independent sequential native RGB/processor/tensor evidence differs')
    transfer=r.read(done_path.parent/'gpu_input.json')
    r.require(transfer['status']=='PASS_ACTUAL_CPU_GPU_TENSOR_EQUALITY' and
        transfer['tensor_signature']==evidence['tensor_signature'],'actual GPU tensor transfer acceptance differs')
    ids=raw['output_token_ids']; scores=raw['selected_token_scores']
    r.require(0<len(ids)<=256 and all(type(i) is int and i>=0 for i in ids) and
        len(ids)==len(scores)==raw['generated_score_count']==raw['output_tokens']==done['output_tokens'] and
        all(type(s) in (float,int) and math.isfinite(s) for s in scores),'actual token/finite score denominator differs')
    r.require(int(encoded['input_ids'].shape[1])==raw['input_tokens']==done['input_tokens'], 'independent expanded input token count differs')
    tok=processor.tokenizer
    r.require(tok.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)==raw['raw_output'],
        'actual generated token IDs do not decode to untouched raw output')
    # Pin generation EOS to the original model's saved configuration without loading weights.
    config=r.read(r.RUN/'b_score_aligned_package_v4/config.json')
    generation=r.read(Path(config['model_dir'])/'generation_config.json')
    eos=generation['eos_token_id']; eos=[eos] if isinstance(eos,int) else eos
    r.require(raw['eos_token_ids']==eos,'original generation EOS inventory differs')
    grammar=make_native_constraint(tok,raw['input_tokens'],r.F(window['window_duration']),
        window['all_source_exact_pts'],r.F(window['exact_raw_start']),candidate_token_ids=ascii_token_candidates(tok),
        eos_token_ids=eos,allow_empty=True)
    grammar.assert_complete(ids)
    _,contracts,_,_,_=r.dependencies()
    parsed,errors,warnings=contracts.parse_segments(raw['raw_output'],r.F(window['window_duration']),allow_empty=True)
    r.require(parsed is not None and not errors and parsed==done['parsed_segments'] and warnings==done['parse_warnings'] and
        done['status']==('MODEL_OK' if parsed else 'LEGAL_EMPTY'),'unchanged strict parser replay differs')
    ranges=r.native_ranges(parsed,window)
    r.require(ranges==done['native_frame_realizability']['ranges'],'full-source exact native membership differs')
    del encoded
    return dict(done_path=str(done_path),done_sha256=r.sha(done_path),raw_path=str(raw_path),raw_sha256=r.sha(raw_path),
        source_id=window['source_id'],index=window['index'],parsed_segments=parsed,native_ranges=ranges,
        actual_native_processor_raw_validator_equal=True,full_source_native_nonempty=True,
        input_tokens=raw['input_tokens'],output_tokens=len(ids),new_model_calls=0,new_optimizer_updates=0)


def pilot():
    import torch
    from dense_pilot import PREP,GPU,prepared
    acceptance,extra=prepared(); lock=r.verify_lock('pilot',extra)
    terminal=r.read(GPU/'completion.json')
    r.require(terminal['status']=='PASS_SIX_DENSE128_ENGINEERING_CALLS_NOT_QUALITY' and terminal['actual_model_calls']==6 and
        terminal['source_lock_sha256']==lock['sha256'] and terminal['cpu_acceptance_sha256']==r.sha(PREP/'acceptance.json') and
        terminal['attempts_sha256']==r.sha(GPU/'attempts.jsonl') and terminal['model_identity_sha256']==r.sha(GPU/'model_identity.json'),
        'six actual successful model calls are not complete')
    out=r.HERE/'pilot_01/replay_01'; out.mkdir(parents=True,exist_ok=False)
    try:
        processor=r.processor_cpu(); by_id={e['case_id']:e for e in acceptance['entries']}; proofs=[]
        r.require({e['case_id'] for e in terminal['entries']}==set(by_id) and len(terminal['entries'])==6,'six replay IDs differ')
        for entry in terminal['entries']:
            r.require(r.sha(entry['done_path'])==entry['done_sha256'],'accepted model done changed')
            proof=replay_one(processor,r.read(by_id[entry['case_id']]['proof_path']),entry['done_path'])
            r.save(out/(entry['case_id']+'.json'),proof); proofs.append(proof)
        r.require(not torch.cuda.is_initialized(),'independent CPU replay initialized CUDA')
        r.save(out/'completion.json',dict(status='PASS_SIX_DENSE128_INDEPENDENT_CPU_REPLAYS_NOT_QUALITY',utc=r.utc(),
            proofs=proofs,source_lock_sha256=lock['sha256'],gpu_completion_sha256=r.sha(GPU/'completion.json'),
            CPU_only=True,CUDA_initialized=False,new_model_calls=0,new_optimizer_updates=0,
            formal_quality_reference='FAILED_PRESERVED',official_score=None))
    except Exception as exc:
        r.failure(out,exc); raise


def rematch():
    import torch
    from dense_production import PREP,GPU,prepared
    acceptance,extra=prepared(); lock=r.verify_lock('rematch',extra); terminal=r.read(GPU/'completion.json')
    r.require(terminal['status']=='PASS_DENSE128_426_TEMPORAL_EXECUTION' and terminal['actual_model_calls']==521 and
        terminal['source_lock_sha256']==lock['sha256'] and terminal['cpu_acceptance_sha256']==r.sha(PREP/'acceptance.json') and
        terminal['attempts_sha256']==r.sha(GPU/'attempts.jsonl') and terminal['temporal_sha256']==r.sha(GPU/'temporal.jsonl'),
        'complete 426/521 real-call execution missing')
    out=r.HERE/'rematch_01/replay_01'; out.mkdir(parents=True,exist_ok=False)
    try:
        processor=r.processor_cpu(); proofs=[]
        r.require(len(terminal['entries'])==len(acceptance['entries'])==521,'521 independent replay denominator differs')
        accepted={e['key']:e for e in acceptance['entries']}
        for entry in terminal['entries']:
            r.require(entry['key'] in accepted and r.sha(entry['done_path'])==entry['done_sha256'],'accepted production done changed')
            proof=replay_one(processor,r.read(accepted[entry['key']]['proof_path']),entry['done_path'])
            r.save(out/(entry['key']+'.json'),proof); proofs.append(proof)
            print(__import__('json').dumps(dict(stage='DENSE128_REMATCH_CPU_REPLAY',completed=len(proofs),total=521)),flush=True)
        r.require(len({(p['source_id'],p['index']) for p in proofs})==521 and not torch.cuda.is_initialized(),
            'independent replay duplicate or CUDA initialization')
        r.save(out/'completion.json',dict(status='PASS_521_DENSE128_INDEPENDENT_CPU_REPLAYS',utc=r.utc(),proofs=proofs,
            source_lock_sha256=lock['sha256'],gpu_completion_sha256=r.sha(GPU/'completion.json'),CPU_only=True,
            CUDA_initialized=False,new_model_calls=0,new_optimizer_updates=0,official_score=None))
    except Exception as exc:
        r.failure(out,exc); raise


if __name__=='__main__':
    r.require(len(sys.argv)==2 and sys.argv[1] in ('pilot','rematch'),'usage: dense_replay.py pilot|rematch')
    {'pilot':pilot,'rematch':rematch}[sys.argv[1]]()
