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
