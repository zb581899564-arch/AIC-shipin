"""Original B processor input proofs on CPU after twenty-source RGB admission.

No model weights are loaded and no inference is performed. The final immutable
native input receipt is written only after every registered window succeeds.
"""
import hashlib
import json
import os
import socket
import sys
from fractions import Fraction as F
from pathlib import Path

from map_sources_remote import BASE, read, save, sha
from prepare_rgb_remote import OUT as RGB, admission as rgb_source_admission

OUT = BASE/'processor_01'
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
LEGACY_RUNTIME = Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')


def load_rgb_inputs(registration_path, policy_path, contract_path):
    complete = read(RGB/'completion.json')
    if (complete['status'] != 'PASS_REGISTERED_NATIVE64_RGB_CACHES_NOT_PROCESSOR_ADMISSION' or
            complete['sources'] != 20 or complete['new_model_calls'] != 0 or
            complete['new_optimizer_updates'] != 0):
        raise ValueError('All registered original RGB windows must pass before processor preparation')
    # Independently recheck the unchanged approval/mapping/separation bindings.
    registration, _, _, original_bindings = rgb_source_admission(registration_path)
    if complete['bindings'] != original_bindings:
        raise ValueError('Accepted RGB source bindings changed')
    if sha(RGB/'inputs.json') != complete['inputs_sha256']:
        raise ValueError('Completed original RGB window list changed')
    entries = read(RGB/'inputs.json')
    if (len(entries) != complete['windows'] or not entries or
            len({entry['case_id'] for entry in entries}) != len(entries) or
            {entry['source_name'] for entry in entries} != {row['source_name'] for row in registration['rows']}):
        raise ValueError('Original RGB source/window denominator changed')
    if Path(policy_path).name != 'EVALUATION_POLICY.md' or Path(contract_path).name != 'NATIVE_MAPPING_CONTRACT_V2.md':
        raise ValueError('The frozen human evaluation policy and corrected mapping contract are required')
    return registration, entries, dict(registration_sha256=sha(registration_path),
        evaluation_policy_sha256=sha(policy_path), mapping_contract_sha256=sha(contract_path),
        rgb_completion_sha256=sha(RGB/'completion.json'), rgb_inputs_sha256=sha(RGB/'inputs.json'),
        script_sha256=sha(Path(__file__)))


