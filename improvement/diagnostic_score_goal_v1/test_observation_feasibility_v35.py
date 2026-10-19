"""Small synthetic-only layout/artifact tests; no real cache or processor/model."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

import crop_geometry_v31
import crop_observation_v34 as observation
import observation_feasibility_v35 as feasibility


def layout(tensor_ref, grid=(1, 2, 4), start=0, end=8):
    return dict(tensor_ref=tensor_ref, pixel_key='saved_pixels', row_start=start, row_end_exclusive=end,
        grid_thw=list(grid), grid_locator=dict(kind='TENSOR_ROW', key='saved_grids', row_index=0),
        normalization=feasibility.NORMALIZATION)


def registration(root):
    accepted = root/'accepted.json'
    accepted.write_text('{"status":"SYNTHETIC_OLD_SUCCESS"}', encoding='utf-8')
    entries = []
    for i in range(4):
        y, x = np.indices((32, 64))
        rgb = np.stack(((x+17*i)%256, y, (x+3*y+i)%256), axis=-1).astype(np.uint8)
        pixels, grid = observation.forward_pack_observation_rgb(rgb)
        tensor = root/('synthetic_%d.pt'%i)
        torch.save(dict(saved_pixels=pixels, saved_grids=grid), tensor)
        entries.append(dict(entry_id='external_%d'%i, source_id='synthetic_%d'%i,
            source_sha256=('%064x'%(i+1)), native_dimensions=[160, 90],
            accepted_input_ref=feasibility._ref(accepted), layout=layout(feasibility._ref(tensor))))
    reg = dict(schema=feasibility.SCHEMA, self_code=feasibility._ref(feasibility.__file__),
        recovery_code=feasibility._ref(observation.__file__), geometry_code=feasibility._ref(crop_geometry_v31.__file__),
        identity_evidence_refs=[feasibility._ref(accepted)],
        deadline_utc=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1)).isoformat(),
        selection=dict(method='LEXICOGRAPHIC_SOURCE_SHA256_FIRST4',
            candidate_sources=[{key:row[key] for key in ('source_id', 'source_sha256')} for row in entries]),
        external=entries, production=[])
    return reg


def save_registration(root, reg):
    path = root/'observation_feasibility_registration_35.json'
    path.write_text(json.dumps(reg), encoding='utf-8')
    return path


class ObservationFeasibilityTests(unittest.TestCase):
    def test_explicit_row_offset_and_actual_grid_selection(self):
        dummy = dict(path=str(Path(__file__).resolve()), sha256='a'*64)
        rgb = np.arange(32*64*3, dtype=np.uint8).reshape(32, 64, 3)
        pixels, grid = observation.forward_pack_observation_rgb(rgb)
        payload = dict(saved_pixels=torch.cat((pixels+10, pixels), dim=0), saved_grids=torch.cat((grid, grid)))
        spec = layout(dummy, start=8, end=16); spec['grid_locator']['row_index'] = 1
        actual, actual_grid = feasibility.extract_pixels(payload, spec)
        self.assertTrue(torch.equal(actual, pixels)); self.assertTrue(torch.equal(actual_grid, grid))
        restored, meta = observation.recover_observation_rgb(actual, actual_grid)
        np.testing.assert_array_equal(restored, rgb)
        observation.independent_recovery_check(actual, actual_grid, restored, meta)

    def test_wrong_row_grid_key_and_normalization_fail(self):
        dummy = dict(path=str(Path(__file__).resolve()), sha256='a'*64)
        pixels, grid = observation.forward_pack_observation_rgb(np.zeros((32, 64, 3), np.uint8))
        payload = dict(saved_pixels=pixels, saved_grids=grid)
        for mode in ('rows', 'bounds', 'grid', 'gridrow', 'key', 'normalization'):
            spec = layout(dummy)
            if mode == 'rows': spec['row_end_exclusive'] = 7
            elif mode == 'bounds': spec['row_start'], spec['row_end_exclusive'] = 1, 9
            elif mode == 'grid': spec['grid_thw'] = [1, 4, 2]
            elif mode == 'gridrow': spec['grid_locator']['row_index'] = 1
            elif mode == 'key': spec['pixel_key'] = 'guessed_key'
            else: spec['normalization'] = '(u/255-.5)/.5'
            with self.assertRaises(ValueError): feasibility.extract_pixels(payload, spec)
        bad = dict(payload, saved_pixels=pixels.half())
        with self.assertRaises(ValueError): feasibility.extract_pixels(bad, layout(dummy))

    def test_changed_numeric_normalization_fails_exact_recovery(self):
        dummy = dict(path=str(Path(__file__).resolve()), sha256='a'*64)
        pixels, grid = observation.forward_pack_observation_rgb(np.full((32, 64, 3), 128, np.uint8))
        wrong = pixels.reshape(8, 3, 2, 16, 16).clone()
        wrong[0, 0, :, 0, 0] = torch.nextafter(wrong[0, 0, :, 0, 0], torch.full((2,), float('inf')))
        actual, g = feasibility.extract_pixels(dict(saved_pixels=wrong.reshape(8, 1536), saved_grids=grid), layout(dummy))
        with self.assertRaises(ValueError): observation.recover_observation_rgb(actual, g)

    def test_registration_sha_first4_production_bound_and_no_unknown_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            reg = registration(Path(directory))
            self.assertEqual(len(feasibility.validate_registration(reg)), 4)
            wrong = copy.deepcopy(reg); wrong['external'].reverse()
            with self.assertRaises(ValueError): feasibility.validate_registration(wrong)
            wrong = copy.deepcopy(reg); wrong['production'] = [dict(reg['external'][0], entry_id='p%d'%i) for i in range(3)]
            with self.assertRaises(ValueError): feasibility.validate_registration(wrong)
            wrong = copy.deepcopy(reg); wrong['external'][0]['GT'] = [0, 0, 1, 1]
            with self.assertRaises(ValueError): feasibility.validate_registration(wrong)
            wrong = copy.deepcopy(reg); wrong['external'][0]['layout']['grid_locator'] = dict(kind='GUESS')
            with self.assertRaises(ValueError): feasibility.validate_registration(wrong)

    def test_synthetic_run_saves_only_resized_evidence_and_exclusive_no_retry(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'CUDA_VISIBLE_DEVICES':''}):
            root = Path(directory); reg = registration(root); save_registration(root, reg)
            result = feasibility.run(root)
            self.assertEqual(result['external_sources'], 4); self.assertEqual(result['production_observations'], 0)
            self.assertFalse(result['native_RGB_recovered']); self.assertFalse(result['quality_evaluated'])
            for reference in result['receipts']:
                receipt = feasibility._read(feasibility._bound(reference))
                image = np.load(feasibility._bound(receipt['resized_RGB']), allow_pickle=False)
                self.assertEqual(image.shape, (32, 64, 3)); self.assertEqual(len(receipt['crops']), 2)
                self.assertEqual(receipt['formula_code'], reg['recovery_code'])
                self.assertEqual(receipt['identity_evidence_refs'], reg['identity_evidence_refs'])
                self.assertFalse(receipt['native_RGB_recovered'])
            with self.assertRaises(FileExistsError): feasibility.run(root)

    def test_failure_preserves_completed_entry_and_has_no_fallback(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'CUDA_VISIBLE_DEVICES':''}):
            root = Path(directory); reg = registration(root)
            second = Path(reg['external'][1]['layout']['tensor_ref']['path'])
            data = torch.load(second, map_location='cpu', weights_only=True)
            data['saved_pixels'] = torch.full_like(data['saved_pixels'], 1.01)
            torch.save(data, second); reg['external'][1]['layout']['tensor_ref'] = feasibility._ref(second)
            save_registration(root, reg)
            with self.assertRaises(ValueError): feasibility.run(root)
            out = root/feasibility.OUTPUT_DIRECTORY
            failure = feasibility._read(out/'failure.json')
            self.assertEqual(len(failure['completed_receipts']), 1)
            self.assertEqual(failure['active_entry'], 'external_1')
            self.assertFalse((out/'result.json').exists())
            self.assertTrue((out/'external_0/receipt.json').is_file())
            with self.assertRaises(FileExistsError): feasibility.run(root)


if __name__ == '__main__':
    unittest.main()
