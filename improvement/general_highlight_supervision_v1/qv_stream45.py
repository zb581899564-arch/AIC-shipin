"""Bounded sequential author tar prefix; accepted compressed ranges are never refetched."""
import http.client
import io
from pathlib import Path
import socket
import ssl
from urllib.parse import urlparse

from common import ref, route_for, save


class PrefixLimit(Exception):
    """The registered byte cap was reached, not an empty/failed video."""


class AuthorRanges(io.RawIOBase):
    def __init__(self, root, head, prefix, limit):
        self.root = Path(root)
        self.head = head
        self.parsed = urlparse(head['final_url'])
        self.offset = prefix.stat().st_size
        self.buffer = prefix.read_bytes()
        self.position = 0
        self.limit = limit
        self.chunk_bytes = 8 << 20
        self.index = 0

    def readable(self):
        return True

    def read(self, size=-1):
        if size < 0:
            raise ValueError('Unbounded archive read is forbidden')
        if self.position == len(self.buffer):
            self.next_range()
        result = self.buffer[self.position:self.position + size]
        self.position += len(result)
        return result

    def next_range(self):
        if self.offset >= self.limit:
            raise PrefixLimit('Registered compressed-prefix cap reached')
        first = self.offset
        stop = min(first + self.chunk_bytes, self.limit)
        path = self.root / f'compressed_{first:012d}_{stop-1:012d}.bin'
        connection = http.client.HTTPSConnection(
            self.parsed.hostname, timeout=35, context=ssl.create_default_context())
        connection._create_connection = lambda address, timeout, source_address=None: socket.create_connection(
            (self.head['public_peer'], address[1]), timeout, source_address)
        try:
            connection.connect()
            route = route_for(connection.sock.getpeername()[0])
            connection.request('GET', self.parsed.path, headers={
                'Range': f'bytes={first}-{stop-1}', 'Accept-Encoding': 'identity',
                'User-Agent': 'AIC-noncommercial-source-research'})
            response = connection.getresponse()
            if (response.status != 206 or response.getheader('Content-Range') !=
                    f'bytes {first}-{stop-1}/{self.head["bytes"]}'):
                raise ValueError('Exact author Range not honored; body not accepted')
            save(path.with_suffix('.connected.json'), dict(
                before_first_body_read=True, status=response.status,
                last_modified=response.getheader('Last-Modified'),
                etag=response.getheader('ETag'), **route))
            count = 0
            partial = path.with_suffix('.partial')
            with partial.open('xb') as out:
                while count < stop - first:
                    block = response.read(min(1 << 18, stop - first - count))
                    if not block:
                        raise EOFError('Incomplete new range; partial retained')
                    out.write(block)
                    count += len(block)
            if response.read(1):
                raise ValueError('Author Range exceeded registered extent')
            partial.rename(path)
            save(path.with_suffix('.acceptance.json'), dict(
                compressed=ref(path), range=[first, stop-1], **route))
            self.buffer = path.read_bytes()
            self.position = 0
            self.offset = stop
            self.index += 1
            print('QV_RANGE_ACCEPTED', first, stop-1, flush=True)
        finally:
            connection.close()
