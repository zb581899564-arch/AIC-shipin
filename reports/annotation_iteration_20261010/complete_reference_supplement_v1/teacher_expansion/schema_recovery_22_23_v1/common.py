from pathlib import Path
from fractions import Fraction
import hashlib,json,re
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):return str(Path(p).resolve()).casefold() if p else ''
def save(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)

def bootstrap_metadata(payload,output):
 b=re.search(r'(\d+) bytes',output);n=re.search(r'(\d+) lines',output)
 return bool(payload.endswith(b'\n') and b'\r' not in payload and b and n and int(b.group(1))==len(payload) and int(n.group(1))==len(payload.split(b'\n')) and not any(x in output.lower() for x in ('truncat','not found','cannot read','failed','error')))
def expected_core(index,stop_job=None):
 parts={p['part_id']:p for p in index['text_fragments']}
 def pair(p):return [('view_file',key(p['path'])),('write_to_file',key(p['ack_path']))]
 out=pair(parts[index['main_fragment_id']])
 for w in index['windows']:
  out.extend(pair(parts[w['header_fragment_id']]))
  for g in w['groups']:
   out.extend(pair(parts[w['native_fragment_ids'][g['group']]]))
   out.extend(('view_file',key(f['path'])) for f in g['frames']);out.append(('write_to_file',key(g['output_path'])))
  out.append(('view_file',key(w['clip_path'])))
  out.extend(('view_file',key(f['path'])) for f in w['student_previews']);out.extend(pair(parts[w['proposal_fragment_id']]));out.append(('write_to_file',key(w['proposal_path'])))
  if w['job_index']==stop_job:break
 return out

def scientific_core(index,stop_job=None):
 out=[]
 for w in index['windows']:
  for g in w['groups']:out.extend(('view_file',key(f['path'])) for f in g['frames']);out.append(('write_to_file',key(g['output_path'])))
  out.append(('view_file',key(w['clip_path'])));out.extend(('view_file',key(f['path'])) for f in w['student_previews']);out.append(('write_to_file',key(w['proposal_path'])))
  if w['job_index']==stop_job:break
 return out
def fact_items(doc,group):
 assert set(doc)=={'group','items'} and type(doc['group']) is int and doc['group']==group and isinstance(doc['items'],list) and len(doc['items'])==4
 assert [r['slot'] for r in doc['items']]==[0,1,2,3]
 for r in doc['items']:
  assert type(r['slot']) is int
  assert set(r)=={'slot','subject','composition','subtitle_visible','subtitle_text','visible_fact'}
  assert all(isinstance(r[k],str) and r[k].strip() for k in ('subject','composition','visible_fact'))
  assert type(r['subtitle_visible']) is bool or r['subtitle_visible']=='UNKNOWN'
  if r['subtitle_visible'] is False:assert r['subtitle_text'] is None
  else:assert isinstance(r['subtitle_text'],str) and r['subtitle_text']
 return doc['items']
def proposal_schema(p,w):
 d=read(p);assert set(d)=={'segments','events','student_visibility','limitations'}
 assert isinstance(d['events'],list) and isinstance(d['segments'],list) and d['segments']
 end=Fraction(w['domain_local_seconds'][1]);cursor=Fraction(0)
 for s in d['segments']:
  assert set(s)=={'decision','start_seconds','end_seconds','reason','fact_support','start_uncertainty_range_seconds','end_uncertainty_range_seconds'}
  assert s['decision'] in ('KEEP','NO','UNKNOWN') and s['reason'] and isinstance(s['fact_support'],list)
  lo=Fraction(str(s['start_seconds']));hi=Fraction(str(s['end_seconds']));assert lo==cursor and lo<hi<=end;cursor=hi
  for k in ('start_uncertainty_range_seconds','end_uncertainty_range_seconds'):
   z=s[k];assert len(z)==2 and 0<=Fraction(str(z[0]))<=Fraction(str(z[1]))<=end
  for f in s['fact_support']:assert set(f)=={'group','slot'} and f['group'] in range(16) and f['slot'] in range(4)
 assert cursor==end
 for e in d['events']:
  assert set(e)=={'description','decision','start_seconds','end_seconds','fact_support','boundary_reason'}
  assert e['decision'] in ('KEEP','NO','UNKNOWN') and e['description'] and e['boundary_reason']
  assert 0<=Fraction(str(e['start_seconds']))<Fraction(str(e['end_seconds']))<=end
  assert isinstance(e['fact_support'],list)
  for f in e['fact_support']:assert set(f)=={'group','slot'} and type(f['group']) is int and f['group'] in range(16) and type(f['slot']) is int and f['slot'] in range(4)
 return d
def metadata_errors(steps):
 bare=[];reported=[];keys={'conversation_id','step_index','state','step_type','duration_seconds'}
 for t in steps:
  body={k:v for k,v in t.items() if k not in keys and v not in (None,'',{},[]) and not(isinstance(v,str) and not v.strip())}
  if body:reported.append(t)
  else:bare.append(dict(actual_metadata=t,cause='UNKNOWN_NO_BODY_IN_ACTUAL_STREAM',is_media_failure=False))
 return bare,reported
