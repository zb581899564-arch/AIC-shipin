"""One native-nearest-alignment input, original B0 prompt/greedy/validator/model."""
import argparse,time
import nr_common as c
from nr_native import decode_round_window,round_window

def encode_round(processor,window,rt,student,ex):
    import torch
    from exact_pts import exact_native_pts,verify_native_encoding
    from nr_video import encode,identity
    decoded=decode_round_window(window);arr,metadata,plan,evidence=decoded
    with exact_native_pts(processor,plan,metadata['fps']) as native:
        encoded=encode(processor,text=[rt.prompt(processor,ex.base_texts(None)['B0'])],
            videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[metadata],video_size=student.VIDEO_SIZE,max_input=16384)
        verify_native_encoding(processor,encoded,native)
    return encoded,dict(**evidence,native_processor_identity=native,**identity(processor,encoded,len(arr)),
        registered_prompt_sha256=ex.cc.digest(ex.base_texts(None)['B0']))

def replay(path,job,ix,ex,rt,student,processor):
    v=c.checked(path,job,ix,'Q',ex);w=job['windows'][ix]['window'];encoded,evidence=encode_round(processor,w,rt,student,ex)
    c.require(ex.video_signature(encoded)==v['vision_tensor_signature'] and evidence==v['video_identity'],'new independent native/processor identity')
    raw=c.read(v['raw_receipt']);tok=processor.tokenizer
    c.require(tok.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)==raw['raw_output'],'actual output token decoding')
    from constrained_json import make_prefix_constraint,ascii_token_candidates
    import torch
    make_prefix_constraint(tok,0,w['window_duration_sec'],candidate_token_ids=ascii_token_candidates(tok),eos_token_ids=tok.eos_token_id,allow_empty=True).assert_complete(torch.tensor(raw['output_token_ids']))
    c.require(int(encoded['input_ids'].shape[1])==v['input_tokens'],'actual CPU token count')
    return dict(path=str(path),done_sha256=c.sha(path),input_tokens=v['input_tokens'],actual_native_processor_raw_validator_equal=True,new_model_calls=0,new_optimizer_updates=0)

def run(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
    student,old,model,processor,candidates,unused,identity=ex.loaded_model()
    c.require(identity==c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'actual original B model differs')
    out=c.HERE/(scope+'_01');c.save(out/'model.json',identity);fresh=reused=0;began=time.monotonic()
    for num,job in enumerate(jobs,1):
        for ix,part in enumerate(job['windows']):
            path=c.done_path(scope,job,ix,'Q',cc)
            if part['window']==part['base_window']:
                c.checked(path,job,ix,'Q',ex);reused+=1;continue
            c.require(not path.exists(),'success must not be generated twice')
            w=part['window'];encoded,evidence=encode_round(processor,w,rt,student,ex)
            if scope!='rematch':
                base=c.checked_base(scope,job,ix);ids=evidence['source_frame_ids'];pixels=evidence['frame_pixel_sha256']
                base_ids=base['video_identity']['source_frame_ids'];base_pixels=base['video_identity']['frame_pixel_sha256']
                c.require(len(ids)==len(base_ids) and evidence['video_grid_thw']==base['video_identity']['video_grid_thw'] and
                    all(pixels[ids.index(i)]==base_pixels[base_ids.index(i)] for i in set(ids)&set(base_ids)),'same count/grid and common physical RGB identities')
            value=rt.attempt(model,processor,encoded,evidence,w,path.parent/'raw.json',allow_empty=True,local_candidates=candidates)
            value.update(request_sha256=cc.digest(c.local_request(job,ix,'Q',identity,ex)),bound_files={value['raw_receipt']:c.sha(value['raw_receipt'])},
                arm='Q',window=w,model_identity=identity,context_audit={},vision_tensor_signature=ex.video_signature(encoded))
            c.save(path,value);fresh+=1;del encoded
            if scope=='nontest' and fresh==1:
                c.save(c.HERE/'first_real_acceptance.json',dict(replay(path,job,ix,ex,rt,student,processor),
                    status='PASS_REAL_FIRST_NATIVE_ROUND_ALIGNMENT_AND_INDEPENDENT_CPU_REPLAY',utc=c.utc()))
        c.state('RUNNING_'+scope.upper()+'_ROUND_ALIGNMENT',records_completed=num,total_records=len(jobs),fresh_model_calls=fresh,
            reused_exact_original_calls=reused,new_overview_calls=0,wall_seconds=time.monotonic()-began)
    total={'nontest':8,'developer':112,'rematch':521}[scope]
    c.require(fresh+reused==total and fresh==sum(p['window']!=p['base_window'] for j in jobs for p in j['windows']),'actual fresh+exact reused denominator')
    c.save(out/(scope+'.completion.json'),dict(status='PASS_ALL_NATIVE_ROUND_ALIGNMENT_ATTEMPTS',utc=c.utc(),records=len(jobs),fresh_model_calls=fresh,
        model_identity=identity,reused_exact_original_calls=reused,total_windows=total,new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0))

def plan_rematch():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    c.require(c.read(c.HERE/'developer_01/report.json')['status']=='GO_ONE_NATIVE_ROUND_ALIGNMENT_RISK_PACKAGE','not admitted')
    ref,manifest,clocks=old.inputs('rematch');from fractions import Fraction
    scanner=rt.load(c.CAD/'prepare.py','nr_source_scanner').source_clock;jobs=[];sources={}
    for n,item in enumerate(manifest['records'],1):
        clock=clocks[item['video_id']];a=clock['arrays'];tick=Fraction(a['raw_time_base']);pts=[float(x*tick) for x in a['native_pts_ticks']]
        physical=scanner(item,manifest['allowed_source_roots']);c.require(physical['pts']==pts,'actual rematch native clock differs')
        key=item['source_sha256'];sources[key]=physical;windows=[]
        for ix,(start,end) in enumerate(frames.window_schedule(item,manifest['kind'],clock)):
            raw_start,raw_end=production.raw_window_bounds(a,start,end)
            base=student.window_from_pts(item['source_path'],key,pts,raw_start,raw_end,item['video_id']+':T:'+str(ix))
            base['window_duration_sec']=end-start
            windows.append(dict(start_sec=start,end_sec=end,base_window=base,window=round_window(base,pts),clock_record_sha256=clock['clock_record_sha256'],
                clock_branch=clock['branch'],raw_source_pts_origin_sec=float(a['raw_first_pts_ticks']*tick)))
        jobs.append(dict(video_id=item['video_id'],source_key=key,source_group=key,metadata=item,windows=windows));c.state('REMATCH_NATIVE_PLANNING',sources=n,total=426,new_model_calls=0)
    c.require(len(jobs)==426 and sum(len(x['windows']) for x in jobs)==521,'complete426/521')
    c.prepare_v14_aliases(jobs,ex,student)
    c.save(c.HERE/'input_01/rematch_plan.json',dict(scope='rematch',jobs=jobs,sources=sources,input_ref=ref,records=426,windows=521))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('scope',choices=('nontest','developer','rematch','plan-rematch'));a=p.parse_args().scope
    plan_rematch() if a=='plan-rematch' else run(a)
