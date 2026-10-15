"""Fail-closed byte bindings. Importing this module never starts model work."""
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path
import sys

INITIAL_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
VIDEO_SIZE = {'shortest_edge': 4096, 'longest_edge': 25165824}
HERE = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False,
                  default=lambda x: str(x) if isinstance(x, Fraction) else (_ for _ in ()).throw(TypeError(type(x).__name__)))
        stream.write('\n')


def bound(ref):
    require(set(ref) == {'path', 'sha256'}, 'exact path/SHA binding required')
    p = Path(ref['path']).resolve(strict=True)
    require(p.is_file() and sha(p) == ref['sha256'], 'byte binding differs: ' + str(p))
    return p


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_lock(path, expected):
    require(sha(path) == expected, 'lock SHA differs')
    lock = read(path)
    for p, digest in lock['files'].items():
        require(sha(p) == digest, 'locked bytes changed: ' + p)
    for p in HERE.glob('*.py'):
        require(lock['files'].get(str(p)) == sha(p), 'runtime code absent from lock: ' + str(p))
    return lock


def helpers(config):
    run = Path(config['historical_run_root']).resolve(strict=True)
    student = load(run/'teacher_student_autopilot_v14/train_student.py', 'silver_native_student')
    # Bind only needed public modules; do not import an old launcher or let
    # its public common.py collide with this standalone runtime's common.py.
    sys.path[:0] = [str(run/'teacher_student_autopilot_v14'), str(run/'baseline_a_pts_v1'),
                   str(run/'baseline_a_pts_v1/vendor'), str(run/'temporal_sft8b_v1')]
    for name in ('contracts', 'constrained_json'):
        load(run/'teacher_student_autopilot_v14/precision_helpers'/(name+'.py'), name)
    load(run/'teacher_student_autopilot_v14/autopilot_common.py', 'autopilot_common')
    sft = load(run/'temporal_sft8b_v1/sft_contract.py', 'sft_contract')
    require(student.VIDEO_SIZE == VIDEO_SIZE, 'registered pixel budget differs')
    # Import identities are asserted after legacy helpers have arranged paths.
    video = load(run/'balanced_two_window_risk_v3/bw_video.py', 'silver_explicit_video')
    smoke = load(run/'temporal_sft8b_v1/verify_saved_smoke.py', 'silver_saved_smoke')
    return student, video, sft, smoke


def evaluation_keys(jobs, protocol):
    require(set(j['role'] for j in jobs.values()) == {'train','process_dev','locked_evaluation'}, 'foreign role')
    dev=[k for k,j in jobs.items() if j['role']=='process_dev']
    locked=[k for k,j in jobs.items() if j['role']=='locked_evaluation']
    counts=protocol['counts']
    require(len(dev)==counts['process_dev']['windows'] and len(locked)==counts['locked_evaluation']['windows'], 'evaluation denominator differs')
    return dev,locked


