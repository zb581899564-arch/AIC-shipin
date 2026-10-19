"""One cached-feature CPU experiment, no automatic production or GPU work."""
from event_common import *
from event_features import *
import time


def sources():
    reg = read(SRC/'registration.json')
    context = {s['sid']:s for s in read(SRC/'gpu_completion.json')['context_sources']}
    out = []
    for s in reg['sources']:
        sid = s['sid']
        language = bound(s['language_ref']) if s['group'] == 'train' else bound(context[sid]['language_ref'])
        out.append(dict(sid=sid,group=s['group'],name=s['name'],clock_ref=ref(SRC/'inputs'/sid/'clock.json'),data_ref=ref(SRC/'external'/sid/'data.npz'),language_ref=ref(language)))
    require(sum(s['group']=='train' for s in out)==25 and len(out)==33,'Exactly25train+8 exposed diagnostic sources')
    return out


def load_source(s, labels=False):
    p = np.load(bound(s['data_ref']))
    clock = read(bound(s['clock_ref']))
    baseline,groups = p['baseline'],p['groups']
    language = np.load(bound(s['language_ref']))
    score = p['semantic_score']
    require(baseline.dtype==np.bool_ and len(baseline)==len(groups)==len(clock['normalized_exact_pts']),'Adopted full baseline/native clock')
    require(language.shape==(len(score),4096) and np.isfinite(language).all() and np.isfinite(score).all(),'Accepted full4096/semantic feature denominator')
    bins = np.asarray([int(F(x)*2) for x in clock['normalized_exact_pts']],np.int64)
    _,compressed = np.unique(bins,return_inverse=True)
    require(np.array_equal(compressed,groups),'Exact original occupied2Hz bucket mapping')
    d = dict(sid=s['sid'],group=s['group'],clock=clock,baseline=baseline,groups=groups,language=language,score=score)
    if labels:
        d['labels'] = p['labels']
        require(d['labels'].dtype==np.bool_ and len(d['labels'])==len(baseline),'Original full-source rater domain')
    return d


def raw_input_adoption():
    require(not(ROOT/'registration.json').exists(),'Unique raw-input adoption')
    require(read(SRC/'output_qa.json')['status']=='PASS_FIRST_INDEPENDENT_ALL_EXTERNAL_TOKEN_CONTEXT_REPLAY','Adopt completed external real outputs/QA')
    require(read(SRC/'original_human_label_adoption.json')['status']=='PASS25_ADOPTED_ORIGINAL_AUTHOR_HUMAN_LABEL_BYTES','Original author human labels required')
    require(read(ROOT/'official_primary_02/receipt.json')['new_attachment_bytes_identical_to_full_read'],'Current official rules binding')
    src=sources()
    save(ROOT/'registration.json',dict(sources=src,adopted_raw_input_QA=ref(SRC/'input_qa.json'),adopted_raw_output_QA=ref(SRC/'output_qa.json'),original_human_adoption_ref=ref(SRC/'original_human_label_adoption.json'),baseline_ref=read(SRC/'registration.json')['baseline'],protocol_ref=ref(ROOT/'protocol.json'),clarification_ref=ref(ROOT/'protocol_clarification_01.json'),new_GPU_calls=0,utc=utc()))
    rows=[]
    for s in src:
        d=load_source(s)
        rows.append(dict(sid=s['sid'],group=s['group'],native_frames=len(d['baseline']),feature_rows=len(d['language']),baseline_frames=int(d['baseline'].sum())))
    save(ROOT/'raw_feature_input_QA.json',dict(status='PASS_ALL33_FIRST_NEW_DESCRIPTOR_RAW_INPUT_ADOPTION',sources=rows,diagnostic_labels_read=False,new_media_decode=0,new_processor=0,new_GPU=0,utc=utc()))
    event('RAW_FEATURE_INPUT_ADOPTION_PASS',sources=33)


