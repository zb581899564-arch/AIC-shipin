"""Once-only frozen 104-source-group weak comparison; no competition inputs."""
import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
DELIVERY=RUN/'mac8b_delivery_v1'
HERE=DELIVERY/'dev'
sys.path.insert(0,str(DELIVERY))
from lowres import lowres_encode,decode_dev_av,verify_cuda_adapter
R7 = ROOT/'round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z'
sys.path[:0] = [str(RUN/'temporal_sft8b_v1'), str(R7/'code')]
DEV_SHA = '53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700'
ADAPTER_SHA = '1baa14a96d30d3836478295752c0b932f40f811863c28db99b56102fcfa1d5b5'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''): h.update(chunk)
    return h.hexdigest()
def read(path): return json.loads(Path(path).read_text())
def rows(path): return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def require(condition,message):
    if not condition: raise RuntimeError(message)
def write(path,value):
    with Path(path).open('x') as f: f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def geometry(start,end):
    out=[]
    for i in range(int((end-start+29.999999999)/30)):
        a=start+i*30; b=min(end,a+30)
        if b-a>=.2: out.append((a,b))
    return out

def prepare():
    HERE.mkdir(exist_ok=True)
    require(sha(R7/'inputs/dev_temporal.jsonl')==DEV_SHA,'original 104 dev changed')
    dev=rows(R7/'inputs/dev_temporal.jsonl'); train=rows(R7/'inputs/train_temporal.jsonl')
    require(len(dev)==104 and len({r['youtube_id'] for r in dev})==96,'dev denominator changed')
    require(not {r['youtube_id'] for r in dev}&{r['youtube_id'] for r in train},'source leakage')
    config=read(RUN/'temporal_sft8b_full_v1/config.json')
    report=read(DELIVERY/'training_evidence/train_report.json')
    require(report['full_training_completed'] and report['base_frozen'] and report['vision_frozen'] and
        report['adapter_reload_succeeded'] and report['loss_finite'] and report['optimizer_steps']==227 and
        report['effective_batches']==3620 and report['adapter_model_sha256']==ADAPTER_SHA,'training acceptance failed')
    adapter=DELIVERY/'adapter'
    require(sha(adapter/'adapter_model.safetensors')==ADAPTER_SHA,'final adapter changed')
    receipt=read(config['model_receipt']['path'])
    bound={str(R7/'inputs/dev_temporal.jsonl'):DEV_SHA,
        str(R7/'inputs/train_temporal.jsonl'):sha(R7/'inputs/train_temporal.jsonl'),
        str(R7/'inputs/split_freeze.json'):sha(R7/'inputs/split_freeze.json'),
        str(HERE/'evaluate.py'):sha(HERE/'evaluate.py'),
        str(DELIVERY/'DEV_PROTOCOL.md'):sha(DELIVERY/'DEV_PROTOCOL.md'),
        str(DELIVERY/'training_evidence/train_report.json'):sha(DELIVERY/'training_evidence/train_report.json')}
    for name in ('temporal_common.py','r7_core.py'): bound[str(R7/'code'/name)]=sha(R7/'code'/name)
    for name in ('sft_contract.py','train_sft.py'): bound[str(RUN/'temporal_sft8b_v1'/name)]=sha(RUN/'temporal_sft8b_v1'/name)
    for name in ('adapter_config.json','adapter_model.safetensors'): bound[str(adapter/name)]=sha(adapter/name)
    for item in receipt['completed']:
        path=Path(config['model_dir'])/item['name']
        require(sha(path)==item['sha256'],'pinned model byte changed')
        bound[str(path)]=item['sha256']
    # CPU metadata query only; no new data, no held-out/competition labels.
    import torch
    import decord
    augmented=[]; sources={}
    for r in dev:
        source=r['source_path']
        if source not in sources:
            vr=decord.VideoReader(source); h,w=vr[0].shape[:2]
            sources[source]=dict(sha256=sha(source),n_frames=len(vr),width=w,height=h,fps=float(vr.get_avg_fps()))
        s=sources[source]; require(s['n_frames']==r['decoded_source_frames'],'dev source count changed')
        require(abs(s['fps']-r['source_avg_fps'])<max(1e-6,s['fps']*1e-6),'dev FPS changed')
        augmented.append(dict(r,source_sha256=s['sha256'],n_frames=s['n_frames'],width=s['width'],height=s['height'],
                              fps_num=s['fps'],fps_den=1))
    write(HERE/'input_contract.json',dict(records=augmented,sources=sources,original_dev_sha256=DEV_SHA,
        source_bytes_newly_bound=True,original_pts_source_byte_equality_claimed=False,confirm_read=False))
    bound[str(HERE/'input_contract.json')]=sha(HERE/'input_contract.json')
    write(HERE/'admission.json',dict(authorized=True,user_request='mac的开发测评和提交包尽早完成',scope='MAC_LOWRES_FIXED_104_WEAK_DEV_ONCE',
        frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files=bound,model_dir=config['model_dir'],adapter=str(adapter),
        comparisons=['BASE8B','SFT8B'],video_pixels_per_frame=32768,max_input_tokens=6144,decoder='PYAV_SEQUENTIAL_SAME_AS_MAC_TRAINING',execution_device='CUDA_RELOCATED_MAC_FINAL_ADAPTER',max_new_tokens=256,greedy=True,windows='nonoverlap30s_keep_empty_fail_distinct',
        final_model_evaluations=1,seed=20261006,bootstrap_draws=10000,confirm_read=False,test_read=False,
        stop_definition=dict(any_inference_failure=True,all_final_outputs_invalid=True,all_final_overlap_zero=True,
            paired_F1_CI_upper_below_zero=True,independent_tradeoff_available=False),
        max_wall_seconds=14400,planned_output_bytes=100000000))
    print(json.dumps(dict(status='PASS_CPU_BINDING',videos=104,groups=96,windows=sum(len(geometry(r['clip_start_sec'],r['clip_end_sec'])) for r in augmented),admission_sha256=sha(HERE/'admission.json'))))

