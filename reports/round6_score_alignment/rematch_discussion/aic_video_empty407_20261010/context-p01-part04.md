```


## 原文件全文：reports/annotation_iteration_20261010/contest_results/completion.json
字节=3057；SHA256=b9865a2cb079deeccc7d96f13ffd0c78a372920c4f193f2b7b1a40458d2ef3fb

```json
{
  "utc": "2026-10-09T18:55:13.023341+00:00",
  "status": "PASS_COMPLETE_ONE_426_NEW_TRAINED_IMAGE_SELECTOR_EXPERIMENTAL_ZIP",
  "nontest": {
    "status": "PASS_COMPLETE_IMAGE_SCORE_237STEP_8B_EXPERIMENTAL_ZIP",
    "scope": "nontest",
    "candidate": "/home/inspur/aic_video_work/runs/annotation_iteration_20261010_v2/contest_v1/nontest_01/candidate_IMAGE_SCORE_237STEP_8B.zip",
    "zip_bytes": 241,
    "zip_sha256": "5256ba390a52dbd45e5a75d0c66d9224cdbbbc4b3eea8e14f04d3d394971cc4f",
    "videos": 8,
    "selected_frames": 0,
    "empty_videos": 8,
    "samples": 32,
    "blocks": 8,
    "adapter_sha256": "1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933",
    "logical_parameters": 8774791408,
    "training_optimizer_steps": 237,
    "old_spatial_source_field": {
      "field_frames.jsonl": "c4b53cb7d95442ecaa4c8fa6b82b027fd5779370230a2b97f8c8796526386aed",
      "field_shots.jsonl": "cf4a873053bd2baf24343043eb36f835a5853ce232b409489915329f161c0375",
      "anchor_requests.jsonl": "f630e725ddff54c590a4062c39b98c1b7233773b8c0a391f271378ac157283a7",
      "anchor_output.jsonl": "1ffd45d72c723ec71f973d6b24f5e72d052ddf3f6e3b51150a2e68bacfc1532d"
    },
    "spatial_model_calls": 0,
    "official_score": null,
    "uploaded": false,
    "production_replaced": false,
    "independent_validation_sha256": "13a22aee2a8548cdb31376ca75484e4c279d0fc9ac1eba11062b5c557b2af6d4",
    "quality_evidence": "SEEN_TVSUM_DEVELOPMENT_PROXY_ONLY; NATIVE_PROXY_F_CI_CROSSES_ZERO; AIC_GENERALIZATION_UNKNOWN"
  },
  "rematch": {
    "status": "PASS_COMPLETE_IMAGE_SCORE_237STEP_8B_EXPERIMENTAL_ZIP",
    "scope": "rematch",
    "candidate": "/home/inspur/aic_video_work/runs/annotation_iteration_20261010_v2/contest_v1/rematch_01/candidate_IMAGE_SCORE_237STEP_8B.zip",
    "zip_bytes": 12384,
    "zip_sha256": "01969ab4c8221b279dfa58fe1c9f3c5c47cd01fe8cd7dea312bde93cdb3d6325",
    "videos": 426,
    "selected_frames": 3189,
    "empty_videos": 407,
    "samples": 4439,
    "blocks": 510,
    "adapter_sha256": "1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933",
    "logical_parameters": 8774791408,
    "training_optimizer_steps": 237,
    "old_spatial_source_field": {
      "field_frames.jsonl": "17ba37aadc4cf705e1ff95a78a58d8befcab9e34f7132ef0775f1ed1df0d8bca",
      "field_shots.jsonl": "8e81df10c685527145069cd9c65316ab6341c9da7d6e39bb282ed6c60ce12f1e",
      "anchor_requests.jsonl": "9cb7c4e36597dc8ae723ac3b686b2c3b1f04d5982503478fdf19ee72b18c4798",
      "anchor_output.jsonl": "8f83cd967d7d1f95243ac4ae3cddc7fdb78abb3d4842a78f81f6b187fb1562ab"
    },
    "spatial_model_calls": 0,
    "official_score": null,
    "uploaded": false,
    "production_replaced": false,
    "independent_validation_sha256": "5fdc30627443473133534fab61b27cd2387f1ec947fff49f49d4b5d885b491cf",
    "quality_evidence": "SEEN_TVSUM_DEVELOPMENT_PROXY_ONLY; NATIVE_PROXY_F_CI_CROSSES_ZERO; AIC_GENERALIZATION_UNKNOWN"
  },
  "production_replaced": false,
  "official_score": null,
  "uploaded": false,
  "prior_costs_preserved": true
}
```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3/PROTOCOL.md
字节=4313；SHA256=9dfb8ecf1442568b7738dde2095b2ef4da930c6679782eba55f5c77060cd2e4d

```md
# B8B 最终 adapter 复赛候选

v3工程兼容勘误：训练max_sequence_length=8192原样冻结，不改变任何训练/开发输入或既有结果。v2把该训练内存界错误用于复赛推理；真实相同processor的64帧HD合成CPU输入为12048token，基座原生上下文262144。新独立推理合同max16384，无截断、无帧数或像素改动。真实12048token合成GPU生成/有限选择分数/输出合同、参数与全基座身份通过后才进入复赛恢复。v2成功窗口对象逐个保留，仅原明确发生于generate之前的sequence guard失败及未处理窗口各生成一次，不重跑成功窗口、开发或既有完整非测试链。新扩大的是推理入口准入界，不回写旧冻结协议和失败结果，也不能写成全量复赛原输入<=8192。

继承v2已通过的NONTEST8/427帧/65同帧8B锚点/独立严格ZIP证据；时间提示词、processor、64帧、几何、JSON约束、空间及CPU镜头算法均保持。新的12项CPU检查包含真实Windows时间格式与HD合成输入量纲，4实际native processor case复核。官网上传未授权。

用户“生成一下包中”授权生成Linux完成版8B候选；本轮不上传官网。先按训练前冻结的104/96弱开发单次比较通过停止门，再用原非测试8来源完整链路验收，最后自动426源/521窗口推理并严格打包。Mac训练保持独立。

完整模型参数8,782,459,120，唯一固定Qwen3-VL-8B基座权重在时间和空间中共享计一次。时间用最终5epoch/r16 adapter，空间使用相同8B冻结原生基座、无时间adapter、无二元头、无独立4B。两个阶段分进程加载同样权重，无重复下载。实际加载后的全部基座字节再次与训练冻结哈希比较。

时间保留原R7/A提示词、原最多64 source ordinal抽样与实际原processor默认视频像素预算、30秒窗口/末窗0.2秒资格、greedy256token。新生产版本自始使用已有A_FORMAT_CONSTRAINED_RECOVERY_V1生成时JSON合同：1–5段、有限数、排序非交叠和真实末端，最多4位小数。开发比较遵守原固定greedy无约束协议，生产加合同与开发解码不同，必须区分；不事后裁段/删段/造合法空、调提示词或时间阈值。不是为测试失败挑窗口重试，全部521窗一次确定算法。

输入沿用已审核v4 426元数据/身份/clock registry，416CFR和10native；PTS转换/分数端点/单帧与odd-padding原合同保持。CPU以新8B真实processor跑1/3/63/64合成timestamp测试；源decoder已有合成identity证据仍绑定原冻结实现，新增顺序OpenCV源ordinal读取由非测试实际shots/spatial重开像素逐字节验证。

空间保持原主体中心提示词/128token、合法最大crop几何、HSV .35/GRAY .18镜头阈值、最多8 source-frame锚点间隔与镜头内线性插值。改变基座4B至同一8B是必要参量规模变更，不能单独承诺空间或官方收益。为消除已确证随机seek身份问题，shots和space均从源ordinal0顺序消费并逐帧SHA核验，不随机定位、不用旧测试框/ROI/弱构图框/静默fallback。不展示测试像素或原始模型输出给外部模型。

原8非测试源、v4manifest与registry、代码、最终adapter/训练报告、基座文件、CPU证据逐SHA冻结。所有输出exclusive-create；门未通过或窗口/空间失败STOP并保留，禁止覆盖重试/少交源。100confirm不读取。GPU阶段必须属既有共享gpu_run.py实际祖先进程，继续追加账本与7200秒偏移，累计GPU无限。

本次开发与完整非测试链通过后才进入比赛阶段；空间按真实帧/锚点以及新8B非测试实测耗时登记单次止时与产物占用，不用旧4B速度。每阶段用Windows存活桥接刷新Mac唯一工作根实时容量，Linux动态测量，加入Mac剩余已登记产物与阶段预计输出，合计不超过80GiB，不下载权重/媒体、不抢占外部任务。

最终ZIP仅含predictions.jsonl，426源、全部选择帧合法且同源同帧、完整provenance/重建一致，独立strict loader通过、无缺失/重复/越界、ZIP CRC/最终SHA与本地交付双端一致。格式/工程通过与弱教师指标只分别说明各自证据；官方得分等待用户上传。原33.81 A包保留。

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3/runtime.py
字节=21797；SHA256=9d86d5f5b8248a8ba4fd97f2ff511cf6c1f3722ec8d290a7257eff95f7ee5002

