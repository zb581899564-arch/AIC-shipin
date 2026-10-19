"""Fixed readonly utility policy, preserving all original native coordinates."""
import math
import numpy as np


def require(value,message):
    if not value:raise ValueError(message)


def choose(gains):
    gains=np.asarray(gains,dtype=np.float64)
    require(gains.ndim==1 and len(gains)>0 and np.isfinite(gains).all() and gains[0]==0.,'Finite complete gains with BASE0')
    return max(range(len(gains)),key=lambda i:(float(gains[i]),i==0,-i))


def policy_predictions(sources,pairs,values,beta,old_gain,old_geometry,geometry):
    beta=np.asarray(beta,dtype=np.float64);rms=np.asarray(old_gain['RMS'],dtype=np.float64)
    gb=np.asarray(old_gain['GEOM11_beta'],dtype=np.float64);old_geometry=np.asarray(old_geometry,dtype=np.float64)
    require(beta.shape==gb.shape==(11,) and rms.shape==(14,) and (rms>0).all() and old_geometry.shape==(13,),
        'Frozen exact geometry states')
    require(all(np.isfinite(x).all() for x in (beta,rms,gb,old_geometry)),'Finite frozen states')
    require(len({s['source_id'] for s in sources})==len(sources),'Unique complete source set')
    by_source={s['source_id']:[] for s in sources}
    for p in pairs:
        require(p['source_id'] in by_source,'Unexpected pair source outside scope')
        by_source[p['source_id']].append(p)
    outputs=[];used=set();selfzero=0
    for s in sources:
        sid=s['source_id'];pool=s['pool'];g=np.stack([geometry(b,s['width'],s['height']) for b in pool]);delta=(g-g[0])[:,1:12]
        visual=np.full(len(pool),np.nan);owners={}
        for p in by_source[sid]:
            i=p['candidate_index'];require(type(i)==int and i not in owners and 0<=i<len(pool),'Complete unique candidate owner')
            f,r=values[p['first_id']],values[p['reverse_id']]
            require(all(x['source_id']==sid and x['source_sha256']==s['source_sha256'] for x in (f,r)),'Actual source/raw ownership')
            require((i==0 and p['same_crop'] is True and p['first_id']==p['reverse_id']) or
                (i>0 and p['same_crop'] is False and p['first_id']!=p['reverse_id']),'Exact self and double-order comparisons')
            visual[i]=.5*(float(f['CPU_value'])-float(r['CPU_value']));owners[i]=(p['first_id'],p['reverse_id']);used.update(owners[i])
        require(set(owners)==set(range(len(pool))) and np.isfinite(visual).all(),'No missing candidate silently abstains')
        gains=dict(UTILITY=visual+delta@beta,UTILITY_BETA_GEOMETRY=delta@beta,
            OLD47_GEOM11=(delta/rms[3:])@gb,OLD33_GEOM13=g@old_geometry)
        gains['OLD33_GEOM13']-=gains['OLD33_GEOM13'][0]
        require(all(v[0]==0. for v in gains.values()) and np.array_equal(-visual+(-delta)@beta,-gains['UTILITY']),
            'Actual fixed policy exact selfzero/swap sign')
        selfzero+=1;choices={a:choose(v) for a,v in gains.items()}
        outputs.append(dict(source_id=sid,source_sha256=s['source_sha256'],choices=choices,
            predicted_gains={a:v.tolist() for a,v in gains.items()},native_boxes=pool,
            selected_native_box=pool[choices['UTILITY']],raw_pair_owners={str(k):list(v) for k,v in owners.items()}))
    require(used==set(values),'Every accepted ordered value consumed exactly in full pool')
    return outputs,dict(sources=len(sources),selfzero=selfzero,invalid=0,unknown_missing=0)


def evaluate(sources,predictions,targets,proof,policy):
    n=len(sources);require(n in (19,20) and len(predictions)==n and proof['selfzero']==n and proof['invalid']==0,'Fixed complete19/20 scope')
    gt={t['source_id']:t for t in targets};require(set(gt)=={s['source_id'] for s in sources},'Exact unmodified reference set')
    rows={a:[] for a in ('UTILITY','UTILITY_BETA_GEOMETRY','OLD47_GEOM11','OLD33_GEOM13')}
    for s,p in zip(sources,predictions):
        t=gt[s['source_id']];truth=np.asarray(t['candidate_ious'],dtype=np.float64)
        require(s['source_id']==p['source_id'] and t['source_sha256']==s['source_sha256']
            and t['reference_modified'] is False and t['baseline_index']==0 and s['baseline_box']==s['pool'][0]
            and truth.shape==(len(s['pool']),) and np.isfinite(truth).all() and ((truth>=0)&(truth<=1)).all(),
            'Original native pool/reference/source unchanged')
        gi=p['choices']['OLD33_GEOM13']
        for arm in rows:
            i=p['choices'][arm];rows[arm].append(dict(source_id=s['source_id'],source_sha256=s['source_sha256'],
                baseline_iou=float(truth[0]),selected_iou=float(truth[i]),geometry_iou=float(truth[gi]),oracle_iou=float(truth.max()),
                baseline_index=0,selected_index=i,geometry_index=gi))
    summaries={a:policy.summarize(v) for a,v in rows.items()};u=summaries['UTILITY'];mean=u['mean_selected_iou']
    worst=min(r['selected_iou']-r['baseline_iou'] for r in rows['UTILITY'])
    gates=dict(mean_gain_at_least_point01=mean>=u['mean_baseline_iou']+.01,
        at_least5_sources_improve=sum(r['selected_iou']>r['baseline_iou'] for r in rows['UTILITY'])>=5,
        every_source_loss_at_most_point1=worst>=-.1,
        actual_change=any(r['selected_index']!=0 for r in rows['UTILITY']),invalid0=proof['invalid']==0,
        selfzero_complete=proof['selfzero']==n,
        beats_own_beta_geometry=mean>summaries['UTILITY_BETA_GEOMETRY']['mean_selected_iou'],
        beats_frozen47_geometry=mean>summaries['OLD47_GEOM11']['mean_selected_iou'],
        beats_frozen33_geometry=mean>summaries['OLD33_GEOM13']['mean_selected_iou'])
    return dict(summaries=summaries,per_source=rows,predictions=predictions,
        quality=dict(admitted=all(gates.values()),gates={k:bool(v) for k,v in gates.items()}),
        observed_sources=n,historical_not_blind=True,official_joint_quality=False)
