"""Exact v1 G0 reuse; actual pinned rejection reproduction and v2-only flag repair."""
from pathlib import Path
import ast
import shutil
import socket
import sys
from sg8_common import HERE,RUN,read,rows,sha,digest,save,require,utc,state,old_helpers,verify

def main():
    require(socket.gethostname()=='inspur-NP5570M5' and not (HERE/'source_lock.json').exists(),'already frozen or wrong host')
    previous=RUN/'spatial_gap8_pchip_slot4_v1';old_lock=read(previous/'source_lock.json')
    require(sha(previous/'source_lock.json')=='8de7a100a3a4664b0fa5ec0c24ea2c3867c1ce0f4559f567b48963b2f72cc9d4','original v1 lock changed')
    failure=read(previous/'diagnostic_01/engine_failure.json')
    require('base/vision became trainable during reload' in failure['traceback'] and
        not list((previous/'diagnostic_01/new').glob('*/raw.json')) and not (previous/'diagnostic_01/model.json').exists(),
        'not the registered before-generation rejection')
    ledger=rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    failed_resource=RUN/'controller/aic_SG8_slot4_v1_diagnostic.resource.json';cost=read(failed_resource)
    require(cost['status']=='failed' and cost['exit_code']==1 and cost['stop_reason'] is None and cost['charged_seconds']>0 and
        sum(v==cost for v in ledger)==1,'original failed GPU cost must remain uniquely charged')
    for p,h in old_lock['files'].items():require(sha(p)==h,'v1 frozen dependency changed: '+p)
    # Exact original CPU interfaces and sealed sample are copied internally, never regenerated.
    shutil.copytree(previous/'input_01',HERE/'input_01',copy_function=shutil.copy2)
    for p in previous.glob('g0_*.json'):
        if 'failure' not in p.name and p.name!='g0_admission.json':shutil.copy2(p,HERE/p.name)
    for old in (previous/'input_01').rglob('*'):
        if old.is_file():require(sha(old)==sha(HERE/'input_01'/old.relative_to(previous/'input_01')),'exact input byte reuse failed')
    common,_,_=old_helpers()
    import torch
    from verify_saved_smoke import canonical_frozen_hash
    small=torch.nn.Linear(2,2)
    before={n:p.detach().clone() for n,p in small.named_parameters()}
    rejected=None
    try:canonical_frozen_hash(small,torch)
    except Exception as e:rejected=type(e).__name__+': '+str(e)
    require(rejected and 'base/vision became trainable during reload' in rejected,'actual pinned old symptom did not reproduce')
    for p in small.parameters():p.requires_grad_(False)
    value=canonical_frozen_hash(small,torch)
    require(value['parameters']==6 and all(torch.equal(before[n],p.detach()) and not p.requires_grad for n,p in small.named_parameters()),
        'repair changed parameter values or failed actual validator')
    old_engine=(previous/'sg8_engine.py').read_text();new_engine=(HERE/'sg8_engine.py').read_text()
    require(new_engine==old_engine.replace('    model.model.eval()\n',
        '    model.model.eval()\n    for parameter in model.model.parameters():parameter.requires_grad_(False)\n'),
        'unexpected generation/scientific engine change')
    for name in ['sg8_math.py','sg8_independent_math.py','sg8_sampling.py','sg8_field.py','sg8_independent_field.py',
        'sg8_prepare.py','sg8_replay.py','sg8_report.py','sg8_packager.py','sg8_launch.py']:
        require(sha(HERE/name)==sha(previous/name),'scientific/input/generation dependency changed: '+name)
    save(HERE/'g0_engineering_cpu.json',dict(status='PASS_PINNED_REQUIRES_GRAD_REJECTION_AND_VALUE_PRESERVING_REPAIR_CPU',utc=utc(),
        reproduced_error=rejected,after_hash=value,all_parameter_bytes_identical=True,
        original_source_lock_sha256=sha(previous/'source_lock.json'),original_failure_sha256=sha(previous/'diagnostic_01/engine_failure.json'),
        original_failed_resource_sha256=sha(failed_resource),original_failed_GPU_charge_seconds=cost['charged_seconds'],
        original_raw_count=0,new_model_calls=0,new_decoder_calls=0,new_optimizer_updates=0,original_native_CPU_repeated=False))
    admission=read(previous/'g0_admission.json')
    admission.update(utc=utc(),engineering_version=2,original_G0_admission_sha256=sha(previous/'g0_admission.json'),
        engineering_repair_cpu_sha256=sha(HERE/'g0_engineering_cpu.json'),
        ledger_prefix_records=len(ledger),ledger_prefix_digest=digest(ledger),original_failed_GPU_charge_seconds=cost['charged_seconds'],
        original_component_CPU_repeated=False,original_sample_seal_and_all_88_native_bytes_exact=True)
    save(HERE/'g0_admission.json',admission)
    bound=dict(old_lock['files']);bound[str(previous/'source_lock.json')]=sha(previous/'source_lock.json')
    bound[str(previous/'diagnostic_01/engine_failure.json')]=sha(previous/'diagnostic_01/engine_failure.json')
    bound[str(previous/'execution_failure.json')]=sha(previous/'execution_failure.json')
    bound[str(failed_resource)]=sha(failed_resource)
    for p in HERE.rglob('*'):
        if p.is_file() and ('prelock_repairs' not in p.parts) and p.name not in ('deploy_cpu_only.py','CONTINUE.md'):
            if p.suffix=='.py':ast.parse(p.read_bytes(),filename=str(p))
            bound[str(p)]=sha(p)
    quick={p:h for p,h in bound.items() if (str(HERE) in p or p.endswith('.py')) and not p.endswith('.pt')}
    save(HERE/'source_lock.json',dict(route=HERE.name,utc=utc(),files=bound,quick_files=quick,
        original_G0_source_lock_sha256=sha(previous/'source_lock.json'),scientific_algorithm='spatial_gap8_pchip_slot4_v1',
        engineering_only_requires_grad_repair=True,original_sources_protected=True,sample_and_formula_frozen_before_probe_reveal=True))
    verify()
    save(HERE/'preflight.json',dict(status='PASS_FROZEN_SG8_NATIVE_G0_AND_ALL_BOUND_BYTES',utc=utc(),
        source_lock_sha256=sha(HERE/'source_lock.json'),frozen_files=len(bound),new_model_calls=0,new_optimizer_updates=0,
        engineering_CPU_repair_pass=True,original_all_88_native_CPU_exact_reference=True))
    state('G0_V2_ENGINEERING_PREFLIGHT_PASS_SINGLE_LAUNCH_PENDING',new_spatial_calls=0,
        source_lock_sha256=sha(HERE/'source_lock.json'),frozen_files=len(bound))

if __name__=='__main__':main()
