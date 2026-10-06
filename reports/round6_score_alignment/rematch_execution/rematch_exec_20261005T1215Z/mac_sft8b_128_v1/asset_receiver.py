"""No extractall: exclusive files, registered names/sizes and streaming SHA256."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path,PurePosixPath
import shutil
import sys
import tarfile
import time
import traceback

ROOT=Path('/Users/choubk/codex-workspace')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)
def within(path):
    resolved=path.resolve();assert ROOT==resolved or ROOT in resolved.parents
    for parent in [path,*path.parents]:
        if parent==ROOT:break
        assert not parent.is_symlink()
    return resolved

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--expected-sha',required=True)
    args=p.parse_args();manifest_path=within(Path(args.manifest));assert sha(manifest_path)==args.expected_sha
    manifest=json.loads(manifest_path.read_text());project=within(Path(manifest['mac_project']))
    entries={e['destination']:e for e in manifest['files']};assert len(entries)==len(manifest['files'])
    controller=project/'controller';controller.mkdir(parents=True,exist_ok=True)
    completion=controller/'asset_completion.json';assert not completion.exists()
    seen=set();received=0;started=time.monotonic();total=sum(e['bytes'] for e in entries.values())
    result=dict(status='RECEIVING_PINNED_NONTEST_ASSETS',manifest_sha256=args.expected_sha,total_bytes=total,total_files=len(entries))
    try:
        assert shutil.disk_usage(project).free>=total,'current capacity does not cover received assets'
        with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
            for member in archive:
                name=member.name;relative=PurePosixPath(name)
                assert member.isfile() and name in entries and name not in seen
                assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
                entry=entries[name];assert member.size==entry['bytes']
                target=within(project/relative);target.parent.mkdir(parents=True,exist_ok=True)
                assert not target.exists();part=within(target.with_name(target.name+'.part'));assert not part.exists()
                digest=hashlib.sha256();count=0;stream=archive.extractfile(member)
                with part.open('xb') as f:
                    while True:
                        block=stream.read(8<<20)
                        if not block:break
                        f.write(block);digest.update(block);count+=len(block);received+=len(block)
                        result.update(received_bytes=received,current_file=name,current_file_bytes=count,wall_seconds=time.monotonic()-started)
                        write(controller/'asset_progress.json',result)
                assert count==entry['bytes'] and digest.hexdigest()==entry['sha256'],'received byte identity mismatch'
                part.rename(target);seen.add(name)
        assert seen==set(entries) and received==total,'incomplete registered asset stream'
        result.update(status='PASS_MAC_PINNED_MODEL_AND_704_TRAIN_MEDIA_TRANSFER',received_bytes=received,received_files=len(seen),
                      all_sizes_and_sha256_match=True,test_assets_received=False)
    except Exception as exc:
        result.update(status='STOP_MAC_ASSET_TRANSFER',failure=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
    result.update(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),wall_seconds=time.monotonic()-started)
    write(completion,result);write(controller/'asset_progress.json',result);print(json.dumps(result),flush=True)
    raise SystemExit(0 if result['status'].startswith('PASS_') else 3)
