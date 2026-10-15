"""One new prompt-token input per VERIFY candidate; old vision cache is reused."""
import hashlib
import os
import resource
import time

import cv_contract as c
import cv_io as io
from cv_tokens import retarget, VISION_KEYS, TOKEN_KEYS


def main():
    io.check_host(cpu=True)
    reg, reg_sha = io.registration()
    plan = io.read(io.BASE/'plan_01/completion.json')
    if (plan['status'] != 'PASS_EXTERNAL_VERIFY_PLAN_NOT_CPU_ADMISSION' or
            plan['registration_sha256'] != reg_sha or plan['code_files'] != io.code_files() or
            plan['requests_sha256'] != io.sha(io.BASE/'plan_01/requests.json')):
        raise ValueError('Complete frozen VERIFY plan/code changed')
    requests = io.read(io.BASE/'plan_01/requests.json')
    if len(requests) != reg['actual_model_call_budget']:
        raise ValueError('Registered complete VERIFY request denominator changed')
    out = io.BASE/'cpu_01'
    out.mkdir(exist_ok=False)
    bindings = dict(registration_sha256=reg_sha, plan_completion_sha256=io.sha(io.BASE/'plan_01/completion.json'),
                    code_files=io.code_files())
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), bindings=bindings,
        media_decodes=0, vision_processor_calls=0, model_calls=0))
    current, proofs = None, []
    try:
        import torch
        runtime, processor, identity = io.cpu_processor()
        bindings['original_b_processor_runtime'] = identity
        if hashlib.sha256(runtime.EMPTY_PROMPT.encode()).hexdigest() != c.EMPTY_PROMPT_SHA256:
            raise ValueError('Actual original empty-capable prompt changed')
        for planned in requests:
            started = time.monotonic()
            current = planned['request_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            cache_path = io.checked(dict(path=planned['original_vision_cache_path'],
                                        sha256=planned['original_vision_cache_sha256']))
            original = io.load_tensor_cache(cache_path)
            if runtime.tensor_signature(original) != planned['original_input_evidence']['tensor_signature']:
                raise ValueError('Actual original accepted vision/token cache signature differs')
            tokens, combined, retarget_evidence = retarget(original, processor.tokenizer,
                runtime.EMPTY_PROMPT, planned['prompt'], runtime.tensor_signature)
            token_path = folder/'prompt_tokens.pt.gz'
            io.save_tensor_cache(token_path, tokens)
            restored_tokens = io.load_tensor_cache(token_path)
            if runtime.tensor_signature(restored_tokens) != runtime.tensor_signature(tokens):
                raise ValueError('Lossless token-only cache changed the new CPU input')
            input_evidence = dict(planned['original_input_evidence'], case_id=current,
                original_case_id=planned['original_case_id'], input_tokens=retarget_evidence['input_tokens'],
                prompt_sha256=hashlib.sha256(planned['prompt'].encode()).hexdigest(),
                tensor_signature=retarget_evidence['full_tensor_signature'],
                unchanged_vision_tensor_signature=retarget_evidence['unchanged_vision_tensor_signature'],
                vision_processor_calls=0, media_decodes=0, prompt_tokens_only_new=True)
            req = dict(planned, input_evidence=input_evidence, retarget_evidence=retarget_evidence,
                token_cache_path=str(token_path), token_cache_sha256=io.sha(token_path),
                token_cache_scope='PROMPT_TOKENS_ONLY_VISION_FROM_HASH_BOUND_ORIGINAL',
                token_cache_format=io.TENSOR_CACHE_FORMAT, bindings=bindings)
            input_path = folder/'input.json'
            io.save(input_path, req)
            proof_path = folder/'cpu_input.json'
            io.save(proof_path, dict(status='PASS_CPU_VERIFY_PROMPT_TOKENS_UNCHANGED_ORIGINAL_VISION',
                request_id=current, event_id=req['event_id'], bindings=bindings,
                input_path=str(input_path), input_sha256=io.sha(input_path), input_evidence=input_evidence,
                input_tokens=retarget_evidence['input_tokens'], retarget_evidence=retarget_evidence,
                token_cache_path=str(token_path), token_cache_sha256=io.sha(token_path),
                token_cache_format=io.TENSOR_CACHE_FORMAT,
                original_vision_cache_path=str(cache_path), original_vision_cache_sha256=req['original_vision_cache_sha256'],
                token_cache_file_bytes=token_path.stat().st_size,
                original_vision_cache_file_bytes=cache_path.stat().st_size,
                new_prompt_prepare_seconds=time.monotonic()-started,
                process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                CPU_only=True, CUDA_initialized=False, new_prompt_tokenizer_calls=1,
                original_text_roundtrip_tokenizer_calls=1, new_media_decodes=0, vision_processor_calls=0,
                new_model_calls=0, new_optimizer_updates=0))
            if torch.cuda.is_initialized():
                raise ValueError('Actual token-only CPU preparation initialized CUDA')
            proofs.append(dict(request_id=current, event_id=req['event_id'],
                proof_path=str(proof_path), proof_sha256=io.sha(proof_path)))
            print(__import__('json').dumps(dict(request_id=current, accepted_inputs=len(proofs),
                total_inputs=len(requests), vision_processor_calls=0)), flush=True)
            del original, tokens, combined, restored_tokens
        io.save(out/'completion.json', dict(status='PASS_ALL_EXTERNAL_VERIFY_TOKEN_INPUTS_NOT_GPU_ADMISSION',
            requests=len(proofs), proofs=proofs, bindings=bindings, CPU_only=True, CUDA_initialized=False,
            new_prompt_tokenizer_calls=len(proofs), original_text_roundtrip_tokenizer_calls=len(proofs),
            new_media_decodes=0, vision_processor_calls=0, new_model_calls=0, new_optimizer_updates=0,
            original_vision_caches_reused=True, GPU_launch_admitted=False))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_VERIFY_CPU_KEEP_ALL_SUCCESS_NO_UNKNOWN_FALLBACK',
            request_id=current, successful_proofs=proofs, error=repr(error),
            report_original_cache_absence_to_main=isinstance(error, io.MissingOriginalCacheError),
            new_media_decodes=0, vision_processor_calls=0, new_model_calls=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main()
