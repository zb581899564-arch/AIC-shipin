"""Single pinned 8B base, temporal final LoRA, native spatial base only."""
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
from lowres import lowres_encode,verify_cuda_adapter
import sys
import time

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
HERE=RUN/'mac8b_delivery_v2'
ASSETS=RUN/'mac8b_delivery_v1'
CODE=RUN/'baseline_a_pts_v1'
sys.path[:0]=[str(CODE),str(CODE/'vendor'),str(RUN/'baseline_a_format_recovery_v1'),
              str(RUN/'temporal_sft8b_v1')]

def require(ok,message):
    if not ok: raise RuntimeError(message)
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()
def write(path,value):
    with Path(path).open('x') as f:f.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify():
    lock=read(HERE/'source_lock.json');a=read(HERE/'admission.json');files=dict(lock['files'])
    for path,digest in a['files'].items():
        require(path not in files or files[path]==digest,'conflicting source/model binding: '+path)
        files[path]=digest
    for path,digest in files.items():require(sha(path)==digest,'bound bytes changed: '+path)
    return a

def inputs(scope):
    a=read(HERE/'inputs.json')[scope]
    require(sha(a['manifest'])==a['manifest_sha256'],'metadata manifest changed')
    from pts_contract import load_clocks
    manifest=read(a['manifest']);clocks=load_clocks(manifest,a['registry'],a['registry_sha256'])
    return a,manifest,clocks

def stage_admission(stage,scope,out):
    a=read(HERE/('rematch_MAC8B_v2_'+scope+'_'+stage+'_01.admission.json'))
    require(a.get('authorized') is True and a.get('scope')==scope and a.get('stage')==stage and
        a.get('output')==str(Path(out)) and a.get('source_lock_sha256')==sha(HERE/'source_lock.json'), 'phase authority changed')
    require(read(HERE/'processor_cpu_01.json')['status']=='PASS_ACTUAL_MAC_LOWRES_PROCESSOR','processor gate missing')
    if stage!='long_probe':
        require(read(HERE/'dev/decision.json')['status']=='PASS_FROZEN_WEAK_DEV_GATE','Mac fixed dev gate STOP')
        require(read(HERE/'long_probe_01/probe.stage.json')['status']=='PASS_SYNTHETIC_MAC_LOWRES_8B_INFERENCE','relocation probe missing')
    if scope=='rematch':
        require(read(HERE/'nontest_01/package.stage.json')['status']=='PASS_COMPLETE_8B_PACKAGE_NOT_SCORED_NOT_UPLOADED','Mac NONTEST8 missing')
    if stage=='spatial': require(read(Path(out)/'schedule.stage.json')['status']=='PASS_EXACT_SCHEDULING','scheduling missing')

class OrdinalReader:
    """Start at ordinal zero, never random seek. Selected gaps remain shot boundaries."""
    def __init__(self,item,clock):
        from pts_contract import BRANCH_NATIVE
        self.native=clock['branch']==BRANCH_NATIVE;self.item=item;self.next=0;self.last=None
        if self.native:
            from native_frames import VerifiedNativeReader
            self.reader=VerifiedNativeReader(item['source_path'],item,clock)
        else:
            import cv2
            self.reader=cv2.VideoCapture(item['source_path'])
            require(self.reader.isOpened(),'source decoder open failed')
    def get(self,ordinal,expected_sha=None):
        require(type(ordinal) is int and 0<=ordinal<self.item['n_frames'],'invalid source ordinal')
        if self.native:frame=self.reader.read(ordinal)
        else:
            require(ordinal>=self.next-1,'backward source ordinal rejected')
            while self.next<=ordinal:
                ok,self.last=self.reader.read();require(ok,'sequential decode failed');self.next+=1
            frame=self.last
        require(frame.shape==(self.item['height'],self.item['width'],3),'decoded geometry changed')
        pixel=hashlib.sha256(memoryview(frame).cast('B')).hexdigest()
        if expected_sha is not None:require(pixel==expected_sha,'same-frame byte identity changed')
        return frame,pixel
    def close(self):
        if not self.native:self.reader.release()

