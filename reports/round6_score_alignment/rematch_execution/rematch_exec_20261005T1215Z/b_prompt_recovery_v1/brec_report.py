"""Full104 and expanded72 administrative gate; no post-result retuning."""
import statistics
import brec_common as c
from brec_engine import replay

def gate(delta,new_delta,changed,down):
    return changed>0 and delta>=0 and new_delta>0 and not(delta<=-.05 and down>=.75)

def main():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    from transformers import AutoProcessor
    from native_segment_contract import native_segment_ranges
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    plan=c.read(c.HERE/'input_01/developer_plan.json');rows=[];proofs=[]
    first=c.read(c.HERE/'first_real_acceptance.json')['path']
    for job in plan['developer_jobs']:
        row={'video_id':job['video_id'],'source_group':job['source_group'],'arms':{}}
        for arm in ('B1','B0'):
            intervals=[];ids=set()
            for ix,part in enumerate(job['windows']):
                p=c.done_path('developer',job,ix,arm,cc);v=c.checked(p,job,ix,arm,ex)
                if arm=='B1' and str(p).startswith(str(c.HERE)) and str(p)!=first:
                    proofs.append(replay(p,job,ix,ex,rt,student,processor))
                base=part['window']['planned_source_frame_ordinals'][0]
                for a,b in v['native_frame_realizability']['ranges']:ids.update(range(base+a,base+b))
                offset=part['start_sec']-job.get('clip_start_sec',0)
                intervals.extend([[offset+a,offset+b] for a,b in v['parsed_segments']])
            row['arms'][arm]={'closed_world_output_agreement':cc.weak_metrics(intervals,job['weak_reference']),
                'native_source_ordinals':sorted(ids),'segments':intervals,'selected_seconds':cc.seconds(intervals),'legal_empty':not intervals}
        rows.append(row)
    c.require(len(rows)==104 and len({x['source_group'] for x in rows})==96 and len(proofs)==85,'independent full replay denominator')
    pilot=set(plan['pilot_source_groups']);new=[r for r in rows if r['source_group'] not in pilot]
    c.require(len(new)==80 and len({r['source_group'] for r in new})==72,'expanded72 denominator')
    original_report=rt.load(c.CAD/'report.py','brec_bootstrap_only')
    delta=lambda r:r['arms']['B1']['closed_world_output_agreement']['f1']-r['arms']['B0']['closed_world_output_agreement']['f1']
    all_metric=original_report.bootstrap_video_macro([delta(r) for r in rows],rows)
    new_metric=original_report.bootstrap_video_macro([delta(r) for r in new],new)
    groups=sorted({r['source_group'] for r in rows})
    down=sum(statistics.mean(delta(r) for r in rows if r['source_group']==g)<0 for g in groups)
    changed=sum(r['arms']['B1']['native_source_ordinals']!=r['arms']['B0']['native_source_ordinals'] for r in rows)
    admitted=gate(all_metric['mean'],new_metric['mean'],changed,down/96)
    c.save(c.HERE/'developer_01/matched_rows.json',rows)
    c.save(c.HERE/'developer_01/replay_acceptance.json',{'status':'PASS_ALL_86_NEW_B1_NATIVE_CPU_REPLAY',
        'first_proof_sha256':c.sha(c.HERE/'first_real_acceptance.json'),'remaining_proofs':proofs,'new_model_calls':0})
    result={'status':'GO_ONE_HISTORICAL_B1_RISK_PACKAGE' if admitted else 'STOP_HISTORICAL_B1_INVESTMENT',
        'utc':c.utc(),'records':104,'groups':96,'windows':112,'new_B1_calls':86,'original_B1_reused':26,
        'original_B0_reused':112,'all104_B1_minus_B0':all_metric,'expanded72_B1_minus_B0':new_metric,
        'changed_native_sets':changed,'groups_down':down,'B1_legal_empty_records':sum(r['arms']['B1']['legal_empty'] for r in rows),
        'B0_legal_empty_records':sum(r['arms']['B0']['legal_empty'] for r in rows),'reference_coverage':'UNKNOWN',
        'metric_is_closed_world_weak_output_agreement_not_quality_truth':True,'new_optimizer_updates':0,
        'coupled_prompt_and_grammar_alternative':True,'official_score':None,'no_post_result_retuning':True}
    c.save(c.HERE/'developer_01/report.json',result);print(result,flush=True)

if __name__=='__main__':main()
