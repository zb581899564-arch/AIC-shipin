"""Independent field reconstruction and unchanged frozen strict-loader checks.

Does not import sg8_math or sg8_field. New-source validity means rebuilding every
box, eligibility, four-support identity and raw binding, not string allowance.
"""
from bisect import bisect_left
import hashlib
from pathlib import Path
import sys
import zipfile

from sg8_common import BASE, OLD, old_helpers, require, digest, sha
from sg8_independent_math import rebuild


def legal(box,m):
    if not isinstance(box,list) or len(box)!=3 or any(type(v) is not int for v in box):return False
    x,y,w=box;tw,th=m['targetRatioWH']
    return x>=0 and y>=0 and w==min(m['width'],m['height']*tw//th) and x+w<=m['width'] and y*tw+w*th<=m['height']*tw


def rebuild_field(manifest, field_frames, shots, requests, outputs):
    common,p2j,_=old_helpers()
    fc=sys.modules['field_contract'];pc=sys.modules['package_contract']
    metadata=pc.validate_manifest(manifest)
    require(fc.build_field_requests(field_frames,shots,8)==requests,'independent original request/shot plan mismatch')
    require(pc.keyset(requests)==pc.keyset(outputs),'independent original observation set mismatch')
    req={(r['video_id'],r['source_frame']):r for r in requests}
    out={(r['video_id'],r['source_frame']):r for r in outputs}
    parser=sys.modules['contracts'].parse_focus_norm
    baseline=common.load(OLD/'spatial_baseline.py','sg8_independent_original_box_mapping')
    for key,r in req.items():
        o=out[key];m=metadata[key[0]]
        require(o['status']=='MODEL_OK' and o['used_fallback'] is False and
            o['spatial_source']=='QWEN_ANCHOR_SAME_FRAME' and
            o['anchor_request_sha256']==r['anchor_request_sha256'] and
            o['decoded_pixel_sha256']==r['expected_pixel_sha256'] and legal(o['box_xyw'],m),
            'independent original support identity/geometry failure')
        center=parser(o['raw_output'],m['width'],m['height'])
        require(center is not None,'independent unchanged original parser rejects raw')
        w,h=baseline.compute_crop_size(m['width'],m['height'],*m['targetRatioWH'])
        require(baseline.center_to_box(*center,m['width'],m['height'],w,h)==o['box_xyw'],
                'independent original raw-to-box mismatch')
    result={};eligible=linear=anchors=0
    for sid,shot in enumerate(p2j.group_shots(shots)):
        vid=shot[0]['video_id'];m=metadata[vid]
        q=p2j.anchor_frames([r['source_frame'] for r in shot],8)
        boxes={f:out[vid,f]['box_xyw'] for f in q}
        require(all(1<=b-a<=8 for a,b in zip(q,q[1:])),'invalid original gap')
        for row in shot:
            f=row['source_frame'];ix=bisect_left(q,f)
            if f in boxes:
                box,source=p2j.interpolate_box(f,boxes);anchors+=1
            elif ix>=2 and ix+1<len(q) and q[ix]-q[ix-1]==8:
                support=q[ix-2:ix+2]
                box=[rebuild(support,[boxes[n][axis] for n in support],f)[1] for axis in (0,1)]+[boxes[support[1]][2]]
                source=dict(spatial_source='SHOT_PCHIP_XY_ORDINAL_GAP8',support_ordinals=support,
                    left_anchor=support[1],right_anchor=support[2],left_distance=f-support[1],right_distance=support[2]-f,
                    arithmetic='FRACTION_FINAL_HALF_EVEN',algorithm='spatial_gap8_pchip_slot4_v1',
                    support_request_sha256=[req[vid,n]['anchor_request_sha256'] for n in support],
                    support_output_sha256=[digest(out[vid,n]) for n in support],
                    support_raw_sha256=[hashlib.sha256(out[vid,n]['raw_output'].encode()).hexdigest() for n in support])
                eligible+=1
            else:
                box,source=p2j.interpolate_box(f,boxes);linear+=1
            require(legal(box,m),'independent illegal result; no clipping')
            result[vid,f]=dict(video_id=vid,source_frame=f,shot_id=sid,box_xyw=box,legal=True,**source)
    require(set(result)==pc.keyset(field_frames),'independent full-source field denominator mismatch')
    return result,dict(full_source_frames=len(result),pchip_frames=eligible,ordinary_linear_frames=linear,original_anchors=anchors)


def strict(manifest, selected, predictions, provenance, field_frames, shots, requests, outputs,
           predictions_path, zip_path, full_predictions=None, full_provenance=None):
    expected_full,counts=rebuild_field(manifest,field_frames,shots,requests,outputs)
    pc=sys.modules['package_contract'];metadata=pc.validate_manifest(manifest)
    expected=pc.keyset(selected)
    require(expected<=set(expected_full),'selected keys outside full source')
    sys.path.insert(0,str(BASE/'vendor/frozen_strict_loader'))
    from aic6.scoring import load_predictions
    loaded=load_predictions(Path(predictions_path),metadata)
    actual={(vid,f) for vid,frames in loaded.rows.items() for f in frames}
    ids=[r['video_id'] for r in predictions]
    boxes={(r['video_id'],p['frame']):p['bboxes'] for r in predictions for p in r['predictions']}
    pkeys=[(r['video_id'],r['source_frame']) for r in provenance]
    pmap={k:v for k,v in zip(pkeys,provenance)}
    source_exact=all(pmap[k]==expected_full[k] for k in pmap if k in expected_full) and set(pmap)<=set(expected_full)
    with zipfile.ZipFile(zip_path) as archive:
        names=archive.namelist()
        crc=archive.testzip() is None
        archived=archive.read('predictions.jsonl') if names==['predictions.jsonl'] else b''
    checks=dict(strict_loader_ok=loaded.ok and not loaded.validation['issues'],
        video_record_set_exact=len(ids)==len(set(ids))==len(metadata) and set(ids)==set(metadata),
        selected_key_set_exact=expected==actual,
        ratio_fields_exact=all(r['targetRatioWH']==metadata[r['video_id']]['targetRatioWH'] for r in predictions),
        frames_sorted=all([p['frame'] for p in r['predictions']]==sorted(p['frame'] for p in r['predictions']) for r in predictions),
        provenance_key_set_exact=len(pkeys)==len(set(pkeys)) and set(pkeys)==expected,
        provenance_boxes_match_predictions={k:v['box_xyw'] for k,v in pmap.items()}==boxes,
        provenance_all_legal=all(r['legal'] is True and legal(r['box_xyw'],metadata[r['video_id']]) for r in provenance),
        provenance_sources_allowed=source_exact,
        archive_single_file=names==['predictions.jsonl'] and crc,
        archive_roundtrip_exact=archived==Path(predictions_path).read_bytes())
    full_ok=None
    if full_predictions is not None or full_provenance is not None:
        require(full_predictions is not None and full_provenance is not None,'both full field artifacts required')
        full_map={(r['video_id'],r['source_frame']):r for r in full_provenance}
        full_boxes={(r['video_id'],p['frame']):p['bboxes'] for r in full_predictions for p in r['predictions']}
        full_ok=(len(full_provenance)==len(full_map) and full_map==expected_full and
                 full_boxes=={k:r['box_xyw'] for k,r in expected_full.items()})
        require(full_ok,'independent full field reconstruction differs before fixed selection')
    require(len(checks)==11 and all(checks.values()),'independent original 11 strict substances failed')
    return dict(status='PASS_INDEPENDENT_SG8_STRICT_AND_FOUR_SUPPORT_RECONSTRUCTION',checks=checks,
        extra_checks=dict(full_field_before_selection_exact=full_ok,
            original_anchor_and_ordinary_linear_exact=True,uniform_eligibility_and_same_shot_exact=True,
            four_support_request_output_raw_hashes_exact=True),
        strict_loader_sha256=sha(BASE/'vendor/frozen_strict_loader/aic6/scoring.py'),
        video_records=len(ids),selected_frames=len(expected),counts=counts,
        zip_bytes=Path(zip_path).stat().st_size,zip_sha256=sha(zip_path),predictions_sha256=sha(predictions_path),
        independent_math_source_sha256=sha(Path(__file__).parent/'sg8_independent_math.py'),
        new_model_calls=0,new_optimizer_updates=0,official_score=None,uploaded=False)
