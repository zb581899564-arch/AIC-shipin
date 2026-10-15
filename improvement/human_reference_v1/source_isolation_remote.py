"""Audit actual authorized media against the frozen known source identities."""
import json
import socket
from pathlib import Path

from download_sources_remote import identity
from map_sources_remote import BASE, MEDIA, check_download_admission, read, save, sha


def main():
    assert socket.gethostname() == 'inspur-NP5570M5'
    target = BASE/'source_isolation_acceptance.json'
    assert not target.exists(), 'Successful source separation must not be repeated'
    registration_path = BASE/'human_source_registration_01.json'
    registration, downloaded, _ = check_download_admission(registration_path)
    snapshot_path = BASE/'known_identity_snapshot_01.json'
    snapshot = read(snapshot_path)
    assert snapshot['status'] == 'COMPLETE_KNOWN_B_TRAINING_AND_FROZEN_426_IDENTITIES_NOT_NEW_MEDIA_SEPARATION'
    train = snapshot['training']['sources']
    test = snapshot['testing']['records']
    assert len(train) == 704 and len(test) == 426
    assert {int(r['video_id']) for r in test} == set(range(426))
    assert len({r['youtube_id'] for r in train}) == 602
    remote_provenance = {}
    for name, digest in snapshot['provenance_bindings'].items():
        pieces = name.replace('\\', '/').split('/')
        assert pieces[0] == 'reports' and pieces[1] == 'round6_score_alignment'
        path = Path('/home/inspur/aic_video_work').joinpath(*pieces[1:])
        assert sha(path) == digest, 'Current B training provenance changed'
        remote_provenance[str(path)] = digest
    known = train+test
    known_bytes = {r['source_sha256'] for r in known}
    assert all(len(x) == 64 for x in known_bytes)
    aliases = {}
    for r in known:
        values = [str(r.get(k, '')) for k in ('source_name', 'source_group', 'video_id', 'youtube_id', 'parent_sample_id')]
        values.append(Path(r['source_path']).stem)
        for value in values:
            if value:
                aliases.setdefault(value.casefold().replace(' ', '_'), []).append(r['source_sha256'])
    byte_intersections, identity_intersections, checked = [], [], []
    for row in registration['rows']:
        path = MEDIA/(row['source_name']+'.webm')
        actual = identity(path)
        assert actual == downloaded[row['source_name']]['identity']
        if actual['sha256'] in known_bytes:
            byte_intersections.append(dict(source=row['source_name'], sha256=actual['sha256']))
        for name in (row['source_name'], row['source_group']):
            key = name.casefold().replace(' ', '_')
            if key in aliases:
                identity_intersections.append(dict(source=row['source_name'], comparable_identifier=name, known_sha256=aliases[key]))
        checked.append(dict(source_name=row['source_name'], **actual))
    assert len({r['sha256'] for r in checked}) == 20, 'Registered sources contain byte duplicates'
    result = dict(status='PASS_KNOWN_SOURCE_IDENTITY_AND_BYTE_SEPARATION' if not byte_intersections and not identity_intersections else 'FAILED_KNOWN_SOURCE_INTERSECTION',
        registered_sources=20, registration_sha256=sha(registration_path),
        media_completion_sha256=sha(MEDIA/'completion.json'),
        known_current_b_training_and_426_test_identities_complete=True,
        known_identity_snapshot_path=str(snapshot_path), known_identity_snapshot_sha256=sha(snapshot_path),
        current_training_provenance=remote_provenance, identity_intersections=identity_intersections,
        byte_intersections=byte_intersections, actual_original_media=checked,
        scope_limitations=snapshot['identity_limitations'], semantic_separation_proven=False,
        new_model_calls=0, new_optimizer_updates=0, audit_code_sha256=sha(Path(__file__)))
    if byte_intersections or identity_intersections:
        save(BASE/'source_isolation_failure_01.json', result)
        raise ValueError('Known source intersection; no model admission')
    save(target, result)
    print(json.dumps(dict(status=result['status'], sources=20, known_training_clips=704, known_test_sources=426, semantic_separation_proven=False)), flush=True)


if __name__ == '__main__':
    main()
