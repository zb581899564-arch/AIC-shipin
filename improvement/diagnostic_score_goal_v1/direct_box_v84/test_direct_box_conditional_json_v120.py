import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_conditional_review_json_v120 as review


class JsonTests(unittest.TestCase):
    def test_actual_evaluate_scope_numpy_counts_and_nested_arrays_serialize(self):
        sources=[];targets=[];predictions=[]
        for i in range(20):
            sid='synthetic'+str(i);sha=hashlib.sha256(sid.encode()).hexdigest()
            sources.append(dict(source_id=sid,source_sha256=sha,width=100,height=80,pool=[[10,20,60]],baseline_box=[10,20,60],original_BASE_observed=True))
            targets.append(dict(source_id=sid,source_sha256=sha,width=100,height=80,original_reference_xywh=[20.,20.,40.,22.5],reference_modified=False))
            predictions.append(dict(source_id=sid,source_sha256=sha,native_boxes=dict(DIRECT=[30,20,40],ANCHORED_HALF=[20,20,40])))
        controls={name:dict(source_ids=[s['source_id'] for s in sources],mean_iou=.1) for name in review.review84.CONTROLS}
        result=review.review84.evaluate_scope(sources,targets,predictions,controls)
        self.assertIsInstance(result['arms']['DIRECT']['summary']['improved'],np.integer)
        result['nested_numpy']=dict(values=np.array([[np.int64(3),np.int64(4)]]),flag=np.bool_(True),number=np.float32(.5))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'result.json';review.save(path,result);saved=json.loads(path.read_text())
            self.assertEqual(saved['arms']['DIRECT']['summary']['improved'],20)
            self.assertEqual(saved['nested_numpy'],dict(values=[[3,4]],flag=True,number=.5))
            self.assertEqual(saved['admitted_arm_names'],result['admitted_arm_names'])

    def test_numpy_NaN_and_non_JSON_objects_remain_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for i,value in enumerate((np.float64('nan'),np.array([1.,float('nan')]),np.float32('inf'))):
                with self.subTest(value=i),self.assertRaises(ValueError):review.save(Path(directory)/(str(i)+'.json'),dict(nested=[value]))
            with self.assertRaises(TypeError):review.json_primitives(dict(value=np.complex128(1+2j)))
            with self.assertRaises(TypeError):review.json_primitives(dict(value=np.clongdouble(1+2j)))


if __name__=='__main__':unittest.main()
