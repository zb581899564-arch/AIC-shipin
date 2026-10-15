"""New CPU-only development comparison adopting all old completed calls/QA.

Both old groups are now exposed development data. None is called blind or
replayed. No media/tensor/processor/model operations or old writes occur.
"""
import argparse
from fractions import Fraction as F
import json
import os
from pathlib import Path
import sys
import traceback
from consensus import agreed_keep


def main(root, old):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(old/'code'))
    import stage_io as io
    import evaluate_pilot as proxy
    io.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only child required')
    protocol = io.read(root/'protocol.json')
    io.require(protocol['candidate'] == 'TWO_DISTINCT_OVERLAP_VIEWS_EXPLICIT_KEEP_INTERSECTION' and
               protocol['development_source_count'] == 8 and protocol['old_confirmation_is_exposed_development'] is True,
               'New frozen single-arm development protocol required')
    io.require(io.sha(root/'code/consensus.py') == protocol['code_sha256']['consensus.py'] and
               io.sha(__file__) == protocol['code_sha256']['evaluate_development.py'], 'Frozen new code changed')
    out = root/'development_01'
    out.mkdir(exist_ok=False)
    io.save(out/'started.json', dict(utc=io.utc(), pid=os.getpid(), CPU_only=True,
        new_model_calls=0, new_decode_calls=0, new_processor_calls=0,
        no_old_model_QA_or_metric_rerun=True, protocol_sha256=io.sha(root/'protocol.json')))
    try:
        cases, adopted = [], {}
        for group, chain in [('dev', 'chain_02'), ('confirm', 'chain_03')]:
            complete_path = old/group/chain/'completion.json'
            complete = io.read(complete_path)
            prior_path = old/group/'comparison_01/result.json'
            prior = io.read(prior_path)
            io.require(complete['comparison_sha256'] == io.sha(prior_path) and
                       len(prior['cases']) == 4 and complete['group'] == group,
                       'Original complete source denominator/terminal changed')
            io.require(io.sha(prior_path) == protocol['adopted_prior_results'][group], 'Original outcome changed')
            export_path = old/group/'VERIFY/verification_export.json'
            export = io.read(export_path)
            replay_path = old/group/'VERIFY/replay_01/completion.json'
            replay = io.read(replay_path)
            io.require(export['status'] == 'PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY' and
                       replay['status'] == 'PASS_ALL_RECALL_VERIFY_INDEPENDENT_REPLAYS_NOT_QUALITY' and
                       export['independent_replay_completion_sha256'] == io.sha(replay_path) and
                       replay['calls'] == len(export['events']) and replay['CPU_only'] is True and
                       replay['CUDA_initialized'] is False and
                       prior['bindings']['verification_export_sha256'] == io.sha(export_path),
                       'Adopt only complete real VERIFY calls and original independent QA')
            cpu_path = old/('cpu_acceptance_'+group+'.json')
            io.require(prior['bindings']['cpu_acceptance_sha256'] == io.sha(cpu_path), 'Original CPU inputs changed')
            inputs = {row['case_id']: io.read(row['input_path']) for row in io.read(cpu_path)['entries']}
            pointer_path = old/('reference_completion_'+group+'.json')
            pointer = io.read(pointer_path)
            media = io.read(io.checked(pointer['path'], pointer['sha256']))['accepted']
            prior_cases = {c['video_id']: c for c in prior['cases']}
            io.require(set(prior_cases) == {r['video_id'] for r in media}, 'Original reference identities changed')
            by_source = {row['video_id']: [] for row in media}
            seen = set()
            for event in export['events']:
                io.require(event['event_id'] not in seen, 'Duplicate original event')
                seen.add(event['event_id'])
                by_source[event['source_name']].append(event)
            for row in media:
                vid = row['video_id']; events = by_source[vid]
                views = {}
                for event in events:
                    result = event['decision_result']
                    io.require(result['successful_model_call_required'] is True and
                               result['decision'] in ('KEEP', 'UNKNOWN', 'DROP'), 'Actual decision missing')
                    meta = inputs[event['original_case_id']]
                    roles = meta.get('view_roles', [meta['window_role']])
                    if 'overlap' not in roles:
                        continue
                    geometry = (str(F(meta['window_start'])), str(F(meta['window_end'])))
                    views.setdefault(geometry, [])
                    if result['decision'] == 'KEEP':
                        views[geometry].append(result['original_interval_exact'])
                addition = agreed_keep(views)
                previous = prior_cases[vid]
                baseline = proxy.merged(previous['baseline_spans'])
                augmented = proxy.merged(baseline+addition)
                clock = io.read(row['clock_path']); ref = io.read(row['reference_path'])
                reviewers = ref['annotator_intervals_exact_seconds']
                io.require(len(reviewers) == ref['annotator_count'] >= 2, 'All original reviewers required')
                values = [proxy.metrics(augmented, r) for r in reviewers]
                mean = {k: sum((v[k] for v in values), F(0))/len(values) for k in ('f1', 'recall', 'precision')}
                before = {k: F(previous['baseline'][k]['exact']) for k in mean}
                pts = list(map(F, clock['original_exact_pts']))
                before_frames = proxy.frames(baseline, pts); after_frames = proxy.frames(augmented, pts)
                io.require(before_frames <= after_frames and proxy.merged(baseline+augmented) == augmented,
                           'Protected baseline changed')
                serial = lambda m: {k: dict(exact=str(v), value=float(v)) for k,v in m.items()}
                cases.append(dict(video_id=vid, exposed_previous_group=group, baseline=serial(before),
                    augmented=serial(mean), F1_delta_exact=str(mean['f1']-before['f1']),
                    added_native_frames=len(after_frames-before_frames), distinct_original_overlap_views=len(views),
                    all_baseline_frames_retained=True, all_rater_recall_retained_by_superset=True,
                    old_single_view_added_frames=previous['added_native_frames'],
                    new_KEEP_consensus_spans=[[str(a), str(b)] for a,b in addition]))
            adopted[group] = dict(completion_sha256=io.sha(complete_path), comparison_sha256=io.sha(prior_path),
                verification_export_sha256=io.sha(export_path), first_QA_sha256=io.sha(replay_path),
                prior_real_calls=len(export['events']), reused_without_repeating=True)
        io.require(len(cases) == len({c['video_id'] for c in cases}) == 8, 'Complete eight-source development required')
        macro = lambda arm,k: sum((F(c[arm][k]['exact']) for c in cases),F(0))/8
        d = {k: macro('augmented', k)-macro('baseline', k) for k in ('f1','recall','precision')}
        gates = protocol['quality_gates']
        conditions = dict(full_group=True, macro_F1_not_lower=d['f1'] >= 0,
            macro_recall_gain=d['recall'] >= F(gates['macro_recall_delta_min']),
            every_source_loss_within_gate=all(F(c['F1_delta_exact']) >= F(gates['per_source_F1_delta_min']) for c in cases),
            macro_precision_not_lower=d['precision'] >= 0,
            all_rater_recall_retained=True, all_baseline_native_frames_retained=True,
            real_changed_sources=sum(c['added_native_frames']>0 for c in cases) >= gates['minimum_changed_sources'])
        passed = all(conditions.values())
        result = dict(status='PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM' if passed else 'STOP_CONSENSUS_DEVELOPMENT_REJECTED',
            utc=io.utc(),candidate=protocol['candidate'],conditions=conditions,
            macro={k:dict(baseline=float(macro('baseline',k)),augmented=float(macro('augmented',k)),
                         delta_exact=str(d[k]),delta=float(d[k])) for k in d}, cases=cases,
            adopted_original_evidence=adopted,new_model_calls=0,new_decode_calls=0,new_processor_calls=0,
            old_confirmation_used_as_blind=False, prior_failure_and_gates_unchanged=True,
            protocol_sha256=io.sha(root/'protocol.json'),production_admitted=False,
            scope='EXPOSED_EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NOT_HIGHLIGHT_GOLD',online_improvement='UNKNOWN')
        io.save(out/'result.json',result)
        if passed:
            io.save(root/'selection_before_fresh_confirmation.json',dict(status='FROZEN_CONSENSUS2_AFTER_DEV_PASS',
                protocol_sha256=io.sha(root/'protocol.json'),result_sha256=io.sha(out/'result.json'),
                fresh_confirm_metrics_examined=False,candidate=protocol['candidate']))
        print(json.dumps(dict(status=result['status'],conditions=conditions,macro=result['macro'])))
        return 0 if passed else 5
    except BaseException as error:
        io.save(out/'failure.json',dict(utc=io.utc(),error=repr(error),traceback=traceback.format_exc(),no_repeated_success=True))
        raise


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--old-root',type=Path,required=True)
    a=p.parse_args();sys.exit(main(a.root,a.old_root))
