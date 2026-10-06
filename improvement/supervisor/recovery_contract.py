"""Evidence contract for a generic spatial reader repair, without temporal retuning."""
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work')
RECOVERY_KIND = 'exact_source_frame_reader_v1'
TEMPORAL_FIELDS = ('video_id', 'source_group', 'segments_sec', 'segments_frames',
                   'query', 'policy', 'adapter', 'constrained_json', 'constraint_backend', 'sampling')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def frozen_temporal(directory, root=ROOT):
    directory = Path(directory).resolve()
    root = Path(root).resolve()
    if not directory.is_relative_to(root / 'runs'):
        raise ValueError('recovery temporal input outside project runs')
    launch = json.loads((directory / 'launch.json').read_text())
    report = json.loads((directory / 'freeze_report.json').read_text())
    if report['status'] != 'passed' or report['changed_fields'] or report['videos'] != 174:
        raise ValueError('temporal freeze/identity gate failed')
    if sha(directory / 'temporal.jsonl') != report['temporal_sha256']:
        raise ValueError('frozen temporal file changed')
    if sha(directory / 'launch.json') != report['launch_sha256']:
        raise ValueError('temporal launch changed')
    original = Path(launch['original_run']).resolve()
    if original != root / 'runs/improvement_test174_multi_v2':
        raise ValueError('recovery original run identity mismatch')
    for name, digest in launch['original_artifact_hashes'].items():
        if Path(name).name != name or sha(original / name) != digest:
            raise ValueError('original failed evidence changed: ' + name)
    if sha(root / 'inference/test_index.json') != launch['index_sha256']:
        raise ValueError('temporal test index changed')
    for relative, digest in launch['source_hashes'].items():
        if relative != 'dev' and sha(root / relative) != digest:
            raise ValueError('frozen temporal/model code changed: ' + relative)
    rows = read(directory / 'temporal.jsonl')
    by_id = {str(r['video_id']): r for r in rows}
    if len(rows) != 174 or len(by_id) != 174:
        raise ValueError('temporal exact unique coverage failed')
    original_rows = read(original / 'status.jsonl')
    if len(original_rows) != report['compared_original_complete_rows']:
        raise ValueError('partial-run comparison coverage mismatch')
    for old in original_rows:
        new = by_id[str(old['video_id'])]
        if any(old[k] != new[k] for k in TEMPORAL_FIELDS):
            raise ValueError('original temporal decision was changed')
        if any(old['metadata'][k] != new['metadata'][k] for k in ('n_frames', 'fps', 'width', 'height')):
            raise ValueError('original temporal metadata was changed')
    for r in rows:
        if r['status'] not in ('ok', 'valid_empty') or r['policy'] != 'multi' or r['query'] is not None:
            raise ValueError('invalid frozen temporal result')
        if r['adapter'] is not None or r['constrained_json'] is not True:
            raise ValueError('unapproved temporal model or decoding')
        last = 0
        n = r['metadata']['n_frames']
        for interval in r['segments_frames']:
            if len(interval) != 2 or any(type(x) is not int for x in interval):
                raise ValueError('frozen frame intervals must use integers')
            a, b = interval
            if not 0 <= last <= a < b <= n:
                raise ValueError('invalid or overlapping frozen frame intervals')
            last = b
        if bool(r['segments_frames']) != (r['status'] == 'ok'):
            raise ValueError('frozen empty status mismatch')
    return by_id, launch, report


