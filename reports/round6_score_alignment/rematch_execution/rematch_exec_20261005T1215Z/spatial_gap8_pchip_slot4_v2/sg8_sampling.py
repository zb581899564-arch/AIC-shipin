"""Deterministic metadata-only sample ordering, independent of output coordinates."""
import hashlib
import json

TASK='AIC-VIDEO-REMATCH-NEXT-20261005/spatial_gap8_pchip_slot4_v1'
KEYS={'source_group','source_sha256','video_id','shot_id','support_ordinals','support_request_sha256','scope'}


def key(value):
    return hashlib.sha256((TASK+'\n'+json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))).encode()).hexdigest()


def select(candidates):
    """Prefer registered NONTEST groups; never reads boxes/probe/score fields.

    All candidate source identities, original shot membership and support request
    SHA must be independently validated by G0 caller before this pure function.
    """
    groups={}
    for row in candidates:
        if set(row)!=KEYS or row['scope'] not in ('nontest','developer'):
            raise ValueError('only registered metadata fields allowed')
        if not isinstance(row['source_group'],str) or not row['source_group']:
            raise ValueError('source group missing')
        if type(row['shot_id']) is not int or not isinstance(row['video_id'],str):
            raise ValueError('invalid metadata identity')
        hashes=[row['source_sha256']]+row['support_request_sha256']
        if len(hashes)!=5 or any(not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h) for h in hashes):
            raise ValueError('invalid bound support hashes')
        q=row['support_ordinals']
        if len(q)!=4 or any(type(f) is not int or f<0 for f in q) or not (1<=q[1]-q[0]<=8 and q[2]-q[1]==8 and 1<=q[3]-q[2]<=8):
            raise ValueError('invalid four-support central gap8')
        groups.setdefault(row['source_group'],[]).append(row)
    ranked=[]
    for group,rows in groups.items():
        first_scope='nontest' if any(r['scope']=='nontest' for r in rows) else 'developer'
        eligible=[r for r in rows if r['scope']==first_scope]
        file_sha=min({r['source_sha256'] for r in eligible},key=lambda h:key({'source_group':group,'source_sha256':h}))
        file_rows=[r for r in eligible if r['source_sha256']==file_sha]
        chosen=min(file_rows,key=key)
        ranked.append((0 if first_scope=='nontest' else 1,key({'source_group':group}),chosen))
    if len(ranked)<8:
        raise ValueError('NO_426: fewer than eight registered eligible source groups')
    selected=[r for _,__,r in sorted(ranked,key=lambda v:v[:2])[:8]]
    return [dict(row,group_index=i,role='engineering' if i<2 else 'confirmation',probe_ordinals=list(range(row['support_ordinals'][1]+1,row['support_ordinals'][2]))) for i,row in enumerate(selected)]
