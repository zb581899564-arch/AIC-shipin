"""Seekable, durable-cache HTTP Range reader; all bodies require direct TLS routes."""
import http.client
import io
from pathlib import Path
import time
from urllib.parse import urlparse

from t_io import identity, public_route, save


class DirectRanges:
    def __init__(self, url, size, folder, byte_cap=4 << 20, seconds=600):
        self.parsed = urlparse(url)
        if self.parsed.scheme != 'https':
            raise ValueError('Only original HTTPS CDN locations are allowed')
        self.size, self.folder, self.byte_cap = size, Path(folder), byte_cap
        self.position, self.network_bytes = 0, 0
        self.deadline = time.monotonic() + seconds
        self.cache, self.connection, self.route, self.etag = [], None, None, None
        self.folder.mkdir()
        self.journal = (self.folder / 'ranges.jsonl').open('x')

    def close(self):
        if self.connection is not None:
            self.connection.close()
        self.journal.close()

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        destination = offset + (0 if whence == io.SEEK_SET else
                                self.position if whence == io.SEEK_CUR else
                                self.size if whence == io.SEEK_END else self.size + 1)
        if not 0 <= destination <= self.size:
            raise ValueError('Archive seek outside the declared object')
        self.position = destination
        return destination

    def _connect(self):
        if self.connection is None or self.connection.sock is None:
            self.connection = http.client.HTTPSConnection(self.parsed.hostname, timeout=20)
            self.connection.connect()
            self.route = public_route(self.connection.sock.getpeername()[0])
            save(self.folder / ('connection_%03d.json' % len(list(self.folder.glob('connection_*.json')))),
                 dict(host=self.parsed.hostname, strict_TLS=True, before_body_read=True, **self.route))

    def _request(self, start, count):
        import json
        if time.monotonic() > self.deadline or self.network_bytes + count > self.byte_cap:
            raise ValueError('Registered metadata range/time budget exhausted')
        self._connect()
        headers = {'User-Agent': 'AIC-academic-T-range-metadata', 'Accept-Encoding': 'identity',
                   'Range': f'bytes={start}-{start + count - 1}'}
        if self.etag:
            headers['If-Match'] = self.etag
        target = self.parsed.path + ('?' + self.parsed.query if self.parsed.query else '')
        self.connection.request('GET', target, headers=headers)
        response = self.connection.getresponse()
        expected = f'bytes {start}-{start + count - 1}/{self.size}'
        if response.status != 206 or response.getheader('Content-Range') != expected:
            raise ValueError('Range not honored; do not read a full archive response')
        length = response.getheader('Content-Length')
        if length is not None and int(length) != count:
            raise ValueError('Range response length differs before reading')
        new_etag = response.getheader('ETag')
        if self.etag and new_etag != self.etag:
            raise ValueError('Archive object changed between ranges')
        self.etag = new_etag
        path = self.folder / f'{start:012d}_{count:08d}.bin'
        data = response.read(count)
        self.network_bytes += len(data)
        with path.open('xb') as stream:
            stream.write(data)
        if len(data) != count or response.read(1):
            raise ValueError('Incomplete range; retain partial evidence, no automatic repeat')
        record = dict(start=start, count=count, response_range=expected, body=identity(path),
                      object_etag=self.etag, **self.route)
        self.journal.write(json.dumps(record) + '\n')
        self.journal.flush()
        self.cache.append((start, start + count, path))
        return data

    def read(self, size):
        if size < 0:
            raise ValueError('Unbounded archive read is prohibited')
        stop = min(self.position + size, self.size)
        chunks = []
        while self.position < stop:
            cached = next((row for row in self.cache if row[0] <= self.position < row[1]), None)
            if cached:
                first, last, path = cached
                count = min(last, stop) - self.position
                with path.open('rb') as stream:
                    stream.seek(self.position - first)
                    chunks.append(stream.read(count))
            else:
                next_cached = min([row[0] for row in self.cache if row[0] > self.position] + [stop])
                count = min(next_cached, stop) - self.position
                chunks.append(self._request(self.position, count))
            self.position += count
        return b''.join(chunks)

