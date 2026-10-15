"""Meaningful CPU contracts; synthetic arithmetic is not model/quality acceptance."""
import ast
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path
import random
import unittest
from sg8_math import scalar,interpolate,box_iou,numeric_gate
from sg8_independent_math import rebuild
from sg8_sampling import select


def original_function():
    path=Path(__file__).resolve().parent.parent/'baseline_pts_v3/vendor/p2j_core.py'
    module=ast.parse(path.read_text(encoding='utf-8'))
    fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='interpolate_box')
    env={'bisect_left':bisect_left}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec',flags=__import__('__future__').annotations.compiler_flag),env)
    return env['interpolate_box']


class Contracts(unittest.TestCase):
    def test_independent_nondegenerate_and_nonuniform(self):
        rng=random.Random(20261009)
        for _ in range(2500):
            h0,h2=rng.randint(1,8),rng.randint(1,8)
            q=[0,h0,h0+8,h0+8+h2]; z=[rng.randrange(400) for _ in range(4)]
            for f in range(q[1],q[2]+1):
                exact,integer=rebuild(q,z,f)
                self.assertEqual(scalar(q,z,f),exact)
                self.assertEqual(round(exact),integer)
                self.assertTrue(min(z[1:3])<=exact<=max(z[1:3]))

    def test_counterexample_not_quality(self):
        self.assertEqual(scalar([0,8,16,24],[0,0,8,16],12),F(3))
        self.assertEqual(box_iou([3,0,20],[4,0,20],[16,9]),F(19,21))
        self.assertEqual(box_iou([4,0,20],[4,0,20],[16,9]),F(1))

    def test_original_linear_and_anchor_unchanged(self):
        old=original_function()
        for q in [[0],[0,8],[0,8,16],[0,8,16,19],[0,3,11,19,21]]:
            anchors={f:[f%10,0,20] for f in q}
            for frame in range(q[0],q[-1]+1):
                box,provenance=interpolate(frame,anchors,40,20,[1,1],old)
                if provenance['spatial_source']!='SHOT_PCHIP_XY_ORDINAL_GAP8':
                    self.assertEqual((box,provenance),old(frame,anchors))
                else:
                    self.assertEqual(box[2],20)

    def test_bad_anchors_stop_instead_of_linear(self):
        old=original_function()
        for anchors in [{0:[0,0,20],9:[0,0,20]}, {0:[0,0,19],8:[0,0,20]},
                        {0:[-1,0,20],8:[0,0,20]}, {False:[0,0,20],8:[0,0,20]}]:
            with self.assertRaises(ValueError):interpolate(1,anchors,40,20,[1,1],old)
        for q,f in [([0,8,16,24],25),([0,8,15,23],12),([0,0,8,16],1)]:
            with self.assertRaises(ValueError):scalar(q,[0,0,8,16],f)

    def test_numeric_gate_is_not_total_go(self):
        result=numeric_gate([F(1,10)]*8)
        self.assertEqual(result['status'],'PASS_NUMERIC_ONLY');self.assertFalse(result['total_GO'])
        # Four tiny positives can be outweighed by two negatives.
        self.assertEqual(numeric_gate([F(1)]*2+[F(1,100)]*4+[F(-1)]*2)['status'],'NO_426')
        # A lone outlier cannot hide five groups with negative leave-one sum.
        self.assertEqual(numeric_gate([F(1)]*2+[F(10)]+[F(1,100)]*3+[F(-1)]*2)['status'],'NO_426')
        self.assertEqual(numeric_gate([F(0)]*8)['status'],'NO_426')

    def test_ratio_no_default_or_height_rounding(self):
        self.assertEqual(box_iou([0,0,3],[0,1,3],[2,3]),F(7,11))
        self.assertNotEqual(box_iou([0,0,3],[0,1,3],[2,3]),box_iou([0,0,3],[0,1,3],[9,16]))
        with self.assertRaises(ValueError):box_iou([0,0,3],[0,1,3],[9.0,16])

    def test_sample_order_and_no_coordinate_access(self):
        rows=[dict(source_group='group'+str(i),source_sha256=format(i+1,'064x'),video_id='v'+str(i),shot_id=0,
                   support_ordinals=[0,8,16,24],support_request_sha256=[format(i*4+j+20,'064x') for j in range(4)],scope='nontest') for i in range(8)]
        result=select(rows)
        self.assertEqual(result,select(list(reversed(rows))))
        self.assertEqual(len({r['source_group'] for r in result}),8)
        self.assertEqual([r['role'] for r in result],['engineering']*2+['confirmation']*6)
        self.assertTrue(all(r['probe_ordinals']==list(range(9,16)) for r in result))
        with self.assertRaises(ValueError):select(rows[:7])
        leaked=[dict(r) for r in rows];leaked[0]['box_xyw']=[0,0,20]
        with self.assertRaises(ValueError):select(leaked)
        duplicated=[dict(r) for r in rows];duplicated[-1]['source_group']='group0'
        with self.assertRaises(ValueError):select(duplicated)


if __name__=='__main__':unittest.main()
