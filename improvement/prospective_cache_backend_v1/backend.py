"""Prospective exact producer and byte-bound lifecycle extension.

No old policy, code, successful input, tensor or lifecycle event is rewritten.
Activation requires a new main-owned admission after a quiescent handoff.
"""
from contextlib import contextmanager, nullcontext
from fractions import Fraction
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import re
import stat
import sys

SCHEMA = 'PROSPECTIVE_EXACT_CACHE_BACKEND_V1'
LOCK_ORDER = 'CONSUMER_THEN_VISUAL_THEN_GLOBAL'
PROOF_SCHEMA = 'CACHE_FIRST_INDEPENDENT_REPLAY_ACCEPTANCE_V1'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def checked_external(ref):
    path = Path(ref['path']).absolute()
    require(path.is_file() and sha(path) == ref['sha256'], 'Extension evidence/code changed')
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'Extension evidence/code cannot follow a link')
    if 'bytes' in ref:
        require(path.stat().st_size == ref['bytes'], 'Extension evidence size changed')
    return path


@contextmanager
def key_lock(store, kind, key):
    """Persistent descriptor-relative Linux flock; never remove its guard.

    No caller may hold the global journal lock while acquiring a key lock.
    The only acquisition order is consumer -> visual -> global.
    """
    require(sys.platform == 'linux' and kind in ('consumer', 'visual') and
            re.fullmatch(r'[0-9a-f]{64}', key), 'Explicit Linux key lock required')
    import fcntl
    directory = store.path('permanent/prospective_key_locks', 'permanent')
    directory.mkdir(exist_ok=True)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fds = []; guard = None; acquired = False
    name = kind+'_'+key+'.lock'
    try:
        current = os.open('/', flags); fds.append(current)
        for part in store.base.parts[1:]+('permanent', 'prospective_key_locks'):
            current = os.open(part, flags, dir_fd=current); fds.append(current)
        guard = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                        0o600, dir_fd=current)
        os.set_inheritable(guard, False)
        def identity():
            opened = os.fstat(guard)
            named = os.stat(name, dir_fd=current, follow_symlinks=False)
            require(stat.S_ISREG(opened.st_mode) and stat.S_ISREG(named.st_mode) and
                    opened.st_nlink == named.st_nlink == 1 and opened.st_size == named.st_size == 0 and
                    (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino),
                    'Persistent key guard replaced, linked or nonempty')
            return opened.st_dev, opened.st_ino
        original = identity()
        fcntl.flock(guard, fcntl.LOCK_EX); acquired = True
        require(identity() == original, 'Key guard changed while waiting')
        opened = os.fstat(current); named = directory.stat()
        require((opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino),
                'Key lock directory replaced while waiting')
        os.fsync(guard); os.fsync(current)
        yield
    finally:
        if guard is not None:
            try:
                if acquired: fcntl.flock(guard, fcntl.LOCK_UN)
            finally: os.close(guard)
        for fd in reversed(fds): os.close(fd)


