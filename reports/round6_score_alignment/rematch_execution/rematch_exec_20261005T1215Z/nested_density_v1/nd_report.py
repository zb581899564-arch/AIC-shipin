"""Independent density replay and full104/expanded72 fixed investment gate."""
import statistics
import nd_common as c
from nd_engine import replay

def gate(delta,new_delta,changed,down):
    return changed>0 and delta>=0 and new_delta>0 and not(delta<=-.05 and down>=.75)

def main(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    from transformers import AutoProcessor
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs'];rows=[];proofs=[]
    first=c.read(c.HERE/'first_real_acceptance.json')['path']
    for job in jobs:
        row=dict(video_id=job['video_id'],source_group=job['source_group'],arms={})
        for arm in ('D','B0') if scope=='developer' else ('D',):
            intervals=[];ids=set()
            for ix,part in enumerate(job['windows']):
                if arm=='D':
                    p=c.done_path(scope,job,ix,'D',cc);v=c.checked(p,job,ix,'D',ex)
                    if str(p)!=first:proofs.append(replay(p,job,ix,ex,rt,student,processor))
                else:v=c.checked_base(scope,job,ix)
                base=part['window']['planned_source_frame_ordinals'][0]
                for a,b in v['native_frame_realizability']['ranges']:ids.update(range(base+a,base+b))
                offset=part['start_sec']-job.get('clip_start_sec',0);intervals.extend([[offset+a,offset+b] for a,b in v['parsed_segments']])
            row['arms'][arm]=dict(native_source_ordinals=sorted(ids),segments=intervals,legal_empty=not intervals)
            if scope=='developer':row['arms'][arm]['closed_world_output_agreement']=cc.weak_metrics(intervals,job['weak_reference'])
        rows.append(row)
    c.require(len(proofs)==(7 if scope=='nontest' else 112),'new independent replay denominator')
    c.save(c.HERE/(scope+'_01/replay_acceptance.json'),dict(status='PASS_ALL_SCOPE_NESTED_DENSITY_NATIVE_CPU_REPLAY',first_proof_sha256=c.sha(c.HERE/'first_real_acceptance.json'),proofs=proofs,new_model_calls=0))
    if scope=='nontest':return
    c.require(len(rows)==104 and len({x['source_group'] for x in rows})==96,'full developer denominator')
    pilot=set(plan['pilot_source_groups']);new=[r for r in rows if r['source_group'] not in pilot];c.require(len(new)==80 and len({r['source_group'] for r in new})==72,'expanded72')
    original=rt.load(c.CAD/'report.py','nd_bootstrap_only');delta=lambda r:r['arms']['D']['closed_world_output_agreement']['f1']-r['arms']['B0']['closed_world_output_agreement']['f1']
    all_metric=original.bootstrap_video_macro([delta(r) for r in rows],rows);new_metric=original.bootstrap_video_macro([delta(r) for r in new],new)
    groups=sorted({r['source_group'] for r in rows});down=sum(statistics.mean(delta(r) for r in rows if r['source_group']==g)<0 for g in groups)
    changed=sum(r['arms']['D']['native_source_ordinals']!=r['arms']['B0']['native_source_ordinals'] for r in rows)
    c.save(c.HERE/'developer_01/matched_rows.json',rows)
    result=dict(status='GO_ONE_NESTED_DENSITY_RISK_PACKAGE' if gate(all_metric['mean'],new_metric['mean'],changed,down/96) else 'STOP_NESTED_DENSITY_INVESTMENT',
        utc=c.utc(),records=104,groups=96,windows=112,new_density_calls=112,original_B0_reused=112,all104_D_minus_B0=all_metric,expanded72_D_minus_B0=new_metric,
        changed_native_sets=changed,groups_down=down,reference_coverage='UNKNOWN',metric_is_closed_world_weak_output_agreement_not_quality_truth=True,
        observed_development_not_new_holdout=True,original_total_video_pixel_budget_unchanged=True,physical64_subset_retained=True,
        new_optimizer_updates=0,official_score=None,no_post_result_retuning=True)
    c.save(c.HERE/'developer_01/report.json',result);print(result,flush=True)

if __name__=='__main__':
    import sys;main(sys.argv[1])
