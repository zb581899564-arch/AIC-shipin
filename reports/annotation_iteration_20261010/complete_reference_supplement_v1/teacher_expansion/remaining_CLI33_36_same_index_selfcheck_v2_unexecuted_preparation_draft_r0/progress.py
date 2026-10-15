from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
for n in range(1,11):
    a=ROOT/f'call{n:02d}'
    if not (a/'request.json').exists():continue
    terminal=json.loads((a/'terminal.json').read_text()) if (a/'terminal.json').exists() else None
    raw=a/'stream.jsonl';rows=[]
    for s in raw.read_text(encoding='utf-8-sig').splitlines() if raw.exists() else []:
        try:rows.append(json.loads(s))
        except json.JSONDecodeError:pass
    calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
    print(json.dumps(dict(call=n,CLI_after=26+n,terminal_exit=terminal['exit_code'] if terminal else None,done_tools=len(calls),facts_groups=len(list(a.glob('w*_group*.json'))),
      proposals=[p.name for p in a.glob('w*_proposal.json')],last_tool=calls[-1].get('tool_info',{}).get('parameters') if calls else None),ensure_ascii=False))
