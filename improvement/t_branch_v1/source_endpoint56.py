"""One official Git-blob fallback from cached metadata after actual raw timeout."""
import base64
import hashlib
import re
import traceback

from t_io import ROOT, check, fetch, identity, read, save

OUT = ROOT / 'source_endpoint56'


def main():
    OUT.mkdir()
    failure = ROOT / 'source_endpoint54/failure.json'
    if 'TimeoutError' not in read(failure)['traceback']:
        raise ValueError('Expected actual raw read timeout absent')
    index = read(ROOT / 'author_timing17/completion.json')['index']
    row = next(item for item in read(check(index)) if item['path'] == 'code/downloadVideo.py')
    if row['sha'] != '3638a402ed96813764930faaa88e9e025242ea68' or row['size'] != 3442:
        raise ValueError('Fixed cached original Git blob identity differs')
    expected = 'https://api.github.com/repos/aliensunmin/DomainSpecificHighlight/git/blobs/' + row['sha']
    if row['git_url'] != expected:
        raise ValueError('Cached authoritative alternate endpoint differs')
    save(OUT / 'registration.json', dict(original_cached_index=index, actual_raw_failure=identity(failure),
        alternate='One official Git blob endpoint supplied by original cached index, no mirror or proxy',
        max_API_payload_bytes=8192, max_decoded_code_bytes=3442, no_media_model_or_training=True))
    path = OUT / 'git_blob.json'
    route = fetch(expected, path, 8192, headers={'Accept': 'application/vnd.github+json'})
    payload = read(path)
    if payload['sha'] != row['sha'] or payload['encoding'] != 'base64' or payload['size'] != 3442:
        raise ValueError('Original Git blob response schema/identity differs')
    data = base64.b64decode(''.join(payload['content'].split()), validate=True)
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if len(data) != 3442 or blob != row['sha']:
        raise ValueError('Original decoded source bytes differ')
    source = OUT / 'downloadVideo.py.source'
    with source.open('xb') as stream:
        stream.write(data)
    relevant = [dict(line=index, text=line) for index, line in enumerate(data.decode('utf-8').splitlines(), 1)
        if re.search(r'fps|frame|ffmpeg|avconv|rate|\.clip|offset|start|end', line, re.I)]
    save(OUT / 'source_evidence.json', dict(source=identity(source), relevant_lines=relevant,
        source_material_not_instructions=True, author_script_not_executed=True))
    save(OUT / 'completion.json', dict(state='PINNED_ORIGINAL_GIT_BLOB_SOURCE_READ_COMPLETE',
        source=identity(source), evidence=identity(OUT / 'source_evidence.json'), route=route,
        training_admission=False, new_media_model_or_label_downloads=0, new_GPU_calls=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_further_automatic_retry_or_route_fallback=True))
        raise
