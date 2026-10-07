"""Build pinned llama.cpp in the project using the existing CUDA toolkit.

No system installation, Python environment edit, model load, or GPU inference.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import urllib.request

HERE=Path(__file__).resolve().parent


def write(name,value):
    p=HERE/name;tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)


def utc():return datetime.now(timezone.utc).isoformat()


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda:stream.read(8*2**20),b''):h.update(b)
    return h.hexdigest()


def main():
    recipe=json.loads((HERE/'runtime_recipe.json').read_text(encoding='utf-8-sig'))
    runtime=HERE/'runtime'
    assert str(runtime)==recipe['install_root']
    with (HERE/'runtime_build_registration.json').open('x') as f:
        json.dump(dict(pid=os.getpid(),utc=utc(),recipe_sha256=sha(HERE/'runtime_recipe.json'),
             project_disk_limit_bytes=None,GPU_used=False,Mac_used=False),f)
    runtime.mkdir(exist_ok=True)
    for name in ['tmp','cache','downloads']:(runtime/name).mkdir(exist_ok=True)
    env=dict(os.environ,TMPDIR=str(runtime/'tmp'),XDG_CACHE_HOME=str(runtime/'cache'),
         CUDA_CACHE_PATH=str(runtime/'cache/cuda'),PYTHONDONTWRITEBYTECODE='1')
    try:
        cuda=Path(recipe['CUDA_toolkit_existing']);assert cuda.is_file()
        cap=subprocess.check_output(['nvidia-smi','--query-gpu=compute_cap','--format=csv,noheader'],text=True).strip()
        assert len(cap.splitlines())==1 and cap.replace('.','').isdigit()
        archive=runtime/'downloads/llama-source.tar.gz'
        write('runtime_build_progress.json',dict(status='DOWNLOADING_PINNED_RUNTIME_SOURCE',utc=utc(),pid=os.getpid()))
        with urllib.request.urlopen(recipe['source_url'],timeout=60) as source,archive.open('xb') as out:
            shutil.copyfileobj(source,out,length=8*2**20)
        source_root=runtime/('llama.cpp-'+recipe['revision'])
        with tarfile.open(archive,'r:gz') as tar:
            for member in tar.getmembers():
                p=PurePosixPath(member.name)
                assert not p.is_absolute() and '..' not in p.parts
                assert p.parts[0]=='llama.cpp-'+recipe['revision']
                assert member.isdir() or member.isfile(), 'unsupported archive link/device'
            tar.extractall(runtime)
        assert (source_root/'src/models/qwen3vl.cpp').is_file()
        assert (source_root/'tools/mtmd/models/qwen3vl.cpp').is_file()
        build=runtime/'build'
        configure=['cmake','-S',str(source_root),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release',
           '-DGGML_CUDA=ON','-DCMAKE_CUDA_COMPILER='+str(cuda),'-DCMAKE_CUDA_ARCHITECTURES='+cap.replace('.',''),
           '-DLLAMA_CURL=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_TESTS=OFF']
        write('runtime_build_progress.json',dict(status='CONFIGURING_PINNED_CUDA_RUNTIME',utc=utc(),pid=os.getpid(),
             source_archive_sha256=sha(archive),cuda_architecture=cap,source_revision=recipe['revision']))
        with (HERE/'runtime_configure.log').open('x') as log:
            subprocess.run(configure,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        # The tool's default build scheduling keeps this CPU preparation independent
        # of the active GPU job. No persistent CPU/RAM allocation cap is introduced.
        command=['cmake','--build',str(build),'--config','Release','--target','llama-server','llama-mtmd-cli']
        write('runtime_build_progress.json',dict(status='BUILDING_PINNED_CUDA_RUNTIME',utc=utc(),pid=os.getpid(),
             command=command,source_revision=recipe['revision'],GPU_model_loaded=False))
        with (HERE/'runtime_compile.log').open('x') as log:
            subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        binaries=[build/'bin'/n for n in ['llama-server','llama-mtmd-cli']]
        assert all(p.is_file() for p in binaries)
        links={p.name:subprocess.check_output(['ldd',str(p)],text=True) for p in binaries}
        assert all('not found' not in v for v in links.values())
        result=dict(status='PASS_PINNED_CUDA_RUNTIME_BUILD_ONLY',utc=utc(),pid=os.getpid(),source_revision=recipe['revision'],
             source_archive_sha256=sha(archive),binaries=[dict(path=str(p),sha256=sha(p)) for p in binaries],
             links=links,GPU_model_loaded=False,real_video_probe_passed=False,system_settings_changed=False,
             project_disk_limit_bytes=None,Mac_used=False)
    except Exception as exc:
        result=dict(status='STOP_RUNTIME_BUILD',utc=utc(),pid=os.getpid(),failure_type=type(exc).__name__,failure=str(exc),
                    logs_and_partial_sources_preserved=True,GPU_model_loaded=False,Mac_used=False)
    write('runtime_build_completion.json',result);write('runtime_build_progress.json',result)
    return 0 if result['status'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
