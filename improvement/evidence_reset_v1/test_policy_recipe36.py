import json
import unittest
import numpy as np
from policy_recipe36_math import materialize,rate,state_digest


class Checks(unittest.TestCase):
    def test_hex_recipe_exact_reconstruction_and_original_untouched(self):
        original={'x.weight':np.asarray([1.,-2.],dtype=np.float32)}
        before=state_digest(original)
        direction={'x.policy.weight':np.asarray([.25,.5],dtype=np.float32)}
        alpha=rate(.8,.2)
        recipe=json.loads(json.dumps(dict(alpha_hex=alpha.hex())))
        candidate,stats=materialize(original,direction,recipe['alpha_hex'])
        np.testing.assert_array_equal(candidate['x.weight'],np.array([2.,0.],np.float32))
        rebuilt,stats2=materialize(original,direction,recipe['alpha_hex'])
        self.assertEqual(state_digest(candidate),state_digest(rebuilt))
        self.assertEqual(stats,stats2)
        self.assertEqual(before,state_digest(original))

    def test_no_nonpositive_or_nonfinite_plane_dose(self):
        for a,b in [(0.,1.),(1.,0.),(1.,-1.),(float('nan'),1.)]:
            with self.assertRaises(ValueError):rate(a,b)


if __name__=='__main__':unittest.main()
