"""One read-only SSH check of current host/resources and existing B source records."""
import base64
import json
import shlex
import subprocess
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2]/'reports/human_reference_iteration_20261013_v1'
SCRIPT = r'''import os,socket,json,hashlib,subprocess,datetime
from pathlib import Path
host=socket.gethostname()
if host!='inspur-NP5570M5': raise ValueError('Unexpected remote host identity')
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
legacy=Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
def read(path):return json.loads(path.read_text())
memory={}
for line in Path('/proc/meminfo').read_text().splitlines():
    key,value=line.split(':',1)
    if key in ('MemTotal','MemAvailable','SwapFree'):memory[key]=value.strip()
disk=os.statvfs(run)
gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True,capture_output=True,timeout=15)
gpu_jobs=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True,capture_output=True,timeout=15)
owned=[]
for path in Path('/proc').iterdir():
    if not path.name.isdigit() or int(path.name)==os.getpid():continue
    try:
        argv=[value.decode(errors='replace') for value in (path/'cmdline').read_bytes().split(b'\0') if value]
        if not argv or not ('python' in Path(argv[0]).name or 'torchrun' in Path(argv[0]).name):continue
        if not any('aic_video_work' in value for value in argv):continue
        fields=(path/'stat').read_text().rsplit(')',1)[1].split()
        owned.append(dict(pid=int(path.name),ppid=int(fields[1]),process_group=int(fields[2]),
                          state=fields[0],argv=argv,io=(path/'io').read_text()))
    except (OSError,ValueError):pass
resources=dict(host=host,architecture=os.uname().machine,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               load=os.getloadavg(),memory=memory,project_disk_available_bytes=disk.f_bavail*disk.f_frsize,
               gpu_query_exit=gpu.returncode,gpu=gpu.stdout.strip(),gpu_compute_processes=gpu_jobs.stdout.strip(),
               actual_owned_python_commands=owned,resource_admission_decision=False)
paths=[legacy/'runtime.py',run/'b_score_aligned_package_v4/engine.py',run/'b_score_aligned_package_v4/contracts.py',
       run/'balanced_two_window_risk_v3/bw_video.py',run/'balanced_two_window_risk_v3/exact_pts.py',
       run/'balanced_two_window_risk_v3/native_frames.py',run/'b_score_aligned_package_v4/config.json',
       run/'temporal_sft8b_full_v1/config.json',run/'temporal_sft8b_full_v1/train_01/train_report.json',
       run/'temporal_sft8b_v1/inputs_01/full_train.jsonl',run/'temporal_sft8b_v1/inputs_01/r7_train_registry.json']
files={str(path):dict(exists=path.is_file(),bytes=path.stat().st_size if path.is_file() else None,
                      sha256=sha(path) if path.is_file() else None) for path in paths}
cfg=read(run/'temporal_sft8b_full_v1/config.json')
manifest=Path(cfg['train_manifest']['path'])
registry_path=Path(cfg['r7_train_registry']['path'])
rows=[json.loads(line) for line in manifest.read_text().splitlines()]
registry=read(registry_path)['records']
train=dict(manifest_path=str(manifest),manifest_sha256=sha(manifest),manifest_matches_frozen_config=sha(manifest)==cfg['train_manifest']['sha256'],
           registry_path=str(registry_path),registry_sha256=sha(registry_path),registry_matches_frozen_config=sha(registry_path)==cfg['r7_train_registry']['sha256'],
           windows=len(rows),parents=len({row['parent_sample_id'] for row in rows}),groups=len({row['source_group'] for row in rows}),
           registry_parents=len(registry),expected_windows=cfg['expected_windows'],expected_parents=cfg['expected_parents'],expected_groups=cfg['expected_groups'],
           all_train_sha_present=all(len(row.get('source_sha256',''))==64 for row in rows),
           all_registry_sha_present=all(len(row.get('source_sha256',''))==64 for row in registry),
           actual_video_content_read=False,labels_exported=False)
b=read(run/'b_score_aligned_package_v4/config.json')
adapter_config=Path(b['b_adapter'])/'adapter_config.json'
result=dict(status='READ_ONLY_CURRENT_RUNTIME_AND_B_TRAINING_PROVENANCE_METADATA',resources=resources,files=files,training_metadata=train,
            b_config_parameters=b['complete_parameters'],b_adapter_expected_sha256=b['b_adapter_sha256'],
            adapter_config_exists=adapter_config.is_file(),new_media_downloads=0,new_video_decodes=0,
            new_processor_or_model_loads=0,new_optimizer_updates=0,source_separation_not_yet_evaluated=True)
print(json.dumps(result,ensure_ascii=False),flush=True)
'''


if __name__ == '__main__':
    output = REPORT/'existing_runtime_readonly_01.json'
    if output.exists():
        raise SystemExit('This successful read-only check already has a receipt; do not repeat it')
    payload = base64.b64encode(SCRIPT.encode()).decode()
    command = 'python3 -u -c '+shlex.quote('import base64;exec(base64.b64decode('+repr(payload)+'))')
    result = subprocess.run(['ssh','-o','StrictHostKeyChecking=yes','-o','BatchMode=yes',
        '-o','ConnectTimeout=12','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',
        'aic-inspur-home',command],capture_output=True,text=True,timeout=55)
    if result.returncode:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or 'Read-only SSH failed')
    receipt = json.loads(result.stdout)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(dict(status=receipt['status'],resources=receipt['resources'],
        missing_files=[path for path,row in receipt['files'].items() if not row['exists']],
        training_metadata=receipt['training_metadata'],model_loads=0),ensure_ascii=False,indent=2))
