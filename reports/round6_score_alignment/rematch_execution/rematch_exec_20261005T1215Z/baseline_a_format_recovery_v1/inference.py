"""One constrained regeneration attempt, preserving the frozen A model/prompt.

Probe uses only approved non-test sources. Recover derives its denominator
from the complete preserved failed run and copies every successful window
unchanged. No post-hoc clipping, deleting, empty fallback or semantic input.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RUN = HERE.parent
CODE = RUN/'baseline_a_pts_v1'
CTRL = RUN/'controller'
sys.path[:0] = [str(CODE),str(CODE/'vendor'),str(HERE)]
from a_contract import sha, write_json, write_rows, read_rows
from pts_contract import load_clocks, BRANCH_CFR, native_clip_plan, parse_native_segments
from run_pts import verify_vendor, verify_models, verify_admission
from native_frames import build_native_clip
from exact_pts import exact_native_pts, verify_native_encoding
from constrained_json import BoundedSegmentsGrammar, make_prefix_constraint, ascii_token_candidates

LOCK = '86fc0da7cf631a2afe33c54fb5b66246bba88adfd95c1d8ce80ccbf73522d70d'
OLD_TEMPORAL_SHA = '2790809c4defd2988dba5a44ed659b436ab78efe942b6f2f1d0f118ab92071c9'
VARIANT = 'A_FORMAT_CONSTRAINED_RECOVERY_V1'

def require(ok,message):
    if not ok:
        raise RuntimeError(message)

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['probe','recover'],required=True)
    ap.add_argument('--admission',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args = ap.parse_args()
    a = json.loads(args.admission.read_text())
    require(not args.output.exists() and args.output.resolve().parent == HERE.resolve(),
        'new exclusive output inside this recovery version required')
    require(a['recovery_variant'] == VARIANT and a['recovery_source_hashes']['inference.py'] == sha(__file__)
        and a['recovery_source_hashes']['constrained_json.py'] == sha(HERE/'constrained_json.py')
        and sha(CODE/'source_lock.json') == LOCK,'recovery or base production source identity changed')
    manifest_path,registry_path = Path(a['manifest_path']),Path(a['clock_registry_path'])
    require(sha(manifest_path) == a['manifest_sha256'],'input manifest changed')
    manifest = json.loads(manifest_path.read_text())
    clocks = load_clocks(manifest,registry_path,a['clock_registry_sha256'])
    verify_admission(args.admission,a['manifest_sha256'],manifest['kind'],args.output,
        a['clock_registry_sha256'],'temporal')
    verify_vendor()
    config_path = CODE/'config_a.json'
    config = json.loads(config_path.read_text())
    require(sha(config_path) == '137a60e3efae567794105bac8d2fcb4288c7d1b289ab4ad1d0a81e2ba11c5414',
        'frozen A config changed')
    verify_models(config)
    spec = importlib.util.spec_from_file_location('tc_frozen_format_recovery',CODE/'vendor/temporal_common.py')
    tc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tc)
    metadata = {r['video_id']:r for r in manifest['records']}
    tasks,old_rows = [],None
    if args.mode == 'probe':
        original_n8 = CODE/'nontest_e2e_02/temporal.jsonl'
        previous = read_rows(original_n8)
        require(len(previous) == 8 and manifest['kind'] == 'NONTEST_FROZEN8','fixed probe denominator changed')
        for row in previous:
            for w in row['windows']:
                tasks.append(dict(video_id=row['video_id'],start=w['start_sec'],end=w['end_sec'],
                    index=w['index'],case='frozen8_'+row['video_id']))
        # Additional scopes are fixed on the first already-authorized non-test
        # source, independent of labels, images and rematch failure values.
        vid = previous[0]['video_id']
        tasks += [dict(video_id=vid,start=0.0,end=end,index=0,case='non_test_geometry_'+str(end))
            for end in (13.0,30.0)]
    else:
        original = CODE/'rematch_e2e_01/temporal.jsonl'
        require(sha(original) == OLD_TEMPORAL_SHA,'complete preserved temporal output changed')
        old_rows = read_rows(original)
        old_report = json.loads((CODE/'rematch_e2e_01/temporal.jsonl.run.json').read_text())
        require(len(old_rows) == 426 and old_report['videos'] == 426 and old_report['windows'] == 521
            and old_report['invalid_windows'] == 5,'original full run denominator changed')
        for row in old_rows:
            for w in row['windows']:
                if not w['output_valid']:
                    require(w['status'] == 'PARSE_FAILURE' and clocks[row['video_id']]['branch'] == BRANCH_CFR,
                        'this version admits only preserved parse-contract failures')
                    tasks.append(dict(video_id=row['video_id'],start=w['start_sec'],end=w['end_sec'],
                        index=w['index'],case='parse_failure_'+row['video_id'],old_window_sha256=canonical_sha(w)))
        require(len(tasks) == 5,'failed-window denominator changed')
        probe_path = Path(a['format_probe_evidence_path'])
        probe = json.loads(probe_path.read_text())
        require(sha(probe_path) == a['format_probe_evidence_sha256']
            and probe['status'] == 'PASS_REAL_NONTEST_FORMAT_CONSTRAINT_ONLY'
            and probe['cases'] == 10 and probe['failures'] == 0
            and probe['source_hashes'] == a['recovery_source_hashes'],
            'same-version actual non-test generation probe missing')
    args.output.mkdir()
    write_json(args.output/'registered_tasks.json',dict(mode=args.mode,tasks=tasks,
        labels_used=False,original_output_modified=False,posthoc_segment_rewrite=False))
    # Retain the proven torch-before-decord initialization order.
    import torch
    torch.cuda.init()
    diagnostic_tensor = torch.empty((1,),device='cuda',dtype=torch.bfloat16)
    del diagnostic_tensor
    import decord
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    from peft import PeftModel
    started = time.monotonic()
    base = Qwen3VLForConditionalGeneration.from_pretrained(config['base_model'],torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    model = PeftModel.from_pretrained(base,config['adapter'],is_trainable=False).eval()
    processor = AutoProcessor.from_pretrained(config['base_model'],min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    tokenizer = processor.tokenizer
    eos_ids = model.generation_config.eos_token_id
    if isinstance(eos_ids,int):
        eos_ids = [eos_ids]
    require(isinstance(eos_ids,list) and eos_ids and all(type(i) is int for i in eos_ids),
        'actual model generation EOS identity unavailable')
    candidate_started = time.monotonic()
    candidates = ascii_token_candidates(tokenizer)
    coverage = []
    # Text-only fixtures check the real tokenizer's grammar path before media
    # inference. They contain no labels, source pixels or rematch predictions.
    for fixture in ('{"segments":[[0,1]]}',
        '{"segments":[[0.0001,0.9999],[1,2],[3,4],[5,6],[7,8]]}'):
        ids = tokenizer.encode(fixture,add_special_tokens=False)
        fixture_constraint = make_prefix_constraint(tokenizer,0,30.0,
            candidate_token_ids=candidates,eos_token_ids=eos_ids)
        for index,token in enumerate(ids):
            require(token in fixture_constraint(0,ids[:index]),'actual tokenizer cannot follow canonical JSON fixture')
        require(set(fixture_constraint(0,ids)) == set(eos_ids),'actual tokenizer EOS coverage mismatch')
        fixture_constraint.assert_complete(ids+[eos_ids[0]])
        coverage.append(dict(tokens=len(ids),complete=True))
    tokenizer_receipt = dict(eos_token_ids=eos_ids,candidate_tokens=len(candidates),
        fixture_coverage=coverage,seconds=time.monotonic()-candidate_started)
    write_json(args.output/'tokenizer_receipt.json',tokenizer_receipt)
    prompt = processor.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt = prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    results,failures = [],0
    for task in tasks:
        row,clock = metadata[task['video_id']],clocks[task['video_id']]
        start,end = task['start'],task['end']
        duration = end-start
        require(sha(row['source_path']) == row['source_sha256'],'source bytes changed')
        one = time.monotonic()
        record = dict(task=task,status='INFERENCE_FAILURE',output_valid=False,parse_errors=[],raw_output='')
        try:
            if clock['branch'] == BRANCH_CFR:
                array,md,info = tc.build_virtual_clip(row['source_path'],start,end)
                encoded = processor(text=[prompt],videos=[torch.from_numpy(array).permute(0,3,1,2)],
                    video_metadata=[md],padding=True,do_sample_frames=False,return_tensors='pt')
            else:
                plan = native_clip_plan(clock,start,end)
                array,md = build_native_clip(row['source_path'],row,clock,plan)
                with exact_native_pts(processor,plan,row['fps_num']/row['fps_den']) as identity:
                    encoded = processor(text=[prompt],videos=[torch.from_numpy(array).permute(0,3,1,2)],
                        video_metadata=[md],padding=True,do_sample_frames=False,return_tensors='pt')
                    verify_native_encoding(processor,encoded,identity)
                info = dict(n_sampled=plan['n_sampled'])
            prompt_length = encoded['input_ids'].shape[1]
            constraint = make_prefix_constraint(tokenizer,prompt_length,duration,
                candidate_token_ids=candidates,eos_token_ids=eos_ids)
            inputs = encoded.to('cuda')
            torch.cuda.reset_peak_memory_stats()
            with torch.inference_mode():
                generated = model.generate(**inputs,do_sample=False,max_new_tokens=256,
                    prefix_allowed_tokens_fn=constraint)
            torch.cuda.synchronize()
            suffix = generated[0][prompt_length:]
            constraint.assert_complete(suffix)
            raw = processor.tokenizer.decode(suffix,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            require(BoundedSegmentsGrammar(duration).complete(raw),'constrained generation truncated/incomplete')
            parsed,errors,warnings = tc.parse_segments(raw,duration)
            require(parsed is not None and not errors and not warnings,'frozen parser rejects constrained model output')
            require(all(0 <= x < y <= duration for x,y in parsed),'parsed range changed or illegal')
            record.update(status='MODEL_OK',output_valid=True,raw_output=raw,parsed_segments=parsed,
                parse_errors=[],parse_warnings=[],sampled_frames=info['n_sampled'],
                peak_memory_mib=round(torch.cuda.max_memory_allocated()/2**20,2),
                generated_tokens=int(suffix.numel()),constraint_calls=constraint.stats['calls'],
                constraint_stats=constraint.stats)
        except Exception as exc:
            record.update(parse_errors=[type(exc).__name__+': '+str(exc)])
        record['seconds'] = time.monotonic()-one
        failures += int(not record['output_valid'])
        results.append(record)
        write_json(args.output/(task['case']+'.json'),record)
        print(json.dumps(dict(case=task['case'],status=record['status'],errors=record['parse_errors'],
            seconds=record['seconds'])),flush=True)
    report = dict(variant=VARIANT,mode=args.mode,cases=len(tasks),failures=failures,
        status=('PASS_REAL_NONTEST_FORMAT_CONSTRAINT_ONLY' if args.mode == 'probe' else 'PASS_FIVE_PARSE_FAILURE_REGENERATIONS')
            if failures == 0 else 'STOP_FORMAT_RECOVERY_FAILURE',
        wall_seconds=time.monotonic()-started,source_hashes=a['recovery_source_hashes'],
        base_production_source_lock_sha256=LOCK,manifest_sha256=a['manifest_sha256'],
        prompt_sha256=hashlib.sha256(tc.PROMPT.encode()).hexdigest(),frozen_config_sha256=sha(config_path),
        adapter_sha256=config['adapter_sha256'],tokenizer_receipt_sha256=sha(args.output/'tokenizer_receipt.json'),
        posthoc_segment_rewrite=False,
        original_successful_window_reruns=0,labels_used=False,official_quality_claim=False,uploaded=False)
    if args.mode == 'recover' and failures == 0:
        updated = copy.deepcopy(old_rows)
        replacements = {(r['task']['video_id'],r['task']['index']):r for r in results}
        unchanged = 0
        for old,new in zip(old_rows,updated):
            for old_w,new_w in zip(old['windows'],new['windows']):
                key = (old['video_id'],old_w['index'])
                if key not in replacements:
                    require(canonical_sha(old_w) == canonical_sha(new_w),'successful window changed')
                    unchanged += 1
                    continue
                rec = replacements[key]
                require(canonical_sha(old_w) == rec['task']['old_window_sha256'],'failed input changed')
                for field in ('status','output_valid','raw_output','parsed_segments','parse_errors','parse_warnings',
                    'sampled_frames','peak_memory_mib','seconds'):
                    new_w[field] = rec[field]
                new_w['format_recovery'] = dict(variant=VARIANT,original_window_sha256=canonical_sha(old_w),
                    attempt=1,source_hashes=a['recovery_source_hashes'],constraint_calls=rec['constraint_calls'])
        require(unchanged == 516 and sum(len(r['windows']) for r in updated) == 521,
            'unmodified successful denominator changed')
        write_rows(args.output/'temporal.jsonl',updated)
        report.update(original_temporal_sha256=OLD_TEMPORAL_SHA,successful_windows_unchanged=516,
            recovered_windows=5,total_videos=426,total_windows=521,remaining_invalid_windows=0,
            output_sha256=sha(args.output/'temporal.jsonl'))
    write_json(args.output/'report.json',report)
    print(json.dumps(report),flush=True)
    raise SystemExit(0 if failures == 0 else 5)
