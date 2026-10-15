"""Linux-only new risk packages; original scientific FAILED evidence unchanged."""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import traceback
import zipfile
from pathlib import Path
from transform import ARMS,transform,write
from check_transform import verify

ROOT=Path('/home/inspur/aic_video_work/rapid_risk_three_20261013_v1/recovery_01')
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')

def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]

def main():
    p=read(ROOT/'protocol.json');rule=read(ROOT/'official_rule_check.json');auth=read(ROOT/'authorization.json')
    if auth['authority_kind']!='DIRECT_HUMAN_EXPLORATORY_RISK_DELIVERY' or auth['old_scientific_gates_changed']:raise ValueError('explicit risk authority')
    save(ROOT/'started.json',{'pid':os.getpid(),'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'CPU_only':True,'no_model_calls':True})
    baseline_zip=ROOT/'control/baseline_D8.zip'
    if sha(baseline_zip)!=p['baseline']['zip_SHA256']:raise ValueError('D8 ZIP changed')
    with zipfile.ZipFile(baseline_zip) as z:
        if z.namelist()!=['predictions.jsonl'] or z.testzip()!=None:raise ValueError('baseline CRC/member')
        raw=z.read('predictions.jsonl')
    if hashlib.sha256(raw).hexdigest()!=p['baseline']['member_SHA256']:raise ValueError('baseline predictions')
    base=[json.loads(x) for x in raw.splitlines()];wanted={(r['video_id'],v['frame']) for r in base for v in r['predictions']}
    if len(base)!=426 or len(wanted)!=122050:raise ValueError('baseline426/122050')
    metadata_path=RUN/'b_score_aligned_package_v4/rematch_01/metadata.json';metadata=read(metadata_path);meta={r['video_id']:r for r in metadata['records']}
    if len(meta)!=426 or set(meta)!={str(i) for i in range(426)}:raise ValueError('source metadata denominator')
    source=RUN/'b_score_aligned_package_v4/rematch_01'
    binding=read(ROOT/'control/source_binding.json')
    dependencies={str(metadata_path):sha(metadata_path)}
    for name,digest in binding['source_field_files'].items():
        if sha(source/name)!=digest:raise ValueError('original field binding changed '+name)
        dependencies[str(source/name)]=digest
    for name,digest in [('manifest',binding['original_source_manifest']['manifest_sha256']),('registry',binding['original_source_manifest']['registry_sha256'])]:
        q=Path(binding['original_source_manifest'][name]);
        if sha(q)!=digest:raise ValueError('source native identity binding changed')
        dependencies[str(q)]=digest
    # Bind new output to the existing field at exactly the existing native frames.
    sys.path[:0]=[str(RUN/'b_score_aligned_package_v4'),str(RUN/'baseline_a_pts_v1/vendor')]
    from p2j_core import group_shots,anchor_frames,interpolate_box
    shots=group_shots(rows(source/'field_shots.jsonl'));outputs={(r['video_id'],r['source_frame']):r for r in rows(source/'anchor_output.jsonl')}
    field_records={(r['video_id'],r['source_frame']):r for r in rows(source/'field_frames.jsonl')}
    oldmap={(r['video_id'],v['frame']):v['bboxes'] for r in base for v in r['predictions']};selected=[];origin={}
    for shotid,shot in enumerate(shots):
        vid=shot[0]['video_id'];ids=[r['source_frame'] for r in shot]
        anchors={f:outputs[(vid,f)]['box_xyw'] for f in anchor_frames(ids,8)}
        for frame_row in shot:
            f=frame_row['source_frame'];key=(vid,f)
            if key not in wanted:continue
            box,provenance=interpolate_box(f,anchors)
            if box!=oldmap[key]:raise ValueError('D8 original bbox differs from frozen automatic field')
            m=meta[vid]
            native=field_records[key]
            if (native['source_path']!=m['source_path'] or native['source_n_frames']!=m['n_frames'] or native['source_width']!=m['width'] or native['source_height']!=m['height'] or native['target_ratio_wh']!=m['targetRatioWH']):raise ValueError('source-frame provenance')
            selected.append({'video_id':vid,'source_frame':f})
            origin[key]={'video_id':vid,'source_frame':f,'shot_id':shotid,'legal':True,**provenance,
                'upstream_original_box_xyw':box,'original_field_anchor_output_SHA256':binding['source_field_files']['anchor_output.jsonl']}
    if set(origin)!=wanted:raise ValueError('D8 frame field coverage')
    write(ROOT/'selected.jsonl',selected);save(ROOT/'metadata.json',metadata)
    dependencies.update({str(f):sha(f) for f in (ROOT/'code').glob('*.py')})
    dependencies.update({str(ROOT/n):sha(ROOT/n) for n in ['protocol.json','authorization.json','official_rule_check.json','control/baseline_D8.zip','control/source_binding.json']})
    save(ROOT/'source_lock.json',{'files':dependencies,'D8_frames_retained':122050,'model_parameters':8782459120,'new_models':0,'risk_status':'UNVALIDATED_NOT_OLD_GATE_PASS'})
    # External20 developer diagnostic: reuse original answers; no model/replay repeated.
    devroot=Path('/home/inspur/aic_video_work/gnmc_width_iteration_20261013_v1')
    ext=[json.loads(x) for x in (devroot/'recovery_01/screen/predictions.jsonl').read_text().splitlines()]
    extmeta={r['item_id']:r for r in read(devroot/'inputs.json')};refs={r['item_id']:r for r in read(devroot/'reference/labels.json')}
    def iou(b,g):
        x,y,w=b;h=w*9/16;a,c,u,v=g
        intersection=max(0,min(x+w,a+u)-max(x,a))*max(0,min(y+h,c+v)-max(y,c))
        return intersection/(w*h+u*v-intersection)
    diagnostics={}
    for arm in ARMS:
        deltas=[]
        for item in ext:
            old=item['baseline_box'];new=transform([{'targetRatioWH':[16,9],'predictions':[{'frame':0,'bboxes':old}]}],arm)[0]['predictions'][0]['bboxes']
            gt=refs[item['item_id']]['reference_xywh'];deltas.append(iou(new,gt)-iou(old,gt))
        diagnostics[arm]={'native16_static_developer_delta':sum(deltas)/len(deltas),'positive':sum(x>0 for x in deltas),
                         'worst_delta':min(deltas),'samples':20,'native9_human_validation':False,'independent_confirmation':False,'quality_gate_pass_claimed':False}
    save(ROOT/'external_developer_diagnostic.json',diagnostics)
    history=read(ROOT/'control/history.json')
    def canonical(values):
        relevant=[{'video_id':r['video_id'],'targetRatioWH':r['targetRatioWH'],'predictions':r['predictions']} for r in sorted(values,key=lambda x:x['video_id'])]
        return hashlib.sha256(json.dumps(relevant,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    completions=[];semantic_hashes={item['canonical_SHA256'] for item in history}
    for arm in ARMS:
        out=ROOT/arm;out.mkdir();values=transform(base,arm);geometric=verify(base,values,meta,arm)
        write(out/'predictions.jsonl',values)
        prov=[]
        for row in values:
            for v in row['predictions']:
                key=(row['video_id'],v['frame']);prov.append({**origin[key],'box_xyw':v['bboxes'],'postprocess':arm,
                     'postprocess_source_lock':sha(ROOT/'source_lock.json'),'neural_spatial_source_unchanged':True})
        write(out/'provenance.jsonl',prov);save(out/'geometry_validation.json',geometric)
        member=sha(out/'predictions.jsonl')
        semantic=canonical(values)
        if semantic in semantic_hashes or member==p['baseline']['member_SHA256']:raise ValueError('duplicate predictions')
        semantic_hashes.add(semantic)
        pending=out/f'candidate_{arm}_RISK.PENDING.zip'
        with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:z.write(out/'predictions.jsonl','predictions.jsonl')
        validator=RUN/'baseline_a_pts_v1/vendor/independent_validate.py';loader=RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'
        subprocess.run([sys.executable,str(validator),'--strict-loader-root',str(loader),'--metadata',str(ROOT/'metadata.json'),
            '--selected',str(ROOT/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
            '--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True,stdout=subprocess.DEVNULL)
        v=read(out/'independent_validation.json')
        if len(v['checks'])!=11 or not all(v['checks'].values()) or v['prediction_frames']!=122050:raise ValueError('independent11strict')
        with zipfile.ZipFile(pending) as z:
            if z.namelist()!=['predictions.jsonl'] or z.testzip()!=None or hashlib.sha256(z.read('predictions.jsonl')).hexdigest()!=member:raise ValueError('CRC/roundtrip')
        final=out/f'candidate_{arm}_RISK.zip';pending.rename(final)
        receipt={'status':'PASS_ENGINEERING_EXPLICIT_EXPLORATORY_RISK_UNVALIDATED_QUALITY','arm':arm,'zip':str(final),'bytes':final.stat().st_size,
           'SHA256':sha(final),'member_SHA256':member,'frame_count':122050,'same_D8_frames':True,'model_parameters':8782459120,
           'model_params_b':8.78245912,'changed_frames':geometric['changed_frames'],'changed_videos':geometric['changed_videos'],
           'minimum_old_new_IoU':geometric['minimum_original_new_IoU'],'independent11strict':True,'CRC':'PASS',
           'official_score':'UNKNOWN','quality_validated':False,'old_scientific_gates_changed':False,'new_model_calls':0,'new_training':0,
           'source_lock_SHA256':sha(ROOT/'source_lock.json'),'canonical_SHA256':semantic,'distinct_from_all_history':True,
           'external_developer_diagnostic':diagnostics[arm]}
        save(out/'completion.json',receipt);completions.append(receipt);print('READY',arm,json.dumps(receipt),flush=True)
    save(ROOT/'completion.json',{'status':'THREE_NEW_EXPLICIT_RISK_ZIPS_READY_NOT_QUALIFIED_RESEARCH','packages':completions,
          'historical_qualified_goal_remains_2of3':True,'new_old_goal_pass_claimed':False})

if __name__=='__main__':
    try:main()
    except Exception as e:
        if not (ROOT/'failure.json').exists():save(ROOT/'failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'preserve_success':True})
        raise
