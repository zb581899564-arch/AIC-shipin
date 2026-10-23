"""First missing I3D input for the exact40.48 control, never another old render."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import shutil
import subprocess
import sys
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'event_route_inputs75'
CACHE = Path('/dev/shm/aic_T_current40_48_route75')
GENERAL = WORK / 'general_highlight_supervision_20261021_v1'


def main():
    OUT.mkdir()
    inventory = read(ROOT / 'event_route_assets74/completion.json')
    if inventory['state'] != 'FIRST_CURRENT40_48_EXTERNAL_ROUTE_ASSET_INVENTORY_COMPLETE':
        raise ValueError('Exact source/clock/old-feature inventory must pass first')
    needed = {sid: row for sid, row in inventory['sources'].items() if row['new_I3D_needed']}
    expected = sum(row['prospective_new_RGB_uncompressed_bytes'] for row in needed.values())
    temporary_frame_bytes = max((read(check(row['source']['clock']))['width']
        * read(check(row['source']['clock']))['height'] * 3 * 64 for row in needed.values()), default=0)
    if expected + temporary_frame_bytes > shutil.disk_usage('/dev/shm').free:
        raise RuntimeError('Specific missing I3D RGB estimate exceeds current shared tmpfs')
    # A second already successful named profile must be adopted, not rendered.
    for sid in needed:
        if list(GENERAL.glob('*/features/' + sid + '/acceptance.json')):
            raise ValueError('Another existing source feature needs identity adoption first: ' + sid)
    save(OUT / 'registration.json', dict(source_inventory=identity(ROOT / 'event_route_assets74/completion.json'),
        new_sources=list(needed), new_RGB_bytes=expected, temporary_frame_bytes=temporary_frame_bytes,
        capacity_actual_free=shutil.disk_usage('/dev/shm').free,
        actual_CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:9],
        actual_RAM=subprocess.check_output(['free', '-b'], text=True),
        cache=str(CACHE), new_GPU_or_training=0, no_confirmation_or_labels_read=True,
        reason='Only N source lacking any accepted I3D input; existing Nobel I3D adopted. This is a distinct first YUV-frame-resize RGB-I3D input, not a re-render of accepted generic-Qwen RGB or a new clock measurement.',
        successful_original_video_RGB_or_I3D_inputs_not_repeated=True))
    CACHE.mkdir(mode=0o700); (CACHE / 'inputs').mkdir()
    sys.path.insert(0, str(GENERAL / 'code'))
    from routing_production60_prepare import renderer
    module, original = renderer(); module.ROOT = CACHE
    accepted = {}
    for sid, row in needed.items():
        source = row['source']
        ref = module.render(dict(source=sid, media=source['media'], clock=source['clock']))
        result = read(check(ref))
        if result['cells'] != row['original_native_cells'] or result['native_frames'] != row['original_native_frames']:
            raise ValueError('Actual first exact-baseline route RGB/clock denominator differs')
        accepted[sid] = ref
    save(OUT / 'completion.json', dict(state='FIRST_ONLY_MISSING_NATIVE_I3D_INPUTS_PASS',
        new_inputs=accepted, adopted_existing_I3D={sid: row['cached_original_I3D_feature']
            for sid, row in inventory['sources'].items() if not row['new_I3D_needed']},
        original_renderer=identity(original), new_GPU_calls=0, new_model_downloads=0,
        all_clock_and_original_media_adopted=True, no_source_labels_or_confirmation_read=True,
        next='Only one separately locked first backbone/classifier/conditional expert call, charged within fixed downstream budget; no repeat of existing Nobel features. Full temporal comparison still required.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
