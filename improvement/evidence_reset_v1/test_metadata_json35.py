import json
import unittest
import numpy as np
from metadata_json35 import native


class Check(unittest.TestCase):
    def test_numpy_boolean_and_integer_nested_values(self):
        original=dict(condition=np.bool_(True),count=np.int64(2),metrics=(np.float64(.01),False))
        with self.assertRaises(TypeError):json.dumps(original,allow_nan=False)
        value=native(original)
        self.assertEqual(json.loads(json.dumps(value,allow_nan=False)),dict(condition=True,count=2,metrics=[.01,False]))
        self.assertIs(type(value['condition']),bool)
        self.assertIs(type(value['count']),int)


if __name__=='__main__':unittest.main()
