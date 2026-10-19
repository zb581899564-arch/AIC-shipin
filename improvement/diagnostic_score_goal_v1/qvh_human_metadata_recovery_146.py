"""Explicit transport-only recovery: original author's GitHub API, no relay."""
import hashlib
import importlib.util
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/diagnostic_score_goal_20261018_v1')
old_code = ROOT / 'qvh_human_metadata_145.py'
old_failure = ROOT / 'qvh_original_human_145/failure.json'
assert hashlib.sha256(old_code.read_bytes()).hexdigest() == 'c9c646e4244de7a591c61d2007dc4162bde1a66b4be8397fc81c523e30b5d5db'
assert hashlib.sha256(old_failure.read_bytes()).hexdigest() == '72cce62ab215eed643740eb8f140b604cca58b4cbbf98a429f76db9285c06561'
assert sorted(p.name for p in old_failure.parent.iterdir()) == ['claim.json', 'failure.json']
spec = importlib.util.spec_from_file_location('qvh_metadata145_frozen', old_code)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT = ROOT / 'qvh_original_human_146'
module.ROOT.mkdir(exist_ok=True)
module.dump(module.ROOT / 'recovery_registration.json', {
    'schema': 'QVH146_EXPLICIT_REMAINING_TRANSPORT_ONLY_RECOVERY',
    'original_code_sha256': hashlib.sha256(old_code.read_bytes()).hexdigest(),
    'original_failure_sha256': hashlib.sha256(old_failure.read_bytes()).hexdigest(),
    'original_successfully_downloaded_files': 0,
    'reason': 'raw.githubusercontent.com timed out before first response',
    'endpoint': 'https://api.github.com/repos/jayleicn/moment_detr/contents/data/{file}?ref={frozen_commit}',
    'route': 'author GitHub publication direct to Linux; no Windows payload relay/config/proxy change',
    'same_blob_size_and_identity_checks': True,
    'same_registry_join_and_summary': True,
    'media_or_model_calls': 0,
})
original_open = urllib.request.urlopen


def api_open(request, timeout):
    prefix = f'https://raw.githubusercontent.com/jayleicn/moment_detr/{module.COMMIT}/data/'
    if not request.full_url.startswith(prefix):
        raise ValueError('request outside frozen publication')
    name = request.full_url[len(prefix):]
    if name not in module.FILES:
        raise ValueError('file not registered')
    url = ('https://api.github.com/repos/jayleicn/moment_detr/contents/data/'
           + urllib.parse.quote(name, safe='') + '?ref=' + module.COMMIT)
    new_request = urllib.request.Request(url, headers={
        'User-Agent': 'AIC-student-research-metadata-audit/146',
        'Accept': 'application/vnd.github.raw+json',
    })
    return original_open(new_request, timeout=timeout)


module.urllib.request.urlopen = api_open
module.main()
