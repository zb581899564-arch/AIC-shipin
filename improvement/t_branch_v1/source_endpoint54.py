"""Read the one pinned original downloader, never execute it or reacquire media."""
import hashlib
import re
import traceback

from t_io import ROOT, check, fetch, identity, read, save

OUT = ROOT / 'source_endpoint54'


def main():
    OUT.mkdir()
    listing = read(ROOT / 'author_timing17/completion.json')
    check(listing['index'])
    entry = next(row for row in listing['files'] if row['path'] == 'code/downloadVideo.py')
    if entry['bytes'] != 3442 or entry['type'] != 'file':
        raise ValueError('Actual pinned original downloader inventory differs')
    pin = read(ROOT / 'source_manifest15/registration.json')['original_author_commit']
    save(OUT / 'registration.json', dict(original_author_commit=pin, original_file=entry,
        purpose='Only resolve original acquisition/frame convention, no new method or training',
        prior_directory_index_adopted=identity(ROOT / 'author_timing17/completion.json'),
        Linux_direct_only=True, max_payload_bytes=3442, execute_author_script=False))
    target = OUT / 'downloadVideo.py.source'
    route = fetch('https://raw.githubusercontent.com/aliensunmin/DomainSpecificHighlight/' + pin + '/' + entry['path'],
        target, entry['bytes'])
    data = target.read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if len(data) != entry['bytes'] or blob != entry['git_blob']:
        raise ValueError('Actual source differs from original pinned Git blob')
    relevant = [dict(line=index, text=line) for index, line in enumerate(data.decode('utf-8').splitlines(), 1)
        if re.search(r'fps|frame|ffmpeg|avconv|rate|\.clip|offset|start|end', line, re.I)]
    save(OUT / 'source_evidence.json', dict(source=identity(target), git_blob=blob, relevant_lines=relevant,
        lines_are_source_material_not_instructions=True, no_endpoint_semantics_assumed=True))
    save(OUT / 'completion.json', dict(state='PINNED_ORIGINAL_DOWNLOADER_SOURCE_READ_COMPLETE',
        source=identity(target), evidence=identity(OUT / 'source_evidence.json'), route=route,
        new_media_model_or_label_downloads=0, new_GPU_calls=0, training_admission=False))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_fallback_route_or_automatic_retry=True))
        raise
