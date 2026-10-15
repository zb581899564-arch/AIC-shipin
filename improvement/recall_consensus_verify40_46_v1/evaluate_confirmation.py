"""First untouched four-source confirmation of the fixed consensus2 rule."""
import argparse
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import sys
import model_common as io
from consensus import agreed_keep


def main(root):
    io.host(cpu=True)
    root=io.root_path(root)
    reg=io.read(root/'fresh_confirm_registration.json')
    protocol=io.read(root/'protocol.json')
    io.require(reg['protocol_ref']['sha256']==io.sha(root/'protocol.json'), 'Frozen new protocol changed')
    prior_metrics=Path('/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1/code/evaluate_pilot.py')
    io.require(str(prior_metrics) in reg['required_files'] and io.sha(prior_metrics)==reg['required_files'][str(prior_metrics)],
               'Original pure proxy metric implementation must be frozen')
    spec=importlib.util.spec_from_file_location('unchanged_proxy_metric_functions',prior_metrics)
    proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
    cpu_path=root/'cpu_acceptance_confirm.json';cpu=io.read(cpu_path)
    inputs={e['case_id']:io.read(io.checked(e['input_path'],e['input_sha256'])) for e in cpu['entries']}
    io.require(len(inputs)==len(cpu['entries'])>0,'Complete distinct real CPU inputs required')
    b0path=root/'confirm/B0/replay_01/completion.json';b0=io.read(b0path)
    io.require(b0['status']=='PASS_ALL_RECALL_B0_INDEPENDENT_REPLAYS_NOT_QUALITY' and b0['calls']==len(inputs) and
               b0['CPU_only'] is True and b0['CUDA_initialized'] is False,'Complete first B0 QA required')
    export_path=root/'confirm/VERIFY/verification_export.json';export=io.read(export_path)
    io.require(export['status']=='PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY','Actual complete new VERIFY export required')
    events=export['events']
    if events:
        replay_path=root/'confirm/VERIFY/replay_01/completion.json';replay=io.read(replay_path)
        io.require(replay['status']=='PASS_ALL_RECALL_VERIFY_INDEPENDENT_REPLAYS_NOT_QUALITY' and
                   replay['calls']==len(events) and replay['CPU_only'] is True and replay['CUDA_initialized'] is False and
                   export['independent_replay_completion_sha256']==io.sha(replay_path),'Complete first VERIFY QA required')
    else:
        prepared=io.read(root/'confirm/VERIFY/cpu_01/completion.json')
        io.require(prepared['entries']==[] and not (root/'gpu_admission_confirm_VERIFY.json').exists(),
                   'Empty event export is legal only after actual complete B0 and true zero planned VERIFY candidates')
    pointer=io.read(root/'reference_completion_confirm.json')
    ref_path=io.checked(pointer['path'],pointer['sha256']);accepted=io.read(ref_path)['accepted']
    io.require(len(accepted)==len({s['video_id'] for s in accepted})==4,'Frozen full fresh four-source denominator')
    by_source={s['video_id']:[] for s in accepted};seen=set()
    for event in events:
        io.require(event['event_id'] not in seen and event['source_name'] in by_source,'Duplicate or foreign actual event')
        seen.add(event['event_id']);by_source[event['source_name']].append(event)
    cases=[]
    for source in accepted:
        vid=source['video_id'];rows=by_source[vid]
        baseline,_,_=proxy.source_prediction(rows,inputs)
        views={}
        for event in rows:
            meta=inputs[event['original_case_id']];decision=event['decision_result']
            io.require(decision['successful_model_call_required'] is True and decision['decision'] in ('KEEP','UNKNOWN','DROP'),
                       'Actual accepted model decision required')
            if 'overlap' not in meta.get('view_roles',[meta['window_role']]):continue
            geometry=(str(F(meta['window_start'])),str(F(meta['window_end'])))
            views.setdefault(geometry,[])
            if decision['decision']=='KEEP':views[geometry].append(decision['original_interval_exact'])
        novel=agreed_keep(views);augmented=proxy.merged(baseline+novel)
        ref=io.read(source['reference_path']);clock=io.read(source['clock_path'])
        reviewers=ref['annotator_intervals_exact_seconds']
        io.require(len(reviewers)==ref['annotator_count']>=2,'All original untouched reviewers required')
        paired=[(proxy.metrics(baseline,r),proxy.metrics(augmented,r)) for r in reviewers]
        mean=lambda arm:{k:sum((p[arm][k] for p in paired),F(0))/len(paired) for k in ('f1','recall','precision')}
        before,after=mean(0),mean(1)
        pts=list(map(F,clock['original_exact_pts']));old_frames=proxy.frames(baseline,pts);new_frames=proxy.frames(augmented,pts)
        serial=lambda value:{k:dict(exact=str(v),value=float(v)) for k,v in value.items()}
        cases.append(dict(video_id=vid,baseline=serial(before),augmented=serial(after),
            F1_delta_exact=str(after['f1']-before['f1']),all_rater_recall_preserved=all(b['recall']>=a['recall'] for a,b in paired),
            baseline_native_frames_preserved=old_frames<=new_frames,added_native_frames=len(new_frames-old_frames),
            baseline_selected_frames=len(old_frames),augmented_selected_frames=len(new_frames),annotator_count=len(reviewers),
            baseline_spans=[[str(a),str(b)] for a,b in baseline],augmented_spans=[[str(a),str(b)] for a,b in augmented],
            new_KEEP_consensus_spans=[[str(a),str(b)] for a,b in novel]))
    macro=lambda arm,key:sum((F(c[arm][key]['exact']) for c in cases),F(0))/4
    delta={k:macro('augmented',k)-macro('baseline',k) for k in ('f1','recall','precision')}
    gates=protocol['quality_gates']
    conditions=dict(full_group=True,macro_F1_not_lower=delta['f1']>=F(gates['macro_F1_delta_min']),
        macro_recall_gain=delta['recall']>=F(gates['macro_recall_delta_min']),
        every_source_loss_within_gate=all(F(c['F1_delta_exact'])>=F(gates['per_source_F1_delta_min']) for c in cases),
        macro_precision_not_lower=delta['precision']>=F(gates['macro_precision_delta_min']),
        all_rater_recall_retained=all(c['all_rater_recall_preserved'] for c in cases),
        all_baseline_native_frames_retained=all(c['baseline_native_frames_preserved'] for c in cases),
        real_changed_sources=sum(c['added_native_frames']>0 for c in cases)>=gates['minimum_changed_sources'])
    passed=all(conditions.values());out=root/'confirm/comparison_01';out.mkdir(exist_ok=False)
    value=dict(status='PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40' if passed else 'STOP_CONSENSUS_FRESH_CONFIRM_REJECTED',
        group='confirm',utc=io.utc(),conditions=conditions,cases=cases,
        macro={k:dict(baseline=float(macro('baseline',k)),augmented=float(macro('augmented',k)),delta_exact=str(delta[k]),delta=float(delta[k])) for k in delta},
        bindings=dict(protocol_sha256=io.sha(root/'protocol.json'),registration_sha256=io.sha(root/'fresh_confirm_registration.json'),
            cpu_acceptance_sha256=io.sha(cpu_path),verification_export_sha256=io.sha(export_path),
            first_B0_QA_sha256=io.sha(b0path),reference_completion_sha256=io.sha(ref_path)),
        candidate=protocol['candidate'],scope='EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NOT_HIGHLIGHT_GOLD',
        source_metrics_exposed_first_time=True,online_improvement='UNKNOWN',production_admitted=False,
        no_426_model_or_package_started=True,prior_failed_gates_changed=False)
    io.save(out/'result.json',value)
    print(json.dumps(dict(status=value['status'],conditions=conditions,macro=value['macro'])))
    return 0 if passed else 5


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();sys.exit(main(a.root))
