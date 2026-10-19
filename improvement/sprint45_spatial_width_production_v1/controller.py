"""One registered native16 feature/readout chain, no effect evaluation."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from prod_common import Context, read, save, sha, require


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main(root):
    ctx = Context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '0', 'Actual parent GPU0')
    save(root / 'chain_started.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split()[21],
         utc=utc(), argv=sys.argv, parent_cuda='0'))

    def cpu(name, phase):
        env = os.environ.copy()
        env.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
        subprocess.run([sys.executable, str(root / 'code' / name), '--root', str(root),
                        '--phase', phase], env=env, check=True)

    cpu('prepare.py', 'prepare')
    cpu('prepare.py', 'qa')
    unique = ctx.stage('unique_inputs', 'PASS_ALL_NATIVE16_EFFECTIVE_INPUTS_QA_AND_EXACT_DEDUP')
    lock = ctx.stage('freeze_source_lock', 'FROZEN_ALL_WIDTH_EFFECTIVE_INPUTS_BEFORE_GPU')
    require(lock['unique_inputs_sha256'] == sha(root / 'unique_inputs.json') and
            unique['training_overlap_count'] == 0, 'All new actual inputs/overlap checks before GPU')
    name = 'sprint45_native16_width_prefix_20261016_v1'
    command = [sys.executable, str(ctx.run / 'resource_unlimited_v1_20261007/gpu_run.py'),
               '--name', name, '--max-seconds', '5400', '--planned-output-bytes', str(512 << 20),
               '--capacity-reason', 'Same existing8B native16 single-image width-prefix unique inputs; 512MiB feature/provenance estimate, no new image cache or full checkpoint',
               '--queue-seconds', '7200', '--', sys.executable, str(root / 'code/features.py'),
               '--root', str(root), '--phase', 'infer']
    save(root / 'GPU_launch.json', dict(name=name, command=command, utc=utc(),
         actual_unique_inputs=unique['unique_inputs'], actual_new_unique_forwards=unique['new_unique_forwards'],
         freeze_source_lock_sha256=sha(root / 'freeze_source_lock.json')))
    subprocess.run(command, check=True)
    resource = read(ctx.run / 'controller' / (name + '.resource.json'))
    ledger = Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    records = [json.loads(l) for l in ledger.read_text().splitlines()]
    terminal = [r for r in records if r.get('name') == name and r.get('status') in
                ('completed', 'failed', 'timeout', 'terminated')]
    require(resource.get('status') == 'completed' and resource.get('exit_code') == 0 and
            len(terminal) == 1 and terminal[0] == resource, 'Exactly one matching natural GPU terminal')
    save(root / 'GPU_resource.json', resource)
    save(root / 'unique_resource_verified.json', dict(unique_terminal_count=1,
         resource_sha256=sha(root / 'GPU_resource.json'), name=name))
    cpu('features.py', 'qa')
    cpu('widths.py', 'apply')
    width = ctx.stage('width_by_video', 'PASS_FROZEN_WIDTH_HEAD_NATIVE16_SAMPLE_READOUT')
    require(width['new_head_updates'] == 0, 'Production uses exactly the frozen602 head')
    save(root / 'chain_completion.json', dict(status='PASS_NATIVE16_WIDTH_MODEL_OUTPUTS_READY_FOR_ENGINEERING_PACK',
         utc=utc(), width_by_video_sha256=sha(root / 'width_by_video.json'),
         GPU_resource_sha256=sha(root / 'GPU_resource.json'),
         unique_terminal_count=1, online_effect='UNKNOWN', offline_effect_validation=False,
         current_baseline_frames_must_be_preserved=True, new_submission_ZIPs=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    root = Path(parser.parse_args().root)
    try:
        main(root)
    except Exception as error:
        import traceback
        if not (root / 'chain_failure.json').exists():
            save(root / 'chain_failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
                 utc=utc(), preserve_success=True, no_automatic_restart=True))
        raise
