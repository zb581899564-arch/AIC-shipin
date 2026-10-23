"""First426 frozen I3D features and semantically gated expert outputs, saved before QA."""
import json
from pathlib import Path
import sys
import numpy as np
import torch
import torch.nn.functional as F
from routing_production60_common import ROOT,RUN,WORK,ENGINEERING,SPORT,FULL_PARAMETERS,CLASSES,read,ref,save,checked,activate_i3d


def main():
    activate_i3d()
    from runtime import make_models,extract_rgb_features,score_features
    from profile_gpu import load_authorized_backbone
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    sys.path.insert(0,str(SPORT/'code'));from pilot15_gpu import fingerprint
    verify_live_gpu_reservation();torch.set_num_threads(2)
    registration=read(ROOT/'registration.json');lock=read(ROOT/'source_input_lock.json')
    for identity in list(lock['code'].values())+list(lock['dependencies'].values()):checked(identity)
    cpu=read(ROOT/'CPU_completion.json')
    if len(cpu['accepted'])!=426:raise ValueError('All actual CPU inputs required before first model')
    backbone,expert,_=make_models(ENGINEERING);load_authorized_backbone(ENGINEERING,backbone)
    expert.load_state_dict(torch.load(checked(registration['expert_checkpoint']),map_location='cpu',weights_only=True)['model'],strict=True)
    backbone.cuda().eval().requires_grad_(False);expert.cuda().eval().requires_grad_(False)
    count=8782557449+sum(p.numel() for p in backbone.parameters())+sum(p.numel() for p in expert.parameters())
    if count!=FULL_PARAMETERS or count>9000000000:raise ValueError('Actual complete model parameter sum differs')
    before=(fingerprint(backbone),fingerprint(expert))
    names={k.strip('"'):v for k,v in read(checked(registration['class_names'])).items()}
    target={names[k] for k in CLASSES};inverse={v:k for k,v in names.items()}
    (ROOT/'outputs').mkdir();completed=[];cells=0;routed=0
    with (ROOT/'attempts.jsonl').open('x') as journal:
        for record in cpu['accepted']:
            source=read(checked(record));sid=source['video_id'];out=ROOT/'outputs'/sid;out.mkdir()
            rgb=np.load(checked(source['rgb']),mmap_mode='r',allow_pickle=False)
            if rgb.dtype!=np.uint8 or rgb.shape!=(source['cells'],8,224,224,3):raise ValueError('Actual accepted RGB input shape differs')
            values=[]
            for first in range(0,len(rgb),8):
                journal.write(json.dumps(dict(event='BEGIN_I3D',video_id=sid,first_cell=first))+'\n');journal.flush()
                x=torch.from_numpy(rgb[first:first+8].copy()).permute(0,4,1,2,3).cuda().float()/255
                with torch.inference_mode():features=extract_rgb_features(backbone,(x-.45)/.225).cpu().numpy()
                path=out/f'features_{first:04d}.npy'
                with path.open('xb') as handle:np.save(handle,features,allow_pickle=False)
                if features.shape!=(len(x),2048) or not np.isfinite(features).all():raise ValueError('First saved backbone output invalid')
                values.append(features);cells+=len(features)
                journal.write(json.dumps(dict(event='ACCEPTED_I3D',video_id=sid,first_cell=first,output=ref(path)))+'\n');journal.flush()
            values=np.concatenate(values)
            with (out/'features.npy').open('xb') as handle:np.save(handle,values,allow_pickle=False)
            with torch.inference_mode():
                tensor=torch.from_numpy(values).cuda()
                probabilities=F.linear(tensor,backbone.blocks[-1].proj.weight,backbone.blocks[-1].proj.bias).softmax(-1).cpu().numpy()
            with (out/'K400.npy').open('xb') as handle:np.save(handle,probabilities,allow_pickle=False)
            if (probabilities.shape!=(source['cells'],400) or not np.isfinite(probabilities).all()
                    or not np.allclose(probabilities.sum(1),1.,atol=2e-6,rtol=0)):
                raise ValueError('First saved semantic routing probability domain invalid')
            category=int(probabilities.mean(0).argmax());route=category in target;scores=None
            if route:
                journal.write(json.dumps(dict(event='BEGIN_UMT',video_id=sid))+'\n');journal.flush()
                with torch.inference_mode():
                    x=F.normalize(tensor,dim=-1)[None]
                    scores=score_features(expert,x,torch.ones(x.shape[:2],dtype=torch.bool,device=x.device)).cpu().numpy()[0]
                with (out/'expert.npy').open('xb') as handle:np.save(handle,scores,allow_pickle=False)
                if scores.shape!=(source['cells'],) or not np.isfinite(scores).all():raise ValueError('First saved expert output invalid')
                routed+=1;journal.write(json.dumps(dict(event='ACCEPTED_UMT',video_id=sid))+'\n');journal.flush()
            receipt=dict(video_id=sid,input=record,features=ref(out/'features.npy'),probabilities=ref(out/'K400.npy'),
                global_K400_top1=inverse[category],source_routed=route,
                expert=ref(out/'expert.npy') if route else None,default_preservation_when_not_routed=True,
                actual_new_I3D_cells=source['cells'],actual_new_expert_forward=int(route))
            save(out/'acceptance.json',receipt);completed.append(ref(out/'acceptance.json'))
            print('ROUTE426_MODEL_ACCEPTED',len(completed),426,flush=True)
            del rgb,values,tensor,probabilities
    if (fingerprint(backbone),fingerprint(expert))!=before:raise ValueError('Frozen inference model parameters changed')
    if len(completed)!=426 or cells!=cpu['cells']:raise ValueError('Complete formal model denominator differs')
    checked(registration['protected_baseline'])
    save(ROOT/'GPU_completion.json',dict(state='PASS_ALL426_FIRST_FROZEN_I3D_ROUTED_EXPERT_OUTPUTS',accepted=completed,
        source_count=426,I3D_cells=cells,routed_sources=routed,actual_full_parameters=count,
        frozen_model_fingerprints=list(before),new8B_calls=0,new_training=0,peak_allocated_bytes=torch.cuda.max_memory_allocated()))


if __name__=='__main__':main()
