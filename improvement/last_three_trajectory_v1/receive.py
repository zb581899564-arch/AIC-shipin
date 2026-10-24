"""Receive only final ZIPs and short delivery manifests; verify exact Linux bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

POLICIES=('pchip','median3','shot_representative')
LABELS=('LAST_THREE_G01_CURVE_20261024','LAST_THREE_G02_MEDIAN_20261024','LAST_THREE_G03_SHOT_20261024')
ROOT='/home/inspur/aic_video_work/last_three_trajectory_20261024_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    repo=Path(__file__).resolve().parents[2]
    workspace=repo.parents[1]
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12','aic-inspur-home','python3','-']
    remote="from pathlib import Path; import json; r=Path('"+ROOT+"'); d=json.loads((r/'completion.json').read_text()); assert d['status']=='THREE_DISTINCT_COMPLETE_RISK_PACKAGES_READY'; print(json.dumps(d))"
    response=subprocess.run(command,input=remote,text=True,capture_output=True,timeout=30)
    if response.returncode:
        raise RuntimeError(response.stderr)
    summary=json.loads(response.stdout)
    spec=importlib.util.spec_from_file_location('portable_receive',repo/'improvement/final_sprint_v1/verify_received.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    accepted=[]
    for policy,label,delivery in zip(POLICIES,LABELS,summary['deliveries']):
        if delivery['candidate_id'] != 'g_risk_'+policy or delivery['status'] != 'ENGINEERING_ACCEPTED_QUALITY_UNVALIDATED':
            raise ValueError('Unexpected candidate identity or acceptance')
        destination=workspace/'deliveries'/label
        destination.mkdir(exist_ok=True,parents=True)
        for remote_path,local_path in [(ROOT+'/'+policy+'/package/delivery.json',destination/'delivery.json'),
                                       (delivery['zip_path'],destination/Path(delivery['zip_path']).name)]:
            if local_path.exists():
                if local_path.suffix=='.zip' and local_path.stat().st_size==delivery['zip_bytes'] and sha(local_path)==delivery['zip_sha256']:
                    continue
                if local_path.name=='delivery.json' and json.loads(local_path.read_text())==delivery:
                    continue
                raise FileExistsError('Existing local bytes differ; inspect explicit transfer failure before recovery')
            result=subprocess.run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
                'aic-inspur-home:'+remote_path,str(local_path)],capture_output=True,text=True,timeout=180)
            if result.returncode:
                raise RuntimeError(result.stderr)
        zip_path=destination/Path(delivery['zip_path']).name
        verification=module.verify(destination/'delivery.json',zip_path)
        verification.update(policy=policy,absolute_zip_path=str(zip_path),absolute_delivery_path=str(destination/'delivery.json'),
                            changes_from_4048=delivery['changes_from_4048'],model_params_b=delivery['model_params_b'])
        accepted.append(verification)
        print(json.dumps(verification),flush=True)
    report=workspace/'reports/last_three_trajectory_20261024_v1/windows_delivery.json'
    report.parent.mkdir(exist_ok=True,parents=True)
    with report.open('x',encoding='utf-8') as f:
        json.dump(dict(status='THREE_FINAL_ZIP_WINDOWS_ACCEPTED',deliveries=accepted,
            unchanged_4048_4047=True,quality_unvalidated=True,official_scores_unknown=True),f,indent=2)


if __name__=='__main__':
    main()
