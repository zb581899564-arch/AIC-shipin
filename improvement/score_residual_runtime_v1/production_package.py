"""Conditional renderer over frozen continuous spatial field; one final ZIP."""
import sys
import subprocess
import zipfile
from common_runtime import *

def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]

def jsonlines(p,rows):
    with Path(p).open('x',encoding='utf8') as f:
        for row in rows:f.write(json.dumps(row,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n')

def canonical(rows):
    relevant=[{k:r[k] for k in ('video_id','targetRatioWH','predictions')} for r in sorted(rows,key=lambda x:x['video_id'])]
    return hashlib.sha256(json.dumps(relevant,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def main():
    import numpy as np
    reg=read(ROOT/'production_registration.json');done=read(ROOT/'head_output_acceptance.json')
    require(done['status']=='PASS_FROZEN_HEAD_ALL426_FIRST_NATIVE_OUTPUT_REPLAY','Incomplete head inference/replay')
    require(read(ROOT/'official_rule_check_before_package.json')['approved_automatic_external_trained_head_scope'] is True,'Current rules required')
    old=WORK/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3';inputs=read(old/'package_inputs.json')
    field_paths={}
    for name,ref in inputs['source_field_files'].items():
        require(sha(ref['path'])==ref['sha256'],'Accepted continuous field changed');field_paths[name]=ref['path']
    field=lines(field_paths['field_frames.jsonl']);field_map={(r['video_id'],r['source_frame']):r for r in field}
    require(len(field)==len(field_map),'Duplicate field provenance')
    # Available spatial field is a frozen engineering domain, never a label or
    # outcome-dependent filter. New space inference is outside this head's scope.
    selected=set();outside_field=0
    for s in done['sources']:
        p=ROOT/'head_outputs'/s['id']/'output.npz';require(sha(p)==s['sha256'],'Frozen head outputs changed')
        pred=np.load(p)['selected_native']
        for frame in np.flatnonzero(pred).tolist():
            key=(s['id'],frame)
            if key in field_map:selected.add(key)
            else:outside_field+=1
    meta=read(ROOT/'metadata.json')
    source_manifest=read(inputs['source_manifest']['path'])
    require(sha(inputs['source_manifest']['path'])==inputs['source_manifest']['sha256'],'Original source manifest changed')
    sys.path[:0]=[str(RUN/'b_score_aligned_package_v4'),str(RUN/'baseline_a_pts_v1'),str(RUN/'baseline_a_pts_v1/vendor')]
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    chosen=[field_map[k] for k in sorted(selected)]
    predictions,provenance=compose_from_field(legacy_manifest(source_manifest),chosen,lines(field_paths['field_shots.jsonl']),lines(field_paths['anchor_requests.jsonl']),lines(field_paths['anchor_output.jsonl']))
    for r in predictions:r['model_params_b']=done['actual_resident_parameters']/1e9
    with zipfile.ZipFile(reg['baseline']['path']) as z:base=[json.loads(x) for x in z.read('predictions.jsonl').splitlines()]
    b={(r['video_id'],p['frame']):p['bboxes'] for r in base for p in r['predictions']}
    n={(r['video_id'],p['frame']):p['bboxes'] for r in predictions for p in r['predictions']}
    require(set(r['video_id'] for r in predictions)=={str(i) for i in range(426)} and len(predictions)==426,'Complete 426 records')
    require(set(n)==selected and set(b)<=set(n) and all(n[k]==b[k] for k in set(n)&set(b)),'Actual selected field or retained baseline box mismatch')
    semantic=canonical(predictions)
    history=set(reg['historical_prediction_sha256']);history.add(canonical(base))
    require(semantic not in history,'No actual new prediction; do not rename old package')
    out=ROOT/'package';out.mkdir(exist_ok=False)
    jsonlines(out/'predictions.jsonl',predictions);jsonlines(out/'selected.jsonl',chosen);jsonlines(out/'provenance.jsonl',provenance);write(out/'metadata.json',meta)
    p=out/'candidate_SCORE_RESIDUAL.PENDING.zip'
    with zipfile.ZipFile(p,'x',zipfile.ZIP_DEFLATED) as z:z.write(out/'predictions.jsonl','predictions.jsonl')
    validator=RUN/'baseline_a_pts_v1/vendor/independent_validate.py'
    subprocess.run([sys.executable,str(validator),'--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),'--zip',str(p),'--report',str(out/'independent_validation.json')],check=True)
    validation=read(out/'independent_validation.json');require(len(validation['checks'])==11 and all(validation['checks'].values()),'Independent11strict failed')
    with zipfile.ZipFile(p) as z:require(z.namelist()==['predictions.jsonl'] and z.testzip() is None and hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==sha(out/'predictions.jsonl'),'ZIP CRC/member SHA')
    final=out/'candidate_SCORE_RESIDUAL.zip';p.rename(final)
    write(out/'completion.json',dict(status='PASS_ENGINEERING_PROXY_QUALIFIED_NEW_HEAD_ZIP_OFFICIAL_SCORE_UNKNOWN',zip=str(final),bytes=final.stat().st_size,sha256=sha(final),member_sha256=sha(out/'predictions.jsonl'),canonical_sha256=semantic,records=426,frames=len(n),added=len(set(n)-set(b)),removed=len(set(b)-set(n)),empty_sources=sum(not r['predictions'] for r in predictions),automatic_field_domain_excluded_frames=outside_field,retained_boxes_unchanged=True,actual_resident_parameters=done['actual_resident_parameters'],independent11strict=True,website_submitted=False,official_score='UNKNOWN',scope='Historically exposed external human summary proxy; no official joint quality claim'))

if __name__=='__main__':main()
