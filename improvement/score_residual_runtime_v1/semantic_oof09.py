"""Two preregistered semantic views, historical-reference source-isolated OOF."""
import sys
from common_runtime import *

def transform(language,yes_no,native,view):
    import numpy as np
    occupancy=np.array([native['baseline'][native['groups']==j].mean() for j in range(len(language))],np.float32)[:,None]
    if view=='D4':
        s=(yes_no[:,0]-yes_no[:,1]).astype(np.float32)
        delta=np.abs(s-np.r_[s[:1],s[:-1]])
        x=np.column_stack([np.clip(s,-32,32)/4,(s-s.mean())/max(1e-6,float(s.std())),delta/max(1e-6,float(np.sqrt(np.mean(delta.astype(np.float64)**2)))),(occupancy-occupancy.mean())[:,0]])
    elif view=='LM':
        v=language.astype(np.float32);center=v.mean(0,dtype=np.float64).astype(np.float32)
        scale=max(1e-6,float(np.sqrt(np.mean((v-center).astype(np.float64)**2))))
        local=np.stack([v[max(0,j-4):min(len(v),j+5)].mean(0) for j in range(len(v))])
        delta=np.abs(v-np.vstack([v[:1],v[:-1]]));ds=max(1e-6,float(np.sqrt(np.mean(delta.astype(np.float64)**2))))
        x=np.concatenate([(v-center)/scale,(local-center)/scale,delta/ds,occupancy-occupancy.mean()],1)
    else:raise ValueError('No unregistered head view')
    require(np.isfinite(x).all(),'Finite label-free source feature transform')
    return x.astype(np.float32)

