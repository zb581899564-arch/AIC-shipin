        require(record.get('n_frames') == item['n_frames'] and record.get('video_path') == item['source_path'] and
                record.get('targetRatioWH') == item['targetRatioWH'] and math.isfinite(record.get('fps', float('nan'))) and
                abs(record['fps'] - fps) <= max(1e-6, fps * 1e-6), 'T source identity mismatch')
        expected = frames.window_schedule(item, manifest['kind'], clock)
        require(len(record.get('windows', [])) == len(expected), 'T natural window count differs')
        points = [float(p) for p in clock['pts']]
        chosen = set()
        for window, (start, end) in zip(record['windows'], expected):
            require(window.get('output_valid') is True and not window.get('parse_errors') and
                    window.get('clock_record_sha256') == clock['clock_record_sha256'] and
                    abs(window.get('start_sec', -1) - start) <= 1e-6 and
                    abs(window.get('end_sec', -1) - end) <= 1e-6, 'T failed or wrong-clock window blocks candidate')
            segments = window.get('parsed_segments')
            validate_segments(segments, end - start)
            require(window.get('status') == ('MODEL_OK' if segments else 'LEGAL_EMPTY'), 'T empty/failure status mismatch')
            from native_segment_contract import native_segment_ranges
            for first, stop in native_segment_ranges(segments, points, start, end-start):
                chosen.update(range(first, stop))
        for ordinal in sorted(chosen):
            result.append(dict(video_id=video_id, source_frame=ordinal, source_path=item['source_path'],
                source_width=item['width'], source_height=item['height'], source_n_frames=item['n_frames'],
                fps=fps, target_ratio_wh=item['targetRatioWH']))
    return result


def temporal(scope, out):
    verify()
    student, old, frames, _ = helpers()
    from sft_contract import verify_live_gpu_reservation
    from engine import load_model
    from constrained_json import ascii_token_candidates
    verify_live_gpu_reservation()
    completion = read(HERE / 'student_01/student_completion.json')
    require(completion['status'] == 'PASS_TRAINED_SELECTED_STUDENT_ADAPTER', 'selected student not ready')
    require(sha(Path(completion['selected_adapter_dir']) / 'adapter_model.safetensors') ==
            completion['selected_adapter_sha256'], 'selected T adapter changed')
    require(sha(Path(completion['selected_adapter_dir']) / 'adapter_config.json') ==
            completion['selected_adapter_config_sha256'], 'selected T adapter configuration changed')
    config = old.verify()
    config['b_adapter'] = completion['selected_adapter_dir']
    model, processor, count = load_model(config, adapter=True)
    candidates = ascii_token_candidates(processor.tokenizer)
    _, manifest, clocks = old.inputs(scope)
    out = Path(out); out.mkdir(exist_ok=False)
    failed = window_count = 0
    started = time.monotonic()
    with (out / 'temporal.jsonl').open('x', encoding='utf-8') as stream:
        for n, item in enumerate(manifest['records'], 1):
            require(sha(item['source_path']) == item['source_sha256'], 'contest source bytes changed')
            clock = clocks[item['video_id']]
            arrays = clock['arrays']
            tick = Fraction(arrays['raw_time_base'])
            points = [float(value * tick) for value in arrays['native_pts_ticks']]
            exact_origin = arrays['raw_first_pts_ticks'] * tick
            origin = float(exact_origin)
            record = dict(video_id=item['video_id'], targetRatioWH=item['targetRatioWH'],
                          video_path=item['source_path'], n_frames=item['n_frames'],
                          fps=item['fps_num'] / item['fps_den'], arm='T_STRONG_TEACHER_SFT_ALLOW_EMPTY', windows=[])
            for j, (start, end) in enumerate(frames.window_schedule(item, manifest['kind'], clock)):
                one = time.monotonic(); window_count += 1
                raw_start, raw_end = raw_window_bounds(arrays, start, end)
                window = student.window_from_pts(item['source_path'], item['source_sha256'], points,
                                                raw_start, raw_end,
                                                item['video_id'] + ':T:' + str(j))
                window['window_duration_sec'] = end - start
                try:
                    encoded, details = student.production_encode(processor, window)
                    result = student.production_generate(model, processor, window, encoded, details, candidates)
                    del encoded
                except Exception as error:
                    result = dict(status='INFERENCE_FAILURE', output_valid=False, parsed_segments=None,
                                  parse_errors=[type(error).__name__ + ': ' + str(error)], parse_warnings=[])
                result.update(start_sec=start, end_sec=end, index=j, seconds=time.monotonic() - one,
                              clock_record_sha256=clock['clock_record_sha256'],
                              raw_source_pts_origin_sec=origin, clock_branch=clock['branch'])
                failed += not result['output_valid']; record['windows'].append(result)
            stream.write(json.dumps(record, ensure_ascii=False) + '\n'); stream.flush()
            write(out / 'progress.json', dict(stage='T_TEMPORAL', videos=n, total=len(manifest['records']),
                                             windows=window_count, failures=failed,
                                             wall_seconds=time.monotonic() - started))
    write(out / 'temporal.stage.json', dict(status='PASS_TEMPORAL_EXECUTION' if not failed else 'STOP_TEMPORAL_FAILURES',
          videos=len(manifest['records']), windows=window_count, invalid_windows=failed,
          output_sha256=sha(out / 'temporal.jsonl'), logical_parameters=count,
          allow_empty=True, input_contract=student.INPUT_CONTRACT,
          selected_adapter_sha256=completion['selected_adapter_sha256'],
          decoder='SAME_STUDENT_PRODUCTION_FUNCTION_AS_WEAK_DEV',
          wall_seconds=time.monotonic() - started), fresh=True)
    require(failed == 0, 'failed temporal generation blocks candidate; never convert failure to empty')