```py
"""Single pinned 8B base, temporal final LoRA, native spatial base only."""
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
HERE=RUN/'b_sft8b_package_v3'
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
    lock=read(HERE/'source_lock.json')
    for path,digest in lock['files'].items(): require(sha(path)==digest,'package source identity changed: '+path)
    a=read(RUN/'temporal_sft8b_dev_v1/admission.json')
    for path,digest in a['files'].items(): require(sha(path)==digest,'fixed training/model identity changed: '+path)
    return a
def inputs(scope):
    a=read(HERE/'inputs.json')[scope]
    require(sha(a['manifest'])==a['manifest_sha256'],'metadata manifest changed')
    from pts_contract import load_clocks
    manifest=read(a['manifest']);clocks=load_clocks(manifest,a['registry'],a['registry_sha256'])
    return a,manifest,clocks

def stage_admission(stage,scope,out):
    decision=read(RUN/'temporal_sft8b_dev_v1/decision.json')
    require(decision['status']=='PASS_FROZEN_WEAK_DEV_GATE','frozen developer gate has not passed')
    admission=read(HERE/('rematch_B8B_v3_'+scope+'_'+stage+'_01.admission.json'))
    require(admission.get('authorized') is True and admission.get('scope')==scope and admission.get('stage')==stage and
        admission.get('output')==str(Path(out)) and admission.get('source_lock_sha256')==sha(HERE/'source_lock.json') and
        admission.get('dev_decision_sha256')==sha(RUN/'temporal_sft8b_dev_v1/decision.json'),'phase admission identity mismatch')
    require(read(HERE/'processor_cpu_01.json')['status']=='PASS_ACTUAL_8B_NATIVE_PROCESSOR','native processor evidence missing')
    if scope=='rematch':
        require(read(RUN/'b_sft8b_package_v2/nontest_01/package.stage.json')['status']=='PASS_COMPLETE_8B_PACKAGE_NOT_SCORED_NOT_UPLOADED','unchanged non-test full chain gate has not passed')
        require(read(HERE/'long_probe_01/probe.stage.json')['status']=='PASS_SYNTHETIC_LONG_INPUT_8B_INFERENCE','actual long input probe has not passed')
    if stage=='spatial':require(read(Path(out)/'schedule.stage.json')['status']=='PASS_EXACT_SCHEDULING','exact scheduling missing')

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
    count=sum(p.numel() for _,p in unique_parameters(model));require(count==8782459120,'complete 8B parameter inventory changed')
    frozen=canonical_frozen_hash(model,torch)
    expected=read(RUN/'temporal_sft8b_full_v1/train_01/train_report.json')['freeze_evidence']['adapter_off']
    require(frozen==expected,'loaded frozen base differs from accepted training base')
    processor=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=processor.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    eos=model.generation_config.eos_token_id
    if isinstance(eos,int):eos=[eos]
    candidates=ascii_token_candidates(processor.tokenizer)
    failures=0;windows=0
    recovery=read(HERE/'partial_recovery_inputs.json') if scope=='rematch' else None
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
                        encoded=processor(text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[md],
                            padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
                    else:
                        plan=native_clip_plan(clock,start,end);arr,md=build_native_clip(item['source_path'],item,clock,plan)
                        with exact_native_pts(processor,plan,fps) as identity:
                            encoded=processor(text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[md],
                                padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
                            verify_native_encoding(processor,encoded,identity)
                        info=dict(n_sampled=plan['n_sampled'])
                        w.update(clock_branch=clock['branch'],clock_record_sha256=clock['clock_record_sha256'],
                            source_frame_ids=plan['source_frame_ids'],native_processor_identity=identity)
                    require(encoded['input_ids'].shape[1]<=16384,'expanded inference sequence exceeds separately admitted 16384 contract')
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
    report.update(inference_max_sequence_length=16384,training_max_sequence_length_unchanged=8192,
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
    require(frozen==read(RUN/'temporal_sft8b_full_v1/train_01/train_report.json')['freeze_evidence']['adapter_off'],'spatial native base does not equal trained frozen base')
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
    require(sum(p.numel() for _,p in unique_parameters(model))==8782459120,'long probe model parameter count changed')
    fingerprint=canonical_frozen_hash(model,torch)
    require(fingerprint==read(RUN/'temporal_sft8b_full_v1/train_01/train_report.json')['freeze_evidence']['adapter_off'],'long probe base identity changed')
    tc=load(CODE/'vendor/temporal_common.py','long_input_tc')
    p=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=p.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    frames=torch.zeros((64,3,1080,1920),dtype=torch.uint8)
    md=dict(fps=30,frames_indices=[14*i for i in range(64)],total_num_frames=900,video_backend='decord')
    encoded=p(text=[prompt],videos=[frames],video_metadata=[md],padding=True,truncation=False,do_sample_frames=False,return_tensors='pt').to('cuda')
    prefix=int(encoded['input_ids'].shape[1]);require(8192<prefix<=16384,'synthetic case does not exercise corrected inference bound')
    eos=model.generation_config.eos_token_id
    if isinstance(eos,int):eos=[eos]
    constraint=make_prefix_constraint(p.tokenizer,prefix,30,candidate_token_ids=ascii_token_candidates(p.tokenizer),eos_token_ids=eos)
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():g=model.generate(**encoded,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint,return_dict_in_generate=True,output_scores=True)
    torch.cuda.synchronize();ids=g.sequences[0,prefix:];constraint.assert_complete(ids)
    require(all(bool(torch.isfinite(score[0,int(token)])) for score,token in zip(g.scores,ids)),'nonfinite selected generation scores')
    raw=p.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False);parsed,errors,warnings=tc.parse_segments(raw,30)
    require(parsed is not None and not errors,'synthetic actual inference contract failed')
    write(out/'probe.stage.json',dict(status='PASS_SYNTHETIC_LONG_INPUT_8B_INFERENCE',input_tokens=prefix,
        input_shape=[64,1080,1920,3],inference_limit=16384,training_limit_unchanged=8192,
        peak_memory_allocated_mib=torch.cuda.max_memory_allocated()/2**20,wall_seconds=time.monotonic()-started,
        logical_parameters=8782459120,base_hash=fingerprint,selected_scores_finite=True,
        synthetic_pixels_only=True,contest_media_read=False,quality_claim=False,uploaded=False))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['temporal','spatial','long_probe']);ap.add_argument('scope',choices=['nontest','rematch']);ap.add_argument('output');args=ap.parse_args()
    globals()[args.stage](args.scope,args.output)

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/PROTOCOL.md
字节=2796；SHA256=1802b180a67928a5ed0e4f2e3d21a2f3bdfa04a8c5e2feadf0cc1cafad03fea7

```md
# B2 v4：显式原生解码修复与仅失败窗恢复

保留已经训练的B最终8B LoRA、v2统一canonical时长、原提示/64帧/16384/greedy/参数。v1/v2所有锁、raw、STOP及成功物保持。

真实provider视频97在送入processor/模型之前，PyAV17.1/libswscale9拒绝yuv420p/unknown primaries/unknown colorspace/log316 transfer，errno95。全434源头元数据仅这一个SHA为此profile，来源SHA8ec893eb5378452de6223f6c8e5878bcea044cb2f9e4feaabf708fa364871722。OpenCV亦打印同转换失败，read的返回不能当合法RGB。

这是独立登记的新像素转换配方：仅此SHA且精确格式/geometry/trc10/space2/prim2/range1匹配时，将用于转换的transfer标记临时设UNSPECIFIED(2)，明确限定范围ITU601 YUV样本映射，完成后恢复原frame元数据。原YUV样本/PTS/尺寸/range/源文件字节不变；不应用或宣称恢复摄影gamma曲线。不按图像内容选颜色参数，没有复赛视觉调参。其他所有来源保持原转换调用，额外未知错误STOP，绝不try/except自动换任意decoder。

source_color_cpu复现真实errno95、合成有限范围参考、真实64帧RGB/BGR通道完全相等/完整native ordinal与PTS/raw YUV不变；processor实际8非测试像素SHA仍通过。全529端点/529越界拒绝/原29错误及12目标无损合同保持。新source_color/recovery及CPU/processor/所有旧必要成功SHA绑定后单次启动。

v1剩余有效GPU生成继续，不重复成功物。v4在provider全426/521时间与wrapper终态完整记账后，仅准入原失败为登记source97的送模型前errno95，逐SHA/原validator核所有成功，保留旧failed raw/stage。原成功记录整行原字节复制，失败窗口在新目录用修复转换实际生成一次，B288张量/基座全SHA/原输入和原validator/CUDA有限分数都须PASS；不补标签、不将失败变空、不减少分母。新recovery stage明确原成功数/新调用数/两个真实wall成本，不修改旧STOP或借失败总stage给成功回执。

时间新完整PASS后，全源CPU镜头/同一source转换空间/恢复合成/独立strict ZIP；8非测试完整门仍先通过。最终唯一426ZIP留Linux，T0/新分未知，B2不是新教师T微调。每15分钟静默核真实provider/controller/回执，自主独立修复，最后真实大小/SHA/CRC/全部strict通过后报告一次并删除监控。共享锁/追加账本/7200offset/真实容量，Mac退出、不回传/官网提交、新大流量许可继续。

额外v4工程审计修复：完整原始新回答在有效性拒绝前先写独立raw回执，异常另写failure/traceback，避免丢失真实新失败回答。原v3仅停止等待controller，未启动恢复GPU，不重复任何新成功生成；旧冻结568文件仍保留。

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/balanced_two_window_risk_v3/PROTOCOL.md
字节=2986；SHA256=dc2a645a592b5add8fcea0041737e349b6420b8427157b28ace9955490eb6b13

```md
# Balanced two-window user-authorized risk experiment v1

2026-10-09 最新用户明确要求“按照讨论出来的方案去训练打包zip，本来我们就是在试的”。据此独立执行讨论中的双窗均衡候选。保留此前讨论和全部科学STOP，当前用户接受风险的授权取代上一轮主控的G0止步决定。独立质量参考、提分和新官网分均UNKNOWN，不宣称旧科学门通过。

原B8B/288adapter、B0 prompt、0..5原grammar、greedy、原native clock/source97颜色白名单、floor64、input16384/output256、原video像素预算不变。此方案仅改变推理输入分区，新optimizer/32B/overview/空间调用0；原B已经训练过，不增加无依据的权重训练。

仅原来恰好两窗且总域严格30<duration<60秒：改为[a,(a+b)/2)、[(a+b)/2,b)。中点Fraction精确计算，不吸附PTS、不epsilon、不裁端点。其他原窗完全相同、按完整旧身份和SHA引用成功。每个新窗采样精确域内整数floor64，真实decoder/processor/token/prefix/raw/原validator和独立有理数成员核验。失败不转空、不合并模型结果、不强行补证据。

先完整NT8原请求精确引用/空间原完整源场/11strict，再真实非测试104中16个变化窗新生成与独立CPU回放；质量方向仅UNKNOWN，不按弱分改提示/门/样本。工程通过后执行完整426/521的新计划：所有变化请求真实生成、其他V14原成功exact引用。全426先完整原空间源场，再按本候选时间选择；原31295空间锚点/18723.876秒和旧V14全部GPU成本/7200offset保留。新GPU自然终态费用唯一追加。

仅独立final PASS、8/426全部11strict、ZIP实际size/SHA/CRC/唯一predictions.jsonl/426身份/原字节、全部新CPU回放和所有真实GPU账本通过才交付。新包可能低于旧最佳37.63，旧最佳不覆盖。包留Linux，不自动回传/官网提交。源/资产/代码先CPU验收再锁定/单次launcher。新工程错误保留trace/raw，在独立版本修复；不修改冻结代码或重跑成功。

工程v2仅排除运行日志与进度/CONTINUE等可变记录的冻结绑定；v1在模型前冻结阶段日志绑定故障保留。132已验输入与原CPU原字节、decoder/processor/grammar算法完全相同移交，模型调用仍0；不修改v1锁。

工程v3修复首实际回答整数范围list/tuple表示误拒绝，真实范围值完全相等，无端点或源ordinal改变。原v2有效raw原字节保留，单独native/processor/token/prefix/原parser CPU回放后exact移交一次；15开发新+1原有效恢复+96旧exact，116复赛新+405原exact。v2失败实际GPU144.4350819280371秒保留，原NT8完整11strict/ZIP原字节移交，不重复成功NT assemble/finish。新版本仅representation、失败trace导入Path及exact恢复计数/控制接口；原B模型/prompt/grammar/输入与科学分区完全不变，不修改v2冻结代码，不重复真实有效生成。

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/PROTOCOL.md
字节=13456；SHA256=e2d9e76650deb3e2b6a7bce76af9b9e9d23225b8547d9e4eddbf3169799cf215

```md
# V14唯一接续：完成教师复查的精确阶段移交

V13完整160标签/160盲第二选择真实成功后，学生CPU准入因原pilot24的diagnostic_only=True停止。原pilot的诊断标记、原raw、标签、支持/UNKNOWN、全部SHA与STOP均保留。新版本仅允许登记完整160 manifest中原pilot24精确成功回执跨阶段作为同教师弱证据，既不把未知转负，也不宣称人工真值或质量提升。外部/修改/新增diagnostic回答继续拒绝。

