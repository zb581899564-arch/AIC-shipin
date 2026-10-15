"""Read and bind completed scope text; no model, decoder, probe or image viewing."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def verify(binding):
    assert ref(binding['path'])['sha256'] == binding['sha256'], binding['path']
    return Path(binding['path'])


def prepare(index, call):
    folder = ROOT / f'teacher_expansion/engineering_alias_remainder_v4_bootstrap_file/call{call}'
    audit_path = folder / f'w{index:02d}_completed_scope_audit.json'
    audit = read(audit_path)
    window, = [w for w in audit['windows'] if w['job_index'] == index]
    rows = window['bound_fact_rows']
    assert len(rows) == 64 and {x['identity']['frame_id'] for x in rows} == {f'F{i:02d}' for i in range(64)}
    verify(audit['immutable_prefix'])
    proposal_path = Path(window['proposal_path'])
    assert ref(proposal_path)['sha256'] == window['proposal_sha256']
    native_path, = (ROOT / 'native_reviews').glob(f'{index:02d}_*.native_review.json')
    student_path, = (ROOT / 'student_reviews').glob(f'{index:02d}_*.independent_student64_review_v1.json')
    root_path = sorted(ROOT.glob(f'{index:02d}_*main_preteacher_review*.json'), key=lambda p: p.name)[-1]
    native, student, preteacher = map(read, (native_path, student_path, root_path))
    nv = {f['frame_id']: f for f in native['frames']}
    sv = {f['frame_id']: f for f in student['student_view_inventory']}
    comparisons = []
    for row in rows:
        identity = row['identity']; fid = identity['frame_id']
        assert identity['source_ordinal'] == nv[fid]['source_ordinal'] == sv[fid]['source_ordinal']
        assert identity['local_seconds_exact'] == nv[fid]['local_seconds_exact'] == sv[fid]['local_seconds_exact']
        assert identity['png_sha256'] == nv[fid]['png_sha256']
        verify(row['raw_fact_output'])
        comparisons.append(dict(frame_id=fid, identity=identity, teacher_fact=row['facts'],
            teacher_origin=row['origin'], raw_fact_output=row['raw_fact_output'],
            native_static_fact=nv[fid]['static_visual_fact'], student_static_fact=sv[fid]['visible_static_fact'],
            comparison_basis='Bound text only; image inspection exists only when explicitly listed in the separate human crosscheck.'))
    inputs = dict(erratum=ref(ROOT / 'bootstrap_line_representation_erratum_v1.json'),
        actual_original_scope_audit=ref(audit_path), immutable_prefix=audit['immutable_prefix'],
        teacher_proposal=ref(proposal_path), native_initial_seal=ref(native_path),
        student_initial_review=ref(student_path), root_preteacher=ref(root_path))
    lawful = list(ROOT.glob(f'{index:02d}_*lawful_observation_completion.json'))
    if lawful:
        assert len(lawful) == 1
        receipt = read(lawful[0]); assert receipt['prefix_audit'] == inputs['actual_original_scope_audit']
        inputs['root_lawful_media_completion'] = ref(lawful[0])
    return dict(inputs=inputs, audit=audit, window=window, native=native, student=student,
        preteacher=preteacher, proposal=read(proposal_path), comparisons=comparisons)
