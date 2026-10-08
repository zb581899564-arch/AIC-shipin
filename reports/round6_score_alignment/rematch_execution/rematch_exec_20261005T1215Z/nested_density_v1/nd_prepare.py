"""Register one density alternative before any new density weak direction."""
from collections import Counter
import nd_common as c
from nd_native import dense_window

def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    rt,ex,cc,student,old,frames,production=c.helpers()
    upstream=c.RUN/'b_prompt_recovery_v1'
    stop=c.read(upstream/'scientific_stop.json');r=stop['report']
    c.require(r['status']=='STOP_HISTORICAL_B1_INVESTMENT' and r['new_B1_calls']==86 and r['records']==104 and
        r['all104_B1_minus_B0']['mean']<0 and r['expanded72_B1_minus_B0']['mean']<0,'preserved B1 stop differs')
    c.require(c.read(upstream/'developer_01/replay_acceptance.json')['status']=='PASS_ALL_86_NEW_B1_NATIVE_CPU_REPLAY','complete original CPU acceptance missing')
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');resources={}
    p=c.RUN/'controller/aic_BREC_v1_developer.resource.json';v=c.read(p)
    c.require([x for x in ledger if x.get('name')==v['name']]==[v] and v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'original terminal accounting')
    resources[v['name']]=dict(path=str(p),sha256=c.sha(p),charged_seconds=v['charged_seconds'])
    # The inherited source lock protects all old dependencies. Preserve every newly completed B1 byte too.
    upstream_success=[]
    for p in (upstream/'developer_01').rglob('done.json'):
        x=c.read(p)
        for f,s in x['bound_files'].items():c.require(c.sha(f)==s,'newly completed historical B1 raw changed')
        upstream_success.append(dict(path=str(p),sha256=c.sha(p),bound_files=x['bound_files']))
    c.require(len(upstream_success)==86,'old completed B1 denominator')
    authority=[];model=None;counts=Counter();sampling=[]
    for scope in ('nontest','developer'):
        plan=c.read(c.CAD/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        sources=ex.source_tables(plan)
        for job in jobs:
            # Complete a multi-window job before reconstructing its old B0 request.
            for part in job['windows']:
                original=part['window'];part['base_window']=original
                part['window']=dense_window(original,sources[job['source_key']]['pts'])
            for ix,part in enumerate(job['windows']):
                original=part['base_window']
                base=c.checked_base(scope,job,ix)
                if model is None:model=base['model_identity']
                c.require(model==base['model_identity'],'original B0 model differs')
                path=c.base_path(scope,job,ix,cc)
                authority.append(dict(scope=scope,video_id=job['video_id'],index=ix,path=str(path),sha256=c.sha(path),bound_files=base['bound_files']))
                counts[scope]+=1
                a=original['planned_actual_pts_sec'];b=part['window']['planned_actual_pts_sec']
                sampling.append(dict(scope=scope,base_physical_frames=len(a),new_physical_frames=len(b),
                    base_max_gap=max((y-x for x,y in zip(a,a[1:])),default=0),new_max_gap=max((y-x for x,y in zip(b,b[1:])),default=0)))
        c.save(c.HERE/'input_01'/(scope+'_plan.json'),plan)
    c.require(dict(counts)=={'nontest':8,'developer':112} and any(x['new_physical_frames']>x['base_physical_frames'] for x in sampling),'new input mechanism absent')
    c.save(c.HERE/'input_01/resume_manifest.json',dict(rows=authority,counts=dict(counts),model_identity=model,resources=resources,
        preserved_upstream_success=upstream_success,original_B1_stop_sha256=c.sha(upstream/'scientific_stop.json'),
        original_B1_report_sha256=c.sha(upstream/'developer_01/report.json'),new_density_success_reused=0))
    c.save(c.HERE/'input_01/sampling_audit.json',dict(records=sampling,all_old_samples_preserved=True,
        all_physical_first_last_unchanged=True,new_density_frames_max=127,first_replay_not_full_source_decode=True,
        spatial_resolution_tradeoff='TOTAL_VIDEO_PIXEL_BUDGET_UNCHANGED_ACTUAL_GRID_MUST_BE_REPORTED'))
    c.save(c.HERE/'input_01/investment_rule.json',dict(registered_utc=c.utc(),all104_delta_min=0,expanded72_delta_strictly_positive=True,
        native_set_change_required=True,negative_mean_threshold=-.05,negative_group_fraction_threshold=.75,
        bootstrap_draws=10000,bootstrap_seed=20261009,CI_report_only=True,new_density_weak_direction_read=False,
        observed_development_not_new_holdout=True,coverage='UNKNOWN',training_admitted=False))
    c.save(c.HERE/'prepared.json',dict(status='PASS_EXACT_NEGATIVE_B1_AND_NESTED_NATIVE_DENSITY_PLAN',utc=c.utc(),
        records=104,groups=96,developer_windows=112,nontest_windows=8,new_model_calls=0,new_optimizer_updates=0,
        original_baseline_calls_reused=120,new_density_calls_required=120,registered_original_B1_stop=True))
    print(c.read(c.HERE/'prepared.json'),flush=True)

if __name__=='__main__':main()