先Linux CPU复现旧consumer拒绝，并验证新consumer完整160、65train/14dev弱支持及81UNKNOWN/原HTTP/模型/输入/物理帧/原validator。注册完整160精确manifest与独立冻结锁后只启动一次，无新的教师调用。后台完整CPU移交→学生准入→2–4真实更新同optimizer/RNG及288adapter重载→旧B candidate0开发→NONTEST8→426/11独立strict ZIP。未实际更新不能称新T，未全包验收不能交付；历史目录/冻结源码不改、成功模型调用不重复。新大流量先许可，Mac退出，小量SSH控制授权，共享锁/账本7200及外部任务保持。


原科学协议（保持配方、支持判定和UNKNOWN约束）：

V13额外修复：V12在任何GPU/新标注/新复查前因部署漏掉原validator的supervision/teacher_metadata_20261007.json而自然STOP。V12原14562冻结文件/失败日志保持，不重开。这里只部署V11原metadata与schema完全相同字节，并CPU执行当前28条完整verify_blind_review_projection，原13拒绝/160投影/2排序回归保持；其余V12配方原样。

# V13 独立工程修复与完整复查接续

V11 source_lock SHA0ae09ec38ff589baa5e15e16b84457b06442195de502ec7ef6a19bab9b715578。已真实完整标注160（新134/合法复用26），原第二选择28完成，原full GPU charge6748.806357712485秒、exit1/failed/stop_reason null和STOP保持。仅修旧许可V10记录从JSONL读出后对象排序与原canonical字串序列顺序错配。两条旧成功仍按exact manifest和原隔离validator核；返回原始已批准文件parsed对象的顺序，不对回答裁数、重排段或补证据。

V13 v11_resume_manifest在Linux原地逐SHA核160标签/28复查/物理PNG和RGB/原输入/raw/冻结原validator。所有原目录保持；新目录仅复制9MB左右aggregate和validator文件原字节，引用原视频/图像/模型。原学生/生产/科学比较函数原字节保持。新/旧第二选择source-lock绑定只在160原记录exact manifest内允许：新回答绑定V13真实锁；旧回答必须恰为28条已接受原对象/文件SHA，原V11锁。未知旧回答和其他锁拒绝，不放宽通用验证。

新GPU只生成余132独立盲选择；首个原阻塞窗实际新第二选择必须原validator/输入/SHA通过，失败raw不可覆盖保存。已完成标注/复查不能重复。资源预测按28条实际HTTP wall与真实产物大小外推，旧四阶段实际GPU成本分别引用，追加账本7200offset保持。不把引用当零旧成本或新调用。

原弱质量/训练准入不改。未知、分歧保留全160分母，UNKNOWN不当负类；同教师一致性不是人工真值。先完成复查，再按原门选择支持子集/可靠边界/不可用教师三条科学路线。旧B candidate0、原B LoRA lr1e-5/r16/alpha32/dropout.05/有效batch16/最多3epochs、至少2且最多4真实更新前缀/同optimizer与RNG/冻结基座及288张量重载保持。未更新不能称新T。

下列是继承的V11科学协议与历史工程记录；V13跳过已真实完成的视觉/重输入/24小试/160标注调用，只复用经原证据确认的成功；来源与窗口从V11原字节复制，不重新抽样。最终门和B/C自主裁决继续有效。

# 当前唯一接续：teacher_student_autopilot_v11

V10视觉接口8/8与2条真实重输入探针成功，但首个24窗pilot标注的两个区间缺少模型所选物理证据，原validator正确STOP；不是32B权重装载失败或新T训练失败（T仍0更新）。原639冻结文件、失败raw/STOP、两个成功记录全部保留。

V11仅修新输出接口：B前缀边界与F前缀物理帧分离，KEEP每段附模型自行选定的非空证据，固定GBNF只允许该段半开区间内的帧，保留所有合法1..5段与证据子集。程序只做精确PTS/元数据投影，不补造见证、合并/排序/裁段或将失败转空。旧高光定义prompt、原validator、固定160/24输入逐字节不变，不换seed/挑样本。

旧V10已成功2条只按 accepted_resume_manifest 和孤立原validator/全部文件SHA核后原样引用，属于full160且不在pilot24。旧visual8仅在同实际模型/运行时/输入管线与8案HTTP构造body CPU相等后引用；只算旧真实调用和旧GPU成本，新调用0。新格式必须在原失败pilot首窗真实生成通过后继续余23窗，不重复成功探针。

一次controller：真实身份/SHA和B2空间缓存核验→原视觉及重输入容量证据CPU移交→同24实际标注与盲第二选择→逐条分层支持/UNKNOWN与全分母→完整窗口监督合格时完整160标注/复查→B最终LoRA lr1e-5最多3epochs/2–4更新前缀保持optimizer→开发候选0→NONTEST8→426独立strict ZIP。仅边界监督可靠走独立B精修；教师不可靠走独立C同8B全源粗览/局部非测试对照；监控自主实现验收与登记，不盲重试语义。

冻结后不得改source_lock中的文件或重复launcher。读registration/progress/completion、legacy_handoff、pilot/new_format_real_probe、逐窗done/failure/semantic_review、student进度/prefix/完成、NONTEST/rematch全部strict、resource/queue；核真实完整命令/父子PGID/CPU/GPU/RAM/磁盘与共享锁。CPU SHA与顺序解码/合法队列不当卡死。

controller/checkpoint_teacher_v11.py每15分钟静默巡视，故障立即自助复现/独立版本修复。新大流量事先许可；小量控制直SSH、Mac退出、100confirm不读，不看复赛调参。只在真实完整最终ZIP验收后报告；旧B37.63、已交付B2用户37.32（低0.31）分别绑定旧包，新T及新官网分未知。

---

## Historical V10 engineering and retained V8 science protocol

# V10真实重叠边界生成约束修复

v9真实32B视觉接口8/8通过，但第一条非测试探针返回嵌套重叠，被原validator正确拒绝；原HTTP/raw/STOP保持。其真实13675输入token、200输出token无截断，不是下载或装载失败。旧schema仅独立ID enum，生成语言遗漏start<end及跨片段顺序/非重叠关系。

新v10以有限状态GBNF在生成时约束合法原生边界序列：1到5段全部合法选择仍可表达，段内start<end、每段含真实提供帧，下一start>=上一end。schema、提示词、高光标准、原validator和160/24选择原字节保持；直接grammar为单独登记的生成配方修复，不后处理旧重叠输出，不裁段/合并/排序/造空。原事前登记160/24保持，其中已有一条工程失败探针被观察过，不冒充全新未见24；不重新挑样本。两条真实重输入探针在新目录真实生成，旧无效响应不复用为标签。视觉inference入口新增grammar分支，重新测试8个合成接口case有工程必要性，不当作新标签或新科学通过。

先固定运行时CPU：原raw必须拒绝；合法1..5段/贴边/全端点/NO/UNKNOWN及非法重叠倒序/反向/无帧/多于5段验收，然后独立锁/单次launcher。真实24/盲审核/分层UNKNOWN/2..4更新前缀/候选0/开发及NONTEST8/426strict保持下述协议。科学门失败仍按B/C自主准备匹配对照，不无限换提示。

# V9工程修复接续

v8已在B2缓存回执字段status/stage处STOP，GPU调用0/标签0/T更新0，480冻结文件与STOP保持。v9修实际B2回执适配与缓存验收绑定并做真实CPU缓存交接验收；沿用同配方/同输入的原160/24选择原字节，不重复选择或模型生成。当前目录与source_lock/registration为准；下面v8科学协议全部保持。

# V8 独立教师修复与时间监督实验

用户2026-10-08要求按照提供审计修复并接续。旧v1..v7/context全部源码、原答、标签与STOP原样保留；此版本重新登记任务、表示与准入，不宣称旧门通过。

## 修复与成功标准

probe实际新生成且拒绝任何旧done；all/labels对同v8成功逐文件SHA、source/model/prompt/input/原validator核验后复用，只补缺失；review仅审核已有标签。CPU串联实际production函数要验证次数、残缺/失败缓存拒绝与原字节不变。

教师与学生观察相同局部自然30秒/floor64/nativePTS，不给教师额外全源摘要。模型仅输出KEEP/NO_HIGHLIGHT/UNKNOWN、整数边界ID、独立证据帧ID及简短依据；程序拥有nativePTS/原source序号/窗口尾边界。窗口尾无证据帧；禁止float拷写、裁值、补造帧、UNKNOWN当负。原模型回答与canonical程序转换记录分别保存并绑定，原validator验派生格式不冒充原短答。

## 一次有限实验

使用现存固定32B Q4_K_M+F16 projector与原CUDA运行时，不下载/升级。八个合成观察接口case（含64帧正反序）测红方块开始/中/尾、换图/反序/单帧替换；只验视觉输入，不作高光标签。完整真实NONTEST教师重输入probe先执行，随后未经旧提示词修订使用的新24（16train8dev），来源组全部排除旧160。每条独立盲判断先产生再由程序比较，保留所有原答/分歧/UNKNOWN和全分母。相同模型一致性只作弱证据，非人工真值。

整窗空例不设配额，也不作为小试继续收集的硬门。逐条工程有效性与科学可用性分开。实际无法证明完整观察/语义一致者不进入完整窗口监督，争议不转空；原正例补集不当负真值。逐条可用/拒绝/UNKNOWN、各split和来源分布全部报告，不声称过滤后代表全部数据质量。仅明确新工程原因才另立第二次匹配实验；不反复换提示词直到有NO。

小试另登记选择坍塌诊断：按每条原始完整决定累计保留时长占窗口时长，比例≥0.99的条目达到22/24，或任一split全部原始条目均恰好选择[0,duration)，判为明显整窗选择坍塌，不进入A的全量监督收集。记录24条全分母、所有比例和命中ID；该规则不要求正/空类别比例、不把争议改成空。仅程序交付全部计划帧与盲ID选择一致不能证明模型完整理解或事实真值，原记录和弱一致性限制均保留。存在可证实事件边界再独立取B证据；全窗坍塌不能自身充当B边界可靠证明。

## 路由与接续

优先A：24提供可用完整窗口弱证据且无明显整窗坍塌时，继续登记128train32dev；每条盲审核和身份核验，只有可靠完整窗口进入学生目标。无真实NO时记录拒绝行为未得到监督，不能称已解决全空识别。训练从原37.63对应B最终LoRA续训，语言q/k/v/o r16 alpha32 dropout.05，基座/视觉冻结，lr1e-5有效batch16最多3epochs。前缀2..4实际更新（min4与实际总步，至少2）验finite loss/grad、全基座冻结、288adapter保存和独立CPU重载；同optimizer/RNG/scheduler继续，不增加曝光凑20。开发candidate0保留原B，同production输入/解码比较，弱教师指标不当官网分。退化轮拒绝/科学早停，选择合格旧B或先前轮；不能自动称新T胜出。

