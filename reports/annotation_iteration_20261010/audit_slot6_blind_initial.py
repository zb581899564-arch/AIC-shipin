"""Check the actual sealed initial reviews without recasting editorial advice as truth."""
from pathlib import Path
from fractions import Fraction as F
import json, hashlib, sys
root = Path(__file__).resolve().parent / 'slot6_silver24_v1'
sys.path.insert(0, str(root))
from quality_contract import reference, duration
rows = []
for name in json.loads((root/'observations/jobs.json').read_text())['jobs'][:4]:
    folder = Path(name)
    manifest = json.loads((folder/'manifest.json').read_text())
    p = root/'blind_reviews/initial'/f'{folder.name}.independent_initial_blind_v1.json'
    review = json.loads(p.read_text())
    assert review['window_id'] == manifest['window_id']
    assert review['manifest']['sha256_as_initial_read'] == hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest()
    assert review['blind_attestation']['teacher_content_received'] is False
    parts = {k: [] for k in ('K','NO','U')}
    for segment in review['segments']:
        parts[segment['label']].append(segment['global_seconds_exact'])
    domain, k, n, u = reference([manifest['domain_global_seconds_exact']], parts['K'], parts['NO'], parts['U'])
    rows.append(dict(
        window_id=review['window_id'], initial_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        exact_mutually_exclusive_full_coverage=True,
        initial_K_seconds_exact=str(duration(k)), initial_NO_seconds_exact=str(duration(n)),
        initial_U_seconds_exact=str(duration(u)),
        original_pngs_reported_actual_read=review['visibility']['sampled_original_pngs_observed'],
        proposed_keep_segments=len(parts['K']),
        UNKNOWN_titles=[s['title'] for s in review['segments'] if s['label']=='U'],
        main_adjudication_not_completed=True, training_admitted=False,
    ))
receipt = dict(status='PASS_INITIAL_BLIND_GEOMETRY_ONLY_NOT_SILVER_ADMISSION', rows=rows)
with (root/'blind_initial_geometry_acceptance_v1.json').open('x',encoding='utf-8') as f:
    json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
