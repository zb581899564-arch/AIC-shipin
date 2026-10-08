"""One temporal implementation for production and open developer diagnostics."""
from common import *
import contextlib
import time
from contracts import EMPTY_PROMPT, parse_segments
from constrained_json import ascii_token_candidates, make_prefix_constraint, IncompleteConstrainedOutput
from video_contract import encode, identity

def load_model(config, adapter=True):
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from train_sft import unique_parameters
    base = Qwen3VLForConditionalGeneration.from_pretrained(config['model_dir'], local_files_only=True,
        torch_dtype=torch.bfloat16, device_map={'':'cuda:0'}, low_cpu_mem_usage=True, attn_implementation='sdpa')
    model = PeftModel.from_pretrained(base, config['b_adapter'], is_trainable=False) if adapter else base
    model.eval()
    count = sum(p.numel() for _, p in unique_parameters(model))
    require(count == (8782459120 if adapter else 8767123696), 'actual pipeline parameter inventory changed')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
                                               min_pixels=131072, max_pixels=131072)
    require(processor.video_processor.size == config['video_size'], 'legacy processor size changed')
    return model, processor, count

def prompt_for(processor, allow_empty):
    tc = load(BASELINE/'vendor/temporal_common.py', 'next_tc_prompt')
    text = EMPTY_PROMPT if allow_empty else tc.PROMPT
    prompt = processor.apply_chat_template([{'role':'user','content':[{'type':'text','text':text}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)

def encode_window(processor, prompt, item, clock, start, end, config):
    import torch
    from frame_contract import BRANCH_CFR, native_clip_plan
    from native_frames import build_native_clip
    from exact_pts import exact_native_pts, verify_native_encoding
    tc = load(BASELINE/'vendor/temporal_common.py', 'next_tc_decode')
    if clock is None or clock['branch'] == BRANCH_CFR:
        arr, md, info = tc.build_virtual_clip(item['source_path'], start, end)
        require(info['source_total_frames'] == item['n_frames'], 'source ordinal count changed')
        require(abs(info['source_fps']-item['fps_num']/item['fps_den']) <= max(1e-6, info['source_fps']*1e-6), 'FPS changed')
        encoded = encode(processor, text=[prompt], videos=[torch.from_numpy(arr).permute(0,3,1,2)],
            video_metadata=[md], video_size=config['video_size'], max_input=config['max_input_tokens'])
        details = {'clock_branch': BRANCH_CFR, 'clip_decode_plan': info,
                   'clip_local_sample_indices': md['frames_indices']}
    else:
        plan = native_clip_plan(clock, start, end)
        arr, md = build_native_clip(item['source_path'], item, clock, plan)
        with exact_native_pts(processor, plan, item['fps_num']/item['fps_den']) as native_identity:
            encoded = encode(processor, text=[prompt], videos=[torch.from_numpy(arr).permute(0,3,1,2)],
                video_metadata=[md], video_size=config['video_size'], max_input=config['max_input_tokens'])
            verify_native_encoding(processor, encoded, native_identity)
        details = {'clock_branch': clock['branch'], 'clock_record_sha256': clock['clock_record_sha256'],
                   'source_frame_ids': plan['source_frame_ids'], 'native_processor_identity': native_identity}
    details.update(identity(processor, encoded, len(arr)))
    require(arr.shape[1:] == (item['height'],item['width'],3), 'source geometry changed')
    return encoded, details

def generate_window(model, processor, encoded, details, start, end, candidates, allow_empty=False, disable_adapter=False):
    import torch
    prefix = int(encoded['input_ids'].shape[1])
    eos = model.generation_config.eos_token_id
    if isinstance(eos, int):
        eos = [eos]
    constraint = make_prefix_constraint(processor.tokenizer, prefix, end-start,
        candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=allow_empty)
    inputs_gpu = encoded.to('cuda')
    with (model.disable_adapter() if disable_adapter else contextlib.nullcontext()), torch.inference_mode():
        generated = model.generate(**inputs_gpu, do_sample=False, max_new_tokens=256,
                                   prefix_allowed_tokens_fn=constraint)
    torch.cuda.synchronize()
    ids = generated[0,prefix:]
    raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    try:
        constraint.assert_complete(ids)
        parsed, errors, warnings = parse_segments(raw, end-start, allow_empty=allow_empty)
    except IncompleteConstrainedOutput as exc:
        parsed, errors, warnings = None,[type(exc).__name__+': '+str(exc)],[]
    record = dict(start_sec=start,end_sec=end,status='PARSE_FAILURE' if parsed is None else
        'LEGAL_EMPTY' if not parsed else 'MODEL_OK', output_valid=parsed is not None, parsed_segments=parsed,
        parse_errors=errors,parse_warnings=warnings,raw_output=raw,video_identity=details,
        constraint_stats=constraint.stats,generation_time_constraint=True)
    for key in ('clock_branch','clock_record_sha256','source_frame_ids','native_processor_identity'):
        if key in details:
            record[key] = details[key]
    return record

def temporal(scope, out):
    config = verify()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from frame_contract import window_schedule
    _, manifest, clocks = inputs(scope)
    out = Path(out); out.mkdir(exist_ok=True)
    started = time.monotonic()
    model, processor, count = load_model(config, adapter=False)
    candidates = ascii_token_candidates(processor.tokenizer)
    prompt = prompt_for(processor, False)
    failures = windows = 0
    with (out/'temporal.jsonl').open('x',encoding='utf-8') as stream:
        for n,item in enumerate(manifest['records'],1):
            require(sha(item['source_path']) == item['source_sha256'], 'source bytes changed')
            clock = clocks[item['video_id']]
            record = dict(video_id=item['video_id'],targetRatioWH=item['targetRatioWH'],video_path=item['source_path'],
                n_frames=item['n_frames'],fps=item['fps_num']/item['fps_den'],arm='Z_NATIVE8B_MATCHED_B_DECODING',windows=[])
            for j,(start,end) in enumerate(window_schedule(item,manifest['kind'],clock)):
                one = time.monotonic(); windows += 1
                try:
                    encoded, details = encode_window(processor,prompt,item,clock,start,end,config)
                    window = generate_window(model,processor,encoded,details,start,end,candidates,False)
                    del encoded
                except Exception as exc:
                    window = dict(start_sec=start,end_sec=end,status='INFERENCE_FAILURE',output_valid=False,
                                  parsed_segments=None,parse_errors=[type(exc).__name__+': '+str(exc)],parse_warnings=[])
                window.update(index=j,seconds=time.monotonic()-one)
                failures += not window['output_valid']; record['windows'].append(window)
            stream.write(json.dumps(record,ensure_ascii=False)+'\n'); stream.flush()
            progress(out,dict(stage='TEMPORAL',scope=scope,videos=n,total=len(manifest['records']),
                              windows=windows,failures=failures,wall_seconds=time.monotonic()-started))
    write(out/'temporal.stage.json',dict(status='PASS_TEMPORAL_EXECUTION' if failures==0 else 'STOP_TEMPORAL_FAILURES',
        videos=len(manifest['records']),windows=windows,invalid_windows=failures,logical_parameters=count,
        output_sha256=sha(out/'temporal.jsonl'),allow_empty=False,prompt='UNCHANGED_B_1_TO_5',
        decoder='SAME_FUNCTION_AS_ALIGNED_DEVELOPMENT',explicit_video_size=config['video_size'],
        max_input_tokens=config['max_input_tokens'],wall_seconds=time.monotonic()-started,official_score=None))
    require(failures==0,'invalid temporal windows block package')

def aligned_dev(scope, out):
    config = verify()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import statistics
    from r7_core import temporal_stats, bootstrap_ci
    old = load(RUN/'temporal_sft8b_dev_v1/evaluate.py','old_dev_geometry_only')
    records = read(config['open_dev_contract'])['records']
    require(len(records)==104 and len({r['youtube_id'] for r in records})==96,'open developer source denominator changed')
    out=Path(out);out.mkdir(exist_ok=True);started=time.monotonic()
    model,processor,count=load_model(config,adapter=True)
    candidates=ascii_token_candidates(processor.tokenizer);prompt=prompt_for(processor,False)
    totals={'B':[],'Z':[]}; failures=0
    streams={arm:(out/(arm+'.jsonl')).open('x',encoding='utf-8') for arm in totals}
    try:
        for n,r in enumerate(records,1):
            require(sha(r['source_path'])==r['source_sha256'],'open dev media bytes changed')
            item=dict(r,fps_num=r['source_avg_fps'],fps_den=1,n_frames=r['decoded_source_frames'])
            recs={arm:dict(video_id=r['video_id'],youtube_id=r['youtube_id'],pred=[],windows=[]) for arm in totals}
            for start,end in old.geometry(r['clip_start_sec'],r['clip_end_sec']):
                encoded,details=encode_window(processor,prompt,item,None,start,end,config)
                for arm,rec in recs.items():
                    one=time.monotonic()
                    try:
                        w=generate_window(model,processor,encoded,details,start,end,candidates,False,arm=='Z')
                        if w['output_valid']:
                            rec['pred'] += [[start-r['clip_start_sec']+a,start-r['clip_start_sec']+b] for a,b in w['parsed_segments']]
                    except Exception as exc:
                        w=dict(start_sec=start,end_sec=end,status='INFERENCE_FAILURE',output_valid=False,
                               parsed_segments=None,error=type(exc).__name__+': '+str(exc))
                    w['seconds']=time.monotonic()-one;rec['windows'].append(w);failures += not w['output_valid']
                del encoded
            for arm,rec in recs.items():
                rec['metrics']=temporal_stats(rec['pred'],r['segments_clip_local'])
                totals[arm].append(rec);streams[arm].write(json.dumps(rec,ensure_ascii=False)+'\n');streams[arm].flush()
            progress(out,dict(stage='PRODUCTION_ALIGNED_DEV',videos=n,total=104,arms=['B','Z'],
                              failures=failures,wall_seconds=time.monotonic()-started))
    finally:
        for stream in streams.values():stream.close()
    groups=sorted({r['youtube_id'] for r in records});summary={};gf={}
    for arm,values in totals.items():
        ws=[w for r in values for w in r['windows']]
        gf[arm]={g:statistics.mean(r['metrics']['f1'] for r in values if r['youtube_id']==g) for g in groups}
        summary[arm]=dict(video_macro={k:statistics.mean(r['metrics'][k] for r in values) for k in ('precision','recall','f1')},
            mean_selected_duration_fraction=statistics.mean(r['metrics']['pred_seconds']/(row['clip_end_sec']-row['clip_start_sec']) for r,row in zip(values,records)),
            selected_at_least_99pct_videos=sum(r['metrics']['pred_seconds']/(row['clip_end_sec']-row['clip_start_sec'])>=.99 for r,row in zip(values,records)),
            zero_overlap_videos=sum(r['metrics']['zero_overlap'] for r in values),
            windows=len(ws),valid_windows=sum(w['output_valid'] for w in ws),
            inference_failures=sum(w['status']=='INFERENCE_FAILURE' for w in ws),
            parse_failures=sum(w['status']=='PARSE_FAILURE' for w in ws),legal_empty=sum(w['status']=='LEGAL_EMPTY' for w in ws))
    differences=[gf['Z'][g]-gf['B'][g] for g in groups]
    report=dict(status='PASS_PRODUCTION_ALIGNED_DEV_ENGINEERING' if not failures else 'STOP_DEV_ENGINEERING',
        local_metric_role='OPTIONAL_WEAK_TEACHER_DIAGNOSTIC_NOT_OFFICIAL_SCORE',official_score=None,
        official_total_reimplementation_required=False,ci_lower_positive_required=False,comparisons=summary,
        paired_Z_minus_B=dict(mean=statistics.mean(differences),ci95=bootstrap_ci(differences,10000,20261007)),
        videos=104,groups=96,actual_loaded_parameters=count,confirm_read=False,test_read=False,
        same_generation_function=True,same_decoder=True,same_encoded_window_shared=True,
        developer_is_open=True,wall_seconds=time.monotonic()-started)
    write(out/'decision.json',report);require(failures==0,'new production-aligned engineering failures')

def probe(scope,out):
    config=verify()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    out=Path(out);out.mkdir(exist_ok=True);started=time.monotonic()
    model,p,count=load_model(config,adapter=False)
    frames=torch.zeros((64,3,1080,1920),dtype=torch.uint8)
    metadata={'fps':30,'frames_indices':[14*i for i in range(64)],'total_num_frames':900,'video_backend':'decord'}
    encoded=encode(p,text=[prompt_for(p,True)],videos=[frames],video_metadata=[metadata],
                   video_size=config['video_size'],max_input=config['max_input_tokens'])
    details=identity(p,encoded,64);torch.cuda.reset_peak_memory_stats()
    w=generate_window(model,p,encoded,details,0,30,ascii_token_candidates(p.tokenizer),True)
    require(w['output_valid'],'actual optional-empty constrained inference failed')
    del encoded,frames
    from training_target import build_target
    toy=torch.zeros((4,3,72,128),dtype=torch.uint8)
    md=dict(fps=2,frames_indices=[0,1,2,3],total_num_frames=4,video_backend='decord')
    plan=dict(source_frame_ids=[0,1,2,3],source_relative_pts=[0,.4,1.1,1.5],window_start=0)
    target,mask=build_target(p,prompt_for(p,True),toy,md,dict(observation_complete=True,status='OBSERVED_EMPTY',segments=[]),
        2,config['video_size'],native_plan=plan,source_fps=2)
    with torch.inference_mode():loss=model(**target.to('cuda')).loss
    require(bool(torch.isfinite(loss)),'actual empty assistant CE loss is nonfinite')
    write(out/'probe.stage.json',dict(status='PASS_SYNTHETIC_SHARED_VIDEO_AND_EMPTY_CAPABLE_GENERATION',
        logical_parameters=count,input_identity=details,selected_output_status=w['status'],
        grammar_allows_empty=True,synthetic_only=True,contest_media_read=False,
        empty_target_finite_loss=float(loss),empty_target_native_pts_contexts=len(mask['exact_pts_encoding']),
        empty_target_supervision_is_synthetic_only=True,optimizer_updates=0,
        peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,wall_seconds=time.monotonic()-started))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['temporal','aligned_dev','probe'])
    parser.add_argument('scope');parser.add_argument('out');args=parser.parse_args()
    globals()[args.stage](args.scope,args.out)