def scheduling(scope, out):
    verify()
    _, old, frames, source = helpers()
    out = Path(out)
    input_ref, manifest, clocks = old.inputs(scope)
    require(read(out / 'temporal.stage.json')['status'] == 'PASS_TEMPORAL_EXECUTION', 'temporal phase did not pass')
    selected = select_native_frames(manifest, rows(out / 'temporal.jsonl'), clocks)
    cache = RUN / 'b_score_aligned_package_v4' / (scope + '_01')
    freeze_path = HERE / 'cache_01' / (scope + '.json')
    usable = freeze_path.is_file()
    if selected and usable:
        freeze = read(freeze_path)
        evidence = b2_cache_evidence(scope, input_ref)
        require({key: value for key, value in freeze.items() if key != 'utc'} == evidence,
                'spatial cache freeze receipt or current input/base/completion binding differs')
        source_schedule = read(cache / 'schedule.stage.json')
        require(source_schedule['status'] == 'PASS_TIME_INDEPENDENT_SOURCE_FIELD' and
                source_schedule['temporal_selection_used_for_boundaries'] is False, 'space cache depends on Z time decisions')
        require(read(cache / 'spatial.stage.json')['logical_parameters'] == 8767123696 and
                read(cache / 'spatial.stage.json')['time_adapter_enabled'] is False, 'space cache model differs')
        for name, key in (('field_frames.jsonl', 'field_frames_sha256'),
                          ('field_shots.jsonl', 'shots_sha256'), ('anchor_requests.jsonl', 'requests_sha256')):
            require(sha(cache / name) == source_schedule[key], 'source field cache bytes changed')
        field = rows(cache / 'field_frames.jsonl')
        desired = source.field_frames(manifest, clocks)
        wanted = {(r['video_id'], r['source_frame']) for r in desired}
        require({(r['video_id'], r['source_frame']) for r in field} == wanted and
                len(field) == len(wanted) == source_schedule['field_frames'] and field == desired,
                'B2 cached native field differs from current source algorithm')
        outputs = rows(cache / 'anchor_output.jsonl'); requests = rows(cache / 'anchor_requests.jsonl')
        from field_contract import build_field_requests
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
