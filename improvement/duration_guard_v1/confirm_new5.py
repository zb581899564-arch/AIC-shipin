"""Confirm only frozen D2/D4/D8 on the initially reserved five human references."""
import json
import sys
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from receive_new5_export import ROOT,REPORT,read,sha,save
from duration_intervals import THRESHOLDS,spans
from native_mapping_v3 import validate_mapping

sys.path.insert(0,str(ROOT/'improvement/human_reference_v1'))
from human_metrics import mean_pairwise,paired_summary
sys.path.insert(0,str(ROOT/'improvement/boundary_refinement_v1'))
from intervals import expanded_windows,native_membership

EXTERNAL=REPORT/'external_export_01'
SELECTION=REPORT/'screen_01/selection_before_new5_confirm.json'
SCREEN=REPORT/'screen_01/result.json'
OUT=REPORT/'confirm_new5_01'

def input_admission():
    transfer=read(EXTERNAL/'transfer_receipt.json')
    if transfer['status']!='PASS_WINDOWS_LINUX_BYTES_SHA_CRC_AND_ALL_EXPORT_MEMBER_SHA':
        raise ValueError('Actual completed Windows transfer is required')
    for member,item in transfer['manifest'].items():
        path=EXTERNAL/member
        if path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:
            raise ValueError('Transferred external receipt changed')
    native=read(EXTERNAL/'native_input_acceptance.json')
    if (native['status']!='PASS_ALL_REGISTERED_HUMAN_NATIVE_INPUTS' or
            native['registered_sources']!=5 or native['accepted_sources']!=5 or native['accepted_windows']!=28 or
            native['frame_mapping_failures'] or not native['known_source_separation_pass'] or native['new_optimizer_updates'] or
            native['registration_sha256']!=sha(REPORT/'new5_source_registration_01.json') or
            native['mapping_contract_sha256']!=sha(REPORT/'NATIVE_MAPPING_CONTRACT_V3.md') or
            native['evaluation_policy_sha256']!=sha(REPORT/'EVALUATION_POLICY.md')):
        raise ValueError('All original reserved-five native28 inputs must be accepted')
    chain,gpu,replay,export=[read(EXTERNAL/p) for p in ['new5_chain_01/completion.json',
        'new5_gpu_01/completion.json','new5_replay_01/completion.json','developer_export_acceptance.json']]
    resource=read(EXTERNAL/'resource.json')
    if (chain['status']!='PASS_RESERVED5_B_EXPORT_PENDING_FROZEN_CONFIRM_COMPARISON' or
            gpu['status']!='PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY' or
            replay['status']!='PASS_ALL_HUMAN_EXTERNAL_B_INDEPENDENT_CPU_REPLAYS' or
            export['status']!='PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY' or
            any(v['registered_sources']!=5 for v in (chain,gpu,replay,export)) or
            not gpu['actual_model_calls']==gpu['successful_windows']==replay['windows']==28 or
            len(replay['proofs'])!=28 or len({p['case_id'] for p in replay['proofs']})!=28 or
            gpu['model_parameters']!=8782459120 or gpu['new_optimizer_updates'] or gpu['reference_labels_read'] or
            not replay['CPU_only'] or replay['CUDA_initialized'] or
            gpu['source_lock_sha256']!=sha(EXTERNAL/'new5_source_lock_01.json') or
            gpu['model_identity_sha256']!=sha(EXTERNAL/'new5_gpu_01/model_identity.json') or
            replay['gpu_completion_sha256']!=sha(EXTERNAL/'new5_gpu_01/completion.json') or
            export['independent_replay_completion_sha256']!=sha(EXTERNAL/'new5_replay_01/completion.json') or
            export['native_input_acceptance_sha256']!=sha(EXTERNAL/'native_input_acceptance.json') or
            export['developer_prediction_export_sha256']!=sha(EXTERNAL/'developer_prediction_export.json') or
            chain['developer_export_acceptance_sha256']!=sha(EXTERNAL/'developer_export_acceptance.json') or
            chain['prediction_export_sha256']!=sha(EXTERNAL/'developer_prediction_export.json') or
            resource['name']!='duration_guard_reserved5_original_b_native64_20261013_v1' or
            resource['status']!='completed' or resource['exit_code'] or
            read(EXTERNAL/'matching_gpu_ledger.json')!=[resource] or
            any(v[key]!=sha(EXTERNAL/'resource.json') for v,key in
                [(chain,'resource_terminal_sha256'),(replay,'resource_terminal_sha256'),(export,'unique_resource_terminal_sha256')])):
        raise ValueError('Actual unique original-B/CPU/export/ledger lineage changed')
    if sha(EXTERNAL/'new5_source_registration_01.json')!=sha(REPORT/'new5_source_registration_01.json'):
        raise ValueError('Reserved-five source registration changed during transfer')
    screen,selection=read(SCREEN),read(SELECTION)
    if (screen['selection_sha256']!=sha(SELECTION) or selection['protocol_sha256']!=sha(REPORT/'PROTOCOL.md') or
            not selection['frozen_before_new5_media_and_prediction'] or not selection['old8confirm_not_evaluated'] or
            selection['thresholds_seconds']!={arm:str(THRESHOLDS[arm]) for arm in selection['chosen']} or
            screen['chosen']!=selection['chosen'] or not screen['old_reference_failed_preserved']):
        raise ValueError('Before-confirmation selection/rules changed')
    for arm in selection['chosen']:
        checks=screen['known_fact_checks'][arm]
        if (not screen['screen'][arm]['diagnostic_risk_pass'] or len(checks)!=40 or
                len({r['case_id'] for r in checks})!=40 or
                not all(r['known_point_veto_pass'] and not r['core_lost'] and not r['ordinary_added'] for r in checks)):
            raise ValueError('Unchanged prior screen and known-fact veto required')
    for key,path in [('partial_reference_sha256',ROOT/'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json'),
            ('partial_original_export_sha256',ROOT/'reports/boundary_refinement_20261012_v1/developer_readonly_export.json')]:
        if screen[key]!=sha(path):raise ValueError('Frozen known-fact provenance changed')
    return native,selection

