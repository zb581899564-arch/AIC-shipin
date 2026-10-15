"""Reproduce old-probe directory handoff and incremental cost on CPU."""
import json
from pathlib import Path
import tempfile
import unittest
import autopilot_common as c
from cost_contract import teacher_remaining_cost


class LegacyCostContracts(unittest.TestCase):
    def fixture(self, root):
        old=root/'old';new=root/'new';dirs={}
        for identity in ('heavy_train','heavy_dev'):
            p=old/identity;(p/'http').mkdir(parents=True)
            (p/'done.json').write_text('{}');(p/'http/request.json').write_bytes(b'x'*100)
            dirs[identity]=p
        for i in range(24):
            p=new/'windows'/str(i);p.mkdir(parents=True);(p/'done.json').write_text('{}')
        return new,dirs

    def test_original_new_directory_assumption_reproduces_stop(self):
        with tempfile.TemporaryDirectory() as temporary:
            root,dirs=self.fixture(Path(temporary))
            with self.assertRaisesRegex(ValueError,'complete measured probe'):
                teacher_remaining_cost(root,list(dirs),160,accepted_ids=list(dirs))

    def test_exact_original_directories_reuse_2_and_24_existing_labels(self):
        with tempfile.TemporaryDirectory() as temporary:
            root,dirs=self.fixture(Path(temporary))
            result=teacher_remaining_cost(root,list(dirs),160,accepted_ids=list(dirs),measured_directories=dirs)
            self.assertEqual(result['existing_label_windows'],26)
            self.assertEqual(result['remaining_label_windows'],134)
            self.assertFalse(result['already_stored_bytes_charged_again'])
            self.assertFalse((root/'windows/heavy_train').exists())

    def test_existing_blind_reviews_are_not_new_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root,dirs=self.fixture(Path(temporary))
            before=teacher_remaining_cost(root,list(dirs),160,accepted_ids=list(dirs),measured_directories=dirs)
            for i in range(24):
                p=root/'reviews'/str(i);p.mkdir(parents=True);(p/'done.json').write_text('{}')
            after=teacher_remaining_cost(root,list(dirs),160,accepted_ids=list(dirs),measured_directories=dirs)
            self.assertEqual(after['remaining_review_windows'],136)
            self.assertEqual(before['planned_output_bytes']-after['planned_output_bytes'],24*100*2)

    def test_missing_probe_binding_or_review_without_label_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root,dirs=self.fixture(Path(temporary))
            with self.assertRaisesRegex(ValueError,'exact measured probe'):
                teacher_remaining_cost(root,list(dirs),160,measured_directories={})
            p=root/'reviews/unknown';p.mkdir(parents=True);(p/'done.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'lacks an existing'):
                teacher_remaining_cost(root,list(dirs),160,accepted_ids=list(dirs),measured_directories=dirs)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LegacyCostContracts))
    report=dict(status='PASS_EXPLICIT_ORIGINAL_PROBE_COST_CPU' if result.wasSuccessful() else 'STOP_ORIGINAL_PROBE_COST_CPU',
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),GPU_started=False,
        old_bytes_changed=False,production_cost_sha256=c.sha(c.HERE/'cost_contract.py'),
        production_controller_sha256=c.sha(c.HERE/'controller.py'))
    c.write(c.HERE/'legacy_cost_cpu_acceptance.json',report,fresh=True)
    print(json.dumps(report))
    raise SystemExit(0 if result.wasSuccessful() else 1)
