"""Create an independent B2 control tree; never alter registered experiments."""
import ast
import json
from pathlib import Path

RUN = Path(__file__).resolve().parent.parent
OUT = RUN / 'b_score_aligned_package_v1'
REMOTE = '/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def put(name, text):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode('utf-8')
    if path.exists():
        assert path.read_bytes() == data, 'preserve existing B2 work: ' + name
    else:
        path.write_bytes(data)


def source(relative):
    return (RUN / relative).read_text(encoding='utf-8-sig')


def functions(relative, names):
    text = source(relative)
    tree = ast.parse(text)
    selected = {node.name: ast.get_source_segment(text, node) for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names}
    assert set(selected) == set(names)
    return '\n\n'.join(selected[name] for name in names) + '\n'


def main():
    OUT.mkdir(exist_ok=True)
    assert not (OUT / 'source_lock.json').exists(), 'B2 already registered'
    for name in ('frame_contract.py', 'field_contract.py', 'package_contract.py', 'video_contract.py',
                 'spatial_baseline.py', 'test_field_contract.py', 'test_empty_pipeline.py'):
        put(name, source('next_round_v1/' + name))
    for name in ('contracts.py', 'constrained_json.py'):
        put(name, source('teacher_student_autopilot_v7/precision_helpers/' + name))
    for name in ('native_segment_contract.py', 'cost_contract.py'):
        put(name, source('teacher_student_autopilot_v7/' + name))
    names = ('floor_indices', 'window_from_pts', 'decode_window')
    native = ('"""Sequential native PTS and floor sampling, independently registered for B2."""\n'
              'from common import *\nimport math\nimport hashlib\n_VERIFIED_SOURCE_STATS = {}\n\n')
    native += functions('teacher_student_autopilot_v7/train_student.py', names)
    native = native.replace('Public T production', 'Public B2 production').replace('Public sequential T', 'Public sequential B2')
    native = native.replace('invalid T ', 'invalid B2 ').replace('T source ', 'B2 source ').replace('T sampling ', 'B2 sampling ')
    put('native_input.py', native)
    production = source('next_round_v1/production.py')
    original_field = functions('next_round_v1/production.py', ('field_frames',)).rstrip()
    native_field = functions('teacher_student_autopilot_v7/production_t.py', ('native_field_frames',)).rstrip()
    native_field = native_field.replace('def native_field_frames(', 'def field_frames(')
    select = functions('teacher_student_autopilot_v7/production_t.py', ('select_native_frames',)).rstrip()
    select = select.replace('def select_native_frames(', 'def select_frames(').replace('T uses actual PTS', 'B2 uses actual PTS')
    production = production.replace('import math\n', 'import math\nfrom bisect import bisect_left\n')
    production = production.replace(original_field, native_field + '\n\n' + select)
    production = production.replace('from frame_contract import select_frames, legacy_manifest', 'from frame_contract import legacy_manifest')
    production = production.replace('    from field_contract import build_field_requests\n',
        "    from cache_contract import try_reuse\n    if try_reuse(scope,out,manifest,clocks,selected,domain):return\n"
        '    from field_contract import build_field_requests\n', 1)
    production = production.replace("    require(sum(p.numel() for p in model.model.parameters())==8767123696,'space model parameter count changed')",
        "    require(sum(p.numel() for p in model.model.parameters())==8767123696,'space model parameter count changed')\n"
        "    for parameter in model.model.parameters():parameter.requires_grad_(False)\n"
        "    from engine import frozen_identity\n    base_hash=frozen_identity(model.model,config)")
    production = production.replace("strict_units='INTEGER_0_TO_1000',time_adapter_enabled=False", 
                                    "base_hash=base_hash,strict_units='INTEGER_0_TO_1000',time_adapter_enabled=False")
    production = production.replace("    selected=rows(out/'selected.jsonl');shots=rows(out/'field_shots.jsonl')",
        "    require(read(out/'temporal.stage.json')['status']=='PASS_TEMPORAL_EXECUTION' and "
        "read(out/'temporal.stage.json')['adapter_enabled'] is True,'actual trained B time stage required')\n"
        "    require(read(out/'spatial.stage.json')['status'] in ('PASS_STRICT_SOURCE_FIELD_SPATIAL',"
        "'PASS_EMPTY_SPACE_NO_MODEL_CALL'),'complete field spatial inference required')\n"
        "    for item in manifest['records']:require(sha(item['source_path'])==item['source_sha256'],'final source changed')\n"
        "    selected=rows(out/'selected.jsonl');shots=rows(out/'field_shots.jsonl')")
    production = production.replace('candidate_Z_8B', 'candidate_B2_8B').replace('PASS_COMPLETE_Z_8B_PACKAGE', 'PASS_COMPLETE_B2_8B_PACKAGE_ON_LINUX')
    production = production.replace('complete_pipeline_parameters=8767123696', 'complete_pipeline_parameters=8782459120')
    production = production.replace("comparison_to_B='FULL_RECIPE_DIFFERENCE_NOT_PURE_TEMPORAL_ABLATION'",
        "comparison_to_B='PRESERVED_TRAINED_B_NATIVE_INPUT_AND_SOURCE_FIELD_RECIPE',"
        "selected_adapter_sha256=config['b_adapter_sha256'],new_optimizer_updates=0,new_T_training_started=False,"
        "automatic_return=False,uploaded=False")
    put('production.py', production)
    config = json.loads(source('next_round_v1/config.json'))
    config.update(schema='AIC_B2_SCORE_ALIGNED_PACKAGE_V1', candidate_arm='B2_TRAINED_B_NATIVE_PTS_SOURCE_FIELD',
        temporal_adapter_enabled=True, new_optimizer_updates=0, new_T_training_started=False,
        whole_teacher_supervision_admitted=False, official_score=None,
        original_scored_B_zip_sha256='86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54',
        model_revision=json.loads(source('temporal_sft8b_full_v1/config.json'))['revision'],
        expected_base_sha256='74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59',
        base_parameters=8767123696, complete_parameters=8782459120,
        trained_B_report=REMOTE + '/temporal_sft8b_full_v1/train_01/train_report.json',
        existing_B_dev_decision=REMOTE + '/temporal_sft8b_dev_v1/decision.json',
        cpu_cache_root=REMOTE + '/next_round_v1',
        current_runner=REMOTE + '/resource_unlimited_v1_20261007/gpu_run.py',
        b2_input_contract={'sampling': 'INTEGER_FLOOR_64_NATIVE_ORDINAL_ENDPOINTS',
            'clock': 'ACTUAL_NATIVE_PTS_ALL_FORMAT_BRANCHES', 'decoder': 'SEQUENTIAL_PYAV_RGB24',
            'prompt': 'UNCHANGED_B_1_TO_5', 'allow_empty': False, 'truncation': False,
            'max_input_tokens': 16384, 'video_size': config['video_size']},
        developer_repeated=False, confirm_read=False, automatic_return=False, uploaded=False)
    put('config.json', json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS_NEW_B2_CONTROL_TREE', 'path': str(OUT)}))


if __name__ == '__main__':
    main()
