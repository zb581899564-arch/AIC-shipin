"""ROOT verifies actual bindings before one prospective teacher split; no SFT gate."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, ast, copy, hashlib, json, subprocess, sys

R = Path(__file__).parent

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bind(p):
    return {'path': str(p), 'sha256': sha(p)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', required=True, choices=['engineering_CLI36_37_split_fragment_v8v5'])
    parser.add_argument('--independent-review', required=True)
    args = parser.parse_args()
    V = R / 'teacher_expansion' / args.version
    review = Path(args.independent_review)
    assert review.parent == R / 'plan_review'
    review_doc = read(review)
    assert review_doc['status'] == 'PASS_INDEPENDENT_UPDATED_ENGINEERING_START_REVIEW'
    assert review_doc['execution_binding_sha256'] == sha(V / 'execution_code_binding.json')
    binding = read(V / 'execution_code_binding.json')
    for k in ('sources', 'actual_prior_bindings'):
        for p, h in binding[k].items():
            assert sha(p) == h, p
    for p in V.glob('*.py'):
        ast.parse(p.read_text(encoding='utf-8'))
    neg = read(V / 'independent_CPU_negative_acceptance.json')
    assert neg['sources'] == binding['sources']
    assert len(neg['negative_cases']) >= 38
    assert all(c['synthetic_memory_only'] for c in neg['negative_cases'])
    dry = read(V / 'dry_run_acceptance.json')
    assert dry['new_model_calls'] == dry['new_video_decode'] == 0
    assert dry['execution_binding_sha256'] == sha(V / 'execution_code_binding.json')
    TE = R / 'teacher_expansion'
    ledger = TE / 'global_CLI_ledger.jsonl'
    assert ledger.read_bytes() == (V / 'actual_global35_ledger_prefix.jsonl').read_bytes()
    assert max(x['global_count'] for x in map(json.loads, ledger.read_text().splitlines())) == 35
    for n in (36, 37):
        assert not list(TE.glob(f'*/call{n}/request.json'))
    oldV = TE / 'engineering_alias_remainder_v6_fresh_scope_prefix_v2'
    old_gate = read(oldV / 'root_start_admission.json')
    assert old_gate['actual_pixel_checks'] == 360
    sys.path.insert(0, str(V))
    from common import expected_core
    from launch import command
    checks = []
    all_markers = []
    all_parts = []
    count = 0
    for n, oldn, jobs in ((36, 35, [19, 20]), (37, 36, [21, 22, 23])):
        a = V / f'call{n}'
        fr = read(a / 'freeze.json')
        idx = read(a / 'index.json')
        assert fr['fixed_job_indices'] == jobs and fr['global_cap'] == 37
        assert fr['timeout_seconds'] == 7200 and fr['automatic_retry'] is False
        for p, h in fr['inputs'].items():
            assert sha(p) == h, p
        assert not any(Path(p).exists() for p in fr['write_whitelist'])
        olda = oldV / f'call{oldn}'
        old = read(olda / 'index.json')
        assert len(old['windows']) == len(idx['windows'])
        for ow, w in zip(old['windows'], idx['windows']):
            oldprojection = copy.deepcopy(ow)
            for g in oldprojection['groups']:
                g['output_path'] = g['output_path'].replace(str(olda), str(a))
            oldprojection['proposal_path'] = oldprojection['proposal_path'].replace(str(olda), str(a))
            newprojection = copy.deepcopy(w)
            del newprojection['header_fragment_id'], newprojection['native_fragment_ids']
            assert oldprojection == newprojection, w['job_index']
            for f in [f for g in w['groups'] for f in g['frames']] + w['student_previews']:
                assert sha(f['path']) == f['png_sha256'] == sha(f['original_path'])
                count += 1
            assert sha(w['clip_path']) == sha(w['original_clip_path'])
        reads = set(fr['read_whitelist'] + fr['self_read_whitelist'])
        assert str(a / 'index.json') not in reads
        for part in idx['text_fragments']:
            b = Path(part['path']).read_bytes()
            expected = read(part['expected_ACK_path'])
            assert len(b) < 30000 and b.endswith(b'\n') and b'\r' not in b
            assert sha(part['path']) == part['input_sha256']
            assert len(b) == part['payload_bytes'] and len(b.split(b'\n')) == part['exact_Go_LF_lines']
            assert expected['marker'].encode() in b and b.decode().rstrip().endswith(expected['marker'])
            assert part['expected_ACK_path'] not in reads and part['ack_path'] not in reads
            assert sha(part['expected_ACK_path']) == part['expected_ACK_sha256']
            all_parts.append(b)
            all_markers.append(expected['marker'].encode())
        short = (a / 'short_prompt.txt').read_text(encoding='utf-8')
        assert all(m.decode() not in short and m.decode() not in (a / 'index.json').read_text(encoding='utf-8') for m in all_markers)
        assert len(expected_core(idx)) == 2 + 100 * len(jobs)
        units = len(subprocess.list2cmdline(command(n, short)).encode('utf-16-le')) // 2 + 1
        assert units < 1024
        checks.append({'CLI': n, 'jobs': jobs, 'inputs': len(fr['inputs']), 'freeze': bind(a / 'freeze.json'), 'argv_UTF16_units': units, 'core': len(expected_core(idx))})
    assert count == 360 and len(all_parts) == 27
    assert len(set(all_markers)) == 27
    for i, marker in enumerate(all_markers):
        assert [j for j, b in enumerate(all_parts) if marker in b] == [i]
    out = V / 'root_start_admission.json'
    gate = {
        'status': 'ROOT_APPROVED_START_FRAGMENTED_SPLIT36_37_FIXED19_23',
        'utc': datetime.now(timezone.utc).isoformat(),
        'execution_binding_sha256': sha(V / 'execution_code_binding.json'),
        'dry_run_sha256': sha(V / 'dry_run_acceptance.json'),
        'negative_receipt_sha256': sha(V / 'independent_CPU_negative_acceptance.json'),
        'independent_review': bind(review), 'root_verifier_source': bind(__file__),
        'calls': checks, 'actual_360_media_byte_bindings_checked': count,
        'original_360_RGB_geometry_acceptance_exact_reused': bind(oldV / 'root_start_admission.json'),
        'prospective_route': bind(R / 'teacher_dispatch_capacity_v5_split_recovery_authorization.json'),
        'strict_continuation': bind(R / 'teacher_split_v5_continuation_constraints.json'),
        'old_failures_and_frozen_inputs_preserved': True,
        'source_upload_authorized_by_gate': False, 'training_or_semantic_admission': False,
        'new_model_calls_by_this_verification': 0, 'new_video_decode': 0,
    }
    with out.open('x', encoding='utf-8') as f:
        json.dump(gate, f, ensure_ascii=False, indent=2)
    print(json.dumps(bind(out), ensure_ascii=False))

if __name__ == '__main__':
    main()
