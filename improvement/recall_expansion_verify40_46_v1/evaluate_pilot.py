"""All-rater exact-second summary proxy; reference never enters inference."""
import argparse
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path
import sys
from stage_io import read, require, save, sha, utc


def merged(spans):
    out=[]
    for first,last in sorted((F(a),F(b)) for a,b in spans):
        require(0<=first<last, 'Invalid positive interval')
        if out and first<=out[-1][1]:out[-1][1]=max(last,out[-1][1])
        else:out.append([first,last])
    return out


def measure(spans):
    return sum((b-a for a,b in merged(spans)),F(0))


def metrics(pred,ref):
    pred,ref=merged(pred),merged(ref);p=measure(pred);r=measure(ref)
    overlap=sum((max(F(0),min(b,d)-max(a,c)) for a,b in pred for c,d in ref),F(0))
    return dict(f1=F(0) if not p+r else 2*overlap/(p+r),
                recall=F(0) if not r else overlap/r,precision=F(0) if not p else overlap/p)


def frames(spans,pts):
    result=set()
    for a,b in merged(spans):result.update(range(bisect_left(pts,a),bisect_left(pts,b)))
    return result


def source_prediction(events,inputs):
    baseline=[];old_d8=[];new=[]
    seen=set()
    for event in events:
        ident=event['event_id'];require(ident not in seen,'Duplicate VERIFY event');seen.add(ident)
        result=event['decision_result'];decision=result['decision']
        require(decision in ['KEEP','UNKNOWN','DROP'] and result['successful_model_call_required'], 'Incomplete actual model decision')
        meta=inputs[event['original_case_id']]
        roles=meta.get('view_roles',[meta['window_role']])
        a,b=map(F,result['original_interval_exact'])
        lo,hi=F(meta['window_start']),F(meta['window_end'])
        require(lo<=a<b<=hi,'Unmodified segment outside original accepted window')
        if 'baseline' in roles:
            old=[max(lo,a-F(3,4)),min(hi,b+F(1,2)+(F(1,4) if b-a>=8 else F(0)))]
            old_d8.append(old)
            if decision!='DROP':baseline.append(old)
        if 'overlap' in roles and decision=='KEEP':new.append([a,b])
    # The chosen official baseline uses the same source-level empty guard.
    if old_d8 and not baseline:baseline=old_d8
    return merged(baseline),merged(baseline+new),merged(new)


def assess_cases(cases,gates):
    count=len(cases);require(count==4,'Frozen complete four-source denominator')
    macro=lambda arm,key:sum((case[arm][key] for case in cases),F(0))/count
    f1_delta=macro('augmented','f1')-macro('baseline','f1')
    recall_delta=macro('augmented','recall')-macro('baseline','recall')
    conditions=dict(full_group=True,
        macro_F1_not_lower=f1_delta>=F(gates['macro_paired_all_rater_duration_F1_delta_min']),
        macro_recall_gain=recall_delta>=F(gates['macro_all_rater_recall_delta_min']),
        every_source_loss_within_gate=all(case['augmented']['f1']-case['baseline']['f1']>=F(gates['per_source_F1_delta_min']) for case in cases),
        all_rater_recall_retained=all(case['all_rater_recall_preserved'] for case in cases),
        all_baseline_native_frames_retained=all(case['baseline_native_frames_preserved'] for case in cases),
        real_changed_sources=sum(case['added_native_frames']>0 for case in cases)>=gates['minimum_sources_with_real_new_native_frames'])
    return conditions,dict(macro_F1_delta_exact=str(f1_delta),macro_recall_delta_exact=str(recall_delta),
        baseline_macro_F1_exact=str(macro('baseline','f1')),augmented_macro_F1_exact=str(macro('augmented','f1')),
        baseline_macro_recall_exact=str(macro('baseline','recall')),augmented_macro_recall_exact=str(macro('augmented','recall')))