B：完整窗口语义不成立但非测试明确事件边界可靠时，独立登记候选+B边界精修小adapter；候选外UNKNOWN不监督为负，旧B候选adapter保持。先取真实边界对照证据，不能用A剩余正样本偷偷当B完成。

C：连简单观察/边界也不可靠时停止此教师标注，不无限重跑。独立登记同8B全源粗事件表→局部定位的非测试匹配对照；无改进或全局幻觉广泛退化保留B/B2。B/C由当前真实24回执触发，监控Agent继续准备执行，不等待用户。

只改本轮时间监督，空间保持同8B基座原生模式；不加RL/稠密头/空间LoRA。保留已验B2的唯一97SHA/profile显式样本转换与canonical duration修复，其他源默认路径，未知错误STOP。全源空间仅在全部算法/模型/源/采样/请求/回执SHA同一后原样复用B2完整空间，不复用B2时间预测；复用与新GPU成本分开计。

## 资源和交付

既有SSH aic-inspur-home/Linux独立后台，Mac不参与。真实容量、共享GPU锁和追加账本7200历史偏移保持，无人为disk/RAM/VRAM额度。不抢占外部任务、不改系统/连接，不读100confirm或手看复赛调参。控制代码小量部署授权；任何新大传输先说明规模方向链路/可能机场消耗等用户许可。

真实训练/开发→NONTEST8完整独立strict→426/521时间与全源空间→独立strict ZIP才完成。实际ZIP大小/SHA/CRC/唯一JSONL/426身份全部核验；只有PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX可报告训练路线的真实包，candidate0必须明确旧B被选、实际T更新及未胜出。不自动官网上传/回传。旧B37.63对应旧SHA86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54；B2已由用户截图指认37.32/DONE，对应0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3。新候选官网分未知。

```


## 原文件全文：reports/round6_score_alignment/rematch_discussion/aic_video_post_sg8_20261009/pro-p01.md
字节=21278；SHA256=c102f3970b3451b6b93f59f4aec15d889c3de6f5a437b51bfd8bf282002d14b6

```md
# POST-SG8 技术裁决：执行一次有界G0与双窗精确计划，本轮明确NO426

**连续任务：AIC-VIDEO-REMATCH-NEXT-20261005。此次为slot5/8，本次后剩3次；不重置旧额度。**

## 读取范围与证据边界

本次读取的是**本条新上传**的索引及六卷，前五个文件使用带`(1)`的附件路径，没有误用旧四卷版本。

| 新附件 | 实际本卷读取范围 | 对应完整正文行号 | 原始字节数 |
|---|---:|---:|---:|
| `context-p01-index(1).md` | 1–69 | 索引全文 | 2,361 |
| `context-p01-part01(1).md` | 1–2066 | 1–2066 | 139,971 |
| `context-p01-part02(1).md` | 1–1924 | 2067–3990 | 139,765 |
| `context-p01-part03(1).md` | 1–1883 | 3991–5873 | 139,980 |
| `context-p01-part04(1).md` | 1–2556 | 5874–8429 | 139,996 |
| `context-p01-part05.md` | 1–2174 | 8430–10603 | 139,933 |
| `context-p01-part06.md` | 1–680 | 10604–11283 | 51,841 |

初始展示及一处长段输出曾截断，均已分段补齐；最终读至`END_REPLAN_P01`。**对本对话附件副本**按原始字节拼接核对，得到751,486字节、11,283行，SHA256与索引一致：

```text
ae94182cc4b029ae49b195776b53aa24484d59e1dad9b2e361d019003534af44
```

**这不是对Linux原件、实际媒体、模型权重或执行流水线的主机独立复验。**下文采用卷宗中的执行证据；本次没有运行模型、解码媒体、发起远端写操作或重新执行SG8验收。新旧分卷范围以本次索引为准。context-p01-index

---

## 一、唯一决策

**主控接下来只执行一个工作包：**

> **`post_sg8_reference_g0_slot5_v1`：有界的已有参考资格核验＋开放开发集双窗精确CPU计划。总计最多60分钟有效执行工作，完成后封存结果并以NO426结束本轮。**

本工作包**不启动均衡二分的16窗模型实验，不训练，不生成新426包，不自动转任何后备路线**。即使找到有潜力的参考，也只封存其适用范围和资格证据，不让“发现一个标签文件”自动触发训练或生产。

这里的60分钟是**本次投入上限，不是完成时间承诺，也不是每个入口各60分钟**。如果没有未审计且可合法读取的新入口，参考支项提前结束；仍完成已委派的双窗计划或明确记录其阻塞，到限即收口。

### 为什么这次不购买均衡二分风险包

我仍认可：**先划分输入窗口、再完整映射模型原段，与生成后裁段是不同算法。均衡二分没有被SG8证伪，也不因缺少人工真值就天然禁止研究。**

但“允许研究”不等于“当前值得投入426”。本轮可用的正向理由仍是短尾上下文不对称；可观测的新增结果仍主要是输入、采样和模型行为变化。与此同时，它会失去部分旧采样、缩短原主窗上下文，并新增中点边界。**现在没有成立的判据，能够判断这些交换更接近任务目标，而不只是更接近我们偏好的输出形态。**

上次SG8至少有一个事前明确、可以作方向比较的有限命题：是否更接近隔离的同模型逐帧输出。那个命题虽然不是真实构图质量，仍可被实验否证；它现在确实没有通过原门。均衡分区目前提出的“集合变化”“跨缝长段”“极端状态不超过若干个”，没有提供同等清楚的误差方向依据。**不能因为前一项可否证实验失败，就给下一项换成更容易通过的行为条件。**

这不是宣布“以后无真值一律不准产包”。这是本节点的投入选择：**先补齐尚未完成、且范围可以严格限定的证据资格与输入计划；本轮不购买未知方向的整包比较。**

---

## 二、先锁住SG8结论，防止把科学STOP重新包装成工程问题

| 已有证据 | 本次采纳的准确含义 |
|---|---|
| 8个登记来源组、56个隔离相位 | 统计单位是来源组，不是56个独立样本 |
| 53次真实新空间推理＋3条旧成功精确引用 | 不是56次新推理；32个原支持点未重跑 |
| 确认组3/6为正 | 未达到原定至少4/6 |
| 确认均值−0.0026950568804326776；全8组均值−0.002307551408911853 | 原方向门未通过 |
| 确认留一条件失败 | **不能扩写为“全部六个留一均值都为负”** |
| 独立原raw、parser、有理数面积、多项式及费用闭环通过 | 支持按原合同结束，不支持改公式或降门补考 |
| G2退出 | 没有真实G3新完整空间场，也没有新426包 |

以上由SG8终态及独立验收摘要支持。context-p01-part05 context-p01-part05

**SG8没有证明“高阶插值一定放大锚点噪声”，也没有测出人工构图质量下降。**它只证明这份固定方案没有取得其预先要求的支持。无需为了接受STOP，再补一个未经验证的因果故事。

费用也保持原归属：v1生成前失败的103.09017407242209秒、v2的495.22363770753145秒分别保留；原空间约18,723.876秒及7200秒历史偏移不抹除。独立closure记载的165行账本是当时终态，不是未来写入位置。context-p01-part05

V14同样不能重写历史：**15次优化器更新真实发生，但按开发选点规则选回原B；不是“没训过”，也不是“全部未来微调无效”。**原65条CE、原160教师流程、C/B1/D/Q和42次边界诊断，本轮均不重开。context-p01-part01 context-p01-part01

---

## 三、为什么新GNMC协议没有打开训练或426出口

新读到的`reference_protocol.md`第7条明确限定：

> GNMC试点仅授权本地非商业诊断；不得据此批准训练、比赛测试、打包或提交。

该文件同时要求原生目标比例、源身份、来源隔离，并规定稀疏视频只评已标帧。context-p01-part06

因此必须分开三件事：

**第一，项目登记用途。**这份协议可以证明项目曾登记过受限诊断用途，不能当作本次训练或比赛生产的准入依据。

**第二，具体资产使用权。**它是项目参考协议，不能仅凭其存在，就补齐每个源视频及派生标注的权利证据。旧四源审计中未找到的每视频许可，不因出现这份内部协议而自动变成PASS。

**第三，参考的科学用途。**原生16:9单编辑构图参考，即使资格成立，也不自动成为9:16构图真值，更不能评价均衡二分的时间高光选择。稀疏已标帧之外仍不是负例。

**“可本地诊断”“可作为某种有限参考”“可用于训练或比赛决策”必须分别登记，不能合并成一个`eligible=true`。**

这也纠正了两个相反的过度推断：

- 原inventory为0，只说明**没有已登记的独立构图authority**，不能推论全盘不存在其他参考。
- 其他资产尚未扫描，也不能推论那里一定有可用新监督。

只读核验已明确记录`UNKNOWN_NOT_SCANNED`；p1b默认未标注、987条豆包来源和未获许可的LIVE_YT_VC也不能重新算作现成独立标签。context-p01-part06

---

## 四、可直接派发的工作单

### 工作边界

执行主机仍为Linux，使用既有授权和既有连接；**本回答是工作单，不是已启动回执**。

只允许读取规定范围内的现存协议、清单、标注schema、来源登记、曝光记录和已保存的native时钟表。允许在独立新目录写入本次CPU工具、清单及报告。**不读取媒体像素、不调用decoder或processor、不加载8B/32B、不下载、不联系作者、不打开100confirm、不读取复赛预测来选配方。**

本次程序不应提供`train`、`infer`、`rematch`或`package`执行子命令，避免出现“G0通过后旧控制器自动接续”的隐含路径。

### 工作A：固定入口的参考资格核验

先由以下**已点名入口的明确本地引用**构造清单，不全盘搜索，不递归追逐外链：

| 入口 | 本次只补什么 | 已有结论如何处理 |
|---|---|---|
| `context_advisory_v1/fallback.py`及其绑定的NONTEST/developer计划、authority登记 | 是否明确指向尚未审计的本地参考资产 | 已登记authority为0直接引用，不重复跑旧inventory |
| p1b的`pilot_manifest`及其标注状态登记 | 是否有此前未核的、实际完成标注的现存文件 | 默认`UNANNOTATED`不当成标签 |
| `existing_16x9_reference_audit`及其明确引用的本地许可、映射文件 | 只补此前UNKNOWN且确有新文件支持的字段 | 原四源有效语义0、人工复核0等旧结果保留 |
| `round3 label_origin_audit`及来源登记 | 是否存在明确不同来源、未审计的新条目 | 987条`api_doubao`保持弱参考身份 |
| p2r9候选矩阵 | 是否指向已经本地存在、已有读取许可且未审计的资产 | `PERMISSION_REQUIRED`、未下载、仅外链条目直接记阻塞 |
| 新GNMC参考协议 | 精确记录用途限制及其覆盖的资产范围 | 不升级为训练、比赛测试、打包或提交许可 |

这些入口和“只补未知、不重复已知失败”的范围有卷宗依据。实际路径必须从现有登记解析，不能靠文件名猜绝对路径。context-p01-part06

**清单第一次冻结后，不因发现参考质量差而继续扩目录。**只有明确指向、当前许可允许读取、且确实尚未完成相同资格检查的条目，才进入本次增量审计。

