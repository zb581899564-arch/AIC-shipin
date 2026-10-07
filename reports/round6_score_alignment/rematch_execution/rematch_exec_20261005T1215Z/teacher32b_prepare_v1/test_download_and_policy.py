import hashlib
import io
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import download_weights as downloader

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'resource_unlimited_v1_20261007'))
from physical_capacity import admit


class Response(io.BytesIO):
    def __init__(self, data, status=200, content_range=None):
        super().__init__(data)
        self.status=status
        self.headers={} if content_range is None else {'Content-Range':content_range}


class Contracts(unittest.TestCase):
    def recipe(self, payload):
        row={'path':'model.gguf','size_bytes':len(payload),'lfs_sha256':hashlib.sha256(payload).hexdigest()}
        return {'repo':'Qwen/example','revision':'f'*40,'files':[row]},row

    def test_server_ignoring_range_replaces_partial(self):
        payload=b'complete pinned artifact bytes'
        recipe,row=self.recipe(payload)
        with tempfile.TemporaryDirectory() as name:
            path=Path(name);(path/'model.gguf.incomplete').write_bytes(payload[:5])
            with patch.object(downloader.urllib.request,'urlopen',return_value=Response(payload)):
                downloader.download_file(recipe,row,path,lambda *a,**k:None)
            self.assertEqual((path/'model.gguf').read_bytes(),payload)

    def test_correct_range_resume_preserves_prefix(self):
        payload=b'complete pinned artifact bytes';recipe,row=self.recipe(payload)
        with tempfile.TemporaryDirectory() as name:
            path=Path(name);(path/'model.gguf.incomplete').write_bytes(payload[:5])
            response=Response(payload[5:],206,f'bytes 5-{len(payload)-1}/{len(payload)}')
            with patch.object(downloader.urllib.request,'urlopen',return_value=response):
                downloader.download_file(recipe,row,path,lambda *a,**k:None)
            self.assertEqual((path/'model.gguf').read_bytes(),payload)

    def test_mismatched_range_never_appends(self):
        payload=b'complete pinned artifact bytes';recipe,row=self.recipe(payload)
        with tempfile.TemporaryDirectory() as name:
            path=Path(name);partial=path/'model.gguf.incomplete';partial.write_bytes(payload[:5])
            response=Response(payload[5:],206,f'bytes 0-{len(payload)-1}/{len(payload)}')
            with patch.object(downloader.urllib.request,'urlopen',return_value=response),self.assertRaises(ValueError):
                downloader.download_file(recipe,row,path,lambda *a,**k:None)
            self.assertEqual(partial.read_bytes(),payload[:5])
            self.assertFalse((path/'model.gguf').exists())

    def test_wrong_full_bytes_not_accepted(self):
        payload=b'complete pinned artifact bytes';recipe,row=self.recipe(payload)
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)
            with patch.object(downloader.urllib.request,'urlopen',return_value=Response(b'x'*len(payload))),self.assertRaises(ValueError):
                downloader.download_file(recipe,row,path,lambda *a,**k:None)
            self.assertFalse((path/'model.gguf').exists())

    def test_over_old_80gib_allowed_if_actual_disk_fits(self):
        p={'disk_usage_mode':'ACTUAL_CAPACITY_ONLY','added_disk_budget_gib':80}
        self.assertEqual(admit(p,disk_free_bytes=200*2**30,remaining_output_bytes=120*2**30)['status'],'ADMITTED_ACTUAL_CAPACITY')

    def test_actual_disk_exhaustion_refused(self):
        with self.assertRaises(ValueError):
            admit({'disk_usage_mode':'ACTUAL_CAPACITY_ONLY'},disk_free_bytes=10,remaining_output_bytes=11)

    def test_unknown_or_boolean_capacity_refused(self):
        for value in (None,True,-1):
            with self.assertRaises(ValueError):
                admit({'disk_usage_mode':'ACTUAL_CAPACITY_ONLY'},disk_free_bytes=value,remaining_output_bytes=0)


if __name__=='__main__':unittest.main()
