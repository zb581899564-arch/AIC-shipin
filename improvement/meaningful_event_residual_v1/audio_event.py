"""One audio-specific input pass and one fixed audiovisual event-quality fit."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys,gzip,time
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path.insert(0,str(ROOT/'code_v1'))
from event_runtime import *
from audio_features import extract_audio,proposal_audio_features

OUT=ROOT/'event_audio_01'


def adopted_input(s):
    folder='train_inputs'if s['group']=='train'else'diagnostic_inputs'
    r=read(ROOT/folder/(s['sid']+'.json'))
    d=np.load(bound(r['input_ref']))
    return r,d


def independent_audio_qa(cache,clock,b,c,features):
    manifest,arrays=cache['manifest'],cache['arrays'];pts=list(map(F,clock['normalized_exact_pts']));end=F(clock['physical_end_exact'])
    intervals=[(F(a),F(z))for a,z in manifest['observed_coverage_exact']]
    require(all(0<=a<z<=end for a,z in intervals)and all(x[1]<y[0]for x,y in zip(intervals,intervals[1:])),'Exact observed coverage domain/nonoverlap')
    require(sum((z-a for a,z in intervals),F(0))==F(manifest['raw_evidence']['accepted_resampled_samples'],16000),'Actual16k sample count equals observed exact duration')
    require(features.shape==(len(c),8)and np.isfinite(features).all()and np.all((features[:,7]>=0)&(features[:,7]<=1)),'All new audio proposal rows finite and aligned')
    if manifest['no_audio']:require(not arrays['valid'].any()and not features.any(),'Actual absent stream yields explicit successful zero features')
    # Source normalization recomputed from actual saved raw DSP and exact durations.
    duration=np.zeros(len(arrays['z']))
    for index,value in manifest['observed_bin_durations_exact']:duration[index]=float(F(value))
    for j in range(3):
        ok=arrays['valid'][:,j]
        if ok.any():
            mean=np.average(arrays['raw'][ok,j],weights=duration[ok]);std=np.sqrt(np.average((arrays['raw'][ok,j]-mean)**2,weights=duration[ok]));std=std if std>1e-8 else 1.
            require(np.allclose(arrays['z'][ok,j],(arrays['raw'][ok,j]-mean)/std,atol=1e-12,rtol=1e-12),'Independent source-only normalization')
    for index in sorted({0,len(c)//2,len(c)-1})if c else[]:
        p=c[index];indices=[i for i in range(p['left'],p['right'])if not b[i]];observed=[]
        for i in indices:
            if any(a<=pts[i]<z for a,z in intervals):observed.append(int(pts[i]*4))
        expected=np.zeros(8);expected[7]=len(observed)/len(indices)
        for j,col in [(0,0),(1,3),(2,5)]:
            values=[arrays['z'][v,j]for v in observed if arrays['valid'][v,j]]
            if values:
                expected[col]=np.mean(values)
                if j==0:expected[1]=np.std(values);expected[2]=max(values)
                else:expected[col+1]=max(values)
        require(np.allclose(features[index],expected,atol=1e-12,rtol=1e-12),'Independent actual-native-PTS audio proposal pooling')
    evidence_ref=manifest.get('evidence_ref')
    if evidence_ref:
        with gzip.open(bound(evidence_ref),'rt',encoding='utf8')as f:evidence=json.load(f)
        rows=evidence['resampled_frames']
        require(all(r['pts']is not None and F(r['normalized_start_exact'])==F(r['pts'])*F(r['time_base'])-F(manifest['original_video_pts0_exact'])for r in rows),'Actual resampler PTS alignment, not invented origin')
        require(len(rows)==manifest['raw_evidence']['resampled_frame_count'],'All actual resampled frame receipts retained')
    return dict(status='PASS_FIRST_AUDIO_NATIVE_DESCRIPTOR_QA',audio_observed=manifest['audio_observed'],no_audio=manifest['no_audio'],observed_seconds=float(sum((z-a for a,z in intervals),F(0))),physical_seconds=float(end),candidate_rows=len(c),mean_candidate_audio_coverage=None if not len(c)else float(features[:,7].mean()),z_valid_bins=arrays['valid'].sum(0).tolist())


def prepare():
    cpu();require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-18T14:00:00+00:00'),'Main cutoff')
    OUT.mkdir();folder=OUT/'audio_inputs_01';folder.mkdir();start=time.monotonic()
    reg=read(ROOT/'registration.json');sources=reg['sources'];pilot=['S05','V00','S18'];lookup={s['sid']:s for s in sources}
    ordered=[lookup[s]for s in pilot]+[s for s in sources if s['sid']not in pilot]
    save(OUT/'start.json',dict(protocol_ref=ref(ROOT/'event_audio_protocol_01.json'),adopted_source_lock_ref=ref(ROOT/'source_lock.json'),code={p.name:ref(p)for p in sorted(Path(__file__).parent.glob('*.py'))},fixed_pilot=pilot,new_video_decode=0,new_GPU=0,utc=utc()))
    receipts=[]
    for s in ordered:
        require(time.monotonic()-start<1800,'Registered audio-specific extraction wall budget')
        d=load_source(s);c,inputdata=adopted_input(s);clock=d['clock'];clock=dict(clock)
        media=Path(clock['source_path']);clock['source_bytes']=media.stat().st_size
        save(folder/(s['sid']+'_augmented_clock.json'),dict(clock=clock,original_clock_ref=s['clock_ref'],size_added_from_bound_current_media_stat=True,old_clock_unchanged=True))
        cache=extract_audio(media,clock,folder/s['sid']);features=proposal_audio_features(cache,clock,d['baseline'],c['candidates'])
        qa=independent_audio_qa(cache,clock,d['baseline'],c['candidates'],features)
        np.savez(folder/(s['sid']+'_proposals.npz'),x=features)
        save(folder/(s['sid']+'.json'),dict(sid=s['sid'],group=s['group'],input_ref=ref(folder/(s['sid']+'_proposals.npz')),manifest_ref=ref(folder/(s['sid']+'.manifest.json')),adopted_visual_ref=ref(ROOT/('train_inputs'if s['group']=='train'else'diagnostic_inputs')/(s['sid']+'.json')),audio_QA=qa))
        receipts.append(ref(folder/(s['sid']+'.json')));event('FIRST_AUDIO_DESCRIPTOR_QA',sid=s['sid'],**qa)
        if len(receipts)==3:save(OUT/'pilot3_completion.json',dict(status='PASS3_ACTUAL_AUDIO_EXTRACTION_FIRST_QA',sources=receipts.copy(),elapsed_seconds=time.monotonic()-start,remaining_sources=30,utc=utc()))
    save(OUT/'input_completion.json',dict(status='PASS33_ALL_FIRST_AUDIO_NATIVE_INPUTS',sources=receipts,elapsed_seconds=time.monotonic()-start,new_video_decode=0,new_GPU=0,utc=utc()))


def fit():
    cpu();require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-18T14:00:00+00:00'),'Main cutoff')
    require(read(OUT/'input_completion.json')['status']=='PASS33_ALL_FIRST_AUDIO_NATIVE_INPUTS','Every first audio input before model fit')
    old=dict(np.load(bound(read(ROOT/'frozen_selection.json')['weights_ref'])));xs=[];ys=[];weights=[];inputs=[]
    for s in read(ROOT/'registration.json')['sources']:
        if s['group']!='train':continue
        c,d=adopted_input(s);a=read(OUT/'audio_inputs_01'/(s['sid']+'.json'));ax=np.load(bound(a['input_ref']))['x']
        x=np.concatenate([d['x'],ax],1);require(x.shape[1]==110,'Actual102visual+8audio')
        if len(x):xs.append(x);ys.append(d['target']);weights.append(np.full(len(x),1/len(x)))
        inputs.append(ref(OUT/'audio_inputs_01'/(s['sid']+'.json')))
    x,y,w=np.concatenate(xs),np.concatenate(ys),np.concatenate(weights)
    mean=np.average(x,axis=0,weights=w);std=np.sqrt(np.average((x-mean)**2,axis=0,weights=w));std=np.where(std<1e-6,1.,std)
    z=np.column_stack([(x-mean)/std,np.ones(len(x))]);penalty=np.eye(111);penalty[-1,-1]=0.
    beta=np.linalg.solve(z.T@(w[:,None]*z)+penalty,z.T@(w*y))
    model={k:old[k]for k in ['pca_mean','pca_components','rho_train']};model.update(mean=mean,std=std,coef=beta[:110],bias=beta[110])
    np.savez(OUT/'model.npz',**model);restored=dict(np.load(OUT/'model.npz'));require(all(np.array_equal(restored[k],v)for k,v in model.items()),'Actual final audiovisual save/reload equality')
    save(OUT/'frozen_selection.json',dict(status='FROZEN_AUDIO_VISUAL_EVENT_QUALITY',weights_ref=ref(OUT/'model.npz'),input_completion_ref=ref(OUT/'input_completion.json'),protocol_ref=ref(ROOT/'event_audio_protocol_01.json'),source_lock_ref=ref(ROOT/'source_lock.json'),train_inputs=inputs,learned_tensor_scalars=sum(v.size for v in model.values()),feature_dimension=110,training_candidates=len(x),effective_sources=len(xs),ridge_total_source_mass=float(w.sum()),alpha=1.,code_ref=ref(Path(__file__)),first_diagnostic_scoring_not_yet_started=True,utc=utc()))


def evaluate():
    cpu();model=dict(np.load(bound(read(OUT/'frozen_selection.json')['weights_ref'])));items=[]
    for s in read(ROOT/'registration.json')['sources']:
        if s['group']!='check':continue
        d=load_source(s,True);r,v=adopted_input(s);a=read(OUT/'audio_inputs_01'/(s['sid']+'.json'));ax=np.load(bound(a['input_ref']))['x'];x=np.concatenate([v['x'],ax],1);c=r['candidates']
        idx,q,gains=rank(x,c,d['baseline'],model)
        action=None if idx is None else dict(sid=s['sid'],candidate_index=idx,added_frames=c[idx]['added_frames'],predicted_gain=float(gains[idx]))
        items.append(dict(d=d,c=c,q=q,gains=gains,action=action))
    selected=knapsack([v['action']for v in items if v['action']],sum(int(v['d']['baseline'].sum())for v in items)//10);rows=[]
    for v in items:
        d=v['d'];mask=d['baseline'].copy();idx=None
        if d['sid']in selected:idx=v['action']['candidate_index'];c=v['c'][idx];mask[c['left']:c['right']]=True
        b,n=metric(d['baseline'],d['labels']),metric(mask,d['labels']);added=mask&~d['baseline'];qtrue,_=targets(d['baseline'],d['labels'],v['c'])
        rows.append(dict(sid=d['sid'],baseline=b,candidate=n,delta=n['f1']-b['f1'],added_frames=int(added.sum()),chosen=None if idx is None else v['c'][idx],predicted_quality=None if idx is None else float(v['q'][idx]),true_quality=None if idx is None else float(qtrue[idx]),actual_added_rater_precision=None if not added.any()else float(d['labels'][added].mean()),historically_exposed=True))
        np.savez(OUT/(d['sid']+'_output.npz'),selected=mask,predicted_quality=v['q'],estimated_gain=v['gains'])
    summary=dict(sources=len(rows),macro_delta=float(np.mean([r['delta']for r in rows])),improved_sources=sum(r['delta']>0 for r in rows),decreased_sources=sum(r['delta']<0 for r in rows),changed_sources=sum(r['added_frames']>0 for r in rows),added_frames=sum(r['added_frames']for r in rows),worst_delta=min(r['delta']for r in rows),actual_added_seconds=sum(float(F(r['chosen']['added_duration_exact']))for r in rows if r['chosen']))
    save(OUT/'external_evaluation.json',dict(status='FROZEN_AUDIO_VISUAL_EXPOSED_DIAGNOSTIC_ONLY',summary=summary,sources=rows,no_new_blind_claim=True,no_retuning=True,utc=utc()))
    save(OUT/'completion.json',dict(status='COMPLETED_ONE_AUDIO_VISUAL_RESEARCH_MODEL',evaluation_ref=ref(OUT/'external_evaluation.json'),selection_ref=ref(OUT/'frozen_selection.json'),new_8B_calls=0,new_video_decode=0,production_started=False,utc=utc()))
    print(json.dumps(clean(summary)),flush=True)


if __name__=='__main__':
    try:{'prepare':prepare,'fit':fit,'evaluate':evaluate}[sys.argv[1]]()
    except BaseException as e:failure('event_audio_'+sys.argv[1],e);raise
