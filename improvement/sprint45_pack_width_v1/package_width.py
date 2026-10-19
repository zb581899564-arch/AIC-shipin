"""CPU-only C/D rendering and independent validation; no model/launcher/QA rerun."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import traceback
import zipfile
from pack_common import *

NAMES={'C':'NATIVE16_LEARNED_WIDTH','D':'JOINT_CONTEXT_WIDTH'}


def terminal(reg,prefix):
    resource=read(bound(reg[prefix+'_resource']));unique=read(bound(reg[prefix+'_unique_resource']))
    require(resource['status']=='completed' and resource['exit_code']==0 and unique['unique_terminal_count']==1,'Actual natural unique '+prefix+' shared-GPU terminal')


def main(root,width_root,registration,arm):
    import numpy as np
    reg=read(registration)
    require(root.is_absolute() and width_root.is_absolute() and registration.is_absolute(),'Absolute package root/width root/registration paths')
    require(reg['schema']=='SPRINT45_WIDTH_TWO_RISK_PACKAGES_V1' and Path(reg['out_root']).resolve()==root.resolve() and
            Path(reg['width_root']).resolve()==width_root.resolve(),'Independent C/D CPU package registration')
    require(reg['offline_effect_gate_required'] is False and reg['online_effect']=='UNKNOWN' and reg['actual_total_parameters']==TOTAL<=9_000_000_000,'Unknown online effect; exact shared physical parameter count')
    require(read(bound(reg['official_rule_check']))['automatic_local_inference_risk_scope_allowed'] is True,'Current local automatic inference rule scope')
    require(reg['width_head']['sha256']==HEAD and reg['width_normalization']['sha256']==NORM,'Actual frozen602 head/normalization binding');bound(reg['width_head']);bound(reg['width_normalization'])
    terminal(reg,'width')
    width_ref=reg['width_by_video'];width_payload=read(bound(width_ref));qa_ref=reg['width_output_QA'];qa=read(bound(qa_ref))
    require(Path(width_ref['path']).resolve()==(width_root/'width_by_video.json').resolve() and Path(qa_ref['path']).resolve()==(width_root/'width_output_QA.json').resolve(),'Actual width-root output paths')
    require(width_payload['status']=='PASS_FROZEN_WIDTH_HEAD_NATIVE16_SAMPLE_READOUT' and width_payload['head_sha256']==HEAD and width_payload['normalization_sha256']==NORM and
            width_payload['model_parameters']==TOTAL and width_payload['new_head_updates']==0 and width_payload['online_effect']=='UNKNOWN','Frozen width source outputs, no training')
    require(qa['status']=='PASS_NATIVE16_FROZEN_HEAD_NATIVE_SAMPLE_OUTPUT_AND_SAVE_QA' and qa['width_by_video_sha256']==width_ref['sha256'] and qa['head_sha256']==HEAD and qa['normalization_sha256']==NORM,'Actual first successful width/native/output-save QA')
    # Bind the actual serialized head output already accepted by first QA, without
    # a second head forward or any GPU work.
    require(sha(width_root/'head_unique_output.npz')==qa['head_unique_output_sha256'],'Actual saved raw/quantized head output')
    inputs=read(bound(reg['source_field_inputs']))
    fields={name:bound(value) for name,value in inputs['source_field_files'].items()}
    require(set(fields)=={'field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl'},'Full original frozen spatial field closure')
    metadata=read(bound(inputs['metadata']));manifest=read(bound(inputs['source_manifest']))
    actual_clocks=read(bound(inputs['source_clocks']))
    from fractions import Fraction
    require(all([Fraction(x) for x in data['native_pts_exact']]==[Fraction(x) for x in actual_clocks[sid]['normalized_exact_pts']] for sid,data in width_payload['width_by_video'].items()),'Width observation times equal original full native clock registry exactly')
    require({r['video_id'] for r in metadata['records']}=={str(i) for i in range(426)} and len(metadata['records'])==426,'Exact426 metadata')
    meta_index={r['video_id']:r for r in metadata['records']}
    field=lines(fields['field_frames.jsonl']);field_map={(r['video_id'],r['source_frame']):r for r in field}
    require(len(field_map)==len(field),'Unique complete original spatial field')
    baseline=bound(reg['baseline']);require(reg['baseline']['sha256']==BASELINE,'Current40.47 baseline')
    with zipfile.ZipFile(baseline) as archive:
        require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None,'Current baseline archive/CRC')
        base=[json.loads(x) for x in archive.read('predictions.jsonl').splitlines()]
    original=boxes(base)
    require(len(base)==426 and {r['video_id'] for r in base}=={str(i) for i in range(426)} and len(original)==123506 and set(original)<=set(field_map),'Exact current426/123506 frame baseline and spatial domain')
    selected=set(original);excluded=0;global_qa_ref=None
    if arm=='D':
        # D alone waits for global completion. C never opens global results.
        terminal(reg,'global');global_root=Path(reg['global_root']);global_qa_ref=reg['global_output_QA']
        require(Path(global_qa_ref['path']).resolve()==(global_root/'output_acceptance.json').resolve(),'Actual global output root')
        output=read(bound(global_qa_ref))
        require(output['status']=='PASS_ALL426_GLOBAL_LOCAL_BINARY_OUTPUT_QA' and len(output['sources'])==426 and
                {s['id'] for s in output['sources']}=={str(i) for i in range(426)},'All426 first successful global/payoff native QA')
        for source in output['sources']:
            native=np.load(bound(dict(path=source['native_path'],sha256=source['native_sha256'])),allow_pickle=False)
            a=np.load(bound(dict(path=source['global_mask_path'],sha256=source['global_sha256'])),allow_pickle=False)
            b=np.load(bound(dict(path=source['payoff_mask_path'],sha256=source['payoff_sha256'])),allow_pickle=False)
            groups=native['groups']
            require(a.dtype==b.dtype==np.bool_ and a.shape==b.shape==(source['cells'],) and groups.ndim==1 and
                    len(groups)==meta_index[source['id']]['n_frames'] and np.issubdtype(groups.dtype,np.integer) and groups.min()==0 and
                    bool((np.diff(groups)>=0).all()) and int(groups.max())+1==len(a),'Actual two boolean masks and occupied native groups')
            for frame in np.flatnonzero((a|b)[groups]).tolist():
                key=(source['id'],frame)
                if key in field_map:selected.add(key)
                else:excluded+=1
    run=Path(reg['run_root'])
    scoring=run/'baseline_a_pts_v1/vendor/frozen_strict_loader/aic6/scoring.py'
    require(sha(scoring)==reg['frozen_strict_loader_scoring_sha256'],'Original frozen official strict loader unchanged')
    sys.path[:0]=[str(run/'b_score_aligned_package_v4'),str(run/'baseline_a_pts_v1'),str(run/'baseline_a_pts_v1/vendor')]
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    chosen=[field_map[k] for k in sorted(selected)];shot_rows=lines(fields['field_shots.jsonl']);anchors=lines(fields['anchor_output.jsonl'])
    composed,old_provenance=compose_from_field(legacy_manifest(manifest),chosen,shot_rows,lines(fields['anchor_requests.jsonl']),anchors)
    before=boxes(composed)
    require(set(before)==selected and all(before[k]==v for k,v in original.items()),'Exact original accepted current baseline boxes before width')
    renderer=bound(reg['native_apply_module']);dependency=bound(reg['native_apply_dependency'])
    require(renderer.name=='native_apply.py' and dependency.name=='prod_common.py' and dependency.parent==renderer.parent,'Frozen width renderer dependency closure')
    sys.path.insert(0,str(renderer.parent))
    spec=importlib.util.spec_from_file_location('sprint45_frozen_native_width_renderer',renderer);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    require(module.HEAD_SHA==HEAD and module.NORM_SHA==NORM and module.TOTAL==TOTAL,'Actual renderer frozen head/parameter constants')
    rows,provenance=module.apply_to_predictions(composed,old_provenance,width_payload['width_by_video'],shot_rows,anchors,metadata)
    after=boxes(rows);meta={r['video_id']:r for r in metadata['records']}
    require(set(after)==selected and (arm!='C' or selected==set(original)),'C exact123506 frames; D explicit original plus union')
    require(all(after[k]==before[k] for k in before if meta[k[0]]['targetRatioWH']==[9,16]),'All portrait composed boxes unchanged')
    history=set(reg['historical_canonical_sha256'])|{canonical(base)}
    for value in reg.get('comparison_completion_refs',[]):history.add(read(bound(value))['canonical_sha256'])
    for other in NAMES.values():
        path=root/other/'completion.json'
        if path.exists() and read(path).get('independent11strict') is True:history.add(read(path)['canonical_sha256'])
    digest=canonical(rows);out=root/NAMES[arm];out.mkdir(parents=True,exist_ok=False)
    if digest in history:
        save(out/'completion.json',dict(status='STOP_NO_NEW_PREDICTION_FOR_THIS_DIRECTION',direction=NAMES[arm],canonical_sha256=digest,no_ZIP_created=True,online_effect='UNKNOWN'));return
    jsonlines(out/'prewidth_predictions.jsonl',composed);jsonlines(out/'prewidth_provenance.jsonl',old_provenance)
    jsonlines(out/'predictions.jsonl',rows);jsonlines(out/'selected.jsonl',chosen);jsonlines(out/'provenance.jsonl',provenance);save(out/'metadata.json',metadata)
    evidence=dict(schema='SPRINT45_WIDTH_PACKAGE_EVIDENCE_V1',arm=arm,baseline=reg['baseline'],width_by_video=width_ref,width_output_QA=qa_ref,
                  prewidth_predictions=reference(out/'prewidth_predictions.jsonl'),prewidth_provenance=reference(out/'prewidth_provenance.jsonl'),
                  field_frames=reference(fields['field_frames.jsonl']),field_shots=reference(fields['field_shots.jsonl']),
                  anchor_requests=reference(fields['anchor_requests.jsonl']),anchor_outputs=reference(fields['anchor_output.jsonl']),
                  source_clocks=inputs['source_clocks'],
                  renderer=reg['native_apply_module'],registration=reference(registration),global_output_QA=global_qa_ref)
    save(out/'width_evidence.json',evidence)
    pending=out/('candidate_'+NAMES[arm]+'.PENDING.zip')
    with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as archive:archive.write(out/'predictions.jsonl','predictions.jsonl')
    validator=Path(__file__).with_name('independent_validate.py')
    subprocess.run([sys.executable,str(validator),'--strict-loader-root',str(scoring.parent.parent),'--metadata',str(out/'metadata.json'),
        '--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
        '--zip',str(pending),'--report',str(out/'independent_validation.json'),'--width-evidence',str(out/'width_evidence.json')],check=True)
    validation=read(out/'independent_validation.json')
    require(len(validation['checks'])==11 and all(validation['checks'].values()) and validation['width_validation_status']=='PASS_NEW_WIDTH_NATIVE_EVIDENCE' and all(validation['width_evidence_checks'].values()),'Independent11strict AND new native width evidence validation')
    with zipfile.ZipFile(pending) as archive:require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest()==sha(out/'predictions.jsonl'),'Final ZIP single member/CRC/member SHA')
    final=out/('candidate_'+NAMES[arm]+'.zip');pending.rename(final)
    save(out/'completion.json',dict(status='PASS_ENGINEERING_UNKNOWN_ONLINE_WIDTH_RISK_CANDIDATE',direction=NAMES[arm],arm=arm,
         path=str(final),bytes=final.stat().st_size,sha256=sha(final),member_sha256=sha(out/'predictions.jsonl'),canonical_sha256=digest,
         records=426,frames=len(after),baseline_frames=len(original),added=len(selected-set(original)),removed=0,
         changed_landscape_boxes=sum(after[k]!=before[k] for k in before),portrait_boxes_preserved=True,current_frame_membership_exact=arm=='C',
         fixed_field_domain_excluded=excluded,actual_total_parameters=TOTAL,independent11strict=True,independent_width_evidence=True,
         old_strict_loader_sha256=sha(scoring),new_validator_sha256=sha(validator),offline_effect_validation=False,online_effect='UNKNOWN',
         website_submitted=False,registration_sha256=sha(registration),width_output_QA_sha256=qa_ref['sha256'],global_output_QA_sha256=global_qa_ref['sha256'] if global_qa_ref else None))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--width-root',required=True);p.add_argument('--out-root',required=True);p.add_argument('--registration',required=True);p.add_argument('--arm',choices=['C','D'],required=True);args=p.parse_args();root=Path(args.out_root)
    try:main(root,Path(args.width_root),Path(args.registration),args.arm)
    except BaseException as error:
        root.mkdir(parents=True,exist_ok=True);path=root/('failure_%s.json'%args.arm)
        if not path.exists():save(path,dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,no_automatic_repeat=True))
        raise
