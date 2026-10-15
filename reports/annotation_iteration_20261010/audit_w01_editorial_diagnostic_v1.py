"""Audit the new diagnostic's evidence supply and exact coverage, not label truth."""
from pathlib import Path
from fractions import Fraction
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parent/'w01_editorial_diagnostic_v1'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def exact(x): return Fraction(str(x))
def pair(x):
    # Same scientific values may be represented as a list or explicit start/end.
    return (exact(x['start']), exact(x['end'])) if isinstance(x,dict) else tuple(map(exact,x))
def check_doc(path, refs):
    issues=[]
    if not path.exists(): return dict(issues=['MISSING'],path=str(path))
    d=load(path)
    obs=d.get('frame_observations',[])
    if len(obs)!=64: issues.append('FRAME_COUNT')
    for r,ref in zip(obs,refs):
        if r.get('frame_id')!=ref['frame_id']: issues.append('FRAME_ID_ORDER')
        if r.get('source_ordinal')!=ref['source_ordinal']: issues.append('ORDINAL')
        try:
            if exact(r['local_seconds_exact'])!=exact(ref['local_seconds_exact']): issues.append('PTS')
        except (ValueError, KeyError, TypeError): issues.append('PTS_MISSING_OR_INVALID')
        if r.get('actual_view_image_read') is not True: issues.append('ACTUAL_READ_NOT_ATTESTED')
        if not r.get('visible_fact'): issues.append('VISIBLE_FACT_MISSING')
        if 'subtitle_text' not in r or 'subtitle_legibility' not in r: issues.append('SUBTITLE_OBSERVATION_MISSING')
    cov=d.get('window_coverage',[]);cursor=Fraction(0); totals={k:Fraction(0) for k in ('KEEP','NO','UNKNOWN')}
    for r in cov:
        try:
            a,b=exact(r['start']),exact(r['end']);label=r['label']
            if a!=cursor or b<=a or b>30 or label not in totals: issues.append('COVERAGE_GAP_OVERLAP_OR_DOMAIN')
            cursor=b
            if label in totals:totals[label]+=b-a
            if not r.get('evidence_frame_ids') or not r.get('visible_basis') or not r.get('editorial_reason'):issues.append('COVERAGE_BASIS_MISSING')
            if not r.get('candidate_id') or not r.get('narrative_unit_id'):issues.append('PRESEALED_IDENTITY_MISSING')
        except (ValueError,KeyError,TypeError):issues.append('COVERAGE_ROW_INVALID')
    if cursor!=30:issues.append('NOT_FULL_DOMAIN')
    if d.get('training_admitted') is not False:issues.append('UNAUTHORIZED_TRAINING_ADMISSION')
    events=d.get('events',[])
    event_units={e.get('narrative_unit_id') for e in events}
    if None in event_units:issues.append('EVENT_NARRATIVE_ID_MISSING')
    intervals=[]
    for e in events:
        try:
            a,b=pair(e['proposed_local_seconds'])
            if not 0<=a<b<=30:issues.append('EVENT_DOMAIN')
            intervals.append((a,b))
            for key in ('interval_merge_rationale','evidence_frame_ids','boundary_inside_frame_ids','start_uncertainty_range','end_uncertainty_range'):
                if key not in e:issues.append('EVENT_FIELD_MISSING:'+key)
        except (ValueError,KeyError,TypeError):issues.append('EVENT_INTERVAL_INVALID')
    intervals.sort(); union=[]
    for a,b in intervals:
        if union and a<=union[-1][1]:union[-1]=(union[-1][0],max(b,union[-1][1]))
        else:union.append((a,b))
    return dict(path=str(path),sha256=sha(path),issues=sorted(set(issues)),observation_rows=len(obs),
                coverage_rows=len(cov),coverage_seconds_exact={k:str(v) for k,v in totals.items()},
                proposed_event_rows=len(events),presealed_narrative_units=len(event_units),
                contiguous_KEEP_union_intervals=len(union),capacity_check_after_seal_only=True,
                satisfies_numeric_capacity_only=len(event_units)<=5 and len(union)<=5,
                semantic_correctness='NOT_CERTIFIED_BY_THIS_AUDIT',training_admitted=False)

