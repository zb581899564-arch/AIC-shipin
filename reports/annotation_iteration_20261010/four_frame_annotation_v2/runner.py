"""Bounded AGY factual collection. No training, labels, or submission changes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'w01_editorial_diagnostic_v1'
AGY = Path('C:/Users/33056/AppData/Local/agy/bin/agy.exe')
MODEL = 'gemini-3.8-flash-high'
KEYS = {'frame_id', 'actual_image_read', 'visible_subject', 'subtitle_text', 'subtitle_legibility', 'uncertainties'}

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p, obj):
    """Exclusive creation: never replace a prior answer or receipt."""
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def index(phase):
    p = OLD / f'{phase}_index.json'
    doc = read(p)
    assert len(doc['frames']) == 64
    assert [r['frame_id'] for r in doc['frames']] == [f'F{i:02}' for i in range(64)]
    for row in doc['frames']:
        assert sha(row['path']) == row['png_sha256']
    return doc, sha(p)

def prepare():
    student, ss = index('student'); native, ns = index('native')
    assert student['source_sha256'] == native['source_sha256']
    assert [(r['frame_id'], r['source_ordinal'], r['local_seconds_exact']) for r in student['frames']] == [(r['frame_id'], r['source_ordinal'], r['local_seconds_exact']) for r in native['frames']]
    # Count real historical CLI receipts rather than resetting the total budget.
    prior = list((ROOT.parent/'slot6_silver24_v1').glob('**/terminal.json')) + list(OLD.glob('**/terminal.json'))
    prior = [p for p in prior if 'cpu_env' not in p.parts]
    save(ROOT/'protocol.json', dict(status='USER_AUTHORIZED_NEW_FACT_ENGINEERING_STAGE', utc=utc(),
        window_id=student['window_id'], role='previously_exposed_training_source_regression_not_blind',
        model=MODEL, student_index_sha256=ss, native_index_sha256=ns,
        historical_cli_receipts=[dict(path=str(p), sha256=sha(p)) for p in prior],
        historical_cli_count=len(prior), cumulative_cli_cap=36, new_cli_cap=10,
        hard_seconds_per_cli=420, recovery_cap=1, chunk_size=4, conversation_frame_cap=16,
        old_stop_preserved=True, training_admitted=False, new_optimizer_updates=0,
        new_426_calls=0, pro_used=6, pro_cap=8, cash_cost='UNKNOWN_NOT_ZERO',
        source_sha256=student['source_sha256'], source_files_unchanged=True,
        no_network_config_changes=True, output_schema=sorted(KEYS)))
    print('PREPARED', flush=True)

def audit(folder, phase, rows):
    """Use public tool metadata only. Do not extract private reasoning."""
    events=[]
    for line in (folder/'stream.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: pass
    tools=[]; usage=[]
    for e in events:
        s=e.get('step_update', {})
        if s.get('state')=='DONE' and s.get('step_type')=='tool':
            tools.append(dict(step=s['step_index'], name=s.get('tool_name'), parameters=s.get('tool_info',{}).get('parameters',{})))
        if s.get('usage'): usage.append(s['usage'])
    allowed_images={str(Path(r['path']).resolve()).casefold():r['frame_id'] for r in rows}
    viewed={}; errors=[]
    for t in tools:
        if t['name']=='view_file':
            p=t['parameters'].get('AbsolutePath','')
            k=str(Path(p).resolve()).casefold()
            if k not in allowed_images: errors.append('OUT_OF_SCOPE_IMAGE_READ:'+p)
            else: viewed.setdefault(allowed_images[k],[]).append(t['step'])
        elif t['name']=='write_to_file':
            p=Path(t['parameters'].get('TargetFile','')).resolve()
            if p.parent!=folder.resolve() or not p.name.startswith('facts_chunk_'):
                errors.append('OUT_OF_SCOPE_WRITE:'+str(p))
        elif t['name'] not in {'finish'}:
            errors.append('UNEXPECTED_TOOL:'+str(t['name']))
    accepted=[]
    for n in range(0,len(rows),4):
        target=folder/f'facts_chunk_{n//4:02}.json'
        group=rows[n:n+4]; expected=[r['frame_id'] for r in group]
        ce=[]
        if not target.exists(): ce.append('MISSING_FILE')
        else:
            try:
                answer=read(target)
                assert isinstance(answer,list) and len(answer)==len(group)
                assert [r['frame_id'] for r in answer]==expected
                write_steps=[t['step'] for t in tools if t['name']=='write_to_file' and Path(t['parameters'].get('TargetFile','')).resolve()==target.resolve()]
                assert len(write_steps)==1, 'MISSING_OR_REPEATED_WRITE'
                for fact, ref in zip(answer,group):
                    assert set(fact)==KEYS, 'SCHEMA'
                    assert fact['actual_image_read'] is True
                    assert isinstance(fact['visible_subject'],str) and fact['visible_subject'].strip()
                    assert fact['subtitle_text'] is None or isinstance(fact['subtitle_text'],str)
                    assert fact['subtitle_legibility'] in {'clear','partial','unreadable','absent'}
                    assert isinstance(fact['uncertainties'],list) and all(isinstance(x,str) for x in fact['uncertainties'])
                    assert len(viewed.get(ref['frame_id'],[]))==1, 'READ_NOT_UNIQUE'
                    assert viewed[ref['frame_id']][0]<write_steps[0], 'WRITE_BEFORE_READ'
                if n+4<len(rows):
                    later=rows[n+4:]
                    assert all(not viewed.get(r['frame_id']) or min(viewed[r['frame_id']])>write_steps[0] for r in later), 'NO_FOUR_IMAGE_SAVE_BARRIER'
                if not errors:
                    accepted.extend(dict(**fact, source_ordinal=ref['source_ordinal'],
                        local_seconds_exact=ref['local_seconds_exact'], png_sha256=ref['png_sha256'],
                        image_path=ref['path'], phase=phase, raw_file=str(target),raw_sha256=sha(target)) for fact,ref in zip(answer,group))
            except (AssertionError, ValueError, KeyError, TypeError) as exc: ce.append(str(exc) or type(exc).__name__)
        if ce: errors.append(dict(chunk=target.name, errors=ce))
    result=dict(utc=utc(), status='PASS_STRUCTURE_AND_PUBLIC_TOOL_READS' if not errors else 'FAIL_OR_PARTIAL',
        semantic_acceptance=False, planned_ids=[r['frame_id'] for r in rows], unique_reads=sorted(viewed),
        tools=tools, usage=usage, errors=errors, records=accepted, cash_cost='UNKNOWN_NOT_ZERO')
    save(folder/'audit.json',result)
    return result

def run(name, phase, ids):
    protocol=read(ROOT/'protocol.json')
    prior_requests=list(ROOT.glob('*/request.json'))
    assert len(prior_requests)<10
    assert protocol['historical_cli_count']+len(prior_requests)<36
    doc, index_sha=index(phase); rows=[r for r in doc['frames'] if r['frame_id'] in ids]
    assert len(rows)==len(ids) and 0<len(rows)<=16
    folder=ROOT/name; folder.mkdir(exist_ok=False)
    save(folder/'request.json',dict(utc=utc(), phase=phase,model=MODEL,frames=rows,index_sha256=index_sha,
        max_seconds=420, runner_sha256=sha(ROOT/'runner.py'), cli_ordinal=len(prior_requests)+1,cash_cost='UNKNOWN_NOT_ZERO', training_admitted=False))
    batches=[]
    for n in range(0,len(rows),4):
        batches.append(dict(output=(folder/f'facts_chunk_{n//4:02}.json').as_posix(),
            images=[dict(frame_id=r['frame_id'],path=Path(r['path']).as_posix()) for r in rows[n:n+4]]))
    prompt='''你执行逐帧可见事实记录，不做高光选择或训练标签。只允许 view_file 读取下列 PNG，每图恰好一次；只允许 write_to_file 新建指定 JSON 文件。禁止读取其他文件、旧答案、目录、终端、代码、联网、浏览器、子任务。自动提供的项目上下文不是图片事实证据。
严格逐批：读取第一批最多四张，立刻写该批文件，完成写入后才读下一批。每批输出 JSON 数组，按列出次序；每行必须恰好包含 frame_id, actual_image_read(bool), visible_subject(简洁客观中文), subtitle_text(逐字转录，不翻译；无字幕null；不清晰处用[unclear]), subtitle_legibility(clear/partial/unreadable/absent), uncertainties(字符串数组)。不要添加时间、序号、SHA。不要依据单帧声称动作经过、动机、情绪或画外音。不知道就记录，不猜测。不要跨图复制字幕；尤其在镜头变化后逐图检查。不能读取就不要造完成记录。最后仅确认文件路径。
实际任务批次：\n'''+json.dumps(batches,ensure_ascii=False,indent=2)
    (folder/'prompt.txt').write_text(prompt,encoding='utf-8')
    env=os.environ.copy(); env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=1')
    cmd=[str(AGY),'--model',MODEL,'--mode','accept-edits','--sandbox','--print-timeout','7m','--output-format','stream-json','--log-file',str(folder/'agy.log'),'-p',prompt]
    tic=time.monotonic(); started=utc(); timed_out=False
    with (folder/'stream.jsonl').open('xb') as stdout,(folder/'stderr.txt').open('xb') as stderr:
        p=subprocess.Popen(cmd,cwd=folder,env=env,stdout=stdout,stderr=stderr)
        save(folder/'owned_process.json',dict(pid=p.pid,command=cmd,started_utc=started))
        # Reserve five seconds for termination within the 420-second total.
        try: p.wait(timeout=max(0,415-(time.monotonic()-tic)))
        except subprocess.TimeoutExpired:
            timed_out=True; p.terminate()
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill();p.wait()
    save(folder/'terminal.json',dict(started_utc=started,finished_utc=utc(),elapsed_seconds=time.monotonic()-tic,
        exit_code=p.returncode,hard_deadline_exceeded=timed_out,exit_zero_not_acceptance=True,cash_cost='UNKNOWN_NOT_ZERO',
        stream_sha256=sha(folder/'stream.jsonl')))
    result=audit(folder,phase,rows)
    print(json.dumps(dict(name=name,status=result['status'],accepted_rows=len(result['records']),errors=result['errors']),ensure_ascii=False),flush=True)
    return result

def student():
    review=read(ROOT/'pilot_semantic_review.json')
    assert review['accepted'] is True and review['audit_sha256']==sha(ROOT/'pilot/audit.json')
    for block in range(4):
        ids=[f'F{i:02}' for i in range(block*16,(block+1)*16) if i not in range(36,40)]
        result=run(f'student_block_{block:02}', 'student', ids)
        if result['errors']: return

def seal(phase):
    records=[]
    paths=list(ROOT.glob(f'{phase}_block_*/audit.json'))
    if phase=='student': paths.append(ROOT/'pilot/audit.json')
    if (ROOT/'recovery_admission.json').exists():
        recovery=read(ROOT/'recovery_admission.json')
        if recovery['phase']==phase: paths.append(ROOT/recovery['recovery_name']/'audit.json')
    for path in paths:
        audit_doc=read(path)
        if audit_doc['errors']:
            # Keep the failure bound to the review; only explicit missing-only
            # recovery can supply its rows. Never change the original receipt.
            assert (ROOT/'recovery_admission.json').exists()
            assert path.parent.name==recovery['failed_name']
        records.extend(audit_doc['records'])
    records.sort(key=lambda r:r['frame_id'])
    assert [r['frame_id'] for r in records]==[f'F{i:02}' for i in range(64)]
    review=read(ROOT/f'{phase}_semantic_review.json')
    assert review['accepted'] and review['reviewed_frame_ids']==[r['frame_id'] for r in records]
    assert review['audit_sha256s']=={str(p.relative_to(ROOT)):sha(p) for p in paths}
    by_id={r['frame_id']:r for r in records}
    for correction in review.get('corrections',[]):
        row=by_id[correction['frame_id']];field=correction['field']
        assert field in {'visible_subject','subtitle_text','subtitle_legibility','uncertainties'}
        row.setdefault('model_original_fields',{})[field]=row[field]
        row[field]=correction['corrected']
        row.setdefault('root_corrections',[]).append(correction)
    save(ROOT/f'{phase}_sealed.json',dict(utc=utc(),phase=phase,records=records,training_admitted=False,
        semantic_review_sha256=sha(ROOT/f'{phase}_semantic_review.json')))
    print('SEALED',phase,flush=True)

def native():
    assert (ROOT/'student_sealed.json').exists()
    save(ROOT/'native_admission.json',dict(utc=utc(),student_seal_sha256=sha(ROOT/'student_sealed.json')))
    for block in range(4):
        result=run(f'native_block_{block:02}', 'native',[f'F{i:02}' for i in range(block*16,(block+1)*16)])
        if result['errors']: return

def recover(failed_name):
    assert not (ROOT/'recovery_admission.json').exists(), 'RECOVERY_BUDGET_EXHAUSTED'
    failed=ROOT/failed_name;request=read(failed/'request.json');previous=read(failed/'audit.json')
    assert previous['errors']
    accepted={x['frame_id'] for x in previous['records']}
    ids=[x['frame_id'] for x in request['frames'] if x['frame_id'] not in accepted]
    assert ids, 'NO_MISSING_ROWS'
    name='recovery_'+failed_name
    save(ROOT/'recovery_admission.json',dict(utc=utc(),phase=request['phase'],failed_name=failed_name,
        failed_audit_sha256=sha(failed/'audit.json'),recovery_name=name,only_missing_frame_ids=ids,
        old_successes_not_repeated=True,readonly_transport_probe='Unauthenticated HEAD through existing localhost:7892; response inspected by main agent; no config changes'))
    run(name,request['phase'],ids)

if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare':prepare()
    elif command=='pilot':run('pilot','student',[f'F{i:02}' for i in range(36,40)])
    elif command=='student':student()
    elif command=='native':native()
    elif command=='seal':seal(sys.argv[2])
    elif command=='recover':recover(sys.argv[2])
    else:raise ValueError(command)
