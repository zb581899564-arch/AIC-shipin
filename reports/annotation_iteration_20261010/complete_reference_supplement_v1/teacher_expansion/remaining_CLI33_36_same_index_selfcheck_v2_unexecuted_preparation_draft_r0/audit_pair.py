from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction
import json,hashlib,sys
from supply_policy import index_selfchecks,classify_nonmedia_errors
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):return str(Path(p).resolve()).casefold()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def audit(no):
    a=ROOT/f'call{no:02d}';idx=read(a/'index.json');fr=read(a/'freeze.json');t=read(a/'terminal.json');issues=[]
    for p,s in fr['inputs'].items():
        if sha(p)!=s:issues.append(dict(reason='INPUT_SHA_DRIFT',path=p))
    assert sha(a/'stream.jsonl')==t['stream_sha256']
    rows=[json.loads(s) for s in (a/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    steps=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
    all_tool_updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool']
    done_step_ids={s.get('step_index') for s in steps}
    last_tool_updates={s.get('step_index'):s for s in all_tool_updates}
    errored_attempts=[s for s in last_tool_updates.values() if s.get('state')=='ERROR']
    unfinished_attempts=[s for s in last_tool_updates.values() if s.get('state')=='ACTIVE']
    def owner_job(path):
        for w in idx['windows']:
            if path.startswith(key(Path(w['clip_path']).parent)+'\\') or path.startswith(key(Path(w['clip_path']).parent)+'/'):
                return w['job_index']
        return None
    allowed_reads={key(p) for p in fr['read_whitelist']}|{key(p) for p in fr['self_read_whitelist']}
    for s in errored_attempts:
        p=s.get('tool_info',{}).get('parameters',{});path=key(p.get('AbsolutePath') or p.get('TargetFile'))
        issues.append(dict(reason='TOOL_ERROR_TERMINAL',step=s.get('step_index'),tool=s.get('tool_name'),path=path,job_index=owner_job(path)))
    for s in all_tool_updates:
        if s.get('state')!='ACTIVE' or s.get('tool_name')!='view_file':continue
        p=s.get('tool_info',{}).get('parameters',{});path=key(p.get('AbsolutePath'))
        if path not in allowed_reads:issues.append(dict(reason='OUTSIDE_READ_WHITELIST_ATTEMPT',step=s.get('step_index'),path=path,job_index=owner_job(path)))
    steps,index_checks=index_selfchecks(steps,a/'index.json')
    # Exact model supply contract. Optional one self-read may occur after its write.
    expected=[('view_file',key(a/'index.json'))];outputs={};selfcounts={};actual=[];supply=[]
    for w in idx['windows']:
        for g in w['groups']:
            expected += [('view_file',key(f['path'])) for f in g['frames']]
            expected += [('write_to_file',key(g['output_path']))]
            outputs[key(g['output_path'])]=g['output_path']
        expected += [('view_file',key(w['clip_path']))]
        expected += [('view_file',key(f['path'])) for f in w['student_previews']]
        expected += [('write_to_file',key(w['proposal_path']))];outputs[key(w['proposal_path'])]=w['proposal_path']
    written=set()
    for c in steps:
        info=c.get('tool_info',{});p=info.get('parameters',{});name=c.get('tool_name');rawpath=p.get('AbsolutePath') or p.get('TargetFile');path=key(rawpath) if rawpath else None
        output=str(info.get('output','')).lower()
        if any(x in output for x in ('not found','cannot read','error reading','failed to')):issues.append(dict(reason='TOOL_FAILURE',step=c.get('step_index'),path=path))
        if name=='view_file' and path in written:
            selfcounts[path]=selfcounts.get(path,0)+1
            if selfcounts[path]>1:issues.append(dict(reason='SELF_READ_REPEAT',path=path))
        else:
            actual.append((name,path))
            if name=='write_to_file':
                if path in written:issues.append(dict(reason='OUTPUT_OVERWRITE',path=path))
                if path not in outputs:issues.append(dict(reason='OUTSIDE_WRITE_WHITELIST',path=path))
                written.add(path)
        supply.append(dict(step=c.get('step_index'),tool=name,path=path))
    if actual!=expected:
        mismatches=[dict(index=i,expected=e,actual=actual[i] if i<len(actual) else None) for i,e in enumerate(expected) if i>=len(actual) or actual[i]!=e]
        issues.append(dict(reason='SUPPLY_ORDER_BARRIER_OR_WHITELIST',expected_count=len(expected),actual_count=len(actual),first_mismatches=mismatches[:15]))
    result=next((r.get('result',{}) for r in reversed(rows) if r.get('event')=='result'),{})
    wins=[];window_expected_offset=1
    for w in idx['windows']:
        schema=[];bound=[]
        for g in w['groups']:
            p=Path(g['output_path'])
            try:
                doc=read(p);assert set(doc)=={'group','items'} and doc['group']==g['group'];assert len(doc['items'])==4
                assert [r['slot'] for r in doc['items']]==[0,1,2,3]
                for item,f in zip(doc['items'],g['frames']):
                    assert set(item)=={'slot','subject','composition','subtitle_visible','subtitle_text','visible_fact'}
                    assert all(isinstance(item[k],str) and item[k].strip() for k in ('subject','composition','visible_fact'))
                    assert type(item['subtitle_visible']) is bool or item['subtitle_visible']=='UNKNOWN'
                    if item['subtitle_visible'] is False:assert item['subtitle_text'] is None
                    else:assert isinstance(item['subtitle_text'],str) and item['subtitle_text']
                    bound.append(dict(group=g['group'],slot=item['slot'],frame_id=f['frame_id'],source_ordinal=f['source_ordinal'],local_seconds_exact=f['local_seconds_exact'],global_seconds_exact=f['global_seconds_exact'],png_sha256=f['png_sha256'],geometry=f['geometry'],facts=item,raw_output_sha256=sha(p),identity_generated_by_program=True))
            except Exception as e:schema.append(dict(reason='FACT_SCHEMA_OR_MISSING',group=g['group'],error=repr(e)))
        prop=w['proposal_path'];proposalissues=[]
        try:
            d=read(prop);assert set(d)=={'segments','events','student_visibility','limitations'}
            assert isinstance(d['events'],list) and isinstance(d['segments'],list) and d['segments']
            end=Fraction(w['domain_local_seconds'][1]);cursor=Fraction(0)
            for s in d['segments']:
                assert set(s)=={'decision','start_seconds','end_seconds','reason','fact_support','start_uncertainty_range_seconds','end_uncertainty_range_seconds'}
                assert s['decision'] in ('KEEP','NO','UNKNOWN') and s['reason'] and isinstance(s['fact_support'],list)
                lo=Fraction(str(s['start_seconds']));hi=Fraction(str(s['end_seconds']));assert lo==cursor and lo<hi<=end;cursor=hi
                for k in ('start_uncertainty_range_seconds','end_uncertainty_range_seconds'):
                    z=s[k];assert len(z)==2 and 0<=Fraction(str(z[0]))<=Fraction(str(z[1]))<=end
                for f in s['fact_support']:assert set(f)=={'group','slot'} and f['group'] in range(16) and f['slot'] in range(4)
            assert cursor==end
            for e in d['events']:
                assert set(e)=={'description','decision','start_seconds','end_seconds','fact_support','boundary_reason'}
                assert e['decision'] in ('KEEP','NO','UNKNOWN') and e['description'] and e['boundary_reason']
        except Exception as e:proposalissues.append(dict(reason='PROPOSAL_SCHEMA_OR_COVERAGE',error=repr(e)))
        boundpath=a/f"w{w['job_index']:02d}_program_bound_facts.json"
        save(boundpath,dict(status='PROGRAM_IDENTITY_BINDING_ONLY_NOT_LABEL_ADMISSION',window_id=w['window_id'],rows=bound,training_admitted=False))
        windowpaths={key(f['path']) for g in w['groups'] for f in g['frames']}|{key(w['clip_path'])}|{key(f['path']) for f in w['student_previews']}|{key(g['output_path']) for g in w['groups']}|{key(prop)}
        window_expected_count=16*5+1+8+1
        local_supply_complete=actual[window_expected_offset:window_expected_offset+window_expected_count]==expected[window_expected_offset:window_expected_offset+window_expected_count]
        global_disallowed=[i for i in issues if i['reason'] not in ('SUPPLY_ORDER_BARRIER_OR_WHITELIST',) and i.get('job_index') in (None,w['job_index'])]
        # A legal complete first window is not relabeled incomplete solely because the second ran out of time.
        lawful_complete=local_supply_complete and actual[:1]==expected[:1] and not global_disallowed and not schema and not proposalissues and len(bound)==64
        wins.append(dict(job_index=w['job_index'],window_id=w['window_id'],status='PASS_TOOL_STRUCTURE_PENDING_SEMANTIC_REVIEW' if lawful_complete else 'REJECTED_OR_INCOMPLETE_KEEP_RAW',
          window_tool_sequence_complete=local_supply_complete,CLI_terminal_exit_code=t['exit_code'],
          completed_fact_groups=sorted({r['group'] for r in bound}),
          native_read_done=[dict(frame_id=f['frame_id'],path=f['path'],tool_steps=[s['step'] for s in supply if s['tool']=='view_file' and s['path']==key(f['path'])]) for g in w['groups'] for f in g['frames'] if any(s['tool']=='view_file' and s['path']==key(f['path']) for s in supply)],
          clip_read_done=any(s['tool']=='view_file' and s['path']==key(w['clip_path']) for s in supply),
          student_preview_read_done=[dict(frame_id=f['frame_id'],path=f['path']) for f in w['student_previews'] if any(s['tool']=='view_file' and s['path']==key(f['path']) for s in supply)],
          bound_rows=len(bound),schema_issues=schema,proposal_issues=proposalissues,proposal_sha256=sha(prop) if Path(prop).exists() else None,
          program_bound_facts_sha256=sha(boundpath),actual_supply=[s for s in supply if s['path'] in windowpaths],native_geometry=[f['geometry'] for g in w['groups'] for f in g['frames']],student_geometry=[f['geometry'] for f in w['student_previews']],
          semantic_correctness='UNVERIFIED_PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW',training_admitted=False))
        window_expected_offset+=window_expected_count
    nonmedia_steps=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message']
    bare_metadata,reported_errors=classify_nonmedia_errors(nonmedia_steps)
    out=dict(utc=datetime.now(timezone.utc).isoformat(),call=no,windows=wins,tool_issues=issues,index_selfchecks=index_checks,bare_nonmedia_error_metadata=bare_metadata,reported_nonmedia_errors=reported_errors,self_reads=selfcounts,errored_tool_attempts=errored_attempts,unfinished_tool_attempts=unfinished_attempts,teacher_task_completed=(not issues and not errored_attempts and not unfinished_attempts and all(w['status']=='PASS_TOOL_STRUCTURE_PENDING_SEMANTIC_REVIEW' for w in wins)),AGY_result_SUCCESS_does_not_override_missing_or_ERROR_tools=True,error_message_steps=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message'],expected_tool_calls=len(expected),actual_nonself_tool_calls=len(actual),actual_result_status=result.get('status'),actual_result_error=result.get('error'),actual_result_usage=result.get('usage'),
      terminal_sha256=sha(a/'terminal.json'),stream_sha256=sha(a/'stream.jsonl'),freeze_sha256=sha(a/'freeze.json'),CLI_after=fr['CLI_after'],cash_cost='UNKNOWN_NOT_ZERO',automatic_retry=False,new_model_training=0)
    save(a/'audit.json',out);print(json.dumps(dict(call=no,windows=[dict(job_index=w['job_index'],status=w['status'],bound_rows=w['bound_rows'],proposal_issues=w['proposal_issues']) for w in wins],tool_issues=issues,CLI_after=fr['CLI_after']),ensure_ascii=False),flush=True)
if __name__=='__main__':audit(int(sys.argv[1]))
