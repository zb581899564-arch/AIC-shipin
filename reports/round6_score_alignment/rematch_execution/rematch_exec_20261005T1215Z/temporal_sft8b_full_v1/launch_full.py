"""One detached full training job under the unchanged common lock and ledger."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time

from full_contract import verify_lock
from sft_contract import require,sha256

HERE=Path(__file__).resolve().parent; RUN=HERE.parent; CTRL=RUN/'controller'

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--expected-lock',required=True)
    parser.add_argument('--expected-admission',required=True); args=parser.parse_args()
    lock_path=HERE/'source_lock.json'; verify_lock(lock_path,args.expected_lock)
    admission_path=HERE/'admission.json'
    require(sha256(admission_path)==args.expected_admission,'registered full admission changed')
    admission=json.loads(admission_path.read_text())
    for path in [HERE/'launch.json',HERE/'launch_registration.json',CTRL/'rematch_sft8b_full_01.resource.json']:
        require(not path.exists(),'existing full job: do not duplicate '+str(path))
    with (HERE/'launch_registration.json').open('x') as stream:
        stream.write(json.dumps(dict(lock_sha256=args.expected_lock,admission_sha256=args.expected_admission,
                                    launcher_sha256=sha256(__file__)),indent=2)+'\n')
    command=[sys.executable,'-B','-u',str(CTRL/'gpu_run.py'),'--name','rematch_sft8b_full_01',
        '--max-seconds','36000','--planned-output-bytes',str(admission['planned_output_bytes']),
        '--capacity-reason','704_train_724_positive_windows_5_epochs_3620_effective_227_steps_final_adapter_evidence',
        '--queue-seconds','1800','--',sys.executable,'-B','-u',str(HERE/'train_full.py'),
        '--config',str(HERE/'config.json'),'--admission',str(admission_path),
        '--lock',str(lock_path),'--expected-lock',args.expected_lock]
    with (HERE/'background.log').open('xb') as log:
        child=subprocess.Popen(command,cwd=str(HERE),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                               start_new_session=True)
    receipt=dict(status='DETACHED_FULL_8B_GPU_WRAPPER_STARTED',pid=child.pid,
        started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_lock_sha256=args.expected_lock,
        admission_sha256=args.expected_admission,epochs=5,windows=724,effective_batches=3620,updates=227,
        formal_c_bce_admitted=False,test_inference_started=False,uploaded=False)
    with (HERE/'launch.json').open('x') as stream: stream.write(json.dumps(receipt,indent=2)+'\n')
    time.sleep(.5)
    require(child.poll() is None or (CTRL/'rematch_sft8b_full_01.resource.json').exists(),'wrapper exited before receipt')
    print(json.dumps(receipt),flush=True)
