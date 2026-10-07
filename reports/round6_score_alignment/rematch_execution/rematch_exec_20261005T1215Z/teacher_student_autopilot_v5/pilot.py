"""Preregister a label-independent 12-window pilot, then run real weak review.

This pilot never admits student training. The full 128/32 science gate remains
mandatory. No old-recipe label can enter this version's cache.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import time
from types import SimpleNamespace

import autopilot_common as c
import teacher_label as t


def choose(train, dev):
    def ranked(population, count):
        return sorted(population, key=lambda w: (hashlib.sha256(w['window_id'].encode()).hexdigest(), w['window_id']))[:count]
    return ranked(train, 8), ranked(dev, 4)


def prepare():
    config = c.read(c.HERE / 'config.json')
    selection = Path(config['selection_dir'])
    validator = t.validator_for(c.RUN)
    args = SimpleNamespace(selection_receipt=selection/'selection_receipt.json',
        selected_train=selection/'selected_train.jsonl', selected_dev=selection/'selected_dev.jsonl')
    train, dev = t.load_selection(args, validator)
    small_train, small_dev = choose(train, dev)
    out = c.HERE / 'pilot_selection'
    out.mkdir(exist_ok=False)
    for split, values in (('train', small_train), ('dev', small_dev)):
        t.save_rows(out / ('selected_' + split + '.jsonl'), values)
    original = c.read(args.selection_receipt)
    receipt = {**original, 'schema': 'aic_preregistered_nontest_pilot_subset_v5',
        'status': 'PASS_CPU_SELECTION_UNLABELLED', 'purpose': 'PILOT_ONLY_NOT_FULL_STUDENT_ADMISSION',
        'parent_selection_receipt': {'path':str(args.selection_receipt),'sha256':c.sha(args.selection_receipt)},
        'files': {name:c.sha(out/name) for name in ('selected_train.jsonl','selected_dev.jsonl')},
        'pilot_rule': 'SHA256_WINDOW_ID_ASCENDING_8TRAIN_4DEV',
        'label_values_or_prior_answers_read':False, 'confirm_opened':False, 'contest_assets_opened':False,
        'selected_windows':{'train':8,'dev':4}, 'created_utc':c.utc()}
    c.write(out/'selection_receipt.json', receipt, fresh=True)
    c.write(out/'manifest.json', {'status':'PASS_PREREGISTERED_LABEL_INDEPENDENT_PILOT',
        'window_ids':[w['window_id'] for w in small_train+small_dev],
        'counts':{'train':8,'dev':4}, 'rule':receipt['pilot_rule'],
        'parent_files_sha256':{name:c.sha(selection/name) for name in ('selected_train.jsonl','selected_dev.jsonl','selection_receipt.json')},
        'selection_receipt_sha256':c.sha(out/'selection_receipt.json'),
        'no_label_access':True, 'teacher_prompt_sha256':c.sha(c.HERE/'teacher_prompt.txt')}, fresh=True)
    print(json.dumps({'status':'PASS_PREREGISTERED_PILOT_SELECTION','train':8,'dev':4,'GPU_started':False}))


def gate(records):
    """Pilot diversity gate; the stricter full-split gate is unchanged."""
    eligible = [r for r in records if r['sft_eligible']]
    reasons = []
    if len(records) != 12 or len({r['window_id'] for r in records}) != 12:
        reasons.append('pilot must preserve all twelve unique responses')
    if any(r['status'] == 'INVALID_TEACHER_OR_INPUT_RECEIPT' for r in records):
        reasons.append('pilot has an invalid teacher/input receipt')
    if not any(r.get('explicit_no_highlight') is True for r in eligible):
        reasons.append('no real justified empty observed; do not force an empty quota')
    if not any(bool(r.get('retained_segments')) for r in eligible):
        reasons.append('no explainable positive observed; do not force positives')
    for split in ('train','dev'):
        subset = [r for r in eligible if r['split']==split]
        if not subset:
            reasons.append(split + ' has no eligible pilot observation')
        if subset and all(len(r['retained_segments'])==1 and r['retained_segments'][0]['start_sec']==0
                and r['retained_segments'][0]['end_sec']==r['window']['window_duration_sec'] for r in subset):
            reasons.append(split + ' systematically selects the whole window')
    return reasons


def run():
    c.require(socket.gethostname()=='inspur-NP5570M5','real pilot restricted to registered Linux')
    config = c.verify()
    manifest = c.read(c.HERE/'pilot_selection/manifest.json')
    selection = Path(config['selection_dir'])
    c.require(all(c.sha(selection/name)==digest for name,digest in manifest['parent_files_sha256'].items()),'pilot population changed')
    out = c.HERE/'pilot_01'; out.mkdir(exist_ok=False)
    small = c.HERE/'pilot_selection'
    train,dev = c.rows(small/'selected_train.jsonl'),c.rows(small/'selected_dev.jsonl')
    whole_train,whole_dev = c.rows(selection/'selected_train.jsonl'),c.rows(selection/'selected_dev.jsonl')
    c.require((train,dev)==choose(whole_train,whole_dev),'pilot no longer follows preregistered hash rule')
    c.require([w['window_id'] for w in train+dev]==manifest['window_ids'],'pilot identities differ')
    validator = t.validator_for(c.RUN)
    admission = c.read(c.HERE/'teacher_admission.json')
    t.validate_admission(admission,validator)
    server = None; start = time.monotonic(); reviews=[]
    try:
        server,admission=t.start_server(admission,out)
        annotations=[]
        for index,window in enumerate(train+dev):
            annotations.append(t.annotate(window,c.HERE/'teacher_01/windows'/window['window_id'],validator,
                admission,admission['server_url'],3600,config['ffprobe_path'],allow_prior_reuse=False))
            c.write(out/'progress.json',{'stage':'REAL_PILOT_LABELS','completed_windows':index+1,'total_windows':12,
                'last_window_id':window['window_id'],'utc':c.utc(),'optimizer_steps':0})
        t.save_rows(out/'annotation_receipts.jsonl',annotations)
        validation=t.independent_validation(c.RUN,small/'selected_train.jsonl',small/'selected_dev.jsonl',
            small/'selection_receipt.json',out/'annotation_receipts.jsonl',out/'validated')
        records=c.rows(out/'validated/validated_records.jsonl')
        reasons=gate(records)
        c.write(out/'distribution.json',{'status':'PASS_PILOT_DISTRIBUTION' if not reasons else 'STOP_PILOT_DISTRIBUTION',
            'validation_summary':validation,'reasons':reasons,'no_label_changed':True,'no_forced_quota':True,
            'student_training_admitted':False},fresh=True)
        c.require(not reasons,'; '.join(reasons))
        for index,record in enumerate(sorted((r for r in records if r['sft_eligible']),key=lambda r:r['window_id'])):
            reviews.append(t.review_one(record,out/'reviews'/record['window_id'],validator,admission,admission['server_url'],3600))
            c.write(out/'progress.json',{'stage':'REAL_PILOT_SECOND_WEAK_REVIEW','completed_reviews':index+1,
                'eligible_windows':validation['eligible_count'],'utc':c.utc(),'optimizer_steps':0})
        t.save_rows(out/'raw_semantic_review_receipts.jsonl',reviews)
        _,audit=t.semantic_audit(records,validation) # representative data only; full-gate reasons not waived
        c.write(out/'completion.json',{'status':'PASS_REAL_PILOT_READY_FOR_FULL_RELABEL',
            'counts':{'train':8,'dev':4},'eligible_by_split':validation['eligible_by_split'],
            'positive_by_split':validation['positive_by_split'],'explicit_empty_by_split':validation['explicit_empty_by_split'],
            'status_counts':validation['status_counts'],'reviewed_eligible_windows':len(reviews),
            'validation_sha256':c.sha(out/'validated/validation_receipt.json'),
            'raw_reviews_sha256':c.sha(out/'raw_semantic_review_receipts.jsonl'),
            'pilot_manifest_sha256':c.sha(small/'manifest.json'),'teacher_prompt_sha256':c.sha(c.HERE/'teacher_prompt.txt'),
            'wall_sec':time.monotonic()-start,'per_window_wall_sec':[c.read(c.HERE/'teacher_01/windows'/w['window_id']/'done.json')['wall_sec'] for w in train+dev],
            'same_teacher_weak_review_not_truth':True,'student_training_admitted':False,'optimizer_steps':0,
            'full_128train_32dev_and_original_semantic_gate_still_required':True,'utc':c.utc(),**audit},fresh=True)
    except BaseException as error:
        c.write(out/'completion.json',{'status':'STOP_REAL_PILOT_PRESERVED','reason':str(error),
            'completed_review_count':len(reviews),'optimizer_steps':0,'no_labels_salvaged_or_removed':True,'utc':c.utc()},fresh=True)
        raise
    finally:
        if server is not None:
            if server.poll() is None:
                server.terminate()
                try: server.wait(timeout=30)
                except subprocess.TimeoutExpired: server.kill();server.wait(timeout=30)
            c.write(out/'server_stop_receipt.json',{'owned_server_pid':server.pid,'returncode':server.returncode,
                'external_processes_signalled':False,'utc':c.utc()},fresh=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true')
    args=parser.parse_args()
    prepare() if args.prepare else run()
