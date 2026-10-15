"""Audit actual media tool receipts and geometry without accepting semantic labels."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parent/'slot6_silver24_v1'
sys.path.insert(0,str(ROOT))
from quality_contract import reference
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def exact(x):return F(str(x))
def audit(folder,attempt):
    m=json.loads((folder/'manifest.json').read_text());sv=json.loads((folder/'student_views/receipt.json').read_text())
    rows=[json.loads(s) for s in (attempt/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    calls=[e['step_update'] for e in rows if e.get('step_update',{}).get('state')=='DONE' and e['step_update'].get('step_type')=='tool']
    expected={str(Path(r['path']).resolve()):r['frame_id'] for r in m['frames']}
    effective={str(Path(r['path']).resolve()):r['frame_id'] for r in sv['frames'][::8]}
    clip=str((folder/'clip.mp4').resolve());metadata={str((folder/x).resolve()) for x in ('manifest.json','student_views/receipt.json')}
    supplied=set();tool_issues=[];reads={}
    for c in calls:
        info=c.get('tool_info',{});pars=info.get('parameters',{});name=c.get('tool_name')
        path=pars.get('AbsolutePath') or pars.get('TargetFile');path=str(Path(path).resolve()) if path else None
        output=info.get('output','')
        # Tool DONE alone is insufficient: preserve visible read failure indications.
        failed=any(s in output.lower() for s in ('not found','cannot read','failed to','error reading'))
        if name=='view_file':
            reads[path]=reads.get(path,0)+1
            if path not in set(expected)|set(effective)|metadata|{clip}:tool_issues.append(dict(tool=name,path=path,reason='OUTSIDE_WHITELIST'))
            if failed:tool_issues.append(dict(tool=name,path=path,reason='REPORTED_READ_FAILURE',output=output))
            else:supplied.add(path)
        elif name=='write_to_file':
            if path!=str((attempt/'proposal.json').resolve()):tool_issues.append(dict(tool=name,path=path,reason='UNEXPECTED_WRITE'))
        else:tool_issues.append(dict(tool=name,path=path,reason='UNEXPECTED_TOOL'))
    result=next((e['result'] for e in reversed(rows) if e.get('event')=='result'),None)
    init=next((e['init'] for e in rows if e.get('event')=='init'),{})
    docpath=attempt/'proposal.json';doc=json.loads(docpath.read_text(encoding='utf-8-sig')) if docpath.exists() else None
    issues=[];unknown=None;events=None
    if not doc:issues.append('PROPOSAL_MISSING')
    else:
        for field in ('window_id','source_sha256','clip_sha256'):
            if doc.get(field)!=m[field]:issues.append('IDENTITY:'+field)
        obs=doc.get('frame_observations',[])
        if len(obs)!=64:issues.append('FRAME_COUNT')
        for r,ref in zip(obs,m['frames']):
            for key in ('frame_id','source_ordinal'):
                if r.get(key)!=ref[key]:issues.append('FRAME_IDENTITY:'+key)
            try:
                if exact(r['local_seconds_exact'])!=exact(ref['local_seconds_exact']):issues.append('FRAME_PTS')
            except Exception:issues.append('FRAME_PTS_MISSING_OR_INVALID')
            if r.get('observed') is not True:issues.append('FRAME_UNOBSERVED:'+ref['frame_id'])
        if [r.get('frame_id') for r in doc.get('effective_view_observations',[])]!=[r['frame_id'] for r in sv['frames'][::8]]:issues.append('EFFECTIVE_VIEW_ID_ORDER')
        if doc.get('training_admitted') is not False:issues.append('UNAUTHORIZED_TRAINING_ADMISSION_CLAIM')
        if doc.get('full_native_frames_observed') is not False:issues.append('UNPROVEN_FULL_NATIVE_OBSERVATION')
        cov=doc.get('window_coverage',[]);parts={k:[] for k in ('KEEP','NO','UNKNOWN')}
        try:
            for r in cov:
                parts[r['label']].append((r['start'],r['end']))
                if not r.get('visible_basis'):issues.append('COVERAGE_NO_VISIBLE_BASIS')
                if any(x not in {r['frame_id'] for r in m['frames']} for x in r.get('evidence_frame_ids',[])):issues.append('UNBOUND_COVERAGE_FRAME')
            a,b=map(exact,m['domain_global_seconds_exact']);reference([(0,b-a)],parts['KEEP'],parts['NO'],parts['UNKNOWN'])
            unknown=bool(parts['UNKNOWN'])
        except Exception as e:issues.append('COVERAGE_CONTRACT:'+repr(e))
        events=len(doc.get('events',[]))
    return dict(status='OBSERVATION_AUDIT_ONLY_NOT_SILVER_ADMISSION',window_id=m['window_id'],
        actual_model=init.get('model'),actual_result_status=result and result.get('status'),
        actual_result_error=result and result.get('error'),actual_result_usage=result and result.get('usage'),
        original_pngs_delivered=len(set(expected)&supplied),original_pngs_expected=64,
        missing_original=[expected[p] for p in expected if p not in supplied],
        effective_pngs_delivered=len(set(effective)&supplied),effective_pngs_expected=8,
        native_video_delivered=clip in supplied,actual_completed_tool_count=len(calls),read_counts=reads,
        tool_issues=tool_issues,proposal_geometry_identity_issues=issues,proposal_events=events,
        consequential_unknown_coverage=unknown,proposal_sha256=sha(docpath) if doc else None,
        stream_sha256=sha(attempt/'stream.jsonl'),request_sha256=sha(attempt/'request.json'),
        all_floor64_delivered_not_attention_or_full_native_proof=True,training_admitted=False,new_optimizer_updates=0)
if __name__=='__main__':
    index=int(sys.argv[1]);folder=Path(json.loads((ROOT/'observations/jobs.json').read_text())['jobs'][index]);attempt=folder/'teacher_attempt01_http1'
    assert (attempt/'terminal.json').exists(),'Do not freeze an unfinished attempt snapshot'
    result=audit(folder,attempt)
    with (attempt/'audit.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('read_counts','actual_result_error')},ensure_ascii=False))
