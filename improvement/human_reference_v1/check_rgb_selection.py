"""Exact seek-frame recovery using synthetic frame objects; no media is decoded."""
import hashlib
from fractions import Fraction as F
from types import SimpleNamespace
import numpy as np
from prepare_rgb_remote import select_rgb


class Frame(SimpleNamespace):
    def to_ndarray(self, format):
        assert format == 'rgb24'
        return np.full((2,3,3), self.pixel, dtype=np.uint8)


def rejects(clock, window, frames):
    try:
        select_rgb(clock, window, frames)
    except ValueError:
        return
    raise AssertionError('Missing or wrong original native64 frame was accepted')


if __name__ == '__main__':
    clock = dict(original_exact_pts=[str(F(100+i,10)) for i in range(80)], width=3, height=2)
    window = dict(source_frame_ordinals=list(range(8,72)))
    frames = [Frame(pts=100+i,time_base=F(1,10),width=3,height=2,pixel=i) for i in range(80)]
    arrays,pixels = select_rgb(clock, window, iter(frames))
    assert arrays.shape == (64,2,3,3)
    assert arrays[:,0,0,0].tolist() == list(range(8,72))
    assert pixels[0] == hashlib.sha256(np.full((2,3,3),8,dtype=np.uint8).tobytes()).hexdigest()
    rejects(clock,window,frames[:25]+frames[26:])
    rejects(clock,window,frames[:40]+[frames[39]]+frames[40:])
    wrong = [Frame(**vars(frame)) for frame in frames]
    wrong[20].width = 4
    rejects(clock,window,wrong)
    print('PASS synthetic seek exact PTS/native64 RGB order and missing/duplicate/geometry failures')
