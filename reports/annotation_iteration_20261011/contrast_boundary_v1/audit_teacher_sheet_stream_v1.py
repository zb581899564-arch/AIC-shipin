"""Audit completed real teacher calls; no video decoding, model or teacher execution.

Usage: python -B audit_teacher_sheet_stream_v1.py --index 000 \
    --call-directory teacher_calls/000_attempt_02
Output is exclusive: an existing audit is never overwritten. This is an evidence
and mathematical form check, not an independent semantic review or admission.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'science_runtime'))
import science_contract as science
from quality_contract import reference, normalize, duration


def binding(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=science.sha(path))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def exact_pair(value):
    science.need(isinstance(value, list) and len(value) == 2 and
                 all(isinstance(v, str) and v for v in value), 'exact string interval required')
    return tuple(map(F, value))


def image_block(value):
    if isinstance(value, dict):
        return value.get('type') == 'image' or any(k in value for k in
            ('image_url', 'image_data', 'image_bytes')) or any(image_block(v) for v in value.values())
    if isinstance(value, list):
        return any(image_block(v) for v in value)
    return False


def proposal_form(proposal, manifest):
    w = manifest['original_window']
    science.need(proposal['window_id'] == w['window_id'] == manifest['window_id'] and
                 proposal['source_sha256'] == w['source_sha256'] == manifest['source_sha256'],
                 'proposal/manifest source identity differs')
    frames = manifest['frames']
    expected_ids = ['F%02d' % i for i in range(64)]
    science.need([f['frame_id'] for f in frames] == expected_ids, 'manifest F00..F63 identity differs')
    a, b = F(w['domain_start_exact']), F(w['domain_end_exact'])
    for frame in frames:
        science.need(F(frame['local_seconds_exact']) == F(frame['pts_exact']) - a,
                     'manifest local/exact PTS differs')
    facts = proposal['frame_facts']
    science.need(len(facts) == 64 and [f['frame_id'] for f in facts] == expected_ids and
                 all(isinstance(f['visible_fact'], str) and f['visible_fact'].strip() for f in facts),
                 'exact 64 ordered nonempty frame facts required')
    sets = [[exact_pair(v) for v in proposal[k]] for k in
            ('keep_local_exact', 'no_local_exact', 'unknown_local_exact')]
    domain, keep, no, unknown = reference([(F(0), b-a)], *sets)
    pure_no = not keep and not unknown and no == domain
    science.need(type(proposal['explicit_no_highlight']) is bool and
                 proposal['explicit_no_highlight'] is pure_no, 'explicit_no_highlight must be pure NO')
    events = proposal['events']
    science.need(isinstance(events, list) and len(events) <= 5, 'at most five teacher events required')
    event_map = {}
    for event in events:
        key = event['event_id']
        science.need(isinstance(key, str) and key and key not in event_map, 'unique nonempty event ID required')
        local = exact_pair(event['local'])
        science.need(local[0] < local[1] and isinstance(event['visible_reason'], str) and
                     event['visible_reason'].strip(), 'positive event/reason required')
        event_map[key] = local
    science.need(normalize(list(event_map.values())) == keep, 'event union must equal KEEP')
    science.need(sum((hi-lo for lo, hi in event_map.values()), F(0)) == duration(keep),
                 'independent teacher events must not overlap')
    boundaries = proposal['boundaries']
    science.need(isinstance(boundaries, list) and len(boundaries) == len(events)*2,
                 'one start/end boundary per event required')
    identities = set()
    for boundary in boundaries:
        key, side = boundary['event_id'], boundary['side']
        science.need(key in event_map and side in ('start', 'end') and (key, side) not in identities,
                     'boundary event/side identity differs')
        identities.add((key, side))
        position = F(boundary['local_exact'])
        lo, hi = exact_pair(boundary['uncertainty_local_exact'])
        science.need(position == event_map[key][0 if side == 'start' else 1] and
                     0 <= lo <= position <= hi <= b-a and hi-lo <= F(1, 2),
                     'boundary exact endpoint/bracket differs or exceeds half-second')
        inside = boundary['inside_frame_id']
        outside = boundary['outside_frame_id_or_domain']
        science.need(inside in expected_ids and isinstance(outside, str) and
                     outside in expected_ids + ['DOMAIN_START', 'DOMAIN_END', 'domain_start', 'domain_end'],
                     'boundary requires known frame or explicit domain endpoint identity')
        science.need(isinstance(boundary['reason'], str) and boundary['reason'].strip(),
                     'boundary visible reason missing')
    science.need(isinstance(proposal['limitations'], list) and proposal['limitations'] and
                 all(isinstance(v, str) and v.strip() for v in proposal['limitations']),
                 'finite observation limitations required')
    return dict(frame_fact_identity_count=64, complete_partition_exact=True,
                event_union_equals_keep=True, event_count=len(events), boundary_count=len(boundaries),
                boundary_brackets_max_half_second=True, pure_no=bool(pure_no),
                keep_seconds_exact=str(duration(keep)), no_seconds_exact=str(duration(no)),
                unknown_seconds_exact=str(duration(unknown)), semantic_facts_verified=False,
                semantic_boundary_support_verified=False, semantic_quality_verified=False,
                training_admitted=False)


def build(index, call_directory):
    science.need(index.isdigit() and 0 <= int(index) < 96, 'registered observation index required')
    call_directory = Path(call_directory)
    if not call_directory.is_absolute():
        call_directory = ROOT / call_directory
    call_directory = call_directory.resolve(strict=True)
    science.need(call_directory.parent == ROOT / 'teacher_calls', 'call must be in this teacher_calls directory')
    target = call_directory / 'teacher_stream_audit.json'
    science.need(not target.exists(), 'exclusive audit already exists; no overwrite')
    terminal_path = call_directory / 'terminal.json'
    science.need(terminal_path.is_file(), 'call is not terminal; no audit written')
    terminal = read(terminal_path)
    stream_path = call_directory / 'stdout.jsonl'
    stream_binding = binding(stream_path)
    science.need(terminal['stdout_sha256'] == stream_binding['sha256'], 'terminal raw SHA differs')
    rows = [json.loads(line) for line in stream_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    # Existing verifier checks real ERROR before the missing-observation check.
    for row in rows:
        step, result = row.get('step_update', {}), row.get('result', {})
        if (row.get('event') in ('error', 'ERROR') or row.get('error') or
                step.get('state') in ('ERROR', 'FAILED', 'CANCELLED') or step.get('error') or
                result.get('status') in ('ERROR', 'FAILED', 'CANCELLED') or result.get('error')):
            science.verify_teacher_stream(dict(original_stream=stream_binding, sheet_observations=[]), [])
    science.need(terminal['exit_code'] == 0 and terminal['timed_out'] is False and
                 terminal['result_status'] == 'SUCCESS', 'actual teacher terminal is not successful')
    results = [row['result'] for row in rows if row.get('event') == 'result']
    science.need(len(results) == 1 and results[0]['status'] == 'SUCCESS', 'unique real SUCCESS result required')
    result = results[0]
    proposal_path = call_directory / 'proposal.json'
    proposal = read(proposal_path)
    structured = result['structured_output']
    science.need(all(proposal.get(k) == v for k, v in structured.items()) and
                 set(proposal)-set(structured) <= {'toolAction', 'toolSummary'},
                 'saved proposal differs from raw structured_output')
    response = json.loads(result['response'])
    science.need(response == proposal, 'saved proposal differs from exact parsed raw response')
    manifest_path = ROOT / 'observations' / ('%03d' % int(index)) / 'contact_sheet_manifest.json'
    manifest = read(manifest_path)
    audit = dict(schema='CONTRAST_BOUNDARY_TEACHER_STREAM_AUDIT_V1',
                 window_id=manifest['window_id'], source_sha256=manifest['source_sha256'],
                 original_stream=stream_binding, terminal=binding(terminal_path), proposal=binding(proposal_path),
                 contact_sheet_manifest=binding(manifest_path), sheet_observations=[], tool_issues=[],
                 image_block_claimed=False, raw_image_metadata_limitations=[
                     'The raw stream may expose only successful view_file terminal names and paths. '
                     'Absent image blocks, dimensions, MIME metadata and tool_call_id are not inferred. '
                     'Local PNG pixel verification does not prove model image-byte attention.'],
                 old_media_workflow_claimed=False, native_video_delivered=False,
                 semantic_quality_verified=False, training_admitted=False)
    steps = [row['step_update'] for row in rows if row.get('event') == 'step_update']
    blocks = []
    for sheet in manifest['sheets']:
        path = sheet.get('original_image_path', sheet['image']['path'])
        candidates = [step for step in steps if step.get('state') == 'DONE' and
                      step.get('tool_name') == 'view_file' and
                      science.same_tool_path(step.get('tool_info', {}).get('parameters', {}).get('AbsolutePath'), path)]
        science.need(len(candidates) == 1, 'unique real DONE for each actual sheet required')
        step = candidates[0]
        matching_rows = [row for row in rows if row.get('step_update') is step]
        info = step.get('tool_info', {})
        call_id = step.get('tool_call_id', info.get('tool_call_id', matching_rows[0].get('tool_call_id')))
        audit['sheet_observations'].append(dict(sheet_index=sheet['index'], conversation_id=step['conversation_id'],
            step_index=step['step_index'], tool_call_id=call_id, tool_call_id_exposed=call_id is not None,
            tool_image_path=info['parameters']['AbsolutePath'], image_sha256=sheet['image']['sha256'],
            successful=True, raw_image_metadata_visible=science.raw_image_metadata_visible(info)))
        blocks.append(image_block(info))
    science.need(all(obs['conversation_id'] == result['conversation_id'] for obs in audit['sheet_observations']),
                 'sheet/result conversation identity differs')
    audit['image_block_claimed'] = any(blocks)
    audit['stream_acceptance'] = science.verify_teacher_stream(audit, manifest['sheets'])
    audit['pixel_acceptance'] = science.verify_contact_sheet_manifest(manifest, manifest['original_window'])
    audit['proposal_form_acceptance'] = proposal_form(proposal, manifest)
    audit['proposal_raw_binding_acceptance'] = dict(parsed_response_equals_saved_proposal=True,
        structured_output_fields_equal=True,
        response_only_transport_fields=sorted(set(proposal)-set(structured)))
    audit['status'] = 'PASS_REAL_STREAM_PIXELS_AND_PROPOSAL_FORM_ONLY'
    audit['utc'] = datetime.now(timezone.utc).isoformat()
    audit['usage'] = result.get('usage')
    audit['teacher_cash'] = terminal.get('teacher_cash', 'UNKNOWN_NOT_ZERO')
    audit['new_teacher_calls'] = audit['native_video_decoder_calls'] = audit['new_optimizer_updates'] = 0
    # Recheck bindings before exclusive output; no mutation to original evidence.
    for name in ('original_stream', 'terminal', 'proposal', 'contact_sheet_manifest'):
        science.byte_bound(audit[name])
    with target.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(audit, out, ensure_ascii=False, indent=2)
        out.write('\n')
    return dict(path=str(target), sha256=science.sha(target), status=audit['status'],
                stream_acceptance=audit['stream_acceptance'], pixel_acceptance=audit['pixel_acceptance'],
                proposal_form_acceptance=audit['proposal_form_acceptance'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', required=True)
    parser.add_argument('--call-directory', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.index, args.call_directory), ensure_ascii=False))
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(json.dumps(dict(status='REJECT_NO_AUDIT_WRITTEN', reason=str(exc)), ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
