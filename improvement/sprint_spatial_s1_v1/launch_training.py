"""One bounded launch after completed preparation; no model or input retries."""
import json
from pathlib import Path
import subprocess


def main():
    script = '''
import json,os,pathlib,socket,subprocess,sys,datetime
r=pathlib.Path('/home/inspur/aic_video_work/sprint_spatial_s1_20261021_v1')
sys.path.insert(0,str(r/'code'))
from common import read,checked,write,baseline_identity,PY
if socket.gethostname()!='inspur-NP5570M5':raise ValueError('Wrong host')
if (r/'training_launch.json').exists() or (r/'training_claim.json').exists():raise FileExistsError('Unique training controller already claimed')
if read(r/'preparation_completion.json')['status']!='S1_CPU_AND762_FROZEN_CENTERS_READY_FOR_CONDITIONED_TRAINING_INPUTS':raise ValueError('Preparation not naturally complete')
if read(r/'centers_terminal.json')['exit_code']!=0:raise ValueError('Center job not complete')
for asset in read(r/'center_source_lock.json')['code'].values():checked(asset)
for asset in read(r/'training_code_acceptance02.json')['files'].values():checked(asset)
if read(r/'training_cpu_contract_acceptance.json')['status']!='PASS':raise ValueError('Torch contracts not passed')
baseline_identity()
snapshot=dict(host=socket.gethostname(),UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 GPU=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
 GPU_processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip(),
 memory_available=[s for s in pathlib.Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')])
write(r/'training_prelaunch_readonly.json',snapshot)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
command=[str(PY),'-u','-B',str(r/'code/training_controller.py')]
with (r/'training_controller.log').open('x') as log:
 p=subprocess.Popen(command,cwd=r,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
out=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],argv=command,
 UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),prelaunch=snapshot)
write(r/'training_launch.json',out)
print(json.dumps(out))
'''
    done = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-tailscale', '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],
        input=script.encode(), capture_output=True, timeout=45)
    receipt = dict(exit_code=done.returncode, stdout=done.stdout.decode(), stderr=done.stderr.decode())
    path = Path(__file__).resolve().parents[2] / 'reports/sprint_spatial_s1_20261021_v1/training_launch03.json'
    with path.open('x', encoding='utf8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False))
    if done.returncode:
        raise RuntimeError('Launch not confirmed; read actual authority before any retry')


if __name__ == '__main__':
    main()
