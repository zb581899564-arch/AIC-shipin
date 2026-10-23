"""Exactly two frozen final arms; real last-stage visual gradients, no 8B updates."""
import time
import numpy as np
import torch

from qv_common47 import ROOT,ENGINEERING,RUN,read,ref,save,checked
from qv_model47 import fit,original_features,output,late_features
from runtime import make_models,extract_rgb_features
from profile_gpu import load_authorized_backbone
from pilot15_gpu import fingerprint


def bridge_features(backbone, row):
    rgb=np.load(checked(row['input']['rgb']),mmap_mode='r',allow_pickle=False)
    values=[]
    with torch.inference_mode():
        for first in range(0,len(rgb),8):
            x=torch.from_numpy(rgb[first:first+8].copy()).permute(0,4,1,2,3).cuda().float()/255
            values.append(extract_rgb_features(backbone,(x-.45)/.225))
    return torch.cat(values)


def save_features(sid, values, condition):
    path=ROOT/'features'/(sid+'_'+condition+'.npy')
    with path.open('xb') as out:np.save(out,values.detach().cpu().numpy(),allow_pickle=False)


def main():
    import sys
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    registration=read(ROOT/'registration.json');protocol=read(ROOT/'protocol.json')
    lock=read(ROOT/'source_input_lock.json')
    for identity in list(lock['code'].values())+list(lock['dependencies'].values()):checked(identity)
    torch.set_num_threads(2);torch.manual_seed(protocol['seed']);np.random.seed(protocol['seed'])
    started=time.monotonic();backbone,model,cfg=make_models(ENGINEERING)
    load_authorized_backbone(ENGINEERING,backbone);backbone.cuda().eval().requires_grad_(False)
    model.cuda().eval()
    original=torch.load(checked(registration['control_checkpoint']),map_location='cuda',weights_only=True)['model']
    model.load_state_dict(original,strict=True)
    prefix=torch.nn.Sequential(*backbone.blocks[:5]);prefix_hash=fingerprint(prefix)
    late_hash=fingerprint(backbone.blocks[5]);classifier_hash=fingerprint(backbone.blocks[-1])
    parameters=8782557449+sum(p.numel() for p in backbone.parameters())+sum(p.numel() for p in model.parameters())
    if parameters>9000000000:raise ValueError('Actual complete combination exceeds9B')
    (ROOT/'features').mkdir();(ROOT/'outputs').mkdir()
    features={};prefixes={}
    for source in registration['sources']:
        sid=source['sid'];prefixes[sid],features[sid]=original_features(backbone,source)
        output(model,features[sid],sid,'initial')
        print('QV_FIRST_FEATURES',sid,len(features[sid]),flush=True)
    arms=[]
    for arm in ['frozen_visual','late_visual']:
        model.load_state_dict(original,strict=True)
        result=fit(backbone,model,registration['sources'],features,prefixes,protocol,arm)
        if fingerprint(prefix)!=prefix_hash or fingerprint(backbone.blocks[-1])!=classifier_hash:
            raise ValueError('Frozen early visual or original classifier changed')
        if (fingerprint(backbone.blocks[5])==late_hash)!=(arm=='frozen_visual'):
            raise ValueError('Actual visual parameter changes disagree with intervention')
        for source in registration['sources']:
            sid=source['sid']
            values=features[sid] if arm=='frozen_visual' else late_features(backbone,prefixes[sid])
            save_features(sid,values,arm)
            output(model,values,sid,arm)
            output(model,torch.roll(values,len(values)//2,dims=0),sid,arm+'_halfshift')
        for row in registration['external_bridge']:
            sid=row['source']['sid']
            values=(torch.from_numpy(np.load(checked(row['feature']),allow_pickle=False)).cuda()
                    if arm=='frozen_visual' else bridge_features(backbone,row))
            save_features(sid,values,arm)
            output(model,values,sid,arm)
            output(model,torch.roll(values,len(values)//2,dims=0),sid,arm+'_halfshift')
        arms.append(result)
        print('QV_ARM_COMPLETE',arm,result,flush=True)
    checked(registration['protected_baseline'])
    save(ROOT/'gpu_completion.json',dict(state='TWO_FIXED_ARMS_NATURALLY_COMPLETE',arms=arms,
        full_parameters=parameters,new8B_calls=0,new8B_updates=0,
        new_visual_trainable_parameters=sum(p.numel() for p in backbone.blocks[5].parameters()),
        real_prefix_cache_bytes=sum(t.numel()*t.element_size() for t in prefixes.values()),
        prefix_frozen_SHA=prefix_hash,classifier_frozen_SHA=classifier_hash,
        QV_sources=len(registration['sources']),external_sources=len(registration['external_bridge']),
        seconds=time.monotonic()-started,peak_allocated_bytes=torch.cuda.max_memory_allocated()))


if __name__=='__main__':main()
