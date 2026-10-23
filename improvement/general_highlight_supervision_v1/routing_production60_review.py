"""Independent first CPU arithmetic and all426 native policy replay; no backbone rerun."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import hashlib
import zipfile
import json
import numpy as np
import torch
import torch.nn.functional as F
from routing_production60_common import ROOT,WORK,ENGINEERING,SPORT,FULL_PARAMETERS,CLASSES,read,ref,save,checked,activate_i3d


def baseline_masks(assets, baseline):
    with zipfile.ZipFile(checked(baseline)) as archive:
        rows=[json.loads(line) for line in archive.read('predictions.jsonl').splitlines() if line.strip()]
    by_id={row['video_id']:row for row in rows};masks={}
    for source in assets['sources']:
        sid=source['video_id'];mask=np.zeros(source['native_frames'],dtype=bool)
        ids=[p['frame'] for p in by_id[sid]['predictions']]
        if len(ids)!=len(set(ids)) or any(type(i)is not int or not 0<=i<len(mask) for i in ids):
            raise ValueError('Protected actual baseline frame domain invalid')
        mask[ids]=True;masks[sid]=mask
    return masks


def field_domains(assets):
    domains={s['video_id']:np.zeros(s['native_frames'],dtype=bool) for s in assets['sources']}
    identity=assets['field_files']['field_frames.jsonl']['identity']
    with checked(identity).open() as source:
        for line in source:
            row=json.loads(line);sid=row['video_id'];frame=row['source_frame']
            if sid not in domains or type(frame)is not int or not 0<=frame<len(domains[sid]):
                raise ValueError('Frozen field point outside complete native domain')
            if domains[sid][frame]:raise ValueError('Duplicate frozen source field point')
            domains[sid][frame]=True
    return domains


def main():
    torch.set_num_threads(2);activate_i3d()
    from runtime import make_models,score_features
    from profile_gpu import load_authorized_backbone
    registration=read(ROOT/'registration.json');assets=read(checked(registration['assets']))
    primary=read(ROOT/'GPU_completion.json')
    if primary['source_count']!=426 or primary['actual_full_parameters']!=FULL_PARAMETERS:
        raise ValueError('Actual complete model inference gate differs')
    backbone,expert,_=make_models(ENGINEERING);load_authorized_backbone(ENGINEERING,backbone)
    expert.load_state_dict(torch.load(checked(registration['expert_checkpoint']),map_location='cpu',weights_only=True)['model'],strict=True)
    expert.eval().requires_grad_(False)
    names={k.strip('"'):v for k,v in read(checked(registration['class_names'])).items()};targets={names[k] for k in CLASSES}
    baseline=baseline_masks(assets,registration['protected_baseline']);domains=field_domains(assets)
    (ROOT/'selections').mkdir();receipts=[];routed=0
    for identity in primary['accepted']:
        row=read(checked(identity));sid=row['video_id'];source=read(checked(row['input']))
        features=np.load(checked(row['features']),allow_pickle=False);probs=np.load(checked(row['probabilities']),allow_pickle=False)
        if features.shape!=(source['cells'],2048):raise ValueError('Actual pooled feature denominator differs')
        with torch.inference_mode():
            replay=F.linear(torch.from_numpy(features),backbone.blocks[-1].proj.weight,backbone.blocks[-1].proj.bias).softmax(-1).numpy()
        if not np.allclose(replay,probs,atol=2e-6,rtol=1e-4):raise ValueError('Independent classifier arithmetic differs')
        route=int(probs.mean(0).argmax()) in targets
        if route!=row['source_routed']:raise ValueError('Native semantic route differs')
        groups=np.load(checked(source['groups']),allow_pickle=False)
        if not np.array_equal(groups,np.arange(len(baseline[sid]))//64):raise ValueError('Independent original native grouping differs')
        old=baseline[sid];rerank=old.copy();remove=old.copy()
        if not np.all(domains[sid][old]):raise ValueError('A protected baseline frame has no accepted spatial field')
        if route:
            scores=np.load(checked(row['expert']),allow_pickle=False)
            with torch.inference_mode():
                x=F.normalize(torch.from_numpy(features),dim=-1)[None]
                replay_score=score_features(expert,x,torch.ones(x.shape[:2],dtype=torch.bool)).numpy()[0]
            if not np.allclose(replay_score,scores,atol=2e-5,rtol=1e-4) or not np.array_equal(replay_score>=.5,scores>=.5):
                raise ValueError('First independent CPU expert replay or intrinsic binary decision differs')
            allowed=np.flatnonzero(domains[sid]);count=int(old.sum())
            rerank[:]=False;rerank[allowed[np.argsort(-scores[groups[allowed]],kind='stable')[:count]]]=True
            remove=old & (scores[groups]>=.5);routed+=1
        path=ROOT/'selections'/(sid+'.npz')
        with path.open('xb') as out:np.savez_compressed(out,baseline=old,source_rerank=rerank,source_remove=remove)
        if int(rerank.sum())!=int(old.sum()) or np.any(remove & ~old):raise ValueError('Frozen policy selected wrong counts or added to removal arm')
        receipt=dict(video_id=sid,selection=ref(path),source_routed=route,
            baseline_frames=int(old.sum()),rerank_frames=int(rerank.sum()),remove_frames=int(remove.sum()),
            rerank_changed=int(np.logical_xor(rerank,old).sum()),removed=int((old&~remove).sum()),
            nonrouted_exact_identity=bool(np.array_equal(old,rerank) and np.array_equal(old,remove)) if not route else None,
            bbox_domain_excludes_frames=int((~domains[sid]).sum()),native_frames=len(old))
        receipts.append(receipt);print('ROUTE426_CPU_OUTPUT_ACCEPTED',len(receipts),426,flush=True)
    if len(receipts)!=426:raise ValueError('Independent full426 denominator differs')
    save(ROOT/'selection_acceptance.json',dict(state='PASS_ALL426_NATIVE_ROUTING_POLICY_OUTPUTS',sources=receipts,
        baseline_frames=sum(r['baseline_frames'] for r in receipts),rerank_frames=sum(r['rerank_frames'] for r in receipts),
        remove_frames=sum(r['remove_frames'] for r in receipts),routed_sources=routed,
        source_rerank_changed=sum(r['rerank_changed'] for r in receipts),source_remove_removed=sum(r['removed'] for r in receipts),
        actual_full_parameters=FULL_PARAMETERS,no_labels_or_manual_test_edits=True,
        independent_classifier_and_expert_CPU_replay=True,no_backbone_rerun=True,
        source_field_domain_predeclared=True,legal_empty_in_remove_arm_allowed=True))
    checked(registration['protected_baseline'])


if __name__=='__main__':main()
