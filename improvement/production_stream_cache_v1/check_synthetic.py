"""One CPU-only tiny tensor/lease/path test; no real data or model."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['CUDA_VISIBLE_DEVICES'] = ''
from codec import SCHEMA, SYNTHETIC_ROOT, exact_equal, signature
from leases import LeaseStore, PROOF_SCHEMA


def blocked(call, description):
    try:
        call()
    except (ValueError, FileExistsError):
        return description
    raise AssertionError('Unsafe operation accepted: '+description)


def main():
    import torch
    import numpy as np
    root = SYNTHETIC_ROOT
    report = root.parent
    report.mkdir(exist_ok=True)
    policy = dict(schema=SCHEMA, root=str(root.absolute()), mode='PURE_SYNTHETIC',
                  real_media_model_production_calls=0)
    store = LeaseStore.create(root, ['r1', 'r2', 'r3'], policy)
    # Preserve noncontiguous bfloat16 layout, plus exact token/mask input.
    pixels = torch.arange(64*3*2*2, dtype=torch.float32).reshape(64, 3, 2, 2).to(torch.bfloat16).transpose(2, 3)
    encoded1 = dict(input_ids=torch.tensor([[1, 2, 3]], dtype=torch.int64),
        attention_mask=torch.tensor([[True, True, True]]), pixel_values_videos=pixels,
        video_grid_thw=torch.tensor([[32, 1, 1]], dtype=torch.int64))
    encoded2 = {**encoded1, 'input_ids':torch.tensor([[1, 2, 4]], dtype=torch.int64)}
    identity = dict(source_sha256='1'*64, source_ordinals=list(range(64)),
        exact_pts=[str(__import__('fractions').Fraction(i, 25)) for i in range(64)],
        context_origin_exact='0', grid=[[32, 1, 1]],
        processor_assets={'fake-synthetic-tokenizer.json':'2'*64},
        preprocessing_code={'fake-synthetic-runtime.py':'3'*64})
    RGB_rel = 'staging/rgb/first.npz'
    RGB = store.path(RGB_rel, 'staging')
    arrays = np.arange(64*2*2*3, dtype=np.uint8).reshape(64, 2, 2, 3)
    with RGB.open('xb') as stream:
        np.savez_compressed(stream, rgb=arrays)
    RGB_ref = store.ref(RGB_rel, 'staging')
    metadata = dict(frame_array_path=str(RGB), frame_array_sha256=RGB_ref['sha256'],
        source_sha256=identity['source_sha256'], source_frame_ordinals=identity['source_ordinals'],
        sample_exact_pts=identity['exact_pts'],
        pixel_sha256=[hashlib.sha256(a.tobytes()).hexdigest() for a in arrays],
        validation_scope='PURE_SYNTHETIC_CODEC_NOT_NATIVE_OR_MODEL_ADMISSION')
    visual_keys = ['pixel_values_videos', 'video_grid_thw']
    manifests = {name:store.save_input(name, encoded, visual_keys, identity, metadata)
                 for name, encoded in [('r1', encoded1), ('r2', encoded2)]}
    saved1, _ = store.load_input('r1');saved2, _ = store.load_input('r2')
    assert exact_equal(encoded1, saved1) and exact_equal(encoded2, saved2)
    assert saved1['pixel_values_videos'].stride() == pixels.stride()
    assert not torch.equal(saved1['input_ids'], saved2['input_ids'])
    m1, m2 = [json.loads(store.checked_ref(manifests[k]).read_text()) for k in ('r1', 'r2')]
    assert m1['visual_ref'] == m2['visual_ref'] and m1['private_ref'] != m2['private_ref']
    # Different timestamp origin may not share the visual object even when bytes match.
    shifted = {**identity, 'context_origin_exact':'1'}
    m3_ref = store.save_input('r3', encoded1, visual_keys, shifted, metadata)
    m3 = json.loads(store.checked_ref(m3_ref).read_text())
    assert m3['visual_ref'] != m1['visual_ref']
    checks = ['exact_tensor_dict_gzip_readback_dtype_shape_stride_tokenmask',
              'same_visual_actual_bytes_shared_distinct_text_retained',
              'same_visual_bytes_different_time_identity_not_shared']
    checks.append(blocked(lambda:store.save_input('r1', encoded1, visual_keys, identity, metadata),
                          'successful_canonical_input_overwrite_rejected'))
    for path in ('../old/frames.npz', '/home/inspur/aic_video_work/old/frames.npz',
                 'G:/ai/AIC视频/reports/human_reference_iteration_20261013_v1/frames.npz',
                 'permanent/inputs/r1.private.pt.gz', 'staging/../old.bin'):
        checks.append(blocked(lambda p=path:store.path(p, 'staging'), 'old_absolute_or_nonstaging_path_rejected:'+path))
    store.register_rgb('lease1', RGB_rel, ['r1', 'r2'], metadata)
    checks.append(blocked(lambda:store.release_rgb('lease1'), 'missing_independent_consumer_proof_blocks_release'))
    assert RGB.exists()
    proof_refs, resource_refs, ledger_refs = {}, {}, {}
    for consumer in ('r1', 'r2'):
        evidence = {key:store.write_metadata(f'permanent/proofs/{consumer}_{key}.json',
                     {'scope':'PURE_SYNTHETIC', 'kind':key, 'actual_model_call':False})
                    for key in ('request', 'raw', 'done', 'CPU_input_proof')}
        proof = dict(schema=PROOF_SCHEMA, status='PASS_FIRST_INDEPENDENT_REPLAY', consumer=consumer,
            CPU_only=True, new_model_calls=0, first_independent_replay=True,
            prepare_pid=101, verifier_pid=202, input_manifest_ref=manifests[consumer],
            full_input_signature=signature(encoded1 if consumer=='r1' else encoded2),
            GPU_input_signature=signature(encoded1 if consumer=='r1' else encoded2),
            original_RGB_ref=RGB_ref, normal_processor_from_original_RGB_verified=True,
            output_token_decode_grammar_parser_native_verified=True,
            gpu_job_name='SYNTHETIC_NO_GPU', retained_evidence_refs=evidence,
            validation_scope='PURE_SYNTHETIC_NO_PROCESSOR_OR_GPU')
        proof_refs[consumer] = store.write_metadata(f'permanent/proofs/{consumer}_replay.json',proof)
        resource = dict(name='SYNTHETIC_NO_GPU',status='completed',exit_code=0,
                        validation_scope='PURE_SYNTHETIC_NOT_REAL_TERMINAL')
        resource_refs[consumer] = store.write_metadata(f'permanent/proofs/{consumer}_resource.json',resource)
        ledger_refs[consumer] = store.write_ledger_snapshot(f'permanent/proofs/{consumer}_ledger.jsonl',[resource])
    failed = store.write_metadata('permanent/proofs/failed_resource.json',
        dict(name='SYNTHETIC_NO_GPU',status='failed',exit_code=1))
    checks.append(blocked(lambda:store.accept_consumer('r1',proof_refs['r1'],failed,ledger_refs['r1']),
                          'nonnatural_failed_resource_blocks_acceptance'))
    duplicate = store.write_ledger_snapshot('permanent/proofs/duplicate_ledger.jsonl',
        [json.loads(store.checked_ref(resource_refs['r1']).read_text())]*2)
    checks.append(blocked(lambda:store.accept_consumer('r1',proof_refs['r1'],resource_refs['r1'],duplicate),
                          'duplicate_terminal_ledger_blocks_acceptance'))
    store.accept_consumer('r1',proof_refs['r1'],resource_refs['r1'],ledger_refs['r1'])
    checks.append(blocked(lambda:store.release_rgb('lease1'), 'second_frozen_consumer_lease_blocks_release'))
    assert RGB.exists()
    store.accept_consumer('r2',proof_refs['r2'],resource_refs['r2'],ledger_refs['r2'])
    receipt = store.release_rgb('lease1')  # Exactly one successful new temporary RGB release.
    assert receipt['RGB_present'] is False and not RGB.exists()
    state = store.staging_state('lease1')
    assert state['state']=='RELEASED' and state['historical_RGB_ref']==RGB_ref
    assert exact_equal(encoded1, store.load_input('r1')[0]) and exact_equal(encoded2, store.load_input('r2')[0])
    checks.append('one_new_synthetic_RGB_release_permanent_inputs_and_historical_SHA_retained')
    checks.append(blocked(lambda:store.release_rgb('lease1'), 'successful_release_not_repeated'))
    # Retained canonical corruption must block closure of another new staging lease.
    second = store.path('staging/rgb/second.bin','staging');second.write_bytes(b'SYNTHETIC_RGB_2')
    second_meta = {**metadata,'frame_array_path':str(second),'frame_array_sha256':store.ref('staging/rgb/second.bin','staging')['sha256']}
    store.register_rgb('lease2','staging/rgb/second.bin',['r3'],second_meta)
    checks.append(blocked(lambda:store.release_rgb('lease2'),'unaccepted_other_canonical_consumer_blocks_release'))
    # A symlink must be rejected before any external file is read or removed.
    external = report/'protected_synthetic_old_01.bin';external.write_bytes(b'PROTECTED_SYNTHETIC_SENTINEL')
    link = root/'staging/rgb/link.bin'
    try:
        os.symlink(external, link)
    except OSError as error:
        symlink_check = {'status':'SKIPPED_OS_PRIVILEGE_UNAVAILABLE','error':str(error)}
    else:
        checks.append(blocked(lambda:store.register_rgb('linklease','staging/rgb/link.bin',['r3'],second_meta),
                              'symlink_external_staging_escape_rejected'))
        assert external.read_bytes()==b'PROTECTED_SYNTHETIC_SENTINEL'
        symlink_check = {'status':'PASS_EXTERNAL_SYMLINK_REJECTED_SENTINEL_UNCHANGED'}
    capacity = store.capacity(shutil_disk_free(store)+1,0,0)
    assert capacity['status']=='STOP_RETAIN_ALL' and not capacity['automatic_precision_change']
    checks.append('insufficient_capacity_STOP_RETAIN_no_canonical_deletion_or_precision_change')
    assert not torch.cuda.is_initialized()
    result = dict(status='PASS_PURE_SYNTHETIC_CODEC_LEASE_TEST_NOT_PRODUCTION_ADMISSION',
        checks=checks,symlink_check=symlink_check,successful_new_temporary_RGB_releases=1,
        original_media_or_old_success_deletions=0,real_media_or_processor_or_model_calls=0,
        torch_version=torch.__version__,CUDA_initialized=False,code_sha256={
          p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
        fixture_root=str(root),retained_fixture_and_partial_failures=True,
        scientific_quality_claim=False)
    with (report/'synthetic_result_01.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False)
    print(json.dumps(result),flush=True)


def shutil_disk_free(store):
    import shutil
    return shutil.disk_usage(store.base).free


if __name__=='__main__':
    main()
