"""New five-way inference; original cache/weights/results are immutable inputs."""
import datetime as dt
import gzip
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

HOME=Path('/home/inspur/aic_video_work')
ROOT=HOME/'midnight_five_verify40_46_20261015_v1'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY=HOME/'env/qwen3vl_isolated_20260910/bin/python'
PARAMETERS=8782459120
DEADLINE=dt.datetime.fromisoformat('2026-10-15T16:00:00+00:00')
FIELDS=('ordinary','redundant','action','reaction','information')

def require(x,message):
    if not x: raise ValueError(message)

def utc():return dt.datetime.now(dt.timezone.utc).isoformat()

def read(path):return json.loads(Path(path).read_text(encoding='utf8'))

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def ref(path):return dict(path=str(Path(path).resolve()),sha256=sha(path))

def checked(r):
    # Check the actual file location before hashing it. Lexical containment
    # accepts ../ paths and symlinks into another run outside the frozen root.
    p=Path(r['path']).resolve()
    require(p.is_relative_to(HOME.resolve()) and p.is_file() and sha(p)==r['sha256'],
            'Bound source SHA/path differs: '+str(p))
    return p

def library():
    for directory in (RUN/'baseline_a_pts_v1/vendor',RUN/'baseline_a_pts_v1',RUN/'temporal_sft8b_v1'):
        sys.path.insert(0,str(directory))
    sys.path.insert(0,str(HOME/'twenty_hour_five_20261014_v1/candidate_verify_v2/code'))
    import cv_tokens
    sys.path.insert(0,str(HOME/'twenty_hour_five_20261014_v1/production_stream_cache_v2/code'))
    import pixel_dictionary,codec
    sys.path.insert(0,str(HOME/'temporal_refinement_pilot_20261011/dev_01'))
    import runtime
    return runtime,cv_tokens,pixel_dictionary,codec

def tensor_load(r):
    import torch
    p=checked(r)
    with gzip.open(p,'rb') as f:payload=f.read()
    value=torch.load(BytesIO(payload),map_location='cpu',weights_only=True)
    del payload
    if r.get('storage_codec')=='PIXEL_UINT8_BIT_LUT_V1':value=library()[2].unpack(value)
    return value

def original(req):
    if req['input_kind']=='FULL_GZIP':return tensor_load(req['cache_ref'])
    require(req['input_kind']=='SPLIT_LUT','Unknown immutable input format')
    m=read(checked(req['cache_manifest_ref']));base=Path(req['cache_root'])
    refs=[m['private_ref'],m['visual_ref']];out={}
    for r in refs:
        out.update(tensor_load(dict(r,path=str(base/r['relative']))))
    return out

def original_absolute_prompt(req):
    candidates=[dict(id=i,interval_from_window_start=[round(float(__import__('fractions').Fraction(t)-__import__('fractions').Fraction(req['window_exact'][0])),4) for t in v['original_interval_exact']])
                for i,v in enumerate(req['candidate_events'])]
    return ('You are a selective silent-video highlights editor. Review the visible video, not an event caption. '
        'The listed intervals are current selected candidates, measured in seconds from this window start: '
        +json.dumps(candidates,separators=(',',':'))+'. '
        'Return five independent judgments. ordinary: list candidate IDs whose visible content is clearly uneventful setup, waiting, reset, or uninformative filler, with no distinctive visual reason to retain it. '
        'Recognizable people/objects alone do not make a highlight; however sparse evidence, silent speech, static scenic beauty, incomplete action, or uncertain identity alone are NOT grounds for removal. When uncertain leave the ID out. '
        'redundant: list candidate IDs that merely repeat a stronger occurrence visible elsewhere in this same window, adding no meaningful new action, result, reaction, or information; retain the strongest occurrence. Do not mark a sole occurrence redundant. '
        'Then propose at most ONE additional interval in each separate category: action (a distinctive physical action, skill, climax or payoff), reaction (a clearly visible expressive emotional or social reaction), information (a meaningful visual reveal, demonstration result, informative change or striking view). '
        'Find material OUTSIDE the listed current selections; do not use an existing selected highlight to justify an uneventful neighboring interval. Each proposed interval must have its own visible positive evidence. '
        'There are exactly 64 chronological displayed samples numbered 0..63. Express a proposal as [a,b], 0<=a<b<=64, selecting sample a through just before b; b=64 denotes this window actual end. Use [] when no distinct additional interval is supported. '
        'Categories may be empty and there is no required number of positive decisions. No audio, hidden labels, or external descriptions are available. '
        'Return ONLY canonical JSON with exactly these keys in this order: '
        '{"ordinary":[],"redundant":[],"action":[],"reaction":[],"information":[]}. No explanation.')

def validate(value,n):
    require(list(value)==list(FIELDS),'Exact five-field schema/order required')
    for name in FIELDS[:2]:
        x=value[name];require(isinstance(x,list) and all(type(i)is int and 0<=i<n for i in x) and x==sorted(set(x)),'Candidate index list invalid')
    for name in FIELDS[2:]:
        x=value[name];require(x==[] or isinstance(x,list) and len(x)==2 and all(type(i)is int for i in x) and 0<=x[0]<x[1]<=64,'Sample interval invalid')
    return value

def append(path,value):
    with Path(path).open('a',encoding='utf8') as f:
        f.write(json.dumps(value,separators=(',',':'))+'\n');f.flush();__import__('os').fsync(f.fileno())


def prompt(req):
    original=original_absolute_prompt(req)
    start=original.index('Return five independent judgments. ordinary:')
    end=original.index('Then propose at most ONE additional interval')
    rank=('First rank ONLY the listed current candidate intervals by how visually distinctive, informative, compelling, and worth keeping they are relative to one another in THIS visible window. '
      'This is a comparative edit, not a claim that rejected content is objectively ordinary. '
      'If there are two or more candidates, choose the SINGLE strongest candidate. In ordinary put all the OTHER candidate IDs, sorted ascending. '
      'In redundant put ONLY the SINGLE weakest candidate ID, which must also appear in ordinary. '
      'When only one candidate exists, both arrays are empty. Compare actual visible action, meaningful results, expressive reactions and information; do not rank merely by earlier time or candidate number. '
      'The two resulting edits are independent: ordinary keeps the strongest per window; redundant removes only the weakest per multi-candidate window. ')
    return original[:start]+rank+original[end:]

_base_validate=validate
def validate(value,n):
    _base_validate(value,n)
    require(len(value['ordinary'])==max(0,n-1) and len(value['redundant'])==(1 if n>1 else 0),'Relative ranking must account for each actual candidate')
    require(set(value['redundant'])<=set(value['ordinary']),'Weakest must be among candidates outside the strongest')
    return value
