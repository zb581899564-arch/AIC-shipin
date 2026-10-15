"""Read-only permanent exact input ABI for a separately admitted model driver."""
from pathlib import Path

import tp_io as io
from tp_contract import require
from tp_device import transfer_exact


def load_consumer(reg,consumer):
    lib=io.libraries(reg)
    store=lib['cache'].LeaseStore(reg['cache_root'])
    initialization=io.read(io.BASE/'cache_initialization.json')
    require(initialization['cache_root']==reg['cache_root'] and
            initialization['control_registration_path']==reg['_registration_path'] and
            initialization['control_registration_sha256']==reg['_registration_sha256'] and
            io.sha(Path(reg['cache_root'])/'policy.json')==initialization['policy_sha256'] and
            store.frozen_ref==initialization['frozen_consumers_ref'],'Cache root/policy/consumer lock changed')
    encoded,manifest_ref=store.load_input(consumer)
    manifest=io.read(store.checked_ref(manifest_ref))
    meta=manifest['original_metadata']
    proof_ref=store.ref('permanent/proofs/'+consumer+'_CPU_input.json')
    proof=io.read(store.checked_ref(proof_ref))
    require(meta['request_id']==consumer and proof['consumer']==consumer and
            proof['input_manifest_ref']==manifest_ref and proof['full_input_signature']==manifest['full_signature'] and
            proof['CPU_only'] is True and proof['actual_new_processor_encodes']==1 and proof['new_model_calls']==0,
            'Frozen request/first CPU proof/full input binding changed')
    require(lib['cache'].signature(encoded)==manifest['full_signature'],'Canonical complete dictionary differs')
    require(meta['reference_available_to_inference'] is False and meta['audio_observed'] is False and
            len(meta['source_frame_ordinals'])==len(set(meta['source_frame_ordinals']))==64,
            'Production input reference/native64 identity changed')
    role=reg['endpoint_model_role'] if meta['kind']=='ENDPOINT' else reg['verify_model_role']
    return dict(encoded=encoded,metadata=meta,manifest=manifest,input_manifest_ref=manifest_ref,
        CPU_input_proof_ref=proof_ref,store=store,libraries=lib,model_role=role,
        model_driver_still_requires_independent_admission=True)


def gpu_input(reg,consumer,device):
    """Caller must bind these signatures to its raw output and actual weight role."""
    loaded=load_consumer(reg,consumer)
    encoded,proof=transfer_exact(loaded['encoded'],device,loaded['manifest']['full_signature'])
    require(proof['actual_GPU_transfer'] is True,'Real model input requires a CUDA transfer')
    proof.update(consumer=consumer,input_manifest_ref=loaded['input_manifest_ref'],
        CPU_input_proof_ref=loaded['CPU_input_proof_ref'],model_role=loaded['model_role'],
        actual_weight_identity_verified=False,new_model_calls=0)
    return encoded,loaded['metadata'],proof
