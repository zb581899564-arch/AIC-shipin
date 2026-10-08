"""Exact C-to-B diagnostic bindings. Unique name avoids old helper imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
CAD = RUN / 'context_advisory_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value, fresh=True):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if fresh:
        with p.open('x', encoding='utf-8', newline='\n') as f:
            f.write(data)
    else:
        tmp = p.with_suffix(p.suffix + '.tmp'); tmp.write_text(data, encoding='utf-8'); tmp.replace(p)


def utc():
    return datetime.now(timezone.utc).isoformat()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def helpers():
    sys.path.insert(0, str(CAD))
    cad = load(CAD / 'runtime.py', 'bdiag_cad_runtime')
    student, old, _, _ = cad.bind_helpers()
    ex = load(CAD / 'experiment.py', 'bdiag_cad_experiment')
    teacher_root = RUN / 'teacher_student_autopilot_v14'
    sys.path.insert(0, str(teacher_root))
    boundary = load(teacher_root / 'boundary_ids.py', 'boundary_ids')
    teacher = load(teacher_root / 'teacher_label.py', 'bdiag_frozen_teacher')
    return cad, ex, student, old, teacher, boundary


def verify():
    lock = read(HERE / 'source_lock.json')
    for p, expected in lock['files'].items():
        require(sha(p) == expected, 'frozen B diagnostic dependency changed: ' + p)
    for name in ('start.json', 'registration.json'):
        if (HERE / name).exists():
            require(read(HERE / name)['source_lock_sha256'] == sha(HERE / 'source_lock.json'), 'registration lock changed')
    return lock


def progress(stage, **fields):
    value = dict(stage=stage, utc=utc(), pid=__import__('os').getpid(),
        new_optimizer_updates=0, new_8B_calls=0, official_score=None, uploaded=False, **fields)
    save(HERE / 'progress.json', value, fresh=False)
    print(json.dumps(value, ensure_ascii=False), flush=True)


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def iou(a, b):
    n = overlap(a, b)
    return n / ((a[1]-a[0]) + (b[1]-b[0]) - n)


def matched_projection(value, observation, candidate, boundary):
    boundary.validate_decision(value, observation)
    projected = boundary.canonical_response(value, observation)
    origin = observation['window_pts_start_sec']
    matches = [[origin+x['start_sec'], origin+x['end_sec']] for x in projected['retained_segments']
        if overlap([origin+x['start_sec'], origin+x['end_sec']], candidate) > 0]
    if value['state'] != 'KEEP' or len(matches) != 1:
        return {'status': 'UNKNOWN_UNCONFIRMED_CANDIDATE', 'candidate_boundary_seconds': None,
            'original_model_state': value['state'], 'overlapping_segments': len(matches),
            'candidate_outside_unknown_not_negative': True}
    return {'status': 'WEAK_UNIQUE_OVERLAPPING_CANDIDATE', 'candidate_boundary_seconds': matches[0],
        'original_model_state': value['state'], 'overlapping_segments': 1,
        'same_event_semantic_identity': 'UNKNOWN_NO_INDEPENDENT_HUMAN_EVIDENCE',
        'candidate_outside_unknown_not_negative': True}


def diagnostic_prompt(observation, candidate, teacher, boundary):
    template = (Path(teacher.HERE) / 'teacher_prompt.txt').read_text(encoding='utf-8')
    table = boundary.tables(observation)
    inside = ['F'+str(f['evidence_frame_id']) for f in table['evidence_frames']
        if candidate[0] <= observation['actual_pts_sec'][f['evidence_frame_id']] < candidate[1]]
    hint = {'candidate_source_seconds': candidate,
        'candidate_local_seconds': [x-observation['window_pts_start_sec'] for x in candidate],
        'sampled_candidate_frame_ids': inside, 'proposal_is_not_truth': True}
    focused = ('\n本次是独立登记的候选事件边界诊断。下述时间仅为8B提出的候选，不能当成真实高光、'
        '正确边界或教师答案。只在实际提供的画面支持时辨认该候选附近的同一事件，并按上面的原生B/F'
        '输出规则给出可见事件的完整边界；不能为了贴合候选而裁段、扩段或填补证据。'
        '无法辨认、事件歧义、或采样缺少证据时选择UNKNOWN。候选外内容不属于负类监督，'
        'NO_HIGHLIGHT也不会被本程序当作候选外负类或训练空标签。不得根据窗口位置推断事件。\n'
        'CANDIDATE_PROPOSAL_JSON=' + json.dumps(hint, ensure_ascii=False, sort_keys=True))
    return boundary.prompt(template, observation) + focused
