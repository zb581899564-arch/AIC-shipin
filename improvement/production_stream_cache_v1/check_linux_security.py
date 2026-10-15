"""New Linux-only synthetic safety branches skipped by Windows privilege limits."""
import hashlib
import json
import os
import socket
from pathlib import Path

os.environ['CUDA_VISIBLE_DEVICES']=''
from codec import SCHEMA, SYNTHETIC_ROOT, signature
from leases import LeaseStore, PROOF_SCHEMA


def blocked(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Unsafe operation was accepted')


def main():
    import torch
    require = lambda c: c or (_ for _ in ()).throw(AssertionError())
    require(os.name=='posix' and socket.gethostname()=='inspur-NP5570M5')
    root=SYNTHETIC_ROOT;report=root.parent
    store=LeaseStore.create(root,['secure'],dict(schema=SCHEMA,root=str(root),mode='PURE_SYNTHETIC'))
    protected=report/'protected_synthetic_01';protected.mkdir()
    sentinel=protected/'sentinel.bin';sentinel.write_bytes(b'PROTECTED_SYNTHETIC_SENTINEL')
    os.symlink(protected,root/'staging/rgb/outside')
    os.symlink(sentinel,root/'staging/rgb/link.bin')
    blocked(lambda:store.path('staging/rgb/outside/sentinel.bin','staging'))
    blocked(lambda:store.path('staging/rgb/link.bin','staging'))
    blocked(lambda:LeaseStore('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1'))
    RGB=store.path('staging/rgb/one.bin','staging');RGB.write_bytes(b'NEW_SYNTHETIC_RGB')
    RGBref=store.ref('staging/rgb/one.bin','staging')
    identity=dict(source_sha256='1'*64,source_ordinals=list(range(64)),
        exact_pts=[str(__import__('fractions').Fraction(i,25)) for i in range(64)],
        context_origin_exact='0',grid=[[32,1,1]],processor_assets={'fake':'2'*64},preprocessing_code={'fake':'3'*64})
    meta=dict(frame_array_path=str(RGB),frame_array_sha256=RGBref['sha256'],source_sha256='1'*64,
        source_frame_ordinals=identity['source_ordinals'],sample_exact_pts=identity['exact_pts'],pixel_sha256=['4'*64]*64)
    encoded=dict(input_ids=torch.tensor([[1,2]]),attention_mask=torch.tensor([[1,1]]),
                 pixel_values_videos=torch.tensor([[1.,2.]],dtype=torch.bfloat16))
    manifest=store.save_input('secure',encoded,['pixel_values_videos'],identity,meta)
    store.register_rgb('lease','staging/rgb/one.bin',['secure'],meta)
    evidence={k:store.write_metadata('permanent/proofs/'+k+'.json',dict(scope='PURE_SYNTHETIC',actual_model_call=False))
              for k in ('request','raw','done','CPU_input_proof')}
    proof=dict(schema=PROOF_SCHEMA,status='PASS_FIRST_INDEPENDENT_REPLAY',consumer='secure',CPU_only=True,
        new_model_calls=0,first_independent_replay=True,prepare_pid=101,verifier_pid=202,
        input_manifest_ref=manifest,full_input_signature=signature(encoded),GPU_input_signature=signature(encoded),
        original_RGB_ref=RGBref,normal_processor_from_original_RGB_verified=True,
        output_token_decode_grammar_parser_native_verified=True,gpu_job_name='SYNTHETIC_NO_GPU',
        retained_evidence_refs=evidence,validation_scope='PURE_SYNTHETIC_NO_PROCESSOR_OR_GPU')
    proofref=store.write_metadata('permanent/proofs/replay.json',proof)
    terminal=dict(name='SYNTHETIC_NO_GPU',status='completed',exit_code=0,validation_scope='PURE_SYNTHETIC_NOT_REAL_TERMINAL')
    resource=store.write_metadata('permanent/proofs/resource.json',terminal)
    ledger=store.write_ledger_snapshot('permanent/proofs/ledger.jsonl',[terminal])
    store.accept_consumer('secure',proofref,resource,ledger)
    # Missing canonical file blocks release. Temporarily move this synthetic file
    # within its same dedicated new permanent directory, then restore it unchanged.
    parsed=json.loads(store.checked_ref(manifest).read_text())
    private=store.checked_ref(parsed['private_ref']);holding=private.with_name(private.name+'.synthetic_hold')
    private.rename(holding)
    blocked(lambda:store.release_rgb('lease'))
    require(RGB.exists() and holding.exists())
    holding.rename(private)
    store.release_rgb('lease')
    require(not RGB.exists() and sentinel.read_bytes()==b'PROTECTED_SYNTHETIC_SENTINEL')
    require(store.staging_state('lease')['state']=='RELEASED' and not torch.cuda.is_initialized())
    store.load_input('secure')
    result=dict(status='PASS_LINUX_SYMLINK_FD_UNLINK_AND_CANONICAL_MISSING_BRANCH_SYNTHETIC_ONLY',
        checks=['external_symlink_file_rejected','external_symlink_ancestor_rejected','old_root_rejected_before_read',
                'missing_canonical_blocks_release','descriptor_relative_NOFOLLOW_new_RGB_release',
                'external_sentinel_unchanged','permanent_full_input_present_after_release'],
        successful_new_synthetic_RGB_releases=1,old_or_real_media_deletions=0,
        real_media_processor_model_production_calls=0,torch_version=torch.__version__,CUDA_initialized=False,
        code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')})
    with (report/'linux_security_result_01.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
