"""Read retained source/audio identities; no decoding, encoding, fit or model call."""
import argparse
import hashlib
import json
from pathlib import Path
import time


def read(path):
    return json.loads(Path(path).read_text())


def ref(path):
    p = Path(path).resolve(strict=True)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return dict(path=str(p), bytes=p.stat().st_size, sha256=h.hexdigest())


def main(root):
    import av
    t = time.monotonic()
    N = Path(root); R = N.parent; W = R.parent
    assert not (N/'completion13.json').exists(), 'Do not repeat completed inventory'
    inv = read(R/'domain_inventory10/completion10.json')
    records = {}
    for row in inv['all_source_rows']:
        record = read(row['record_ref']['path'])
        records[record['source_sha256']] = record
    old = W/'bottleneck_24h_20261019_v1/audio_semantic23'
    retained = {}
    for row in read(old/'first_audio_inputs.json')['receipts']:
        receipt = read(row['path'])
        retained[receipt['media_ref']['sha256']] = receipt['source_audio_frames_ref']
    train = read(R/'domain_rank11/input_acceptance11.json')
    check = read(R/'relative_ranker06/input_acceptance06.json')
    targets = dict(train=read(train['training_target_ref']['path']), check=read(check['check_target_ref']['path']))
    case_refs = dict(train['case_refs'])
    case_refs.update({k:v for k,v in check['case_refs'].items() if k.startswith('check_')})
    required = {r[k] for rows in targets.values() for r in rows for k in ('left', 'right')}
    assert len(required) == 100
    sources = {}; cases = {}
    for uid in sorted(required):
        c = read(case_refs[uid]['path']); sha = c['source_sha256']; r = records[sha]
        if sha not in sources:
            original = read(r['cache_windows'][0]['input_ref']['path'])
            media = Path(original['source_path']).resolve(strict=True)
            assert original['source_sha256'] == sha and media.stat().st_size == original['source_bytes']
            with av.open(str(media)) as container:
                streams = [dict(index=s.index, codec=s.codec_context.name, rate=s.codec_context.sample_rate,
                                time_base=str(s.time_base), start_time=s.start_time, duration=s.duration)
                           for s in container.streams if s.type == 'audio']
            sources[sha] = dict(video_id=r['video_id'], media_path=str(media), media_bytes=media.stat().st_size,
                media_sha256=sha, original_clock_ref=r['clock_ref'],
                retained_PCM_ref=retained.get(sha), audio_streams=streams, original_scope=r['old_scope'],
                global_original_media_provenance='UNKNOWN', no_audio=not bool(streams))
        b = c['block']
        cases[uid] = dict(uid=uid, source_sha256=sha, start_exact=b['start_exact'], end_exact=b['end_exact'],
                          adopted_visual_case_ref=case_refs[uid], source_id=c.get('sid', uid.split('_')[1]))
    model = read(old/'download_completion.json')['model_ref']
    assert ref(model['path']) == model
    result = dict(status='COMPLETE_RETAINED_ACOUSTIC_ASSET_INVENTORY_NO_MODEL_ADMISSION',
        sources=sources, cases=cases, targets=targets, model_ref=model,
        original_author_code_ref=ref(old/'code/audio_semantic23.py'),
        sources_count=len(sources), retained_PCM_sources=sum(s['retained_PCM_ref'] is not None for s in sources.values()),
        sources_without_audio=[s['video_id'] for s in sources.values() if s['no_audio']],
        new_media_decode=0, new_model_calls=0, new_download=0, new_fit=0,
        seconds=time.monotonic()-t, automatic_model_or_production=False)
    with (N/'completion13.json').open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ['sources','cases','targets']}))


if __name__ == '__main__':
    a=argparse.ArgumentParser(); a.add_argument('--run-root', required=True)
    main(a.parse_args().run_root)
