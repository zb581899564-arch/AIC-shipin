"""Isolated mocked ownership/queue tests; never signal a real process or GPU."""
from pathlib import Path
import hashlib
import importlib.util
import json
import signal
import sys
import tempfile
from types import SimpleNamespace
import argparse
import re

RUN = Path(__file__).resolve().parent.parent
arguments = argparse.ArgumentParser()
arguments.add_argument('--entry', default='b_score_aligned_package_v2')
entry_name = arguments.parse_args().entry
assert re.fullmatch(r'b_score_aligned_package_v[1-9][0-9]*', entry_name)
ENTRY = RUN / entry_name
sys.path.insert(0, str(ENTRY))
TARGET = ENTRY / 'temporal_reuse.py'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def case(base, name):
    root = base / name; old = root / 'old'; out = root / 'out'; out.mkdir(parents=True)
    put(old / 'source_lock.json', {'files': {}})
    put(old / 'launch.json', {'pid': 123456789, 'source_lock_sha256': digest(old / 'source_lock.json')})
    put(old / 'rematch_01/temporal.stage.json', {'status': 'PASS_TEMPORAL_EXECUTION'})
    resource = root / 'controller/rematch_B2_v1_rematch_temporal_01.resource.json'
    put(resource, {'status': 'completed', 'exit_code': 0})
    specification = importlib.util.spec_from_file_location('handoff_test_' + name, TARGET)
    module = importlib.util.module_from_spec(specification); specification.loader.exec_module(module)
    module.HERE = out; module.RUN = root; module.ROOT = root
    module.old_entry = lambda: old
    # Data/validator replay is covered by actual CPU contracts. These cases
    # isolate controller ownership and never claim to validate synthetic labels.
    module.verify_temporal = lambda *args, **kwargs: {'failed_windows': []}
    pid = 123456789; child = pid + 1; wrapper = pid + 2
    expected = [sys.executable, '-B', str(old / 'controller.py')]
    state = {'alive': True, 'waited': False, 'wrapper': name == 'wrapper_wait', 'clock': 0., 'signals': []}
    marker = root / 'improvement_round1/active_gpu_job.json'
    if name in ('gpu_wait', 'external_gpu_untouched'):
        put(marker, {'name': 'rematch_B2_v1_rematch_temporal_01' if name == 'gpu_wait' else 'external_job'})
    if name == 'provider_stopped_before_completion':
        (old / 'rematch_01/temporal.stage.json').unlink()
        put(old / 'completion.json', {'stage': 'STOP_B2_PACKAGE_V1'})
    if name in ('declared_failed_provider_complete','unexpected_wrapper_failure'):
        put(old / 'rematch_01/temporal.stage.json', {'status': 'STOP_TEMPORAL_FAILURES'})
        put(resource, {'status':'failed','exit_code':1 if name=='declared_failed_provider_complete' else 2,
                       'stop_reason':None})
    original = {p: digest(p) for p in (old / 'source_lock.json', old / 'launch.json', resource)}
    if (old / 'rematch_01/temporal.stage.json').exists():
        original[old / 'rematch_01/temporal.stage.json'] = digest(old / 'rematch_01/temporal.stage.json')

    def command(which):
        if not state['alive'] or name == 'provider_already_terminal':
            return []
        if which == pid:
            return expected if name != 'PID_reused' else [sys.executable, '-B', '/unrelated/task.py']
        if which == child:
            return [sys.executable, '-B', str(old / 'production.py'), 'scheduling', 'rematch', str(old / 'rematch_01')]
        if which == wrapper and state['wrapper']:
            return [sys.executable, '-B', '/mock/gpu_run.py']
        if which == wrapper and name == 'foreign_descendant':
            return ['/mock/unrelated_service']
        return []

    def members(group):
        values = [dict(pid=pid, parent=1, pgid=pid, stat='S'), dict(pid=child, parent=pid, pgid=pid, stat='R')]
        if state['wrapper'] or name == 'foreign_descendant':
            values.append(dict(pid=wrapper, parent=pid, pgid=pid, stat='S'))
        return values

    def sleep(seconds):
        state['clock'] += seconds; state['waited'] = True; state['wrapper'] = False
        if name == 'gpu_wait' and marker.exists():
            marker.unlink()

    def killpg(group, sig):
        assert group == pid and sig == signal.SIGTERM
        assert name not in ('foreign_descendant', 'PID_reused', 'wrong_PGID', 'provider_stopped_before_completion')
        assert not state['wrapper'] and (name != 'gpu_wait' or state['waited'])
        state['signals'].append((group, int(sig))); state['alive'] = False

    module.command = command; module.group_members = members
    module.os = SimpleNamespace(getpgid=lambda value: pid + (name == 'wrong_PGID'), killpg=killpg)
    module.time = SimpleNamespace(monotonic=lambda: state['clock'], sleep=sleep)
    blocked = name in ('foreign_descendant', 'PID_reused', 'wrong_PGID', 'provider_stopped_before_completion',
                      'unexpected_wrapper_failure')
    try:
        module.wait_and_handoff()
    except ValueError:
        assert blocked and not state['signals'], name
    else:
        assert not blocked, name
        receipt = json.loads((out / 'handoff_receipt.json').read_text())
        assert receipt['status'].startswith('PASS_'), name
        assert len(state['signals']) == (0 if name == 'provider_already_terminal' else 1)
        if name in ('gpu_wait', 'wrapper_wait'):
            assert state['waited']
        if name == 'external_gpu_untouched':
            assert json.loads(marker.read_text()) == {'name': 'external_job'}
    assert all(digest(path) == expected for path, expected in original.items())
    return dict(case=name, passed=True, real_signals_sent=0, original_provider_bytes_unchanged=True)


def main():
    before = digest(TARGET)
    lock = json.loads((ENTRY / 'source_lock.json').read_text())
    assert lock['files'][str(TARGET)] == before
    names = ('owned_CPU_only', 'provider_already_terminal', 'foreign_descendant', 'PID_reused',
             'wrong_PGID', 'provider_stopped_before_completion', 'gpu_wait', 'wrapper_wait', 'external_gpu_untouched')
    if entry_name in ('b_score_aligned_package_v3','b_score_aligned_package_v4'):
        names += ('declared_failed_provider_complete','unexpected_wrapper_failure')
    with tempfile.TemporaryDirectory(prefix='b2_handoff_mock_', dir=RUN / 'controller') as directory:
        cases = [case(Path(directory), name) for name in names]
    assert digest(TARGET) == before
    report = dict(status='PASS_B2_OWNERSHIP_AND_HANDOFF_CPU', cases=cases, tests=len(cases),
        live_helper_sha256=before, source_lock_sha256=digest(ENTRY / 'source_lock.json'),
        actual_process_signals_sent=0, actual_GPU_calls=0, actual_frozen_sources_changed=False)
    path = RUN / 'controller' / ('B2_'+entry_name.rsplit('_',1)[1]+'_handoff_cpu_20261008.json')
    assert not path.exists(), 'preserve prior test evidence'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
