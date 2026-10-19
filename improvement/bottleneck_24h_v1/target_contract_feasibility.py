"""New native-target representability statistics only; no training admission."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import pathlib,json,hashlib,datetime as dt
from fractions import Fraction as Q
from bisect import bisect_left
from collections import Counter
import numpy as np
W=pathlib.Path('/home/inspur/aic_video_work');ROOT=W/'bottleneck_24h_20261019_v1'
def read(p):return json.loads(pathlib.Path(p).read_text())
def ref(p):
    p=pathlib.Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def bound(r):
    p=pathlib.Path(r['path']);a=ref(p);assert a['sha256']==r['sha256'] and ('bytes' not in r or a['bytes']==r['bytes']);return p
def save(p,x):
    with pathlib.Path(p).open('x') as s:json.dump(x,s,ensure_ascii=False,indent=2,allow_nan=False)
def runs(mask):
    changes=np.diff(np.r_[False,mask,False].astype(np.int8));return list(zip(np.flatnonzero(changes==1),np.flatnonzero(changes==-1)))
def serialize(mask,points,start,end):
    assert len(mask)==len(points) and all(start<=p<end for p in points)
    intervals=[]
    for lo,hi in runs(mask):
        left=start if lo==0 else (points[lo-1]+points[lo])/2
        right=end if hi==len(points) else (points[hi-1]+points[hi])/2
        pair=[float(format(float(left-start),'.6f')),float(format(float(right-start),'.6f'))]
        assert 0<=Q(str(pair[0]))<Q(str(pair[1]))<=end-start
        intervals.append(pair)
    text=json.dumps({'segments':intervals},separators=(',',':'),allow_nan=False)
    parsed=json.loads(text);back=np.zeros(len(mask),bool)
    for a,b in parsed['segments']:
        a,b=start+Q(str(a)),start+Q(str(b));back|=np.asarray([a<=p<b for p in points])
    assert np.array_equal(back,mask),'No added/removed native labels from serialization'
    return text,len(intervals)
def self_check():
    points=list(map(Q,['0','33/1000','67/1000','1/10','133/1000']))
    for values in [[0,0,0,0,0],[1,1,1,1,1],[0,1,0,1,0],[1,0,0,0,1]]:
        serialize(np.array(values,bool),points,Q(0),Q('167/1000'))
def main():
    self_check();reg=read(ROOT/'target_feasibility_registration_02.json');source_reg=read(bound(reg['prior_registration_ref']));sources={s['sid']:s for s in source_reg['sources'] if s['group']=='train'}
    assert len(sources)==25;out=ROOT/'target_contract_02';out.mkdir();cache={};rows=[];hist=Counter();targets=[]
    for window in source_reg['windows']:
        sid=window['sid']
        if sid not in sources:continue
        s=sources[sid];m=window['meta'];assert m['source_sha256']==s['media']['sha256'] and m['source_name']==s['name']
        if sid not in cache:
            clock=read(bound(s['clock_ref']));labels=np.load(bound(s['labels_ref']),allow_pickle=False)>0;points=list(map(Q,clock['normalized_exact_pts']))
            assert labels.ndim==2 and len(labels)==len(points)==m['source_total_frames'] and points[0]==0
            cache[sid]=(clock,labels,points)
        clock,labels,points=cache[sid];start=Q(m['window_start']);end=Q(m['window_end']);lo=bisect_left(points,start);hi=bisect_left(points,end)
        assert 0<=start<end<=Q(clock['physical_end_exact']) and lo<hi
        target_counts=[]
        for reviewer in range(labels.shape[1]):
            text,count=serialize(labels[lo:hi,reviewer],points[lo:hi],start,end);target_counts.append(count);hist[count]+=1
            targets.append(dict(uid=window['uid'],sid=sid,reviewer=reviewer,segments_count=count,target_json=text,native_range=[lo,hi],window_start_exact=str(start),window_end_exact=str(end),target_semantics='ONE_ORIGINAL_REVIEWER_SOURCE_SUMMARY_SELECTION_NOT_NO_HIGHLIGHT',source_labels_ref=s['labels_ref'],source_clock_ref=s['clock_ref']))
        rows.append(dict(uid=window['uid'],sid=sid,source_name=s['name'],start_exact=str(start),end_exact=str(end),native_frames=hi-lo,reviewers=labels.shape[1],max_runs=max(target_counts),empty_reviewers=target_counts.count(0),original_RGB_cache_exists=pathlib.Path(m['frame_array_path']).exists()))
    assert len(cache)==25 and len(rows)==144
    with (out/'candidate_targets_not_training_admitted.jsonl').open('x') as stream:
        for row in targets:stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
    result=dict(status='COMPLETE_FIRST_NATIVE_TARGET_CONTRACT_FEASIBILITY_NO_TRAINING_ADMISSION',sources=25,windows=len(rows),reviewer_window_targets=len(targets),run_count_histogram={str(k):hist[k] for k in sorted(hist)},max_native_runs=max(hist),targets_exceed_original_max5=sum(v for k,v in hist.items() if k>5),empty_targets=hist[0],empty_semantics='Reviewer did not include excerptframes in fullsource summary; NOT no worthwhilecontent/ordinary/UNKNOWN',serialization='Sixdecimal boundaries strictlyinside neighboringnativePTS gaps;allactualnativeframe labels exactlyroundtrip,no truncation/padding/stretching',windows_detail=rows,candidate_targets_ref=ref(out/'candidate_targets_not_training_admitted.jsonl'),new_decoder_calls=0,new_processor_calls=0,new_model_calls=0,new_optimizer_updates=0,old_targets_or_QA_repeated=False,training_admitted=False,GPU_admitted=False,missing_contracts=['Sourceoverview+excerpt matchedinput','Finaltaskprompt accepting source-summarynonselection distinctfrom nohighlight','Sameinput frozeninit baseline','Actualinput+cost+gradient/save-reload acceptance before training'],registration_ref=ref(ROOT/'target_feasibility_registration_02.json'),utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(out/'result.json',result);print(json.dumps({k:result[k] for k in ['status','sources','windows','reviewer_window_targets','run_count_histogram','max_native_runs','targets_exceed_original_max5','empty_targets','training_admitted']}))
if __name__=='__main__':main()
