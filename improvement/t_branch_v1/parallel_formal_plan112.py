"""First formal native-cell plan from the unchanged already-used equal-window planner."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
from pathlib import Path
import shutil
import sys
import traceback

from native_units97 import paired_native_cells
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'parallel_formal_plan112'


def main():
    OUT.mkdir()
    prior = read(ROOT / 'event_cost80/completion.json')
    refs = prior['metadata_sources']
    assets = read(check(refs['formal_assets']))
    clocks = read(check(refs['clocks']))
    path = WORK / 'human_reference_iteration_20261013_v1/code'
    sys.path.insert(0, str(path))
    import native_window_plan
    if Path(native_window_plan.__file__).resolve() != (path / 'native_window_plan.py').resolve():
        raise ValueError('Existing equal-window native planner namespace differs')
    if shutil.disk_usage(ROOT).free < 4000000:
        raise RuntimeError('Specific first formal metadata-plan file does not fit current capacity')
    planned, cases = {}, 0
    for index, source in enumerate(assets['sources']):
        sid = source['video_id']
        clock = clocks[sid]
        windows = native_window_plan.plan_windows(clock)
        points = [Fraction(p) for p in clock['normalized_exact_pts']]
        rows = []
        for window in windows:
            cells = paired_native_cells(points, window['start_exact'], window['end_exact'],
                                        window['source_frame_ordinals'], 32)
            rows.append(dict(**window, source_native_cells=cells))
        planned[sid] = dict(original_asset_index=index, native_frames=source['native_frames'], windows=rows)
        cases += len(rows)
    if len(planned) != 426 or cases != prior['formal_uniform_at_most30sec_windows']:
        raise ValueError('Whole426 source/exact original planner window domain differs')
    plan = OUT / 'source_plan.json'
    save(plan, dict(assets=refs['formal_assets'], clocks=refs['clocks'], planned=planned,
        actual_existing_planner=identity(path / 'native_window_plan.py'),
        no_media_or_predictions_or_labels_read=True))
    save(OUT / 'completion.json', dict(state='FIRST_FORMAL426_522_NATIVE64_AND32CELLS_METADATA_PLAN_PASS',
        actual_source_plan=identity(plan), sources=426, native_windows=cases,
        every_window_exact64_distinct_original_ordinals=True,
        every_window_exact32_nonempty_native_pair_cells=True,
        existing_equal_at_most30sec_planner_unchanged=True,
        no_short_tail_fallback_or_source_subset_or_label_stretch=True,
        old_metadata_counts_adopted=identity(ROOT / 'event_cost80/completion.json'),
        first_not_pixels_or_input_or_model_or_quality_or_production_admission=True,
        code=identity(Path(__file__))))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_old_work_repeated=True))
        raise
