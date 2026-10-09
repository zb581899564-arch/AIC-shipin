"""One native-nearest-alignment input, original B0 prompt/greedy/validator/model."""
import argparse,time
import bw_common as c
from bw_native import decode_balanced_window,exact_ranges

def encode_balanced(processor,window,rt,student,ex):
    import torch
    from exact_pts import exact_native_pts,verify_native_encoding
    from bw_video import encode,identity
    decoded=decode_balanced_window(window);arr,metadata,plan,evidence=decoded
    with exact_native_pts(processor,plan,metadata['fps']) as native:
        encoded=encode(processor,text=[rt.prompt(processor,ex.base_texts(None)['B0'])],
            videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[metadata],video_size=student.VIDEO_SIZE,max_input=16384)
        verify_native_encoding(processor,encoded,native)
    return encoded,dict(**evidence,native_processor_identity=native,**identity(processor,encoded,len(arr)),
        registered_prompt_sha256=ex.cc.digest(ex.base_texts(None)['B0']))

def replay(path,job,ix,ex,rt,student,processor):
    v=c.checked(path,job,ix,'BW',ex);w=job['windows'][ix]['window'];encoded,evidence=encode_balanced(processor,w,rt,student,ex)
    c.require(exact_ranges(v['parsed_segments'],w)==v['native_frame_realizability']['ranges'],'exact rational replay differs')
    c.require(ex.video_signature(encoded)==v['vision_tensor_signature'] and evidence==v['video_identity'],'new independent native/processor identity')
    raw=c.read(v['raw_receipt']);tok=processor.tokenizer
    c.require(tok.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)==raw['raw_output'],'actual output token decoding')
    from constrained_json import make_prefix_constraint,ascii_token_candidates
    import torch
    make_prefix_constraint(tok,0,__import__('fractions').Fraction(w['exact_raw_end'])-__import__('fractions').Fraction(w['exact_raw_start']),candidate_token_ids=ascii_token_candidates(tok),eos_token_ids=tok.eos_token_id,allow_empty=True).assert_complete(torch.tensor(raw['output_token_ids']))
    c.require(int(encoded['input_ids'].shape[1])==v['input_tokens'],'actual CPU token count')
    return dict(path=str(path),done_sha256=c.sha(path),input_tokens=v['input_tokens'],actual_native_processor_raw_validator_equal=True,new_model_calls=0,new_optimizer_updates=0)

def run(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
    student,old,model,processor,candidates,unused,identity=ex.loaded_model()
    c.require(identity==c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'actual original B model differs')
    admitted={(p['scope'],p['video_id'],p['index']):p for p in c.read(c.HERE/'cpu_acceptance.json')['proofs']}
    out=c.HERE/(scope+'_01');c.save(out/'model.json',identity);fresh=reused=recovered=0;recovery={r['path']:r for r in c.read(c.HERE/'engineering_handoff.json')['recovered_successes']};began=time.monotonic()
    for num,job in enumerate(jobs,1):
        for ix,part in enumerate(job['windows']):
            path=c.done_path(scope,job,ix,'BW',cc)
            if part['window']==part['base_window']:
                c.checked(path,job,ix,'BW',ex);reused+=1;continue
            if str(path) in recovery:
                c.require(path.exists() and c.sha(path)==recovery[str(path)]['sha256'],'recovered exact success changed')
                c.checked(path,job,ix,'BW',ex);recovered+=1;continue
            c.require(not path.exists(),'success must not be generated twice')
            w=part['window'];encoded,evidence=encode_balanced(processor,w,rt,student,ex)
            proof=admitted[(scope,job['video_id'],ix)]
            c.require(proof['window']==w and proof['video_identity']==evidence and proof['vision_signature']==ex.video_signature(encoded),'actual GPU request differs from accepted native CPU input')
            from bw_attempt import attempt
            value=attempt(model,processor,encoded,evidence,w,path.parent/'raw.json',allow_empty=True,local_candidates=candidates)
            c.require(exact_ranges(value['parsed_segments'],w)==value['native_frame_realizability']['ranges'],'exact vs pinned float realizability differs')
            value.update(request_sha256=cc.digest(c.local_request(job,ix,'BW',identity,ex)),bound_files={value['raw_receipt']:c.sha(value['raw_receipt'])},
                arm='BW',window=w,model_identity=identity,context_audit={},vision_tensor_signature=ex.video_signature(encoded))
            c.save(path,value);fresh+=1;del encoded
            if not (c.HERE/'first_real_acceptance.json').exists():
                import subprocess,os
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
                with (c.HERE/'first_replay.cpu.log').open('x') as log:
                    result=subprocess.run([c.PY,'-B',str(c.HERE/'bw_first_replay.py'),scope,job['video_id'],str(ix)],
                        cwd=c.RUN,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                c.require(result.returncode==0 and c.read(c.HERE/'first_real_acceptance.json')['separate_CPU_process'],'independent first CPU replay failed')
        c.state('RUNNING_'+scope.upper()+'_BALANCED_TWO_WINDOW',records_completed=num,total_records=len(jobs),fresh_model_calls=fresh,
            reused_exact_original_calls=reused,recovered_exact_prior_model_calls=recovered,new_overview_calls=0,wall_seconds=time.monotonic()-began)
    total={'nontest':8,'developer':112,'rematch':521}[scope]
    c.require(fresh+reused+recovered==total and fresh+recovered==sum(p['window']!=p['base_window'] for j in jobs for p in j['windows']),'actual fresh+exact reused denominator')
    c.save(out/(scope+'.completion.json'),dict(status='PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS',utc=c.utc(),records=len(jobs),fresh_model_calls=fresh,
        model_identity=identity,reused_exact_original_calls=reused,recovered_exact_prior_model_calls=recovered,total_windows=total,new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0))


if __name__=='__main__':
    import sys
    run(sys.argv[1])
