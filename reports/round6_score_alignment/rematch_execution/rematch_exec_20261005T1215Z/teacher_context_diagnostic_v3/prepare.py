"""Register label-independent pairs and byte-based output estimate before freezing."""
import hashlib
import json
import socket

import diagnostic as d

d.c.require(socket.gethostname() == 'inspur-NP5570M5', 'unexpected diagnostic registration host')
records_path = d.V7 / 'pilot_01/validated/validated_records.jsonl'
records = d.c.rows(records_path)
selected = d.choose(records)
original_http_bytes = sum((d.V7 / 'teacher_01/windows' / r['window_id'] / 'http/request.json').stat().st_size
                          for r in selected)
# Four original-target requests, two source overviews and their base64 payloads, logs/schema/answer headroom.
overview_rgb_upper_bound = 4 * 64 * 384 * 384 * 3
planned = 2 * original_http_bytes + 5 * overview_rgb_upper_bound + 8 * (8 << 20)
manifest = {'schema': 'AIC_RELATIVE_SUMMARY_DIAGNOSTIC_REGISTRATION_V3', 'utc': d.c.utc(),
            'scientific_change': 'whole-source visible summary and marginal target information before keep decision; four fresh context requests plus four real weak reviews',
            'selection': 'two minimum SHA256(window_id) per split from original calibration excluding the registered v2 pair; native64 and outside-window metadata only; no labels or review used',
            'window_ids': [r['window_id'] for r in selected], 'splits': [r['split'] for r in selected],
            'original_records_sha256': d.c.sha(records_path),
            'original_done_sha256': {r['window_id']: d.c.sha(d.V7 / 'teacher_01/windows' / r['window_id'] / 'done.json') for r in selected},
            'request_count': 8, 'annotation_requests': 4, 'review_requests': 4,
            'target_frames_per_request': 64, 'overview_max_frames': 64,
            'overview_max_edge': 384, 'diagnostic_outputs_are_training_labels': False,
            'original_target_request_bytes_for_four_windows': original_http_bytes,
            'predicted_incremental_output_bytes': planned, 'capacity_mode': 'ACTUAL_CAPACITY_ONLY',
            'queue_max_sec': 86400, 'job_wall_max_sec': 10800}
d.c.write(d.HERE / 'manifest.json', manifest, fresh=True)
lock = d.c.read(d.V7 / 'source_lock.json')
files = dict(lock['files'])
files.update(d.c.read(d.HERE / 'cpu_acceptance.json')['failure_replay_files'])
for name in ('diagnostic.py', 'cpu_tests.py', 'prepare.py', 'launch.py', 'PROTOCOL.md', 'prompt.txt', 'review_prompt.txt', 'CONTINUE.md', 'REPAIR.md',
             'manifest.json', 'cpu_acceptance.json'):
    files[str(d.HERE / name)] = d.c.sha(d.HERE / name)
for path in (records_path, d.V7 / 'source_lock.json', d.V7 / 'teacher_admission.json',
             d.RUN/'teacher_context_diagnostic_v2/manifest.json',d.RUN/'teacher_context_diagnostic_v2/completion.json'):
    files[str(path)] = d.c.sha(path)
for r in selected:
    directory = d.V7 / 'teacher_01/windows' / r['window_id']
    files[str(directory / 'done.json')] = d.c.sha(directory / 'done.json')
    for name, digest in d.c.read(directory / 'done.json')['files'].items():
        d.c.require(d.c.sha(directory / name) == digest, 'prior accepted record changed')
        files[str(directory / name)] = digest
    files[r['window']['source_path']] = r['window']['source_sha256']
d.c.write(d.HERE / 'source_lock.json', {'schema': 'AIC_RELATIVE_SUMMARY_DIAGNOSTIC_LOCK_V3', 'files': files}, fresh=True)
print(json.dumps({'status': 'PASS_REGISTERED_CONTEXT_DIAGNOSTIC_SOURCE_LOCK', 'windows': manifest['window_ids'],
                  'files': len(files), 'source_lock_sha256': d.c.sha(d.HERE / 'source_lock.json'),
                  'predicted_incremental_output_bytes': planned}))
