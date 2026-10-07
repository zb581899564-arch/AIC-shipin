"""Remove only named, archived owned paths inside the approved Mac root."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import shutil
import stat
import subprocess

ROOT=Path('/Users/choubk/codex-workspace')
EXPECTED='cc65ecc03158fe6cb2ad51c68107183776152eb488ef25ab1c6c9ba1c9d06537'
assert subprocess.check_output(['hostname'],text=True).strip()=='choubkdeMac-Mini.local'
assert ROOT.resolve()==ROOT and not ROOT.is_symlink()
manifest=json.loads((ROOT/'tmp/aic_mac_retirement_manifest_20261007.json').read_text())
assert manifest['archive_sha256']==EXPECTED
archive=Path(manifest['archive']);assert archive.parent==ROOT/'tmp'
h=hashlib.sha256()
with archive.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8<<20),b''):h.update(chunk)
assert h.hexdigest()==EXPECTED and archive.stat().st_size==manifest['archive_bytes']
targets=[Path(p) for p in manifest['targets']]
expected=[ROOT/x for x in ('projects','cache','envs','downloads','runs','data','datasets','models','state','logs','configs','tmp')]
expected += [ROOT/'bin'/x for x in ('ml-run','python3.11','uv','uvx','watch_night_mac_repair.sh')]
assert targets==expected,'cleanup target list changed'
assert {p.name for p in (ROOT/'projects').iterdir()}=={'aic-video'},'another project exists: STOP'
expected_top={p.name for p in expected if p.parent==ROOT}|{'bin','AGENTS.md','README.md'}
assert {p.name for p in ROOT.iterdir()}<=expected_top,'unknown owner/root item: STOP'
assert {p.name for p in (ROOT/'bin').iterdir()}=={'run','ml-run','python3.11','uv','uvx','watch_night_mac_repair.sh'},'unknown shared bin item: STOP'
device=ROOT.stat().st_dev
for p in targets:
    assert p.parent.resolve().is_relative_to(ROOT)
    if p.is_symlink():continue  # unlink the link itself; never traverse its target.
    assert p.resolve().is_relative_to(ROOT) and p.resolve()!=ROOT and not p.is_mount()
    if p.is_dir():
        for parent,dirs,files in os.walk(p,followlinks=False):
            assert Path(parent).lstat().st_dev==device,'mounted directory: STOP'
            dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()]
            assert all((Path(parent)/x).lstat().st_dev==device for x in files)
# Kernel open-file inventory, restricted to this root. Refuse another user's use.
query=subprocess.run(['/usr/sbin/lsof','-Fpcfn','+D',str(ROOT)],capture_output=True,text=True)
assert query.returncode in (0,1),query.stderr
pid=None;command=None;busy=[]
for line in query.stdout.splitlines():
    if line.startswith('p'):pid=int(line[1:])
    elif line.startswith('c'):command=line[1:]
    elif line.startswith('n') and line[1:].startswith(str(ROOT)):
        if pid!=os.getpid() and command!='lsof':busy.append(dict(pid=pid,command=command,path=line[1:]))
assert not busy,'owned workspace is in use: '+json.dumps(busy)
before_stat=os.statvfs(ROOT);before_work=int(subprocess.check_output(['du','-sk',str(ROOT)],text=True).split()[0])*1024
removed=[]
for p in targets:
    if p.is_symlink() or p.is_file():p.unlink()
    elif p.is_dir():shutil.rmtree(p)
    assert not p.exists() and not p.is_symlink()
    removed.append(str(p))
after_stat=os.statvfs(ROOT);after_work=int(subprocess.check_output(['du','-sk',str(ROOT)],text=True).split()[0])*1024
assert {p.name for p in ROOT.iterdir()}=={'AGENTS.md','README.md','bin'}
assert {p.name for p in (ROOT/'bin').iterdir()}=={'run'}
result=dict(status='PASS_MAC_OWNED_STORAGE_REMOVED',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    approved_root=str(ROOT),removed=removed,archive_verified_on_windows_before_delete=True,archive_sha256=EXPECTED,
    original_owned_work_bytes=manifest['before_work_bytes'],before_cleanup_including_archive_bytes=before_work,after_work_bytes=after_work,
    original_owned_occupancy_released_bytes=manifest['before_work_bytes']-after_work,
    volume_available_increase_bytes=(after_stat.f_bavail*after_stat.f_frsize)-(before_stat.f_bavail*before_stat.f_frsize),
    retained=['AGENTS.md','README.md','bin/run'],active_owned_jobs=0,other_users_files_touched=False,system_or_ssh_or_tailscale_changed=False,
    managed_projects_environments_models_media_and_caches_removed=True)
print(json.dumps(result),flush=True)
