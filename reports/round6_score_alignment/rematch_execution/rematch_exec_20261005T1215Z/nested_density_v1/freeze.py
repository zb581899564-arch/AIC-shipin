"""Freeze all old dependencies and exact completed receipts once."""
import nd_common as c

def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    cpu=c.read(c.HERE/'cpu_acceptance.json')
    c.require(cpu['status']=='PASS_ALL120_ACTUAL_NESTED_NATIVE_PROCESSOR_AND_BASE_PIXEL_IDENTITY','CPU not admitted')
    path=c.RUN/'b_prompt_recovery_v1/source_lock.json';files=dict(c.read(path)['files']);files[str(path)]=c.sha(path)
    for p in (c.RUN/'b_prompt_recovery_v1').rglob('*.json'):
        if p.name in ('scientific_stop.json','report.json','replay_acceptance.json','developer.completion.json'):files[str(p)]=c.sha(p)
    for p in (c.RUN/'b_boundary_diagnostic_v1/matched_rows.json',c.CAD/'scientific_stop.json'):
        files[str(p)]=c.sha(p)
    resume=c.read(c.HERE/'input_01/resume_manifest.json')
    for row in resume['rows']+resume['preserved_upstream_success']:
        files[row['path']]=row['sha256'];files.update(row['bound_files'])
    for row in resume['resources'].values():files[row['path']]=row['sha256']
    for p in c.HERE.rglob('*'):
        if p.is_file() and (p.suffix in ('.py','.md') or p.parent.name=='input_01' or p.name in ('prepared.json','cpu_acceptance.json')):
            files[str(p)]=c.sha(p)
    for p,s in files.items():c.require(c.sha(p)==s,'pre-freeze identity changed: '+p)
    c.save(c.HERE/'source_lock.json',{'schema':'AIC_NESTED_NATIVE_DENSITY_V1','files':files,
        'utc':c.utc(),'new_model_calls_at_freeze':0,'optimizer_updates_at_freeze':0})
    c.save(c.HERE/'preflight.json',{'status':'PASS_FROZEN_NESTED_DENSITY_CPU_BINDING','utc':c.utc(),
        'source_lock_sha256':c.sha(c.HERE/'source_lock.json'),'cpu_acceptance_sha256':c.sha(c.HERE/'cpu_acceptance.json'),
        'new_processor_calls':0,'original_CPU_acceptance_reused':True,'new_model_calls':0})
    print({'files':len(files),'source_lock_sha256':c.sha(c.HERE/'source_lock.json')},flush=True)

if __name__=='__main__':main()
