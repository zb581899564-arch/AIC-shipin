"""Time-independent source shot/anchor field, legitimate empty and strict delivery."""
from common import *
import math
from bisect import bisect_left
import subprocess
import time
from package_contract import package, validate_predictions, keyset
from frame_contract import legacy_manifest

class OrdinalReader:
    def __init__(self,item,clock):
        from frame_contract import BRANCH_NATIVE
        self.item=item;self.native=clock['branch']==BRANCH_NATIVE;self.next=0;self.last=None
        if self.native:
            from native_frames import VerifiedNativeReader
            self.reader=VerifiedNativeReader(item['source_path'],item,clock)
        else:
            import cv2
            self.reader=cv2.VideoCapture(item['source_path']);require(self.reader.isOpened(),'source open failed')
    def get(self,index):
        import hashlib
        require(type(index) is int and 0<=index<self.item['n_frames'],'invalid ordinal')
        if self.native:
            frame=self.reader.read(index)
            return frame,hashlib.sha256(frame.tobytes()).hexdigest()
        if index==self.next-1 and self.last is not None:return self.last
        require(index>=self.next,'random/backwards source seek forbidden')
        while self.next<=index:
            ok,frame=self.reader.read();require(ok,'source ended before registered ordinal');self.next+=1
        require(frame.shape==(self.item['height'],self.item['width'],3),'decoded geometry changed')
        self.last=(frame,hashlib.sha256(frame.tobytes()).hexdigest());return self.last
    def close(self):
        if self.native:self.reader=None
        else:self.reader.release()

def field_frames(manifest, clocks):
    result = []
    for item in manifest['records']:
        clock = clocks[item['video_id']]
        points = [float(p) for p in clock['pts']]
        first = bisect_left(points, item['scope_start_sec'])
        stop = bisect_left(points, item['scope_end_sec'])
        for ordinal in range(first, stop):
            result.append(dict(video_id=item['video_id'], source_frame=ordinal,
                source_path=item['source_path'], source_width=item['width'], source_height=item['height'],
                source_n_frames=item['n_frames'], fps=item['fps_num'] / item['fps_den'],
                target_ratio_wh=item['targetRatioWH']))
    return result

def select_frames(manifest, temporal, clocks):
    """B2 uses actual PTS in every branch; nominal FPS never decides a boundary."""
    import frame_contract as frames
    from contracts import validate_segments
    metadata = {r['video_id']: r for r in manifest['records']}
    predictions = {r.get('video_id'): r for r in temporal}
    require(len(metadata) == len(manifest['records']) and len(predictions) == len(temporal) and
            set(predictions) == set(metadata) == set(clocks), 'T temporal/source/clock denominator differs')
    result = []
    for video_id in sorted(metadata):
        item, record, clock = metadata[video_id], predictions[video_id], clocks[video_id]
        fps = item['fps_num'] / item['fps_den']
        require(record.get('n_frames') == item['n_frames'] and record.get('video_path') == item['source_path'] and
                record.get('targetRatioWH') == item['targetRatioWH'] and math.isfinite(record.get('fps', float('nan'))) and
                abs(record['fps'] - fps) <= max(1e-6, fps * 1e-6), 'T source identity mismatch')
        expected = frames.window_schedule(item, manifest['kind'], clock)
        require(len(record.get('windows', [])) == len(expected), 'T natural window count differs')
        points = [float(p) for p in clock['pts']]
        chosen = set()
        for window, (start, end) in zip(record['windows'], expected):
            require(window.get('output_valid') is True and not window.get('parse_errors') and
                    window.get('clock_record_sha256') == clock['clock_record_sha256'] and
                    abs(window.get('start_sec', -1) - start) <= 1e-6 and
                    abs(window.get('end_sec', -1) - end) <= 1e-6, 'T failed or wrong-clock window blocks candidate')
            segments = window.get('parsed_segments')
            validate_segments(segments, end - start)
            require(window.get('status') == ('MODEL_OK' if segments else 'LEGAL_EMPTY'), 'T empty/failure status mismatch')
            from native_segment_contract import native_segment_ranges
            for first, stop in native_segment_ranges(segments, points, start, end-start):
                chosen.update(range(first, stop))
        for ordinal in sorted(chosen):
            result.append(dict(video_id=video_id, source_frame=ordinal, source_path=item['source_path'],
                source_width=item['width'], source_height=item['height'], source_n_frames=item['n_frames'],
                fps=fps, target_ratio_wh=item['targetRatioWH']))
    return result

