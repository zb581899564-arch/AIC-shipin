"""Independent project-local CMake repair for the same pinned CUDA runtime."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,os,subprocess,urllib.request,zipfile

HERE=Path(__file__).resolve().parent

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*2**20),b''):h.update(b)
    return h.hexdigest()
def write(name,value):
    p=HERE/name;t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');t.replace(p)

def main():
    recipe=json.loads((HERE/'recipe.json').read_text())
    with (HERE/'runtime_build_registration.json').open('x') as f:
        json.dump(dict(pid=os.getpid(),utc=utc(),source_sha256=sha(Path(__file__)),recipe_sha256=sha(HERE/'recipe.json'),
              original_failed_build_preserved=True,project_disk_limit_bytes=None,Mac_used=False),f)
    try:
        runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
        for name in ['tools','downloads','tmp','cache']:(runtime/name).mkdir(exist_ok=True)
        env=dict(os.environ,TMPDIR=str(runtime/'tmp'),XDG_CACHE_HOME=str(runtime/'cache'),CUDA_CACHE_PATH=str(runtime/'cache/cuda'))
        source=Path(recipe['reuse_source_root']);archive=Path(recipe['original_source_archive'])
        assert source.name=='llama.cpp-'+recipe['llama_revision'] and archive.is_file()
        assert (source/'src/models/qwen3vl.cpp').is_file() and (source/'tools/mtmd/models/qwen3vl.cpp').is_file()
        wheel=runtime/'downloads'/recipe['cmake']['filename']
        write('runtime_build_progress.json',dict(status='DOWNLOADING_PROJECT_LOCAL_CMAKE',utc=utc(),pid=os.getpid()))
        with urllib.request.urlopen(recipe['cmake']['url'],timeout=45) as remote,wheel.open('xb') as out:
            for b in iter(lambda:remote.read(8*2**20),b''):out.write(b)
        assert wheel.stat().st_size==recipe['cmake']['bytes'] and sha(wheel)==recipe['cmake']['sha256']
        with zipfile.ZipFile(wheel) as z:
            assert z.testzip() is None
            for n in z.namelist():
                p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts
            z.extractall(runtime/'tools')
        cmake=runtime/'tools/cmake/data/bin/cmake'
        assert cmake.is_file();cmake.chmod(0o755)
        for name in ['ctest','cpack']:
            p=cmake.parent/name
            if p.exists():p.chmod(0o755)
        version=subprocess.check_output([str(cmake),'--version'],text=True).splitlines()[0]
        assert recipe['cmake']['version'] in version
        cap=subprocess.check_output(['nvidia-smi','--query-gpu=compute_cap','--format=csv,noheader'],text=True).strip()
        assert len(cap.splitlines())==1 and cap.replace('.','').isdigit()
        build=runtime/'build'
        command=[str(cmake),'-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DGGML_CUDA=ON',
             '-DCMAKE_CUDA_COMPILER='+recipe['cuda_compiler'],'-DCMAKE_CUDA_ARCHITECTURES='+cap.replace('.',''),
             '-DLLAMA_CURL=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_TESTS=OFF']
        write('runtime_build_progress.json',dict(status='CONFIGURING_PROJECT_LOCAL_CMAKE_CUDA_RUNTIME',utc=utc(),pid=os.getpid(),cmake_version=version))
        with (HERE/'runtime_configure.log').open('x') as log:
            subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        command=[str(cmake),'--build',str(build),'--config','Release','--target','llama-server','llama-mtmd-cli']
        write('runtime_build_progress.json',dict(status='BUILDING_PINNED_CUDA_RUNTIME',utc=utc(),pid=os.getpid(),source_revision=recipe['llama_revision'],cmake_version=version,GPU_model_loaded=False))
        with (HERE/'runtime_compile.log').open('x') as log:
            subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        binaries=[build/'bin'/n for n in ['llama-server','llama-mtmd-cli']]
        assert all(p.is_file() for p in binaries)
        links={p.name:subprocess.check_output(['ldd',str(p)],text=True) for p in binaries}
        assert all('not found' not in s for s in links.values())
        result=dict(status='PASS_PINNED_CUDA_RUNTIME_BUILD_ONLY',utc=utc(),pid=os.getpid(),source_revision=recipe['llama_revision'],
              source_archive_sha256=sha(archive),cmake_version=version,cmake_wheel_sha256=sha(wheel),
              binaries=[dict(path=str(p),sha256=sha(p)) for p in binaries],links=links,project_disk_limit_bytes=None,
              GPU_model_loaded=False,real_video_probe_passed=False,system_settings_changed=False,Mac_used=False)
    except Exception as exc:
        result=dict(status='STOP_RUNTIME_BUILD',utc=utc(),pid=os.getpid(),failure_type=type(exc).__name__,failure=str(exc),
               logs_and_sources_preserved=True,GPU_model_loaded=False,Mac_used=False)
    write('runtime_build_completion.json',result);write('runtime_build_progress.json',result)
    return 0 if result['status'].startswith('PASS_') else 1

if __name__=='__main__':raise SystemExit(main())
