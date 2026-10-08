"""Reuse exact original successful observations; never claim new generation."""
from autopilot_common import *
import ast
import v10_cache_reuse as reuse


def function_code(path, names):
    tree=ast.parse(Path(path).read_bytes())
    return {node.name:ast.dump(node,include_attributes=False) for node in tree.body
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names}


def main():
    config=verify()
    old=RUN/'teacher_student_autopilot_v10'
    require(read(old/'completion.json')['status']=='STOP_AUTOPILOT_PRESERVED','old STOP changed')
    admission=read(HERE/'teacher_admission.json'); original=read(old/'teacher_admission.json')
    keys=('base_model_id','model_id','model_revision','runtime_revision','weight_files',
          'max_sequence_length','max_pixels_per_frame','image_min_tokens','image_max_tokens',
          'max_new_tokens','server_binary_sha256','server_parallel','server_log_verbosity')
    require(all(admission[k]==original[k] for k in keys),'legacy model/processor/capacity identity differs')
    require(sha(HERE/'visual_interface_probe.py')==sha(old/'visual_interface_probe.py'),
        'synthetic visual inputs and interface recipe changed')
    # These construct/process the actual ordered image requests, independent of
    # the boundary-output grammar. Any input-route change invalidates reuse.
    names=('image_data_url','record_processor_runtime','input_contract','start_server')
    left=function_code(HERE/'teacher_label.py',names);right=function_code(old/'teacher_label.py',names)
    require(left==right and 'start_server' in left,'ordered image/runtime call path changed')
    interface=read(HERE/'evidence_boundary_cpu_acceptance.json')
    require(interface['legacy_visual_requests_equal_actual_count']==8 and
        interface['production_teacher_sha256']==sha(HERE/'teacher_label.py') and
        interface['old_teacher_sha256']==sha(old/'teacher_label.py'),
        'all eight actual request constructors must match the original visual interface')
    visual=read(old/'visual_probe_01/completion.json')
    require(visual['status']=='PASS_REAL_SYNTHETIC_VISUAL_INTERFACE' and
        visual['case_count']==visual['real_model_calls']==8 and
        all(v['pass'] is True and v['expected_red_square_frame_ids']==v['actual_red_square_frame_ids'] for v in visual['cases']),
        'original real visual8 failed/incomplete')
    require(visual['weight_files']==admission['weight_files'] and
        visual['runtime_revision']==admission['runtime_revision'],'original visual model identity differs')
    probe,resource,visual_resource=reuse.original_probe_evidence()
    for receipt in (resource,visual_resource):
        require(receipt['status']=='completed' and receipt['exit_code']==0 and receipt['stop_reason'] is None,
            'original GPU receipt incomplete or uncharged')
    windows={w['window_id']:w for n in ('selected_train.jsonl','selected_dev.jsonl')
        for w in rows(Path(config['selection_dir'])/n)}
    pilot=read(HERE/'pilot_selection/manifest.json')['window_ids']
    require(all(w not in pilot for w in probe['window_ids']),'old heavy successes cannot count as pilot labels')
    out=HERE/'teacher_01';out.mkdir(exist_ok=False)
    original_selection=old/'teacher_01/probe_selection.json'
    (out/'probe_selection.json').write_bytes(original_selection.read_bytes())
    refs={}
    for identity in probe['window_ids']:
        require(reuse.verify_approved_annotation(windows[identity]) is not None,'legacy successful probe not admitted')
        directory=old/'teacher_01/windows'/identity
        refs[identity]={**probe['probe_receipts'][identity],'directory':str(directory)}
    final={**admission,'status':'PASS_REAL_STRONGER_TEACHER_ADMISSION',
        'capacity':{'status':'PASS_REAL_STRONGER_TEACHER_ADMISSION','original_actual_probe_receipt_sha256':sha(old/'teacher_01/teacher_probe_completion.json')},
        'capacity_admission_pass':True,'real_non_test_probe_windows':probe['window_ids'],
        'original_probe_completed_utc':probe['completed_utc'],'probe_reused_verified_utc':utc(),
        'fresh_model_calls':0,'old_success_records_unchanged':True}
    write(out/'teacher_admission.json',final,fresh=True)
    write(out/'teacher_probe_completion.json',{**probe,'admission_sha256':sha(out/'teacher_admission.json'),
        'probe_receipts':refs,'original_probe_receipt':{'path':str(old/'teacher_01/teacher_probe_completion.json'),
            'sha256':sha(old/'teacher_01/teacher_probe_completion.json')},
        'fresh_model_calls':0,'verified_reused_real_probe_windows':2,
        'original_probe_wall_sec':probe['wall_sec'],'original_gpu_charged_seconds':resource['charged_seconds'],
        'new_format_not_yet_generated_or_accepted':True,'original_completed_utc':probe['completed_utc'],
        'reuse_completed_utc':utc()},fresh=True)
    write(HERE/'legacy_handoff.json',dict(status='PASS_VERIFIED_LEGACY_INTERFACE_AND_CAPACITY_NOT_NEW_GENERATION',
        utc=utc(),accepted_manifest_sha256=sha(HERE/'accepted_resume_manifest.json'),
        original_visual_receipt_sha256=sha(old/'visual_probe_01/completion.json'),original_visual_calls=8,
        original_visual_charged_seconds=visual_resource['charged_seconds'],original_probe_calls=2,
        original_probe_charged_seconds=resource['charged_seconds'],fresh_model_calls=0,
        pilot_old_success_reuse_count=0,new_T_optimizer_updates=0,new_format_actual_first_pilot_required=True),fresh=True)
    print(json.dumps(read(HERE/'legacy_handoff.json')),flush=True)


if __name__=='__main__':main()
