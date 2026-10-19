"""Shared-wrapper BASE forwards for unique independent images; first output QA."""
import sys
from prod_common import *


def frozen_inputs(ctx):
    unique=ctx.stage('unique_inputs','PASS_ALL_NATIVE16_EFFECTIVE_INPUTS_QA_AND_EXACT_DEDUP')
    lock=ctx.stage('freeze_source_lock','FROZEN_ALL_WIDTH_EFFECTIVE_INPUTS_BEFORE_GPU')
    require(lock['unique_inputs_sha256']==sha(ctx.root/'unique_inputs.json') and lock['query_manifest_sha256']==sha(ctx.root/'query_manifest.json'),'All effective inputs frozen before GPU')
    for path,digest in lock['code'].items():require(sha(path)==digest,'Frozen production module changed '+path)
    require(unique['training_overlap_count']==0,'STOP_TRAIN_TEST_INPUT_OVERLAP')
    return unique


def collate(values,pad_id):
    import torch
    length=max(v['input_ids'].shape[1] for v in values)
    ids=torch.full((len(values),length),pad_id,dtype=torch.long);mask=torch.zeros_like(ids)
    for i,value in enumerate(values):
        n=value['input_ids'].shape[1];ids[i,-n:]=value['input_ids'][0];mask[i,-n:]=1
    return dict(input_ids=ids,attention_mask=mask,pixel_values=torch.cat([v['pixel_values'] for v in values]),
                image_grid_thw=torch.cat([v['image_grid_thw'] for v in values]))


