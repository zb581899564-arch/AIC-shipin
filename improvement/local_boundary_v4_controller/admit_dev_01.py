"""Main-agent admission for the fixed37 real development inputs plus3 structural points."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # This is a CPU admission child only.
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v4/dev')
sys.path.insert(0, str(BASE.parent/'code'))
import lb_io as io


def main():
    io.host(cpu=True)
    if (BASE/'gpu_admission.json').exists():
        raise ValueError('V4 development already admitted; do not launch or re-admit twice')
    cpu = io.read(BASE/'cpu_01/completion.json')
    plan, events, requests, skips, counts = io.plan_partition(BASE)
    registration = io.read(plan['registration_path'])
    if (cpu['status'] != 'PASS_ALL_NEW_LOCAL_BOUNDARY_CPU_INPUTS_NOT_GPU_ADMISSION' or
            len(cpu['proofs']) != 37 or
            registration['validation_scope'] != 'EXTERNAL_DEVELOPMENT_DIAGNOSTIC'):
        raise ValueError('Actual37-request CPU input denominator required')
    # Explicit equality avoids a chained != expression accidentally accepting
    # unequal values when one side happens to equal the expected constant.
    if not (cpu['requests'] == plan['requests'] == plan['actual_model_call_budget'] == 37 and registration['max_model_call_budget'] == 40):
        raise ValueError('Actual frozen smoke count mismatch')
    if cpu['bindings']['own_code_files'] != io.own_code_files():
        raise ValueError('Prepared input code changed')
    rt, original_files = io.legacy_runtime()
    import torch
    import sft_contract
    import constrained_json
    if torch.cuda.is_initialized():
        raise ValueError('CPU admission initialized CUDA')
    lock = dict(io.own_code_files())
    lock.update(original_files)
    lock.update(cpu['bindings']['original_b_processor_runtime']['processor_assets'])
    lock.update(registration['required_files'])
    for p in [Path(__file__).resolve(), BASE/'cpu_01/completion.json', BASE/'plan_01/completion.json',
              BASE/'plan_01/events.json', BASE/'plan_01/requests.json', Path(plan['registration_path']),
              io.RUN/'b_score_aligned_package_v4/config.json',
              Path(sft_contract.__file__).resolve(), Path(constrained_json.__file__).resolve()]:
        lock[str(p)] = io.sha(p)
    for path in sorted((BASE/'plan_01').glob('*.json')):
        lock[str(path)] = io.sha(path)
    for skip in skips:
        ref = skip['independent_geometry_proof']
        path = io.checked_ref(ref, roots=(BASE,))
        lock[str(path)] = ref['sha256']
    for control_path in sorted(Path(__file__).parent.glob('*.py')):
        lock[str(control_path.resolve())] = io.sha(control_path)
    sizes = []
    for entry in cpu['proofs']:
        proof = io.read(entry['proof_path'])
        meta = io.read(entry['input_path'])
        if (io.sha(entry['proof_path']) != entry['proof_sha256'] or
                io.sha(entry['input_path']) != entry['input_sha256'] or
                proof['input_tokens'] != entry['input_tokens'] or proof['input_tokens'] > 16384 or
                len(set(meta['source_frame_ordinals'])) != 64 or
                meta['reference_available_to_inference'] is not False):
            raise ValueError('Actual native64/CPU metadata changed')
        tensor = io.load_tensor_cache(proof['encoded_tensor_path'])
        if rt.tensor_signature(tensor) != proof['input_evidence']['tensor_signature']:
            raise ValueError('Independent accepted cache-byte signature differs')
        for p in [entry['proof_path'], entry['input_path'], proof['encoded_tensor_path'], meta['frame_array_path']]:
            lock[str(p)] = io.sha(p)
        if lock[meta['frame_array_path']] != meta['frame_array_sha256'] or lock[proof['encoded_tensor_path']] != proof['encoded_tensor_sha256']:
            raise ValueError('Actual pixels/tensor file bytes changed')
        for ref in meta['original_evidence'].values():
            path = io.checked_ref(ref)
            lock[str(path)] = ref['sha256']
        for ref in meta['reuse_rgb_inputs']:
            path = io.checked_ref(ref)
            lock[str(path)] = ref['sha256']
        sizes.append(dict(request_id=entry['request_id'], input_tokens=proof['input_tokens'],
                          logical_tensor_bytes=sum(t.numel()*t.element_size() for t in tensor.values()),
                          tensor_cache_bytes=Path(proof['encoded_tensor_path']).stat().st_size,
                          RGB_cache_bytes=Path(meta['frame_array_path']).stat().st_size))
        del tensor
    admission = dict(status='PASS_INDEPENDENT_LOCAL_BOUNDARY_GPU_ADMISSION',
        cpu_completion_sha256=io.sha(BASE/'cpu_01/completion.json'), registration_sha256=plan['registration_sha256'],
        actual_model_call_budget=37, model_parameters=8782459120, optimizer_updates=0,
        original_successful_stages_reused=True, source_input_lock_files=lock,
        gpu_job_name='aic20h_charades_dev37_time_boundary_20261014_v1',
        deadline='2026-10-14T11:56:40+00:00', science_quality_claim=False,
        native_input_sizes=sizes, nominal_endpoints=40, structural_skips=3, new_model_calls=0, utc=io.utc())
    io.save(BASE/'gpu_admission.json', admission)
    io.admitted_inputs(BASE)  # Existing independent consumer validates the lock/schema too.
    io.save(BASE/'gpu_admission_independent_check_01.json', dict(status='PASS_REAL37_INPUT_CACHE_AND_CONSUMER_ADMISSION_NOT_GPU_COMPLETE',
        gpu_admission_sha256=io.sha(BASE/'gpu_admission.json'), sizes=sizes, processor_encodes_in_admission=0,
        complete_clock_decodes_in_admission=0, model_calls=0, utc=io.utc()))
    print(json.dumps(dict(status=admission['status'], requests=37, sizes=sizes, new_model_calls=0)), flush=True)


if __name__ == '__main__':
    main()
