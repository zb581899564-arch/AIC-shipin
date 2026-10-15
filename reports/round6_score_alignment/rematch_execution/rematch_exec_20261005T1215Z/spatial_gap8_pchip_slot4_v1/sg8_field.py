"""New full-source field; frozen time and original observations remain authorities."""
import hashlib
import sys

from sg8_common import old_helpers, require, digest
from sg8_math import interpolate


def supports_identity(q, vid, requests, outputs):
    return dict(support_request_sha256=[requests[vid,f]['anchor_request_sha256'] for f in q],
        support_output_sha256=[digest(outputs[vid,f]) for f in q],
        support_raw_sha256=[hashlib.sha256(outputs[vid,f]['raw_output'].encode()).hexdigest() for f in q])


def compose(manifest, selected, field_frames, shots, requests, outputs):
    _, p2j, _ = old_helpers()
    fc=sys.modules['field_contract'];pc=sys.modules['package_contract']
    metadata=pc.validate_manifest(manifest)
    require(fc.build_field_requests(field_frames,shots,8)==requests,'full original shot/request plan changed')
    field_keys=pc.keyset(field_frames);selected_keys=pc.keyset(selected)
    require(selected_keys<=field_keys,'selected frames outside complete source field')
    require(pc.keyset(requests)==pc.keyset(outputs),'original observation count/identity mismatch')
    req={(r['video_id'],r['source_frame']):r for r in requests}
    out={(r['video_id'],r['source_frame']):r for r in outputs}
    for key,r in req.items():
        o=out[key];m=metadata[key[0]]
        require(o['status']=='MODEL_OK' and o['used_fallback'] is False and
            o['spatial_source']=='QWEN_ANCHOR_SAME_FRAME' and o['anchor_request_sha256']==r['anchor_request_sha256'] and
            o['decoded_pixel_sha256']==r['expected_pixel_sha256'],'original support is not exact successful same-frame observation')
    predictions={vid:[] for vid in metadata};provenance=[]
    for shot_id,shot in enumerate(p2j.group_shots(shots)):
        vid=shot[0]['video_id'];m=metadata[vid]
        q=p2j.anchor_frames([r['source_frame'] for r in shot],8)
        boxes={f:out[vid,f]['box_xyw'] for f in q}
        for row in shot:
            frame=row['source_frame']
            box,source=interpolate(frame,boxes,m['width'],m['height'],m['targetRatioWH'],p2j.interpolate_box)
            if source['spatial_source']=='SHOT_PCHIP_XY_ORDINAL_GAP8':
                source.update(supports_identity(source['support_ordinals'],vid,req,out))
            predictions[vid].append(dict(frame=frame,bboxes=box))
            provenance.append(dict(video_id=vid,source_frame=frame,shot_id=shot_id,box_xyw=box,legal=True,**source))
    full=[dict(video_id=vid,targetRatioWH=m['targetRatioWH'],predictions=predictions[vid]) for vid,m in sorted(metadata.items())]
    chosen=[dict(row,predictions=[p for p in row['predictions'] if (row['video_id'],p['frame']) in selected_keys]) for row in full]
    chosen_provenance=[r for r in provenance if (r['video_id'],r['source_frame']) in selected_keys]
    return full,provenance,chosen,chosen_provenance
