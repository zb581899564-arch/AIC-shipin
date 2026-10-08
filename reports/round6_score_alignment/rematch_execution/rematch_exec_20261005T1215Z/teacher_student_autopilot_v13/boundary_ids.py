"""Program-owned exact native-PTS boundary and separate physical evidence IDs.

The model selects IDs. It never serializes timestamps or observation metadata.
The terminal boundary has no physical frame and is never an evidence ID.
"""
from fractions import Fraction
import hashlib
import json
import math


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()


def tables(observation):
    origin = Fraction(str(observation['window_pts_start_sec']))
    duration = Fraction(str(observation['window_duration_sec']))
    points = observation['actual_pts_sec']
    ordinals = observation['source_frame_ordinals']
    require(duration > 0 and points and len(points) == len(ordinals), 'native observation table missing')
    require(all(type(p) in (int, float) and math.isfinite(p) for p in points), 'finite native PTS required')
    require(all(a < b for a, b in zip(points, points[1:])), 'native evidence PTS must increase strictly')
    local = [Fraction(str(p)) - origin for p in points]
    require(all(0 <= p < duration for p in local), 'native evidence outside canonical local window')
    values = sorted(set([Fraction(0), *local, duration]))
    boundary = []
    for index, value in enumerate(values):
        evidence = [i for i, point in enumerate(local) if point == value]
        boundary.append({'boundary_id': index, 'local_seconds': float(value),
            'local_seconds_fraction': str(value), 'source_pts_fraction': str(origin + value),
            'evidence_frame_ids': evidence, 'terminal_without_frame': value == duration})
    frames = [{'evidence_frame_id': i, 'source_frame_ordinal': ordinal,
        'source_pts_sec': points[i], 'source_pts_fraction': str(Fraction(str(points[i]))),
        'local_seconds_fraction': str(local[i]),
        'boundary_id': values.index(local[i])} for i, ordinal in enumerate(ordinals)]
    return {'schema': 'aic_native_boundary_ids_v1', 'window_id': observation['window_id'],
        'boundary_ids': boundary, 'evidence_frames': frames,
        'window_duration_fraction': str(duration), 'program_owned_metadata': True,
        'sampling_gaps_are_unknown': True, 'terminal_boundary_is_not_evidence': True}


def schema(observation):
    import copy
    table=tables(observation)
    evidence={'type':'array','minItems':1,'maxItems':len(table['evidence_frames']),'uniqueItems':True,
        'items':{'type':'string','enum':['F'+str(i) for i in range(len(table['evidence_frames']))]}}
    segment={'type':'object','additionalProperties':False,
        'required':['start_boundary_id','end_boundary_id','evidence_frame_ids'],'properties':{
            'start_boundary_id':{'type':'string','enum':['B'+str(i) for i in range(len(table['boundary_ids']))]},
            'end_boundary_id':{'type':'string','enum':['B'+str(i) for i in range(len(table['boundary_ids']))]},
            'evidence_frame_ids':evidence}}
    base={'type':'object','additionalProperties':False,'required':['state','segments','evidence_frame_ids','reason'],
        'properties':{'state':{'type':'string'},'segments':{'type':'array','maxItems':5,'items':segment},
            'evidence_frame_ids':evidence,'reason':{'type':'string','minLength':1,'maxLength':600}}}
    branches=[]
    for state in ('KEEP','NO_HIGHLIGHT','UNKNOWN'):
        branch=copy.deepcopy(base);branch['properties']['state']={'const':state}
        if state=='KEEP':
            branch['properties']['segments']['minItems']=1
            branch['properties']['evidence_frame_ids']={'type':'array','maxItems':0}
        else:branch['properties']['segments']['maxItems']=0
        branches.append(branch)
    return {'anyOf':branches}


def native_pair_domain(observation):
    table=tables(observation)
    positions=[Fraction(point['local_seconds_fraction']) for point in table['boundary_ids']]
    frames=[Fraction(point['local_seconds_fraction']) for point in table['evidence_frames']]
    return [(a,e) for a in range(len(positions)) for e in range(a+1,len(positions))
        if any(positions[a]<=point<positions[e] for point in frames)]


