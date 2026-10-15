"""Read-only source history audit; no media inference or contest pixels."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
OLD=ROOT/'reports/qwen8b_annotation_20261009_v1'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()
receipt_path=OLD/'corpus_acceptance.json'
receipt=json.loads(receipt_path.read_text(encoding='utf-8-sig'))
issues={r['source_id'] for r in receipt['human_frame_alignment_issues']}
rows=[]
for p in sorted((OLD/'input').glob('*/manifest.json')):
    m=json.loads(p.read_text(encoding='utf-8-sig')); sid=m['source_id']
    media=p.parent/m['media_file']; actual=sha(media)
    if actual!=m['media_sha256']: raise ValueError('source bytes changed: '+sid)
    rows.append(dict(source_id=sid,source_group=m['source_group'],category=m['category'],
        prior_split=m['split'],media_sha256=actual,media_bytes=media.stat().st_size,
        media_path=str(media),native_frames=m['native_frames'],duration=m['source_duration_seconds'],
        human_ordinal_alignment=m.get('human_ordinal_alignment','NOT_RECORDED'),
        excluded_human_vector_alignment=sid in issues,
        exposure='PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND',
        current_B_native_training_exposure='NOT_PROVEN_FROM_THIS_MANIFEST',
        license_history=m.get('historical_license_state','UNKNOWN')))
evidence=[]
for e in receipt['evidence']:
    p=Path(e['path']); actual=sha(p)
    if actual!=e['sha256']: raise ValueError('old overlap evidence changed: '+str(p))
    evidence.append(dict(path=str(p),actual_sha256=actual,comparison=e['comparison']))
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_EXISTING_MEDIA_BYTES_AND_HISTORICAL_AUDIT_BINDING',
    sources=len(rows),human_alignment_eligible=sum(not r['excluded_human_vector_alignment'] for r in rows),
    all_sources_previously_exposed=True,source_rows=rows,
    original_overlap_receipt=dict(path=str(receipt_path),sha256=sha(receipt_path),
        status=receipt['source_overlap_status'],overlap=receipt['overlap']),
    unchanged_overlap_evidence=evidence,semantic_reencoded_duplicate_exclusion_proven=False,
    limitations='Existing exact hashes and available IDs only; no new semantic deduplication, test pixels, or blind evaluation claim. Historical license discrepancy retained, not adjudicated by this audit.')
with (OUT/'source_exposure_audit.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('source_rows','unchanged_overlap_evidence')},ensure_ascii=False))
