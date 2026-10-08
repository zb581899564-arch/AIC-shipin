"""Program-owned exact native-PTS boundary and separate physical evidence IDs.

The model selects IDs. It never serializes timestamps or observation metadata.
The terminal boundary has no physical frame and is never an evidence ID.
"""
from fractions import Fraction
import hashlib
import json
import math


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()


def tables(observation):
    origin = Fraction(str(observation['window_pts_start_sec']))
    duration = Fraction(str(observation['window_duration_sec']))
    points = observation['actual_pts_sec']
    ordinals = observation['source_frame_ordinals']
    require(duration > 0 and points and len(points) == len(ordinals), 'native observation table missing')
    require(all(type(p) in (int, float) and math.isfinite(p) for p in points), 'finite native PTS required')
    require(all(a < b for a, b in zip(points, points[1:])), 'native evidence PTS must increase strictly')
    local = [Fraction(str(p)) - origin for p in points]
    require(all(0 <= p < duration for p in local), 'native evidence outside canonical local window')
    values = sorted(set([Fraction(0), *local, duration]))
    boundary = []
    for index, value in enumerate(values):
        evidence = [i for i, point in enumerate(local) if point == value]
        boundary.append({'boundary_id': index, 'local_seconds': float(value),
            'local_seconds_fraction': str(value), 'source_pts_fraction': str(origin + value),
            'evidence_frame_ids': evidence, 'terminal_without_frame': value == duration})
    frames = [{'evidence_frame_id': i, 'source_frame_ordinal': ordinal,
        'source_pts_sec': points[i], 'source_pts_fraction': str(Fraction(str(points[i]))),
        'local_seconds_fraction': str(local[i]),
        'boundary_id': values.index(local[i])} for i, ordinal in enumerate(ordinals)]
    return {'schema': 'aic_native_boundary_ids_v1', 'window_id': observation['window_id'],
        'boundary_ids': boundary, 'evidence_frames': frames,
        'window_duration_fraction': str(duration), 'program_owned_metadata': True,
        'sampling_gaps_are_unknown': True, 'terminal_boundary_is_not_evidence': True}


def schema(observation):
    table = tables(observation)
    ids = list(range(len(table['boundary_ids'])))
    segment = {'type': 'object', 'additionalProperties': False,
        'required': ['start_boundary_id', 'end_boundary_id'], 'properties': {
            'start_boundary_id': {'type': 'integer', 'enum': ids},
            'end_boundary_id': {'type': 'integer', 'enum': ids}}}
    base = {'type': 'object', 'additionalProperties': False,
        'required': ['state', 'segments', 'evidence_frame_ids', 'reason'], 'properties': {
            'state': {'type': 'string'}, 'segments': {'type': 'array', 'maxItems': 5, 'items': segment},
            'evidence_frame_ids': {'type': 'array', 'minItems': 1,
                'maxItems': len(table['evidence_frames']), 'items': {'type': 'integer',
                    'enum': list(range(len(table['evidence_frames'])))}},
            'reason': {'type': 'string', 'minLength': 1, 'maxLength': 600}}}
    branches = []
    import copy
    for state in ('KEEP', 'NO_HIGHLIGHT', 'UNKNOWN'):
        branch = copy.deepcopy(base)
        branch['properties']['state'] = {'const': state}
        if state == 'KEEP':
            branch['properties']['segments']['minItems'] = 1
        else:
            branch['properties']['segments']['maxItems'] = 0
        branches.append(branch)
    return {'anyOf': branches}