if __name__=='__main__':
    t=ROOT/'teacher';assert (t/'terminal.json').exists(), 'unfinished stream must not be finalized'
    rows=[json.loads(s) for s in (t/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('state')=='DONE']
    st=load(ROOT/'student_index.json')['frames'];nt=load(ROOT/'native_index.json')['frames']
    student={str(Path(r['path']).resolve()):r['frame_id'] for r in st};native={str(Path(r['path']).resolve()):r['frame_id'] for r in nt}
    metadata={str((ROOT/n).resolve()) for n in ('student_index.json','native_index.json')}
    outputs={str((t/n).resolve()) for n in ('student_sealed.json','native_addendum.json','seal.json')}
    counts={};issues=[];student_write_at=[];native_read_at=[];successful=set()
    for i,c in enumerate(calls):
        info=c.get('tool_info',{});pars=info.get('parameters',{})
        if isinstance(pars,str):pars=json.loads(pars)
        value=pars.get('AbsolutePath') or pars.get('TargetFile');p=str(Path(value).resolve()) if value else None
        name=c.get('tool_name');out=info.get('output','')
        failed=any(k in str(out).lower() for k in ('not found','cannot read','failed to','error reading'))
        if name=='view_file':
            counts[p]=counts.get(p,0)+1
            if p not in set(student)|set(native)|metadata:issues.append(dict(reason='OUTSIDE_READ_WHITELIST',path=p))
            if failed:issues.append(dict(reason='REPORTED_READ_FAILURE',path=p))
            else:successful.add(p)
            if p in native:native_read_at.append(i)
        elif name=='write_to_file':
            if p not in outputs:issues.append(dict(reason='OUTSIDE_WRITE_WHITELIST',path=p))
            if p==str((t/'student_sealed.json').resolve()):student_write_at.append(i)
        else:issues.append(dict(reason='UNEXPECTED_TOOL',name=name,path=p))
    student_seal_precedes_native=bool(student_write_at and native_read_at and len(student_write_at)==1 and student_write_at[0]<min(native_read_at))
    if not student_seal_precedes_native:issues.append(dict(reason='STUDENT_SEAL_ORDER'))
    for p in set(student)|set(native):
        if counts.get(p,0)!=1:issues.append(dict(reason='MISSING_OR_REPEATED_PNG',path=p,count=counts.get(p,0)))
    result=next((r['result'] for r in reversed(rows) if r.get('event')=='result'),None)
    init=next((r['init'] for r in rows if r.get('event')=='init'),{})
    report=dict(status='DIAGNOSTIC_EVIDENCE_AUDIT_NOT_TRAINING_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),
        actual_model=init.get('model'),actual_result_status=result and result.get('status'),
        actual_result_usage=result and result.get('usage'),terminal=load(t/'terminal.json'),
        completed_tools=len(calls),student_PNGs_delivered=len(set(student)&successful),native_PNGs_delivered=len(set(native)&successful),
        student_seal_precedes_native=student_seal_precedes_native,tool_issues=issues,
        student=check_doc(t/'student_sealed.json',st),native=check_doc(t/'native_addendum.json',nt),
        stream_sha256=sha(t/'stream.jsonl'),cash_cost='UNKNOWN_NOT_ZERO',
        blinding='REQUIRES_SEAL_ATTESTATION_AND_INPUT_AUDIT_NOT_ASSUMED',new_optimizer_updates=0,new_426_calls=0)
    output_name=sys.argv[1] if len(sys.argv)>1 else 'audit.json'
    assert output_name in ('audit.json','audit_v2.json')
    if output_name=='audit_v2.json':
        report['prior_audit_sha256']=sha(t/'audit.json')
        report['prior_audit_representation_error_preserved']='event interval dict was incorrectly treated as iterable list; numeric values unchanged'
    with (t/output_name).open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('tool_issues','terminal')},ensure_ascii=False))
