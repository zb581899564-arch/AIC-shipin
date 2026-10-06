"""Bounded CPU selection, sequential shots, anchors, compose and independent ZIP check."""
from runtime import *
from a_contract import compose,validate_predictions,keyset,package,write_rows
from pts_contract import select_frames,legacy_manifest,validate_frame_request
import subprocess

def scheduling(scope,out):
    bound,manifest,clocks=inputs(scope);out=Path(out)
    selected=select_frames(manifest,rows(out/'temporal.jsonl'),clocks)
    write_rows(out/'selected.jsonl',selected)
    metadata={r['video_id']:r for r in manifest['records']}
    from detect_shots_pts import descriptors,HIST_THRESHOLD,GRAY_MAD_THRESHOLD
    import cv2
    import numpy as np
    results=[];current=None;reader=None;previous=None
    try:
        for request in sorted(selected,key=lambda r:(r['video_id'],r['source_frame'])):
            item=validate_frame_request(request,metadata)
            if current!=item['video_id']:
                if reader is not None:reader.close()
                require(sha(item['source_path'])==item['source_sha256'],'shot source hash changed')
                current=item['video_id'];reader=OrdinalReader(item,clocks[current])
            frame,pixel=reader.get(request['source_frame'])
            hist,gray=descriptors(frame)
            contiguous=previous is not None and previous['video_id']==current and previous['source_frame']+1==request['source_frame']
            reasons=[];distance=mad=None
            if not contiguous:reasons=['VIDEO_OR_SELECTION_DISCONTINUITY']
            else:
                distance=float(cv2.compareHist(previous['hist'],hist,cv2.HISTCMP_BHATTACHARYYA))
                mad=float(np.mean(cv2.absdiff(previous['gray'],gray))/255)
                if distance>=HIST_THRESHOLD:reasons.append('HSV_HIST_CUT')
                if mad>=GRAY_MAD_THRESHOLD:reasons.append('GRAY_MAD_CUT')
            results.append(dict(video_id=current,source_frame=request['source_frame'],decoded_pixel_sha256=pixel,
                is_shot_start=bool(reasons),boundary_reasons=reasons,hist_bhattacharyya=distance,gray_mad=mad))
            previous=dict(video_id=current,source_frame=request['source_frame'],hist=hist,gray=gray)
    finally:
        if reader is not None:reader.close()
    write_rows(out/'shots.jsonl',results)
    subprocess.run([sys.executable,'-B',str(CODE/'vendor/build_anchors.py'),'--selected',str(out/'selected.jsonl'),
        '--shots',str(out/'shots.jsonl'),'--max-gap','8','--output',str(out/'anchor_requests.jsonl'),
        '--summary',str(out/'anchors.summary.json')],check=True)
    write(out/'schedule.stage.json',dict(status='PASS_EXACT_SCHEDULING',selected_frames=len(selected),
        shot_starts=sum(r['is_shot_start'] for r in results),anchors=len(rows(out/'anchor_requests.jsonl')),
        hist_threshold=HIST_THRESHOLD,gray_mad_threshold=GRAY_MAD_THRESHOLD,max_anchor_gap=8,
        decoder_identity='SEQUENTIAL_FROM_SOURCE_ORDINAL_ZERO',selected_sha256=sha(out/'selected.jsonl'),
        requests_sha256=sha(out/'anchor_requests.jsonl'),scope=scope))

def finish(scope,out):
    bound,manifest,clocks=inputs(scope);out=Path(out);projected=legacy_manifest(manifest)
    selected,shots,requests,outputs=[rows(out/name) for name in ('selected.jsonl','shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl')]
    pred,prov=compose(projected,selected,shots,requests,outputs)
    write_rows(out/'predictions.jsonl',pred);write_rows(out/'provenance.jsonl',prov)
    result=validate_predictions(projected,pred,keyset(selected),prov)
    rebuilt,rebuilt_prov=compose(projected,selected,shots,requests,outputs)
    require(pred==rebuilt and prov==rebuilt_prov,'serialized composition changed')
    write(out/'metadata.json',dict(records=manifest['records'],errors=[]))
    pending=out/'candidate_MAC_8B.PENDING_VALIDATION.zip'
    result.update(package(out/'predictions.jsonl',pending))
    subprocess.run([sys.executable,'-B',str(CODE/'vendor/independent_validate.py'),
        '--strict-loader-root',str(CODE/'vendor/frozen_strict_loader'),'--metadata',str(out/'metadata.json'),
        '--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),
        '--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),
        '--report',str(out/'independent_validation.json')],check=True)
    independent=read(out/'independent_validation.json')
    require(independent['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and all(independent['checks'].values()),'independent strict validation failed')
    candidate=out/'candidate_MAC_8B.zip';pending.rename(candidate)
    result.update(status='PASS_COMPLETE_8B_PACKAGE_NOT_SCORED_NOT_UPLOADED',scope=scope,candidate=str(candidate),
        complete_pipeline_parameters=8782459120,shared_base_counted_once=True,spatial_base='SAME_PINNED_8B_WITHOUT_TEMPORAL_LORA',
        model_identity_from_test_content=False,source_lock_sha256=sha(HERE/'source_lock.json'))
    write(out/'package.stage.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['scheduling','finish']);ap.add_argument('scope',choices=['nontest','rematch']);ap.add_argument('output');args=ap.parse_args()
    globals()[args.stage](args.scope,args.output)
