"""Small independent geometry/evidence check; no scores, data or model calls."""
from copy import deepcopy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from improvement.sprint45_spatial_width_production_v1.native_apply import apply_to_predictions
from validate_width import verify_arrays
from pack_common import HEAD,NORM


def main():
    meta={'records':[dict(video_id='0',targetRatioWH=[16,9],width=1920,height=1080,n_frames=2),dict(video_id='1',targetRatioWH=[9,16],width=1080,height=1920,n_frames=1)]}
    old=[dict(video_id='0',targetRatioWH=[16,9],predictions=[dict(frame=0,bboxes=[0,0,1920]),dict(frame=1,bboxes=[499,0,1000])]),dict(video_id='1',targetRatioWH=[9,16],predictions=[dict(frame=0,bboxes=[0,0,1080])])]
    provenance=[dict(video_id=r['video_id'],source_frame=p['frame'],box_xyw=deepcopy(p['bboxes']),spatial_source='QWEN_ANCHOR_SAME_FRAME',legal=True) for r in old for p in r['predictions']]
    shots=[dict(video_id='0',source_frame=0,is_shot_start=True),dict(video_id='0',source_frame=1,is_shot_start=False),dict(video_id='1',source_frame=0,is_shot_start=True)]
    anchors=[dict(video_id='0',source_frame=f,status='MODEL_OK',used_fallback=False,spatial_source='QWEN_ANCHOR_SAME_FRAME',raw_output='{"cx":990,"cy":100}',center_norm=[.99,.1],anchor_request_sha256='a'*64,decoded_pixel_sha256='b'*64) for f in (0,1)]
    widths={'0':dict(sample_ordinals=[0,1],predicted_width=[500,1000],native_pts_exact=['0','1/10'],head_sha256=HEAD,normalization_sha256=NORM)}
    new,proof=apply_to_predictions(old,provenance,widths,shots,anchors,meta)
    checks,count=verify_arrays(meta,old,provenance,new,proof,widths,shots,anchors,old,'C')
    assert all(checks.values()) and count==1 and new[0]['predictions'][1]['bboxes']==[499,0,1000]
    wrong=deepcopy(proof);wrong[0]['raw_center_norm']=[.5,.5]
    try:verify_arrays(meta,old,provenance,new,wrong,widths,shots,anchors,old,'C')
    except ValueError:pass
    else:raise AssertionError('Independent checker accepted wrong raw focal center')
    print('PASS_SYNTHETIC_INDEPENDENT_GEOMETRY_RAW_CENTER_WIDTH1000_499_PORTRAIT_AND_REJECTION')


if __name__=='__main__':main()
