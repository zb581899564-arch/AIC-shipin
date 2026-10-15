"""Tool delivery is an observation receipt, never attention or training proof."""
from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parent/'native_event_pilot_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(media,attempt):
    m=json.loads((media/'manifest.json').read_text())
    ev=[json.loads(x) for x in (attempt/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
    calls=[x['step_update'] for x in ev if x.get('step_update',{}).get('state')=='DONE' and x['step_update'].get('step_type')=='tool']
    expected={str(Path(x['path']).resolve()):x['frame_id'] for x in m['frames']}
    allowedread=set(expected)|{str((media/'manifest.json').resolve()),str((media/'clip.mp4').resolve())}
    observed=set();issues=[];video=False
    for c in calls:
        name=c.get('tool_name');info=c.get('tool_info',{});pars=info.get('parameters',{})
        path=pars.get('AbsolutePath') or pars.get('TargetFile')
        resolved=str(Path(path).resolve()) if path else None
        output=info.get('output','');failed=any(s in output.lower() for s in ('not found','error','cannot','failed'))
        if name=='view_file':
            if resolved not in allowedread:issues.append(dict(kind='UNEXPECTED_READ_PATH',path=resolved,output=output))
            if not failed and resolved in expected:observed.add(resolved)
            if not failed and resolved==str((media/'clip.mp4').resolve()):video=True
        elif name=='write_to_file':
            if not resolved or not Path(resolved).is_relative_to(attempt.resolve()):issues.append(dict(kind='UNEXPECTED_WRITE_PATH',path=resolved))
        else:issues.append(dict(kind='UNEXPECTED_TOOL',name=name))
    result=next((x['result'] for x in reversed(ev) if x.get('event')=='result'),None)
    docpath=attempt/'teacher_proposal.json';doc=json.loads(docpath.read_text(encoding='utf-8-sig')) if docpath.exists() else None
    schema=[]
    if doc:
        for field in ('window_id','source_sha256','clip_sha256'):
            if doc.get(field)!=m[field]:schema.append(field)
        if [x.get('frame_id') for x in doc.get('frame_observations',[])]!=[x['frame_id'] for x in m['frames']]:schema.append('frame_id_order')
        for row,ref in zip(doc.get('frame_observations',[]),m['frames']):
            for field in ('source_ordinal','local_seconds_exact'):
                if row.get(field)!=ref[field]:schema.append(row['frame_id']+':'+field)
    return dict(window_id=m['window_id'],attempt=str(attempt),stream_sha256=sha(attempt/'stream.jsonl'),
        actual_result_status=result and result.get('status'),actual_result_error=result and result.get('error'),
        pngs_delivered=len(observed),expected_pngs=64,missing=[expected[x] for x in expected if x not in observed],
        actual_correct_video_delivery=video,unexpected_tool_or_path=issues,identity_schema_issues=schema,
        proposal_sha256=sha(docpath) if doc else None,training_admitted=False,
        notes='Partial/error outputs retained for independent audit only; no inferred attention/full native observation/student visibility')
if __name__=='__main__':
    reports=[]
    for media in [Path(x) for x in json.loads((ROOT/'jobs.json').read_text())['jobs']]:
        for name in ('attempt02_proxy','attempt03_correct_path'):
            attempt=media/name
            if (attempt/'teacher_proposal.json').exists():reports.append(audit(media,attempt))
    out=ROOT/'teacher_observation_audit_01.json'
    with out.open('x',encoding='utf-8') as f:json.dump(reports,f,ensure_ascii=False,indent=2)
    print(json.dumps(reports,ensure_ascii=False,indent=2))
