"""Two pure checks: fixed interval geometry and bound production cut extraction."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import native_motion_inputs42 as inputs


class Checks(unittest.TestCase):
    def test_fixed_native_interval_and_exact_crop_geometry(self):
        sha = 'a' * 64
        for n in [9, 10, 10001]:
            expected = int(hashlib.sha256(('motion42:' + sha).encode()).hexdigest(), 16) % (n - 8)
            self.assertEqual(inputs.interval_start(sha, n), expected)
            self.assertLess(expected + 8, n)
        self.assertEqual(inputs.crop_geometry(1920, 1080)['width_exact'], '1215/2')
        self.assertEqual(inputs.crop_geometry(320, 1000)['height_exact'], '5120/9')
        with self.assertRaises(ValueError):
            inputs.interval_start(sha, 8)
        with self.assertRaises(ValueError):
            inputs.interval_start('not-a-source-sha', 9)

    def test_bound_cut_extraction_and_single_use_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            path = root / 'production_cut.py'
            # Unrelated production imports/main must not execute on this path.
            path.write_text('raise RuntimeError("unrelated CLI side effect")\n'
                'HIST_THRESHOLD = .35\nGRAY_MAD_THRESHOLD = .18\n'
                'def descriptors(frame):\n    return cv2.marker, np.marker, frame\n', encoding='utf-8')
            helper = inputs.cut_helper(inputs.ref(path), root,
                type('CV', (), {'marker': 7})(), type('NP', (), {'marker': 11})())
            self.assertEqual(helper.descriptors('native-BGR'), (7, 11, 'native-BGR'))
            self.assertEqual(len(helper.descriptor_ast_sha256), 64)
            self.assertEqual((helper.HIST_THRESHOLD, helper.GRAY_MAD_THRESHOLD), (.35, .18))
            budget = inputs.OutputBudget(root)
            budget.write(root / 'first.bin', b'actual-first-buffer')
            with self.assertRaises(ValueError):
                budget.write(root / 'first.bin', b'replace-forbidden')
            self.assertEqual((root / 'first.bin').read_bytes(), b'actual-first-buffer')
            altered = inputs.ref(path)
            altered['sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                inputs.cut_helper(altered, root, object(), object())


if __name__ == '__main__':
    unittest.main()