def infer(ctx):
    import torch
    from peft.tuners.tuners_utils import BaseTunerLayer
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Only declared shared-wrapper GPU0 child')
    torch.set_num_threads(2);unique=frozen_inputs(ctx);query=ctx.stage('query_manifest','PASS_NATIVE16_NEW_SINGLE_IMAGE_WIDTH_TOKENS')
    sys.path.insert(0,str(ctx.run/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation();ctx.claim('infer');directory=ctx.root/'feature_batches';directory.mkdir()
    pending=[u for u in unique['unique_records'] if 'adopted_feature' not in u]
    records={};new_calls=0
    # Existing successful aliases do not cause fresh visual/model forwards.
    for record in unique['unique_records']:
        if 'adopted_feature' in record:
            adopted=record['adopted_feature'];ref(adopted)
            records[record['uid']]=dict(uid=record['uid'],input_fingerprint=record['input_fingerprint'],feature_path=adopted['path'],feature_sha256=adopted['sha256'],feature_row=adopted['row'],saved_uid=adopted['uid'],adopted_successful_forward=True)
    # A single model load verifies original base even when every input aliases.
    sys.path.insert(0,str(ctx.run/'b_score_aligned_package_v4'));import engine
    require(Path(engine.__file__).resolve()==(ctx.run/'b_score_aligned_package_v4/engine.py').resolve(),'Original-B engine only')
    model,processor,identity=engine.load_model(ctx.cfg);native=model.get_base_model();core=native.model
    flags=[(p,p.requires_grad) for p in model.parameters()];layers=[m for m in model.modules() if isinstance(m,BaseTunerLayer)]
    require(len(layers)==144 and all(not m.disable_adapters for m in layers) and identity['logical_parameters']==BACKBONE,'Actual physical TIME/base inventory')
    try:
        with model.disable_adapter(),torch.inference_mode():
            require(all(m.disable_adapters for m in layers),'Actual BASE role')
            for start in range(0,len(pending),8):
                batch=pending[start:start+8];values=[];cache={}
                for record in batch:
                    case=record['case'];key=(case['chunk']['path'],case['query_path'])
                    if key not in cache:
                        require(sha(key[0])==case['chunk']['sha256'] and sha(key[1])==case['query_sha256'],'Actual frozen batch inputs')
                        cache[key]=(torch.load(key[0],map_location='cpu',weights_only=True),torch.load(key[1],map_location='cpu',weights_only=True))
                    item=one_input(case,record['image_index'],cache[key]);require(signature(item)==record['input_fingerprint'],'Actual effective input differs from exact dedup proof');values.append(item)
                tensors=collate(values,query['pad_token_id']);actual_batch=info(tensors)
                gpu={key:value.to('cuda:0') for key,value in tensors.items()}
                output=core(**gpu,use_cache=False,return_dict=True);latent=output.last_hidden_state[:,-1,:].float().cpu().contiguous()
                require(latent.shape==(len(batch),4096) and bool(torch.isfinite(latent).all()),'Actual independent-image BASE prefix features')
                path=directory/('batch_%06d.pt'%(start//8))
                # Save the ENTIRE successful forward before per-member receipts.
                tensor_save(path,dict(language=latent,uids=[u['uid'] for u in batch],input_fingerprints=[u['input_fingerprint'] for u in batch]))
                digest=sha(path);save(path.with_suffix('.json'),dict(status='PASS_UNIQUE_BASE_WIDTH_BATCH',path=str(path),sha256=digest,actual_batch_tensors=actual_batch,
                    uids=[u['uid'] for u in batch],new_forward_images=len(batch),new_forward_batches=1))
                for row,record in enumerate(batch):records[record['uid']]=dict(uid=record['uid'],input_fingerprint=record['input_fingerprint'],feature_path=str(path),feature_sha256=digest,feature_row=row,saved_uid=record['uid'],adopted_successful_forward=False)
                new_calls+=len(batch)
                if len(records)>=4 and not (ctx.root/'engineering4.json').exists():
                    save(ctx.root/'engineering4.json',dict(status='PASS_FIRST_REAL_WIDTH_PREFIX_INPUT_DIMENSION',sources=list(records.values())[:4],labels_read=False,**ctx.binding))
                del gpu,output,latent,tensors,values,cache
    finally:
        for parameter,flag in flags:parameter.requires_grad_(flag)
    require(all(p.requires_grad==flag for p,flag in flags) and all(not m.disable_adapters for m in layers),'Exact PEFT context-exit flags restored')
    after=dict(base=engine.frozen_identity(model,ctx.cfg),adapter=engine.adapter_identity(model,ctx.cfg))
    require(after['base']==identity['base'] and after['adapter']==identity['adapter'],'Actual bytewise frozen base/adapter identity')
    require(new_calls==unique['new_unique_forwards'] and len(records)==unique['unique_inputs'],'Every unique effective input resolved exactly once')
    save(ctx.root/'feature_completion.json',dict(status='PASS_NATIVE16_WIDTH_BASE_FEATURES',domain=DOMAIN,
         unique_records=[records[u['uid']] for u in unique['unique_records']],targets=unique['targets'],model_identity=identity,
         unique_inputs=unique['unique_inputs'],new_unique_forwards=new_calls,alias_target_count=unique['alias_target_count'],
         covered_sources=unique['covered_sources'],new_language_generations=0,new_optimizer_updates=0,
         actual_backbone_parameters=BACKBONE,future_joint_resident_parameters=TOTAL,unique_inputs_sha256=sha(ctx.root/'unique_inputs.json'),**ctx.binding))


def qa(ctx):
    cpu_only();ctx.claim('output_qa')
    import numpy as np
    import torch
    unique=frozen_inputs(ctx);done=ctx.stage('feature_completion','PASS_NATIVE16_WIDTH_BASE_FEATURES')
    require(done['unique_inputs_sha256']==sha(ctx.root/'unique_inputs.json') and done['targets']==unique['targets'],'Full native source/alias mapping identity')
    expected={u['uid']:u for u in unique['unique_records']};require(len(done['unique_records'])==len(expected),'Complete unique feature denominator')
    matrix=[];cache={};uids=[]
    for record in done['unique_records']:
        wanted=expected[record['uid']];require(record['input_fingerprint']==wanted['input_fingerprint'],'Member effective input proof')
        path=record['feature_path']
        if path not in cache:
            require(sha(path)==record['feature_sha256'],'Saved successful batch/alias bytes');cache[path]=torch.load(path,map_location='cpu',weights_only=True)
        saved=cache[path];row=record['feature_row']
        require(saved['uids'][row]==record['saved_uid'] and saved['input_fingerprints'][row]==record['input_fingerprint'],'Actual saved unique member mapping')
        value=saved['language'][row]
        require(value.shape==(4096,) and value.dtype==torch.float32 and bool(torch.isfinite(value).all()),'Independent latent shape/finite')
        matrix.append(value.numpy());uids.append(record['uid'])
    require(uids==[u['uid'] for u in unique['unique_records']],'Fixed actual unique order')
    array=np.stack(matrix)
    with (ctx.root/'unique_features.npy').open('xb') as handle:np.save(handle,array,allow_pickle=False)
    save(ctx.root/'output_QA.json',dict(status='PASS_NATIVE16_UNIQUE_LATENT_NATIVE_MAPPING_QA',unique_uids=uids,
         unique_features_path=str(ctx.root/'unique_features.npy'),unique_features_sha256=sha(ctx.root/'unique_features.npy'),
         feature_completion_sha256=sha(ctx.root/'feature_completion.json'),native_target_count=len(unique['targets']),
         new_model_forwards=0,training_overlap_count=0,labels_read=False,**ctx.binding))


if __name__=='__main__':
    ctx,phase=cli()
    try:{'infer':infer,'qa':qa}[phase](ctx)
    except BaseException as error:failure(ctx,phase,error);raise
