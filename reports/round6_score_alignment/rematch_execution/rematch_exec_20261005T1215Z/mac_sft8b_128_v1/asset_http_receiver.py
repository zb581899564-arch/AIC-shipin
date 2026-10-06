"""Whole-file restart of incomplete copies, preserving the first transfer evidence."""
import datetime as dt
import hashlib
import json
from pathlib import Path,PurePosixPath
import shutil
import time
import traceback
import urllib.request

HERE=Path(__file__).resolve().parent;ROOT=Path('/Users/choubk/codex-workspace')
assert ROOT in HERE.resolve().parents
manifest=json.loads((HERE/'assets_manifest.json').read_text());configuration=json.loads((HERE/'http_transport_config.json').read_text())
entries=manifest['files'];headers={'Authorization':'Bearer '+configuration['token']}
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
assert configuration['url'].startswith('http://100.127.244.47:')
controller=HERE/'controller';started=time.monotonic();total=sum(e['bytes'] for e in entries);received=0
result=dict(status='RECEIVING_DIRECT_TAILSCALE_HTTP_ASSETS',total_bytes=total,total_files=len(entries),
            first_bridge_failure_preserved=True,partial_bridge_files_not_resumed=True)
def write(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()
try:
    assert shutil.disk_usage(HERE).free>=total
    for i,entry in enumerate(entries):
        relative=PurePosixPath(entry['destination']);assert not relative.is_absolute() and '..' not in relative.parts
        target=HERE/relative;assert ROOT in target.resolve().parents and not target.is_symlink()
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            assert target.stat().st_size==entry['bytes'] and sha(target)==entry['sha256']
            received+=entry['bytes'];continue
        temporary=target.with_name(target.name+'.http02.part');assert not temporary.exists()
        digest=hashlib.sha256();count=0
        request=urllib.request.Request(configuration['url']+'/asset/'+str(i),headers=headers)
        with opener.open(request,timeout=120) as response,temporary.open('xb') as output:
            assert int(response.headers['Content-Length'])==entry['bytes']
            while True:
                block=response.read(8<<20)
                if not block:break
                output.write(block);digest.update(block);count+=len(block);received+=len(block)
                result.update(received_bytes=received,current_file=entry['destination'],current_file_bytes=count,
                              wall_seconds=time.monotonic()-started)
                write(controller/'asset_http_progress.json',result)
        assert count==entry['bytes'] and digest.hexdigest()==entry['sha256']
        temporary.rename(target)
    assert received==total
    result.update(status='PASS_MAC_PINNED_MODEL_AND_704_TRAIN_MEDIA_TRANSFER',received_bytes=received,
                  received_files=len(entries),all_sizes_and_sha256_match=True,test_assets_received=False)
except Exception as exc:
    result.update(status='STOP_MAC_DIRECT_ASSET_TRANSFER',failure=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    try:
        request=urllib.request.Request(configuration['url']+'/done',headers=headers,data=b'',method='POST')
        opener.open(request,timeout=10).read()
        result['owned_sender_closed']=True
    except Exception:result['owned_sender_closed']=False
result.update(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),wall_seconds=time.monotonic()-started)
write(controller/'asset_http_completion.json',result);print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status'].startswith('PASS_') else 3)
