"""Stream only registered non-test assets; stdout is exclusively tar bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--expected-sha',required=True)
    args=p.parse_args();assert sha(args.manifest)==args.expected_sha
    manifest=json.loads(Path(args.manifest).read_text());entries=manifest['files']
    roots=[Path('/home/inspur/aic_video_data/videos'),Path(manifest['linux_model_dir'])]
    with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as archive:
        for i,entry in enumerate(entries):
            source=Path(entry['source']);assert source.is_file() and not source.is_symlink()
            assert any(root==source.resolve() or root in source.resolve().parents for root in roots)
            stat=source.stat();assert stat.st_size==entry['bytes'] and sha(source)==entry['sha256']
            info=tarfile.TarInfo(entry['destination']);info.size=stat.st_size;info.mode=0o600;info.mtime=0
            with source.open('rb') as f:archive.addfile(info,f)
            assert source.stat().st_size==stat.st_size and source.stat().st_mtime_ns==stat.st_mtime_ns
            print(json.dumps(dict(sent=i+1,total=len(entries),destination=entry['destination'],bytes=stat.st_size)),file=sys.stderr,flush=True)
