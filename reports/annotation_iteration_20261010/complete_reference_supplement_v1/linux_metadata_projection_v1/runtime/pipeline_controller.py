"""Single fresh execution; scientific failure never starts the 426 candidate.

All GPU work uses the existing shared-lock runner. This entry has no resume or
retry path: engineering failures preserve their real outputs and terminal costs.
"""
import argparse
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from common import HERE, admit, bound, read, require, save, sha, verify_lock

CAPS = {'train': 1200, 'evaluate': 2400, 'candidate': 7200}
TOTAL_CAP = 10800
STOP_RESERVE = 45  # Inside each frozen upper bound: sampling and owned teardown.


def utc():
    return datetime.now(timezone.utc).isoformat()


def accept_terminal(receipt, ledger_before, ledger_after, *, name, command,
                    runner_sha, policy_sha, phase, prior_current_cost):
    """Require one real append; preserve historical bytes, including failed work."""
    charged = receipt['charged_seconds']
    require(type(charged) in (int, float) and math.isfinite(charged) and charged > 0,
            'real terminal time must be finite and positive, including failures')
    require(ledger_after.startswith(ledger_before), 'historical GPU ledger prefix changed')
    suffix = ledger_after[len(ledger_before):]
    import json
    rows = [json.loads(line) for line in suffix.splitlines() if line.strip()]
    # Other shared jobs may append between our phases; accept only this job once.
    actual = [row for row in rows if row.get('name') == name]
    require(len(actual) == 1 and actual[0] == receipt, 'owned terminal receipt is not one unique appended ledger row')
    all_rows = [json.loads(line) for line in ledger_after.splitlines() if line.strip()]
    require(sum(row.get('name') == name for row in all_rows) == 1, 'duplicate job name in full ledger')
    require(receipt['name'] == name and receipt['command'] == command and
            receipt['runner_source_sha256'] == runner_sha and
            receipt['resource_policy_sha256'] == policy_sha and
            receipt['status'] in ('completed', 'failed') and receipt.get('finished_utc') and
            isinstance(receipt['exit_code'], int), 'terminal command/identity/status differs')
    return charged


def run_cpu(command, folder, name, expected_exit=(0,)):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
        TOKENIZERS_PARALLELISM='false', PYTHONNOUSERSITE='1')
    started = time.monotonic()
    with (folder/(name+'.log')).open('x', encoding='utf-8') as log:
        p = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log,
                           stderr=subprocess.STDOUT, env=env, cwd=HERE)
    save(folder/(name+'.execution.json'), dict(command=command, exit_code=p.returncode,
        wall_seconds=time.monotonic()-started, cuda_visible_devices='', utc=utc(),
        actual_process=True, result_acceptance_is_separate=True))
    require(p.returncode in expected_exit, 'CPU entry failed: '+name)
    return p.returncode


