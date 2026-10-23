"""First bounded mirror metadata only; no media, model, decoder, or training."""
from pathlib import Path
import traceback
from t_io import ROOT, WORK, read, save, identity, fetch


def main():
    output = ROOT / 'source_metadata01'; output.mkdir()
    prior = WORK / 'i3d_umt_cross_domain_20261021_v1/source_inventory01.json'
    original = read(prior)
    save(output / 'registration.json', dict(original_author_inventory=identity(prior),
        original_author_commit=original['commit'], requested='Pinned mirror API/card/manifest and original README only',
        request_max_bytes=2 << 20, no_media_or_models=True, no_implicit_training=True))
    sources = [('mirror_api.json', 'https://huggingface.co/api/datasets/jhanglee/youtube-highlights-full'),
        ('author_README.md', 'https://raw.githubusercontent.com/aliensunmin/DomainSpecificHighlight/' + original['commit'] + '/README.md')]
    accepted = []; failed = []
    for name, url in sources:
        try: accepted.append(fetch(url, output / name, 2 << 20))
        except Exception: failed.append(dict(url=url, traceback=traceback.format_exc()))
    api = output / 'mirror_api.json'
    if api.exists():
        meta = read(api); sha = meta['sha']
        files = [entry['rfilename'] for entry in meta.get('siblings', [])]
        save(output / 'pinned_mirror.json', dict(commit=sha, files=files, card=meta.get('cardData'),
            no_media_downloaded=True, not_original_author=True))
        targets = [name for name in files if name in ['README.md', 'manifest.json', 'SHA256SUMS']]
        for name in targets:
            try:
                accepted.append(fetch('https://huggingface.co/datasets/jhanglee/youtube-highlights-full/resolve/' + sha + '/' + name,
                    output / ('mirror_' + name), 2 << 20))
            except Exception: failed.append(dict(name=name, traceback=traceback.format_exc()))
    save(output / 'completion.json', dict(state='BOUNDED_METADATA_ATTEMPT_COMPLETE_NOT_MEDIA_ADMISSION',
        accepted=accepted, failed=failed, new_media=0, new_model_calls=0, new_training=0))
    print('T_METADATA01_COMPLETE', len(accepted), 'accepted', len(failed), 'failed', flush=True)


if __name__ == '__main__': main()
