"""Independent v4 packaging with measured current-model parameter inventory."""
import subprocess
import sys
import zipfile
from pathlib import Path

# Local source lives beside common.py; the deployed script lives in ROOT/package_04.
_HERE = Path(__file__).resolve().parent
_CODE = _HERE if (_HERE/'common.py').is_file() else _HERE.parent/'code'
if not (_CODE/'common.py').is_file() or not (_CODE/'head.py').is_file():
    raise RuntimeError('Cannot locate the original temporal-selector code directory')
sys.path.insert(0, str(_CODE))
from common import *


def lines(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def write_lines(path,rows):
    with Path(path).open('x',encoding='utf-8') as stream:
        for row in rows:stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')


def canonical(rows):
    values=[{key:r[key] for key in ('video_id','targetRatioWH','predictions')} for r in sorted(rows,key=lambda r:r['video_id'])]
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def parameter_inventory(selection, arm_ref):
    """Count the loaded new head and the already measured physical TIME model."""
    import torch
    from head import TemporalHead

    identity_path = ROOT/'pilot32_model_identity.json'
    measured = read(identity_path)
    identity = measured['identity']
    frozen = identity['logical_parameters']
    base = identity['base']['parameters']
    require(type(frozen) is int and frozen == 8782459120 and
            type(base) is int and base == 8767123696 and
            frozen-base == 15335424 and measured['model_parameters'] == frozen,
            'Actual frozen base+TIME inventory differs from successful measured model')
    head = read(checked(selection['head']))
    require(head['arm'] == selection['arm'] and head['feature_dim'] == 8192 and head['hidden'] == 128,
            'Frozen selected temporal head architecture/arm mismatch')
    weights_path = checked(head['weights'])
    state = torch.load(weights_path,map_location='cpu',weights_only=True)
    model = TemporalHead(head['feature_dim'],head['hidden'])
    model.load_state_dict(state,strict=True)
    model.eval()
    parameters = dict(model.named_parameters())
    require(set(state) == set(parameters) and not list(model.buffers()),
            'Temporal head state must contain exactly its actual parameters')
    tensors = {}
    for name, value in state.items():
        require(isinstance(value,torch.Tensor) and value.device.type == 'cpu' and
                value.is_floating_point() and bool(torch.isfinite(value).all()),
                'Nonfinite or invalid persisted temporal head parameter')
        key = (value.untyped_storage().data_ptr(), value.storage_offset(),
               tuple(value.shape), tuple(value.stride()), value.dtype)
        tensors.setdefault(key,value)
    state_count = sum(value.numel() for value in tensors.values())
    unique_parameters = {id(value):value for value in parameters.values()}
    head_count = sum(value.numel() for value in unique_parameters.values())
    require(state_count == head_count == model.parameter_count == 1147393 and
            head['head_parameters'] == head_count,
            'Actual loaded temporal head/state-dict parameter count mismatch')
    total = frozen+head_count
    require(total == 8783606513 and total <= 9_000_000_000,
            'Actual all-component parameter budget exceeded')
    require(head['frozen_parameters'] == 8782557449 and
            head['resident_parameters'] == head['frozen_parameters']+head_count and
            selection['actual_resident_parameters'] == head['resident_parameters'],
            'Preserved historical conservative budget differs from original training/selection')
    return dict(schema='ACTUAL_TEMPORAL_MODEL_PARAMETER_INVENTORY_V4',arm=selection['arm'],
                model_identity=reference(identity_path),head_training=selection['head'],
                selection=arm_ref,weights=head['weights'],
                components=dict(base=base,TIME=frozen-base,new_temporal_head=head_count),
                actual_frozen_parameters=frozen,actual_head_parameters=head_count,
                actual_unique_state_dict_parameters=state_count,
                actual_total_parameters=total,old_semantic_head_parameters_loaded=0,
                normalization_parameters=0,head_tensors=len(state),
                historical_conservative_frozen_parameters=head['frozen_parameters'],
                historical_conservative_resident_parameters=head['resident_parameters'],
                historical_records_modified=False,
                basis='Successful physical base+TIME inventory plus actual loaded TemporalHead; '
                      'old40.47 ZIP is comparison data, old semantic head is not loaded')


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
    # Use the registered exact paths and bytes; missing historical evidence blocks release.
    trajectory=read(WORK/'trajectory_risk_20261017_v1/registration.json')
    for completion_ref in trajectory['current_candidate_completions']:
        value=read(checked(completion_ref));digest=value['canonical_sha256']
        require(isinstance(digest,str) and len(digest)==64 and
                all(char in '0123456789abcdef' for char in digest),
                'Historical candidate completion lacks actual prediction canonical')
        history.add(digest)
    history.update(read(ROOT/'protocol.json')['later_historical_canonical'])
    accepted=read(ROOT/'selection_completion.json');out=ROOT/'packages';out.mkdir(exist_ok=False);deliveries=[];rejected=[]
    for arm_ref in accepted['arms']:
        selection=read(checked(arm_ref));arm=selection['arm'];chosen_keys=set()
        require(len(selection['sources'])==426 and {r['id'] for r in selection['sources']}==set(clocks),'Complete successful426 selection statuses')
        inventory=parameter_inventory(selection,arm_ref)
        actual_parameters=inventory['actual_total_parameters']
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
        for row in predictions:row['model_params_b']=actual_parameters/1e9
        n={(r['video_id'],p['frame']):p['bboxes'] for r in predictions for p in r['predictions']}
        require(len(predictions)==426 and {r['video_id'] for r in predictions}==set(clocks) and set(n)==chosen_keys,'Exact426/native mask package identity')
        require(all(n[k]==b[k] for k in n.keys()&b.keys()),'Shared baseline frame boxes changed')
        digest=canonical(predictions)
        if digest in history:
            rejected.append(dict(arm=arm,status='STOP_IDENTICAL_PREDICTION_NO_RENAMED_PACKAGE',canonical=digest));continue
        dst=out/arm;dst.mkdir()
        write(dst/'parameter_inventory.json',inventory)
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
                 actual_total_parameters=actual_parameters,parameter_inventory=reference(dst/'parameter_inventory.json'),independent11strict=True,
                 time_selection=arm_ref,spatial_field_bindings=field_refs,website_submitted=False,
                 quality_scope='Historical public summary temporal proxy; no new blind or official joint validation',online_score='UNKNOWN')
        write(dst/'completion.json',row);deliveries.append(row);history.add(digest)
        event('NEW_TEMPORAL_PACKAGE_ENGINEERING_ACCEPTED',arm=arm,bytes=row['bytes'],frames=row['frames'],added=row['added'],removed=row['removed'])
    write(ROOT/'completion.json',dict(status='COMPLETE_NEW_TIME_SELECTOR_CANDIDATES_UNKNOWN_OFFICIAL_EFFECT',
          deliveries=deliveries,rejected_duplicates=rejected,baseline_sha256=BASELINE_SHA,
          achieved_score_improvement=False,website_submitted=False))


if __name__=='__main__':main()
