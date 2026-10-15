"""Synthetic decode objects only; does not open media or launch the Linux entry."""
import copy
from fractions import Fraction as F
from types import SimpleNamespace
from map_sources_remote import clock_from_frames


def reject(source, media, frames):
    try:
        clock_from_frames(source, media, frames)
    except ValueError:
        return
    raise AssertionError('Invalid native decode sequence was accepted')


if __name__ == '__main__':
    source = dict(source_name='hand_decode', annotation_frames=3, annotation_fps=30,
                  annotation_duration=1, member=dict(bytes=12, crc32='12345678'))
    media = dict(bytes=12, crc32='12345678', sha256='a'*64)
    frames = [SimpleNamespace(pts=point, time_base=F(1,50), duration=duration, width=100, height=60)
              for point,duration in [(100,5), (105,35), (140,10)]]
    clock, proof = clock_from_frames(source, media, iter(frames))
    assert clock['first_original_pts_exact'] == '2'
    assert clock['normalized_exact_pts'] == ['0','1/10','4/5']
    assert clock['original_exact_pts'] == ['2','21/10','14/5']
    assert clock['physical_end_exact'] == '1' and proof['human_frames'] == 3
    assert clock['physical_endpoint_evidence']['last_frame_duration_exact'] == '1/5'
    for key,value,index in [('duration',0,2),('pts',105,2),('pts',None,0),('width',101,1)]:
        changed = copy.deepcopy(frames)
        setattr(changed[index],key,value)
        reject(source,media,changed)
    reject(source,media,frames[:-1])
    print('PASS synthetic native clock offset, exact last duration and missing-duration/PTS/count/geometry rejection')