def temporal(scope,out):
    a=verify()
    stage_admission('temporal',scope,out)
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    # CUDA before native decoder imports, matching accepted training initialization.
    import torch
    torch.cuda.init()
    import decord
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from pts_contract import BRANCH_CFR,window_schedule,native_clip_plan,parse_native_segments
    from native_frames import build_native_clip
    from exact_pts import exact_native_pts,verify_native_encoding
    from constrained_json import ascii_token_candidates,make_prefix_constraint
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    bound,manifest,clocks=inputs(scope);out=Path(out);out.mkdir(exist_ok=True)
    tc=load(CODE/'vendor/temporal_common.py','package_tc')
    start_time=time.monotonic()
    base=Qwen3VLForConditionalGeneration.from_pretrained(a['model_dir'],local_files_only=True,torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()
    relocation=verify_cuda_adapter(model,a)
    count=sum(p.numel() for _,p in unique_parameters(model));require(count==8782459120,'complete 8B parameter inventory changed')
    frozen=relocation['base_hash']
    expected=read(ASSETS/'training_evidence/train_report.json')['freeze_evidence']['adapter_off']
    require(frozen==expected,'loaded frozen base differs from accepted training base')
    processor=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=processor.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    eos=model.generation_config.eos_token_id
    if isinstance(eos,int):eos=[eos]
    candidates=ascii_token_candidates(processor.tokenizer)
    failures=0;windows=0
    recovery=None
    previous={r['video_id']:r for r in rows(recovery['partial_path'])} if recovery else {}
    if recovery:require(sha(recovery['partial_path'])==recovery['partial_sha256'],'preserved partial output changed')
    reused=regenerated=0
    with (out/'temporal.jsonl').open('x') as stream:
        for i,item in enumerate(manifest['records'],1):
            require(sha(item['source_path'])==item['source_sha256'],'source hash changed')
            clock=clocks[item['video_id']];fps=item['fps_num']/item['fps_den']
            source=dict(video_id=item['video_id'],targetRatioWH=item['targetRatioWH'],video_path=item['source_path'],
                n_frames=item['n_frames'],fps=fps,arm='B_8B_FINAL_CONSTRAINED',windows=[])
            for j,(start,end) in enumerate(window_schedule(item,manifest['kind'],clock)):
                one=time.monotonic();windows+=1
                old=previous.get(item['video_id'],{}).get('windows',[])
                if j<len(old) and old[j].get('output_valid') is True:
                    kept=old[j]
                    require(kept['status']=='MODEL_OK' and kept['start_sec']==start and kept['end_sec']==end and not kept['parse_errors'],'old successful window identity mismatch')
                    source['windows'].append(kept);reused+=1;continue
                if j<len(old):
                    require(old[j]['status']=='INFERENCE_FAILURE' and old[j]['parse_errors']==['RuntimeError: expanded temporal sequence exceeds training contract'],'recovery admits only pre-generation input-limit failure')
                    regenerated+=1
                w=dict(index=j,start_sec=start,end_sec=end,status='INFERENCE_FAILURE',output_valid=False,
                    parsed_segments=None,parse_errors=[],parse_warnings=[],raw_output='')
                try:
                    if clock['branch']==BRANCH_CFR:
                        arr,md,info=tc.build_virtual_clip(item['source_path'],start,end)
                        require(info['source_total_frames']==item['n_frames'] and abs(info['source_fps']-fps)<=max(1e-6,fps*1e-6),'temporal source count/FPS changed')
                        require(arr.shape[1:]==(item['height'],item['width'],3),'temporal source geometry changed')
                        encoded=lowres_encode(processor,text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[md],
                            padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
                    else:
                        plan=native_clip_plan(clock,start,end);arr,md=build_native_clip(item['source_path'],item,clock,plan)
                        with exact_native_pts(processor,plan,fps) as identity:
                            encoded=lowres_encode(processor,text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[md],
                                padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
                            verify_native_encoding(processor,encoded,identity)
                        info=dict(n_sampled=plan['n_sampled'])
                        w.update(clock_branch=clock['branch'],clock_record_sha256=clock['clock_record_sha256'],
                            source_frame_ids=plan['source_frame_ids'],native_processor_identity=identity)
                    require(encoded['input_ids'].shape[1]<=6144,'expanded inference sequence exceeds registered Mac lowres 6144 contract')
                    encoded=encoded.to('cuda');prefix=int(encoded['input_ids'].shape[1])
                    constraint=make_prefix_constraint(processor.tokenizer,prefix,end-start,candidate_token_ids=candidates,eos_token_ids=eos)
                    with torch.inference_mode():
                        generated=model.generate(**encoded,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint)
                    torch.cuda.synchronize();ids=generated[0,prefix:];constraint.assert_complete(ids)
                    raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                    if clock['branch']==BRANCH_CFR:parsed,errors,warnings=tc.parse_segments(raw,end-start)
                    else:parsed,errors,warnings,events=parse_native_segments(raw,end-start);w['native_parse_representation_events']=events
                    w.update(status='MODEL_OK' if parsed is not None else 'PARSE_FAILURE',output_valid=parsed is not None,
                        parsed_segments=parsed,parse_errors=errors,parse_warnings=warnings,raw_output=raw,
                        sampled_frames=info['n_sampled'],constraint_stats=constraint.stats)
                    del encoded,generated,arr
                except Exception as exc:w['parse_errors']=[type(exc).__name__+': '+str(exc)]
                failures+=int(not w['output_valid']);w['seconds']=time.monotonic()-one;source['windows'].append(w)
            stream.write(json.dumps(source,sort_keys=True)+'\n');stream.flush()
            progress=dict(scope=scope,stage='TEMPORAL',videos=i,total=len(manifest['records']),windows=windows,failures=failures,
                wall_seconds=time.monotonic()-start_time)
            temp=out/'progress.tmp';temp.write_text(json.dumps(progress));temp.replace(out/'progress.json')
            print(json.dumps(progress),flush=True)
    report=dict(status='PASS_TEMPORAL_EXECUTION' if failures==0 else 'STOP_TEMPORAL_FAILURES',videos=len(manifest['records']),
        windows=windows,invalid_windows=failures,logical_parameters=count,base_hash=frozen,adapter_sha256=sha(Path(a['adapter'])/'adapter_model.safetensors'),
        output_sha256=sha(out/'temporal.jsonl'),manifest_sha256=bound['manifest_sha256'],wall_seconds=time.monotonic()-start_time,
        generation_time_constraint=True,posthoc_segment_rewrite=False,failure_to_empty_conversions=0,uploaded=False)
    report.update(inference_max_sequence_length=6144,training_max_sequence_length_unchanged=6144,video_pixels_per_frame=32768,
        reused_successful_windows=reused,regenerated_pre_generation_guard_failures=regenerated)
    if recovery:
        require(reused==recovery['successful_windows_to_keep'] and regenerated==recovery['pre_generation_guard_failures'],
            'complete preserved/recovered window denominator changed')
        report.update(original_successful_window_objects_unchanged=True,old_partial_sha256=recovery['partial_sha256'])
    write(out/'temporal.stage.json',report);require(failures==0,'temporal failures block candidate')

def spatial(scope,out):
    a=verify()
    stage_admission('spatial',scope,out)
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    torch.cuda.init()
    bound,manifest,clocks=inputs(scope);out=Path(out)
    from pts_contract import validate_frame_request
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    from PIL import Image
    import cv2
    baseline=load(ROOT/'inference/baseline_qwen3vl.py','spatial_baseline_8b')
    started=time.monotonic()
    # Same pinned weight bytes; no separate 4B, head, temporal LoRA or optimizer.
    model=baseline.Qwen3VL(a['model_dir'],device_map={'':'cuda:0'})
    count=sum(p.numel() for _,p in unique_parameters(model.model));require(count==8767123696,'spatial base count changed')
    for p in model.model.parameters():p.requires_grad_(False)
    frozen=canonical_frozen_hash(model.model,torch)
    require(frozen==read(ASSETS/'training_evidence/train_report.json')['freeze_evidence']['adapter_off'],'spatial native base does not equal trained frozen base')
    metadata={r['video_id']:r for r in manifest['records']}; requests=rows(out/'anchor_requests.jsonl')
    require(requests and len({(r['video_id'],r['source_frame']) for r in requests})==len(requests),'anchor denominator invalid')
    current=None;reader=None;failures=0;measure=[]
    with (out/'anchor_output.jsonl').open('x') as stream:
        try:
            for i,request in enumerate(requests,1):
                one=time.monotonic()
                rec=dict(video_id=request['video_id'],source_frame=request['source_frame'],anchor_request_sha256=request['anchor_request_sha256'],
                    spatial_source='QWEN_ANCHOR_SAME_FRAME',used_fallback=False,box_xyw=None,raw_output='',parse_error=None,status='DECODE_OR_MODEL_FAILURE')
                try:
                    item=validate_frame_request(request,metadata)
                    if current!=item['video_id']:
                        if reader is not None:reader.close()
                        require(sha(item['source_path'])==item['source_sha256'],'spatial source bytes changed')
                        reader=OrdinalReader(item,clocks[item['video_id']]);current=item['video_id']
                    frame,pixel=reader.get(request['source_frame'],request['expected_pixel_sha256']);rec['decoded_pixel_sha256']=pixel
                    image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));tw,th=request['target_ratio_wh']
                    raw=model.predict_focus(image,(tw,th),max_new_tokens=baseline.DEFAULT_CROP_TOKENS);rec['raw_output']=raw
                    center=baseline.parse_focus_norm(raw,image.width,image.height)
                    require(center is not None,'no valid native focus')
                    crop_w,crop_h=baseline.compute_crop_size(image.width,image.height,tw,th)
                    box=baseline.center_to_box(center[0],center[1],image.width,image.height,crop_w,crop_h)
                    require(baseline.validate_box(box,image.width,image.height,tw,th),'illegal native crop')
                    rec.update(status='MODEL_OK',box_xyw=[int(x) for x in box],decoder_identity='SEQUENTIAL_FROM_SOURCE_ORDINAL_ZERO')
                except Exception as exc:rec['parse_error']=type(exc).__name__+': '+str(exc)
                rec['seconds']=time.monotonic()-one;measure.append(rec['seconds']);failures+=rec['status']!='MODEL_OK'
                stream.write(json.dumps(rec,sort_keys=True)+'\n');stream.flush()
                if i%25==0 or i==len(requests):
                    progress=dict(stage='SPATIAL',scope=scope,anchors=i,total=len(requests),failures=failures,wall_seconds=time.monotonic()-started)
                    temp=out/'progress.tmp';temp.write_text(json.dumps(progress));temp.replace(out/'progress.json');print(json.dumps(progress),flush=True)
        finally:
            if reader is not None:reader.close()
    report=dict(status='PASS_SAME_FRAME_NATIVE_8B_SPACE' if failures==0 else 'STOP_SPATIAL_FAILURES',rows=len(requests),invalid=failures,
        manifest_sha256=bound['manifest_sha256'],requests_sha256=sha(out/'anchor_requests.jsonl'),output_sha256=sha(out/'anchor_output.jsonl'),
        wall_seconds=time.monotonic()-started,measured_seconds_per_anchor=sum(measure)/len(measure),
        base_hash=frozen,spatial_base_parameters=count,complete_pipeline_parameters=8782459120,shared_base_counted_once=True,
        temporal_adapter_enabled=False,weak_roi_inputs_used=0,old_test_boxes_used=0,silent_fallbacks=0,uploaded=False)
    write(out/'spatial.stage.json',report);require(failures==0,'native spatial failures block candidate')

def long_probe(scope,out):
    a=verify();stage_admission('long_probe',scope,out)
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    torch.cuda.init()
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from constrained_json import ascii_token_candidates,make_prefix_constraint
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    out=Path(out);out.mkdir(exist_ok=True);started=time.monotonic()
    base=Qwen3VLForConditionalGeneration.from_pretrained(a['model_dir'],local_files_only=True,torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()
    relocation=verify_cuda_adapter(model,a)
    require(sum(p.numel() for _,p in unique_parameters(model))==8782459120,'long probe model parameter count changed')
    fingerprint=relocation['base_hash']
    require(fingerprint==read(ASSETS/'training_evidence/train_report.json')['freeze_evidence']['adapter_off'],'long probe base identity changed')
    tc=load(CODE/'vendor/temporal_common.py','long_input_tc')
    p=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=p.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    frames=torch.zeros((64,3,1080,1920),dtype=torch.uint8)
    md=dict(fps=30,frames_indices=[14*i for i in range(64)],total_num_frames=900,video_backend='decord')
    encoded=lowres_encode(p,text=[prompt],videos=[frames],video_metadata=[md],padding=True,truncation=False,do_sample_frames=False,return_tensors='pt').to('cuda')
    prefix=int(encoded['input_ids'].shape[1]);require(0<prefix<=6144,'synthetic lowres input exceeds Mac protocol')
    eos=model.generation_config.eos_token_id
    if isinstance(eos,int):eos=[eos]
    constraint=make_prefix_constraint(p.tokenizer,prefix,30,candidate_token_ids=ascii_token_candidates(p.tokenizer),eos_token_ids=eos)
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():g=model.generate(**encoded,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint,return_dict_in_generate=True,output_scores=True)
    torch.cuda.synchronize();ids=g.sequences[0,prefix:];constraint.assert_complete(ids)
    require(all(bool(torch.isfinite(score[0,int(token)])) for score,token in zip(g.scores,ids)),'nonfinite selected generation scores')
    raw=p.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False);parsed,errors,warnings=tc.parse_segments(raw,30)
    require(parsed is not None and not errors,'synthetic actual inference contract failed')
    write(out/'probe.stage.json',dict(status='PASS_SYNTHETIC_MAC_LOWRES_8B_INFERENCE',input_tokens=prefix,
        input_shape=[64,1080,1920,3],inference_limit=6144,training_limit_unchanged=6144,video_pixels_per_frame=32768,
        peak_memory_allocated_mib=torch.cuda.max_memory_allocated()/2**20,wall_seconds=time.monotonic()-started,
        logical_parameters=8782459120,base_hash=fingerprint,selected_scores_finite=True,
        relocation=relocation,synthetic_pixels_only=True,contest_media_read=False,quality_claim=False,uploaded=False))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['temporal','spatial','long_probe']);ap.add_argument('scope',choices=['nontest','rematch']);ap.add_argument('output');args=ap.parse_args()
    globals()[args.stage](args.scope,args.output)
