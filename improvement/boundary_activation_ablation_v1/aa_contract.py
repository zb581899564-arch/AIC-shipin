"""Finite activation diagnostic: same successful two inputs, no quality gate."""
SCHEMA = 'LOCAL_BOUNDARY_ACTIVATION_ABLATION_V1'
PHYSICAL_PARAMETERS = 8782459120
BASE_PARAMETERS = 8767123696
ADAPTER_PARAMETERS = PHYSICAL_PARAMETERS-BASE_PARAMETERS
LORA_LAYERS = 144
MAX_CALLS = 2
REQUEST_IDS = ('SMOKE_ORIGINAL_SCREEN_001.start', 'SMOKE_ORIGINAL_SCREEN_001.end')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def protocol(value, source_root):
    require(value['schema'] == SCHEMA and value['hypothesis'] == 'LOCAL_BOUNDARY_TIME_ADAPTER_ACTIVATION_ABLATION' and
        value['validation_scope'] == 'PAIRED_TWO_CALL_SAME_INPUT_ACTIVATION_DIAGNOSTIC' and
        value['source_root'] == str(source_root) and value['max_new_model_calls'] == MAX_CALLS and
        value['actual_physical_parameters'] == PHYSICAL_PARAMETERS and
        value['activated_base_parameters'] == BASE_PARAMETERS and value['disable_time_adapter_layers'] == LORA_LAYERS and
        value['optimizer_updates'] == 0 and value['new_input_processor_encodes'] == 0 and value['new_media_decodes'] == 0 and
        value['coarse_and_verify_time_adapter_unchanged'] is True and
        value['old_base_only12_failed_status_and_cost_unchanged'] is True and
        value['quality_gate_or_change_based_selection_admitted'] is False,
        'Frozen same-input two-call local activation hypothesis is required')
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
