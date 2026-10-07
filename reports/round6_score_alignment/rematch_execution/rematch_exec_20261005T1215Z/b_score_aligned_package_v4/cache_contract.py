"""Reuse SHA-frozen full-source fields, never a different model's temporal output."""
from common import *
import shutil


def try_reuse(scope, out, manifest, clocks, selected, domain):
    from field_contract import build_field_requests
    bindings = read(HERE / 'cache_bindings.json')
    binding = bindings['scopes'].get(scope)
    if not selected or not binding or not binding['cpu_eligible']:
        return False
    cache = Path(binding['path'])
    for name, digest in binding['files'].items():
        require(sha(cache / name) == digest, 'frozen source cache changed: ' + name)
    require(binding['manifest_sha256'] == settings()['inputs'][scope]['manifest_sha256'] and
            binding['registry_sha256'] == settings()['inputs'][scope]['registry_sha256'], 'cache source binding differs')
    field = rows(cache / 'field_frames.jsonl')
    desired = {(row['video_id'], row['source_frame']): row for row in domain}
    existing = {(row['video_id'], row['source_frame']): row for row in field}
    if len(desired) != len(domain) or len(existing) != len(field) or existing != desired:
        return False
    shots = rows(cache / 'field_shots.jsonl')
    requests = rows(cache / 'anchor_requests.jsonl')
    require(build_field_requests(field, shots, 8) == requests, 'cache is not complete same-frame source-field schedule')
    schedule = read(cache / 'schedule.stage.json')
    require(schedule['status'] == 'PASS_TIME_INDEPENDENT_SOURCE_FIELD' and
            schedule['temporal_selection_used_for_boundaries'] is False and schedule['max_gap'] == 8,
            'source-field cache depends on temporal decisions')
    for name, key in (('field_frames.jsonl', 'field_frames_sha256'), ('field_shots.jsonl', 'shots_sha256'),
                      ('anchor_requests.jsonl', 'requests_sha256')):
        require(sha(cache / name) == schedule[key], 'cache schedule hashes differ')
    # Caller wrote the new B2 selection; Z temporal/selected files are never copied.
    for name in ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl'):
        require(not (out / name).exists(), 'refuse overwrite B2 field output')
        shutil.copyfile(cache / name, out / name)
        require(sha(out / name) == binding['files'][name], 'copied field bytes differ')
    value = dict(schedule, selected_frames=len(selected), source_cache=str(cache),
                 reused_time_independent_source_field=True, old_temporal_results_reused=False)
    write(out / 'schedule.stage.json', value)
    if binding['spatial_eligible']:
        spatial = read(cache / 'spatial.stage.json')
        outputs = rows(cache / 'anchor_output.jsonl')
        require(spatial['status'] == 'PASS_STRICT_SOURCE_FIELD_SPATIAL' and spatial['invalid'] == 0 and
                spatial['logical_parameters'] == 8767123696 and spatial['time_adapter_enabled'] is False and
                len(outputs) == len(requests) == spatial['rows'], 'cached native base spatial result incomplete')
        for request, output in zip(requests, outputs):
            require(output['status'] == 'MODEL_OK' and output['used_fallback'] is False and
                    request['anchor_request_sha256'] == output['anchor_request_sha256'] and
                    request['expected_pixel_sha256'] == output['decoded_pixel_sha256'], 'cached anchor identity differs')
        shutil.copyfile(cache / 'anchor_output.jsonl', out / 'anchor_output.jsonl')
        require(sha(out / 'anchor_output.jsonl') == binding['files']['anchor_output.jsonl'], 'copied space bytes differ')
        write(out / 'spatial.stage.json', dict(spatial, reused_cache=True, model_calls_this_B2_candidate=0,
            source_cache=str(cache), cache_binding_sha256=sha(HERE / 'cache_bindings.json')))
    write(out / 'cache_reuse_receipt.json', dict(status='PASS_SHA_FROZEN_SOURCE_FIELD_CACHE',
        source_cache=str(cache), cpu_reused=True, spatial_reused=binding['spatial_eligible'],
        temporal_reused=False, source_binding_sha256=sha(HERE / 'cache_bindings.json'),
        files={name: sha(out / name) for name in ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl')}))
    return True
