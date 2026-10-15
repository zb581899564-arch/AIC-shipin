import io
import unittest
from unittest.mock import patch
import zipfile
import numpy as np
from temporal_reference_diagnostic import matching_tsv_rows, verify_publisher, assert_bound, EXPECTED_BINDINGS


class TemporalTests(unittest.TestCase):
    def test_other_source_invalid_text_not_decoded(self):
        archive=io.BytesIO()
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr('data/ydata-tvsum50-anno.tsv',
                       b'other_source\tDS\t\xff\xff\n'
                       b'kLxoNp-UchI\tDS\t1,2,3\n'
                       b'locked_source\tDS\tINVALID_SCORES\n')
        archive.seek(0)
        self.assertEqual(matching_tsv_rows(archive),[['kLxoNp-UchI','DS','1,2,3']])

    def test_publisher_mean_frame_or_values_differ_rejected(self):
        vectors=[[1,2,3],[3,4,5]]
        self.assertEqual(verify_publisher(vectors,np.array(vectors),3,3,np.array([2,3,4])),(True,True))
        for array,frames,mean in [(np.array(vectors),3,np.array([0,3,4])),
                                  (np.array(vectors),2,np.array([2,3,4])),
                                  (np.array([[2,2,3],[3,4,5]]),3,np.array([2.5,3,4]))]:
            with self.assertRaises(ValueError):
                verify_publisher(vectors,array,frames,3,mean)

    def test_self_declared_identity_cannot_replace_frozen_identity(self):
        with patch('temporal_reference_diagnostic.sha',return_value='0'*64):
            with self.assertRaises(ValueError):
                assert_bound('same_declared_source','source')
        with patch('temporal_reference_diagnostic.sha',return_value=EXPECTED_BINDINGS['source']):
            assert_bound('original_bound_source','source')


if __name__=='__main__':
    unittest.main()