每条资产至少逐项记录：

| 字段组 | 必须回答的问题 |
|---|---|
| 存在与身份 | 文件是否实际存在；版本、文件SHA及所引用旧回执是什么 |
| 生成来源 | 人工、模型、混合还是未知；是否完成标注；采用什么协议 |
| 任务适配 | 时间选择还是空间构图；有无query；原生目标比例是什么 |
| 映射与覆盖 | 源文件、来源组、坐标或时间基准是否可追溯；哪些范围有判断，未选含义是什么 |
| 使用范围 | 元数据读取、本地诊断、训练、比赛用途及对外共享各自有何依据 |
| 本任务曝光 | 是否参与过训练、选点、选方案或既往查看；是否由当前候选输出派生 |
| 当前结论 | 每项`PASS / FAIL / UNKNOWN`及证据位置，不只给一个总通过标志 |

其中，`PASS`只能表示对应资格字段得到证据支持，**不表示已经独立看过画面、验证语义正确**。来源隔离也不等于模型预训练绝未见过该视频。

缺少隔离依据时，不能通过打开100confirm来“补证”；只引用此前可用的保护登记，无法核清就记UNKNOWN。模型预测缓存不转为人工参考，只有正例的时间标签不把补集补成负例。

### 工作B：全部适用双窗记录的纯CPU精确计划

这部分使用开放开发manifest、原窗口计划及**已经存在的native PTS表**，不读取新旧预测答案或弱标签来挑记录。

必须先实核：

**104条记录中实际哪些旧计划恰有两窗、对应多少真实来源组、许可范围是什么。**现有证据支持8条双窗记录和8个相邻接缝，但尚不能把它写成8个独立来源组。NT8没有接缝，不移植其来源组验收作为这8条开发记录的证明。context-p01-part06

本次只规划以下规则，不扩大成任意多窗均分：

\[
W_{\rm new}=
\begin{cases}
\{[a,m),[m,b)\},&\text{旧计划恰两窗且 }30<b-a<60,\\
W_{\rm old},&\text{其他正常情况},
\end{cases}
\qquad m=\frac{a+b}{2}.
\]

时长恰60秒时，须核新旧边界及计划确实一致，才记录恒等。旧计划异常、有缺口或身份冲突则标阻塞，不能归入正常恒等分支。

**精确实现要求：**

1. 从原登记数值的规范表示构造有理数，不用报告里四舍五入的“约30.3秒”重建边界；不假设源起点为0。
2. 中点**不必落在某个物理帧PTS上**。禁止为此吸附到帧或加入epsilon。
3. 对已有PTS表 \(P_j\)，分别建立
   \[
   I(a,m)=\{j:a\le P_j<m\},\quad
   I(m,b)=\{j:m\le P_j<b\}.
   \]
   两者必须不相交，并完整覆盖原许可域中的物理帧。
4. 对一窗中连续的 \(N\) 个物理ordinal，\(N\le64\)时全部取用；否则按原floor64合同取
   \[
   j_k=j_{\rm first}+\left\lfloor\frac{k(N-1)}{63}\right\rfloor,\quad k=0,\ldots,63.
   \]
   不换为nearest64，不补插值帧。
5. 检查中点、局部时长及源时间转换能否由现有消费者保持同一语义。发现序列化或浮点接口改变半开归属时，记录具体反例并阻塞；**不为了让计划通过，静默舍入或修改旧端点。**

每条适用记录输出旧新窗口、实际来源组、旧尾长度、物理帧数、floor64计划索引，以及**新增与丢失的采样ordinal**。同时分别报告旧主窗区域和旧短尾区域中的采样间隔变化，而不是只报整体平均密度。

原30秒接缝两侧是否有计划样本、新中点两侧间隔多大，可以由现存时钟计算；**“这些样本是否含有更有效的语义信息”仍是UNKNOWN。**

原理上，生成前均分并完整投影模型段不属于输出裁段；但此工作单尚未运行模型。可以用合成区间测试消费者不裁、不延长、不混用旧新答案，不能据此声称真实模型原段已验收。

### 工作C：独立检查并关闭工作包

建议只实现四个职责明确的小模块：

| 模块 | 职责 |
|---|---|
| `qualify_references.py` | 固定入口、用途资格及曝光证据 |
| `plan_two_windows.py` | 纯元数据精确分区、native PTS归属和采样增删 |
| `verify_g0.py` | 独立重算计划与资格结论，检查禁止项和报告一致性 |
| `run_g0.py` | 一次运行、总时限、阶段结果与终态；无GPU或426分支 |

**不要导入会触发模型加载、解码或旧自动接续的通用controller。**纯计划器只接收已解析的元数据。

新CPU测试至少覆盖：非零源起点、单窗、恰60秒恒等、三窗以上保持、二分点恰有或没有物理帧、半开边界唯一归属、空物理窗口拒绝、非法数值、不同文件同来源组、禁止路径访问，以及**GNMC本地诊断资格不能使训练/比赛准入变成True**。

这些测试是本单要实施的要求，**不是本次已完成的验收结果**。旧SG8的53次CPU回放、原strict、旧完整空间场以及18104项冻结文件，不重新跑一遍来填工作量。

---

## 五、前瞻成功门与停止门

本轮不设置任何“涨分门”。设置的是**工作完整性、资格和计划门**：

| 结果 | 精确含义 | 后续动作 |
|---|---|---|
| `NO_NEW_AUDITABLE_ENTRY` | 固定入口没有指向新的可审本地资产 | 结束参考支项，完成双窗计划后NO426 |
| `NO_REFERENCE_ESTABLISHED` | 有资产，但用途、来源、监督含义、映射或曝光史仍缺证 | 列明缺项，不用UNKNOWN填充通过；NO426 |
| `REFERENCE_QUALIFIED_FOR_DECLARED_PURPOSE` | 某资产的特定用途资格成立 | 封存其适用域与证据；**本轮仍不评分、训练或426** |
| `PASS_TWO_WINDOW_PLAN_ONLY` | 既有元数据足以证明精确分区及采样计划成立 | 保存计划，不能改写为真实输入或模型验收 |
| `STOP_PLAN_CONTRACT` | 时钟、来源、许可域或消费者映射存在具体阻塞 | 保存最小反例，不修改端点救过门 |
| `STOP_G0_SCOPE_OR_BUDGET` | 越出白名单、触及禁止数据或达到总时限 | 保存已完成范围及未完成项，停止扩展 |

**本工作单所有正常和阻塞出口，最终都汇总为`NO426`。**不存在“未找到参考→风险推理”“资格PASS→自动加载模型”这两条控制流。

如果发现任务匹配、来源可追溯、用途适当的新参考，下一次可行动的信息应是**具体哪份资产、支持哪个目标、允许什么用途、还缺哪个证据**，而不是再写一句“建议找高质量标签”。是否据此开展新的有限实验，必须针对那份真实新信息重新冻结；不必为了知会消耗一次Pro，也不能把本次NO426回写成GO。

### 真实GPU和训练条件

**本单没有准入真实GPU的分支，新增优化器更新固定为0。**原因是目前没有成立的新训练目标与监督依据，而不是“模型再也不能提高”。

纯CPU计划也不能提供以下验收：

- 实际解码RGB或像素SHA一致；
- 实际processor grid、token长度、显存峰值；
- 新模型原raw及完整区间投影；
- 新NONTEST8或426的11项strict；
- 新官方成绩。

这些字段应记`NOT_RUN`或`UNKNOWN`，不填PASS，更不把0次调用写成“零失败实验成功”。

---

## 六、我为什么否决当前行为门，而不是再替它挑一个数字

### 最强反例仍然穿过原跨缝GO

考虑一个**构造例，不是本题实测标签**：

许可范围为\([0,30.3)\)，均分点为15.15秒。新右窗输出完整合法原段\([15.2,30.2)\)。它不是整窗，跨过旧30秒接缝，两侧有真实帧，也可以改变最终选择集合。

然而，这个长段可能大部分无关；新中点附近原来完整的事件可能被拆散，旧0.3秒尾窗曾密集看到的短瞬态也可能因新采样变稀而遗漏。**非整窗、跨旧缝、集合变化可以全部成立，选择质量仍然更差。**卷内Tibo已给出这一反例。context-p01-part06

Gemini后加的“至少3个新99%全选或全空才阻断”也没有补上这个缺口：刚才的误报可以低于99%，遗漏也不必表现为整窗变空。它是一个拟议的行为限制，不是已有数据支持的质量判据。

全104均值还会被96条恒等记录稀释。卷内构造例中，8条受影响记录假设分属8组，5条弱F1各降0.8，其他记录不变，全104均值仅下降约0.03846；下降组占受影响组62.5%。这足以说明原0.05／75%粗门可能放过严重的局部损失，**不是证明这些弱F1就是真实质量**。context-p01-part06

我的处理不是再换一个全选比例、组数或分母来“修好放行门”，而是**本次不让这些行为指标承担质量准入职责**。新增99%／3窗条件及“几十次调用”的成本表述，卷末主控也已明确指出缺乏依据或与190窗上界不一致。context-p01-part06

### 对本裁决最强的反对意见

**可能所有已许可资产都没有新参考，G0最终没有新包；均衡二分即使没有方向证据，仍可能实际提高官方分。**

我接受这个机会成本，不声称NO426在未知真实分数上必然最优。选择G0的理由是：它用一个短、可提前结束的工作包，补齐目前确实未完成的资格字段和真实采样交换；而不是继续购买一批无法用当前条件判断方向的新答案。

因此本轮结束后，不应自动开始“第二次寻找参考”，也不应因GPU空闲而启动均衡二分。**没有新证据就是这份工作单的终点，不是无限等待人工的起点。**

---

## 七、最终产物与费用验收

工作包应留下以下可审查产物，实际路径在新目录建立时登记：

| 产物 | 内容 |
|---|---|
| `input_scope.json` | 本次白名单、真实路径、版本／SHA、允许用途和引用来源 |
| `reference_qualification.jsonl` | 全部审计条目、逐字段结论、排除或未知原因 |
| `source_exposure.json` | 来源派生、组关系及本任务训练／选法曝光证据 |
| `two_window_plan.json` | 全部适用记录的精确边界、PTS归属、floor64及采样增删 |
| `cpu_acceptance.json` | 本次新CPU合同、独立计划重算结果及失败反例 |
| `closure.json`、简短结论 | 实际读取范围、未完成项、费用、禁止项计数及最终NO426 |

**不生成`predictions.jsonl`或候选ZIP，不重复封装旧包伪装成新候选。**

费用记录为本次实际CPU时间、文件读取量、峰值占用和产物大小；新增模型、decoder、processor及优化器调用均应为0。没有GPU作业，就不伪造一次`completed`的GPU回执。其他合法作业若追加了共享账本，应核实是正常追加，不要求整份共享账本始终不变；**旧记录、7200偏移和历史空间成本必须保留。**

旧B37.63仍保护原ZIP：

```text
86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54
```

