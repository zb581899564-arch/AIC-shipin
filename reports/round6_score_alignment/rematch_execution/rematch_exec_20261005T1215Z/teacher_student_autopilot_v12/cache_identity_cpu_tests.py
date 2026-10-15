"""Real canonical parameter hashing and real Linux B2 receipt consumption; no GPU."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import torch
import autopilot_common as c
import production_t as p
import train_student as s

s.helper_paths(c.RUN)
from verify_saved_smoke import canonical_frozen_hash


class LoadedBaseIdentity(unittest.TestCase):
    def setUp(self):
        self.model = torch.nn.Linear(2, 2, bias=False)
        with torch.no_grad():
            self.model.weight.copy_(torch.tensor([[1., 2.], [3., 4.]]))
        self.model.requires_grad_(False)
        self.identity = canonical_frozen_hash(self.model, torch)
        self.config = dict(model_dir='CPU_ONLY_MODEL', expected_base_sha256=self.identity['sha256'],
                           base_parameters=self.identity['parameters'])
        self.pins = patch.multiple(p, BASE_SHA=self.identity['sha256'], BASE_PARAMETERS=self.identity['parameters'])
        self.pins.start()
        self.addCleanup(self.pins.stop)

    def test_real_canonical_hash_and_all_parameters_frozen(self):
        self.model.requires_grad_(True)
        self.assertEqual(p.verify_spatial_base(self.model, self.config), self.identity)
        self.assertTrue(all(not parameter.requires_grad for parameter in self.model.parameters()))

    def test_changed_bytes_same_count_rejected(self):
        with torch.no_grad():
            self.model.weight[0, 0] += 1
        with self.assertRaisesRegex(RuntimeError, 'full frozen base identity'):
            p.verify_spatial_base(self.model, self.config)

    def test_adapter_parameter_rejected(self):
        self.model.register_parameter('lora_A', torch.nn.Parameter(torch.ones(1)))
        with self.assertRaisesRegex(RuntimeError, 'contains an adapter'):
            p.verify_spatial_base(self.model, self.config)

    def run_spatial(self, *, corrupt=False, empty=False, fail=False):
        events, writes = [], []
        def constructor(*args, **kwargs):
            events.append(('construct', args, kwargs))
            return NS(model=self.model, predict_focus=lambda: events.append(('predict',)))
        baseline = NS(Qwen3VL=constructor)
        source = NS(HERE=c.RUN/'next_round_v1',
                    load=lambda path, name: baseline, write=lambda path, value: writes.append((path, value)))
        original_load, original_write = source.load, source.write
        out = Path('CPU_ONLY_OUT')
        def spatial(scope, output):
            if empty:
                source.write(out/'spatial.stage.json', dict(status='PASS_EMPTY_SPACE_NO_MODEL_CALL', rows=0))
                return
            module = source.load(source.HERE/'spatial_baseline.py', 'next_strict_spatial_baseline')
            wrapper = module.Qwen3VL(self.config['model_dir'], device_map={'':'cuda:0'})
            wrapper.predict_focus()
            if fail:
                raise ValueError('CPU_FAILURE_AFTER_IDENTITY')
            source.write(out/'spatial.stage.json', dict(status='PASS_STRICT_SOURCE_FIELD_SPATIAL', rows=1))
        source.spatial = spatial
        if corrupt:
            with torch.no_grad():
                self.model.weight[0, 0] += 1
        try:
            p.spatial_with_base_identity(source, 'nontest', out, self.config)
        finally:
            self.assertIs(source.load, original_load)
            self.assertIs(source.write, original_write)
            self.assertIs(baseline.Qwen3VL, constructor)
            if corrupt:
                self.assertFalse(any(event[0] == 'predict' for event in events))
        return events, writes

    def test_model_load_arguments_generation_and_actual_receipt_preserved(self):
        events, writes = self.run_spatial()
        self.assertEqual(events, [('construct', ('CPU_ONLY_MODEL',), {'device_map': {'':'cuda:0'}}), ('predict',)])
        self.assertEqual(writes[0][1]['base_hash'], self.identity)

    def test_wrong_base_stops_before_prediction_and_restores_helpers(self):
        with self.assertRaisesRegex(RuntimeError, 'full frozen base identity'):
            self.run_spatial(corrupt=True)

    def test_execution_exception_restores_helpers(self):
        with self.assertRaisesRegex(ValueError, 'CPU_FAILURE_AFTER_IDENTITY'):
            self.run_spatial(fail=True)

    def test_empty_phase_does_not_construct_or_invent_base_hash(self):
        events, writes = self.run_spatial(empty=True)
        self.assertEqual(events, [])
        self.assertNotIn('base_hash', writes[0][1])


@unittest.skipUnless(all((c.RUN/'b_score_aligned_package_v4'/scope/'spatial.stage.json').is_file()
                        for scope in ('nontest_01', 'rematch_01')),
                     'actual B2 completion remains on Linux')
class ActualB2Receipts(unittest.TestCase):
    def test_real_two_scopes_and_original_missing_hash_preserved(self):
        prior = c.read(c.RUN/'next_round_v1/config.json')
        baseline = {str(path): c.sha(path) for path in
            (c.RUN/'b_score_aligned_package_v4/completion.json',
             c.RUN/'b_score_aligned_package_v4/nontest_01/spatial.stage.json',
             c.RUN/'b_score_aligned_package_v4/rematch_01/spatial.stage.json')}
        for scope in ('nontest', 'rematch'):
            result = p.b2_cache_evidence(scope, prior['inputs'][scope])
            self.assertEqual(result['status'], 'PASS_FROZEN_B2_SOURCE_FIELD_CACHE')
            self.assertEqual(result['base_hash_measured_in_this_scope'], scope == 'rematch')
            self.assertFalse(result['temporal_reuse_permitted'])
            self.assertEqual(set(result['files']), set(p.CACHE_FILES))
        self.assertNotIn('base_hash', c.read(c.RUN/'b_score_aligned_package_v4/nontest_01/spatial.stage.json'))
        self.assertTrue(all(c.sha(path) == digest for path, digest in baseline.items()))

    def test_real_receipt_faults_rejected_without_editing_history(self):
        b2 = c.RUN/'b_score_aligned_package_v4'
        scope = 'nontest'
        source = c.read(c.RUN/'next_round_v1/config.json')['inputs'][scope]
        original_read = p.read
        independent = b2/'nontest_01/independent_validation.json'
        package = b2/'nontest_01/package.stage.json'
        def drop_check(row): row['checks'].pop('archive_roundtrip_exact')
        faults = [
            (independent, drop_check),
            (independent, lambda row: row['checks'].update(strict_loader_ok=1)),
            (independent, lambda row: row.update(status='STOP')),
            (independent, lambda row: row.update(video_records=7)),
            (independent, lambda row: row.update(strict_loader_issues=['CPU_FAULT'])),
            (independent, lambda row: row.update(expected_frames=0)),
            (package, lambda row: row.update(issues=['CPU_FAULT'])),
            (package, lambda row: row.update(video_records=426)),
            (b2/'completion.json', lambda row: row.update(independent_validation_sha256='0'*64)),
            (b2/'completion.json', lambda row: row.update(nontest_package_receipt_sha256='0'*64)),
            (b2/'completion.json', lambda row: row.update(source_lock_sha256='0'*64)),
            (b2/'rematch_01/spatial.stage.json', lambda row: row['base_hash'].update(sha256='0'*64)),
            (b2/'nontest_01/spatial.stage.json', lambda row: row.update(cache_binding_sha256='0'*64)),
        ]
        for path, mutate in faults:
            with self.subTest(path=path, mutate=mutate):
                def corrupted_read(candidate):
                    value = original_read(candidate)
                    if Path(candidate) == path:
                        value = copy.deepcopy(value)
                        mutate(value)
                    return value
                with patch.object(p, 'read', side_effect=corrupted_read), self.assertRaises(RuntimeError):
                    p.b2_cache_evidence(scope, source)
        for key in ('manifest_sha256', 'registry_sha256'):
            with self.subTest(input_key=key), self.assertRaisesRegex(RuntimeError, 'current scope inputs'):
                p.b2_cache_evidence(scope, dict(source, **{key:'0'*64}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
