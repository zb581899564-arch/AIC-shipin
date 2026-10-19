"""Unique engineering-only workflow; no offline effect screening or production."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from width_common import Context, require, read, save, sha, BACKBONE


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main(root):
    ctx = Context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '0', 'Physical parent GPU index')
    save(root / 'chain_started.json', dict(pid=os.getpid(), utc=utc(), argv=sys.argv,
         start_ticks=Path('/proc/self/stat').read_text().split()[21], parent_cuda='0'))

    def cpu(script, *extra):
        env = os.environ.copy()
        env.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
        subprocess.run([sys.executable, str(root / 'code' / script), '--root', str(root), *extra],
                       env=env, check=True)

    cpu('prepare.py', '--stage', 'prepare')
    cpu('prepare.py', '--stage', 'qa')
    accepted = ctx.checked_stage('cpu_acceptance', 'PASS_602_NEW_PURPOSE_JPEG_RGB_PREFIX_INPUTS')
    qa = ctx.checked_stage('input_QA', 'PASS_602_FIRST_INDEPENDENT_SAVED_RGB_PROCESSOR_BIT_QA')
    require(qa['cpu_acceptance_sha256'] == sha(root / 'cpu_acceptance.json'), 'All first input QA precedes GPU')
    save(root / 'input_source_lock.json', dict(status='FROZEN_ALL602_FIRST_REAL_CPU_INPUTS',
         protocol_sha256=sha(root / 'protocol.json'), source_manifest_sha256=sha(root / 'source_manifest.json'),
         cpu_acceptance_sha256=sha(root / 'cpu_acceptance.json'), input_QA_sha256=sha(root / 'input_QA.json'),
         code={str(p): sha(p) for p in (root / 'code').glob('*.py')},
         inputs=[dict(id=s['id'], tensor_path=s['tensor_path'], tensor_sha256=s['tensor_sha256'],
                      RGB_path=s['RGB_path'], RGB_file_sha256=s['RGB_file_sha256']) for s in accepted['sources']],
         new_quality_gate=False))
    name = 'gnmc602_base_width_prefix_features_20261016_v1'
    wrapper = ctx.run / 'resource_unlimited_v1_20261007/gpu_run.py'
    command = [sys.executable, str(wrapper), '--name', name, '--max-seconds', '1800',
               '--planned-output-bytes', str(64 * 1024 * 1024), '--capacity-reason',
               '602 first single-image BASE width-prefix features; inherited model, 64MiB outputs; no full checkpoint or external task interruption',
               '--queue-seconds', '900', '--', sys.executable, str(root / 'code/infer.py'),
               '--root', str(root), '--stage', 'infer']
    save(root / 'GPU_launch.json', dict(utc=utc(), name=name, command=command,
         input_source_lock_sha256=sha(root / 'input_source_lock.json')))
    subprocess.run(command, check=True)
    resource = read(ctx.run / 'controller' / (name + '.resource.json'))
    ledger = ctx.run.parents[2] / 'improvement_round1/gpu_ledger.jsonl'
    # RUN is WORK/round6_score_alignment/rematch_execution/rematch_exec_*.
    require(ledger == Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl'),
            'Exact shared terminal ledger path')
    matching = [json.loads(l) for l in ledger.read_text().splitlines()
                if json.loads(l).get('name') == name and json.loads(l).get('status') in
                ('completed', 'failed', 'timeout', 'terminated')]
    require(resource.get('status') == 'completed' and resource.get('exit_code') == 0 and
            len(matching) == 1 and matching[0] == resource, 'Unique natural shared-GPU completion')
    save(root / 'GPU_resource.json', resource)
    cpu('infer.py', '--stage', 'qa')
    cpu('fit.py')
    done = read(root / 'completion.json')
    require(done['status'] == 'PASS_ENGINEERING_FROZEN_HEAD_ONLINE_EFFECT_UNKNOWN' and
            done['head_optimizer_updates'] == 200 and done['backbone_optimizer_updates'] == 0,
            'One final-only602 CPU head, no proxy quality gate')
    save(root / 'chain_completion.json', dict(status=done['status'], utc=utc(),
         completion_sha256=sha(root / 'completion.json'), resource_sha256=sha(root / 'GPU_resource.json'),
         first_feature_forwards=602, new_head_updates=200, production_admitted=False,
         new_submission_ZIPs=0, online_effect='UNKNOWN'))


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
