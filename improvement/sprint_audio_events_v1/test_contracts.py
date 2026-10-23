"""Targeted temporal-control and missing-observation contracts."""
import json
import unittest
import numpy as np
from event_review import descriptor, block


class AudioControlContracts(unittest.TestCase):
    def test_partial_bin_and_missing_audio_are_explicit(self):
        values = np.full((451, 4), .5, dtype=np.float32)
        observed = np.ones(144000, dtype=bool)
        observed[64000:128000] = False
        rows = descriptor(values, observed, ['a', 'b', 'c', 'd'], 4.5)
        self.assertEqual(rows[-1]['interval'], [4, 4.5])
        self.assertEqual(rows[1]['status'], 'audio_coverage_unknown')
        self.assertNotIn('events', rows[1])
        self.assertEqual([x['name'] for x in rows[0]['events']], ['a', 'b', 'c'])

    def test_shift_preserves_evidence_multiset_and_all_time_slots(self):
        rows = [dict(interval=[i*2, i*2+2], events=[dict(name=str(i), score=.5)]) for i in range(5)]
        right = json.loads(block(rows).splitlines()[-1])['evidence']
        wrong = json.loads(block(rows, wrong=True).splitlines()[-1])['evidence']
        self.assertEqual([r['interval'] for r in right], [r['interval'] for r in wrong])
        self.assertCountEqual([r['events'] for r in right], [r['events'] for r in wrong])
        self.assertTrue(all(a['events'] != b['events'] for a,b in zip(right, wrong)))


if __name__ == '__main__':
    unittest.main()
