"""Fixed12-screen, freeze, then8-confirm after full original-B export admission."""
import json
from pathlib import Path

from deploy_direct_media_05 import REPORT
from stage_common_04 import read,save,sha
from evaluate_l16_intervals_07 import evaluate_group

EXTERNAL=REPORT/'cohort_external_export_08'
OUT=REPORT/'l16_comparison_08'


def admission():
    transfer=read(EXTERNAL/'transfer_acceptance.json')
    if transfer['status']!='PASS_WINDOWS_LINUX_BYTES_SHA_CRC_AND_ALL_COHORT_EXPORT_MEMBERS':
        raise ValueError('Complete actual Windows export transfer required')
    for name,item in transfer['manifest'].items():
        p=EXTERNAL/name
        if p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:raise ValueError('Actual transferred evidence changed')
    chain=read(EXTERNAL/'cohort_chain_07/completion.json')
    gpu=read(EXTERNAL/'cohort_gpu_07/completion.json')
    replay=read(EXTERNAL/'cohort_replay_07/completion.json')
    export=read(EXTERNAL/'developer_export_acceptance.json')
    native=read(EXTERNAL/'cohort_input_acceptance_07.json')
    payload=read(EXTERNAL/'developer_prediction_export.json')
    resource=read(EXTERNAL/'resource.json')
    if (chain['status']!='PASS_B20_EXPORT_PENDING_FROZEN_SCREEN_AND_CONFIRM_NOT_PACKAGE' or
        gpu['status']!='PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY' or
        replay['status']!='PASS_ALL_HUMAN_EXTERNAL_B_INDEPENDENT_CPU_REPLAYS' or
        export['status']!='PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY' or
        native['status']!='PASS_INDEPENDENT_EFFECTIVE20_ACTUAL_CPU_INPUTS_BEFORE_B' or
        any(x['registered_sources']!=20 for x in [chain,gpu,replay,export,native,payload]) or
        not native['accepted_windows']==gpu['actual_model_calls']==gpu['successful_windows']==replay['windows']==payload['started_windows']==payload['successful_windows'] or
        gpu['model_parameters']!=8782459120 or gpu['new_optimizer_updates'] or gpu['reference_labels_read'] or
        payload['model_parameters']!=8782459120 or payload['new_optimizer_updates'] or payload['reference_labels_read'] or
        not replay['CPU_only'] or replay['CUDA_initialized'] or
        read(EXTERNAL/'matching_gpu_ledger.json')!=[resource] or resource['status']!='completed' or resource['exit_code'] or
        resource['name']!='videoxum20_original_b_native64_20261013_v1'):
        raise ValueError('Actual unique original-B20 inference/replay/resource admission changed')
    for body,key,p in [(gpu,'source_lock_sha256','cohort_source_lock_07.json'),(gpu,'native_input_acceptance_sha256','cohort_input_acceptance_07.json'),
        (gpu,'attempts_sha256','cohort_gpu_07/attempts.jsonl'),(gpu,'model_identity_sha256','cohort_gpu_07/model_identity.json'),
        (replay,'gpu_completion_sha256','cohort_gpu_07/completion.json'),(replay,'resource_terminal_sha256','resource.json'),
        (export,'independent_replay_completion_sha256','cohort_replay_07/completion.json'),
        (export,'native_input_acceptance_sha256','cohort_input_acceptance_07.json'),(export,'developer_prediction_export_sha256','developer_prediction_export.json'),
        (chain,'developer_export_acceptance_sha256','developer_export_acceptance.json'),(chain,'prediction_export_sha256','developer_prediction_export.json'),
        (chain,'resource_terminal_sha256','resource.json')]:
        if body[key]!=sha(EXTERNAL/p):raise ValueError('Completed inference/export lineage changed')
    events=[json.loads(x) for x in (EXTERNAL/'cohort_gpu_07/attempts.jsonl').read_text().splitlines()]
    if len(events)!=2*native['accepted_windows']:raise ValueError('Unique actual call count differs')
    for index,proof in enumerate(native['proofs'],1):
        begun,accepted=events[2*(index-1):2*index]
        if (begun['event']!='BEGIN_MODEL_CALL' or accepted['event']!='ACCEPTED_MODEL_CALL' or
            begun['call_id']!=index or accepted['call_id']!=index or
            begun['case_id']!=proof['case_id'] or accepted['case_id']!=proof['case_id']):
            raise ValueError('Actual call order differs from accepted native requests')
    original_remote='/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/'
    references={}
    for source in native['sources']:
        path=source['reference_path']
        if not path.startswith(original_remote):raise ValueError('Unexpected original reference path')
        p=EXTERNAL/path[len(original_remote):]
        if sha(p)!=source['reference_sha256']:raise ValueError('Unmodified reference changed in transfer')
        references[source['video_id']]=read(p)[0]
    expected={x['video_id']:x['group'] for x in native['sources']}
    predicted={x['video_id']:x['group'] for x in payload['rows']}
    if expected!=predicted or len(payload['rows'])!=20:raise ValueError('Frozen effective20 prediction roles changed')
    return payload,references