def scheduling(scope,out):
    verify();_,manifest,clocks=inputs(scope);out=Path(out)
    selected=select_frames(manifest,rows(out/'temporal.jsonl'),clocks)
    write_rows(out/'selected.jsonl',selected)
    # Empty predictions need no model invocation, and never arise from a failed window.
    domain=field_frames(manifest,clocks) if selected else []
    from cache_contract import try_reuse
    if try_reuse(scope,out,manifest,clocks,selected,domain):return
    from field_contract import build_field_requests
    from detect_shots_pts import descriptors,HIST_THRESHOLD,GRAY_MAD_THRESHOLD
    from frame_contract import validate_frame_request
    import cv2
    import numpy as np
    metadata={r['video_id']:r for r in manifest['records']};shots=[];reader=None;current=None;previous=None
    started=time.monotonic()
    try:
        for n,request in enumerate(sorted(domain,key=lambda r:(r['video_id'],r['source_frame'])),1):
            item=validate_frame_request(request,metadata)
            if current!=item['video_id']:
                if reader is not None:reader.close()
                require(sha(item['source_path'])==item['source_sha256'],'field source bytes changed')
                current=item['video_id'];reader=OrdinalReader(item,clocks[current]);previous=None
            frame,pixel=reader.get(request['source_frame']);hist,gray=descriptors(frame)
            contiguous=previous is not None and previous['source_frame']+1==request['source_frame']
            reasons=[];distance=mad=None
            if not contiguous:reasons=['SOURCE_VIDEO_OR_SCOPE_START']
            else:
                distance=float(cv2.compareHist(previous['hist'],hist,cv2.HISTCMP_BHATTACHARYYA))
                mad=float(np.mean(cv2.absdiff(previous['gray'],gray))/255)
                if distance>=HIST_THRESHOLD:reasons.append('HSV_HIST_CUT')
                if mad>=GRAY_MAD_THRESHOLD:reasons.append('GRAY_MAD_CUT')
            shots.append(dict(video_id=current,source_frame=request['source_frame'],decoded_pixel_sha256=pixel,
                              is_shot_start=bool(reasons),boundary_reasons=reasons))
            previous=dict(source_frame=request['source_frame'],hist=hist,gray=gray)
            if n%3000==0:progress(out,dict(stage='SOURCE_FIELD_SHOTS',frames=n,total=len(domain),
                temporal_selection_used_for_boundaries=False,wall_seconds=time.monotonic()-started))
    finally:
        if reader is not None:reader.close()
    requests=build_field_requests(domain,shots,8)
    write_rows(out/'field_frames.jsonl',domain);write_rows(out/'field_shots.jsonl',shots)
    write_rows(out/'anchor_requests.jsonl',requests)
    write(out/'schedule.stage.json',dict(status='PASS_TIME_INDEPENDENT_SOURCE_FIELD',selected_frames=len(selected),
        field_frames=len(domain),anchors=len(requests),temporal_selection_used_for_boundaries=False,
        max_gap=8,whole_batch_empty=not selected,empty_spatial_calls=0 if not selected else None,
        field_frames_sha256=sha(out/'field_frames.jsonl'),shots_sha256=sha(out/'field_shots.jsonl'),
        requests_sha256=sha(out/'anchor_requests.jsonl'),wall_seconds=time.monotonic()-started))