本轮不比较旧B与V14逐例测试预测来决定方向。Grok已撤回该提议；只读或聚合并不会把“据测试输出选择／取消配方”变成单纯完整性检查。context-p01-part06

对席位来源另作一处明确说明：卷内`sol-r01.md`正文仍保留均衡风险与跨缝门的旧表述，**Sol最终撤回由本次用户说明及卷末`host-pre-pro.md`登记提供**；不能声称所附Sol正文已经逐字同步撤回。我的裁决不以三比一或所谓全文共识为依据。context-p01-part06 context-p01-part06

## 最终执行结论

**现在安排：一次有界的增量参考资格G0＋全部适用双窗记录的精确CPU计划。只补未知，不重验旧成功；不启动新GPU，不训练，不产新426。**

**GNMC保持本地诊断用途，SG8保持原NO426，均衡二分保持“工程上可讨论、质量方向未成立”的状态。**完成工作单后，交付具体资产资格、计划收益与损失、阻塞证据及NO426终态；没有新证据就结束本轮，不靠剩余额度、换阈值或另起同类实验延长流水线。
```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/official_rematch_snapshot.txt
字节=4125；SHA256=c5e218ca636c4a8c102e51b8a8d223dd12b612c35e2755e9da2fa07b29db3e04

```txt
Title: 全球校园人工智能算法精英大赛 智青春·算未来

URL Source: https://www.aicomp.cn/notice/notice-3/5307.html

Markdown Content:
关于举办产业命题赛道“基于视频大模型的通用视频高光剪辑”复赛的通知

各参赛团队：

2026年第八届全球校园人工智能算法精英大赛产业命题赛道“基于视频大模型的通用视频高光剪辑”赛题报名将于9月30日11:00截止，初赛赛题结果文档提交截止时间为9月30日11:30。结合赛事整体组织安排，经大赛组委会研究决定，现将复赛有关事项通知如下：

###### 一、赛程安排

1.复赛数据集开放时间：9月30日18:00；

2.复赛赛题结果文档提交开始时间：10月1日09:00；

3.复赛赛题结果文档提交截止时间：10月23日20:00；

4.复赛作品文档提交截止时间：10月25日23:59。

###### 二、评审原则

1.初赛晋级。参赛团队须于9月30日11:30前提交初赛赛题结果文档，且在初赛排行榜上成绩得分＞0分的团队，方可进入复赛。

2.复赛数据集下载。复赛数据集开放后，各参赛团队登录大赛平台，查看“我的参赛信息—详情”，即可下载复赛数据集。

3.复赛成绩。复赛阶段，参赛团队每日可提交5次赛题结果文档，最终以复赛阶段排行榜最高得分为最终成绩（因排行榜存在算分延迟，最终成绩以组委会公示结果为准）。

4.复赛评测。复赛阶段实际推理所使用的主模型及辅助模型总参数量不得超过 9B。参赛团队须在技术报告中如实填写模型总参数量。参数统计口径及违规处理方式详见《基于视频大模型的通用视频高光剪辑算法赛题规则》（附件 1）。

5.复赛作品提交。参赛团队需在规定时间内提交参赛作品文档。作品提交截止日期后，不再接受任何形式的修改和补充。评审团队对复赛参赛作品文档进行结果复现与审核，如有疑问，将要求参赛者进行解释说明。

6.复赛评奖规则。以复赛排行榜得分为依据评选复赛一、二、三等奖，获奖作品数量分别按照不超过15%、25%、30%的比例取整计算。复赛一、二等奖获奖作品将推荐参加半决赛。

###### 三、作品提交注意事项

参赛队伍需将复赛提交内容（预测结果JSONL文件、算法代码、模型文件与运行环境、技术报告）提交至大赛平台。提交前，需按指定入口和文档命名规则仔细检查作品文档，确保内容准确且无格式错误。作品提交要求详见《基于视频大模型的通用视频高光剪辑复赛作品提交要求》（附件2）。

###### 四、联系方式

赛题QQ群：389921008

国赛组委会联系电话：025-85778806

国赛组委会仲裁邮箱：office@aicomp.cn

