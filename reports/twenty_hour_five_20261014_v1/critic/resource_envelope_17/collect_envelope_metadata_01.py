"""One existing-proof/index/stat metadata collection. No weight/input bodies."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import socket

HOME = Path('/home/inspur/aic_video_work')
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CAMPAIGN = HOME/'twenty_hour_five_20261014_v1'
ROOT = CAMPAIGN/'resource_envelope_17'
TIME = CAMPAIGN/'local_boundary_v4/dev'
BASE = CAMPAIGN/'local_boundary_base_dev_v1'
CPU_COMPLETE = TIME/'cpu_01/completion.json'
MAX_INPUT_TOKENS = 16384


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path)
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def resource_fields(path):
    if not path.exists():
        return dict(path=str(path), present=False)
    value = read(path)
    candidates = {}
    def walk(node, prefix=''):
        if isinstance(node, dict):
            for key, child in node.items():
                here = prefix+'.'+key if prefix else key
                low = key.lower()
                if ('rss' in low or 'hwm' in low) and not isinstance(child,(dict,list)):
                    candidates[here] = child
                walk(child, here)
        elif isinstance(node, list):
            for ix, child in enumerate(node):
                walk(child,prefix+'['+str(ix)+']')
    walk(value)
    return dict(ref=ref(path), present=True, status=value.get('status'),
                recorded_RSS_or_HWM_fields=candidates,
                no_field_is_claimed_to_measure_GPU_cold_load_HWM=True)


def main():
    assert socket.gethostname() == 'inspur-NP5570M5'
    assert Path(__file__).resolve() == ROOT/'code/collect_envelope_metadata_01.py'
    assert not (ROOT/'completion_01.json').exists()
    config_path = RUN/'b_score_aligned_package_v4/config.json'
    engine_path = RUN/'b_score_aligned_package_v4/engine.py'
    config = read(config_path)
    engine = engine_path.read_text()
    assert 'torch_dtype=torch.bfloat16' in engine and "device_map={'': 'cuda:0'}" in engine and 'low_cpu_mem_usage=True' in engine
    model_path = BASE/'gpu_01/model_identity.json'
    model = read(model_path)
    actual_base_params = model['identity']['base']['parameters']
    assert actual_base_params == model['inventory']['activated_base_parameters'] == 8767123696
    adapter_params = model['inventory']['loaded_adapter_parameters']
    assert adapter_params == 15335424 and model['inventory']['actual_physical_parameters'] == 8782459120
    model_dir = Path(config['model_dir'])
    architecture_path = model_dir/'config.json'
    architecture = read(architecture_path)
    vision = architecture['vision_config']
    assert vision['spatial_merge_size'] == 2 and vision['patch_size'] == 16 and vision['temporal_patch_size'] == 2
    index_path = model_dir/'model.safetensors.index.json'
    index = read(index_path)
    base_bytes = actual_base_params*2
    assert index['metadata']['total_size'] == base_bytes
    shards = []
    for name in sorted(set(index['weight_map'].values())):
        assert Path(name).name == name
        path = model_dir/name
        info = path.stat()
        shards.append(dict(path=str(path), bytes=info.st_size, inode=info.st_ino,
                           mtime_ns=info.st_mtime_ns, weight_body_read_or_hashed=False))
    assert len(shards) == 4
    maximum_shard = max(row['bytes'] for row in shards)
    shard_manifest = dict(schema='CHECKPOINT_SHARD_INDEX_AND_STAT_ONLY_ENVELOPE_V1',
        model_identity_ref=ref(model_path), config_ref=ref(config_path), engine_ref=ref(engine_path),
        model_architecture_metadata_ref=ref(architecture_path),
        index_ref=ref(index_path), index_weight_payload_total_bytes=base_bytes,
        actual_loaded_base_parameters=actual_base_params, BF16_bytes_per_parameter=2,
        BF16_provenance='Actual saved loaded-base identity parameter count + existing loader torch.bfloat16 + index total_size equality',
        checkpoint_shards=shards, maximum_checkpoint_shard_bytes=maximum_shard,
        full_weights_body_reads_or_hashes=0)
    shard_path = ROOT/'checkpoint_shard_manifest_01.json'
    save(shard_path, shard_manifest)
    cpu = read(CPU_COMPLETE)
    assert cpu['status'] == 'PASS_ALL_NEW_LOCAL_BOUNDARY_CPU_INPUTS_NOT_GPU_ADMISSION' and len(cpu['proofs']) == 37
    observations = []
    for binding in cpu['proofs']:
        path = Path(binding['proof_path'])
        assert sha(path) == binding['proof_sha256']
        proof = read(path)
        assert proof['CPU_only'] is True and proof['CUDA_initialized'] is False and proof['new_model_calls'] == 0
        sig = proof['input_evidence']['tensor_signature']
        assert set(sig) == {'input_ids','attention_mask','pixel_values_videos','video_grid_thw'}
        assert sig['pixel_values_videos']['dtype'] == 'torch.float32'
        shape = sig['pixel_values_videos']['shape']
        assert len(shape) == 2 and shape[1] == 1536 and 0 < proof['input_tokens'] <= MAX_INPUT_TOKENS
        assert shape[0] <= 4*proof['input_tokens']
        observations.append(dict(request_id=proof['request_id'], proof_ref=ref(path),
            process_peak_rss_kib=proof['process_peak_rss_kib'],
            logical_tensor_payload_bytes=proof['logical_tensor_payload_bytes'], input_tokens=proof['input_tokens'],
            pixel_rows=shape[0], pixel_columns=shape[1], whole_process_peak_not_isolated_import_peak=True))
    peak = max(observations, key=lambda row:row['process_peak_rss_kib'])
    largest_input = max(observations, key=lambda row:row['logical_tensor_payload_bytes'])
    cpu_bytes = peak['process_peak_rss_kib']*1024
    cpu_envelope = dict(schema='CPU_EXISTING_PROCESS_PEAK_RESOURCE_ENVELOPE_V2',
        status='ACTUAL_EXISTING_PREPARE_WHOLE_PROCESS_PEAK_REUSED_AS_CONSERVATIVE_OVERHEAD',
        actual_peak_rss_kib=peak['process_peak_rss_kib'], actual_CPU_peak_rss_bytes=cpu_bytes,
        conservative_overhead_bound_bytes=cpu_bytes, actual_proof_ref=peak['proof_ref'],
        CPU_completion_ref=ref(CPU_COMPLETE), CPU_proof_count=37,
        isolated_import_peak_observed=False,
        whole_process_peak_includes_import_and_previous_input_allocations=True,
        source_specific_union_RGB_tensor_and_codec_memory_must_be_reserved_separately=True,
        measured_production_peak=False, new_import_model_processor_or_input_calls=0)
    cpu_path = ROOT/'CPU_resource_envelope_01.json'
    save(cpu_path, cpu_envelope)
    # Accepted inputs have at most 16384 merged visual+text tokens. Qwen3-VL
    # merge2x2 maps each visual token to 4 rows of 1536 float32 entries.
    # IDs/mask are both int64; reserve a full64-grid metadata payload too.
    prefill_code_bound = 4*MAX_INPUT_TOKENS*1536*4 + 2*MAX_INPUT_TOKENS*8 + 64*3*8
    assert prefill_code_bound >= largest_input['logical_tensor_payload_bytes']
    # Additional copies are explicit scheduling margins, not measured peaks.
    adapter_margin = 2*adapter_params*8
    cache_signature_margin = 3*prefill_code_bound
    host_bound = base_bytes+maximum_shard+cpu_bytes+prefill_code_bound+adapter_margin+cache_signature_margin
    resource_paths = [RUN/'controller/aic20h_charades_dev37_base_boundary_20261014_v1.resource.json',
        BASE/'controller_01/resource_before_wait.json', BASE/'controller_01/resource_before_run.json']
    time_admission = read(TIME/'gpu_admission.json')
    for key in ('gpu_job_name','job_name','name'):
        if isinstance(time_admission.get(key),str):
            resource_paths.append(RUN/'controller'/(time_admission[key]+'.resource.json'))
            break
    records = [resource_fields(path) for path in resource_paths]
    gpu_envelope = dict(schema='GPU_HOST_CODE_BOUNDED_RESOURCE_ENVELOPE_V2',
        status='OBSERVATION_UNAVAILABLE_WITH_CODE_BOUNDED_ENVELOPE',
        cold_load_HWM_observed=False, observed_BASE_host_peak_rss_bytes=None,
        observed_peak_proof_ref=None, steady_RSS_is_not_HWM=True,
        actual_base_BF16_bytes=base_bytes, maximum_checkpoint_shard_bytes=maximum_shard,
        actual_CPU_peak_rss_bytes=cpu_bytes,
        maximum_actual_logical_prefill_tensor_bytes=largest_input['logical_tensor_payload_bytes'],
        maximum_actual_logical_prefill_tensor_ref=largest_input['proof_ref'],
        maximum_prefill_tensor_code_bound_bytes=prefill_code_bound,
        prefill_bound_derivation=dict(max_input_tokens=MAX_INPUT_TOKENS, rows_per_merged_visual_token=4,
            float32_patch_row_columns=1536, float32_bytes=4, int64_ID_and_mask_bytes_per_token=16,
            metadata_grid_reserve_bytes=64*3*8, checked_existing_signature_count=37),
        explicit_additional_adapter_two_copy_at_8_bytes_per_parameter_margin=adapter_margin,
        explicit_additional_three_prefill_cache_signature_copy_margin_bytes=cache_signature_margin,
        conservative_host_memory_bound_bytes=host_bound, observed_host_peak_or_strict_allocator_max_claim=False,
        maximum_shard_manifest_ref=ref(shard_path), CPU_resource_envelope_ref=ref(cpu_path),
        model_identity_ref=ref(model_path), existing_loader_code_ref=ref(engine_path),
        model_architecture_metadata_ref=ref(architecture_path),
        required_future_same_processor_and_input_token_cap=MAX_INPUT_TOKENS,
        existing_resource_or_snapshot_metadata=records,
        new_GPU_host_disk_temporary_bytes=0, disk_note='Existing local checkpoint, cuda-only map and no model offload; actual registered batch raw/proof output reserved separately',
        applicability='Existing identical loader/weights/finite schema/accepted token cap; first real batch lifecycle and live capacity still required',
        new_model_calls=0, full_weight_body_reads_or_hashes=0)
    gpu_path = ROOT/'GPU_host_resource_envelope_01.json'
    save(gpu_path,gpu_envelope)
    obs_path = ROOT/'CPU_metadata_observations_01.json'
    save(obs_path,dict(schema='EXISTING37_CPU_METADATA_ONLY_RESOURCE_OBSERVATIONS_V1', observations=observations))
    complete = dict(schema='RESOURCE_ENVELOPE_METADATA_COMPLETION_17', status='COMPLETE_EXISTING_METADATA_ONLY_CODE_ENVELOPE_NOT_COLD_HWM_MEASUREMENT',
        code_ref=ref(Path(__file__)), CPU_envelope_ref=ref(cpu_path), GPU_envelope_ref=ref(gpu_path),
        shard_manifest_ref=ref(shard_path), CPU_observation_ref=ref(obs_path),
        CPU_actual_peak_rss_kib=peak['process_peak_rss_kib'], maximum_actual_logical_prefill_tensor_bytes=largest_input['logical_tensor_payload_bytes'],
        base_BF16_bytes=base_bytes, maximum_checkpoint_shard_bytes=maximum_shard,
        prefill_tensor_code_bound_bytes=prefill_code_bound, GPU_host_memory_code_envelope_bytes=host_bound,
        GPU_cold_load_HWM_observation_available=False, model_or_processor_or_decoder_calls=0, full_weight_body_hashes=0,
        old_proofs_or_files_modified=False)
    save(ROOT/'completion_01.json',complete)
    print(json.dumps(complete,sort_keys=True))


if __name__ == '__main__':
    main()
