"""Replay the real B2 terminal/cache handoff without a GPU or cache writes."""
from autopilot_common import *
import subprocess
import sys
import controller


def main():
    previous = RUN / 'teacher_student_autopilot_v8'
    terminal = read(previous / 'completion.json')
    require(terminal['status'] == 'STOP_AUTOPILOT_PRESERVED', 'old failed run must remain stopped')
    baseline = {str(p): sha(p) for p in (previous/'completion.json', previous/'source_lock.json',
        RUN/'b_score_aligned_package_v4/completion.json')}
    code = "import controller\ntry:\n controller.freeze_z_cache(None)\nexcept KeyError as error:\n assert error.args == ('status',), repr(error)\n print('REPRODUCED_V8_REAL_B2_STATUS_KEY_ERROR')\nelse:\n raise AssertionError('original failure was not reproduced')\n"
    old = subprocess.run([str(PY), '-B', '-c', code], cwd=previous,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    require(old.returncode == 0 and old.stdout.strip() == 'REPRODUCED_V8_REAL_B2_STATUS_KEY_ERROR',
        'actual previous function replay failed: ' + old.stdout + old.stderr)
    captured = {}
    original_write = controller.write
    def isolated_write(path, value, *, fresh=False):
        require(Path(path).parent == HERE/'cache_01' and fresh, 'unexpected production write')
        require(Path(path).name not in captured, 'duplicate cache receipt')
        captured[Path(path).name] = value
    controller.write = isolated_write
    try:
        controller.freeze_z_cache(None)
    finally:
        controller.write = original_write
    require(set(captured) == {'nontest.json', 'rematch.json'}, 'full cache scopes differ')
    for row in captured.values():
        require(row['status'] == 'PASS_FROZEN_B2_SOURCE_FIELD_CACHE' and
            row['temporal_reuse_permitted'] is False, 'source-field bridge changed scope')
    require(all(sha(p) == digest for p, digest in baseline.items()), 'historical evidence changed')
    require(not (HERE/'cache_01').exists(), 'CPU bridge created production output')
    write(HERE/'real_cache_bridge_cpu_acceptance.json', {
        'status':'PASS_ACTUAL_B2_COMPLETE_CACHE_BRIDGE_CPU', 'utc':utc(),
        'actual_production_function':'controller.freeze_z_cache',
        'production_controller_sha256':sha(HERE/'controller.py'),
        'original_controller_sha256':sha(previous/'controller.py'),
        'original_actual_failure_reproduced':True,
        'same_actual_B2_final_JSON_stage_key_used':True,
        'actual_cache_models_input_and_all_artifact_SHA_verified':True,
        'only_output_writes_isolated_into_memory':True, 'receipts':captured,
        'GPU_started':False, 'old_data_changed':False, 'baseline_evidence':baseline})
    print('PASS_ACTUAL_B2_COMPLETE_CACHE_BRIDGE_CPU: old failure reproduced; two actual scopes passed')


if __name__ == '__main__':
    main()
