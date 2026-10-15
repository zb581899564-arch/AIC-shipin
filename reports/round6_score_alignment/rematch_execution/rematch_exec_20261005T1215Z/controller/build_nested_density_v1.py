"""Build one independent nested-native density experiment without old edits."""
from pathlib import Path

RUN=Path(__file__).resolve().parent.parent
OUT=RUN/'nested_density_v1'
assert not OUT.exists(),'new entry already exists; do not rebuild running work'
OUT.mkdir()

def put(name,source):
    (OUT/name).write_text(source,encoding='utf-8',newline='\n')
    if name.endswith('.py'):compile(source,str(OUT/name),'exec')

base=(RUN/'b_prompt_recovery_v1/brec_common.py').read_text(encoding='utf-8')
base=base[:base.index('def local_request')]
base=base.replace('brec_original_','nd_original_').replace('frozen recovery','frozen nested-density')
base+='''def base_job(job):
    import copy
    value=copy.deepcopy(job)
    for part in value['windows']:
        part['window']=part['base_window'];part.pop('base_window',None)
    return value

def base_path(scope,job,ix,cc):
    return CAD/('developer_01' if scope=='developer' else scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'B0/done.json'

def checked_base(scope,job,ix):
    upstream=load(RUN/'b_prompt_recovery_v1/brec_common.py','nd_preserved_base_authority')
    rt,ex,cc,student,old,frames,production=helpers()
    return upstream.checked(base_path(scope,job,ix,cc),base_job(job),ix,'B0',ex)

def local_request(job,ix,arm,identity,ex):
    require(arm=='D','only one nested-density arm')
    return dict(kind='local',window=job['windows'][ix]['window'],arm='D',
        prompt=ex.base_texts(None)['B0'],model=identity,max_input=16384,max_output=256,
        allow_empty=True,context_audit={},sampling_recipe='BASE_FLOOR64_PLUS_ALL_ADJACENT_NATIVE_ORDINAL_MIDPOINTS',
        video_size={'shortest_edge':4096,'longest_edge':25165824},
        spatial_resolution_tradeoff='SAME_TOTAL_VIDEO_PIXEL_BUDGET_ACTUAL_GRID_RECORDED_NOT_ASSUMED_EQUAL')

def done_path(scope,job,ix,arm,cc):
    require(arm=='D','wrong new arm')
    return HERE/(scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'D/done.json'

def checked(path,job,ix,arm,ex):
    value=read(path);ex.checked_done(path,local_request(job,ix,arm,value['model_identity'],ex))
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=job['windows'][ix]['window']
    require(value['arm']=='D' and value['window']==w and value['context_audit']=={},'wrong density window/arm/context')
    parsed,errors,_=parse_segments(value['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==value['parsed_segments'],'original unchanged validator differs')
    native=native_segment_ranges(parsed,value['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in native]==value['native_frame_realizability']['ranges'],'original native selection differs')
    raw=read(value['raw_receipt'])
    require(raw['raw_output']==value['raw_output'] and raw['overview_adapter_disabled'] is False,'new density raw identity')
    import math
    require(raw['selected_token_scores'] and all(isinstance(s,(float,int)) and math.isfinite(s) for s in raw['selected_token_scores']),'invalid actual token scores')
    return value
'''
put('nd_common.py',base)

