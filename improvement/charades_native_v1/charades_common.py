"""Distinct Charades-only state; never shadow the original runtime common."""
import datetime
import hashlib
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/charades_boundary_v1')
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
LEGACY = Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')
KNOWN = Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1/known_identity_snapshot_01.json')
CACHE_CODE = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v1/code')
CACHE_DEPENDENCIES = {
    str(CACHE_CODE/'lb_io.py'): 'c1a1c459a022c08d248aab220c72b4784158a2230e51c695996d57794f1bf614',
    str(CACHE_CODE/'lb_contract.py'): '7ddd9d2aa0439a1bd784c7fab5e2769c4668b03597e844016b7dfc0d0de57077',
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def require(ok, why):
    if not ok:
        raise ValueError(why)


def check_deadline():
    deadline = read(ROOT/'media_native_protocol_01.json')['goal_deadline']
    require(datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat(deadline),
            'No new media/preparation after frozen goal deadline')


def assert_cpu_host():
    require(socket.gethostname() == 'inspur-NP5570M5', 'Unexpected Linux host')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only explicit empty CUDA visibility required')
    check_deadline()


def resource_snapshot():
    mem = {line.split(':')[0]: int(line.split(':')[1].split()[0])*1024
           for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    peers = subprocess.run(['ps', '-eo', 'pid,ppid,pcpu,pmem,comm', '--sort=-pcpu'],
                           capture_output=True, text=True, check=True, timeout=10).stdout.splitlines()[:18]
    return dict(utc=utc(), hostname=socket.gethostname(), mem_available_bytes=mem['MemAvailable'],
                disk_available_bytes=shutil.disk_usage(ROOT).free,
                own_output_bytes=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),
                peer_processes=peers, cpu_parallelism='serial; one AV/torch thread; external jobs untouched')


def check_metadata():
    protocol_path = ROOT/'media_native_protocol_01.json'
    protocol = read(protocol_path)
    require(protocol['approved'] and protocol['linux_root'] == str(ROOT), 'Approved current independent root required')
    meta = ROOT/'metadata_01'
    manifest_path, complete_path = meta/'source_manifest_01.json', meta/'completion.json'
    require(sha(manifest_path) == protocol['source_manifest_sha256'], 'Frozen successful source manifest changed')
    require(sha(complete_path) == protocol['metadata_completion_sha256'], 'Frozen successful metadata completion changed')
    manifest, complete = read(manifest_path), read(complete_path)
    require(complete['status'] == 'PASS_METADATA_AND_DIRECTORY_ONLY_NOT_MEDIA_ADMISSION', 'Actual prior metadata success required')
    require(len(manifest['rows']) == 60 and len({x['source_id'] for x in manifest['rows']}) == 60,
            'Frozen twenty plus forty distinct metadata sources')
    require(sha(meta/'Charades.zip') == manifest['annotation_zip_sha256'], 'Existing author annotation ZIP changed')
    require(sha(meta/'video_archive_index_01.json') == manifest['archive_index_sha256'], 'Existing CD metadata changed')
    require(manifest['primary_compressed_media_bytes'] == protocol['primary_compressed_media_bytes']
            and manifest['all60_compressed_media_bytes'] == protocol['all60_compressed_media_bytes_budget'],
            'Specific byte scope changed')
    return protocol, manifest, {str(p): sha(p) for p in [protocol_path, manifest_path, complete_path,
                              meta/'Charades.zip', meta/'video_archive_index_01.json', meta/'author_license.txt']}


def known_metadata():
    snapshot = read(KNOWN)
    require(snapshot['status'] == 'COMPLETE_KNOWN_B_TRAINING_AND_FROZEN_426_IDENTITIES_NOT_NEW_MEDIA_SEPARATION',
            'Existing full known identity snapshot required')
    train, test = snapshot['training']['sources'], snapshot['testing']['records']
    require(len(train) == 704 and len({x['youtube_id'] for x in train}) == 602
            and len(test) == 426 and {int(x['video_id']) for x in test} == set(range(426)),
            'Known B602 and protected426 metadata completeness')
    provenance = {}
    for oldpath, digest in snapshot['provenance_bindings'].items():
        parts = [p for p in oldpath.replace('\\', '/').split('/') if p]
        require(parts[:2] == ['reports', 'round6_score_alignment'], 'Unexpected metadata provenance path')
        path = Path('/home/inspur/aic_video_work').joinpath(*parts[1:])
        require(sha(path) == digest, 'Current known B metadata provenance changed')
        provenance[str(path)] = digest
    # Only metadata strings/hashes; never open protected videos or GT.
    aliases, hashes = {}, set()
    for row in train+test:
        digest = row['source_sha256']
        require(len(digest) == 64, 'Incomplete known source hash metadata')
        hashes.add(digest)
        for value in [row.get(k, '') for k in ['source_name', 'source_group', 'video_id', 'youtube_id', 'parent_sample_id']]+[Path(row['source_path']).stem]:
            for alias in canonical_aliases(str(value)):
                aliases.setdefault(alias, set()).add(digest)
    return snapshot, aliases, hashes, provenance


def canonical_aliases(value):
    value = value.strip().casefold().replace(' ', '_').replace('\\', '/')
    if not value:
        return set()
    values = {value, value.rsplit('/', 1)[-1]}
    values.add(Path(value.rsplit('/', 1)[-1]).stem)
    for text in tuple(values):
        if text.startswith('charades:'):
            values.add(text[9:])
        if text.startswith('charades_v1/'):
            values.add(Path(text.rsplit('/', 1)[-1]).stem)
    return values


def identity_hits(row, aliases):
    candidates = canonical_aliases(row['source_id']) | canonical_aliases(row['member']['name']) | canonical_aliases('charades:'+row['source_id'])
    return {key: sorted(aliases[key]) for key in sorted(candidates) if key in aliases}


def verify_registration():
    reg_path = ROOT/'registration_01.json'
    reg = read(reg_path)
    for path, digest in reg['input_and_code_bindings'].items():
        require(sha(path) == digest, 'Registered metadata/code changed: '+path)
    require(reg['new_GPU_admitted'] is False and reg['new_optimizer_updates'] == 0, 'Only CPU preparation admitted')
    return reg, sha(reg_path)
