"""One new frozen vision forward per registered sample, no text generation."""
import sys
from common_runtime import *

def main():
    import numpy as np
    import torch
    torch.set_num_threads(2)
    accepted=read(ROOT/'cpu_acceptance.json')
    require(accepted['status']=='PASS_ALL_REGISTERED_NEW_FEATURE_INPUTS','CPU gate')
    require(accepted['protocol_sha256']==sha(ROOT/'protocol.json'),'Protocol changed')
    sys.path.insert(0,str(RUN/'b_score_aligned_package_v4'))
    import engine
    cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    model,processor,identity=engine.load_model(cfg)
    core=model.get_base_model().model
    require(hasattr(core,'get_image_features'),'Actual Qwen feature API')
    output=[]
    for ix,src in enumerate(accepted['sources']):
        sid=src['id']; arrays=[]
        out=ROOT/'features'/sid;out.mkdir(parents=True,exist_ok=False)
        for chunk in src['chunks']:
            require(sha(chunk['path'])==chunk['sha256'],'CPU input cache changed')
            cache=torch.load(chunk['path'],map_location='cpu',weights_only=True)
            with torch.inference_mode():
                images,deep=core.get_image_features(cache['pixel_values'].to('cuda:0'),cache['image_grid_thw'].to('cuda:0'))
                require(len(images)==len(chunk['samples']),'Feature/image mapping')
                means=torch.stack([v.float().mean(0) for v in images]).cpu().contiguous()
                require(means.ndim==2 and torch.isfinite(means).all(),'Nonfinite feature')
            arrays.append(means.numpy())
            event('NEW_FEATURE_CHUNK',id=sid,samples=chunk['samples'],dimension=means.shape[1])
        feat=np.concatenate(arrays,axis=0)
        require(feat.shape[0]==src['feature_cells'],'Feature cell missing')
        np.save(out/'vision.npy',feat)
        record=dict(status='PASS_NEW_FROZEN_FEATURE_SOURCE',id=sid,cells=len(feat),dimension=feat.shape[1],feature_sha256=sha(out/'vision.npy'),input_acceptance_sha256=sha(ROOT/'inputs'/sid/'acceptance.json'))
        write(out/'completion.json',record);output.append(record)
        if ix==3:
            require(len({r['dimension'] for r in output})==1,'Dimension drift')
            sys.path.insert(0,str(ROOT))
            from score_residual_head_v1.contracts import build_contract
            from score_residual_head_v1.head import ResidualHead,native_prediction
            for previous in accepted['sources'][:4]:
                n=np.load(ROOT/'inputs'/previous['id']/'native.npz')
                clock=read(ROOT/'inputs'/previous['id']/'clock.json')
                contract=build_contract(n['groups'].tolist(),n['baseline'].tolist(),[None]*len(n['baseline']),previous['feature_cells'],clock['normalized_exact_pts'])
                full_dimension=3*output[0]['dimension']+1
                zero=ResidualHead(full_dimension,8)
                x=torch.zeros((previous['feature_cells'],full_dimension),dtype=torch.float32)
                require(native_prediction(zero(x).detach(),contract)==contract.baseline_native,'Four-source zero residual native identity')
            write(ROOT/'engineering4.json',dict(status='PASS_FOUR_REAL_SOURCES_FEATURE_EXTRACTION_AND_ZERO_NATIVE_IDENTITY',sources=output,model_identity=identity,head_dimension=full_dimension,head_parameters=zero.parameter_count,resident_parameters=8782459120+zero.parameter_count,no_generation=True))
        event('FEATURE_SOURCE_ACCEPTED',id=sid,cells=len(feat))
    # Recompute exact base and adapter identity after forwards, not just requires_grad.
    after=dict(base=engine.frozen_identity(model,cfg),adapter=engine.adapter_identity(model,cfg))
    require(after['base']==identity['base'] and after['adapter']==identity['adapter'],'Frozen weights changed')
    write(ROOT/'feature_completion.json',dict(status='PASS_ALL426_NEW_FROZEN_FEATURES',sources=output,model_identity=identity,frozen_after=after,new_generation_calls=0,new_feature_samples=sum(x['cells'] for x in output)))

if __name__=='__main__':main()
