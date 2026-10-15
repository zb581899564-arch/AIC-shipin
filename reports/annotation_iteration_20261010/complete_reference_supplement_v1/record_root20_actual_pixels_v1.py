"""Seal the actual ROOT post-teacher PNG observations and complete fact reading."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).parent
def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bind(path):
    return {'path': str(path), 'sha256': sha(path)}

native_path = R / 'native_reviews/20_cjibtmSLxQ4_W13.native_review.json'
student_path = R / 'student_reviews/20_cjibtmSLxQ4_W13.independent_student64_review_v1.json'
native = read(native_path)
student = read(student_path)
native_notes = {
    12: '双臂屈肘、肩头较靠横梁；可支持有限屈臂升高，不能确定此前首次抓梁。',
    14: '两臂较伸直，肩头低于横梁；与F12对照支持局部回低，不确定完整放手。',
    17: '树林远景浅色长斜物、暗圆端及邻近小暗影；不足以明确手撑倒立的完整动作，保留UNKNOWN。',
    24: '中央粗长树干样物近直立，暗人物局部在其底侧，接触细节不足。',
    27: '粗长物明显倾斜、右侧模糊人物偏离；不接受普通奔跑叙述，不推断用力或谁导致倾斜。',
    28: '长物处于低横位，中央有圆暗端，地面灰影；不接受人物贴地翻滚或完整毁物结果。',
    33: '人物在高窗台附近直起，手近窗侧，腿仍屋外；有限站位成立。',
    34: '上身在窗框后或被窗框遮挡，腿部仍可见于外侧；不确定完整进入室内。',
    42: '室内低亮度胡须男子近景、手近下巴、前景暗遮；普通连续面部姿态，没有另立有限高光。',
    57: '彩色住宅前人物步行或持手腹前，后有垃圾桶；普通移动，保持NO。',
    61: '门口人与抱孩子成人、前景推车，人物手部交流；接触细节与声音未知，保持普通交流NO。',
}
student_notes = {
    14: '实际processor预览仍能分辨双臂较伸直、肩头回低的有限关系。',
    17: '实际processor预览长物斜立和附近暗影，完整手撑倒置动作不可可靠分辨，UNKNOWN不清除。',
    24: '实际processor预览中央长物近竖直、下端旁人影细节低清；仅有限位置关系。',
    27: '实际processor预览仍可分辨倾斜长物与旁侧人影，因果和动作目的不明。',
    28: '实际processor预览可分辨低横长物及中央圆暗端；不推出人物滑地翻滚。',
    34: '实际processor预览可见窗框遮上身、腿仍外侧；完整入室结果保持未知。',
}
observations = []
for kind, inventory, notes in [('native', native['frames'], native_notes), ('actual_student', student['student_view_inventory'], student_notes)]:
    assert len(inventory) == 64
    for index, note in notes.items():
        frame = inventory[index]
        assert frame['frame_id'] == f'F{index:02d}' and sha(frame['path']) == frame['png_sha256']
        observations.append({'kind': kind, 'frame_id': frame['frame_id'], 'path': frame['path'], 'png_sha256': frame['png_sha256'], 'bound_rgb_pixel_sha256': frame['rgb_pixel_sha256'], 'source_ordinal': frame['source_ordinal'], 'global_seconds_exact': frame['global_seconds_exact'], 'local_seconds_exact': frame['local_seconds_exact'], 'root_actual_visible_fact': note})
assert len(observations) == 17
call = R / 'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5/call36'
facts = [bind(call / f'w20_group{index:02d}.json') for index in range(16)]
document = {
    'status': 'ROOT_ACTUAL_POSTTEACHER_17_PNGS_AND_ALL64_FACT_REVIEW_NOT_REFERENCE_ADMISSION',
    'utc': datetime.now(timezone.utc).isoformat(), 'window_id': native['window_id'],
    'native_review': bind(native_path), 'student_review': bind(student_path),
    'original_teacher_fact_outputs': facts, 'original_rejected_teacher_proposal': bind(call / 'w20_proposal.json'),
    'original_rejected_scope': bind(call / 'w20_completed_scope_audit.json'),
    'frames': observations, 'actual_new_native_pngs_viewed': 11, 'actual_new_student_pngs_viewed': 6,
    'root_read_all64_teacher_facts': True, 'root_read_all64_native_and_student_facts': True,
    'root_direct64_image_review': False, 'root_native_video_view': False,
    'root_not_blind': True, 'candidate_prediction_exposure': False,
    'old_preteacher_review_and_UNKNOWN_15_to_18_preserved': True,
    'all_NO_ranges_reviewed': True,
    'major_conflicts': [
        'TeacherF16..18 asserts moving/standing wood but native and student identification differ; retain UNKNOWN15..18.',
        'TeacherF20 uses force/拉伸 beyond direct visibility; finite target does not adopt it.',
        'TeacherF26..28 ordinary run/sliding/rolling conflicts with actual upright-to-tilted-to-low long-object images; preserve only preregistered finite local position-change target.',
        'TeacherF32..34 claims successful entry; actualF34 does not prove full entry, only partial body behind frame.',
        'Malformed proposal descriptive segmentation and classroom-student visibility are rejected historical content, not labels.',
    ],
    'new_model_calls': 0, 'new_video_decode': 0, 'new_optimizer_updates': 0,
}
destination = R / '20_cjibt_w13_root_actual_postteacher_pixels_v1.json'
serialized = json.dumps(document, ensure_ascii=False, indent=2) + '\n'
with destination.open('x', encoding='utf-8', newline='\n') as handle:
    handle.write(serialized)
print(json.dumps(bind(destination), ensure_ascii=False))
