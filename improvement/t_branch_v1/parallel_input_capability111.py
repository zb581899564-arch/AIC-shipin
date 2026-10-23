"""Metadata-only unique64 support audit; never inspect test content/predictions."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from bisect import bisect_left
from fractions import Fraction
import math
from pathlib import Path
import traceback

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'parallel_input_capability111'


def main():
    OUT.mkdir()
    prior = read(ROOT / 'event_cost80/completion.json')
    refs = prior['metadata_sources']
    assets = read(check(refs['formal_assets']))
    clocks = read(check(refs['clocks']))
    counts = [row['native_frames'] for row in assets['sources']]
    short_tails = 0
    for row in assets['sources']:
        clock = clocks[row['video_id']]
        end = Fraction(clock['physical_end_exact'])
        start = 30 * (math.ceil(end / 30) - 1)
        points = [Fraction(x) for x in clock['normalized_exact_pts']]
        short_tails += int(len(points) - bisect_left(points, start) < 64)
    save(OUT / 'completion.json', dict(state='FIRST_NATIVE64_FORMAL_INPUT_CAPABILITY_METADATA_ONLY',
        adopted_original_asset_metadata=refs['formal_assets'], adopted_original_clocks=refs['clocks'],
        source_count=len(counts), minimum_whole_source_native_frames=min(counts),
        whole_sources_below64_unique_native_frames=sum(value < 64 for value in counts),
        naive_nonoverlap30sec_last_views_below64_native_frames=short_tails,
        no_actual_production_window_plan_created=True, no_old_clock_or_model_QA_repeated=True,
        no_test_content_or_predictions_or_labels_read=True,
        interpretation='The new cell interface requires64distinct original frames. Counts only reveal representation capability, not target-score preference. A naive short tail is not a finalized view. Before any production, an external/synthetic-tested general native view contract must cover every source without label stretching, silent subset selection or execution-to-empty fallback.',
        no_new_model_or_data_download_or_production_admission=True, code=identity(Path(__file__))))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_old_work_repeated=True))
        raise