大赛官网：[www.aicomp.cn](https://www.aicomp.cn/)

**附件:1.**[基于视频大模型的通用视频高光剪辑算法赛题](https://www.aicomp.cn/wp-content/uploads/2026/09/%E9%99%84%E4%BB%B61-%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E7%AE%97%E6%B3%95%E8%B5%9B%E9%A2%98-0930.pdf)

**[2.基于视频大模型的通用视频高光剪辑复赛作品提交要求](https://www.aicomp.cn/wp-content/uploads/2026/09/%E9%99%84%E4%BB%B62%EF%BC%9A%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E5%A4%8D%E8%B5%9B%E4%BD%9C%E5%93%81%E6%8F%90%E4%BA%A4%E8%A6%81%E6%B1%82-1.pdf)**

[关于举办产业命题赛道“基于视频大模型的通用视频高光剪辑”复赛的通知](https://www.aicomp.cn/wp-content/uploads/2026/09/%E5%85%B3%E4%BA%8E%E4%B8%BE%E5%8A%9E%E4%BA%A7%E4%B8%9A%E5%91%BD%E9%A2%98%E8%B5%9B%E9%81%93%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E5%A4%8D%E8%B5%9B%E7%9A%84%E9%80%9A%E7%9F%A5-1.pdf)

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/baseline_a_pts_v1/vendor/temporal_common.py
字节=8859；SHA256=bb8f47896e20e069e9ddf992d94488132ccbee46dc850a2658851f4aa52946b4

```py
#!/usr/bin/env python3
"""temporal_round5 — shared query-free temporal I/O.

Virtual clip:
  The clip is taken ON THE FLY from the source video at
  [clip_start_sec, clip_end_sec]. No clip files are rendered in batch.
  `qwen_vl_utils`' own video_start/video_end slicing records ABSOLUTE frame
  indices, so the processor would label the clip with absolute source times.
  To make the model see time starting at 0 we decode the clip's frames
  ourselves and hand the processor 0-BASED `frames_indices` plus the source fps,
  which makes `_calculate_timestamps` produce clip-local seconds.

Prompt: one query-free prompt, identical for every arm and for training.
  It never receives a QVHighlights query, a teacher summary, cropRois or any
  test-set information.
"""
from __future__ import annotations

import json
import math
import re

MAX_FRAMES = 64
MAX_PIXELS = 128 * 32 * 32           # same per-frame budget as the frozen baseline

PROMPT = (
    "You are shown a short video clip. Identify every time interval in the clip that is "
    "worth keeping in a short highlight edit.\n"
    "Times are seconds measured from the START of this clip, where 0 is the clip start.\n"
    'Return ONLY JSON of the form {"segments": [[start_sec, end_sec], ...]} using '
    "clip-local seconds.\n"
    "Rules:\n"
    "- every interval must satisfy 0 <= start_sec < end_sec <= clip duration\n"
    "- return between 1 and 5 intervals\n"
    "- sort them by start time and do not let them overlap\n"
    "- output nothing except the JSON"
)

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)"


def build_virtual_clip(source_path, clip_start_sec, clip_end_sec, max_frames=MAX_FRAMES):
    """Decode the clip's frames and build 0-based video metadata.

    Returns (frames_uint8_THWC, metadata, info).
    """
    import numpy as np
    import decord

    vr = decord.VideoReader(str(source_path))
    total = len(vr)
    fps = float(vr.get_avg_fps())
    if fps <= 0 or total <= 0:
        raise RuntimeError(f"unreadable video {source_path}: total={total} fps={fps}")
    sf = int(math.ceil(max(0.0, clip_start_sec) * fps))
    ef = int(math.floor(clip_end_sec * fps))
    sf = max(0, min(sf, total - 1))
    ef = max(sf + 1, min(ef, total - 1))
    n_clip = ef - sf + 1
    nframes = int(max(1, min(max_frames, n_clip)))
    if nframes == 1:
        local_idx = [0]
    else:
        local_idx = [int(round(x)) for x in np.linspace(0, n_clip - 1, nframes)]
    abs_idx = [sf + i for i in local_idx]
    arr = vr.get_batch(abs_idx).asnumpy()          # (T, H, W, C) uint8
    md = {"fps": fps, "frames_indices": local_idx,
          "total_num_frames": n_clip, "video_backend": "decord"}
    info = {"source_total_frames": total, "source_fps": fps,
            "clip_start_frame_abs": sf, "clip_end_frame_abs": ef,
            "n_frames_in_clip": n_clip, "n_sampled": nframes,
            "clip_local_indices": local_idx, "absolute_indices": abs_idx,
            "clip_local_times_sec": [round(i / fps, 4) for i in local_idx],
            "clip_duration_sec": round(clip_end_sec - clip_start_sec, 6),
            "sampled_span_sec": [round(local_idx[0] / fps, 4),
                                 round(local_idx[-1] / fps, 4)]}
    return arr, md, info


# ---------------------------------------------------------------- parsing
def parse_segments(raw, clip_duration, max_segments=5):
    """Strict parse -> (segments|None, errors, warnings).

    Accepts only a single JSON object with a "segments" list of [a, b] pairs.
    Ranges must be numeric, finite, 0 <= a < b <= clip_duration.
    Overlaps are reported; the returned list is sorted and merged-free (the
    evaluator uses the UNION, so overlaps do not inflate the score).
    """
    errors, warnings = [], []
    if not isinstance(raw, str) or not raw.strip():
        return None, ["empty model output"], warnings
    objs = re.findall(r"\{(?:[^{}]|\{[^{}]*\})*\}", raw, re.S)
    found = None
    for o in objs:
        try:
            d = json.loads(o)
        except Exception:
            continue
        if isinstance(d, dict) and "segments" in d:
            if found is not None:
                return None, [f"ambiguous: more than one JSON object with 'segments'"], warnings
            found = d
    if found is None:
        return None, ["no JSON object containing 'segments'"], warnings
    segs = found["segments"]
    if not isinstance(segs, list):
        return None, [f"'segments' is not a list: {type(segs).__name__}"], warnings
    if len(segs) == 0:
        return None, ["'segments' is empty"], warnings
    if len(segs) > max_segments:
        return None, [f"{len(segs)} segments exceeds the requested maximum {max_segments}"], warnings
    out = []
    for i, s in enumerate(segs):
        if not (isinstance(s, (list, tuple)) and len(s) == 2):
            errors.append(f"segment {i} is not a 2-element list: {s!r}")
            continue
        a, b = s
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (a, b)):
            errors.append(f"segment {i} has non-numeric bounds: {s!r}")
            continue
        a, b = float(a), float(b)
        if not (math.isfinite(a) and math.isfinite(b)):
            errors.append(f"segment {i} has non-finite bounds: {s!r}")
            continue
        if not (0 <= a < b):
            errors.append(f"segment {i} violates 0 <= start < end: [{a},{b}]")
            continue
        if b > clip_duration + 1e-3:
            errors.append(f"segment {i} exceeds clip duration {clip_duration}: [{a},{b}]")
            continue
        out.append([round(a, 4), round(min(b, clip_duration), 4)])
    if not out:
        return None, errors or ["no usable segment"], warnings
    out.sort()
    for (a1, b1), (a2, b2) in zip(out, out[1:]):
        if a2 < b1 - 1e-9:
            warnings.append(f"overlapping segments [[{a1},{b1}],[{a2},{b2}]]")
    if errors:
        return None, errors, warnings
    return out, errors, warnings


def union_length(segs):
    if not segs:
        return 0.0
    s = sorted(segs)
    tot, a, b = 0.0, s[0][0], s[0][1]
    for x, y in s[1:]:
        if x <= b + 1e-9:
            b = max(b, y)
        else:
            tot += b - a
            a, b = x, y
    return tot + (b - a)


def interval_metrics(pred_segs, gt_segs, clip_duration):
    """Union-based precision / recall / F1 in the clip's time span."""
    if clip_duration <= 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    pl = union_length(pred_segs or [])
    gl = union_length(gt_segs or [])
    if pl <= 0 or gl <= 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0,
                "pred_union_sec": round(pl, 4), "gt_union_sec": round(gl, 4),
                "inter_sec": 0.0}
    # intersection length of two union-of-intervals
    def to_segments(segs):
        s = sorted(segs)
        m, a, b = [], s[0][0], s[0][1]
        for x, y in s[1:]:
            if x <= b + 1e-9:
                b = max(b, y)
            else:
                m.append([a, b]); a, b = x, y
        m.append([a, b])
        return m
    A, B = to_segments(pred_segs), to_segments(gt_segs)
    inter, i, j = 0.0, 0, 0
    while i < len(A) and j < len(B):
        lo, hi = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if hi > lo:
            inter += hi - lo
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    p = inter / pl
    r = inter / gl
    f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
    return {"precision": round(p, 6), "recall": round(r, 6), "f1": round(f1, 6),
            "pred_union_sec": round(pl, 4), "gt_union_sec": round(gl, 4),
            "inter_sec": round(inter, 4)}


def materialize_clip_file(source_path, clip_start_sec, clip_end_sec, out_path):
    """Write ONE temporary clip file for the virtual window.

    Needed for the Qwen3.5 (Video-ORA-4B) video path, whose processor rejects a
    directly supplied frame tensor. The file is cut with -ss/-t so its timeline
    starts at 0, i.e. the clip is still "virtual" (one file at a time, deleted
    after use; nothing is batch-rendered onto disk).
    """
    import subprocess
    from pathlib import Path
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = max(0.04, clip_end_sec - clip_start_sec)
    subprocess.run(["/usr/local/bin/ffmpeg", "-nostdin", "-y", "-v", "error",
                    "-ss", f"{clip_start_sec:.6f}", "-i", str(source_path),
                    "-t", f"{dur:.6f}", "-c:v", "mpeg4", "-q:v", "3",
                    "-pix_fmt", "yuv420p", "-an", str(out)],
                   check=True, stdin=subprocess.DEVNULL)
    return str(out)


def load_split(name, r5root):
    from pathlib import Path
    p = Path(r5root) / "data" / f"{name}.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

```

END_EMPTY407_R00B


## 第一轮原始完整公开回答：tibo-r00.md
SHA256=5470e02ee3f86f8de522e954db6c72bd7bbbf9203b05077ac8eb1fc426fb98d6

12:36收到。我先完整读取这份新卷宗，核清407/426空输出的实际证据，再区分校准、语义、时序和训练目标的问题，给出唯一有界路线。本轮只讨论，不联网或执行实验，也不会把声明SHA当作已独立验签。12:36

已完整分段读取 context-r00(3).md 第1–37132行，读至 END_EMPTY407_R00；展示截断处已补读。quality_result.json 的4臂×9源、共5404个评分四元组也已完整核对。841249字节及 d41e…fea0 是主控声明；本次读取的是工具提供的文本，没有独立验证原文件字节SHA。我的唯一主案：先做“可审计事件标签小试”，通过后从37.66对应原B续训一次；未通过就保留原B、NO426。停止扩训当前图片评分配方。校准检查用于辨别病因，不另开一条降阈值冲包路线。407空的病因：目前可以确定什么校准问题有实证，但不是唯一原因。阈值49来自训练集人工分数的80分位，没有证明它可直接用作模型输出的决策界。已有9源开发结果中，新模型1351点预测范围24–53，80分位38、95分位48；≥49仅48点，占3.55%。对应人工≥49有293点，占21.69%。新模型已有4/9开发源为空，这四源都有人工作为高重要性的评分点。但不能据此把阈值改成38。新模型≥49那部分平均预测50.69、平均人工50.65，尾部均值并非普遍低估；尺度压缩与具体排序错误同时存在。语义错误不能靠标量校准修好。最直接的非测试反例来自同一源 sTEELN-vY30：grid5/ordinal329，人工87、预测48，被丢；grid32/ordinal1949，人工27、预测50，被选。任何保序一维校准都不能纠正这对逆序。这里的人工分数仍只是TVSum重要性，不是AIC高光真值。时序问题是另一层：单个中点的重要性不能推出整个2秒都应保留。已有扇舞28/29秒与29.96秒行人切镜，足以推翻整格无条件扩展。反过来，短动作若根本没进入学生输入，降低阈值也无法补回信息。目标函数问题尚未排除。237步、非零梯度和权重改变证明真实训练，不能证明任务目标正确。附件的 observed_train.py 是外部训练器包装；没有展示实际collator的label mask和完整loss实现，不能独立确认prompt、padding是否正确排除。整数文本CE本身也不直接优化事件召回和边界。grammar没有强制空输出：它约束每图20–100整数，再由≥49选择；有效低分形成合法空。11项strict和回放PASS主要证明工程合同。407空是严重风险信号，但没有测试真值，不能宣称真实召回就是零。我对主控的关键批评旧投入门比较的是新评分器与base在新图片任务上的点估计，native代理F的差值区间还跨零；production_B也被放进图片评分prompt，并未与37.66原生视频系统公平比较。这个门能放行“相对很弱基线略好、绝对质量仍差”的候选。新立场仍有一个容易重犯的漏洞：“UNKNOWN不转负例”不够。若完整窗口含UNKNOWN，却把目标写成只列KEEP的完整segments列表，闭括号和停止生成仍在教学生遗漏未知区域。必须整窗排除这种样本，不能只在记录里写一句unknown_never_negative。此外，“强闭源能产高质量标签”应当是待检验假设，不能当开工前提。最小非测试判别与G0先复用已有成功raw，不重跑四臂生成：冻结上述分布、逆序例、4个开发空源及随机对照，逐项检查事件是否进入实际学生采样。分清“看见但低估”“看见却认错”“根本没看见”“单点正确但扩段错误”。已见9源和NT8只作诊断，不改名盲确认。取一条实际训练batch核input/labels、视觉占位及padding的mask、答案token数量、损失归一化；补齐外部训练器的真实合同。candidate0锁定37.66那套完整balanced_two_window_v3 native系统：原B adapter、实际展开prompt、grammar、processor、floor64、精确PTS、双窗、解码和空间场。不能拿旧CFR入口或图片评分版production_B替代。特别核实版本缝隙：最新协议写0..5，旧附录prompt写1..5。材料不足以断言当前生产冲突，必须核实际运行锁的字节；不能借核验偷偷修改candidate0。若实际prompt不支持明确空窗，须先解决新训练合同与原基线的兼容问题，本轮不得直接喂入冲突的空目标。建来源关系表：原视频、转载、裁剪、近重复及历史训练曝光归组。9已见dev、旧标注和104/96开发经历如实登记；不读100confirm，不假设库存里天然有未暴露金标。这些检查若已表明没有可审计观察路径、来源无法隔离或训练合同无法绑定，就STOP，不花训练费。标签必须怎样才可入训优先终端agy，但native MP4调用成功和“1fps/30images”自报不等于实际观察证明。现在6片90格的teacher入训仍为0，处理正确。每条事件记录至少包含：来源组、源SHA、窗口、原生ordinal/PTS、学生实际输入清单、标注规则版本。程序生成的证据帧ID与像素哈希；实际供给回执、教师声称看过的ID、独立审查确认的事实分别存储。KEEP/明确NO/UNKNOWN，可见动作事实与高光理由分开写。起止边界的内外证据ID、不确定区间、切镜关系、上下文不足或音频缺失等限制。审查者、盲审原始结论、争议及准入理由。教师引用已存在的证据ID，不自由编精确秒数。关键动作与边界补供显式连续原生帧；仍看不清就UNKNOWN。确切坐标不代表确切语义。切镜触发检查，不机械充当高光边界：跨镜事件可以成立，但两侧都须有证据；单镜头也可能早已结束事件。禁止把一侧KEEP自动扩到另一侧，禁止事后裁剪教师端点来伪造通过。独立审查先看媒体和冻结规则、后看教师答案；所有NO也审，不只审高置信KEEP。同教师复查或多个教师一致只算弱证据。闭源标签称“可审计银标”，没有人工独立裁决就不升级为金标。完整segments SFT只收全窗可监督样本：整个声明范围均有经审查KEEP或明确NO，未列区域不自动算NO。含未解决UNKNOWN整窗排除。明确全窗NO才可输出[]。边界仍只有模糊包围范围时，不取中点冒充精确标签。教师看见而学生输入不可辨认的关键事件，也不能强塞为精确监督。唯一有界工作包以下数字是我建议新冻结的投入上限，不是统计保证，也不改写旧STOP。标注阶段：先复用原六片及原raw检查新证据合同；新增请求只为新观察或独立盲审，不重复成功调用。扩展上限24个现有许可source_group，每组事前固定2个≤30秒窗口，共48窗。12组训练、6组流程开发、6组锁定确认，按来源关系和真实曝光史先冻结；不能根据模型结果选窗、换组。总计最多108次闭源请求，含48次提案、48次盲审和12次证据补查；原六片若产生新调用也计入此总额。供给视频累计上限30分钟，实际usage及费用逐项追加。至少取得8个训练组、16个完整可监督窗口才训练；明确正事件和明确NO均须跨多个来源。开发、确认集合若无法提供可评价的正事件及NO范围，就NO426，不能反复换样本凑门。缺乏足够来源、上下文或观测能力，在上限内无法解决就停止。无需无限等人工，也不拿弱参考冒充真值。训练阶段：从原B全部288个adapter张量精确加载；保持原r16/alpha32、语言q/k/v/o，基座及视觉冻结。新建优化器明确记账，不宣称恢复原优化器轨迹。一次固定lr=1e-5、3遍已接纳数据，有效batch4、最多18次更新；不扫学习率、轮数或checkpoint。采用源均衡及逐样本答案长度归一的assistant-only CE，具体公式与mask在开跑前冻结。前2步做真实梯度、冻结参数和保存重载验收，随后沿同一优化器/RNG继续，不能重启重复曝光。只评估固定终点与candidate0。新训练计费上限1200秒，非测试推理1200秒，获准的唯一426出口另限2400秒；任一阶段到限未完成即停，不拿半成品充当通过。沿用现有算力，不新增租卡。闭源费用还须按实际终端计费方式登记，次数上限不等于免费。前瞻质量门与出口先完成参考、冻结标签和规则，再揭示候选预测。开发用于一次淘汰，不用于改配方；确认只使用一次。旧曝光无法排除时如实降为锁定开发审查，不能宣称独立泛化验证。主指标是逐source等权的经审查区间F1，辅助必须同时报：事件召回、明确NO误选时长、含正事件却全空的窗口数、边界外溢及不确定范围。完整分母、拒收和UNKNOWN都报告，不能丢掉难例再报好看均值。TVSum排序、教师一致率和格式合法率单列。建议放行条件：开发均值ΔF1>0；确认6组至少4组ΔF1>0、均值>0、留一组后均值均≥0；确认宏precision、recall均不退化，正事件漏空数及明确NO误选比例均不增加。证据、来源、采样或切镜合同出现未解决违规直接STOP。以上只是小预算风险筛选，六组不能证明统计显著或官方涨分。全部通过且参考具备可审查事实依据，才允许制作一个质量UNKNOWN的426风险包：沿用冻结native管线和完整空间场后过滤，核实际总参数≤9B、全部426记录、时钟/边界/JSON严格验收和唯一成本终态。不在426结果上调整阈值、TopK或重选权重；制包不等于官网提交或替换生产授权。任何门失败则NO426，继续保留原B37.66。对我自己主案的最强反例强闭源审查也可能把“显著、热闹、有运动”系统性偏好成高光；学生在银标F1上胜原B，官方却下降。两张都正确的1fps画面还可能共同漏掉中间动作，教师一致只会强化同一个错误。上述门只能压低这种风险，不能消除共同偏差。另一种反例是：目标一致的非测试审查最终发现排序已足够好，主要只是尺度问题，那么续训不是最省钱的办法。故小试必须允许否定续训必要性；此时本轮STOP并提交新证据讨论，不能为了兑现“要训练”硬跑。最终裁决：有可靠的TVSum重要性监督，不等于已有可靠的AIC事件边界监督。当前最值得买的新信息，是可复查的事件与完整窗口监督，以及相对原B native的真实配对证据。先验证这两件事，再决定是否花那一次续训和426预算。12:44

## 第一轮原始完整公开回答：sol-r00.md
SHA256=3d2f0a034019c68bb369555108b887a645049eda68c4c8b8de0a51e5af15cb57

说：
EMPTY407-20261010｜第一轮独立会诊

任务ID： AIC-VIDEO-REMATCH-NEXT-20261005
子议题： EMPTY407-20261010
版本： r00
实际附件： context-r00(3).md

一、附件核验与读取范围

已在本地直接读取附件，并独立完成文件完整性核验：

核验项

	

结果




文件字节数

	

841,249，吻合




文件行数

	

37,132，吻合




SHA-256

	

与主控声明完全一致




文件末尾

	

END_EMPTY407_R00，存在




本轮边界

	

仅文字会诊，不执行实验、不联网

独立计算的 SHA-256：

d41e34c692283252bec48c0635d5ea3a2ac1f84f3eada219f5fcea60a570fea0

后续判断以附件中的真实结果、代码、协议及历史裁决为基础，不把报告自述的成功等同于独立实验复现。

二、独立技术判断：为什么出现407个空视频
1. 现有证据

以下数值来自附件记录及保存的代码，不是本轮重新执行的模型实验。

指标

	

历史最佳B

	

新237步评分器




复赛视频数

	

426

	

426




选中帧数

	

102,112

	

3,189




空视频数

	

未给出精确数量

	

407




非测试8源

	

旧生产链已有验收

	

8/8为空




已知官网分

	

用户反馈37.66

	

未知

新评分器空视频比例为 95.54%。它不是一个有可靠AIC质量证据支持的替代方案。
context-r00.md

我另外检查了 quality_result.json 保存的9个开发源预测分布，发现一个比总体Spearman更值得重视的现象：

新模型9源预测分数的最高值分别为：50、47、50、52、42、48、46、53、50。

9源中有4源，最高预测分仍低于冻结阈值49，所以这些源在该规则下必然全空。

新模型的排序相关系数明显提高，但它给出的绝对分数集中在较低范围，且最高分普遍只比阈值略高。

阈值49来自人工训练标签的80%分位数，并不是模型预测分数的已验证校准分位数。

这构成了当前最具体的校准失配证据。

还要注意：新模型在已见9源上的TVSum Spearman为0.522329，相对基座0.043629，确实有排序学习；但native代理F改善的配对95%区间为[-0.001096, 0.210326]，包含0。
context-r00.md

因此不能简单说模型完全没学会，也不能据此认定其具有AIC高光选择能力。

2. 四类根因必须分开

根因

	

当前证据强度

	

我的判断




分数校准失配

	

较强

	

很可能直接导致大量阈值下全空




语义任务错配

	

较强的机制证据

	

TVSum重要性与AIC可剪辑高光并非相同标签目标




时序信息与边界缺失

	

已有具体失败案例

	

单个2秒中点不能代表整格内的动作及切镜




目标函数与任务不一致

	

代码可以确认

	

训练优化评分文本的交叉熵，未直接优化高光事件召回与时间边界

我检查了 selector_contract.py、score_grammar.py 和 contest_engine.py。

新系统的实际决策结构为：

2秒格中点采样 → 每批最多16张有序静态图

预测 scores_x20，语法限制为20–100

score >= 49 保留，否则丢弃

整个2秒格选入或排除 → 复用完整空间场

这个管线具有明确的结构性限制：

即使评分器正确发现某一帧很重要，它也不能直接确定真实事件的开始、结束、动作是否完成，以及2秒范围内是否出现切镜。

407空则是另一种失败表现：绝对分数偏低时，严格阈值把弱但有价值的候选也全部过滤掉。

不能在这两种错误之间直接选择“降低阈值”。降低阈值可能增加召回，也可能仅仅增加无意义帧。

3. 校准和语义哪个是主因？

我会区分两个问题：

问题A：为什么新系统几乎不输出？
现有证据首先指向校准失配与阈值化机制。

问题B：就算让新系统多输出，能否提高AIC成绩？
现有证据不足，而且语义与边界监督不匹配仍可能造成重大损失。

因此，修复407空的输出分布，不等于修复高光质量。

我反对继续扩大相同TVSum评分配方，也反对仅通过改变分数阈值产出另一个426包。

三、唯一推荐路线：原B Native事件监督续训
推荐主案：B-NATIVE-EVENT-SFT-v1

保留37.66原B作为candidate0，以原B原生视频窗口为训练单位，利用agy产生事件候选，再通过独立视觉与边界审查获得小规模高可信监督。只有监督完整且公平对照通过，才允许一次有界LoRA续训和后续候选验收。

不继续训练TVSum图片评分器，不引入新架构，不并行探索其他模型。

这条路线的核心不是寻找更强的教师，而是把训练目标从“帧重要性打分”重新对准“可实际剪辑的高光事件区间”。

阶段A：最小根因判别，先不训练

严格限定在已有非测试资源。

检查

	

最小操作

	

判别结果




校准

	

读取冻结的train/9dev评分，统计分位数、分数范围、阈值49以上比例

	

排序尚可但分数普遍低，支持校准失配




语义

	

对少量独立审查的非测试事件，比较TVSum高分与实际可剪辑事件

	

高重要性不等于高光，支持目标错配




时序

	

比较原B64帧原生采样、新模型2秒中点与事件真实可见帧

	

有事件但采样不可见，支持时序瓶颈




输出目标

	

检查完整事件标签、缺失区间、模型格式及可表达范围

	

判断是否可用现有B协议做完整窗口监督

这里最重要的是可观察性检查。

如果独立参考确认某个关键动作发生，但原B的实际输入采样根本没有捕获该动作的可识别证据，那么增加微调步数不可能稳定解决这个特定问题。

如果原B能够观察到动作，却没有选择，才具有进一步研究语义监督的价值。

所有检查必须在训练配方冻结前完成，不读取复赛单视频输出。

阶段B：agy标注，最多24个原生窗口

建议一次前瞻试验上限：

项目

	

冻结上限




数据

	

现有且用途许可明确的非测试视频




来源组

	

最多12个彼此隔离的来源组




每组

	

2个不重叠的原B原生窗口




总视频窗口

	

24个，每窗不超过30秒




agy首次调用

	

最多24次




定点边界补查

	

最多8次




新大数据下载

	

0

预先按照来源组划分6组训练、3组校准、3组确认。相同视频、同源派生裁剪、重复素材不能跨组；还需核对历史B训练和开发曝光记录。如果找不到满足条件的来源，就缩小可用集合并明确降低证据等级，不把已见开发集冒充全新盲测。

历史已有6段90格标注保留为流程失效案例，不直接升级训练样本。
context-r00.md

新标注不再以2秒KEEP列表作为最终训练目标，而是要求agy针对原B实际窗口输出可追溯的事件及其起止证据。

阶段C：标注格式与真实观测要求

建议使用如下核心字段；具体枚举和路径应在首次模型调用前冻结。

JSON
{
  "source_id": "source-id",
  "source_group": "group-id",
  "source_sha256": "...",
  "window_id": "...",
  "clip_sha256": "...",
  "time_basis": "native_pts",
  "observation": {
    "tool": "agy/view_file",
    "actual_observed_ordinals": [],
    "coverage": "SPARSE",
    "full_observation_proven": false
  },
  "events": [
    {
      "state": "KEEP",
      "event_type": "action_or_result",
      "start_native_ordinal": 1200,
      "end_native_ordinal_exclusive": 1240,
      "positive_evidence_ordinals": [],
      "boundary_evidence_ordinals": [],
      "boundary_status": "UNVERIFIED",
      "confidence": "MEDIUM"
    }
  ],
  "unresolved_ranges": [],
  "full_window_supervision_eligible": false
}

这些是格式示意，不代表已存在对应帧或审核结果。

需要保留原模型答复、原生媒体SHA、实际输入、模型声明的观察时刻、独立核验的物理帧以及规范映射结果。教师声称看见的内容与审查人员实际验证过的内容必须分字段存储。

建议用双层观察方式：

第一层通过agy读取原生短MP4并描述候选事件。第二层基于真实native PTS提供可索引的视觉证据，尤其是事件起止和切镜附近的较密集帧序列。即使视频工具报告1fps，也不能推断模型连续观察了完整视频。

对正例区间，必须至少能够核验事件内部的正向证据，并用起止附近的前后帧支持边界。只有内部证据而没有边界证据的片段，不应取得精确时间监督资格。

切镜是硬边界问题，而不是标注格式问题。

以附件中28–30秒扇舞案例为例，28/29秒确有扇舞，29.96秒已经出现行人。不能因为28/29秒正确，就把整个28–30秒赋为KEEP。
context-r00.md

接受条件应是：

区间端点映射到合法原生ordinal，半开范围精确，无来源漂移。

每个KEEP都有真实可观察的事件依据，且原B实际采样至少具有足以识别该事件的证据。

已确认的切镜必须分段或截断；切镜位置不确定则边界保持UNKNOWN。

REJECT必须有已观察到的明确过渡或冗余证据，UNKNOWN不能当负例。

未能覆盖完整窗口时，禁止把部分KEEP列表转换为完整窗口的segments监督。