def spatial(scope,out):
    config=verify();_,manifest,clocks=inputs(scope);out=Path(out)
    require(read(out/'schedule.stage.json')['status']=='PASS_TIME_INDEPENDENT_SOURCE_FIELD','field schedule missing')
    requests=rows(out/'anchor_requests.jsonl')
    if not requests:
        write_rows(out/'anchor_output.jsonl',[])
        write(out/'spatial.stage.json',dict(status='PASS_EMPTY_SPACE_NO_MODEL_CALL',rows=0,invalid=0,
            model_calls=0,wall_seconds=0,measured_seconds_per_anchor=None,logical_parameters=8767123696))
        return
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from frame_contract import validate_frame_request
    from contracts import parse_focus_norm
    from PIL import Image
    import cv2
    baseline=load(HERE/'spatial_baseline.py','next_strict_spatial_baseline')
    model=baseline.Qwen3VL(config['model_dir'],device_map={'':'cuda:0'})
    require(sum(p.numel() for p in model.model.parameters())==8767123696,'space model parameter count changed')
    for parameter in model.model.parameters():parameter.requires_grad_(False)
    from engine import frozen_identity
    base_hash=frozen_identity(model.model,config)
    metadata={r['video_id']:r for r in manifest['records']};current=None;reader=None;failed=0;seconds=[];started=time.monotonic()
    with (out/'anchor_output.jsonl').open('x',encoding='utf-8') as stream:
        try:
            for n,request in enumerate(requests,1):
                one=time.monotonic();item=validate_frame_request(request,metadata)
                rec=dict(video_id=request['video_id'],source_frame=request['source_frame'],status='INFERENCE_FAILURE',
                    used_fallback=False,spatial_source='QWEN_ANCHOR_SAME_FRAME',
                    anchor_request_sha256=request['anchor_request_sha256'])
                try:
                    if current!=item['video_id']:
                        if reader is not None:reader.close()
                        require(sha(item['source_path'])==item['source_sha256'],'spatial source bytes changed')
                        current=item['video_id'];reader=OrdinalReader(item,clocks[current])
                    frame,pixel=reader.get(request['source_frame']);rec['decoded_pixel_sha256']=pixel
                    require(pixel==request['expected_pixel_sha256'],'same-frame pixel identity mismatch')
                    image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));tw,th=request['target_ratio_wh']
                    raw=model.predict_focus(image,(tw,th),max_new_tokens=baseline.DEFAULT_CROP_TOKENS)
                    rec['raw_output']=raw;center=parse_focus_norm(raw,image.width,image.height)
                    require(center is not None,'strict integer JSON center failed; no unit guessing')
                    cw,ch=baseline.compute_crop_size(image.width,image.height,tw,th)
                    box=baseline.center_to_box(*center,image.width,image.height,cw,ch)
                    require(baseline.validate_box(box,image.width,image.height,tw,th),'illegal crop')
                    rec.update(status='MODEL_OK',box_xyw=[int(x) for x in box],center_norm=center)
                except Exception as exc:rec['error']=type(exc).__name__+': '+str(exc)
                rec['seconds']=time.monotonic()-one;seconds.append(rec['seconds']);failed+=rec['status']!='MODEL_OK'
                stream.write(json.dumps(rec,ensure_ascii=False)+'\n');stream.flush()
                if n%50==0 or n==len(requests):progress(out,dict(stage='SOURCE_FIELD_SPATIAL',anchors=n,
                    total=len(requests),failures=failed,wall_seconds=time.monotonic()-started))
        finally:
            if reader is not None:reader.close()
    write(out/'spatial.stage.json',dict(status='PASS_STRICT_SOURCE_FIELD_SPATIAL' if not failed else 'STOP_SPACE_FAILURE',
        rows=len(requests),invalid=failed,model_calls=len(requests),wall_seconds=time.monotonic()-started,
        measured_seconds_per_anchor=sum(seconds)/len(seconds),logical_parameters=8767123696,
        base_hash=base_hash,strict_units='INTEGER_0_TO_1000',time_adapter_enabled=False,failure_to_empty_conversions=0))
    require(failed==0,'space failures block candidate')

def finish(scope,out):
    config=verify();_,manifest,clocks=inputs(scope);out=Path(out)
    from field_contract import compose_from_field
    require(read(out/'temporal.stage.json')['status']=='PASS_TEMPORAL_EXECUTION' and read(out/'temporal.stage.json')['adapter_enabled'] is True,'actual trained B time stage required')
    require(read(out/'spatial.stage.json')['status'] in ('PASS_STRICT_SOURCE_FIELD_SPATIAL','PASS_EMPTY_SPACE_NO_MODEL_CALL'),'complete field spatial inference required')
    for item in manifest['records']:require(sha(item['source_path'])==item['source_sha256'],'final source changed')
    selected=rows(out/'selected.jsonl');shots=rows(out/'field_shots.jsonl')
    requests=rows(out/'anchor_requests.jsonl');outputs=rows(out/'anchor_output.jsonl')
    projected=legacy_manifest(manifest)
    pred,provenance=compose_from_field(projected,selected,shots,requests,outputs)
    write_rows(out/'predictions.jsonl',pred);write_rows(out/'provenance.jsonl',provenance)
    result=validate_predictions(projected,pred,keyset(selected),provenance)
    write(out/'metadata.json',dict(records=manifest['records'],errors=[]))
    pending=out/'candidate_B2_8B.PENDING.zip';result.update(package(out/'predictions.jsonl',pending))
    subprocess.run([sys.executable,'-B',str(BASELINE/'vendor/independent_validate.py'),
        '--strict-loader-root',str(BASELINE/'vendor/frozen_strict_loader'),'--metadata',str(out/'metadata.json'),
        '--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),
        '--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    independent=read(out/'independent_validation.json')
    require(independent['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and all(independent['checks'].values()),'strict candidate check failed')
    candidate=out/'candidate_B2_8B.zip';pending.rename(candidate)
    result.update(status='PASS_COMPLETE_B2_8B_PACKAGE_ON_LINUX',candidate=str(candidate),scope=scope,
        complete_pipeline_parameters=8782459120,shared_base_counted_once=True,official_score=None,
        old_B_package_unchanged=True,time_independent_source_field=True,strict_coordinate_units=True,
        comparison_to_B='PRESERVED_TRAINED_B_NATIVE_INPUT_AND_SOURCE_FIELD_RECIPE',selected_adapter_sha256=config['b_adapter_sha256'],new_optimizer_updates=0,new_T_training_started=False,automatic_return=False,uploaded=False,source_lock_sha256=sha(HERE/'source_lock.json'))
    write(out/'package.stage.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['scheduling','spatial','finish']);p.add_argument('scope');p.add_argument('out')
    a=p.parse_args();globals()[a.stage](a.scope,a.out)