def load_cpu_runtime():
    import torch
    import transformers
    if torch.cuda.is_initialized() or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('This preparation child must remain CPU-only')
    sys.path.insert(0, str(LEGACY_RUNTIME))
    import runtime
    if Path(runtime.__file__).resolve() != (LEGACY_RUNTIME/'runtime.py').resolve():
        raise ValueError('Original native B runtime resolved to an unexpected module')
    modules = ('runtime', 'engine', 'contracts', 'bw_video', 'exact_pts', 'native_frames')
    files = {str(Path(sys.modules[name].__file__).resolve()): sha(sys.modules[name].__file__) for name in modules}
    config_path = RUN/'b_score_aligned_package_v4/config.json'
    config = read(config_path)
    model_dir = Path(config['model_dir'])
    assets = {str(path): sha(path) for path in sorted(model_dir.iterdir())
              if path.is_file() and path.suffix in ('.json', '.txt', '.jinja')}
    if not assets:
        raise ValueError('No existing local original processor/tokenizer assets')
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(model_dir, local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    return runtime, processor, dict(runtime_files=files, processor_assets=assets,
        original_config_sha256=sha(config_path), torch_version=torch.__version__,
        transformers_version=transformers.__version__,
        prompt_sha256=hashlib.sha256(runtime.EMPTY_PROMPT.encode()).hexdigest())


def main(registration_path, policy_path, contract_path, resume=False):
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('This CPU entry is confined to the existing Linux training host')
    registration, entries, bindings = load_rgb_inputs(registration_path, policy_path, contract_path)
    if (BASE/'native_input_acceptance.json').exists() or (OUT/'completion.json').exists():
        raise ValueError('Completed CPU processor input acceptance must not be run again')
    # No torch/runtime/processor is imported before the real RGB admission above.
    runtime, processor, runtime_identity = load_cpu_runtime()
    bindings['original_b_processor_runtime'] = runtime_identity
    if resume:
        if read(OUT/'launch_claim.json')['bindings'] != bindings or (OUT/'failure.json').exists():
            raise ValueError('Failed or changed processor preparation requires separate recovery')
    else:
        OUT.mkdir(parents=True, exist_ok=False)
        save(OUT/'launch_claim.json', dict(pid=os.getpid(), bindings=bindings,
             new_model_calls=0, new_optimizer_updates=0))
    proofs = []
    current = None
    try:
        for entry in entries:
            current = entry['case_id']
            meta_path = Path(entry['input_path'])
            if not meta_path.resolve().is_relative_to(RGB.resolve()) or sha(meta_path) != entry['input_sha256']:
                raise ValueError('Accepted native RGB input metadata changed')
            meta = read(meta_path)
            if meta['case_id'] != current or meta['source_name'] != entry['source_name']:
                raise ValueError('Processor window identity changed')
            if meta['reference_available_to_inference'] is not False or meta['audio_observed'] is not False:
                raise ValueError('Original visual-only window received extra evidence')
            proof_path = OUT/(current+'.cpu_input.json')
            if proof_path.exists():
                proof = read(proof_path)
                if (proof['status'] != 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' or
                        proof['bindings'] != bindings or proof['input_sha256'] != entry['input_sha256'] or
                        sha(meta['frame_array_path']) != meta['frame_array_sha256']):
                    raise ValueError('Successful actual CPU input proof changed')
                # Completed processor encoding is reused; no successful encode is repeated.
            else:
                frames = runtime.baseline_frames(meta)
                encoded, detail = runtime.encode(processor, meta, frames, F(meta['window_start']), runtime.EMPTY_PROMPT)
                input_tokens = int(encoded['input_ids'].shape[1])
                if input_tokens > 16384 or detail['physical_frames'] != 64:
                    raise ValueError('Actual processor input exceeded the fixed native64/token protocol')
                if any(value.device.type != 'cpu' for value in encoded.values() if hasattr(value, 'device')):
                    raise ValueError('Actual processor preparation unexpectedly used GPU tensors')
                proof = dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT',
                             case_id=current, source_name=entry['source_name'], bindings=bindings,
                             input_path=str(meta_path), input_sha256=entry['input_sha256'],
                             input_evidence=detail, input_tokens=input_tokens,
                             source_start_exact=meta['window_start'], source_end_exact=meta['window_end'],
                             CPU_only=True, new_model_calls=0, new_optimizer_updates=0)
                save(proof_path, proof)
                del encoded, frames
            proofs.append(dict(case_id=current, source_name=entry['source_name'],
                               proof_path=str(proof_path), proof_sha256=sha(proof_path),
                               input_tokens=proof['input_tokens']))
            print(json.dumps(dict(case_id=current, accepted_windows=len(proofs)), ensure_ascii=False), flush=True)
        import torch
        if torch.cuda.is_initialized():
            raise ValueError('Actual processor acceptance initialized CUDA')
        complete = dict(status='PASS_ALL_REGISTERED_CPU_NATIVE64_PROCESSOR_INPUTS',
                        registered_sources=20, accepted_sources=20, accepted_windows=len(proofs),
                        proofs=proofs, bindings=bindings, CPU_only=True, CUDA_initialized=False,
                        new_model_calls=0, new_optimizer_updates=0)
        save(OUT/'completion.json', complete)
        save(BASE/'native_input_acceptance.json', dict(status='PASS_ALL_REGISTERED_HUMAN_NATIVE_INPUTS',
            registered_sources=20, accepted_sources=20, accepted_windows=len(proofs), frame_mapping_failures=0,
            known_source_separation_pass=True, registration_sha256=bindings['registration_sha256'],
            evaluation_policy_sha256=bindings['evaluation_policy_sha256'],
            mapping_contract_sha256=bindings['mapping_contract_sha256'],
            processor_completion_sha256=sha(OUT/'completion.json'),
            new_model_calls=0, new_optimizer_updates=0, GPU_launch_admitted=False,
            requires_frozen_full_source_input_lock_and_unique_gpu_wrapper=True))
    except Exception as error:
        save(OUT/'failure.json', dict(status='FAILED_CPU_ORIGINAL_PROCESSOR_INPUT', case_id=current,
             error_type=type(error).__name__, error=str(error), successful_proofs_retained=proofs,
             new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Only the CPU child, never the chain parent.
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), resume='--resume' in sys.argv[4:])
