import copy
import unittest
import numpy as np

from crop_full_readout_run_v52 import training_rows, scope_design


class Geometry:
    @staticmethod
    def geometry_features(box, width, height):
        return np.array([1., box[0]/width, box[1]/height, box[2]/width]+[0.]*8+[width/height])


class ReadoutOwnerAndTargets(unittest.TestCase):
    def training(self):
        sources, pairs, lookup, targets = [], [], {}, {}
        forward, reverse = np.ones(4096), np.zeros(4096)
        for i in range(602):
            sid, sha = 's'+str(i), format(i, '064x')
            sources.append(dict(source_id=sid, source_sha256=sha, role='train',
                width=32, height=18, pool=[[0, 0, 16], [1, 0, 16], [2, 0, 16]]))
            targets[sid] = [.2, .3, .1]
            for b in (1, 2):
                f, r = sid+'f'+str(b), sid+'r'+str(b)
                pairs.append(dict(source_id=sid, source_sha256=sha, a=0, b=b, first_id=f, reverse_id=r))
                for key, values in ((f, forward), (r, reverse)):
                    lookup[key] = dict(source_id=sid, source_sha256=sha,
                        readout4096=values, class_logits3=np.zeros(3))
        return sources, pairs, lookup, targets

    def test_original_iou_difference_sign_and_unordered_scope(self):
        sources, pairs, lookup, targets = self.training()
        rows = training_rows(sources, pairs, lookup, targets, Geometry)
        self.assertEqual(len(rows), 602)
        for row in rows:
            self.assertEqual([p['pair'] for p in row['pairs']], [[0, 1], [0, 2]])
            self.assertEqual([p['target'] for p in row['pairs']], [.3-.2, .1-.2])
            self.assertTrue(np.array_equal(row['pairs'][0]['x4096'], np.ones(4096)))

    def test_other_source_raw_cannot_enter_pair(self):
        sources, pairs, lookup, targets = self.training()
        lookup['s0f1'] = dict(lookup['s0f1'], source_sha256='f'*64)
        with self.assertRaises(ValueError):
            training_rows(sources, pairs, lookup, targets, Geometry)

    def test_complete_twenty_source_self_and_alternative_mapping(self):
        sources, pairs, lookup = [], [], {}
        for i in range(20):
            sid, sha = 'v'+str(i), format(i, '064x')
            sources.append(dict(source_id=sid, source_sha256=sha, role='screen', width=32,
                height=18, pool=[[0, 0, 16], [1, 0, 16]]))
            f, r, own = sid+'f', sid+'r', sid+'self'
            pairs.extend([dict(source_id=sid, candidate_index=1, first_id=f, reverse_id=r, same_crop=False),
                dict(source_id=sid, candidate_index=0, first_id=own, reverse_id=own, same_crop=True)])
            for key, value in ((f, 2.), (r, 1.), (own, 3.)):
                lookup[key] = dict(source_id=sid, source_sha256=sha, readout4096=np.full(4096, value))
        result = scope_design(sources, pairs, lookup, Geometry)
        self.assertEqual(len(result), 20)
        self.assertTrue(all(np.array_equal(item['X'][0], np.zeros(4096))
                            and np.array_equal(item['X'][1], np.ones(4096)) for item in result))
        broken = copy.deepcopy(pairs)
        broken[1]['reverse_id'] = broken[0]['first_id']
        with self.assertRaises(ValueError):
            scope_design(sources, broken, lookup, Geometry)


if __name__ == '__main__':
    unittest.main()
