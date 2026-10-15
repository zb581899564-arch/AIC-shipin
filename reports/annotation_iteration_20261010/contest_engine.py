"""New image-score time selector; immutable original source/crop field, strict ZIP."""
import argparse,hashlib,json,subprocess,sys,time
from bisect import bisect_left
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
B4=RUN/'b_score_aligned_package_v4';sys.path.insert(0,str(B4))
import common as c
import selector_contract as sc
from score_grammar import Constraint,candidates
MODEL=RUN/'models/Qwen3-VL-8B-Instruct';ADAPTER=H/'train/adapter'
ADAPTER_SHA='1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933'
ADAPTER_CONFIG_SHA='dcd134aecf4573d0f462d70adcf96b8beeba6bd76e62ec6c5bf57593fe79a8e1'
EXPECTED={
 'nontest':dict(zip(('field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl'),(
 'c4b53cb7d95442ecaa4c8fa6b82b027fd5779370230a2b97f8c8796526386aed','cf4a873053bd2baf24343043eb36f835a5853ce232b409489915329f161c0375',
 'f630e725ddff54c590a4062c39b98c1b7233773b8c0a391f271378ac157283a7','1ffd45d72c723ec71f973d6b24f5e72d052ddf3f6e3b51150a2e68bacfc1532d'))),
 'rematch':dict(zip(('field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl'),(
 '17ba37aadc4cf705e1ff95a78a58d8befcab9e34f7132ef0775f1ed1df0d8bca','8e81df10c685527145069cd9c65316ab6341c9da7d6e39bb282ed6c60ce12f1e',
 '9cb7c4e36597dc8ae723ac3b686b2c3b1f04d5982503478fdf19ee72b18c4798','8f83cd967d7d1f95243ac4ae3cddc7fdb78abb3d4842a78f81f6b187fb1562ab')))}
def sha(p):return c.sha(p)
def user(sequence,images):
    text='<image>\n'*len(images)+sc.prompt(sequence);parts=text.split('<image>');content=[]
    for i,part in enumerate(parts):
        if part:content.append({'type':'text','text':part})
        if i<len(images):content.append({'type':'image','image':images[i]})
    return [{'role':'user','content':content}]
def out(scope):return H/'contest_v1'/(scope+'_01')
def data(scope):
    c.verify();item,manifest,clocks=c.inputs(scope)
    assert sha(ADAPTER/'adapter_model.safetensors')==ADAPTER_SHA
    assert sha(ADAPTER/'adapter_config.json')==ADAPTER_CONFIG_SHA
    cache=B4/(scope+'_01');assert all(sha(cache/name)==digest for name,digest in EXPECTED[scope].items())
    schedule=c.read(cache/'schedule.stage.json');spatial=c.read(cache/'spatial.stage.json')
    assert schedule['status']=='PASS_TIME_INDEPENDENT_SOURCE_FIELD' and schedule['max_gap']==8 and schedule['temporal_selection_used_for_boundaries'] is False
    assert spatial['status']=='PASS_STRICT_SOURCE_FIELD_SPATIAL' and spatial['invalid']==0 and spatial['time_adapter_enabled'] is False
    assert spatial['logical_parameters']==8767123696
    return item,manifest,clocks,cache
def binding(scope):
    b=c.read(out(scope)/'prepared.json')
    assert all(sha(H/name)==digest for name,digest in b['code_sha256'].items())
    assert sha(out(scope)/'blocks.jsonl')==b['blocks_sha256'] and sha(out(scope)/'samples.jsonl')==b['samples_sha256']
    assert sha(H/'quality_result.json')==b['quality_sha256'] and c.read(H/'quality_result.json')['stage2_pass'] is True
    return b
