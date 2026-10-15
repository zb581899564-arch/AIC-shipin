"""Audit four-image barriers, bind identities, compare frozen finite-image facts."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,unicodedata
ROOT=Path(__file__).resolve().parent; A=ROOT/'attempt01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s).split()) if isinstance(s,str) else s
def key(p):return str(Path(p).resolve()).casefold()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
terminal=read(A/'terminal.json'); freeze=read(ROOT/'freeze.json');idx=read(ROOT/'teacher_index.json');oracle=read(ROOT/'oracle_frozen.json')
for n,s in freeze['files'].items():assert sha(ROOT/n)==s
assert sha(A/'stream.jsonl')==terminal['stream_sha256']
frames=[r for g in idx['groups'] for r in g['frames']]; imagekeys=[key(r['path']) for r in frames]
outputs={key(g['output_path']):g['group'] for g in idx['groups']}
rows=[json.loads(s) for s in (A/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
seen=[];written=[];selfreads={};metadata_reads=0;issues=[]
for c in calls:
    info=c.get('tool_info',{});params=info.get('parameters',{});name=c.get('tool_name')
    path=params.get('AbsolutePath') or params.get('TargetFile');path=key(path) if path else None
    output=str(info.get('output',''));failed=any(s in output.lower() for s in ('not found','cannot read','failed to','error reading'))
    if name=='view_file':
        if failed:issues.append(dict(path=path,reason='READ_FAILURE'))
        elif path in imagekeys:
            i=len(seen)
            if i>=20 or path!=imagekeys[i]:issues.append(dict(path=path,reason='IMAGE_ORDER_OR_REPEAT'))
            if i//4!=len(written):issues.append(dict(path=path,reason='NEXT_GROUP_READ_BEFORE_PRIOR_WRITE'))
            seen.append(path)
        elif path==key(ROOT/'teacher_index.json'):
            metadata_reads+=1
            if metadata_reads>1 or seen:issues.append(dict(path=path,reason='METADATA_ORDER_REPEAT'))
        elif path in outputs and outputs[path] in written:
            selfreads[path]=selfreads.get(path,0)+1
            if selfreads[path]>1:issues.append(dict(path=path,reason='REPEATED_SELF_READ'))
        else:issues.append(dict(path=path,reason='OUTSIDE_READ_WHITELIST_OR_UNCREATED_OUTPUT'))
    elif name=='write_to_file':
        if path not in outputs:issues.append(dict(path=path,reason='OUTSIDE_WRITE_WHITELIST'))
        else:
            g=outputs[path]
            if g!=len(written) or len(seen)!=(g+1)*4:issues.append(dict(path=path,reason='GROUP_WRITE_BARRIER'))
            written.append(g)
    else:issues.append(dict(tool=name,path=path,reason='UNEXPECTED_TOOL'))
if seen!=imagekeys:issues.append(dict(reason='20_IMAGE_SUPPLY_INCOMPLETE_OR_ORDER_DIFFERS'))
if written!=list(range(5)):issues.append(dict(reason='5_WRITES_INCOMPLETE_OR_REPEATED'))
if metadata_reads!=1:issues.append(dict(reason='METADATA_SUPPLY'))
bound=[];differences=[];schema=[]
for g in idx['groups']:
    p=Path(g['output_path'])
    if not p.is_file():schema.append(dict(group=g['group'],reason='OUTPUT_MISSING'));continue
    try:
        doc=read(p)
        assert set(doc)=={'group','items'} and doc['group']==g['group']
        assert len(doc['items'])==4 and [r['slot'] for r in doc['items']]==[0,1,2,3]
        for item,f in zip(doc['items'],g['frames']):
            assert set(item)=={'slot','subject','composition','subtitle_visible','subtitle_text','visible_fact'}
            assert item['subject'] in idx['subject_enum'] and item['composition'] in idx['composition_enum']
            assert item['subtitle_visible'] in [True,False,'UNKNOWN'] and isinstance(item['visible_fact'],str) and item['visible_fact'].strip()
            assert sha(Path(f['path']))==f['png_sha256']
            # Identity is taken ONLY from the frozen index, never model-generated metadata.
            row=dict(group=g['group'],slot=item['slot'],frame_id=f['frame_id'],source_ordinal=f['source_ordinal'],
             local_seconds_exact=f['local_seconds_exact'],global_seconds_exact=f['global_seconds_exact'],png_sha256=f['png_sha256'],
             facts=item,raw_output_sha256=sha(p),identity_generated_by_program=True)
            expected=next(o for o in oracle['items'] if o['group']==g['group'] and o['slot']==item['slot'])
            for field in ('subject','composition','subtitle_visible','subtitle_text'):
                if norm(item[field])!=norm(expected[field]):differences.append(dict(frame_id=f['frame_id'],field=field,actual=item[field],expected=expected[field]))
            bound.append(row)
    except Exception as e:schema.append(dict(group=g['group'],reason='INVALID_GROUP_SCHEMA_OR_SHA',error=repr(e)))
save(ROOT/'program_bound_facts.json',dict(status='PROGRAM_BINDING_NOT_HIGHLIGHT_LABELS',rows=bound,oracle_sha256=sha(ROOT/'oracle_frozen.json'),full_window=False,training_admitted=False))
result=next((r.get('result',{}) for r in reversed(rows) if r.get('event')=='result'),{})
accepted=not issues and not schema and not differences and len(bound)==20 and terminal['exit_code']==0
out=dict(status='FIELD_COMPARISON_PASS_PENDING_MAIN_FACT_REVIEW' if accepted else 'STOP_MINIMUM_METHOD_TEST_FAILED',
 utc=datetime.now(timezone.utc).isoformat(),actual_images_delivered=len(seen),group_writes=written,tool_issues=issues,schema_issues=schema,
 field_differences=differences,bound_rows=len(bound),all_frozen_semantic_fields_match=not differences and len(bound)==20,
 program_bound_facts_sha256=sha(ROOT/'program_bound_facts.json'),freeze_sha256=sha(ROOT/'freeze.json'),
 stream_sha256=sha(A/'stream.jsonl'),terminal_sha256=sha(A/'terminal.json'),actual_result_status=result.get('status'),
 actual_result_usage=result.get('usage'),cash_cost='UNKNOWN_NOT_ZERO',new_CLI_calls=1,total_CLI_after=23,global_CLI_cap=36,
 new_training=0,new_426=0,new_Pro=0,full_window_admitted=False,human_gold=False,old_v3_STOP_preserved=True,automatic_retry=False)
save(ROOT/'audit.json',out)
print(json.dumps(out,ensure_ascii=False))
