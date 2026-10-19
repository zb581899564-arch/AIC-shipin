"""Pure fixed connected-star support; no artifact/model/processor IO."""
from collections import Counter
import copy
import hashlib
import json
import math

SCHEMA='UTILITY_CONNECTED_STAR_TRAIN_SCHEDULE_V68'
GATE='PASS_UTILITY68_CONNECTED_STAR_ALL_INPUTS_FIRST_CPU_QA'
TARGET_RMS=.15513293164263023
RECIPE=dict(updates=800,initial_step=500,final_step=1300,grad_accum=4,rank=8,alpha=16,dropout=0.,
    lora_lr=5e-5,head_lr=.001,geometry_lr=.001,weight_decay=0.,grad_clip=1.,seed=20261018,
    head_init_std=.001,head_bias=False,geometry_init=0.,
    loss='DRAW_WEIGHT_TIMES_TARGET_RMS_NORMALIZED_SQUARED_GAIN_ERROR',final_only=True)


def require(value,message):
    if not value:raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def key(*values):
    return hashlib.sha256('|'.join(map(str,values)).encode()).hexdigest()[:24]


def build_plan(catalog,gain,old_requests):
    """Metadata-only plan; old_requests maps accepted44 id to loaded request."""
    sources=sorted([copy.deepcopy(s) for s in catalog['sources'] if s['role']=='train'],
        key=lambda s:(s['source_sha256'],s['source_id']))
    require(len(sources)==len({s['source_id'] for s in sources})==len({s['source_sha256'] for s in sources})==602
        and all(len(s['pool'])==6 and s['original_BASE_observed'] is False for s in sources), 'Original602 synthetic six-pools only')
    byid={s['source_id']:s for s in sources};old={};crop_refs={sid:{} for sid in byid};templates={}
    entries={e['id']:e for e in gain['train_inputs']}
    require(len(entries)==len(old_requests)==2408,'Accepted44 complete ordered input metadata')
    for cid,entry in entries.items():
        q=old_requests[cid];s=byid[q['source_id']];a,b=q['candidate_indices']
        require(q['id']==entry['id']==key(s['source_sha256'],a,b,'CROP31_TRIPLET')
            and q['source_id']==entry['source_id'] and q['source_sha256']==entry['source_sha256']==s['source_sha256']
            and q['role']=='train' and q['reference_or_target_in_prompt'] is False and a!=b
            and q['boxes']==[s['pool'][a],s['pool'][b]] and q['vision_inputs'][0]==s['source_vision']
            and q['class_token_ids']==gain['class_token_ids'],'Adopted44 request owner/box/class identity')
        require(not any(k in q for k in ('target','labels','candidate_ious','original_reference_xywh')),'No human targets in input metadata')
        require((s['source_id'],a,b) not in old,'Duplicate ordered candidate owner')
        old[s['source_id'],a,b]=entry
        templates.setdefault(s['source_id'],copy.deepcopy(entry))
        for i,r in zip((a,b),q['vision_inputs'][1:]):
            require(crop_refs[s['source_id']].get(i,r)==r,'Old candidate has conflicting crop refs')
            crop_refs[s['source_id']][i]=copy.deepcopy(r)
    cases=[];pairs=[]
    for s in sources:
        sid=s['source_id']
        for b in range(1,6):
            ids=[]
            for a,c in ((0,b),(b,0)):
                cid=key(s['source_sha256'],a,c,'CROP31_TRIPLET');ids.append(cid);prior=old.get((sid,a,c))
                cases.append(dict(id=cid,source_id=sid,source_sha256=s['source_sha256'],a=a,b=c,
                    adopted_input=prior is not None,input=copy.deepcopy(prior['input']) if prior else None))
            pairs.append(dict(source_id=sid,source_sha256=s['source_sha256'],a=0,b=b,first_id=ids[0],reverse_id=ids[1]))
    return dict(sources=sources,cases=cases,pair_index=pairs,crop_refs=crop_refs,templates=templates,
        adopted_inputs=sum(c['adopted_input'] for c in cases),first_new_combinations=sum(not c['adopted_input'] for c in cases),
        new_crop_count=sum(6-len(crop_refs[sid]) for sid in byid),class_token_ids=copy.deepcopy(gain['class_token_ids']),
        GT_used_for_input_or_pair_choice=False,selection='ALL_GEOMETRY_BASE0_TO_1_2_3_4_5')


