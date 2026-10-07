"""Four relative-summary diagnostics and four real weak reviews; no training labels."""
import argparse
import base64
from collections import Counter
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
V7 = RUN / 'teacher_student_autopilot_v7'
sys.path.insert(0, str(V7))
import autopilot_common as c
import teacher_label as t


def choose(records):
    seen=set(c.read(RUN/'teacher_context_diagnostic_v2/manifest.json')['window_ids'])
    chosen=[]
    for split in ('train','dev'):
        eligible=[r for r in records if r['split']==split and r['window_id'] not in seen
                  and len(r['actual_observation']['frame_files'])==64 and r['window']['source_natural_window_count']>1]
        eligible.sort(key=lambda r:(hashlib.sha256(r['window_id'].encode()).hexdigest(),r['window_id']))
        c.require(len(eligible)>=2,'insufficient pre-registered complete-source diagnostic candidates')
        chosen.extend(eligible[:2])
    return chosen


def ordinal_sample(count, limit=64):
    if type(count) is not int or count < 1 or type(limit) is not int or limit < 1:
        raise ValueError('nonempty source required')
    amount = min(count, limit)
    return [0] if amount == 1 else [i * (count - 1) // (amount - 1) for i in range(amount)]


def clock_text(value):
    # The pinned C++ JSON/runtime conversion can change numeric constant lexemes.
    # A decimal string keeps the source's validated shortest round-trip identity.
    return format(Decimal(str(value)), 'f')


def schema(record):
    obs = record['actual_observation']
    points = t.window_local_points(obs)
    boundaries = sorted(set([0.0, float(record['window']['window_duration_sec']), *points]))
    evidence = {'anyOf': [
        {'type': 'object', 'additionalProperties': False,
         'properties': {'frame_ordinal': {'const': ordinal},
                        'window_local_sec': {'const': clock_text(point)},
                        'description': {'type': 'string', 'minLength': 3}},
         'required': ['frame_ordinal', 'window_local_sec', 'description']}
        for ordinal, point in zip(obs['source_frame_ordinals'], points)]}
    segment = {'type': 'object', 'additionalProperties': False,
               'properties': {'start_sec': {'type': 'string', 'enum': [clock_text(v) for v in boundaries]},
                              'end_sec': {'type': 'string', 'enum': [clock_text(v) for v in boundaries]},
                              'reason': {'type': 'string', 'minLength': 3}},
               'required': ['start_sec', 'end_sec', 'reason']}
    branches = []
    for state in ('POSITIVE', 'NO_HIGHLIGHT', 'UNCERTAIN'):
        props = {'window_id': {'const': record['window_id']},
                 'global_visible_summary': {'type': 'string', 'minLength': 10},
                 'comparison_to_rest': {'type': 'string', 'minLength': 10},
                 'decision_reason': {'type': 'string', 'minLength': 10},
                 'state': {'const': state},
                 'evidence': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': evidence},
                 'retained_segments': {'type': 'array', 'minItems': 1 if state == 'POSITIVE' else 0,
                                       'maxItems': 5 if state == 'POSITIVE' else 0, 'items': segment}}
        branches.append({'type': 'object', 'additionalProperties': False,
                         'properties': props, 'required': list(props)})
    return {'anyOf': branches}


def validate_result(answer, record):
    validator = t.validator_for(RUN)
    value = validator.strict_json(answer)
    c.require(isinstance(value, dict), 'diagnostic response must be an object')
    c.require(set(value) == {'window_id', 'global_visible_summary', 'comparison_to_rest',
                            'decision_reason', 'state', 'evidence', 'retained_segments'}, 'diagnostic keys differ')
    for key in ('global_visible_summary','comparison_to_rest'):
        c.require(isinstance(value[key],str) and len(value[key])>=10,'actual whole-source comparison missing')
    c.require(value['window_id'] == record['window_id'], 'diagnostic source differs')
    c.require(value['state'] in ('POSITIVE', 'NO_HIGHLIGHT', 'UNCERTAIN'), 'diagnostic state invalid')
    c.require(isinstance(value['decision_reason'], str) and len(value['decision_reason']) >= 10,
              'diagnostic decision reason missing')
    obs = record['actual_observation']
    mapping = {ordinal: clock_text(point) for ordinal, point in zip(obs['source_frame_ordinals'], t.window_local_points(obs))}
    c.require(isinstance(value['evidence'], list) and 1 <= len(value['evidence']) <= 8, 'actual evidence required')
    for item in value['evidence']:
        c.require(isinstance(item, dict) and set(item) == {'frame_ordinal', 'window_local_sec', 'description'},
                  'diagnostic evidence keys invalid')
        c.require(type(item['frame_ordinal']) is int and item['frame_ordinal'] in mapping
                  and isinstance(item['window_local_sec'], str)
                  and item['window_local_sec'] == mapping[item['frame_ordinal']],
                  'evidence source ordinal and window time disagree')
        c.require(isinstance(item['description'], str) and len(item['description']) >= 3,
                  'diagnostic visible evidence description missing')
    segments = value['retained_segments']
    c.require(isinstance(segments, list) and len(segments) <= 5, 'diagnostic segment list invalid')
    c.require(bool(segments) == (value['state'] == 'POSITIVE'), 'state/segments contradict')
    allowed = {clock_text(0.0), clock_text(float(record['window']['window_duration_sec'])), *mapping.values()}
    previous = Decimal(0)
    for item in segments:
        c.require(isinstance(item, dict) and set(item) == {'start_sec', 'end_sec', 'reason'}, 'diagnostic segment keys invalid')
        a, b = item['start_sec'], item['end_sec']
        c.require(isinstance(a, str) and isinstance(b, str) and a in allowed and b in allowed,
                  'diagnostic endpoints are not exact registered decimal strings')
        a, b = Decimal(a), Decimal(b)
        c.require(previous <= a < b <= Decimal(str(record['window']['window_duration_sec'])),
                  'diagnostic segment clock invalid')
        c.require(isinstance(item['reason'], str) and len(item['reason']) >= 3, 'diagnostic segment reason missing')
        previous = b
    return value


def verify():
    lock = c.read(HERE / 'source_lock.json')
    for path, expected in lock['files'].items():
        c.require(c.sha(path) == expected, 'diagnostic bound file changed: ' + path)
    manifest = c.read(HERE / 'manifest.json')
    c.require(c.sha(V7 / 'pilot_01/validated/validated_records.jsonl') == manifest['original_records_sha256'],
              'original diagnostic population changed')
    records = c.rows(V7 / 'pilot_01/validated/validated_records.jsonl')
    selected = choose(records)
    c.require([r['window_id'] for r in selected] == manifest['window_ids'], 'registered diagnostic selection changed')
    validator = t.validator_for(RUN)
    for record in selected:
        directory = V7 / 'teacher_01/windows' / record['window_id']
        done = c.read(directory / 'done.json')
        c.require(c.sha(directory / 'done.json') == manifest['original_done_sha256'][record['window_id']],
                  'original accepted receipt changed')
        c.require(all(c.sha(directory / n) == h for n, h in done['files'].items()), 'original accepted files changed')
        annotation = c.read(directory / 'annotation.json')
        rebuilt = validator.make_record(record['window'], annotation['observation'], annotation['teacher'], annotation['raw_answer'])
        c.require({k:v for k,v in rebuilt.items() if k != 'created_utc'} ==
                  {k:v for k,v in record.items() if k != 'created_utc'}, 'original validator replay failed')
        t.frame_content(record['actual_observation'])
        c.require(c.sha(record['window']['source_path']) == record['window']['source_sha256'], 'source bytes changed')
    return manifest, selected, validator


def overview(record, out):
    import av
    import numpy as np
    from PIL import Image
    source = Path(record['window']['source_path'])
    ffprobe = c.read(V7 / 'config.json')['ffprobe_path']
    result = subprocess.run([ffprobe, '-v', 'error', '-select_streams', 'v:0', '-show_frames',
                             '-show_entries', 'frame=best_effort_timestamp_time,pkt_duration_time,duration_time',
                             '-of', 'json', str(source)], capture_output=True, text=True, check=True, timeout=600)
    t.validator_for(RUN)  # bind the v7 frozen supervision loader before importing its clock parser
    from select_windows import parse_clock_frames
    c.require(Path(sys.modules['select_windows'].__file__).resolve() == (V7 / 'supervision/select_windows.py').resolve(),
              'overview clock helper identity differs')
    points, clock = parse_clock_frames(json.loads(result.stdout)['frames'])
    c.require(clock['pts_sequence_sha256'] == record['window']['clock_sequence_sha256'], 'overview full clock changed')
    wanted = set(ordinal_sample(len(points)))
    out.mkdir(parents=True, exist_ok=False)
    frames = []
    count = 0
    with av.open(str(source), 'r') as container:
        stream = container.streams.video[0]
        for ordinal, frame in enumerate(container.decode(stream)):
            count = ordinal + 1
            c.require(frame.pts is not None and frame.time_base is not None, 'overview missing native PTS')
            point = float(frame.pts * frame.time_base)
            c.require(ordinal < len(points) and abs(point - points[ordinal]) <= 1e-6, 'overview PTS differs from full source clock')
            if ordinal in wanted:
                rgb = np.ascontiguousarray(frame.to_ndarray(format='rgb24'))
                im = Image.fromarray(rgb, mode='RGB')
                im.thumbnail((384,384), Image.Resampling.LANCZOS)
                file = out / (str(ordinal).zfill(9) + '.png'); im.save(file, format='PNG')
                resized = np.ascontiguousarray(np.asarray(im))
                frames.append({'path':str(file), 'sha256':c.sha(file), 'source_frame_ordinal':ordinal,
                               'source_pts_sec':point, 'source_rgb_sha256':hashlib.sha256(rgb.tobytes()).hexdigest(),
                               'provided_rgb_sha256':hashlib.sha256(resized.tobytes()).hexdigest(),
                               'provided_size':list(im.size), 'downsampled_context_only':True})
    c.require(count == len(points) and len(frames) == len(wanted), 'overview complete source decode missing')
    c.require(c.sha(source) == record['window']['source_sha256'], 'source changed during overview')
    receipt = {'source':str(source), 'source_sha256':record['window']['source_sha256'],
               'full_source_frame_count':count, 'clock_sequence_sha256':clock['pts_sequence_sha256'],
               'context_is_downloaded_source_not_original_full_youtube':True,
               'sequential_decode_from_ordinal_zero':True, 'frames':frames}
    c.write(out / 'decode_receipt.json', receipt, fresh=True)
    return receipt


def overview_content(receipt):
    content = [{'type':'text', 'text':'以下是整段已下载源片的低分辨率背景overview，不能作为目标窗内保留端点；缺失的原始视频上下文未知。'}]
    for f in receipt['frames']:
        c.require(c.sha(f['path']) == f['sha256'], 'overview PNG changed')
        content.extend([{'type':'text','text':f"CONTEXT_ONLY source_frame_ordinal={f['source_frame_ordinal']}; source_PTS_sec={f['source_pts_sec']!r}"},
                        {'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(Path(f['path']).read_bytes()).decode()}}])
    return content


def request(record, arm, context, admission, out):
    out.mkdir(parents=True, exist_ok=False)
    prompt = (HERE / 'prompt.txt').read_text(encoding='utf-8') + '\n目标窗：' + json.dumps({k:record['window'][k] for k in
                ('window_id','window_pts_start_sec','window_pts_end_exclusive_sec','window_duration_sec',
                 'source_clock_first_pts_sec','source_clock_end_exclusive_sec','source_natural_window_count')}, ensure_ascii=False)
    (out / 'prompt.txt').write_text(prompt, encoding='utf-8')
    content = [{'type':'text','text':prompt}]
    context_count = 0
    if arm == 'WINDOW_WITH_SOURCE_OVERVIEW':
        content.extend(overview_content(context)); context_count = len(context['frames'])
    content.append({'type':'text','text':'下面是目标窗口64个完整native RGB帧，以下window_local_sec才是输出时钟：'})
    content.extend(t.frame_content(record['actual_observation']))
    generated = schema(record);c.write(out/'generation_schema.json', generated, fresh=True)
    log=Path(admission['server_log']);offset=log.stat().st_size
    payload={'model':t.TEACHER_ID,'messages':[{'role':'user','content':content}], 'temperature':0,'seed':20261008,
             'top_k':1,'max_tokens':8192,'stream':False,'cache_prompt':False,'n_cache_reuse':0,'timings_per_token':True,
             'chat_template_kwargs':{'enable_thinking':False},'response_format':t.response_format(generated)}
    started=time.monotonic()
    result=t.http_json(admission['server_url']+'/v1/chat/completions',payload,out/'http',timeout=3600)
    c.write(out/'server_response.json',result,fresh=True)
    choices=result.get('choices')
    choice=choices[0] if isinstance(choices,list) and len(choices)==1 else {}
    answer=choice.get('message',{}).get('content')
    if isinstance(answer,str): (out/'raw_answer.txt').write_text(answer,encoding='utf-8')
    c.require(log.stat().st_size >= offset, 'diagnostic server log rotated')
    with log.open('rb') as stream: stream.seek(offset);log_bytes=stream.read()
    (out/'processor.log').write_bytes(log_bytes)
    grids=t.parse_processor_log(log_bytes.decode('utf-8',errors='replace'),context_count+len(record['actual_observation']['frame_files']))
    tokens=result.get('usage',{}).get('prompt_tokens')
    c.require(type(tokens) is int and 0<tokens<=65536 and all(g['pixels']<=admission['max_pixels_per_frame'] for g in grids),
              'actual diagnostic processor/context limits violated')
    c.require(choice.get('finish_reason')=='stop' and result.get('truncated',False) is False,'diagnostic context/output truncated')
    c.require(isinstance(choices,list) and len(choices)==1 and isinstance(answer,str) and answer.strip(),
              'diagnostic missing a unique actual text response')
    t.verify_runtime_grammar(result,generated,answer,out)
    value=validate_result(answer,record)
    receipt={'status':'PASS_REAL_CONTEXT_DIAGNOSTIC_REQUEST','window_id':record['window_id'],'arm':arm,'result':value,
             'actual_prompt_tokens':tokens,'physical_images':len(grids),'actual_processor_grids':grids,
             'target_original_decode_receipt_sha256':c.sha(V7/'teacher_01/windows'/record['window_id']/'decode_receipt.json'),
             'context_decode_sha256':c.sha(Path(context['frames'][0]['path']).parent/'decode_receipt.json') if context_count else None,
             'wall_sec':time.monotonic()-started,'raw_answer_sha256':c.sha(out/'raw_answer.txt'),
             'labels_created':0,'optimizer_steps':0,'utc':c.utc()}
    c.write(out/'diagnostic_receipt.json',receipt,fresh=True)
    return receipt


def review_schema(record):
    properties={'window_id':{'const':record['window_id']},'all_provided_frames_reviewed':{'type':'boolean'},
                'semantics_consistent':{'type':'boolean'},'uncertain':{'type':'boolean'},
                'reason':{'type':'string','minLength':10},'issues':{'type':'array','items':{'type':'string','minLength':1}}}
    return {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties)}


def review(record, candidate, context, admission, out):
    out.mkdir(parents=True,exist_ok=False)
    prompt=(HERE/'review_prompt.txt').read_text(encoding='utf-8')+'\n实际目标与源时钟：'+json.dumps({key:record['window'][key] for key in
        ('window_id','window_pts_start_sec','window_pts_end_exclusive_sec','window_duration_sec',
         'source_clock_first_pts_sec','source_clock_end_exclusive_sec')},ensure_ascii=False)
    prompt+='\n待检查的原始诊断对象（不得替它补造事实）：'+json.dumps(candidate['result'],ensure_ascii=False)
    (out/'prompt.txt').write_text(prompt,encoding='utf-8')
    content=[{'type':'text','text':prompt},*overview_content(context),
             {'type':'text','text':'以下是目标64帧；输出片段秒数是window_local，source PTS只作元数据。'},
             *t.frame_content(record['actual_observation'])]
    generated=review_schema(record);c.write(out/'generation_schema.json',generated,fresh=True)
    log=Path(admission['server_log']);offset=log.stat().st_size
    payload={'model':t.TEACHER_ID,'messages':[{'role':'user','content':content}],'temperature':0,'seed':20261008,
             'top_k':1,'max_tokens':8192,'stream':False,'cache_prompt':False,'n_cache_reuse':0,'timings_per_token':True,
             'chat_template_kwargs':{'enable_thinking':False},'response_format':t.response_format(generated)}
    started=time.monotonic()
    response=t.http_json(admission['server_url']+'/v1/chat/completions',payload,out/'http',timeout=3600)
    c.write(out/'server_response.json',response,fresh=True)
    choices=response.get('choices');choice=choices[0] if isinstance(choices,list) and len(choices)==1 else {}
    raw=choice.get('message',{}).get('content')
    if isinstance(raw,str):(out/'raw_answer.txt').write_text(raw,encoding='utf-8')
    c.require(log.stat().st_size>=offset,'review server log rotated')
    with log.open('rb') as stream:stream.seek(offset);log_bytes=stream.read()
    (out/'processor.log').write_bytes(log_bytes)
    grids=t.parse_processor_log(log_bytes.decode(errors='replace'),len(context['frames'])+64)
    tokens=response.get('usage',{}).get('prompt_tokens')
    c.require(type(tokens)is int and 0<tokens<=65536 and all(g['pixels']<=admission['max_pixels_per_frame'] for g in grids),
              'actual source-summary review input contract violated')
    c.require(choice.get('finish_reason')=='stop' and response.get('truncated',False)is False
              and isinstance(raw,str)and raw.strip(),'actual source-summary review incomplete')
    t.verify_runtime_grammar(response,generated,raw,out)
    value=t.validator_for(RUN).strict_json(raw)
    c.require(set(value)==set(generated['required'])and value['window_id']==record['window_id'],'weak review identity/keys differ')
    c.require(all(type(value[k])is bool for k in ('all_provided_frames_reviewed','semantics_consistent','uncertain'))
              and isinstance(value['reason'],str)and len(value['reason'])>=10
              and isinstance(value['issues'],list)and all(isinstance(i,str)and i for i in value['issues']),
              'weak review semantic types differ')
    supported=value['all_provided_frames_reviewed']and value['semantics_consistent']and not value['uncertain']and not value['issues']
    receipt={'status':'PASS_REAL_RELATIVE_SUMMARY_WEAK_REVIEW_REQUEST','window_id':record['window_id'],
             'review_status':'SUPPORTED'if supported else'REJECTED_OR_UNCERTAIN','result':value,
             'candidate_receipt_sha256':c.sha(Path(candidate['receipt_path'])),'actual_prompt_tokens':tokens,
             'physical_images':len(grids),'raw_answer_sha256':c.sha(out/'raw_answer.txt'),'wall_sec':time.monotonic()-started,
             'weak_same_teacher_not_human_truth':True,'utc':c.utc()}
    c.write(out/'review_receipt.json',receipt,fresh=True)
    return receipt


def run():
    c.require(socket.gethostname()=='inspur-NP5570M5','unexpected context diagnostic host')
    c.require(not (HERE/'registration.json').exists() and not (HERE/'completion.json').exists()
              and not (HERE/'run_01').exists(), 'one-shot diagnostic already registered or attempted')
    out=HERE/'run_01';server=None;receipts=[];reviews=[];started=time.monotonic()
    try:
        manifest,records,validator=verify()
        c.write(HERE/'registration.json',{'pid':os.getpid(),'utc':c.utc(),'source_lock_sha256':c.sha(HERE/'source_lock.json'),
                 'manifest_sha256':c.sha(HERE/'manifest.json'),'student_training_admitted':False},fresh=True)
        out.mkdir(exist_ok=False)
        c.write(HERE/'progress.json',{'stage':'SEQUENTIAL_SOURCE_OVERVIEW_AND_WEIGHT_CHECK','utc':c.utc(),
                 'completed_requests':0,'total_requests':8,'pid':os.getpid(),'optimizer_steps':0})
        contexts={r['window_id']:overview(r,out/'overview'/r['window_id']) for r in records}
        admission=c.read(V7/'teacher_admission.json');admission['job_source_lock_sha256']=c.sha(HERE/'source_lock.json')
        with socket.socket() as sock: sock.bind(('127.0.0.1',0));number=sock.getsockname()[1]
        admission['server_command'][admission['server_command'].index('--port')+1]=str(number)
        admission['server_url']='http://127.0.0.1:'+str(number)
        t.validate_admission(admission,validator)
        c.write(HERE/'progress.json',{'stage':'LOADING_PINNED_CONTEXT_DIAGNOSTIC_TEACHER','utc':c.utc(),
                 'completed_requests':0,'total_requests':8,'pid':os.getpid(),'optimizer_steps':0})
        server,admission=t.start_server(admission,out)
        c.write(out/'teacher_admission.json',admission,fresh=True)
        for record in records:
            for arm in ('WINDOW_WITH_SOURCE_OVERVIEW',):
                receipts.append(request(record,arm,contexts[record['window_id']],admission,out/'requests'/record['window_id']/arm))
                receipts[-1]['receipt_path']=str(out/'requests'/record['window_id']/arm/'diagnostic_receipt.json')
                c.write(HERE/'progress.json',{'stage':'REAL_CONTEXT_DIAGNOSTIC','completed_requests':len(receipts),
                         'total_requests':8,'annotation_requests':len(receipts),'review_requests':0,
                         'states':dict(Counter(r['result']['state'] for r in receipts)),
                         'optimizer_steps':0,'utc':c.utc()})
        t.save_rows(out/'diagnostic_receipts.jsonl',receipts)
        for record,candidate in zip(records,receipts):
            reviews.append(review(record,candidate,contexts[record['window_id']],admission,out/'reviews'/record['window_id']))
            c.write(HERE/'progress.json',{'stage':'REAL_RELATIVE_SUMMARY_WEAK_REVIEW','completed_requests':len(receipts)+len(reviews),
                    'total_requests':8,'annotation_requests':len(receipts),'review_requests':len(reviews),
                    'states':dict(Counter(r['result']['state']for r in receipts)),
                    'review_states':dict(Counter(r['review_status']for r in reviews)),'optimizer_steps':0,'utc':c.utc()})
        t.save_rows(out/'review_receipts.jsonl',reviews)
        completion={'status':'PASS_CONTEXT_DIAGNOSTIC_COMPLETE','request_count':8,'annotation_requests':4,'review_requests':4,
                    'states':dict(Counter(r['result']['state']for r in receipts)),
                    'review_states':dict(Counter(r['review_status']for r in reviews)),
                    'per_window':[{'window_id':r['window_id'],'split':r['split'],'state':a['result']['state'],
                                   'weak_review':b['review_status']}for r,a,b in zip(records,receipts,reviews)],
                    'same_teacher_not_independent_truth':True,'new_training_labels':0,'student_training_admitted':False,
                    'optimizer_steps':0,'raw_receipts_sha256':c.sha(out/'diagnostic_receipts.jsonl'),
                    'wall_sec':time.monotonic()-started,'utc':c.utc()}
        c.write(HERE/'completion.json',completion,fresh=True);c.write(HERE/'progress.json',completion)
    except BaseException as error:
        stopped={'status':'STOP_CONTEXT_DIAGNOSTIC_PRESERVED','reason':str(error),
                 'completed_requests':len(receipts)+len(reviews),'annotation_requests':len(receipts),'review_requests':len(reviews),
                 'optimizer_steps':0,'new_training_labels':0,'utc':c.utc()}
        c.write(HERE/'completion.json',stopped,fresh=True);c.write(HERE/'progress.json',stopped)
        raise
    finally:
        if server is not None:
            if server.poll() is None:
                server.terminate()
                try: server.wait(timeout=30)
                except subprocess.TimeoutExpired: server.kill();server.wait(timeout=30)
            c.write(out/'server_stop_receipt.json',{'owned_server_pid':server.pid,'returncode':server.returncode,
                     'external_processes_signalled':False,'utc':c.utc()},fresh=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true');args=parser.parse_args()
    if args.preflight:
        _,records,_=verify();print(json.dumps({'status':'PASS_CONTEXT_DIAGNOSTIC_PREFLIGHT','windows':len(records),'GPU_started':False}))
    else: run()