def run_gpu(contract, folder, phase, command, costs):
    c=contract['config'];run=Path(c['historical_run_root'])
    runner=run/'resource_unlimited_v1_20261007/gpu_run.py'
    policy=bound(c['resource_policy']);ledger=Path(c['gpu_ledger_path'])
    require(contract['lock']['files'].get(str(runner)) == sha(runner), 'resource runner absent from lock')
    require(contract['lock']['files'].get(str(policy)) == sha(policy), 'resource policy absent from lock')
    require(read(policy)['gpu_time_mode']=='UNLIMITED' and read(policy)['disk_usage_mode']=='ACTUAL_CAPACITY_ONLY',
            'existing resource allocation policy changed')
    name=c['pipeline_job_prefix']+'_'+phase
    prior=ledger.read_bytes()
    budget=min(CAPS[phase], math.floor(TOTAL_CAP-sum(costs.values())))-STOP_RESERVE
    require(budget>0, 'no current experiment time remains')
    inputs=Path(c['train_output_dir']).parent/'native_inputs_01'
    sizes=[p.stat().st_size for p in inputs.glob('*.input.json')]
    require(sizes, 'actual completed CPU input receipt sizes required')
    if phase=='train':
        estimate=(Path(c['initial_adapter_dir'])/'adapter_model.safetensors').stat().st_size*4 + sum(sizes)*2 + (8<<20)
    elif phase=='evaluate':
        estimate=max(sizes)*24*4 + (8<<20)
    else:
        from candidate_engine import estimate_output_bytes
        estimate=estimate_output_bytes(contract)
    require(type(estimate) is int and estimate>0, 'actual artifact output estimate required')
    call=[sys.executable,'-B',str(runner),'--name',name,'--max-seconds',str(budget),
          '--planned-output-bytes',str(estimate),'--capacity-reason',
          'Fixed silver final-only experiment; measured artifact estimate, live shared conflicts and actual capacity',
          '--queue-seconds','0','--']+command
    save(folder/(phase+'.launch_plan.json'),dict(command=command,runner_command=call,
         output_estimate_bytes=estimate,estimate_basis='Actual existing adapter/input receipts; candidate estimator binds actual source-field files and completed evaluation receipts',
         phase_upper_bound_seconds=CAPS[phase],runner_wall_seconds=budget,
         reserved_owned_teardown_seconds=STOP_RESERVE,current_charged_before=sum(costs.values()),
         frozen_total_upper_bound_seconds=TOTAL_CAP,utc=utc()))
    with (folder/(phase+'.runner.log')).open('x',encoding='utf-8') as log:
        result=subprocess.run(call,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=HERE)
    path=run/'controller'/(name+'.resource.json')
    # If resource admission failed before launch, there is no fictional charge.
    require(path.exists(), 'runner has no terminal: admission/engineering blocker, no automatic retry')
    terminal=read(path)
    charged=accept_terminal(terminal,prior,ledger.read_bytes(),name=name,command=command,
        runner_sha=sha(runner),policy_sha=sha(policy),phase=phase,prior_current_cost=sum(costs.values()))
    costs[phase]=charged
    save(folder/(phase+'.terminal_binding.json'),dict(utc=utc(),receipt=dict(path=str(path),sha256=sha(path)),
         real_charged_seconds=charged,current_experiment_charged_seconds=sum(costs.values()),
         historical_ledger_prefix_sha256=__import__('hashlib').sha256(prior).hexdigest(),
         ledger_after_sha256=sha(ledger),runner_exit_code=result.returncode,
         original_historical_costs_preserved=True))
    require(charged <= CAPS[phase] and sum(costs.values()) <= TOTAL_CAP,
            'frozen experiment GPU time upper bound exceeded; actual charge retained, do not advance')
    return terminal