def prepare(scope):
    import production
    from field_contract import build_field_requests
    from frame_contract import legacy_manifest
    from package_contract import keyset
    item,manifest,clocks,cache=data(scope);dest=out(scope);assert not dest.exists();dest.mkdir(parents=True)
    assert c.read(H/'quality_result.json')['stage2_pass'] is True
    domain=production.field_frames(manifest,clocks);cached=c.rows(cache/'field_frames.jsonl')
    assert len(domain)==len(keyset(domain)) and len(cached)==len(keyset(cached))
    assert {(r['video_id'],r['source_frame']):r for r in domain}=={(r['video_id'],r['source_frame']):r for r in cached}
    shots=c.rows(cache/'field_shots.jsonl');requests=c.rows(cache/'anchor_requests.jsonl');outputs=c.rows(cache/'anchor_output.jsonl')
    assert build_field_requests(cached,shots,8)==requests and len(outputs)==len(requests)==spatial_rows(cache)
    assert keyset(shots)==keyset(domain)
    for request,answer in zip(requests,outputs):
        assert answer['status']=='MODEL_OK' and answer['used_fallback'] is False and request['anchor_request_sha256']==answer['anchor_request_sha256']
        assert request['expected_pixel_sha256']==answer['decoded_pixel_sha256']
    pixel_lookup={(s['video_id'],s['source_frame']):s['decoded_pixel_sha256'] for s in shots}
    del cached,shots,requests,outputs
    samples=[];blocks=[]
    for record in sorted(manifest['records'],key=lambda r:r['video_id']):
        vid=record['video_id'];clock=clocks[vid];assert sha(record['source_path'])==record['source_sha256']
        start=Fraction(str(record['scope_start_sec']));end=clock['duration'] if scope=='rematch' else Fraction(str(record['scope_end_sec']))
        g=sc.grid(clock['pts'],start,end)
        lo=bisect_left([float(p) for p in clock['pts']],record['scope_start_sec'])
        hi=bisect_left([float(p) for p in clock['pts']],record['scope_end_sec'])
        assert g[0]['first_native_ordinal']==lo and g[-1]['end_native_ordinal_exclusive']==hi
        reader=production.OrdinalReader(record,clock);folder=dest/'frames'/vid;folder.mkdir(parents=True)
        try:
            for s in g:
                ordinal=s['sample_native_ordinal'];bgr,pixel=reader.get(ordinal)
                assert pixel==pixel_lookup[(vid,ordinal)] and bgr.shape==(record['height'],record['width'],3)
                rgb=np.ascontiguousarray(bgr[:,:,::-1]);assert np.array_equal(rgb[:,:,::-1],bgr)
                path=folder/(str(ordinal)+'.png');Image.fromarray(rgb).save(path)
                with Image.open(path) as im:assert np.array_equal(np.asarray(im.convert('RGB')),rgb)
                s.update(video_id=vid,source_sha256=record['source_sha256'],clock_record_sha256=clock['clock_record_sha256'],
                  image=str(path.relative_to(H)),image_sha256=sha(path),bgr_pixel_sha256=pixel,
                  rgb_pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),color_operation='ONE_EXPLICIT_BGR_TO_RGB_AFTER_REGISTERED_DECODER')
        finally:reader.close()
        samples.extend(g)
        for first in range(0,len(g),16):
            seq=g[first:first+16];blocks.append({'id':vid+':score:'+str(first//16),'video_id':vid,'samples':seq,'prompt':sc.prompt(seq)})
        c.progress(dest,dict(stage='PREPARE_EXACT_IMAGE_SELECTOR',videos_done=len({s['video_id'] for s in samples}),videos_total=len(manifest['records']),samples=len(samples)))
    c.write_rows(dest/'samples.jsonl',samples);c.write_rows(dest/'blocks.jsonl',blocks)
    c.write(dest/'prepared.json',dict(status='PASS_EXACT_SOURCE_FIELD_PIXELS_RGB_GRID_AND_BLOCKS',videos=len(manifest['records']),samples=len(samples),blocks=len(blocks),
      code_sha256={name:sha(H/name) for name in ('contest_engine.py','selector_contract.py','score_grammar.py')},
      blocks_sha256=sha(dest/'blocks.jsonl'),samples_sha256=sha(dest/'samples.jsonl'),quality_sha256=sha(H/'quality_result.json'),
      manifest_sha256=item['manifest_sha256'],registry_sha256=item['registry_sha256'],source_field_sha256=EXPECTED[scope],
      adapter_sha256=ADAPTER_SHA,adapter_config_sha256=ADAPTER_CONFIG_SHA,threshold_x20=49,scope=scope,spatial_model_calls=0,old_spatial_costs_preserved=True))
def spatial_rows(cache):return c.read(cache/'spatial.stage.json')['rows']
def processor():
    from transformers import AutoProcessor
    return AutoProcessor.from_pretrained(MODEL,local_files_only=True,min_pixels=4096,max_pixels=65536)
def encode(p,block):
    images=[]
    for s in block['samples']:
        path=H/s['image'];assert sha(path)==s['image_sha256']
        with Image.open(path) as im:rgb=im.convert('RGB');rgb.load()
        assert hashlib.sha256(np.asarray(rgb).tobytes()).hexdigest()==s['rgb_pixel_sha256'];images.append(rgb)
    assert block['prompt']==sc.prompt(block['samples'])
    messages=user(block['samples'],images);text=p.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    e=p(text=[text],images=images,return_tensors='pt');n=e['input_ids'].shape[1]
    assert n<=16384 and e['image_grid_thw'].shape[0]==len(images)
    signature=hashlib.sha256(e['pixel_values'].contiguous().numpy().tobytes()).hexdigest()
    return e,{'input_tokens':n,'prompt_sha256':hashlib.sha256(text.encode()).hexdigest(),'pixel_tensor_sha256':signature,
      'image_grid_thw':e['image_grid_thw'].tolist(),'input_ids_sha256':hashlib.sha256(e['input_ids'].contiguous().numpy().tobytes()).hexdigest()}
def generate(scope):
    import torch
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation();data(scope);b=binding(scope);dest=out(scope);assert not (dest/'raw.jsonl').exists()
    p=processor();ids=candidates(p.tokenizer)
    model=PeftModel.from_pretrained(Qwen3VLForConditionalGeneration.from_pretrained(MODEL,local_files_only=True,
      torch_dtype=torch.bfloat16,attn_implementation='sdpa'),ADAPTER,local_files_only=True).to('cuda').eval()
    total=sum(x.numel() for x in model.parameters());assert total==8774791408
    assert list(model.peft_config)==['default'] and model.active_adapters==['default']
    pc=model.peft_config['default'];assert pc.r==8 and pc.lora_alpha==16 and set(pc.target_modules)=={'q_proj','k_proj','v_proj','o_proj'}
    actual_adapter={'active_adapters':model.active_adapters,'rank':pc.r,'alpha':pc.lora_alpha,'target_modules':sorted(pc.target_modules),
      'parameter_count':sum(x.numel() for name,x in model.named_parameters() if 'lora_' in name)}
    assert actual_adapter['parameter_count']==7667712
    for parameter in model.parameters():parameter.requires_grad_(False)
    planned=c.rows(dest/'blocks.jsonl');assert len(planned)==b['blocks']
    with (dest/'raw.jsonl').open('x',encoding='utf-8') as f:
        for i,block in enumerate(planned):
            e,sig=encode(p,block);constraint=Constraint(p.tokenizer,sig['input_tokens'],len(block['samples']),ids)
            with torch.inference_mode():answer=model.generate(**e.to('cuda'),do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint)
            tokens=answer[0,sig['input_tokens']:].tolist();text,obj=constraint.finish(tokens)
            row={'id':block['id'],'video_id':block['video_id'],'answer':text,'output_token_ids':tokens,**sig}
            f.write(json.dumps(row)+'\n');f.flush()
            c.progress(dest,dict(stage='ACTUAL_NEW_SELECTOR_GENERATION',done=i+1,total=len(planned)))
    c.write(dest/'generation.json',dict(status='PASS_ALL_NEW_SELECTOR_BLOCKS',model_calls=len(planned),adapter_sha256=ADAPTER_SHA,
      logical_parameters=total,shared_base_counted_once=True,new_optimizer_updates_this_inference=0,training_optimizer_steps=237,
      old_B_time_adapter_used=False,adapter_config_sha256=ADAPTER_CONFIG_SHA,actual_adapter=actual_adapter,
      raw_sha256=sha(dest/'raw.jsonl'),prepared_sha256=sha(dest/'prepared.json')))
def replay(scope):
    import torch
    data(scope);b=binding(scope);dest=out(scope);g=c.read(dest/'generation.json')
    assert g['raw_sha256']==sha(dest/'raw.jsonl') and g['prepared_sha256']==sha(dest/'prepared.json')
    p=processor();ids=candidates(p.tokenizer);raw=c.rows(dest/'raw.jsonl');planned=c.rows(dest/'blocks.jsonl')
    assert len(raw)==len(planned)==b['blocks'] and [r['id'] for r in raw]==[r['id'] for r in planned]
    for block,row in zip(planned,raw):
        e,sig=encode(p,block);assert all(row[k]==v for k,v in sig.items()) and row['video_id']==block['video_id']
        text,obj=Constraint(p.tokenizer,sig['input_tokens'],len(block['samples']),ids).finish(row['output_token_ids'])
        assert text==row['answer'] and set(obj)=={'scores_x20'} and len(obj['scores_x20'])==len(block['samples'])
        assert all(type(v) is int and 20<=v<=100 for v in obj['scores_x20'])
    assert not torch.cuda.is_initialized()
    c.write(dest/'cpu_replay.json',dict(status='PASS_ALL_ACTUAL_PROCESSOR_PIXELS_TOKENS_RAW_PARSER_CPU',blocks=len(raw),raw_sha256=sha(dest/'raw.jsonl'),new_model_calls=0,CUDA_initialized=False))
def finish(scope):
    from production import field_frames
    from field_contract import compose_from_field
    from frame_contract import legacy_manifest
    from package_contract import keyset,validate_predictions,package
    item,manifest,clocks,cache=data(scope);b=binding(scope);dest=out(scope)
    replayed=c.read(dest/'cpu_replay.json');assert replayed['raw_sha256']==sha(dest/'raw.jsonl')
    samples=c.rows(dest/'samples.jsonl');blocks=c.rows(dest/'blocks.jsonl');raw=c.rows(dest/'raw.jsonl')
    assert len(blocks)==len(raw)==b['blocks'] and [(s['video_id'],s['grid_index']) for r in blocks for s in r['samples']]==[(s['video_id'],s['grid_index']) for s in samples]
    chosen=set();scored=[]
    for block,row in zip(blocks,raw):
        assert block['id']==row['id'];scores=json.loads(row['answer'])['scores_x20'];assert len(scores)==len(block['samples'])
        for s,score in zip(block['samples'],scores):
            assert type(score) is int and 20<=score<=100
            scored.append(dict(video_id=s['video_id'],grid_index=s['grid_index'],score_x20=score,selected=score>=49,
              first_native_ordinal=s['first_native_ordinal'],end_native_ordinal_exclusive=s['end_native_ordinal_exclusive']))
            if score>=49:chosen.update((s['video_id'],ordinal) for ordinal in range(s['first_native_ordinal'],s['end_native_ordinal_exclusive']))
    domain=field_frames(manifest,clocks);assert chosen<=keyset(domain);selected=[r for r in domain if (r['video_id'],r['source_frame']) in chosen]
    assert len(selected)==len(chosen)
    for record in manifest['records']:assert sha(record['source_path'])==record['source_sha256']
    pred,provenance=compose_from_field(legacy_manifest(manifest),selected,c.rows(cache/'field_shots.jsonl'),c.rows(cache/'anchor_requests.jsonl'),c.rows(cache/'anchor_output.jsonl'))
    c.write_rows(dest/'selected.jsonl',selected);c.write_rows(dest/'scored_bins.jsonl',scored)
    c.write_rows(dest/'predictions.jsonl',pred);c.write_rows(dest/'provenance.jsonl',provenance)
    c.write(dest/'metadata.json',dict(records=manifest['records'],errors=[]))
    checks=validate_predictions(legacy_manifest(manifest),pred,keyset(selected),provenance)
    pending=dest/'candidate_IMAGE_SCORE_237STEP_8B.PENDING.zip';checks.update(package(dest/'predictions.jsonl',pending))
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
      '--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(dest/'metadata.json'),
      '--selected',str(dest/'selected.jsonl'),'--predictions',str(dest/'predictions.jsonl'),'--provenance',str(dest/'provenance.jsonl'),
      '--zip',str(pending),'--report',str(dest/'independent_validation.json')],check=True)
    report=c.read(dest/'independent_validation.json');assert report['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and len(report['checks'])==11 and all(report['checks'].values())
    candidate=dest/'candidate_IMAGE_SCORE_237STEP_8B.zip';pending.rename(candidate)
    c.write(dest/'package_receipt.json',dict(status='PASS_COMPLETE_IMAGE_SCORE_237STEP_8B_EXPERIMENTAL_ZIP',scope=scope,
      candidate=str(candidate),zip_bytes=candidate.stat().st_size,zip_sha256=sha(candidate),videos=len(pred),selected_frames=len(selected),
      empty_videos=sum(not r['predictions'] for r in pred),samples=len(samples),blocks=len(blocks),adapter_sha256=ADAPTER_SHA,
      logical_parameters=8774791408,training_optimizer_steps=237,old_spatial_source_field=EXPECTED[scope],spatial_model_calls=0,
      official_score=None,uploaded=False,production_replaced=False,independent_validation_sha256=sha(dest/'independent_validation.json'),
      quality_evidence='SEEN_TVSUM_DEVELOPMENT_PROXY_ONLY; NATIVE_PROXY_F_CI_CROSSES_ZERO; AIC_GENERALIZATION_UNKNOWN'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','generate','replay','finish']);p.add_argument('scope',choices=['nontest','rematch']);a=p.parse_args()
    globals()[a.mode](a.scope)