def physical_evidence_domain(observation,a,e):
    table=tables(observation)
    start,end=[Fraction(table['boundary_ids'][i]['local_seconds_fraction']) for i in (a,e)]
    return [f['evidence_frame_id'] for f in table['evidence_frames']
        if start<=Fraction(f['local_seconds_fraction'])<end]


def grammar_rules(observation):
    """Finite DAG: every ordered 1..5 interval and every local nonempty F subset."""
    table=tables(observation);pairs=native_pair_domain(observation);pair_set=set(pairs)
    positions=[Fraction(point['local_seconds_fraction']) for point in table['boundary_ids']]
    physical=[Fraction(point['local_seconds_fraction']) for point in table['evidence_frames']]
    ends=sorted({end for _,end in pairs});rules={}
    token=lambda value:json.dumps(json.dumps(value))
    def evidence(lo,hi):
        name=f'ev-{lo}-{hi}'
        if name not in rules:
            first=token('F'+str(lo))+' space'
            rest=evidence(lo+1,hi) if lo<hi else None
            rules[name]=first+(' ("," space '+rest+')? | '+rest if rest else '')
        return name
    def pair(a,end):
        name=f'pair-{a}-{end}'
        if name not in rules:
            frames=[i for i,point in enumerate(physical) if positions[a]<=point<positions[end]]
            require(frames and frames==list(range(frames[0],frames[-1]+1)),'physical evidence domain must be contiguous')
            rules[name]=('"{" space '+token('start_boundary_id')+' space ":" space '+token('B'+str(a))
                +' space "," space '+token('end_boundary_id')+' space ":" space '+token('B'+str(end))
                +' space "," space '+token('evidence_frame_ids')+' space ":" space "[" space '
                +evidence(frames[0],frames[-1])+' "]" space "}" space')
        return name
    def span(minimum,end):
        name=f'span-{minimum}-{end}'
        if name not in rules:
            if minimum>=end:return None
            rest=span(minimum+1,end)
            first=pair(minimum,end) if (minimum,end) in pair_set else None
            choices=[item for item in (first,rest) if item is not None]
            if not choices:return None
            rules[name]=' | '.join(choices)
        return name
    def sequence(remaining,minimum):
        name=f'seq-{remaining}-{minimum}'
        if name in rules:return name
        rules[name]='';alternatives=[]
        for end in ends:
            if end<=minimum:continue
            segment=span(minimum,end)
            if segment is None:continue
            tail=sequence(remaining-1,end) if remaining>1 else None
            alternatives.append(segment+(' ("," space '+tail+')?' if tail else ''))
        if not alternatives:del rules[name];return None
        rules[name]=' | '.join(alternatives);return name
    initial=sequence(5,0);require(initial is not None,'no physical native interval available for KEEP')
    all_evidence=evidence(0,len(table['evidence_frames'])-1)
    prefix='"{" space '+token('state')+' space ":" space '
    middle=' space "," space '+token('segments')+' space ":" space '
    ending=' space "," space '+token('reason')+' space ":" space reason space "}" space'
    global_field=' space "," space '+token('evidence_frame_ids')+' space ":" space '
    base={'root':'keep | no-highlight | unknown',
        'keep':prefix+token('KEEP')+middle+'"[" space '+initial+' "]"'+global_field+'"[" space "]"'+ending,
        'no-highlight':prefix+token('NO_HIGHLIGHT')+middle+'"[" space "]"'+global_field+'"[" space '+all_evidence+' "]"'+ending,
        'unknown':prefix+token('UNKNOWN')+middle+'"[" space "]"'+global_field+'"[" space '+all_evidence+' "]"'+ending,
        'reason':'"\\\"" char{1,600} "\\\"" space',
        'char':r'[^"\\\x7F\x00-\x1F] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F]{4})',
        'space':r'[ \t\n\r]*'}
    return {**base,**dict(sorted(rules.items()))}


