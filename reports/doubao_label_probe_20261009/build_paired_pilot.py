"""Merge existing teacher outputs as eight traceable pilot candidates."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root=Path(__file__).resolve().parent
meta_path=root/'input/keyframes_v1/manifest.json'
crop_path=root/'raw/image_v3/crop_keyframes.json'
gemini_frame_path=root.parent/'gemini_distillation_data_20261009/annotation_pilot_01/gemini_labels.jsonl'
comparison=json.loads((root/'highlight_comparison.json').read_text(encoding='utf-8'))
meta=json.loads(meta_path.read_text(encoding='utf-8'))
crops=json.loads(crop_path.read_text(encoding='utf-8'))
gemini_frames={row['local_index']:row for row in (json.loads(line) for line in gemini_frame_path.read_text(encoding='utf-8').splitlines())}
spatial={row['probe_index']:row for row in crops['frames']}
gemini_intervals=comparison['models']['Gemini_native_MP4']['intervals']
doubao_intervals=comparison['models']['Doubao_1FPS_images']['intervals']
review_notes=[
    'Non-action crowd frame. Review reduces blue-back obstruction but still emphasizes gear/bystanders.',
    'Non-action crowd frame. Right-side faces and backpack retained; foreground still obstructs.',
    'Review restores main woman; lower foreground obstruction remains and other people are dropped.',
    'Review restores main woman and much of the adjacent man; other people are dropped.',
    'Review restores gesturing woman; foreground head and adjacent man are partly cut.',
    'Review restores most athlete, but source-visible left body remains clipped; needs further correction. Source itself truncates the feet.',
    'Review restores most athlete and stair context; extremities remain near edges, right onlookers dropped.',
    'Review restores head and torso at rail; lower leg/foot is dropped as an explicit vertical-ratio tradeoff.'
]
rows=[]
for item in meta['frames']:
    index=item['probe_index']
    image_path=root/'input/keyframes_v1'/item['file']
    assert hashlib.sha256(image_path.read_bytes()).hexdigest()==item['png_sha256']
    row=spatial[index]
    assert row['frame_index']==item['frame_index'] and abs(row['pts_seconds']-item['pts_seconds'])<1e-9
    hits=[pair for pair in gemini_intervals if pair[0]<=item['pts_seconds']<pair[1]]
    temporal={'annotator':'ANTIGRAVITY_GEMINI_3_8_FLASH_HIGH_UI','label_kind':'WEAK_TEACHER_CANDIDATE','interval_hits':hits}
    if 'gemini_comparison_local_index' in item:
        old=gemini_frames[item['gemini_comparison_local_index']]
        assert old['frame_index']==item['frame_index']
        temporal.update(state=old['highlight_state'],reason=old['highlight_reason'],observation='Explicit original-image frame label')
    else:
        temporal.update(state='KEEP_INTERVAL_CANDIDATE' if hits else 'UNANNOTATED',observation='Membership in coarse native-video teacher interval; no new per-frame call')
    rows.append({'source_id':meta['source_id'],'media_sha256':meta['media_sha256'],
        'frame_index':item['frame_index'],'pts':item['pts'],'time_base':item['time_base'],
        'pts_seconds':item['pts_seconds'],'image':str(image_path),'image_sha256':item['png_sha256'],
        'dataset_role':'ANNOTATION_PIPELINE_PILOT','temporal':temporal,
        'doubao_coarse_interval_hits':[pair for pair in doubao_intervals if pair[0]<=item['pts_seconds']<pair[1]],
        'spatial':{'annotator':'DOUBAO_2_1_PRO_UI','raw_version':'image_v3','crops':row['crops']},
        'visual_review':{'kind':'QUALITATIVE_CODEX_REVIEW_NOT_HUMAN_GROUND_TRUTH','note':review_notes[index],
                         'status':'NEEDS_CORRECTION' if index==5 else 'REVIEWED_WITH_LIMITATIONS'},
        'ready_for_direct_training':False})
out=root/'paired_pilot_labels.jsonl'
out.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
proof={'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_EIGHT_PILOT_CANDIDATES_MERGED_WITHOUT_CHANGING_TEACHER_COORDINATES',
    'rows':len(rows),'training_started':False,'teacher_boxes_modified_by_merge':False,
    'unobserved_frames_auto_negative':False,'source_videos':1,
    'output':{'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},
    'inputs':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [meta_path,crop_path,gemini_frame_path,root/'highlight_comparison.json']]}
(root/'paired_pilot_receipt.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,ensure_ascii=False))