student=(RUN/'teacher_student_autopilot_v14/train_student.py').read_text(encoding='utf-8')
decoder=student[student.index('def decode_window('):student.index('\ndef decode_observed(')]
assert decoder.count('len(ids) == len(pts) <= 64')==1
assert decoder.count('ids == floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"])')==1
decoder=decoder.replace('def decode_window(','def decode_nested_window(').replace('len(ids) == len(pts) <= 64','len(ids) == len(pts) <= 127')
decoder=decoder.replace('ids == floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"])','ids == nested_indices(floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"]))')
prefix='''"""Declared new127-frame decoder; original V14 remains immutable."""
import hashlib,math,sys
from pathlib import Path
import nd_common as c
require,sha,load=c.require,c.sha,c.load
HERE=c.RUN/'teacher_student_autopilot_v14'
_VERIFIED_SOURCE_STATS={}

def floor_indices(first,stop):
    require(type(first) is int and type(stop) is int and 0<=first<stop,'bad original ordinal range')
    n=stop-first
    return list(range(first,stop)) if n<=64 else [first+i*(n-1)//63 for i in range(64)]

def nested_indices(base):
    require(base and base==sorted(set(base)) and len(base)<=64 and all(type(i) is int and i>=0 for i in base),'bad preserved floor64 ordinals')
    return sorted(set(base)|{(a+b)//2 for a,b in zip(base,base[1:]) if b-a>1})

def dense_window(original,points):
    import copy
    value=copy.deepcopy(original);base=original['planned_source_frame_ordinals'];ids=nested_indices(base)
    require(base==floor_indices(base[0],base[0]+original['eligible_source_frame_count']),'original floor64 contract differs')
    require(set(base)<=set(ids) and ids[0]==base[0] and ids[-1]==base[-1] and len(ids)<=127,'dense plan dropped or expanded physical endpoints')
    require([points[i] for i in base]==original['planned_actual_pts_sec'],'preserved source PTS differs')
    value.update(planned_source_frame_ordinals=ids,planned_actual_pts_sec=[points[i] for i in ids],
        sampling_recipe='BASE_FLOOR64_PLUS_ALL_ADJACENT_NATIVE_ORDINAL_MIDPOINTS',
        baseline_floor64_ordinals=base,physical_frames_added=len(ids)-len(base))
    return value

'''
decoder=decoder.replace('    before = Path(w["source_path"]).stat()',
    '    require(w.get("sampling_recipe")=="BASE_FLOOR64_PLUS_ALL_ADJACENT_NATIVE_ORDINAL_MIDPOINTS" and set(w["baseline_floor64_ordinals"])<=set(ids),"unregistered nested-density authority")\n    before = Path(w["source_path"]).stat()')
put('nd_native.py',prefix+decoder)

video=(RUN/'next_round_v1/video_contract.py').read_text(encoding='utf-8')
assert video.count('MAX_FRAMES = 64')==1
put('nd_video.py',video.replace('MAX_FRAMES = 64','MAX_FRAMES = 127').replace('one-video/64-frame','one-video/127-frame'))

