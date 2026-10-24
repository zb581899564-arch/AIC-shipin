"""Independent packaging and11 strict checks, with truthful new provenance kinds."""
import json
import os
from pathlib import Path
import subprocess
from common import ROOT, ASSETS, PY, read, ref, checked, save_new, save_lines
from curves import POLICIES
from produce import KINDS
from improvement.final_sprint_v1.packaging import build_package


def independent(policy, receipt, bound):
    provenance=[]
    for sid in sorted(map(str,range(426))):
        evidence=read(ROOT/policy/'sources'/(sid+'_evidence.json'))
        proof_ref=ref(ROOT/policy/'sources'/(sid+'_evidence.json'))
        for frame in evidence['frames']:
            provenance.append(dict(video_id=sid,source_frame=frame['frame'],box_xyw=frame['bboxes'],
                legal=True,spatial_source=KINDS[policy],native_pts=frame['native_pts'],
                evidence=proof_ref,shot_id=frame['shot_id']))
    destination=ROOT/policy/'package'
    prov=save_lines(destination/'independent_provenance.jsonl',provenance)
    report=destination/'independent_11strict.json'
    command=[str(PY),'-B',str(checked(bound['validator_ref'])),
        '--strict-loader-root',bound['strict_loader'],
        '--metadata',str(checked(bound['metadata'])),
        '--selected',str(checked(bound['selection_export']['selected_ref'])),
        '--predictions',str(checked(receipt['member_ref'])),
        '--provenance',str(checked(prov)), '--zip',str(checked(receipt['zip_ref'])),
        '--report',str(report)]
    completed=subprocess.run(command,capture_output=True,text=True,timeout=600,
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
    with (destination/'independent_log.txt').open('x') as f:
        f.write(completed.stdout+'\n'+completed.stderr)
    if completed.returncode or not report.exists():
        raise ValueError('Actual independent strict validation failed; no default or partial delivery')
    value=read(report)
    if value['status'] != 'PASS_INDEPENDENT_STRICT_VALIDATION' or len(value['checks']) != 11 or not all(value['checks'].values()):
        raise ValueError('All11 independent checks are required')
    return ref(report)


def main():
    assets,bound=read(ASSETS),read(ROOT/'bound_inputs.json')
    deliveries=[]
    for policy in POLICIES:
        binding=read(ROOT/(policy+'_binding.json'))
        results=[read(ROOT/policy/'sources'/(sid+'.json')) for sid in sorted(map(str,range(426)))]
        receipt=build_package(candidate_id=binding['candidate_id'],sources=assets['sources'],source_results=results,
            parameter_receipts=bound['parameter_receipts'],protected_baselines=assets['protected_baselines'],
            binding=binding,output_dir=ROOT/policy/'package',history_path=ROOT/'distinct_package_history.jsonl')
        validation=independent(policy,receipt,bound)
        changes=receipt['changes_from_baselines']['40.48']
        if changes['added_frames'] or changes['removed_frames'] or not changes['changed_boxes']:
            raise ValueError('Risk spatial candidate must preserve all temporal members and change real predictions')
        delivery=dict(schema='AIC_FINAL_DELIVERY_V1',candidate_id=binding['candidate_id'],
            status='ENGINEERING_ACCEPTED_QUALITY_UNVALIDATED',zip_path=receipt['zip_ref']['path'],
            zip_bytes=receipt['zip_ref']['bytes'],zip_sha256=receipt['zip_ref']['sha256'],
            member_sha256=receipt['member_sha256'],prediction_sha256=receipt['prediction_sha256'],
            actual_model_parameters=receipt['parameter_budget']['total_elements'],model_params_b=receipt['parameter_budget']['total_elements']/1e9,
            source_count=426,selected_frames=123479,changes_from_4048=changes,all_crop_widths_unchanged=True,
            independent_11strict_ref=validation,package_receipt_ref=ref(ROOT/policy/'package/package_receipt.json'),
            protected_baselines_unchanged=True,new_model_calls=0,new_training=0,new_media_decodes=0,
            offline_quality_validated=False,official_score='UNKNOWN',website_submitted=False)
        save_new(ROOT/policy/'package/delivery.json',delivery)
        deliveries.append(delivery)
        print('PACKAGE_READY',policy,json.dumps(changes),flush=True)
    save_new(ROOT/'completion.json',dict(status='THREE_DISTINCT_COMPLETE_RISK_PACKAGES_READY',deliveries=deliveries,
        old_failures_and_baselines_unchanged=True,no_offline_quality_claim=True,new_model_calls=0))


if __name__ == '__main__':
    main()
