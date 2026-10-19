"""Synthetic geometry/shot/identity checks only; no proxy quality experiment."""
from copy import deepcopy
from prod_common import HEAD_SHA,NORM_SHA
from native_apply import apply_to_predictions,SOURCE


def main():
    meta={'records':[dict(video_id='0',targetRatioWH=[16,9],width=1920,height=1080,n_frames=12),
                     dict(video_id='1',targetRatioWH=[9,16],width=1080,height=1920,n_frames=2)]}
    frames=[0,2,4,5,8,10]
    rows=[dict(video_id='0',targetRatioWH=[16,9],predictions=[dict(frame=f,bboxes=[499,0,1000] if f==4 else [0,0,1920]) for f in frames]),
          dict(video_id='1',targetRatioWH=[9,16],predictions=[dict(frame=0,bboxes=[0,0,1080])])]
    provenance=[dict(video_id=r['video_id'],source_frame=p['frame'],box_xyw=deepcopy(p['bboxes']),spatial_source='ORIGINAL_ACCEPTED',legal=True) for r in rows for p in r['predictions']]
    field=[dict(video_id='0',source_frame=f,is_shot_start=f in (0,5,10),boundary_reasons=[]) for f in range(12)]
    field+=[dict(video_id='1',source_frame=f,is_shot_start=f==0,boundary_reasons=[]) for f in range(2)]
    anchors=[]
    for f in (0,4,5,9,10,11):
        anchors.append(dict(video_id='0',source_frame=f,status='MODEL_OK',used_fallback=False,spatial_source='QWEN_ANCHOR_SAME_FRAME',
                            center_norm=[.99,.1],raw_output='{"cx":990,"cy":100}',anchor_request_sha256='a'*64,decoded_pixel_sha256='b'*64))
    data={'0':dict(sample_ordinals=[0,4,8],predicted_width=[500,1000,250],
          native_pts_exact=['0','1/10','3/20','4/5','1','11/10','6/5','13/10','7/5','3/2','8/5','17/10'],
          head_sha256=HEAD_SHA,normalization_sha256=NORM_SHA)}
    saved=deepcopy((rows,provenance,data,field,anchors,meta))
    out,proof=apply_to_predictions(rows,provenance,data,field,anchors,meta)
    boxes={(r['video_id'],p['frame']):p['bboxes'] for r in out for p in r['predictions']}
    p={(r['video_id'],r['source_frame']):r for r in proof}
    assert boxes[('0',4)]==[499,0,1000]  # exact accepted499 boundary, no reconstruction.
    assert boxes[('0',0)]==[960,0,960]   # true raw focal center, not full-box center.
    assert p[('0',2)]['width_model']['predicted_width']==575  # true VFR PTS axis.
    assert p[('0',5)]['width_model']['predicted_width']==250  # no borrow across cut.
    assert p[('0',5)]['width_model']['left_sample_ordinal']==8
    assert boxes[('0',10)]==[0,0,1920] and p[('0',10)]['width_head_application']['decision']=='NO_SAME_SHOT_OBSERVATION_KEEP_BASELINE'
    assert boxes[('1',0)]==[0,0,1080] and p[('1',0)]==provenance[-1]
    assert p[('0',0)]['spatial_source']==SOURCE
    assert (rows,provenance,data,field,anchors,meta)==saved
    assert sum(len(r['predictions']) for r in out)==7
    print('PASS_SYNTHETIC_VFR_SHOT_CUT_RAW_CENTER_WIDTH1000_499_BOUNDARY_PORTRAIT_IDENTITY')


if __name__=='__main__':main()