put('nd_prepare.py','''"""Register one density alternative before any new density weak direction."""
from collections import Counter
import nd_common as c
from nd_native import dense_window

def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    rt,ex,cc,student,old,frames,production=c.helpers()
    upstream=c.RUN/'b_prompt_recovery_v1'
    stop=c.read(upstream/'scientific_stop.json');r=stop['report']
    c.require(r['status']=='STOP_HISTORICAL_B1_INVESTMENT' and r['new_B1_calls']==86 and r['records']==104 and
        r['all104_B1_minus_B0']['mean']<0 and r['expanded72_B1_minus_B0']['mean']<0,'preserved B1 stop differs')
    c.require(c.read(upstream/'developer_01/replay_acceptance.json')['status']=='PASS_ALL_86_NEW_B1_NATIVE_CPU_REPLAY','complete original CPU acceptance missing')
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');resources={}
    p=c.RUN/'controller/aic_BREC_v1_developer.resource.json';v=c.read(p)
    c.require([x for x in ledger if x.get('name')==v['name']]==[v] and v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'original terminal accounting')
    resources[v['name']]=dict(path=str(p),sha256=c.sha(p),charged_seconds=v['charged_seconds'])
    # The inherited source lock protects all old dependencies. Preserve every newly completed B1 byte too.
    upstream_success=[]
    for p in (upstream/'developer_01').rglob('done.json'):
        x=c.read(p)
        for f,s in x['bound_files'].items():c.require(c.sha(f)==s,'newly completed historical B1 raw changed')
        upstream_success.append(dict(path=str(p),sha256=c.sha(p),bound_files=x['bound_files']))
    c.require(len(upstream_success)==86,'old completed B1 denominator')
    authority=[];model=None;counts=Counter();sampling=[]
    for scope in ('nontest','developer'):
        plan=c.read(c.CAD/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        sources=ex.source_tables(plan)
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                original=part['window'];part['base_window']=original
                part['window']=dense_window(original,sources[job['source_key']]['pts'])
                base=c.checked_base(scope,job,ix)
                if model is None:model=base['model_identity']
                c.require(model==base['model_identity'],'original B0 model differs')
                path=c.base_path(scope,job,ix,cc)
                authority.append(dict(scope=scope,video_id=job['video_id'],index=ix,path=str(path),sha256=c.sha(path),bound_files=base['bound_files']))
                counts[scope]+=1
                a=original['planned_actual_pts_sec'];b=part['window']['planned_actual_pts_sec']
                sampling.append(dict(scope=scope,base_physical_frames=len(a),new_physical_frames=len(b),
                    base_max_gap=max((y-x for x,y in zip(a,a[1:])),default=0),new_max_gap=max((y-x for x,y in zip(b,b[1:])),default=0)))
        c.save(c.HERE/'input_01'/(scope+'_plan.json'),plan)
    c.require(dict(counts)=={'nontest':8,'developer':112} and any(x['new_physical_frames']>x['base_physical_frames'] for x in sampling),'new input mechanism absent')
    c.save(c.HERE/'input_01/resume_manifest.json',dict(rows=authority,counts=dict(counts),model_identity=model,resources=resources,
        preserved_upstream_success=upstream_success,original_B1_stop_sha256=c.sha(upstream/'scientific_stop.json'),
        original_B1_report_sha256=c.sha(upstream/'developer_01/report.json'),new_density_success_reused=0))
    c.save(c.HERE/'input_01/sampling_audit.json',dict(records=sampling,all_old_samples_preserved=True,
        all_physical_first_last_unchanged=True,new_density_frames_max=127,first_replay_not_full_source_decode=True,
        spatial_resolution_tradeoff='TOTAL_VIDEO_PIXEL_BUDGET_UNCHANGED_ACTUAL_GRID_MUST_BE_REPORTED'))
    c.save(c.HERE/'input_01/investment_rule.json',dict(registered_utc=c.utc(),all104_delta_min=0,expanded72_delta_strictly_positive=True,
        native_set_change_required=True,negative_mean_threshold=-.05,negative_group_fraction_threshold=.75,
        bootstrap_draws=10000,bootstrap_seed=20261009,CI_report_only=True,new_density_weak_direction_read=False,
        observed_development_not_new_holdout=True,coverage='UNKNOWN',training_admitted=False))
    c.save(c.HERE/'prepared.json',dict(status='PASS_EXACT_NEGATIVE_B1_AND_NESTED_NATIVE_DENSITY_PLAN',utc=c.utc(),
        records=104,groups=96,developer_windows=112,nontest_windows=8,new_model_calls=0,new_optimizer_updates=0,
        original_baseline_calls_reused=120,new_density_calls_required=120,registered_original_B1_stop=True))
    print(c.read(c.HERE/'prepared.json'),flush=True)

if __name__=='__main__':main()
''')

