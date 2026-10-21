import unittest
from center_ablation46 import center_box,independent_center,metadata_index,canonical,semantic_digest
import copy
class CenterTests(unittest.TestCase):
    def test_exact_integer_centers_keep_widths_and_fractional_height_legal(self):
        for width,height,ratio,cw in [(1600,900,[9,16],506),(1920,1080,[16,9],1920),(720,1280,[16,9],720),(169,300,[9,16],168),(1001,1000,[16,9],800)]:
            a=center_box([0,0,cw],width,height,ratio)
            self.assertEqual(a,independent_center(width,height,cw,*ratio))
            self.assertEqual(a[2],cw)
            self.assertGreaterEqual(a[0],0);self.assertGreaterEqual(a[1],0)
            self.assertLessEqual(a[0]+cw,width)
            self.assertLessEqual(a[1]*ratio[0]+cw*ratio[1],height*ratio[0])
        self.assertEqual(center_box([0,0,720],720,1280,[16,9]),[0,438,720])
        self.assertEqual(center_box([0,0,60],192,108,[9,16]),[66,1,60])
    def test_metadata_representation_does_not_change_the_target_ratio(self):
        index=metadata_index({'records':[{'video_id':'0','targetRatioWH':'9 16'},{'video_id':'1','targetRatioWH':[16,9]}]})
        self.assertEqual(index['0']['targetRatioWH'],[9,16]);self.assertEqual(index['1']['targetRatioWH'],[16,9])
    def test_actual_prediction_semantics_ignore_order_equivalent_numbers_and_extra_keys(self):
        rows=[dict(video_id=str(i),targetRatioWH=[9,16],predictions=[])for i in range(426)]
        rows[0]['predictions']=[dict(frame=1,bboxes=[18,0,60]),dict(frame=2,bboxes=[20,1,60])]
        alternate=copy.deepcopy(rows)
        alternate[0]['predictions']=[dict(frame=2,bboxes=[20.,1.,60.],ignored='x'),dict(frame=1,bboxes=[18.,-0.,60.])]
        alternate.reverse()
        self.assertNotEqual(canonical(rows),canonical(alternate))
        self.assertEqual(semantic_digest(rows),semantic_digest(alternate))
        alternate[-1]['predictions'].append(dict(frame=1,bboxes=[18,0,60]))
        with self.assertRaises(AssertionError):semantic_digest(alternate)
if __name__=='__main__':unittest.main()
