"""First bounded parallel-policy control/micro job and real remaining-cost gate."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'parallel_cost107'
CODE = Path(__file__).parent
TEMP = Path('/dev/shm/aic_T_parallel_first107')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_parallel_queries_original50_first_gradient_20261023_v107'


def run(script, phase, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '750',
            '--planned-output-bytes', '8000000', '--capacity-reason',
            'New fixed parallel native-query method:50originalTIME controls plus1first full-prefill gradient; all417text/loss bindings CPU accepted, no old65token generation or failed native98 training reused. Preserve gradient/RNG and gate all216remaining+150dev within new3600phase/5400profile and original43200Goal.',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '', OMP_NUM_THREADS='2',
                     MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = process.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First parallel policy stage failed; preserve successful controls/micro: ' + phase)


def admission():
    protocol = read(CODE / 'parallel_protocol105.json')
    inputs = read(ROOT / 'parallel_inputs106/completion.json')
    prior = read(ROOT / 'native_next_two104/completion.json')
    if (inputs['state'] != 'FIRST_ALL417_PARALLEL_QUERY_TEXT_AND_LOSS_ADOPTION_CPU_PASS'
            or protocol['Goal_GPU_seconds_already_settled'] != prior['all_goal_GPU_seconds']
            or protocol['Goal_GPU_seconds_already_settled'] + protocol['profile_GPU_seconds_max_all_failures'] > 43200):
        raise ValueError('Current full inputs/source/budget binding differs')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Actual host/CONTROL5 guard changed; do not signal it')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if (apps.strip() or shutil.disk_usage(ROOT).free < 8000000
            or shutil.disk_usage(TEMP.parent).free < 150000000 or TEMP.exists()):
        raise RuntimeError('Specific first-query artifacts conflict with current capacity/external GPU')
    rules = ROOT / 'official_rules23_before_native101/completion.json'
    if read(rules)['state'] != 'CURRENT23_OFFICIAL_HTML_AND_NOTICE_LINKS_REVIEWED':
        raise ValueError('Current23 official scope review absent')
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'parallel_protocol105.json'),
        current_official=identity(rules), original_native98_cost_STOP=identity(
            ROOT / 'native_next_two104/completion.json'), no_old_calls_repeated=True,
        first_original_parallel_controls=50, first_actual_target_forward_backward=1,
        optimizer_updates=0, whole_source_fit=9, all_original_reviewers=86,
        first_GPU_limit_seconds=750, profile_max_seconds=5400, combined_native_max_seconds=3600,
        root_artifact_upper_bytes=8000000, tmpfs_artifact_upper_bytes=150000000,
        actual_GPU_apps=apps, CPU=subprocess.check_output(
            ['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    names = ['parallel_cost107.py', 'parallel_cost107_gpu.py', 'parallel_cost107_cpu.py',
        'parallel_forward107.py', 'parallel_training107.py', 'parallel_teacher107_cpu.py',
        'parallel_audit107.py', 'parallel_input106.py', 'parallel_query105.py', 'parallel_protocol105.json',
        'native_prepared103.py', 'native_actor98.py', 'native_codec98.py', 'native_state100.py',
        'native_render100.py', 'native_training_data99.py', 'native_input99.py', 'native_next_two104_cpu.py',
        'actor_roles33.py', 'joint_rollout47.py', 'joint_checkpoint44.py', 'summary_recovery88.py',
        'native_sets.py', 'joint_data44.py', 'development_data46.py', 't_io.py', 't_runtime39.py']
    wrapper = identity(WRAPPER)
    if wrapper['sha256'] != '9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec':
        raise ValueError('Existing unique shared GPU wrapper identity differs')
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        actual_inputs=identity(ROOT / 'parallel_inputs106/completion.json'),
        actual_source_loss=inputs['loss_bindings'], protocol=identity(CODE / 'parallel_protocol105.json'),
        query_CPU=identity(ROOT / 'parallel_contract105/completion.json'), wrapper=wrapper,
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies']))
    return protocol


def main():
    OUT.mkdir()
    protocol = admission()
    run('parallel_cost107_gpu.py', 'GPU', gpu=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip()]
    if (resource['status'] != 'completed' or resource['exit_code'] != 0
            or [row for row in ledger if row.get('name') == JOB] != [resource]):
        raise ValueError('First parallel control/micro natural terminal or unique ledger differs')
    run('parallel_cost107_cpu.py', 'first_CPU')
    cpu = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=cpu['state'], GPU_seconds=resource['charged_seconds'],
        all_goal_GPU_seconds=protocol['Goal_GPU_seconds_already_settled'] + resource['charged_seconds'],
        profile_GPU_seconds=resource['charged_seconds'], remaining_native3600_seconds=cpu['remaining_native3600_seconds'],
        first_CPU=identity(OUT / 'CPU_completion.json'), actual_outputs=identity(OUT / 'GPU_completion.json'),
        actual_initial_control_calls=50, actual_training_forward_backward=1, actual_optimizer_updates=0,
        remaining216_and150dev_cost_admitted=cpu['remaining216_and150dev_cost_admitted'],
        no_quality_or_confirmation_or_production_admission=True,
        next='If costPASS, exact first-micro gradient/RNG/initialactor+Adam restore, fixed remaining216 training/five updates then150dev; never repeat107controls or firstTF. If costSTOP stop this new fixed parallel profile.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_all_successful_raw_controls_gradient_RNG_and_fees=True,
                no_automatic_repeat_or_failure_to_empty=True))
        raise
