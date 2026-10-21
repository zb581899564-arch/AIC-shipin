import unittest
from signature_projection45 import runtime_projection
class SignatureTests(unittest.TestCase):
    def test_nested_codec_and_flat_runtime_are_compared_by_explicit_contract(self):
        names=['pixel_values','image_grid_thw','input_ids','attention_mask']
        rows={name:dict(shape=[1,2],dtype='torch.int64',sha256='a'*64,stride=[2,1],storage_offset=0,
                       layout='torch.strided',requires_grad=False,bytes=16)for name in names}
        codec=dict(tensors=rows,alias_groups=[])
        expected={name:dict(shape=[1,2],dtype='torch.int64',sha256='a'*64)for name in names}
        self.assertNotEqual(codec,expected)
        self.assertEqual(runtime_projection(codec),expected)
        codec['tensors']['input_ids']['sha256']='b'*64
        self.assertNotEqual(runtime_projection(codec),expected)
        codec['alias_groups']=[['input_ids','attention_mask']]
        with self.assertRaises(AssertionError):runtime_projection(codec)
if __name__=='__main__':unittest.main()