class ExactExtension:
    """Mixin for the frozen LeaseStore. Original load/codec/unlink remain exact."""
    def _allowed(self, phase, item):
        require(item in self._extension[phase], 'This prospective phase/item was not admitted')

    def _core(self):
        return importlib.import_module(self._legacy_codec_module)

    def canonical_byte_binding(self, consumer):
        """Check every actual reachable byte without reconstructing torch tensors.

        First ordinary-processor replay already establishes tensor/CRC/layout
        equality against this exact manifest and these exact payload hashes.
        This method is not a replacement for producer or first input replay.
        """
        core = self._core(); core.valid_id(consumer)
        require(consumer in self.consumers, 'Unfrozen canonical consumer')
        ref = self.ref('permanent/inputs/'+consumer+'.json')
        manifest = read(self.checked_ref(ref))
        require(manifest['schema'] == core.SCHEMA and manifest['consumer'] == consumer and
                manifest['retained_exact_full_input'] is True and
                manifest['model_calls_in_this_module'] == 0 and
                manifest['RGB_role'] == 'EPHEMERAL_NATIVE_RGB_STAGING' and
                set(manifest['identity']) == core.IDENTITY_FIELDS,
                'Complete canonical input manifest identity is missing')
        private = manifest['private_keys']; visual = manifest['visual_keys']
        tensors = manifest['full_signature']['tensors']
        require(private == sorted(set(private)) and visual == sorted(set(visual)) and
                not set(private) & set(visual) and set(private) | set(visual) == set(tensors) and
                {'input_ids', 'attention_mask'} <= set(private) and
                set(visual) <= core.VISUAL_KEYS and bool(visual) == bool(manifest['visual_ref']),
                'Complete private/visual tensor partition changed')
        refs = [manifest['private_ref']] + ([manifest['visual_ref']] if visual else [])
        for payload in refs:
            path = self.checked_ref(payload)
            require(path.suffixes[-2:] == ['.pt', '.gz'] and
                    payload.get('storage_codec', 'TORCH_GZIP_LOSSLESS') in
                    ('TORCH_GZIP_LOSSLESS', 'PIXEL_UINT8_BIT_LUT_V1'),
                    'Canonical lossless payload format changed')
        return manifest, ref

    def save_input(self, consumer, encoded, visual_keys, identity, metadata):
        """Exact prepare, per-key heavy work, then short global commit.

        A partial payload is retained and blocks implicit retry. All readers
        still need the committed full manifest/source completion barrier.
        """
        self._allowed('producer_consumers', consumer)
        core = self._core(); core.valid_id(consumer)
        require(consumer in self.consumers, 'Frozen denominator changed')
        expected = core.signature(encoded)
        require({'input_ids', 'attention_mask'} <= set(encoded), 'Full token input required')
        require(isinstance(visual_keys, (list, tuple)) and len(set(visual_keys)) == len(visual_keys) and
                set(visual_keys) <= core.VISUAL_KEYS and set(visual_keys) <= set(encoded),
                'Invalid visual/private partition')
        require(set(identity) == core.IDENTITY_FIELDS and re.fullmatch(r'[0-9a-f]{64}', identity['source_sha256']) and
                len(identity['source_ordinals']) == len(identity['exact_pts']) == 64 and
                all(type(i) is int and i >= 0 for i in identity['source_ordinals']) and
                all(a < b for a, b in zip(identity['source_ordinals'], identity['source_ordinals'][1:])),
                'Exact distinct native64 visual identity required')
        pts = [Fraction(p) for p in identity['exact_pts']]
        require(all(isinstance(p, str) for p in identity['exact_pts']) and
                all(a < b for a, b in zip(pts, pts[1:])) and
                isinstance(identity['context_origin_exact'], str), 'Exact native PTS/context required')
        Fraction(identity['context_origin_exact'])
        for field in ('processor_assets', 'preprocessing_code'):
            require(isinstance(identity[field], dict) and identity[field] and
                    all(re.fullmatch(r'[0-9a-f]{64}', value) for value in identity[field].values()),
                    'Actual processor/code SHA identity required')
        selected = set(visual_keys)
        if any(set(group) & selected and set(group)-selected for group in expected['alias_groups']): selected = set()
        visual = {key: value for key, value in encoded.items() if key in selected}
        private = {key: value for key, value in encoded.items() if key not in selected}
        manifest_rel = 'permanent/inputs/'+consumer+'.json'
        consumer_key = hashlib.sha256(consumer.encode()).hexdigest()
        with key_lock(self, 'consumer', consumer_key):
            require(not self.path(manifest_rel, 'permanent').exists(), 'Successful input cannot repeat')
            visual_ref = None
            if visual:
                key_data = dict(identity=identity, visual_signature=core.signature(visual))
                key = hashlib.sha256(core.json_bytes(key_data)).hexdigest()
                with key_lock(self, 'visual', key):
                    index_rel = 'permanent/visual/'+key+'.json'
                    index_path = self.path(index_rel, 'permanent')
                    if index_path.exists():
                        previous = read(index_path)
                        require(previous['schema'] == core.SCHEMA and previous['key_data'] == key_data,
                                'Visual key collision/identity change')
                        restored = self._load_tensors(previous['tensor_ref'])
                        require(core.exact_equal(visual, restored), 'Hash-only visual dedup is forbidden')
                        visual_ref = previous['tensor_ref']
                    else:
                        # Frozen codec performs LUT exact validation, gzip CRC,
                        # complete signature and actual byte-equality readback.
                        visual_ref = self._save_tensors('permanent/visual/'+key+'.pt.gz', visual)
                        with self.locked():
                            self.checked_ref(self.frozen_ref)
                            require(not index_path.exists(), 'Visual index changed despite key lock')
                            self._write(index_path, dict(schema=core.SCHEMA, key_data=key_data, tensor_ref=visual_ref))
            private_ref = self._save_tensors('permanent/inputs/'+consumer+'.private.pt.gz', private)
            restored = self._load_tensors(private_ref)
            if visual_ref:
                restored_visual = self._load_tensors(visual_ref)
                require(not set(restored) & set(restored_visual), 'Overlapping tensor partition')
                restored.update(restored_visual)
            require(core.signature(restored) == expected and core.exact_equal(encoded, restored),
                    'Full actual tensor roundtrip failed before manifest commit')
            manifest = dict(schema=core.SCHEMA, consumer=consumer, full_signature=expected,
                identity=identity, original_metadata=metadata, visual_keys=sorted(selected),
                private_keys=sorted(private), visual_ref=visual_ref, private_ref=private_ref,
                retained_exact_full_input=True, RGB_role='EPHEMERAL_NATIVE_RGB_STAGING', model_calls_in_this_module=0,
                prospective_backend_ref=self._extension_ref, producer_complete_bit_exact_roundtrip=True,
                producer_lock_order=LOCK_ORDER)
            with self.locked():
                self.checked_ref(self.frozen_ref)
                require(not self.path(manifest_rel, 'permanent').exists(), 'Input concurrently committed')
                self._write(self.path(manifest_rel, 'permanent'), manifest)
                self._append(dict(event='PROSPECTIVE_INPUT_EXACT_COMMITTED', consumer=consumer,
                    input_manifest_ref=self.ref(manifest_rel), prospective_backend_ref=self._extension_ref,
                    full_roundtrip_verified=True, exact_visual_dedup_verified=True, model_calls_in_this_module=0))
            return self.ref(manifest_rel)

    def accept_consumer(self, consumer, proof_ref, resource_ref, ledger_ref):
        self._allowed('accept_consumers', consumer)
        with self.locked():
            self.checked_ref(self.frozen_ref)
            require(not any(row.get('event') == 'CONSUMER_ACCEPTED' and row.get('consumer') == consumer
                            for row in self._rows()), 'First acceptance cannot repeat')
            manifest, manifest_ref = self.canonical_byte_binding(consumer)
            proof = read(self.checked_ref(proof_ref)); resource = read(self.checked_ref(resource_ref))
            ledger = [json.loads(line) for line in self.checked_ref(ledger_ref).read_text().splitlines() if line]
            require(proof['schema'] == PROOF_SCHEMA and proof['status'] == 'PASS_FIRST_INDEPENDENT_REPLAY' and
                    proof['consumer'] == consumer and proof['CPU_only'] is True and proof['new_model_calls'] == 0 and
                    proof['first_independent_replay'] is True and type(proof['prepare_pid']) is int and
                    type(proof['verifier_pid']) is int and proof['prepare_pid'] != proof['verifier_pid'] and
                    proof['input_manifest_ref'] == manifest_ref and
                    proof['full_input_signature'] == proof['GPU_input_signature'] == manifest['full_signature'] and
                    proof['normal_processor_from_original_RGB_verified'] is True and
                    proof['output_token_decode_grammar_parser_native_verified'] is True and
                    proof['actual_weight_identity_verified'] is True, 'Real full independent acceptance proof incomplete')
            rgb_ref = proof['original_RGB_ref']; rgb_path = self.checked_ref(rgb_ref, 'staging')
            require(manifest['original_metadata']['frame_array_path'] == str(rgb_path) and
                    manifest['original_metadata']['frame_array_sha256'] == rgb_ref['sha256'], 'Original RGB binding changed')
            require(resource['status'] == 'completed' and type(resource['exit_code']) is int and resource['exit_code'] == 0 and
                    resource['name'] == proof['gpu_job_name'] and
                    [row for row in ledger if row.get('name') == resource['name']] == [resource], 'Natural unique GPU terminal required')
            evidence = proof['retained_evidence_refs']
            require(isinstance(evidence, dict) and {'request', 'raw', 'done', 'CPU_input_proof',
                    'first_independent_input_replay'} <= set(evidence), 'Retained raw/first QA closure incomplete')
            for ref in evidence.values(): self.checked_ref(ref)
            first = read(self.checked_ref(evidence['first_independent_input_replay']))
            require(first['status'] == 'PASS_FIRST_INDEPENDENT_INPUT_REPLAY_ONLY_NOT_LEASE_ACCEPTANCE' and
                    first['consumer'] == consumer and first['CPU_only'] is True and
                    first['first_independent_input_replay'] is True and
                    first['normal_processor_from_original_RGB_verified'] is True and
                    first['actual_first_independent_processor_encodes'] == 1 and
                    first['input_manifest_ref'] == manifest_ref and
                    first['full_input_signature'] == manifest['full_signature'] and
                    first['original_RGB_ref'] == rgb_ref and first['resource_ref'] == resource_ref and
                    first['ledger_ref'] == ledger_ref and first['CPU_input_proof_ref'] == evidence['CPU_input_proof'] and
                    first['new_model_calls'] == first['new_source_decodes'] == 0 and
                    first['prepare_pid'] == proof['prepare_pid'] and first['prepare_pid'] != first['verifier_pid'],
                    'Actual first ordinary processor input QA cannot be replaced by byte-only checks')
            if self.policy['mode'] == 'PRODUCTION':
                require(proof['validation_scope'] == 'PRODUCTION_FIRST_INDEPENDENT_REPLAY' and
                        proof['verifier_code_sha256'] == self.policy['independent_replay_code_sha256'] and
                        resource.get('validation_scope') != 'PURE_SYNTHETIC_NOT_REAL_TERMINAL' and
                        read(self.checked_ref(evidence['raw'])).get('actual_model_call') is True,
                        'Synthetic/model-failure evidence cannot authorize production release')
            self._append(dict(event='CONSUMER_ACCEPTED', consumer=consumer, input_manifest_ref=manifest_ref,
                proof_ref=proof_ref, resource_ref=resource_ref, ledger_ref=ledger_ref,
                retained_evidence_refs=evidence, first_independent_replay=True,
                canonical_validation='ACTUAL_ALL_PAYLOAD_BYTES_SHA_AFTER_FIRST_FULL_QA_NO_TENSOR_REBUILD',
                prospective_backend_ref=self._extension_ref))

    def _closure(self, lease):
        self._allowed('release_leases', lease['lease_id'])
        require(lease['frozen_consumers_ref'] == self.frozen_ref, 'Frozen full graph changed')
        self.checked_ref(self.frozen_ref); rows = self._rows()
        registrations = [row for row in rows if row.get('event') == 'RGB_LEASE_REGISTERED' and row.get('lease_id') == lease['lease_id']]
        require(len(registrations) == 1, 'Unique original lease registration required')
        self.checked_ref(registrations[0]['lease_ref'])
        require(not any(row.get('lease_id') == lease['lease_id'] and row.get('event') in
                        ('RGB_RELEASE_INTENT', 'RGB_RELEASED') for row in rows), 'Attempted release requires explicit recovery')
        accepted = {}
        for row in rows:
            if row.get('event') == 'CONSUMER_ACCEPTED':
                require(row['consumer'] not in accepted, 'Duplicate first acceptance'); accepted[row['consumer']] = row
        closure = []
        for consumer in lease['consumers']:
            require(consumer in accepted, 'All frozen consumers must be accepted')
            row = accepted[consumer]; manifest, current = self.canonical_byte_binding(consumer)
            require(current == row['input_manifest_ref'], 'Accepted manifest changed')
            for field in ('frame_array_path', 'frame_array_sha256', 'source_sha256',
                          'source_frame_ordinals', 'sample_exact_pts', 'pixel_sha256'):
                require(manifest['original_metadata'][field] == lease['original_metadata'][field], 'RGB/native source binding changed')
            require(manifest['identity']['source_sha256'] == lease['original_metadata']['source_sha256'] and
                    manifest['identity']['source_ordinals'] == lease['original_metadata']['source_frame_ordinals'] and
                    manifest['identity']['exact_pts'] == lease['original_metadata']['sample_exact_pts'], 'Canonical/native identity changed')
            for key in ('proof_ref', 'resource_ref', 'ledger_ref'): self.checked_ref(row[key])
            for ref in row['retained_evidence_refs'].values(): self.checked_ref(ref)
            closure.append(row)
        return closure


