from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
ROOT=Path(__file__).resolve().parent; OLD=ROOT.parent
CID='7f341ecf-da15-407b-94af-83316fccaeaa'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def prepare():
    olda=OLD/'call00';audit=read(olda/'audit.json');t=read(olda/'terminal.json');oldidx=read(olda/'index.json')
    w=oldidx['windows'][0];report=audit['windows'][0]
    assert report['job_index']==3 and report['bound_rows']==64 and not report['schema_issues']
    assert report['clip_read_done'] and not audit['unfinished_tool_attempts']
    assert not Path(w['proposal_path']).exists();assert audit['actual_nonself_tool_calls']==85
    assert all(i['reason']=='SUPPLY_ORDER_BARRIER_OR_WHITELIST' for i in audit['tool_issues'])
    assert t['stream_sha256']==sha(olda/'stream.jsonl')=='ba9a6b05fa287c610b53fced62b2df907df9821b4bbfd8976dbcad02ab5756c6'
    a=ROOT/'resume_w11';a.mkdir(exist_ok=False)
    done={f['frame_id'] for f in report['student_preview_read_done']};remaining=[f for f in w['student_previews'] if f['frame_id'] not in done]
    assert [f['frame_id'] for f in remaining]==['F27','F36','F45','F54','F63']
    inputs={str(olda/p):sha(olda/p) for p in ('terminal.json','stream.jsonl','audit.json','index.json','freeze.json','w03_program_bound_facts.json')}
    for g in w['groups']:inputs[g['output_path']]=sha(g['output_path'])
    for p in remaining:inputs[p['path']]=sha(p['path']);assert inputs[p['path']]==p['png_sha256']
    nw=copy.deepcopy(w);nw['proposal_path']=str(a/'w03_proposal.json')
    index=dict(window=nw,remaining_previews=remaining,conversation_id=CID,cancelled_old_second_job_index=4,
       inherited_completed_native_frames=64,inherited_completed_fact_groups=list(range(16)),inherited_clip_done=True,inherited_student_previews=sorted(done),
       original_actual_supply=report['actual_supply'],logical_proposal_count=1,actual_student_frames=64,teacher_preview_count=8)
    save(a/'index.json',index);inputs[str(a/'index.json')]=sha(a/'index.json')
    save(a/'freeze.json',dict(utc=datetime.now(timezone.utc).isoformat(),inputs=inputs,conversation_id=CID,
       read_whitelist=[str(a/'index.json')]+[f['path'] for f in remaining],self_read_whitelist=[nw['proposal_path']],write_whitelist=[nw['proposal_path']],
       inherited_parent_terminal_sha256=sha(olda/'terminal.json'),inherited_parent_raw_sha256=sha(olda/'stream.jsonl'),
       protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(OLD/'PROTOCOL.md'),CLI_before=24,CLI_after=25,global_cap=36,timeout_seconds=4500,automatic_retry=False))
    # Repartition original fixed jobs4..23, using frozen original media/index entries without decoding again.
    byjob={}
    for n in range(11):
        for v in read(OLD/f'call{n:02d}/index.json')['windows']:byjob[v['job_index']]=v
    calls=[]
    for n,start in enumerate(range(4,24,2),1):
        dest=ROOT/f'call{n:02d}';dest.mkdir(exist_ok=False);wins=[];inp={};writes=[];reads=[str(dest/'index.json')]
        for j in (start,start+1):
            v=copy.deepcopy(byjob[j])
            for g in v['groups']:
                g['output_path']=str(dest/f'w{j:02d}_group{g["group"]:02d}.json');writes.append(g['output_path'])
                for f in g['frames']:assert sha(f['path'])==f['png_sha256'];inp[f['path']]=f['png_sha256'];reads.append(f['path'])
            v['proposal_path']=str(dest/f'w{j:02d}_proposal.json');writes.append(v['proposal_path']);wins.append(v)
        for v in wins:
            reads.append(v['clip_path']);inp[v['clip_path']]=sha(v['clip_path'])
            for f in v['student_previews']:assert sha(f['path'])==f['png_sha256'];inp[f['path']]=f['png_sha256'];reads.append(f['path'])
        save(dest/'index.json',dict(windows=wins,model_identity_forbidden=True));inp[str(dest/'index.json')]=sha(dest/'index.json')
        save(dest/'freeze.json',dict(utc=datetime.now(timezone.utc).isoformat(),inputs=inp,read_whitelist=reads,self_read_whitelist=writes,write_whitelist=writes,
          protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(OLD/'PROTOCOL.md'),fixed_job_indices=[start,start+1],CLI_before=24+n,CLI_after=25+n,global_cap=36,timeout_seconds=4500,automatic_retry=False))
        calls.append(dict(call=n,job_indices=[start,start+1],path=str(dest),freeze_sha256=sha(dest/'freeze.json')))
    save(ROOT/'plan.json',dict(utc=datetime.now(timezone.utc).isoformat(),resumed_window=dict(job_index=3,path=str(a),conversation_id=CID,freeze_sha256=sha(a/'freeze.json')),calls=calls,fixed_windows=21,prior_global_count=24,max_after=35,
       original_failure_preserved=True,original_25m_plan_not_started=True,training_admitted=False))
    print(json.dumps(dict(frozen_resume=3,remaining_previews=5,new_fixed_pairs=10,max_global_CLI=35)))
if __name__=='__main__':prepare()
