"""Frozen602 CPU head once per unique feature; no labels or new optimization."""
from prod_common import *


def apply(ctx):
    cpu_only();ctx.claim('width_apply')
    import numpy as np
    import torch
    from torch import nn
    done=ctx.stage('feature_completion','PASS_NATIVE16_WIDTH_BASE_FEATURES')
    qa=ctx.stage('output_QA','PASS_NATIVE16_UNIQUE_LATENT_NATIVE_MAPPING_QA')
    require(qa['feature_completion_sha256']==sha(ctx.root/'feature_completion.json') and sha(qa['unique_features_path'])==qa['unique_features_sha256'],'First successful output QA/stack')
    norm=np.load(ctx.done['normalization_path'],allow_pickle=False);mean=norm['mean'];std=norm['std']
    require(mean.shape==std.shape==(4096,) and np.isfinite(mean).all() and np.isfinite(std).all() and (std>=.001).all(),'Frozen train602 normalization')
    model=nn.Module();model.network=nn.Sequential(nn.Linear(4096,8),nn.GELU(),nn.Linear(8,1))
    model.load_state_dict(torch.load(ctx.done['weights_path'],map_location='cpu',weights_only=True));model.eval()
    require(sum(p.numel() for p in model.parameters())==32785 and BACKBONE+98329+32785==TOTAL,'Actual shared physical parameter accounting')
    features=np.load(qa['unique_features_path'],allow_pickle=False)
    require(features.shape==(len(qa['unique_uids']),4096) and np.isfinite(features).all(),'Complete unique actual features')
    x=torch.from_numpy(((features-mean)/std).astype(np.float32))
    with torch.no_grad():
        raw=model.network(x).squeeze(-1);require(bool(torch.isfinite(raw).all()),'Finite actual frozen width readout')
        predicted=torch.round(1000*torch.clamp(1+raw,min=.001,max=1.)).to(torch.int64).clamp(1,1000)
    # Independent NumPy width quantization over the actual saved raw outputs.
    direct=np.clip(np.rint(1000*np.clip(1+raw.numpy(),.001,1.)).astype(np.int64),1,1000)
    require(np.array_equal(direct,predicted.numpy()),'Independent actual width quantization')
    raw_path=ctx.root/'head_unique_output.npz'
    with raw_path.open('xb') as handle:np.savez(handle,raw=raw.numpy(),predicted_width=predicted.numpy(),unique_uids=np.asarray(qa['unique_uids']))
    saved=np.load(raw_path,allow_pickle=False)
    require(np.array_equal(saved['raw'],raw.numpy()) and np.array_equal(saved['predicted_width'],direct) and saved['unique_uids'].tolist()==qa['unique_uids'],'Actual saved head raw/width/UID bit equality')
    mapping=dict(zip(qa['unique_uids'],predicted.tolist()));by_video={}
    for target in done['targets']:by_video.setdefault(target['video_id'],[]).append(dict(**target,predicted_width=mapping[target['uid']]))
    records={}
    for meta in ctx.landscape:
        sid=meta['video_id'];targets=sorted(by_video[sid],key=lambda t:t['cell'])
        require(sha(ctx.adopted/'inputs'/sid/'native.npz')==ctx.sources[sid]['native_sha256'] and sha(ctx.adopted/'inputs'/sid/'clock.json')==ctx.sources[sid]['clock_sha256'],'Actual unchanged native sample/PTS files')
        native=np.load(ctx.adopted/'inputs'/sid/'native.npz',allow_pickle=False);clock=read(ctx.adopted/'inputs'/sid/'clock.json')
        require([t['cell'] for t in targets]==list(range(len(native['sample_ordinals']))) and
                [t['sample_ordinal'] for t in targets]==native['sample_ordinals'].tolist(),'Actual full per-source native sample mapping')
        records[sid]=dict(sample_ordinals=native['sample_ordinals'].tolist(),predicted_width=[t['predicted_width'] for t in targets],
                          native_pts_exact=clock['normalized_exact_pts'],head_sha256=HEAD_SHA,normalization_sha256=NORM_SHA,
                          unique_uids=[t['uid'] for t in targets],interpolation_axis='native_pts_exact')
    payload=dict(status='PASS_FROZEN_WIDTH_HEAD_NATIVE16_SAMPLE_READOUT',width_by_video=records,
         output_QA_sha256=sha(ctx.root/'output_QA.json'),head_sha256=HEAD_SHA,normalization_sha256=NORM_SHA,
         unique_head_readouts=len(mapping),new_head_updates=0,model_parameters=TOTAL,online_effect='UNKNOWN',**ctx.binding)
    save(ctx.root/'width_by_video.json',payload)
    require(read(ctx.root/'width_by_video.json')==payload,'Actual serialized width/native source receipt equality')
    save(ctx.root/'width_output_QA.json',dict(status='PASS_NATIVE16_FROZEN_HEAD_NATIVE_SAMPLE_OUTPUT_AND_SAVE_QA',
         width_by_video_sha256=sha(ctx.root/'width_by_video.json'),head_unique_output_sha256=sha(raw_path),
         head_sha256=HEAD_SHA,normalization_sha256=NORM_SHA,unique_head_readouts=len(mapping),
         native_sources=len(records),new_model_forwards=0,new_head_updates=0,**ctx.binding))


if __name__=='__main__':
    ctx,phase=cli()
    try:{'apply':apply}[phase](ctx)
    except BaseException as error:failure(ctx,phase,error);raise
