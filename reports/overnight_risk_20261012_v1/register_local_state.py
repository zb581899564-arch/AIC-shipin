import pathlib,sys,json
header=sys.stdin.read()
for name in ['AGENTS.md','ROADMAP.md']:
 p=pathlib.Path(name);old=p.read_bytes();b=pathlib.Path('reports/overnight_risk_20261012_v1')/(name+'.before_risk')
 with b.open('xb') as f:f.write(old)
 p.write_bytes(header.encode('utf-8')+old)
p=pathlib.Path('improvement/annotation_pipeline/policy.json');old=p.read_bytes()
with pathlib.Path('reports/overnight_risk_20261012_v1/policy.before_risk.json').open('xb') as f:f.write(old)
x=json.loads(old);x['diagnostic_experiments']['temporal_refinement_fact6_20261011_v2'].update(status='STOP_NATIVE_UNREALIZABLE_ACTUAL_OUTPUT',actual_model_calls=5,accepted_model_calls=4,charged_seconds=113.77065153233707)
x['risk_submission_iterations']={'overnight_risk_20261012_v1':{'status':'AUTHORIZED_NEW_RISK_CANDIDATES','protocol':'reports/overnight_risk_20261012_v1/registration_receipt.json','scientific_quality_pass':False,'official_score':None}}
p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')