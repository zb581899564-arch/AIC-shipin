"""Only exact frozen index rereads are engineering selfchecks, not media."""
from pathlib import Path
def key(p):return str(Path(p).resolve()).casefold()
def index_selfchecks(steps,index_path):
    target=key(index_path);kept=[];checks=[]
    for t in steps:
        p=t.get('tool_info',{}).get('parameters',{})
        if t.get('tool_name')=='view_file' and key(p.get('AbsolutePath',''))==target:
            checks.append(dict(step=t.get('step_index'),path=p.get('AbsolutePath'),core_tools_before=len(kept),initial=(len(checks)==0)))
            if len(checks)==1:kept.append(t)
        else:kept.append(t)
    return kept,dict(exact_index_path=str(index_path),DONE_read_count=len(checks),extra_read_count=max(0,len(checks)-1),reads=checks,advisory_total_max=5,hard_count_limit=False,index_is_not_media=True)
def classify_nonmedia_errors(steps):
    metadata={'conversation_id','step_index','state','step_type','duration_seconds'}
    bare=[];reported=[]
    for t in steps:
        body={k:v for k,v in t.items() if k not in metadata and v not in (None,'',{},[]) and not (isinstance(v,str) and not v.strip())}
        if body:reported.append(t)
        else:bare.append(dict(actual_metadata=t,cause='UNKNOWN_NO_BODY_IN_ACTUAL_STREAM',is_media_read_failure=False))
    return bare,reported
