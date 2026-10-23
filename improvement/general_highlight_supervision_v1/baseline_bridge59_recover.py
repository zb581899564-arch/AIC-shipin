"""First CPU review adopts all57 forwards; failed post-flag GPU ledger stays failed."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import json
import subprocess
import traceback
from common import ROOT as ADMISSION,WORK,read,ref,save
from time_control50_common import RUN,PY,checked

ROOT=ADMISSION/'baseline_bridge59';DATA=ADMISSION/'baseline_bridge57'
JOB='sportclip_diving_full_VERIFY_semantic_baseline_20261022_v57'


def peft_contract():
    import torch
    from peft import get_peft_model,LoraConfig
    class Tiny(torch.nn.Module):
        def __init__(self):super().__init__();self.fc=torch.nn.Linear(2,2)
        def forward(self,input_ids=None,**kwargs):return self.fc(input_ids)
    model=get_peft_model(Tiny(),LoraConfig(r=1,lora_alpha=1,target_modules=['fc'],bias='none')).eval()
    for p in model.parameters():p.requires_grad_(False)
    flags=[(p,p.requires_grad) for p in model.parameters()]
    weights={k:v.detach().clone() for k,v in model.state_dict().items()}
    with model.disable_adapter():pass
    changed=sum(p.requires_grad!=flag for p,flag in flags)
    for p,flag in flags:p.requires_grad_(flag)
    if not changed or any(p.requires_grad for p in model.parameters()):raise ValueError('Installed PEFT flag side effect/fix not reproduced')
    if any(not torch.equal(weights[k],v) for k,v in model.state_dict().items()):raise ValueError('Synthetic flags changed tensor weights')
    return dict(state='PASS',synthetic_only=True,real8B_calls=0,changed_flags=changed,
        restored_flags_exact=True,tensor_values_unchanged=True,no_forward_or_backward_or_optimizer=True)


def main():
    ROOT.mkdir();resource=read(RUN/'controller'/(JOB+'.resource.json'))
    ledger=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status']!='failed' or resource['exit_code']!=1 or [r for r in ledger if r.get('name')==JOB]!=[resource]:
        raise ValueError('Actual failed postguard GPU terminal differs')
    log=RUN/'controller'/(JOB+'.log');text=log.read_text()
    if ('trained B adapter disabled or a parameter trainable' not in text or
        'adapter_identity' not in text or not (DATA/'semantic_GPU_completion.json').exists()):
        raise ValueError('Not the narrowly registered post-flag failure')
    lock=read(DATA/'source_input_lock.json')
    for identity in list(lock['code'].values())+list(lock['dependencies'].values()):checked(identity)
    verify=read(DATA/'verify_GPU_completion.json');semantic=read(DATA/'semantic_GPU_completion.json')
    if (len(verify['outputs'])!=lock['expected_VERIFY_calls'] or len(semantic['outputs'])!=lock['expected_semantic_batches']
            or semantic['actual_target_queries']!=lock['expected_semantic_queries']):
        raise ValueError('A first model output is missing; no adoption permitted')
    for identity in verify['outputs']+semantic['outputs']:checked(identity)
    engine=RUN/'b_score_aligned_package_v4/engine.py'
    if ref(engine)['sha256']!='73be89785dad2585c16713373ddfc561153c11289a9f6528962a16c01e7a9e6d':
        raise ValueError('Canonical weight-check control flow differs')
    save(ROOT/'adoption_registration.json',dict(actual_failed_resource=ref(RUN/'controller'/(JOB+'.resource.json')),
        actual_failure_detail=ref(log),source_lock=ref(DATA/'source_input_lock.json'),
        first_saved_VERIFY_outputs=len(verify['outputs']),first_saved_semantic_batches=len(semantic['outputs']),
        first_saved_semantic_target_queries=semantic['actual_target_queries'],
        evidence='Reached canonical adapter_identity final flags require after all288 tensor byte-value comparisons; short-circuit expression reached adapter check only after frozen base comparison matched. No optimizer/backward in locked inference source.',
        actual_post_exit_parameter_flags_not_observable=True,
        no_claim_that_original_GPU_exit_was_success=True,no_ledger_rewrite=True,
        original_model_outputs_not_repeated=True,CPU_review_not_previously_run=True))
    save(ROOT/'synthetic_PEFT_flag_contract.json',peft_contract())
    if (DATA/'review.json').exists() or (DATA/'independent_CPU_audit.json').exists():
        raise ValueError('First CPU review already exists; do not repeat')
    command=[str(PY),'-B','-u',str(Path(__file__).parent/'baseline_bridge57_review.py')]
    with (ROOT/'first_CPU_review.log').open('x') as output:
        result=subprocess.run(command,stdout=output,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
    save(ROOT/'CPU_review_terminal.json',dict(exit_code=result.returncode,command=command))
    if result.returncode:raise RuntimeError('Actual first independent CPU review failed; all model outputs retained')
    protected=read(DATA/'registration.json')['protected_baseline'];checked(protected)
    save(ROOT/'completion.json',dict(state=read(DATA/'review.json')['state'],review=ref(DATA/'review.json'),
        independent_CPU=ref(DATA/'independent_CPU_audit.json'),adoption=ref(ROOT/'adoption_registration.json'),
        original_GPU_status='failed',original_failed_GPU_seconds=resource['charged_seconds'],
        all_model_outputs_complete=True,only_post_flag_guard_failed=True,
        new_GPU_calls=0,new_training=0,new_ZIP=0,baseline40_47_unchanged=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),no_model_success_repeat=True))
        raise
