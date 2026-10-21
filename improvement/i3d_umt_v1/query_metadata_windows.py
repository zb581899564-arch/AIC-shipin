"""Exactly two explicitly authorized YouTube metadata queries, never media."""
import argparse
import json
from pathlib import Path
import time


class MetadataLogger:
    def __init__(self):
        self.messages = []

    def debug(self, message):
        pass

    def warning(self, message):
        self.messages.append(str(message))

    def error(self, message):
        self.messages.append(str(message))


def query_one(row):
    from yt_dlp import YoutubeDL
    logger = MetadataLogger()
    started = time.monotonic()
    options = dict(skip_download=True, quiet=True, noplaylist=True, cachedir=False,
                   socket_timeout=10, retries=0, extractor_retries=0,
                   ignore_no_formats_error=True, logger=logger,
                   writethumbnail=False, writesubtitles=False, writeautomaticsub=False)
    try:
        with YoutubeDL(options) as api:
            info = api.extract_info('https://www.youtube.com/watch?v=' + row['source_id'], download=False)
        assert info and info['id'] == row['source_id']
        keys = ['id', 'title', 'license', 'duration', 'fps', 'width', 'height',
                'uploader', 'channel_id', 'availability', 'upload_date', 'timestamp',
                'description', 'live_status', 'webpage_url']
        metadata = {k: info.get(k) for k in keys}
        # No signed media URLs are saved or fetched. Format metadata alone is sufficient.
        metadata['formats'] = [{k: f.get(k) for k in ['format_id', 'ext', 'fps', 'width', 'height',
                                                     'filesize', 'filesize_approx', 'vcodec', 'acodec']}
                               for f in info.get('formats', [])]
        complete = bool(metadata['formats']) and metadata.get('duration') is not None
        status = 'METADATA_RECEIVED_NO_MEDIA' if complete else 'INCOMPLETE_OR_UNAVAILABLE_METADATA_NO_MEDIA'
        result = dict(status=status, source=row, metadata=metadata)
    except Exception as error:
        result = dict(status='METADATA_QUERY_FAILED_NO_MEDIA', source=row,
                      error_type=type(error).__name__, error=str(error))
    result.update(seconds=time.monotonic() - started, warnings=logger.messages,
                  media_downloads=0, model_calls=0, network_config_changed=False)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=[0, 1], required=True)
    args = parser.parse_args()
    registration = json.loads(args.registration.read_text(encoding='utf8'))
    assert registration['active_answer'] == '\u5141\u8bb8\u67e5\u8fd9\u4e24\u6761\uff0c\u521a\u8bf4\u9519\u4e86'
    assert [r['source_id'] for r in registration['sources']] == ['AUAsfZtcB4E', 'KKjovY6uXFY']
    row = registration['sources'][args.index]
    output = args.registration.parent / f"{row['source_id']}_result.json"
    with output.with_suffix('.claim.json').open('x', encoding='utf8') as stream:
        json.dump(dict(source=row, scope='METADATA_ONLY', media_downloads=0), stream)
    result = query_one(row)
    with output.open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k not in ['metadata', 'warnings']}, ensure_ascii=True))


if __name__ == '__main__':
    main()
