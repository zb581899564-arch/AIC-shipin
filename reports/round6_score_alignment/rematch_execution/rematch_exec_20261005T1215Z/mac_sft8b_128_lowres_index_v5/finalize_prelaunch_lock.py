from pathlib import Path
import json,hashlib,datetime as dt
HERE=Path(__file__).resolve().parent
path=HERE/'source_lock.json'
lock=json.loads(path.read_text());path.rename(HERE/'source_lock_initial_unlaunched.json')
lock['created_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
lock['files']={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in lock['files']}
path.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(hashlib.sha256(path.read_bytes()).hexdigest())
