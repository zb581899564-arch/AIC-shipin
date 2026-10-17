"""Synthetic file-reference checks only; no model, media, or historical stage."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mf_common as common


class ReferencePathTests(unittest.TestCase):
    def test_checked_uses_actual_location_before_reading_bytes(self):
        with tempfile.TemporaryDirectory(prefix='aic_ref_contract_') as temporary:
            task_root = Path(temporary)/'run'
            task_root.mkdir()
            inside = task_root/'input.json'
            outside = Path(temporary)/'other_run.json'
            # Identical bytes show that a matching SHA alone cannot establish
            # membership in the registered root.
            inside.write_text('{"synthetic":true}', encoding='utf-8')
            outside.write_bytes(inside.read_bytes())
            digest = common.sha(inside)
            with patch.object(common, 'HOME', task_root):
                self.assertEqual(common.checked(dict(path=str(inside), sha256=digest)), inside)
                with self.assertRaises(ValueError):
                    common.checked(dict(path=str(inside), sha256='0'*64))

                escaped = task_root/'..'/'other_run.json'
                escaped_link = task_root/'escaped.json'
                escaped_link.symlink_to(outside)
                for target in (escaped, escaped_link):
                    with self.subTest(target=target):
                        # A wrong-root file is rejected without reading or
                        # hashing it, even when its recorded digest matches.
                        with patch.object(common, 'sha', side_effect=AssertionError('outside bytes read')):
                            with self.assertRaises(ValueError):
                                common.checked(dict(path=str(target), sha256=digest))

                internal_link = task_root/'internal.json'
                internal_link.symlink_to(inside)
                self.assertEqual(common.checked(dict(path=str(internal_link), sha256=digest)), inside)
                with self.assertRaises(ValueError):
                    common.checked(dict(path=str(task_root), sha256=digest))


if __name__ == '__main__':
    unittest.main()
