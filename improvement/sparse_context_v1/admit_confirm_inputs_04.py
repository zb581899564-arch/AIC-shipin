"""Independent metadata/clock/proof review; no decoding, encoding or inference."""
from fractions import Fraction as F
from pathlib import Path

import confirm_run_common_04 as r
from native_profile_04 import native64_windows,validate_original_origin,validate_reference_endpoints


def main():
    cohort_path=r.BASE/'new_confirm_CPU_02/completion.json'
    complete=r.read(cohort_path)
    if (complete['status']!='PASS_FRESH_CONFIRM8_NATIVE64_CPU_INPUTS_PENDING_INDEPENDENT_ADMISSION' or
        complete['sources']!=8 or complete['screen']!=0 or complete['confirm']!=8 or
        complete['new_model_calls'] or complete['new_optimizer_updates'] or
        complete['source_selection_uses_predictions_or_quality_scores']):
        raise ValueError('Actual complete engineering8-source cohort required')
    accepted=complete['accepted']
    source_reg=r.read(r.BASE/'new_confirm_source_registration_01.json')
    allowed={x['video_id'] for x in source_reg['selection']+source_reg['ordered_engineering_reserves']}
    old_ids=set(source_reg['old_exposed_source_ids'])
    if any(x['video_id'] not in allowed or x['video_id'] in old_ids for x in accepted):
        raise ValueError('Fresh confirmation source identity overlaps exposed20 or unregistered pool')
    if len(accepted)!=8 or {x['slot'] for x in accepted}!=set(range(1,9)) or len({x['video_id'] for x in accepted})!=8:
        raise ValueError('Frozen source slots duplicated or missing')
    if sum(x['group']=='screen' for x in accepted)!=0 or sum(x['group']=='confirm' for x in accepted)!=8:
        raise ValueError('Frozen12/8 roles changed')
    proofs=[];runtime_identity=None;runtime_sha=None;sources=[]
    for source in accepted:
        vid=source['video_id']
        cpu_path=r.check_file(source['cpu_completion_path'],source['cpu_completion_sha256'])
        cpu=r.read(cpu_path)
        media=r.read(r.check_file(source['media_completion_path'],source['media_completion_sha256']))
        if cpu['status']!='PASS_FRESH_CONFIRM_BATCH_NATIVE64_CPU_INPUTS_NOT_GPU_ADMISSION' or cpu['new_model_calls'] or cpu['sources']!=1:
            raise ValueError('Each source actual CPU preparation required')
        original_ref=r.read(r.check_file(source['reference_path'],source['reference_sha256']))[0]
        if original_ref['video_id']!=vid or original_ref['group']!=source['group'] or len(original_ref['original_onehot'])!=10:
            raise ValueError('Original reference source/group/schema changed')
        if any(v not in (0,1) for values in original_ref['original_onehot'] for v in values):
            raise ValueError('Original one-second reference contains non-binary values')
        clock_path=cpu_path.parent/vid/'clock.json';mapping_path=clock_path.with_name('mapping.json')
        clock=r.read(clock_path);mapping=r.read(mapping_path)
        if mapping['clock_sha256']!=r.sha(clock_path):raise ValueError('Accepted actual source clock changed')
        validate_original_origin(clock)
        validate_reference_endpoints(clock,original_ref['annotator_intervals_exact_seconds'])
        windows=native64_windows(clock)
        if mapping['windows']!=windows or len(cpu['proofs'])!=len(windows) or len(source['proofs'])!=len(windows):
            raise ValueError('Actual native plan or CPU proof count changed')
        identity_path=cpu_path.parent/'processor_runtime_identity.json'
        identity=r.read(identity_path);identity_sha=r.sha(identity_path)
        if runtime_identity is None:runtime_identity,runtime_sha=identity,identity_sha
        elif identity!=runtime_identity or identity_sha!=runtime_sha:raise ValueError('Source processor/runtime identities differ')
        for media_member in media['members']:
            r.check_file(media_member['path'],media_member['sha256'],media_member['bytes'])
            if not media_member['known_identity_and_whole_file_byte_separation'] or media_member['video_id']!=vid:
                raise ValueError('Known source separation or accepted bytes changed')
        for entry,window in zip(source['proofs'],windows):
            proof=r.read(r.check_file(entry['proof_path'],entry['proof_sha256']))
            meta=r.read(r.check_file(entry['input_path'],entry['input_sha256']))
            if (proof['bindings']!=cpu['bindings'] or proof['runtime_identity_sha256']!=runtime_sha or
                proof['case_id']!=entry['case_id'] or proof['source_name']!=vid or meta['source_name']!=vid or
                meta['source_group']!=source['group'] or meta['all_source_exact_pts']!=clock['original_exact_pts'] or
                meta['source_frame_ordinals']!=window['source_frame_ordinals'] or meta['sample_exact_pts']!=window['sample_exact_pts'] or
                F(meta['window_start'])!=F(window['start_exact']) or F(meta['window_end'])!=F(window['end_exact']) or
                meta['reference_available_to_inference'] or meta['audio_observed']):
                raise ValueError('Actual cached native input differs from source plan')
            r.check_file(meta['frame_array_path'],meta['frame_array_sha256'])
            proofs.append(dict(entry,source_name=vid))
        sources.append(dict(video_id=vid,group=source['group'],slot=source['slot'],
            native_clock_path=str(clock_path),native_clock_sha256=r.sha(clock_path),
            reference_path=source['reference_path'],reference_sha256=source['reference_sha256']))
    r.save(r.ACCEPTANCE,dict(status='PASS_INDEPENDENT_FRESH_CONFIRM8_ACTUAL_CPU_INPUTS_BEFORE_B',
        registered_sources=8,accepted_sources=8,accepted_windows=len(proofs),cohort_completion_sha256=r.sha(cohort_path),
        proofs=proofs,sources=sources,runtime_identity=runtime_identity,runtime_identity_sha256=runtime_sha,
        model_parameters=8782459120,new_model_calls=0,new_optimizer_updates=0,utc=r.utc(),
        human_reference_not_model_input=True,requires_full_frozen_source_lock_and_unique_gpu_wrapper=True))
    r.inputs()
    print(__import__('json').dumps(dict(status='PASS_INDEPENDENT_FRESH8_INPUT_REVIEW',sources=8,windows=len(proofs),new_model_calls=0)))


if __name__=='__main__':main()
