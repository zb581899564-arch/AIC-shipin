"""No-permission and changed-registration checks without any real I/O or network."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import download_sources_remote as download


if __name__ == '__main__':
    registration = dict(exact_compressed_media_payload_bytes=861654036, rows=[dict(source_name='test')]*20)
    canonical = hashlib.sha256(json.dumps(registration, sort_keys=True, ensure_ascii=False,
                                         separators=(',', ':')).encode()).hexdigest()
    authorization = dict(approved=False, registration_canonical_sha256=canonical,
                         compressed_media_bytes=861654036, route='ETH_ORIGINAL_ORIGIN_TO_LINUX_DIRECT',
                         registration_sha256='b'*64)
    modified = copy.deepcopy(registration)
    modified['rows'][0]['source_name'] = 'altered_after_approval'
    with tempfile.TemporaryDirectory(prefix='aic_download_guard_') as directory:
        target = Path(directory)/'must_not_exist'
        with patch.object(download, 'OUT', target), patch.object(download.socket, 'gethostname',
                          return_value='inspur-NP5570M5'), patch.object(download.urllib.request, 'urlopen') as network:
            for reference, permission in [(registration, authorization),
                                         (modified, dict(authorization, approved=True))]:
                try:
                    download.main(reference, permission)
                except AssertionError:
                    pass
                else:
                    raise AssertionError('Unapproved or rebound data reached execution')
                assert not target.exists() and network.call_count == 0
    print('PASS: missing permission and changed source registration rejected before mkdir/network')
