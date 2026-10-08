"""One preregistered fresh 16-train/8-dev local-window experiment.

All 24 original decisions and blind selections are preserved. This admits
collection only, never student training and never a fabricated empty class.
"""
import argparse
from collections import Counter
from pathlib import Path
import socket
import subprocess
import time
import autopilot_common as c
import teacher_label as t


def verify_selection(config, validator):
    small=c.HERE/'pilot_selection'
    manifest=c.read(small/'manifest.json')
    receipt=c.read(small/'selection_receipt.json')
    train,dev=c.rows(small/'selected_train.jsonl'),c.rows(small/'selected_dev.jsonl')
    c.require(len(train)==16 and len(dev)==8 and all(w['split']=='train' for w in train)
        and all(w['split']=='dev' for w in dev),'preregistered fresh 16/8 pilot required')
    c.require(receipt['status']=='PASS_CPU_SELECTION_UNLABELLED' and receipt['confirm_opened'] is False
        and receipt['contest_assets_opened'] is False,'isolated successful pilot selection required')
    c.require(all(c.sha(small/name)==receipt['files'][name] for name in ('selected_train.jsonl','selected_dev.jsonl')),
        'pilot selected file bytes changed')
    c.require(manifest['selection_receipt_sha256']==c.sha(small/'selection_receipt.json')
        and manifest['window_ids']==[w['window_id'] for w in train+dev]
        and manifest['counts']=={'train':16,'dev':8} and manifest['no_label_access'] is True,'pilot manifest changed')
    population=Path(config['selection_dir'])
    parent_train,parent_dev=c.rows(population/'selected_train.jsonl'),c.rows(population/'selected_dev.jsonl')
    by_id={w['window_id']:w for w in parent_train+parent_dev}
    c.require(all(by_id.get(w['window_id'])==w for w in train+dev),'pilot not an exact subset of current new selection')
    if 'parent_files_sha256' in manifest:
        c.require(all(c.sha(population/name)==digest for name,digest in manifest['parent_files_sha256'].items()),'parent population changed')
    validator.validate_isolation(train,dev)
    for window in train+dev: validator.validate_window(window)
    return train,dev,small,manifest


def prepare():
    config=c.read(c.HERE/'config.json')
    verify_selection(config,t.validator_for(c.RUN))
    print('{"status":"PASS_PREREGISTERED_PILOT_SELECTION","train":16,"dev":8,"GPU_started":false}')


def gate(records):
    reasons=[]
    if len(records)!=24 or len({r['window_id'] for r in records})!=24:
        reasons.append('preserve every one of the 24 preregistered decisions')
    if any(r['status']=='INVALID_TEACHER_OR_INPUT_RECEIPT' for r in records):
        reasons.append('pilot input/model/canonical receipt invalid')
    return reasons


def reviewed_gate(records,reviews):
    reasons=gate(records)
    ids={r['window_id'] for r in records}
    reviewed=[v['window_id'] for v in reviews]
    if set(reviewed)!=ids or len(reviewed)!=len(ids):
        reasons.append('every original pilot decision requires exactly one blind second selection')
    unknown=[v['window_id'] for v in reviews if v['support_class']=='UNKNOWN']
    # Per-record disagreement stays UNKNOWN, not a batch engineering failure.
    return reasons,unknown