def evaluate():
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    a=read(HERE/'admission.json')
    require(a['authorized'] and a['scope']=='MAC_LOWRES_FIXED_104_WEAK_DEV_ONCE','missing scope')
    for path,digest in a['files'].items(): require(sha(path)==digest,'bound input/source/model changed: '+path)
    require(not (HERE/'evaluation_started.json').exists(),'once-only evaluation already started')
    write(HERE/'evaluation_started.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),admission_sha256=sha(HERE/'admission.json')))
    import torch
    torch.cuda.init()
    import decord
    import numpy as np
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from train_sft import decode_cfr_clip,verify_video_encoding,unique_parameters
    from r7_core import temporal_stats,bootstrap_ci
    tc=load(R7/'code/temporal_common.py','fixed_dev_tc')
    started=time.monotonic()
    base=Qwen3VLForConditionalGeneration.from_pretrained(a['model_dir'],local_files_only=True,torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()
    relocation=verify_cuda_adapter(model,a)
    write(HERE/'cuda_relocation.json',relocation)
    count=sum(p.numel() for _,p in unique_parameters(model))
    require(count==8782459120 and count<=9000000000,'parameter count mismatch')
    processor=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=processor.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    contract=read(HERE/'input_contract.json'); records=contract['records']; totals={}
    for source,s in contract['sources'].items(): require(sha(source)==s['sha256'],'dev source hash changed')
    for arm in a['comparisons']:
        outputs=[]
        with (HERE/(arm+'.jsonl')).open('x') as stream:
            for n,r in enumerate(records,1):
                rec=dict(video_id=r['video_id'],youtube_id=r['youtube_id'],arm=arm,windows=[],pred=[])
                for index,(start,end) in enumerate(geometry(r['clip_start_sec'],r['clip_end_sec'])):
                    w=dict(index=index,start_sec=start,end_sec=end,status='INFERENCE_FAILURE',parsed_segments=None)
                    one=time.monotonic()
                    try:
                        row=dict(r,clip_start_sec=start,clip_end_sec=end)
                        arr,md,info=decode_dev_av(row,tc,np,decord)
                        encoded=lowres_encode(processor,text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],
                            video_metadata=[md],padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
                        identity=verify_video_encoding(processor,encoded,md,info)
                        require(encoded['input_ids'].shape[1]<=6144,'expanded input exceeds trained contract')
                        inputs=encoded.to('cuda'); prefix=int(inputs['input_ids'].shape[1])
                        with (model.disable_adapter() if arm=='BASE8B' else contextlib.nullcontext()),torch.inference_mode():
                            generated=model.generate(**inputs,do_sample=False,max_new_tokens=256)
                        torch.cuda.synchronize()
                        raw=processor.tokenizer.decode(generated[0,prefix:],skip_special_tokens=True,clean_up_tokenization_spaces=False)
                        parsed,errors,warnings=tc.parse_segments(raw,end-start)
                        empty=False
                        if parsed is None:
                            try: empty=json.loads(raw.strip())=={'segments':[]}
                            except Exception: pass
                        w.update(status='MODEL_OK' if parsed is not None else 'EMPTY_UNSUPPORTED' if empty else 'PARSE_FAILURE',
                            raw_output=raw,parsed_segments=parsed,parse_errors=errors,parse_warnings=warnings,video_identity=identity,
                            output_valid=parsed is not None,legal_empty=False)
                        if parsed is not None: rec['pred'] += [[start-r['clip_start_sec']+x,start-r['clip_start_sec']+y] for x,y in parsed]
                        del inputs,encoded,generated,arr
                    except Exception as exc:
                        w.update(error=type(exc).__name__+': '+str(exc),output_valid=False,legal_empty=False)
                    w['seconds']=time.monotonic()-one; rec['windows'].append(w)
                rec.update(metrics=temporal_stats(rec['pred'],r['segments_clip_local']))
                outputs.append(rec); stream.write(json.dumps(rec,ensure_ascii=False)+'\n');stream.flush()
                write_progress=dict(arm=arm,videos_completed=n,videos=104,wall_seconds=time.monotonic()-started)
                temp=HERE/'progress.tmp';temp.write_text(json.dumps(write_progress));temp.replace(HERE/'progress.json')
                print(json.dumps(write_progress),flush=True)
        totals[arm]=outputs
    groups=sorted({r['youtube_id'] for r in records}); summary={}; group_f1={}
    for arm,output in totals.items():
        ws=[w for r in output for w in r['windows']]
        group_f1[arm]={g:statistics.mean(r['metrics']['f1'] for r in output if r['youtube_id']==g) for g in groups}
        summary[arm]=dict(video_macro={k:statistics.mean(r['metrics'][k] for r in output) for k in ('precision','recall','f1')},
            source_group_macro_f1=statistics.mean(group_f1[arm].values()),covered_weak_positive_recall=statistics.mean(r['metrics']['recall'] for r in output),
            windows=len(ws),parse_failure_rate=sum(w['status'] in ('PARSE_FAILURE','EMPTY_UNSUPPORTED') for w in ws)/len(ws),
            inference_failure_rate=sum(w['status']=='INFERENCE_FAILURE' for w in ws)/len(ws),legal_empty_rate=0,
            unsupported_empty_rate=sum(w['status']=='EMPTY_UNSUPPORTED' for w in ws)/len(ws),valid_windows=sum(w['output_valid'] for w in ws))
    differences=[group_f1['SFT8B'][g]-group_f1['BASE8B'][g] for g in groups]
    ci=bootstrap_ci(differences,10000,20261006)
    stop=dict(inference_failure=any(s['inference_failure_rate']>0 for s in summary.values()),
        all_final_outputs_invalid=summary['SFT8B']['valid_windows']==0,
        all_final_overlap_zero=summary['SFT8B']['covered_weak_positive_recall']==0,
        paired_weak_F1_CI_all_negative=ci[1]<0)
    report=dict(status='STOP_B_PACKAGE_DEV_GATE' if any(stop.values()) else 'PASS_FROZEN_WEAK_DEV_GATE',
        metric_status='WEAK_TEACHER_AGREEMENT_INTERNAL_SPEC_REIMPLEMENTATION',official_score=False,
        videos=104,groups=96,comparisons=summary,paired=dict(mean=statistics.mean(differences),ci95=ci,draws=10000,seed=20261006),
        stop_checks=stop,logical_parameters=count,original_dev_sha256=DEV_SHA,adapter_sha256=ADAPTER_SHA,
        video_pixels_per_frame=32768,decoder="PYAV_SEQUENTIAL",execution_device="CUDA",full_protocol_sha256=a['files'][str(DELIVERY/'DEV_PROTOCOL.md')],
        wall_seconds=time.monotonic()-started,confirm_read=False,test_read=False,evaluation_runs_per_final_model=1,
        failures_kept_in_video_denominator=True,unknown_unselected_not_certified_negatives=True)
    write(HERE/'decision.json',report); print(json.dumps(report),flush=True)
    return 0 if not any(stop.values()) else 5

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','evaluate']); args=ap.parse_args()
    if args.phase=='prepare': prepare()
    else: raise SystemExit(evaluate())
