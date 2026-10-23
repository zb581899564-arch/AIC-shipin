"""Read-only formal asset availability and work estimates, no frames/prediction tuning."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import shutil
from common import ROOT as ADMISSION,WORK,read,ref,save
from time_control50_common import checked

ROOT=ADMISSION/'production_assets58'


def main():
    ROOT.mkdir()
    family=WORK/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3'
    inputs=read(family/'package_inputs.json')
    metadata=read(checked(inputs['metadata']));clocks=read(checked(inputs['source_clocks']))
    if len(metadata['records'])!=426 or set(clocks)!={str(i) for i in range(426)}:
        raise ValueError('Frozen formal source metadata denominator differs')
    sources=[]
    for item in metadata['records']:
        vid=item['video_id'];clock=clocks[vid];path=Path(item['source_path']).resolve(strict=True)
        if not path.is_relative_to(WORK) or not path.is_file() or clock['source_sha256']!=item['source_sha256']:
            raise ValueError('Registered formal media missing or source binding differs')
        n=len(clock['normalized_exact_pts'])
        if n!=item['n_frames']:raise ValueError('Frozen complete native clock count differs from formal metadata')
        stat=path.stat()
        sources.append(dict(video_id=vid,path=str(path),source_sha256=item['source_sha256'],bytes=stat.st_size,
            mtime_ns=stat.st_mtime_ns,native_frames=n,RGB_I3D_native64_cells=(n+63)//64,
            width=item['width'],height=item['height'],clock_origin=clock['first_original_pts_exact']))
    field_refs={name:dict(identity=identity,exists=Path(identity['path']).is_file(),
                   actual_bytes=Path(identity['path']).stat().st_size) for name,identity in inputs['source_field_files'].items()}
    if not all(row['exists'] for row in field_refs.values()):raise ValueError('Existing full spatial source field unavailable')
    baseline=read(ADMISSION/'media24/registration.json')['protected_baseline'];checked(baseline)
    save(ROOT/'completion.json',dict(state='READ_ONLY_FORMAL_ASSETS_AVAILABLE_NOT_PRODUCTION_ADMISSION',
        sources=sources,records=426,total_native_frames=sum(s['native_frames'] for s in sources),
        total_I3D_cells=sum(s['RGB_I3D_native64_cells'] for s in sources),
        total_original_media_bytes=sum(s['bytes'] for s in sources),field_files=field_refs,
        source_manifest=inputs['source_manifest'],metadata=inputs['metadata'],clocks=inputs['source_clocks'],
        protected_baseline=baseline,current_available_bytes=shutil.disk_usage(ROOT).free,
        no_decode_no_GPU_no_prediction_analysis=True,
        no_test_GT_or_new_labels=True,no_automatic_production=True))


if __name__=='__main__':main()
