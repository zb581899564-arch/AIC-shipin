"""Two process-exposed windows, direct local model input, no bulk annotation/training."""
import base64
import datetime as dt
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
IDS=['complete_7757d020fcdef4d4db1f4dbc','complete_e1e3a1030b7e5f5e7f4b9fb2']


def sha(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):d.update(b)
    return d.hexdigest()


def write(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)


def validate(obj):
    if type(obj)!=dict or set(obj)!={'keep','ordinary','uncertain'}:raise ValueError('wrong response keys')
    spans=[]
    for key,items in obj.items():
        if type(items)!=list:raise ValueError('span list required')
        for item in items:
            if type(item)!=dict or set(item)!={'start','end','evidence','fact'}:raise ValueError('wrong span fields')
            a,b=item['start'],item['end']
            if type(a)!=int or type(b)!=int or not 0<=a<=b<64:raise ValueError('invalid source observation IDs')
            evidence=item['evidence']
            if type(evidence)!=list or not 1<=len(evidence)<=3 or len(set(evidence))!=len(evidence) or any(type(v)!=int or not a<=v<=b for v in evidence):raise ValueError('evidence outside span')
            if type(item['fact'])!=str or not 1<=len(item['fact'])<=96:raise ValueError('fact length')
            spans.append((a,b))
    if not 1<=len(spans)<=3:raise ValueError('bounded total span count required')
    for i,(a,b) in enumerate(spans):
        if any(max(a,c)<=min(b,d) for c,d in spans[i+1:]):raise ValueError('overlapping incompatible spans')
    return obj


