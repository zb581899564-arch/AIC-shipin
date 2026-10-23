"""One fixed old-to-new-supervision fit, first outputs saved before review."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
import torch.nn.functional as F

from pilot15_common import ROOT, ENGINEERING, read, checked, ref, save, native_cells, original_targets
from runtime import make_models, extract_rgb_features, score_features
from profile_gpu import load_authorized_backbone


def fingerprint(model):
    digest=hashlib.sha256()
    for name,value in sorted(model.state_dict().items()):
        digest.update(name.encode());digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def features(source,backbone):
    target=ROOT/'features'/source['source'];target.mkdir()
    accepted=read(ROOT/'inputs'/source['source']/'acceptance.json')
    rgb=np.load(checked(accepted['rgb']),mmap_mode='r',allow_pickle=False)
    parts=[]
    for first in range(0,len(rgb),8):
        clips=torch.from_numpy(rgb[first:first+8].copy()).permute(0,4,1,2,3).cuda().float()/255
        with torch.inference_mode():
            values=extract_rgb_features(backbone,(clips-.45)/.225).cpu().numpy()
        path=target/f'batch_{first:04d}.npy'
        with path.open('xb') as handle:np.save(handle,values,allow_pickle=False)
        if values.shape!=(len(clips),2048) or not np.isfinite(values).all():
            raise ValueError('First feature output invalid; raw retained')
        parts.append(values)
    array=np.concatenate(parts)
    with (target/'all.npy').open('xb') as handle:np.save(handle,array,allow_pickle=False)
    save(target/'acceptance.json',dict(features=ref(target/'all.npy'),cells=len(array),
        input_acceptance=ref(ROOT/'inputs'/source['source']/'acceptance.json')))
    print('FEATURE_ACCEPTED',source['source'],len(array),flush=True)
    return F.normalize(torch.from_numpy(array).cuda(),dim=-1)[None]


def write_scores(model,x,source,condition):
    valid=torch.ones(x.shape[:2],dtype=torch.bool,device=x.device)
    with torch.inference_mode():value=score_features(model,x,valid).cpu().numpy()[0]
    path=ROOT/'outputs'/(source+'_'+condition+'.npy')
    with path.open('xb') as handle:np.save(handle,value,allow_pickle=False)
    if value.shape!=(x.shape[1],) or not np.isfinite(value).all():
        raise ValueError('First temporal output invalid, raw retained')
    return value


def training_logits(model,x):
    mask=torch.ones(x.shape[:2],dtype=torch.long,device=x.device)
    encoded=model.video_enc(x,mask=mask)
    query=model.query_gen(encoded,None)
    decoded=model.query_dec(query,encoded)
    if len(decoded)!=1 or len(model.pred_head)!=1:raise ValueError('Unexpected original UMT structure')
    return model.pred_head[0].saliency_pred(decoded[0]).squeeze(-1)


def train(model,arrays,sources,protocol):
    tensors=[]
    for source in sources:
        if source['role']!='development':continue
        labels=original_targets(source);bounds,_,_=native_cells(len(labels))
        counts=np.asarray([(labels[a:b]>=0).sum() for a,b in bounds],dtype=np.float32)
        positives=np.asarray([(labels[a:b]==1).sum() for a,b in bounds],dtype=np.float32)
        targets=np.divide(positives,counts,out=np.zeros_like(positives),where=counts>0)
        if counts.sum()<=0:raise ValueError('No known native training labels')
        tensors.append((source['source'],arrays[source['source']],
            torch.from_numpy(targets).cuda()[None],torch.from_numpy(counts/counts.sum()).cuda()[None]))
    if len(tensors)!=3:raise ValueError('Frozen source roles changed')
    opt=torch.optim.AdamW(model.parameters(),lr=protocol['learning_rate'],weight_decay=1e-4)
    rng=np.random.default_rng(protocol['seed']);order=[];losses=[]
    model.train()
    with (ROOT/'training_journal.jsonl').open('x') as log:
        for update in range(protocol['updates']):
            if not order:order=list(rng.permutation(len(tensors)))
            stem,x,y,weights=tensors[order.pop()];opt.zero_grad(set_to_none=True)
            loss=(F.binary_cross_entropy_with_logits(training_logits(model,x),y,reduction='none')*weights).sum()
            if not torch.isfinite(loss):raise ValueError('Nonfinite first fit')
            loss.backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
            if not float(norm)>0:raise ValueError('No real gradients')
            opt.step();losses.append(float(loss.detach()))
            log.write(json.dumps(dict(update=update+1,source=stem,loss=losses[-1]))+'\n');log.flush()
    return tensors,losses


def main():
    import sys
    sys.path.insert(0,'/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1')
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    registration=read(ROOT/'registration.json');protocol=read(ROOT/'protocol.json')
    lock=read(ROOT/'source_input_lock.json')
    for value in list(lock['code'].values())+list(lock['adopted_old_code'].values()):checked(value)
    torch.manual_seed(protocol['seed']);np.random.seed(protocol['seed']);torch.set_num_threads(2)
    started=time.monotonic();backbone,model,cfg=make_models(ENGINEERING)
    control=checked(registration['control_checkpoint'])
    state=torch.load(control,map_location='cpu',weights_only=True)
    model.load_state_dict(state['model'],strict=True);model.cuda().eval()
    counts=dict(I3D=sum(p.numel() for p in backbone.parameters()),UMT=sum(p.numel() for p in model.parameters()))
    counts['complete_with_protected_base']=8782557449+sum(counts.values())
    if counts['complete_with_protected_base']>9000000000:raise ValueError('Complete parameters exceed9B')
    load_authorized_backbone(ENGINEERING,backbone);backbone.cuda().eval().requires_grad_(False)
    frozen=fingerprint(backbone);(ROOT/'features').mkdir();(ROOT/'outputs').mkdir()
    sources=registration['sources'];arrays={source['source']:features(source,backbone) for source in sources}
    if fingerprint(backbone)!=frozen:raise ValueError('Frozen I3D changed')
    del backbone;torch.cuda.empty_cache()
    for source in sources:write_scores(model,arrays[source['source']],source['source'],'old_summary')
    tensors,losses=train(model,arrays,sources,protocol)
    checkpoint=ROOT/'umt_matched_HL_final.pt'
    torch.save(dict(model=model.state_dict(),config=cfg,updates=len(losses),seed=protocol['seed']),checkpoint)
    model.eval();first=tensors[0][1]
    with torch.inference_mode():before=score_features(model,first,torch.ones(first.shape[:2],dtype=torch.bool,device='cuda')).clone()
    model.load_state_dict(torch.load(checkpoint,map_location='cuda',weights_only=True)['model'],strict=True)
    with torch.inference_mode():after=score_features(model,first,torch.ones(first.shape[:2],dtype=torch.bool,device='cuda'))
    if not torch.allclose(before,after,atol=1e-7,rtol=1e-6):raise ValueError('Final saved/reloaded output differs')
    save(ROOT/'frozen_final.json',dict(checkpoint=ref(checkpoint),updates=len(losses),
        train_sources=[item[0] for item in tensors],held_source_in_loss=False,
        final_checkpoint_only=True,save_reload_pass=True,first20_loss=float(np.mean(losses[:20])),
        final20_loss=float(np.mean(losses[-20:]))))
    for source in sources:
        stem=source['source'];x=arrays[stem]
        write_scores(model,x,stem,'matched_HL')
        write_scores(model,torch.roll(x,x.shape[1]//2,dims=1),stem,'matched_halfshift')
    checked(registration['protected_baseline']);checked(registration['control_checkpoint'])
    save(ROOT/'gpu_completion.json',dict(state='FIRST_FEATURES_FIT_AND_OUTPUTS_COMPLETE',parameters=counts,
        new_features=sum(x.shape[1] for x in arrays.values()),old_control_not_rerun_on_old_sources=True,
        new_temporal_outputs=12,updates=len(losses),I3D_frozen_fingerprint=frozen,
        base_TIME_updates=0,no_automatic_production=True,seconds=time.monotonic()-started,
        peak_allocated_bytes=torch.cuda.max_memory_allocated()))


if __name__=='__main__':main()
