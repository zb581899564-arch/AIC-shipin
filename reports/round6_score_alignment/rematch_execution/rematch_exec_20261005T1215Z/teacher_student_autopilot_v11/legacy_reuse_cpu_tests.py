"""Actual exact V10 legacy admission/rejection; immutable old files, no GPU."""
import copy
import json
import socket
import unittest
from unittest.mock import patch
import v10_cache_reuse as reuse


class ExactLegacyReuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert socket.gethostname() == 'inspur-NP5570M5', 'actual legacy CPU acceptance is Linux-only'
        cls.manifest = reuse._load_manifest()
        reuse._ensure_authority(cls.manifest)
        cls.original = {identity:reuse.read(reuse.original_directory(identity)/'validated_record.json') for identity in reuse.PINS}
        cls.before = {identity:reuse.directory_snapshot(reuse.original_directory(identity)) for identity in reuse.PINS}

    def test_original_two_records_annotation_projection_and_all_directory_sha(self):
        for identity, record in self.original.items():
            with self.subTest(identity=identity):
                self.assertTrue(reuse.verify_approved_record(record))
                annotation = reuse.verify_approved_annotation(record['window'])
                self.assertEqual(annotation, reuse.read(reuse.original_directory(identity)/'annotation.json'))
                self.assertEqual(reuse.approved_canonical_projection(record), record['parsed_answer'])
                self.assertEqual(reuse.directory_snapshot(reuse.original_directory(identity)), self.before[identity])

    def test_successes_are_full160_members_and_not_pilot24(self):
        full = {row['window_id']:row for split in ('train','dev') for row in reuse.rows(reuse.HERE/'selection_01'/('selected_'+split+'.jsonl'))}
        pilot = {row['window_id'] for split in ('train','dev') for row in reuse.rows(reuse.HERE/'pilot_selection'/('selected_'+split+'.jsonl'))}
        for identity, record in self.original.items():
            self.assertEqual(record['window'], full[identity])
            self.assertNotIn(identity, pilot)

    def test_record_mutation_never_gains_old_format_approval(self):
        original = next(iter(self.original.values()))
        for key in ('model_raw_answer', 'raw_answer', 'canonical_answer'):
            altered = copy.deepcopy(original); altered[key] += ' '
            self.assertFalse(reuse.verify_approved_record(altered))
        altered = copy.deepcopy(original); altered['teacher']['job_source_lock_sha256'] = '0'*64
        self.assertFalse(reuse.verify_approved_record(altered))
        altered = copy.deepcopy(original); altered['actual_observation']['actual_pts_sec'][0] += 0.1
        self.assertFalse(reuse.verify_approved_record(altered))

    def test_four_original_inputs_required_and_original_record_returned(self):
        record = next(iter(self.original.values()))
        annotation = reuse.verify_approved_annotation(record['window'])
        args = [record['window'], annotation['observation'], annotation['teacher'], annotation['raw_answer']]
        self.assertEqual(reuse.approved_original_record(*args), record)
        for index in range(4):
            altered = copy.deepcopy(args)
            if index == 3: altered[index] += ' '
            else: altered[index]['CPU_TAMPER'] = True
            self.assertIsNone(reuse.approved_original_record(*altered))

    def test_approved_window_change_rejects_without_regeneration(self):
        window = copy.deepcopy(next(iter(self.original.values()))['window'])
        window['source_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'approved legacy window changed'):
            reuse.verify_approved_annotation(window)

    def test_unknown_failed_and_marker_only_are_not_legacy_authority(self):
        self.assertFalse(reuse.verify_approved_record({'window_id':next(iter(reuse.PINS)), 'legacy_approved':True}))
        for identity in ('CPU_UNKNOWN', reuse.FAILED_ID):
            window = {'window_id':identity, 'legacy_approved':True}
            self.assertIsNone(reuse.verify_approved_annotation(window))
            self.assertFalse(reuse.verify_approved_record({'window_id':identity, 'legacy_approved':True}))
            self.assertIsNone(reuse.approved_original_record(window, {}, {}, '{}'))
        failed = reuse.OLD/'teacher_01/windows'/reuse.FAILED_ID
        self.assertFalse((failed/'done.json').exists())
        self.assertTrue((failed/'failure.json').is_file())
        self.assertTrue((failed/'raw_answer.txt').is_file())

    def test_manifest_or_original_directory_sha_change_rejected(self):
        forged = copy.deepcopy(self.manifest)
        forged['accepted'][0]['teacher_record_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'manifest differs'):
            reuse._ensure_authority(forged)
        identity = next(iter(reuse.PINS))
        changed = dict(self.before[identity]); changed[next(iter(changed))] = '0'*64
        with patch.object(reuse, 'directory_snapshot', return_value=changed), self.assertRaisesRegex(ValueError, 'directory bytes changed'):
            reuse.verify_approved_annotation(self.original[identity]['window'])

    def test_original_probe_cost_and_visual_receipts_remain_real_and_separate(self):
        probe, resource, visual_resource = reuse.original_probe_evidence()
        self.assertEqual(set(probe['window_ids']), set(reuse.PINS))
        self.assertEqual(resource['status'], 'completed')
        self.assertEqual(visual_resource['status'], 'completed')
        self.assertTrue(all(reuse.directory_snapshot(reuse.original_directory(identity)) == original
                            for identity,original in self.before.items()))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExactLegacyReuse))
    passed = result.wasSuccessful() and result.testsRun == 8
    report = {'status':'PASS_EXACT_V10_SUCCESS_REUSE_CPU' if passed else 'STOP_EXACT_V10_SUCCESS_REUSE_CPU',
        'tests_run':result.testsRun, 'failures':len(result.failures), 'errors':len(result.errors),
        'GPU_started':False, 'old_bytes_changed':False, 'accepted_count':2,
        'manifest_sha256':reuse.sha(reuse.MANIFEST), 'production_reuse_sha256':reuse.sha(reuse.HERE/'v10_cache_reuse.py'),
        'legacy_tests_sha256':reuse.sha(reuse.HERE/'legacy_reuse_cpu_tests.py'),
        'isolated_original_validator':True, 'successful_probes_not_pilot24':True,
        'old_source_lock_sha256':reuse.sha(reuse.OLD/'source_lock.json')}
    output = reuse.HERE/'legacy_reuse_cpu_acceptance.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if passed else 1)
