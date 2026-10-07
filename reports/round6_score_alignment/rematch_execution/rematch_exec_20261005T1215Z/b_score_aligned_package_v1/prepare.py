"""Freeze tested B2 bytes, model identity and qualified existing source caches."""
from common import *
import ast


def node_identity(path, names=None):
    tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    if names is not None:
        tree.body = [node for node in tree.body if getattr(node,'name',None) in names]
        require({node.name for node in tree.body} == set(names), 'cache algorithm function missing')
    return ast.dump(tree, include_attributes=False)


def main():
    require(not (HERE/'source_lock.json').exists() and not (HERE/'registration.json').exists(), 'never reseal B2')
    require(read(HERE/'cpu_acceptance.json')['status']=='PASS_B2_CPU_CONTRACTS' and
            read(HERE/'processor_acceptance.json')['status']=='PASS_B2_REAL_PROCESSOR_AND_NATIVE_SOURCE', 'CPU acceptance incomplete')
    bind_helpers(); config=settings(); dependencies=set()
    receipt=Path(config['model_receipt']['path'])
    require(sha(receipt)==config['model_receipt']['sha256'], 'fixed model receipt changed')
    model_receipt=read(receipt)
    require(model_receipt['revision']==config['model_revision'], 'fixed model revision differs')
    dependencies.add(receipt)
    for item in model_receipt['completed']:
        path=Path(config['model_dir'])/item['name']
        require(sha(path)==item['sha256'], 'fixed base file changed: '+item['name'])
        dependencies.add(path)
    adapter=Path(config['b_adapter'])
    require(sha(adapter/'adapter_model.safetensors')==config['b_adapter_sha256'], 'trained B adapter changed')
    recipe=read(adapter/'adapter_config.json')
    require(recipe['r']==16 and recipe['lora_alpha']==32 and recipe['bias']=='none' and
            recipe['modules_to_save'] is None, 'trained B adapter recipe differs')
    dependencies.update((adapter/'adapter_model.safetensors',adapter/'adapter_config.json'))
    trained=Path(config['trained_B_report']); report=read(trained)
    require(report['status']=='PASS_FULL_INTERVAL_SFT_TRAINING_ENGINEERING' and report['epochs']==5 and
            report['optimizer_steps']==227 and report['adapter_model_sha256']==config['b_adapter_sha256'] and
            report['freeze_evidence']['adapter_off']['sha256']==config['expected_base_sha256'], 'original trained B lineage differs')
    dev=Path(config['existing_B_dev_decision'])
    require(read(dev)['status']=='PASS_FROZEN_WEAK_DEV_GATE', 'original B weak developer gate missing')
    dependencies.update((trained,dev))
    dependencies.update(BASELINE.rglob('*.py'))
    dependencies.update((RUN/'temporal_sft8b_v1'/name for name in ('sft_contract.py','train_sft.py','verify_saved_smoke.py')))
    runner=Path(config['current_runner'])
    dependencies.update((runner,runner.with_name('physical_capacity.py')))
    old=Path(config['cpu_cache_root'])
    old_lock=read(old/'source_lock.json')
    require(sha(old/'production.py')==old_lock['files'][str(old/'production.py')], 'original cached algorithm source changed')
    for name in ('field_contract.py','spatial_baseline.py'):
        require(node_identity(HERE/name)==node_identity(old/name), 'cache helper semantics differ: '+name)
    require(node_identity(HERE/'production.py',('OrdinalReader',)) == node_identity(old/'production.py',('OrdinalReader',)),
            'cache source decoder algorithm differs')
    require(node_identity(HERE/'contracts.py',('_strict_json','_unique_object','_reject_constant','parse_focus_norm')) ==
            node_identity(old/'contracts.py',('_strict_json','_unique_object','_reject_constant','parse_focus_norm')),
            'spatial coordinate parser differs from source cache')
    dependencies.update((old/name for name in ('source_lock.json','production.py','field_contract.py','spatial_baseline.py','contracts.py','config.json')))
    require(read(old/'config.json')['model_receipt']==config['model_receipt'] and
            read(old/'config.json')['model_dir']==config['model_dir'], 'cached native spatial model identity differs')
    bindings={}
    from field_contract import build_field_requests
    from production import field_frames
    for scope in ('nontest','rematch'):
        item,manifest,clocks=inputs(scope)
        dependencies.update((Path(item['manifest']),Path(item['registry'])))
        for record in read(item['registry'])['records']:
            dependencies.add(Path(record['clock_arrays']['path']))
        cache=old/(scope+'_01'); names=('schedule.stage.json','field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl')
        binding=dict(path=str(cache),manifest_sha256=item['manifest_sha256'],registry_sha256=item['registry_sha256'],
                     cpu_eligible=False,spatial_eligible=False,files={})
        if all((cache/name).is_file() for name in names):
            schedule=read(cache/'schedule.stage.json'); field=rows(cache/'field_frames.jsonl')
            desired={(r['video_id'],r['source_frame']):r for r in field_frames(manifest,clocks)}
            existing={(r['video_id'],r['source_frame']):r for r in field}
            requests=rows(cache/'anchor_requests.jsonl'); shots=rows(cache/'field_shots.jsonl')
            binding['cpu_eligible']=(schedule['status']=='PASS_TIME_INDEPENDENT_SOURCE_FIELD' and
                schedule['temporal_selection_used_for_boundaries'] is False and existing==desired and
                len(existing)==len(field)==len(desired) and build_field_requests(field,shots,8)==requests)
            if binding['cpu_eligible']:
                binding['files']={name:sha(cache/name) for name in names}
                for name,key in (('field_frames.jsonl','field_frames_sha256'),('field_shots.jsonl','shots_sha256'),('anchor_requests.jsonl','requests_sha256')):
                    require(binding['files'][name]==schedule[key], 'cached schedule hash differs')
                if (cache/'spatial.stage.json').is_file() and (cache/'anchor_output.jsonl').is_file():
                    spatial=read(cache/'spatial.stage.json')
                    if (spatial['status']=='PASS_STRICT_SOURCE_FIELD_SPATIAL' and spatial['invalid']==0 and
                        spatial['logical_parameters']==8767123696 and spatial['time_adapter_enabled'] is False):
                        outputs=rows(cache/'anchor_output.jsonl')
                        binding['spatial_eligible']=(len(outputs)==len(requests)==spatial['rows'] and all(
                            output['status']=='MODEL_OK' and output['used_fallback'] is False and
                            request['anchor_request_sha256']==output['anchor_request_sha256'] and
                            request['expected_pixel_sha256']==output['decoded_pixel_sha256']
                            for request,output in zip(requests,outputs)))
                        if binding['spatial_eligible']:
                            binding['files'].update({name:sha(cache/name) for name in ('spatial.stage.json','anchor_output.jsonl')})
                dependencies.update((cache/name for name in binding['files']))
        bindings[scope]=binding
    # A genuine same-8B non-test timing is required even if a new selection is all empty.
    from cost_contract import measured_spatial_cost
    old_cost=old/'nontest_01/spatial.stage.json'
    cost_path,cost=measured_spatial_cost([(old_cost,read(old_cost))])
    dependencies.add(old_cost)
    dependencies.add(RUN/'teacher_student_autopilot_v5/pilot_01/validated/validated_records.jsonl')
    write(HERE/'cache_bindings.json',dict(schema='B2_FROZEN_SOURCE_FIELD_REUSE_V1',scopes=bindings,
        temporal_reuse_allowed=False,original_spatial_seconds_per_anchor=cost,original_spatial_cost_receipt=cost_path,
        old_algorithms_semantically_equal=True,old_artifacts_modified=False))
    files={str(path):sha(path) for path in sorted(dependencies)}
    for path in HERE.iterdir():
        if path.is_file() and path.suffix in ('.py','.md','.json','.txt') and path.name!='source_lock.json':
            files[str(path)]=sha(path)
    write(HERE/'source_lock.json',dict(schema='B2_SCORE_ALIGNED_SOURCE_LOCK_V1',utc=utc(),files=files,
        model_revision=config['model_revision'],temporal_adapter_sha256=config['b_adapter_sha256'],
        new_optimizer_updates=0,old_frozen_sources_modified=False,actual_capacity_only=True,
        gpu_ledger_initial_offset_seconds=7200,automatic_return=False))
    print(json.dumps(dict(status='PASS_B2_SOURCE_BINDING',files=len(files),source_lock_sha256=sha(HERE/'source_lock.json'),
        cache_scopes={scope:{k:v for k,v in b.items() if k not in ('files',)} for scope,b in bindings.items()})),flush=True)


if __name__=='__main__':
    main()
