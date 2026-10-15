"""New small exact/race/lifecycle fixture only; no real input/model/processor."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys

from backend import ExactExtension, LOCK_ORDER, key_lock, require


def run(core_directory, fixture_root):
    import numpy as np
    import torch
    torch.set_num_threads(1)
    root = Path(fixture_root).absolute()
    require(sys.platform == 'linux' and root == Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/prospective_cache_backend_v1/pure_01') and
            not root.exists(), 'Unique dedicated new Linux synthetic fixture only')
    spec = importlib.util.spec_from_file_location('_new_backend_frozen_cache', Path(core_directory)/'__init__.py',
        submodule_search_locations=[str(core_directory)])
    library = importlib.util.module_from_spec(spec); sys.modules[spec.name] = library; spec.loader.exec_module(library)
    core = sys.modules[spec.name+'.codec']

    class Fixture(ExactExtension, library.LeaseStore):
        def __init__(self, base):
            # Test-only constructor: no production root policy is bypassed by
            # open_store, and this class is not exported by the backend API.
            require(Path(base).absolute() == root, 'Fixture owner escaped')
            self.base = root; self.policy = core.read(root/'policy.json')
            self.frozen = core.read(root/'permanent/frozen_consumers.json')
            self.consumers = set(self.frozen['consumers']); self.frozen_ref = self.ref('permanent/frozen_consumers.json')
            self._extension = dict(producer_consumers=['C0','C1','C2'], accept_consumers=['C0','C1','C2'], release_leases=['L0','L1'])
            self._extension_ref = dict(synthetic=True, schema='PURE_NEW_BACKEND_FIXTURE_NOT_PRODUCTION')
            self._legacy_codec_module = spec.name+'.codec'; self._global = False; self._forbid_decode = False
        @contextmanager
        def locked(self):
            with super().locked():
                require(not self._global, 'Nested global lock'); self._global = True
                try: yield
                finally: self._global = False
        def _save_tensors(self, relative, encoded):
            require(not self._global, 'Heavy tensor save ran under global journal lock')
            return super()._save_tensors(relative, encoded)
        def _load_tensors(self, ref):
            require(not self._global and not self._forbid_decode, 'Heavy tensor reconstruction in lifecycle/global lock')
            return super()._load_tensors(ref)

    root.mkdir(parents=True); (root/'permanent').mkdir(); (root/'staging/rgb').mkdir(parents=True)
    plan = dict(L0=dict(rgb_relative='staging/rgb/L0.npz', consumers=['C0','C1']),
                L1=dict(rgb_relative='staging/rgb/L1.npz', consumers=['C2']))
    policy = dict(schema=core.SCHEMA, root=str(root), mode='PURE_SYNTHETIC',
        process_lock_backend=core.LOCK_BACKEND, input_storage_codec='PIXEL_UINT8_BIT_LUT_V1', frozen_RGB_leases=plan)
    core.Store._write(root/'policy.json', policy)
    core.Store._write(root/'permanent/frozen_consumers.json', dict(schema=core.SCHEMA, consumers=['C0','C1','C2'],
        frozen_RGB_leases=plan, policy_sha256=core.sha(root/'policy.json')))
    store = Fixture(root)
    meta = {}
    for lease_id, row in plan.items():
        rgb = np.arange(64*2*2*3, dtype=np.uint8).reshape(64,2,2,3)
        path = root/row['rgb_relative']
        with path.open('xb') as stream: np.savez_compressed(stream, rgb=rgb)
        value = dict(frame_array_path=str(path), frame_array_sha256=core.sha(path), source_sha256='a'*64,
            source_frame_ordinals=list(range(64)), sample_exact_pts=[str(i)+'/25' for i in range(64)],
            pixel_sha256=[hashlib.sha256(frame.tobytes()).hexdigest() for frame in rgb])
        store.register_rgb(lease_id, row['rgb_relative'], row['consumers'], value); meta[lease_id] = value
    identity = dict(source_sha256='a'*64, source_ordinals=list(range(64)), exact_pts=meta['L0']['sample_exact_pts'],
        context_origin_exact='0', grid=[1,2,2], processor_assets={'synthetic':'b'*64}, preprocessing_code={'synthetic':'c'*64})
    patterns = np.array([0,0x80000000,0x7fc00001,0x7fc00002,0x3f800000,0xbf800000], dtype=np.uint32)
    pixel = torch.from_numpy(np.tile(patterns, 64).reshape(8,48).view(np.float32).copy())
    def encoded(i, pixels=pixel):
        return dict(input_ids=torch.tensor([[1,2,3,i]],dtype=torch.int64), attention_mask=torch.ones((1,4),dtype=torch.int64),
                    pixel_values_videos=pixels.clone(), video_grid_thw=torch.tensor([[1,2,2]],dtype=torch.int64))
    def worker(i, ready, start, queue):
        try:
            child = Fixture(root); ready.put(i); start.wait()
            ref = child.save_input('C'+str(i), encoded(i), ['pixel_values_videos','video_grid_thw'], identity, meta['L0'])
            got, _ = child.load_input('C'+str(i))
            require(core.exact_equal(encoded(i), got), 'Concurrent exact reconstruction failed')
            queue.put(dict(id=i, ok=True, manifest_ref=ref))
        except BaseException as error: queue.put(dict(id=i,ok=False,error=repr(error)))
    context = mp.get_context('fork'); ready = context.Queue(); results = context.Queue(); start = context.Event()
    processes = [context.Process(target=worker,args=(i,ready,start,results)) for i in (0,1)]
    for process in processes: process.start()
    for _ in processes: ready.get(timeout=30)
    start.set(); rows = [results.get(timeout=60) for _ in processes]
    for process in processes: process.join(timeout=60); require(process.exitcode == 0, 'New fixture child failed')
    require(all(row['ok'] for row in rows), 'Concurrent backend failure: '+repr(rows))
    manifests = [core.read(root/'permanent/inputs'/('C'+str(i)+'.json')) for i in (0,1)]
    require(manifests[0]['visual_ref'] == manifests[1]['visual_ref'] and
            len(list((root/'permanent/visual').glob('*.json'))) == 1, 'Same actual visual key did not deduplicate once')
    guards = {p.name:[p.stat().st_dev,p.stat().st_ino] for p in (root/'permanent/prospective_key_locks').glob('*.lock')}
    try:
        with key_lock(store,'consumer','e'*64): raise RuntimeError('intentional new lock exception fixture')
    except RuntimeError: pass
    with key_lock(store,'consumer','e'*64): pass
    require(all([p.stat().st_dev,p.stat().st_ino] == guards[p.name] for p in
                (root/'permanent/prospective_key_locks').glob('*.lock') if p.name in guards), 'Guard inode removed/replaced')
    overflow = torch.arange(8*768,dtype=torch.float32).reshape(8,768)
    id2 = dict(identity, grid=[1,4,4]); store.save_input('C2',encoded(2,overflow),['pixel_values_videos','video_grid_thw'],id2,meta['L1'])
    got,_ = store.load_input('C2'); require(core.exact_equal(encoded(2,overflow),got), 'Overflow fallback changed bytes')
    require(core.read(root/'permanent/inputs/C2.json')['visual_ref']['codec_report']['pixel_values_videos']['storage']=='ORIGINAL_TORCH_GZIP',
            'Unique>256 fallback did not preserve original tensors')

    resource_ref = store.write_metadata('permanent/proofs/resource.json',dict(name='synthetic-only',status='completed',exit_code=0,
        validation_scope='PURE_SYNTHETIC_NOT_REAL_TERMINAL'))
    ledger_ref = store.write_ledger_snapshot('permanent/proofs/ledger.jsonl',[core.read(store.checked_ref(resource_ref))])
    store._forbid_decode = True  # All lifecycle paths must now remain tensor-free.
    def acceptance(i):
        consumer='C'+str(i); manifest, manifest_ref=store.canonical_byte_binding(consumer)
        rgb_ref=store.ref('staging/rgb/L0.npz','staging')
        refs={key:store.write_metadata('permanent/proofs/'+consumer+'_'+key+'.json',
            dict(synthetic=True,actual_model_call=False)) for key in ('request','raw','done','CPU_input_proof')}
        first=store.write_metadata('permanent/proofs/'+consumer+'_first.json',dict(
            status='PASS_FIRST_INDEPENDENT_INPUT_REPLAY_ONLY_NOT_LEASE_ACCEPTANCE',consumer=consumer,CPU_only=True,
            first_independent_input_replay=True,normal_processor_from_original_RGB_verified=True,
            actual_first_independent_processor_encodes=1,input_manifest_ref=manifest_ref,full_input_signature=manifest['full_signature'],
            original_RGB_ref=rgb_ref,resource_ref=resource_ref,ledger_ref=ledger_ref,prepare_pid=1,verifier_pid=2,
            CPU_input_proof_ref=refs['CPU_input_proof'],new_model_calls=0,new_source_decodes=0,
            fixture_is_synthetic_not_actual_processor=True))
        refs['first_independent_input_replay']=first
        proof=store.write_metadata('permanent/proofs/'+consumer+'_proof.json',dict(schema='CACHE_FIRST_INDEPENDENT_REPLAY_ACCEPTANCE_V1',
            status='PASS_FIRST_INDEPENDENT_REPLAY',consumer=consumer,CPU_only=True,new_model_calls=0,first_independent_replay=True,
            prepare_pid=1,verifier_pid=3,input_manifest_ref=manifest_ref,full_input_signature=manifest['full_signature'],
            GPU_input_signature=manifest['full_signature'],normal_processor_from_original_RGB_verified=True,
            output_token_decode_grammar_parser_native_verified=True,actual_weight_identity_verified=True,
            original_RGB_ref=rgb_ref,gpu_job_name='synthetic-only',retained_evidence_refs=refs,
            fixture_is_synthetic_not_actual_replay=True))
        store.accept_consumer(consumer,proof,resource_ref,ledger_ref)
    acceptance(0)
    try: store.release_rgb('L0')
    except ValueError: pass
    else: raise ValueError('Pending consumer failed to block release')
    acceptance(1); release=store.release_rgb('L0')
    require(release['RGB_present'] is False and release['canonical_files_retained'] is True, 'First closure/release failed')
    try: store.accept_consumer('C1',store.ref('permanent/proofs/C1_proof.json'),resource_ref,ledger_ref)
    except ValueError: pass
    else: raise ValueError('Repeated acceptance was allowed')
    # Corruption rejection on an unused synthetic canonical payload; no repair,
    # production file, media, model or successful real proof is touched.
    m2=core.read(root/'permanent/inputs/C2.json'); payload=store.checked_ref(m2['private_ref'])
    with payload.open('ab') as stream:stream.write(b'new-fixture-corruption')
    try: store.canonical_byte_binding('C2')
    except ValueError: pass
    else: raise ValueError('Actual payload mutation was not rejected')
    for kind,key,mode in [('visual','f'*64,'symlink'),('consumer','d'*64,'hardlink')]:
        guard=root/'permanent/prospective_key_locks'/(kind+'_'+key+'.lock')
        original=root/'permanent/prospective_key_locks'/('consumer_'+'e'*64+'.lock')
        if mode=='symlink':guard.symlink_to(original)
        else:os.link(original,guard)
        try:
            with key_lock(store,kind,key):pass
        except (ValueError,OSError):pass
        else:raise ValueError('Unsafe '+mode+' guard accepted')
    result=dict(status='PASS_NEW_PROSPECTIVE_BACKEND_SYNTHETIC_RACE_EXACT_AND_BYTE_ONLY_LIFECYCLE',
        checks=['two_process_same_visual_exact_once','global_lock_no_tensor_work','NaN_payload_signed_zero_bit_exact',
            'unique_gt256_original_fallback','guard_inode_retained_on_exception','pending_consumer_blocks_release',
            'lifecycle_no_tensor_reconstruction','actual_payload_mutation_rejected','repeat_accept_rejected',
            'symlink_hardlink_guard_rejected'],fixture_root=str(root),model_calls=0,processor_encodes=0,media_decodes=0,
        production_cache_modified=False,old_successful_checks_repeated=False,synthetic_not_production_admission=True,
        lock_order=LOCK_ORDER)
    core.Store._write(root/'completion.json',result)
    return result
