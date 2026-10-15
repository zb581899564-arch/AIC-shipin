      logical_parameters=total,shared_base_counted_once=True,new_optimizer_updates_this_inference=0,training_optimizer_steps=237,
      old_B_time_adapter_used=False,adapter_config_sha256=ADAPTER_CONFIG_SHA,actual_adapter=actual_adapter,
      raw_sha256=sha(dest/'raw.jsonl'),prepared_sha256=sha(dest/'prepared.json')))
def replay(scope):
    import torch
    data(scope);b=binding(scope);dest=out(scope);g=c.read(dest/'generation.json')
    assert g['raw_sha256']==sha(dest/'raw.jsonl') and g['prepared_sha256']==sha(dest/'prepared.json')
    p=processor();ids=candidates(p.tokenizer);raw=c.rows(dest/'raw.jsonl');planned=c.rows(dest/'blocks.jsonl')
    assert len(raw)==len(planned)==b['blocks'] and [r['id'] for r in raw]==[r['id'] for r in planned]
    for block,row in zip(planned,raw):
        e,sig=encode(p,block);assert all(row[k]==v for k,v in sig.items()) and row['video_id']==block['video_id']
        text,obj=Constraint(p.tokenizer,sig['input_tokens'],len(block['samples']),ids).finish(row['output_token_ids'])
        assert text==row['answer'] and set(obj)=={'scores_x20'} and len(obj['scores_x20'])==len(block['samples'])
        assert all(type(v) is int and 20<=v<=100 for v in obj['scores_x20'])
    assert not torch.cuda.is_initialized()
    c.write(dest/'cpu_replay.json',dict(status='PASS_ALL_ACTUAL_PROCESSOR_PIXELS_TOKENS_RAW_PARSER_CPU',blocks=len(raw),raw_sha256=sha(dest/'raw.jsonl'),new_model_calls=0,CUDA_initialized=False))
