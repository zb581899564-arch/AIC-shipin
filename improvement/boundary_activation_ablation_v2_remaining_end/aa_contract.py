"""Finite activation diagnostic: same successful two inputs, no quality gate."""
SCHEMA = 'LOCAL_BOUNDARY_ACTIVATION_ABLATION_V2_REMAINING_END'
PHYSICAL_PARAMETERS = 8782459120
BASE_PARAMETERS = 8767123696
ADAPTER_PARAMETERS = PHYSICAL_PARAMETERS-BASE_PARAMETERS
LORA_LAYERS = 144
MAX_CALLS = 1
SOURCE_TIME_CALLS = 2
SOURCE_REQUEST_IDS = ('SMOKE_ORIGINAL_SCREEN_001.start', 'SMOKE_ORIGINAL_SCREEN_001.end')
REQUEST_IDS = ('SMOKE_ORIGINAL_SCREEN_001.end',)
WEIGHT_CHECK_STRATEGY = 'ENGINE_LOADED_IDENTITY_BEFORE_AND_FULL_REHASH_AFTER_SINGLE_CALL'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def protocol(value, source_root):
    require(value['schema'] == SCHEMA and value['hypothesis'] == 'LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION' and
        value['validation_scope'] == 'REMAINING_END_ONLY_WITH_PRIOR_START_UNACCEPTED_POST_STATE_PROOF' and
        value['source_root'] == str(source_root) and value['max_new_model_calls'] == MAX_CALLS and
        value['actual_physical_parameters'] == PHYSICAL_PARAMETERS and
        value['activated_base_parameters'] == BASE_PARAMETERS and value['disable_time_adapter_layers'] == LORA_LAYERS and
        value['optimizer_updates'] == 0 and value['new_input_processor_encodes'] == 0 and value['new_media_decodes'] == 0 and
        value['coarse_and_verify_time_adapter_unchanged'] is True and
        value['old_base_only12_failed_status_and_cost_unchanged'] is True and
        value['quality_gate_or_change_based_selection_admitted'] is False and
        value['weight_check_strategy'] == WEIGHT_CHECK_STRATEGY and value['no_repeat_started_start_call'] is True,
        'Frozen same-input remaining END-only activation recovery is required')
    require(isinstance(value['gpu_job_name'], str) and 1 <= len(value['gpu_job_name']) <= 100 and
            all(letter.isalnum() or letter in '_-' for letter in value['gpu_job_name']), 'New safe unique GPU job name required')


def layer_state(model, disabled, expected_names=None):
    layers = [(name, layer) for name, layer in model.named_modules()
              if hasattr(layer, 'disable_adapters') and hasattr(layer, 'lora_A')]
    names = [name for name, _ in layers]
    flags = [bool(layer.disable_adapters) for _, layer in layers]
    require(len(layers) == LORA_LAYERS and len(set(names)) == LORA_LAYERS and flags == [disabled]*LORA_LAYERS,
            'All actual 144 TIME LoRA layer activation states must match')
    require(expected_names is None or names == expected_names, 'TIME LoRA layer identity changed across disable context')
    require(model.active_adapter == 'default', 'Loaded original default adapter identity changed')
    return dict(layer_names=names, disable_adapters=flags, layers=LORA_LAYERS,
                active_adapter=model.active_adapter, activated_parameters=BASE_PARAMETERS if disabled else PHYSICAL_PARAMETERS)


def serialized_layer_state(value, disabled, expected_names=None):
    require(value['layers'] == LORA_LAYERS and len(value['layer_names']) == LORA_LAYERS and
            len(set(value['layer_names'])) == LORA_LAYERS and value['disable_adapters'] == [disabled]*LORA_LAYERS and
            value['active_adapter'] == 'default' and
            value['activated_parameters'] == (BASE_PARAMETERS if disabled else PHYSICAL_PARAMETERS) and
            (expected_names is None or value['layer_names'] == expected_names),
            'Recorded before/inside/after activation proof does not show all 144 states')


def parameter_inventory(model):
    seen, all_count, adapter_count = set(), 0, 0
    for name, parameter in model.named_parameters():
        if id(parameter) in seen:
            continue
        seen.add(id(parameter))
        require(not parameter.requires_grad, 'Activation-only model has a trainable parameter')
        all_count += parameter.numel()
        if 'lora_' in name:
            adapter_count += parameter.numel()
    require(all_count == PHYSICAL_PARAMETERS and adapter_count == ADAPTER_PARAMETERS and
            all_count-adapter_count == BASE_PARAMETERS, 'Physical/base/loaded adapter parameter inventory changed')
    return dict(actual_physical_parameters=all_count, loaded_adapter_parameters=adapter_count,
                activated_base_parameters=all_count-adapter_count, adapter_unloaded=False, optimizer_updates=0)


def restore_frozen_gradients(model):
    """PEFT re-enable changes requires_grad flags; restore, never optimize."""
    before = [(name,parameter.numel()) for name,parameter in model.named_parameters() if parameter.requires_grad]
    model.requires_grad_(False)
    after = [(name,parameter.numel()) for name,parameter in model.named_parameters() if parameter.requires_grad]
    require(not after, 'Explicit post-context gradient freeze failed')
    return dict(trainable_tensor_count_before_restore=len(before),
                trainable_parameters_before_restore=sum(count for _,count in before),
                trainable_tensor_names_before_restore=[name for name,_ in before],
                trainable_tensor_count_after_restore=0,trainable_parameters_after_restore=0,
                action='MODEL_REQUIRES_GRAD_FALSE_AFTER_PEFT_CONTEXT',optimizer_updates=0)
