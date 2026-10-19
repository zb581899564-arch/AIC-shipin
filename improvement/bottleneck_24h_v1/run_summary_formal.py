"""Finite production after main's actual external-capability admission only.

One explicit registration, no newest-version lookup, retries, scheduler or upload.
Never called by the development/training chain. Stages stop on real failure.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

W = Path('/home/inspur/aic_video_work')
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(W) and path.is_file() and sha(path) == reference['sha256'],
            'Registered artifact changed/outside explicit workspace')
    if 'bytes' in reference:
        require(path.stat().st_size == reference['bytes'], 'Registered artifact size changed')
    return path


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())


def event(root, stage, **values):
    with (root/'formal_sequence_14.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), stage=stage,
                                    **values), allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())


def snapshot():
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    return dict(host=os.uname().nodename, load=os.getloadavg(), disk_free=shutil.disk_usage(W).free,
        mem_available_bytes=int(memory['MemAvailable'].split()[0])*1024,
        gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.total,utilization.gpu',
                                     '--format=csv,noheader'], text=True).strip(),
        gpu_apps=subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                          '--format=csv,noheader'], text=True).strip())


def capacity(reg, stage, planned_disk, planned_ram):
    require(type(planned_disk) is int and planned_disk > 0 and type(planned_ram) is int and planned_ram > 0,
            'Explicit stage output/working-memory estimate required')
    current = snapshot()
    require(current['host'] == 'inspur-NP5570M5', 'Actual training host identity')
    require(current['disk_free'] > planned_disk and current['mem_available_bytes'] > planned_ram,
            'Actual declared stage outputs/working set do not fit current resources; preserve all and stop')
    return dict(stage=stage, actual_resources=current, planned_disk_bytes=planned_disk,
                planned_ram_bytes=planned_ram, reason=reg['resource_estimate_basis'])


def cpu(root, reg, name, code_name, registration_path, disk, ram):
    require(datetime.now(timezone.utc) < datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),
            'No new CPU preparation, QA or package stage after original24h boundary')
    measured = capacity(reg, name, disk, ram)
    save(root/(name+'_resource_before.json'), measured)
    event(root, 'BEGIN_'+name)
    with (root/(name+'.log')).open('xb') as stream:
        result = subprocess.run([reg['python'], '-B', str(bound(reg['code'][code_name])),
            '--registration', str(registration_path)], stdin=subprocess.DEVNULL, stdout=stream,
            stderr=subprocess.STDOUT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
    save(root/(name+'_terminal.json'), dict(exit_code=result.returncode, automatic_retry=False,
         utc=datetime.now(timezone.utc).isoformat()))
    require(result.returncode == 0, name+' failed; no retry/failed-to-empty or successful-stage repeat')
    event(root, 'COMPLETE_'+name)


def run(registration_path):
    path = Path(registration_path).resolve(strict=True); reg = read(path)
    require(reg['schema'] == 'SUMMARY_TWO_VIEW_FORMAL_426_V14' and reg['role'] == 'SUMMARY_FINAL',
            'Explicit new production configuration only')
    root = Path(reg['root']).resolve(strict=True)
    require(root.is_relative_to(W) and root != W and path.parent == root, 'Independent exact production root')
    here = Path(__file__).resolve().parent
    for name, reference in reg['code'].items():
        require(Path(name).name == name and bound(reference) == here/name, 'Actual executed code binding')
    require(bound(reg['code']['run_summary_formal.py']) == Path(__file__).resolve(), 'Actual finite sequence code')
    admission = read(bound(reg['production_admission_ref']))
    require(admission['status'] == 'ADMIT_FIXED_SUMMARY_FINAL559_426'
            and admission['main_review_completed'] is True and admission['production_allowed'] is True
            and admission['allow_first_formal_inputs'] is True
            and admission['final_adapter_ref']['sha256'] == reg['final_adapter_ref']['sha256'],
            'Real external capability main-review admission must exist; code preparation is insufficient')
    bound(admission['external_evaluation_ref']); bound(reg['final_adapter_ref']); bound(reg['final_freeze_ref'])
    require(0 < reg['actual_resident_parameters'] <= reg['actual_pipeline_parameters'] <= 9_000_000_000,
            'Actual complete main/auxiliary model parameter count')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == str(reg['gpu_index']),
            'Parent launched with verified actual GPU index; CPU children only mask themselves')
    current = snapshot(); require(current['host'] == 'inspur-NP5570M5', 'Actual host')
    save(root/'formal_sequence_claim_14.json', dict(pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        command=Path('/proc/self/cmdline').read_bytes().replace(b'\0',b' ').decode(),
        registration_ref=ref(path), resources=current, automatic_retry=False,
        utc=datetime.now(timezone.utc).isoformat()))
    budget = reg['stage_resource_estimates']
    cpu(root, reg, 'formal_inputs_14', 'prepare_summary_formal.py', path,
        budget['input_disk_bytes'], budget['input_ram_bytes'])
    gate_path = root/'formal_inputs_14/input_acceptance.json'
    gate = read(gate_path)
    require(gate['status'] == 'PASS_ALL426_FIRST_SUMMARY_FORMAL_TWO_VIEW_INPUTS'
            and gate['sources'] == 426 and gate['windows'] == reg['expected_windows'],
            'Every actual new input must be accepted before first GPU')
    # CPU admission and GPU input lock are separate immutable registrations:
    # the second can only bind a first-input acceptance that actually exists.
    generated_reg = dict(reg, first_input_acceptance_ref=ref(gate_path),
        input_phase_registration_ref=ref(path), input_prepared_ref=gate['prepared_ref'])
    generation_reg_path = root/'generation_registration_14.json'; save(generation_reg_path, generated_reg)
    cutoff = datetime.fromisoformat(reg['new_model_start_cutoff_utc'].replace('Z','+00:00'))
    require(datetime.now(timezone.utc) < cutoff, 'No new formal model after the original20h cutoff')
    before = capacity(reg, 'formal_generation_14', budget['generation_disk_bytes'], budget['generation_ram_bytes'])
    require(not before['actual_resources']['gpu_apps'], 'External GPU work appeared; stop without touching it')
    job = reg['job_name']; resource_path = RUN/'controller'/(job+'.resource.json')
    ledger_path = W/'improvement_round1/gpu_ledger.jsonl'
    prior = [json.loads(line) for line in ledger_path.read_text().splitlines()
             if line.strip() and json.loads(line).get('name') == job]
    require(not resource_path.exists() and not prior, 'Existing named GPU job cannot be relaunched')
    wrapper = bound(reg['gpu_wrapper_ref'])
    command = [reg['python'], str(wrapper), '--name', job, '--max-seconds', str(reg['max_gpu_seconds']),
        '--planned-output-bytes', str(budget['generation_disk_bytes']), '--capacity-reason',
        'One admitted fixed-final559 model, complete522-or-registered source-summary inputs accepted. '
        'Source-serial original image patches, no decoder/processor/retraining/retries. '+json.dumps(before),
        '--queue-seconds', str(reg['queue_seconds']), '--', reg['python'], '-B',
        str(bound(reg['code']['summary_formal_generate.py'])), '--registration', str(generation_reg_path)]
    save(root/'formal_gpu_launch_14.json', dict(command=command, resources=before,
        input_acceptance_ref=ref(gate_path), registration_ref=ref(generation_reg_path),
        utc=datetime.now(timezone.utc).isoformat()))
    event(root, 'BEGIN_FORMAL_GPU', job=job)
    with (root/'formal_gpu_wrapper_14.log').open('xb') as stream:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(reg['gpu_index']), PYTHONDONTWRITEBYTECODE='1'))
    require(result.returncode == 0, 'Formal GPU wrapper failed; preserve raw successes, no retry')
    terminal = read(resource_path)
    ledger = [json.loads(line) for line in ledger_path.read_text().splitlines()
              if line.strip() and json.loads(line).get('name') == job]
    require(terminal['status'] == 'completed' and terminal['exit_code'] == 0 and ledger == [terminal],
            'Unique natural GPU terminal and ledger must exactly agree')
    event(root, 'COMPLETE_FORMAL_GPU', resource_ref=ref(resource_path))
    cpu(root, reg, 'formal_first_output_QA_14', 'summary_formal_output_qa.py', generation_reg_path,
        budget['output_QA_disk_bytes'], budget['output_QA_ram_bytes'])
    qa_path = Path(reg['output_directory'])/'first_independent_output_QA.json'
    qa = read(qa_path)
    require(qa['status'] == 'PASS_ALL426_FIRST_INDEPENDENT_SUMMARY_FORMAL_TOKEN_GRAMMAR_NATIVE_QA',
            'All independent output QA before packaging')
    package_reg = dict(generated_reg, formal_output_QA_ref=ref(qa_path))
    package_reg_path = root/'package_registration_14.json'; save(package_reg_path, package_reg)
    cpu(root, reg, 'formal_package_14', 'package_summary_formal.py', package_reg_path,
        budget['package_disk_bytes'], budget['package_ram_bytes'])
    package_path = root/'package_14/completion.json'
    complete = read(package_path)
    require(complete['status'] == 'NEW_SUMMARY_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN',
            'Actual full package completion required')
    save(root/'formal_sequence_completion_14.json', dict(status='COMPLETE_NEW_SUMMARY_ZIP_WINDOWS_DELIVERY_PENDING',
        zip=complete['zip'], package_completion_ref=ref(package_path), output_QA_ref=ref(qa_path),
        resource_ref=ref(resource_path), website_submitted=False, Windows_delivery_completed=False,
        official_improvement_asserted=False, utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--registration', required=True)
    args = parser.parse_args()
    try:
        run(args.registration)
    except BaseException as error:
        root = Path(args.registration).resolve().parent
        failure = root/'formal_sequence_failure_14.json'
        if root.is_dir() and not failure.exists():
            save(failure, dict(error=repr(error), traceback=traceback.format_exc(),
                successful_stages_preserved=True, automatic_retry=False, website_submitted=False,
                utc=datetime.now(timezone.utc).isoformat()))
        raise
