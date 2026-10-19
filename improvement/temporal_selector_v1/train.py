"""Two final-only heads. Historical public summaries are a temporal proxy."""
import argparse
import math
import time
from pathlib import Path
from common import *
from mapping import merge_window_features


def assemble(scope):
    assert_cpu()
    import numpy as np
    import torch
    accepted=read(ROOT/('acceptance_'+scope+'.json'))
    phases=['pilot32','remaining_external'] if scope=='external' else ['production']
    qa_cases=[]
    for phase in phases:
        qa=read(ROOT/(phase+'_output_QA.json'))
        require(qa['status']=='PASS_ALL_FIRST_OUTPUT_QA_WITHOUT_NEW_FORWARD','First independent output QA gate')
        qa_cases.extend(qa['cases'])
    require(len(qa_cases)==len(set(qa_cases))==accepted['window_count'] and
            set(qa_cases)=={c['case_id'] for c in accepted['cases']}, 'No missing/repeated feature window')
    out=ROOT/('assembled_'+scope);out.mkdir(exist_ok=False)
    rows=[]
    for s in accepted['sources']:
        windows=[]
        for case in s['windows']:
            receipt=read(ROOT/('features_'+scope)/(case['case_id']+'.json'))
            value=torch.load(checked(receipt['features']),map_location='cpu',weights_only=True)
            require(value['source_sha256']==s['source_sha256'] and value['request_sha256']==case['request']['sha256'],
                    'Persisted source/window feature identity')
            windows.append((value['group_ids'].numpy(),value['features'].numpy()))
        means,counts=merge_window_features(windows,s['temporal_groups'])
        feature=out/(s['id']+'.npz')
        np.savez(feature,features=means.astype(np.float32),window_counts=counts,
                 native_group=np.load(checked(s['native_groups'])))
        rows.append(dict(id=s['id'],role=s['role'],features=reference(feature),
                         source_sha256=s['source_sha256'],clock=s['clock'],native=s['native'],
                         feature_dimension=int(means.shape[1]),groups=len(means),native_frames=s['native_frames'],
                         annotation_sha256=s.get('annotation_sha256'),name=s['name']))
    write(ROOT/('assembled_'+scope+'.json'),dict(status='PASS_UNIQUE_NATIVE_GROUPS_OVERLAP_MEAN',sources=rows,
          windows=accepted['window_count'],new_forwards=0,all_sources_native_length_unchanged=True))


def paired_metrics(mask,reference):
    import numpy as np
    mask=np.asarray(mask,dtype=bool);ref=np.asarray(reference,dtype=bool)
    p=int(mask.sum());g=ref.sum(0);intersection=(mask[:,None]&ref).sum(0)
    denominator=p+g
    score=np.divide(2*intersection,denominator,out=np.ones_like(g,dtype=float),where=denominator!=0)
    return dict(mean_paired_f1=float(score.mean()),selected=p,frames=len(mask),raters=ref.shape[1],
                coverage=float(mask.mean()),scope='AUTHOR_SUMMARY_TEMPORAL_PROXY_NO_SPATIAL_IOU')


def candidate_oracle(native_group,reference):
    """Per-reference constrained-group optima, a relaxed multi-rater upper bound.

    Each rater may choose a different group subset. Their mean is NOT an
    attainable common-output score and is never reported as a model result.
    """
    import numpy as np
    group=np.asarray(native_group);ref=np.asarray(reference);n=np.bincount(group)
    scores=[]
    for r in range(ref.shape[1]):
        c=np.bincount(group,weights=ref[:,r],minlength=len(n))
        ratio=c/n;order=np.argsort(-ratio,kind='stable')
        pc=np.cumsum(n[order]);tc=np.cumsum(c[order]);total=c.sum()
        possible=2*tc/(pc+total) if total>0 else np.zeros(len(n))
        scores.append(float(max(1.0 if total==0 else 0.0,possible.max(initial=0))))
    return dict(relaxed_mean_paired_upper_bound=float(np.mean(scores)),
                group_selection='Any subset of actual paired-observation native groups',
                relaxation='Different selected subset per original reviewer; not one attainable common selector',
                model_performance=False,spatial_iou_available=False)


