from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import json, hashlib, struct
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'slot6_silver24_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def geometry(p):
    b=Path(p).read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';return list(struct.unpack('>II',b[16:24]))
def prepare():
    jobs=read(BASE/'observations/jobs.json')['jobs'];assert len(jobs)==24
    calls=[]
    for no,nums in enumerate([list(range(i,min(i+2,24))) for i in range(3,24,2)]):
        a=ROOT/f'call{no:02d}';a.mkdir(exist_ok=False);windows=[];inputs={};writes=[]
        for j in nums:
            job=Path(jobs[j]);m=read(job/'manifest.json');r=read(job/'student_views/receipt.json')
            assert len(m['frames'])==len(r['frames'])==64
            assert r['status']=='PASS_ACTUAL_LOCAL_CPU_NATIVE_PROCESSOR_TENSOR_VIEWS' and not r['cuda_initialized']
            for p in (job/'manifest.json',job/'student_views/receipt.json'):inputs[str(p.resolve())]=sha(p)
            assert sha(m['clip_path'])==m['clip_sha256'];inputs[m['clip_path']]=m['clip_sha256']
            groups=[]
            for g in range(16):
                out=a/f'w{j:02d}_group{g:02d}.json';writes.append(str(out));frames=[]
                for s,f in enumerate(m['frames'][g*4:g*4+4]):
                    assert sha(f['path'])==f['png_sha256'];inputs[f['path']]=f['png_sha256']
                    frames.append(dict(slot=s,**f,geometry=geometry(f['path'])))
                groups.append(dict(group=g,frames=frames,output_path=str(out)))
            previews=[]
            for n in (0,9,18,27,36,45,54,63):
                f=r['frames'][n];assert f['frame_id']==m['frames'][n]['frame_id'] and f['source_ordinal']==m['frames'][n]['source_ordinal']
                assert sha(f['path'])==f['png_sha256'];inputs[f['path']]=f['png_sha256'];previews.append(dict(**f,geometry=geometry(f['path'])))
            proposal=a/f'w{j:02d}_proposal.json';writes.append(str(proposal))
            windows.append(dict(job_index=j,window_id=m['window_id'],domain_local_seconds=[0,str(Fraction(m['domain_global_seconds_exact'][1])-Fraction(m['domain_global_seconds_exact'][0]))],
                source_group=m['source_group'],role=m['role'],groups=groups,clip_path=m['clip_path'],clip_pts_offset_exact=m['clip_pts_offset_exact'],
                student_previews=previews,actual_student_frames=64,teacher_student_preview_count=8,student_width=r['student_width'],student_height=r['student_height'],
                proposal_path=str(proposal),manifest_sha256=sha(job/'manifest.json'),student_receipt_sha256=sha(job/'student_views/receipt.json')))
        index=a/'index.json';save(index,dict(windows=windows,fact_schema=['slot','subject','composition','subtitle_visible','subtitle_text','visible_fact'],model_identity_forbidden=True))
        inputs[str(index)]=sha(index)
        reads=[str(index)]+[f['path'] for w in windows for g in w['groups'] for f in g['frames']]+[p for w in windows for p in [w['clip_path']]+[f['path'] for f in w['student_previews']]]
        save(a/'freeze.json',dict(utc=datetime.now(timezone.utc).isoformat(),inputs=inputs,read_whitelist=reads,self_read_whitelist=writes,write_whitelist=writes,
          protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(ROOT.parent/'PROTOCOL.md'),fixed_job_indices=nums,
          CLI_before=23+no,CLI_after=24+no,global_cap=36,stage_cap=11,timeout_seconds=1500,automatic_retry=False))
        calls.append(dict(call=no,job_indices=nums,path=str(a),index_sha256=sha(index),freeze_sha256=sha(a/'freeze.json')))
    save(ROOT/'plan.json',dict(utc=datetime.now(timezone.utc).isoformat(),calls=calls,windows=21,prior_CLI_calls=23,max_after_CLI_calls=34,
         prior_jobs_sha256=sha(BASE/'observations/jobs.json'),training_admitted=False,old_W11_audit_not_reused=True))
    print(json.dumps(dict(prepared_calls=len(calls),fixed_windows=21,max_after=34)))
if __name__=='__main__':prepare()
