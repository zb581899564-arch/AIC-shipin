"""Extract one frozen internal source snapshot into a new project directory."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import stat
import zipfile

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
TARGET = RUN/'baseline_a_pts_v1'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    source = RUN/'controller/a_pts_runtime_01.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest() != args.sha256:
        raise RuntimeError('internal source archive SHA mismatch')
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len({i.filename for i in entries}) != len(entries):
            raise RuntimeError('duplicate internal source member')
        for info in entries:
            relative = PurePosixPath(info.filename)
            if relative.is_absolute() or '..' in relative.parts or stat.S_ISLNK(info.external_attr >> 16):
                raise RuntimeError('unsafe internal source member')
            destination = (TARGET/info.filename).resolve()
            if TARGET.resolve() not in destination.parents:
                raise RuntimeError('internal source extraction escaped project target')
        TARGET.mkdir(exist_ok=False)
        for info in entries:
            destination = TARGET/info.filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as output:
                output.write(archive.read(info))
    print('DEPLOYED_FROZEN_A_PTS_RUNTIME_NEW_DIRECTORY')
