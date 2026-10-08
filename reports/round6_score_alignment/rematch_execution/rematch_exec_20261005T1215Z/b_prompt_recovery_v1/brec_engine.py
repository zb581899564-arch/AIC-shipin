"""Missing historical B1 calls only; immutable raw then original validator."""
import argparse
import time
import brec_common as c

def replay(path,job,ix,ex,rt,student,processor):
    v=c.checked(path,job,ix,'B1',ex);w=job['windows'][ix]['window']
    decoded=student.decode_window(w)
    encoded,evidence=rt.encode_decoded(processor,decoded,ex.base_texts(None)['B1'])
    c.require(ex.video_signature(encoded)==v['vision_tensor_signature'] and evidence==v['video_identity'],'independent new B1 decoder/processor identity')
    raw=c.read(v['raw_receipt']);tok=processor.tokenizer
    c.require(tok.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)==raw['raw_output'],'actual raw token decoding changed')
    from constrained_json import make_prefix_constraint,ascii_token_candidates
    import torch
    make_prefix_constraint(tok,0,w['window_duration_sec'],candidate_token_ids=ascii_token_candidates(tok),
        eos_token_ids=tok.eos_token_id,allow_empty=False).assert_complete(torch.tensor(raw['output_token_ids']))
    c.require(int(encoded['input_ids'].shape[1])==v['input_tokens'],'actual replay input token count')
    return {'path':str(path),'done_sha256':c.sha(path),'input_tokens':v['input_tokens'],
        'native_decoder_processor_actual_prefix_raw_validator_equal':True,'new_model_calls':0,'new_optimizer_updates':0}

def run(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'))
    jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
    student,old,model,processor,candidates,unused,identity=ex.loaded_model()
    c.require(identity==c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'new live original B identity differs')
    out=c.HERE/(scope+'_01');c.save(out/'model.json',identity)
    fresh=reused=0;began=time.monotonic()
    for num,job in enumerate(jobs,1):
        for ix,part in enumerate(job['windows']):
            path=c.done_path(scope,job,ix,'B1',cc)
            if path.exists():
                c.checked(path,job,ix,'B1',ex);reused+=1;continue
            w=part['window'];decoded=student.decode_window(w)
            encoded,evidence=rt.encode_decoded(processor,decoded,ex.base_texts(old)['B1']);sig=ex.video_signature(encoded)
            if scope=='developer':
                base=c.checked(c.done_path(scope,job,ix,'B0',cc),job,ix,'B0',ex)
                c.require(sig==base['vision_tensor_signature'] and evidence['frame_pixel_sha256']==base['video_identity']['frame_pixel_sha256'],'new B1 visual input differs from exact B0')
            raw=path.parent/'raw.json'
            value=rt.attempt(model,processor,encoded,evidence,w,raw,allow_empty=False,local_candidates=candidates)
            value.update(request_sha256=cc.digest(c.local_request(job,ix,'B1',identity,ex)),
                bound_files={str(raw):c.sha(raw)},arm='B1',window=w,model_identity=identity,
                context_audit={},vision_tensor_signature=sig)
            c.save(path,value);fresh+=1;del encoded,decoded
            if scope=='developer' and fresh==1:
                proof=replay(path,job,ix,ex,rt,student,processor)
                c.save(c.HERE/'first_real_acceptance.json',dict(proof,status='PASS_REAL_FIRST_MISSING_B1_AND_INDEPENDENT_CPU_REPLAY',utc=c.utc()))
        c.state('RUNNING_'+scope.upper()+'_B1',records_completed=num,total_records=len(jobs),
            fresh_B1_calls=fresh,reused_B1_calls=reused,wall_seconds=time.monotonic()-began)
    expected=(86,26) if scope=='developer' else (521,0)
    c.require((fresh,reused)==expected,'actual fresh/reuse B1 denominator')
    c.save(out/(scope+'.completion.json'),{'status':'PASS_ALL_REGISTERED_HISTORICAL_B1_ATTEMPTS',
        'utc':c.utc(),'records':len(jobs),'fresh_B1_calls':fresh,'reused_B1_calls':reused,
        'model_identity':identity,'new_optimizer_updates':0,'new_32B_calls':0})

def plan_rematch():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    c.require(c.read(c.HERE/'developer_01/report.json')['status']=='GO_ONE_HISTORICAL_B1_RISK_PACKAGE','production not admitted')
    ref,manifest,clocks=old.inputs('rematch')
    from fractions import Fraction
    source_clock=rt.load(c.CAD/'prepare.py','brec_original_native_scan').source_clock
    jobs=[];sources={}
    for n,item in enumerate(manifest['records'],1):
        clock=clocks[item['video_id']];a=clock['arrays'];tick=Fraction(a['raw_time_base'])
        points=[float(x*tick) for x in a['native_pts_ticks']]
        physical=source_clock(item,manifest['allowed_source_roots'])
        c.require(physical['pts']==points,'rematch registered native clock changed')
        key=item['source_sha256'];sources[key]=physical;windows=[]
        for j,(start,end) in enumerate(frames.window_schedule(item,manifest['kind'],clock)):
            raw_start,raw_end=production.raw_window_bounds(a,start,end)
            w=student.window_from_pts(item['source_path'],key,points,raw_start,raw_end,
                item['video_id']+':CAD:'+str(j),width=item['width'],height=item['height'])
            w['window_duration_sec']=end-start
            windows.append({'start_sec':start,'end_sec':end,'window':w,'clock_record_sha256':clock['clock_record_sha256'],
                'clock_branch':clock['branch'],'raw_source_pts_origin_sec':float(a['raw_first_pts_ticks']*tick)})
        jobs.append(dict(video_id=item['video_id'],source_key=key,source_group=key,metadata=item,windows=windows))
        c.state('REMATCH_NATIVE_SOURCE_PLANNING',sources=n,total=426,new_model_calls=0)
    c.require(len(jobs)==426 and sum(len(x['windows']) for x in jobs)==521,'426/521 native denominator')
    c.save(c.HERE/'input_01/rematch_plan.json',dict(scope='rematch',jobs=jobs,sources=sources,input_ref=ref,records=426,windows=521))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('scope',choices=('developer','rematch','plan-rematch'))
    a=p.parse_args().scope
    if a=='plan-rematch':plan_rematch()
    else:run(a)
