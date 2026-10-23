"""Pre-quality follow-up cost metadata; no test content, labels or new model calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import traceback

from t_io import ROOT, identity, read, save

OUT = ROOT / 'parallel_cost_inventory110'


def main():
    OUT.mkdir()
    protocol = read(ROOT / 'code/parallel_protocol105.json')
    prior = read(ROOT / 'event_cost80/completion.json')
    first = read(ROOT / 'parallel_cost107/CPU_completion.json')
    actual = read(ROOT / 'parallel_cost107/completion.json')
    rate = first['projection']['measured_dev_producer_consumer_rate_seconds']
    held = prior['fresh_confirmation_windows']
    formal = prior['formal_uniform_at_most30sec_windows']
    # This records conditional follow-up phases before any new quality result.
    #5400 remains the entire107/108/109 development closure, without any fee move.
    maximum = dict(fixed105_development_closure=5400, conditional_frozen_confirmation=9000,
                   conditional_formal_production_QA=12000)
    total = protocol['Goal_GPU_seconds_already_settled'] + sum(maximum.values())
    if (total > 43200 or formal != 522 or held != 198
            or (ROOT / 'parallel_full109/review.json').exists()):
        raise ValueError('Pre-quality cost scope, frozen inventory or original Goal budget differs')
    save(OUT / 'completion.json', dict(state='FIRST_PARALLEL_FOLLOWUP_COST_METADATA_NO_ADMISSION',
        old_whole_scope_metadata_adopted=identity(ROOT / 'event_cost80/completion.json'),
        current_protocol=identity(ROOT / 'code/parallel_protocol105.json'),
        actual_first_query_cost=identity(ROOT / 'parallel_cost107/completion.json'),
        formal_source_count=426, formal_native_frames=prior['formal_native_frames'],
        formal_original_media_bytes=prior['formal_original_media_bytes'], formal_windows=formal,
        frozen_confirmation_sources=4, frozen_confirmation_windows=held,
        confirmation_parallel_correct_and_joint_shift_calls=2 * held,
        confirmation_original_TIME_and_BASE_still_missing=True,
        first_confirmation_BASE_batches=prior['fresh_confirmation_first_BASE_batches'],
        observed_parallel_window_producer_consumer_seconds=rate,
        projected_formal_parallel_forward_seconds=formal * rate,
        projected_confirmation_parallel_forward_seconds=2 * held * rate,
        adopted_BASE_batch_upper_average_seconds=prior['observed_BASE_batch_upper_average_seconds'],
        adopted_formal426_I3D_UMT_route=prior['existing_formal_fixed_route_reuse'],
        exact_VERIFY_count_unknown_until_complete_candidate_actions=True,
        actual_input_cache_and_CPU_ASR_preparation_cost_still_required=True,
        pre_quality_conditional_phase_maxima=maximum,
        original5400_development_limit_and_all_107_108_109_fees_unchanged=True,
        original_global_maximum_seconds=43200, total_if_all_conditional_maxima_used=total,
        actual_settled_through107=actual['all_goal_GPU_seconds'],
        no_confirmation_or_production_job_or_input_lock_created=True,
        qualification='Development must pass first. One frozen four-source confirmation then needs its own source/input/budget/current-resource lock. Production needs confirmation benefit and measured full cost/deadline. These conditional budgets are maxima, never permission to spend without those gates.',
        original_no_test_content_predictions_or_labels_read=True,
        original4confirmation_quality_not_read=True, new_model_or_data_downloads=0,
        current_new_T_ZIPs=0, no_quality_or_transfer_or_runtime_guarantee=True,
        code=identity(Path(__file__))))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_old_work_repeated=True))
        raise
