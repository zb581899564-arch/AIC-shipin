"""New time-selector package contract; unchanged full-source spatial field."""
import subprocess
import sys
import zipfile
from pathlib import Path
from common import *


def lines(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def write_lines(path,rows):
    with Path(path).open('x',encoding='utf-8') as stream:
        for row in rows:stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')


def canonical(rows):
    values=[{key:r[key] for key in ('video_id','targetRatioWH','predictions')} for r in sorted(rows,key=lambda r:r['video_id'])]
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main():
    assert_cpu()
    import numpy as np
    require(read(ROOT/'official_rule_check.json')['approved_external_local_time_head_scope'] is True,'Current official rule binding required')
    require(sha(BASELINE)==BASELINE_SHA,'Protected40.47 archive changed')
    with zipfile.ZipFile(BASELINE) as z:
        require(z.namelist()==['predictions.jsonl'] and z.testzip() is None,'Protected baseline structure')
        baseline=[json.loads(line) for line in z.read('predictions.jsonl').splitlines()]
    b={(r['video_id'],p['frame']):p['bboxes'] for r in baseline for p in r['predictions']}
    origin=WORK/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'
    source=read(origin)
    manifest=read(checked(source['source_manifest']));metadata=read(checked(source['metadata']));clocks=read(checked(source['source_clocks']))
    field_refs=source['source_field_files'];field={name:lines(checked(ref)) for name,ref in field_refs.items()}
    field_rows=field['field_frames.jsonl'];field_map={(r['video_id'],r['source_frame']):r for r in field_rows}
    require(len(field_rows)==len(field_map),'Continuous spatial field duplicate source/frame')
    require(set(clocks)=={str(i) for i in range(426)},'All426 original native source clocks')
    sys.path[:0]=[str(RUN/'b_score_aligned_package_v4'),str(RUN/'baseline_a_pts_v1'),str(RUN/'baseline_a_pts_v1/vendor')]
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    history=set(read(PRODUCTION/'production_registration.json')['historical_prediction_sha256'])
    history.add(canonical(baseline))
    # Include every later delivered candidate's actual canonical, not merely renamed files.
    for completion in [WORK/'sprint45_global_context_20261016_v1/packages/GLOBAL_CONTEXT/completion.json',
                       WORK/'sprint45_global_context_20261016_v1/packages/EVENT_PAYOFF/completion.json',
                       WORK/'sprint45_width_packages_20261016_v1/C/completion.json',
                       WORK/'sprint45_consensus_veto_last_risk_20261016_v1/completion.json']:
        if completion.is_file():
            value=read(completion)
            for key in ('canonical_sha256','prediction_sha256'):
                if isinstance(value.get(key),str):history.add(value[key])
    history.update(read(ROOT/'protocol.json')['later_historical_canonical'])
    accepted=read(ROOT/'selection_completion.json');out=ROOT/'packages';out.mkdir(exist_ok=False);deliveries=[];rejected=[]
    for arm_ref in accepted['arms']:
        selection=read(checked(arm_ref));arm=selection['arm'];chosen_keys=set()
        require(len(selection['sources'])==426 and {r['id'] for r in selection['sources']}==set(clocks),'Complete successful426 selection statuses')
        require(selection['actual_resident_parameters']<=9_000_000_000,'Actual all-component parameter budget')
        for s in selection['sources']:
            clock=clocks[s['id']]
            require(s['source_sha256']==clock['source_sha256'] and
                    read(checked(s['clock']))['normalized_exact_pts']==clock['normalized_exact_pts'],
                    'New selection source bytes/native PTS differ from target clock')
            value=np.load(checked(s['output']));mask=value['selected_native']
            require(mask.dtype==np.bool_ and len(mask)==clock['n_frames'] and s['status'] in ['ACCEPTED','ACCEPTED_EMPTY'],
                    'Failed or incomplete output must not become empty')
            head=read(checked(selection['head']))
            require(np.array_equal(mask,value['group_probability'][value['native_group']]>head['threshold']), 'Independent final exact native replay')
            chosen_keys.update((s['id'],int(i)) for i in np.flatnonzero(mask))
        require(chosen_keys<=field_map.keys(),'New selected frame outside the frozen full spatial domain; never silently filter')
        chosen=[field_map[k] for k in sorted(chosen_keys)]
        predictions,provenance=compose_from_field(legacy_manifest(manifest),chosen,field['field_shots.jsonl'],
                                                 field['anchor_requests.jsonl'],field['anchor_output.jsonl'])
        for row in predictions:row['model_params_b']=selection['actual_resident_parameters']/1e9
        n={(r['video_id'],p['frame']):p['bboxes'] for r in predictions for p in r['predictions']}
        require(len(predictions)==426 and {r['video_id'] for r in predictions}==set(clocks) and set(n)==chosen_keys,'Exact426/native mask package identity')
        require(all(n[k]==b[k] for k in n.keys()&b.keys()),'Shared baseline frame boxes changed')
        digest=canonical(predictions)
        if digest in history:
            rejected.append(dict(arm=arm,status='STOP_IDENTICAL_PREDICTION_NO_RENAMED_PACKAGE',canonical=digest));continue
        dst=out/arm;dst.mkdir()
        write_lines(dst/'predictions.jsonl',predictions);write_lines(dst/'selected.jsonl',chosen);write_lines(dst/'provenance.jsonl',provenance);write(dst/'metadata.json',metadata)
        pending=dst/('candidate_TEMPORAL_SELECTOR_'+arm+'.PENDING.zip')
        with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:z.write(dst/'predictions.jsonl','predictions.jsonl')
        validator=RUN/'baseline_a_pts_v1/vendor/independent_validate.py'
        subprocess.run([sys.executable,str(validator),'--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
             '--metadata',str(dst/'metadata.json'),'--selected',str(dst/'selected.jsonl'),'--predictions',str(dst/'predictions.jsonl'),
             '--provenance',str(dst/'provenance.jsonl'),'--zip',str(pending),'--report',str(dst/'independent_validation.json')],check=True)
        checks=read(dst/'independent_validation.json')['checks'];require(len(checks)==11 and all(checks.values()),'Independent11strict')
        with zipfile.ZipFile(pending) as z:
            require(z.namelist()==['predictions.jsonl'] and z.testzip() is None and
                    hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==sha(dst/'predictions.jsonl'),'CRC and single-member SHA')
        final=dst/('candidate_TEMPORAL_SELECTOR_'+arm+'.zip');pending.rename(final)
        row=dict(status='PASS_ENGINEERING_NEW_TIME_SELECTOR_OFFICIAL_EFFECT_UNKNOWN',arm=arm,
                 zip=str(final),bytes=final.stat().st_size,sha256=sha(final),member_sha256=sha(dst/'predictions.jsonl'),
                 canonical_sha256=digest,records=426,frames=len(n),added=len(n.keys()-b.keys()),removed=len(b.keys()-n.keys()),
                 changed_sources=sum({p['frame'] for p in r['predictions']}!={p['frame'] for p in next(x for x in baseline if x['video_id']==r['video_id'])['predictions']} for r in predictions),
                 empty_sources=sum(not r['predictions'] for r in predictions),shared_baseline_boxes_unchanged=True,
                 actual_total_parameters=selection['actual_resident_parameters'],independent11strict=True,
                 time_selection=arm_ref,spatial_field_bindings=field_refs,website_submitted=False,
                 quality_scope='Historical public summary temporal proxy; no new blind or official joint validation',online_score='UNKNOWN')
        write(dst/'completion.json',row);deliveries.append(row);history.add(digest)
        event('NEW_TEMPORAL_PACKAGE_ENGINEERING_ACCEPTED',arm=arm,bytes=row['bytes'],frames=row['frames'],added=row['added'],removed=row['removed'])
    write(ROOT/'completion.json',dict(status='COMPLETE_NEW_TIME_SELECTOR_CANDIDATES_UNKNOWN_OFFICIAL_EFFECT',
          deliveries=deliveries,rejected_duplicates=rejected,baseline_sha256=BASELINE_SHA,
          achieved_score_improvement=False,website_submitted=False))


if __name__=='__main__':main()
