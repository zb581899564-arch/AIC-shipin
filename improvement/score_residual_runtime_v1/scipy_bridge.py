"""Existing Linux SciPy process reads MAT, isolated torch process remains fixed."""
import subprocess
from common_runtime import *

def loadmat(path):
    import numpy as np
    path=Path(path)
    require(path.resolve().parent==ROOT/'GT','Only registered external MAT inputs')
    out=ROOT/'label_arrays'/(path.stem+'.npy');out.parent.mkdir(exist_ok=True)
    require(not out.exists(),'Do not repeat successful label conversion')
    script='from scipy.io import loadmat; import numpy as np,sys; np.save(sys.argv[2],loadmat(sys.argv[1])["user_score"])'
    subprocess.run(['/home/inspur/anaconda3/bin/python','-c',script,str(path),str(out)],check=True)
    event('FIRST_NATIVE_HUMAN_MAT_READ',source=path.stem,reader='existing scipy1.12.0',path=str(out),sha256=sha(out))
    return {'user_score':np.load(out)}
