        require(build_field_requests(field, rows(cache / 'field_shots.jsonl'), 8) == requests, 'B2 source cache requests differ from current field algorithm')
        require(len(outputs) == len(requests) == read(cache / 'spatial.stage.json')['rows'] and
                all(r['status'] == 'MODEL_OK' and r.get('used_fallback') is False for r in outputs),
                'cached source spatial inference incomplete')
        for request, output in zip(requests, outputs):
            require(request['anchor_request_sha256'] == output['anchor_request_sha256'] and
                    request['expected_pixel_sha256'] == output['decoded_pixel_sha256'] and
                    request['video_id'] == output['video_id'] and request['source_frame'] == output['source_frame'],
                    'cached anchor identity changed')
        old.write_rows(out / 'selected.jsonl', selected)
        for name in ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl'):
            shutil.copyfile(cache / name, out / name)
            require(sha(out / name) == freeze['files'][name], 'copied source cache bytes differ')
        schedule = dict(source_schedule, selected_frames=len(selected), source_cache=str(cache),
                        reused_time_independent_source_field=True)
        write(out / 'schedule.stage.json', schedule, fresh=True)
        space = dict(read(cache / 'spatial.stage.json'), reused_cache=True, model_calls_this_T_candidate=0,
                     source_cache=str(cache), anchor_output_sha256=sha(out / 'anchor_output.jsonl'))
        write(out / 'spatial.stage.json', space, fresh=True)
        write(out / 'cache_reuse_receipt.json', {'status': 'PASS_COMPLETE_TIME_INDEPENDENT_SOURCE_CACHE',
             'utc': utc(), 'frozen_cache_receipt_sha256': sha(freeze_path),
             'B2_completion_sha256': freeze['B2_completion_sha256'],
             'manifest_sha256': input_ref['manifest_sha256'], 'clock_registry_sha256': input_ref['registry_sha256'],
             'files': {name: sha(out / name) for name in
             ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl')}}, fresh=True)
    else:
        # A failed or incomplete old cache is never silently accepted.
        source.scheduling(scope, out)


def verify_spatial_base(model, config):
    import torch
    from verify_saved_smoke import canonical_frozen_hash
    require(not any('lora_' in name for name, _ in model.named_parameters()), 'space base unexpectedly contains an adapter')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    value = canonical_frozen_hash(model, torch)
    check_base_hash(value, config)
    return value


def spatial_with_base_identity(source, scope, out, config):
    """Keep the frozen inference algorithm; verify its loaded model before any prediction."""
    original_load, original_write = source.load, source.write
    measured = {}
    constructors = []
    def bound_load(path, name):
        module = original_load(path, name)
        if Path(path) == source.HERE / 'spatial_baseline.py' and name == 'next_strict_spatial_baseline':
            constructor = module.Qwen3VL
            constructors.append((module, constructor))
            def bound_constructor(*args, **kwargs):
                require(args and str(args[0]) == config['model_dir'], 'spatial load model path differs')
                wrapper = constructor(*args, **kwargs)
                measured['base_hash'] = verify_spatial_base(wrapper.model, config)
                return wrapper
            module.Qwen3VL = bound_constructor
        return module
    def bound_write(path, value):
        if Path(path) == Path(out) / 'spatial.stage.json' and value.get('status') != 'PASS_EMPTY_SPACE_NO_MODEL_CALL':
            require('base_hash' in measured, 'spatial execution lacks actual base byte identity')
            value = dict(value, base_hash=measured['base_hash'])
        original_write(path, value)
    source.load, source.write = bound_load, bound_write
    try:
        source.spatial(scope, out)
    finally:
        source.load, source.write = original_load, original_write
        for module, constructor in constructors:
            module.Qwen3VL = constructor


def spatial(scope, out):
    verify()
    _, old, _, source = helpers()
    out = Path(out)
    require(not (out / 'spatial.stage.json').exists(), 'spatial phase already completed')
    input_ref, _, _ = old.inputs(scope)
    evidence = b2_cache_evidence(scope, input_ref)
    frozen = read(HERE / 'cache_01' / (scope + '.json'))
    require({key: value for key, value in frozen.items() if key != 'utc'} == evidence,
            'fresh spatial base authority or input binding differs')
    spatial_with_base_identity(source, scope, out, read(RUN / 'b_score_aligned_package_v4/config.json'))


def finish(scope, out):
    verify()
    _, old, frames, _ = helpers()
    from field_contract import compose_from_field
    from package_contract import package, validate_predictions, keyset
    out = Path(out)
    _, manifest, _ = old.inputs(scope)
    require(read(out / 'temporal.stage.json')['invalid_windows'] == 0, 'temporal failures cannot be packaged')
    require(read(out / 'spatial.stage.json')['status'] in ('PASS_STRICT_SOURCE_FIELD_SPATIAL', 'PASS_EMPTY_SPACE_NO_MODEL_CALL'),
            'source spatial phase not complete')
    selected, shots = rows(out / 'selected.jsonl'), rows(out / 'field_shots.jsonl')
    requests, outputs = rows(out / 'anchor_requests.jsonl'), rows(out / 'anchor_output.jsonl')
    projected = frames.legacy_manifest(manifest)
    predictions, provenance = compose_from_field(projected, selected, shots, requests, outputs)
    old.write_rows(out / 'predictions.jsonl', predictions); old.write_rows(out / 'provenance.jsonl', provenance)
    result = validate_predictions(projected, predictions, keyset(selected), provenance)
    write(out / 'metadata.json', dict(records=manifest['records'], errors=[]), fresh=True)
    pending = out / 'candidate_T_8B.PENDING.zip'
    result.update(package(out / 'predictions.jsonl', pending))
    subprocess.run([sys.executable, '-B', str(RUN / 'baseline_a_pts_v1/vendor/independent_validate.py'),
         '--strict-loader-root', str(RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader'),
         '--metadata', str(out / 'metadata.json'), '--selected', str(out / 'selected.jsonl'),
         '--predictions', str(out / 'predictions.jsonl'), '--provenance', str(out / 'provenance.jsonl'),
         '--zip', str(pending), '--report', str(out / 'independent_validation.json')], check=True)
    independent = read(out / 'independent_validation.json')
    check_independent(independent, scope, len(selected))
    require(independent.get('predictions_sha256') == sha(out / 'predictions.jsonl') and
            independent.get('provenance_sha256') == sha(out / 'provenance.jsonl') and
            independent.get('zip_sha256') == sha(pending), 'independent accepted artifact SHA differs')
    candidate = out / 'candidate_T_8B.zip'; pending.rename(candidate)
    student = read(HERE / 'student_01/student_completion.json')
    result.update(status='PASS_COMPLETE_T_8B_PACKAGE_ON_LINUX', candidate=str(candidate), scope=scope,
         complete_pipeline_parameters=8782459120, shared_base_counted_once=True, offline_teacher_deployed=False,
         selected_adapter_sha256=student['selected_adapter_sha256'], official_score=None,
         uploaded=False, automatic_return=False, source_lock_sha256=sha(HERE / 'source_lock.json'),
         time_independent_source_field=True, comparison_to_B='NEW_COMPLETE_WINDOW_WEAK_TEACHER_AND_INPUT_RECIPE')
    write(out / 'package.stage.json', result, fresh=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('temporal', 'scheduling', 'spatial', 'finish'))
    parser.add_argument('scope', choices=('nontest', 'rematch'))
    parser.add_argument('out')
    args = parser.parse_args()
    globals()[args.stage](args.scope, args.out)

```


## 匹配工程诊断与模型/生成函数完整原文

来源与字节身份：{"path": "G:\\ai\\AIC视频\\reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\teacher_student_autopilot_v14\\precision_helpers\\engine.py", "bytes": 15496, "sha256": "3fbad758ba7fbfe66499434fe209f7c4494c6a78ebf55dc40805fea970830115"}

```python
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

```


## 学生输入/训练/选点完整核心代码原文（无实际弱标签）

来源与字节身份：{"path": "G:\\ai\\AIC视频\\reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\teacher_student_autopilot_v14\\train_student.py", "bytes": 78139, "sha256": "7b79a6713e3a406d015bc546fc45ce6172b7cf8d3967592779bfdd8c23a6fe09"}

```python
"""One admitted Route A run: inspect an early prefix, compare B and T on weak dev.

All model imports are deferred until authority/data/semantic admission passes.
This engine never downloads, transfers, opens confirm/test, or starts a GPU job.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import statistics
import subprocess
import sys
import time
import traceback

REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
HERE = Path(__file__).resolve().parent
VERSION = HERE.name
INITIAL_SHA = "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23"
APPROVED_MANIFEST_SHA = {"train": "ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf",
                         "dev": "53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700"}
VIDEO_SIZE = {"shortest_edge": 4096, "longest_edge": 25165824}
INPUT_CONTRACT = {
    "max_frames": 64, "video_size": VIDEO_SIZE, "max_input_tokens": 16384,
    "clock": "REAL_SOURCE_PRESENTATION_PTS_RELATIVE_TO_WINDOW_START",
    "sampling": "SELECTED_WINDOW_INTEGER_FLOOR_ENDPOINTS",
    "decoder": "SEQUENTIAL_PYAV_RGB24_WITH_ACTUAL_PTS_AND_PIXEL_SHA",
    "allow_empty": True, "prompt": "NEXT_ROUND_0_TO_5", "truncation": False,
    "same_contract_train_dev_production": True,
    "endpoint_precision": "EXACT_FINITE_DECIMAL_UP_TO_18_FRACTIONAL_DIGITS_NO_ROUNDING",
    "positive_segment_realizability": "ACTUAL_SOURCE_PTS_HALF_OPEN_NONEMPTY",
}
REQUIRED_HELPERS = (
    "next_round_v1/common.py", f"{VERSION}/precision_helpers/contracts.py", "next_round_v1/video_contract.py",
    f"{VERSION}/precision_helpers/training_target.py", f"{VERSION}/precision_helpers/engine.py",
    f"{VERSION}/supervision/validate_teacher.py", f"{VERSION}/supervision/select_windows.py",
    f"{VERSION}/supervision/teacher_prompt.txt", f"{VERSION}/supervision/teacher_metadata_20261007.json",
    f"{VERSION}/supervision/teacher_response.schema.json", f"{VERSION}/precision_helpers/constrained_json.py",
    f"{VERSION}/native_segment_contract.py",
    f"{VERSION}/source_color.py",
    f"{VERSION}/teacher_label.py", f"{VERSION}/boundary_ids.py",
    f"{VERSION}/teacher_prompt.txt", f"{VERSION}/review_prompt.txt",
    "baseline_a_pts_v1/exact_pts.py", "baseline_a_pts_v1/native_frames.py", "baseline_a_pts_v1/pts_contract.py",
    "baseline_a_pts_v1/a_contract.py", "temporal_sft8b_v1/sft_contract.py",
    "temporal_sft8b_v1/train_sft.py", "temporal_sft8b_v1/verify_saved_smoke.py",
    "baseline_a_pts_v1/vendor/temporal_common.py",
)
_VERIFIED_SOURCE_STATS = {}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def record_sha(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def bound(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "missing bound file reference")
    path = Path(ref["path"]).resolve(strict=True)
    require(path.is_file() and sha(path) == ref["sha256"], "bound file changed: " + str(path))
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def helper_paths(run):
    # Frozen modules import each other by their historical names.
    paths = [run / "next_round_v1", run / "baseline_a_pts_v1", run / "baseline_a_pts_v1/vendor",
             run / "temporal_sft8b_v1", run / VERSION / "supervision"]
    sys.path[:0] = list(map(str, paths))
    # common.py prepends old search paths. Explicit module identities, rather
    # than path priority alone, bind the entire serializer/target/generation
    # bridge to this registered version, even after a legacy import.
    precision = Path(__file__).resolve().parent / "precision_helpers"
    for name in ("contracts", "constrained_json", "engine", "training_target"):
        expected = precision / (name + ".py")
        current = sys.modules.get(name)
        if current is None or Path(current.__file__).resolve() != expected.resolve():
            load(expected, name)
        require(Path(sys.modules[name].__file__).resolve() == expected.resolve(), "precision helper binding differs: " + name)
    owner = str(Path(__file__).resolve().parent)
    if owner not in sys.path:
        sys.path.insert(0, owner)


def schedule(n, epochs=3, batch=16, seed=20261007):
    require(type(n) is int and n > 0 and type(epochs) is int and 1 <= epochs <= 3 and
            type(batch) is int and batch > 0, "invalid training schedule")
    rng = random.Random(seed)
    result = []
    for epoch in range(1, epochs + 1):
        order = list(range(n))
        rng.shuffle(order)
        for offset in range(0, n, batch):
            result.append({"epoch": epoch, "indices": order[offset:offset + batch],
                           "epoch_last": offset + batch >= n})
    require(len(result) >= 2, "STOP_T_INSUFFICIENT_ELIGIBLE_UPDATES_WITHIN_MAX_3_EPOCHS")
    return result


def prefix_update_count(batches, limit=4):
    require(type(limit) is int and 2 <= limit <= 4, "early prefix update limit must be 2..4")
    require(len(batches) >= 2, "STOP_T_INSUFFICIENT_ELIGIBLE_UPDATES_WITHIN_MAX_3_EPOCHS")
    return min(limit, len(batches))


def supervision_classes(targets):
    """Only actual admitted complete-window targets establish class availability."""
    require(targets, "STOP_T_NO_ADMITTED_TRAIN_SUPERVISION")
    counts = {"positive": 0, "explicit_no_highlight": 0}
    for target in targets:
        require(type(target.get("explicit_no_highlight")) is bool, "missing observed target class")
        segments = json.loads(target["target_json"])["segments"]
        require(isinstance(segments, list) and (not segments) == target["explicit_no_highlight"],
                "actual empty target and explicit NO semantics differ")
        counts["explicit_no_highlight" if target["explicit_no_highlight"] else "positive"] += 1
    require(counts["positive"] > 0, "STOP_T_NO_POSITIVE_SUPERVISION_FOR_ROUTE_A")
    return dict(**counts, rejection_supervision_available=counts["explicit_no_highlight"] > 0,
        whole_window_rejection_learning_claim=False,
        supervision_role="ACCEPTED_COMPLETE_WINDOW_WEAK_TEACHER_NOT_HUMAN_TRUTH")


def select_checkpoint(candidates):
    """Candidate zero is retained; a weak-metric tie always preserves original B."""
    require(candidates and any(c["epoch"] == 0 for c in candidates), "original B candidate zero missing")
    require(all(type(c["epoch"]) is int and c["epoch"] >= 0 and
                type(c["video_macro_f1"]) in (int, float) and math.isfinite(c["video_macro_f1"])
                for c in candidates), "invalid candidate development evidence")
    return max(candidates, key=lambda value: (value["video_macro_f1"], -value["epoch"]))


def floor_indices(first, stop, max_frames=64):
    require(type(first) is int and type(stop) is int and 0 <= first < stop and max_frames == 64,
            "invalid T source ordinal window")
    count = stop - first
    if count <= max_frames:
        return list(range(first, stop))
    return [first + i * (count - 1) // (max_frames - 1) for i in range(max_frames)]


def window_from_pts(source_path, source_sha256, points, start, end, window_id, **identity):
    """Public T production planner; points are raw presentation seconds.

    The controller supplies a SHA-bound full source PTS table and natural
    windows, including the packet-duration endpoint. It must preserve raw
    origin in start/end; this function never derives timestamps from FPS.
    """
    from bisect import bisect_left
    require(points and all(math.isfinite(t) for t in points) and all(b > a for a, b in zip(points, points[1:])),
            "full source native PTS required")
    require(math.isfinite(start) and math.isfinite(end) and start < end and end - start <= 30 + 1e-6,
            "invalid T natural time window")
    first, stop = bisect_left(points, start), bisect_left(points, end)
    ids = floor_indices(first, stop)
    return dict(identity, source_path=str(source_path), source_sha256=source_sha256, window_id=window_id,
        window_pts_start_sec=start, window_pts_end_exclusive_sec=end, window_duration_sec=end - start,
        planned_source_frame_ordinals=ids, planned_actual_pts_sec=[points[i] for i in ids],
        eligible_source_frame_count=stop - first, source_total_frames=len(points))


def validate_isolation(train, dev):
    require(train and dev and len(train) <= 512 and len(dev) <= 64, "invalid eligible train/dev denominator")
    all_ids = [r["window"]["window_id"] for r in train + dev]
    require(len(set(all_ids)) == len(all_ids), "duplicate eligible window")
    for split, values in (("train", train), ("dev", dev)):
        for row in values:
            w = row["window"]
            require(w.get("split") == split and w.get("source_group") == w.get("youtube_id"), "wrong split/source unit")
            p = PurePosixPath(w.get("source_path", ""))
            require(p.is_absolute() and ".." not in p.parts and
                    PurePosixPath("/home/inspur/aic_video_data/videos") in p.parents, "confirm/test/outside-media path rejected")
    for key in ("youtube_id", "source_path", "source_sha256"):
        require(not ({r["window"][key] for r in train} & {r["window"][key] for r in dev}), "train/dev leakage: " + key)


def validate_lineage(eligible, approved, split):
    identities = {(r["source_path"], r["youtube_id"]): set() for r in approved}
    for row in approved:
        require(row.get("split") == split, "approved manifest split changed")
        identities[(row["source_path"], row["youtube_id"])].add(row["sample_id"])
    for row in eligible:
        window = row["window"]
        key = (window["source_path"], window["youtube_id"])
        parents = window.get("parent_sample_ids")
        require(key in identities and isinstance(parents, list) and parents and
                set(parents) <= identities[key], "eligible source/parent not in approved original " + split + " registry")


def validate_raw_semantic(item, original):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "duplicate raw semantic review JSON key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("nonfinite raw semantic review JSON: " + value)
    value = json.loads(item["raw_response"], object_pairs_hook=pairs, parse_constant=invalid_constant)
    require(isinstance(value, dict) and set(value) == {"window_id", "observation_scope", "semantics_consistent", "uncertain", "reason", "issues"},
            "raw semantic review response schema changed")
    require(value["window_id"] == original["window_id"] and value["semantics_consistent"] is True and
            value["uncertain"] is False and value["issues"] == [] and value["reason"] == item["reason"] and
            isinstance(value["reason"], str) and value["reason"].strip(), "raw semantic review does not support receipt PASS")
    scope = value["observation_scope"]
    require(isinstance(scope, dict) and set(scope) == {"window_pts_start_sec", "window_pts_end_exclusive_sec", "sampled_pts_sec", "all_provided_frames_reviewed"}
            and scope["all_provided_frames_reviewed"] is True, "raw semantic review observation scope changed")
    window = original["window"]; observation = original["actual_observation"]
    for key in ("window_pts_start_sec", "window_pts_end_exclusive_sec"):
        require(type(scope[key]) in (int, float) and math.isfinite(scope[key]) and abs(scope[key] - window[key]) <= 1e-6,
                "raw semantic review window extent differs")
    points = scope["sampled_pts_sec"]
    require(isinstance(points, list) and len(points) == len(observation["actual_pts_sec"]) and
            all(type(a) in (int, float) and math.isfinite(a) and abs(a - b) <= 1e-6 for a, b in zip(points, observation["actual_pts_sec"])),
            "raw semantic review did not observe same actual PTS")
    require(item.get("parsed_response") == value and item.get("source_frame_pixel_sha256") == observation["frame_pixel_sha256"] and
            item.get("source_frame_ordinals") == observation["source_frame_ordinals"] and item.get("actual_pts_sec") == observation["actual_pts_sec"],
            "semantic review raw/frame identity differs from teacher observation")


def verify_semantic(review, validation_sha, file_hashes, eligible, records, verifier, validator):
    """Engineering-complete review admits only individually supported records.

    Every reviewed raw decision is checked, including disagreement/UNKNOWN.
    The full denominator and all original records remain SHA-bound.
    """
    require(review.get("schema") == "aic_automated_weak_semantic_review_v2" and
            review.get("status") == "PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW" and
            review.get("mode") == "AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH" and
            review.get("manual_ground_truth") is False and review.get("confirm_opened") is False and
            review.get("contest_assets_opened") is False and
            review.get("second_review_same_teacher_not_independent_evidence") is True and
            review.get("review_blind_to_first_answer") is True and
            review.get("no_unknown_or_unobserved_gaps_certified_negative") is True and
            review.get("no_forced_empty_quota") is True, "STOP_T_SEMANTIC_REVIEW_REQUIRED")
    require(review.get("validation_receipt_sha256") == validation_sha and review.get("files") == file_hashes,
            "semantic review does not bind actual supervision files")
    eligible_expected = {r["teacher_record_sha256"] for r in eligible}
    expected = set(records)
    reviewed = review.get("reviewed_teacher_record_sha256", [])
    supported = review.get("supported_teacher_record_sha256", [])
    require(isinstance(reviewed, list) and len(set(reviewed)) == len(reviewed) and set(reviewed) == expected,
            "eligible semantics not exhaustively reviewed")
    require(isinstance(supported, list) and len(set(supported)) == len(supported) and set(supported) <= eligible_expected,
            "unknown/foreign/duplicate supported teacher record")
    raw_path = bound(review["raw_review_receipts"])
    raw = rows(raw_path)
    indexed = {r.get("teacher_record_sha256"): r for r in raw}
    require(len(indexed) == len(raw) and expected == set(indexed), "missing/duplicate/foreign real blind reviews")
    actual_supported = set()
    classification = {}
    actual_table = []
    for digest in expected:
        item = indexed[digest]
        original = records[digest]
        require(item.get("schema") == "aic_blind_local_window_second_selection_v1" and
                item.get("window_id") == original["window_id"] and
                item.get("program_complete_observation") is True and
                item.get("same_teacher_not_independent_truth") is True and item.get("manual_ground_truth") is False and
                (item.get("diagnostic_only") is False or verifier.approved_registered_pilot_review(item, original)) and
                isinstance(item.get("reason"), str) and item["reason"].strip() and
                item.get("reviewer_model_id") == verifier.TEACHER_ID and
                item.get("reviewer_model_revision") == verifier.TEACHER_REVISION and
                item.get("reviewer_runtime_revision") == item.get("second_teacher", {}).get("runtime_revision") and
                isinstance(item.get("raw_response"), str) and item["raw_response"].strip(),
                "STOP_T_UNBOUND_OR_UNEXPLAINABLE_BLIND_REVIEW")
        require(item.get("raw_response_sha256") == hashlib.sha256(item["raw_response"].encode()).hexdigest() and
                item["raw_response"] == item.get("model_raw_answer"),
                "semantic review raw response not bound")
        comparison = verifier.verify_blind_review_projection(item, original, validator)
        classification[digest] = comparison["support_class"]
        if comparison["supported"]:
            expected_class = ("SUPPORTED_COMPLETE_WINDOW_NO_HIGHLIGHT" if original["explicit_no_highlight"]
                              else "SUPPORTED_COMPLETE_WINDOW_POSITIVE")
            require(comparison["support_class"] == expected_class and
                    item.get("review_status") == "PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW" and
                    item.get("uncertain") is False and item.get("semantics_consistent") is True,
                    "supported review does not agree with actual canonical target class")
            if digest in eligible_expected:
                require(original.get("sft_eligible") is True, "supported target lacks original strict eligibility")
                actual_supported.add(digest)
        else:
            require(comparison["support_class"] == "UNKNOWN" and
                    item.get("review_status") == "UNKNOWN_WEAK_SELECTION_DISAGREEMENT" and
                    item.get("uncertain") is True and item.get("semantics_consistent") is False,
                    "disagreement/UNKNOWN was changed to usable supervision")
        actual_table.append(dict(window_id=original["window_id"], split=original["split"], teacher_record_sha256=digest,
            support_class=comparison["support_class"], boundary_supported=comparison["boundary_supported"],
            reasons=comparison["reasons"]))
    require(actual_supported == set(supported), "semantic supported set differs from actual blind raw decisions")
    support_table = review.get("perrecord_support")
    require(isinstance(support_table, list) and len(support_table) == len(actual_table) and
            sorted(support_table, key=lambda value: value["teacher_record_sha256"]) ==
            sorted(actual_table, key=lambda value: value["teacher_record_sha256"]),
            "perrecord support audit differs from original blind receipts")
    selected_by_split = {split: sum(record["split"] == split for record in records.values()) for split in ("train", "dev")}
    supported_records = [records[digest] for digest in actual_supported]
    supported_count = lambda predicate: {split: sum(record["split"] == split and predicate(record)
        for record in supported_records) for split in ("train", "dev")}
    expected_counts = dict(selected_denominator=len(expected), selected_by_split=selected_by_split,
        support_class_counts=dict(Counter(classification.values())), supported_by_split=supported_count(lambda record: True),
        supported_positive_by_split=supported_count(lambda record: not record["explicit_no_highlight"]),
        supported_explicit_empty_by_split=supported_count(lambda record: record["explicit_no_highlight"]),
        unknown_count=sum(value == "UNKNOWN" for value in classification.values()),
        boundary_supported_count=sum(value["boundary_supported"] for value in actual_table))
    for key, value in expected_counts.items():
        require(review.get(key) == value, "semantic denominator/class count differs: " + key)
    return raw_path, actual_supported, dict(**expected_counts, original_eligible_records=len(eligible_expected),
        supported_records=len(actual_supported), excluded_records=len(expected - actual_supported),
        perrecord_classification=classification,
        all_original_denominators_and_bytes_bound=True,
        teacher_consistency_is_weak_evidence_not_human_truth=True)


def owns(path, run):
    """All student stages must stay under this independent version, not v1."""
    return Path(run).resolve() / Path(__file__).resolve().parent.name in Path(path).resolve().parents


def admit(args):
    run = Path(args.run_dir).resolve(strict=True)
    labels = Path(args.labels_dir).resolve(strict=True)
    out = Path(args.out_dir).resolve()
    require(owns(out, run) and not out.exists(), "fresh owned output directory required")
    config_path = Path(args.config).resolve(strict=True)
    config = read(config_path)
    require(config.get("schema") == "aic_t_student_config_v1" and config.get("authorized") is True and
            config.get("formal_C_BCE_admitted") is False and config.get("official_upload_authorized") is False,
            "student execution authority/scope missing")
    require(config.get("input_contract") == INPUT_CONTRACT, "T train/dev/production input contract differs")
    opt = config["optimization"]
    expected = {"lr": 1e-5, "optimizer": "AdamW", "betas": [0.9, 0.999], "eps": 1e-8,
                "weight_decay": 0.0, "grad_clip_norm": 1.0, "effective_batch_windows": 16,
                "microbatch_windows": 1, "gradient_accumulation_steps": 16, "max_epochs": 3,
                "prefix_update_limit": opt.get("prefix_update_limit"), "seed": 20261007, "precision": "bf16", "attn_implementation": "sdpa",
                "gradient_checkpointing_use_reentrant": False}
    require(opt == expected, "frozen student optimization recipe changed")
    require(type(opt["prefix_update_limit"]) is int and 2 <= opt["prefix_update_limit"] <= 4,
            "early prefix update limit must be 2..4")
    require(config.get("dev_stop_rule") == {"all_selected_fraction": 0.99, "widespread_degraded_group_fraction": 0.75,
                "widespread_macro_f1_drop": 0.05}, "undeclared developer stop rule")
    lock_path = bound(config["source_lock"])
    lock = read(lock_path)
    files = lock.get("files", {})
    require(files and isinstance(files, dict), "source lock files missing")
    def locked(path):
        absolute = str(Path(path).resolve(strict=True))
        require(absolute in files and sha(absolute) == files[absolute], "source helper outside dynamic source lock: " + absolute)
    for relative in REQUIRED_HELPERS:
        locked(run / relative)
    locked(__file__)
    for path, digest in files.items():
        require(sha(path) == digest, "source lock changed: " + path)
    helper_paths(run)
    import sft_contract as old
    validation_path = bound(config["data"]["validation_receipt"])
    require(validation_path == labels / "validation_receipt.json", "labels directory/validation reference differs")
    validation = read(validation_path)
    require(validation.get("schema") == "aic_complete_window_validation_receipt_v1" and
            validation.get("weak_teacher_only") is True and validation.get("confirm_opened") is False and
            validation.get("contest_assets_opened") is False and validation.get("unlabelled_windows_never_converted_to_empty") is True,
            "non-test weak supervision validation required")
    hashes = {name: sha(labels / name) for name in ("eligible_train.jsonl", "eligible_dev.jsonl", "validated_records.jsonl")}
    require(validation.get("files") == hashes, "eligible/raw validated supervision bytes changed")
    eligible = {split: rows(labels / ("eligible_" + split + ".jsonl")) for split in ("train", "dev")}
    validate_isolation(eligible["train"], eligible["dev"])
    approved_paths = {}
    for split in ("train", "dev"):
        ref = config["data"]["approved_" + split + "_manifest"]
        require(ref["sha256"] == APPROVED_MANIFEST_SHA[split], "original approved split registry changed")
        path = bound(ref); approved_paths[split] = path
        validate_lineage(eligible[split], rows(path), split)
    verifier = load(HERE / "teacher_label.py", "t_registered_teacher_label")
    require(Path(verifier.__file__).resolve() == HERE / "teacher_label.py", "teacher protocol verifier identity differs")
    require(Path(verifier.boundary.__file__).resolve() == HERE / "boundary_ids.py", "native boundary protocol identity differs")
    validator = verifier.validator_for(run)
    actual_records = rows(labels / "validated_records.jsonl")
    records = {record_sha(r): r for r in actual_records}
    require(len(records) == len(actual_records) == validation.get("record_count") and
            len({record["window_id"] for record in actual_records}) == len(actual_records), "duplicate/missing validated record")
    require({split: sum(record["split"] == split for record in actual_records) for split in ("train", "dev")} ==
            {"train": 128, "dev": 32}, "original full-window collection denominator changed")
    original_by_split = {split: [dict(window=record["window"]) for record in actual_records if record["split"] == split]
                         for split in ("train", "dev")}
    validate_isolation(original_by_split["train"], original_by_split["dev"])
    for split, targets in original_by_split.items():
        validate_lineage(targets, rows(approved_paths[split]), split)
    sources = {}
    for original in actual_records:
        require(original.get("status") in ("PASS_WEAK_COMPLETE_WINDOW_TARGET", "EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET",
                "EXCLUDED_UNREPRESENTABLE_SEGMENT_COUNT") and original.get("label_status") == "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH",
                "original collection contains engineering-invalid or foreign teacher record")
        w, obs = original["window"], original["actual_observation"]
        validator.validate_window(w); validator.validate_observation(w, obs)
        verifier.verify_model_decision_projection(original)
        # Exact legacy first-record identity already passed its original validator.
        if not verifier.approved_legacy_record(original):
            validator.validate_teacher(original["teacher"], validator.prompt_for(w, obs))
        response = validator.strict_json(original["raw_answer"])
        validator.validate_response(w, obs, response)
        require(response == original["parsed_answer"] and original["split"] == w["split"] and
                original["window_id"] == w["window_id"] and original["source_group"] == w["source_group"],
                "original complete collection canonical projection or identity differs")
        source = Path(w["source_path"]).resolve(strict=True)
        media_root = Path("/home/inspur/aic_video_data/videos").resolve(strict=True)
        require(media_root in source.parents and source.is_file(), "original source escapes approved media root")
        require(str(source) not in sources or sources[str(source)] == w["source_sha256"], "inconsistent original media SHA")
        sources[str(source)] = w["source_sha256"]
    for split, targets in eligible.items():
        for target in targets:
            require(target.get("schema") == "aic_complete_window_sft_target_v1", "foreign target schema")
            original = records.get(target.get("teacher_record_sha256"))
            require(original is not None and original.get("status") == "PASS_WEAK_COMPLETE_WINDOW_TARGET" and
                    original.get("sft_eligible") is True and original.get("uncertain") is False and
                    original.get("label_status") == "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH", "target lacks eligible actual teacher record")
            require(original["window"] == target["window"] and original["target_json"] == target["target_json"] and
                    original["explicit_no_highlight"] == target["explicit_no_highlight"], "target projection differs from reviewed teacher")
            w, obs = original["window"], original["actual_observation"]
            verifier.verify_model_decision_projection(original)
            validator.validate_window(w); validator.validate_observation(w, obs)
            # Exact legacy first-record identity already passed its original validator.
            if not verifier.approved_legacy_record(original):
                validator.validate_teacher(original["teacher"], validator.prompt_for(w, obs))
            response = validator.strict_json(original["raw_answer"])
            validator.validate_response(w, obs, response)
            require(response == original["parsed_answer"] and original["split"] == split, "raw response differs from validator projection")
            from contracts import answer_string
            parsed = json.loads(target["target_json"])["segments"]
            require(parsed == [[s["start_sec"], s["end_sec"]] for s in response["retained_segments"]] and
                    target["explicit_no_highlight"] == response["explicit_no_highlight"],
                    "raw teacher answer/interval-only target projection differs")
            answer_string(parsed, w["window_duration_sec"], allow_empty=True)
            source = Path(w["source_path"]).resolve(strict=True)
            media_root = Path("/home/inspur/aic_video_data/videos").resolve(strict=True)
            require(media_root in source.parents and source.is_file(), "resolved source escapes approved media root")
            digest = w["source_sha256"]
            require(str(source) not in sources or sources[str(source)] == digest, "inconsistent media SHA")
            sources[str(source)] = digest
    eligible_digests = {target["teacher_record_sha256"] for targets in eligible.values() for target in targets}
    original_strict_eligible = {digest for digest, original in records.items() if original["sft_eligible"] is True}
    require(eligible_digests == original_strict_eligible and validation.get("eligible_count") == len(eligible_digests) and
            validation.get("eligible_by_split") == {split: len(targets) for split, targets in eligible.items()},
            "original strict eligible denominator or projection was reduced before blind review")
    review_path = bound(config["data"]["semantic_review_receipt"])
    raw_review_path, supported, semantic_admission = verify_semantic(read(review_path), sha(validation_path), hashes,
                                     eligible["train"] + eligible["dev"], records, verifier, validator)
    original_eligible_by_split = {split: len(targets) for split, targets in eligible.items()}
    eligible = {split: [target for target in targets if target["teacher_record_sha256"] in supported]
                for split, targets in eligible.items()}
    validate_isolation(eligible["train"], eligible["dev"])
    semantic_admission.update(original_eligible_by_split=original_eligible_by_split,
        supported_by_split={split: len(targets) for split, targets in eligible.items()})
    model = config["model"]
    require(model.get("base_id") == "Qwen/Qwen3-VL-8B-Instruct" and model.get("base_revision") == REVISION and
            Path(model["base_model_dir"]).resolve() == run / "models/Qwen3-VL-8B-Instruct" and
            Path(model["initial_adapter_dir"]).resolve() == run / "temporal_sft8b_full_v1/train_01/adapter" and
            model.get("initial_adapter_model_sha256") == INITIAL_SHA and model.get("lora_rank") == 16 and
            model.get("lora_alpha") == 32 and model.get("lora_dropout") == .05,
            "pinned B continuation identity changed")
    initial = Path(model["initial_adapter_dir"])
    require(sha(initial / "adapter_model.safetensors") == INITIAL_SHA and
            sha(initial / "adapter_config.json") == model["initial_adapter_config_sha256"], "B adapter bytes changed")
    initial_recipe = read(initial / "adapter_config.json")
    require(initial_recipe["r"] == 16 and initial_recipe["lora_alpha"] == 32 and initial_recipe["lora_dropout"] == .05 and
            initial_recipe["bias"] == "none" and initial_recipe["modules_to_save"] is None, "initial B LoRA recipe changed")
    model_receipt = bound(model["model_receipt"])
    old.verify_model_receipt(Path(model["base_model_dir"]), read(model_receipt))
    classes = supervision_classes(eligible["train"])
    batches = schedule(len(eligible["train"]), epochs=opt["max_epochs"],
                       batch=opt["effective_batch_windows"], seed=opt["seed"])
    prefix_updates = prefix_update_count(batches, opt["prefix_update_limit"])
    for path, digest in sources.items():
        require(sha(path) == digest, "source video changed: " + path)
        st = Path(path).stat()
        _VERIFIED_SOURCE_STATS[path] = (digest, st.st_size, st.st_mtime_ns)
    authorities = {str(p): sha(p) for p in (config_path, lock_path, validation_path, review_path, raw_review_path, model_receipt)}
    authorities.update({str(p): sha(p) for p in approved_paths.values()})
    authorities.update({str(initial / name): sha(initial / name) for name in ("adapter_model.safetensors", "adapter_config.json")})
    authorities.update({str(labels / name): digest for name, digest in hashes.items()})
    return dict(run=run, out=out, config=config, config_path=config_path, files=files, authorities=authorities,
                targets=eligible, records=records, sources=sources, batches=batches,
                prefix_update_count=prefix_updates, supervision_classes=classes,
                semantic_admission=semantic_admission)


def decode_window(window, observation=None):
    """Public sequential T decoder, with optional teacher-observation equality.

    Return (numpy THWC RGB, video_metadata, exact_native_pts_plan, evidence).
    This function also handles contest windows when called by the separately
    admitted production job; training never manufactures such a window.
    """
    import av
    import numpy as np
    w = window
    ids, pts = w["planned_source_frame_ordinals"], w["planned_actual_pts_sec"]
    require(ids and len(ids) == len(pts) <= 64 and ids == sorted(set(ids)) and
            all(type(i) is int and i >= 0 for i in ids) and all(math.isfinite(t) for t in pts), "invalid T frame/PTS plan")
    if "eligible_source_frame_count" in w:
        require(ids == floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"]), "T sampling is not registered integer-floor rule")
    before = Path(w["source_path"]).stat()
    key = str(Path(w["source_path"]).resolve(strict=True))
    signature = (w["source_sha256"], before.st_size, before.st_mtime_ns)
    if _VERIFIED_SOURCE_STATS.get(key) != signature:
        require(sha(w["source_path"]) == w["source_sha256"], "T source byte identity changed")
        _VERIFIED_SOURCE_STATS[key] = signature
    frames, actual_pts, pixels, window_source_pts = [], [], [], []
    with av.open(w["source_path"]) as container:
        require(len(container.streams.video) == 1, "ambiguous source video stream")
        stream = container.streams.video[0]
        rate = stream.average_rate
        require(rate is not None and float(rate) > 0, "actual source FPS unavailable")
        if observation is not None:
            require(observation["fps_num"] == rate.numerator and observation["fps_den"] == rate.denominator,
                    "student/teacher source average FPS metadata differs")
        wanted = iter(ids); current = next(wanted, None)
        for ordinal, frame in enumerate(container.decode(stream)):
            if current is None:
                break
            if ids[0] <= ordinal <= ids[-1]:
                require(frame.pts is not None and frame.time_base is not None, "actual unsampled source frame PTS missing")
                window_source_pts.append(float(frame.pts * frame.time_base))
            if ordinal != current:
                continue
            require(frame.pts is not None and frame.time_base is not None, "actual source frame PTS missing")
            point = float(frame.pts * frame.time_base)
            require(abs(point - pts[len(frames)]) <= 1e-6, "actual decoded ordinal PTS differs from teacher observation")
            color_path = HERE / "source_color.py"
            color = sys.modules.get("t_registered_source_color")
            if color is None or Path(color.__file__).resolve() != color_path.resolve():
                color = load(color_path, "t_registered_source_color")
            require(Path(color.__file__).resolve() == color_path.resolve(), "source color helper identity differs")
            image = color.convert_frame(frame, w["source_sha256"], "rgb24")
            require(image.ndim == 3 and image.shape[-1] == 3, "source RGB geometry changed")
            if "height" in w and "width" in w:
                require(image.shape[:2] == (w["height"], w["width"]), "registered source geometry changed")
            digest = hashlib.sha256(image.tobytes(order="C")).hexdigest()
            if observation is not None:
                require(digest == observation["frame_pixel_sha256"][len(frames)], "student/teacher frame pixel SHA differs")
            frames.append(image); actual_pts.append(point); pixels.append(digest)
            current = next(wanted, None)
    after = Path(w["source_path"]).stat()
    require(len(frames) == len(ids) and (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            "source changed or a planned frame was not decoded")
    arr = np.stack(frames)
    plan = dict(source_frame_ids=ids, source_relative_pts=actual_pts, window_start=w["window_pts_start_sec"])
    total = observation["source_total_frames"] if observation is not None else w.get("source_total_frames", w.get("n_frames"))
    require(type(total) is int and total > ids[-1], "actual full-source frame count must be declared")
    metadata = dict(fps=float(rate), frames_indices=ids, total_num_frames=total, video_backend="pyav")
    from native_frames import prepare_native_processor_input
    arr, metadata = prepare_native_processor_input(arr, metadata, plan)
    return arr, metadata, plan, dict(window_id=w["window_id"], source_sha256=w["source_sha256"],
        source_frame_ids=ids, actual_pts_sec=actual_pts, frame_pixel_sha256=pixels,
        window_source_pts_sec=window_source_pts,
        native_source_clock=True, explicit_lone_frame_copy=len(ids) == 1,
        teacher_pixel_identity_checked=observation is not None, source_fps_num=rate.numerator, source_fps_den=rate.denominator)


def decode_observed(target, record, np=None):
    return decode_window(target["window"], record["actual_observation"])


def production_encode(processor, window, observation=None):
    """Public T encode shared by fixed dev and full contest T inference."""
    import torch
    from engine import prompt_for
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    arr, metadata, plan, decoded = decode_window(window, observation)
    with exact_native_pts(processor, plan, metadata["fps"]) as native:
        encoded = encode(processor, text=[prompt_for(processor, True)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata],
            video_size=VIDEO_SIZE, max_input=16384)
        verify_native_encoding(processor, encoded, native)
    return encoded, dict(**decoded, native_processor_identity=native, **identity(processor, encoded, len(arr)))


def production_generate(model, processor, window, encoded, details, candidates=None):
    from engine import generate_window
    from constrained_json import ascii_token_candidates
    if candidates is None:
        candidates = ascii_token_candidates(processor.tokenizer)
    # Output remains window-local; the controller adds source-global start for packaging.
    result = generate_window(model, processor, encoded, details, 0, window["window_duration_sec"], candidates, True)
    if result["output_valid"]:
        from native_segment_contract import native_segment_ranges
        try:
            ranges = native_segment_ranges(result["parsed_segments"], details["window_source_pts_sec"],
                window["window_pts_start_sec"], window["window_duration_sec"])
            result["native_frame_realizability"] = {"status":"PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY", "ranges":ranges,
                "not_limited_to_64_teacher_samples":True}
        except (ValueError, KeyError) as error:
            result.update(status="PARSE_FAILURE", output_valid=False,
                rejected_parsed_segments=result["parsed_segments"], parsed_segments=None,
                parse_errors=["SOURCE_FRAME_CONTRACT: " + str(error)],
                native_frame_realizability={"status":"STOP_NO_ACTUAL_SOURCE_FRAME", "failure_converted_to_empty":False})
    return result


def encode_example(processor, target, record, torch, np):
    from training_target import build_target, from_teacher_record
    from engine import prompt_for
    from video_contract import identity
    arr, metadata, plan, decoded = decode_observed(target, record, np)
    video = torch.from_numpy(arr).permute(0, 3, 1, 2)
    encoded, mask = build_target(processor, prompt_for(processor, True), video, metadata,
        from_teacher_record(record), target["window"]["window_duration_sec"], VIDEO_SIZE,
        max_input=16384, native_plan=plan, source_fps=metadata["fps"])
    return encoded, dict(**decoded, assistant_mask=mask, input_identity=identity(processor, encoded, len(arr)))


def encode_dev(processor, target, record, torch, np):
    return production_encode(processor, target["window"], record["actual_observation"])


def union(segments):
    result = []
    for start, end in sorted(segments):
        if not result or start > result[-1][1]:
            result.append([start, end])
        else:
            result[-1][1] = max(end, result[-1][1])
    return result


def temporal_stats(pred, truth):
    p, g = union(pred), union(truth)
    ps, gs = sum(b - a for a, b in p), sum(b - a for a, b in g)
    overlap = sum(max(0, min(b, d) - max(a, c)) for a, b in p for c, d in g)
    return dict(f1=2 * overlap / (ps + gs) if ps + gs else 1.0,
        precision=overlap / ps if ps else float(gs == 0), recall=overlap / gs if gs else float(ps == 0),
        pred_seconds=ps, truth_seconds=gs, intersection_seconds=overlap)


def bootstrap(values, seed=20261007, draws=10000):
    rng = random.Random(seed)
    sims = sorted(statistics.mean(rng.choice(values) for _ in values) for _ in range(draws))
    return [sims[int(.025 * draws)], sims[int(.975 * draws)]]


def prefix_resume_position(batches, completed_update, report):
    """Persist work pending *after* the optimizer update, including epoch dev."""
    require(0 < completed_update <= len(batches), "invalid prefix data position")
    batch = batches[completed_update - 1]
    next_batch = batches[completed_update] if completed_update < len(batches) else None
    return dict(completed_update=completed_update, next_schedule_index=completed_update,
        completed_epoch_checkpoints=copy.deepcopy(report.get("checkpoints", [])),
        completed_epoch_devmetrics=copy.deepcopy(report.get("devmetrics", [])),
        current_epoch=batch["epoch"], current_epoch_last_batch=bool(batch["epoch_last"]),
        pending_phase="EPOCH_END_CHECKPOINT_AND_DEV_PENDING" if batch["epoch_last"] else "NEXT_TRAIN_BATCH",
        pending_epoch_end=batch["epoch"] if batch["epoch_last"] else None,
        next_epoch=next_batch["epoch"] if next_batch else None,
        report_snapshot=copy.deepcopy(report), entire_schedule=copy.deepcopy(batches))


def rng_snapshot(torch, np, *, cuda=True):
    return dict(python_rng=random.getstate(), numpy_rng=np.random.get_state(),
        torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state_all() if cuda else [])


def assert_tree_equal(expected, actual, torch, np, location="state"):
    """Compare real checkpoint tensor bytes/dtypes and Python/NumPy metadata."""
    if isinstance(expected, torch.Tensor):
        require(isinstance(actual, torch.Tensor) and expected.dtype == actual.dtype and
                expected.shape == actual.shape and torch.equal(expected.detach().cpu(), actual.detach().cpu()),
                "checkpoint tensor roundtrip mismatch: " + location)
    elif isinstance(expected, np.ndarray):
        require(isinstance(actual, np.ndarray) and expected.dtype == actual.dtype and
                expected.shape == actual.shape and np.array_equal(expected, actual),
                "checkpoint NumPy roundtrip mismatch: " + location)
    elif isinstance(expected, dict):
        require(isinstance(actual, dict) and set(expected) == set(actual), "checkpoint mapping mismatch: " + location)
        for key in expected:
            assert_tree_equal(expected[key], actual[key], torch, np, location + "/" + str(key))
    elif isinstance(expected, (list, tuple)):
        require(type(expected) is type(actual) and len(expected) == len(actual), "checkpoint sequence mismatch: " + location)
        for index, (left, right) in enumerate(zip(expected, actual)):
            assert_tree_equal(left, right, torch, np, location + "/" + str(index))
    else:
        require(type(expected) is type(actual) and expected == actual, "checkpoint scalar mismatch: " + location)


def trusted_state_roundtrip(path, expected, optimizer, trainable, torch, np, *, cuda=True):
    """Read this job's just-written state without replacing active objects/RNG."""
    before_rng = rng_snapshot(torch, np, cuda=cuda)
    assert_tree_equal({key: expected[key] for key in before_rng}, before_rng, torch, np, "saved_current_rng")
    optimizer_identity = id(optimizer)
    parameter_ids = [id(p) for _, p in trainable]
    # It contains Python/NumPy RNG structures; only this SHA-bound own file is
    # trusted. Loading it on CPU avoids a second CUDA optimizer allocation.
    loaded = torch.load(path, map_location="cpu", weights_only=False)
    assert_tree_equal(expected, loaded, torch, np)
    assert_tree_equal(loaded["optimizer"], optimizer.state_dict(), torch, np, "active_optimizer")
    current = {name: p.detach().cpu() for name, p in trainable}
    assert_tree_equal(loaded["lora"], current, torch, np, "active_lora")
    assert_tree_equal(before_rng, rng_snapshot(torch, np, cuda=cuda), torch, np, "unchanged_active_rng")
    require(id(optimizer) == optimizer_identity and [id(p) for _, p in trainable] == parameter_ids,
            "prefix validation replaced active optimizer/parameters")
    return dict(status="PASS_TRUSTED_PREFIX_STATE_ROUNDTRIP", state_sha256=sha(path),
        optimizer_tensor_metadata_and_bytes_equal=True, lora_tensor_metadata_and_bytes_equal=True,
        python_numpy_torch_cuda_rng_equal=True, schedule_and_pending_epoch_state_equal=True,
        active_optimizer_reference_unchanged=True, active_parameter_references_unchanged=True,
        active_rng_unchanged=True, cuda_rng_checked=cuda, loaded_on="cpu", optimizer_updates_performed=0)


def prefix_cpu_reload(args):
    """Independent CPU process; cannot alter the active CUDA model/RNG."""
    run = Path(args.run_dir).resolve(strict=True)
    helper_paths(run)
    adapter = Path(args.prefix_adapter).resolve(strict=True)
    require(owns(adapter, run), "prefix adapter outside owned run")
    config = read(args.config)
    bound(config["source_lock"])
    for path, digest in read(config["source_lock"]["path"])["files"].items():
        require(sha(path) == digest, "prefix CPU reload source changed")
    require(sha(adapter / "adapter_model.safetensors") == args.expected_adapter_sha and
            sha(adapter / "adapter_config.json") == args.expected_adapter_config_sha, "prefix adapter changed before CPU reload")
    import torch
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    from safetensors.torch import load_file
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "independent adapter reload must be CPU-only")
    base = Qwen3VLForConditionalGeneration.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
        local_files_only=True, torch_dtype=torch.bfloat16, device_map={"": "cpu"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    model = PeftModel.from_pretrained(base, adapter, is_trainable=False)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    inventory = sum(p.numel() for _, p in unique_parameters(model))
    require(inventory == 8782459120, "independent prefix model parameter inventory differs")
    targets = {name.removeprefix("base_model.model.") for name, module in model.named_modules()
               if hasattr(module, "lora_A") and "default" in module.lora_A}
    expected_targets = {f"model.language_model.layers.{i}.self_attn.{proj}" for i in range(36)
                        for proj in ("q_proj", "k_proj", "v_proj", "o_proj")}
    require(targets == expected_targets, "independent prefix LoRA target modules differ")
    saved = load_file(str(adapter / "adapter_model.safetensors"))
    actual = {name.replace(".default.", "."): p.detach().cpu() for name, p in unique_parameters(model) if "lora_" in name}
    require(len(actual) == 288 and set(actual) == set(saved) and all(
        actual[name].dtype == saved[name].dtype and torch.equal(actual[name], saved[name]) for name in actual),
        "independent prefix reload tensor bytes differ")
    frozen = canonical_frozen_hash(model, torch)
    with model.disable_adapter():
        adapter_off = canonical_frozen_hash(model, torch)
    require(frozen == adapter_off and frozen["sha256"] == args.expected_base_sha,
            "independent prefix CPU reload frozen base/vision differs")
    write(args.verification_report, dict(status="PASS_INDEPENDENT_PREFIX_ADAPTER_CPU_RELOAD",
        adapter_dir=str(adapter), adapter_model_sha256=args.expected_adapter_sha,
        adapter_config_sha256=args.expected_adapter_config_sha, logical_parameters=inventory,
        language_target_modules=len(targets), lora_tensors=len(actual), base_frozen=frozen, adapter_off=adapter_off,
        optimizer_updates=0, device="cpu", active_training_objects_accessed=False,
        checked_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    return 0


def verify_prefix_adapter_in_child(contract, adapter, model, trainable, frozen, torch, np):
    import psutil
    from train_sft import unique_parameters
    frozen_bytes = sum(p.numel() * p.element_size() for name, p in unique_parameters(model) if "lora_" not in name)
    lora_bytes = sum(p.numel() * p.element_size() for _, p in trainable)
    # Fresh CPU base plus PEFT/saved/actual adapter buffers. This estimate is
    # computed from actual tensors, never a fixed RAM quota or admission line.
    estimated_additional_bytes = frozen_bytes + 4 * lora_bytes
    available = psutil.virtual_memory().available
    require(available >= estimated_additional_bytes, "STOP_T_PREFIX_RELOAD_ACTUAL_RAM_CAPACITY_INSUFFICIENT")
    before_rng = rng_snapshot(torch, np)
    optimizer_parameters = [id(p) for _, p in trainable]
    result_path = contract["out"] / "prefix_adapter_reload.json"
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "verify-prefix-adapter",
        "--run-dir", str(contract["run"]), "--config", str(contract["config_path"]),
        "--prefix-adapter", str(adapter), "--expected-adapter-sha", sha(adapter / "adapter_model.safetensors"),
        "--expected-adapter-config-sha", sha(adapter / "adapter_config.json"),
        "--expected-base-sha", frozen["sha256"], "--verification-report", str(result_path)]
    with (contract["out"] / "prefix_adapter_reload.log").open("x", encoding="utf-8") as log:
        subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = read(result_path)
    require(result.get("status") == "PASS_INDEPENDENT_PREFIX_ADAPTER_CPU_RELOAD", "prefix CPU reload did not pass")
    assert_tree_equal(before_rng, rng_snapshot(torch, np), torch, np, "post_child_active_rng")
    require(optimizer_parameters == [id(p) for _, p in trainable], "CPU child replaced active training parameters")
    result.update(actual_ram_available_bytes=available, estimated_additional_cpu_bytes=estimated_additional_bytes,
        active_rng_unchanged=True, active_parameter_references_unchanged=True,
        verification_process="INDEPENDENT_CPU_SUBPROCESS_NO_ACTIVE_MODEL_MUTATION")
    write(result_path, result)
    return result


def dev_failure(summary, baseline, rule):
    if summary["legal_empty_windows"] == summary["windows"] and summary.get("reference_positive_windows", 1):
        return "STOP_T_SYSTEMATIC_ALL_EMPTY_DEV"
    if summary["all_selected_windows"] == summary["windows"]:
        return "STOP_T_SYSTEMATIC_ALL_SELECTED_DEV"
    if baseline is not None:
        groups = summary["group_f1"]
        fraction = sum(groups[g] < baseline["group_f1"][g] for g in groups) / len(groups)
        if fraction >= rule["widespread_degraded_group_fraction"] and baseline["video_macro_f1"] - summary["video_macro_f1"] >= rule["widespread_macro_f1_drop"]:
            return "STOP_T_WIDESPREAD_OPEN_DEV_DEGRADATION"
    return None


def evaluate(model, processor, contract, out, name, torch, np):
    from constrained_json import ascii_token_candidates
    model.eval(); model.config.use_cache = True
    candidates = ascii_token_candidates(processor.tokenizer)
    values = []
    started = time.monotonic()
    with (out / (name + ".jsonl")).open("x", encoding="utf-8") as stream:
        for target in contract["targets"]["dev"]:
            w = target["window"]; record = contract["records"][target["teacher_record_sha256"]]
            encoded, details = encode_dev(processor, target, record, torch, np)
            result = production_generate(model, processor, w, encoded, details, candidates)
            # A parse/inference failure blocks this run; it never receives an [] score.
            stream.write(json.dumps(dict(window_id=w["window_id"], result=result), ensure_ascii=False) + "\n"); stream.flush()
            require(result["output_valid"], "STOP_T_DEV_PARSE_OR_INFERENCE_FAILURE")
            values.append(dict(window_id=w["window_id"], youtube_id=w["youtube_id"], source_path=w["source_path"],
                duration=w["window_duration_sec"], pred=result["parsed_segments"],
                truth=json.loads(target["target_json"])["segments"], status=result["status"]))
            del encoded
    videos = {}
    for value in values:
        video = videos.setdefault(value["source_path"], dict(youtube_id=value["youtube_id"], pred=[], truth=[], duration=0))
        # Each selected source has one natural window. Fail if later manifests introduce more without global clocks.
        require(not video["duration"], "multiple windows/video require a separately declared global-time metric")
        video.update(pred=value["pred"], truth=value["truth"], duration=value["duration"])
    scored = [{**v, "metrics": temporal_stats(v["pred"], v["truth"])} for v in videos.values()]
    groups = sorted({v["youtube_id"] for v in scored})
    group_f1 = {g: statistics.mean(v["metrics"]["f1"] for v in scored if v["youtube_id"] == g) for g in groups}
    result = dict(name=name, windows=len(values), videos=len(scored), groups=len(groups), group_f1=group_f1,
        video_macro_f1=statistics.mean(v["metrics"]["f1"] for v in scored), group_bootstrap_ci95=bootstrap(list(group_f1.values())),
        parse_failures=0, inference_failures=0, legal_empty_windows=sum(not v["pred"] for v in values),
        reference_positive_windows=sum(bool(v["truth"]) for v in values),
        reference_explicit_no_highlight_windows=sum(not v["truth"] for v in values),
        all_selected_windows=sum(temporal_stats(v["pred"], v["truth"])["pred_seconds"] / v["duration"] >= .99 for v in values),
        local_metric_role="SAME_TEACHER_BLIND_AGREEMENT_WEAK_COMPLETE_WINDOW_SELECTION_NOT_HUMAN_TRUTH_OR_OFFICIAL_SCORE",
        confirm_opened=False, contest_assets_opened=False, seconds=time.monotonic() - started,
        same_input_contract=INPUT_CONTRACT, production_generation_function=VERSION + ".train_student.production_generate",
        independent_quality_reference_available=False)
    write(out / (name + ".metrics.json"), result)
    model.config.use_cache = False; model.train()
    for module_name, module in model.named_modules():
        if module_name.endswith(".visual"):
            module.eval()
    return result


def execute(contract):
    out = contract["out"]; out.mkdir(parents=True)
    config = contract["config"]
    prefix_updates = contract["prefix_update_count"]
    report = dict(status="RUNNING_T_STUDENT", schema="aic_t_student_completion_v2", optimizer_steps=0,
        backward_examples=0, prefix_updates=0, total_planned_updates=len(contract["batches"]),
        prefix_required_updates=prefix_updates, prefix_configured_update_limit=config["optimization"]["prefix_update_limit"],
        config_sha256=sha(contract["config_path"]), quality_claim=False, official_score=None,
        confirm_opened=False, contest_assets_opened=False, formal_C_BCE_admitted=False,
        input_contract=INPUT_CONTRACT, updates=[], devmetrics=[], checkpoints=[], candidates=[],
        supervision_classes=contract["supervision_classes"],
        semantic_admission=contract["semantic_admission"],
        learning_rate_schedule="CONSTANT_1E-5_NO_SCHEDULER_OR_RESTART",
        teacher_truth_status="SAME_32B_BLIND_SELECTION_AGREEMENT_WEAK_ONLY_NOT_HUMAN_GROUND_TRUTH")
    started = time.monotonic(); write(out / "progress.json", report)
    try:
        import sft_contract as old
        old.verify_live_gpu_reservation()
        import numpy as np
        import torch
        import transformers
        import peft
        from peft import PeftModel
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        from train_sft import unique_parameters, gradient_evidence
        from verify_saved_smoke import canonical_frozen_hash
        require(transformers.__version__ == "4.57.1" and peft.__version__ == "0.17.1" and torch.cuda.is_available(),
                "pinned CUDA training runtime required")
        seed = config["optimization"]["seed"]
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        base = Qwen3VLForConditionalGeneration.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
            low_cpu_mem_usage=True, attn_implementation="sdpa")
        for parameter in base.parameters():
            parameter.requires_grad_(False)
        model = PeftModel.from_pretrained(base, config["model"]["initial_adapter_dir"], is_trainable=True)
        trainable = [(name, p) for name, p in unique_parameters(model) if p.requires_grad]
        old.validate_trainable_names([name for name, _ in trainable])
        require(len(trainable) == 288 and sum(p.numel() for _, p in unique_parameters(model)) == 8782459120,
                "student logical parameter/LoRA inventory differs")
        targets = {name.removeprefix("base_model.model.") for name, module in model.named_modules()
                   if hasattr(module, "lora_A") and "default" in module.lora_A}
        expected_targets = {f"model.language_model.layers.{i}.self_attn.{proj}" for i in range(36)
                            for proj in ("q_proj", "k_proj", "v_proj", "o_proj")}
        require(targets == expected_targets, "student LoRA target inventory changed")
        processor = AutoProcessor.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
            local_files_only=True, min_pixels=131072, max_pixels=131072)
        require(processor.video_processor.size == VIDEO_SIZE, "legacy-equivalent processor size changed")
        frozen = canonical_frozen_hash(model, torch)
        report["base_frozen_evidence"] = {"before": frozen}
        model.eval(); model.config.use_cache = False
        # Real CE only probes classes which actually exist in admitted data.
        real_ce = {}
        for kind, empty in (("explicit_empty", True), ("positive", False)):
            target = next((t for t in contract["targets"]["train"] if t["explicit_no_highlight"] is empty), None)
            if target is None:
                real_ce[kind] = dict(status="NOT_AVAILABLE_IN_ACCEPTED_SUPERVISION", optimizer_updates=0,
                                     no_synthetic_target_created=True)
                continue
            record = contract["records"][target["teacher_record_sha256"]]
            encoded, evidence = encode_example(processor, target, record, torch, np)
            encoded = {key: value.to("cuda:0") if hasattr(value, "to") else value for key, value in encoded.items()}
            with torch.inference_mode():
                loss = model(**encoded).loss
            require(loss is not None and bool(torch.isfinite(loss)), "real empty/positive assistant CE is missing/nonfinite")
            real_ce[kind] = dict(status="PASS_REAL_ASSISTANT_CE", loss=float(loss), window_id=target["window"]["window_id"],
                teacher_record_sha256=target["teacher_record_sha256"], evidence=evidence, optimizer_updates=0)
            del encoded, loss
        report["real_assistant_ce_acceptance"] = real_ce
        # Input B developer baseline is evaluated once on the same new weak dev before updates.
        baseline = evaluate(model, processor, contract, out, "initial_B_dev", torch, np)
        report["initial_B_dev"] = baseline
        report["candidates"].append(dict(epoch=0, completed_updates=0,
            adapter_dir=config["model"]["initial_adapter_dir"], adapter_model_sha256=INITIAL_SHA,
            adapter_config_sha256=config["model"]["initial_adapter_config_sha256"],
            video_macro_f1=baseline["video_macro_f1"], candidate_role="ORIGINAL_B_37_63_ADAPTER_SAME_NEW_DEV_CONTRACT",
            candidate_eligible=True, rejection_reason=None))
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        optimizer = torch.optim.AdamW([p for _, p in trainable], lr=1e-5, betas=(.9, .999), eps=1e-8, weight_decay=0)
        before_lora = {name: p.detach().cpu().clone() for name, p in trainable}
        torch.cuda.reset_peak_memory_stats()
        with (out / "example_evidence.jsonl").open("x", encoding="utf-8") as evidence_stream:
            # Prefix inspection belongs to this same optimizer/RNG schedule.
            for update, batch in enumerate(contract["batches"], 1):
                optimizer.zero_grad(set_to_none=True); losses = []
                for index in batch["indices"]:
                    target = contract["targets"]["train"][index]
                    record = contract["records"][target["teacher_record_sha256"]]
                    encoded, evidence = encode_example(processor, target, record, torch, np)
                    encoded = {key: value.to("cuda:0") if hasattr(value, "to") else value for key, value in encoded.items()}
                    result = model(**encoded)
                    require(result.loss is not None and bool(torch.isfinite(result.loss)), "missing/nonfinite assistant CE")
                    (result.loss / len(batch["indices"])).backward()
                    loss = float(result.loss.detach().cpu()); losses.append(loss)
                    report["backward_examples"] += 1
                    evidence.update(epoch=batch["epoch"], optimizer_update=update, loss=loss,
                        accumulation_denominator=len(batch["indices"]), teacher_record_sha256=target["teacher_record_sha256"])
                    evidence_stream.write(json.dumps(evidence, ensure_ascii=False) + "\n"); evidence_stream.flush()
                    del result, encoded
                grads = gradient_evidence(trainable, torch, update)
                norm = torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1)
                require(bool(torch.isfinite(norm)) and float(norm) > 0, "invalid LoRA gradient norm")
                optimizer.step()
                current = {name: p.detach().cpu().clone() for name, p in trainable}
                require(len(current) == 288 and all(bool(torch.isfinite(value).all()) for value in current.values()),
                        "missing/nonfinite student LoRA tensor after optimizer update")
                changed = sum(not torch.equal(current[name], before_lora[name]) for name in current)
                require(changed > 0, "LoRA unchanged after genuine optimizer update")
                before_lora = current
                report["optimizer_steps"] = update
                report["prefix_updates"] = min(update, prefix_updates)
                report["updates"].append(dict(update=update, epoch=batch["epoch"], mean_loss=statistics.mean(losses),
                    windows=len(losses), gradient_norm=float(norm), changed_lora_tensors=changed, gradient_evidence=grads))
                if update == prefix_updates:
                    prefix_frozen = canonical_frozen_hash(model, torch)
                    require(prefix_frozen == frozen, "frozen base/vision changed before early-prefix gate")
                    state_path = out / "prefix_state.pt"
                    prefix_adapter = out / f"prefix_{prefix_updates}" / "adapter"
                    before_save_rng = rng_snapshot(torch, np)
                    model.save_pretrained(prefix_adapter, safe_serialization=True)
                    prefix_recipe = read(prefix_adapter / "adapter_config.json")
                    require(prefix_recipe["r"] == 16 and prefix_recipe["lora_alpha"] == 32 and prefix_recipe["lora_dropout"] == .05 and
                            prefix_recipe["bias"] == "none" and prefix_recipe["modules_to_save"] is None, "prefix adapter scalar recipe changed")
                    assert_tree_equal(before_save_rng, rng_snapshot(torch, np), torch, np, "prefix_adapter_save_rng")
                    state = dict(schema="aic_t_prefix_recovery_state_v3", optimizer=optimizer.state_dict(), lora=current,
                        prefix_required_updates=prefix_updates, learning_rate_schedule=report["learning_rate_schedule"],
                        optimizer_parameter_name_order=[name for name, _ in trainable],
                        data_config_sha256=report["config_sha256"], bound_authorities=contract["authorities"],
                        frozen_base_identity=frozen, prefix_adapter_dir=str(prefix_adapter),
                        prefix_adapter_model_sha256=sha(prefix_adapter / "adapter_model.safetensors"),
                        prefix_adapter_config_sha256=sha(prefix_adapter / "adapter_config.json"),
                        **rng_snapshot(torch, np), **prefix_resume_position(contract["batches"], prefix_updates, report))
                    torch.save(state, state_path)
                    roundtrip = trusted_state_roundtrip(state_path, state, optimizer, trainable, torch, np)
                    independent_reload = verify_prefix_adapter_in_child(contract, prefix_adapter, model, trainable, frozen, torch, np)
                    assert_tree_equal(state["optimizer"], optimizer.state_dict(), torch, np, "optimizer_after_independent_reload")
                    report["prefix_gate"] = dict(status="PASS_SAME_RUN_EARLY_UPDATE_PREFIX", completed_updates=prefix_updates,
                        state_path=str(state_path), state_sha256=sha(state_path), base_frozen=prefix_frozen,
                        same_optimizer_rng_data_position=True, extra_epochs_started=False,
                        state_roundtrip=roundtrip, independent_adapter_reload=independent_reload,
                        pending_phase=state["pending_phase"], pending_epoch_end=state["pending_epoch_end"],
                        completed_epoch_checkpoints=state["completed_epoch_checkpoints"])
                    write(out / "prefix_gate.json", report["prefix_gate"])
                    del state
                if batch["epoch_last"]:
                    epoch = batch["epoch"]
                    checkpoint = out / f"epoch_{epoch}"; model.save_pretrained(checkpoint, safe_serialization=True)
                    saved = read(checkpoint / "adapter_config.json")
                    require(saved["r"] == 16 and saved["lora_alpha"] == 32 and saved["lora_dropout"] == .05 and
                            saved["bias"] == "none" and saved["modules_to_save"] is None, "saved student LoRA recipe changed")
                    metrics = evaluate(model, processor, contract, out, f"epoch_{epoch}_dev", torch, np)
                    checkpoint_record = dict(epoch=epoch, completed_updates=update, adapter_dir=str(checkpoint),
                        adapter_model_sha256=sha(checkpoint / "adapter_model.safetensors"),
                        adapter_config_sha256=sha(checkpoint / "adapter_config.json"), video_macro_f1=metrics["video_macro_f1"])
                    failure = dev_failure(metrics, baseline, config["dev_stop_rule"])
                    checkpoint_record.update(candidate_eligible=failure is None, rejection_reason=failure,
                                             candidate_role="TRAINED_T_EPOCH")
                    report["devmetrics"].append(metrics); report["checkpoints"].append(checkpoint_record)
                    report["candidates"].append(checkpoint_record)
                    if failure is not None:
                        report.setdefault("scientific_dev_stop", dict(reason=failure, detected_update=update,
                            detected_epoch=epoch, prefix_gate_required_before_stop=prefix_updates))
                report["wall_seconds"] = time.monotonic() - started
                write(out / "progress.json", report)
                print(json.dumps(dict(stage="T_TRAINING", updates=update, total=len(contract["batches"]),
                                      backward_examples=report["backward_examples"])), flush=True)
                if report.get("scientific_dev_stop") and update >= prefix_updates:
                    report["scientific_dev_stop"].update(actual_stop_update=update,
                        original_schedule_not_expanded=True, selected_candidates_preserved=True)
                    break
        actual_batches = contract["batches"][:report["optimizer_steps"]]
        require(report["prefix_updates"] == prefix_updates and "prefix_gate" in report and
                report["backward_examples"] == sum(len(batch["indices"]) for batch in actual_batches) and
                len(report["checkpoints"]) == sum(batch["epoch_last"] for batch in actual_batches),
                "incomplete same-run prefix or actual data schedule")
        schedule_complete = report["optimizer_steps"] == len(contract["batches"])
        require(schedule_complete or "scientific_dev_stop" in report, "unexplained partial student schedule")
        final_frozen = canonical_frozen_hash(model, torch)
        require(final_frozen == frozen, "frozen base/vision changed during student training")
        selected = select_checkpoint([candidate for candidate in report["candidates"] if candidate["candidate_eligible"]])
        # Semantic reload uses real saved adapter bytes and module identities.
        trained_selected_path = Path(selected["adapter_dir"])
        del optimizer, before_lora, current, trainable
        plain = model.unload(); del model
        reloaded = PeftModel.from_pretrained(plain, trained_selected_path, is_trainable=False)
        for parameter in reloaded.parameters():
            parameter.requires_grad_(False)
        actual_targets = {name.removeprefix("base_model.model.") for name, module in reloaded.named_modules()
                          if hasattr(module, "lora_A") and "default" in module.lora_A}
        require(actual_targets == expected_targets, "selected adapter reload modules changed")
        from safetensors.torch import load_file
        saved_tensors = load_file(str(trained_selected_path / "adapter_model.safetensors"))
        actual = {name.replace(".default.", "."): p.detach().cpu() for name, p in unique_parameters(reloaded) if "lora_" in name}
        require(len(actual) == 288 and set(actual) == set(saved_tensors) and all(torch.equal(actual[n], saved_tensors[n]) and
                actual[n].dtype == saved_tensors[n].dtype for n in actual), "selected adapter reload tensor bytes differ")
        reload_frozen = canonical_frozen_hash(reloaded, torch)
        with reloaded.disable_adapter():
            adapter_off_frozen = canonical_frozen_hash(reloaded, torch)
        require(reload_frozen == adapter_off_frozen == frozen, "selected reload/adapter-off base bytes changed")
        for path, digest in {**contract["files"], **contract["authorities"], **contract["sources"]}.items():
            require(sha(path) == digest, "bound data/source/authority changed during training: " + path)
        report["base_frozen_evidence"].update(after=final_frozen, selected_reload=reload_frozen, adapter_off=adapter_off_frozen)
        report.update(status="PASS_TRAINED_SELECTED_STUDENT_ADAPTER", selected_adapter_dir=selected["adapter_dir"],
            selected_adapter_sha256=selected["adapter_model_sha256"], selected_adapter_config_sha256=selected["adapter_config_sha256"],
            selected_epoch=selected["epoch"], selected_video_macro_f1=selected["video_macro_f1"],
            selection_rule="MAX_SAME_TEACHER_WEAK_DEV_VIDEO_MACRO_F1_THEN_LOWER_EPOCH_INCLUDING_ORIGINAL_B_ZERO",
            prefix_completed_updates=prefix_updates, registered_schedule_completed=schedule_complete,
            selected_candidate_original_B=selected["epoch"] == 0, trained_candidate_selected=selected["epoch"] > 0,
            selected_new_T_improvement_claim=False,
            total_updates=report["optimizer_steps"], base_frozen=True, vision_frozen=True, adapter_reload_succeeded=True,
            actual_logical_parameters=8782459120, peak_memory_allocated_mib=torch.cuda.max_memory_allocated() / 2**20,
            student_training_completed=True, student_training_completed_under_registered_stop_rule=True,
            T_production_inference_started=False, ZIP_delivered=False)
    except Exception as exc:
        report.update(status="STOP_T_STUDENT", failure_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
    report.update(wall_seconds=time.monotonic() - started, checked_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    write(out / "student_completion.json", report); write(out / "progress.json", report)
    return 0 if report["status"] == "PASS_TRAINED_SELECTED_STUDENT_ADAPTER" else 4


def main():
    if sys.argv[1:2] == ["verify-prefix-adapter"]:
        parser = argparse.ArgumentParser(description="Independent trusted prefix adapter CPU reload")
        for field in ("run-dir", "config", "prefix-adapter", "expected-adapter-sha", "expected-adapter-config-sha", "expected-base-sha", "verification-report"):
            parser.add_argument("--" + field, required=True)
        return prefix_cpu_reload(parser.parse_args(sys.argv[2:]))
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("run-dir", "labels-dir", "out-dir", "config"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        contract = admit(args)
    except Exception as exc:
        failure = dict(schema="aic_t_student_completion_v2", status="STOP_T_BEFORE_RUNTIME_IMPORTS",
            failure=type(exc).__name__ + ": " + str(exc), training_started=False, optimizer_steps=0,
            checked_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        # Preserve a concrete failure receipt without overwriting an older run.
        output = Path(args.out_dir).resolve()
        if not args.check_only and owns(output, args.run_dir) and not output.exists():
            output.mkdir(parents=True); write(output / "student_completion.json", failure)
        print(json.dumps(failure), flush=True)
        return 3
    if args.check_only:
        print(json.dumps(dict(status="PASS_T_AUTHORITY_INPUT_AND_WEAK_SEMANTIC_ADMISSION",
            train=len(contract["targets"]["train"]), dev=len(contract["targets"]["dev"]),
            total_updates=len(contract["batches"]), prefix_required_updates=contract["prefix_update_count"],
            supervision_classes=contract["supervision_classes"], training_started=False)), flush=True)
        return 0
    return execute(contract)


if __name__ == "__main__":
    raise SystemExit(main())

```


# 原文附件 r00-tibo.md

# Tibo之父 r00 — actual visible public replies

URL: https://chatgpt.com/dots/01a0f089-8f7d-7137-b9a7-249ad0fa701a

我先核对附件版本、SHA256和完整读取范围，再按文件里的问题做独立裁决。本轮只讨论可审查决策；会以“32B已推理成功、8B已真实训练但新权重未胜出”为当前状态，不把旧问题重新当作待修，也不把教师一致性当真值。

---

版本已核实：AIC-VIDEO-REMATCH-NEXT-20261005，接续20261009-r00；实际附件名context-r00(1).md，233190字节、3540行，SHA256与给定值完全一致。我已完整读完L1–L3540，包括三次Pro原文、V14验收、协议和所附代码。

硬约束确认：37.60仅为用户差值推算，最佳37.63保留；15次更新真实发生，但最终选回原B；81条UNKNOWN不作负例；9B上限、原地模型、100confirm不读、不用复赛内容调参、Pro三次额度已尽。本轮只给讨论决策。

一个需要重点区分的新点：所附旧104开发入口仍有走旧CFR编码分支的路径，而V14的14条开发与生产共用新native-PTS函数。下一轮不能直接把前者的“matched”标签当作已经与V14生产完全一致。

---

我的裁决：今晚优先做一次“不删局部窗口的全局上下文C”匹配实验；后备选S的定向空间诊断，有具体证据才升级为空间候选。停止延长同65条弱样本的CE训练，不立即重开二元网格头，也不因为32B现在跑通就默认再训练边界adapter。

这是按新增信息价值和成本排序，尚不是“C已被证明最可能涨分”。下面是可直接供主控审查、冻结的决策。

一、版本、证据与硬边界

已完整读取20261009-r00，实际文件context-r00(1).md，L1–L3540，233190字节；SHA256：
efff65e7e31b50c964fec3bc0562a22c31a295b5971da5f0c443bc694539d947

当前事实按卷宗确认：

最佳37.63仍属于旧B包；V14的37.60是用户报告低0.03后的推算，未独立核官网
32B已完成160标注＋160盲第二选择；8B真实15更新、195次样本反向，但最终按登记规则选epoch0原B
81 UNKNOWN不作负例；79条受支持窗口仍只是同教师弱一致性
参赛推理总参数≤9B；仅用原地模型，32B不得进入测试生产链；不读100confirm，不看复赛内容或个别预测调参
Pro三次已用尽；Linux容量动态核查，Mac不进关键路径；新大流量仍需另行许可

我核查的是附件文本、代码和聚合验收，不是独立重跑验收或看过媒体。空间插值等被import但未展开的依赖，不能假称已逐行审完。本轮没有连接Linux或执行项目。

二、当前结果真正说明什么

线上低0.03，不能作为“新训练权重线上退化”的证据。

实际提交选回了原B权重。旧B与V14仍有提示、输入时钟和空间生产配方差异。因此可确定的是：新训练轮次没有赢得本次弱开发选择；V14完整配方据用户低于旧B。不能把两件事合并成新权重的线上因果结论。

同理，epoch1与epoch0的宏F1完全相同，也不自动等于逐条预测相同；需看已有原始结果才能判断。

14条开发集的局限比“小样本”更具体。

它是原32条中经同教师支持筛出的14条，另外18条没有进入选轮指标。这里评的是“教师容易一致的子集”，不是原32条总体。

其中4条为空，代码将双空记为F1=1。若四条都答对，单这部分就能贡献4/14≈0.286的宏均值；我没有证据说实际确实如此。因此下一轮必须拆开正例、空例和UNKNOWN覆盖率，不能只盯0.379这个汇总数。

所附代码有两个值得保留的新审计结论，但不足以推翻已完成验收。
L2304、L2313：旧engine.aligned_dev使用强制非空提示，并传clock=None；L2204–2211因此走旧virtual-CFR入口。V14的14条开发与生产则共用L2999–3032的native-PTS、allow-empty入口。下一轮应直接共用后者，不能调用名字叫aligned_dev的旧函数就宣称matched。
L2523–2533、L3370–3387：65条训练每轮实际分成16、16、16、16、1；尾部单样本独立做一次AdamW更新。所谓有效batch16存在尾批例外，可能增加小数据更新方差，但这不是已经证实的退化原因，更不值得因此立即重训。

另一个报告口径问题：旧104入口的点估计报视频宏，配对CI却按来源均值差计算（L2336、L2343–2347）。若主估计是视频宏，bootstrap应抽来源组后带回组内全部视频，重新计算视频宏差；来源宏可另报。

三、C的最强反例，以及我允许的C是什么

最强反例：150秒视频里，一次短暂关键动作落在全源64帧的采样间隙；局部30秒64帧原本看得到。粗览却把反复出现的普通动作写成主线，局部B受到文字暗示，漏掉关键动作、重复保留普通动作。输出更接近弱教师，真实质量仍可能更差。

因此我的C只允许增加上下文，不允许粗览成为窗口筛选器：

所有原自然30秒窗口仍执行，局部帧、PTS和分辨率保持
粗览没列出的事件不等于负例，不能跳过对应窗口
不把C和B结果取并集兜底，不自动扩大边界
合法空事件表可以存在；生成失败不能伪装成空表
事件表引用实际采样帧ID，程序映射PTS；不让模型抄长时间戳
引用ID合法只证明引用存在，不证明事件描述真实

粗览用同8B基座关闭adapter做简短事实描述；局部仍启用原B。模型共享，参数账不因多一次调用而翻倍。首轮不训练，也不加第三层自我审核。

这里还有一个实现边界：L2588–2589明确限制window_from_pts≤30秒。全源粗览需要独立计划器，不能删掉这个断言，把既有局部合同偷偷改成任意时长。保留native PTS和实际采样间隔；floor64按帧序号均匀，并不保证变帧率材料按时间均匀。

Qwen官方确实采用显式时间戳对齐来支持视频定位，这支持严守真实时间输入；它并不能证明本题稀疏粗览必然有效。官方说明

四、今晚具体做什么：固定24来源、三臂、只裁决一次

样本选择：

从已开放104视频／96来源中按来源去重，只使用已许可范围。按源时长四分位分层，每层按固定哈希顺序取6个，共24来源；每源预先固定一个自然窗口，不按预测、教师支持或预期收益选样。某层不足时事前登记顺延规则，不能事后挑补。

预先指定其中8个作工程与成本小试，其余16个只在工程通过后按原提示继续。24来源全保留，UNKNOWN、失败和历史被观察情况全部报告。这是开放开发诊断，不叫盲测；原NONTEST8继续承担完整生产回归，两者不混称。

如果所谓“全源”超出已有使用许可，或未具备相应媒体身份依据，就停止该粗览范围扩展；不能把开发片段许可自动扩大为任意源内容。

三臂固定为：

A：B-match。原B adapter＋当前V14局部native输入、0–5段语法和空间场。
B：C-null。同一个新增上下文模板，事件表为空。
C：C-real。同模板填入一次真实全源粗览事件表。

A是当前生产合同下的控制，不冒称精确复现旧37.63包。B用来分辨“换了提示模板”和“全局事件信息”各自的作用，不自动成为第三个交付包。

共同固定局部像素、64帧、PTS、窗口、processor预算、16384输入上限、greedy、输出语法、权重字节和空间场。C的文本上下文本来就会改变总token，须承认这是整个上下文处理的效果，不能声称纯视觉信息消融。

粗览输出字段、最大条数和文本长度在小试前固定，允许零条；触及token上限不得临时截断或降局部画质。已有控制结果只有完整请求、输入、时钟、模型及运行身份一致才可复用。

本轮先评固定窗口，不能把24窗口均值叫全源视频宏指标。若扩成多窗口评估，要先映射回源时间再限定参考覆盖域；现有evaluate在L3261–3263明确假设每源只有一窗。

必须产出的字段：

源／窗口／分组ID及全部SHA，粗览与局部帧ID、PTS、像素身份
源时长、实际采样间隔、最大间隔、视频token／总token、原始事件表
各臂合法空、失败、选中时长、段数、边界变化；新增、删除和共同选中的时间范围
B/C共同选帧的空间框字节一致性
弱标签覆盖域、支持／UNKNOWN分母、正空分层；不把未知区域计算为负
每阶段真实调用数、顺序解码时间、GPU记账、排队、峰值、父子进程和终态

五、科学门：允许风险候选，但不允许自证

证据分三类：

程序证据：帧身份、PTS、引用范围、格式、完成状态。可以严格验。
弱证据：旧教师／新教师一致性。只能作诊断，而且全局摘要选择与局部教师任务可能不同。
独立语义证据：确实存在的非测试参考，或主控在获准本地画面上对具体事实的可复核审阅。后者也应标为审阅判断，不能冒称人工真值或全库召回。

不要让同一8B或32B再回答一句“支持”，就把第三类填满。看不到画面或没有独立参考时，明确缺失，不能编造幻觉率和真实边界误差。

工程no-go：来源越界、PTS/局部像素不匹配、截断、失败转空、参数超限、共同帧空间场意外改变、缺失结果或账本。相关候选不得生产。

科学no-go：

C-real没有产生有用差异，或变化基本由C-null复现，额外粗览没有增量依据
可复核地出现粗览错误压过局部可见事实，且属于重复机制而非孤立未判案例
出现跨来源的全选／全空或其他系统性退化
收益只来自筛掉难例、UNKNOWN或失败样本
实际成本挤掉一轮更有依据的候选，而新增信息仍不清楚

科学go：工程全过，存在可解释的非测试增量，未观察到上述系统性失败，成本可接受。独立质量参考不足但机制未被否定时，可明确登记为一个“风险整包”；不能称已证明提高真实高光质量。

弱CI跨零不自动拒绝，弱CI大于零也不自动通过。没有可判断的增量、只有一次弱分微升时，我倾向停止本版，而不是用“风险候选”给任何输出开绿灯。

固定24完成后裁决一次。语义结果不合意，不得重写提示再测同24直到变好。确有新工程错误可以独立修复版本，但不能将科学失败改名为工程故障。

六、为什么我的后备选S诊断，而不是马上训练B或D

C：无新监督和训练，主要增加粗览调用；能直接检查上下文是否帮助，故优先。

S：我选作后备，因为它提供不同于教师时间监督的信息。先固定全部时间选择，在非测试来源分别检查横／竖目标比例、主体连续性、镜头边界、锚点插值和尺度限制。只有观察到具体机制，才设计一个改变中心／尺度或插值的候选；不同时改三项。

若有可信构图参考，可比较“实际框”和“最佳中心但固定尺度”的上界；若没有，不能把主体检测框当构图真值，也不能宣称缩框必涨。空间实现本体部分未附，我目前没有证据断言它跨镜头插错或尺度就是主瓶颈。纯S变化会使相关空间缓存失效，不能沿用旧框后宣称空间算法已更新。

B边界精修：仍保留，但触发条件必须是已有固定非测试案例显示同一事件的边界参考可靠，且边界确实有可改善余地。它无法找回B根本没提出的事件；新教师样本、独立adapter训练和第二次推理也不一定比C便宜。两个rank16 adapter的逻辑参数推算为8,797,794,544，须再按真实模块实计；这只是合规可行性，不是质量依据。

D二元网格：本轮暂不重开。14个弱空窗口确实增加了部分负监督，但79个受支持窗口不自动意味着所有时间格都有可信正负。UNKNOWN及未证明覆盖的正区间补集仍不能变负。再同时改头、损失、监督和解码，只会增加归因成本。旧Pro第一轮偏好网格头的前提，尚未被“现在训练确实跑了15步”补齐。

E空输出／采样／后处理：不盲扫。若C-null已有独立机制依据，可以另行登记模板候选，但不能在本轮看到结果后临时扩出一排阈值包。

七、成本、停止和完整交付

24来源各一固定窗口，三臂局部各24次，加24次粗览，最多96次模型调用；能合法复用的控制调用另列。8来源小试最多32次。次数不是GPU时间，必须测实际token、长源顺解和装载开销。

特别注意L2944–2955：当前每窗从源头顺序解码。不能用“只输入64帧”估算CPU耗时；长源后段窗口可能已顺解大量帧。

若生产每源粗览一次，C为426粗览＋521局部＝947次，相对原521次增加约81.8%的调用数，不能直接写成耗时增加81.8%。原时间生产5430秒约1.51小时，只是对照成本；原空间18723.876秒约5.20小时。C符合完整身份复用条件才有空间新增调用0，历史成本仍保留。

我建议的管理止损是：只允许这一套三臂提示、8→24一次扩展；小试后按实际源长/token分层预测剩余时间。若无法在预留完整生产与验收时间后完成，不启动全量。完成24仍无增量依据就停，不自动扩104、512条标注或增加训练轮数。这是投入决策，不是统计定律；不新增固定显存／磁盘配额。

通过裁决后，先冻结唯一C的代码、提示、权重、输入与失败规则，再跑NONTEST8完整链，之后才执行426源／521局部窗及新增粗览。粗览失败也必须计入完整性验收。

最终仍需NONTEST8与426各11项独立strict、全身份和窗口齐全、ZIP大小／SHA／CRC、唯一predictions.jsonl及原字节一致、所有新增阶段账本与终态闭环。账本保留7200历史offset，不抢占外部任务，不改连接服务。旧37.63包绝不覆盖，不自动官网上传。

最后收口：这轮应购买“一个新机制是否值得生产”的证据，而不是再购买同一批弱标签的更多拟合。先用三臂把C的真实上下文增量和提示效应拆开；C不成立就转有事实依据的空间诊断。没有证据时允许今晚不产新包，但不能再把15次真实更新、一次strict通过或教师更一致包装成提分。


# 原文附件 r00-sol.md

# GPT5.6 Sol High — r00 原始可见完整回答

来源：https://chatgpt.com/c/6ac7c498-c174-83ea-9b7f-9fc388b4b18b
读取UTC：2026-10-08T16:36:01.575Z
附件：context-r00(1).md 与原文件同字节

读取与任务确认

连续任务 AIC-VIDEO-REMATCH-NEXT-20261005，接续版本 20261009-r00。上传文件显示为 context-r00(1).md，与用户说明的 context-r00.md 为同一文件。本地实测 233,190 字节，SHA256 = efff65e7e31b50c964fec3bc0562a22c31a295b5971da5f0c443bc694539d947，已从首行读到末尾代码块；本地有 3540 个换行符，Files 解析为 3541 行，这是末行换行计数口径差异，不是少读一行。

当前边界我按卷宗冻结：37.60 只是用户“37.63−0.03”的推算，不是我独立官网核验；37.63 旧 B 继续保护；32B 已真实完成推理；8B 新路线真实做了 15 次 optimizer update / 195 个反向样本，但最终按预登记规则重新选回 epoch0 原 B；81 个 UNKNOWN 保持 UNKNOWN，绝不转负；参赛推理仍受 9B 上限；8B/32B 均已在 Linux 原地；不读 100confirm、不看复赛视频/个别预测调参；Pro 三次额度已经用完。 
context-r00

这里有一个对旧 Pro 结论很重要的新证据：这次不是“微调尚未真正试过”。训练、梯度、冻结、adapter 重载都已经通过，epoch1 与 B 完全同分，epoch2/3 更差，最后明确选择 epoch0，trained_candidate_selected=false。所以我否决继续围绕同 65 个弱训练样本、同 CE 目标延长训练，也不同意再靠换学习率/多几轮碰运气。 
context-r00

我的裁决

优先主案：C，但不是简单版 C，而是「C-advisory + matched negative control」。

也就是：仍然用同一个 8B，对完整源视频做一次 64 帧粗览，生成的是描述性“可见事件表”，而不是“哪些一定是高光”的伪真值；随后 所有原来的 30 秒局部窗口仍然全部运行 B，粗览结果只能作为附加上下文，绝不能因为全局粗览没发现事件就跳过某个局部窗口。

这一点我和主控原始 C 有实质区别。原 C 最大风险是全局 64 帧漏掉短事件后形成候选召回上限；我建议彻底取消这个上限，让全局信息只帮助局部模型理解“整段视频在干什么”，不能剥夺 B 原本观察局部窗口的机会。

**唯一后备：B 边界精修。**但今晚不直接训第二个 adapter。必须先证明 32B 对“事件是什么时候开始/结束”这一窄任务有稳定性；只有这个门过了才训练。它不负责拒绝整窗、不负责发现 B 漏掉的事件，候选外仍然 UNKNOWN。

D 本轮不启动训练。S 本轮只做诊断，不列为后备生产路线。

卷宗当前四条路线的状态本身也支持这种资源排序：C 不需要下载、不需要训练；B 要增加教师边界证据和小 adapter；D 仍面对 coverage/弱负格与极小独立来源问题；S 缺可信 ROI 真值，而且一旦真正改变空间模型，不能再复用现有 31,295 个锚点的空间推理，历史这部分实际成本约 18,723.9 秒。 
context-r00

路线	我给的优先级	新信息量	主要成本/风险
C-advisory	1，立即 matched 验证	高：新增“全局语境”而不是重复教师 CE	无训练；增加每源一次粗览；风险是幻觉/文本诱导
B 边界精修	2，唯一后备	中高：只学习一个更窄、更可验证的机制	32B 边界调用＋小 LoRA；但无法恢复漏召回
D 网格头	暂缓	中，但仍使用同一批弱监督	65 train / 14 dev 的来源规模太小，格子数不能冒充独立样本数
S 空间	只诊断	潜在很高	缺 ROI 真值；若改空间模型，全量空间成本很高，归因也更难
今晚 Linux 应该做的 matched 对照

我建议不要再挑“漂亮的 24 条”。先跑现有 NONTEST8 做工程/机制探针；它通过后，科学比较直接上开放的完整 104 视频 / 96 来源，不按 C 的结果重选数据。卷宗已有 production-aligned 开发入口，104/96 的来源范围和同一生成函数思路已经存在，因此不必另造一套开发体系。 
context-r00

冻结三个臂：

**B0：**当前 37.63 对应 B 的局部推理机制，不给全局事件表。

**C-real：**本视频自己的 64 帧全源粗览 → 固定 schema 事件表 → 所有局部窗口继续逐个运行。

C-shuffle：局部视频完全不变，但给它另一条确定性配对、相近时长来源的事件表。粗览表本身已经生成，所以 shuffle 不新增全局模型调用。

C-shuffle 是我认为这轮最重要的反事实控制。它回答的不是“weak F1 高不高”，而是：

C-real 的效果究竟来自该视频真正的全局信息，还是模型单纯因为前面多了一段很像事件摘要的文本就改变输出？

如果 C-real 和 C-shuffle 差不多，我会直接判 C 的机制证据失败。即使某个 weak F1 恰好涨，也不值得跑 426。

事件表也应保持简单：只输出事件短描述＋64 帧粗览里的边界/位置 ID，程序负责映射真实 PTS；不要再让模型抄长浮点时间。不要让粗览回答“这个一定值得进入最终高光”，只回答“看到了什么、粗略在哪”。之前教师链已经证明，让模型同时承担视觉判断、时间数值抄写和复杂审查只会增加无意义故障。当前 V14 的边界 ID/程序映射思路已经走通，不应倒退。 
context-r00

必须记录的字段

这轮不只记 F1。至少保留：每源粗览输入帧 ID/PTS、事件数、事件表 token 数；三个臂每窗口的原始输出、合法空、segment 数、selected-duration fraction、首尾边界、解析/推理失败；B→C 增加和删除的帧数/时长；C-real 与 C-shuffle 相对 B 的帧集合 Jaccard；粗览事件在源时间上的位置与 B 无全局上下文独立局部选择的重叠关系；以及 104 上已有弱参考的 video-macro P/R/F1、短事件/窗口边缘分层结果。

这里 weak F1 只是 smoke test，不是真值。同教师的一致性、旧弱标签一致性都不能升级为人工 ground truth，卷宗本身已经明确这一点。 
context-r00

C 的科学 Go / No-Go 门

工程门先于质量门：输入 SHA/clock/native PTS/64 帧采样必须冻结；三个臂共享同一局部视频输入；不能截断；不得人工修改事件表；解析失败和合法空严格区分；不能出现未记录跳样本。任何正式候选最后仍必须走 NONTEST8 和 426 各 11 项 strict、521 时间窗、426 身份、ZIP/SHA/CRC/唯一 predictions.jsonl 全验收。 
context-r00

科学门我建议这样定：

**Go：**C-real 明显表现出“视频特异性”。最直接要求是，在 104 来源配对比较中，正确事件表相比 shuffle 事件表，与独立 B 局部视觉判断的兼容性更强，而且 C-real 没有全空、全选、事件数爆炸等坍塌；现有弱开发指标可以持平、改善或 CI 跨零，只要没有广泛退化。

No-Go：C-real≈C-shuffle；或者正确上下文反而比错误上下文更容易把局部 B 带偏；或者发生系统性长段化/全选/全空；或者沿用代码中现有的广泛退化门——大多数来源都退化且 macro F1 出现明显整体下降。弱 F1 不是 Go 的充分条件，但严重退化可以作为止损证据。

尤其不要再要求“CI 下界必须 >0 才允许继续”；卷宗已经明确禁止把弱 CI 当工程硬门。 
context-r00

B 后备怎么验证，先别训练

如果 C 被上述机制门否掉，我才转 B。

固定当前 B 提出的非测试候选事件，让 32B 只回答“同一可见事件的物理开始/结束在哪里”。对同一事件做两个匹配输入：原上下文和轻微平移后的局部上下文；模型输出都采用离散边界 ID，程序映射 PTS。

一个合格的边界教师应该在上下文轻微移动后仍然识别同一个事件，且映射回源 PTS 后的端点漂移只在采样分辨率附近，而不是整个事件换掉。这个稳定性验证不证明 32B 是真值，但可以证明它有没有资格承担“边界精修教师”这个更窄的任务。

通过后才考虑在原 B 候选能力外增加一个小边界 adapter；候选外 UNKNOWN 永远不负。推理仍是 B 提候选→边界 adapter 精修，因此它的最大缺点也非常明确：

B 的召回上限就是原 B 的候选召回。它可以修得更准，但永远救不回 B 根本没提出的高光。

所以 B 是后备而不是主案。卷宗原 B 路线自己也承认这一风险。 
context-r00

为什么现在不推 D

旧 Pro 第一次把二元网格头作为优先主案，当时最大阻塞是可靠负格不足。现在情况确实变化了：完整 160 次标注/复查已经完成，有 79 条弱支持，而不是工程没跑通。

但这个变化不足以让我重新把 D 提到主线。

因为真正进入学生的还是 65 train + 14 dev，其中 81 UNKNOWN 被正确排除。把 65 个来源窗口切成几百上千网格，不会创造几百上千个独立视频证据；它只会把同一教师判断复制成高相关格标签。更危险的是，局部老师错一次边界，就可以同时制造多个假正/假负格。V14 已经证明“继续拟合这批教师监督”没有胜过原 B；D 只是换了归纳偏置，尚没有新数据依据。 
context-r00

D 以后如果要复活，先做纯 CPU 网格表示上界、coverage/mask 和来源级有效样本数报告；今晚不花 GPU 训练它。

S 只做一个便宜诊断

空间端不能因为 V14 只掉 0.03 就推断“空间没问题”，也不能因为空间可能重要就立刻重跑 31,295 anchors。

今晚只检查已有可信非测试构图参考里：

固定最大尺度、中心完全正确时的 IoU 上界；允许尺度变化后的上界；当前中心误差；以及 anchor 插值误差。

如果中心正确但固定最大 crop 本身已经形成明显系统性上界，S 才值得以后进入正式路线。如果两种 oracle 上界几乎一样，就停止 S；加密锚点、空间 LoRA、比例感知 crop 暂时都没有机制依据。

如果当前没有足够可信 ROI 参考，则结论只能写 UNKNOWN，不能拿“8B框和另一版框很像”代替真实空间真值。

成本和生产账怎么记

C 的成本优势很明确：没有新训练、没有新模型下载。科学对照增加全源 overview 调用和 C-real/C-shuffle 局部推理。真正冻结后跑复赛，C 需要 426 次全源 overview + 原 521 个局部时间窗；overview 的真实成本先由 NONTEST8/104 实测再外推，不预写速度。

只要空间算法、源、clock、锚点请求和模型全部与已有 time-independent source field 一致，就继续复用现有空间场，新空间模型调用记 0，但必须同时引用原空间成本约 18,723.876 秒，不能写成“空间成本为零”。V14 正是这么记账的；训练、NONTEST 时间和 426 时间也分别有独立 charged seconds。 
context-r00

每个新作业继续单独记：GPU charged seconds、model-call 数、输入/输出 token、wall time、峰值显存、exit code/stop reason、父子 PGID、配置/代码/model/prompt SHA，以及是否复用缓存。CPU 预处理、缓存引用、启动计划都不能算新模型生成。

完整停止条件

我给主控的路线是：

先 C-advisory 的 NONTEST8 → 全 104 matched B/C-real/C-shuffle。机制不成立就当晚停 C，不换第二个 C prompt。机制成立且没有广泛退化，就冻结这一版，跑完整 NONTEST8 strict → 426 → ZIP。

这个完整包如果用户之后拿到的官方成绩 >37.63，保留为新最高包；如果 ≤37.63，这个 C 版本立即结束，不根据 37.xx 的数值去生成“更激进一点/更保守一点”的覆盖率、event 数量、阈值或逐视频规则。

然后只给后备 B 一次机会：边界稳定性门通过才训练；门不过就停止 32B→学生微调链。不顺势把 D 拉起来凑第三轮训练。

官方总分只能做已经冻结的整包排序和资源止损，不能成为隐藏测试标签的代理。这一条与卷宗边界保持一致。 
context-r00

最强反例

即使我这版 C-advisory 通过所有上述门，它仍有一个无法完全排除的失败模式：

长视频的 64 帧粗览天然偏向持续时间长、视觉显眼的大事件，而官方真正奖励的可能包含极短的动作转折。C-real 可能确实比 C-shuffle 更“懂这个视频”，在现有弱开发上也不差，但它提供的真实全局语境仍可能让局部 B 更相信“大事件主线”，反而抑制原 B 对短暂局部高光的选择。换句话说，“全局信息是真实的”不等于“它对官方高光目标有利”。

因此我特意要求 C 绝不能用 overview 跳过局部窗口，并且必须记录 B→C 被删除的短 segment、窗口边缘 segment 和 selected-duration 变化。这个反例仍不能被弱教师彻底消灭，最终只能由一个冻结、完整、合规的官方整包结果裁决。

最终优先顺序：C-advisory matched 对照 → 合格则完整包；失败则 B 边界精修；D 不训；S 仅做空间上界诊断。继续同 65 样本 CE 延长训练直接否决。


# 原文附件 r00-grok.md

# Grok Expert — r00 原始可见回答

来源：https://grok.com/c/874d3d1a-fd50-4c12-b4da-ca0ee8f65514?rid=8fe43c15-fd92-4edd-a794-ff1d3a2ef4b3
读取UTC：2026-10-08T16:33:37.205Z
附件：context-r00.md，233190 bytes，SHA256 efff65e7e31b50c964fec3bc0562a22c31a295b5971da5f0c443bc694539d947

工作了 56s

连续任务 ID：AIC-VIDEO-REMATCH-NEXT-20261005。接续版本：20261009-r00。附件 /workspace/attachments/context-r00.md 已完整读到文件尾：233190 字节、3540 行，SHA256 efff65e7e31b50c964fec3bc0562a22c31a295b5971da5f0c443bc694539d947，与声明一致。可读范围是该卷宗正文：三次 Pro 可见会话、V14 验收 JSON、V14 协议、production_t.py（finish() 在卷宗内被截断约 16747 字符，此后封装细节我没有独立读到）、train_student.py 全文。没有读 100confirm、没有复赛视频、没有逐帧预测、没有教师 raw。Pro 三次已尽，本轮不是新的 Pro 认可。

必须原样保留的事实：37.63 只绑定旧 B ZIP 86bd5301…ebe54；用户回报的 −0.03 只绑定 V14 ZIP 95173d93…f3a2（308278 字节），据此推算 37.60，不是我独立官网核验。B2 37.32 绑定 0f8c95f0…83a3。8B 确已续训 15 次更新、195 次反传、3 epoch；弱 14 dev 视频宏时间 F1 为 epoch0/1 = 0.3786251362162477、epoch2 = 0.3596785770535768、epoch3 = 0.36453995670744305；预登记同分取更早，选中 epoch0 原 B，trained_candidate_selected=false。65 正（55/10）、14 空（10/4）、81 UNKNOWN 保留全 160 分母且不当负。逻辑参数 8782459120，共享基座只计一次，低于 9B。8B/32B 在 Linux 原地。禁止测试内容调参、禁止手看复赛预测调参、禁止把弱教师一致性当官网分或人工真值。

事实 / 推断 / 未知

事实：V14 工程验收通过，不能解释线上 −0.03。V14 用的是原 B adapter，但生产合同不是旧 B：提示为 NEXT_ROUND_0_TO_5、允许合法空、时间按 native PTS、空间复用 B2 的时间无关全源场，新空间调用为 0。权重相同不能推定包相同。

推断：−0.03 是整包混杂，至少同时改变了提示/空输出合同和空间场来源。它不能归因于“新训练失败”，因为新权重根本没被选中；也不能归因于“允许空一定有害”或“B2 空间场一定更差”。B2 自身 −0.31 同样混杂，不能当空间因果。

未知：官网分差来自空视频、边界偏移、框尺度还是插值。14 条同教师 dev 不能分解这 0.03。我没有看到旧 B 与 V14 的 NONTEST8 逐窗对照表。

优先主案：先做可归因的非测试分解，不先跑 C 全包

不同意主控把 C 放成今晚第一执行项。C 是未训练的新上下文通道；64 帧全源粗览比局部 30 秒更稀，事件文本训练时没见过，幻觉会把原 B 局部选择带偏。14 弱 dev 与教师同源，不能当 C 的优越真值。主控自己的反例成立，不应先付 426 的额外全源调用。

今晚 Linux 只做一条冻结的非测试 matched 对照，名字登记为 attr_s_c_nontest_v1，新目录、新锁，不改 V14/B/B2。

固定样本：已有开放 NONTEST8，外加与旧 160 来源组隔离、且未用于本轮提示修订的 16 个自然 30 秒窗。16 窗事前按源哈希排序取前 16，不许事后剔除。不读 100confirm，不看复赛。

三个同输入臂，空间场都锁定为已验收的 B2 时间无关场，只换时间合同：

臂	时间	回答的问题
B-contract	原 B adapter，历史强制 1..5 提示与语法	空合同本身的增量
V14-contract	原 B adapter，NEXT_ROUND_0_TO_5、允许空	已有 V14 非测试复现
C-contract	同 8B 无新训练；每源 64 帧粗览只出事件 ID 与粗边界 ID，程序映射 PTS；局部仍用原 B	粗览文本是否改变局部选择

可测字段只在这 24 个非测试窗上报，全分母：合法空数、解析失败数、推理失败数、预测秒数、与旧弱标签的时间交并（明确叫同教师一致性，不当真值）、短于 2 秒事件是否被 C 粗览漏掉、C 事件文本是否指向该窗未见的帧、框中心位移、固定最大裁剪下的几何 IoU 上界。几何上界用已有身份可信的非测试参考框：即使中心完美，IoU ≤ (w_g / w_max)^2。没有可信框的视频单列缺失，不许用检测框冒充构图真值。

工程门：NONTEST8 的 11 项 strict 必须全真；失败不转空；GPU 锁与 7200 历史 offset 只追加。科学 go：C 相对 B-contract 少漏掉至少一条非测试短事件，且没有新增“粗览事件在该窗无对应帧”的幻觉，才允许以后单列冻结 C 全包。no-go：粗览漏事件、幻觉改变局部选择、或三臂弱一致性差值区间跨零且无独立机制差。no-go 不自动改提示重跑。

完整包：今晚不产 426 ZIP。只有 go 之后，下一轮才用冻结臂生成 426，空间继续复用同一 B2 场，独立 strict、521 窗、426 身份、单 predictions.jsonl、CRC。费用按父子 PGID 的真实 GPU charge 记账，粗览与局部分开，不用 wall 冒充。停止：共享锁冲突、一次全源粗览实测后外推超过原 426 时间费用的 1.5 倍、或 NONTEST 幻觉率 ≥ 漏检改善，都停 C。

后备：空间尺度，而不是再训边界

后备是 S，不是 B，也不是 D。Pro 第二次已给出固定最大裁剪的几何反例，这项诊断仍未测量。若上述上界在可信非测试参考上中位已经 ≤ 0.64，继续改时间选择不能补回尺度损失；下一候选应是同一未微调 8B、目标比例约束下的中心加尺度，先推理、不训空间 LoRA。禁止统一乘 0.8、禁止删难例。

B 只在主案证明事件身份稳定、但边界系统性偏出参考区间时才独立开小 adapter。候选外 UNKNOWN 不标负；两个 LoRA 都计入参数账。今晚不训。

D 反对。79 条整窗弱支持不是帧格负监督；UNKNOWN 仍不能当负。证据相对 Pro 第一次没有变好，重启网格头会重复已正确停止的路线。

再训 65 条同配方也反对。15 次更新已发生，epoch2/3 弱 F1 更低，选模规则已保留原 B。

最强反例

对 C：粗览把短转折写成不存在，局部 B 跟随该文本，NONTEST 弱一致性上升或不变，426 整包仍低于 37.63。8 条非测试可以完全看不到这个失败。

对主案自己：NONTEST8 加 16 窗仍是同分布弱标签，几何上界只用稀疏参考框；两者都可能把真正的官网损失归因错。所以主案只决定下一包值不值得生成，不宣称会超过 37.63。旧 B ZIP 保持不动。


# 原文附件 main-r01-critique.md

# 主控第二轮修订与待裁决问题

连续任务AIC-VIDEO-REMATCH-NEXT-20261005，接续20261009-r01。主控已完整读取r00同一233190字节卷宗。Pro连续任务3/3已用完，本轮新Pro调用0；不能重置额度。Gemini真实附件发送两次均未留下回答（第一次网页1099，第二次索引+四卷短暂生成后回到草稿），不记为完整参与，不另换模型。本轮继续真实可用席位；最终由主控在额度耗尽条款下具名兜底，明确保留缺席限制。

## 事实性修正

r00由本地文件直接读取完整production_t.py、engine.py、train_student.py拼接，未插入truncated标记；Grok称finish段被截16747字符是其阅读工具的限制，不能写成本地卷宗缺少源码。本轮再次原样继承完整r00，请其读取缺段或明确阅读限制。其意见原文仍完整保留。

Tibo发现旧104开发入口aligned_dev调用encode_window(...clock=None...)触发CFR分支，属真实代码证据。新matched诊断必须顺序PyAV扫描全源nativePTS，统一V14实际processor/像素/局部floor64/端点duration，不直接使用旧入口，不回写旧104产物。旧最佳37.63的包可保护，但“本次nativeB-control”只是同权重局部控制，不能声称与旧37.63包逐字节相同。

本轮只读Linux实际input_contract元数据：104记录/96来源的label_status=WEAK_TEACHER，annotation_source=api_doubao_doubao-seed-2-1-pro-260628，原标示MODEL_UNSEEN_FIXED_WEAK_DIAGNOSTIC；不是本轮32B盲复查产生的14dev。来源交集仍应实际核完整集合，历史名称不保证新方案从未使用。元数据未读取或共享逐条弱标签内容；所有104参考指标仅称固定外部教师弱参考一致性，不能当人工真值。NONTEST8有8独立源及现成clock_registry，可用于真实输入/成本/封包工程验收。

## 主控接受的修订

1. 不延长65弱样本同CE训练，不强选较晚epoch。D缺少合法coverage负格，暂不训练；S先诊断参考身份和尺度上界，缺真值写UNKNOWN。32B已推理成功，8B已15更新；当前问题不再冒称模型没装好。
2. 先NONTEST8机制/工程验证，再完整开放104视频/96源matched，所有记录固定、不按结果换样本。若来源与既有训练重合，按实际交集标示“已观察开发”，不能假称新独立人工真值。
3. C-advisory：同8B粗览输出描述性事件表（非高光判决），所有原自然30秒窗继续原B局部视觉推理。全局表不能删窗口、否决未覆盖事件或作硬召回mask。每次原回答先不可覆盖落盘再校验，无效不转空。
4. 冻结五臂分离合同混杂：B1(历史1..5语义提示/语法、当前native输入)，B0(V14 0..5无事件表)、C-null(B0采用同一C模板但事件表为空)、C-real(B0采用该模板加真实本源描述性事件表)、C-shuffle(B0加确定性别源错配事件表)。C-null/C-real/C-shuffle的局部原像素、clock、greedy、validator、参数相同；唯一新上下文明确登记，B1/B0差异独立归因。空间同已验收B2全源场，当前0新空间调用且原成本保留。
5. 全源64稀疏观测可能遗漏短事件，全部局部窗仍计算并明确记录B→C增加/删除的短段、边缘段、选中时长。错配表不外传给官网，只有非测试诊断臂。字符/token限长必须事先登记，不能静默截断实际模型输入。

## 不接受或需要收紧的意见

Grok的“改善至少一条<2秒事件且无幻觉才Go”需要可信非测试参考和可独立观测依据；缺少时不能让同教师宣称满足。其弱CI跨0即STOP和1.5倍旧费用上限不是用户既有工程门，不采用为硬门。费用按真实小试外推、容量和共享冲突，不能发明固定机器额度。弱参考可以提供排序/止损，不能等于官网分。

Sol的“更兼容B局部选择”只能证明上下文是否产生视频特异性，B不是真值；若与B越像被定义为越好，会禁止真正改善并奖励不变输出。需要可实现数值定义且不能将“更像B”作为Go唯一条件。