def coverage_threshold(probabilities,native_groups,target):
    """One global cutoff from label-free dev coverage; never score optimized."""
    import numpy as np
    values=[];weights=[];sources=len(probabilities)
    for sid,p in probabilities.items():
        groups=native_groups[sid];counts=np.bincount(groups,minlength=len(p))
        values.extend(np.asarray(p,dtype=np.float64));weights.extend(counts/(len(groups)*sources))
    values=np.array(values);weights=np.array(weights);order=np.argsort(-values,kind='stable')
    values=values[order];weights=weights[order]
    ends=np.r_[np.flatnonzero(values[:-1]!=values[1:]),len(values)-1]
    thresholds=np.r_[math.nextafter(float(values[0]),math.inf),
                     [math.nextafter(float(values[e]),-math.inf) for e in ends]]
    coverage=np.r_[0.,np.cumsum(weights)[ends]]
    best=min(range(len(coverage)),key=lambda i:(abs(coverage[i]-target),-thresholds[i]))
    return float(thresholds[best]),float(coverage[best])


def train():
    assert_cpu()
    import numpy as np
    import torch
    from head import TrainingVideo,fit,predict,TemporalHead
    torch.set_num_threads(2)
    assembled=read(ROOT/'assembled_external.json')
    require(assembled['status']=='PASS_UNIQUE_NATIVE_GROUPS_OVERLAP_MEAN','Complete external feature assembly')
    sources=assembled['sources'];require(sum(s['role']=='train' for s in sources)==20 and sum(s['role']=='dev' for s in sources)==5,'Fixed20/5 source hash roles')
    samples={};references={};baseline={};groups={}
    old=EXTERNAL
    for s in sources:
        sid=s['id'];data=np.load(checked(s['features']))
        raw=old/'GT'/(s['name']+'.mat');labels=old/'label_arrays'/(s['name']+'.npy')
        require(sha(raw)==s['annotation_sha256'],'Original author annotation bytes changed')
        journal=[json.loads(x) for x in (old/'journal.jsonl').read_text().splitlines() if x.strip()]
        proofs=[x for x in journal if x.get('stage')=='FIRST_NATIVE_HUMAN_MAT_READ' and x.get('path')==str(labels)]
        require(len(proofs)==1 and sha(labels)==proofs[0]['sha256'],'Original once-read annotation array identity')
        reference=np.load(labels)>0
        require(reference.ndim==2 and reference.shape[0]==s['native_frames']==len(data['native_group']), 'No annotation resampling, padding or truncation')
        samples[sid]=data['features'].copy();groups[sid]=data['native_group'].copy();references[sid]=reference
        baseline[sid]=np.load(checked(s['native']))['baseline'].copy()
    train_ids=[s['id'] for s in sources if s['role']=='train'];dev_ids=[s['id'] for s in sources if s['role']=='dev']
    pool=np.concatenate([samples[sid] for sid in train_ids])
    mean=pool.mean(0,dtype=np.float64).astype(np.float32);std=pool.std(0,dtype=np.float64).astype(np.float32)
    std=np.maximum(std,1e-4)
    del pool
    out=ROOT/'training';out.mkdir(exist_ok=False)
    np.savez(out/'normalization.npz',mean=mean,std=std)
    videos={sid:TrainingVideo(sid,torch.from_numpy(((x-mean)/std).astype(np.float32)),
                             torch.from_numpy(groups[sid]),torch.from_numpy(references[sid])) for sid,x in samples.items()}
    diagnostics={sid:dict(baseline=paired_metrics(baseline[sid],references[sid]),
                         candidate_oracle=candidate_oracle(groups[sid],references[sid])) for sid in videos}
    write(out/'candidate_coverage_diagnostic.json',dict(sources=diagnostics,historical_exposure=True,
          baseline_scope='Saved external original B0, not a claimed full VERIFY40.47 replica',new_model_calls=0))
    target=float(np.mean([baseline[sid].mean() for sid in dev_ids]));results=[]
    frozen=8782557449 # conservatively include the original semantic head retained in the protected baseline lineage
    for arm in ('BCE','SET'):
        one=time.monotonic();model,report=fit([videos[sid] for sid in train_ids],arm,seed=105,updates=200,
              hidden=128,learning_rate=1e-3,frozen_parameters=frozen)
        path=out/(arm+'.pt');torch.save(model.state_dict(),path)
        restored=TemporalHead(model.feature_dim,128);restored.load_state_dict(torch.load(path,map_location='cpu',weights_only=True));restored.eval()
        require(all(torch.equal(x,y) for x,y in zip(model.parameters(),restored.parameters())),'Actual final head save/reload')
        probabilities={sid:predict(restored,v.features).numpy() for sid,v in videos.items()}
        dev={sid:probabilities[sid] for sid in dev_ids}
        require(float(np.std(np.concatenate(list(dev.values()))))>1e-7,'STOP_CONSTANT_OUTPUT_NO_NEW_TIME_SELECTION_MECHANISM')
        threshold,coverage=coverage_threshold(dev,{sid:groups[sid] for sid in dev_ids},target)
        metrics={sid:paired_metrics(probabilities[sid][groups[sid]]>threshold,references[sid]) for sid in dev_ids}
        report.update(weights=reference(path),normalization=reference(out/'normalization.npz'),
                      threshold=threshold,coverage_target=target,actual_dev_coverage=coverage,
                      threshold_selection='Nearest equal-source original external B0 coverage, no reference-score search',
                      dev_metrics=metrics,dev_sources=dev_ids,all25_historically_exposed=True,
                      independent_confirmation=False,new_fivefold=False,proxy_effect_gate=False,seconds=time.monotonic()-one)
        write(out/(arm+'_completion.json'),report);results.append(reference(out/(arm+'_completion.json')))
        event('FINAL_TIME_HEAD_TRAINED',arm=arm,updates=200,parameters=model.parameter_count,seconds=report['seconds'])
    write(ROOT/'training_completion.json',dict(status='TWO_FINAL_TIME_HEADS_FROZEN_UNKNOWN_OFFICIAL_EFFECT',arms=results,
          sources=25,train_sources=20,dev_sources=5,new_cpu_optimizer_updates=400,backbone_updates=0,
          no_new_human_annotation=True,no_new_fivefold=True,proxy_effect_gate=False))