def descriptor_qa(d,c,x,pca):
    require(x.shape==(len(c),102),'All new descriptor rows mapped')
    pts=list(map(F,d['clock']['normalized_exact_pts']));p=projected(d['language'],pca);baseline=d['baseline'];seen=set()
    for row in c:
        a,b=F(row['start_exact']),F(row['end_exact']);l,r=row['left'],row['right']
        require(l==bisect_left(pts,a) and r==bisect_left(pts,b),'Actual exact native half-open membership')
        indices=np.flatnonzero(~baseline[l:r])+l
        require(len(indices)==row['added_frames'] and tuple(indices) not in seen,'Unique real native addition action')
        seen.add(tuple(indices))
        require(F(row['added_duration_exact'])>=2 and F(row['longest_new_run_exact'])>=1,'Actual multi-second new action, not only envelope')
    # Independent scalar means/std for representative first/middle/final rows.
    for i in sorted({0,len(c)//2,len(c)-1}) if c else []:
        row=c[i];idx=np.flatnonzero(~baseline[row['left']:row['right']])+row['left'];v=p[d['groups'][idx]]
        require(np.allclose(v.mean(0),x[i,:32],atol=1e-10,rtol=1e-10),'Independent native weighted mean')
        require(np.allclose(v.std(0),x[i,64:96],atol=1e-9,rtol=1e-9),'Independent native population std')
    return dict(candidates=len(c),actual_new_duration_min=None if not c else str(min(F(v['added_duration_exact'])for v in c)))


def prepare():
    cpu()
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-18T14:00:00+00:00'),'No new main experiment after fallback reserve cutoff')
    raw_input_adoption()
    reg=read(ROOT/'registration.json');train=[load_source(s,True)for s in reg['sources']if s['group']=='train']
    pca,singular=weighted_pca(train)
    np.savez(ROOT/'pca.npz',**pca)
    save(ROOT/'pca_fit.json',dict(train_sources=[d['sid']for d in train],source_mass=1,total_source_mass=25,components=32,seed=20261018,singular_values=singular.tolist(),pca_ref=ref(ROOT/'pca.npz'),diagnostic_or_formal_fit=False))
    folder=ROOT/'train_inputs';folder.mkdir();receipts=[]
    for d in train:
        c=proposals(d['clock'],d['baseline']);x=descriptors(d['language'],d['score'],d['groups'],d['clock'],d['baseline'],pca,c)
        q,gain=targets(d['baseline'],d['labels'],c);audit=descriptor_qa(d,c,x,pca)
        np.savez(folder/(d['sid']+'.npz'),x=x,target=q,true_delta=gain)
        save(folder/(d['sid']+'.json'),dict(sid=d['sid'],candidates=c,input_ref=ref(folder/(d['sid']+'.npz')),descriptor_QA=audit))
        receipts.append(ref(folder/(d['sid']+'.json')))
        event('TRAIN_DESCRIPTOR_FIRST_QA',sid=d['sid'],candidates=len(c))
    save(ROOT/'train_descriptor_input_QA.json',dict(status='PASS25_ALL_FIRST_NATIVE_EVENT_DESCRIPTOR_INPUTS',sources=receipts,all_exact_quality_identities=True,no_diagnostic_labels_in_fit=True,utc=utc()))
    save(ROOT/'source_lock.json',dict(registration_ref=ref(ROOT/'registration.json'),raw_QA_ref=ref(ROOT/'raw_feature_input_QA.json'),train_descriptor_QA_ref=ref(ROOT/'train_descriptor_input_QA.json'),pca_ref=ref(ROOT/'pca.npz'),code={p.name:ref(p)for p in sorted((ROOT/'code_v1').glob('*.py'))},utc=utc()))


def fit():
    cpu();lock=read(ROOT/'source_lock.json')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-18T14:00:00+00:00'),'No new main-model fit after fallback reserve cutoff')
    for v in lock['code'].values():bound(v)
    require(read(bound(lock['train_descriptor_QA_ref']))['status']=='PASS25_ALL_FIRST_NATIVE_EVENT_DESCRIPTOR_INPUTS','First new train input QA before ridge')
    require(not(ROOT/'model.npz').exists(),'One fit only, final checkpoint only')
    xs=[];ys=[];weights=[];rhos=[];effective=[];zero=[]
    reg=read(ROOT/'registration.json')
    for s in reg['sources']:
        if s['group']!='train':continue
        r=read(ROOT/'train_inputs'/(s['sid']+'.json'));d=np.load(bound(r['input_ref']));x,y=d['x'],d['target']
        raw=np.load(bound(s['data_ref']));rhos.append(float(raw['labels'].mean()))
        if len(x):
            xs.append(x);ys.append(y);weights.append(np.full(len(x),1/len(x)));effective.append(s['sid'])
        else:zero.append(s['sid'])
    require(len(rhos)==25 and xs,'All25 training sources, nonempty eligible training actions')
    x=np.concatenate(xs);y=np.concatenate(ys);w=np.concatenate(weights)
    mean=(w[:,None]*x).sum(0)/w.sum();std=np.sqrt((w[:,None]*(x-mean)**2).sum(0)/w.sum());std=np.where(std<1e-6,1.,std)
    z=np.column_stack([(x-mean)/std,np.ones(len(x))]);penalty=np.eye(103);penalty[-1,-1]=0.
    beta=np.linalg.solve(z.T@(w[:,None]*z)+penalty,z.T@(w*y))
    require(np.isfinite(beta).all(),'One finite closed-form signed-quality ridge')
    model={**dict(np.load(bound(lock['pca_ref']))), 'mean':mean,'std':std,'coef':beta[:102],'bias':beta[102],'rho_train':np.asarray(np.mean(rhos))}
    np.savez(ROOT/'model.npz',**model);restored=dict(np.load(ROOT/'model.npz'))
    require(all(np.array_equal(v,restored[k])for k,v in model.items()),'Actual final tensor save/reload equality')
    save(ROOT/'frozen_selection.json',dict(status='FROZEN_ONE_EVENT_SIGNED_QUALITY_HEAD',weights_ref=ref(ROOT/'model.npz'),source_lock_ref=ref(ROOT/'source_lock.json'),learned_tensor_scalars=sum(v.size for v in restored.values()),registered_train_sources=25,effective_ridge_train_sources=effective,zero_candidate_train_sources=zero,ridge_total_source_mass=float(w.sum()),source_weight_per_eligible=1.,PCA_and_rho_sources=25,diagnostic_sources=8,alpha=1.,feature_dim=102,risk_budget_fraction='1/10',max_actions_per_source=1,proposal_seconds=[2,4,8],minimum_actual_added_seconds=2,minimum_contiguous_new_seconds=1,q_clip=[-.5,1.],seed=20261018,first_diagnostic_scoring_not_yet_started=True,utc=utc()))
    event('ONE_EVENT_HEAD_FROZEN',training_candidates=len(x),learned_scalars=sum(v.size for v in restored.values()))


def actions_for(d,c,x,model):
    best,q,gain=rank(x,c,d['baseline'],model)
    raw=((x-model['mean'])/model['std'])@model['coef']+float(model['bias'])
    action=None if best is None else dict(sid=d['sid'],candidate_index=best,added_frames=c[best]['added_frames'],predicted_gain=float(gain[best]))
    # Fixed original-semantic ordering, same candidate set/indivisible budget.
    control=None
    if c:
        idx=int(np.argmax(x[:,96]));control=dict(sid=d['sid'],candidate_index=idx,added_frames=c[idx]['added_frames'],predicted_gain=float(1/(1+np.exp(-np.clip(x[idx,96],-30,30)))))
    return action,control,q,gain,dict(min=None if not len(raw)else float(raw.min()),max=None if not len(raw)else float(raw.max()),outside_mathematical_range=int(((raw<-.5)|(raw>1)).sum()))


def evaluate():
    cpu();selection=read(ROOT/'frozen_selection.json');model=dict(np.load(bound(selection['weights_ref'])));reg=read(ROOT/'registration.json');data=[]
    folder=ROOT/'diagnostic_inputs';folder.mkdir()
    for s in reg['sources']:
        d=load_source(s,True)
        if s['group']=='train':
            r=read(ROOT/'train_inputs'/(s['sid']+'.json'));v=np.load(bound(r['input_ref']));c,x=r['candidates'],v['x']
        else:
            c=proposals(d['clock'],d['baseline']);x=descriptors(d['language'],d['score'],d['groups'],d['clock'],d['baseline'],model,c);audit=descriptor_qa(d,c,x,model)
            np.savez(folder/(d['sid']+'.npz'),x=x)
            save(folder/(d['sid']+'.json'),dict(candidates=c,descriptor_QA=audit,input_ref=ref(folder/(d['sid']+'.npz')),weights_frozen_ref=ref(ROOT/'frozen_selection.json')))
        action,control,q,gains,raw=actions_for(d,c,x,model)
        data.append(dict(d=d,c=c,x=x,action=action,control=control,q=q,gains=gains,raw=raw))
    rows=[]
    for group in ['train','check']:
        items=[x for x in data if x['d']['group']==group];budget=sum(int(x['d']['baseline'].sum())for x in items)//10
        selected=knapsack([x['action']for x in items if x['action']],budget)
        controls=knapsack([x['control']for x in items if x['control']],budget)
        for item in items:
            d=item['d'];mask=d['baseline'].copy();controlmask=mask.copy();chosen=None
            if d['sid']in selected:
                chosen=item['action']['candidate_index'];c=item['c'][chosen];mask[c['left']:c['right']]=True
            if d['sid']in controls:
                c=item['c'][item['control']['candidate_index']];controlmask[c['left']:c['right']]=True
            b,n,ctrl=metric(d['baseline'],d['labels']),metric(mask,d['labels']),metric(controlmask,d['labels']);added=mask&~d['baseline']
            qtrue,gtrue=targets(d['baseline'],d['labels'],item['c'])
            spec=None if chosen is None else item['c'][chosen]
            rows.append(dict(sid=d['sid'],group=group,candidates=len(item['c']),baseline=b,candidate=n,delta=n['f1']-b['f1'],semantic_order_control=ctrl,chosen=spec,added_frames=int(added.sum()),actual_added_rater_precision=None if not added.any()else float(d['labels'][added].mean()),predicted_quality=None if chosen is None else float(item['q'][chosen]),true_quality=None if chosen is None else float(qtrue[chosen]),raw_quality_range=item['raw'],historically_exposed=True))
            np.savez(folder/(d['sid']+'_output.npz'),selected=mask,predicted_quality=item['q'],estimated_gain=item['gains'])
        require(sum(r['added_frames']for r in rows if r['group']==group)<=budget,'Actual group exposure guard')
    summary={}
    for group in ['train','check']:
        v=[r for r in rows if r['group']==group]
        summary[group]=dict(sources=len(v),macro_delta=float(np.mean([r['delta']for r in v])),improved_sources=sum(r['delta']>0 for r in v),decreased_sources=sum(r['delta']<0 for r in v),changed_sources=sum(r['added_frames']>0 for r in v),added_frames=sum(r['added_frames']for r in v),worst_delta=min(r['delta']for r in v),control_macro_delta=float(np.mean([r['semantic_order_control']['f1']-r['baseline']['f1']for r in v])),actual_added_seconds=sum(float(F(r['chosen']['added_duration_exact']))for r in v if r['chosen']))
    save(ROOT/'external_evaluation.json',dict(status='FROZEN_EVENT_LEVEL_DEVELOPMENT_DIAGNOSTIC_NOT_OFFICIAL_SCORE',summary=summary,sources=rows,no_new_blind_claim=True,no_retuning=True,no_new_fivefold=True,utc=utc()))
    event('EVENT_LEVEL_FROZEN_DIAGNOSTIC_COMPLETE',summary=summary)
    save(ROOT/'development_completion.json',dict(status='ONE_CPU_EVENT_METHOD_DONE_MAIN_REVIEW_REQUIRED_BEFORE_PRODUCTION',evaluation_ref=ref(ROOT/'external_evaluation.json'),selection_ref=ref(ROOT/'frozen_selection.json'),new_GPU_calls=0,new_media_decode=0,utc=utc()))


if __name__=='__main__':
    try:
        stage=sys.argv[1]
        {'prepare':prepare,'fit':fit,'evaluate':evaluate}[stage]()
    except BaseException as error:
        failure('event_'+sys.argv[1],error)
        raise
