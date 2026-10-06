"""Regression checks for spatial recovery lineage and frozen temporal decisions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from recovery_contract import RECOVERY_KIND, frozen_temporal, sha, validate_recovery


class RecoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for directory in ('runs/improvement_test174_multi_v2', 'runs/temporal', 'inference',
                          'inference_v2', 'inference_recovery', 'improvement_round1'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self.temporal = self.root / 'runs/temporal'
        self.original = self.root / 'runs/improvement_test174_multi_v2'
        (self.root / 'inference/test_index.json').write_text('[]')
        (self.root / 'inference_v2/baseline_v2.py').write_text('# frozen\n')
        (self.root / 'inference_recovery/reader.py').write_text('# sequential\n')
        self.rows = [dict(video_id=str(i), source_group=str(i), status='ok',
                          segments_sec=[[0.0, 1.0]], segments_frames=[[0, 25]],
                          query=None, policy='multi', adapter=None, constrained_json=True,
                          constraint_backend='regex', sampling=[],
                          metadata=dict(n_frames=50, fps=25.0, width=1280, height=720)) for i in range(174)]
        self.jsonl(self.original / 'status.jsonl', self.rows[:2])
        self.jsonl(self.temporal / 'temporal.jsonl', self.rows)
        self.temporal_launch = dict(original_run=str(self.original),
            original_artifact_hashes={'status.jsonl': sha(self.original / 'status.jsonl')},
            index_sha256=sha(self.root / 'inference/test_index.json'),
            source_hashes={'inference_v2/baseline_v2.py': sha(self.root / 'inference_v2/baseline_v2.py')},
            holdout_plan_sha256='fixed_plan', holdout_summary_sha256='fixed_result')
        self.dump(self.temporal / 'launch.json', self.temporal_launch)
        self.report = dict(status='passed', changed_fields=[], videos=174, compared_original_complete_rows=2,
                           temporal_sha256=sha(self.temporal / 'temporal.jsonl'), launch_sha256=sha(self.temporal / 'launch.json'))
        self.dump(self.temporal / 'freeze_report.json', self.report)
        self.launch = dict(policy='multi', command=['python', '-m', 'inference_recovery.spatial_replay'],
            holdout_plan_sha256='fixed_plan', holdout_summary_sha256='fixed_result',
            index_sha256=self.temporal_launch['index_sha256'],
            engineering_recovery=dict(kind=RECOVERY_KIND, no_new_holdout_or_tuning=True, all_test_videos_replayed=True,
                temporal_run=str(self.temporal), temporal_sha256=self.report['temporal_sha256'], job_name='spatial',
                recovery_source_hashes={'inference_recovery/reader.py': sha(self.root / 'inference_recovery/reader.py')}))
        self.resource = dict(status='completed', exit_code=0, command=self.launch['command'])
        self.dump(self.root / 'improvement_round1/spatial.resource.json', self.resource)

    @staticmethod
    def dump(path, value):
        path.write_text(json.dumps(value))

    @staticmethod
    def jsonl(path, rows):
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows))

    def test_valid_frozen_replay(self):
        result = validate_recovery(self.launch, self.rows, self.root)
        self.assertTrue(result['all_174_frozen_temporal_decisions_preserved'])

    def test_spatial_stage_cannot_change_time_frames(self):
        changed = copy.deepcopy(self.rows)
        changed[-1]['segments_frames'] = [[1, 25]]
        with self.assertRaisesRegex(ValueError, 'changed frozen temporal'):
            validate_recovery(self.launch, changed, self.root)

    def test_original_partial_evidence_must_remain(self):
        (self.original / 'status.jsonl').write_text('')
        with self.assertRaisesRegex(ValueError, 'original failed evidence changed'):
            validate_recovery(self.launch, self.rows, self.root)

    def test_self_consistent_report_cannot_hide_changed_old_decision(self):
        changed = copy.deepcopy(self.rows)
        changed[0]['segments_frames'] = [[1, 25]]
        self.jsonl(self.temporal / 'temporal.jsonl', changed)
        self.report['temporal_sha256'] = sha(self.temporal / 'temporal.jsonl')
        self.dump(self.temporal / 'freeze_report.json', self.report)
        with self.assertRaisesRegex(ValueError, 'original temporal decision'):
            frozen_temporal(self.temporal, self.root)

    def test_query_cannot_be_added(self):
        changed = copy.deepcopy(self.rows)
        changed[3]['query'] = 'manual hint'
        with self.assertRaisesRegex(ValueError, 'changed frozen temporal'):
            validate_recovery(self.launch, changed, self.root)

    def test_resource_must_match_exact_command(self):
        self.resource['command'] = ['other command']
        self.dump(self.root / 'improvement_round1/spatial.resource.json', self.resource)
        with self.assertRaisesRegex(ValueError, 'exact launch'):
            validate_recovery(self.launch, self.rows, self.root)

    def test_missing_video_rejected(self):
        with self.assertRaisesRegex(ValueError, 'coverage'):
            validate_recovery(self.launch, self.rows[:-1], self.root)

    def test_reader_source_drift_rejected(self):
        (self.root / 'inference_recovery/reader.py').write_text('# changed\n')
        with self.assertRaisesRegex(ValueError, 'recovery source changed'):
            validate_recovery(self.launch, self.rows, self.root)


if __name__ == '__main__':
    unittest.main()
