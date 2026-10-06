"""Independent metadata-only recovery audit; never print prediction content."""
import hashlib,json
from pathlib import Path
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CODE,REC,CTRL=RUN/'baseline_a_pts_v1',RUN/'baseline_a_format_recovery_v1',RUN/'controller'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def require(ok,message):
    if not ok:raise RuntimeError(message)
old_path,new_path=CODE/'rematch_e2e_01/temporal.jsonl',REC/'recover_01/temporal.jsonl'
require(sha(old_path)=='2790809c4defd2988dba5a44ed659b436ab78efe942b6f2f1d0f118ab92071c9','original output changed')
old=[json.loads(x) for x in old_path.read_text().splitlines() if x.strip()]
new=[json.loads(x) for x in new_path.read_text().splitlines() if x.strip()]
require(len(old)==len(new)==426,'video denominator changed')
require(len({r['video_id'] for r in new})==426,'duplicate video IDs')
unchanged=recovered=windows=0
for before,after in zip(old,new):
    require({k:v for k,v in before.items() if k!='windows'}=={k:v for k,v in after.items() if k!='windows'},
        'video metadata changed')
    require(len(before['windows'])==len(after['windows']),'window denominator changed')
    for a,b in zip(before['windows'],after['windows']):
        windows+=1
        if a['output_valid']:
            require(canonical(a)==canonical(b),'successful window changed')
            unchanged+=1
        else:
            allowed={'status','output_valid','raw_output','parsed_segments','parse_errors','parse_warnings',
                'sampled_frames','peak_memory_mib','seconds','format_recovery'}
            require({k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in b.items() if k not in allowed},
                'failed-window identity or scope changed')
            require(b['format_recovery']['attempt']==1 and b['format_recovery']['original_window_sha256']==canonical(a)
                and b['status']=='MODEL_OK' and b['output_valid'] and not b['parse_errors'] and not b['parse_warnings'],
                'recovery evidence is incomplete')
            parsed=json.loads(b['raw_output'])['segments']
            require(parsed==b['parsed_segments'] and 1<=len(parsed)<=5,'raw generation was rewritten')
            duration=b['end_sec']-b['start_sec']
            require(all(0<=x<y<=duration for x,y in parsed)
                and all(parsed[i][0]>=parsed[i-1][1] for i in range(1,len(parsed))), 'raw intervals are illegal')
            recovered+=1
require(windows==521 and unchanged==516 and recovered==5,'recovery denominator changed')
result=dict(status='PASS_INDEPENDENT_RECOVERY_PRESERVATION',videos=426,windows=windows,
    successful_window_objects_unchanged=unchanged,recovered_windows=recovered,raw_equals_parsed=True,
    original_sha256=sha(old_path),recovered_sha256=sha(new_path),uploaded=False)
with (CTRL/'format_preservation_audit.json').open('x') as handle:handle.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