put('nd_engine.py','''"""One nested-density input, original B0 prompt/greedy/validator/model."""
import argparse,time
import nd_common as c
from nd_native import decode_nested_window,dense_window

def encode_nested(processor,window,rt,student,ex):
    import torch
    from exact_pts import exact_native_pts,verify_native_encoding
    from nd_video import encode,identity
    decoded=decode_nested_window(window);arr,metadata,plan,evidence=decoded
    with exact_native_pts(processor,plan,metadata['fps']) as native:
        encoded=encode(processor,text=[rt.prompt(processor,ex.base_texts(None)['B0'])],
            videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[metadata],video_size=student.VIDEO_SIZE,max_input=16384)
        verify_native_encoding(processor,encoded,native)
    return encoded,dict(**evidence,native_processor_identity=native,**identity(processor,encoded,len(arr)),
        registered_prompt_sha256=ex.cc.digest(ex.base_texts(None)['B0']))

def replay(path,job,ix,ex,rt,student,processor):
    v=c.checked(path,job,ix,'D',ex);w=job['windows'][ix]['window'];encoded,evidence=encode_nested(processor,w,rt,student,ex)
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
    out=c.HERE/(scope+'_01');c.save(out/'model.json',identity);fresh=0;began=time.monotonic()
    for num,job in enumerate(jobs,1):
        for ix,part in enumerate(job['windows']):
            path=c.done_path(scope,job,ix,'D',cc);c.require(not path.exists(),'success must not be generated twice')
            w=part['window'];encoded,evidence=encode_nested(processor,w,rt,student,ex)
            if scope!='rematch':
                base=c.checked_base(scope,job,ix);ids=evidence['source_frame_ids'];pixels=evidence['frame_pixel_sha256']
                c.require([pixels[ids.index(i)] for i in base['video_identity']['source_frame_ids']]==base['video_identity']['frame_pixel_sha256'],'preserved64 pixel identities')
            value=rt.attempt(model,processor,encoded,evidence,w,path.parent/'raw.json',allow_empty=True,local_candidates=candidates)
            value.update(request_sha256=cc.digest(c.local_request(job,ix,'D',identity,ex)),bound_files={value['raw_receipt']:c.sha(value['raw_receipt'])},
                arm='D',window=w,model_identity=identity,context_audit={},vision_tensor_signature=ex.video_signature(encoded))
            c.save(path,value);fresh+=1;del encoded
            if scope=='nontest' and fresh==1:
                c.save(c.HERE/'first_real_acceptance.json',dict(replay(path,job,ix,ex,rt,student,processor),
                    status='PASS_REAL_FIRST_NESTED_DENSITY_AND_INDEPENDENT_CPU_REPLAY',utc=c.utc()))
        c.state('RUNNING_'+scope.upper()+'_DENSITY',records_completed=num,total_records=len(jobs),fresh_model_calls=fresh,new_overview_calls=0,wall_seconds=time.monotonic()-began)
    c.require(fresh=={'nontest':8,'developer':112,'rematch':521}[scope],'actual new density denominator')
    c.save(out/(scope+'.completion.json'),dict(status='PASS_ALL_NESTED_DENSITY_ATTEMPTS',utc=c.utc(),records=len(jobs),fresh_model_calls=fresh,
        model_identity=identity,new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0))

def plan_rematch():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    c.require(c.read(c.HERE/'developer_01/report.json')['status']=='GO_ONE_NESTED_DENSITY_RISK_PACKAGE','not admitted')
    ref,manifest,clocks=old.inputs('rematch');from fractions import Fraction
    scanner=rt.load(c.CAD/'prepare.py','nd_source_scanner').source_clock;jobs=[];sources={}
    for n,item in enumerate(manifest['records'],1):
        clock=clocks[item['video_id']];a=clock['arrays'];tick=Fraction(a['raw_time_base']);pts=[float(x*tick) for x in a['native_pts_ticks']]
        physical=scanner(item,manifest['allowed_source_roots']);c.require(physical['pts']==pts,'actual rematch native clock differs')
        key=item['source_sha256'];sources[key]=physical;windows=[]
        for ix,(start,end) in enumerate(frames.window_schedule(item,manifest['kind'],clock)):
            raw_start,raw_end=production.raw_window_bounds(a,start,end)
            base=student.window_from_pts(item['source_path'],key,pts,raw_start,raw_end,item['video_id']+':CAD:'+str(ix),width=item['width'],height=item['height'])
            base['window_duration_sec']=end-start
            windows.append(dict(start_sec=start,end_sec=end,base_window=base,window=dense_window(base,pts),clock_record_sha256=clock['clock_record_sha256'],
                clock_branch=clock['branch'],raw_source_pts_origin_sec=float(a['raw_first_pts_ticks']*tick)))
        jobs.append(dict(video_id=item['video_id'],source_key=key,source_group=key,metadata=item,windows=windows));c.state('REMATCH_NATIVE_PLANNING',sources=n,total=426,new_model_calls=0)
    c.require(len(jobs)==426 and sum(len(x['windows']) for x in jobs)==521,'complete426/521')
    c.save(c.HERE/'input_01/rematch_plan.json',dict(scope='rematch',jobs=jobs,sources=sources,input_ref=ref,records=426,windows=521))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('scope',choices=('nontest','developer','rematch','plan-rematch'));a=p.parse_args().scope
    plan_rematch() if a=='plan-rematch' else run(a)
''')

