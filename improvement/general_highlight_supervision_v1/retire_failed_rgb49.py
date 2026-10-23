"""Retire only seven failed-profile derived RGB arrays, with explicit immutable manifest."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import shutil
from common import ROOT,read,ref,save


def main():
    target=ROOT/'retire_failed_rgb49';target.mkdir()
    terminal=read(ROOT/'pilot28/completion.json')
    if terminal['state']!='STOP_FIXED_NONCOMPETITIVE_SUPERVISION_PROFILE':
        raise ValueError('Failed fixed profile terminal differs')
    native=(ROOT/'native25').resolve();files=[];protected=[]
    for record in read(native/'completion.json')['accepted']:
        source=read(record['path']);accepted=read(source['input']['path'])
        path=Path(accepted['rgb']['path']).resolve(strict=True)
        if not path.is_relative_to(native) or path.name!='rgb.npy' or path.is_symlink():
            raise ValueError('Retirement path outside the specific seven derived arrays')
        actual=ref(path)
        if actual!=accepted['rgb']:raise ValueError('Derived array identity changed; do not delete')
        files.append(actual)
        for identity in [source['media'],source['clock'],source['annotations'],source['input']]:
            protected.append(ref(identity['path']))
        feature=ROOT/'pilot28/features'/source['sid']/'all.npy'
        protected.append(ref(feature))
    if len(files)!=7:raise ValueError('Exact retirement denominator differs')
    selected={row['path'] for row in files}
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:
            for fd in (process/'fd').iterdir():
                try:
                    if str(fd.resolve(strict=True)) in selected:raise RuntimeError('Retirement target still open by '+process.name)
                except FileNotFoundError:pass
        except (PermissionError,FileNotFoundError):continue
    save(target/'manifest.json',dict(human_authority='Existing request to clean failed Linux derived outputs; only current task failed-profile RGB caches',
        terminal=ref(ROOT/'pilot28/completion.json'),files=files,protected=protected,
        warning='These seven RGB input bytes will be retired; do not claim complete cached input retention or silently regenerate them',
        original_media_clocks_labels_features_weights_raw_metrics_costs_kept=True,
        no_recursive_delete=True,no_shared_baseline_or_external_job_data=True))
    before=shutil.disk_usage(ROOT).free
    for row in files:Path(row['path']).unlink()
    if any(Path(row['path']).exists() for row in files):raise ValueError('Exact file removal incomplete')
    save(target/'completion.json',dict(state='SEVEN_FAILED_PROFILE_RGB_CACHES_RETIRED',
        files=len(files),logical_bytes=sum(r['bytes'] for r in files),
        before_available_bytes=before,after_available_bytes=shutil.disk_usage(ROOT).free,
        protected_refs_preserved=True,baseline_unchanged=True))


if __name__=='__main__':main()
