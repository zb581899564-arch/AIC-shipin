"""Inspect pickle opcodes, never execute them, from accepted nonoverlapping bytes."""
import io
import pickletools
import zipfile
from common import ROOT, checked, read, ref, write


class PartialArchive(io.RawIOBase):
    """Fail closed if ZIP metadata tries to read an unreceived byte range."""

    def __init__(self, prefix, tail):
        self.length = tail['stop']
        self.parts = [(row['start'], row['stop'], checked(row['file'])) for row in [prefix, tail]]
        self.position = 0

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.length}[whence]
        self.position = base + offset
        assert 0 <= self.position <= self.length
        return self.position

    def read(self, count=-1):
        count = self.length - self.position if count < 0 else min(count, self.length - self.position)
        for start, stop, path in self.parts:
            if start <= self.position and self.position + count <= stop:
                with path.open('rb') as stream:
                    stream.seek(self.position - start)
                    result = stream.read(count)
                assert len(result) == count
                self.position += count
                return result
        raise ValueError('Metadata read entered an unreceived weight range')


def main():
    recovery = read(ROOT / 'recovery_registration04.json')
    view = PartialArchive(recovery['prefix'], recovery['tail'])
    with zipfile.ZipFile(view) as archive:
        candidates = [r for r in archive.infolist() if r.filename.endswith('/data.pkl')]
        assert len(candidates) == 1 and candidates[0].file_size <= 1000000
        raw = archive.read(candidates[0])
        assert archive.getinfo(candidates[0].filename).CRC == __import__('zlib').crc32(raw)
        globals_used = sorted({str(arg) for op, arg, _ in pickletools.genops(raw) if op.name == 'GLOBAL'})
        rows = len(archive.infolist())
    write(ROOT / 'checkpoint_metadata07.json', dict(
          status='PICKLE_OPCODES_READ_WITHOUT_EXECUTION', bytes=len(raw), archive_entries=rows,
          pickle_globals=globals_used, prefix=recovery['prefix']['file'], tail=recovery['tail']['file'],
          no_missing_ranges_read=True, no_unpickle=True, model_constructed=False,
          full_weight_CRC_or_tensor_compatibility_claim=False, new_network_payload=0))
    print(globals_used)


if __name__ == '__main__':
    main()
