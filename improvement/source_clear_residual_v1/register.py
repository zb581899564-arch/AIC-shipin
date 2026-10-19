"""Fixed source manifest, original B0 adoption, and bounded missing-stage inventory."""
from sr_common import *
from fractions import Fraction as F

def main():
    cpu()
    require(not (ROOT/'registration.json').exists(),'Do not repeat registration')
    sources=[];windows=[];bindings=[]
    ext=read(EXT/'protocol.json');by_name={s['name']:s for s in ext['sources']}
    cohorts=[('SumMe20',W/'human_reference_iteration_20261013_v1','processor_02/completion.json','human_gpu_01/completion.json'),
             ('SumMe5',W/'duration_guard_iteration_20261013_v1','processor_01/completion.json','new5_gpu_01/completion.json')]
    def window(cohort,e,proof,meta,done,sid):
        require(done.get('status')in ('MODEL_OK','LEGAL_EMPTY') and done['segments'] is not None,'Adopt actual successful B0 only')
        require(meta['audio_observed'] is False and meta['reference_available_to_inference'] is False,'No labels in observation')
        uid=sid+'_'+meta['case_id'];out=dict(uid=uid,sid=sid,cohort=cohort,meta=meta,old_proof=proof,old_done=done,events=[])
        lo,hi=F(meta['window_start']),F(meta['window_end'])
        require(len(meta['source_frame_ordinals'])==64 and len(set(meta['source_frame_ordinals']))==64,'Original64 domain')
        for i,pair in enumerate(done['segments']):
            a,b=map(lambda x:F(str(x)),pair);require(0<=a<b<=hi-lo,'Original segment domain')
            out['events'].append(dict(event_id='sr.'+sid+'.'+meta['case_id']+'.seg'+str(i),original_segment_index=i,original_interval_exact=[str(lo+a),str(lo+b)]))
        windows.append(out)
    for cohort,b,cp,gp in cohorts:
        ac=read(b/cp);gc=read(b/gp);by={x['case_id']:x for x in gc['entries']};bindings.extend([ref(b/cp),ref(b/gp)])
        for e in ac['proofs']:
            bound(dict(path=e['proof_path'],sha256=e['proof_sha256']));proof=read(e['proof_path']);bound(dict(path=proof['input_path'],sha256=proof['input_sha256']));meta=read(proof['input_path'])
            d=by[e['case_id']];bound(dict(path=d['done_path'],sha256=d['done_sha256']));done=read(d['done_path']);s=by_name[meta['source_name']];sid=s['id']
            if not any(x['sid']==sid for x in sources):
                sources.append(dict(sid=sid,name=s['name'],group='train',native_ref=ref(PRIOR/'inputs'/sid/'native.npz'),clock_ref=ref(PRIOR/'inputs'/sid/'clock.json'),language_ref=ref(EXT/'features'/sid/'language.npy'),yes_no_ref=ref(EXT/'features'/sid/'yes_no.npy'),labels_ref=ref(PRIOR/'label_arrays'/(s['name']+'.npy')),media=dict(path=meta['source_path'],sha256=meta['source_sha256'],bytes=meta['source_bytes']),historical_exposure=True))
            window(cohort,e,proof,meta,done,sid)
    vb=W/'videoxum_reference_iteration_20261013_v1';va=read(vb/'cohort_input_acceptance_07.json');vg=read(vb/'cohort_gpu_07/completion.json');vd={x['case_id']:x for x in vg['entries']}
    chosen=sorted(va['sources'],key=lambda s:hashlib.sha256(('SOURCE_CLEAR_RESIDUAL_CHECK_V1:'+s['video_id']).encode()).hexdigest())[:8]
    ids={s['video_id']:'V%02d'%i for i,s in enumerate(chosen)}
    bindings.extend([ref(vb/'cohort_input_acceptance_07.json'),ref(vb/'cohort_gpu_07/completion.json')])
    for s in chosen:
        sid=ids[s['video_id']];sources.append(dict(sid=sid,name=s['video_id'],group='check',clock_ref=dict(path=s['native_clock_path'],sha256=s['native_clock_sha256']),reference_ref=dict(path=s['reference_path'],sha256=s['reference_sha256']),historical_exposure=True))
    for e in va['proofs']:
        if e['video_id'] not in ids:continue
        proof=read(bound(dict(path=e['proof_path'],sha256=e['proof_sha256'])));meta=read(bound(dict(path=e['input_path'],sha256=e['input_sha256'])));d=vd[e['case_id']];done=read(bound(dict(path=d['done_path'],sha256=d['done_sha256'])))
        sid=ids[e['video_id']];next(s for s in sources if s['sid']==sid)['media']=dict(path=meta['source_path'],sha256=meta['source_sha256'],bytes=meta['source_bytes'])
        window('VideoXum8',e,proof,meta,done,sid)
    require(len(sources)==33 and sum(s['group']=='train'for s in sources)==25 and len(windows)==187,'Frozen source/window denominator')
    baseline=ref(OLD/'package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip');require(baseline['sha256']==BASE_SHA,'Protected40.47 changed')
    reg=dict(schema='SOURCE_CLEAR_FULL_BASELINE_SINGLE_RESIDUAL_V1',utc=utc(),start_utc='2026-10-18T04:36:50Z',deadline_utc='2026-10-18T08:36:50Z',baseline=baseline,sources=sources,windows=windows,old_bindings=bindings,verify_role='TIME_ENABLED',feature_role='BASE_DISABLED',model_parameters=8782459120,old_semantic_parameters=98329,new_head='source_equal_ridge_alpha1_linear_12_input_delta_F1',new_head_scalars=37,max_add_cells_per_source=1,no_new426_model=True,new_backbone_updates=0,train_sources=25,check_sources=8,all_reference_historical=True,code={p.name:sha(p)for p in sorted((ROOT/'code').glob('*.py'))},missing_RGB_recovery_scope='116 expired SumMe native64 RGB caches: first new-purpose read of original media, exact old sample/pixel SHA comparison; no old B0 encode/generation rerun',new_input_scope='First VERIFY prompt inputs; shared vision once/window; VideoXum8 first halfsecond image/context query inputs; inherit old native mappings, do not recreate labels/clocks',rules=read(ROOT/'authorization.json'))
    save(ROOT/'registration.json',reg)
    event('REGISTRATION_COMPLETE',sources=33,old_B0_windows_adopted=len(windows),new_verify_decisions=sum(len(w['events'])for w in windows),cached_old_RGB=sum(Path(w['meta']['frame_array_path']).exists()for w in windows),formal_new_GPU=0)

if __name__=='__main__':
    try:main()
    except BaseException as e:failure('register',e);raise
