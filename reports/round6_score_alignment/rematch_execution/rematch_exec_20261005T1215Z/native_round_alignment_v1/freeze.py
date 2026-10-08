"""Freeze all old dependencies and exact completed receipts once."""
import nr_common as c

def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    cpu=c.read(c.HERE/'cpu_acceptance.json')
    c.require(cpu['status']=='PASS_ALL120_NATIVE_NEAREST_PROCESSOR_AND_COMMON_PIXEL_IDENTITY','CPU not admitted')
    prompt_proof=c.RUN/'controller/NRA_future_V14_prompt_contract_20261009.json'
    c.require(c.read(prompt_proof)['status']=='PASS_EXACT_OLD_V14_NEW_CONSUMER_B0_FULL_PROCESSOR_PROMPT','V14 consumer prompt authority missing')
    path=c.RUN/'nested_density_v1/source_lock.json';files=dict(c.read(path)['files']);files[str(path)]=c.sha(path)
    for p in (c.RUN/'nested_density_v1').rglob('*.json'):
        if p.name in ('scientific_stop.json','report.json','replay_acceptance.json','first_real_acceptance.json','developer.completion.json','nontest.completion.json','independent_validation.json','package.stage.json'):
            files[str(p)]=c.sha(p)
    for p in (c.RUN/'controller/REMAINING_MECHANISM_READONLY_AUDIT_20261009.json',prompt_proof,
        c.RUN/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl',
        c.RUN/'teacher_student_autopilot_v14/rematch_01/temporal.stage.json',
        c.RUN/'teacher_student_autopilot_v14/student_01/student_completion.json',
        c.RUN/'teacher_student_autopilot_v14/completion.json'):
        files[str(p)]=c.sha(p)
    for p in (c.RUN/'b_prompt_recovery_v1').rglob('*.json'):
        if p.name in ('scientific_stop.json','report.json','replay_acceptance.json','developer.completion.json'):files[str(p)]=c.sha(p)
    for p in (c.RUN/'b_boundary_diagnostic_v1/matched_rows.json',c.CAD/'scientific_stop.json'):
        files[str(p)]=c.sha(p)
    resume=c.read(c.HERE/'input_01/resume_manifest.json')
    for row in resume['rows']+resume['preserved_upstream_success']:
        files[row['path']]=row['sha256'];files.update(row['bound_files'])
    for row in resume['resources'].values():files[row['path']]=row['sha256']
    rt,ex,cc,student,old,frames,production=c.helpers()
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    for name in ('student_train','nontest_temporal','rematch_temporal'):
        p=c.RUN/'controller'/('rematch_TAUTO_v14_'+name+'.resource.json');v=c.read(p)
        c.require(v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0 and
            [x for x in ledger if x.get('name')==v['name']]==[v],'preserved V14 original terminal accounting')
        files[str(p)]=c.sha(p)
    for p in c.HERE.rglob('*'):
        if p.is_file() and (p.suffix in ('.py','.md') or p.parent.name=='input_01' or p.name in ('prepared.json','cpu_acceptance.json')):
            files[str(p)]=c.sha(p)
    for p,s in files.items():c.require(c.sha(p)==s,'pre-freeze identity changed: '+p)
    c.save(c.HERE/'source_lock.json',{'schema':'AIC_NATIVE_ROUND_ALIGNMENT_V1','files':files,
        'utc':c.utc(),'new_model_calls_at_freeze':0,'optimizer_updates_at_freeze':0})
    c.save(c.HERE/'preflight.json',{'status':'PASS_FROZEN_NATIVE_ROUND_ALIGNMENT_CPU_BINDING','utc':c.utc(),
        'source_lock_sha256':c.sha(c.HERE/'source_lock.json'),'cpu_acceptance_sha256':c.sha(c.HERE/'cpu_acceptance.json'),
        'new_processor_calls':0,'original_CPU_acceptance_reused':True,'new_model_calls':0})
    print({'files':len(files),'source_lock_sha256':c.sha(c.HERE/'source_lock.json')},flush=True)

if __name__=='__main__':main()
