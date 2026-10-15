"""Independently accept one supplied scope; never infer an active CLI terminal."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
VERSION = ROOT/'teacher_expansion/remaining_CLI33_36_same_index_selfcheck_v2'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bind(p):
    return dict(path=str(p), sha256=sha(p))


def key(p):
    return str(Path(p).resolve()).casefold()


def accept(call, job, output):
    assert call.parent == VERSION and not output.exists()
    ap = call/f'w{job:02d}_completed_scope_audit.json'
    a = read(ap)
    assert a['status'] == 'PASS_ACTUAL_COMPLETED_SCOPE_TOOL_STRUCTURE_PENDING_ROOT_REVIEW' and not a['issues']
    for name in ('proposal', 'program_bound_facts', 'stream_prefix', 'freeze', 'index', 'request'):
        assert sha(a[name]['path']) == a[name]['sha256']
    freeze = read(call/'freeze.json'); request = read(call/'request.json')
    assert sha(call/'freeze.json') == request['freeze_sha256']
    assert freeze['protocol_sha256'] == sha(VERSION/'PROTOCOL.md')
    assert freeze['execution_binding_sha256'] == sha(VERSION/'execution_code_binding.json')
    assert request['root_start_admission_sha256'] == sha(VERSION/'root_start_admission.json')
    assert request['model'] == 'gemini-3.8-flash-high' and 33 <= request['CLI_after'] <= 36
    assert freeze['global_cap'] == 36 and not freeze['automatic_retry']
    assert freeze['same_index_selfcheck']['hard_count_limit'] is False
    assert key(freeze['same_index_selfcheck']['exact_path']) == key(call/'index.json')
    for p, h in freeze['inputs'].items():
        assert sha(p) == h
    source = freeze['source_index']
    assert sha(source['path']) == source['sha256'] == sha(call/'index.json')
    w = read(call/'index.json')['windows'][0]
    assert w['job_index'] == job and job in freeze['fixed_job_indices']

    # This saved prefix is immutable. Inspect final states as well as every
    # attempted tool path; an ERROR/unfinished/outside read is not hidden by
    # a later DONE. Bare error metadata is preserved without inventing a cause.
    states = {}; attempts = []; error_metadata = []
    for line in Path(a['stream_prefix']['path']).read_text(encoding='utf-8-sig').splitlines():
        item = json.loads(line)
        if item.get('event') != 'step_update':
            continue
        s = item['step_update']; states[s['step_index']] = s
        if s.get('step_type') == 'tool':
            attempts.append(s)
        elif s.get('step_type') == 'error_message':
            error_metadata.append(s)
            # Do not treat a reported real error as a media supply success.
            assert not s.get('error_message') and not s.get('text') and not s.get('message') and not s.get('content')
    whitelist = set(map(key, freeze['read_whitelist']+freeze['self_read_whitelist']))
    for s in attempts:
        assert s.get('state') != 'ERROR' and s.get('tool_name') in ('view_file', 'write_to_file')
        p = s.get('tool_info', {}).get('parameters', {})
        if s['tool_name'] == 'view_file':
            assert key(p['AbsolutePath']) in whitelist
    tools = [s for _, s in sorted(states.items()) if s.get('step_type') == 'tool']
    assert tools and all(s['state'] == 'DONE' for s in tools)
    assert tools[0]['tool_name'] == 'view_file' and key(tools[0]['tool_info']['parameters']['AbsolutePath']) == key(call/'index.json')
    core = []; index_steps = []; self_reads = []; written = set(); counts = {}
    for s in tools:
        info = s['tool_info']; p = info['parameters']; name = s['tool_name']
        path = key(p.get('AbsolutePath') or p.get('TargetFile'))
        assert not any(t in str(info.get('output', '')).lower() for t in ('not found', 'cannot read', 'error reading', 'failed to'))
        if name == 'view_file' and path == key(call/'index.json'):
            index_steps.append(s['step_index'])
            if len(index_steps) > 1:
                continue
        if name == 'view_file' and path in written:
            counts[path] = counts.get(path, 0)+1
            assert counts[path] == 1
            self_reads.append(dict(step=s['step_index'], path=path))
            continue
        core.append((name, path))
        if name == 'write_to_file':
            assert path not in written
            written.add(path)
    expected = [('view_file', key(call/'index.json'))]
    for g in w['groups']:
        for fr in g['frames']:
            assert sha(fr['path']) == fr['png_sha256']
            with Image.open(fr['path']) as im:
                assert list(im.size) == fr['geometry']
                assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest() == fr['rgb_pixel_sha256']
            expected.append(('view_file', key(fr['path'])))
        expected.append(('write_to_file', key(g['output_path'])))
    expected.append(('view_file', key(w['clip_path'])))
    student_receipt_path = Path(w['student_previews'][0]['path']).parent/'receipt.json'
    assert sha(student_receipt_path) == w['student_receipt_sha256']
    student_receipt = read(student_receipt_path)
    assert student_receipt['patch_inverse_exact'] is True and len(student_receipt['frames']) == 64
    student_frames = {fr['frame_id']: fr for fr in student_receipt['frames']}
    for fr in w['student_previews']:
        assert sha(fr['path']) == fr['png_sha256']
        with Image.open(fr['path']) as im:
            assert list(im.size) == fr['geometry']
            assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest() == fr['rgb_pixel_sha256']
        sf = student_frames[fr['frame_id']]
        assert sf['png_sha256'] == fr['png_sha256'] and sf['rgb_pixel_sha256'] == fr['rgb_pixel_sha256']
        assert sf['source_ordinal'] == fr['source_ordinal']
        expected.append(('view_file', key(fr['path'])))
    expected.append(('write_to_file', key(w['proposal_path'])))
    assert core == expected and len(core) == 91
    rows = read(a['program_bound_facts']['path'])['rows']
    assert len(rows) == 64 and [r['frame_id'] for r in rows] == [f'F{i:02d}' for i in range(64)]
    for i, row in enumerate(rows):
        g = w['groups'][i//4]; fr = g['frames'][i%4]
        assert row['source_ordinal'] == fr['source_ordinal'] and row['png_sha256'] == fr['png_sha256']
        assert row['geometry'] == fr['geometry'] and row['identity_generated_by_program'] is True
        assert row['raw_output_sha256'] == sha(g['output_path']) and row['facts'] == read(g['output_path'])['items'][i%4]
    cursor = F(0)
    for seg in read(w['proposal_path'])['segments']:
        assert seg['decision'] in ('KEEP', 'NO', 'UNKNOWN') and F(str(seg['start_seconds'])) == cursor
        stop = F(str(seg['end_seconds']))
        assert cursor < stop <= F(w['domain_local_seconds'][1])
        cursor = stop
    assert cursor == F(w['domain_local_seconds'][1])
    receipt = dict(status='PASS_ROOT_INDEPENDENT_FIXED_SELF_CHECK_SCOPE_MEDIA_PENDING_SEMANTIC_REFERENCE',
        utc=datetime.now(timezone.utc).isoformat(), window_id=w['window_id'],
        original_pngs_delivered=64, effective_pngs_delivered=8, native_video_delivered=True,
        tool_issues=[], proposal_geometry_identity_issues=[], ordered_core_tool_count=91,
        original_index_read_steps=index_steps, additional_index_reads=len(index_steps)-1,
        exact_frozen_index_read_only_selfchecks=True, same_index_hard_count_limit=False,
        actual_proposal_self_reads=self_reads, bare_error_metadata=error_metadata,
        bare_error_cause='UNKNOWN' if error_metadata else None,
        prefix_audit=bind(ap), stream_prefix=a['stream_prefix'], proposal=a['proposal'],
        program_bound_facts=a['program_bound_facts'], protocol=bind(VERSION/'PROTOCOL.md'),
        freeze=a['freeze'], request=a['request'], global_CLI=request['CLI_after'],
        parent_terminal_at_original_scope_audit=a['parent_CLI_terminal_present'],
        whole_CLI_status_not_inferred=True, whole_job_cost='PENDING_ACTUAL_PARENT_TERMINAL',
        cash_cost='UNKNOWN_NOT_ZERO', teacher_semantics_not_truth=True,
        root_semantic_facts_read_not_asserted_by_this_helper=True,
        semantic_admission_pending=True, training_admitted=False, new_optimizer_updates=0)
    with output.open('x', encoding='utf-8') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(dict(window_id=w['window_id'], observation_completion=bind(output), semantic_admission_pending=True)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--call-directory', required=True); p.add_argument('--job-index', type=int, required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    op = Path(a.output).resolve(); assert op.parent == ROOT
    accept(Path(a.call_directory).resolve(strict=True), a.job_index, op)
