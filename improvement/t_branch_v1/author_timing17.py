"""Obtain the original author's small code-directory index for frame semantics."""
import traceback

from t_io import ROOT, fetch, identity, read, save


def main():
    output = ROOT / 'author_timing17'
    output.mkdir()
    pin = read(ROOT / 'source_manifest15/registration.json')['original_author_commit']
    save(output / 'registration.json', dict(original_author_commit=pin,
        purpose='Locate original code defining frame endpoint semantics, no mirror inference',
        maximum_payload_bytes=128 << 10, no_media_or_model=True))
    path = output / 'code_listing.json'
    fetch('https://api.github.com/repos/aliensunmin/DomainSpecificHighlight/contents/code?ref=' + pin,
          path, 128 << 10)
    rows = read(path)
    if not isinstance(rows, list) or not all(isinstance(row, dict) and 'path' in row for row in rows):
        raise ValueError('Original code index schema differs')
    save(output / 'completion.json', dict(state='ORIGINAL_CODE_DIRECTORY_INDEX_COMPLETE',
        index=identity(path), files=[dict(path=r['path'], bytes=r['size'], git_blob=r['sha'],
                                        type=r['type']) for r in rows],
        endpoint_semantics_not_assumed=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        output = ROOT / 'author_timing17'
        if output.exists():
            save(output / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