def apply_production():
    assert_cpu()
    import numpy as np
    import torch
    from head import TemporalHead,predict
    torch.set_num_threads(2)
    assembled=read(ROOT/'assembled_production.json')
    require(len(assembled['sources'])==426,'All426 actual production features required')
    done=read(ROOT/'training_completion.json');out=ROOT/'selections';out.mkdir(exist_ok=False)
    results=[]
    for arm_ref in done['arms']:
        reg=read(checked(arm_ref));arm=reg['arm'];dst=out/arm;dst.mkdir()
        normalization=np.load(checked(reg['normalization']));model=TemporalHead(reg['feature_dim'],reg['hidden'])
        model.load_state_dict(torch.load(checked(reg['weights']),map_location='cpu',weights_only=True));model.eval()
        rows=[]
        for s in assembled['sources']:
            value=np.load(checked(s['features']));features=torch.from_numpy(((value['features']-normalization['mean'])/normalization['std']).astype(np.float32))
            probability=predict(model,features).numpy();group=value['native_group'];selected=probability[group]>reg['threshold']
            require(selected.dtype==np.bool_ and len(selected)==s['native_frames'] and np.isfinite(probability).all(), 'Actual complete native selection')
            p=dst/(s['id']+'.npz');np.savez(p,group_probability=probability,native_group=group,selected_native=selected)
            # Independent output replay from persisted scores and exact ownership.
            replay=np.load(p)
            require(np.array_equal(replay['selected_native'],replay['group_probability'][replay['native_group']]>reg['threshold']), 'Independent persisted native selection replay')
            rows.append(dict(id=s['id'],status='ACCEPTED_EMPTY' if not selected.any() else 'ACCEPTED',
                   source_sha256=s['source_sha256'],clock=s['clock'],features=s['features'],output=reference(p),
                   native_frames=len(selected),selected_frames=int(selected.sum())))
        completion=dict(status='PASS_ALL426_NEW_TIME_HEAD_NATIVE_REPLAY',arm=arm,head=arm_ref,
                        actual_resident_parameters=reg['resident_parameters'],sources=rows,invalid_outputs=0,
                        empty_sources=sum(r['status']=='ACCEPTED_EMPTY' for r in rows),new_model_forwards=0)
        p=dst/'completion.json';write(p,completion);results.append(reference(p))
    write(ROOT/'selection_completion.json',dict(status='PASS_BOTH_COMPLETE_NATIVE_TIME_SELECTIONS',arms=results))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['assemble','train','apply']);parser.add_argument('--scope',choices=['external','production'])
    args=parser.parse_args()
    if args.stage=='assemble':assemble(args.scope)
    elif args.stage=='train':train()
    else:apply_production()