def validate_recovery(launch, statuses, root=ROOT):
    root = Path(root).resolve()
    proof = launch['engineering_recovery']
    if proof['kind'] != RECOVERY_KIND or launch['policy'] != 'multi':
        raise ValueError('unapproved engineering recovery')
    if not proof['no_new_holdout_or_tuning'] or not proof['all_test_videos_replayed']:
        raise ValueError('recovery must apply the same frozen algorithm to every test video')
    temporal_dir = Path(proof['temporal_run'])
    frozen, temporal_launch, report = frozen_temporal(temporal_dir, root)
    if proof['temporal_sha256'] != report['temporal_sha256']:
        raise ValueError('spatial launch temporal identity mismatch')
    for field in ('holdout_plan_sha256', 'holdout_summary_sha256', 'index_sha256'):
        if launch[field] != temporal_launch[field]:
            raise ValueError('recovery lineage mismatch: ' + field)
    actual_sources = {str(p.relative_to(root)): sha(p) for p in (root / 'inference_recovery').glob('*.py')}
    if actual_sources != proof['recovery_source_hashes']:
        raise ValueError('recovery source changed')
    if not actual_sources or 'inference_recovery/reader.py' not in actual_sources:
        raise ValueError('corrected reader source is missing')
    resource = json.loads((root / 'improvement_round1' / (proof['job_name'] + '.resource.json')).read_text())
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or resource['command'] != launch['command']:
        raise ValueError('recovery GPU job has not completed with its exact launch')
    if len(statuses) != 174 or {str(r['video_id']) for r in statuses} != set(frozen):
        raise ValueError('recovery spatial status coverage failed')
    for r in statuses:
        original = frozen[str(r['video_id'])]
        if any(r[k] != original[k] for k in TEMPORAL_FIELDS):
            raise ValueError('spatial replay changed frozen temporal decisions')
        if any(r['metadata'][k] != original['metadata'][k] for k in ('n_frames', 'fps', 'width', 'height')):
            raise ValueError('spatial replay changed video metadata')
    return {'kind': RECOVERY_KIND, 'temporal_sha256': report['temporal_sha256'],
            'compared_original_complete_rows': report['compared_original_complete_rows'],
            'recovery_source_hashes': actual_sources, 'resource_sha256': sha(root / 'improvement_round1' / (proof['job_name'] + '.resource.json')),
            'all_174_frozen_temporal_decisions_preserved': True}


def validate_recovery_artifacts(run, launch, statuses, root=ROOT):
    """Bind the actual inference manifest and every row to the accepted repair."""
    root, run = Path(root).resolve(), Path(run).resolve()
    proof = launch['engineering_recovery']
    review_path = root / 'improvement_round1/recovery_reader_review.json'
    if sha(review_path) != proof['reader_review_sha256']:
        raise ValueError('supervisor recovery review changed')
    review = json.loads(review_path.read_text())
    if review['status'] != 'passed' or review['source_hashes'] != proof['recovery_source_hashes']:
        raise ValueError('spatial repair is not the reviewed implementation')
    manifest_path = run / 'status.jsonl.recovery.json'
    manifest = json.loads(manifest_path.read_text())
    expected_params = dict(max_pixels=131072, max_video_frames=64, detect_fps=2.0,
                           crop_stride=15, crop_tokens=128, device_map='auto', attn_implementation='sdpa')
    if manifest['fixed_parameters'] != expected_params:
        raise ValueError('spatial parameters changed')
    if manifest['expected_videos'] != 174 or manifest['index_sha256'] != launch['index_sha256']:
        raise ValueError('spatial input identity changed')
    if manifest['model_path'] != str(root / 'models/Qwen3-VL-4B-Instruct'):
        raise ValueError('spatial base model changed')
    source_values = dict(temporal_sha256=proof['temporal_sha256'],
                         reader_sha256=proof['recovery_source_hashes']['inference_recovery/reader.py'],
                         spatial_replay_sha256=proof['recovery_source_hashes']['inference_recovery/spatial_replay.py'])
    for name, expected in source_values.items():
        if manifest[name] != expected:
            raise ValueError('actual spatial provenance mismatch: ' + name)
    for row in statuses:
        evidence = row['recovery']
        for name, expected in source_values.items():
            if evidence[name] != expected:
                raise ValueError('row spatial provenance mismatch: ' + name)
        if evidence['model_tree_sha256'] != manifest['model_tree_sha256']:
            raise ValueError('row base model identity mismatch')
    return {'manifest_sha256': sha(manifest_path), 'model_tree_sha256': manifest['model_tree_sha256'],
            'fixed_spatial_parameters_verified': True}
