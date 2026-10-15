"""Only new Linux process-guard checks; no Torch/media/codec replay/release."""
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import queue
import socket
import sys
import time

from codec import Store, SCHEMA, LOCK_BACKEND, SYNTHETIC_ROOT


def worker(role,ready,attempting,release,entered,events):
    try:
        store=Store(SYNTHETIC_ROOT)
        attempting.set()
        try:
            with store.locked():
                entered.set();events.put((role,'ENTER',time.monotonic_ns()))
                if role=='A':
                    ready.set()
                    if not release.wait(8):raise AssertionError('Bounded synthetic release event missing')
                    events.put((role,'RAISE',time.monotonic_ns()))
                    raise RuntimeError('EXPECTED_SYNTHETIC_CONTEXT_EXCEPTION')
                events.put((role,'EXIT',time.monotonic_ns()))
        except RuntimeError as error:
            if role!='A' or str(error)!='EXPECTED_SYNTHETIC_CONTEXT_EXCEPTION':raise
            events.put((role,'EXPECTED_EXCEPTION_CAUGHT',time.monotonic_ns()))
        if 'torch' in sys.modules:raise AssertionError('New lock test imported Torch')
        events.put((role,'DONE',time.monotonic_ns()))
    except BaseException as error:
        events.put((role,'FAIL',repr(error)));raise


def blocked(call):
    try:call()
    except (ValueError,OSError):return
    raise AssertionError('Symlink or hardlink guard was accepted')


def touch_lock(store):
    with store.locked():pass


def main():
    if socket.gethostname()!='inspur-NP5570M5' or sys.platform!='linux' or os.environ.get('CUDA_VISIBLE_DEVICES')!='':
        raise ValueError('Only new Linux CUDA-hidden synthetic branch is authorized')
    root=SYNTHETIC_ROOT;parent=root.parent
    if root.exists():raise FileExistsError('Never repeat a completed synthetic fixture')
    parent.mkdir(parents=True,exist_ok=True)
    receipt=parent/'process_lock_check_01.json'
    if receipt.exists():raise FileExistsError('Preserve original pure receipt')
    store=Store.create(root,['A','B'],dict(schema=SCHEMA,root=str(root),mode='PURE_SYNTHETIC',
        process_lock_backend=LOCK_BACKEND))
    context=mp.get_context('spawn')
    ready,attempt_A,attempt_B,release,enter_A,enter_B=[context.Event() for _ in range(6)]
    events=context.Queue()
    a=context.Process(target=worker,args=('A',ready,attempt_A,release,enter_A,events))
    b=context.Process(target=worker,args=('B',ready,attempt_B,release,enter_B,events))
    processes=[a,b];records=[]
    try:
        a.start()
        if not ready.wait(8):raise AssertionError('Owner did not acquire new persistent guard')
        guard=root/'permanent/journal_write.lock'
        initial=(guard.stat().st_dev,guard.stat().st_ino)
        b.start()
        if not attempt_B.wait(8):raise AssertionError('Contender did not attempt acquire')
        if enter_B.wait(.3):raise AssertionError('Two processes entered one cache transaction concurrently')
        release.set()
        for process in processes:
            process.join(10)
            if process.is_alive() or process.exitcode!=0:raise AssertionError('Synthetic process did not naturally complete')
        while True:
            try:records.append(events.get(timeout=.1))
            except queue.Empty:break
        times={(role,event):value for role,event,value in records}
        assert ('A','EXPECTED_EXCEPTION_CAUGHT') in times and ('A','DONE') in times and ('B','DONE') in times
        assert times[('A','ENTER')]<times[('A','RAISE')]<times[('B','ENTER')]<times[('B','EXIT')]
        assert guard.is_file() and guard.stat().st_nlink==1 and (guard.stat().st_dev,guard.stat().st_ino)==initial
        assert guard.read_bytes()==b''
        # A later normal acquire must reuse the persistent inode, never create a new lock path.
        touch_lock(store)
        assert (guard.stat().st_dev,guard.stat().st_ino)==initial
        kept=root/'permanent/guard_original_kept.bin';guard.rename(kept)
        protected=parent/'new_protected_synthetic.bin';protected.write_bytes(b'NEW_GUARD_TEST_SENTINEL')
        sentinel=hashlib.sha256(protected.read_bytes()).hexdigest()
        os.symlink(protected,guard)
        blocked(lambda:touch_lock(store));guard.unlink()
        os.link(protected,guard)
        blocked(lambda:touch_lock(store));guard.unlink()
        kept.rename(guard)
        assert hashlib.sha256(protected.read_bytes()).hexdigest()==sentinel and protected.stat().st_nlink==1
        assert (guard.stat().st_dev,guard.stat().st_ino)==initial
        touch_lock(store)
        assert guard.read_bytes()==b'' and 'torch' not in sys.modules
        result=dict(status='PASS_NEW_TWO_PROCESS_FLOCK_MUTEX_EXCEPTION_RELEASE_PERSISTENT_INODE_NO_LINK_GUARD',
            backend=LOCK_BACKEND,worker_processes=2,worker_exit_codes=[a.exitcode,b.exitcode],
            checks=['contender_blocks_while_owner_inside','owner_context_exception_releases_lock',
                'contender_then_enters_naturally','guard_inode_persists_across_both_workers_and_later_acquires',
                'empty_guard_content_unchanged','symlink_guard_rejected','hardlink_guard_rejected',
                'new_synthetic_sentinel_untouched','no_Torch_import'],
            guard_inode=list(initial),synthetic_root=str(root),events=records,
            old_cache_or_production_roots_accessed=False,old_codec_tests_repeated=False,
            RGB_releases=0,media_reads=0,processor_or_model_calls=0)
        with receipt.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
        print(json.dumps(result))
    except BaseException as error:
        release.set()
        for process in processes:
            if process.pid is not None:
                process.join(2)
                if process.is_alive():process.terminate();process.join(2)
        with (parent/'process_lock_failure_01.json').open('x') as f:
            json.dump(dict(error=repr(error),preserve_new_fixture=True,automatic_retry=False,
                          processor_or_model_calls=0),f,indent=2)
        raise


if __name__=='__main__':main()
