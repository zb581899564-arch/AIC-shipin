"""Capture bounded live evidence; never start/stop a job or edit frozen code."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')


def read(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def capture(version, entry=None):
    if socket.gethostname() != 'inspur-NP5570M5':
        raise RuntimeError('unexpected training host')
    entry = entry or ('teacher_student_autopilot_' + version)
    if not re.fullmatch(r'(?:teacher_(?:student_autopilot|context_diagnostic)|b_score_aligned_package)_v[1-9][0-9]*', entry):
        raise RuntimeError('unexpected inspection entry')
    here = RUN / entry
    if not here.is_dir():
        raise RuntimeError('unregistered version directory')
    now = datetime.datetime.now(datetime.timezone.utc)
    process_lines = subprocess.check_output(
        ['ps', '-eo', 'pid,ppid,pgid,etimes,pcpu,pmem,args'], text=True).splitlines()
    # python -B is a genuine controller/worker command, never filter it out.
    processes = [line.strip() for line in process_lines if str(here) + '/' in line]
    owned_ids = {int(line.split()[0]) for line in processes}
    servers = [line.strip() for line in process_lines if 'llama-server' in line
               and any(int(line.split()[i]) in owned_ids for i in (1, 2))]
    windows = []
    for directory in sorted((here / 'teacher_01/windows').glob('*')):
        done, failure = read(directory / 'done.json'), read(directory / 'failure.json')
        if not done and not failure:
            continue
        record = read(directory / 'validated_record.json') or {}
        checks = {}
        for name, expected in (done or {}).get('files', {}).items():
            path = directory / name
            checks[name] = path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
        windows.append({'window_id': directory.name, 'done_status': (done or {}).get('status'),
                        'completed_utc': (done or {}).get('completed_utc'),
                        'wall_sec': (done or {}).get('wall_sec'), 'failure': failure,
                        'status': record.get('status'), 'split': record.get('split'),
                        'sft_eligible': record.get('sft_eligible'),
                        'explicit_no_highlight': record.get('explicit_no_highlight'),
                        'uncertain': record.get('uncertain'),
                        'segment_count': len(record.get('retained_segments', [])),
                        'file_sha_checks': checks})
    states = Counter()
    for row in windows:
        if row['failure']:
            states['engineering_failure'] += 1
        elif row['explicit_no_highlight'] is True:
            states['explicit_empty'] += 1
        elif row['uncertain'] is True:
            states['uncertain'] += 1
        elif row['segment_count']:
            states['positive'] += 1
        else:
            states['unclassified'] += 1
    snapshot = {'utc': now.isoformat(), 'host': socket.gethostname(), 'version': version, 'entry': entry,
                'processes': processes, 'owned_servers': servers,
                'gpu': subprocess.check_output(['nvidia-smi', '--query-gpu=index,name,utilization.gpu,memory.used,memory.total',
                                                '--format=csv,noheader'], text=True).strip(),
                'memory': subprocess.check_output(['free', '-m'], text=True).strip(),
                'disk': dict(zip(('total', 'used', 'free'), shutil.disk_usage(RUN))),
                'window_counts': dict(states), 'window_receipts': windows,
                'all_completed_window_file_sha_pass': all(all(w['file_sha_checks'].values()) and w['file_sha_checks']
                                                          for w in windows if w['done_status']),
                'new_zip_paths': [str(p.relative_to(here)) for pattern in ('**/candidate_T_8B.zip','**/candidate_B2_8B.zip')
                                  for p in here.glob(pattern)],
                'source_lock_sha256': hashlib.sha256((here/'source_lock.json').read_bytes()).hexdigest()
                    if (here/'source_lock.json').is_file() else None,
                'launch_receipt': read(here/'start_receipt.json') or read(here/'launch.json')}
    if entry.startswith('b_score_aligned_package_'):
        snapshot['b2_cpu_acceptance'] = read(here/'cpu_acceptance.json')
        snapshot['b2_processor_acceptance'] = read(here/'processor_acceptance.json')
        snapshot['b2_probe'] = read(here/'probe_01/probe.stage.json')
        snapshot['b2_probe_receipt_sha256'] = hashlib.sha256((here/'probe_01/probe.stage.json').read_bytes()).hexdigest() \
            if (here/'probe_01/probe.stage.json').is_file() else None
        snapshot['active_gpu_job'] = read(RUN.parents[2]/'improvement_round1/active_gpu_job.json')
        snapshot['b2_resource_receipts'] = {p.name:read(p) for p in
            sorted((RUN/'controller').glob('rematch_B2_'+entry.rsplit('_',1)[1]+'*.resource.json'))}
        snapshot['b2_queue_receipts'] = {p.name:read(p) for p in
            sorted((RUN/'controller').glob('rematch_B2_'+entry.rsplit('_',1)[1]+'*.queue.json'))}
        snapshot['b2_artifact_activity'] = {
            scope:{p.name:{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
            for p in sorted((here/scope).glob('*')) if p.is_file()}
            for scope in ('probe_01','nontest_01','rematch_01')}
    if entry.startswith('teacher_context_diagnostic_'):
        snapshot['context_diagnostic_requests'] = [
            {'window_id': row['window_id'], 'arm': row['arm'], 'status': row['status'],
             'state': row['result']['state'], 'wall_sec': row['wall_sec'],
             'actual_prompt_tokens': row['actual_prompt_tokens'], 'physical_images': row['physical_images'],
             'raw_answer_sha256': row['raw_answer_sha256'], 'receipt_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted((here/'run_01/requests').glob('*/*/diagnostic_receipt.json'))
            for row in [read(path)]]
        snapshot['context_overview_receipts'] = [
            {'source_sha256': row['source_sha256'], 'full_source_frame_count': row['full_source_frame_count'],
             'provided_context_frames': len(row['frames']), 'clock_sequence_sha256': row['clock_sequence_sha256'],
             'receipt_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted((here/'run_01/overview').glob('*/decode_receipt.json'))
            for row in [read(path)]]
        snapshot['context_diagnostic_reviews'] = [
            {'window_id':row['window_id'],'status':row['status'],'review_status':row['review_status'],
             'actual_prompt_tokens':row['actual_prompt_tokens'],'physical_images':row['physical_images'],
             'raw_answer_sha256':row['raw_answer_sha256'],'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted((here/'run_01/reviews').glob('*/review_receipt.json'))for row in [read(path)]]
        snapshot['context_resource_receipt'] = read(RUN/'controller'/('rematch_CONTEXT_DIAG_'+entry.rsplit('_',1)[1]+'.resource.json'))
    snapshot['review_counts'] = {}
    for phase in ('pilot_01', 'teacher_01'):
        reviews = [read(p) for p in sorted((here / phase / 'reviews').glob('*/review_receipt.json'))]
        snapshot['review_counts'][phase] = dict(Counter(r.get('review_status', 'missing_status') for r in reviews))
    for key, relative in {'registration': 'registration.json', 'progress': 'progress.json',
                          'completion': 'completion.json', 'pilot_progress': 'pilot_01/progress.json',
                          'pilot_completion': 'pilot_01/completion.json', 'distribution': 'pilot_01/distribution.json',
                          'semantic_quality': 'pilot_01/pilot_semantic_quality.json',
                          'teacher_progress': 'teacher_01/progress.json', 'teacher_completion': 'teacher_01/teacher_completion.json',
                          'teacher_semantic_review': 'teacher_01/semantic_review.json',
                          'teacher_stop': 'teacher_01/teacher_stop.json',
                          'student_progress': 'student_01/progress.json', 'student_report': 'student_01/student_completion.json',
                          'nontest8_package': 'nontest_01/package.stage.json',
                          'nontest8_strict': 'nontest_01/independent_validation.json',
                          'rematch_package': 'rematch_01/package.stage.json',
                          'rematch_strict': 'rematch_01/independent_validation.json'}.items():
        snapshot[key] = read(here / relative)
    snapshot['production_stage_receipts'] = {
        scope: {p.name: read(p) for p in sorted((here / scope).glob('*.stage.json'))}
        for scope in ('nontest_01', 'rematch_01')}
    monitor = RUN / 'controller/monitor_aic_linux'
    monitor.mkdir(exist_ok=True)
    data = json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'
    snapshot_path = monitor / ('comprehensive_' + entry + '_' + now.strftime('%Y%m%dT%H%M%SZ') + '.json')
    snapshot_path.write_text(data, encoding='utf-8')
    temporary=monitor/'latest.json.tmp';temporary.write_text(data,encoding='utf-8');temporary.replace(monitor/'latest.json')
    return snapshot_path, snapshot


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default='v7')
    parser.add_argument('--entry')
    args = parser.parse_args()
    path, snapshot = capture(args.version,args.entry)
    print(json.dumps({'snapshot_path': str(path), 'snapshot': snapshot}, ensure_ascii=False))
