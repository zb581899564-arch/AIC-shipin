"""Exact cached authority; register before any B1 reference direction is read."""
from collections import Counter
import brec_common as c

def main():
    rt,ex,cc,student,old,frames,production=c.helpers()
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    upstream=c.RUN/'b_boundary_diagnostic_v1'
    d=c.read(upstream/'diagnostic_completion.json')
    c.require(d['status']=='PASS_REAL_MATCHED_32B_BOUNDARY_DIAGNOSTIC_AND_CPU_ACCOUNTING' and
        d['events']==16 and d['context_attempts']==42 and d['engineering_failures']==0 and
        d['all_contexts_unique_temporal_overlap_events']==3 and d['independent_weak_direction_events']==2 and
        d['external_weak_event_macro_delta']<0 and d['training_admitted'] is False,'boundary diagnostic terminal changed')
    matched=c.read(upstream/'matched_rows.json')
    deltas=[__import__('statistics').mean(x['per_context_external_weak_IoU_delta_vs_B']) for x in matched if x['per_context_external_weak_IoU_delta_vs_B'] is not None]
    c.require(len(matched)==16 and sum(len(x['contexts']) for x in matched)==42 and len(deltas)==2 and
        all(x<0 for x in deltas) and __import__('statistics').mean(deltas)==d['external_weak_event_macro_delta'],'negative original boundary aggregates differ')
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    resources={}
    for name in ('aic_CAD_v1_nontest','aic_CAD_v1_pilot','aic_CAD_v1_full','aic_BBOUND_v1_diagnostic'):
        p=c.RUN/'controller'/(name+'.resource.json');v=c.read(p)
        c.require([x for x in ledger if x.get('name')==name]==[v] and v['status']=='completed' and
            v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'upstream unique terminal accounting')
        resources[name]={'path':str(p),'sha256':c.sha(p),'charged_seconds':v['charged_seconds']}
    for p in (upstream/'run_01').rglob('done.json'):
        value=c.read(p)
        for f,s in value['bound_files'].items():c.require(c.sha(f)==s,'completed boundary bytes changed')
    c.require(c.read(c.CAD/'scientific_stop.json')['C']['status']=='STOP_C_PRODUCTION_INVESTMENT','original C stop changed')
    plans={s:c.read(c.CAD/'input_01'/(s+'_plan.json')) for s in ('nontest','developer')}
    c.require(len(plans['developer']['developer_jobs'])==104 and len(set(x['source_group'] for x in plans['developer']['developer_jobs']))==96 and
        sum(len(x['windows']) for x in plans['developer']['developer_jobs'])==112,'original developer denominator')
    resume=[];counts=Counter();missing=[];model=None
    for scope,plan in plans.items():
        c.save(c.HERE/'input_01'/(scope+'_plan.json'),plan)
        jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                for arm in ('B1','B0'):
                    path=c.old_path(scope,job,ix,arm,cc)
                    if not path.exists():
                        c.require(scope=='developer' and arm=='B1','missing original control')
                        missing.append({'video_id':job['video_id'],'index':ix,'window':part['window']});continue
                    value=c.checked(path,job,ix,arm,ex)
                    if model is None:model=value['model_identity']
                    c.require(value['model_identity']==model,'original inference model receipts differ')
                    resume.append({'scope':scope,'video_id':job['video_id'],'index':ix,'arm':arm,
                        'path':str(path),'sha256':c.sha(path),'request_sha256':value['request_sha256'],'bound_files':value['bound_files']})
                    counts[scope+'_'+arm]+=1
    c.require(dict(counts)=={'nontest_B1':8,'nontest_B0':8,'developer_B1':26,'developer_B0':112} and len(missing)==86,'exact recovery call budget')
    c.save(c.HERE/'input_01/resume_manifest.json',{'rows':resume,'counts':dict(counts),'missing_B1_windows':missing,
        'model_identity':model,'original_C_lock_sha256':c.sha(c.CAD/'source_lock.json'),
        'original_boundary_completion_sha256':c.sha(upstream/'diagnostic_completion.json'),
        'original_matched_rows_sha256':c.sha(upstream/'matched_rows.json'),'resources':resources})
    c.save(c.HERE/'input_01/investment_rule.json',{'registered_utc':c.utc(),'all104_delta_min':0,
        'expanded72_delta_strictly_positive':True,'native_set_change_required':True,
        'negative_mean_threshold':-.05,'negative_group_fraction_threshold':.75,'bootstrap_draws':10000,
        'bootstrap_seed':20261009,'CI_report_only':True,'B1_weak_direction_not_read':True,
        'coupled_original_prompt_and_grammar_not_cardinality_only':True,'coverage':'UNKNOWN'})
    c.save(c.HERE/'prepared.json',{'status':'PASS_EXACT_CACHED_B1_B0_AND_NEGATIVE_BOUNDARY_HANDOFF',
        'utc':c.utc(),'records':104,'groups':96,'windows':112,'missing_B1':86,'exact_resume_counts':dict(counts),
        'new_model_calls':0,'new_optimizer_updates':0,'no_reference_metric_read':True})
    print(c.read(c.HERE/'prepared.json'),flush=True)

if __name__=='__main__':main()
