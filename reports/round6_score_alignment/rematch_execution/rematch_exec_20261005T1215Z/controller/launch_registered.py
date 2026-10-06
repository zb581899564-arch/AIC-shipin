"""Launch one explicit frozen owned task; no external tasks or scheduler changes."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
PYTHON='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
CTRL=RUN/'controller'

def spec(which):
    if which in ['a_nontest','a_nontest_02','a_nontest_03','a_nontest_04']:
        attempt=which.rsplit('_',1)[-1] if which[-2:].isdigit() else '01'
        return ['--name','rematch_a_nontest_e2e_'+attempt,'--max-seconds','1800',
            '--planned-output-bytes','268435456','--capacity-reason',
            '8-source new entry regression: JSONL logs and ZIP, no media/model duplication',
            '--queue-seconds','600','--',PYTHON,'-B',str(CTRL/'run_a_e2e.py'),'--attempt',attempt]
    if which in ('c_probe', 'c_probe_02'):
        attempt='02' if which=='c_probe_02' else '01'
        state=json.loads((CTRL/'model_download_v2_status.json').read_text())
        preflight=json.loads((RUN/'dense_head/processor_preflight_02/processor_preflight_report.json').read_text())
        if state['status']!='COMPLETE_HASH_VERIFIED' or not preflight['status'].startswith('PASS'):
            raise RuntimeError('weights/processor hard gates not ready; no GPU job launched')
        return ['--name','rematch_c_engineering_probe_'+attempt,'--max-seconds','1800',
            '--planned-output-bytes','268435456','--capacity-reason',
            '8B rank16 synthetic probe: ~64MB adapter and head plus JSON evidence, no base checkpoint copy',
            '--queue-seconds','1800','--',PYTHON,'-B',str(RUN/'dense_head/probe_8b.py'),
            '--model-dir',str(RUN/'models/Qwen3-VL-8B-Instruct'),
            '--model-receipt',str(CTRL/'model_download_v2_status.json'),
            '--out-dir',str(RUN/('dense_head/probe8b_'+attempt)),'--engineering-only','--updates','3']
    if which=='c_cost_32s_01':
        admission=json.loads((CTRL/'c_cost_32s_01.admission.json').read_text())
        config_path=CTRL/'c_cost_32s_01.config.json'
        if admission.get('config_sha256')!=hashlib.sha256(config_path.read_bytes()).hexdigest():
            raise RuntimeError('32s cost configuration changed after admission')
        if admission.get('cost_probe_admitted') is not True or admission.get('formal_c_bce_admitted') is not False:
            raise RuntimeError('32s engineering cost probe scope not admitted')
        return ['--name','rematch_c_cost_32s_01','--max-seconds','1800',
            '--planned-output-bytes','134217728','--capacity-reason',
            'one fixed non-test native PTS index and three synthetic-label 32s updates; no new model or media copy',
            '--queue-seconds','600','--',PYTHON,'-B',str(RUN/'dense_head_cost_v1/cost_probe.py'),
            '--config',str(config_path),'--admission',str(CTRL/'c_cost_32s_01.admission.json')]
    if which=='a_rematch_temporal_01':
        admission=json.loads((CTRL/'a_rematch_temporal_01.admission.json').read_text())
        if admission.get('authorized') is not True or admission.get('scope')!='A_TEMPORAL_SELECT_SHOTS_ANCHORS_ONLY':
            raise RuntimeError('A temporal/scheduling evidence admission missing')
        return ['--name','rematch_a_temporal_01','--max-seconds','7200',
            '--planned-output-bytes','536870912','--capacity-reason',admission['capacity_reason'],
            '--queue-seconds','1800','--',PYTHON,'-B',str(CTRL/'run_a_rematch_temporal.py')]
    raise ValueError('unknown registered task')

if __name__=='__main__':
    which=sys.argv[1]
    command=[PYTHON,'-B','-u',str(CTRL/'gpu_run.py'),*spec(which)]
    with (CTRL/(which+'.launcher.log')).open('x') as log:
        child=subprocess.Popen(command,cwd=RUN,stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt={'task':which,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'pid':child.pid,'command':command,'launcher_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    with (CTRL/(which+'.launch.json')).open('x') as out:
        json.dump(receipt,out,indent=2)
        out.write('\n')
    print(json.dumps(receipt),flush=True)
