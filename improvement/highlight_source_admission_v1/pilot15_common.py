"""Explicit paths and content identities for one new-supervision pilot."""
import hashlib
import json
from pathlib import Path
import sys

from direct import ROOT as ADMISSION, save, ref

WORK=Path('/home/inspur/aic_video_work')
ENGINEERING=WORK/'i3d_umt_cross_domain_20261021_v1'
ROOT=ADMISSION/'matched_hl_pilot15'
sys.path.insert(0,str(ENGINEERING))


def read(path):
    return json.loads(Path(path).read_text())


def checked(record):
    path=Path(record['path'])
    if ref(path)!=record:
        raise ValueError('Content-bound dependency changed: '+str(path))
    return path


def native_cells(count):
    import numpy as np
    bounds=[(first,min(first+64,count)) for first in range(0,count,64)]
    indices=np.asarray([[min(first+8*k,stop-1) for k in range(8)] for first,stop in bounds])
    groups=np.repeat(np.arange(len(bounds)),[b-a for a,b in bounds])
    return bounds,indices,groups


def original_targets(source):
    import numpy as np
    value=read(checked(source['labels']))
    labels=np.full(source['native_frames'],-1,dtype=np.int8)
    for row in value['intervals']:
        labels[row['first']:row['last']+1]=row['label']
    if not set(np.unique(labels)) <= {-1,0,1}:
        raise ValueError('Unexpected original HL/NHL/UN value')
    return labels
