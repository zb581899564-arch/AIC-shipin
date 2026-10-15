"""Control-only hand oracles; no TIME read, launcher, source gate or resource scan."""
import argparse
import ast
import json
from pathlib import Path
from unittest.mock import patch

import cc_common as cc
from chain import GPU_argv


def rejected(callback):
    try:
        callback()
    except (ValueError, RuntimeError, json.JSONDecodeError):
        return
    raise AssertionError('Malformed control case unexpectedly admitted')


class MemoryPath:
    def __init__(self, path, files):
        self.path, self.files = path, files
    def __truediv__(self, name):
        return MemoryPath(self.path+'/'+str(name), self.files)
    def exists(self):
        return self.path in self.files
    def __str__(self):
        return self.path


def main(code_dir, sources=None):
    sources = sources if sources is not None else {
        p.name: p.read_text(encoding='utf-8') for p in Path(code_dir).glob('*.py')}
    for name, source in sources.items():
        ast.parse(source, filename=str(Path(code_dir)/name))
    driver = {'one.py': 'a'*64}
    control = {'controller.py': 'b'*64}
    scope = dict(schema=cc.SCOPE_SCHEMA, status=cc.SCOPE_STATUS, role='dev', base_root=str(cc.BASE), source_root=str(cc.TIME),
        actual_model_call_budget=37, events=20, **cc.COUNTS, gpu_job_name=cc.NAME, max_gpu_seconds=1500,
        planned_output_bytes=8<<20, new_input_processor_encodes=0, new_media_decodes=0, optimizer_updates=0,
        deadline='2080-10-14T11:56:40Z', driver_code_files=driver, controller_code_files=control,
        no_successful_TIME_or_input_stage_repeat=True, quality_selection_or_production_by_controller=False)
    cc.validate_scope(scope, scope['deadline'], control, driver)
    assert cc.check_deadline(scope).utcoffset().total_seconds() == 0
    rejected(lambda: cc.validate_scope(dict(scope, actual_model_call_budget=40), scope['deadline'], control, driver))
    rejected(lambda: cc.validate_scope(dict(scope, max_gpu_seconds=1501), scope['deadline'], control, driver))
    rejected(lambda: cc.validate_scope(dict(scope, planned_output_bytes=9<<20), scope['deadline'], control, driver))
    rejected(lambda: cc.validate_scope(dict(scope, driver_code_files={}), scope['deadline'], control, driver))
    with patch.dict(cc.os.environ, {'CUDA_VISIBLE_DEVICES': '0'}):
        assert cc.child_env(False)['CUDA_VISIBLE_DEVICES'] == '0'
        assert cc.child_env(True)['CUDA_VISIBLE_DEVICES'] == ''
        assert cc.os.environ['CUDA_VISIBLE_DEVICES'] == '0'
    argv = GPU_argv('synthetic resource reason')
    assert argv.count('--name') == 1 and argv[argv.index('--name')+1] == cc.NAME
    assert argv[argv.index('--max-seconds')+1] == '1500'
    assert argv[argv.index('--planned-output-bytes')+1] == str(8<<20)
    assert argv[-3:] == ['infer', '--base', str(cc.BASE)]
    files = {}
    root = MemoryPath('/TIME', files)
    complete = dict(status='COMPLETE_REAL_DEV37_TIME_AND_FIRST_INDEPENDENT_CPU_REPLAY_NOT_QUALITY', actual_model_calls=37,
        nominal_endpoints=40, structural_skips=3, gpu_completion_sha256='fixed',
        independent_replay_completion_sha256='fixed', export_sha256='fixed')
    def memory_read(path):
        value = files[str(path)]
        if value == 'PARTIAL_JSON':
            raise json.JSONDecodeError('synthetic create-x in progress', '', 0)
        return value
    with patch.object(cc, 'TIME', root), patch.object(cc, 'sha', lambda path: 'fixed'), patch.object(cc, 'read', memory_read):
        assert cc.time_terminal() is None
        files['/TIME/chain_01/completion.json'] = 'PARTIAL_JSON'
        assert cc.time_terminal(tolerate_incomplete=True) is None
        rejected(lambda: cc.time_terminal())
        files['/TIME/chain_01/completion.json'] = complete
        assert cc.time_terminal()['sha256'] == 'fixed'
        files['/TIME/chain_01/completion.json'] = dict(complete, actual_model_calls=36)
        rejected(lambda: cc.time_terminal())
        files['/TIME/chain_01/completion.json'] = complete
        files['/TIME/gpu_01/failure.json'] = {}
        rejected(lambda: cc.time_terminal())
    controller_tree = ast.parse(sources['controller.py'])
    wait = next(x for x in controller_tree.body if isinstance(x, ast.FunctionDef) and x.name == 'wait_TIME')
    calls = [x.func.attr if isinstance(x.func, ast.Attribute) else x.func.id if isinstance(x.func, ast.Name) else ''
             for x in ast.walk(wait) if isinstance(x, ast.Call)]
    assert not set(calls) & {'resource_snapshot', 'source_bundle', 'run', 'sleep', 'generate', 'encode'}
    assert 'inotify_init1' in calls and 'select' in calls and 'time_terminal' in calls
    prepare_tree = ast.parse(sources['register_admit.py'])
    forbidden = {'AutoProcessor', 'AutoTokenizer', 'load_tensor_cache', 'encode', 'baseline_frames', 'generate'}
    prepare_calls = [x.func.attr if isinstance(x.func, ast.Attribute) else x.func.id if isinstance(x.func, ast.Name) else ''
                     for x in ast.walk(prepare_tree) if isinstance(x, ast.Call)]
    assert not set(prepare_calls) & forbidden
    assert 'source_bundle' in prepare_calls and 'admitted' in prepare_calls
    print(json.dumps(dict(status='PASS_BASE37_CONTROLLER_PURE_SCOPE_EVENT_WAIT_TERMINAL_SINGLE_JOB', all5_AST=True,
        counts=[20,40,37,3], GPU_budget_seconds=1500, output_budget_bytes=8<<20,
        wrong_counts_budget_code_fail=True, real_Z_deadline_parser=True,
        CPU_child_only_CUDA_empty=True, parent_CUDA_unchanged=True,
        no_live_task_GPU_or_large_bundle_polling=True, native_file_event_wait=True,
        partial_create_JSON_waits_for_closed_file=True, TIME_missing_not_ready=True,
        TIME36_or_failure_blocks_BASE=True, one_GPU_wrapper_argv=True,
        admission_no_tensor_RGB_or_processor=True, actual_source_gate_executions=0,
        resource_scans=0, launcher_calls=0, media_reads=0, processor_encodes=0, model_calls=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--code-dir', required=True)
    main(parser.parse_args().code_dir)
