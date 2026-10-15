"""Finish exports after the already running annotation batch reaches a terminal state.
No model invocation, training, downloads, process termination, or remote operations.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,time
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def main():
    waiting='--wait' in sys.argv;last=None
    while True:
        p=read(ROOT/'gemini_progress.json');brief={k:p.get(k) for k in ('stage','completed','expected','active_source','active_attempt')}
        if brief!=last:print(json.dumps(brief,ensure_ascii=False),flush=True);last=brief
        if p['stage'] in ('COMPLETE','COMPLETE_WITH_UNRESOLVED'):break
        if not waiting:raise SystemExit('Native annotation batch is still running; no completion receipt written.')
        time.sleep(10)
    crop=read(ROOT/'exports/codex_crop_v1/independent_audit.json')
    assert crop['status']=='PASS_INDEPENDENT_FULL_CORPUS_ARTIFACT_AUDIT' and crop['frames']==600
    assert sha(ROOT/'exports/codex_crop_v1/acceptance.json')==crop['acceptance_sha256']
    for name,a in crop['artifacts'].items():assert sha(ROOT/'exports/codex_crop_v1'/name)==a['sha256']
    for script in ('export_preparation.py','audit_temporal_delivery.py'):
        cp=subprocess.run([sys.executable,'-B',str(ROOT/script)],cwd=ROOT,text=True,capture_output=True,check=False)
        (ROOT/'exports'/f'{script}.final.log').write_text(cp.stdout+'\n'+cp.stderr,encoding='utf-8')
        assert cp.returncode==0,script+' failed; original logs preserved'
    temporal=read(ROOT/'exports/temporal_independent_audit.json');prep=read(ROOT/'exports/preparation_status.json')
    assert temporal['completed_sources']==p['completed']==prep['gemini_accepted_sources']
    assert temporal['complete_temporal_sft_rows']==prep['complete_temporal_sft_rows']==0
    files=['DATASET_README.md','split.json','corpus_acceptance.json',
        'exports/codex_crop_v1/labels.jsonl','exports/codex_crop_v1/crop_sft_train.jsonl','exports/codex_crop_v1/crop_sft_validation.jsonl',
        'exports/codex_crop_v1/crop_sft_train_nonidentity.jsonl','exports/codex_crop_v1/crop_sft_validation_nonidentity.jsonl',
        'exports/codex_crop_v1/acceptance.json','exports/codex_crop_v1/independent_audit.json',
        'exports/temporal_event_candidates.jsonl','exports/temporal_independent_audit.json','exports/preparation_status.json']
    result=dict(status='COMPLETE_SPATIAL_PREPARATION_AND_NATIVE_TEMPORAL_CANDIDATE_BATCH' if p['completed']==50 else 'SPATIAL_COMPLETE_TEMPORAL_BATCH_HAS_UNRESOLVED_SOURCES',
        utc=datetime.now(timezone.utc).isoformat(),crop_sources=50,crop_sampled_frames=600,crop_ratio_records=1200,
        crop_verdict_counts=crop['verdict_counts'],crop_sft=crop['sft'],
        temporal_native_accepted_sources=p['completed'],temporal_expected_sources=50,temporal_candidate_events=prep['temporal_candidate_events'],
        temporal_alignment_quarantined_sources=prep['temporal_alignment_quarantined_sources'],
        temporal_complete_sft_rows=0,temporal_pending_sources=temporal['pending_sources'],
        input_observation_and_file_identity_verified=True,temporal_quality_independently_proven=False,
        spatial_quality='MODEL_ANNOTATION_AND_SELF_REVIEW_NOT_HUMAN_GOLD',
        student_training_started=False,gpu_started=False,remote_file_transfer=False,new_model_calls_in_finalizer=0,
        artifacts={name:dict(path=str(ROOT/name),bytes=(ROOT/name).stat().st_size,sha256=sha(ROOT/name)) for name in files},
        protocol='Spatial SFT is the new explicit integer-pixel box task. Temporal outputs are candidates; unseen domains are not negatives.',
        raw_outputs_and_failed_attempts_preserved=True)
    dest=ROOT/'preparation_completion.json';assert not dest.exists(),'Do not overwrite completed delivery receipt'
    save(dest,result);print(json.dumps({k:v for k,v in result.items() if k!='artifacts'},ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
