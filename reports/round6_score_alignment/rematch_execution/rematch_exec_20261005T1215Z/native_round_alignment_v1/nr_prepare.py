"""Register one round_alignment alternative before any new round_alignment weak direction."""
from collections import Counter
import nr_common as c
from nr_native import round_window

def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    rt,ex,cc,student,old,frames,production=c.helpers()
    upstream=c.RUN/'nested_density_v1'
    stop=c.read(upstream/'scientific_stop.json');r=stop['report']
    c.require(r['status']=='STOP_NESTED_DENSITY_INVESTMENT' and r['new_density_calls']==112 and r['records']==104 and
        r['all104_D_minus_B0']['mean']<0 and r['expanded72_D_minus_B0']['mean']<0,'preserved density stop differs')
    c.require(c.read(upstream/'developer_01/replay_acceptance.json')['status']=='PASS_ALL_SCOPE_NESTED_DENSITY_NATIVE_CPU_REPLAY','complete original CPU acceptance missing')
    audit=c.read(c.RUN/'controller/REMAINING_MECHANISM_READONLY_AUDIT_20261009.json')
    c.require(audit['native_floor_vs_training_nearest_windows_changed']==102 and
        audit['historical_raw_rejected_only_for_json_whitespace']==0 and audit['new_model_calls']==0,'actual train-serving mechanism audit differs')
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');resources={}
    for stage in ('nontest','developer'):
        p=c.RUN/'controller'/('aic_ND_v1_'+stage+'.resource.json');v=c.read(p)
        c.require([x for x in ledger if x.get('name')==v['name']]==[v] and v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'original terminal accounting')
        resources[v['name']]=dict(path=str(p),sha256=c.sha(p),charged_seconds=v['charged_seconds'])
    # The inherited source lock protects old dependencies; retain all completed density bytes.
    upstream_success=[]
    for p in list((upstream/'developer_01').rglob('done.json'))+list((upstream/'nontest_01').rglob('done.json')):
        x=c.read(p)
        for f,s in x['bound_files'].items():c.require(c.sha(f)==s,'completed density raw changed')
        upstream_success.append(dict(path=str(p),sha256=c.sha(p),bound_files=x['bound_files']))
    c.require(len(upstream_success)==120,'old completed density denominator')
    authority=[];model=None;counts=Counter();sampling=[]
    for scope in ('nontest','developer'):
        plan=c.read(c.CAD/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        sources=ex.source_tables(plan)
        for job in jobs:
            # Complete a multi-window job before reconstructing its old B0 request.
            for part in job['windows']:
                original=part['window'];part['base_window']=original
                part['window']=round_window(original,sources[job['source_key']]['pts'])
            for ix,part in enumerate(job['windows']):
                original=part['base_window']
                base=c.checked_base(scope,job,ix)
                if model is None:model=base['model_identity']
                c.require(model==base['model_identity'],'original B0 model differs')
                path=c.base_path(scope,job,ix,cc)
                authority.append(dict(scope=scope,video_id=job['video_id'],index=ix,path=str(path),sha256=c.sha(path),bound_files=base['bound_files']))
                counts[scope]+=1
                a=original['planned_actual_pts_sec'];b=part['window']['planned_actual_pts_sec']
                sampling.append(dict(scope=scope,changed=part['window']!=original,base_physical_frames=len(a),new_physical_frames=len(b),
                    base_max_gap=max((y-x for x,y in zip(a,a[1:])),default=0),new_max_gap=max((y-x for x,y in zip(b,b[1:])),default=0)))
        c.save(c.HERE/'input_01'/(scope+'_plan.json'),plan)
    c.require(dict(counts)=={'nontest':8,'developer':112} and sum(x['changed'] for x in sampling if x['scope']=='developer')==102 and
        all(x['new_physical_frames']==x['base_physical_frames'] for x in sampling),'new nearest64 input mechanism absent')
    c.save(c.HERE/'input_01/resume_manifest.json',dict(rows=authority,counts=dict(counts),model_identity=model,resources=resources,
        preserved_upstream_success=upstream_success,original_density_stop_sha256=c.sha(upstream/'scientific_stop.json'),
        original_density_report_sha256=c.sha(upstream/'developer_01/report.json'),new_round_alignment_success_reused=0,
        changed_windows={scope:sum(x['changed'] for x in sampling if x['scope']==scope) for scope in ('nontest','developer')}))
    c.save(c.HERE/'input_01/sampling_audit.json',dict(records=sampling,all_old_samples_preserved=False,
        unchanged_ordinals_have_exact_original_RGB_authority=True,all_physical_first_last_unchanged=True,
        new_round_alignment_frames_max=64,first_replay_not_full_source_decode=True,
        spatial_resolution_tradeoff='SAME_FRAME_COUNT_AND_GRID_OR_STOP'))
    c.save(c.HERE/'input_01/investment_rule.json',dict(registered_utc=c.utc(),all104_delta_min=0,expanded72_delta_strictly_positive=True,
        native_set_change_required=True,negative_mean_threshold=-.05,negative_group_fraction_threshold=.75,
        bootstrap_draws=10000,bootstrap_seed=20261009,CI_report_only=True,new_round_alignment_weak_direction_read=False,
        observed_development_not_new_holdout=True,coverage='UNKNOWN',training_admitted=False))
    c.save(c.HERE/'prepared.json',dict(status='PASS_EXACT_DENSITY_STOP_AND_NATIVE_NEAREST_PLAN',utc=c.utc(),
        records=104,groups=96,developer_windows=112,nontest_windows=8,new_model_calls=0,new_optimizer_updates=0,
        original_baseline_calls_reused=120,new_round_alignment_calls_required=sum(x['changed'] for x in sampling),
        exact_unchanged_input_success_reused=sum(not x['changed'] for x in sampling),registered_original_density_stop=True))
    print(c.read(c.HERE/'prepared.json'),flush=True)

if __name__=='__main__':main()
