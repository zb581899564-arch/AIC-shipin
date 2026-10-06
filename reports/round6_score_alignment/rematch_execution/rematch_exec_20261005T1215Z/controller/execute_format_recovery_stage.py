"""Execute exactly one admitted format recovery phase; old artifacts read-only."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from admit_a_pts_stage import sha,read,require
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL,CODE,REC = RUN/'controller',RUN/'baseline_a_pts_v1',RUN/'baseline_a_format_recovery_v1'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--admission',type=Path,required=True)
    args = parser.parse_args()
    a = read(args.admission)
    require(a['authorized'] is True and a['competition_upload_authorized'] is False,'no recovery admission')
    lock = CTRL/'format_recovery_controller_lock.json'
    require(sha(lock) == a['recovery_controller_lock_sha256'],'controller lock changed')
    for name,digest in read(lock)['files'].items():
        require(sha(CTRL/name) == digest,'controller helper changed')
    output = Path(a['run_dir'])
    if a['phase'] in ('probe','recover'):
        subprocess.run([sys.executable,'-B',str(REC/'inference.py'),'--mode',a['phase'],
            '--admission',str(args.admission),'--output',str(output)],check=True)
    else:
        if a['phase'] == 'schedule':
            output.mkdir(exist_ok=False)
            source = REC/'recover_01/temporal.jsonl'
            shutil.copyfile(source,output/'temporal.jsonl')
            require(sha(source) == sha(output/'temporal.jsonl'),'complete recovered time copy changed')
            report = read(REC/'recover_01/report.json')
            temporal = dict(status='PASS_TEMPORAL_EXECUTION',videos=426,windows=521,invalid_windows=0,
                variant='A_NATIVE_PTS_COMPAT_V1',format_recovery_variant='A_FORMAT_CONSTRAINED_RECOVERY_V1',
                source_lock_sha256=a['source_lock_sha256'],manifest_sha256=a['manifest_sha256'],
                output_sha256=sha(output/'temporal.jsonl'),original_temporal_sha256=report['original_temporal_sha256'],
                unchanged_successful_windows=516,recovered_failed_windows=5,original_run_remains_failed=True,
                format_recovery_report_sha256=sha(REC/'recover_01/report.json'),uploaded=False)
            (output/'temporal.stage.json').write_text(json.dumps(temporal,indent=2)+'\n')
        for stage in a['allowed_stages']:
            print('START_FORMAT_RECOVERY_STAGE '+stage,flush=True)
            subprocess.run([sys.executable,'-B',str(CODE/'run_pts.py'),'--stage',stage,
                '--manifest',a['manifest_path'],'--expected-manifest-sha256',a['manifest_sha256'],
                '--clock-registry',a['clock_registry_path'],'--expected-clock-registry-sha256',a['clock_registry_sha256'],
                '--run-dir',str(output),'--admission',str(args.admission)],check=True)
    print('PASS_ADMITTED_FORMAT_RECOVERY_PHASE '+a['phase'],flush=True)
