"""Prepare the already-downloaded TVSum corpus with exact native frame IDs."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
from collections import defaultdict
import av
import hashlib
import json
import numpy as np
import shutil
import zipfile
import sys

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'gemini_distillation_data_20261009'
ARCHIVE=OLD/'data/tvsum/ydata-tvsum50-v1_1/ydata-tvsum50-video.zip'
CATALOG=OLD/'tvsum_catalog.json'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(p)
def main():
    catalog=json.loads(CATALOG.read_text(encoding='utf-8'))['sources']
    groups=defaultdict(list)
    for row in catalog:groups[row['category']].append(row)
    splits={}
    for category,rows in sorted(groups.items()):
        ordered=sorted(rows,key=lambda r:hashlib.sha256(('tvsum-qwen8b-v1:'+r['source_id']).encode()).hexdigest())
        for i,row in enumerate(ordered):splits[row['source_id']]='validation' if i==0 else 'train'
    # This already-observed pilot is a train/pipeline source, never a fresh holdout.
    if splits['GsAD1KT1xo8']=='validation':
        other=next(r['source_id'] for r in groups['PK'] if r['source_id']!='GsAD1KT1xo8' and splits[r['source_id']]=='train')
        splits['GsAD1KT1xo8']='train';splits[other]='validation'
    source_rows=[dict(source_id=r['source_id'],source_group=r['source_group'],category=r['category'],
        split=splits[r['source_id']],previous_pilot_exposed=r['source_id']=='GsAD1KT1xo8') for r in catalog]
    save(ROOT/'split.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),seed='tvsum-qwen8b-v1',
        train_sources=40,validation_sources=10,grouping='Whole original source video; all frames and ratios follow source',
        pilot_not_fresh_validation=True,sources=source_rows))
    # Start with a new parkour train source, then continue the complete corpus.
    ordered=sorted(catalog,key=lambda r:(not(r['category']=='PK' and splits[r['source_id']]=='train' and r['source_id']!='GsAD1KT1xo8'),r['category'],r['source_id']))
    only=sys.argv[1:] and sys.argv[1]=='first'
    completed=[]
    with zipfile.ZipFile(ARCHIVE) as archive:
        members={Path(i.filename).stem:i for i in archive.infolist() if not i.is_dir() and Path(i.filename).suffix.lower()=='.mp4'}
        assert set(members)=={r['source_id'] for r in catalog}
        projected=sum(i.file_size for i in members.values())+len(catalog)*12*640*480*3
        available=shutil.disk_usage(ROOT).free
        if projected>available:raise RuntimeError('Local capacity does not cover media and PNG estimate')
        for source in (ordered[:1] if only else ordered):
            sid=source['source_id']
            dest=ROOT/'input'/sid
            receipt=dest/'manifest.json'
            if receipt.exists():
                existing=json.loads(receipt.read_text(encoding='utf-8'))
                assert existing['source_id']==sid and existing['split']==splits[sid]
                assert sha(dest/f'{sid}.mp4')==existing['media_sha256']
                assert all(sha(dest/r['file'])==r['png_sha256'] for r in existing['frames'])
                completed.append(existing)
                print(json.dumps(dict(status='EXACT_REUSE',source_id=sid)),flush=True)
                continue
            dest.mkdir(parents=True,exist_ok=True)
            video=dest/f'{sid}.mp4'
            member=members[sid]
            if video.exists():
                assert video.stat().st_size==member.file_size
                # Compare to source archive before recovering an interrupted copy.
                expected=hashlib.sha256(archive.read(member)).hexdigest()
                assert sha(video)==expected
            else:
                with archive.open(member) as incoming,video.open('xb') as outgoing:
                    shutil.copyfileobj(incoming,outgoing,1<<20)
            all_pts=[];frames=[];time_base=None;last_duration=None
            with av.open(str(video)) as container:
                stream=container.streams.video[0]
                stream.thread_count=2
                stream_metadata=dict(width=stream.width,height=stream.height,average_rate=str(stream.average_rate),
                    stream_duration_ticks=stream.duration,stream_start_time_ticks=stream.start_time,
                    rotation_metadata=stream.metadata.get('rotate'),sample_aspect_ratio=str(stream.sample_aspect_ratio))
                for ordinal,frame in enumerate(container.decode(stream)):
                    if frame.pts is None:raise ValueError('Missing native PTS')
                    tb=Fraction(frame.time_base)
                    if time_base is None:time_base=tb
                    if tb!=time_base:raise ValueError('Changing native time base')
                    if all_pts and frame.pts<=all_pts[-1]:raise ValueError('Non-increasing native PTS')
                    all_pts.append(frame.pts);last_duration=frame.duration
            # Published human-score vector length is not a native frame-ID
            # authority. Preserve count differences without padding labels.
            native_count=len(all_pts)
            picks=[(native_count-1)*(2*i+1)//24 for i in range(12)]
            by_ordinal={n:i for i,n in enumerate(picks)}
            from PIL import Image
            with av.open(str(video)) as container:
                stream=container.streams.video[0];stream.thread_count=2
                for ordinal,frame in enumerate(container.decode(stream)):
                    if ordinal not in by_ordinal:continue
                    assert frame.pts==all_pts[ordinal] and Fraction(frame.time_base)==time_base
                    pi=by_ordinal[ordinal];file=f'f{pi:02d}.png';path=dest/file
                    rgb=frame.to_ndarray(format='rgb24')
                    rgb_sha=hashlib.sha256(rgb.tobytes()).hexdigest()
                    if path.exists() and hashlib.sha256(Image.open(path).convert('RGB').tobytes()).hexdigest()!=rgb_sha:
                        # Keep the old uncommitted frame untouched; the new
                        # manifest refers to a native-ordinal-named recovery.
                        file=f'f{pi:02d}_native_{ordinal}.png';path=dest/file
                    if path.exists():
                        assert hashlib.sha256(Image.open(path).convert('RGB').tobytes()).hexdigest()==rgb_sha
                    else:Image.fromarray(rgb).save(path)
                    frames.append(dict(sample_index=pi,sample_id=f'{sid}:{ordinal}',frame_index=ordinal,
                        pts=frame.pts,time_base=[time_base.numerator,time_base.denominator],pts_seconds=float(frame.pts*time_base),
                        relative_pts_seconds=float((frame.pts-all_pts[0])*time_base),width=frame.width,height=frame.height,
                        file=file,png_sha256=sha(path),rgb24_sha256=rgb_sha))
                    if len(frames)==12:break
            assert len(frames)==12 and [r['sample_index'] for r in frames]==list(range(12))
            final_step=last_duration or (all_pts[-1]-all_pts[-2])
            end=Fraction(all_pts[-1]+final_step-all_pts[0])*time_base
            np.savez_compressed(dest/'native_pts.npz',pts=np.asarray(all_pts,dtype=np.int64),time_base=np.asarray([time_base.numerator,time_base.denominator],dtype=np.int64))
            info=dict(source_id=sid,source_group=source['source_group'],category=source['category'],split=splits[sid],
                media_file=video.name,media_bytes=video.stat().st_size,media_sha256=sha(video),native_frames=len(all_pts),
                human_vector_length=source['annotation_vector_length'],
                human_vector_native_count_equal=native_count==source['annotation_vector_length'],
                human_ordinal_alignment='COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF' if native_count==source['annotation_vector_length'] else 'UNRESOLVED_COUNT_DIFFERENCE_NOT_PADDED',
                native_time_base=[time_base.numerator,time_base.denominator],first_pts=all_pts[0],last_pts=all_pts[-1],
                source_duration_seconds=float(end),stream_metadata=stream_metadata,native_pts_sha256=sha(dest/'native_pts.npz'),
                sample_policy='12 fixed native decoded ordinals at midpoint of equal-count strata; no teacher or human score selection',
                frames=frames,human_scores_provided_to_teacher=False,previous_pilot_exposed=sid=='GsAD1KT1xo8',
                license_record_ref=str(CATALOG),historical_license_state=source['license_state'],
                competition_overlap_status='PENDING_SOURCE_ID_AND_HASH_AUDIT',
                utc=datetime.now(timezone.utc).isoformat())
            save(receipt,info);completed.append(info)
            print(json.dumps(dict(status='PREPARED',source_id=sid,split=info['split'],native_frames=len(all_pts),duration=float(end))),flush=True)
    ready=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'input').glob('*/manifest.json'))]
    save(ROOT/'corpus.json',dict(utc=datetime.now(timezone.utc).isoformat(),expected_sources=50,prepared_sources=len(ready),
        expected_spatial_frames=600,prepared_spatial_frames=sum(len(s['frames']) for s in ready),sources=ready))
    print(json.dumps(dict(status='FIRST_READY' if only else 'PASS_COMPLETE_CORPUS_PREPARATION',sources=len(ready),first_source=ordered[0]['source_id'])),flush=True)
if __name__=='__main__':main()
