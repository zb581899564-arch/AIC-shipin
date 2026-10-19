"""Synthetic metadata/tensors only; no HF, real production inputs or models."""
import copy
import datetime as dt
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

import numpy as np
import torch

import pair_production_prepare as production


def test_bound(reference):
    path = Path(reference['path'])
    if production.sha(path) != reference['sha256']:
        raise ValueError('Synthetic reference bytes changed')
    return path


def row(sid, frames):
    return dict(video_id=sid, predictions=[dict(frame=f, bboxes=[0, 0, 16]) for f in frames])


def image_frames(count, offset=0):
    frames = []
    for index in range(count):
        pixels = torch.arange(4*3*256, dtype=torch.float32).reshape(4, 3, 16, 16)+index*10000+offset
        frames.append(torch.stack([pixels, pixels], dim=2).reshape(4, 1536))
    return frames


class ProductionPrepareTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.binding = patch.object(production, 'bound', side_effect=test_bound)
        self.binding.start()

    def tearDown(self):
        self.binding.stop(); self.directory.cleanup()

    def geometry_fixture(self):
        #24 old observations,12 paired groups,48 original native frames.
        native = self.root/'native.npz'; groups_path = self.root/'native_groups.npy'; clock = self.root/'clock.json'
        cells = np.repeat(np.arange(24, dtype=np.int64), 2)
        # This object array is deliberately unreadable with allow_pickle=False.
        # It proves the original40.46/B0 baseline is never an input authority.
        np.savez(native, groups=cells, sample_ordinals=np.arange(0, 48, 2),
                 baseline=np.array([object()], dtype=object))
        np.save(groups_path, cells//2)
        clock.write_text(json.dumps(dict(source_sha256='a'*64,
            normalized_exact_pts=[str(Fraction(i*i+i, 100)) for i in range(48)])), encoding='utf-8')
        source = dict(id='0', source_sha256='a'*64, native_frames=48, feature_cells=24,
            native=production.ref(native), native_groups=production.ref(groups_path), clock=production.ref(clock))
        baseline = production.protected_masks([row('0', list(range(16))+[47])], {'0': 48})['0']
        return source, baseline

    def test_zip_baseline_preserves_added40_47_frames_without_old_native_baseline(self):
        source, baseline = self.geometry_fixture()
        protected = self.root/'protected.zip'
        with zipfile.ZipFile(protected, 'x') as archive:
            archive.writestr('predictions.jsonl', json.dumps(row('0', list(range(16))+[47]))+'\n')
        restored = production.load_protected_masks(protected, {'0': 48})['0']
        geometry = production.source_geometry(source, restored)
        self.assertTrue(restored[47]); self.assertEqual(int(restored.sum()), 17)
        self.assertTrue(np.array_equal(restored, baseline))
        self.assertEqual(geometry['inventory']['baseline_native_frames'], 17)
        self.assertEqual([c['start_group'] for c in geometry['inventory']['candidates']], [4])

    def test_zero_based_native_endpoints_and_bad_frames(self):
        masks = production.protected_masks([row('0', [0, 7])], {'0': 8})
        self.assertEqual(np.flatnonzero(masks['0']).tolist(), [0, 7])
        for frames in ([-1], [8], [True], [1.0], [2, 2], [2, 1]):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                production.protected_masks([row('0', frames)], {'0': 8})

    def test_complete_source_identity_including_legal_empty_baseline(self):
        self.assertEqual(int(production.protected_masks([row('0', [])], {'0': 8})['0'].sum()), 0)
        for rows in ([], [row('1', [])], [row('0', []), row('0', [])]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                production.protected_masks(rows, {'0': 8})

    def test_original_pts_and_full_group_native_boundaries_are_unchanged(self):
        source, baseline = self.geometry_fixture(); saved = baseline.copy()
        geometry = production.source_geometry(source, baseline)
        anchor = geometry['inventory']['anchor']; candidate = geometry['inventory']['candidates'][0]
        self.assertEqual((anchor['cell_start'], anchor['cell_end_exclusive'], anchor['native_start'], anchor['native_end_exclusive']), (0, 8, 0, 16))
        self.assertEqual((candidate['cell_start'], candidate['cell_end_exclusive'], candidate['native_start'], candidate['native_end_exclusive']), (8, 16, 16, 32))
        self.assertEqual(geometry['clock']['normalized_exact_pts'][31], str(Fraction(31*32, 100)))
        self.assertTrue(np.array_equal(saved, baseline))

    def test_mismatched_ownership_or_native_clock_fails(self):
        source, baseline = self.geometry_fixture()
        np.save(Path(source['native_groups']['path']), np.zeros(48, dtype=np.int64))
        source['native_groups'] = production.ref(Path(source['native_groups']['path']))
        with self.assertRaises(ValueError): production.source_geometry(source, baseline)
        source, baseline = self.geometry_fixture()
        clock = production.read(source['clock']['path']); clock['normalized_exact_pts'][1] = 0.02
        Path(source['clock']['path']).write_text(json.dumps(clock), encoding='utf-8')
        source['clock'] = production.ref(Path(source['clock']['path']))
        with self.assertRaises(ValueError): production.source_geometry(source, baseline)

    def test_no_anchor_or_candidate_never_builds_a_model_input(self):
        source, baseline = self.geometry_fixture(); forbidden = Mock(side_effect=AssertionError('No input expected'))
        for mask, status in ((np.zeros(48, dtype=np.bool_), 'ABSTAIN_NO_COMPLETE_BASELINE_ANCHOR'),
                             (np.ones(48, dtype=np.bool_), 'ABSTAIN_NO_DISJOINT_COMPLETE_CANDIDATE')):
            inventory = production.source_geometry(source, mask)['inventory']
            self.assertEqual(production.candidate_requests(inventory, forbidden), [])
            self.assertEqual(production.source_status(inventory), status)
        forbidden.assert_not_called()

    def test_eligible_candidates_have_exactly_both_orders(self):
        source, baseline = self.geometry_fixture()
        inventory = production.source_geometry(source, baseline)['inventory']
        make_input = Mock(side_effect=['candidate_first', 'anchor_first'])
        candidates = production.candidate_requests(inventory, make_input)
        self.assertEqual(make_input.call_args_list[0].args, (inventory['candidates'][0], inventory['anchor']))
        self.assertEqual(make_input.call_args_list[1].args, (inventory['anchor'], inventory['candidates'][0]))
        self.assertEqual(candidates[0]['first_id'], 'candidate_first')
        self.assertEqual(candidates[0]['reverse_id'], 'anchor_first')

    def test_new_saved_baseline_is_full_bool_native_with_protected_binding(self):
        _, baseline = self.geometry_fixture(); path = self.root/'new_baseline.npz'
        production._save_baseline(path, baseline, 'a'*64)
        with np.load(path, allow_pickle=False) as saved:
            self.assertEqual(saved['baseline'].dtype, np.bool_)
            self.assertTrue(np.array_equal(saved['baseline'], baseline))
            self.assertEqual(str(saved['protected_baseline_sha256']), production.PROTECTED_SHA)
        with self.assertRaises(FileExistsError): production._save_baseline(path, baseline, 'a'*64)

    def input_fixture(self):
        reader = production.ProductionInputs.__new__(production.ProductionInputs)
        reader.reg = dict(original_pairing_proof=None); reader.cache = {}; reader.expected = {}; reader.sources = {}
        reader.prepared = dict(class_token_ids=[7, 8, 9])
        appearances = []
        for number in range(2):
            sid = str(number); source_sha = chr(97+number)*64
            clock = self.root/(sid+'.clock.json')
            clock.write_text(json.dumps(dict(source_sha256=source_sha,
                normalized_exact_pts=[str(Fraction(i, 2)) for i in range(16)])), encoding='utf-8')
            frames = image_frames(16, number*1000000)
            pair = production.pair_video_pixels(frames, [2, 2], [[0, 8], [8, 16]], list(range(16)),
                [str(Fraction(i, 2)) for i in range(16)])
            tokens = dict(input_ids=torch.tensor([[11, 12, 13]]), attention_mask=torch.ones((1, 3), dtype=torch.int64))
            tokens_path = self.root/(sid+'.tokens.pt'); torch.save(tokens, tokens_path)
            request_path = self.root/(sid+'.request.json')
            request = dict(id=sid, source_id=sid, source_sha256=source_sha, clip_ranges=[[0, 8], [8, 16]],
                class_token_ids=[7, 8, 9], tokens=production.ref(tokens_path), role='PRODUCTION_NO_LABELS',
                input_signature=production.signature(dict(**tokens, pixel_values_videos=pair['pixel_values_videos'], video_grid_thw=pair['video_grid_thw'])),
                video_grid_thw=pair['video_grid_thw'].tolist(), clip_metadata=pair['clip_metadata'], sample_bindings=pair['sample_bindings'])
            request_path.write_text(json.dumps(request), encoding='utf-8')
            reader.expected[sid] = dict(id=sid, source_id=sid, input=production.ref(request_path))
            reader.sources[sid] = dict(id=sid, source_sha256=source_sha, native_frames=16,
                clock=production.ref(clock), synthetic_frames=frames)
        def loader(source):
            self.assertEqual(len(reader.cache), 0, 'The old source must be released before the next load')
            appearances.append(source['id'])
            return source['synthetic_frames'], [2, 2], list(range(16))
        reader.source_pixels = loader
        return reader, appearances

    def test_runtime_replays_first_signature_and_only_keeps_current_source(self):
        reader, loads = self.input_fixture()
        for sid in ('0', '0', '1', '0'):
            values, request = reader.get(reader.expected[sid]['input'])
            self.assertEqual(set(reader.cache), {sid})
            self.assertEqual(production.signature(values), request['input_signature'])
        self.assertEqual(loads, ['0', '1', '0'])

    def test_runtime_rejects_changed_token_cache_or_unaccepted_request(self):
        reader, _ = self.input_fixture(); original = reader.expected['0']['input']
        changed = copy.deepcopy(production.read(original['path'])); changed['role'] = 'EXTERNAL_DEV_INFERENCE'
        other = self.root/'foreign.json'; other.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaises(ValueError): reader.get(production.ref(other))
        token_path = Path(production.read(original['path'])['tokens']['path'])
        with token_path.open('ab') as stream: stream.write(b'changed')
        with self.assertRaises(ValueError): reader.get(original)

    def test_past_goal_deadline_blocks_new_preparation(self):
        with self.assertRaises(ValueError): production._deadline(dict(deadline_utc='2000-01-01T00:00:00Z'))
        production._deadline(dict(deadline_utc=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat()))


if __name__ == '__main__':
    unittest.main()