def ordered_grammar(observation):
    return '\n'.join(name+' ::= '+body for name,body in grammar_rules(observation).items())+'\n'


def relation_contract(observation,grammar=None):
    grammar=ordered_grammar(observation) if grammar is None else grammar
    return {'schema':'aic_segment_local_evidence_generation_contract_v11',
        'grammar_sha256':hashlib.sha256(grammar.encode()).hexdigest(),'grammar_bytes':len(grammar.encode()),
        'grammar_rule_count':len(grammar.splitlines()),'boundary_table_sha256':digest(tables(observation)),
        'physical_pair_count':len(native_pair_domain(observation)),'all_legal_segment_counts':[1,2,3,4,5],
        'maximum_segments':5,'start_strictly_before_end':True,'next_start_at_least_previous_end':True,
        'each_half_open_interval_contains_provided_frame':True,'each_segment_selects_own_physical_evidence':True,
        'boundary_namespace':'B','evidence_namespace':'F','evidence_strictly_increasing_and_distinct':True,
        'all_nonempty_local_evidence_subsets_expressible':True,'KEEP_global_evidence_is_empty':True,
        'semantic_standard_unchanged':True,'answer_postprocessing_performed':False,
        'canonical_global_evidence_is_union_of_model_selected_segment_evidence_only':True}


def parse_id(value,prefix,limit):
    require(type(value) is str and value.startswith(prefix) and value[len(prefix):].isdigit(),prefix+' namespace ID required')
    number=int(value[len(prefix):])
    require(value==prefix+str(number) and 0<=number<limit,prefix+' ID outside physical namespace/range')
    return number


def selected_frames(values,count):
    require(isinstance(values,list) and values,'nonempty physical evidence IDs required')
    result=[parse_id(value,'F',count) for value in values]
    require(all(a<b for a,b in zip(result,result[1:])),'physical evidence IDs must be distinct and increasing')
    return result


def normalized_decision(value,observation):
    table=validate_decision(value,observation)
    segments=[];frames=[]
    for pair in value['segments']:
        selected=selected_frames(pair['evidence_frame_ids'],len(table['evidence_frames']))
        segments.append({'start_boundary_id':parse_id(pair['start_boundary_id'],'B',len(table['boundary_ids'])),
            'end_boundary_id':parse_id(pair['end_boundary_id'],'B',len(table['boundary_ids']))})
        frames.extend(selected)
    if value['state']!='KEEP':frames=selected_frames(value['evidence_frame_ids'],len(table['evidence_frames']))
    return {'state':value['state'],'segments':segments,'evidence_frame_ids':frames,'reason':value['reason']}


def validate_decision(value,observation):
    require(isinstance(value,dict) and set(value)=={'state','segments','evidence_frame_ids','reason'},'short decision fields differ')
    state=value['state'];require(state in ('KEEP','NO_HIGHLIGHT','UNKNOWN'),'unknown decision state')
    require(isinstance(value['reason'],str) and 0<len(value['reason'].strip())<=600,'short visible reason required')
    table=tables(observation);segments=value['segments']
    require(isinstance(segments,list) and len(segments)<=5,'bounded segment list required')
    require(bool(segments)==(state=='KEEP'),'KEEP requires segments; NO_HIGHLIGHT/UNKNOWN require none')
    if state=='KEEP':require(value['evidence_frame_ids']==[],'KEEP evidence must be selected inside each segment')
    else:selected_frames(value['evidence_frame_ids'],len(table['evidence_frames']))
    previous=Fraction(0)
    for pair in segments:
        require(isinstance(pair,dict) and set(pair)=={'start_boundary_id','end_boundary_id','evidence_frame_ids'},'segment-local evidence fields required')
        a,e=[parse_id(pair[key],'B',len(table['boundary_ids'])) for key in ('start_boundary_id','end_boundary_id')]
        require(a<e,'boundary IDs out of order/range')
        start,end=[Fraction(table['boundary_ids'][i]['local_seconds_fraction']) for i in (a,e)]
        require(start>=previous,'unordered or overlapping native boundary segments')
        contained=physical_evidence_domain(observation,a,e)
        require(contained,'half-open native interval contains no provided physical frame')
        frames=selected_frames(pair['evidence_frame_ids'],len(table['evidence_frames']))
        require(set(frames)<=set(contained),'every selected physical evidence frame must be inside its own KEEP segment')
        require(0<=float(start)<float(end)<=observation['window_duration_sec'],'student boundary conversion invalid')
        previous=end
    return table


