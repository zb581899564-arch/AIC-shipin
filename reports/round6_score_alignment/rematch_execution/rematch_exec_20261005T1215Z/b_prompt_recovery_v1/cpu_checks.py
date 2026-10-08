"""New recipe admission with exact old proofs and a genuinely new B1 input."""
import brec_common as c

def main():
    rt,ex,cc,student,old,frames,production=c.helpers()
    resume=c.read(c.HERE/'input_01/resume_manifest.json')
    original=c.read(c.CAD/'draft_preflight.json')
    c.require(original['status']=='PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS' and
        len(original['non_test_proofs'])==8,'original five-arm processor proof')
    nontest=c.read(c.HERE/'input_01/nontest_plan.json')
    proof_by_id={x['video_id']:x for x in original['non_test_proofs']}
    for job in nontest['jobs']:
        for arm in ('B1','B0'):
            v=c.checked(c.old_path('nontest',job,0,arm,cc),job,0,arm,ex)
            p=proof_by_id[job['video_id']]
            c.require(p['all_five_vision_tensors_equal'] and p['B0_all_encoded_tensors_equal_actual_V14'] and
                v['video_identity']['frame_pixel_sha256']==p['pixel_sha256'],'original NONTEST CPU/GPU pixel link')
    plan=c.read(c.HERE/'input_01/developer_plan.json')
    missing=resume['missing_B1_windows'][0]
    job=next(x for x in plan['developer_jobs'] if x['video_id']==missing['video_id']);ix=missing['index']
    from transformers import AutoProcessor
    from constrained_json import ascii_token_candidates,make_prefix_constraint
    from contracts import parse_segments
    import torch
    from brec_report import gate
    # The strict expanded direction must reject a tie and any empty change.
    c.require(gate(0,.001,1,0) and not gate(.1,0,1,0) and not gate(.1,.1,0,0) and
        not gate(-.05,.1,1,.75) and not gate(-.001,.1,1,0),'registered investment rule contracts')
    cfg=c.read(c.RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    decoded=student.decode_window(job['windows'][ix]['window']);signatures={};tokens={}
    for arm in ('B1','B0'):
        encoded,evidence=rt.encode_decoded(processor,decoded,ex.base_texts(old)[arm])
        signatures[arm]=ex.video_signature(encoded);tokens[arm]=int(encoded['input_ids'].shape[1]);del encoded
    control=c.checked(c.old_path('developer',job,ix,'B0',cc),job,ix,'B0',ex)
    c.require(signatures['B1']==signatures['B0']==control['vision_tensor_signature'] and
        decoded[3]['frame_pixel_sha256']==control['video_identity']['frame_pixel_sha256'],'new B1 native vision differs from B0')
    c.require(all(0<n<=16384 for n in tokens.values()),'real processor input budget')
    # Validate actual grammar and parser acceptance/rejection; no model generation.
    candidates=ascii_token_candidates(processor.tokenizer)
    constraint=make_prefix_constraint(processor.tokenizer,0,job['windows'][ix]['window']['window_duration_sec'],
        candidate_token_ids=candidates,eos_token_ids=processor.tokenizer.eos_token_id,allow_empty=False)
    good='{"segments":[[0,1]]}'
    ids=processor.tokenizer.encode(good,add_special_tokens=False)
    constraint.assert_complete(torch.tensor(ids))
    rejection=0
    try:constraint.assert_complete(torch.tensor(processor.tokenizer.encode('{"segments":[]}',add_special_tokens=False)))
    except (AssertionError,ValueError,RuntimeError):rejection+=1
    c.require(rejection==1,'historical grammar must reject empty')
    for text,empty,expected in ((good,False,True),('{"segments":[]}',False,False),('{"segments":[]}',True,True),
        ('{"segments":[[1,0]]}',False,False),('{"segments":[[0,1],[0,1]]}',False,False)):
        parsed,errors,_=parse_segments(text,job['windows'][ix]['window']['window_duration_sec'],allow_empty=empty)
        c.require((not errors and parsed is not None)==expected,'original parser contract disagreement')
    # Wrong prompt/grammar/model/window is not exact cache reuse.
    for key,value in (('prompt',ex.base_texts(old)['B1']),('allow_empty',False),('max_input',16385)):
        request=c.local_request(job,ix,'B0',control['model_identity'],ex);request[key]=value
        c.require(cc.digest(request)!=control['request_sha256'],'changed contract admitted as original B0')
    c.save(c.HERE/'cpu_acceptance.json',{'status':'PASS_ACTUAL_NEW_B1_NATIVE_PROCESSOR_AND_EXACT_RESUME',
        'utc':c.utc(),'original_NONTEST8_five_arm_proof_reused':True,'original_proof_sha256':c.sha(c.CAD/'draft_preflight.json'),
        'new_processor_source':missing['video_id'],'new_processor_window':ix,'input_tokens':tokens,
        'B1_B0_actual_video_tensor_equal':True,'original_native_pixel_SHA_equal':True,'actual_B1_empty_rejected':True,
        'original_parser_cases':5,'changed_cache_contract_rejections':3,'new_model_calls':0,'new_optimizer_updates':0})
    print(c.read(c.HERE/'cpu_acceptance.json'),flush=True)

if __name__=='__main__':main()
