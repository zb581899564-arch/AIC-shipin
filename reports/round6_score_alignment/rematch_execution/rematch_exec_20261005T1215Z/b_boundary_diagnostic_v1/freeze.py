"""Bind original C successes and the independent new diagnostic before launch."""
import bdiag_common as c


def main():
    c.require(not (c.HERE/'source_lock.json').exists(),'already frozen')
    proof=c.read(c.HERE/'cpu_acceptance.json')
    c.require(proof['status']=='PASS_EXACT_C_STOP_AND_B_MATCHED_NATIVE_CPU_INTERFACES' and proof['new_32B_calls']==0,'actual CPU admission')
    old=c.read(c.CAD/'source_lock.json');files=dict(old['files'])
    paths=[c.CAD/'source_lock.json',c.CAD/'scientific_stop.json',c.CAD/'fallback_s_inventory.json',c.CAD/'fallback_b_diagnostic_handoff.json']
    paths += list((c.HERE/'input_01').rglob('*')) + list((c.HERE/'cpu_01').rglob('*'))
    paths += [p for p in c.HERE.iterdir() if p.suffix in ('.py','.md') or p.name in ('cpu_acceptance.json','prepared.json')]
    for done in c.CAD.rglob('done.json'):
        value=c.read(done);paths.append(done)
        for p,wanted in value['bound_files'].items():
            c.require(c.sha(p)==wanted,'original successful attempt changed');files[p]=wanted
    for p in (c.CAD/'developer_01').glob('full.*.json'):paths.append(p)
    paths.append(c.RUN/'controller/aic_CAD_v1_full.resource.json')
    for p in paths:
        if p.is_file():files[str(p)]=c.sha(p)
    for p,wanted in files.items():c.require(c.sha(p)==wanted,'frozen byte mismatch: '+p)
    c.save(c.HERE/'source_lock.json',{'schema':'AIC_MATCHED_32B_BOUNDARY_DIAGNOSTIC_V1','files':files,
        'C_source_lock_sha256':c.sha(c.CAD/'source_lock.json'),'cpu_acceptance_sha256':c.sha(c.HERE/'cpu_acceptance.json'),
        'new_model_calls_at_freeze':0,'optimizer_updates_at_freeze':0,'not_training_or_final_package':True})
    c.save(c.HERE/'preflight.json',{'status':'PASS_FROZEN_B_DIAGNOSTIC_CPU_BINDING','utc':c.utc(),
        'source_lock_sha256':c.sha(c.HERE/'source_lock.json'),'frozen_files':len(files),
        'original_CPU_proof_reused':True,'new_model_calls':0,'optimizer_updates':0})
    print('PASS_FROZEN_B_DIAGNOSTIC_CPU_BINDING',len(files),c.sha(c.HERE/'source_lock.json'),flush=True)


if __name__=='__main__':main()
