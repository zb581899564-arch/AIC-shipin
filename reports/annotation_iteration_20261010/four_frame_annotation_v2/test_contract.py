"""Synthetic rejection tests; these are never annotation evidence."""
import json
from pathlib import Path
import runner as r

out=r.ROOT/'synthetic_contract_tests';out.mkdir(exist_ok=False)
rows=[dict(frame_id=f'F{i:02}',path=str(out/f'input_{i}.png'),source_ordinal=i,local_seconds_exact=str(i),png_sha256='synthetic') for i in range(4)]
facts=[dict(frame_id=x['frame_id'],actual_image_read=True,visible_subject='synthetic',subtitle_text=None,subtitle_legibility='absent',uncertainties=[]) for x in rows]

results=[]
for case in ['valid','wrong_identity','no_read','write_before_read','outside_image','extra_identity_field']:
    folder=out/case;folder.mkdir()
    target=folder/'facts_chunk_00.json'
    answer=json.loads(json.dumps(facts))
    if case=='wrong_identity':answer[0]['frame_id']='F99'
    if case=='extra_identity_field':answer[0]['source_ordinal']=999
    r.save(target,answer)
    tools=[dict(step=i,name='view_file',parameters={'AbsolutePath':x['path']}) for i,x in enumerate(rows)]
    if case=='no_read':tools=tools[:-1]
    if case=='outside_image':tools[0]['parameters']['AbsolutePath']=str(out/'outside.png')
    tools.append(dict(step=-1 if case=='write_before_read' else 5,name='write_to_file',parameters={'TargetFile':str(target)}))
    with (folder/'stream.jsonl').open('x',encoding='utf-8') as f:
        for t in tools:
            f.write(json.dumps(dict(step_update=dict(state='DONE',step_type='tool',step_index=t['step'],tool_name=t['name'],tool_info={'parameters':t['parameters']})))+'\n')
    result=r.audit(folder,'synthetic',rows)
    passed=not result['errors']
    assert passed==(case=='valid'),case
    results.append(dict(case=case,expected_accept=case=='valid',actual_accept=passed))
r.save(out/'results.json',dict(status='PASS_6_CONTRACT_CASES',synthetic_not_model_evidence=True,cases=results))
print('PASS: six positive/rejection contract cases')
