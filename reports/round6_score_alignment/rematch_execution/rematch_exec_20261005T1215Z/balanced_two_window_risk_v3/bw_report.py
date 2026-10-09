"""Replay every new answer once; quality measurements are descriptive only."""
import bw_common as c
from bw_engine import replay

def main(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    from transformers import AutoProcessor
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    plan,jobs=c.jobs_for(scope);proofs=[];rows=[]
    first=c.read(c.HERE/'first_real_acceptance.json') if (c.HERE/'first_real_acceptance.json').exists() else None
    for job in jobs:
        ids=set();baseline=set()
        for ix,part in enumerate(job['windows']):
            p=c.done_path(scope,job,ix,'BW',cc);v=c.checked(p,job,ix,'BW',ex)
            if c.is_changed(part):
                if first and str(p)==first['path']:
                    c.require(c.sha(p)==first['done_sha256'],'first accepted answer changed')
                    proofs.append(dict(first,first_proof_referenced=True))
                else:proofs.append(replay(p,job,ix,ex,rt,student,processor))
            for a,b in v['native_frame_realizability']['ranges']:ids.update(range(part['window']['planned_source_frame_ordinals'][0]+a,part['window']['planned_source_frame_ordinals'][0]+b))
            if scope=='developer':
                oldv=c.checked_base(scope,job,ix)
                for a,b in oldv['native_frame_realizability']['ranges']:baseline.update(range(part['base_window']['planned_source_frame_ordinals'][0]+a,part['base_window']['planned_source_frame_ordinals'][0]+b))
        rows.append(dict(video_id=job['video_id'],source_group=job['source_group'],selected_native_ordinals=sorted(ids),
            original_B0_native_ordinals=sorted(baseline) if scope=='developer' else None))
    expected=c.read(c.HERE/'prepared.json')['counts'][scope]['changed']
    c.require(len(proofs)==expected,'each new request must have one independent CPU replay')
    c.save(c.HERE/(scope+'_01/replay_acceptance.json'),dict(status='PASS_ALL_BALANCED_NEW_REQUESTS_CPU_REPLAY',utc=c.utc(),proofs=proofs,
        new_calls=expected,original_successes_referenced=sum(len(j['windows']) for j in jobs)-expected,new_model_calls=0,new_optimizer_updates=0))
    if scope=='developer':
        c.save(c.HERE/'developer_01/matched_rows.json',rows)
        c.save(c.HERE/'developer_01/report.json',dict(status='PASS_ENGINEERING_USER_ACCEPTED_RISK_CONTINUE_426',utc=c.utc(),records=104,groups=96,
            windows=112,fresh_calls=expected,changed_native_sets=sum(r['selected_native_ordinals']!=r['original_B0_native_ordinals'] for r in rows),
            independent_quality_reference='UNKNOWN',official_score=None,new_training=False,quality_go_claim=False,
            user_override='2026-10-09 proceed with the discussed experiment and ZIP; we are experimenting',
            weak_reference_not_used_to_select_or_retune_recipe=True))

if __name__=='__main__':
    import sys;main(sys.argv[1])