put('nd_cpu.py','''"""Actual full120 density CPU feasibility; no GPU or teacher calls."""
import nd_common as c
from nd_native import nested_indices,floor_indices
from nd_engine import encode_nested

def main():
    rt,ex,cc,student,old,frames,production=c.helpers()
    from transformers import AutoProcessor
    from nd_report import gate
    c.require(gate(0,.001,1,0) and not gate(.1,0,1,0) and not gate(.1,.1,0,0) and not gate(-.01,.1,1,0),'fixed administrative gate')
    for n in range(1,2001):
        base=floor_indices(13,13+n);dense=nested_indices(base)
        c.require(set(base)<=set(dense) and dense[0]==13 and dense[-1]==12+n and len(dense)<=127 and dense==sorted(set(dense)),'native subset/endpoints/count')
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    proofs=[]
    for scope in ('nontest','developer'):
        plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                base=c.checked_base(scope,job,ix);encoded,evidence=encode_nested(processor,part['window'],rt,student,ex)
                ids=evidence['source_frame_ids'];pixels=evidence['frame_pixel_sha256']
                c.require([pixels[ids.index(i)] for i in base['video_identity']['source_frame_ids']]==base['video_identity']['frame_pixel_sha256'],'actual preserved old64 RGB/native identity')
                c.require(evidence['window_source_pts_sec']==base['video_identity']['window_source_pts_sec'],'all source-selection PTS unchanged')
                tokens=int(encoded['input_ids'].shape[1]);c.require(0<tokens<=16384,'actual input overflow, no truncation')
                proofs.append(dict(scope=scope,video_id=job['video_id'],index=ix,input_tokens=tokens,base_sample_count=len(base['video_identity']['source_frame_ids']),
                    dense_sample_count=len(ids),base_grid=base['video_identity']['video_grid_thw'],dense_grid=evidence['video_grid_thw'],
                    preserved_RGB_equal=True,exact_native_processor_used=True,spatial_resolution_change_reported=True,
                    vision_signature=ex.video_signature(encoded),video_identity=evidence))
                del encoded;c.state('CPU_DENSITY_ACTUAL_INPUTS',checked_windows=len(proofs),total_windows=120,new_model_calls=0)
    c.require(len(proofs)==120 and sum(x['scope']=='nontest' for x in proofs)==8 and sum(x['scope']=='developer' for x in proofs)==112,'CPU full registered denominator')
    c.save(c.HERE/'cpu_acceptance.json',dict(status='PASS_ALL120_ACTUAL_NESTED_NATIVE_PROCESSOR_AND_BASE_PIXEL_IDENTITY',utc=c.utc(),proofs=proofs,
        physical_sampling_contract_cases=2000,registered_gate_cases=4,max_input_tokens=max(x['input_tokens'] for x in proofs),
        actual_all120_inputs_not_estimated=True,new_model_calls=0,new_optimizer_updates=0,new_32B_calls=0))
    print('PASS_ALL120_ACTUAL_NESTED_NATIVE_PROCESSOR_AND_BASE_PIXEL_IDENTITY',flush=True)

if __name__=='__main__':main()
''')

report='''"""Independent density replay and full104/expanded72 fixed investment gate."""
import statistics
import nd_common as c
from nd_engine import replay

def gate(delta,new_delta,changed,down):
    return changed>0 and delta>=0 and new_delta>0 and not(delta<=-.05 and down>=.75)

def main(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    from transformers import AutoProcessor
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs'];rows=[];proofs=[]
    first=c.read(c.HERE/'first_real_acceptance.json')['path']
    for job in jobs:
        row=dict(video_id=job['video_id'],source_group=job['source_group'],arms={})
        for arm in ('D','B0') if scope=='developer' else ('D',):
            intervals=[];ids=set()
            for ix,part in enumerate(job['windows']):
                if arm=='D':
                    p=c.done_path(scope,job,ix,'D',cc);v=c.checked(p,job,ix,'D',ex)
                    if str(p)!=first:proofs.append(replay(p,job,ix,ex,rt,student,processor))
                else:v=c.checked_base(scope,job,ix)
                base=part['window']['planned_source_frame_ordinals'][0]
                for a,b in v['native_frame_realizability']['ranges']:ids.update(range(base+a,base+b))
                offset=part['start_sec']-job.get('clip_start_sec',0);intervals.extend([[offset+a,offset+b] for a,b in v['parsed_segments']])
            row['arms'][arm]=dict(native_source_ordinals=sorted(ids),segments=intervals,legal_empty=not intervals)
            if scope=='developer':row['arms'][arm]['closed_world_output_agreement']=cc.weak_metrics(intervals,job['weak_reference'])
        rows.append(row)
    c.require(len(proofs)==(7 if scope=='nontest' else 112),'new independent replay denominator')
    c.save(c.HERE/(scope+'_01/replay_acceptance.json'),dict(status='PASS_ALL_SCOPE_NESTED_DENSITY_NATIVE_CPU_REPLAY',first_proof_sha256=c.sha(c.HERE/'first_real_acceptance.json'),proofs=proofs,new_model_calls=0))
    if scope=='nontest':return
    c.require(len(rows)==104 and len({x['source_group'] for x in rows})==96,'full developer denominator')
    pilot=set(plan['pilot_source_groups']);new=[r for r in rows if r['source_group'] not in pilot];c.require(len(new)==80 and len({r['source_group'] for r in new})==72,'expanded72')
    original=rt.load(c.CAD/'report.py','nd_bootstrap_only');delta=lambda r:r['arms']['D']['closed_world_output_agreement']['f1']-r['arms']['B0']['closed_world_output_agreement']['f1']
    all_metric=original.bootstrap_video_macro([delta(r) for r in rows],rows);new_metric=original.bootstrap_video_macro([delta(r) for r in new],new)
    groups=sorted({r['source_group'] for r in rows});down=sum(statistics.mean(delta(r) for r in rows if r['source_group']==g)<0 for g in groups)
    changed=sum(r['arms']['D']['native_source_ordinals']!=r['arms']['B0']['native_source_ordinals'] for r in rows)
    c.save(c.HERE/'developer_01/matched_rows.json',rows)
    result=dict(status='GO_ONE_NESTED_DENSITY_RISK_PACKAGE' if gate(all_metric['mean'],new_metric['mean'],changed,down/96) else 'STOP_NESTED_DENSITY_INVESTMENT',
        utc=c.utc(),records=104,groups=96,windows=112,new_density_calls=112,original_B0_reused=112,all104_D_minus_B0=all_metric,expanded72_D_minus_B0=new_metric,
        changed_native_sets=changed,groups_down=down,reference_coverage='UNKNOWN',metric_is_closed_world_weak_output_agreement_not_quality_truth=True,
        observed_development_not_new_holdout=True,original_total_video_pixel_budget_unchanged=True,physical64_subset_retained=True,
        new_optimizer_updates=0,official_score=None,no_post_result_retuning=True)
    c.save(c.HERE/'developer_01/report.json',result);print(result,flush=True)

if __name__=='__main__':
    import sys;main(sys.argv[1])
'''
put('nd_report.py',report)

