"""Recover bandwidth, then compare only if class identities actually change."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.append('/home/inspur/aic_video_work/sprint_audio_events_20261021_v1/code')
import json
import os
import subprocess
import traceback
import common
BASE = common.ROOT
common.ROOT = BASE/'native32k10'
from common import ROOT, WORK, PY, WRAPPER, LEDGER, read, write, checked, reference
from controller import resources
ENTRY = Path(__file__).parent/'profile_entry10.py'


def phase(name, cpu=True):
    command = [str(PY), '-u', '-B', str(ENTRY), name]
    if not cpu:
        count = read(ROOT/'model_cpu_acceptance.json')['actual_parameters']
        estimate = count*4+32000*30*4*256 if name == 'events' else 8782459120*2+65536*4096*2*8+2*1024**3
        job = 'pann_native32k8_profile_20261021_v10' if name == 'events' else 'pann_native32k_TIME16_20261021_v10'
        admission = resources(job, estimate)
        command = [str(PY), '-B', str(WRAPPER), '--name', job, '--max-seconds', '180' if name == 'events' else '1800',
            '--planned-output-bytes', '134217728', '--capacity-reason', json.dumps(admission), '--queue-seconds', '0', '--']+command
    with (ROOT/(name+'.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='' if cpu else '0',
            OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2'), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        write(ROOT/(name+'_launch.json'), dict(pid=process.pid, argv=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code = process.wait()
    write(ROOT/(name+'_terminal.json'), dict(exit_code=code))
    if code:
        raise ValueError('First native-bandwidth phase failed: '+name)
    if not cpu:
        record = read(WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'/(job+'.resource.json'))
        matches = [row for row in map(json.loads, LEDGER.read_text().splitlines()) if row.get('name') == job]
        if record['status'] != 'completed' or record['exit_code'] != 0 or matches != [record]:
            raise ValueError('Native profile GPU terminal or unique ledger differs')
        return record


def changed_evidence():
    rows = []
    for entry in read(ROOT/'first_event_output_acceptance.json')['rows']:
        new = read(checked(entry));old = read(BASE/'event_descriptors'/(new['uid']+'.json'))
        changed = sum({x['name'] for x in a.get('events',[])} != {x['name'] for x in b.get('events',[])}
            for a,b in zip(new['bins'], old['bins']))
        rows.append(dict(uid=new['uid'], sid=new['sid'], changed_bins=changed, bins=len(new['bins'])))
    totals = {sid:dict(changed=sum(x['changed_bins'] for x in rows if x['sid']==sid),
        bins=sum(x['bins'] for x in rows if x['sid']==sid)) for sid in {x['sid'] for x in rows}}
    sources = {sid for sid,x in totals.items() if x['changed']/x['bins'] >= .25}
    result = dict(status='EVENT_CLASS_CONTENT_CHANGED' if len(sources) >= 2 else 'STOP_NATIVE_PROFILE_NO_MATERIAL_EVENT_CLASS_CHANGE',
        windows=rows, source_totals=totals, sources_with_at_least_quarter_bins_changed=len(sources), labels_used=False,
        meaning='First input-information gate only; not evidence of better highlight quality')
    write(ROOT/'event_change_gate.json', result)
    return len(sources) >= 2


def main():
    write(ROOT/'controller_claim.json', dict(pid=os.getpid()))
    phase('native_inputs10')
    write(ROOT/'source_input_lock.json', dict(protocol=reference(ROOT/'protocol.json'),
        inputs=reference(ROOT/'input_acceptance.json'), weight_adoption=reference(ROOT/'acquisition05_completion.json'),
        original_A0=reference(BASE/'source_input_lock.json'),
        new_code={p.name:reference(p) for p in sorted(Path(__file__).parent.glob('*.py'))}))
    events = phase('events', cpu=False)
    phase('event_review')
    if not changed_evidence():
        write(ROOT/'completion.json', dict(status=read(ROOT/'event_change_gate.json')['status'],
            new_TIME_calls=0, new_PANN_forwards=8, new_ZIP=0, GPU_seconds=events['charged_seconds']))
        return
    phase('text_inputs')
    write(ROOT/'TIME_input_lock.json', dict(event_change_gate=reference(ROOT/'event_change_gate.json'),
        first16_CPU_inputs=reference(ROOT/'text_input_acceptance.json'), source_lock=reference(ROOT/'source_input_lock.json')))
    temporal = phase('time_calls', cpu=False)
    phase('review')
    checked(read(BASE/'source_input_lock.json')['baseline'])
    write(ROOT/'completion.json', dict(status=read(ROOT/'review.json')['status'],
        new_PANN_forwards=8, new_TIME_calls=16, new_ZIP=0, baseline40_47_unchanged=True,
        GPU_seconds=events['charged_seconds']+temporal['charged_seconds'],
        original16k_profile_STOP_unchanged=True, no_automatic_production=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT/'failure.json', dict(status='ACTUAL_NATIVE32K_FAILURE_PRESERVE_SUCCESS', traceback=traceback.format_exc()))
        raise
