"""A frozen-prefix cache and paired last-stage updates within whole-source context."""
import json
import numpy as np
import torch
import torch.nn.functional as F

from qv_common47 import ROOT, checked, ref, save
from pilot15_gpu import fingerprint, training_logits
from runtime import score_features


def original_features(backbone, source):
    folder=ROOT/'features'/source['sid'];folder.mkdir()
    with np.load(checked(source['rgb']),allow_pickle=False) as data:
        rgb=data['rgb'].copy()
    prefixes=[];features=[]
    with torch.inference_mode():
        for first in range(0,len(rgb),8):
            x=torch.from_numpy(rgb[first:first+8]).permute(0,4,1,2,3).cuda().float()/255
            x=(x-.45)/.225
            for block in backbone.blocks[:5]:x=block(x)
            prefixes.append(x.cpu())
            feature=backbone.blocks[5](x).mean((2,3,4)).cpu().numpy()
            with (folder/f'initial_{first:04d}.npy').open('xb') as out:np.save(out,feature,allow_pickle=False)
            features.append(feature)
    values=np.concatenate(features)
    with (folder/'initial_all.npy').open('xb') as out:np.save(out,values,allow_pickle=False)
    save(folder/'acceptance.json',dict(input=source['rgb'],features=ref(folder/'initial_all.npy'),
        shape=list(values.shape),frozen_prefix_cache_bytes=sum(t.numel()*t.element_size() for t in prefixes)))
    return torch.cat(prefixes),torch.from_numpy(values).cuda()


def output(model, values, sid, condition):
    x=F.normalize(values.float(),dim=-1)[None]
    with torch.inference_mode():
        score=score_features(model,x,torch.ones(x.shape[:2],dtype=torch.bool,device=x.device))[0].cpu().numpy()
    with (ROOT/'outputs'/(sid+'_'+condition+'.npy')).open('xb') as out:np.save(out,score,allow_pickle=False)
    if score.shape!=(len(values),) or not np.isfinite(score).all():raise ValueError('Saved first scores invalid')


def source_examples(sources):
    return {s['sid']:[q for q in s['queries'] if q['pairs']]
            for s in sources if s['role']=='development' and any(q['pairs'] for q in s['queries'])}


def fit(backbone, model, sources, features, prefixes, protocol, arm):
    late=backbone.blocks[5]
    late.requires_grad_(arm=='late_visual')
    model.requires_grad_(True)
    groups=[dict(params=list(model.parameters()),lr=protocol['temporal_lr'])]
    if arm=='late_visual':groups.append(dict(params=list(late.parameters()),lr=protocol['visual_lr']))
    optimizer=torch.optim.AdamW(groups,weight_decay=1e-4)
    torch.manual_seed(protocol['seed']);rng=np.random.default_rng(protocol['seed'])
    examples=source_examples(sources);source_order=[];pair_positions={};losses=[];visual_gradient=[]
    model.train();backbone.eval()  # BN running statistics and the entire early visual prefix remain frozen.
    with (ROOT/(arm+'_training.jsonl')).open('x') as journal:
        for step in range(protocol['updates_per_arm']):
            if not source_order:source_order=list(rng.permutation(sorted(examples)))
            sid=str(source_order.pop());queries=examples[sid]
            q=queries[(step//len(examples))%len(queries)]
            cursor=pair_positions.get((sid,q['qid']),0);pair=q['pairs'][cursor%len(q['pairs'])]
            pair_positions[(sid,q['qid'])]=cursor+1
            ids=torch.tensor([pair['high'],pair['low']],device='cuda')
            values=features[sid].detach()
            if arm=='late_visual':
                # Reuse accepted frozen-prefix activations; only the paired late-stage cells carry gradient.
                activation=prefixes[sid][ids.cpu()].cuda().clone()
                local=late(activation).mean((2,3,4))
                values=values.index_copy(0,ids,local)
            x=F.normalize(values,dim=-1)[None]
            logits=training_logits(model,x)[0]
            delta=logits[ids[0]]-logits[ids[1]]
            target=(torch.tensor(pair['three_vote_differences'],device='cuda')+4)/8
            loss=F.binary_cross_entropy_with_logits(delta.expand(3),target)
            if not torch.isfinite(loss):raise ValueError('Nonfinite new preference loss')
            optimizer.zero_grad(set_to_none=True);loss.backward()
            if arm=='late_visual':
                norm=sum(float(p.grad.detach().abs().sum()) for p in late.parameters() if p.grad is not None)
                if not np.isfinite(norm) or norm<=0:raise ValueError('No actual late-visual gradient')
                visual_gradient.append(norm)
            torch.nn.utils.clip_grad_norm_([p for g in groups for p in g['params']],1.,error_if_nonfinite=True)
            optimizer.step();losses.append(float(loss.detach()))
            journal.write(json.dumps(dict(update=step+1,sid=sid,qid=q['qid'],
                high=pair['high'],low=pair['low'],loss=losses[-1]))+'\n');journal.flush()
    path=ROOT/(arm+'_final.pt')
    checkpoint=dict(temporal=model.state_dict(),late_visual=late.state_dict() if arm=='late_visual' else None,
                    arm=arm,updates=len(losses))
    torch.save(checkpoint,path)
    model.eval();probe=F.normalize(features[sorted(examples)[0]],dim=-1)[None]
    valid=torch.ones(probe.shape[:2],device='cuda',dtype=torch.bool)
    with torch.inference_mode():before=score_features(model,probe,valid).clone()
    late_before=fingerprint(late)
    restored=torch.load(path,map_location='cuda',weights_only=True)
    model.load_state_dict(restored['temporal'],strict=True)
    if arm=='late_visual':late.load_state_dict(restored['late_visual'],strict=True)
    if fingerprint(late)!=late_before:raise ValueError('Final late-visual save/reload differs')
    with torch.inference_mode():after=score_features(model,probe,valid)
    if not torch.equal(before,after):raise ValueError('Final temporal save/reload differs')
    save(ROOT/(arm+'_frozen.json'),dict(checkpoint=ref(path),updates=len(losses),training_sources=sorted(examples),
        prefix_unchanged=True,visual_gradient_steps=len(visual_gradient),save_reload_exact=True,
        first16_loss=float(np.mean(losses[:16])),last16_loss=float(np.mean(losses[-16:]))))
    return dict(arm=arm,updates=len(losses),visual_gradient_steps=len(visual_gradient))


def late_features(backbone, prefix):
    outputs=[]
    with torch.inference_mode():
        for first in range(0,len(prefix),8):
            outputs.append(backbone.blocks[5](prefix[first:first+8].cuda()).mean((2,3,4)))
    return torch.cat(outputs)
