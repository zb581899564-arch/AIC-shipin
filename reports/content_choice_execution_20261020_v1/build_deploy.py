"""Build exact-commit code-only transfer; deploy and start CPU gates once."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / '.github-publication/AIC-shipin'
SHA = 'cb6095cc3156319054f23e5a3ad5baeb5ed9d0c1'
PREFIX = 'improvement/content_choice_v1/'
W = '/home/inspur/aic_video_work'
R = W + '/content_choice_20261019_v1'
PY = W + '/env/qwen3vl_isolated_20260910/bin/python'
ALIAS = 'aic-inspur-tailscale'
ARCHIVE = HERE / 'incoming_content_choice_cb6095cc_20261020_01.zip'
REMOTE_ZIP = W + '/' + ARCHIVE.name


def raw(path):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', SHA + ':' + path])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def build():
    head = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    assert head == SHA
    manifest = json.loads(raw(PREFIX + 'code_manifest.json'))
    entries = {}
    for name, expected in manifest['files'].items():
        data = raw(PREFIX + name)
        assert digest(data) == expected, name
        entries['code/' + PREFIX + name] = data
    for name, expected in manifest['dependencies'].items():
        data = raw(name)
        assert digest(data) == expected, name
        entries['code/' + name] = data
    entries['code/' + PREFIX + 'code_manifest.json'] = raw(PREFIX + 'code_manifest.json')
    for name in ['PLAN.md', 'RUNBOOK.md', 'RESEARCH.md', 'CPU_NOTES.md']:
        entries['code/' + PREFIX + name] = raw(PREFIX + name)
    entries['config.json'] = raw(PREFIX + 'config.example.json')
    entries['control.py'] = (HERE / 'control.py').read_bytes()
    for name, data in entries.items():
        if name.endswith('.py'):
            ast.parse(data, filename=name)
    entries['deployment_source.json'] = (json.dumps(dict(
        utc=datetime.now(timezone.utc).isoformat(), implementation_sha=SHA,
        parent_sha=manifest['base_commit'], pr='https://github.com/zb581899564-arch/AIC-shipin/pull/3',
        source='EXACT_GIT_SHOW_MEMBERS_NOT_REMOTE_GIT_CHECKOUT',
        members={name: dict(bytes=len(data), sha256=digest(data)) for name, data in entries.items()},
        source_scope='PRIVATE_OLD_ASSETS_REUSED_READ_ONLY', stage='CPU_GATES_ONLY',
        automatic_production=False, automatic_submission=False), ensure_ascii=False, indent=2) + '\n').encode()
    with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(entries)
    data = ARCHIVE.read_bytes()
    receipt = dict(archive=str(ARCHIVE), bytes=len(data), sha256=digest(data),
        members=len(entries), implementation_sha=SHA, remote_archive=REMOTE_ZIP,
        run_root=R, route=ALIAS, transfer_scope='NECESSARY_SMALL_CODE_ONLY',
        new_media=0, new_models=0, new_qwen_calls=0)
    write_new(HERE / 'deployment_registration_01.json', receipt)
    print(json.dumps(receipt))


def deploy():
    registration = json.loads((HERE / 'deployment_registration_01.json').read_text())
    # First independently check that neither this deployment nor its run root exists.
    probe = f"from pathlib import Path; import socket; assert socket.gethostname()=='inspur-NP5570M5'; assert not Path({R!r}).exists(); assert not Path({REMOTE_ZIP!r}).exists(); print('NEW_EXPLICIT_DEPLOYMENT_PATHS_ABSENT')"
    subprocess.run(['ssh', '-o', 'ConnectTimeout=15', ALIAS, PY + ' -B -c ' + shlex.quote(probe)], check=True, timeout=40)
    subprocess.run(['scp', '-o', 'ConnectTimeout=15', str(ARCHIVE), ALIAS + ':' + REMOTE_ZIP], check=True, timeout=100)
    install = r'''
import hashlib, json, os, pathlib, socket, subprocess, zipfile
R=pathlib.Path(RUN_ROOT); archive=pathlib.Path(REMOTE_ARCHIVE)
assert socket.gethostname()=='inspur-NP5570M5'
assert not R.exists(), 'Do not redeploy or repeat a claim'
blob=archive.read_bytes()
assert len(blob)==EXPECTED_BYTES and hashlib.sha256(blob).hexdigest()==EXPECTED_SHA
with zipfile.ZipFile(archive) as z:
    names=z.namelist()
    assert len(names)==len(set(names)) and z.testzip() is None
    for item in z.infolist():
        p=pathlib.PurePosixPath(item.filename)
        assert not p.is_absolute() and '..' not in p.parts and not item.is_dir()
        assert (item.external_attr>>16)&0o170000 != 0o120000
    manifest=json.loads(z.read('deployment_source.json'))
    assert set(names)==set(manifest['members'])|{'deployment_source.json'}
    for name, expected in manifest['members'].items():
        data=z.read(name)
        assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
    assert manifest['implementation_sha']==IMPLEMENTATION_SHA
    R.mkdir()
    z.extractall(R)
env=dict(os.environ, CUDA_VISIBLE_DEVICES='0', PYTHONDONTWRITEBYTECODE='1')
with (R/'cpu_control_parent.log').open('x') as log:
    p=subprocess.Popen([PYTHON,'-B',str(R/'control.py'),'--mode','cpu'],cwd=R/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    ticks=pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
receipt=dict(status='CODE_ACCEPTED_CPU_ONLY_STARTED',pid=p.pid,start_ticks=ticks,archive_bytes=len(blob),archive_sha256=EXPECTED_SHA,implementation_sha=IMPLEMENTATION_SHA,crc_pass=True,members_sha_pass=True,new_qwen_calls=0,automatic_production=False)
with (R/'cpu_launch.json').open('x') as stream:json.dump(receipt,stream,indent=2)
print(json.dumps(receipt))
'''
    values = dict(RUN_ROOT=R, REMOTE_ARCHIVE=REMOTE_ZIP, EXPECTED_BYTES=registration['bytes'],
        EXPECTED_SHA=registration['sha256'], IMPLEMENTATION_SHA=SHA, PYTHON=PY)
    source = '\n'.join(k + '=' + repr(v) for k,v in values.items()) + '\n' + install
    result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', ALIAS, PY + ' -B -'],
        input=source, text=True, capture_output=True, timeout=90)
    write_new(HERE / 'deployment_result_01.json', dict(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
    print(result.stdout); print(result.stderr, file=sys.stderr)
    result.check_returncode()


if __name__ == '__main__':
    dict(build=build, deploy=deploy)[sys.argv[1]]()
