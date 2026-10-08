"""Actual full120 density CPU feasibility; no GPU or teacher calls."""
import nd_common as c
from nd_native import nested_indices,floor_indices
from nd_engine import encode_nested

def main():
    rt,ex,cc,student,old,frames,production=c.helpers()
    from transformers import AutoProcessor
    from nd_report import gate
    c.require(gate(0,.001,1,0) and not gate(.1,0,1,0) and not gate(.1,.1,0,0) and not gate(-.01,.1,1,0),'fixed administrative gate')
    for n in range(1,2001):
        base=floor_indices(13,13+n);dense=nested_indices(base)
        c.require(set(base)<=set(dense) and dense[0]==13 and dense[-1]==12+n and len(dense)<=127 and dense==sorted(set(dense)),'native subset/endpoints/count')
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    proofs=[]
    for scope in ('nontest','developer'):
        plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                base=c.checked_base(scope,job,ix);encoded,evidence=encode_nested(processor,part['window'],rt,student,ex)
                ids=evidence['source_frame_ids'];pixels=evidence['frame_pixel_sha256']
                c.require([pixels[ids.index(i)] for i in base['video_identity']['source_frame_ids']]==base['video_identity']['frame_pixel_sha256'],'actual preserved old64 RGB/native identity')
                c.require(evidence['window_source_pts_sec']==base['video_identity']['window_source_pts_sec'],'all source-selection PTS unchanged')
                tokens=int(encoded['input_ids'].shape[1]);c.require(0<tokens<=16384,'actual input overflow, no truncation')
                proofs.append(dict(scope=scope,video_id=job['video_id'],index=ix,input_tokens=tokens,base_sample_count=len(base['video_identity']['source_frame_ids']),
                    dense_sample_count=len(ids),base_grid=base['video_identity']['video_grid_thw'],dense_grid=evidence['video_grid_thw'],
                    preserved_RGB_equal=True,exact_native_processor_used=True,spatial_resolution_change_reported=True,
                    vision_signature=ex.video_signature(encoded),video_identity=evidence))
                del encoded;c.state('CPU_DENSITY_ACTUAL_INPUTS',checked_windows=len(proofs),total_windows=120,new_model_calls=0)
    c.require(len(proofs)==120 and sum(x['scope']=='nontest' for x in proofs)==8 and sum(x['scope']=='developer' for x in proofs)==112,'CPU full registered denominator')
    c.save(c.HERE/'cpu_acceptance.json',dict(status='PASS_ALL120_ACTUAL_NESTED_NATIVE_PROCESSOR_AND_BASE_PIXEL_IDENTITY',utc=c.utc(),proofs=proofs,
        physical_sampling_contract_cases=2000,registered_gate_cases=4,max_input_tokens=max(x['input_tokens'] for x in proofs),
        actual_all120_inputs_not_estimated=True,new_model_calls=0,new_optimizer_updates=0,new_32B_calls=0))
    print('PASS_ALL120_ACTUAL_NESTED_NATIVE_PROCESSOR_AND_BASE_PIXEL_IDENTITY',flush=True)

if __name__=='__main__':main()
