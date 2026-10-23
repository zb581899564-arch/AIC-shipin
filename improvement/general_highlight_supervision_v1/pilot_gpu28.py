"""One fixed noncompetitive supervision intervention on the original frozen I3D inputs."""
from pathlib import Path
import sys
import time
import numpy as np
import torch
import torch.nn.functional as F

from pilot_common28 import ROOT,WORK,ENGINEERING,RUN,read,ref,save,checked,native_reference
from runtime import make_models,extract_rgb_features,score_features
from profile_gpu import load_authorized_backbone

OLD=WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16/code'
sys.path.insert(0,str(OLD))
from pilot15_gpu import fingerprint,training_logits


def extract(source,backbone):
    target=ROOT/'features'/source['sid'];target.mkdir()
    accepted=read(checked(source['input']));rgb=np.load(checked(accepted['rgb']),mmap_mode='r',allow_pickle=False)
    parts=[]
    for first in range(0,len(rgb),8):
        x=torch.from_numpy(rgb[first:first+8].copy()).permute(0,4,1,2,3).cuda().float()/255
        with torch.inference_mode():value=extract_rgb_features(backbone,(x-.45)/.225).cpu().numpy()
        with (target/f'batch_{first:04d}.npy').open('xb') as out:np.save(out,value,allow_pickle=False)
        if value.shape!=(len(x),2048) or not np.isfinite(value).all():raise ValueError('First I3D output invalid; raw kept')
        parts.append(value)
    values=np.concatenate(parts)
    with (target/'all.npy').open('xb') as out:np.save(out,values,allow_pickle=False)
    save(target/'acceptance.json',dict(features=ref(target/'all.npy'),input=source['input'],cells=len(values)))
    print('FEATURE_ACCEPTED',source['sid'],len(values),flush=True)
    return F.normalize(torch.from_numpy(values).cuda(),dim=-1)[None]


def output(model,x,sid,condition):
    valid=torch.ones(x.shape[:2],dtype=torch.bool,device=x.device)
    with torch.inference_mode():scores=score_features(model,x,valid).cpu().numpy()[0]
    with (ROOT/'outputs'/(sid+'_'+condition+'.npy')).open('xb') as out:np.save(out,scores,allow_pickle=False)
    if scores.shape!=(x.shape[1],) or not np.isfinite(scores).all():raise ValueError('First saved scores invalid')


