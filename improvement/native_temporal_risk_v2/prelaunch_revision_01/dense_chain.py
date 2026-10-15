"""One prospective production attempt, with separate prepare/GPU/replay/package steps."""
import datetime as dt
import os
import subprocess
import sys
import traceback
from pathlib import Path
import dense_runtime as r

OUT = r.HERE/'chain_01'
NAME = 'dense128_native_rematch521_20261012_v2'
PILOT_ROOT = r.RUN/'overnight_risk_20261012_v1/dense128_v1'
CUTOFF = dt.datetime(2026, 10, 12, 0, 0, tzinfo=dt.timezone.utc)


def state(stage, **fields):
    value = dict(stage=stage, utc=r.utc(), **fields)
    temp = OUT/'chain_state.tmp.json'
    temp.write_text(__import__('json').dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(OUT/'chain_state.json')
    print(__import__('json').dumps(value, ensure_ascii=False), flush=True)


def child(name, command, gpu=False):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONNOUSERSITE='1',
               HF_HOME=str(r.RUN/'cache/hf'), XDG_CACHE_HOME=str(r.RUN/'cache'),
               TMPDIR=str(r.RUN/'tmp'), TORCH_HOME=str(r.RUN/'cache/torch'))
    if not gpu:
        env['CUDA_VISIBLE_DEVICES'] = ''
    with (OUT/(name+'.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=r.HERE, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT)
        state(name+'_RUNNING', command=command, child_pid=process.pid)
        result = process.wait()
    r.require(result == 0, name+' failed with exit '+str(result)+'; preserve raw and do not retry this attempt')
    state(name+'_COMPLETED', exit_code=result)


def main():
    r.registration('rematch')
    OUT.mkdir(exist_ok=False)
    try:
        r.require(subprocess.check_output(['hostname'], text=True).strip() == 'inspur-NP5570M5', 'wrong host')
        registration = r.read(r.HERE/'production_registration.json')
        r.require(registration['chain_script_sha256']==r.sha(r.HERE/'dense_chain.py') and
                  registration['engineering_protocol_sha256']==r.sha(r.HERE/'ENGINEERING_V2.json'),
                  'prospective recovery entry or engineering contract changed')
        engineering=r.read(r.HERE/'ENGINEERING_V2.json')
        r.require(engineering['schema']=='DENSE128_ODD_FRAME_PADDING_ENGINEERING_RECOVERY_V2' and
                  engineering['new_production_calls']==521 and engineering['prior_production_calls']==0 and
                  engineering['old_successful_cpu_proofs_reused']==314 and
                  engineering['max_gpu_job_seconds']==21600 and
                  engineering['native_sampling_changed'] is False and engineering['pixel_budget_relaxed'] is False,
                  'engineering recovery changed the scientific input contract')
        for path,expected in engineering['implementation_files'].items():
            r.require(r.sha(path)==expected, 'registered v2 implementation changed: '+path)
        diagnostic = Path(registration['partial_reference_diagnostic_path'])
        r.require(r.sha(diagnostic) == registration['partial_reference_diagnostic_sha256'] and
                  r.read(diagnostic)['predeclared_obviously_bad'] is False, 'fixed dev obvious-loss diagnosis differs')
        best_lock_path = r.RUN/'balanced_two_window_risk_v3/source_lock.json'
        r.require(r.sha(best_lock_path)=='66668c77abf824e95892989f507a7ccd8ffce234da45ed3af2b0ac324322f490',
                  'accepted original best lock changed')
        best = r.read(best_lock_path)
        files = dict(best['files'])
        pilot_lock_path = PILOT_ROOT/'source_lock.json'
        r.require(r.sha(pilot_lock_path) == '4cff45a470f3e9bdc8a63035db18f0c65f23ed5c11d27a01622f946a6421aabe',
                  'original six-call pilot source lock changed')
        pilot = r.read(pilot_lock_path)
        for path, expected in pilot['files'].items():
            r.require(path not in files or files[path] == expected, 'inherited immutable source bindings conflict')
            files[path] = expected
        state('VERIFY_INHERITED_ACCEPTED_SOURCES', files=len(files))
        for path, expected in files.items():
            r.require(r.sha(path) == expected, 'accepted historical source changed: '+path)
        for path in [best_lock_path, pilot_lock_path, r.HERE/'dense_production.py',
                     r.HERE/'dense_chain.py', r.HERE/'production_registration.json', diagnostic,
                     PILOT_ROOT/'pilot_replay_bundle.json', PILOT_ROOT/'pilot_01/replay_01/completion.json',
                     r.HERE/'dense_context_package.py', r.HERE/'DENSE_CONTEXT025_PROTOCOL.json',
                     r.HERE/'cpu_transfer.py', r.HERE/'CPU_TRANSFER314.json', r.HERE/'ENGINEERING_V2.json',
                     r.HERE/'test_dense_video.py', r.HERE/'target_cpu_01/completion.json',
                     r.HERE.parent/'DENSE128_PROTOCOL.json']:
            files[str(path)] = r.sha(path)
        for name in ('dense_runtime.py','dense_video.py','dense_pilot.py','dense_replay.py','native_grammar.py','original_grammar.py'):
            files[str(r.HERE/name)] = r.sha(r.HERE/name)
        r.require(dt.datetime.now(dt.timezone.utc) < CUTOFF, 'morning cutoff: no new production attempt')
        child('PRODUCTION_CPU_PREPARE', [sys.executable, '-B', str(r.HERE/'dense_production.py'), 'prepare'])
        from dense_production import prepared
        acceptance, extra = prepared()
        for path in extra:
            actual = r.sha(path)
            r.require(str(path) not in files or files[str(path)] == actual, 'prepared source conflicts with accepted historical bytes')
            files[str(path)] = actual
        r.save(r.HERE/'production_source_lock.json', dict(schema='DENSE128_FULL_PRODUCTION_ACTUAL_INPUTS_V2_PARTIAL_CPU_RECOVERY',
               utc=r.utc(), files=files, original_best_lock_sha256=r.sha(best_lock_path),
               original_pilot_lock_sha256=r.sha(pilot_lock_path),recovery=acceptance['recovery'],
               scientific_quality_pass=False, sources=426, windows=521, new_optimizer_updates=0))
        lock = r.verify_lock('rematch', extra)
        state('PRODUCTION_INPUTS_FROZEN', windows=521, files=len(files), source_lock_sha256=lock['sha256'])
        r.require(dt.datetime.now(dt.timezone.utc) < CUTOFF, 'morning cutoff before new GPU job')
        command = [sys.executable, '-B', str(r.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
                   '--name', NAME, '--max-seconds', '21600', '--planned-output-bytes', '536870912',
                   '--capacity-reason', 'Original B dense128 pilot measured21184MiB, production uses identical fixed pixel/token limits; actual521CPU inputs accepted; dynamic no-external-compute lock and physical output capacity, no fixed resource gate',
                   '--', sys.executable, '-B', str(r.HERE/'dense_production.py'), 'run']
        child('PRODUCTION_GPU_WRAPPER', command, gpu=True)
        receipt_path = r.RUN/('controller/'+NAME+'.resource.json')
        receipt = r.read(receipt_path)
        matching = [x for x in r.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl') if x['name'] == NAME]
        r.require(matching == [receipt] and receipt['status'] == 'completed' and receipt['exit_code'] == 0,
                  'real unique GPU terminal and ledger do not agree')
        child('PRODUCTION_CPU_REPLAY', [sys.executable, '-B', str(r.HERE/'dense_replay.py'), 'rematch'])
        child('PRODUCTION_PACKAGE', [sys.executable, '-B', str(r.HERE/'dense_production.py'), 'assemble'])
        completion_path = r.HERE/'rematch_01/package_01/completion.json'
        completion = r.read(completion_path)
        r.require(completion['status'] == 'PASS_COMPLETE_NEW_DENSE128_USER_AUTHORIZED_RISK_ZIP' and
                  completion['video_records'] == 426 and completion['windows'] == 521 and
                  r.sha(completion['candidate']) == completion['zip_sha256'], 'full new artifact is not accepted')
        r.save(OUT/'completion.json', dict(status='PASS_NEW_DENSE128_ZIP_READY_FOR_SMALL_DOWNLOAD', utc=r.utc(),
               artifact=completion, package_completion_sha256=r.sha(completion_path),
               unique_resource_terminal_sha256=r.sha(receipt_path), charged_seconds=receipt['charged_seconds'],
               new_optimizer_updates=0, official_score=None, scientific_quality_pass=False))
        state('PASS_NEW_DENSE128_ZIP_READY_FOR_SMALL_DOWNLOAD', candidate=completion['candidate'],
              zip_bytes=completion['zip_bytes'], zip_sha256=completion['zip_sha256'])
        child('PRODUCTION_CONTEXT025_PACKAGE', [sys.executable, '-B', str(r.HERE/'dense_context_package.py')])
        context_path = r.HERE/'rematch_01/context025_package_01/completion.json'
        context = r.read(context_path)
        r.require(context['status'] == 'PASS_COMPLETE_DENSE128_CONTEXT025_RISK_ZIP' and
                  r.sha(context['candidate']) == context['zip_sha256'], 'context artifact is not accepted')
        r.save(OUT/'context_completion.json', dict(status='PASS_DENSE128_CONTEXT025_READY_FOR_SMALL_DOWNLOAD',
               utc=r.utc(), artifact=context, completion_sha256=r.sha(context_path)))
        state('PASS_TWO_DENSE128_ZIPS_READY_FOR_SMALL_DOWNLOAD',
              candidates=[completion['candidate'],context['candidate']],
              new_actual_model_calls=521, new_optimizer_updates=0, scientific_quality_pass=False)
    except BaseException as exc:
        state('STOP_CHAIN_FAILURE_PRESERVE_NO_SAME_ATTEMPT_RETRY', error=str(exc), traceback=traceback.format_exc())
        r.failure(OUT, exc)
        raise


if __name__ == '__main__':
    main()
