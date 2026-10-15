"""First independent conservative VERIFY prompt-token QA, before its GPU job."""
import argparse
import os
from pathlib import Path
import traceback

import model_common as io
from fresh_registration import registration
import pilot_verify as verify


def main(root):
    io.host(cpu=True); root = io.root_path(root); reg = registration(root)
    cpu_path = root/'confirm/VERIFY/cpu_01/completion.json'; cpu = io.read(cpu_path)
    io.require(cpu['status'] == verify.CPU_STATUS and cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False and
        cpu['new_model_calls'] == cpu['vision_processor_calls'] == cpu['media_decodes'] == 0 and
        cpu['expected_input_count'] == len(cpu['entries']) <= reg['gpu_budget']['VERIFY']['max_actual_calls'],
        'Complete real conservative VERIFY prompt preparation required')
    output = root/'confirm/VERIFY/input_qa_01'; output.mkdir(exist_ok=False)
    io.save(output/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), CPU_only=True,
        first_new_prompt_input_QA_before_GPU=True, cpu_completion_sha256=io.sha(cpu_path),
        no_vision_processor_or_media_decode=True, new_model_calls=0))
    io.require(io.read(root/'confirm/VERIFY/cpu_01/launch_claim.json')['pid'] != os.getpid(),
               'First independent VERIFY input QA requires its own process')
    proofs, current = [], None
    files = dict(io.read(root/'source_lock_confirm_B0.json')['files'])
    def add(path, digest=None):
        path = io.checked(path, digest); actual = io.sha(path)
        io.require(str(path) not in files or files[str(path)] == actual, 'Previously frozen dependency/input changed')
        files[str(path)] = actual; return path
    try:
        runtime, processor = io.cpu_processor(); contract, _, tm = io.cv_modules()
        for entry in cpu['entries']:
            current = entry['case_id']; req = io.read(add(entry['input_path'], entry['input_sha256']))
            proof = io.read(add(entry['proof_path'], entry['proof_sha256']))
            original = io.load_cache(add(proof['original_vision_cache_path'], proof['original_vision_cache_sha256']))
            cached = io.load_cache(add(proof['token_cache_path'], proof['token_cache_sha256']))
            io.require(req['prompt'] == contract.prompt(req) and runtime.tensor_signature(original) == req['original_input_evidence']['tensor_signature'],
                       'Exact conservative prompt and original first-QA-admitted cache required')
            tokens, combined, observed = verify.independent_tokens(original, processor.tokenizer, req['prompt'],
                runtime.tensor_signature, tm.vision_prefix, tm.VISION_KEYS)
            io.require(runtime.tensor_signature(tokens) == runtime.tensor_signature(cached) and
                all(proof['retarget_evidence'][key] == value for key, value in observed.items()) and
                runtime.tensor_signature(combined) == req['input_evidence']['tensor_signature'] == proof['input_evidence']['tensor_signature'] and
                0 < observed['input_tokens'] <= 16384, 'First actual independent conservative new-token input QA failed')
            path = output/(current+'.json')
            io.save(path, dict(status='PASS_FIRST_INDEPENDENT_FRESH_VERIFY_INPUT_QA_PRE_GPU', group='confirm', case_id=current,
                input_sha256=entry['input_sha256'], proof_sha256=entry['proof_sha256'],
                input_evidence=proof['input_evidence'], independent_token_evidence=observed,
                CPU_only=True, CUDA_initialized=False, vision_processor_calls=0, media_decodes=0,
                actual_first_independent_prompt_QA=1, new_model_calls=0)); add(path)
            proofs.append(dict(case_id=current, proof_ref=dict(path=str(path), sha256=io.sha(path))))
            print(__import__('json').dumps(dict(stage='FIRST_FRESH_VERIFY_INPUT_QA', completed=len(proofs), expected=len(cpu['entries']))), flush=True)
            for value in req['original_evidence'].values():
                add(value['path'], value['sha256'])
            del original, cached, tokens, combined
        import torch
        io.require(not torch.cuda.is_initialized(), 'CPU VERIFY input QA initialized CUDA')
        qa_path = output/'completion.json'
        io.save(qa_path, dict(status='PASS_FIRST_INDEPENDENT_FRESH_VERIFY_INPUT_QA_PRE_GPU', group='confirm',
            calls=len(proofs), proofs=proofs, CPU_only=True, CUDA_initialized=False,
            vision_processor_calls=0, media_decodes=0, new_model_calls=0, new_optimizer_updates=0)); add(qa_path)
        add(cpu_path); add(cpu['requests_path'], cpu['requests_sha256']); add(output/'launch_claim.json')
        for key in ('b0_cpu_acceptance', 'b0_source_lock', 'b0_admission', 'b0_gpu_completion', 'b0_replay_completion'):
            add(cpu['bindings'][key+'_path'], cpu['bindings'][key+'_sha256'])
        # Every natural B0 terminal/raw/request and first output QA is inherited
        # into this later stage closure; this performs file checks, no replay.
        gate = io.read(root/'gpu_admission_confirm_B0.json')
        add(io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json'))
        for path in (root/'confirm/B0/gpu_01').rglob('*.json'):
            add(path)
        add(root/'confirm/B0/gpu_01/attempts.jsonl')
        for path in (root/'confirm/B0/replay_01').glob('*.json'):
            add(path)
        io.save(root/'source_lock_confirm_VERIFY.json', dict(files=files, group='confirm', stage='VERIFY', utc=io.utc()))
    except BaseException as error:
        io.save(output/'failure.json', dict(current=current, successful_proofs=proofs, error=repr(error),
            traceback=traceback.format_exc(), preserve_all_success=True, implicit_resume=False, new_model_calls=0))
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args(); os.environ['CUDA_VISIBLE_DEVICES']=''; main(args.root)