def run():
    c.require(socket.gethostname()=='inspur-NP5570M5','real pilot restricted to registered Linux')
    config=c.verify()
    validator=t.validator_for(c.RUN)
    train,dev,small,manifest=verify_selection(config,validator)
    teacher_out=c.HERE/'teacher_01'
    probe=c.read(teacher_out/'teacher_probe_completion.json')
    c.require(probe['status']=='PASS_REAL_NONTEST_TEACHER_PROBE'
        and probe['admission_sha256']==c.sha(teacher_out/'teacher_admission.json'),'fresh heavy probe must finish before pilot')
    admission=c.read(c.HERE/'teacher_admission.json')
    t.validate_admission(admission,validator)
    out=c.HERE/'pilot_01';out.mkdir(exist_ok=False)
    server=None;start=time.monotonic();reviews=[];fresh_count=0;reuse_count=0
    try:
        server,admission=t.start_server(admission,out)
        annotations=[]
        for index,window in enumerate(train+dev):
            directory=teacher_out/'windows'/window['window_id']
            cached=(directory/'done.json').is_file()
            if cached:
                c.require(window['window_id'] in probe['window_ids'],'only verified current heavy probe can predate pilot')
                c.require(c.sha(directory/'done.json')==probe['probe_receipts'][window['window_id']]['done_sha256'],
                    'heavy probe successful receipt changed')
            annotations.append(t.annotate(window,directory,validator,admission,admission['server_url'],3600,config['ffprobe_path'],allow_prior_reuse=True))
            fresh_count+=int(not cached);reuse_count+=int(cached)
            c.write(out/'progress.json',{'stage':'REAL_PILOT_LABELS','completed_windows':index+1,'total_windows':24,
                'fresh_model_calls':fresh_count,'verified_probe_reused_windows':reuse_count,'utc':c.utc(),'optimizer_steps':0})
        t.save_rows(out/'annotation_receipts.jsonl',annotations)
        validation=t.independent_validation(c.RUN,small/'selected_train.jsonl',small/'selected_dev.jsonl',
            small/'selection_receipt.json',out/'annotation_receipts.jsonl',out/'validated')
        records=c.rows(out/'validated/validated_records.jsonl')
        reasons=gate(records)
        c.write(out/'distribution.json',{'status':'PASS_PILOT_ENGINEERING_DISTRIBUTION_RECORDED' if not reasons else 'STOP_PILOT_ENGINEERING',
            'validation_summary':validation,'reasons':reasons,'no_label_changed':True,'no_forced_quota':True,
            'missing_empty_class_does_not_stop_collection':True,'student_training_admitted':False},fresh=True)
        c.require(not reasons,'; '.join(reasons))
        # Same exact current recipe record identity permits later all-phase reuse.
        for index,record in enumerate(sorted(records,key=lambda r:r['window_id'])):
            reviews.append(t.review_one(record,teacher_out/'reviews'/record['window_id'],validator,admission,admission['server_url'],3600,diagnostic=True))
            c.write(out/'progress.json',{'stage':'REAL_PILOT_BLIND_SECOND_SELECTION','completed_reviews':index+1,
                'selected_windows':24,'utc':c.utc(),'optimizer_steps':0})
        t.save_rows(out/'raw_semantic_review_receipts.jsonl',reviews)
        reasons,unknown=reviewed_gate(records,reviews)
        c.require(not reasons,'; '.join(reasons))
        by_id={r['window_id']:r for r in records}
        support=[by_id[v['window_id']] for v in reviews if v['support_class']!='UNKNOWN' and by_id[v['window_id']]['sft_eligible']]
        positive={split:sum(r['split']==split and bool(r['retained_segments']) for r in support) for split in ('train','dev')}
        negative={split:sum(r['split']==split and r['explicit_no_highlight'] for r in support) for split in ('train','dev')}
        can_collect=bool(positive['train'] and positive['dev'])
        boundary_count=sum(v['boundary_supported'] for v in reviews)
        # Preregistered collapse diagnostic, distinct from a negative-class quota.
        # Near-total coverage in 22/24 is a reason to inspect a narrow route,
        # rather than pretending a local-window selector has learned selectivity.
        near_whole=[r['window_id'] for r in records if r.get('retained_segments') and
            sum(s['end_sec']-s['start_sec'] for s in r['retained_segments'])/r['window']['window_duration_sec']>=0.99]
        whole_by_split={split:all(len(r.get('retained_segments',[]))==1 and r['retained_segments'][0]['start_sec']==0
            and r['retained_segments'][0]['end_sec']==r['window']['window_duration_sec'] for r in records if r['split']==split)
            for split in ('train','dev')}
        collapse=len(near_whole)>=22 or any(whole_by_split.values())
        can_collect=can_collect and not collapse
        route='COLLECT_COMPLETE_WINDOW_WEAK_SUPERVISION' if can_collect else ('ROUTE_B_BOUNDARY_FEASIBILITY' if boundary_count and not collapse else 'ROUTE_C_STOP_TEACHER')
        _,audit=t.semantic_audit(records,validation)
        completion={'status':'PASS_REAL_PILOT_READY_FOR_FULL_RELABEL' if can_collect else 'PASS_REAL_PILOT_ROUTE_DECISION_REQUIRED',
            'route_decision':route,'counts':{'train':16,'dev':8},'selected_denominator':24,
            'fresh_model_calls':fresh_count,'verified_probe_reused_windows':reuse_count,
            'eligible_by_split':validation['eligible_by_split'],'positive_by_split':positive,'explicit_empty_by_split':negative,
            'status_counts':validation['status_counts'],'support_class_counts':dict(Counter(v['support_class'] for v in reviews)),
            'original_positive_by_split':validation['positive_by_split'],'original_explicit_empty_by_split':validation['explicit_empty_by_split'],
            'unknown_window_ids':unknown,'boundary_supported_count':boundary_count,
            'near_whole_window_coverage_rule':{'fraction_at_least':0.99,'collapse_count_at_least':22,'denominator':24},
            'near_whole_window_ids':near_whole,'original_all_whole_window_by_split':whole_by_split,
            'systematic_near_whole_window_collapse':collapse,
            'raw_labels_and_reviews_preserved':True,'no_required_empty_class':True,'no_required_all_agreement':True,
            'positive_only_capability_limit':not any(negative.values()),'full_empty_rejection_supervision_available':bool(negative['train'] and negative['dev']),
            'validation_sha256':c.sha(out/'validated/validation_receipt.json'),
            'raw_reviews_sha256':c.sha(out/'raw_semantic_review_receipts.jsonl'),'pilot_manifest_sha256':c.sha(small/'manifest.json'),
            'teacher_prompt_sha256':c.sha(c.HERE/'teacher_prompt.txt'),'review_prompt_sha256':c.sha(c.HERE/'review_prompt.txt'),
            'wall_sec':time.monotonic()-start,'per_window_wall_sec':[c.read(teacher_out/'windows'/w['window_id']/'done.json')['wall_sec'] for w in train+dev],
            'same_teacher_weak_review_not_truth':True,'student_training_admitted':False,'optimizer_steps':0,
            'full_128train_32dev_review_and_new_training_gate_still_required':True,'utc':c.utc(),**audit}
        c.write(out/'pilot_semantic_quality.json',completion,fresh=True)
        c.write(out/'completion.json',completion,fresh=True)
    except BaseException as error:
        c.write(out/'completion.json',{'status':'STOP_REAL_PILOT_PRESERVED','reason':str(error),
            'completed_review_count':len(reviews),'optimizer_steps':0,'no_labels_salvaged_or_removed':True,'utc':c.utc()},fresh=True)
        raise
    finally:
        if server is not None:
            if server.poll() is None:
                server.terminate()
                try:server.wait(timeout=30)
                except subprocess.TimeoutExpired:server.kill();server.wait(timeout=30)
            c.write(out/'server_stop_receipt.json',{'owned_server_pid':server.pid,'returncode':server.returncode,
                'external_processes_signalled':False,'utc':c.utc()},fresh=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true')
    args=parser.parse_args()
    prepare() if args.prepare else run()
