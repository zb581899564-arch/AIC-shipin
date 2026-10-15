"""Small offline checks of >4GiB ZIP64 parsing and unsafe/duplicate members."""
import struct
import unittest
import metadata_index as m


def central(name, size=100, packed=80, offset=10, extra=b''):
    raw = name.encode()
    return struct.pack('<4s6H3I5H2I', b'PK\x01\x02', 45, 45, 0, 8, 0, 0, 123,
        packed, size, len(raw), len(extra), 0, 0, 0, 0, offset)+raw+extra


class DirectoryTests(unittest.TestCase):
    def test_member_zip64_sizes_and_offset_above4gib(self):
        extra = struct.pack('<HH3Q', 1, 24, 5000000001, 4500000001, 55000000001)
        raw = central('Charades_v1/ABCDE.mp4', 0xffffffff, 0xffffffff, 0xffffffff, extra)
        row = m.parse_directory(raw, 1, 58000000000)[0]
        self.assertEqual((row['bytes'], row['compressed_bytes'], row['header_offset']),
                         (5000000001, 4500000001, 55000000001))

    def test_zip64_directory_offset_above4gib(self):
        cd_offset, cd_size, rec_offset, total = 58000000000, 100, 58000000100, 58000000198
        record = struct.pack('<4sQ2H2I4Q', b'PK\x06\x06', 44, 45, 45, 0, 0, 1, 1, cd_size, cd_offset)
        locator = struct.pack('<4sIQI', b'PK\x06\x07', 0, rec_offset, 1)
        eocd = struct.pack('<4s4H2IH', b'PK\x05\x06', 0, 0, 1, 1, cd_size, 0xffffffff, 0)
        calls = []
        def fetch(offset, length):
            calls.append((offset, length))
            return record
        result = m.end_records(record+locator+eocd, total, fetch)
        self.assertEqual((result['directory_offset'], result['directory_bytes']), (cd_offset, cd_size))
        self.assertEqual(calls, [(rec_offset, 56)])

    def test_unsafe_and_duplicate_members_rejected(self):
        for name in ('../ABCDE.mp4', '/ABCDE.mp4', 'X:\\ABCDE.mp4'):
            with self.assertRaises(ValueError):
                m.parse_directory(central(name), 1, 1000)
        raw = central('ABCDE.mp4')*2
        with self.assertRaises(ValueError):
            m.parse_directory(raw, 2, 1000)

    def test_missing_zip64_member_payload_rejected(self):
        with self.assertRaises(ValueError):
            m.parse_directory(central('ABCDE.mp4', offset=0xffffffff), 1, 58000000000)


if __name__ == '__main__':
    unittest.main()