def main():
    native,selection=input_admission()  # Never inspect new predictions before complete admission.
    registration=read(REPORT/'new5_source_registration_01.json')
    payload=read(EXTERNAL/'developer_prediction_export.json')
    if (payload['status']!='PASS_NEW_B_NATIVE_INFERENCE_AND_INDEPENDENT_CPU_REPLAY' or
            payload['registered_sources']!=5 or payload['model_parameters']!=8782459120 or
            payload['new_optimizer_updates'] or payload['reference_labels_read'] or
            payload['started_windows']!=28 or payload['successful_windows']!=28):
        raise ValueError('New5 prediction export is incomplete')
    predicted={r['source_name']:r for r in payload['rows']}
    if len(predicted)!=5 or len(payload['rows'])!=5 or set(predicted)!={r['source_name'] for r in registration['rows']}:
        raise ValueError('Initially reserved-five source denominator changed')
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json',dict(script_sha256=sha(__file__),interval_rule_sha256=sha(Path(__file__).with_name('duration_intervals.py')),
        input_acceptance_sha256=sha(EXTERNAL/'native_input_acceptance.json'),selection_sha256=sha(SELECTION),screen_sha256=sha(SCREEN),
        export_sha256=sha(EXTERNAL/'developer_prediction_export.json'),new_model_calls=0,new_optimizer_updates=0,
        only_initial_reserved5_confirm=True,no_threshold_retuning=True))
    values=[]
    for expected in registration['rows']:
        row=predicted[expected['source_name']]
        mapping=validate_mapping(expected,row['native_clock'])
        annotation=Path(expected['annotation_path'])
        if sha(annotation)!=expected['annotation_sha256']:raise ValueError('Original reserved human annotation changed')
        human=loadmat(annotation)['user_score']
        if human.shape!=(expected['annotation_frames'],expected['human_summary_columns']):raise ValueError('Original human denominator changed')
        points=[F(p) for p in row['native_clock']['normalized_exact_pts']]
        windows=row['windows']
        if (not windows or F(windows[0]['start_exact'])!=0 or F(windows[-1]['end_exact'])!=F(row['native_clock']['physical_end_exact']) or
                any(F(a['end_exact'])!=F(b['start_exact']) for a,b in zip(windows,windows[1:])) or
                any(w['original_status']!=('MODEL_OK' if w['segments'] else 'LEGAL_EMPTY') for w in windows)):
            raise ValueError('Original source interval coverage/status differs')
        base=native_membership(points,spans(windows))
        if base!=native_membership(points,expanded_windows(windows,'3/4','1/2')):raise ValueError('Baseline reproduction differs')
        metrics={}
        for arm,threshold in [('baseline',None),*[(arm,THRESHOLDS[arm]) for arm in selection['chosen']]]:
            indices=native_membership(points,spans(windows,threshold))
            if not base<=indices:raise ValueError('Original baseline frame removed')
            mask=np.zeros(len(points),dtype=bool);mask[list(indices)]=True
            metrics[arm]=dict(mean_pairwise(mask,human),added_frames=len(indices-base))
            if arm!='baseline' and any(a<b for a,b in zip(metrics[arm]['user_recall'],metrics['baseline']['user_recall'])):
                raise ValueError('Original human-summary recall decreased')
        values.append(dict(source_name=expected['source_name'],role='new_confirm',mapping=mapping,metrics=metrics))
    if len(values)!=5:raise ValueError('Reserved-five confirmation count changed')
    summary={arm:paired_summary([r['metrics']['baseline']['f1'] for r in values],[r['metrics'][arm]['f1'] for r in values]) for arm in selection['chosen']}
    qualified=[arm for arm in selection['chosen'] if summary[arm]['diagnostic_risk_pass']]
    result=dict(status='PASS_FROZEN_D_SCREEN_FACT_AND_RESERVED5_CONFIRM_RISK_ADMISSION' if qualified else 'STOP_ALL_FROZEN_D_CONFIRM_CANDIDATES_REJECTED',
        qualified=qualified,confirm=summary,rows=values,selection_sha256=sha(SELECTION),screen_sha256=sha(SCREEN),
        launch_sha256=sha(OUT/'launch_claim.json'),transfer_receipt_sha256=sha(EXTERNAL/'transfer_receipt.json'),
        no_threshold_retuning=True,all_baseline_frames_and_per_reviewer_recall_retained=True,old40_reference_failed_preserved=True,
        reference_is_summary_proxy_not_crop_quality=True,new_model_calls=0,new_optimizer_updates=0,new_submission_zips=0,official_score='UNKNOWN')
    save(OUT/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':main()
