"""Bounded synthetic media-admission checks. No network, media or model work."""
import ast
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types

sys.dont_write_bytecode = True
import positive_media as m


def rejects(call, kind=ValueError):
    try:
        call()
    except kind:
        return
    raise AssertionError('Expected explicit rejection')


def main():
    ast.parse(Path(m.__file__).read_text(encoding='utf8'))
    document = json.loads((Path(__file__).resolve().parents[2]/
        'reports/recall_positive_admission_verify40_46_20261015_v1/reference_candidates.json').read_text(encoding='utf-8-sig'))
    selected, reserves = m.canonical_candidates(document)
    assert tuple(row['video_id'] for row in selected) == m.SELECTED
    assert tuple(row['video_id'] for row in reserves) == m.RESERVES and m.POOL_BYTES == 49919698
    changed = deepcopy(document); changed['selection'].reverse()
    rejects(lambda: m.canonical_candidates(changed))
    changed = deepcopy(document); changed['selection'][0]['provider']['size_bytes'] += 1
    rejects(lambda: m.canonical_candidates(changed))
    reference = m.original_reference(dict(video_id='fixture', vsum=[[[0, 1],[1,2],[2,3]], [[3,4],[4,5],[5,6]]]))
    assert reference['annotator_count'] == 3 and len(reference['annotator_intervals_exact_seconds']) == 3
    rejects(lambda: m.original_reference(dict(video_id='fixture', vsum=[[[0,1],[1,2]], [[2,3]]])))
    clock = dict(original_exact_pts=[str(F(i,30)) for i in range(900)], physical_end_exact='30',
        native_frames=900, first_original_pts_exact='0', original_zero_origin_verified=True,
        timeline_shift_applied=False, last_frame_duration_exact='1/30')
    m.validate_reference_domain(clock, reference)
    bad = deepcopy(reference); bad['annotator_intervals_exact_seconds'][0].append(['29','3001/100'])
    rejects(lambda: m.validate_reference_domain(clock, bad), m.NativeDomainRejected)
    bad = dict(clock, original_zero_origin_verified=False)
    rejects(lambda: m.validate_reference_domain(bad, reference), m.NativeDomainRejected)
    bad = dict(clock, original_exact_pts=['0','1','2'], native_frames=3, physical_end_exact='3', last_frame_duration_exact='1')
    rejects(lambda: m.validate_reference_domain(bad, m.original_reference(dict(video_id='x',vsum=[[[0,1],[1,2]]]))), m.NativeDomainRejected)
    rejects(lambda: m.pool_budget(m.POOL_BYTES+1))
    routes = dict(windows_video_body_bytes=0, routes=[dict(video_id=row['video_id'], bytes=row['provider']['size_bytes'],
        metadata_only=True,status='PINNED_NORMAL_PUBLIC_REDIRECT',initial_public_url=row['provider']['video_url'],
        publisher_redirect_url='https://us.aws.cdn.hf.co/object/'+row['youtube_id'],etag='"fixture"') for row in selected+reserves])
    m.validate_routes(routes, selected+reserves)
    bad = deepcopy(routes); bad['routes'][0]['status'] = 'NETWORK_TIMEOUT'
    rejects(lambda: m.validate_routes(bad, selected+reserves))
    bad = deepcopy(routes); bad['routes'][0]['publisher_redirect_url'] = 'https://evil.example/object'
    rejects(lambda: m.validate_routes(bad, selected+reserves))

    payload = b'test'; calls = []
    class Body:
        status_code = 200
        headers = {'ETag':'"fixture"','Content-Length':'4'}
        url = 'https://us.aws.cdn.hf.co/object/fixture'
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def iter_content(self, _): yield payload
    state = {'body':Body()}
    def fake_get(url, **kwargs):
        assert kwargs['allow_redirects'] is False and kwargs['headers']['If-Match']=='"fixture"'
        calls.append(url); return state['body']
    fake = types.SimpleNamespace(get=fake_get, auth=types.SimpleNamespace(AuthBase=object))
    original_requests = sys.modules.get('requests'); sys.modules['requests'] = fake
    row = dict(video_id='v_fixture', provider=dict(size_bytes=4,video_url=m.public_url('fixture')))
    route = dict(status='PINNED_NORMAL_PUBLIC_REDIRECT', publisher_redirect_url=Body.url, etag='"fixture"')
    try:
        with tempfile.TemporaryDirectory(prefix='positive_media_pure_') as temp:
            def folder(name):
                path=Path(temp)/name; path.mkdir(); return path
            output=folder('ok'); transfer=dict(actual_new_media_payload_bytes=0)
            receipt, reason=m.download(output,row,route,set(),transfer)
            assert reason is None and receipt['sha256']==hashlib.sha256(payload).hexdigest()
            assert transfer['actual_new_media_payload_bytes']==4 and (output/'media_receipt.json').is_file()
            state['body']=Body(); state['body'].status_code=404
            assert m.download(folder('404'),row,route,set(),dict(actual_new_media_payload_bytes=0))[1]=='ACTUAL_PUBLIC_OBJECT_404'
            state['body']=Body(); state['body'].status_code=503
            rejects(lambda:m.download(folder('503'),row,route,set(),dict(actual_new_media_payload_bytes=0)))
            state['body']=Body(); state['body'].url='https://us.aws.cdn.hf.co/other'
            rejects(lambda:m.download(folder('changed_path'),row,route,set(),dict(actual_new_media_payload_bytes=0)))
            state['body']=Body(); duplicate=folder('duplicate')
            rejects(lambda:m.download(duplicate,row,route,{hashlib.sha256(payload).hexdigest()},dict(actual_new_media_payload_bytes=0)))
            assert (duplicate/'media.mp4.partial').read_bytes()==payload and not (duplicate/'media.mp4').exists()
    finally:
        if original_requests is None: del sys.modules['requests']
        else: sys.modules['requests']=original_requests
    assert len(calls)==5
    print('PASS: AST, frozen4+2 identity/bytes/order, dynamic-rater schema, exact native-domain veto, source cap, route veto, single mock GET,404-only substitution,503/path/whole-file-duplicate STOP with retained partial')


if __name__ == '__main__':
    main()