freeze=(RUN/'b_prompt_recovery_v1/freeze.py').read_text(encoding='utf-8').replace('brec_common','nd_common')
freeze=freeze.replace('PASS_ACTUAL_NEW_B1_NATIVE_PROCESSOR_AND_EXACT_RESUME','PASS_ALL120_ACTUAL_NESTED_NATIVE_PROCESSOR_AND_BASE_PIXEL_IDENTITY')
freeze=freeze.replace("path=c.RUN/'b_boundary_diagnostic_v1/source_lock.json'","path=c.RUN/'b_prompt_recovery_v1/source_lock.json'")
freeze=freeze.replace("for p in (c.RUN/'b_boundary_diagnostic_v1').glob('*completion.json'):files[str(p)]=c.sha(p)","for p in (c.RUN/'b_prompt_recovery_v1').rglob('*.json'):\n        if p.name in ('scientific_stop.json','report.json','replay_acceptance.json','developer.completion.json'):files[str(p)]=c.sha(p)")
freeze=freeze.replace("for row in resume['rows']:","for row in resume['rows']+resume['preserved_upstream_success']:")
freeze=freeze.replace('AIC_B_HISTORICAL_PROMPT_RECOVERY_V1','AIC_NESTED_NATIVE_DENSITY_V1').replace('PASS_FROZEN_B_PROMPT_RECOVERY_CPU_BINDING','PASS_FROZEN_NESTED_DENSITY_CPU_BINDING')
put('freeze.py',freeze)

pack=(RUN/'b_prompt_recovery_v1/packager.py').read_text(encoding='utf-8').replace('brec_common','nd_common')
pack=pack.replace("'B1'","'D'").replace('HISTORICAL_B1_PROMPT_AND_1_TO_5_GRAMMAR','ORIGINAL_B0_PROMPT_WITH_NESTED_NATIVE_DENSITY')
pack=pack.replace('PASS_ALL_REGISTERED_HISTORICAL_B1_ATTEMPTS','PASS_ALL_NESTED_DENSITY_ATTEMPTS').replace("terminal['fresh_B1_calls']","terminal['fresh_model_calls']")
pack=pack.replace('allow_empty=False','allow_empty=True').replace("nontest_exact_existing_B1_reuse=scope=='nontest'","nontest_exact_existing_B1_reuse=False")
pack=pack.replace('candidate_B_PROMPT_RECOVERY_8B','candidate_NESTED_DENSITY_8B').replace('PASS_COMPLETE_B_PROMPT_RECOVERY_8B_PACKAGE_ON_LINUX','PASS_COMPLETE_NESTED_DENSITY_8B_PACKAGE_ON_LINUX')
put('packager.py',pack)

