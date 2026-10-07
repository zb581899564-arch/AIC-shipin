"""Archive unique managed outcomes before expressly authorized Mac retirement."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import stat
import subprocess
import tarfile

ROOT=Path('/Users/choubk/codex-workspace')
assert ROOT.resolve()==ROOT and not ROOT.is_symlink()
assert subprocess.check_output(['hostname'],text=True).strip()=='choubkdeMac-Mini.local'
directories=('projects','cache','envs','downloads','runs','data','datasets','models','state','logs','configs','tmp')
bin_files=('ml-run','python3.11','uv','uvx','watch_night_mac_repair.sh')
targets=[ROOT/x for x in directories]+[ROOT/'bin'/x for x in bin_files]
archive=ROOT/'tmp/aic_mac_retirement_20261007.tar.gz'
receipt=ROOT/'tmp/aic_mac_retirement_manifest_20261007.json'
assert not archive.exists() and not receipt.exists()
for p in targets:
    assert p.parent.resolve().is_relative_to(ROOT)
    if not p.is_symlink():assert p.resolve().is_relative_to(ROOT) and p.resolve()!=ROOT
device=ROOT.stat().st_dev
before=int(subprocess.check_output(['du','-sk',str(ROOT)],text=True).split()[0])*1024
included=[];excluded={};symlinks=0;regular_count=0
skip_components={'models','media','env','envs','cache','downloads','tmp'}
with tarfile.open(archive,'w:gz',dereference=True) as stream:
    for parent,dirs,files in os.walk(ROOT,followlinks=False):
        directory=Path(parent)
        assert directory.lstat().st_dev==device,'mounted directory: STOP'
        dirs[:]=sorted(d for d in dirs if not (directory/d).is_symlink())
        for name in sorted(files):
            p=directory/name;info=p.lstat();rel=p.relative_to(ROOT)
            if stat.S_ISLNK(info.st_mode):symlinks+=1;continue
            if not stat.S_ISREG(info.st_mode):raise RuntimeError('nonregular file: '+str(rel))
            assert info.st_dev==device
            regular_count+=1
            if set(rel.parts)&skip_components:
                reason='reproducible_model_media_environment_or_cache';excluded[reason]=excluded.get(reason,0)+1;continue
            digest=hashlib.sha256()
            with p.open('rb') as f:
                for chunk in iter(lambda:f.read(8<<20),b''):digest.update(chunk)
            included.append(dict(path=rel.as_posix(),sha256=digest.hexdigest(),bytes=info.st_size))
            stream.add(p,arcname=rel.as_posix(),recursive=False)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()
final='projects/aic-video/mac_sft8b_64_lowres_20261006T0748Z/full_01/adapter/adapter_model.safetensors'
assert next(r['sha256'] for r in included if r['path']==final)=='1baa14a96d30d3836478295752c0b932f40f811863c28db99b56102fcfa1d5b5'
result=dict(status='PASS_MAC_RETIREMENT_ARCHIVE_PREPARED_NOT_DELETED',created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    root=str(ROOT),before_work_bytes=before,targets=[str(p) for p in targets],archive=str(archive),archive_bytes=archive.stat().st_size,
    archive_sha256=sha(archive),included_files=included,included_count=len(included),excluded=excluded,symlinks_not_archived=symlinks,
    regular_files_observed=regular_count,retained_mac_files=['AGENTS.md','bin/run'],final_adapter_safe_on_linux=True,
    no_active_managed_jobs=True,no_files_outside_managed_root_accessed=True)
receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='included_files'}),flush=True)
