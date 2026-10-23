"""Metadata-only full-scope cost forecast; never test-content or quality analysis."""
from fractions import Fraction
import math
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'event_cost80'
GENERAL = WORK / 'general_highlight_supervision_20261021_v1'


def main():
    OUT.mkdir()
    registration = read(GENERAL / 'routing_production62/registration.json')
    assets = read(check(registration['assets']))
    clocks = read(check(assets['clocks']))
    if len(assets['sources']) != 426 or len(clocks) != 426:
        raise ValueError('Full formal source metadata count differs')
    windows = 0
    for source in assets['sources']:
        clock = clocks[source['video_id']]
        points = clock['normalized_exact_pts']; end = Fraction(clock['physical_end_exact'])
        if (len(points) != source['native_frames'] or Fraction(points[0]) != 0
                or end <= Fraction(points[-1])):
            raise ValueError('Already accepted formal native duration metadata differs')
        windows += math.ceil(end / 30)
    # Counts only: do not inspect held descriptions, labels or video content.
    held_path = ROOT / 'confirmation_inventory53/completion.json'
    held = read(held_path)
    event = read(ROOT / 'event_adoption73/completion.json')
    selection = read(ROOT / 'event_selection72/completion.json')
    route = read(ROOT / 'event_route77/completion.json')
    caption_rate = event['GPU_seconds'] / 50
    selector_rate = selection['GPU_seconds'] / 150
    old_base = read(ROOT / 'development51/coarse_GPU_completion.json')['outputs']
    forward = 0.
    for conditions in old_base.values():
        for arm, cases in conditions.items():
            if arm == 'original_correct':
                continue
            for ref in cases.values():
                forward += read(check(read(check(ref))['raw']))['seconds']
    resource = read(WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/T_joint4_dev_greedy_BASE_20261022_v51.resource.json')
    # This bound includes model loading/I/O in addition to BASE computation.
    base_batch_upper_average = max(0., resource['charged_seconds'] - forward) / 365
    cached = read(GENERAL / 'routing_production62/GPU_completion.json')
    if cached['source_count'] != 426 or cached['I3D_cells'] != assets['total_I3D_cells']:
        raise ValueError('Accepted original fixed-route formal cache scope differs')
    save(OUT / 'completion.json', dict(state='FIRST_WHOLE_SCOPE_COST_METADATA_NOT_ADMISSION',
        formal_sources=426, formal_native_frames=assets['total_native_frames'],
        formal_uniform_at_most30sec_windows=windows,
        formal_original_media_bytes=assets['total_original_media_bytes'],
        planned_same_shared_BASE_TIME_no_training=True,
        observed_caption_GPU_seconds_per_task=caption_rate,
        observed_native_selector_GPU_seconds_per_task=selector_rate,
        projected_formal_caption_plus_selector_seconds=windows * (caption_rate + selector_rate),
        extra_formal_VERIFY_unknown_until_new_actions=True,
        existing_formal_fixed_route_reuse=dict(source_count=426, I3D_cells=assets['total_I3D_cells'],
            conditional_on_unchanged_media_clock_model_inputs=True, new_I3D_or_UMT_forward_not_expected=True),
        fresh_confirmation_sources=4, fresh_confirmation_windows=held['total_windows'],
        fresh_confirmation_first_BASE_batches=held['semantic_batches'],
        observed_BASE_batch_upper_average_seconds=base_batch_upper_average,
        projected_confirmation_caption_and_correct_shift_selector_seconds=held['total_windows'] * (caption_rate + 2 * selector_rate),
        extra_confirmation_original_TIME_BASE_and_VERIFY_still_required=True,
        all_goal_GPU_seconds_settled_before_VERIFY=route['all_goal_GPU_seconds'],
        aggregate_Goal_GPU_ceiling=43200, current_profile_development_max_seconds=6300,
        no_quality_or_runtime_guarantee=True, no_fresh_confirmation_labels_read=True,
        no_test_pixels_predictions_or_score_distribution_used=True,
        exact_production_inputs_and_real_peak_cache_capacity_must_be_accepted_later=True,
        metadata_sources=dict(formal_assets=registration['assets'], clocks=assets['clocks'],
            held_inventory=identity(held_path), route_cache=identity(GENERAL / 'routing_production62/GPU_completion.json')),
        next='Only a complete development benefit can admit one frozen four-source confirmation. Add actual baseline/BASE/VERIFY cost and real first input cache measurements, retain production/QA/transfer margin; no automatic model call.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