def open_store(legacy_class, base, admission_path):
    """Explicit factory, never mutates a frozen class/module or old policy."""
    path = Path(admission_path).absolute(); value = read(path)
    require(value['schema'] == SCHEMA and value['status'] == 'MAIN_APPROVED_PROSPECTIVE_EXACT_BACKEND_AFTER_QUIESCENT_HANDOFF' and
            value['cache_root'] == str(Path(base).absolute()) and value['no_old_writer_active'] is True and
            value['original_graph_membership_and_roles_unchanged'] is True and
            value['first_normal_processor_replay_required'] is True and value['model_algorithm_changed'] is False and
            value['lock_order'] == LOCK_ORDER, 'Separate main-approved exact backend handoff required')
    for ref in value['required_code_refs']: checked_external(ref)
    own = Path(__file__).resolve()
    require(any(Path(ref['path']).resolve() == own and ref['sha256'] == sha(own) for ref in value['required_code_refs']),
            'Actual new backend code SHA must be explicit')
    owner = Path(inspect.getfile(legacy_class)).resolve()
    require(checked_external(value['original_lease_code_ref']).resolve() == owner, 'Frozen LeaseStore owner changed')
    handoff = read(checked_external(value['quiescent_handoff_ref']))
    require(handoff['status'] == 'MAIN_CONTROLLED_HANDOFF_STOP' and
            handoff['all_begun_owned_children_naturally_terminal'] is True and
            handoff['active_old_writer_count'] == 0 and handoff['old_parent_scheduling_stopped'] is True and
            handoff['old_failure_promoted_to_success'] is False,
            'A parent hold alone is not a quiescent writer handoff')
    for field in ('producer_consumers', 'accept_consumers', 'release_leases'):
        require(isinstance(value[field], list) and len(set(value[field])) == len(value[field]), 'Freeze unique remaining phase IDs')
    cls = type('ProspectiveExactLeaseStore', (ExactExtension, legacy_class), {})
    store = cls(base)
    require(sha(store.base/'policy.json') == value['original_cache_policy_sha256'] and
            store.frozen_ref == value['original_frozen_consumers_ref'] and
            set(value['producer_consumers']) <= store.consumers and set(value['accept_consumers']) <= store.consumers and
            set(value['release_leases']) <= set(store.frozen['frozen_RGB_leases']), 'Original policy/graph or remaining subset changed')
    store._extension = value
    store._extension_ref = dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)
    store._legacy_codec_module = legacy_class.__module__.rsplit('.', 1)[0]+'.codec'
    return store
