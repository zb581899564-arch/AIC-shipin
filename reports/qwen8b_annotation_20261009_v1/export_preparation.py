"""Export accepted annotations with source split and honest unresolved denominators."""
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction
import json,hashlib
import numpy as np
from spatial_prepare import validate,load,save,sha,ROOT
def lines(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows),encoding='utf-8');tmp.replace(path)
def main():
    sources=load(ROOT/'corpus.json')['sources'];temporal=[];spatial=[];quarantine=[];sft={'train':[],'validation':[]};status=[];time_quarantined=[]
    for m in sources:
        sid=m['source_id'];accepted_paths=list((ROOT/'raw/gemini'/sid).glob('attempt_*/acceptance.json'))
        assert len(accepted_paths)<=1,'Multiple successful temporal versions require an explicit selection'
        acceptance=accepted_paths[0] if accepted_paths else ROOT/'raw/gemini'/sid/'attempt_01'/'acceptance.json'
        if acceptance.exists():
            receipt=load(acceptance);rp=Path(receipt['raw']['path']);assert sha(rp)==receipt['raw']['sha256'];raw=load(rp)
            assert receipt['media_sha256']==m['media_sha256'] and raw['source_id']==sid
            quality_path=ROOT/'temporal_quality'/f'{sid}.json';quality=load(quality_path) if quality_path.exists() else None
            if quality:
                assert quality['source_id']==sid and quality['raw_sha256']==sha(rp)
                if quality['verdict'].startswith('REJECT'):time_quarantined.append(sid)
            pts=np.load(ROOT/'input'/sid/'native_pts.npz')['pts'];tb=Fraction(*m['native_time_base']);start_pts=int(pts[0])
            for k,e in enumerate(raw['events']):
                a=Fraction(str(e['start_seconds']));b=Fraction(str(e['end_seconds_exclusive']))
                # Exact half-open comparisons. Teacher time uncertainty is preserved, not hidden by PTS precision.
                ordinals=[i for i,p in enumerate(pts) if a<=(int(p)-start_pts)*tb<b]
                row=dict(source_id=sid,source_group=m['source_group'],split=m['split'],event_index=k,event=e,
                    media_sha256=m['media_sha256'],native_time_base=m['native_time_base'],
                    first_native_ordinal=ordinals[0] if ordinals else None,last_native_ordinal=ordinals[-1] if ordinals else None,native_frame_count=len(ordinals),
                    raw_path=str(rp),raw_sha256=sha(rp),label_role='POSITIVE_OR_UNKNOWN_EVENT_CANDIDATE',
                    complete_temporal_training_target=False,unobserved_domains_negative=False,
                    full_model_observation_independently_proven=False,
                    temporal_quality_status=quality['verdict'] if quality else 'UNVERIFIED_MODEL_EVENT_CANDIDATE',
                    temporal_quality_receipt=str(quality_path) if quality else None)
                temporal.append(row)
        draft=ROOT/'raw/doubao'/sid/'draft_01.json';review=draft.with_name('review_01.json');final=draft.with_name('final_checks_01.json')
        info=dict(source_id=sid,split=m['split'],gemini=acceptance.exists(),doubao_draft=draft.exists(),doubao_review=review.exists(),accepted_crop_targets=0)
        if review.exists():
            try:
                mm,doc,rs=validate(sid,review)
                render=load(ROOT/'review/doubao'/sid/'render_manifest.json')
                assert render['draft_sha256']==sha(draft)
                declared=set(doc['observed_review_files']);assert all(f'f{i:02d}_review.png' in {Path(p).name for p in declared} for i in range(12))
                final_doc=load(final) if final.exists() else {'checks':[]}
                for row in rs:
                    i=row['sample_index'];ratio=row['ratio'];f=mm['frames'][i]
                    teacher=next(c for r in doc['frames'] if r['sample_index']==i for c in r['crops'] if c['targetRatioWH']==ratio)
                    record=dict(row,source_id=sid,source_group=m['source_group'],split=m['split'],frame_index=f['frame_index'],pts=f['pts'],time_base=f['time_base'],
                        image_path=str(ROOT/'input'/sid/f['file']),png_sha256=f['png_sha256'],media_sha256=mm['media_sha256'],
                        review_path=str(review),review_sha256=sha(review),teacher_quality_reference='SELF_REVIEW_ONLY_NOT_HUMAN_GOLD',review=teacher)
                    ok=teacher.get('critical_subject_preserved') is True and teacher.get('review_verdict') in ('KEEP','REVISED') and row['state']=='CROP'
                    if teacher.get('review_verdict')=='REVISED':
                        tag=f'f{i:02d}_{ratio[0]}x{ratio[1]}_actual.png';actual=ROOT/'review_final/doubao'/sid/tag
                        check=next((c for c in final_doc['checks'] if c.get('sample_index')==i and c.get('targetRatioWH')==ratio),None)
                        ok=ok and check is not None and check.get('verdict')=='PASS' and actual.exists() and check.get('actual_crop_sha256')==sha(actual)
                    record['structurally_eligible_weak_sft']=bool(ok);spatial.append(record)
                    if ok:
                        x,y,w,h=row['box_xywh'];prompt=f'Reframe this video frame to {ratio[0]}:{ratio[1]}. Preserve the main visible subject and its essential action or object. Source image is {f["width"]}x{f["height"]} pixels. Return ONLY JSON {{"box_xyw":[x,y,width]}} in original integer pixels. Height is width*{ratio[1]}/{ratio[0]}; keep the rectangle inside the source image.'
                        sample=dict(id=f'{f["sample_id"]}:{ratio[0]}x{ratio[1]}',source_id=sid,source_group=m['source_group'],
                            images=[record['image_path']],messages=[{'role':'user','content':'<image>\n'+prompt},{'role':'assistant','content':json.dumps({'box_xyw':[x,y,w]},separators=(',',':'))}],
                            label_quality='DOUBAO_SELF_REVIEWED_WEAK_LABEL',label_record_sha256=hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode()).hexdigest())
                        sft[m['split']].append(sample);info['accepted_crop_targets']+=1
                    else:quarantine.append(dict(source_id=sid,sample_id=row['sample_id'],ratio=ratio,reason='UNKNOWN_REJECTED_OR_REVISED_ACTUAL_CROP_NOT_YET_CONFIRMED'))
            except Exception as exc:quarantine.append(dict(source_id=sid,reason='REVIEW_SCHEMA_OR_IDENTITY_REJECTED',error=repr(exc)))
        status.append(info)
    out=ROOT/'exports'
    lines(out/'temporal_event_candidates.jsonl',temporal);lines(out/'spatial_reviewed_labels.jsonl',spatial);lines(out/'quarantine.jsonl',quarantine)
    for split in sft:lines(out/f'crop_sft_{split}.jsonl',sft[split])
    report=dict(utc=datetime.now(timezone.utc).isoformat(),expected_sources=50,expected_spatial_frames=600,expected_ratio_targets=1200,
        gemini_accepted_sources=sum(r['gemini'] for r in status),temporal_candidate_events=len(temporal),
        doubao_drafted_sources=sum(r['doubao_draft'] for r in status),doubao_reviewed_sources=sum(r['doubao_review'] for r in status),
        reviewed_crop_rows=len(spatial),weak_crop_sft_rows={k:len(v) for k,v in sft.items()},quarantined_rows=len(quarantine),
        source_status=status,actual_student_training_started=False,
        target_contract='NEW_EXPLICIT_PIXEL_BOX_TARGET; existing center-only production decoder is not modified or directly compatible',
        complete_temporal_sft_rows=0,temporal_alignment_quarantined_sources=time_quarantined,
        limitations=['Gemini candidates are not complete temporal targets or negative labels.','Teacher-reviewed crop labels are weak reference, not human gold.','Dataset source identity audit does not exclude semantic/reencoded overlap.'])
    save(out/'preparation_status.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_status','limitations')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
