"""New single-image width tokens and first independent exact-combination QA."""
from prod_common import *


def prepare(ctx):
    cpu_only();ctx.claim('prepare')
    import numpy as np
    import torch
    from transformers import AutoProcessor
    processor=AutoProcessor.from_pretrained(ctx.cfg['model_dir'],local_files_only=True)
    processor.tokenizer.padding_side='left'
    template=processor.apply_chat_template([{'role':'user','content':[{'type':'image'},{'type':'text','text':QUESTION}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    require(template.count('<|image_pad|>')==1,'Native one-image generation prefix')
    training_cpu=read(ctx.training/'cpu_acceptance.json')
    require(training_cpu['status']=='PASS_602_NEW_PURPOSE_JPEG_RGB_PREFIX_INPUTS' and len(training_cpu['sources'])==602 and all(s['template_text']==template for s in training_cpu['sources']),'Exact original602 template equality; no prompt drift')
    directory=ctx.root/'query';directory.mkdir();sources=[]
    for meta in ctx.landscape:
        sid=meta['video_id'];source=ctx.sources[sid];native=np.load(ctx.adopted/'inputs'/sid/'native.npz',allow_pickle=False)
        require(read(ctx.adopted/'inputs'/sid/'acceptance.json')==source and sha(ctx.adopted/'inputs'/sid/'native.npz')==source['native_sha256'] and sha(ctx.adopted/'inputs'/sid/'clock.json')==source['clock_sha256'],'Adopted CPU/native/clock source identity')
        require([o for chunk in source['chunks'] for o in chunk['samples']]==native['sample_ordinals'].tolist(),'Actual original observation order')
        clock=read(ctx.adopted/'inputs'/sid/'clock.json')
        require(len(clock['normalized_exact_pts'])==meta['n_frames']==len(native['groups'])==source['native_frames'],'Actual adopted native clock/metadata ordinal domain')
        out=directory/sid;out.mkdir();cases=[];offset=0
        for ci,chunk in enumerate(source['chunks']):
            texts=[]
            for grid in chunk['grid']:
                require(len(grid)==3 and grid[0]==1 and grid[1]*grid[2]%4==0,'Actual original one-image merge grid')
                texts.append(template.replace('<|image_pad|>','<|image_pad|>'*(grid[0]*grid[1]*grid[2]//4)))
            values=processor.tokenizer(texts,return_tensors='pt',padding=True,add_special_tokens=False)
            values={key:values[key].contiguous() for key in ('input_ids','attention_mask')}
            require(values['input_ids'].shape[0]==len(chunk['samples']) and values['input_ids'].shape[1]<=2048,'Independent images per batch, fixed token budget')
            path=out/('query_%04d.pt'%ci);tensor_save(path,values)
            cases.append(dict(query_path=str(path),query_sha256=sha(path),chunk=chunk,cell_start=offset))
            offset+=len(chunk['samples'])
        sources.append(dict(id=sid,cells=offset,cases=cases,native_sha256=source['native_sha256'],clock_sha256=source['clock_sha256']))
    save(ctx.root/'query_manifest.json',dict(status='PASS_NATIVE16_NEW_SINGLE_IMAGE_WIDTH_TOKENS',sources=sources,
         template=template,pad_token_id=processor.tokenizer.pad_token_id,training_CPU_acceptance_sha256=sha(ctx.training/'cpu_acceptance.json'),
         no_new_decode=True,no_new_image_processor=True,labels_read=False,**ctx.binding))


def qa(ctx):
    cpu_only();ctx.claim('input_qa')
    import torch
    from transformers import AutoTokenizer
    query=ctx.stage('query_manifest','PASS_NATIVE16_NEW_SINGLE_IMAGE_WIDTH_TOKENS')
    require(query['training_CPU_acceptance_sha256']==sha(ctx.training/'cpu_acceptance.json'),'Actual602 input inventory binding')
    tokenizer=AutoTokenizer.from_pretrained(ctx.cfg['model_dir'],local_files_only=True)
    pad=tokenizer.convert_tokens_to_ids('<|image_pad|>')
    train=read(ctx.training/'cpu_acceptance.json');training_signatures=set()
    for source in train['sources']:
        require(sha(source['tensor_path'])==source['tensor_sha256'],'Existing actual602 train inputs needed for overlap audit')
        values=torch.load(source['tensor_path'],map_location='cpu',weights_only=True)
        require(info(values)==source['tensors'],'Actual602 saved effective tensors')
        training_signatures.add(signature(values))
    prior={}
    for reference in ctx.p.get('adopted_successful_feature_manifests',[]):
        old=read(ref(reference))
        require(old['status']=='PASS_NATIVE16_WIDTH_BASE_FEATURES' and old['domain']==DOMAIN and old['question_sha256']==ctx.binding['question_sha256'] and old['training_completion_sha256']==DONE_SHA,'Only exact successful official same-query BASE features may alias')
        require(old['model_identity']['base']['sha256']==ctx.cfg['expected_base_sha256'] and old['model_identity']['adapter']['sha256']==ctx.cfg['b_adapter_sha256'] and old['model_identity']['logical_parameters']==BACKBONE,'Exact alias model base/physical TIME inventory')
        for record in old['unique_records']:
            require(record['input_fingerprint'] not in training_signatures,'STOP_TRAIN_TEST_INPUT_OVERLAP')
            ref(dict(path=record['feature_path'],sha256=record['feature_sha256']))
            prior.setdefault(record['input_fingerprint'],dict(path=record['feature_path'],sha256=record['feature_sha256'],row=record['feature_row'],uid=record.get('saved_uid',record['uid'])))
    uniques=[];by_fingerprint={};targets=[]
    for source in query['sources']:
        for ci,case in enumerate(source['cases']):
            chunk=case['chunk'];require(sha(chunk['path'])==chunk['sha256'],'Original chunk identity')
            original=torch.load(chunk['path'],map_location='cpu',weights_only=True)
            require(sha(case['query_path'])==case['query_sha256'],'Actual serialized new query')
            serialized=torch.load(case['query_path'],map_location='cpu',weights_only=True)
            require(info({'pixel_values':original['pixel_values']})['pixel_values']['sha256']==chunk['pixel_sha256'] and list(original['pixel_values'].shape)==chunk['pixel_shape'],'Original whole pixel bit signature')
            for index,ordinal in enumerate(chunk['samples']):
                values=one_input(case,index,(original,serialized))
                ids=values['input_ids'][0].tolist();expected=chunk['grid'][index][0]*chunk['grid'][index][1]*chunk['grid'][index][2]//4
                require(ids.count(pad)==expected and len(ids)<=2048,'Exact per-image visual placeholder count')
                decoded=tokenizer.decode(ids,skip_special_tokens=False)
                require(QUESTION in decoded and decoded.count('<|vision_start|>')==decoded.count('<|vision_end|>')==1,'Exact single-image frozen width task')
                # Independent tokenizer reconstruction, without image processing.
                rebuilt=tokenizer(query['template'].replace('<|image_pad|>','<|image_pad|>'*expected),return_tensors='pt',add_special_tokens=False)
                require(torch.equal(rebuilt['input_ids'],values['input_ids']) and torch.equal(rebuilt['attention_mask'],values['attention_mask']),'Independent exact new token/mask QA')
                fingerprint=signature(values)
                require(fingerprint not in training_signatures,'STOP_TRAIN_TEST_INPUT_OVERLAP')
                target=dict(video_id=source['id'],cell=case['cell_start']+index,sample_ordinal=ordinal)
                if fingerprint not in by_fingerprint:
                    uid='U%06d'%len(uniques);record=dict(uid=uid,input_fingerprint=fingerprint,case=case,image_index=index,targets=[])
                    if fingerprint in prior:record['adopted_feature']=prior[fingerprint]
                    by_fingerprint[fingerprint]=record;uniques.append(record)
                record=by_fingerprint[fingerprint];record['targets'].append(target);targets.append(dict(**target,uid=record['uid']))
    expected=sum(s['cells'] for s in query['sources'])
    require(len(targets)==expected and len({(r['video_id'],r['cell']) for r in targets})==expected,'Every landscape native observation mapped once')
    save(ctx.root/'unique_inputs.json',dict(status='PASS_ALL_NATIVE16_EFFECTIVE_INPUTS_QA_AND_EXACT_DEDUP',unique_records=uniques,targets=targets,
         training_overlap_count=0,unique_inputs=len(uniques),new_unique_forwards=sum('adopted_feature' not in u for u in uniques),
         alias_target_count=len(targets)-sum('adopted_feature' not in u for u in uniques),covered_sources=len(query['sources']),
         query_manifest_sha256=sha(ctx.root/'query_manifest.json'),training_CPU_acceptance_sha256=query['training_CPU_acceptance_sha256'],**ctx.binding))
    code={str(path):sha(path) for path in sorted(Path(__file__).parent.glob('*.py'))}
    save(ctx.root/'freeze_source_lock.json',dict(status='FROZEN_ALL_WIDTH_EFFECTIVE_INPUTS_BEFORE_GPU',unique_inputs_sha256=sha(ctx.root/'unique_inputs.json'),
         query_manifest_sha256=sha(ctx.root/'query_manifest.json'),code=code,**ctx.binding))


if __name__=='__main__':
    ctx,phase=cli()
    try:{'prepare':prepare,'qa':qa}[phase](ctx)
    except BaseException as error:failure(ctx,phase,error);raise
