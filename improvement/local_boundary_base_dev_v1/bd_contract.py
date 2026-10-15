"""Same-input TIME/BASE pairing; no optimizer, encoder, or quality selector."""
SCHEMA = 'LOCAL_BOUNDARY_BASE_PAIRED_ROLE_V1'
REGISTRATION_STATUS = 'FROZEN_LOCAL_BOUNDARY_BASE_PAIRED_ROLE_V1'
ADMISSION_STATUS = 'PASS_INDEPENDENT_LOCAL_BOUNDARY_BASE_PAIRED_GPU_ADMISSION'
PHYSICAL_PARAMETERS = 8782459120
BASE_PARAMETERS = 8767123696
ADAPTER_PARAMETERS = PHYSICAL_PARAMETERS-BASE_PARAMETERS
LORA_LAYERS = 144
WEIGHT_CHECK_STRATEGY = 'ENGINE_LOAD_BASE_AND_288_ADAPTER_BEFORE_FULL_REHASH_AFTER_JOB'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def counts(events, requests, skips):
    expected = {event['event_id']+'.'+side for event in events for side in ('start', 'end')}
    actual = [entry['request_id'] for entry in requests]
    skipped = [entry['request_id'] for entry in skips]
    require(len({e['event_id'] for e in events}) == len(events) and len(expected) == 2*len(events),
            'Every registered event must retain both nominal endpoints')
    require(len(set(actual+skipped)) == len(actual)+len(skipped) and set(actual+skipped) == expected,
            'Nominal/actionable/structural partition is incomplete or duplicated')
    for skip in skips:
        endpoint = skip['endpoint_result']
        require(skip['structural_status'] == 'SHORT_NATIVE_CONTEXT_UNAVAILABLE' and
                skip['actionable'] is False and skip['structural_skip'] is True and
                skip['actual_context_native_frames'] < 64 and
                endpoint['applied_decision'] == 'UNKNOWN_SHORT_NATIVE_CONTEXT_UNAVAILABLE' and
                endpoint['actual_model_call'] is False and endpoint['predeclared_skip'] is True and
                endpoint['changed'] is False and
                endpoint['original_endpoint_exact'] == endpoint['endpoint_exact'],
                'Only predeclared original-clock short-context skips can preserve original endpoints')
    require(all(r['actionable'] is True and r['structural_skip'] is False and
                r['actual_context_native_frames'] >= 64 for r in requests),
            'A callable endpoint has no accepted native64 context')
    return dict(nominal_endpoints=len(expected), actionable_requests=len(actual), structural_skips=len(skipped))


def protocol(value, role, source, denominators):
    require(value['schema'] == SCHEMA and value['role'] == role and value['source_root'] == str(source) and
            value['hypothesis'] == 'SAME_INPUT_LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION' and
            value['actual_model_call_budget'] == denominators['actionable_requests'] and
            all(value[k] == v for k, v in denominators.items()) and
            value['actual_physical_parameters'] == PHYSICAL_PARAMETERS and
            value['activated_base_parameters'] == BASE_PARAMETERS and value['disable_time_adapter_layers'] == 144 and
            value['optimizer_updates'] == 0 and value['new_input_processor_encodes'] == 0 and
            value['new_media_decodes'] == 0 and value['prior_TIME_completed_and_first_input_replay_required'] is True and
            value['same_prompt_grammar_native_conversion'] is True and
            value['weight_check_strategy'] == WEIGHT_CHECK_STRATEGY and
            value['independent_prefill_per_call'] is True and
            value['quality_claim_or_selection_by_this_driver'] is False,
            'Frozen single-factor same-input BASE pairing protocol missing or changed')
    require(role in ('dev', 'confirm'), 'Explicit registered source role required')
    require(isinstance(value['gpu_job_name'], str) and 1 <= len(value['gpu_job_name']) <= 100 and
            all(x.isalnum() or x in '_-' for x in value['gpu_job_name']), 'New safe unique shared GPU job name required')
    if role == 'dev':
        require(denominators == dict(nominal_endpoints=40, actionable_requests=37, structural_skips=3),
                'This dev scope is the unchanged original20/40 with37 callable and3 structural endpoints')


def gradients(model):
    rows = [(name, p.numel()) for name, p in model.named_parameters() if p.requires_grad]
    return dict(trainable_tensor_count=len(rows), trainable_parameters=sum(n for _, n in rows),
                trainable_tensor_names=[name for name, _ in rows])


