"""Adopt proven successful label conversions, first-read heldout only after freeze."""
from common_runtime import *

def loadmat(path):
    import numpy as np
    path=Path(path);out=ROOT/'label_arrays'/(path.stem+'.npy')
    if not out.exists():
        from scipy_bridge import loadmat as first_read
        return first_read(path)
    records=[json.loads(l) for l in (ROOT/'journal.jsonl').read_text().splitlines() if l.strip()]
    accepted=[x for x in records if x.get('stage')=='FIRST_NATIVE_HUMAN_MAT_READ' and x.get('path')==str(out)]
    require(len(accepted)==1 and accepted[0]['sha256']==sha(out),'Successful native label cache identity')
    return {'user_score':np.load(out)}
