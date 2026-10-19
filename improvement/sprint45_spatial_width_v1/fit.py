"""Single fixed602 final-only CPU fit. No eval, five-fold or proxy quality gate."""
from width_common import *


def fit(ctx):
    cpu_only()
    import numpy as np
    import torch
    from torch.nn import functional as F
    from head import WidthHead,scale,quantized_width
    accepted,sources=checked_cpu_sources(ctx)
    output=ctx.checked_stage('output_QA','PASS_602_FIRST_INDEPENDENT_LATENT_STACK_QA')
    feature=ctx.checked_stage('feature_completion','PASS_602_BASE_PREFIX_FEATURES')
    require(output['feature_completion_sha256']==sha(ctx.root/'feature_completion.json') and output['feature_sha256']==feature['feature_sha256'] and sha(feature['feature_path'])==feature['feature_sha256'],'Frozen actual features/first independent output QA')
    label_path=ctx.root/'labels/train602.json'
    require(sha(label_path)==accepted['train_label_file_sha256'],'Separately retained original602 target artifact')
    labels=read(label_path);require(labels['status']=='ADOPT_ORIGINAL602_HUMAN_WIDTH_TARGETS' and labels['original_accepted_journal_sha']==ctx.proto['original_accepted_journal_sha'] and
            all(labels[k]==v for k,v in ctx.binding.items()),'Original human target provenance')
    target_rows=labels['rows'];require(len(target_rows)==602,'No train source omitted')
    for source,target in zip(sources,target_rows):
        require(target['sample_id']==source['sample_id'] and target['id']==source['id'] and target['source_sha256']==source['source_sha256'] and
                type(target['target_width']) is int and 1<=target['target_width']<=1000 and target['target_source']==TARGET_SOURCE,'Original source-aligned target width')
    x=np.load(feature['feature_path'],allow_pickle=False)
    require(x.shape==(602,4096) and x.dtype==np.float32 and np.isfinite(x).all(),'Actual602 train-only latent matrix')
    ctx.claim('fit');directory=ctx.root/'fit';directory.mkdir()
    mean=x.mean(axis=0,dtype=np.float64).astype(np.float32)
    std=np.maximum(x.std(axis=0,dtype=np.float64).astype(np.float32),np.float32(.001))
    z=torch.from_numpy(((x-mean)/std).astype(np.float32))
    require(bool(torch.isfinite(z).all()),'Finite train-only normalized features')
    target=torch.tensor([r['target_width']/1000 for r in target_rows],dtype=torch.float32)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(20261016);model=WidthHead()
    require(bool((quantized_width(model(z))==1000).all()),'Actual zero initialization yields exact1000 width')
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
    history=[];model.train()
    for update in range(200):
        optimizer.zero_grad(set_to_none=True)
        loss=F.smooth_l1_loss(scale(model(z)),target,beta=.1,reduction='mean')
        require(bool(torch.isfinite(loss)),'Nonfinite fitting loss; no fallback')
        loss.backward()
        require(all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters()),'Nonfinite head gradients')
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        optimizer.step();history.append(float(loss.detach()))
    require(all(bool(torch.isfinite(p).all()) for p in model.parameters()),'Nonfinite final head')
    model.eval();weights=directory/'final_head.pt';tensor_save(weights,model.state_dict())
    restored=WidthHead();restored.load_state_dict(torch.load(weights,map_location='cpu',weights_only=True));restored.eval()
    require(set(model.state_dict())==set(restored.state_dict()) and all(torch.equal(model.state_dict()[k],restored.state_dict()[k]) for k in model.state_dict()),'Actual final-only save/reload parameter bit equality')
    with torch.no_grad():
        width=quantized_width(model(z));reloaded_width=quantized_width(restored(z))
    require(torch.equal(width,reloaded_width) and bool(((width>=1)&(width<=1000)).all()),'Final reload/width legality')
    norm=directory/'normalization.npz'
    with norm.open('xb') as handle:np.savez(handle,mean=mean,std=std)
    require(sum(p.numel() for p in model.parameters())==HEAD_PARAMETERS and BACKBONE+SEMANTIC_HEAD_PARAMETERS+HEAD_PARAMETERS==8_782_590_234,'Actual physical aggregate parameter accounting')
    save(directory/'training.json',dict(training=TRAINING,updates=200,sources=602,loss_history=history,
         loss_interpretation='Training fit diagnostic only; no heldout/official quality claim',
         sample_ids=[s['sample_id'] for s in sources],source_ids=[s['id'] for s in sources],
         feature_sha256=feature['feature_sha256'],labels_sha256=sha(label_path),**ctx.binding))
    save(ctx.root/'completion.json',dict(status=FINAL_STATUS,weights_path=str(weights),weights_sha256=sha(weights),
         normalization_path=str(norm),normalization_sha256=sha(norm),feature_dimension=4096,hidden_dim=8,
         head_parameters=HEAD_PARAMETERS,physical_base_TIME_parameters=BACKBONE,semantic_head_parameters=SEMANTIC_HEAD_PARAMETERS,
         future_joint_resident_parameters=BACKBONE+SEMANTIC_HEAD_PARAMETERS+HEAD_PARAMETERS,
         training_sources=602,head_optimizer_updates=200,backbone_optimizer_updates=0,
         screen_sources=0,confirm_sources=0,new_production_runs=0,official_score='UNKNOWN',
         quality_gate_applied=False,production_admitted=False,explicit_risk_exploration=True,
         old_scientific_failures_unchanged=True,known_exposure=ctx.proto['known_exposure'],origin_independence='UNKNOWN',
         training_report_sha256=sha(directory/'training.json'),**ctx.binding))


if __name__=='__main__':
    ctx=cli()
    try:fit(ctx)
    except BaseException as error:fail(ctx,'fit',error);raise