def finish(scope):
    from production import field_frames
    from field_contract import compose_from_field
    from frame_contract import legacy_manifest
    from package_contract import keyset,validate_predictions,package
    item,manifest,clocks,cache=data(scope);b=binding(scope);dest=out(scope)
    replayed=c.read(dest/'cpu_replay.json');assert replayed['raw_sha256']==sha(dest/'raw.jsonl')
    samples=c.rows(dest/'samples.jsonl');blocks=c.rows(dest/'blocks.jsonl');raw=c.rows(dest/'raw.jsonl')
    assert len(blocks)==len(raw)==b['blocks'] and [(s['video_id'],s['grid_index']) for r in blocks for s in r['samples']]==[(s['video_id'],s['grid_index']) for s in samples]
    chosen=set();scored=[]
    for block,row in zip(blocks,raw):
        assert block['id']==row['id'];scores=json.loads(row['answer'])['scores_x20'];assert len(scores)==len(block['samples'])
        for s,score in zip(block['samples'],scores):
            assert type(score) is int and 20<=score<=100
            scored.append(dict(video_id=s['video_id'],grid_index=s['grid_index'],score_x20=score,selected=score>=49,
              first_native_ordinal=s['first_native_ordinal'],end_native_ordinal_exclusive=s['end_native_ordinal_exclusive']))
            if score>=49:chosen.update((s['video_id'],ordinal) for ordinal in range(s['first_native_ordinal'],s['end_native_ordinal_exclusive']))
    domain=field_frames(manifest,clocks);assert chosen<=keyset(domain);selected=[r for r in domain if (r['video_id'],r['source_frame']) in chosen]
    assert len(selected)==len(chosen)
    for record in manifest['records']:assert sha(record['source_path'])==record['source_sha256']
    pred,provenance=compose_from_field(legacy_manifest(manifest),selected,c.rows(cache/'field_shots.jsonl'),c.rows(cache/'anchor_requests.jsonl'),c.rows(cache/'anchor_output.jsonl'))
    c.write_rows(dest/'selected.jsonl',selected);c.write_rows(dest/'scored_bins.jsonl',scored)
    c.write_rows(dest/'predictions.jsonl',pred);c.write_rows(dest/'provenance.jsonl',provenance)
    c.write(dest/'metadata.json',dict(records=manifest['records'],errors=[]))
    checks=validate_predictions(legacy_manifest(manifest),pred,keyset(selected),provenance)
    pending=dest/'candidate_IMAGE_SCORE_237STEP_8B.PENDING.zip';checks.update(package(dest/'predictions.jsonl',pending))
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
      '--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(dest/'metadata.json'),
      '--selected',str(dest/'selected.jsonl'),'--predictions',str(dest/'predictions.jsonl'),'--provenance',str(dest/'provenance.jsonl'),
      '--zip',str(pending),'--report',str(dest/'independent_validation.json')],check=True)
    report=c.read(dest/'independent_validation.json');assert report['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and len(report['checks'])==11 and all(report['checks'].values())
    candidate=dest/'candidate_IMAGE_SCORE_237STEP_8B.zip';pending.rename(candidate)
    c.write(dest/'package_receipt.json',dict(status='PASS_COMPLETE_IMAGE_SCORE_237STEP_8B_EXPERIMENTAL_ZIP',scope=scope,
      candidate=str(candidate),zip_bytes=candidate.stat().st_size,zip_sha256=sha(candidate),videos=len(pred),selected_frames=len(selected),
      empty_videos=sum(not r['predictions'] for r in pred),samples=len(samples),blocks=len(blocks),adapter_sha256=ADAPTER_SHA,
      logical_parameters=8774791408,training_optimizer_steps=237,old_spatial_source_field=EXPECTED[scope],spatial_model_calls=0,
      official_score=None,uploaded=False,production_replaced=False,independent_validation_sha256=sha(dest/'independent_validation.json'),
      quality_evidence='SEEN_TVSUM_DEVELOPMENT_PROXY_ONLY; NATIVE_PROXY_F_CI_CROSSES_ZERO; AIC_GENERALIZATION_UNKNOWN'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','generate','replay','finish']);p.add_argument('scope',choices=['nontest','rematch']);a=p.parse_args()
    globals()[a.mode](a.scope)

```


## 原文件全文：reports/annotation_iteration_20261010/agy_short_clips_v2.py
字节=9437；SHA256=a8d7dda1dd3f67a7c7aa3a309ecb737b9980d5adf02eaa36553b0b867bf86d61

```py
"""Six fixed 30-second teacher checks, native PTS mapping, no guessed times."""
import av,hashlib,json,subprocess
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;OLD=H.parent/'qwen8b_annotation_20261009_v1'
AGY=Path('C:/Users/33056/AppData/Local/agy/bin/agy.exe');MODEL='gemini-3.8-flash-high'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def prepare():
    manifests=[json.loads(p.read_text()) for p in sorted((OLD/'input').glob('*/manifest.json'))]
    selected=[m for m in manifests if m['source_id'] in ('37rzWOQsNIw','0tmA_C6XwfM')]
    categories={m['category'] for m in selected}
    extra=next(m for m in manifests if m['split']=='train' and m['category'] not in categories and m['source_duration_seconds']>80)
    selected.append(extra);assert len(selected)==3 and all(m['split']=='train' for m in selected)
    jobs=[]
    for m in selected:
        sid=m['source_id'];src=OLD/'input'/sid/m['media_file'];assert sha(src)==m['media_sha256']
        # Fixed time domains are selected without teacher labels or human scores.
        domains=[(20,50),(max(50,int(m['source_duration_seconds']/2)),max(50,int(m['source_duration_seconds']/2))+30)]
        for j,(start,end) in enumerate(domains):
            folder=H/'agy_v2'/f'{sid}_{j:02d}';folder.mkdir(parents=True,exist_ok=False)
            dest=folder/'clip.mp4';mapping=[];original=[]
            with av.open(str(src)) as inp,av.open(str(dest),'w') as out:
                source=inp.streams.video[0];rate=source.average_rate;base=source.time_base;first=source.start_time or 0
                stream=out.add_stream('libx264',rate=source.average_rate)
                stream.width=source.codec_context.width;stream.height=source.codec_context.height
                stream.pix_fmt='yuv420p';stream.options={'crf':'18','preset':'fast'}
                stream.time_base=base;stream.codec_context.time_base=base
                offset=None
                for ordinal,frame in enumerate(inp.decode(source)):
                    source_time=Fraction(frame.pts-first)*base
                    if source_time<start:continue
                    if source_time>=end:break
                    if offset is None:offset=frame.pts
                    rel=Fraction(frame.pts-offset)*base
                    rgb=frame.to_image();original.append((ordinal,frame.pts,source_time,rgb))
                    new=av.VideoFrame.from_image(rgb);new.pts=frame.pts-offset;new.time_base=base
                    for packet in stream.encode(new):out.mux(packet)
                    mapping.append({'ordinal':ordinal,'source_pts':frame.pts,'global_seconds_exact':str(source_time),
                                    'local_seconds_exact':str(rel)})
                for packet in stream.encode():out.mux(packet)
            assert mapping
            with av.open(str(dest)) as check:
                decoded=[Fraction(f.pts)*f.time_base for f in check.decode(video=0)]
            assert len(decoded)==len(mapping)
            assert all(t==Fraction(r['local_seconds_exact']) for t,r in zip(decoded,mapping))
            anchors=[]
            for k in (0,len(original)//2,len(original)-1):
                ordinal,pts,t,rgb=original[k];p=folder/f'original_anchor_{k:04d}.png';rgb.save(p)
                anchors.append({'ordinal':ordinal,'global_seconds_exact':str(t),'local_seconds_exact':mapping[k]['local_seconds_exact'],
                                'file':str(p),'sha256':sha(p)})
            actual_duration=Fraction(mapping[-1]['local_seconds_exact'])+Fraction(1,1)/rate
            bins=[]
            for k in range(15):
                members=[r for r in mapping if 2*k<=Fraction(r['local_seconds_exact'])<min(2*k+2,actual_duration)]
                assert members
                bins.append({'candidate_id':k,'local_start':2*k,'local_end_exclusive':min(2*k+2,float(actual_duration)),
                             'first_native_ordinal':members[0]['ordinal'],'last_native_ordinal':members[-1]['ordinal']})
            manifest={'source_id':sid,'source_group':m['source_group'],'split':'train','source_sha256':m['media_sha256'],
                      'clip_file':str(dest),'clip_sha256':sha(dest),'source_mapping':mapping,'candidates':bins,'anchors':anchors,
                      'duration_seconds':float(actual_duration),'no_audio':True,'derived_video_encoding':'libx264 crf18 yuv420p; all sequential source frames; unchanged geometry; native PTS exact; lossy pixels declared'}
            save(folder/'manifest.json',manifest);jobs.append(str(folder))
    save(H/'agy_v2/jobs.json',{'jobs':jobs,'expected':6,'train_only':True,'selected_without_labels':True})
def run():
    if not (H/'agy_v2/jobs.json').exists():prepare()
    jobs=json.loads((H/'agy_v2/jobs.json').read_text())['jobs'];receipts=[]
    for path in jobs:
        folder=Path(path);m=json.loads((folder/'manifest.json').read_text());out=folder/'labels.json'
        if (folder/'acceptance.json').exists():
            r=json.loads((folder/'acceptance.json').read_text());assert sha(out)==r['raw_sha256'];receipts.append(r);continue
        assert not out.exists() and not (folder/'stream.jsonl').exists(),'Partial attempt preserved; no automatic replay'
        task=f'''用户明确授权高光标注。只处理{m['source_id']}的这一个30秒派生短视频。先view_file原生读取{(folder/'manifest.json').as_posix()}，再view_file原生直接读{(folder/'clip.mp4').as_posix()}。
禁止终端/代码/外部API/浏览器/联网/其他模型或子代理；不要读取原人类评分、旧标签、PNG或其他视频。视频无音频。
这次只做固定候选格分类，不自由报起止秒。顶层source_id、input_sha256(clip的sha)、native_video_accepted、actual_tool_name、observation_scope、limitations、candidates。
必须按manifest的15个candidate_id依序逐条返回candidate_id、state(KEEP/REJECT/UNKNOWN)、visible_evidence、actually_observed_local_seconds(精确不了就空列表)、confidence(LOW/MEDIUM/HIGH)。KEEP意味着实际可见的重要动作、结果或叙事核心；REJECT仅用于实际观察到且明确冗余/过渡的格，不是把未观察当低分。抽样未覆盖、动作不清或边界无法定位就UNKNOWN。不要声称逐帧/完整连续观看。若工具只给概览而不能准确归属时间格，应全部UNKNOWN且解释，不能编造时间。
仅write_to_file写{out.as_posix()}，已存在不能覆盖。工具失败写{(folder/'failure.json').as_posix()}后停止。'''
        (folder/'prompt.txt').write_text(task,encoding='utf-8')
        cmd=[str(AGY),'--model',MODEL,'--mode','accept-edits','--sandbox','--output-format','stream-json','--log-file',str(folder/'agy.log'),'-p',task]
        with (folder/'stream.jsonl').open('xb') as stdout,(folder/'stderr.txt').open('xb') as stderr:
            r=subprocess.run(cmd,cwd=H,stdout=stdout,stderr=stderr)
        save(folder/'terminal.json',{'exit_code':r.returncode,'utc':datetime.now(timezone.utc).isoformat()})
        assert r.returncode==0 and out.exists()
        events=[json.loads(s) for s in (folder/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
        init=next(e['init'] for e in events if e.get('event')=='init');assert init['model']==MODEL
        result=next(e['result'] for e in reversed(events) if e.get('event')=='result');assert result['status']=='SUCCESS'
        calls=[e['step_update'] for e in events if e.get('step_update',{}).get('state')=='DONE' and e['step_update'].get('tool_name')=='view_file'
               and e['step_update'].get('tool_info',{}).get('parameters',{}).get('AbsolutePath','').replace('\\','/').endswith('/clip.mp4')]
        assert calls
        doc=json.loads(out.read_text(encoding='utf-8-sig'));assert doc['source_id']==m['source_id'] and doc['input_sha256']==m['clip_sha256']
        assert doc['native_video_accepted'] is True and doc['actual_tool_name']=='view_file'
        assert [x['candidate_id'] for x in doc['candidates']]==list(range(15))
        for x in doc['candidates']:
            assert x['state'] in ('KEEP','REJECT','UNKNOWN') and x['visible_evidence']
            for t in x['actually_observed_local_seconds']:assert type(t) in (int,float) and 0<=t<m['duration_seconds']
        receipt={'status':'NATIVE_CLIP_AND_SCHEMA_PASS_SEMANTIC_REVIEW_PENDING','source_id':m['source_id'],'folder':str(folder),
                 'raw_sha256':sha(out),'stream_sha256':sha(folder/'stream.jsonl'),'states':{s:sum(x['state']==s for x in doc['candidates']) for s in ('KEEP','REJECT','UNKNOWN')},
                 'full_observation_proven':False,'training_admitted':False,'conversation_id':result['conversation_id']}
        save(folder/'acceptance.json',receipt);receipts.append(receipt)
        (H/'agy_v2/progress.json').write_text(json.dumps({'done':len(receipts),'expected':6,'receipts':receipts},indent=2),encoding='utf-8')
        print(json.dumps(receipt),flush=True)
    save(H/'agy_v2/completion.json',{'status':'SIX_NATIVE_CLIP_TEACHER_RESPONSES_SEMANTIC_REVIEW_PENDING','receipts':receipts,'training_admitted':False})
if __name__=='__main__':run()

```


## 原文件全文：reports/annotation_iteration_20261010/quality_result.json
字节=635982；SHA256=33d2bed1dc542741ceb324ec036ba021e8aefc77e646c5773258baacdb55bbfb

```json