def targets(sources,arrays):
    result=[]
    for source in sources:
        if source['role']!='development':continue
        labels,durations=native_reference(source)
        groups=np.load(checked(read(checked(source['input']))['groups']),allow_pickle=False)
        if not np.array_equal(groups,np.arange(len(labels))//64):raise ValueError('Native frame group changed')
        weights=np.bincount(groups,weights=durations)
        votes=labels.mean(axis=1)
        positive=np.bincount(groups,weights=durations*votes)
        y=(positive/weights).astype(np.float32)
        result.append((source['sid'],arrays[source['sid']],torch.from_numpy(y).cuda()[None],
            torch.from_numpy((weights/weights.sum()).astype(np.float32)).cuda()[None]))
    return result


def fit(model,examples,protocol):
    opt=torch.optim.AdamW(model.parameters(),lr=protocol['learning_rate'],weight_decay=1e-4)
    rng=np.random.default_rng(protocol['seed']);order=[];losses=[];model.train()
    with (ROOT/'training_journal.jsonl').open('x') as journal:
        for update in range(protocol['updates']):
            if not order:order=list(rng.permutation(len(examples)))
            sid,x,y,w=examples[order.pop()];opt.zero_grad(set_to_none=True)
            loss=(F.binary_cross_entropy_with_logits(training_logits(model,x),y,reduction='none')*w).sum()
            if not torch.isfinite(loss):raise ValueError('Nonfinite fixed preference loss')
            loss.backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
            if not float(norm)>0:raise ValueError('No real supervised gradient')
            opt.step();losses.append(float(loss.detach()))
            journal.write(__import__('json').dumps(dict(update=update+1,sid=sid,loss=losses[-1]))+'\n');journal.flush()
    return losses


def main():
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation();registration=read(ROOT/'registration.json');protocol=read(ROOT/'protocol.json')
    for record in read(ROOT/'source_input_lock.json')['code'].values():checked(record)
    for record in read(ROOT/'source_input_lock.json')['dependencies'].values():checked(record)
    torch.manual_seed(protocol['seed']);np.random.seed(protocol['seed']);torch.set_num_threads(2)
    started=time.monotonic();backbone,model,cfg=make_models(ENGINEERING)
    model.load_state_dict(torch.load(checked(registration['control_checkpoint']),map_location='cpu',weights_only=True)['model'],strict=True)
    model.cuda().eval();load_authorized_backbone(ENGINEERING,backbone);backbone.cuda().eval().requires_grad_(False)
    parameters=8782557449+sum(p.numel() for p in model.parameters())+sum(p.numel() for p in backbone.parameters())
    if parameters>9000000000:raise ValueError('Full production combination exceeds9B')
    frozen=fingerprint(backbone);(ROOT/'features').mkdir();(ROOT/'outputs').mkdir()
    sources=registration['sources'];arrays={s['sid']:extract(s,backbone) for s in sources}
    if fingerprint(backbone)!=frozen:raise ValueError('Frozen original I3D changed')
    del backbone;torch.cuda.empty_cache()
    for s in sources:output(model,arrays[s['sid']],s['sid'],'old_summary')
    # An already frozen sport-trained control, first inference on new sources only.
    model.load_state_dict(torch.load(checked(registration['sport_checkpoint']),map_location='cpu',weights_only=True)['model'],strict=True)
    for s in sources:output(model,arrays[s['sid']],s['sid'],'sport_control')
    model.load_state_dict(torch.load(checked(registration['control_checkpoint']),map_location='cpu',weights_only=True)['model'],strict=True)
    examples=targets(sources,arrays);losses=fit(model,examples,protocol)
    checkpoint=ROOT/'umt_noncompetitive_final.pt'
    torch.save(dict(model=model.state_dict(),config=cfg,updates=len(losses),seed=protocol['seed']),checkpoint)
    model.eval();x=examples[0][1];valid=torch.ones(x.shape[:2],dtype=torch.bool,device=x.device)
    with torch.inference_mode():before=score_features(model,x,valid).clone()
    model.load_state_dict(torch.load(checkpoint,map_location='cuda',weights_only=True)['model'],strict=True)
    with torch.inference_mode():after=score_features(model,x,valid)
    if not torch.allclose(before,after,atol=1e-7,rtol=1e-6):raise ValueError('Final save/reload differs')
    save(ROOT/'frozen_final.json',dict(checkpoint=ref(checkpoint),actual_updates=len(losses),
        training_sources=[row[0] for row in examples],no_held_source_in_loss=True,final_checkpoint_only=True,
        save_reload_pass=True,first20_loss=float(np.mean(losses[:20])),last20_loss=float(np.mean(losses[-20:]))))
    for s in sources:
        sid=s['sid'];x=arrays[sid]
        output(model,x,sid,'new_noncompetitive')
        output(model,torch.roll(x,x.shape[1]//2,dims=1),sid,'new_halfshift')
    for bridge in registration['external_bridge']:
        values=np.load(checked(bridge['feature']),allow_pickle=False)
        x=F.normalize(torch.from_numpy(values).cuda(),dim=-1)[None]
        sid=bridge['source']['sid']
        output(model,x,sid,'new_noncompetitive')
        output(model,torch.roll(x,x.shape[1]//2,dims=1),sid,'new_halfshift')
    checked(registration['protected_baseline'])
    save(ROOT/'gpu_completion.json',dict(state='NEW_FIXED_PREFERENCE_FIT_AND_OUTPUTS_COMPLETE',
        full_parameters=parameters,updates=len(losses),new8B_calls=0,new8B_updates=0,
        new_I3D_cells=sum(x.shape[1] for x in arrays.values()),
        saved_temporal_outputs=4*len(sources)+2*len(registration['external_bridge']),
        peak_allocated_bytes=torch.cuda.max_memory_allocated(),seconds=time.monotonic()-started))


if __name__=='__main__':main()
