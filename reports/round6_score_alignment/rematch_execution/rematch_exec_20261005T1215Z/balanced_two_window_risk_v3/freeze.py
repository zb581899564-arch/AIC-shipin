import bw_common as c
def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    c.require(c.read(c.HERE/'cpu_acceptance.json')['status']=='PASS_ALL_CHANGED_BALANCED_NATIVE_PROCESSOR_AND_EXACT_BOUNDARIES','CPU admission missing')
    c.require(c.read(c.HERE/'prefix_cpu_acceptance.json')['status']=='PASS_EXISTING_PINNED_GRAMMAR_EXACT_FRACTION_DURATION','actual Fraction grammar acceptance missing')
    c.require(c.read(c.HERE/'engineering_handoff.json')['status']=='PASS_V2_TYPE_REPRESENTATION_REPAIR_EXACT_RAW_CPU_AND_NT_HANDOFF','actual engineering CPU recovery missing')
    previous=c.RUN/'balanced_two_window_risk_v2/source_lock.json';files=dict(c.read(previous)['files']);files[str(previous)]=c.sha(previous)
    for row in c.read(c.HERE/'engineering_handoff.json')['references']:files[row['path']]=row['sha256']
    resume=c.read(c.HERE/'input_01/resume_manifest.json')
    for row in resume['rows']:files[row['path']]=row['sha256'];files.update(row['bound_files'])
    for p in c.HERE.rglob('*'):
        if p.is_file() and p.suffix!='.log' and p.name not in ('progress.json','CONTINUE.md','source_lock.json','preflight.json','start.json','registration.json','controller.log','controller.lock','launch.lock'):
            files[str(p)]=c.sha(p)
    for p,s in files.items():c.require(c.sha(p)==s,'pre-freeze source changed: '+p)
    c.save(c.HERE/'source_lock.json',dict(schema='AIC_BALANCED_TWO_WINDOW_USER_ACCEPTED_RISK_V1',files=files,utc=c.utc(),
        scientific_recipe='exact two equal windows only when original two-window duration strictly between30and60',new_model_calls_at_freeze=0))
    c.save(c.HERE/'preflight.json',dict(status='PASS_FROZEN_BALANCED_TWO_WINDOW_CPU_BINDING',utc=c.utc(),source_lock_sha256=c.sha(c.HERE/'source_lock.json')))
    print(dict(files=len(files),source_lock_sha256=c.sha(c.HERE/'source_lock.json')),flush=True)
if __name__=='__main__':main()
