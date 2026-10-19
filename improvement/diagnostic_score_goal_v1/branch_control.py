"""One explicit CPU or shared-GPU stage. Never repeats a claimed stage."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

from branch_pilot import PYTHON, WORK, require, read, save, ref, utc, check_registration


def run(root, group, phase):
    reg = check_registration(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') != '', 'Controller keeps explicit physical CUDA index')
    claim = root/('branch_'+group+'_'+phase+'_claim_03.json')
    save(claim, dict(pid=os.getpid(), utc=utc(), phase=phase, group=group,
                    registration=ref(root/'branch_registration_03.json')))
    entries = []
    try:
        commands = []
        base = [str(PYTHON), '-B', '-u', str(root/'branch_code_03/branch_pilot.py')]
        if phase == 'cpu':
            commands = [('prepare', base+['prepare','--root',str(root),'--group',group], True),
                        ('input_qa', base+['input_qa','--root',str(root),'--group',group], True)]
        else:
            require((root/('branch_'+group+'_03/input_acceptance.json')).is_file(), 'All real input QA must precede GPU claim')
            require(group == 'dev' or (root/'branch_confirm_admission_04.json').is_file(),
                    'Confirmation needs explicit frozen dev capability decision')
            name = reg['GPU_jobs'][group]
            wrapper = WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
            remaining = int((dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))-
                             dt.datetime.now(dt.timezone.utc)).total_seconds())
            require(remaining >= reg['max_GPU_job_seconds']+120, 'Leave time for native/output QA within10h')
            command = [str(PYTHON), '-B', str(wrapper), '--name', name,
                       '--max-seconds', str(reg['max_GPU_job_seconds']), '--planned-output-bytes','1200000000',
                       '--capacity-reason','New finite branch likelihoods only; accepted cached visual input references, measured idle GPU and raw decision-logit estimate under1.2GB with30GB available; no duplicated media',
                       '--queue-seconds','60','--']+base+['infer','--root',str(root),'--group',group]
            commands = [('GPU',command,False), ('output_qa',base+['output_qa','--root',str(root),'--group',group],True)]
        for name, command, cpu in commands:
            env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
            if cpu:
                env['CUDA_VISIBLE_DEVICES'] = ''
            with (root/('branch_'+group+'_'+name+'_03.log')).open('xb') as log:
                process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                                           stdin=subprocess.DEVNULL)
                stat = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()
                entry = dict(stage=name, argv=command, pid=process.pid, start_ticks=stat[19], CPU_child=cpu)
                save(root/('branch_'+group+'_'+name+'_launch_03.json'),entry)
                entries.append(entry)
                code = process.wait()
                require(code == 0, 'First stage naturally failed: '+name+' exit='+str(code))
        if phase == 'gpu':
            resource = WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'/(reg['GPU_jobs'][group]+'.resource.json')
            record = read(resource)
            ledger = [json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                      if line.strip() and json.loads(line).get('name') == reg['GPU_jobs'][group]]
            require(record['status'] == 'completed' and record['exit_code'] == 0
                    and ledger == [record], 'One actual shared GPU natural terminal required')
            save(root/('branch_'+group+'_resource_03.json'), dict(resource=ref(resource), record=record,
                 unique_ledger_entries=1, complete_branch_readout_not_quality=True))
        save(root/('branch_'+group+'_'+phase+'_terminal_03.json'), dict(status='NATURAL_COMPLETE_REGISTERED_STAGES',
             exit_code=0, entries=entries, utc=utc(), no_426_or_package_started=True))
    except BaseException as error:
        save(root/('branch_'+group+'_'+phase+'_failure_03.json'),dict(error=repr(error), traceback=traceback.format_exc(),
             entries=entries, preserve_all_success=True, no_automatic_retry=True, utc=utc()))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--group',choices=['dev','confirm'],required=True)
    p.add_argument('--phase',choices=['cpu','gpu'],required=True)
    a = p.parse_args()
    run(a.root,a.group,a.phase)
