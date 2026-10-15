"""Read-only project inventory by exact filename; does not open other video content."""
from pathlib import Path
import json,subprocess
HERE=Path(__file__).resolve().parent/'slot6_silver24_v1'
plan=json.loads((HERE/'source_window_plan.json').read_text());names=[r['source_id']+'.mp4' for r in plan['media']]
code='''import json,os,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path('/home/inspur/aic_video_work');names=set(NAMES);found=[];scanned=0
for d,dirs,files in os.walk(root):
 dirs[:]=[x for x in dirs if x.lower() not in {'100confirm','confirmation','test','tests','.git','env','models','cpu_env'}]
 for n in files:
  if n in names:
   p=Path(d)/n;found.append(dict(path=str(p),bytes=p.stat().st_size))
 scanned+=1
print(json.dumps(dict(status='READ_ONLY_PROJECT_FILENAME_INVENTORY',root=str(root),host=socket.gethostname(),
 exact_original_filenames=found,directories_scanned=scanned,no_other_video_content_read=True,
 not_a_semantic_reencoded_duplicate_search=True)))
'''.replace('NAMES',repr(names))
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','aic-inspur-home','python3','-B','-'],input=code,text=True,capture_output=True,timeout=60)
assert p.returncode==0,p.stderr
value=json.loads(p.stdout)
with (HERE/'linux_existing_sources_filename_audit_02.json').open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(value,ensure_ascii=False))