def canonical_response(value,observation):
    table=validate_decision(value,observation);view=normalized_decision(value,observation);mapped=[]
    for pair in view['segments']:
        a,e=(table['boundary_ids'][pair[key]] for key in ('start_boundary_id','end_boundary_id'))
        mapped.append({'start_sec':a['local_seconds'],'end_sec':e['local_seconds'],'reason':value['reason']})
    unknown=value['state']=='UNKNOWN'
    return {'window_id':observation['window_id'],'observation_scope':{
        'window_pts_start_sec':observation['window_pts_start_sec'],'window_pts_end_exclusive_sec':observation['window_pts_end_exclusive_sec'],
        'sampled_pts_sec':observation['actual_pts_sec'],'all_provided_frames_reviewed':True},'retained_segments':mapped,
        'explicit_no_highlight':value['state']=='NO_HIGHLIGHT','uncertain':unknown,
        'uncertainty_reasons':[value['reason']] if unknown else [],'decision_reason':value['reason'],
        'boundary_notes':['PROGRAM_NATIVE_BOUNDARY_IDS; physical evidence IDs='+json.dumps(view['evidence_frame_ids']),
            'PROGRAM_DELIVERY_METADATA_ONLY; sampled gaps remain UNKNOWN; no model claim of every-frame comprehension']}


def prompt(template,observation):
    table=tables(observation)
    old='每段只有start_boundary_id、end_boundary_id，按顺序、非重叠，边界采用半开区间[start,end)。每段至少选一个真正显示相关事件的evidence_frame_id。'
    new='每段字段恰好为start_boundary_id、end_boundary_id、evidence_frame_ids，按顺序、非重叠，边界采用半开区间[start,end)。边界用B前缀字符串（如B0）；每段在自己的半开区间内至少选一个真正显示相关事件的F证据帧，evidence_frame_ids用F前缀字符串的非空递增列表（如["F3","F5"]）。KEEP的顶层evidence_frame_ids固定为空列表[]，表示证据逐段存放，不能借用其他片段的见证。'
    require(template.count(old)==1,'registered semantic template interface phrase differs')
    template=template.replace(old,new)
    template=template.replace('边界编号与证据帧编号是两种独立编号。','边界编号B与证据帧编号F是两种独立字符串编号；NO_HIGHLIGHT/UNKNOWN顶层evidence_frame_ids为所选F帧的非空递增列表。')
    contract={'output_interface':'aic_B_boundary_F_segment_local_evidence_v11','window_id':observation['window_id'],
        'local_window_duration_sec':observation['window_duration_sec'],'evidence_frame_count':len(table['evidence_frames']),
        'boundary_ids_in_time_order':['B'+str(point['boundary_id']) for point in table['boundary_ids']],
        'frame_to_boundary_id':[{'evidence_frame_id':'F'+str(f['evidence_frame_id']),'boundary_id':'B'+str(f['boundary_id'])}
            for f in table['evidence_frames']],'terminal_boundary_id':'B'+str(table['boundary_ids'][-1]['boundary_id']),
        'terminal_boundary_has_no_frame':True,'window_start_boundary_id':'B0'}
    require(template.count('{{WINDOW_CONTRACT_JSON}}')==1,'short prompt placeholder mismatch')
    return template.replace('{{WINDOW_CONTRACT_JSON}}',json.dumps(contract,ensure_ascii=False,sort_keys=True))
