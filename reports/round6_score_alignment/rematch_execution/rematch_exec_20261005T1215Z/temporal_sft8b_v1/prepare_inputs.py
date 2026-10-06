"""CPU-only fixed-train identity and positive-window preparation; no ML load."""
import hashlib,json,math,subprocess,time
from fractions import Fraction
from pathlib import Path

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
HERE=RUN/'temporal_sft8b_v1'
R7=ROOT/'round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z'
TRAIN=R7/'inputs/train_temporal.jsonl'
SMOKE=R7/'inputs/smoke_temporal.jsonl'
FFPROBE='/home/inspur/anaconda3/envs/Andy/bin/ffprobe'

def require(ok,message):
    if not ok:raise RuntimeError(message)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def write(path,value):
    with path.open('x') as f:f.write(json.dumps(value,indent=2)+'\n')
def rows(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def current(done,total):
    p=HERE/'input_preparation_latest.json';tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(stage='PREPARING_TRAIN_SOURCE_IDENTITIES_CPU_ONLY',done=done,total=total,models_run=False))+'\n')
    tmp.replace(p)

if __name__=='__main__':
    output=HERE/'inputs_01';output.mkdir(exist_ok=False)
    require(sha(TRAIN)=='ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf','frozen704 changed')
    require(sha(SMOKE)=='faca879e7c177a6f9fd5fc9193cfa6e016922f98850a62bef442831fb4716940','fixed smoke changed')
    parents=rows(TRAIN);smoke=rows(SMOKE)
    require(len(parents)==704 and len({r['youtube_id'] for r in parents})==602,'frozen training denominator changed')
    wanted={r['sample_id'] for r in smoke}
    require(len(wanted)==16 and wanted<={r['sample_id'] for r in parents},'fixed smoke is outside train')
    registered,manifest,identities=[],[],{}
    ignored_unknown,quantized_changes=0,0
    original_positive_seconds=represented_positive_seconds=0.0
    started=time.monotonic()
    for i,row in enumerate(parents):
        require(row['split']=='train' and row['label_status']=='WEAK_TEACHER' and row['pts_audit_status']=='PASS','unapproved parent')
        path=Path(row['source_path']).resolve(strict=True)
        require(Path('/home/inspur/aic_video_data/videos') in path.parents and not path.is_symlink(),'source path outside training root')
        stat=path.stat()
        if str(path) not in identities:
            probe=json.loads(subprocess.check_output([FFPROBE,'-v','error','-select_streams','v:0',
                '-show_entries','stream=width,height,avg_frame_rate,r_frame_rate,nb_frames','-of','json',str(path)],text=True))['streams']
            require(len(probe)==1,'source video stream absent')
            md=probe[0];fps=Fraction(md['avg_frame_rate'])
            require(fps>0 and abs(float(fps)-row['source_avg_fps'])<=1e-6,'current source FPS disagrees with historical audit')
            frames=int(row['decoded_source_frames'])
            require(frames>0 and (md.get('nb_frames') in (None,'N/A') or int(md['nb_frames'])==frames),'current source frame count differs')
            identities[str(path)]=dict(source_sha256=sha(path),n_frames=frames,fps_num=fps.numerator,fps_den=fps.denominator,
                width=int(md['width']),height=int(md['height']),source_bytes=stat.st_size,source_mtime_ns=stat.st_mtime_ns)
        identity=identities[str(path)]
        require(path.stat().st_size==stat.st_size and path.stat().st_mtime_ns==stat.st_mtime_ns,'source changed during hashing')
        start,end=float(row['clip_start_sec']),float(row['clip_end_sec'])
        duration=end-start
        require(0<=start<end and end<=identity['n_frames']/(identity['fps_num']/identity['fps_den'])+1e-3,'clip scope outside actual source')
        expected_seconds=sum(b-a for a,b in row['segments_clip_local'])
        raw_window_seconds=0.0
        original_positive_seconds+=expected_seconds
        parent=dict(parent_sample_id=row['sample_id'],video_id=row['video_id'],youtube_id=row['youtube_id'],
            source_group=row['source_group'],source_path=str(path),clip_start_sec=start,clip_end_sec=end,
            split='train',label_status='WEAK_TEACHER',pts_audit_status='PASS',registered_windows=[],**identity)
        for j in range(math.ceil(duration/30)):
            local_start,local_end=j*30.,min((j+1)*30.,duration)
            intersections=[[max(a,local_start)-local_start,min(b,local_end)-local_start]
                for a,b in row['segments_clip_local'] if max(a,local_start)<min(b,local_end)]
            if not intersections:
                ignored_unknown+=1
                continue
            raw_window_seconds+=sum(b-a for a,b in intersections)
            represented=[]
            for a,b in intersections:
                q_a=round(a,4);q_b=min(round(b,4),math.floor((local_end-local_start)*10000)/10000)
                require(0<=q_a<q_b<=local_end-local_start,'interval cannot be represented at fixed decimal precision')
                quantized_changes+=int(q_a!=a or q_b!=b)
                require(abs(q_a-a)<=0.000100001 and abs(q_b-b)<=0.000100001,'quantization exceeds registered precision')
                represented.append([q_a,q_b])
                represented_positive_seconds+=q_b-q_a
            require(1<=len(represented)<=5 and all(represented[k][0]>=represented[k-1][1] for k in range(1,len(represented))),
                'positive-window target violates segment contract')
            window=dict(parent_sample_id=row['sample_id'],window_id=row['sample_id']+'__w'+str(j),
                clip_start_sec=start+local_start,clip_end_sec=start+local_end,segments_clip_local=represented)
            parent['registered_windows'].append(window)
            prepared=dict(sample_id=row['sample_id'],video_id=row['video_id'],youtube_id=row['youtube_id'],
                source_group=row['source_group'],source_path=str(path),split='train',label_status='WEAK_TEACHER',
                pts_audit_status='PASS',**window,**identity)
            manifest.append(prepared)
        require(parent['registered_windows'],'positive parent lost all registered windows')
        require(abs(raw_window_seconds-expected_seconds)<=1e-8,'geometric cutting lost positive duration')
        registered.append(parent)
        current(i+1,len(parents))
        if (i+1)%64==0:print(json.dumps(dict(source_identity_prepared=i+1,total=704)),flush=True)
    registry=output/'r7_train_registry.json'
    write(registry,dict(schema='aic_sft8b_r7_train_registry_v1',expected_parent_count=704,
        origin_train_manifest_sha256=sha(TRAIN),records=registered))
    for name,selected in [('smoke_train.jsonl',[r for r in manifest if r['parent_sample_id'] in wanted]),('full_train.jsonl',manifest)]:
        with (output/name).open('x') as f:
            for row in selected:f.write(json.dumps(row,sort_keys=True)+'\n')
    # The per-endpoint precision change is explicitly recorded; original labels
    # and the original train file stay read-only. No new negative target exists.
    report=dict(status='PASS_TRAIN_ONLY_SFT_INPUT_PREPARATION_NOT_TRAINING',parents=704,source_groups=602,
        source_paths=len(identities),registered_positive_windows=len(manifest),smoke_source_groups=16,
        smoke_windows=sum(r['parent_sample_id'] in wanted for r in manifest),
        geometric_unknown_windows_not_used=ignored_unknown,targets_quantized_at_four_decimals=quantized_changes,
        per_endpoint_precision_change_max_sec=0.000100001,unselected_to_negative_conversions=0,
        original_positive_seconds=original_positive_seconds,represented_positive_seconds=represented_positive_seconds,
        geometric_positive_duration_conserved=True,
        complete_negative_semantics_claim=False,teacher_observation_claim=False,
        old_pts_audit_reused_metadata_checked_only=True,all908_pts_reaudited=False,
        original_source_byte_hashes_available_in_old_pts_record=False,current_source_bytes_newly_bound=True,
        confirm_labels_read=False,dev_labels_used_for_training=False,models_run=False,GPU_used=False,
        wall_seconds=time.monotonic()-started,files={p.name:sha(p) for p in (registry,output/'smoke_train.jsonl',output/'full_train.jsonl')})
    write(output/'preparation_report.json',report)
    print(json.dumps(report),flush=True)
