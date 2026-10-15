"""Fail-closed silver admission; reads PNG evidence, never native video/model."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import re
from quality_contract import reference, duration, normalize, schedule

KIND = 'CONTRAST_BOUNDARY_NATIVE_SILVER_V1'
ROLES = ('train', 'process_dev', 'locked_evaluation')
COUNTS = {'train': {'groups': 16, 'windows': 64},
          'process_dev': {'groups': 4, 'windows': 16},
          'locked_evaluation': {'groups': 4, 'windows': 16},
          'total_windows': 96, 'evaluation_windows': 32, 'evaluation_model_calls': 64,
          'optimizer_updates': 32, 'examples_backward': 128}


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as s:
        for b in iter(lambda: s.read(8 << 20), b''): h.update(b)
    return h.hexdigest()


def byte_bound(binding):
    need(set(binding) == {'path', 'sha256'}, 'exact path/SHA required')
    p = Path(binding['path']).resolve(strict=True)
    need(p.is_file() and sha(p) == binding['sha256'], 'evidence bytes differ: '+str(p))
    return p


def read_bound(binding):
    return json.loads(byte_bound(binding).read_text(encoding='utf-8-sig'))


def verified_rgb_png(binding, size):
    from PIL import Image
    path=byte_bound(binding)
    try:
        with Image.open(path) as image:
            need(image.format=='PNG' and image.mode=='RGB' and image.size==size,'PNG RGB geometry differs')
            image.verify()
        with Image.open(path) as image:
            image.load(); result=image.copy()
    except (OSError,SyntaxError) as exc:
        raise ValueError('invalid PNG evidence: '+str(path)) from exc
    need(sha(path)==binding['sha256'],'PNG changed during pixel verification')
    return result


def same_tool_path(a,b):
    def normalized(x):
        need(isinstance(x,str) and x,'actual absolute tool path required')
        text=x.replace('\\','/').rstrip('/')
        need(text.startswith('/') or (len(text)>2 and text[1:3]==':/'),'absolute tool path required')
        return text.casefold() if len(text)>1 and text[1]==':' else text
    return normalized(a)==normalized(b)


def raw_image_metadata_visible(value):
    if isinstance(value,dict):
        if value.get('type')=='image' or any(k in value for k in ('image_url','image_data','image_bytes','images')):
            return True
        if 'width' in value and 'height' in value and any(k in value for k in ('mime_type','mimeType','format')):
            return True
        return any(raw_image_metadata_visible(v) for v in value.values())
    if isinstance(value,list):return any(raw_image_metadata_visible(v) for v in value)
    return False


def structured_tool_failure(value):
    if isinstance(value,dict):
        if any(value.get(k) for k in ('error','error_message','errorMessage','isError')):return True
        if str(value.get('status','')).upper() in ('ERROR','FAILED','CANCELLED'):return True
        if value.get('success') is False:return True
        return any(structured_tool_failure(v) for v in value.values())
    if isinstance(value,list):return any(structured_tool_failure(v) for v in value)
    return False


def verify_teacher_stream(audit,sheets):
    observations=audit['sheet_observations']
    text=byte_bound(audit['original_stream']).read_text(encoding='utf-8-sig')
    rows=[json.loads(line) for line in text.splitlines() if line.strip()]
    need(rows,'actual NDJSON sheet stream required')
    for row in rows:
        need(isinstance(row,dict),'stream row must be structured JSON')
        step=row.get('step_update',{}); result=row.get('result',{})
        need(row.get('event') not in ('error','ERROR') and not row.get('error') and
             step.get('state') not in ('ERROR','FAILED','CANCELLED') and not step.get('error') and
             result.get('status') not in ('ERROR','FAILED','CANCELLED') and not result.get('error'),
             'teacher stream has real ERROR/failure')
    need(len(observations)==8,'exact eight actual sheet tool observations required')
    identities=set(); metadata=[]; blocks=[]
    for ix,obs in enumerate(observations):
        need(obs['sheet_index']==ix and obs['successful'] is True and
             obs['image_sha256']==sheets[ix]['image']['sha256'],'sheet observation identity differs')
        cid=obs['conversation_id']; index=obs['step_index']
        need(isinstance(cid,str) and cid and type(index) is int and index>=0,'real conversation/step identity required')
        need((cid,index) not in identities,'duplicate teacher sheet step identity');identities.add((cid,index))
        matches=[(line,row['step_update']) for line,row in enumerate(rows) if row.get('event')=='step_update' and
                 row.get('step_update',{}).get('conversation_id')==cid and row.get('step_update',{}).get('step_index')==index]
        need(len(matches)==2 and [v['state'] for _,v in matches]==['ACTIVE','DONE'],'one actual ACTIVE then DONE required')
        expected_path=sheets[ix].get('original_image_path',sheets[ix]['image']['path'])
        need(same_tool_path(obs['tool_image_path'],expected_path),'tool path differs from actual sheet source path')
        call_ids=[]
        for line,step in matches:
            info=step.get('tool_info',{})
            need(step.get('step_type')=='tool' and step.get('tool_name')=='view_file' and info.get('name')=='view_file',
                 'sheet observation must be actual view_file tool')
            path=info.get('parameters',{}).get('AbsolutePath')
            need(same_tool_path(path,obs['tool_image_path']),'ACTIVE/DONE tool image path differs')
            need(not info.get('error') and not info.get('isError'),'view_file result failed')
            output=info.get('output')
            need(not structured_tool_failure(output),'view_file DONE carries a structured failure')
            if isinstance(output,str):
                need(not re.search(r'(?i)\b(error|failed|not found|unsupported|could not|unable)\b',output),
                     'view_file DONE carries a textual failure')
            call_ids.append(step.get('tool_call_id',info.get('tool_call_id',rows[line].get('tool_call_id'))))
        exposed=any(v is not None for v in call_ids)
        need(obs['tool_call_id_exposed'] is exposed and call_ids[0]==call_ids[1] and
             obs['tool_call_id']==call_ids[0],'actual exposed/missing tool_call_id differs')
        if exposed:need(isinstance(call_ids[0],str) and call_ids[0],'empty raw tool_call_id')
        visible=raw_image_metadata_visible(matches[-1][1].get('tool_info',{}))
        need(obs['raw_image_metadata_visible'] is visible,'raw image metadata visibility claim differs')
        metadata.append(visible)
        def image_block(v):
            if isinstance(v,dict):return v.get('type')=='image' or any(k in v for k in ('image_url','image_data','image_bytes')) or any(image_block(t) for t in v.values())
            if isinstance(v,list):return any(image_block(t) for t in v)
            return False
        blocks.append(image_block(matches[-1][1].get('tool_info',{})))
    need(audit['image_block_claimed'] is any(blocks),'image-block/metadata claim must match raw stream')
    if not all(metadata):need(isinstance(audit['raw_image_metadata_limitations'],list) and
         bool(audit['raw_image_metadata_limitations']),'missing raw image metadata limitation must be explicit')
    return dict(successful_sheet_tools=8,raw_image_metadata_visible_count=sum(metadata),image_bytes_attention_proven=False)


def evidence_bindings(record):
    """Recursively return original evidence files, without media decoding."""
    for binding in record['evidence'].values():
        yield binding
    sheet = read_bound(record['evidence']['contact_sheet_manifest'])
    for row in sheet['frames']: yield row['png']
    for row in sheet['sheets']: yield row['image']
    audit = read_bound(record['evidence']['teacher_stream_audit'])
    yield audit['original_stream']


def validate_protocol(p):
    need(p['counts'] == COUNTS, 'registered contrast denominator differs')
    for name in ('epochs','seed','micro_batch','gradient_accumulation'):
        need(type(p[name]) is int,'integer recipe field required: '+name)
    need(p['epochs'] == 2 and p['seed'] == 20261011 and p['micro_batch'] == 1 and
         p['gradient_accumulation'] == 4, 'registered contrast training recipe differs')
    need(p['fixed_final_checkpoint_only'] is True and p['quality_failure_NO426_no_recipe_retuning'] is True,
         'final-only/no-retuning protocol absent')
    q = p['quality']
    need(q['locked_positive_macro_F1_gain_min'] == '0.05' and
         q['positive_empty_window_count_nonincrease'] is True and
         q['positive_locked_sources_min'] == 3 and
         q['strictly_improved_locked_sources_min'] == 2 and
         q['locked_complete_silver_min'] == 12 and
         q['locked_sources_with_at_least_5sec_no_min'] == 2, 'quality protocol differs')
    return p['counts']


def validate_plan(plan, protocol):
    counts = validate_protocol(protocol)
    jobs = {j['window']['window_id']: j for j in plan['jobs']}
    need(len(jobs) == len(plan['jobs']) == counts['total_windows'], 'full contrast denominator differs')
    source_role = {}; source_group = {}; domains = {}; group_source={}; quarter_indices={}; source_clock={}
    for key, j in jobs.items():
        role = j['role']; group = j['source_group']; w = j['window']; source = w['source_sha256']
        need(role in ROLES and key == w['window_id'], 'foreign role/identity')
        need(j['coverage_class'] in ('ordinary', 'mixed', 'highlight','unknown'), 'frozen coverage class missing')
        need(j['coverage_class']!='unknown' or role!='train','UNKNOWN coverage class cannot enter training')
        need(group not in source_role or source_role[group] == role, 'source group role leakage')
        need(source not in source_group or source_group[source] == group, 'same source split over groups')
        need(group not in group_source or group_source[group]==source,'multiple source SHA in one group')
        group_source[group]=source
        source_role[group] = role; source_group[source] = group
        a, b = F(w['domain_start_exact']), F(w['domain_end_exact'])
        need(0 < b-a <= 30, 'quarter-end max30s contrast domain required')
        origin,span=F(w['source_origin_exact']),F(w['source_duration_exact'])
        ix=w['original_window_index']
        need(type(ix) is int and 0<=ix<4 and span>0,'source quarter identity missing')
        need(group not in source_clock or source_clock[group]==(origin,span),'same source clock differs across windows')
        source_clock[group]=(origin,span)
        quarter_start=origin+span*ix/4;quarter_end=origin+span*(ix+1)/4
        need(b==quarter_end and a==max(quarter_start,quarter_end-30),'frozen exact source-quarter domain differs')
        quarter_indices.setdefault(group,[]).append(ix)
        domains.setdefault(group, []).append((a, b))
    for role in ROLES:
        rows = [j for j in jobs.values() if j['role'] == role]
        need(len(rows) == counts[role]['windows'] and len({j['source_group'] for j in rows}) == counts[role]['groups'],
             'role source/window denominator differs: '+role)
        need({'ordinary', 'mixed'} <= {j['coverage_class'] for j in rows}, 'ordinary/mixed coverage absent: '+role)
    for group, rows in domains.items():
        rows.sort()
        need(len(rows) == 4 and sorted(quarter_indices[group])==list(range(4)) and all(b <= c for (_, b), (c, _) in zip(rows, rows[1:])),
             'four nonoverlapping fixed windows per source required')
    return jobs


def verify_contact_sheet_manifest(sheet,w):
    frames=sheet['frames'];sheets=sheet['sheets']
    need(sheet['source_rgb_unscaled'] is True and len(frames) == 64 and len(sheets) == 8, 'sourceRGB 64/8 delivery differs')
    ids = w['planned_source_frame_ordinals']; pts = list(map(F,w['planned_exact_pts']))
    need([r['ordinal'] for r in frames] == ids and [F(r['pts_exact']) for r in frames] == pts, 'contact sheet native identity differs')
    images=[]
    for r in frames:
        need(r['width'] == w['width'] and r['height'] == w['height'] and
             len(r['pixel_sha256']) == 64, 'original RGB geometry/SHA missing')
        image=verified_rgb_png(r['png'],(w['width'],w['height']))
        need(hashlib.sha256(image.tobytes()).hexdigest()==r['pixel_sha256'],'actual original PNG pixels differ from declared SHA')
        images.append(image)
    for ix, r in enumerate(sheets):
        need(r['index'] == ix and r['frame_ordinals'] == ids[ix*8:(ix+1)*8] and F(r['scale_exact']) == 1,
             'sheet order/scale differs')
        width,height=w['width'],w['height']
        image=verified_rgb_png(r['image'],(width*2,(height+26)*4))
        for tile in range(8):
            x=(tile%2)*width;y=(tile//2)*(height+26)+26
            need(image.crop((x,y,x+width,y+height)).tobytes()==images[ix*8+tile].tobytes(),
                 'sheet tile must equal original unscaled source PNG pixels')
    return dict(source_pngs_pixel_verified=64,unscaled_sheet_tiles_verified=64,sheets_pixel_verified=8,header_pixels_per_row=26)


def verify_window(record, planned):
    w = planned['window']; a, b = F(w['domain_start_exact']), F(w['domain_end_exact'])
    need(record['window_id'] == w['window_id'] and record['source_sha256'] == w['source_sha256'], 'reference identity differs')
    need(record.get('reference_kind') == KIND and not record.get('example_only'), 'contrast silver kind required')
    d, keep, no, unknown = reference([(a,b)], record['keep_global_exact'], record['no_global_exact'], record['unknown_global_exact'])
    names = {'contact_sheet_manifest','teacher_stream_audit','blind_initial','student_processor','final_main_review'}
    need(set(record['evidence']) == names, 'exact contrast evidence workflow required')
    ev = {k: read_bound(v) for k,v in record['evidence'].items()}
    for name in names - {'student_processor'}:
        need(ev[name]['window_id'] == w['window_id'] and ev[name]['source_sha256'] == w['source_sha256'], 'foreign evidence: '+name)
    sheet = ev['contact_sheet_manifest']; frames = sheet['frames']; sheets = sheet['sheets']
    ids=w['planned_source_frame_ordinals']
    contact_acceptance=verify_contact_sheet_manifest(sheet,w)
    audit = ev['teacher_stream_audit']; observations = audit['sheet_observations']
    need(not audit['tool_issues'] and audit['old_workflow_claimed'] is False and
         audit['native_video_delivered'] is False and len(observations) == 8, 'actual sheet workflow differs')
    stream_acceptance=verify_teacher_stream(audit,sheets)
    blind = ev['blind_initial']
    need(blind['blind_attestation']['teacher_content_received'] is False and
         blind['blind_attestation']['candidate_prediction_received'] is False and
         blind['independent_semantic_review_complete'] is True, 'independent preteacher review incomplete')
    student = ev['student_processor']
    need(student['patch_inverse_exact'] is True and len(student['frames']) == 64 and
         student['evidence']['source_frame_ids'] == ids and
         student['evidence']['frame_pixel_sha256'] == [r['pixel_sha256'] for r in frames] and
         len(student['normalized_tensor_sha256']) == 64 and 0 < student['input_tokens'] <= 16384,
         'actual visible student64 input binding differs')
    final = ev['final_main_review']
    need(final['reviewer_role'] == 'root' and all(final.get(k) is True for k in
         ('teacher_stream_reviewed','preteacher_independent_review_crosschecked',
          'no_candidate_prediction_exposure_before_reference_freeze','complete_partition_reviewed')), 'root cross adjudication incomplete')
    required = ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented',
                'necessary_preparation_and_result_considered','no_artificial_event_merging',
                'no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')
    need(all(record.get('main_review_assertions',{}).get(k) is True for k in required), 'semantic review assertions missing')
    events = record['events']; need(len(events) <= 5, 'fixed grammar event count exceeded')
    need(len({e['event_id'] for e in events}) == len(events), 'duplicate event identity')
    event_ranges = []
    expected_boundaries = set()
    for e in events:
        x,y = map(F,e['local']); need(0 <= x < y <= b-a and e['visible_reason'], 'event exact interval/reason missing')
        event_ranges.append((a+x,a+y))
        expected_boundaries.update(((e['event_id'],'start',a+x),(e['event_id'],'end',a+y)))
    need(normalize(event_ranges) == keep, 'complete events must equal KEEP')
    actual_boundaries = []
    for r in record['boundary_decisions']:
        x,y,z = F(r['uncertainty_start_exact']),F(r['uncertainty_end_exact']),F(r['boundary_global_exact'])
        need(a <= x <= z <= y <= b and y-x <= F('0.5') and r['inside_evidence'] and
             r['outside_evidence_or_domain_boundary'], 'exact boundary bracket/support differs')
        actual_boundaries.append((r['event_id'],r['side'],z))
    need(len(actual_boundaries) == len(set(actual_boundaries)) and set(actual_boundaries) == expected_boundaries,
         'every KEEP boundary needs exactly one adjudicated bracket')
    pure_no=not keep and not unknown and no==d
    need(type(record['explicit_no_highlight']) is bool and pure_no==record['explicit_no_highlight'], 'pure NO/UNKNOWN empty semantics differ')
    coverage = planned['coverage_class']
    need(coverage!='highlight' or duration(keep)>0,'highlight coverage needs confirmed KEEP')
    need(coverage!='unknown' or (planned['role']!='train' and duration(unknown)>0 and record.get('training_admitted') is not True),
         'unknown coverage is evaluation-only and requires actual UNKNOWN')
    need(coverage != 'mixed' or (duration(keep)>0 and duration(no)>=5), 'mixed window lacks KEEP/ordinary coverage')
    need(coverage != 'ordinary' or (not keep and not unknown and no==d and record['explicit_no_highlight'] is True),
         'ordinary requires complete explicit pure NO')
    if record.get('training_admitted'):
        need(planned['role'] == 'train' and not unknown and not record['consequential_unknowns'], 'UNKNOWN/evaluation cannot enter SFT')
        need(record['student_observable_complete_target'] is True and record['all_target_boundaries_adjudicated'] is True,
             'student complete target/boundaries not admitted')
    return dict(window_id=w['window_id'],role=planned['role'],source_group=planned['source_group'],
                admitted=record.get('training_admitted') is True,known_keep_seconds=duration(keep),
                known_no_seconds=duration(no),unknown_seconds=duration(unknown),teacher_stream_acceptance=stream_acceptance,contact_sheet_acceptance=contact_acceptance)


def training_schedule(plan, records, protocol):
    jobs = validate_plan(plan, protocol)
    need(set(records) == set(jobs), 'all contrast denominators must be recorded')
    accepted = []
    for key,j in jobs.items():
        if j['role'] == 'train':
            need(records[key].get('training_admitted') is True, 'all fixed training windows must be admitted')
            r = verify_window(records[key],j)
            accepted.append((key,j['source_group'],r['known_keep_seconds']>0))
        else: need(records[key].get('training_admitted') is not True, 'evaluation source admitted to SFT')
    need(len({g for _,g,p in accepted if p}) >= 12, 'at least twelve positive training sources required')
    for cls,min_windows,min_groups in (('ordinary',8,4),('mixed',16,8)):
        rows=[jobs[k] for k,_,_ in accepted if jobs[k]['coverage_class']==cls]
        need(len(rows)>=min_windows and len({j['source_group'] for j in rows})>=min_groups, 'training coverage insufficient: '+cls)
    accepted.sort(); s = schedule([g for _,g,_ in accepted],protocol['epochs'],protocol['seed'])
    need(s['updates'] == protocol['counts']['optimizer_updates'] and
         sum(len(b['indices']) for b in s['batches']) == protocol['counts']['examples_backward'], 'computed training denominator differs')
    return dict(window_ids=[k for k,_,_ in accepted],**s)
