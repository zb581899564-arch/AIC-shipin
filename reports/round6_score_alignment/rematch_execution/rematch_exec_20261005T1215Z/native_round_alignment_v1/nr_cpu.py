"""Actual full120 round_alignment CPU feasibility; no GPU or teacher calls."""
import nr_common as c
from nr_native import round_indices,floor_indices
from nr_engine import encode_round

def main():
    rt,ex,cc,student,old,frames,production=c.helpers()
    original_model=c.read(c.HERE/'input_01/resume_manifest.json')['model_identity']
    v14_source,v14_stage,v14_rows=c.v14_authority(student,original_model)
    from types import SimpleNamespace
    for bad_student,bad_model in ((student,dict(original_model,adapter_sha256='0'*64)),
        (SimpleNamespace(INPUT_CONTRACT=dict(student.INPUT_CONTRACT,max_frames=127)),original_model)):
        try:c.v14_authority(bad_student,bad_model)
        except ValueError:pass
        else:raise ValueError('V14 model/input mutation was not refused')
    from transformers import AutoProcessor
    from nr_report import gate
    c.require(gate(0,.001,1,0) and not gate(.1,0,1,0) and not gate(.1,.1,0,0) and not gate(-.01,.1,1,0),'fixed administrative gate')
    for n in range(1,2001):
        base=floor_indices(13,13+n);dense=round_indices(base)
        c.require(len(base)==len(dense) and dense[0]==13 and dense[-1]==12+n and len(dense)<=64 and dense==sorted(set(dense)),'native nearest/endpoints/count')
        import numpy as np
        expected=[13+int(round(x)) for x in np.linspace(0,n-1,min(n,64))]
        c.require(dense==expected,'actual historical NumPy nearest arithmetic differs')
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    proofs=[]
    for scope in ('nontest','developer'):
        plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                base=c.checked_base(scope,job,ix)
                if part['window']==part['base_window']:
                    proofs.append(dict(scope=scope,video_id=job['video_id'],index=ix,
                        input_tokens=base['input_tokens'],base_sample_count=len(base['video_identity']['source_frame_ids']),
                        dense_sample_count=len(base['video_identity']['source_frame_ids']),base_grid=base['video_identity']['video_grid_thw'],
                        dense_grid=base['video_identity']['video_grid_thw'],exact_original_success_reused=True,
                        original_done_path=str(c.base_path(scope,job,ix,cc)),original_done_sha256=c.sha(c.base_path(scope,job,ix,cc)),
                        new_decoder_processor_calls=0))
                    continue
                encoded,evidence=encode_round(processor,part['window'],rt,student,ex)
                ids=evidence['source_frame_ids'];pixels=evidence['frame_pixel_sha256']
                base_ids=base['video_identity']['source_frame_ids'];base_pixels=base['video_identity']['frame_pixel_sha256']
                common=set(ids)&set(base_ids)
                c.require(all(pixels[ids.index(i)]==base_pixels[base_ids.index(i)] for i in common),'actual common physical observation RGB differs')
                c.require(len(ids)==len(base_ids) and evidence['video_grid_thw']==base['video_identity']['video_grid_thw'],'same frame count/spatial grid required')
                c.require(evidence['window_source_pts_sec']==base['video_identity']['window_source_pts_sec'],'all source-selection PTS unchanged')
                tokens=int(encoded['input_ids'].shape[1]);c.require(0<tokens<=16384,'actual input overflow, no truncation')
                proofs.append(dict(scope=scope,video_id=job['video_id'],index=ix,input_tokens=tokens,base_sample_count=len(base['video_identity']['source_frame_ids']),
                    dense_sample_count=len(ids),base_grid=base['video_identity']['video_grid_thw'],dense_grid=evidence['video_grid_thw'],
                    common_observation_RGB_equal=True,common_observation_count=len(common),
                    same_physical_count_and_grid=True,exact_native_processor_used=True,spatial_resolution_change_reported=False,
                    vision_signature=ex.video_signature(encoded),video_identity=evidence))
                del encoded;c.state('CPU_ROUND_ALIGNMENT_ACTUAL_INPUTS',checked_windows=len(proofs),total_windows=120,new_model_calls=0)
    c.require(len(proofs)==120 and sum(x['scope']=='nontest' for x in proofs)==8 and sum(x['scope']=='developer' for x in proofs)==112,'CPU full registered denominator')
    c.save(c.HERE/'cpu_acceptance.json',dict(status='PASS_ALL120_NATIVE_NEAREST_PROCESSOR_AND_COMMON_PIXEL_IDENTITY',utc=c.utc(),proofs=proofs,
        physical_sampling_contract_cases=2000,registered_gate_cases=4,max_input_tokens=max(x['input_tokens'] for x in proofs),
        actual_all120_inputs_not_estimated=True,changed_inputs_decoded_and_encoded=sum(not x.get('exact_original_success_reused',False) for x in proofs),
        exact_unchanged_successes_referenced=sum(x.get('exact_original_success_reused',False) for x in proofs),
        original_V14_complete_raw_validator_checked=521,original_V14_temporal_sha256=c.sha(v14_source),
        V14_cache_mutation_refusal_cases=2,new_model_calls=0,new_optimizer_updates=0,new_32B_calls=0))
    print('PASS_ALL120_NATIVE_NEAREST_PROCESSOR_AND_COMMON_PIXEL_IDENTITY',flush=True)

if __name__=='__main__':main()