def main():
    import numpy as np
    import torch
    from monotone_head06 import TrainingVideo,ResidualHead,train_head,native_prediction
    from score_residual_head_v1.contracts import build_contract
    torch.set_num_threads(2)
    proto=read(ROOT/'protocol.json');prior=Path(proto['prior_root'])
    require(read(ROOT/'completion.json')['status']=='PASS_ALL25_NEW_LANGUAGE_CONTEXT_FEATURES','Actual feature completion gate')
    require((ROOT/'chain_completion.json').exists(),'Unique wrapper must end naturally before CPU head training')
    out=ROOT/'semantic_oof09';out.mkdir(exist_ok=False)
    old_journal=[json.loads(x) for x in (prior/'journal.jsonl').read_text().splitlines() if x.strip()]
    examples={view:{} for view in ['D4','LM']};refs={};native={}
    for source in proto['sources']:
        sid=source['id'];n=np.load(prior/'inputs'/sid/'native.npz');native[sid]=n
        original=prior/'GT'/(source['name']+'.mat');labels=prior/'label_arrays'/(source['name']+'.npy')
        require(sha(original)==source['annotation_sha256'],'Original annotations identity')
        proof=[x for x in old_journal if x.get('stage')=='FIRST_NATIVE_HUMAN_MAT_READ' and x.get('path')==str(labels)]
        require(len(proof)==1 and sha(labels)==proof[0]['sha256'],'Adopt once-read original human label cache')
        scores=np.load(labels);require(scores.shape[0]==len(n['baseline']),'No label resampling')
        refs[sid]=scores>0
        fc=read(ROOT/'features'/sid/'completion.json');lp=ROOT/'features'/sid/'language.npy';yp=ROOT/'features'/sid/'yes_no.npy'
        require(sha(lp)==fc['language_sha256'] and sha(yp)==fc['yes_no_sha256'],'Actual semantic features identity')
        language=np.load(lp);yesno=np.load(yp)
        pieces=[];pairs=[]
        for ci,case in enumerate(read(ROOT/'inputs'/sid/'acceptance.json')['cases']):
            proof=read(ROOT/'features'/sid/('context_%04d.json'%ci));require(sha(proof['path'])==proof['sha256'],'Saved context forward identity')
            part=torch.load(proof['path'],map_location='cpu',weights_only=True)
            require(part['language'].shape==(case['queries'],4096) and part['yes_no'].shape==(case['queries'],2),'Actual per-query feature shape')
            require(bool(torch.isfinite(part['language']).all()) and bool(torch.isfinite(part['yes_no']).all()),'Independent finite new outputs')
            pieces.append(part['language'].numpy());pairs.append(part['yes_no'].numpy())
        require(np.array_equal(language,np.concatenate(pieces)) and np.array_equal(yesno,np.concatenate(pairs)),'Independent source concatenation/order')
        require(len(language)==len(yesno)==int(n['groups'].max())+1,'Complete original occupied cell mapping')
        c=build_contract(n['groups'].tolist(),n['baseline'].tolist(),refs[sid].mean(1).tolist(),len(language),read(prior/'inputs'/sid/'clock.json')['normalized_exact_pts'])
        counts=np.zeros((len(c.n),refs[sid].shape[1]),np.float32);np.add.at(counts,np.asarray(c.native_unit),refs[sid].astype(np.float32))
        for view in examples:examples[view][sid]=TrainingVideo(sid,torch.from_numpy(transform(language,yesno,n,view)),c,torch.from_numpy(counts))
    write(out/'independent_output_QA.json',dict(status='PASS_ALL7988_CONTEXT_OUTPUTS_AND_NATIVE_TARGET_MAPPING',source_count=25,new_8B_forward_calls=0,labels_only_in_head_objective=True))
    def metric(mask,sid):
        p=np.array(mask,dtype=bool);g=refs[sid];count=int(p.sum());inter=(g&p[:,None]).sum(0);gcount=g.sum(0)
        require(bool((gcount>0).all()),'Unexpected empty rater')
        return dict(f1=float((2*inter/(count+gcount)).mean()),precision=float((inter/max(1,count)).mean()),recall=float((inter/gcount).mean()),selected=count)
    results={}
    for view,videos in examples.items():
        dst=out/view;dst.mkdir();rows=[]
        for fold in range(5):
            train=[s['id'] for s in proto['sources'] if s['fold']!=fold];held=[s['id'] for s in proto['sources'] if s['fold']==fold]
            require(len(train)==20 and len(held)==5 and not set(train)&set(held),'Source isolated fitting')
            event('SEMANTIC_HEAD_FOLD_START',view=view,fold=fold)
            model,receipt=train_head([videos[x] for x in train],'SCORE',105,updates=100,hidden_dim=8,learning_rate=.003,margin=1.,score_weight=10.)
            weights=dst/('fold%d.pt'%fold);torch.save(model.state_dict(),weights)
            fold_rows=[]
            for sid in held:
                video=videos[sid]
                with torch.no_grad():mask=native_prediction(model(video.features),video.contract)
                b=metric(video.contract.baseline_native,sid);m=metric(mask,sid)
                row=dict(id=sid,fold=fold,baseline=b,candidate=m,delta=m['f1']-b['f1'],changed_frames=sum(x!=y for x,y in zip(mask,video.contract.baseline_native)))
                require(all(not b or p for b,p in zip(video.contract.baseline_native,mask)),'No original selected frame deleted')
                np.save(dst/(sid+'_native_prediction.npy'),np.array(mask,bool));fold_rows.append(row);rows.append(row)
            delta=float(np.mean([x['delta'] for x in fold_rows]));write(dst/('fold%d.json'%fold),dict(training=receipt,weights_sha256=sha(weights),sources=fold_rows,macro_delta=delta))
            event('SEMANTIC_HEAD_FOLD_DONE',view=view,fold=fold,macro_delta=delta)
        require(len(rows)==25 and len({x['id'] for x in rows})==25,'Complete OOF denominator')
        macro=float(np.mean([x['delta'] for x in rows]));folds=[float(np.mean([x['delta'] for x in rows if x['fold']==k])) for k in range(5)]
        worst=min(x['delta'] for x in rows);changed=sum(x['changed_frames']>0 for x in rows);empty=sum(x['candidate']['selected']==0 for x in rows)
        passed=macro>=.005 and min(folds)>=-.01 and worst>=-.10 and changed>=10 and empty<=5
        results[view]=dict(passed=passed,macro_delta=macro,fold_macro_deltas=folds,worst_source_delta=worst,changed_sources=changed,empty_sources=empty,sources=rows,head_parameters=model.parameter_count)
        write(dst/'result.json',results[view]);event('SEMANTIC_VIEW_COMPLETE',view=view,passed=passed,macro_delta=macro)
    selected=None
    if results['D4']['passed']:selected='D4'
    if results['LM']['passed'] and (selected is None or results['LM']['macro_delta']>=results['D4']['macro_delta']+.01):selected='LM'
    write(out/'selection.json',dict(selected=selected,views=results,scope=proto['scope'],new_optimizer_updates=1000))
    if selected is None:
        write(out/'result.json',dict(status='STOP_BOTH_SEMANTIC_VIEWS_OOF_REJECTED',new_production_allowed=False,new_optimizer_updates=1000,views=results));return
    videos=examples[selected];model,receipt=train_head([videos[s['id']] for s in proto['sources']],'SCORE',105,updates=100,hidden_dim=8,learning_rate=.003,margin=1.,score_weight=10.)
    weights=out/'final25.pt';torch.save(model.state_dict(),weights)
    restored=ResidualHead(next(iter(videos.values())).features.shape[1],8);restored.load_state_dict(torch.load(weights,weights_only=True))
    require(all(torch.equal(a,b) for a,b in zip(model.parameters(),restored.parameters())),'Actual selected final head save/reload')
    write(out/'final_training.json',receipt)
    write(out/'result.json',dict(status='PASS_FIXED_SEMANTIC_OOF_EXPLORATION_FINAL25_NO_POSTFIT_REFERENCE',new_production_allowed=True,selected_view=selected,weights_path=str(weights),weights_sha256=sha(weights),head_parameters=model.parameter_count,resident_parameters=8782459120+model.parameter_count,new_optimizer_updates=1100,views=results,scope=proto['scope'],production_scope=proto['production_scope']))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        import traceback
        write(ROOT/'semantic_oof09_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()));raise
