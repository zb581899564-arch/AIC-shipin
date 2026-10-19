"""One deployment claim, verified control ZIP, and one new parent launch."""
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import urllib.request
import zipfile

WORK=Path('/home/inspur/aic_video_work')
ROOT=WORK/'temporal_selector_20261018_v1'
INCOMING=WORK/'incoming_temporal_selector_control_20261018_01.zip'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()


def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)


def deploy(expected):
    assert socket.gethostname()=='inspur-NP5570M5'
    assert not ROOT.exists(),'Existing root must be inspected; never relaunch'
    assert sha(INCOMING)==expected,'Small control archive bytes differ'
    with zipfile.ZipFile(INCOMING) as z:
        assert z.testzip() is None
        members=json.loads(z.read('members.json'))
        assert set(z.namelist())==set(members)|{'members.json'}
        for name,digest in members.items():
            p=(ROOT/name).resolve()
            assert p.is_relative_to(ROOT) and not name.startswith('/') and '..' not in Path(name).parts
            data=z.read(name);assert hashlib.sha256(data).hexdigest()==digest
            if name.endswith('.py'):ast.parse(data.decode('utf-8'))
        ROOT.mkdir()
        z.extractall(ROOT)
    save(ROOT/'deployment_acceptance.json',dict(status='PASS_SMALL_CONTROL_SIZE_SHA_CRC_MEMBERS_AND_AST',
         control_sha256=expected,control_bytes=INCOMING.stat().st_size,members=len(members),utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    code={p.name:sha(p) for p in sorted((ROOT/'code').glob('*.py')) if p.name!='register_remote.py'}
    save(ROOT/'code_manifest.json',code)
    rules=ROOT/'rules';rules.mkdir()
    previous=json.loads((WORK/'trajectory_risk_20261017_v1/official_rule_check_before_package.json').read_text())
    attachments=[];pages=[]
    for i,row in enumerate(previous['attachments']):
        request=urllib.request.Request(row['url'],headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=40) as response:data=response.read()
        path=rules/('attachment%d.pdf'%i);path.write_bytes(data)
        assert len(data)==row['bytes'] and sha(path)==row['sha256'],'Changed attachment requires source review, no model run'
        attachments.append(dict(url=row['url'],bytes=len(data),sha256=sha(path),same_as_prior_full_read=True))
    for i,url in enumerate(['https://www.aicomp.cn/tracks/tracks-6/4267.html',
                            'https://www.aicomp.cn/notice/notice-3/5307.html',
                            'https://www.aicomp.cn/notice/notice-3/']):
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as response:data=response.read()
        path=rules/('page%d.html'%i);path.write_bytes(data);pages.append(dict(url=url,bytes=len(data),sha256=sha(path)))
    save(ROOT/'official_rule_check.json',dict(status='CURRENT_OFFICIAL_PAGES_AND_UNCHANGED_REVIEWED_ATTACHMENTS_BOUND',
         pages=pages,attachments=attachments,utc=dt.datetime.now(dt.timezone.utc).isoformat(),
         approved_external_local_time_head_scope=True,
         interpretation='Compliant public research summaries only for training; test only local reproducible open-model inference. No test teacher/labels, no hidden-label probes, all physical parameter elements <=9B. This is a rules interpretation, not special organizer permission.',
         no_special_organizer_permission_claim=True))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',AIC_TEMPORAL_ROOT=str(ROOT),PYTHONDONTWRITEBYTECODE='1',
             OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    python=WORK/'env/qwen3vl_isolated_20260910/bin/python'
    command=[str(python),'-B','-u',str(ROOT/'code/controller.py')]
    with (ROOT/'parent.log').open('xb') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                                 env=env,start_new_session=True)
    stat=Path('/proc',str(process.pid),'stat').read_text();tail=stat[stat.rfind(')')+2:].split()
    save(ROOT/'chain_launch.json',dict(pid=process.pid,start_ticks=tail[19],command=command,
         CUDA_VISIBLE_DEVICES=env['CUDA_VISIBLE_DEVICES'],utc=dt.datetime.now(dt.timezone.utc).isoformat(),
         protocol_sha256=sha(ROOT/'protocol.json'),control_sha256=expected,code=code,
         free_bytes=shutil.disk_usage(WORK).free,goal_created=False,automation_created=False))
    print(json.dumps(json.loads((ROOT/'chain_launch.json').read_text()),ensure_ascii=False))


if __name__=='__main__':
    import sys
    deploy(sys.argv[1])
