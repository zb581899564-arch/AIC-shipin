"""One root-admitted wait -> BASE registration -> check -> GPU/replay chain."""
import argparse
import ctypes
import os
from pathlib import Path
import select
import struct
import subprocess
import sys
import traceback

import cc_common as cc


def wait_TIME(scope):
    """Linux file events; no live-task/GPU/large-metadata polling."""
    existing = cc.time_terminal(tolerate_incomplete=True)
    if existing is not None:
        return existing
    libc = ctypes.CDLL(None, use_errno=True)
    libc.inotify_init1.argtypes = [ctypes.c_int]
    libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    cc.require(fd >= 0, 'Cannot establish native file-event wait; stop without polling fallback')
    watched = {}
    mask = 0x00000100 | 0x00000080 | 0x00000008  # CREATE, MOVED_TO, CLOSE_WRITE
    def watch(path):
        if path.exists() and path not in watched.values():
            wd = libc.inotify_add_watch(fd, os.fsencode(path), mask)
            cc.require(wd >= 0, 'Cannot watch existing TIME terminal directory')
            watched[wd] = path
    try:
        watch(cc.TIME)
        for name in ('chain_01', 'gpu_01', 'replay_01'):
            watch(cc.TIME/name)
        # No lost wakeup if a stage completed during watcher installation.
        existing = cc.time_terminal(tolerate_incomplete=True)
        if existing is not None:
            return existing
        while True:
            deadline = cc.check_deadline(scope)
            remaining = (deadline-cc.dt.datetime.now(cc.dt.timezone.utc)).total_seconds()
            readable, _, _ = select.select([fd], [], [], min(60.0, remaining))
            if not readable:
                continue  # Only deadline clock is checked; no filesystem/task polling.
            data = os.read(fd, 65536)
            offset, terminal_event, closed_terminal = 0, False, False
            while offset < len(data):
                wd, flags, cookie, length = struct.unpack_from('iIII', data, offset)
                del cookie
                offset += 16
                name = os.fsdecode(data[offset:offset+length].split(b'\0', 1)[0])
                offset += length
                directory = watched.get(wd)
                if directory == cc.TIME and name in ('chain_01', 'gpu_01', 'replay_01'):
                    watch(cc.TIME/name)
                    terminal_event = True
                if name in ('completion.json', 'failure.json', 'controller_failure_01.json') and flags & (0x8 | 0x80):
                    terminal_event = True
                    closed_terminal = True
            if terminal_event:
                existing = cc.time_terminal(tolerate_incomplete=not closed_terminal)
                if existing is not None:
                    return existing
    finally:
        os.close(fd)


def main(scope_path):
    cc.host(cpu=False)
    scope_path, scope = cc.scope(scope_path)
    cc.check_deadline(scope)
    cc.unique_job_absent()
    # Reports from pure checks are allowed; no partially written admission is retried.
    for name in ('registration_01.json', 'protocol.json', 'official_rule_check.json', 'source_lock.json',
                 'gpu_admission.json', 'chain_01', 'gpu_01', 'replay_01', 'controller_01'):
        cc.require(not (cc.BASE/name).exists(), 'BASE stage already claimed; no automatic restart: '+name)
    out = cc.BASE/'controller_01'
    out.mkdir(exist_ok=False)
    cc.save(out/'launch_claim.json', dict(pid=os.getpid(), parent_pid=os.getppid(), argv=sys.argv, utc=cc.utc(),
        control_scope_path=str(scope_path), control_scope_sha256=cc.sha(scope_path),
        controller_code_files=cc.own_code_files(), parent_CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),
        future_BASE_actual_model_call_budget=37, **cc.COUNTS, stage='WAIT_FOR_TIME_NATURAL_COMPLETION_NOT_BASE_ADMISSION'))
    stage = 'WAIT_TIME'
    try:
        cc.save(out/'resource_before_wait.json', cc.resource_snapshot())
        terminal = wait_TIME(scope)
        cc.save(out/'TIME_natural_terminal.json', dict(status='TIME_CHAIN_NATURAL_TERMINAL_OBSERVED_NOT_BASE_ADMISSION',
            TIME_chain_completion=terminal, original_successful_stages_not_repeated=True, utc=cc.utc()))
        cc.check_deadline(scope)
        steps = [('register', 'register_admit.py', 'register', True),
                 ('independent_check', 'register_admit.py', 'check', True), ('chain', 'chain.py', None, False)]
        for stage, filename, operation, cpu in steps:
            argv = [str(cc.PY), '-B', '-u', str(Path(__file__).parent/filename)]
            if operation is not None:
                argv.append(operation)
            argv.extend(['--scope', str(scope_path)])
            env = cc.child_env(cpu)
            cc.save(out/(stage+'_launch.json'), dict(argv=argv, CPU_only=cpu,
                child_CUDA_VISIBLE_DEVICES=env.get('CUDA_VISIBLE_DEVICES'), utc=cc.utc()))
            with (out/(stage+'.log')).open('x') as log:
                result = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            cc.save(out/(stage+'_exit.json'), dict(exit_code=result.returncode, utc=cc.utc()))
            if result.returncode:
                raise RuntimeError(stage+' failed; keep all evidence and never retry automatically')
        cc.save(out/'completion.json', dict(status='COMPLETE_BASE37_CONTROLLER_AND_NEW_OUTPUT_ONLY_REPLAY_NOT_QUALITY',
            chain_completion_sha256=cc.sha(cc.BASE/'chain_01/completion.json'), TIME_chain_completion=terminal,
            actual_model_calls=37, events=20, **cc.COUNTS, new_processor_encodes=0, new_media_decodes=0,
            new_ZIPs=0, SCI=False, utc=cc.utc()))
    except BaseException as error:
        cc.save(out/'failure.json', dict(stage=stage, error=repr(error), traceback=traceback.format_exc(),
            preserve_success_and_raw=True, successful_or_started_model_calls_must_not_repeat=True,
            no_automatic_retry=True, utc=cc.utc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', required=True)
    main(parser.parse_args().scope)
