"""Deploy only small control code via the already-authorized strict direct SSH."""
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile


def main():
    directory=Path(__file__).resolve().parent
    files={'code/'+p.name:p.read_bytes() for p in directory.glob('*.py') if p.name != 'deploy.py'}
    for name,data in files.items():
        compile(data,name,'exec')
    rules=dict(schema='CURRENT_RULE_REVIEW_FOR_REGISTERED_CPU_TRAJECTORY_RISK',
        checked_utc=datetime.now(timezone.utc).isoformat(),
        primary='https://www.aicomp.cn/tracks/tracks-6/4267.html',
        notice='https://www.aicomp.cn/notice/notice-3/5307.html',
        catalog='https://www.aicomp.cn/notice/notice-3',
        current_main_notice_catalog_and_three_linked_PDFs_read=True,
        attachment_links_match_prior_review=True,attachment_byte_equality_not_claimed=True,
        observed_constraints=dict(actual_all_models_max=9000000000,official_data_stays_local=True,
            no_test_training_pseudolabels_manual_correction_or_reverse_rules=True,all_outputs_automatic_reproducible=True),
        existing_page_deadline='2026-10-23T20:00:00+08:00',
        human_reported_extension='2026-10-24T12:00:00+08:00',
        extension_not_independently_present_in_public_notice=True,
        account_already_accepted_two_after_midnight=True,account_real_quota_and_deadline_will_be_respected=True,
        interpretation_not_special_organizer_permission=True,
        new_calls_training_downloads=0,quality_unvalidated=True)
    files['official_rule_check_before_package.json']=json.dumps(rules,indent=2).encode()
    manifest={n:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for n,v in files.items()}
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in files.items():z.writestr(n,v)
    payload=buffer.getvalue();digest=hashlib.sha256(payload).hexdigest()
    remote='''import base64,hashlib,io,json,os,pathlib,subprocess,zipfile
root=pathlib.Path('/home/inspur/aic_video_work/last_three_trajectory_20261024_v1')
assert not root.exists(),'Independent root exists: inspect actual terminal, do not overwrite/relaunch'
raw=base64.b64decode(PAYLOAD);assert hashlib.sha256(raw).hexdigest()==DIGEST
manifest=MANIFEST
root.mkdir()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None and set(z.namelist())==set(manifest)
 for n in z.namelist():
  p=root/n;assert p.resolve().is_relative_to(root)
  b=z.read(n);assert len(b)==manifest[n]['bytes'] and hashlib.sha256(b).hexdigest()==manifest[n]['sha256']
  p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(b)
(root/'deployment.json').write_text(json.dumps(dict(bytes=len(raw),sha256=DIGEST,members=manifest),indent=2))
environment=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (root/'controller.log').open('x') as log:
 p=subprocess.Popen([py,'-u','-B',str(root/'code/controller.py')],cwd=root,env=environment,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 ticks=pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
 receipt=dict(pid=p.pid,start_ticks=ticks,bytes=len(raw),sha256=DIGEST)
 (root/'launch.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
'''
    remote=remote.replace('PAYLOAD',repr(base64.b64encode(payload).decode())).replace('DIGEST',repr(digest)).replace('MANIFEST',repr(manifest))
    completed=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
        'aic-inspur-home','python3','-'],input=remote,text=True,capture_output=True,timeout=40)
    print(completed.stdout)
    if completed.returncode:
        raise RuntimeError(completed.stderr)


if __name__ == '__main__':
    main()