def compile_schedule(plan,targets,input_refs,geometry):
    sources={s['source_id']:s for s in plan['sources']};labels={s['source_id']:s for s in targets if s['role']=='train'}
    require(set(labels)==set(sources),'Exact original602 train target source set')
    entries={c['id']:dict(id=c['id'],source_id=c['source_id'],source_sha256=c['source_sha256'],input=copy.deepcopy(input_refs[c['id']])) for c in plan['cases']}
    require(set(input_refs)==set(entries) and len(entries)==6020,'Complete ordered6020 immutable request refs')
    pairs=sorted(plan['pair_index'],key=lambda p:key(p['source_sha256'],p['a'],p['b'],'UTILITY68_STAR_PAIR'))
    require(len(pairs)==3010,'Every five star edges/source')
    extras=sorted(pairs,key=lambda p:key(p['source_sha256'],p['b'],'UTILITY68_EXTRA'))[:190]
    draws=[(p,0) for p in pairs]+[(p,1) for p in extras]
    draws.sort(key=lambda pr:key(pr[0]['source_sha256'],pr[0]['b'],pr[1],'UTILITY68_DRAW_ORDER'))
    counts=Counter((p['source_id'],p['b']) for p,_ in draws);rows=[]
    for i,(p,repeat) in enumerate(draws):
        s=sources[p['source_id']];t=labels[p['source_id']];truth=t['candidate_ious'];b=p['b']
        require(t['source_sha256']==s['source_sha256'] and t['baseline_index']==0 and t['reference_modified'] is False
            and len(truth)==6 and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in truth),'Unmodified original train IoUs')
        reverse=int(key(s['source_sha256'],b,repeat,'UTILITY68_ORIENTATION'),16)%2==1
        a,c=(b,0) if reverse else (0,b);forward=entries[p['reverse_id'] if reverse else p['first_id']]
        backward=entries[p['first_id'] if reverse else p['reverse_id']]
        delta=geometry(s['pool'][c],s['width'],s['height'])[1:12]-geometry(s['pool'][a],s['width'],s['height'])[1:12]
        rows.append(dict(id='S%04d'%i,source_id=s['source_id'],source_sha256=s['source_sha256'],a=a,b=c,
            unordered_pair=[0,b],forward=forward,reverse=backward,forward_id=forward['id'],reverse_id=backward['id'],
            geometry_delta11=[float(v) for v in delta],target=float(truth[c])-float(truth[a]),
            draw_weight=3200/(3010*counts[s['source_id'],b])))
    return rows


def validate_schedule(prepared):
    require(prepared['schema']==SCHEMA and prepared['train_target_RMS']==TARGET_RMS,'New68 schema and unchanged55 RMS')
    rows=prepared['train_schedule'];require(len(rows)==len({r['id'] for r in rows})==3200,'Exact3200 unique draws')
    classes=prepared['class_token_ids'];require(len(classes)==len(set(classes))==3 and all(type(v)==int and v>=0 for v in classes),'Actual three class IDs')
    counts=Counter();owners={};canonical={}
    for r in rows:
        sid=r['source_id'];a,b=r['a'],r['b'];pair=sorted((a,b));require(pair[0]==0 and 1<=pair[1]<=5 and r['unordered_pair']==pair,'Only registered connected star pairs')
        require(owners.get(sid,r['source_sha256'])==r['source_sha256'],'Conflicting source SHA');owners[sid]=r['source_sha256']
        y=r['target'];g=r['geometry_delta11'];require(type(y) in (int,float) and math.isfinite(y) and -1<=y<=1
            and len(g)==11 and all(math.isfinite(v) for v in g),'Finite original continuous target/geometry')
        value=(y if a==0 else -y,tuple(v if a==0 else -v for v in g));k=(sid,pair[1])
        require(canonical.get(k,value)==value,'Swap/repeat target changed');canonical[k]=value;counts[k]+=1
        for name in ('forward','reverse'):
            e=r[name];require(e['id']==r[name+'_id'] and e['source_id']==sid and e['source_sha256']==r['source_sha256']
                and set(e['input'])=={'path','sha256'},'Actual ordered request ownership')
        require(r['forward_id']!=r['reverse_id'],'Two real opposite-order owners')
    require(len(owners)==len(set(owners.values()))==602 and len(counts)==3010
        and all({b for sid,b in counts if sid==s}==set(range(1,6)) for s in owners),'602 complete five-edge source stars')
    require(Counter(counts.values())=={1:2820,2:190},'Fixed3010+190 empirical support')
    for r in rows:require(r['draw_weight']==3200/(3010*counts[r['source_id'],r['unordered_pair'][1]]),'Exact source/pair equal inverse draw mass')
    return rows,digest(rows),dict(sources=602,unordered_pairs=3010,micro=3200,source_pair_equal_empirical_objective=True,
        pair_draw_histogram=dict(Counter(counts.values())),train_target_RMS=TARGET_RMS,all_source_stars_connected=True,
        original55_STOP_preserved=True,individual_Adam_steps_are_not_equal_weight_solves=True)


def phase_steps(phase):
    require(phase in ('pilot4','remaining796'),'Only new4 engineering steps or explicit remaining796')
    return range(501,505) if phase=='pilot4' else range(505,1301)


def loss(predicted_gain,target,draw_weight,target_RMS):
    require(type(target) in (int,float) and math.isfinite(target) and -1<=target<=1
        and type(draw_weight) in (int,float) and math.isfinite(draw_weight) and draw_weight>0
        and target_RMS==TARGET_RMS,'Unchanged55 normalized continuous loss')
    return draw_weight*((predicted_gain-target)/target_RMS).square()
