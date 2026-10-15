"""Exact completed V11 observations and blind reviews, with original costs.

This manifest authorizes 160 first answers and 28 completed second answers only.
It never authorizes a failed answer, a new label, or a semantic reclassification.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import shutil
import socket
import sys
from datetime import datetime

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
OLD = RUN/'teacher_student_autopilot_v11'
MANIFEST = HERE/'v11_resume_manifest.json'
LOCK_SHA = '0ae09ec38ff589baa5e15e16b84457b06442195de502ec7ef6a19bab9b715578'
SCHEMA = 'AIC_EXACT_V11_COMPLETE_LABELS_AND_REVIEWS_RESUME_V1'
LEGACY = {'complete_087af79e4b421be308d6cf6f', 'complete_8ab21c80e0bff423c3ce016b'}

def require(ok, message):
    if not ok: raise ValueError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''): h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def files_match(files, *, frozen_runtime_library_links=False):
    for path, expected in files.items():
        p=Path(path)
        if p.is_symlink():
            runtime=RUN/'teacher32b_runtime_v2/runtime/build/bin'
            require(frozen_runtime_library_links and p.parent==runtime and p.name.startswith('lib')
                and '.so' in p.name and p.resolve().parent==runtime
                and files.get(str(p.resolve()))==expected,'unapproved receipt or runtime link: '+path)
        require(p.is_file() and sha(p)==expected,'original receipt bytes changed: '+path)

def load_manifest():
    value=read(MANIFEST)
    require(value['schema']==SCHEMA and value['status']=='PASS_ORIGINAL_V11_VALIDATOR_AND_ALL_BOUND_BYTES_CPU'
        and value['original_source_lock_sha256']==LOCK_SHA and len(value['labels'])==160
        and len(value['reviews'])==28 and value['GPU_started'] is False and value['new_model_calls']==0,
        'exact V11 resume authority differs')
    if (HERE/'source_lock.json').exists():
        require(read(HERE/'source_lock.json')['files'].get(str(MANIFEST))==sha(MANIFEST),'resume manifest is not frozen')
    files_match(value['authority_files'])
    return value

def entry(record, manifest=None):
    value=manifest or load_manifest()
    identity=record.get('window_id')
    matches=[row for row in value['labels'] if row['window_id']==identity]
    require(len(matches)==1 and matches[0]['teacher_record_sha256']==digest(record),'unapproved first answer or identity')
    row=matches[0]
    require(read(Path(row['directory'])/'validated_record.json')==record,'first answer differs from its original file')
    return row

def approved_review(record, admission):
    value=load_manifest(); entry(record,value)
    original=read(OLD/'teacher_admission.json')
    require(all(admission[k]==original[k] for k in value['admission_keys']),'review model/runtime/input recipe differs')
    matches=[row for row in value['reviews'] if row['window_id']==record['window_id']]
    if not matches: return None
    require(len(matches)==1,'duplicate old second answer')
    row=matches[0]; files_match(row['files'])
    review=read(Path(row['directory'])/'review_receipt.json')
    require(digest(review)==row['review_sha256'] and review['teacher_record_sha256']==digest(record),
        'original blind review changed')
    return review

def verify_review_job_binding(review, record):
    value=load_manifest(); entry(record,value)
    actual=review['second_teacher']['job_source_lock_sha256']
    current=read(HERE/'teacher_admission.json')['job_source_lock_sha256']
    require(current==sha(HERE/'source_lock.json'),'review consumer source lock changed')
    if actual==current:
        return # Fresh current review; all other raw/model/input checks remain in teacher_label.
    require(actual==LOCK_SHA,'unapproved old reviewer source lock')
    approved=[row for row in value['reviews'] if row['window_id']==record['window_id']]
    require(len(approved)==1 and approved[0]['review_sha256']==digest(review),'unapproved old blind review')
    files_match(approved[0]['files'])
    require(read(Path(approved[0]['directory'])/'review_receipt.json')==review,'original review object changed')

def function_view(path,names):
    return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(Path(path).read_bytes()).body
        if isinstance(node,ast.FunctionDef) and node.name in names}

def prepare_manifest():
    require(socket.gethostname()=='inspur-NP5570M5','actual original evidence is Linux only')
    require(not MANIFEST.exists() and not any((HERE/n).exists() for n in ('source_lock.json','registration.json','start_receipt.json')),
        'never overwrite or reseal a resume authority')
    require(sha(OLD/'source_lock.json')==LOCK_SHA,'V11 original lock differs')
    files_match(read(OLD/'source_lock.json')['files'],frozen_runtime_library_links=True)
    require(read(OLD/'completion.json')['status']=='STOP_AUTOPILOT_PRESERVED','V11 STOP must remain')
    semantic=read(OLD/'teacher_01/semantic_review.json')
    require(semantic['status']=='STOP_AUTOMATED_WEAK_SEMANTIC_REVIEW'
        and semantic['reasons']==['ValueError: canonical response is not the exact native ID projection']
        and semantic['selected_denominator']==160 and semantic['completed_review_count']==5,'unexpected prior failure')
    require(not (OLD/'student_01/student_completion.json').exists(),'unexpected previous student execution')
    # Scientific functions and real request construction are unchanged.
    for name in ('boundary_ids.py','teacher_prompt.txt','review_prompt.txt','supervision/validate_teacher.py',
        'supervision/select_windows.py','train_student.py','production_t.py','source_color.py','cost_contract.py'):
        require(sha(HERE/name)==sha(OLD/name),'recipe/validator/student changed: '+name)
    unchanged=('image_data_url','record_processor_runtime','input_contract','start_server','inference',
        'review_prompt','review_response','compare_selections','teacher_receipt','semantic_audit','semantic_review')
    require(function_view(HERE/'teacher_label.py',unchanged)==function_view(OLD/'teacher_label.py',unchanged),
        'review science or actual visual request changed')
    sys.path.insert(0,str(OLD))
    import teacher_label as original
    require(Path(original.__file__).resolve()==OLD/'teacher_label.py','original helper identity mixed')
    validator=original.validator_for(RUN)
    all_records=rows(OLD/'teacher_01/validated/validated_records.jsonl')
    selected={w['window_id']:w for split in ('train','dev') for w in rows(OLD/'selection_01'/('selected_'+split+'.jsonl'))}
    require(len(all_records)==len(selected)==160 and {v['window_id'] for v in all_records}==set(selected),'original denominator differs')
    labels=[]; reviews=[]; all_files={}; proof=[]
    for record in sorted(all_records,key=lambda r:r['window_id']):
        identity=record['window_id']
        directory=(RUN/'teacher_student_autopilot_v10' if identity in LEGACY else OLD)/'teacher_01/windows'/identity
        done=read(directory/'done.json'); annotation=read(directory/'annotation.json'); original_record=read(directory/'validated_record.json')
        require(done['status']=='PASS_COMPLETE_ANNOTATION_RECEIPT' and record==original_record
            and record['window']==selected[identity],'original successful annotation/selection differs')
        bound={str(directory/name):expected for name,expected in done['files'].items()}
        bound[str(directory/'done.json')]=sha(directory/'done.json')
        for frame in annotation['observation']['frame_files']:
            bound[str(Path(frame['path']))]=sha(frame['path'])
        files_match(bound); all_files.update(bound)
        recomputed=validator.make_record(record['window'],annotation['observation'],annotation['teacher'],annotation['raw_answer'])
        require(recomputed==record and record['status']!='INVALID_TEACHER_OR_INPUT_RECEIPT','frozen original validator no longer reproduces target')
        original.verify_model_decision_projection(original_record)
        original.frame_content(annotation['observation'])
        require(annotation['model_raw_answer']==(directory/'raw_answer.txt').read_bytes().decode('utf-8'),'original model raw alias differs')
        if identity in LEGACY:
            try: original.verify_model_decision_projection(record)
            except ValueError as exc:
                require(str(exc)=='canonical response is not the exact native ID projection','different legacy failure')
                proof.append(dict(window_id=identity,original_file_projection_pass=True,sorted_JSONL_projection_reproduced_failure=str(exc),
                    original_canonical_sha256=original.text_sha(record['raw_answer']),
                    sorted_parsed_serialization_sha256=original.text_sha(json.dumps(record['parsed_answer'],ensure_ascii=False,allow_nan=False,separators=(',',':'))),
                    original_and_JSONL_record_objects_equal=True))
            else: raise ValueError('actual legacy sorted-key failure was not reproduced')
        labels.append(dict(window_id=identity,split=record['split'],directory=str(directory),files=bound,
            teacher_record_sha256=digest(record),model_raw_sha256=original.text_sha(annotation['model_raw_answer']),
            original_validator_reproduced_exact_record=True))
        review_dir=OLD/'teacher_01/reviews'/identity
        if not (review_dir/'done.json').exists():
            require(not review_dir.exists(),'incomplete/failed old review cannot be resumed automatically')
            continue
        review_done=read(review_dir/'done.json'); review=read(review_dir/'review_receipt.json')
        review_files={str(review_dir/name):expected for name,expected in review_done['files'].items()}
        review_files[str(review_dir/'done.json')]=sha(review_dir/'done.json')
        files_match(review_files); all_files.update(review_files)
        require(review_done['teacher_record_sha256']==digest(record),'old review first-record binding differs')
        original.verify_blind_review_projection(review,original_record,validator)
        require(review['second_teacher']['job_source_lock_sha256']==LOCK_SHA,'unapproved prior reviewer')
        reviews.append(dict(window_id=identity,directory=str(review_dir),files=review_files,review_sha256=digest(review),
            teacher_record_sha256=digest(record),original_blind_validator_pass=True))
    require(len(labels)==160 and len(reviews)==28 and len(proof)==2,'actual successful resume set differs')
    authority_paths=[OLD/'source_lock.json',OLD/'completion.json',OLD/'teacher_admission.json',
        OLD/'pilot_01/completion.json',OLD/'teacher_01/teacher_completion.json',OLD/'teacher_01/semantic_review.json',
        OLD/'teacher_01/teacher_stop.json',OLD/'teacher_01/raw_semantic_review_receipts.jsonl',
        OLD/'teacher_01/annotation_receipts.jsonl',*sorted((OLD/'teacher_01/validated').glob('*.json*')),
        RUN/'controller/V11_real_pilot_acceptance_20261008.json',RUN/'controller/V11_real_first_generation_acceptance_20261008.json']
    costs=[]
    for name in ('rematch_TAUTO_v10_teacher_visual_interface','rematch_TAUTO_v10_teacher_probe',
        'rematch_TAUTO_v11_teacher_pilot','rematch_TAUTO_v11_teacher_full'):
        path=RUN/'controller'/(name+'.resource.json');d=read(path)
        require(d['stop_reason'] is None and d['charged_seconds']>0
            and (d['status'],d['exit_code'])==(('failed',1) if name.endswith('v11_teacher_full') else ('completed',0)),
            'original GPU termination/accounting incomplete')
        costs.append(dict(path=str(path),sha256=sha(path),status=d['status'],exit_code=d['exit_code'],charged_seconds=d['charged_seconds']))
        authority_paths.append(path)
    # Costs derive from actual old reviews, never from the label-only wall rate.
    walls=[]; sizes=[]
    for row in reviews:
        directory=Path(row['directory']);http=read(directory/'http/http_receipt.json')
        response=read(directory/'server_response.json')
        timings=response.get('timings',{})
        wall=(datetime.fromisoformat(http['finished_utc'])-datetime.fromisoformat(http['started_utc'])).total_seconds()
        require(math.isfinite(wall) and wall>0,'actual independent review model cost missing')
        walls.append(wall);sizes.append(sum(Path(path).stat().st_size for path in row['files']))
    admission_keys=('base_model_id','model_id','model_revision','runtime_revision','weight_files','max_sequence_length',
        'max_pixels_per_frame','image_min_tokens','image_max_tokens','max_new_tokens','server_binary_sha256',
        'server_parallel','server_log_verbosity')
    value=dict(schema=SCHEMA,status='PASS_ORIGINAL_V11_VALIDATOR_AND_ALL_BOUND_BYTES_CPU',
        original_source_lock_sha256=LOCK_SHA,labels=labels,reviews=reviews,
        authority_files={str(p):sha(p) for p in authority_paths},all_receipt_files=all_files,
        original_gpu_costs=costs,admission_keys=list(admission_keys),serialization_failure_proof=proof,
        selected_denominator=160,selected_by_split={'train':128,'dev':32},
        remaining_review_calls=132,measured_review_wall_sec=max(walls),
        planned_remaining_review_bytes=math.ceil(max(sizes)*132*1.2+20_000_000),
        GPU_started=False,new_model_calls=0,old_success_generation_repeated=False,original_STOP_and_raw_preserved=True,
        semantic_training_admitted=False,new_T_optimizer_updates=0)
    write(MANIFEST,value)
    print(json.dumps({k:value[k] for k in ('status','remaining_review_calls','measured_review_wall_sec','planned_remaining_review_bytes')},ensure_ascii=False),flush=True)

def handoff():
    import autopilot_common as common
    common.verify();value=load_manifest(); files_match(value['all_receipt_files'])
    out=HERE/'teacher_01';out.mkdir(exist_ok=False)
    for name in ('annotation_receipts.jsonl','teacher_completion.json'):
        shutil.copyfile(OLD/'teacher_01'/name,out/name)
        require(sha(out/name)==value['authority_files'][str(OLD/'teacher_01'/name)],'original aggregate bytes changed')
    shutil.copytree(OLD/'teacher_01/validated',out/'validated')
    for p in (OLD/'teacher_01/validated').iterdir():
        if p.is_file():require((out/'validated'/p.name).read_bytes()==p.read_bytes(),'original validation byte copy differs')
    import teacher_label as teacher
    validator=teacher.validator_for(RUN)
    admission=read(HERE/'teacher_admission.json')
    for record in rows(out/'validated/validated_records.jsonl'):
        teacher.verify_model_decision_projection(record)
        prior=approved_review(record,admission)
        if prior is not None:teacher.verify_blind_review_projection(prior,record,validator)
    receipt=dict(status='PASS_EXACT_V11_LABELS_AND_COMPLETED_REVIEWS_HANDOFF',utc=common.utc(),
        resume_manifest_sha256=sha(MANIFEST),first_answer_count=160,completed_review_count=28,remaining_review_calls=132,
        label_records_original_bytes=True,original_GPU_costs_preserved=True,original_gpu_costs=value['original_gpu_costs'],
        measured_review_wall_sec=value['measured_review_wall_sec'],planned_remaining_review_bytes=value['planned_remaining_review_bytes'],
        new_label_calls=0,new_review_calls=0,new_T_optimizer_updates=0,old_reviews_reference_original_directories=True)
    write(HERE/'resume_handoff.json',receipt)
    print(json.dumps(receipt),flush=True)

def record_review_progress(out, record, review, *, reused):
    """New output state only; original review bytes and scientific classes remain intact."""
    import teacher_label as teacher
    out=Path(out);root=out.parent.parent
    completed=sorted((root/'reviews').glob('*/done.json'))
    teacher.save(root/'review_progress.json',dict(status='REAL_MISSING_BLIND_REVIEWS_RUNNING',utc=teacher.utc(),
        selected_denominator=160,original_completed_reviews=28,fresh_model_calls=len(completed),
        total_completed_reviews=28+len(completed),new_label_calls=0,
        last_window_id=record['window_id'],last_review_reused=reused,new_T_optimizer_updates=0))
    if not reused and len(completed)==1:
        teacher.require(record['window_id']==teacher.read(HERE/'config.json')['blocked_first_review_window_id'],
            'first new review must be the original blocked legacy record')
        teacher.save(root/'first_review_generation.json',dict(
            status='PASS_REAL_BLOCKED_LEGACY_BLIND_REVIEW_NOT_TRAINING_OR_TRUTH',utc=teacher.utc(),
            window_id=record['window_id'],fresh_review_model_calls=1,new_label_calls=0,old_success_repeated=False,
            review_done_sha256=sha(out/'done.json'),review_receipt_sha256=sha(out/'review_receipt.json'),
            original_teacher_record_sha256=digest(record),model_raw_sha256=review['model_raw_answer_sha256'],
            resume_manifest_sha256=sha(MANIFEST),new_source_lock_sha256=sha(HERE/'source_lock.json'),
            support_class=review['support_class'],new_T_optimizer_updates=0),fresh=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--handoff',action='store_true');args=parser.parse_args()
    handoff() if args.handoff else prepare_manifest()
