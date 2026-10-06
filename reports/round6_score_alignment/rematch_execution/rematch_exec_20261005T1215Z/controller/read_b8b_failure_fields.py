import collections,json
from pathlib import Path
p=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v2/rematch_01/temporal.jsonl')
rows=[json.loads(x) for x in p.read_text().splitlines()]
c=collections.Counter((w['status'],tuple(w.get('parse_errors',[]))) for r in rows for w in r['windows'])
print(json.dumps(dict(rows=len(rows),failure_fields=[dict(status=k[0],errors=k[1],count=v) for k,v in c.items()]),ensure_ascii=False))
