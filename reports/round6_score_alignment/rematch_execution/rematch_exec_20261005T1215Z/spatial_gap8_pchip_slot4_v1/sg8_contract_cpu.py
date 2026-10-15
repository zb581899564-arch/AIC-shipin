"""New synthetic contract tests against actual Linux pinned old consumers.

No media or model observations. Fixture ZIP is explicitly non-submittable.
"""
import copy
import json
import sys

from sg8_common import HERE,OLD,read,save,sha,digest,require,old_helpers,utc,state
from sg8_field import compose
from sg8_independent_field import rebuild_field,strict


def main():
    common,p2j,_=old_helpers()
    fc=sys.modules['field_contract'];pc=sys.modules['package_contract'];frames=sys.modules['frame_contract']
    manifest=frames.legacy_manifest(read(read(OLD/'config.json')['inputs']['nontest']['manifest']))
    records=[];fields=[];shots=[]
    for i,source in enumerate(manifest['records']):
        r=copy.deepcopy(source);r.update(video_id='SYNTHETIC_SG8_'+str(i),source_group='SG8_FIXTURE_'+str(i),
            source_path=manifest['allowed_source_roots'][0]+'/SG8_SYNTHETIC_NOT_MEDIA_'+str(i),
            source_sha256=digest(['synthetic',i]),n_frames=43,fps_num=25,fps_den=1,scope_start_sec=0,scope_end_sec=43/25,
            width=1280 if i%2==0 else 720,height=720 if i%2==0 else 1280,
            targetRatioWH=[9,16] if i%2==0 else [16,9])
        records.append(r)
        for f in range(43):
            fields.append(dict(video_id=r['video_id'],source_frame=f,source_path=r['source_path'],
                source_width=r['width'],source_height=r['height'],source_n_frames=43,fps=25.0,target_ratio_wh=r['targetRatioWH']))
            shots.append(dict(video_id=r['video_id'],source_frame=f,is_shot_start=f==0,
                              decoded_pixel_sha256=digest(['synthetic_pixel',i,f])))
    manifest['records']=records
    requests=fc.build_field_requests(fields,shots,8)
    baseline=common.load(OLD/'spatial_baseline.py','sg8_synthetic_original_mapping')
    outputs=[]
    vals=[0,250,500,750,1000,500,100]
    for request in requests:
        vid=request['video_id'];i=int(vid.rsplit('_',1)[1]);f=request['source_frame'];value=vals[min(f//8,6)]
        center_int=[value,500] if i%2==0 else [500,value]
        raw=json.dumps(dict(center=center_int));center=[v/1000 for v in center_int];r=records[i]
        cw,ch=baseline.compute_crop_size(r['width'],r['height'],*r['targetRatioWH'])
        box=baseline.center_to_box(*center,r['width'],r['height'],cw,ch)
        outputs.append(dict(video_id=vid,source_frame=f,status='MODEL_OK',used_fallback=False,
            spatial_source='QWEN_ANCHOR_SAME_FRAME',anchor_request_sha256=request['anchor_request_sha256'],
            decoded_pixel_sha256=request['expected_pixel_sha256'],raw_output=raw,center_norm=center,box_xyw=box))
    selected=[r for r in fields if r['source_frame']%2==0]
    full,provenance,pred,chosen=compose(manifest,selected,fields,shots,requests,outputs)
    independent,counts=rebuild_field(manifest,fields,shots,requests,outputs)
    require({(r['video_id'],r['source_frame']):r for r in provenance}==independent,'new full synthetic field differs independently')
    folder=HERE/'g0_synthetic_contract_fixture';folder.mkdir(exist_ok=False)
    pc.write_rows(folder/'predictions.jsonl',pred)
    pc.package(folder/'predictions.jsonl',folder/'DO_NOT_SUBMIT_SYNTHETIC8.zip')
    result=strict(manifest,selected,pred,chosen,fields,shots,requests,outputs,
        folder/'predictions.jsonl',folder/'DO_NOT_SUBMIT_SYNTHETIC8.zip',full,provenance)
    failures=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,AssertionError):failures.append(name);return
        raise ValueError('invalid mutation accepted: '+name)
    bad=copy.deepcopy(chosen)
    target=next(r for r in bad if r['spatial_source']=='SHOT_PCHIP_XY_ORDINAL_GAP8')
    target['support_raw_sha256'][0]='0'*64
    reject('corrupted_four_support_raw_binding',lambda:strict(manifest,selected,pred,bad,fields,shots,requests,outputs,folder/'predictions.jsonl',folder/'DO_NOT_SUBMIT_SYNTHETIC8.zip'))
    bad2=copy.deepcopy(chosen);bad2[0]['shot_id']+=1
    reject('wrong_original_shot_identity',lambda:strict(manifest,selected,pred,bad2,fields,shots,requests,outputs,folder/'predictions.jsonl',folder/'DO_NOT_SUBMIT_SYNTHETIC8.zip'))
    bad3=copy.deepcopy(outputs);bad3[0]['raw_output']='{"center":[0.5,500]}'
    reject('unchanged_strict_integer_parser',lambda:rebuild_field(manifest,fields,shots,requests,bad3))
    bad4=copy.deepcopy(outputs);bad4[0]['box_xyw'][2]-=1
    reject('changed_maximum_width',lambda:rebuild_field(manifest,fields,shots,requests,bad4))
    bad5=copy.deepcopy(requests);bad5.append(copy.deepcopy(requests[0]))
    reject('duplicate_request_identity',lambda:rebuild_field(manifest,fields,shots,bad5,outputs))
    bad6=copy.deepcopy(provenance);bad6[0]['box_xyw'][0]+=1
    reject('full_field_not_validated_before_time_selection',lambda:strict(manifest,selected,pred,chosen,fields,shots,requests,outputs,
        folder/'predictions.jsonl',folder/'DO_NOT_SUBMIT_SYNTHETIC8.zip',full,bad6))
    save(HERE/'g0_new_field_contract.json',dict(status='PASS_SYNTHETIC_NEW_FIELD_AND_ACTUAL_PINNED_11_STRICT_CONTRACT_NOT_G3',
        utc=utc(),strict=result,rejected_mutations=failures,fixture_only=True,actual_media_decode_calls=0,
        new_model_calls=0,new_optimizer_updates=0,full_G0=False,G3_accepted=False))
    state('G0_NEW_FIELD_11_STRICT_SYNTHETIC_CONTRACT_PASS',new_spatial_calls=0,mutation_rejections=len(failures))


if __name__=='__main__':main()