final=(RUN/'b_prompt_recovery_v1/final_acceptance.py').read_text(encoding='utf-8').replace('brec_common','nd_common').replace("'B1'","'D'")
final=final.replace('candidate_B_PROMPT_RECOVERY_8B','candidate_NESTED_DENSITY_8B').replace("('developer','rematch')","('nontest','developer','rematch')")
final=final.replace('aic_BREC_v1_','aic_ND_v1_').replace('PASS_INDEPENDENT_HISTORICAL_B1_FINAL','PASS_INDEPENDENT_NESTED_NATIVE_DENSITY_FINAL')
final=final.replace("'coupled_historical_B1_prompt_and_nonempty_grammar':True","'native_floor64_subset_plus_all_ordinal_midpoints':True,'new_training':False,'original_B0_prompt_allow_empty':True")
put('final_acceptance.py',final)

control=(RUN/'b_prompt_recovery_v1/controller.py').read_text(encoding='utf-8').replace('brec_common','nd_common').replace('aic_BREC_v1_','aic_ND_v1_').replace('brec_engine.py','nd_engine.py').replace('brec_report.py','nd_report.py')
control=control.replace("charges['developer']=gpu('developer'", "charges['nontest']=gpu('nontest',[c.HERE/'nd_engine.py','nontest'],14400,500<<20)\n        cpu('nontest_replay',[c.HERE/'nd_report.py','nontest'])\n        for step in ('assemble','finish'):cpu('nontest_'+step,[c.HERE/'packager.py',step,'nontest'])\n        charges['developer']=gpu('developer'")
control=control.replace("[c.HERE/'nd_report.py'])","[c.HERE/'nd_report.py','developer'])")
control=control.replace("        for step in ('assemble','finish'):cpu('nontest_'+step,[c.HERE/'packager.py',step,'nontest'])\n        cpu('rematch_prepare'", "        cpu('rematch_prepare'")
control=control.replace('GO_ONE_HISTORICAL_B1_RISK_PACKAGE','GO_ONE_NESTED_DENSITY_RISK_PACKAGE').replace('STOP_B1_INVESTMENT_AGENT_CONTINUES','STOP_DENSITY_INVESTMENT_AGENT_CONTINUES')
control=control.replace('PASS_INDEPENDENT_HISTORICAL_B1_FINAL','PASS_INDEPENDENT_NESTED_NATIVE_DENSITY_FINAL').replace('PASS_COMPLETE_426_B_PROMPT_RECOVERY_ZIP_ON_LINUX','PASS_COMPLETE_426_NESTED_DENSITY_ZIP_ON_LINUX')
control=control.replace('only missing B1 local receipts','registered additional native observations on original natural windows')
put('controller.py',control)
launch=(RUN/'b_prompt_recovery_v1/launch.py').read_text(encoding='utf-8').replace('brec_common','nd_common').replace('PASS_FROZEN_B_PROMPT_RECOVERY_CPU_BINDING','PASS_FROZEN_NESTED_DENSITY_CPU_BINDING')
put('launch.py',launch)

