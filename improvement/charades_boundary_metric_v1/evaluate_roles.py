"""Evaluate accepted projected role exports against frozen matches on Linux."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
from metric import evaluate, apply_predeclared_availability, diagnostic_role_advice, SCHEMA

BASE=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/charades_boundary_metric_v1')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main(bundle_path,scope,out_name):
    if socket.gethostname()!='inspur-NP5570M5':raise ValueError('Linux evaluation only')
    frozen=read(BASE/'freeze_01/frozen_matches.json');complete=read(BASE/'freeze_01/completion.json')
    if complete['frozen_matches_sha256']!=sha(BASE/'freeze_01/frozen_matches.json'):
        raise ValueError('Original correspondence changed')
    bundle_path=bundle_path.resolve()
    if not bundle_path.is_relative_to(BASE) or scope not in ('dev','confirm') or not out_name.isidentifier():
        raise ValueError('Explicit new evaluator metadata bundle and one frozen group required')
    bundle=read(bundle_path)
    if bundle['schema']!='ACCEPTED_PAIRED_BOUNDARY_ROLE_EXPORTS_FOR_FIXED_METRIC_V1' or bundle['scope']!=scope:
        raise ValueError('Explicit upstream accepted role export projection required')
    plan_ref=bundle['planned_event_ids_ref'];plan_path=Path(plan_ref['path']).resolve()
    if not plan_path.is_relative_to(BASE) or sha(plan_path)!=plan_ref['sha256']:
        raise ValueError('Unchanged pre-fine candidate plan witness copy required')
    planned=read(plan_path)
    if (planned['schema']!='FROZEN_BOUNDARY_ROLE_CANDIDATES_FROM_COARSE_NATIVE_GEOMETRY_ONLY_V1'
            or planned['scope']!=scope or planned['reference_labels_used_to_select'] is not False
            or planned['fine_results_available_at_freeze'] is not False
            or planned['coarse_complete_sha256']!=frozen['coarse_complete_sha256']
            or planned['availability_frozen_before_fine_results'] is not True
            or len(planned['event_ids'])>20 or len(set(planned['event_ids']))!=len(planned['event_ids'])):
        raise ValueError('Frozen cap20 coarse/native-only candidate table required')
    group_ids={e['event_id'] for e in frozen['events'] if e['source_role']==scope}
    if not set(planned['event_ids'])<=group_ids:
        raise ValueError('Planned fine identity escaped original coarse group')
    availability_ref=planned['availability_independent_clock_receipt_ref']
    availability_path=Path(availability_ref['path']).resolve()
    if not availability_path.is_relative_to(BASE) or sha(availability_path)!=availability_ref['sha256']:
        raise ValueError('Unchanged independent clock-only availability witness required')
    availability_witness=read(availability_path)
    if not str(availability_witness.get('status','')).startswith('PASS_'):
        raise ValueError('Failed clock geometry witness cannot authorize a typed skip')
    choice_ref=None
    if scope=='confirm':
        choice_ref=bundle['frozen_dev_role_choice_ref'];choice_path=Path(choice_ref['path']).resolve()
        if not choice_path.is_relative_to(BASE) or sha(choice_path)!=choice_ref['sha256']:
            raise ValueError('Frozen development role choice must precede confirmation')
        choice=read(choice_path)
        if (choice['status']!='FROZEN_GLOBAL_REFINER_ROLE_FROM_DEV_DIAGNOSTIC_NOT_SCIENCE_PASS'
                or choice['chosen_role'] not in ('TIME','BASE') or choice['confirm_outputs_read'] is not False):
            raise ValueError('Confirmation may not select the role or rewrite the development choice')
    receipts={}
    for role in ('TIME','BASE'):
        witness=bundle['roles'][role]['upstream_independent_acceptance_receipt']
        p=Path(witness['path']).resolve()
        if not p.is_relative_to(BASE) or sha(p)!=witness['sha256']:
            raise ValueError('Evaluator needs an unchanged new-root metadata witness copy')
        value=read(p)
        if value['status'] not in ('PASS_BOUNDARY_ROLE_OUTPUT_REPLAYS_WITH_EXISTING_INPUT_PROOF',
                'FAILED_BOUNDARY_ROLE_OUTPUT_REPLAY_KEEP_RAW_AND_PARTIAL') or value['role']!=role:
            raise ValueError('Raw/token/native outputs must be independently accepted upstream')
        receipts[role]=witness
    subset={**frozen,'events':[e for e in frozen['events'] if e['event_id'] in planned['event_ids']],
            'source_coverage':[s for s in frozen['source_coverage'] if s['role']==scope]}
    subset['sources']=len(subset['source_coverage'])
    subset=apply_predeclared_availability(subset,planned['endpoint_availability'])
    report=evaluate(subset,{r:bundle['roles'][r]['events'] for r in ('TIME','BASE')})
    for role in ('TIME','BASE'):
        witness=read(receipts[role]['path'])
        if witness['status'].startswith('FAILED_'):
            report['roles'][role]['upstream_replay_failed']=True
            report['roles'][role]['engineering_pass']=False
            report['roles'][role]['diagnostic_MAE_seconds']=None
            report['paired_comparison_engineering_admitted']=False
            report['paired_mean_BASE_minus_TIME_seconds']=None
    report['diagnostic_role_advice']=diagnostic_role_advice(subset,
        {r:bundle['roles'][r]['events'] for r in ('TIME','BASE')},report)
    if scope=='confirm':
        report['confirm_diagnostic_would_pass_conservative_rule']=not report['diagnostic_role_advice']['reasons']
        report['diagnostic_role_advice']['chosen_role_advice']=None
        report['diagnostic_role_advice']['role_selection_allowed']=False
    report.update(scope=scope,upstream_acceptance_receipts=receipts,bundle_sha256=sha(bundle_path),
                  frozen_matches_sha256=complete['frozen_matches_sha256'],model_calls=0,
                  all_group_coarse_events=len(group_ids),planned_event_ids_ref=plan_ref,
                  planned_fine_events=len(planned['event_ids']),unselected_coarse_events=len(group_ids)-len(planned['event_ids']),
                  endpoint_availability_ref=availability_ref,
                  frozen_dev_role_choice_ref=choice_ref)
    out=BASE/out_name;out.mkdir(exist_ok=False)
    with (out/'result.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in report.items() if k not in ('roles','source_coverage','paired')}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--scope',choices=('dev','confirm'),required=True);p.add_argument('--out-name',required=True)
    a=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']='';main(a.bundle,a.scope,a.out_name)
