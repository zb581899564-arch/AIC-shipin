"""Immutable actual stream prefix audit; no final CLI or semantic admission claim."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import json, hashlib, sys
from supply_policy import index_selfchecks
ROOT=Path(__file__).resolve().parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(b): return hashlib.sha256(b).hexdigest()
def sha(p): return digest(Path(p).read_bytes())
def key(p): return str(Path(p).resolve()).casefold()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2)
def main(no, job):
    a=ROOT/f'call{no:02d}'; idx=read(a/'index.json'); fr=read(a/'freeze.json')
    w=next(w for w in idx['windows'] if w['job_index']==job)
    assert w is idx['windows'][0], 'Only complete first scope is supported'
    issues=[]
    for p,s in fr['inputs'].items():
        if sha(p)!=s: issues.append({'reason':'INPUT_SHA_DRIFT','path':p})
    raw=(a/'stream.jsonl').read_bytes(); valid=[]; cutoff=None; upto=0
    for line in raw.splitlines(keepends=True):
        upto+=len(line)
        try: r=json.loads(line)
        except (json.JSONDecodeError,UnicodeDecodeError): break
        valid.append(r)
        t=r.get('step_update',{})
        if t.get('state')=='DONE' and t.get('step_type')=='tool' and t.get('tool_name')=='write_to_file' and key(t.get('tool_info',{}).get('parameters',{}).get('TargetFile',''))==key(w['proposal_path']):
            cutoff=upto; break
    assert cutoff is not None, 'No actual DONE proposal write'
    prefix=raw[:cutoff]; snap=a/f'w{job:02d}_completed_scope_stream_prefix.jsonl'
    with snap.open('xb') as f:f.write(prefix)
    all_prefix_tools=[r['step_update'] for r in valid if r.get('step_update',{}).get('step_type')=='tool']
    latest_prefix_tools={t['step_index']:t for t in all_prefix_tools}
    allowed_read_paths={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']}
    for t in latest_prefix_tools.values():
        if t.get('state') in ('ERROR','ACTIVE'):issues.append(dict(reason='PREFIX_TOOL_ERROR_OR_UNFINISHED',step=t['step_index'],actual_state=t.get('state')))
        if t.get('tool_name') not in ('view_file','write_to_file'):issues.append(dict(reason='PREFIX_ILLEGAL_TOOL',step=t['step_index']))
    for t in all_prefix_tools:
        if t.get('tool_name')=='view_file' and key(t.get('tool_info',{}).get('parameters',{}).get('AbsolutePath','')) not in allowed_read_paths:issues.append(dict(reason='PREFIX_OUTSIDE_READ_WHITELIST_ATTEMPT',step=t['step_index']))
    steps=[r['step_update'] for r in valid if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
    steps,index_checks=index_selfchecks(steps,a/'index.json')
    expected=[('view_file',key(a/'index.json'))]; outputpaths=set()
    for g in w['groups']:
        expected.extend(('view_file',key(f['path'])) for f in g['frames'])
        expected.append(('write_to_file',key(g['output_path']))); outputpaths.add(key(g['output_path']))
    expected.append(('view_file',key(w['clip_path'])))
    expected.extend(('view_file',key(f['path'])) for f in w['student_previews'])
    expected.append(('write_to_file',key(w['proposal_path']))); outputpaths.add(key(w['proposal_path']))
    actual=[]; written=set(); selfcounts={}; supply=[]
    for t in steps:
        info=t.get('tool_info',{}); p=info.get('parameters',{}); name=t.get('tool_name'); path=key(p.get('AbsolutePath') or p.get('TargetFile'))
        if any(x in str(info.get('output','')).lower() for x in ('not found','cannot read','error reading','failed to')):issues.append({'reason':'TOOL_FAILURE','step':t['step_index']})
        if name=='view_file' and path in written:
            selfcounts[path]=selfcounts.get(path,0)+1
            if selfcounts[path]>1:issues.append({'reason':'SELF_READ_REPEAT','path':path})
        else:
            actual.append((name,path))
            if name=='write_to_file':
                if path in written or path not in outputpaths:issues.append({'reason':'ILLEGAL_WRITE','path':path})
                written.add(path)
        supply.append({'step':t['step_index'],'tool':name,'path':path})
    if actual!=expected:issues.append({'reason':'SUPPLY_ORDER_BARRIER_OR_WHITELIST','expected_count':len(expected),'actual_count':len(actual)})
    bound=[]
    for g in w['groups']:
        p=Path(g['output_path']); d=read(p)
        assert set(d)=={'group','items'} and d['group']==g['group'] and len(d['items'])==4
        assert [x['slot'] for x in d['items']]==[0,1,2,3]
        for item,f in zip(d['items'],g['frames']):
            assert set(item)=={'slot','subject','composition','subtitle_visible','subtitle_text','visible_fact'}
            assert all(isinstance(item[k],str) and item[k].strip() for k in ('subject','composition','visible_fact'))
            assert type(item['subtitle_visible']) is bool or item['subtitle_visible']=='UNKNOWN'
            if item['subtitle_visible'] is False:assert item['subtitle_text'] is None
            else:assert isinstance(item['subtitle_text'],str) and item['subtitle_text']
            assert sha(f['path'])==f['png_sha256']
            bound.append(dict(group=g['group'],slot=item['slot'],frame_id=f['frame_id'],source_ordinal=f['source_ordinal'],local_seconds_exact=f['local_seconds_exact'],global_seconds_exact=f['global_seconds_exact'],png_sha256=f['png_sha256'],geometry=f['geometry'],facts=item,raw_output_sha256=sha(p),identity_generated_by_program=True))
    prop=read(w['proposal_path']); assert set(prop)=={'segments','events','student_visibility','limitations'}
    assert isinstance(prop['events'],list) and isinstance(prop['segments'],list) and prop['segments']
    end=Fraction(w['domain_local_seconds'][1]); cursor=Fraction(0)
    for s in prop['segments']:
        assert set(s)=={'decision','start_seconds','end_seconds','reason','fact_support','start_uncertainty_range_seconds','end_uncertainty_range_seconds'}
        assert s['decision'] in ('KEEP','NO','UNKNOWN') and s['reason'] and isinstance(s['fact_support'],list)
        lo=Fraction(str(s['start_seconds']));hi=Fraction(str(s['end_seconds']));assert lo==cursor and lo<hi<=end;cursor=hi
        for k in ('start_uncertainty_range_seconds','end_uncertainty_range_seconds'):
            z=s[k];assert len(z)==2 and 0<=Fraction(str(z[0]))<=Fraction(str(z[1]))<=end
        for f in s['fact_support']:assert set(f)=={'group','slot'} and f['group'] in range(16) and f['slot'] in range(4)
    assert cursor==end
    for e in prop['events']:
        assert set(e)=={'description','decision','start_seconds','end_seconds','fact_support','boundary_reason'}
        assert e['decision'] in ('KEEP','NO','UNKNOWN') and e['description'] and e['boundary_reason']
    bp=a/f'w{job:02d}_program_bound_facts_completed_scope.json'
    save(bp,dict(status='PROGRAM_IDENTITY_BINDING_ONLY_NOT_LABEL_ADMISSION',window_id=w['window_id'],rows=bound,training_admitted=False))
    errors=[r['step_update'] for r in valid if r.get('step_update',{}).get('step_type')=='error_message']
    receipt=dict(status='PASS_ACTUAL_COMPLETED_SCOPE_TOOL_STRUCTURE_PENDING_ROOT_REVIEW' if not issues else 'REJECTED_SCOPE_KEEP_RAW',utc=datetime.now(timezone.utc).isoformat(),job_index=job,window_id=w['window_id'],global_CLI=26+no,parent_CLI_terminal_present=(a/'terminal.json').exists(),parent_stream_is_active_snapshot=True,issues=issues,actual_supply=supply,index_selfchecks=index_checks,native_read_done=64,clip_read_done=1,student_preview_read_done=8,fact_groups=16,bound_rows=len(bound),self_read_counts=selfcounts,error_message_steps=errors,proposal={'path':w['proposal_path'],'sha256':sha(w['proposal_path'])},program_bound_facts={'path':str(bp),'sha256':sha(bp)},stream_prefix={'path':str(snap),'sha256':sha(snap),'bytes':len(prefix)},active_stream_at_read={'path':str(a/'stream.jsonl'),'sha256':digest(raw),'bytes':len(raw)},freeze={'path':str(a/'freeze.json'),'sha256':sha(a/'freeze.json')},index={'path':str(a/'index.json'),'sha256':sha(a/'index.json')},request={'path':str(a/'request.json'),'sha256':sha(a/'request.json')},native_geometry=[f['geometry'] for g in w['groups'] for f in g['frames']],student_geometry=[f['geometry'] for f in w['student_previews']],semantic_correctness='UNVERIFIED_PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW',training_admitted=False)
    out=a/f'w{job:02d}_completed_scope_audit.json';save(out,receipt)
    print(json.dumps({'audit_path':str(out),'audit_sha256':sha(out),'status':receipt['status'],'proposal':receipt['proposal'],'prefix':receipt['stream_prefix']},ensure_ascii=False))
if __name__=='__main__':main(int(sys.argv[1]),int(sys.argv[2]))
