"""Exclusive main registration after CPU tests and accepted smoke addendum."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from full_contract import SCOPE,verify_lock,validate_config,validate_authority
from sft_contract import require,sha256,LORA_PARAMS

HERE=Path(__file__).resolve().parent
RUN=HERE.parent; ROOT=RUN.parents[2]; CTRL=RUN/'controller'

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--expected-lock',required=True); args=parser.parse_args()
    lock_path=HERE/'source_lock.json'; verify_lock(lock_path,args.expected_lock)
    config_path=HERE/'config.json'; config=json.loads(config_path.read_text()); validate_config(config)
    authority_path=HERE/'authorization.json'; validate_authority(json.loads(authority_path.read_text()))
    acceptance=json.loads((CTRL/'sft8b_smoke_acceptance_01.json').read_text())
    original=json.loads((RUN/'temporal_sft8b_v1/smoke_01/train_report.json').read_text())
    reload_path=RUN/'temporal_sft8b_v1/saved_adapter_check_01/verification_report.json'
    reload=json.loads(reload_path.read_text())
    require(acceptance['status']=='PASS_FIVE_UPDATE_SMOKE_WITH_RELOAD_ADDENDUM' and
        acceptance['original_training_report_sha256']==sha256(RUN/'temporal_sft8b_v1/smoke_01/train_report.json') and
        acceptance['reload_addendum_sha256']==sha256(reload_path) and original['optimizer_steps']==5 and
        original['effective_batches']==80 and reload['status']=='PASS_SAVED_ADAPTER_SEMANTIC_RELOAD_ADDENDUM',
        'five-update engineering acceptance invalid')
    for name in ['rematch_sft8b_smoke_02','rematch_sft8b_saved_adapter_check_01']:
        resource=json.loads((CTRL/(name+'.resource.json')).read_text())
        require((resource['status']=='failed' and resource['exit_code']==4) if name.endswith('smoke_02')
                else (resource['status']=='completed' and resource['exit_code']==0),'prior job receipt unexpected')
    compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip()
    require(not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists(), 'shared GPU conflict; untouched')
    planned=LORA_PARAMS*4+3620*8192*32+(1<<27)
    work=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0]); free=shutil.disk_usage(ROOT).free
    require(work+planned<=json.loads((ROOT/'resource_policy.json').read_text())['added_disk_budget_gib']*2**30 and
            free>=planned,'measured capacity cannot cover full final adapter/evidence')
    admission=dict(scope=SCOPE,authorized=True,source_lock_sha256=args.expected_lock,
        config_sha256=sha256(config_path),authority=dict(path=str(authority_path),sha256=sha256(authority_path)),
        resource_preflight_pass=True,shared_gpu_queue_approved=True,disk_peak_within_80gib=True,
        planned_output_bytes=planned,work_bytes=work,free_bytes=free,formal_c_bce_admitted=False,
        full_training_admitted=True,smoke_acceptance_sha256=sha256(CTRL/'sft8b_smoke_acceptance_01.json'))
    path=HERE/'admission.json'
    with path.open('x') as stream: stream.write(json.dumps(admission,indent=2)+'\n')
    subprocess.run([sys.executable,'-B',str(HERE/'train_full.py'),'--config',str(config_path),'--admission',str(path),
        '--lock',str(lock_path),'--expected-lock',args.expected_lock,'--check-only'],check=True)
    print(json.dumps(dict(status='REGISTERED_FULL_8B_AND_BYTE_CONTRACT_PASSED',admission_sha256=sha256(path),
                         planned_output_bytes=planned,training_started=False)),flush=True)