def main():
    if OUT.exists():raise ValueError('Comparison already exists; do not rerun or retune its results')
    payload,references=admission()
    fact=read(REPORT/'followup_fact_veto_02.json')
    checks=fact['checks']['L16']
    if ('L16' not in fact['eligible_for_new_human_screen'] or len(checks)!=40 or
        not all(row['known_point_veto_pass'] and not row['core_lost'] and not row['ordinary_added'] for row in checks) or
        not fact['old40_quality_failed_preserved'] or not fact['original_L8_factual_failure_preserved']):
        raise ValueError('Unchanged fixed known-fact veto required')
    OUT.mkdir()
    save(OUT/'launch_claim.json',dict(script_sha256=sha(__file__),
        metric_sha256=sha(Path(__file__).with_name('evaluate_l16_intervals_07.py')),
        interval_rule_sha256=sha(Path(__file__).with_name('lead_guard_v2.py')),
        protocol_sha256=sha(REPORT/'FOLLOWUP_PROTOCOL_02.md'),fact_veto_sha256=sha(REPORT/'followup_fact_veto_02.json'),
        transfer_acceptance_sha256=sha(EXTERNAL/'transfer_acceptance.json'),
        prediction_export_sha256=sha(EXTERNAL/'developer_prediction_export.json'),new_model_calls=0,new_optimizer_updates=0))
    screen=evaluate_group(payload['rows'],references,'screen')
    save(OUT/'screen_result.json',screen)
    if not screen['original_fixed_gates_pass']:
        save(OUT/'result.json',dict(status='STOP_L16_SCREEN_REJECTED_CONFIRM_NOT_EVALUATED',
            screen_sha256=sha(OUT/'screen_result.json'),confirmation_evaluated=False,new_submission_zips=0,new_model_calls=0))
        print(json.dumps(dict(status='STOP_L16_SCREEN',macro_delta=screen['macro_delta'],changed_sources=screen['actual_changed_sources'])))
        return
    save(OUT/'selection_before_confirm.json',dict(chosen='L16',screen_sha256=sha(OUT/'screen_result.json'),
        protocol_sha256=sha(REPORT/'FOLLOWUP_PROTOCOL_02.md'),minimum_original_segment_seconds='16',extra_pre_seconds='1/4',
        frozen_before_confirm_metrics=True,no_threshold_retuning=True))
    confirm=evaluate_group(payload['rows'],references,'confirm')
    save(OUT/'confirm_result.json',confirm)
    qualified=confirm['original_fixed_gates_pass']
    save(OUT/'result.json',dict(status='PASS_L16_FIXED_SCREEN_FACT_AND_CONFIRM_RISK_ADMISSION' if qualified else 'STOP_L16_CONFIRM_REJECTED',
        qualified=qualified,candidate='L16',screen_sha256=sha(OUT/'screen_result.json'),confirm_sha256=sha(OUT/'confirm_result.json'),
        selection_sha256=sha(OUT/'selection_before_confirm.json'),launch_sha256=sha(OUT/'launch_claim.json'),
        old40_quality_failed_preserved=True,no_threshold_retuning=True,new_model_calls=0,new_optimizer_updates=0,
        new_submission_zips=0,official_score='UNKNOWN',quality_scope='Original manual interval proxy; no crop or official score guarantee'))
    print(json.dumps(dict(status='PASS_L16_RISK_ADMISSION' if qualified else 'STOP_L16_CONFIRM',
        screen_delta=screen['macro_delta'],confirm_delta=confirm['macro_delta'],
        screen_changed_sources=screen['actual_changed_sources'],confirm_changed_sources=confirm['actual_changed_sources'])))


if __name__=='__main__':main()
