import copy
from fractions import Fraction
import json
import unittest

import numpy as np
from PIL import Image
import torch

from crop_observation_v34 import (forward_pack_observation_rgb, recover_observation_rgb,
    independent_recovery_check, render_observation_crop, independent_observation_crop_check)


class ObservationTests(unittest.TestCase):
    def test_coordinate_channel_ramp_full_spatial_and_color_identity(self):
        y,x=np.indices((64,96));rgb=np.stack(((3*x+7*y)%256,y%256,x%256),axis=-1).astype(np.uint8)
        pixels,grid=forward_pack_observation_rgb(rgb)
        # Independent explicit merged-row/channel/temporal indexing, including boundaries.
        for yy,xx in ((0,0),(15,15),(16,31),(31,32),(32,63),(63,95)):
            py,px=yy//16,xx//16
            row=((py//2)*(96//32)+px//2)*4+(py%2)*2+px%2
            for channel in range(3):
                for temporal in range(2):
                    column=((channel*2+temporal)*16+yy%16)*16+xx%16
                    expected=(torch.tensor(float(rgb[yy,xx,channel]),dtype=torch.float32)-127.5)/127.5
                    self.assertEqual(pixels[row,column].view(torch.int32).item(),expected.view(torch.int32).item())
        recovered,meta=recover_observation_rgb(pixels,grid)
        np.testing.assert_array_equal(recovered,rgb)
        check=independent_recovery_check(pixels,grid,recovered,meta)
        self.assertTrue(check['all_input_pixel_bits_equal']);self.assertFalse(meta['native_RGB_recovered'])
        json.dumps(meta,allow_nan=False)

    def test_random_two_shapes_and_all_uint8_colors_have_loss_zero(self):
        rng=np.random.default_rng(20261018)
        for shape in ((32,64,3),(96,128,3)):
            rgb=rng.integers(0,256,size=shape,dtype=np.uint8)
            pixels,grid=forward_pack_observation_rgb(rgb);restored,meta=recover_observation_rgb(pixels,grid)
            np.testing.assert_array_equal(restored,rgb);independent_recovery_check(pixels,grid,restored,meta)
        rgb=np.repeat(np.tile(np.arange(256,dtype=np.uint8),(4,1)).reshape(32,32,1),3,axis=2)
        pixels,grid=forward_pack_observation_rgb(rgb);restored,_=recover_observation_rgb(pixels,grid)
        np.testing.assert_array_equal(restored,rgb)

    def test_temporal_nonidentical_one_ulp_and_no_clipping_rejected(self):
        pixels,grid=forward_pack_observation_rgb(np.full((32,32,3),128,np.uint8))
        bad=pixels.clone();bad[0,0]=torch.nextafter(bad[0,0],torch.tensor(float('inf')))
        with self.assertRaises(ValueError):recover_observation_rgb(bad,grid)
        # Change BOTH copies identically: temporal check passes, exact forward bytes still fail.
        bad=pixels.reshape(4,3,2,16,16).clone()
        bad[0,0,:,0,0]=torch.nextafter(bad[0,0,:,0,0],torch.full((2,),float('inf')))
        with self.assertRaises(ValueError):recover_observation_rgb(bad.reshape(4,1536),grid)
        bad=torch.full_like(pixels,1.01)
        with self.assertRaises(ValueError):recover_observation_rgb(bad,grid)
        with self.assertRaises(ValueError):recover_observation_rgb(pixels*float('nan'),grid)

    def test_bad_grid_dtype_dimension_and_profile_claim_rejected(self):
        pixels,grid=forward_pack_observation_rgb(np.zeros((32,32,3),np.uint8))
        for g in ([[2,2,2]],[[1,3,2]],[[1.,2,2]],[[1,2,2],[1,2,2]]):
            with self.assertRaises(ValueError):recover_observation_rgb(pixels,g)
        with self.assertRaises(ValueError):recover_observation_rgb(pixels.half(),grid)
        with self.assertRaises(ValueError):recover_observation_rgb(pixels[:-1],grid)
        rgb,meta=recover_observation_rgb(pixels,grid);wrong=dict(meta,native_RGB_recovered=True)
        with self.assertRaises(ValueError):independent_recovery_check(pixels,grid,rgb,wrong)

    def test_wrong_spatial_or_channel_source_order_rejected_independently(self):
        rng=np.random.default_rng(7);rgb=rng.integers(0,256,(32,64,3),dtype=np.uint8)
        pixels,grid=forward_pack_observation_rgb(rgb);recovered,meta=recover_observation_rgb(pixels,grid)
        for wrong in (recovered[:,:,::-1].copy(),recovered[:,::-1].copy()):
            with self.assertRaises(ValueError):independent_recovery_check(pixels,grid,wrong,meta)


class RenderTests(unittest.TestCase):
    def test_fractional_native_extent_scaled_in_both_axes(self):
        y,x=np.indices((64,96));rgb=np.stack((x,y,(x+y)%256),axis=-1).astype(np.uint8)
        box=[17,11,101];native=[503,307]
        rendered,proof=render_observation_crop(rgb,box,native)
        exact=[Fraction(17*96,503),Fraction(11*64,307),Fraction(118*96,503),Fraction((16*11+9*101)*64,16*307)]
        self.assertEqual(proof['extent_observation_xyxy_exact'],list(map(str,exact)))
        expected=np.array(Image.fromarray(rgb).transform((320,180),Image.Transform.EXTENT,tuple(map(float,exact)),resample=Image.Resampling.BICUBIC))
        np.testing.assert_array_equal(rendered,expected)
        independent_observation_crop_check(rgb,box,native,rendered,proof)
        self.assertEqual(proof['profile'],'RESIZED_OBSERVATION_PLANE');self.assertFalse(proof['native_RGB_recovered'])
        json.dumps(proof,allow_nan=False)

    def test_native_illegal_box_and_wrong_extent_source_render_rejected(self):
        rgb=np.zeros((32,64,3),np.uint8)
        for box,dims in (([0,0,501],[500,300]),([0,299,10],[500,300]),([0.,0,100],[500,300]),([0,0,100],[0,300])):
            with self.assertRaises(ValueError):render_observation_crop(rgb,box,dims)
        rendered,proof=render_observation_crop(rgb,[0,0,100],[500,300]);wrong=copy.deepcopy(proof)
        wrong['extent_observation_xyxy_exact'][2]='999'
        with self.assertRaises(ValueError):independent_observation_crop_check(rgb,[0,0,100],[500,300],rendered,wrong)
        bad=rendered.copy();bad[0,0,0]=1
        with self.assertRaises(ValueError):independent_observation_crop_check(rgb,[0,0,100],[500,300],bad,proof)


if __name__=='__main__':unittest.main()
