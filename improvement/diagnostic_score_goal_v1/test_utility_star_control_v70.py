from pathlib import Path
import tempfile
import unittest
from unittest import mock

import utility_star_control_v70 as control


class StarControlTests(unittest.TestCase):
    def fixture(self, root):
        def ref(path): return dict(path=str(path), sha256='a'*64)
        original_path = root/'utility_star_GPU_registration_69.json'
        original = dict(schema='UTILITY_CONNECTED_STAR_CONTINUATION_V69', controller_code=ref(Path(control.__file__).resolve()),
            input_acceptance=ref(root/'gate.json'), prepared=ref(root/'prepared.json'), CPU_registration=ref(root/'cpu.json'),
            GPU_code=ref(root/'gpu.py'), math_code=ref(root/'math.py'), max_seconds=1200, GPU_job='new_pilot')
        gate = dict(status='PASS_UTILITY68_CONNECTED_STAR_ALL_INPUTS_FIRST_CPU_QA', prepared=original['prepared'], registration=original['CPU_registration'])
        remaining = dict(schema='UTILITY_CONNECTED_STAR_REMAINING796_V69', original_GPU_registration=ref(original_path),
            expected_remaining_updates=796, pilot_output_acceptance=ref(root/'pilotQA.json'),
            immutable_pilot_progress=ref(root/'pilot_progress.pt'), pilot_completion=ref(root/'pilot_completion.json'),
            max_seconds=6000, GPU_job='new_remaining', **{k:original[k] for k in ('GPU_code', 'math_code', 'prepared', 'input_acceptance')})
        prior = dict(status='PASS_STAR_GLOBAL504_FIRST_ENGINEERING_QA', registration=ref(original_path),
            engineering=dict(global_updates=504, progress=remaining['immutable_pilot_progress']), pilot_completion=remaining['pilot_completion'])
        docs = {str(original_path):original, str(root/'gate.json'):gate,
            str(root/'utility_star_remaining_admission_69.json'):remaining, str(root/'pilotQA.json'):prior}
        return docs, prior, ref

    def test_only_explicit_new_phase_and_accepted504(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); docs, prior, ref = self.fixture(root)
            with mock.patch.object(control, 'bound', side_effect=lambda r:Path(r['path'])), \
                 mock.patch.object(control, 'read', side_effect=lambda p:docs[str(p)]), mock.patch.object(control, 'ref', side_effect=ref):
                self.assertEqual(control.phase_contract(root, 'pilot4')[-1], 1200)
                self.assertEqual(control.phase_contract(root, 'remaining796')[-1], 6000)
                with self.assertRaises(ValueError): control.phase_contract(root, 'cpu')
                prior['engineering']['global_updates'] = 4
                with self.assertRaises(ValueError): control.phase_contract(root, 'remaining796')


if __name__ == '__main__': unittest.main()