def frozen_gradients(model):
    value = gradients(model)
    require(value['trainable_tensor_count'] == value['trainable_parameters'] == 0,
            'BASE inference requires all parameters frozen before and inside each call')
    return value


def layer_state(model, disabled, expected_names=None):
    rows = [(name, layer) for name, layer in model.named_modules()
            if hasattr(layer, 'disable_adapters') and hasattr(layer, 'lora_A')]
    names = [name for name, _ in rows]
    flags = [bool(layer.disable_adapters) for _, layer in rows]
    require(len(rows) == LORA_LAYERS and len(set(names)) == LORA_LAYERS and flags == [disabled]*LORA_LAYERS,
            'All actual144 TIME LoRA layer activation states must match')
    require(expected_names is None or names == expected_names, 'Loaded TIME layer identities changed')
    require(model.active_adapter == 'default', 'Original loaded default adapter identity changed')
    return dict(layer_names=names, disable_adapters=flags, layers=LORA_LAYERS, active_adapter='default',
                activated_parameters=BASE_PARAMETERS if disabled else PHYSICAL_PARAMETERS)


def serialized_state(value, disabled, names):
    require(value['layers'] == LORA_LAYERS and value['layer_names'] == names and
            len(names) == len(set(names)) == LORA_LAYERS and value['disable_adapters'] == [disabled]*LORA_LAYERS and
            value['active_adapter'] == 'default' and
            value['activated_parameters'] == (BASE_PARAMETERS if disabled else PHYSICAL_PARAMETERS),
            'Recorded all144 before/inside/after activation states differ')


def inventory(model):
    seen, all_count, adapter_count = set(), 0, 0
    for name, parameter in model.named_parameters():
        if id(parameter) in seen:
            continue
        seen.add(id(parameter))
        require(not parameter.requires_grad, 'Activation-only model has trainable parameters')
        all_count += parameter.numel()
        if 'lora_' in name:
            adapter_count += parameter.numel()
    require(all_count == PHYSICAL_PARAMETERS and adapter_count == ADAPTER_PARAMETERS,
            'Actual physical/base/loaded adapter inventory differs')
    return dict(actual_physical_parameters=all_count, loaded_adapter_parameters=adapter_count,
                activated_base_parameters=BASE_PARAMETERS, adapter_unloaded=False, optimizer_updates=0)


def restore_frozen_gradients(model):
    before = gradients(model)
    model.requires_grad_(False)
    after = frozen_gradients(model)
    return dict(before_restore=before, after_restore=after,
                action='MODEL_REQUIRES_GRAD_FALSE_AFTER_PEFT_CONTEXT', optimizer_updates=0)


def validate_restoration(before, inside, after, restored, names):
    serialized_state(before['layer_state'], False, names)
    serialized_state(inside['layer_state'], True, names)
    serialized_state(after['layer_state'], False, names)
    for value in (before['gradients'], inside['gradients'], after['gradients'], restored['after_restore']):
        require(value == dict(trainable_tensor_count=0, trainable_parameters=0, trainable_tensor_names=[]),
                'Recorded before/inside/restored gradient count is not zero')
    require(restored['action'] == 'MODEL_REQUIRES_GRAD_FALSE_AFTER_PEFT_CONTEXT' and
            restored['optimizer_updates'] == 0, 'Explicit post-PEFT gradient restoration is missing')
    observed = restored['before_restore']
    require(type(observed['trainable_tensor_count']) is int and observed['trainable_tensor_count'] >= 0 and
            type(observed['trainable_parameters']) is int and observed['trainable_parameters'] >= 0 and
            observed['trainable_tensor_count'] == len(set(observed['trainable_tensor_names'])),
            'Post-context pre-restore gradient observations are malformed')


def validate_journal(journal, ordered_ids, entries):
    require(len(journal) == 2*len(ordered_ids) and len(entries) == len(ordered_ids) and
            [e['request_id'] for e in entries] == ordered_ids, 'Complete unique BEGIN/ACCEPTED denominator required')
    for index, rid in enumerate(ordered_ids, 1):
        before, after = journal[2*(index-1):2*index]
        require(before['event'] == 'BEGIN_MODEL_CALL' and after['event'] == 'ACCEPTED_MODEL_CALL' and
                before['call_id'] == after['call_id'] == index and before['request_id'] == after['request_id'] == rid and
                after['done_path'] == entries[index-1]['done_path'] and
                after['done_sha256'] == entries[index-1]['done_sha256'], 'Actual journal order or done binding differs')