def execute(contract):
    c=contract['config'];root=Path(c['train_output_dir']).parent
    require(Path(sys.executable).resolve()==Path(c['execution_python']).resolve(), 'use registered isolated runtime')
    for phase in CAPS:
        require(not Path(c[phase+'_output_dir']).exists(), 'existing phase must never be rerun')
    out=root/'pipeline_01';out.mkdir(exist_ok=False)
    report=dict(status='RUNNING_FRESH_FIXED_SILVER_PIPELINE',utc=utc(),lock_sha256=contract['lock_sha'],
                config_sha256=contract['config_sha'],costs={},official_upload=False,production_replaced=False)
    costs=report['costs']
    common=['--config',str(Path(contract['config_path']).resolve()),'--lock',str(Path(contract['lock_path']).resolve()),
            '--expected-lock',contract['lock_sha']]
    def cmd(name,tail=()): return [sys.executable,'-B',str(HERE/(name+'.py'))]+common+list(tail)
    try:
        # Reject candidate input/dependency defects before spending training GPU
        # time. This separate process does only actual static byte/clock checks.
        static = root/'candidate_static_input_acceptance.json'
        run_cpu(cmd('candidate_static_preflight',['--output',str(static)]),out,'candidate_static_cpu')
        sr=read(static)
        require(sr['status']=='PASS_ACTUAL_CPU_STATIC_FIXED_426_521_CANDIDATE_INPUT_BINDINGS' and
                sr['config_sha256']==contract['config_sha'] and sr['lock_sha256']==contract['lock_sha'] and
                sr['records']==426 and sr['planned_temporal_calls']==521 and
                sr['changed_windows']==116 and sr['unchanged_windows']==405 and
                sr['original_spatial_anchor_rows']==31295 and
                sr['candidate_contract']==c['candidate_contract'] and
                all(sr[k] is False for k in ('model_loaded','processor_loaded','native_decoder_called',
                    'candidate_output_created','quality_claim','training_started')) and
                sr['new_model_calls']==sr['new_native_decodes']==sr['processor_calls']==sr['new_optimizer_updates']==0,
                'actual static candidate input acceptance differs')
        report['candidate_static_admission']=dict(path=str(static),sha256=sha(static))
        pre=root/'native_inputs_01'
        run_cpu(cmd('preflight_native_inputs',['--output-dir',str(pre)]),out,'native_cpu')
        pr=pre/'receipt.json'
        from train import validate_preflight
        validate_preflight(contract,pr,sha(pr))
        terminal=run_gpu(contract,out,'train',cmd('train',['--preflight-receipt',str(pr),
                  '--expected-preflight-receipt',sha(pr)]),costs)
        require(terminal['status']=='completed' and terminal['exit_code']==0 and terminal['stop_reason'] is None,
                'training did not naturally complete')
        tr=Path(c['train_output_dir'])/'training_receipt.json'
        from evaluate import validate_final
        final,training=validate_final(contract,tr,sha(tr))
        train_args=['--final-receipt',str(tr),'--expected-final-receipt',sha(tr)]
        terminal=run_gpu(contract,out,'evaluate',cmd('evaluate',train_args),costs)
        require(terminal['stop_reason'] is None and terminal['exit_code'] in (0,5), 'evaluation failed engineering/time/resource checks')
        ev=Path(c['evaluate_output_dir'])/'evaluation_receipt.json'
        q=ev.parent/'independent_quality_receipt.json'
        run_cpu(cmd('verify_evaluation',train_args+['--evaluation-receipt',str(ev),
            '--expected-evaluation-receipt',sha(ev),'--output',str(q)]),out,'independent_quality',(0,5))
        quality=read(q)
        require(quality['status']=='PASS_INDEPENDENT_CPU_FINAL_ONLY_EVALUATION_RECONSTRUCTION' and
                quality['model_calls_reconstructed']==24 and quality['new_model_calls']==0 and
                quality['final_adapter_sha256']==training['final_adapter_sha256'], 'independent quality receipt differs')
        if not quality['quality_gate_passed']:
            report.update(status='STOP_SCIENTIFIC_QUALITY_NO426_NO_RETUNING',quality_receipt=dict(path=str(q),sha256=sha(q)),
                          candidate_started=False,final_adapter_retained=str(final))
            save(out/'completion.json',report)
            return 5
        require(terminal['status']=='completed' and terminal['exit_code']==0, 'quality PASS but resource terminal differs')
        candidate_args=train_args+['--quality-receipt',str(q),'--expected-quality-receipt',sha(q)]
        terminal=run_gpu(contract,out,'candidate',cmd('candidate_engine',candidate_args),costs)
        require(terminal['status']=='completed' and terminal['exit_code']==0 and terminal['stop_reason'] is None,
                'candidate did not naturally complete')
        replay=Path(c['candidate_output_dir'])/'independent_temporal_replay.json'
        run_cpu(cmd('candidate_replay',candidate_args+['--output',str(replay)]),out,'independent_candidate_cpu')
        run_cpu(cmd('candidate_package',candidate_args+['--replay-receipt',str(replay),
                '--expected-replay-receipt',sha(replay)]),out,'candidate_package_cpu')
        verify_lock(contract['lock_path'],contract['lock_sha'])
        # The package entry owns strict validation; bind its actual final receipt.
        completion=Path(c['candidate_output_dir'])/'completion.json'
        result=read(completion)
        require(result['status']=='PASS_COMPLETE_FIXED_SILVER_426_CANDIDATE_ON_LINUX' and
                result['records']==426 and result['fresh_temporal_model_calls']==521 and
                result['final_adapter_sha256']==training['final_adapter_sha256'] and
                result['all_11_strict_checks_passed'] is True, 'complete independent package acceptance absent')
        zip_path=Path(result['candidate']).resolve(strict=True)
        require(zip_path.parent==Path(c['candidate_output_dir']).resolve() and
                zip_path.stat().st_size==result['zip_bytes'] and sha(zip_path)==result['zip_sha256'], 'final ZIP actual bytes differ')
        report.update(status='PASS_FRESH_FIXED_SILVER_PIPELINE_COMPLETE_ZIP_ON_LINUX',
            candidate=dict(path=str(zip_path),sha256=sha(zip_path),bytes=zip_path.stat().st_size),
            package_completion=dict(path=str(completion),sha256=sha(completion)),quality_receipt=dict(path=str(q),sha256=sha(q)),
            official_score=None,scientific_scope='FINITE_SILVER_DIAGNOSTIC_NOT_OFFICIAL_SCORE')
        save(out/'completion.json',report)
        return 0
    except BaseException as exc:
        report.update(status='STOP_PIPELINE_ENGINEERING_PRESERVE_ALL_SUCCESS_AND_COSTS',
            failure_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc(),
            failed_call_not_converted_to_empty=True,automatic_retry=False)
        if not (out/'completion.json').exists():save(out/'completion.json',report)
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','lock','expected-lock'):p.add_argument('--'+name,required=True)
    a=p.parse_args();contract=admit(a.config,a.lock,a.expected_lock,'train')
    # The new runtime must be fully frozen before any phase or model starts.
    for name in ('candidate_engine.py','candidate_replay.py','candidate_package.py','candidate_static_preflight.py'):
        require((HERE/name).exists() and contract['lock']['files'].get(str(HERE/name))==sha(HERE/name), 'candidate implementation incomplete')
    return execute(contract)

if __name__=='__main__':raise SystemExit(main())
