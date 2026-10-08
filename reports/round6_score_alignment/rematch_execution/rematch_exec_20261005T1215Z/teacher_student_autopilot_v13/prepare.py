"""Freeze independent exact review continuation, never modify old run evidence."""
from autopilot_common import *
import socket
import v11_resume as resume

def main():
    require(socket.gethostname()=='inspur-NP5570M5','wrong preparation host')
    require(not any((HERE/n).exists() for n in ('source_lock.json','registration.json','start_receipt.json')),'never reseal')
    accepted=read(HERE/'resume_cpu_acceptance.json'); manifest=resume.load_manifest()
    require(accepted['status']=='PASS_V13_ACTUAL_SORTED_LEGACY_PROJECTION_AND_EXACT_RESUME_CPU'
        and accepted['actual_original_records_checked']==160 and accepted['completed_reviews_replayed']==28
        and accepted['remaining_review_calls']==132 and accepted['rejection_tests']>=13
        and accepted['actual_current_blind_validator_replayed']==28 and accepted['exact_original_dependency_files']==2
        and accepted['GPU_started'] is False and accepted['new_model_calls']==0,'actual resume CPU tests required')
    for name,key in (('teacher_label.py','production_teacher_sha256'),('v10_cache_reuse.py','production_legacy_sha256'),
        ('v11_resume.py','production_resume_sha256')):
        require(sha(HERE/name)==accepted[key],'accepted production code changed')
    previous=resume.OLD/'source_lock.json';files=dict(read(previous)['files'])
    failed=RUN/'teacher_student_autopilot_v12'
    require(read(failed/'completion.json')['status']=='STOP_AUTOPILOT_PRESERVED','V12 STOP must remain')
    for n in ('source_lock.json','completion.json','verified_v11_full_label_and_review_handoff.cpu.log'):
        files[str(failed/n)]=sha(failed/n)
    files[str(previous)]=sha(previous);files.update(manifest['authority_files']);files.update(manifest['all_receipt_files'])
    for directory in ('selection_01','pilot_selection'):
        for p in (HERE/directory).rglob('*'):
            if p.is_file():
                original=resume.OLD/directory/p.relative_to(HERE/directory)
                require(p.read_bytes()==original.read_bytes(),'original selection byte identity changed')
                files[str(p)]=sha(p)
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name!='source_lock.json':files[str(p)]=sha(p)
    for path,expected in files.items():require(sha(path)==expected,'immutable receipt/source changed: '+path)
    write(HERE/'source_lock.json',dict(schema='AIC_TEACHER_STUDENT_SOURCE_LOCK_V13',utc=utc(),files=files,
        predecessor_source_lock_sha256=resume.LOCK_SHA,original_STOP_preserved=True,
        exact_resume_manifest_sha256=sha(resume.MANIFEST),new_label_calls=0,
        complete_original_labels=160,completed_original_reviews=28,missing_blind_reviews=132,
        original_model_input_science_unchanged=True,actual_capacity_only=True,teacher_is_offline_only=True),fresh=True)
    print(json.dumps(dict(status='PASS_V13_EXACT_RESUME_SOURCE_BINDING',files=len(files),
        source_lock_sha256=sha(HERE/'source_lock.json'))),flush=True)

if __name__=='__main__':main()