put('CONTINUE.md','''# Sole independent nested-native density entry
Read PROTOCOL.md/source_lock/start/registration/preflight/prepared/cpu_acceptance and current actual process tree. Only one launcher, never repeat successful calls or finished CPU acceptance. Modules use nd_ namespaces. Original C,32B boundary and B1 recovery scientific STOP/raw/UNKNOWN are immutable. This route is different physical sampling and must never be described as unchanged floor64 model input. Original floor64 observations remain an exact subset. No final426 delivery before independent final/8&426 each11strict/ZIP and full terminal accounting. Main agent owns concrete continuation.
''')
put('PROTOCOL.md','''# One preregistered nested-native observation alternative
Original C,32B matched-boundary and complete historicalB1 alternatives failed their registered scientific evidence gates. Preserve all successful bytes/negative results/UNKNOWN/costs. No prompt search, old teacher calls, old65CE, training or new models. This is one finite, different input mechanism: more physical observations within every original local natural window.

Keep all original104 developer records/96groups/112windows, same24/72source split, and8NONTEST. Use original B0 prompt,0..5 original constrained grammar, originalB8B/288adapter/8782459120parameters/greedy/256output/16384input. Begin with every original integer-floor64 ordinal; add the floor ordinal midpoint of EVERY adjacent nonconsecutive pair. At most127 distinct physical frames, sorted; first/last/endpoints and full native source clock unchanged. Do not insert synthetic frames, time interpolation, more than one midpoint, cross-window merging, selected difficult-example deletion or external-answer conditioning. Original64 control success is referenced only after exact original request/raw/model/validator/SHA validation. Existing B1 responses cannot substitute for density responses.

This is explicitly a new sampling contract, not a change to frozen V14/C/B1 code. Sequential PyAV decoding stops after the actual last planned frame, not an asserted full-source decode. Only the declared frame-count and midpoint-admission contract of the independently copied V14 decoder changes; original97exactSHA/profile color mapping stays. Existing documented processor same-last-frame temporal padding is retained and recorded, never treated as an additional physical observation.

The original total-video pixel budget(shortest_edge4096,longest_edge25165824) stays. More sampled frames can REDUCE actual spatial grid resolution. This temporal-density/spatial-resolution tradeoff is registered and measured; do not claim identical model video tensors or per-frame resized resolution. Original physical RGB hashes and endpoints must stay exact for all64 control observations. CPU checks all120 actual decoder/processor inputs, native timestamp override, old64subsetRGB/full-selectionPTS, actual grid and expanded input token counts. Input overflow or unexpected sampling/truncation is engineering STOP; no silent resolution/length adjustment. CPU/plan are not model inference.

Pipeline: full120 real CPU interfaces and2000 ordinal-property cases→new source lock→singlecontroller→8 real NONTEST density calls/first call independent decoder/processor/token/raw/validatorCPUreplay→remaining7 independentCPUreplay→NONTEST full spatial exact cache and11strict→112 real developer calls→all112 independentCPUreplay→one fixed investment gate. No new32B/overview/optimizer. Fresh model raw is saved exclusively before validity checks; failure is not empty and success is never generated twice.

Gate is registered before ANY new density reference direction: full104 video-macro density−B0>=0, expanded72groups(80records) video-macro>0, actual native-selected-frame set change, and no simultaneous mean<=−.05 with>=75percent96groupsdeclining. Groupbootstrap10000/seed20261009 recomputes video-macro; CIreportonly. These are ALREADY OBSERVED DEVELOPMENT references, not fresh holdout/humantruth; Doubao coverage UNKNOWN. Closed-world output agreement is administrative investment evidence, not officialscore, hallucinationproof or guaranteed improvement. No post-result parameter/prompt/gate/subset retuning; candidate outside/UNKNOWN not negative.

GO→complete426source nativeCPUplanning/521 original local windows with same nested input→real521B0 density generation→exact full-source spatial field reuse(allalgorithm/source/model/request/manifest/clock/artifactSHA/denominators/strict/terminalidentities), original spatial costs preserved→426all11strict/sizeSHA/CRC/uniqueJSONL/426identity/originalbytes→independentfinal/uniqueGPUledger. Completion PASS_COMPLETE_426_NESTED_DENSITY_ZIP_ON_LINUX AND final_acceptance PASS_INDEPENDENT_NESTED_NATIVE_DENSITY_FINAL are required. OriginalB selected, newtraining0, newofficialscoreUNKNOWN; no claim to exceed37.63. KeepZIPLinux/noautotransfer/websiteupload.

EngineeringSTOP: originalraw/traceback/success retained; reproduce and repair only in new independent frozen version with exact success reuse. ScientificSTOP: main agent audits remaining concrete production mechanisms or finite evidence exhaustion, not unsupported training or hidden prompt sweeps. User already authorized scientific/engineering decisions, no mid-stage questions. Quiet15minuteaic-linux, project records only, notify only final accepted426 and curatedpublication, then deleteautomation/noarchive. Sharedtasks/locks/append7200ledger/connections protected, livecapacity/peaks/output/conflicts determine resources rather than fixed machine quotas. Mac online/notinvolved, existing small-control directSSH exception; no newbulk/model/data/ZIP transfer without prior direction/bytes/link/proxypermission.
''')
print('PASS_BUILD_NEW_ENTRY',len(list(OUT.iterdir())))
