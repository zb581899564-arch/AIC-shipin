"""New loss-only final model comparison; reuse accepted old control metrics.

No old INIT/model/QA/metric replay. New native masks use first output-QA ranges.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import traceback
import numpy as np

from evaluate_summary import (ROOT, SIDS, WINDOWS, bound, read, ref, save, require,
    load_requests, load_sources, metric, matched_semantic, comparison, macro)


def masks_from_accepted_qa(qa_ref, requests, sources, role, weight_ref, resource_ref):
    qa = read(bound(qa_ref)); complete = read(bound(qa['completion_ref']))
    require(qa['status'] == 'PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA'
            and qa['model_role'] == role and qa['windows'] == WINDOWS and qa['sources'] == 8
            and qa['invalid_outputs'] == 0 and qa['unique_ledger_equal'] is True,
            'Actual accepted all43 first independent output QA required')
    resource = read(bound(resource_ref))
    require(resource['status'] == 'completed' and resource['exit_code'] == 0
            and qa['resource_ref'] == resource_ref, 'Exact natural role terminal')
    require(complete['model_role'] == role and complete['status'] == 'PASS_ALL43_MATCHED_SUMMARY_GENERATIONS'
            and complete['outputs'] == qa['outputs'] and complete['model_weights_ref'] == weight_ref,
            'Accepted exact output/model completion')
    bound(weight_ref)
    seen = set(); masks = {sid: np.zeros(len(sources[sid]['points']), dtype=bool) for sid in SIDS}
    counts = defaultdict(lambda: dict(windows=0, empty_windows=0, generated_intervals=0))
    for item in qa['details']:
        uid, sid = item['uid'], item['sid']
        require(uid in requests and uid not in seen and requests[uid]['request']['sid'] == sid,
                'Every accepted source/window exactly once')
        seen.add(uid); bound(item['output_ref']); counts[sid]['windows'] += 1
        counts[sid]['empty_windows'] += int(item['valid_empty_JSON'])
        counts[sid]['generated_intervals'] += len(item['native_ranges'])
        for left, right in item['native_ranges']:
            require(type(left) is int and type(right) is int and 0 <= left <= right <= len(masks[sid]),
                    'Only first-QA exact native ordinal ranges')
            masks[sid][left:right] = True
    require(seen == set(requests) and len(seen) == WINDOWS, 'All43 native output-QA records')
    return masks, dict(counts)


def main(manifest_path):
    path = Path(manifest_path).resolve(strict=True); require(path.parent == ROOT, 'Explicit objective20 manifest')
    manifest = read(path); old = read(bound(manifest['adopted_previous_evaluation_ref']))
    require(old['status'] == 'COMPLETE_CPU_EVALUATION_NOT_SCIENTIFIC_PROMOTION'
            and old['raw_output_counts']['INIT_TIME'] == 43 and old['invalid_output_count'] == 0,
            'Adopt the unchanged same-input original control evaluation')
    frozen = read(bound(manifest['frozen_selection_ref']))
    require(frozen['status'] == 'FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS'
            and frozen['final_adapter_ref'] == manifest['final_adapter_ref'], 'Fixed new final559')
    old_sources = {row['sid']: row for row in old['sources']}
    prepared, requests = load_requests(manifest); sources = load_sources(manifest, requests)
    require(old['dev_prepared_ref'] == manifest['dev_prepared_ref']
            and old['baseline_human_adoption_ref'] == manifest['baseline_human_adoption_ref'],
            'Same original8/43 input and human-reference source identities')
    trained, counts = masks_from_accepted_qa(manifest['trained_output_QA_ref'], requests, sources,
        'TRAINED', manifest['final_adapter_ref'], manifest['trained_resource_ref'])
    initial, initial_counts = masks_from_accepted_qa(old['role_output_QA_refs']['INIT_TIME'], requests, sources,
        'INIT_TIME', old['initial_TIME_ref'], old['role_resource_refs']['INIT_TIME'])
    out = ROOT/'evaluation_20'; out.mkdir(exist_ok=False); rows = []
    try:
        for sid in SIDS:
            adopted = sources[sid]; source = adopted['source']; prior = old_sources[sid]
            require(prior['baseline_human_data_ref'] == source['data_ref']
                    and prior['source_clock_ref'] == source['clock_ref'], 'Exact original labels/native baseline binding')
            with np.load(bound(source['data_ref']), allow_pickle=False) as data:
                baseline, labels = data['baseline'], data['labels']
                groups, score = data['groups'], data['semantic_score']
            require(baseline.dtype == labels.dtype == np.bool_
                    and labels.ndim == 2 and labels.shape[0] == baseline.size == len(adopted['points']),
                    'Actual unchanged original native/all-rater domain')
            matched = matched_semantic(groups, score, int(trained[sid].sum()))
            # Old BASELINE/INIT metrics copied byte-values from their accepted
            # first evaluation; only this new final model and new-K control scored.
            metrics = dict(BASELINE_40_47=prior['metrics']['BASELINE_40_47'],
                           INIT_TIME=prior['metrics']['INIT_TIME'],
                           TRAINED=metric(trained[sid], labels), MATCHED_SEMANTIC=metric(matched, labels))
            require(int(baseline.sum()) == metrics['BASELINE_40_47']['selected_native_frames']
                    and int(initial[sid].sum()) == metrics['INIT_TIME']['selected_native_frames'],
                    'Adopted control metrics correspond to exactly accepted control masks')
            masks = dict(BASELINE_40_47=baseline, INIT_TIME=initial[sid], TRAINED=trained[sid],
                         MATCHED_SEMANTIC=matched)
            comparisons = {name: comparison(metrics['TRAINED'], metrics[control], masks['TRAINED'], masks[control])
                for name, control in [('TRAINED_vs_INIT_TIME', 'INIT_TIME'),
                    ('TRAINED_vs_BASELINE_40_47', 'BASELINE_40_47'),
                    ('TRAINED_vs_MATCHED_SEMANTIC', 'MATCHED_SEMANTIC')]}
            row = dict(sid=sid, name=source['name'], native_frames=len(adopted['points']), reviewers=labels.shape[1],
                source_clock_ref=source['clock_ref'], baseline_human_data_ref=source['data_ref'],
                metrics=metrics, comparisons=comparisons, window_results=dict(TRAINED=counts[sid], INIT_TIME=initial_counts[sid]),
                old_baseline_and_INIT_metrics_adopted_not_recomputed=True, invalid_outputs=0,
                native_masks_saved=False, spatial_contribution='UNKNOWN_NO_SPATIAL_LABELS')
            save(out/(sid+'.json'), row); rows.append(row)
        names = ('BASELINE_40_47', 'INIT_TIME', 'TRAINED', 'MATCHED_SEMANTIC')
        macros = {name: macro(rows, name) for name in names}
        comparisons = {}
        for name, control in [('TRAINED_vs_INIT_TIME', 'INIT_TIME'),
                ('TRAINED_vs_BASELINE_40_47', 'BASELINE_40_47'),
                ('TRAINED_vs_MATCHED_SEMANTIC', 'MATCHED_SEMANTIC')]:
            delta = [row['comparisons'][name]['delta']['f1'] for row in rows]
            comparisons[name] = dict(macro_delta={key: macros['TRAINED'][key]-macros[control][key]
                for key in ('precision', 'recall', 'f1', 'native_frame_coverage')},
                improved_sources=sum(v > 0 for v in delta), decreased_sources=sum(v < 0 for v in delta),
                worst_source_delta_f1=min(delta),
                added_native_frames=sum(row['comparisons'][name]['added_native_frames'] for row in rows),
                removed_native_frames=sum(row['comparisons'][name]['removed_native_frames'] for row in rows))
        result = dict(status='COMPLETE_FIXED_NORMALIZER20_NEW_MODEL_COMPARISON_NOT_PROMOTION',
            utc=datetime.now(timezone.utc).isoformat(), generation_manifest_ref=ref(path),
            adopted_previous_evaluation_ref=manifest['adopted_previous_evaluation_ref'],
            final_adapter_ref=manifest['final_adapter_ref'], frozen_selection_ref=manifest['frozen_selection_ref'],
            sources=rows, macro=macros, comparisons=comparisons, new_model_calls=0, new_fit=0,
            previous_INIT_generation_or_control_metrics_repeated=False, raw_model_QA_replayed=False,
            historical_exposure=True, blind_test=False, official_joint_score=None,
            spatial_contribution='UNKNOWN', production_admitted=False, automatic_promotion=False,
            masks_or_submittable_oracle_saved=False, invalid_outputs=0)
        save(out/'result.json', result)
        print(__import__('json').dumps(dict(status=result['status'], macro=macros, comparisons=comparisons)))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
            successful_rows_preserved=True, automatic_retry=False, failure_to_empty=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--manifest', required=True)
    main(parser.parse_args().manifest)