def main():
    from sft_contract import verify_live_gpu_reservation
    from PIL import Image
    verify_live_gpu_reservation()
    config=json.loads((HERE/'config.json').read_text())
    lock=json.loads((HERE/'source_lock.json').read_text())
    for p,digest in lock['files'].items():
        if sha(p)!=digest:raise ValueError('locked source changed: '+p)
    for asset in config['assets']:
        if Path(asset['path']).stat().st_size!=asset['bytes'] or sha(asset['path'])!=asset['sha256']:
            raise ValueError('teacher asset identity mismatch')
    records=[json.loads(s) for s in Path(config['records']).read_text().splitlines()]
    records={r['window_id']:r for r in records if r['window_id'] in IDS}
    if set(records)!=set(IDS) or len({r['source_sha256'] for r in records.values()})!=2:
        raise ValueError('two independent source identities missing')
    prepared=[]
    for wid in IDS:
        record=records[wid];obs=record['actual_observation']
        if not obs['all_planned_frames_delivered'] or not obs['teacher_student_same_source_range_frame_rgb']:
            raise ValueError('accepted native observation missing')
        frames=obs['frame_files'];points=obs['actual_pts_sec']
        if len(frames)!=64 or len(points)!=64 or any(a>=b for a,b in zip(points,points[1:])):
            raise ValueError('native64 frame/PTS denominator changed')
        if sha(obs['source_path'])!=record['source_sha256']:raise ValueError('source SHA changed')
        content=[];binding=[]
        for index,(frame,pts) in enumerate(zip(frames,points)):
            raw=Path(frame['path']).read_bytes()
            im=Image.open(frame['path']).convert('RGB')
            if hashlib.sha256(raw).hexdigest()!=frame['sha256'] or hashlib.sha256(im.tobytes()).hexdigest()!=frame['pixel_sha256']:
                raise ValueError('cached native image bytes/RGB changed')
            content += [{'type':'text','text':f'Observation ID {index}, source ordinal {frame["source_frame_ordinal"]}, native source PTS {pts:.9f}s:'},
                        {'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(raw).decode()}}]
            binding.append(dict(id=index,native_pts=pts,ordinal=frame['source_frame_ordinal'],
                                file_sha256=frame['sha256'],pixel_sha256=frame['pixel_sha256']))
        content.append({'type':'text','text':config['prompt']})
        prepared.append((wid,content,binding))
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    command=config['server_command']+['--port',str(port)]
    server=None;log=(HERE/'server.log').open('x');responses=[];setup_start=time.monotonic()
    try:
        server=subprocess.Popen(command,cwd=HERE,stdout=log,stderr=subprocess.STDOUT)
        write(HERE/'server_start.json',dict(pid=server.pid,command=command,inherited_pgid=os.getpgid(server.pid),
                                           utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        url=f'http://127.0.0.1:{port}'
        while True:
            if server.poll() is not None:raise RuntimeError('owned server exited before readiness')
            try:
                with urllib.request.urlopen(url+'/health',timeout=2) as r:
                    if r.status==200:break
            except Exception:
                if time.monotonic()-setup_start>120:raise TimeoutError('server readiness budget')
                time.sleep(1)
        write(HERE/'server_ready.json',dict(load_seconds=time.monotonic()-setup_start))
        for wid,content,binding in prepared:
            schema=config['schema']
            body=dict(model='Qwen/Qwen3-VL-32B-Instruct-GGUF',messages=[{'role':'user','content':content}],
                      temperature=0,seed=20261011,top_k=1,max_tokens=512,stream=True,cache_prompt=False,
                      n_cache_reuse=0,chat_template_kwargs={'enable_thinking':False},
                      stream_options={'include_usage':True},response_format={'type':'json_schema',
                      'json_schema':{'name':'bounded_native_span_pilot','strict':True,'schema':schema}})
            directory=HERE/wid;directory.mkdir()
            write(directory/'input_binding.json',dict(window_id=wid,frames=binding,
                source_sha256=records[wid]['source_sha256'],prior_labels_provided=False,
                window_pts_start=records[wid]['actual_observation']['window_pts_start_sec'],
                window_pts_end=records[wid]['actual_observation']['window_pts_end_exclusive_sec']))
            wire=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
            write(directory/'request_identity.json',dict(sha256=hashlib.sha256(wire).hexdigest(),bytes=len(wire),
                model=config['assets'][0]['sha256'],prompt_sha256=hashlib.sha256(config['prompt'].encode()).hexdigest()))
            request=urllib.request.Request(url+'/v1/chat/completions',data=wire,headers={'Content-Type':'application/json'})
            start=time.monotonic();first_content=None;answer='';events=[];usage=None;finish=None
            with (directory/'stream.jsonl').open('x') as raw_stream:
                with urllib.request.urlopen(request,timeout=180) as stream:
                    for line in stream:
                        if not line.startswith(b'data:'):continue
                        data=line[5:].strip()
                        if data==b'[DONE]':break
                        event=json.loads(data);events.append(event)
                        raw_stream.write(json.dumps(event,ensure_ascii=False)+'\n');raw_stream.flush()
                        usage=event.get('usage') or usage
                        for choice in event.get('choices',[]):
                            text=choice.get('delta',{}).get('content') or ''
                            if text and first_content is None:first_content=time.monotonic()-start
                            answer+=text
                            finish=choice.get('finish_reason') or finish
                        if time.monotonic()-start>180:raise TimeoutError('fixed single-request elapsed budget')
            (directory/'answer.txt').write_text(answer,encoding='utf-8')
            write(directory/'response_timing.json',dict(seconds=time.monotonic()-start,
                first_content_seconds=first_content,usage=usage,finish_reason=finish))
            if finish!='stop':raise ValueError('truncated/nonterminal model answer')
            value=validate(json.loads(answer))
            points=records[wid]['actual_observation']['actual_pts_sec']
            mapped={key:[dict(**span,native_start_pts=points[span['start']],native_end_observed_pts=points[span['end']])
                         for span in spans] for key,spans in value.items()}
            receipt=dict(window_id=wid,status='PASS_INTERFACE_ONLY_NOT_SEMANTIC_QUALITY',
                seconds=time.monotonic()-start,first_content_seconds=first_content,usage=usage,
                answer_sha256=sha(directory/'answer.txt'),output=value,native_mapping=mapped,
                prior_labels_provided=False,training_label=False,unobserved_is_not_negative=True)
            write(directory/'accepted.json',receipt);responses.append(receipt)
            print(json.dumps({'window_id':wid,'seconds':receipt['seconds'],'status':receipt['status']}),flush=True)
        write(HERE/'completion.json',dict(status='PASS_TWO_SHORT_NATIVE_TEACHER_INTERFACE_NOT_QUALITY',
            responses=responses,new_model_calls=2,new_optimizer_updates=0,bulk_annotation_admitted=False))
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:server.wait(timeout=15)
            except subprocess.TimeoutExpired:server.kill();server.wait()
        log.close()
        write(HERE/'server_stop.json',dict(pid=server.pid if server else None,
            exit_code=server.returncode if server else None,owned_server_terminated=True))


if __name__=='__main__':
    try:main()
    except Exception as e:
        write(HERE/'failure.json',dict(status='STOP_NO_RETRY_NO_FALLBACK',error=type(e).__name__+': '+str(e),traceback=traceback.format_exc()))
        raise
