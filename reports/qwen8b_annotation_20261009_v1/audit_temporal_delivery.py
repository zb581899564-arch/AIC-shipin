"""Read-only audit of completed native-video jobs and exact PTS candidate export."""
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction
from collections import Counter
import json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def numeric(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def main():
    corpus=read(ROOT/'corpus.json');rows=[];pending=[];known_quality_failures=[];event_states=Counter();usage=Counter();durations=0.0
    for m in corpus['sources']:
        sid=m['source_id'];receipts=list((ROOT/'raw/gemini'/sid).glob('attempt_*/acceptance.json'))
        assert len(receipts)<=1
        if not receipts:pending.append(sid);continue
        receipt_path=receipts[0];r=read(receipt_path);assert r['source_id']==sid and r['media_sha256']==m['media_sha256']
        raw=Path(r['raw']['path']);assert sha(raw)==r['raw']['sha256'];doc=read(raw)
        assert doc['source_id']==sid and doc['native_video_accepted'] is True
        expected=(ROOT/'input'/sid/m['media_file']).resolve();video_calls=[];job=receipt_path.parent
        if r['status']=='EXACT_PRIOR_NATIVE_UI_RECEIPT_REUSED':
            prior=Path(r['prior_acceptance']['path']);assert sha(prior)==r['prior_acceptance']['sha256']
            old=read(prior);assert old['source_sha256']==m['media_sha256'] and old['native_mp4_read_entry_observed_in_ui'] is True
            observation_receipt='EXACT_PRIOR_UI_VIDEO_RECEIPT'
        else:
            assert sha(job/'stream.jsonl')==r['stream_sha256'] and read(job/'cli_terminal.json')['exit_code']==0
            events=[json.loads(t) for t in (job/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if t.strip()]
            init=next(e['init'] for e in events if e.get('event')=='init');final=next(e['result'] for e in reversed(events) if e.get('event')=='result')
            assert init['model']==r['model']=='gemini-3.8-flash-high' and final['status']=='SUCCESS'
            assert final['conversation_id']==r['conversation_id']
            for e in events:
                step=e.get('step_update',{});params=step.get('tool_info',{}).get('parameters',{})
                if step.get('state')=='DONE' and step.get('tool_name')=='view_file' and params.get('AbsolutePath'):
                    if Path(params['AbsolutePath']).resolve()==expected:video_calls.append(step)
            assert video_calls,'Exact expected local video path must have a completed native view_file call'
            for k,v in (r.get('usage') or {}).items():
                if isinstance(v,int):usage[k]+=v
            durations+=float(r.get('duration_seconds') or 0)
            observation_receipt='EXACT_NATIVE_VIDEO_PATH_AND_SUCCESSFUL_CLI_TOOL_CALL'
        assert r['full_source_frame_observation_independently_proven'] is False
        unknown_timestamps=[]
        for t in doc.get('observed_timestamps_seconds',[]):
            assert numeric(t)
            if not 0<=t<=m['source_duration_seconds']+1e-6:unknown_timestamps.append(t)
        counts=Counter();zero_native_frames=[];pts=np.load(ROOT/'input'/sid/'native_pts.npz')['pts'];tb=Fraction(*m['native_time_base']);p0=int(pts[0])
        for i,e in enumerate(doc['events']):
            assert e['state'] in ('KEEP','UNKNOWN') and e.get('visible_evidence')
            a,b=e['start_seconds'],e['end_seconds_exclusive'];assert numeric(a) and numeric(b) and 0<=a<b<=m['source_duration_seconds']+1e-6
            uncertainty=e.get('boundary_uncertainty_seconds');assert uncertainty is None or numeric(uncertainty) and uncertainty>=0
            assert e['confidence'] in ('LOW','MEDIUM','HIGH')
            aa,bb=Fraction(str(a)),Fraction(str(b));native=[j for j,p in enumerate(pts) if aa<=(int(p)-p0)*tb<bb]
            if not native:zero_native_frames.append(i)
            counts[e['state']]+=1;event_states[e['state']]+=1
        quality_path=ROOT/'temporal_quality'/f'{sid}.json';quality=read(quality_path) if quality_path.exists() else None
        if quality:
            assert quality['raw_sha256']==sha(raw)
            known_quality_failures.append(sid)
            for c in quality.get('contradictions',[]):
                f=m['frames'][c['sample_index']];event=doc['events'][c['event_index']]
                assert abs(f['pts_seconds']-c['pts_seconds'])<0.006
                assert [event['start_seconds'],event['end_seconds_exclusive']]==c['event_interval']
                assert event['start_seconds']+event['boundary_uncertainty_seconds']<f['pts_seconds']<event['end_seconds_exclusive']-event['boundary_uncertainty_seconds']
        rows.append(dict(source_id=sid,split=m['split'],events=dict(counts),attempt=job.name,receipt_path=str(receipt_path),receipt_sha256=sha(receipt_path),raw_sha256=sha(raw),
            observation_receipt=observation_receipt,exact_native_video_tool_calls=len(video_calls),
            independently_proven_continuous_observation=False,declared_timestamps_out_of_domain=unknown_timestamps,empty_native_event_ordinals=zero_native_frames,
            temporal_alignment_quality='REJECT_TEMPORAL_ALIGNMENT_FOR_TRAINING' if quality else 'UNVERIFIED_MODEL_CANDIDATE',audio_observed_model_claim=doc.get('audio_observed')))
    report=dict(status='PASS_COMPLETED_NATIVE_TOOL_IDENTITY_AND_CANDIDATE_SCHEMA_ONLY',utc=datetime.now(timezone.utc).isoformat(),
        completed_sources=len(rows),expected_sources=50,annotation_batch_raw_complete=len(rows)==50,pending_sources=pending,
        event_states=dict(event_states),known_temporal_alignment_failures=known_quality_failures,complete_temporal_sft_rows=0,
        all_events_are_candidates_not_complete_training_targets=True,unobserved_domain_negative_labels=0,
        continuous_video_observation_independently_proven=False,native_video_accepted_is_not_quality_acceptance=True,
        aggregated_successful_new_cli_usage=dict(usage),successful_cli_wall_seconds=durations,prior_ui_cost_not_counted_as_zero=True,
        source_receipts=rows,new_model_calls_in_audit=0,gpu_used=False,training_started=False)
    out=ROOT/'exports/temporal_independent_audit.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_receipts','pending_sources')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
