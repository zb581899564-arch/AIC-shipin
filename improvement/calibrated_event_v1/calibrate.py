"""One source-balanced monotone probability field and plug-in event utility."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import datetime as dt,hashlib,json,sys,traceback
from pathlib import Path
import numpy as np

W=Path('/home/inspur/aic_video_work')
ROOT=W/'calibrated_event_20261018_v1'
EVENT=W/'meaningful_residual_20261018_v1'
SRC=W/'source_clear_residual_20261018_v1'
sys.path.insert(0,str(EVENT/'code_v1'))
from event_features import knapsack,metric


def require(ok,text):
    if not ok:raise ValueError(text)


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def bound(v):
    p=Path(v['path']);require(p.is_file()and sha(p)==v['sha256'],'Changed adopted artifact '+str(p));return p
def clean(v):
    if isinstance(v,dict):return {k:clean(x)for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x)for x in v]
    if isinstance(v,Path):return str(v)
    if hasattr(v,'item'):return v.item()
    return v
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8')as f:json.dump(clean(v),f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def deadline():
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-18T14:00:00+00:00'),'New main experiment cutoff reached')


def pava(score,target,weight):
    score,target,weight=map(lambda v:np.asarray(v,np.float64),(score,target,weight))
    require(score.ndim==target.ndim==weight.ndim==1 and len(score)==len(target)==len(weight)>0,'Aligned nonempty calibration inputs')
    require(np.isfinite(score).all()and np.isfinite(target).all()and np.isfinite(weight).all()and (weight>0).all()and np.all((target>=0)&(target<=1)),'Finite scores/positive weights/original reviewer vote probabilities')
    scores,inverse=np.unique(score,return_inverse=True)
    mass=np.bincount(inverse,weights=weight);positive=np.bincount(inverse,weights=weight*target)
    blocks=[]
    for i in range(len(scores)):
        blocks.append([i,i,float(mass[i]),float(positive[i])])
        while len(blocks)>1 and blocks[-2][3]/blocks[-2][2]>blocks[-1][3]/blocks[-1][2]:
            a,b=blocks[-2:];blocks[-2:]=[[a[0],b[1],a[2]+b[2],a[3]+b[3]]]
    values=np.asarray([v[3]/v[2]for v in blocks]);cuts=np.asarray([(scores[a[1]]+scores[b[0]])/2 for a,b in zip(blocks,blocks[1:])])
    require(np.all(np.diff(values)>=0)and np.all((values>=0)&(values<=1))and len(cuts)+1==len(values),'Monotone original weighted-block probabilities')
    return dict(cuts=cuts,values=values),dict(unique_scores=len(scores),blocks=len(blocks),total_source_mass=float(weight.sum()),weighted_prevalence=float(np.sum(weight*target)/weight.sum()))


def probability(scores,m):return m['values'][np.searchsorted(m['cuts'],np.asarray(scores),side='right')]


def gains(b,p,candidates):
    require(b.dtype==np.bool_ and p.shape==b.shape and np.isfinite(p).all()and np.all((p>=0)&(p<=1)),'Full native probability field')
    selected=int(b.sum());tp=float(p[b].sum());gt=float(p.sum());f0=0. if selected+gt==0 else 2*tp/(selected+gt)
    prefix=np.r_[0.,np.cumsum(p*(~b))];out=[]
    for c in candidates:
        added=prefix[c['right']]-prefix[c['left']];k=int(c['added_frames'])
        require(k==int((~b[c['left']:c['right']]).sum()),'Real unique native addition denominator')
        out.append(2*(tp+added)/(selected+k+gt)-f0)
    return np.asarray(out),dict(soft_tp=tp,soft_G=gt,soft_baseline_f1=f0)


def load_source(s,labels=True):
    d=np.load(bound(s['data_ref']));cpath=EVENT/('train_inputs'if s['group']=='train'else'diagnostic_inputs')/(s['sid']+'.json');c=read(cpath)
    baseline,groups,score=d['baseline'],d['groups'],d['semantic_score'];require(baseline.dtype==np.bool_ and len(baseline)==len(groups) and groups.min()==0 and groups.max()+1==len(score),'Adopted native semantic mapping')
    labels_data=d['labels']if labels else None
    if labels:require(labels_data.dtype==np.bool_ and labels_data.ndim==2 and len(labels_data)==len(baseline),'All original full-source human reviewers')
    return dict(sid=s['sid'],group=s['group'],baseline=baseline,groups=groups,score=score,labels=labels_data,candidates=c['candidates'],candidate_receipt=ref(cpath),descriptor=c)


def checks():
    m,a=pava([0,1,2],[1,0,1],[1,1,1]);require(np.array_equal(m['values'],[.5,1])and np.array_equal(m['cuts'],[1.5]),'Pool adjacent violations, not sorting labels')
    m,a=pava([0,0,1],[0,1,0],[1,3,4]);require(np.allclose(m['values'],[.375]),'Coalesce tied scores and preserve source weights')
    m,a=pava([0,1],[0,1],[1,1]);require(np.array_equal(probability([-10,0,.5,1,10],m),[0,0,1,1,1]),'Piecewise lookup endpoint extrapolation')
    b=np.array([1,1,0,0],bool);c=[dict(left=2,right=4,added_frames=2)]
    g,_=gains(b,np.array([1.,1.,0.,0.]),c);require(g[0]<0,'Confident unselected event permits successful null')
    g,_=gains(b,np.array([.1,.1,1.,1.]),c);require(g[0]>0,'High-probability new event can improve soft criterion')
    hard=np.array([1.,1.,0.,1.]);g,stats=gains(b,hard,c);direct=2*hard.sum()/(4+hard.sum())-2*hard[b].sum()/(2+hard.sum());require(abs(g[0]-direct)<1e-14,'Native soft count formula equals independent direct hard special case')
    bad=False
    try:pava([0],[1.1],[1])
    except ValueError:bad=True
    require(bad,'Invalid label cannot silently become probability or empty success')
    save(ROOT/'targeted_checks.json',dict(status='PASS7_TARGETED_MONOTONE_FIELD_NULL_AND_NATIVE_UTILITY_CHECKS',new_model_calls=0,utc=utc()))


def fit():
    deadline();require(not(ROOT/'model.npz').exists(),'One final calibration fit only')
    checks();reg=read(EVENT/'registration.json');xs=[];ys=[];weights=[];rho=[];rows=[]
    require(read(SRC/'original_human_label_adoption.json')['status']=='PASS25_ADOPTED_ORIGINAL_AUTHOR_HUMAN_LABEL_BYTES','Original author label bytes binding')
    for s in reg['sources']:
        if s['group']!='train':continue
        d=load_source(s);n=len(d['baseline']);groups=d['groups'];count=np.bincount(groups,minlength=len(d['score']));vote=d['labels'].mean(1)
        target=np.bincount(groups,weights=vote,minlength=len(count))/count;weight=count/n
        require(abs(weight.sum()-1)<1e-12,'Each full native source exactly one calibration weight unit')
        xs.append(d['score']);ys.append(target);weights.append(weight);rho.append(float(vote.mean()))
        rows.append(dict(sid=s['sid'],data_ref=s['data_ref'],candidate_ref=d['candidate_receipt'],native_frames=n,score_rows=len(count),reviewers=d['labels'].shape[1],source_weight=float(weight.sum())))
    require(len(rows)==25,'Fixed exactly25 public training sources')
    save(ROOT/'train_input_QA.json',dict(status='PASS25_FIRST_NEW_CALIBRATION_INPUTS',sources=rows,source_weight_total=25.,adopted_original_human_ref=ref(SRC/'original_human_label_adoption.json'),old_native_or_model_reexecution=0,utc=utc()))
    m,stats=pava(np.concatenate(xs),np.concatenate(ys),np.concatenate(weights));m['rho_train']=np.asarray(np.mean(rho))
    np.savez(ROOT/'model.npz',**m);restored=dict(np.load(ROOT/'model.npz'));require(all(np.array_equal(restored[k],v)for k,v in m.items()),'Final actual save/reload equality')
    save(ROOT/'frozen_selection.json',dict(status='FROZEN_ONE_MONOTONE_PROBABILITY_FIELD',weights_ref=ref(ROOT/'model.npz'),fit=stats,train_input_QA_ref=ref(ROOT/'train_input_QA.json'),protocol_ref=ref(ROOT/'protocol.json'),code_ref=ref(Path(__file__)),active_new_scalars=sum(v.size for v in restored.values()),constant_control_prevalence=float(restored['rho_train']),check_labels_not_read_by_fit=True,utc=utc()))


def evaluate():
    deadline();frozen=read(ROOT/'frozen_selection.json');m=dict(np.load(bound(frozen['weights_ref'])));items=[];reg=read(EVENT/'registration.json')
    oldcontrols={v['sid']:v for v in read(EVENT/'semantic_event_01/adopted_evaluation.json')['sources']}
    for s in reg['sources']:
        if s['group']!='check':continue
        d=load_source(s);p=probability(d['score'],m)[d['groups']];gain,stats=gains(d['baseline'],p,d['candidates']);constant,cstats=gains(d['baseline'],np.full(len(p),float(m['rho_train'])),d['candidates'])
        def action(values):
            if len(values)==0 or values.max()<=0:return None
            idx=int(values.argmax());return dict(sid=d['sid'],candidate_index=idx,added_frames=d['candidates'][idx]['added_frames'],predicted_gain=float(values[idx]))
        items.append(dict(d=d,p=p,gain=gain,stats=stats,action=action(gain),constant_action=action(constant),old=oldcontrols[d['sid']]))
    budget=sum(int(v['d']['baseline'].sum())for v in items)//10;selected=knapsack([v['action']for v in items if v['action']],budget);ctrl=knapsack([v['constant_action']for v in items if v['constant_action']],budget);rows=[];out=ROOT/'development_01';out.mkdir()
    for v in items:
        d=v['d'];mask=d['baseline'].copy();cmask=mask.copy();idx=None
        if d['sid']in selected:idx=v['action']['candidate_index'];c=d['candidates'][idx];mask[c['left']:c['right']]=True
        if d['sid']in ctrl:
            c=d['candidates'][v['constant_action']['candidate_index']];cmask[c['left']:c['right']]=True
        b,n,constant=metric(d['baseline'],d['labels']),metric(mask,d['labels']),metric(cmask,d['labels']);vote=d['labels'].mean(1);added=mask&~d['baseline']
        row=dict(sid=d['sid'],baseline=b,candidate=n,delta=n['f1']-b['f1'],added_frames=int(added.sum()),newframe_reviewer_precision=None if not added.any()else float(vote[added].mean()),chosen=None if idx is None else d['candidates'][idx],successful_source_null=v['action']is None,omitted_by_budget=v['action']is not None and d['sid']not in selected,positive_candidate_count=int((v['gain']>0).sum()),candidate_count=len(d['candidates']),soft_stats=v['stats'],brier=float(np.mean((v['p']-vote)**2)),constant_brier=float(np.mean((float(m['rho_train'])-vote)**2)),constant_control=constant,original_semantic_control=v['old']['candidate'],historically_exposed=True)
        rows.append(row);np.savez(out/(d['sid']+'_output.npz'),probability=v['p'],selected=mask,estimated_gain=v['gain'])
    summary=dict(sources=len(rows),macro_delta=float(np.mean([v['delta']for v in rows])),improved_sources=sum(v['delta']>0 for v in rows),decreased_sources=sum(v['delta']<0 for v in rows),changed_sources=sum(v['added_frames']>0 for v in rows),successful_source_nulls=sum(v['successful_source_null']for v in rows),added_frames=sum(v['added_frames']for v in rows),worst_delta=min(v['delta']for v in rows),macro_constant_control_delta=float(np.mean([v['constant_control']['f1']-v['baseline']['f1']for v in rows])),macro_original_semantic_delta=float(np.mean([v['original_semantic_control']['f1']-v['baseline']['f1']for v in rows])),macro_brier=float(np.mean([v['brier']for v in rows])),macro_constant_brier=float(np.mean([v['constant_brier']for v in rows])))
    save(ROOT/'development_evaluation.json',dict(status='ONE_FROZEN_CALIBRATION_EXPOSED8_DEVELOPMENT_ONLY',summary=summary,sources=rows,no_threshold_search=True,no_new_blind_claim=True,no_official_labels=True,utc=utc()))
    save(ROOT/'completion.json',dict(status='COMPLETED_ONE_CALIBRATION_RESEARCH_REVIEW_REQUIRED',selection_ref=ref(ROOT/'frozen_selection.json'),evaluation_ref=ref(ROOT/'development_evaluation.json'),new_GPU_calls=0,production_started=False,utc=utc()))
    print(json.dumps(clean(summary)),flush=True)


if __name__=='__main__':
    try:{'fit':fit,'evaluate':evaluate}[sys.argv[1]]()
    except BaseException as e:
        save(ROOT/('failure_'+sys.argv[1]+'_'+str(os.getpid())+'.json'),dict(error=repr(e),traceback=traceback.format_exc(),successes_preserved=True,utc=utc()));raise
