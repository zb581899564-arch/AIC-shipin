"""Only final frozen-graph/lease-mutation guards; no repeated codec/model stage."""
import hashlib
import json
from pathlib import Path
from codec import Store, SYNTHETIC_ROOT
from leases import LeaseStore


def blocked(call):
    try:call()
    except ValueError:return
    raise AssertionError('Frozen-contract mutation was accepted')


def main():
    valid=dict(mode='PRODUCTION',frozen_RGB_leases={'fixed':dict(rgb_relative='staging/rgb/fixed.npz',consumers=['a','b'])})
    assert Store.validate_RGB_plan(['a','b'],valid)==valid['frozen_RGB_leases']
    blocked(lambda:Store.validate_RGB_plan(['a','b'],dict(mode='PRODUCTION')))
    blocked(lambda:Store.validate_RGB_plan(['a','b'],dict(mode='PRODUCTION',frozen_RGB_leases={
        'fixed':dict(rgb_relative='staging/rgb/fixed.npz',consumers=['a'])})))
    blocked(lambda:Store.validate_RGB_plan(['a','b'],dict(mode='PRODUCTION',frozen_RGB_leases={
        'fixed':dict(rgb_relative='staging/rgb/fixed.npz',consumers=['a','b','b'])})))
    blocked(lambda:Store.validate_RGB_plan(['a'],dict(mode='PRODUCTION',frozen_RGB_leases={
        'fixed':dict(rgb_relative='../old/fixed.npz',consumers=['a'])})))
    store=LeaseStore(SYNTHETIC_ROOT)
    rgb_rel='staging/rgb/guard_addition.bin';rgb=store.path(rgb_rel,'staging');rgb.write_bytes(b'NEW_SYNTHETIC_GUARD_FIXTURE')
    manifest=json.loads(store.path('permanent/inputs/secure.json','permanent').read_text())
    metadata={**manifest['original_metadata'],'frame_array_path':str(rgb),'frame_array_sha256':store.ref(rgb_rel,'staging')['sha256']}
    store.register_rgb('guard_addition',rgb_rel,['secure'],metadata)
    lease=store.path('permanent/leases/guard_addition.json','permanent')
    original=lease.read_bytes();tampered=json.loads(original);tampered['consumers']=[]
    # A new synthetic metadata fault, retained as a separate diagnostic file.
    bad=json.dumps(tampered,sort_keys=True).encode()
    with (SYNTHETIC_ROOT.parent/'tampered_synthetic_lease_02.json').open('xb') as f:f.write(bad)
    lease.write_bytes(bad)
    try:blocked(lambda:store.release_rgb('guard_addition'))
    finally:lease.write_bytes(original)
    assert rgb.exists()
    result=dict(status='PASS_FINAL_GRAPH_AND_ORIGINAL_LEASE_SHA_GUARDS_PURE_SYNTHETIC',
        checks=['missing_frozen_RGB_graph_rejected','missing_consumer_rejected','duplicate_consumer_rejected',
                'escaped_frozen_RGB_path_rejected','tampered_empty_lease_rejected_before_release'],
        additional_RGB_releases=0,real_media_processor_model_production_calls=0,old_success_deletions=0,
        code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')})
    with (SYNTHETIC_ROOT.parent/'contract_additions_result_02.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
