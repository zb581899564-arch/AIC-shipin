"""One explicit root; immutable historical assets, new-purpose evidence only."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

W = Path('/home/inspur/aic_video_work')
ROOT = W/'source_clear_residual_20261018_v1'
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = W/'env/qwen3vl_isolated_20260910/bin/python'
OLD = W/'semantic_context_production_20261016_v1'
EXT = W/'semantic_context_residual_20261016_v1'
PRIOR = W/'score_residual_execution_20261016_v2'
CV = W/'twenty_hour_five_20261014_v1/candidate_verify_v2/code'
BASE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'

def require(ok, message):
    if not ok: raise ValueError(message)

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def clean(v):
    if hasattr(v,'item') and callable(v.item): return clean(v.item())
    if isinstance(v,Path): return str(v)
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    return v

def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:
        json.dump(clean(v),f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def event(stage,**kw):
    v=clean(dict(utc=utc(),stage=stage,**kw))
    with (ROOT/'journal.jsonl').open('a') as f:
        f.write(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(v,ensure_ascii=False),flush=True)

def ref(p):
    p=Path(p);return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def bound(r):
    p=Path(r['path']);require(p.is_file() and sha(p)==r['sha256'],'Binding changed: '+str(p));return p

def module(name,path):
    path=Path(path)
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve()==path.resolve(),'Module collision: '+name)
        return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def runtime():
    p=W/'temporal_refinement_pilot_20261011/dev_01'
    sys.path.insert(0,str(p));return module('runtime',p/'runtime.py')

def verify_modules():
    sys.path.insert(0,str(CV))
    return module('cv_contract',CV/'cv_contract.py'),module('cv_tokens',CV/'cv_tokens.py'),module('cv_grammar',CV/'cv_grammar.py')

def cpu():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU child must hide only its own CUDA')

def canonical(rows):
    data=[{k:r[k]for k in ('video_id','targetRatioWH','predictions')}for r in sorted(rows,key=lambda r:r['video_id'])]
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def transform(language,baseline,groups):
    """Exact LM transform used by the winning frozen semantic head."""
    import numpy as np
    v=language.astype(np.float32);center=v.mean(0,dtype=np.float64).astype(np.float32)
    scale=max(1e-6,float(np.sqrt(np.mean((v-center).astype(np.float64)**2))))
    local=np.stack([v[max(0,j-4):min(len(v),j+5)].mean(0) for j in range(len(v))])
    delta=np.abs(v-np.vstack([v[:1],v[:-1]]));ds=max(1e-6,float(np.sqrt(np.mean(delta.astype(np.float64)**2))))
    occ=np.bincount(groups,weights=baseline,minlength=len(v))/np.bincount(groups,minlength=len(v))
    # The historical implementation performs the occupancy reduction in float32.
    occ=occ.astype(np.float32)[:,None]
    return np.concatenate([(v-center)/scale,(local-center)/scale,delta/ds,occ-occ.mean()],1).astype(np.float32)

def semantic(language,baseline,groups):
    import numpy as np
    import torch
    state=torch.load(OLD/'selected_head.pt',map_location='cpu',weights_only=True)
    x=torch.from_numpy(transform(language,baseline,groups))
    with torch.no_grad():
        hidden=torch.nn.functional.gelu(torch.nn.functional.linear(x,state['network.0.weight'],state['network.0.bias']))
        score=torch.nn.functional.linear(hidden,state['network.2.weight'],state['network.2.bias']).squeeze(-1)
    return hidden.numpy(),score.numpy(),baseline | (score.numpy()[groups]>1.)

def failure(stage,error):
    import traceback
    save(ROOT/(stage+'_failure_'+str(os.getpid())+'.json'),dict(utc=utc(),error=repr(error),traceback=traceback.format_exc(),old_successes_preserved=True))