def main(root,group):
    protocol=read(root/'protocol.json');gates=protocol['quality_gates']
    acceptance=read(root/('cpu_acceptance_'+group+'.json'))
    export_path=root/group/'VERIFY/verification_export.json';export=read(export_path)
    replay_path=root/group/'VERIFY/replay_01/completion.json';replay=read(replay_path)
    require(export['status']=='PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY' and
            replay['status']=='PASS_ALL_RECALL_VERIFY_INDEPENDENT_REPLAYS_NOT_QUALITY' and
            export['independent_replay_completion_sha256']==sha(replay_path) and
            replay['calls']==len(export['events']) and replay['CPU_only'] is True and
            replay['CUDA_initialized'] is False, 'First independent VERIFY replay receipt required')
    inputs={row['case_id']:read(row['input_path']) for row in acceptance['entries']}
    reference_pointer=read(root/('reference_completion_'+group+'.json'))
    require(sha(reference_pointer['path'])==reference_pointer['sha256'],'Native reference completion changed')
    media=read(reference_pointer['path'])['accepted']
    by_source={row['video_id']:[] for row in media}
    for event in export['events']:
        by_source[event['source_name']].append(event)
    cases=[]
    for row in media:
        vid=row['video_id'];clock=read(row['clock_path']);ref=read(row['reference_path'])
        baseline,augmented,new=source_prediction(by_source[vid],inputs)
        refs=ref['annotator_intervals_exact_seconds'];require(len(refs)==ref['annotator_count']>=2,'All original reviewers required')
        paired=[(metrics(baseline,r),metrics(augmented,r)) for r in refs]
        mean=lambda idx:{key:sum((m[idx][key] for m in paired),F(0))/len(paired) for key in ['f1','recall','precision']}
        pts=list(map(F,clock['original_exact_pts']));old_frames=frames(baseline,pts);aug_frames=frames(augmented,pts)
        cases.append(dict(video_id=vid,baseline=mean(0),augmented=mean(1),
            all_rater_recall_preserved=all(b['recall']>=a['recall'] for a,b in paired),
            baseline_native_frames_preserved=old_frames<=aug_frames,
            added_native_frames=len(aug_frames-old_frames),baseline_selected_frames=len(old_frames),
            augmented_selected_frames=len(aug_frames),added_duration_exact=str(measure(augmented)-measure(baseline)),
            annotator_count=len(refs),baseline_spans=[[str(a),str(b)] for a,b in baseline],
            augmented_spans=[[str(a),str(b)] for a,b in augmented],new_KEEP_spans=[[str(a),str(b)] for a,b in new]))
    conditions,macro=assess_cases(cases,gates);passed=all(conditions.values())
    def serial(case):
        return {**case,**{arm:{key:dict(exact=str(value),value=float(value)) for key,value in case[arm].items()}
                         for arm in ['baseline','augmented']}}
    output=root/group/'comparison_01';output.mkdir(exist_ok=False)
    result=dict(status='PASS_REGISTERED_PROXY_GROUP_PENDING_FIXED_FACT_GATE' if passed else 'STOP_PROXY_RECALL_PILOT_REJECTED',
        group=group,utc=utc(),conditions=conditions,macro=macro,cases=[serial(c) for c in cases],
        bindings=dict(protocol_sha256=sha(root/'protocol.json'),cpu_acceptance_sha256=sha(root/('cpu_acceptance_'+group+'.json')),
                      verification_export_sha256=sha(export_path)),actual_online_improvement='UNKNOWN',
        proxy_is_not_generic_highlight_or_ordinary_GT=True,old_failed_gates_changed=False)
    save(output/'result.json',result)
    if passed and group=='dev':
        save(root/'dev/selection_before_confirmation.json',dict(status='PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION',
            utc=utc(),protocol_sha256=sha(root/'protocol.json'),result_sha256=sha(output/'result.json'),
            candidate='OVERLAP15_STRIDE7_5_EXPLICIT_KEEP_ONLY',confirm_metrics_examined=False))
    print(__import__('json').dumps(dict(status=result['status'],group=group,macro=macro,conditions=conditions)))
    return 0 if passed else 5


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--group',choices=['dev','confirm'],required=True)
    args=parser.parse_args();sys.exit(main(args.root,args.group))
