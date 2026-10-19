"""Explicit shared-wrapper BASE prefill features, or independent CPU output QA.

No generate, label reader, neutral control, checkpoint search or auto-resume.
"""
import sys
from width_common import *


def infer(ctx):
    import numpy as np
    import torch
    from peft.tuners.tuners_utils import BaseTunerLayer
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','GPU infer requires declared shared-wrapper GPU0 child')
    torch.set_num_threads(2)
    accepted,sources=checked_cpu_sources(ctx)
    qa=ctx.checked_stage('input_QA','PASS_602_FIRST_INDEPENDENT_SAVED_RGB_PROCESSOR_BIT_QA')
    require(qa['cpu_acceptance_sha256']==sha(ctx.root/'cpu_acceptance.json'),'First independent input QA binding')
    cfg=ctx.model_config()
    sys.path.insert(0,str(ctx.run/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    ctx.claim('infer');(ctx.root/'features').mkdir()
    # Unique width_common module avoids colliding with engine's own common.py.
    sys.path.insert(0,str(ctx.run/'b_score_aligned_package_v4'))
    import engine
    require(Path(engine.__file__).resolve()==(ctx.run/'b_score_aligned_package_v4/engine.py').resolve(),'Existing original-B engine path')
    model,processor,identity=engine.load_model(cfg)
    require(identity['logical_parameters']==BACKBONE,'Actual physical base+TIME count')
    native=model.get_base_model();core=native.model
    flags=[(p,p.requires_grad) for p in model.parameters()]
    layers=[m for m in model.modules() if isinstance(m,BaseTunerLayer)]
    require(len(layers)==144 and all(not m.disable_adapters for m in layers),'Actual144 initial active TIME layers')
    outputs=[];members=[]
    try:
        with model.disable_adapter(),torch.inference_mode():
            require(all(m.disable_adapters for m in layers),'BASE role requires actual temporary TIME disabling')
            for source in sources:
                sample=source['sample_id'];directory=ctx.root/'features'/sample;directory.mkdir()
                require(sha(source['tensor_path'])==source['tensor_sha256'],'Actual accepted input tensor bytes')
                values=torch.load(source['tensor_path'],map_location='cpu',weights_only=True)
                require(tensor_info(values)==source['tensors'] and set(values)=={'input_ids','attention_mask','pixel_values','image_grid_thw'},'Actual original no-label GPU input inventory')
                gpu={key:value.to('cuda:0') for key,value in values.items()}
                output=core(**gpu,use_cache=False,return_dict=True)
                last=output.last_hidden_state[:,-1,:]
                require(last.shape==(1,4096) and bool(torch.isfinite(last).all()),'Actual single-image final prefix hidden shape/finite')
                latent=last[0].float().cpu().contiguous()
                path=directory/'latent.pt'
                tensor_save(path,dict(latent=latent,sample_id=sample,id=source['id'],source_sha256=source['source_sha256'],input_sha256=source['tensor_sha256']))
                receipt=dict(status='PASS_NEW_BASE_PREFIX_LATENT',sample_id=sample,id=source['id'],source_sha256=source['source_sha256'],
                             path=str(path),sha256=sha(path),input_sha256=source['tensor_sha256'],dimension=4096,
                             labels_read=False,new_forward_calls=1,new_language_generations=0)
                save(directory/'completion.json',receipt);outputs.append(receipt);members.append(latent.numpy())
                if len(outputs)==4:
                    save(ctx.root/'engineering4.json',dict(status='PASS_FOUR_REAL_INPUTS_BASE_PREFIX_DIMENSION',sources=outputs.copy(),
                         selection_used_labels=False,actual_backbone_parameters=BACKBONE,**ctx.binding))
                del gpu,output,last,latent,values
    finally:
        # PEFT context exits FIRST; then undo its requires_grad reactivation.
        for parameter,flag in flags:parameter.requires_grad_(flag)
    require(all(p.requires_grad==flag for p,flag in flags) and all(not m.disable_adapters for m in layers),'Exact original PEFT parameter/activation flags restored')
    after=dict(base=engine.frozen_identity(model,cfg),adapter=engine.adapter_identity(model,cfg))
    require(after['base']==identity['base'] and after['adapter']==identity['adapter'],'Actual bytewise frozen base/adapter identity after all forwards')
    feature=np.stack(members)
    require(feature.shape==(602,4096) and np.isfinite(feature).all() and [r['sample_id'] for r in outputs]==[s['sample_id'] for s in sources],'Complete original602 feature/source order')
    with (ctx.root/'features.npy').open('xb') as handle:np.save(handle,feature,allow_pickle=False)
    save(ctx.root/'feature_completion.json',dict(status='PASS_602_BASE_PREFIX_FEATURES',sources=outputs,shape=[602,4096],
         feature_path=str(ctx.root/'features.npy'),feature_sha256=sha(ctx.root/'features.npy'),input_QA_sha256=sha(ctx.root/'input_QA.json'),
         cpu_acceptance_sha256=sha(ctx.root/'cpu_acceptance.json'),model_identity=identity,frozen_after=after,
         actual_backbone_parameters=BACKBONE,new_forward_calls=602,new_language_generations=0,backbone_optimizer_updates=0,
         labels_read=False,all_original_flags_restored=True,**ctx.binding))


def qa(ctx):
    cpu_only();ctx.claim('output_qa')
    import numpy as np
    import torch
    accepted,sources=checked_cpu_sources(ctx)
    done=ctx.checked_stage('feature_completion','PASS_602_BASE_PREFIX_FEATURES')
    require(done['cpu_acceptance_sha256']==sha(ctx.root/'cpu_acceptance.json') and done['input_QA_sha256']==sha(ctx.root/'input_QA.json'),'Output/input stage binding')
    require(len(done['sources'])==602 and sha(done['feature_path'])==done['feature_sha256'],'Actual full feature artifact')
    combined=np.load(done['feature_path'],allow_pickle=False)
    require(combined.shape==(602,4096) and combined.dtype==np.float32 and np.isfinite(combined).all(),'Finite full602 float32 feature matrix')
    for index,(source,proof) in enumerate(zip(sources,done['sources'])):
        require(proof==read(ctx.root/'features'/source['sample_id']/'completion.json') and proof['sample_id']==source['sample_id'] and
                proof['id']==source['id'] and proof['input_sha256']==source['tensor_sha256'] and proof['source_sha256']==source['source_sha256'],'Complete independent source/input/latent mapping')
        require(sha(proof['path'])==proof['sha256'],'Saved actual member feature bytes')
        item=torch.load(proof['path'],map_location='cpu',weights_only=True)
        require(item['sample_id']==source['sample_id'] and item['id']==source['id'] and item['source_sha256']==source['source_sha256'] and item['input_sha256']==source['tensor_sha256'],'Actual serialized member source/input binding')
        latent=item['latent'];require(latent.shape==(4096,) and latent.dtype==torch.float32 and bool(torch.isfinite(latent).all()) and
                np.array_equal(combined[index],latent.numpy()),'Independent actual member-to-stack bit equality')
    save(ctx.root/'output_QA.json',dict(status='PASS_602_FIRST_INDEPENDENT_LATENT_STACK_QA',sources=602,dimension=4096,
         feature_completion_sha256=sha(ctx.root/'feature_completion.json'),feature_sha256=done['feature_sha256'],
         new_model_forwards=0,labels_read=False,**ctx.binding))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--stage',choices=['infer','qa'],required=True);args=parser.parse_args();ctx=Context(args.root)
    try:{'infer':infer,'qa':qa}[args.stage](ctx)
    except BaseException as error:fail(ctx,args.stage,error);raise
