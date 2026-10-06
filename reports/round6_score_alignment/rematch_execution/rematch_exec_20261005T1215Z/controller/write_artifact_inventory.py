"""Exclusive SHA/size inventory of one completed run; no media or model load."""
import argparse
import hashlib
import json
from pathlib import Path

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source, output = (RUN/args.directory).resolve(strict=True), (RUN/args.output).resolve()
    if RUN not in source.parents or RUN not in output.parents or source in output.parents:
        raise RuntimeError('inventory paths must stay in RUN and output outside the recorded directory')
    records = []
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('symlink artifact is not eligible for this inventory')
        if path.is_file():
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1<<20), b''):
                    digest.update(block)
            records.append(dict(path=path.relative_to(source).as_posix(),bytes=path.stat().st_size,sha256=digest.hexdigest()))
    with output.open('x') as stream:
        json.dump(dict(directory=str(source),records=records),stream,indent=2)
        stream.write('\n')
    print(json.dumps(dict(files=len(records),inventory_sha256=hashlib.sha256(output.read_bytes()).hexdigest())))
