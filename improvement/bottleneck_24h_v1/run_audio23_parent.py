"""One authorized <=80MB author download, then first CPU ASR8. No GPU job."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
import urllib.request

W=Path('/home/inspur/aic_video_work')
R=W/'bottleneck_24h_20261019_v1/audio_semantic23'
PY=str(W/'env/qwen3vl_isolated_20260910/bin/python')


def read(path):return json.loads(Path(path).read_text())


def ref(path):
    path=Path(path);h=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return dict(path=str(path),bytes=path.stat().st_size,sha256=h.hexdigest())


def save(path,value):
    with Path(path).open('x')as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())


def main():
    assert os.uname().nodename=='inspur-NP5570M5'
    assert os.environ.get('CUDA_VISIBLE_DEVICES')not in(None,'')
    reg=read(R/'registration.json');authorization=read(R/'human_download_exception_23.json')
    assert authorization['answer']=='允许本轮≤80MB小模型例外'and authorization['maximum_model_and_author_asset_download_bytes']==80000000
    assert ref(Path(reg['parent_code_ref']['path']))==reg['parent_code_ref']
    save(R/'download_claim.json',dict(pid=os.getpid(),registration_ref=ref(R/'registration.json'),automatic_retry=False))
    successful=[];total=0;start=time.monotonic()
    for item in reg['downloads']:
        assert time.monotonic()-start<900,'Fixed bounded download stage'
        path=R/item['relative_path'];path.parent.mkdir(parents=True,exist_ok=True)
        assert path.is_relative_to(R)and not path.exists()and not path.with_suffix(path.suffix+'.partial').exists()
        partial=path.with_suffix(path.suffix+'.partial');count=0
        with urllib.request.urlopen(item['url'],timeout=45)as response,partial.open('xb')as stream:
            assert response.status==200
            length=response.headers.get('Content-Length')
            if length is not None:assert int(length)<=item['max_bytes']
            for block in iter(lambda:response.read(1<<20),b''):
                count+=len(block)
                assert count<=item['max_bytes']and total+count<=80000000,'Authorized strict total download cap'
                stream.write(block)
            stream.flush();os.fsync(stream.fileno())
        value=ref(partial)
        if item.get('expected_bytes')is not None:assert count==item['expected_bytes']
        if item.get('expected_sha256'):assert value['sha256']==item['expected_sha256']
        os.replace(partial,path);value=ref(path);total+=count;successful.append(dict(url=item['url'],ref=value))
        with(R/'downloaded_files.jsonl').open('a')as log:log.write(json.dumps(successful[-1])+'\n');log.flush();os.fsync(log.fileno())
    assert total<=80000000
    text=(R/'author/README.md').read_text()
    assert 'code and model weights are released under the MIT License'in text
    save(R/'download_completion.json',dict(status='COMPLETE_AUTHORIZED_SINGLE_TINY_AUTHOR_DOWNLOAD',
        files=successful,total_bytes=total,model_ref=ref(R/'model/tiny.pt'),
        authorization_ref=ref(R/'human_download_exception_23.json'),all_models_original_author_only=True,
        no_whole_repository_or_additional_model=True,elapsed_seconds=time.monotonic()-start))
    with(R/'CPU_ASR.log').open('xb')as log:
        process=subprocess.run([PY,'-B',reg['code_ref']['path']],stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    save(R/'CPU_terminal.json',dict(exit_code=process.returncode,automatic_retry=False,
        utc=datetime.now(timezone.utc).isoformat()))
    assert process.returncode==0,'First ASR CPU stage actually failed; preserve partials/successes and stop'
    result=read(R/'ASR_completion.json')
    save(R/'first_ASR_stage_completion.json',dict(status='COMPLETE_DOWNLOAD_AND_CPU_ASR8_AWAITS_SEPARATE_AUDIO_VISUAL_TEST',
        ASR_completion_ref=ref(R/'ASR_completion.json'),usable_transcripts=result['usable_transcripts'],
        successful_abstentions=result['successful_abstentions'],new_GPU=0,new_fit=0,
        automatic_production_or_package=False,utc=datetime.now(timezone.utc).isoformat()))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        path=R/('parent_failure_%s.json'%os.getpid())
        if not path.exists():save(path,dict(error=repr(error),traceback=traceback.format_exc(),
            automatic_retry=False,successes_preserved=True,utc=datetime.now(timezone.utc).isoformat()))
        raise