def validate_decision(value, observation):
    require(isinstance(value, dict) and set(value) == {'state', 'segments', 'evidence_frame_ids', 'reason'},
        'short decision fields differ')
    state = value['state']
    require(state in ('KEEP', 'NO_HIGHLIGHT', 'UNKNOWN'), 'unknown decision state')
    require(isinstance(value['reason'], str) and 0 < len(value['reason'].strip()) <= 600, 'short visible reason required')
    table = tables(observation)
    frames = value['evidence_frame_ids']
    require(isinstance(frames, list) and frames and len(frames) == len(set(frames))
        and all(type(i) is int and 0 <= i < len(table['evidence_frames']) for i in frames),
        'physical evidence IDs invalid; terminal boundary is not a physical frame')
    segments = value['segments']
    require(isinstance(segments, list) and len(segments) <= 5, 'bounded segment list required')
    require(bool(segments) == (state == 'KEEP'), 'KEEP requires segments; NO_HIGHLIGHT/UNKNOWN require none')
    previous = Fraction(0)
    for pair in segments:
        require(isinstance(pair, dict) and set(pair) == {'start_boundary_id', 'end_boundary_id'}, 'segment ID fields differ')
        a, b = pair['start_boundary_id'], pair['end_boundary_id']
        require(type(a) is int and type(b) is int and 0 <= a < b < len(table['boundary_ids']), 'boundary IDs out of order/range')
        start = Fraction(table['boundary_ids'][a]['local_seconds_fraction'])
        end = Fraction(table['boundary_ids'][b]['local_seconds_fraction'])
        require(start >= previous, 'unordered or overlapping native boundary segments')
        contained = [f['evidence_frame_id'] for f in table['evidence_frames']
            if start <= Fraction(f['local_seconds_fraction']) < end]
        require(contained, 'half-open native interval contains no provided physical frame')
        require(set(contained).intersection(frames), 'every KEEP segment needs a selected physical evidence frame')
        # Validate the exact float serialization used by the downstream student.
        local_a, local_b = float(start), float(end)
        require(0 <= local_a < local_b <= observation['window_duration_sec'], 'student boundary conversion invalid')
        previous = end
    return table


def canonical_response(value, observation):
    table = validate_decision(value, observation)
    mapped = []
    for pair in value['segments']:
        a, b = (table['boundary_ids'][pair[key]] for key in ('start_boundary_id', 'end_boundary_id'))
        mapped.append({'start_sec': a['local_seconds'], 'end_sec': b['local_seconds'], 'reason': value['reason']})
    unknown = value['state'] == 'UNKNOWN'
    return {'window_id': observation['window_id'], 'observation_scope': {
        'window_pts_start_sec': observation['window_pts_start_sec'],
        'window_pts_end_exclusive_sec': observation['window_pts_end_exclusive_sec'],
        'sampled_pts_sec': observation['actual_pts_sec'],
        # Legacy validator compatibility; this is a PROGRAM delivery assertion.
        # It is expressly not an autonomous model assertion of comprehension.
        'all_provided_frames_reviewed': True}, 'retained_segments': mapped,
        'explicit_no_highlight': value['state'] == 'NO_HIGHLIGHT', 'uncertain': unknown,
        'uncertainty_reasons': [value['reason']] if unknown else [], 'decision_reason': value['reason'],
        'boundary_notes': ['PROGRAM_NATIVE_BOUNDARY_IDS; physical evidence IDs=' + json.dumps(value['evidence_frame_ids']),
            'PROGRAM_DELIVERY_METADATA_ONLY; sampled gaps remain UNKNOWN; no model claim of every-frame comprehension']}


def prompt(template, observation):
    table = tables(observation)
    contract = {'window_id': observation['window_id'], 'local_window_duration_sec': observation['window_duration_sec'],
        'evidence_frame_count': len(table['evidence_frames']),
        'boundary_ids_in_time_order': [b['boundary_id'] for b in table['boundary_ids']],
        'frame_to_boundary_id': [{'evidence_frame_id': f['evidence_frame_id'], 'boundary_id': f['boundary_id']}
            for f in table['evidence_frames']], 'terminal_boundary_id': table['boundary_ids'][-1]['boundary_id'],
        'terminal_boundary_has_no_frame': True, 'window_start_boundary_id': 0}
    require(template.count('{{WINDOW_CONTRACT_JSON}}') == 1, 'short prompt placeholder mismatch')
    return template.replace('{{WINDOW_CONTRACT_JSON}}', json.dumps(contract, ensure_ascii=False, sort_keys=True))
