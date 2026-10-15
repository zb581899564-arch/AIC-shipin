"""Pure V4 registration adapter. Main owns protocol, role files and execution.

No plan/media/processor/model command is called. The real plan later freezes
actual calls; this declaration freezes all original events and nominal ceiling.
"""
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA='LOCAL_BOUNDARY_NATIVE64_V4_STRUCTURAL_SKIP01'
REVISION='UNCHANGED_V3_ACTIONABLE_PLUS_TYPED_SHORT_NATIVE_SKIP01'
STATUS='FROZEN_EXTERNAL_NONTEST_LOCAL_BOUNDARY_V4_STRUCTURAL_SKIP01'
BASE=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v4')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def ref(path):
    p=Path(path).resolve()
    return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def adapt(template,role,events,base,code_files,protocol,rule,extraction,selection=None):
    """No source/event filtering, no GT, no premature actual call estimate."""
    if role not in ('dev','confirm') or len(events)<10 or len(events)>20:
        raise ValueError('Original full10..20 role event count required; no fill/filter')
    if str(Path(base))!=str(BASE/role):
        raise ValueError('Exact independent V4 role output root required')
    if len({x['event_id'] for x in events})!=len(events):
        raise ValueError('Original event identities must remain distinct')
    if any(x['source_role']!=role for x in events):
        raise ValueError('Role event list changed identity')
    if role=='confirm' and selection is None:
        raise ValueError('Confirmation registration waits for frozen development selection')
    reg=dict(template)
    reg.update(schema=SCHEMA,contract_revision=REVISION,status=STATUS,events=events,
        validation_scope='EXTERNAL_DEVELOPMENT_DIAGNOSTIC' if role=='dev' else 'EXTERNAL_CONFIRMATION_DIAGNOSTIC',
        source_scope='EXTERNAL_NONTEST_DEVELOPMENT_ONLY' if role=='dev' else 'EXTERNAL_NONTEST_CONFIRMATION_ONLY',
        selection_frozen_before_new_model_results=True,
        existing_sources_are_exposed_development_not_new_confirmation=role=='dev',
        confirmation_event_extraction_frozen_before_development_results=True,
        confirmation_metrics_sealed_until_development_selection_frozen=True,
        confirmation_event_extraction_path=extraction['path'],confirmation_event_extraction_sha256=extraction['sha256'],
        protocol_path=protocol['path'],protocol_sha256=protocol['sha256'],
        official_rule_check_path=rule['path'],official_rule_check_sha256=rule['sha256'],
        nominal_endpoint_count=2*len(events),max_model_call_budget=2*len(events),actual_model_call_budget=None,
        endpoint_sides=['start','end'],half_window_exact='3',frames_per_request=64,
        download_media=False,training=False,model_parameters=8782459120,optimizer_updates=0,
        structural_skip_policy='SHORT_NATIVE_CONTEXT_UNAVAILABLE_STATIC_UNKNOWN_ORIGINAL_POINT_NO_MODEL',
        actual_call_budget_source='plan_01/actual_call_budget.json, frozen after all original event endpoints counted',
        short_sides_remain_in_all_event_and_nominal_endpoint_denominators=True)
    required=dict(code_files)
    for value in (protocol,rule,extraction,selection):
        if value is not None:required[value['path']]=value['sha256']
    if selection is not None:
        reg.update(development_selection_path=selection['path'],development_selection_sha256=selection['sha256'])
    else:
        reg.pop('development_selection_path',None);reg.pop('development_selection_sha256',None)
    # Exact original input/proof/done/raw/request/replay/clock/separation refs
    # remain required; no media, annotation or mutable old V3 code dependency.
    for event in events:
        for value in list(event['original_evidence'].values())+event['reuse_rgb_inputs']:
            required[value['path']]=value['sha256']
    reg['required_files']=required
    return reg


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--template',required=True);p.add_argument('--role',choices=['dev','confirm'],required=True)
    p.add_argument('--events',required=True);p.add_argument('--code-dir',required=True)
    p.add_argument('--protocol',required=True);p.add_argument('--rule-check',required=True)
    p.add_argument('--extraction-completion',required=True);p.add_argument('--development-selection')
    p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output).resolve();base=out.parent
    code_files={str(x.resolve()):ref(x)['sha256'] for x in sorted(Path(a.code_dir).glob('*.py'))}
    events=read(a.events)
    reg=adapt(read(a.template),a.role,events,base,code_files,ref(a.protocol),ref(a.rule_check),
              ref(a.extraction_completion),ref(a.development_selection) if a.development_selection else None)
    reg['required_files'][str(Path(a.events).resolve())]=ref(a.events)['sha256']
    reg['required_files'][str(Path(__file__).resolve())]=ref(__file__)['sha256']
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as f:json.dump(reg,f,indent=2,ensure_ascii=False,allow_nan=False)
    print(json.dumps(dict(status='REGISTERED_V4_NOMINAL_SCOPE_NOT_PLANNED',path=str(out),sha256=ref(out)['sha256'],
        events=len(events),nominal_endpoint_count=2*len(events),max_model_call_budget=2*len(events),
        actual_model_call_budget=None,new_plan_runs=0,new_model_calls=0)))


if __name__=='__main__':main()
