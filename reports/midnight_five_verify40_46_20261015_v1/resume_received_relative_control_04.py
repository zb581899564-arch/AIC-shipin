"""Reuse already-received complete control ZIP; fix only a metadata bool-map guard."""
from pathlib import Path
import ast,hashlib,json,subprocess
R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
archive=R/'relative_control_03.zip';size=archive.stat().st_size;digest=hashlib.sha256(archive.read_bytes()).hexdigest()
tree=ast.parse((R/'build_relative_03.py').read_text(encoding='utf8'))
node=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
code=eval(compile(ast.Expression(node),'<own_registered_control>','eval'),dict(ROOT=ROOT,PY=PY,archive=archive,size=size,digest=digest))
before="assert not json.loads((r/'dev_deletion_comparison_01.json').read_text())['passed_arms']"
after="assert not any(json.loads((r/'dev_deletion_comparison_01.json').read_text())['passed_arms'].values())"
assert code.count(before)==1
code=code.replace(before,after,1)
code=code.replace("assert (r/'dev_deletion_comparison_01.json').exists()", "assert not (r/'relative_code_v1').exists() and not (r/'relative_dev_03').exists()\nassert (r/'dev_deletion_comparison_01.json').exists()")
res=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home','python3','-'],input=code,text=True,capture_output=True)
print(res.stdout);print(res.stderr[-2500:] if res.returncode else '');res.check_returncode()
with (R/'received_relative_control_recovery_04.json').open('x',encoding='utf8') as f:json.dump(dict(prior_failure='Bool-map passed_arms evaluated as nonempty dict before extraction/registration/model; both false preserved',bytes=size,sha256=digest,ZIP_retransferred=False,prior_relative_model_calls=0,output=res.stdout),f,indent=2)
