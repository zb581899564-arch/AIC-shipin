"""Read-only checks of sealed proposals. Geometry is not editorial ground truth."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
from collections import Counter
import json, hashlib, zipfile

BASE=Path(__file__).resolve().parent
ROOT=BASE/'w01_editorial_diagnostic_v1'
T=ROOT/'teacher'
REC=T/'engineering_recovery_v4_http2'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def fraction(x):return F(str(x))
def intervals(x):
    if isinstance(x,dict):return [(fraction(x['start']),fraction(x['end']))]
    if len(x)==2 and all(not isinstance(v,(list,dict)) for v in x):return [tuple(map(fraction,x))]
    return [p for v in x for p in intervals(v)]
def union(xs):
    out=[]
    for a,b in sorted(xs):
        if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
        else:out.append((a,b))
    return out
def printable(xs):return [[str(a),str(b)] for a,b in xs]

def doc_audit(path,refs):
    d=load(path); issues=[]; ids={r['frame_id'] for r in refs}
    observations=d.get('frame_observations',[])
    if len(observations)!=64:issues.append('OBSERVATION_COUNT')
    for o,r in zip(observations,refs):
        if (o.get('frame_id'),o.get('source_ordinal'),fraction(o.get('local_seconds_exact',-1))) != (r['frame_id'],r['source_ordinal'],fraction(r['local_seconds_exact'])):issues.append('OBSERVATION_IDENTITY')
        if o.get('actual_view_image_read') is not True or not o.get('visible_fact') or 'subtitle_text' not in o or 'subtitle_legibility' not in o:issues.append('OBSERVATION_FIELDS')
    cov=d.get('window_coverage',[]);cursor=F(0);totals={k:F(0) for k in ('KEEP','NO','UNKNOWN')}; keep=[]
    for row in cov:
        a,b=fraction(row['start']),fraction(row['end']);lab=row['label']
        if a!=cursor or not 0<=a<b<=30 or lab not in totals:issues.append('COVERAGE_DOMAIN')
        cursor=b;totals[lab]+=b-a
        if lab=='KEEP':
            keep.append((a,b))
            if not row.get('candidate_id') or not row.get('narrative_unit_id'):issues.append('KEEP_IDENTITY')
        if not row.get('evidence_frame_ids') or not row.get('visible_basis') or not row.get('editorial_reason'):issues.append('COVERAGE_EVIDENCE')
        if not set(row.get('evidence_frame_ids',[]))<=ids:issues.append('UNKNOWN_FRAME_ID')
    if cursor!=30:issues.append('COVERAGE_INCOMPLETE')
    events=d.get('events',[]); units={e.get('narrative_unit_id') for e in events}; xs=[]
    for event in events:
        pieces=intervals(event['proposed_local_seconds']);xs+=pieces
        if any(not 0<=a<b<=30 for a,b in pieces):issues.append('EVENT_DOMAIN')
        for key in ('interval_merge_rationale','evidence_frame_ids','boundary_inside_frame_ids','start_uncertainty_range','end_uncertainty_range'):
            if not event.get(key):issues.append('EVENT_FIELD:'+key)
    if union(xs)!=union(keep):issues.append('EVENT_COVERAGE_KEEP_MISMATCH')
    if None in units:issues.append('EVENT_IDENTITY')
    if d.get('training_admitted') is not False:issues.append('UNAUTHORIZED_ADMISSION')
    return dict(path=str(path),sha256=sha(path),geometry_issues=sorted(set(issues)),observation_rows=len(observations),coverage_rows=len(cov),
        coverage_seconds_exact={k:str(v) for k,v in totals.items()},event_rows=len(events),presealed_narrative_units=len(units),
        individual_event_intervals=len(xs),contiguous_KEEP_intervals=len(union(keep)),KEEP_union_exact=printable(union(keep)),
        numeric_five_units_and_five_intervals_pass=len(units)<=5 and len(union(keep))<=5,
        semantic_correctness='NOT_CERTIFIED_BY_GEOMETRY',training_admitted=False)

if __name__=='__main__':
    assert (REC/'terminal.json').exists() and (T/'seal.json').exists(),'Wait for owned continuation; never infer completion from exit zero.'
    st=load(ROOT/'student_index.json')['frames'];nt=load(ROOT/'native_index.json')['frames']
    paths={str(Path(r['path']).resolve()):r['frame_id'] for r in st+nt}
    student_paths={str(Path(r['path']).resolve()) for r in st};native_paths={str(Path(r['path']).resolve()) for r in nt}
    meta={str((ROOT/n).resolve()) for n in ('student_index.json','native_index.json')}
    outputs={str((T/n).resolve()) for n in ('student_sealed.json','native_addendum.json','seal.json')}
    allcalls=[]; stream_records=[]
    for folder in (T,T/'engineering_recovery_v2',T/'engineering_recovery_v3_transport_retry',REC):
        records=[json.loads(s) for s in (folder/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
        calls=[r['step_update'] for r in records if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('state')=='DONE']
        result=next((r['result'] for r in reversed(records) if r.get('event')=='result'),None)
        stream_records.append(dict(folder=str(folder),sha256=sha(folder/'stream.jsonl'),completed_tools=len(calls),terminal=load(folder/'terminal.json'),result=result))
        allcalls+=calls
    counts=Counter();tools_issues=[];writes=[];native_reads=[]
    for i,c in enumerate(allcalls):
        pars=c.get('tool_info',{}).get('parameters',{});pars=json.loads(pars) if isinstance(pars,str) else pars
        raw=pars.get('AbsolutePath') or pars.get('TargetFile');p=str(Path(raw).resolve()) if raw else None
        name=c.get('tool_name')
        if name=='view_file':
            counts[p]+=1
            if p not in set(paths)|meta:tools_issues.append(dict(reason='OUTSIDE_READ_WHITELIST',path=p))
            if p in native_paths:native_reads.append(i)
        elif name=='write_to_file':
            if p not in outputs:tools_issues.append(dict(reason='OUTSIDE_WRITE_WHITELIST',path=p))
            if p==str((T/'student_sealed.json').resolve()):writes.append(i)
        else:tools_issues.append(dict(reason='UNEXPECTED_TOOL',name=name,path=p))
    for p in paths:
        if counts[p]!=1:tools_issues.append(dict(reason='MISSING_OR_REPEATED_PNG',path=p,count=counts[p]))
    order=len(writes)==1 and native_reads and writes[0]<min(native_reads)
    if not order:tools_issues.append(dict(reason='STUDENT_SEAL_ORDER'))
    docs={side:{phase:doc_audit(ROOT/side/name,st if phase=='student' else nt) for phase,name in [('student','student_sealed.json'),('native','native_addendum.json')]} for side in ('teacher','independent')}
    preserved={'teacher':sha(T/'student_sealed.json')=='5d65c300cf99c060b00544afa4b2089743e7cacef60a1931dba60adf369539cd',
        'independent':sha(ROOT/'independent/student_sealed.json')=='b4e17a27622db8bde3cef6a38b170d1fe4fe8e6ea6969cbab9a32392cdf7a45d'}
    labels={side:load(ROOT/side/'student_sealed.json')['window_coverage'] for side in ('teacher','independent')}
    cuts=sorted({fraction(r[k]) for rows in labels.values() for r in rows for k in ('start','end')});diff=[]
    for a,b in zip(cuts,cuts[1:]):
        lab={s:next(r['label'] for r in rows if fraction(r['start'])<=a<fraction(r['end'])) for s,rows in labels.items()}
        if len(set(lab.values()))>1:diff.append(dict(start=str(a),end=str(b),labels=lab))
    baseline=Path(r'G:\ai\AIC视频\deliveries\ANNOTATION_ITERATION_20261010\SAFE_37_66\candidate_SAFE_37_66.zip')
    with zipfile.ZipFile(baseline) as z:baseline_check=dict(bytes=baseline.stat().st_size,sha256=sha(baseline),crc_error=z.testzip(),archive_names=z.namelist())
    assert baseline_check['sha256']=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
    baseline_check['historical_score']=37.66;baseline_check['new_score']=None
    report=dict(status='COMPLETE_POST_STOP_DIAGNOSTIC_NOT_TRAINING_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),
        preregistration_sha256=sha(ROOT/'preregistration.json'),original_STOP_sha256=sha(BASE/'slot6_silver24_v1/pilot_final_adjudication_v1.json'),
        teacher_stream_records=stream_records,teacher_combined_tool_issues=tools_issues,teacher_completed_student_PNG_reads=sum(counts[p]==1 for p in student_paths),
        teacher_completed_native_PNG_reads=sum(counts[p]==1 for p in native_paths),teacher_student_write_precedes_native=bool(order),student_original_bytes_preserved=preserved,
        independent_seal_sha256=sha(ROOT/'independent/seal.json'),independent_blinding='ATTESTED_WITH_PROJECT_CONTEXT_DISCLOSURE_NOT_ABSOLUTE_PROOF',
        preregistration_deviation='Original one-CLI/session cap not met: same proposal required one successful continuation after print timeout and two pre-inference transport failures. Original partial failure and all receipts preserved.',
        document_geometry=docs,student_label_disagreement_seconds_exact=str(sum((fraction(r['end'])-fraction(r['start']) for r in diff),F(0))),student_label_disagreement_spans=diff,
        factual_error={'frame_id':'F37','teacher_student_and_native':'dog with y esconderte,','independent_student_and_native_and_root_actual_student':'person with siempre puedes ignorar a esas personas',
            'conclusion':'Confirmed teacher frame-content misassignment in student view; repeated native assertion is not a correction. Root spot receipt retained. Teacher is not accepted as gold.'},
        safe_baseline=baseline_check,cash_cost='UNKNOWN_NOT_ZERO',new_optimizer_updates=0,new_426_calls=0,new_decoder_processor_calls=0,
        interpretation='Evidence supports full-window editorial proposals despite static/text content, with remaining factual and editorial disagreement. Both proposals exceed original five-interval capacity; neither is train-ready.',training_admitted=False)
    save(ROOT/'final_diagnostic_audit_v1.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('teacher_stream_records','student_label_disagreement_spans')},ensure_ascii=False))