def admit(config_path, lock_path, expected_lock, phase):
    require(sys.dont_write_bytecode is True, 'invoke entry with python -B to preserve frozen directories')
    lock = verify_lock(lock_path, expected_lock)
    require(lock['files'].get(str(Path(config_path).resolve())) == sha(config_path), 'config absent from lock')
    c = read(config_path)
    require(c['schema'] == 'CONTRAST_BOUNDARY_NATIVE_RUNTIME_V1', 'unsupported config')
    for name in ('epochs','seed','micro_batch','gradient_accumulation'):
        require(type(c[name]) is int,'integer config recipe field required: '+name)
    require(c['initial_adapter_sha256'] == INITIAL_SHA and c['expected_base_sha256'] == BASE_SHA, 'B identity differs')
    require(c['seed'] == 20261011 and c['epochs'] == 2 and c['micro_batch'] == 1 and c['gradient_accumulation']==4, 'fixed recipe differs')
    require(c['optimizer'] == dict(name='AdamW', lr=1e-5, betas=[.9, .999], eps=1e-8,
                                  weight_decay=0, clip_norm=1), 'optimizer recipe differs')
    run = Path(c['historical_run_root']).resolve(strict=True)
    dependency_names = (
        'teacher_student_autopilot_v14/train_student.py',
        'teacher_student_autopilot_v14/source_color.py',
        'teacher_student_autopilot_v14/autopilot_common.py',
        'teacher_student_autopilot_v14/config.json',
        'teacher_student_autopilot_v14/precision_helpers/contracts.py',
        'teacher_student_autopilot_v14/precision_helpers/constrained_json.py',
        'teacher_student_autopilot_v14/precision_helpers/engine.py',
        'teacher_student_autopilot_v14/precision_helpers/training_target.py',
        'next_round_v1/video_contract.py', 'next_round_v1/common.py',
        'balanced_two_window_risk_v3/bw_video.py',
        'baseline_a_pts_v1/exact_pts.py', 'baseline_a_pts_v1/native_frames.py',
        'baseline_a_pts_v1/pts_contract.py', 'baseline_a_pts_v1/a_contract.py',
        'baseline_a_pts_v1/vendor/p2j_core.py',
        'temporal_sft8b_v1/sft_contract.py', 'temporal_sft8b_v1/verify_saved_smoke.py',
        'resource_unlimited_v1_20261007/gpu_run.py',
        'resource_unlimited_v1_20261007/physical_capacity.py')
    for name in dependency_names:
        p = (run/name).resolve(strict=True)
        require(lock['files'].get(str(p)) == sha(p), 'native/runtime dependency absent from lock: '+name)
    for key in ('quality_contract', 'science_contract', 'event_metrics'):
        p = bound(c[key])
        require(lock['files'].get(str(p)) == sha(p), 'scientific dependency absent from lock: '+key)
    policy = bound(c['resource_policy'])
    require(lock['files'].get(str(policy)) == sha(policy), 'live resource policy absent from lock')
    model_root = Path(c['model_dir']).resolve(strict=True)
    weight_index = read(model_root/'model.safetensors.index.json')
    model_files = {'model.safetensors.index.json', 'config.json', 'generation_config.json'} | set(weight_index['weight_map'].values())
    for name in model_files:
        p = (model_root/name).resolve(strict=True)
        require(p.parent == model_root and lock['files'].get(str(p)) == sha(p), 'base file absent from lock: '+name)
    protocol = read(bound(c['protocol']))
    require(all(c[k]==protocol[k] for k in ('epochs','seed','micro_batch','gradient_accumulation')),
            'config and frozen protocol training recipe differs')
    require(protocol['initial_adapter_sha256'] == INITIAL_SHA and protocol['fixed_final_checkpoint_only'] is True,
            'frozen protocol differs')
    require(protocol['quality']['positive_empty_window_count_nonincrease'] is True, 'explicit empty gate missing')
    require(protocol['quality']['locked_positive_macro_F1_gain_min']=='0.05', 'quality recipe differs')
    for key in ('protocol', 'plan', 'reference_registry', 'processor_binding'):
        p = bound(c[key])
        require(lock['files'].get(str(p)) == sha(p), 'input absent from lock: ' + key)
    plan = read(bound(c['plan']))
    require(len(plan['jobs']) == protocol['counts']['total_windows'] and len({j['window']['window_id'] for j in plan['jobs']}) == protocol['counts']['total_windows'], 'frozen plan denominator differs')
    jobs = {j['window']['window_id']: j for j in plan['jobs']}
    registry = read(bound(c['reference_registry']))
    records = registry.get('records', registry)
    require(set(records) == set(jobs), 'pending/rejected records must remain in denominator')
    qc_dir = bound(c['quality_contract']).parent
    sys.path.insert(0, str(qc_dir))
    quality = load(bound(c['quality_contract']), 'quality_contract')
    silver = load(bound(c['science_contract']), 'science_contract')
    silver.validate_protocol(protocol)
    require(silver.validate_plan(plan, protocol)==jobs, 'science plan differs')
    events = load(bound(c['event_metrics']), 'silver_event_metrics')
    refs = {}
    reference_sha = {}; sidecars = {}
    for key, row in records.items():
        if row.get('reference'):
            ref = read(bound(row['reference']))
            silver.verify_window(ref, jobs[key])
            for binding in silver.evidence_bindings(ref):
                ep=bound(binding)
                require(lock['files'].get(str(ep))==binding['sha256'],'scientific evidence absent from freeze')
            refs[key] = ref
            reference_sha[key] = row['reference']['sha256']
            require(lock['files'].get(str(bound(row['reference']))) == reference_sha[key], 'reference absent from lock')
        else:
            require(row.get('status', row.get('state', '')).startswith(('PENDING', 'REJECTED')), 'missing reference must be explicit')
    # Only declared train/process_dev/locked sources may enter the runtime.
    dev, locked = evaluation_keys(jobs, protocol)
    sources = {}
    role_sources = {}; sha_roles={}
    for key, j in jobs.items():
        w = j['window']; group = j['source_group']; role = j['role']
        require(group not in role_sources or role_sources[group] == role, 'source split leakage')
        role_sources[group] = role
        require(w['source_sha256'] not in sha_roles or sha_roles[w['source_sha256']]==role, 'source SHA role leakage')
        sha_roles[w['source_sha256']]=role
        source = bound(c['source_files'][w['source_sha256']])
        require(c['source_files'][w['source_sha256']]['sha256'] == w['source_sha256'], 'source media SHA differs')
        require(lock['files'].get(str(source)) == w['source_sha256'], 'source media absent from lock')
        sources[key] = source
    binding = read(bound(c['processor_binding']))
    for row in binding['rows']:
        p = Path(c['processor_dir'])/row['file']
        require(sha(p) == row['sha256'] and lock['files'].get(str(p.resolve())) == row['sha256'], 'processor snapshot differs')
    initial = Path(c['initial_adapter_dir'])
    require(sha(initial/'adapter_model.safetensors') == INITIAL_SHA, 'original B adapter changed')
    for name in ('adapter_model.safetensors', 'adapter_config.json'):
        p = (initial/name).resolve()
        require(lock['files'].get(str(p)) == sha(p), 'adapter absent from lock')
    # Complete all static admission before any torch/decoder/processor import.
    train_records = {key: refs.get(key, dict(training_admitted=False)) for key in jobs}
    schedule = silver.training_schedule(plan, train_records, protocol)
    require(c['training_authorization']['unlocked'] is True and c['training_authorization']['complete_silver_admitted'] is True,
            'training has not been unlocked by reviewed reference admission')
    for key in schedule['window_ids']:
        require(refs[key]['training_admitted'] is True, 'unadmitted training target')
        if key in c.get('target_sidecars', {}):
            p = bound(c['target_sidecars'][key])
            require(lock['files'].get(str(p)) == sha(p), 'target sidecar absent from lock')
            sidecars[key] = read(p)
        from objective import target
        text, exact = target(refs[key], jobs[key]['window'], sidecars.get(key), reference_sha[key])
        # The original parser also rejects decimal literals which float cannot
        # retain exactly; a representable decimal alone is insufficient.
        parser = load(run/'teacher_student_autopilot_v14/precision_helpers/contracts.py', 'silver_static_original_parser')
        grammar = load(run/'teacher_student_autopilot_v14/precision_helpers/constrained_json.py', 'silver_static_original_grammar')
        w = jobs[key]['window']; duration = Fraction(w['domain_end_exact'])-Fraction(w['domain_start_exact'])
        parsed, errors, warnings = parser.parse_segments(text, duration, allow_empty=True)
        require(parsed is not None and not errors and grammar.BoundedSegmentsGrammar(duration, allow_empty=True).complete(text),
                'serialized target violates original parser/grammar: '+key)
    require(all(k in refs for k in dev + locked), 'complete evaluation references pending')
    require(c['final_only_evaluation_window_ids'] == sorted(dev + locked), 'pre-registered final-only evaluation differs')
    from scientific_gate import reference_coverage
    coverage = reference_coverage(jobs, refs, quality, protocol)
    require(coverage['status'] == 'PASS_FIXED_EVALUATION_REFERENCE_COVERAGE',
            'fixed evaluation reference coverage insufficient: ' + str(coverage['checks']))
    require(phase in ('train', 'evaluate', 'candidate', 'candidate_replay', 'candidate_package', 'nontest', 'nontest_replay', 'nontest_package'), 'unknown phase')
    if phase in ('candidate_replay', 'candidate_package', 'nontest_replay', 'nontest_package'):
        require(Path(c['nontest_output_dir' if phase.startswith('nontest') else 'candidate_output_dir']).is_dir(), 'completed candidate input directory required')
    else:
        require(not Path(c[phase+'_output_dir']).exists(), 'fresh output directory required')
    return dict(config=c, jobs=jobs, refs=refs, sources=sources, schedule=schedule, quality=quality,
                events=events, lock=lock, lock_path=lock_path, lock_sha=expected_lock,
                config_path=config_path, config_sha=sha(config_path), protocol=protocol,
                reference_sha=reference_sha, sidecars=sidecars, reference_coverage=coverage)
