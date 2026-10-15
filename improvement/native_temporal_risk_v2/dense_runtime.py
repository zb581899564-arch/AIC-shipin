"""New dense128 input/attempt contract, with deferred original-B dependencies.

Importing this module is stdlib-only. It never launches a job, loads weights,
downloads media, reads reference labels, or rewrites a prior artifact.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import traceback
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
HERE = Path(__file__).resolve().parent
DEV = Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')
RECIPE = 'SOURCE_UNIFORM128_NATIVE_REALIZABLE_B0'
ARM = 'DENSE128_NATIVE_REALIZABLE_ORIGINAL_B'
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
ADAPTER_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
_DEPENDENCIES = None
_SOURCE_STATS = {}


def require(ok, why):
    if not ok:
        raise ValueError(why)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush(); os.fsync(stream.fileno())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def registration(scope):
    require(scope in ('pilot', 'rematch'), 'only registered pilot or rematch scope')
    path = HERE / ('registration.json' if scope == 'pilot' else 'production_registration.json')
    value = read(path)
    require(value['recipe'] == RECIPE and value['risks_accepted'] is True and
        value['max_pilot_calls'] == 6 and value['production_windows'] == 521 and
        value['production_records'] == 426 and value['optimizer_updates'] == 0,
        'prospective dense128 registration differs')
    require(value['rematch_admitted'] is (scope == 'rematch'), 'scope is not prospectively admitted')
    return path, value


def verify_lock(scope, additional=()):
    reg, value = registration(scope)
    path = HERE / ('source_lock.json' if scope == 'pilot' else 'production_source_lock.json')
    lock = read(path)
    required = [HERE / name for name in ('dense_runtime.py', 'dense_video.py', 'dense_pilot.py',
        'dense_replay.py', 'native_grammar.py', 'original_grammar.py')]
    if scope == 'rematch':
        required.append(HERE/'dense_production.py')
    required += [reg, RUN / 'b_score_aligned_package_v4/config.json',
        RUN / 'teacher_student_autopilot_v14/source_color.py',
        RUN / 'teacher_student_autopilot_v14/autopilot_common.py',
        RUN / 'teacher_student_autopilot_v14/config.json'] + list(additional)
    require(all(str(p) in lock['files'] for p in required), 'new source lock lacks required actual code/input bindings')
    for p, expected in lock['files'].items():
        require(sha(p) == expected, 'frozen dense128 input changed: ' + p)
    return dict(path=str(path), sha256=sha(path), registration_sha256=sha(reg), value=value)


def dependencies():
    global _DEPENDENCIES
    if _DEPENDENCIES is None:
        base = RUN / 'b_score_aligned_package_v4'
        sys.path[:0] = [str(HERE), str(base), str(RUN/'baseline_a_pts_v1'),
                       str(RUN/'baseline_a_pts_v1/vendor'), str(RUN/'temporal_sft8b_v1')]
        # engine.py imports public common; pin that owner explicitly.
        load(base / 'common.py', 'common')
        engine = load(base / 'engine.py', 'dense_original_b_engine')
        contracts = load(base / 'contracts.py', 'dense_original_b_contracts')
        exact = load(RUN / 'baseline_a_pts_v1/exact_pts.py', 'dense_original_exact_pts')
        frames = load(RUN / 'baseline_a_pts_v1/native_frames.py', 'dense_original_native_frames')
        v14 = RUN / 'teacher_student_autopilot_v14'
        owner = load(v14 / 'autopilot_common.py', 'autopilot_common')
        color = load(v14 / 'source_color.py', 'dense_registered_v14_source_color')
        require(color.HERE == v14 and owner.HERE == v14, 'registered source-color module owner differs')
        require(color.settings()['source_color_repair'] == read(base/'config.json')['source_color_repair'],
                'original temporal and source-field color configuration differ')
        _DEPENDENCIES = (engine, contracts, exact, frames, color)
    return _DEPENDENCIES


def color_identity():
    _, _, _, _, color = dependencies()
    v14 = RUN / 'teacher_student_autopilot_v14'
    return dict(module_path=str(v14/'source_color.py'), module_sha256=sha(v14/'source_color.py'),
        owner_path=str(v14/'autopilot_common.py'), owner_sha256=sha(v14/'autopilot_common.py'),
        configuration_path=str(v14/'config.json'), configuration_sha256=sha(v14/'config.json'),
        recipe=color.settings()['source_color_repair'], original_v14_temporal_recipe=True)


def processor_cpu():
    import torch
    from transformers import AutoProcessor
    require(not torch.cuda.is_initialized(), 'CPU preparation/replay must not initialize CUDA')
    dependencies()
    config = read(RUN/'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    require(processor.video_processor.size == config['video_size'], 'original processor size differs')
    return processor


def floor_indices(first, stop):
    require(type(first) is int and type(stop) is int and 0 <= first < stop, 'invalid native ordinal domain')
    n = stop-first
    return list(range(first, stop)) if n <= 128 else [first+i*(n-1)//127 for i in range(128)]


def make_window(meta, points, raw_start, raw_end, normalized_start, normalized_end, index, origin, clock_sha=None):
    points = [F(x) for x in points]
    raw_start, raw_end, origin = F(raw_start), F(raw_end), F(origin)
    require(points and all(a < b for a,b in zip(points,points[1:])) and points[0] == origin,
            'strict full-source raw clock and origin required')
    first, stop = bisect_left(points, raw_start), bisect_left(points, raw_end)
    ids = floor_indices(first, stop)
    require(raw_start < raw_end and first < stop and len(points) == meta['source_total_frames'], 'native domain/count differs')
    require(F(normalized_start)+origin == raw_start and F(normalized_end)+origin == raw_end,
            'raw and normalized source clock differ')
    return dict(recipe=RECIPE, window_id=meta['source_id']+':D128:'+str(index), source_id=meta['source_id'],
        index=index, source_path=meta['source_path'], source_sha256=meta['source_sha256'],
        source_total_frames=meta['source_total_frames'], width=meta['width'], height=meta['height'],
        fps_num=meta['fps_num'], fps_den=meta['fps_den'], all_source_exact_pts=[str(p) for p in points],
        raw_source_origin=str(origin), exact_raw_start=str(raw_start), exact_raw_end=str(raw_end),
        exact_normalized_start=str(F(normalized_start)), exact_normalized_end=str(F(normalized_end)),
        window_duration=str(raw_end-raw_start), eligible_first=first, eligible_stop=stop,
        source_frame_ordinals=ids, sample_exact_pts=[str(points[i]) for i in ids],
        clock_record_sha256=clock_sha, source_metadata_path=meta.get('source_metadata_path'),
        source_metadata_sha256=meta.get('source_metadata_sha256'))


def dev_windows():
    result = []
    for case in ('T01','T02','T03','T04','T05','T06'):
        path = DEV/case/'input.json'; meta = read(path)
        require(meta['case_id'] == case, 'six-source case identity differs')
        points = [F(x) for x in meta['all_source_exact_pts']]
        a,b = F(meta['window_start']),F(meta['window_end'])
        source = dict(meta, source_id=case, source_metadata_path=str(path), source_metadata_sha256=sha(path))
        result.append(make_window(source, points, a, b, a-points[0], b-points[0], 0, points[0]))
    require(len({w['source_sha256'] for w in result}) == 6, 'six independent source denominator differs')
    return result


def original_helpers():
    sys.path.insert(0, str(RUN/'balanced_two_window_risk_v3'))
    common = load(RUN/'balanced_two_window_risk_v3/bw_common.py', 'dense_original_bw_common')
    return common, common.helpers()


def production_windows():
    common, (_, _, _, _, old, _, _) = original_helpers()
    ref, manifest, clocks = old.inputs('rematch')
    path = RUN/'balanced_two_window_risk_v3/input_01/rematch_plan.json'
    plan = read(path); jobs = plan['jobs']
    records = {m['video_id']:m for m in manifest['records']}
    require(len(records) == len(manifest['records']) == len(jobs) == 426 and
        set(records) == {j['video_id'] for j in jobs} == set(clocks), '426 source manifest/clock/schedule denominator differs')
    output = []
    for job in jobs:
        item = records[job['video_id']]; clock = clocks[job['video_id']]
        arrays = clock['arrays']; tick = F(arrays['raw_time_base'])
        origin = arrays['raw_first_pts_ticks']*tick
        points = [p*tick for p in arrays['native_pts_ticks']]
        meta = dict(item, source_id=item['video_id'], source_total_frames=item['n_frames'])
        windows = []
        for index, part in enumerate(job['windows']):
            a = F(part['window']['exact_normalized_start']) if common.is_changed(part) else F(str(part['start_sec']))
            b = F(part['window']['exact_normalized_end']) if common.is_changed(part) else F(str(part['end_sec']))
            require(float(a) == part['start_sec'] and float(b) == part['end_sec'], 'original balanced schedule boundary differs')
            windows.append(make_window(meta, points, origin+a, origin+b, a, b, index, origin, clock['clock_record_sha256']))
        require(windows and all(F(a['exact_raw_end']) == F(b['exact_raw_start']) for a,b in zip(windows,windows[1:])), 'original schedule is not contiguous')
        output.append(dict(video_id=item['video_id'], targetRatioWH=item['targetRatioWH'],
            video_path=item['source_path'], n_frames=item['n_frames'], fps=item['fps_num']/item['fps_den'],
            arm=ARM, clock_branch=clock['branch'], windows=windows))
    require(sum(len(j['windows']) for j in output) == 521, '521 original balanced windows required')
    return output, dict(source=ref, original_plan_path=str(path), original_plan_sha256=sha(path))


def source_checked(window):
    path = Path(window['source_path']); before = path.stat()
    key = str(path.resolve(strict=True)); signature = (window['source_sha256'],before.st_size,before.st_mtime_ns)
    if _SOURCE_STATS.get(key) != signature:
        require(sha(path) == window['source_sha256'], 'actual source bytes changed')
        _SOURCE_STATS[key] = signature
    return before


def decode_window(window):
    import av
    import numpy as np
    _, _, _, _, color = dependencies()
    w = window; ids = w['source_frame_ordinals']; points = [F(x) for x in w['all_source_exact_pts']]
    require(w['recipe'] == RECIPE and ids == floor_indices(w['eligible_first'],w['eligible_stop']) and
        w['sample_exact_pts'] == [str(points[i]) for i in ids], 'prospective floor128 plan differs')
    before = source_checked(w); frames=[]; pixels=[]
    with av.open(w['source_path']) as container:
        require(len(container.streams.video) == 1, 'ambiguous source video stream')
        stream = container.streams.video[0]; rate = stream.average_rate
        require(rate is not None and (rate.numerator,rate.denominator) == (w['fps_num'],w['fps_den']), 'actual source FPS differs')
        require((stream.width,stream.height) == (w['width'],w['height']), 'source stream geometry differs')
        wanted = iter(ids); current = next(wanted, None)
        for ordinal, frame in enumerate(container.decode(stream)):
            if current is None:
                break
            require(ordinal < len(points) and frame.pts is not None and frame.time_base is not None and
                F(frame.pts)*frame.time_base == points[ordinal], 'actual sequential native raw PTS differs')
            if ordinal != current:
                continue
            image = color.convert_frame(frame,w['source_sha256'],'rgb24')
            require(image.shape == (w['height'],w['width'],3) and str(image.dtype) == 'uint8', 'actual source RGB geometry/dtype differs')
            frames.append(image); pixels.append(hashlib.sha256(image.tobytes(order='C')).hexdigest())
            current = next(wanted,None)
    after = Path(w['source_path']).stat()
    require(len(frames) == len(ids) and (before.st_size,before.st_mtime_ns) == (after.st_size,after.st_mtime_ns), 'source changed or selected native frame missing')
    return np.stack(frames), dict(source_frame_ordinals=ids, sample_exact_pts=w['sample_exact_pts'],
        frame_pixel_sha256=pixels, sequential_raw_pts_verified_through=ids[-1],
        source_sha256=w['source_sha256'],source_fps_num=w['fps_num'],source_fps_den=w['fps_den'],
        source_rgb_geometry=[w['height'],w['width'],3], color_identity=color_identity())


def tensor_signature(encoded):
    import torch
    return {k:dict(shape=list(v.shape),dtype=str(v.dtype),
        sha256=hashlib.sha256(v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
        for k,v in encoded.items() if hasattr(v,'shape')}


def text_prompt(processor, text):
    prompt = processor.apply_chat_template([dict(role='user',content=[dict(type='text',text=text)])],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    require(prompt.count('<|im_start|>user\n') == 1, 'original fixed chat template differs')
    return prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)


def encode_window(processor, window, decoded=None):
    import torch
    from dense_video import encode, identity, LEGACY_VIDEO_SIZE
    _, contracts, exact, frames, _ = dependencies()
    arr, evidence = decode_window(window) if decoded is None else decoded
    require(len(arr) == len(window['source_frame_ordinals']), 'physical frame denominator differs')
    physical = len(arr)
    plan = dict(source_frame_ids=window['source_frame_ordinals'],
        source_relative_pts=[float(F(x)) for x in window['sample_exact_pts']],window_start=float(F(window['exact_raw_start'])))
    metadata = dict(fps=window['fps_num']/window['fps_den'],frames_indices=window['source_frame_ordinals'],
        total_num_frames=window['source_total_frames'],video_backend='pyav')
    arr, metadata = frames.prepare_native_processor_input(arr,metadata,plan)
    with exact.exact_native_pts(processor,plan,metadata['fps']) as native:
        encoded = encode(processor,text=[text_prompt(processor,contracts.EMPTY_PROMPT)],
            videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[metadata],video_size=LEGACY_VIDEO_SIZE,max_input=16384)
        exact.verify_native_encoding(processor,encoded,native)
    return encoded,dict(evidence,window_digest=digest(window),recipe=RECIPE,
        raw_source_origin=window['raw_source_origin'],exact_raw_start=window['exact_raw_start'],
        exact_raw_end=window['exact_raw_end'],physical_frames=physical,
        prompt_sha256=hashlib.sha256(contracts.EMPTY_PROMPT.encode()).hexdigest(),
        native_processor_identity=native,**identity(processor,encoded,len(arr)),tensor_signature=tensor_signature(encoded))


def native_ranges(segments, window):
    points = [F(x) for x in window['all_source_exact_pts']]
    origin = F(window['exact_raw_start']); duration = F(window['window_duration']); result=[]
    for a,b in segments:
        a,b = F(str(a)),F(str(b))
        require(0 <= a < b <= duration, 'actual raw output exceeds exact native window')
        first,stop = bisect_left(points,origin+a),bisect_left(points,origin+b)
        require(window['eligible_first'] <= first < stop <= window['eligible_stop'], 'positive interval has zero actual native source frames')
        result.append([first,stop])
    return result


def check_model(model, identity):
    require(identity['base']['sha256'] == BASE_SHA and identity['base']['parameters'] == 8767123696 and
        identity['logical_parameters'] == 8782459120 and identity['adapter']['sha256'] == ADAPTER_SHA and
        identity['adapter']['tensors'] == 288 and identity['adapter']['actual_saved_values_equal'] is True and
        identity['adapter']['adapter_enabled'] is True and model.active_adapter == 'default' and
        not any(p.requires_grad for p in model.parameters()), 'actual original B weight/active LoRA identity differs')


def loaded_model():
    engine, _, _, _, _ = dependencies()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    config = read(RUN/'b_score_aligned_package_v4/config.json')
    model,processor,identity = engine.load_model(config)
    check_model(model,identity)
    return model,processor,identity,config


def generate(model,processor,encoded,evidence,window,out,attempts,max_calls,candidates):
    import torch
    from native_grammar import make_native_constraint
    _,contracts,_,_,_ = dependencies()
    raw_path = Path(out)/'raw.json'; prefix = int(encoded['input_ids'].shape[1])
    require(not raw_path.exists() and sum(r['event'] == 'BEGIN_MODEL_CALL' for r in rows(attempts)) < max_calls,
        'successful/raw attempt cannot be repeated or actual-call budget exceeded')
    eos = model.generation_config.eos_token_id
    grammar = make_native_constraint(processor.tokenizer,prefix,F(window['window_duration']),
        window['all_source_exact_pts'],F(window['exact_raw_start']),candidate_token_ids=candidates,
        eos_token_ids=eos,allow_empty=True)
    gpu = encoded.to('cuda')
    require(tensor_signature(gpu) == evidence['tensor_signature'], 'actual GPU input tensors differ from accepted CPU input')
    save(Path(out)/'gpu_input.json',dict(status='PASS_ACTUAL_CPU_GPU_TENSOR_EQUALITY',tensor_signature=evidence['tensor_signature']))
    count = 1+sum(r['event'] == 'BEGIN_MODEL_CALL' for r in rows(attempts))
    append(attempts,dict(event='BEGIN_MODEL_CALL',call_id=count,utc=utc(),raw_path=str(raw_path),
        window_digest=digest(window),source_id=window['source_id'],index=window['index']))
    started=time.monotonic()
    with torch.inference_mode():
        answer = model.generate(**gpu,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=grammar,
            return_dict_in_generate=True,output_scores=True)
    torch.cuda.synchronize()
    ids=answer.sequences[0,prefix:]; token_ids=ids.tolist()
    raw=processor.tokenizer.decode(token_ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
    scores=[float(s[0,int(t)]) for s,t in zip(answer.scores,ids)]
    receipt=dict(raw_output=raw,output_token_ids=token_ids,selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
        generated_score_count=len(answer.scores),input_tokens=prefix,output_tokens=len(token_ids),
        generation_seconds=time.monotonic()-started,input_evidence=evidence,constraint_stats=grammar.stats,
        eos_token_ids=[eos] if isinstance(eos,int) else list(eos),actual_model_call=True,new_optimizer_updates=0,
        request_window_digest=digest(window))
    save(raw_path,receipt)  # Preserve untouched raw IDs and scores before acceptance.
    require(0 < len(token_ids) <= 256 and len(answer.scores) == len(scores) == len(token_ids) and
        all(math.isfinite(s) for s in scores), 'actual selected token-score validity failed')
    grammar.assert_complete(token_ids)
    segments,errors,warnings=contracts.parse_segments(raw,F(window['window_duration']),allow_empty=True)
    require(segments is not None and not errors, 'unchanged strict parser rejected: '+repr(errors))
    ranges=native_ranges(segments,window)
    accepted=dict(status='MODEL_OK' if segments else 'LEGAL_EMPTY',output_valid=True,parsed_segments=segments,
        parse_errors=[],parse_warnings=warnings,raw_output=raw,raw_path=str(raw_path),raw_sha256=sha(raw_path),
        source_window=window,input_tokens=prefix,output_tokens=len(token_ids),input_evidence=evidence,
        native_frame_realizability=dict(status='PASS_ACTUAL_FULL_SOURCE_NATIVE_PTS',ranges=ranges,
                                       full_source_ordinals=True,not_limited_to_128_samples=True),
        generation_time_constraint=True,failure_to_empty_conversions=0,actual_model_call=True,new_optimizer_updates=0)
    save(Path(out)/'done.json',accepted)
    append(attempts,dict(event='ACCEPTED_MODEL_CALL',call_id=count,raw_path=str(raw_path),raw_sha256=sha(raw_path),
        done_path=str(Path(out)/'done.json'),done_sha256=sha(Path(out)/'done.json')))
    del gpu,answer
    return accepted


def failure(folder,exc,attempts=None):
    path=Path(folder)/'failure.json'
    if not path.exists():
        events=rows(attempts) if attempts and Path(attempts).exists() else []
        save(path,dict(status='STOP_NO_RETRY_NO_EMPTY_FALLBACK',utc=utc(),
            error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),
            actual_started_model_calls=sum(r['event']=='BEGIN_MODEL_CALL' for r in events),
            raw_receipts_preserved=True,new_optimizer_updates=0,official_score=None))
