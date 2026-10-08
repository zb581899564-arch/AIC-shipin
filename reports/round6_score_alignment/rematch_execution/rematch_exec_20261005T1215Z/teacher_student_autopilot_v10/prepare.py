"""Freeze new tested control bytes and untouched selection; never reseal a job."""
from autopilot_common import *
import socket


def main():
    require(socket.gethostname() == 'inspur-NP5570M5', 'wrong preparation host')
    require(not any((HERE / n).exists() for n in ('source_lock.json','registration.json','start_receipt.json')), 'never reseal registered run')
    accepted = read(HERE / 'cpu_acceptance.json')
    require(accepted['status'] == 'PASS_V8_CPU_STAGE_AND_CONTRACT_TESTS', 'new CPU acceptance required')
    identity = read(HERE / 'v9_cache_identity_cpu_acceptance.json')
    require(identity['status'] == 'PASS_V9_ACTUAL_CACHE_IDENTITY_AND_BRIDGE_CPU' and
            identity['new_contract_tests'] == 9 and identity['GPU_started'] is False and
            identity['old_frozen_source_unchanged'] is True,
            'actual B2 cache identity rejection contracts required before freezing')
    bridge = read(HERE / 'real_cache_bridge_cpu_acceptance.json')
    require(bridge['status'] == 'PASS_ACTUAL_B2_COMPLETE_CACHE_BRIDGE_CPU' and
            bridge['original_actual_failure_reproduced'] is True and
            bridge['production_controller_sha256'] == sha(HERE/'controller.py') and
            bridge['GPU_started'] is False and bridge['old_data_changed'] is False,
            'actual B2 terminal/cache bridge acceptance required before freezing')
    ordered = read(HERE / 'ordered_boundary_cpu_acceptance.json')
    require(ordered['status'] == 'PASS_FIXED_RUNTIME_ORDERED_BOUNDARY_CPU' and
            ordered['GPU_started'] is False and ordered['old_raw_rejected'] is True and
            ordered['production_boundary_sha256'] == sha(HERE/'boundary_ids.py') and
            ordered['production_teacher_sha256'] == sha(HERE/'teacher_label.py'),
            'actual pinned runtime ordered-boundary rejection required')
    previous = RUN / 'teacher_student_autopilot_v9/source_lock.json'
    old = read(previous)
    files = dict(old['files'])
    # Keep original frozen code/evidence as dependencies, add independent new code.
    files[str(previous)] = sha(previous)
    stopped = previous.parent / 'completion.json'
    require(read(stopped)['status'] == 'STOP_AUTOPILOT_PRESERVED', 'v9 failure must remain preserved')
    files[str(stopped)] = sha(stopped)
    failed = previous.parent/'teacher_01/windows/complete_087af79e4b421be308d6cf6f'
    for name in ('server_response.json','failure.json','generation_schema.json','runtime_grammar_validation.json','input_contract.json','decode_receipt.json'):
        require((failed/name).is_file(), 'actual failed raw evidence missing')
        files[str(failed/name)] = sha(failed/name)
    files[str(previous.parent/'teacher_01/teacher_stop.json')] = sha(previous.parent/'teacher_01/teacher_stop.json')

    for path, digest in files.items():
        require(sha(path) == digest, 'predecessor bound bytes changed: ' + path)
    runtime = HERE / 'runtime_schema_check'
    origin = RUN / 'teacher_student_autopilot_v9/runtime_schema_check'
    require(runtime.is_file() and sha(runtime) == sha(origin), 'pinned grammar checker differs')
    for directory in ('selection_01','pilot_selection'):
        receipt = read(HERE / directory / 'selection_receipt.json')
        require(receipt['status'] == 'PASS_CPU_SELECTION_UNLABELLED' and receipt['confirm_opened'] is False
                and receipt['contest_assets_opened'] is False, 'non-test selection incomplete')
        for name, digest in receipt['files'].items():
            path = HERE / directory / name
            require(sha(path) == digest, 'new selection bytes changed')
            files[str(path)] = digest
        files[str(HERE / directory / 'selection_receipt.json')] = sha(HERE / directory / 'selection_receipt.json')
    selection = read(HERE / 'selection_01/selection_receipt.json')
    external_bindings = [selection['source_selector'], *selection['manifests'].values()]
    for ref in external_bindings:
        require(sha(ref['path']) == ref['sha256'], 'selector or approved manifest changed')
        files[ref['path']] = ref['sha256']
    require(selection['fresh_source_groups_disjoint_from_all_prior'] is True, 'fresh groups overlap calibration')
    for path in (HERE/'selection_01/preregistration.json', HERE/'pilot_selection/manifest.json'):
        require(path.is_file(), 'pre-generation selection registration missing')
        files[str(path)] = sha(path)
    selected = rows(HERE / 'selection_01/selected_train.jsonl') + rows(HERE / 'selection_01/selected_dev.jsonl')
    require(len(selected) == 160 and len({w['source_group'] for w in selected}) == 160, 'new group denominator differs')
    for window in selected:
        require(sha(window['source_path']) == window['source_sha256'], 'new source bytes changed')
        files[window['source_path']] = window['source_sha256']
    b2 = RUN / 'b_score_aligned_package_v4'
    for name in ('source_lock.json','config.json','completion.json','source_color.py','source_color_acceptance.json'):
        files[str(b2/name)] = sha(b2/name)
    for scope in ('nontest','rematch'):
        for name in ('schedule.stage.json','spatial.stage.json','field_frames.jsonl','field_shots.jsonl',
                     'anchor_requests.jsonl','anchor_output.jsonl','package.stage.json','independent_validation.json'):
            files[str(b2/(scope+'_01')/name)] = sha(b2/(scope+'_01')/name)
    for path in HERE.rglob('*'):
        if not path.is_file() or any(x in path.parts for x in ('__pycache__','prelock_repairs')): continue
        if path.name in ('source_lock.json','prepare.stdout.txt','prepare.stderr.txt'): continue
        if path.suffix in ('.py','.md','.txt','.json','.cpp') or path.name == 'runtime_schema_check':
            files[str(path)] = sha(path)
    write(HERE/'source_lock.json', dict(schema='AIC_TEACHER_STUDENT_SOURCE_LOCK_V10',utc=utc(),files=files,
        new_protocol=True, predecessor_source_lock_sha256=sha(previous), old_scientific_STOP_preserved=True,
        cross_recipe_label_reuse=False, actual_capacity_only=True, teacher_is_offline_only=True), fresh=True)
    print(json.dumps(dict(status='PASS_V8_SOURCE_BINDING', files=len(files),source_lock_sha256=sha(HERE/'source_lock.json'))),flush=True)


if __name__ == '__main__': main()
