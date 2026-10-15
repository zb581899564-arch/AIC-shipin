"""New RGB staging leases and append-only release records; no old cleanup."""
import datetime
import json
import os
import stat

if __package__:
    from .codec import SCHEMA, Store, _no_links, json_bytes, read, require, sha, valid_id
else:
    from codec import SCHEMA, Store, _no_links, json_bytes, read, require, sha, valid_id

PROOF_SCHEMA = 'CACHE_FIRST_INDEPENDENT_REPLAY_ACCEPTANCE_V1'


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class LeaseStore(Store):
    def _append(self, row):
        path = self.path('permanent/lifecycle.jsonl', 'permanent')
        with path.open('ab') as stream:
            stream.write(json_bytes(dict(schema=SCHEMA, utc=utc(), **row))+b'\n')
            stream.flush()
            os.fsync(stream.fileno())

    def _rows(self):
        path = self.path('permanent/lifecycle.jsonl', 'permanent')
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines() if line]

    def register_rgb(self, lease_id, staging_relative, consumers, original_metadata):
        valid_id(lease_id)
        require(isinstance(consumers, list) and consumers and len(set(consumers)) == len(consumers)
                and set(consumers) <= self.consumers, 'Exact frozen RGB consumer lease is required')
        staging = self.path(staging_relative, 'staging')
        require(staging.is_file(), 'Actual new RGB staging file must exist before its lease')
        for consumer in consumers:
            valid_id(consumer)
        rgb_ref = self.ref(staging_relative, 'staging')
        require(original_metadata['frame_array_path'] == str(staging) and
                original_metadata['frame_array_sha256'] == rgb_ref['sha256'],
                'Historical RGB path/SHA must describe the actual new staging file')
        path = self.path(f'permanent/leases/{lease_id}.json', 'permanent')
        with self.locked():
            self.checked_ref(self.frozen_ref)
            if self.policy['mode'] == 'PRODUCTION':
                require(self.frozen['frozen_RGB_leases'].get(lease_id) ==
                        dict(rgb_relative=staging_relative, consumers=consumers),
                        'RGB lease membership/path differs from the full pre-model dependency plan')
            previous = [read(self.path('permanent/leases/'+p.name, 'permanent'))
                        for p in path.parent.glob('*.json')] if path.parent.exists() else []
            require(not any(x['rgb_ref']['relative'] == staging_relative for x in previous),
                    'One staging path must have one complete frozen consumer lease')
            info = staging.stat()
            lease = dict(schema=SCHEMA, lease_id=lease_id, rgb_ref=rgb_ref,
                consumers=consumers, frozen_consumers_ref=self.frozen_ref,
                artifact_role='EPHEMERAL_NATIVE_RGB_STAGING',
                original_metadata=original_metadata, original_inode=[info.st_dev, info.st_ino],
                retention_declared_before_new_model=True)
            self._write(path, lease)
            self._append(dict(event='RGB_LEASE_REGISTERED', lease_id=lease_id,
                              lease_ref=self.ref(f'permanent/leases/{lease_id}.json')))
        return self.ref(f'permanent/leases/{lease_id}.json')

    def accept_consumer(self, consumer, proof_ref, resource_ref, ledger_ref):
        valid_id(consumer)
        require(consumer in self.consumers, 'Unfrozen consumer cannot close a lease')
        with self.locked():
            self.checked_ref(self.frozen_ref)
            require(not any(x.get('event') == 'CONSUMER_ACCEPTED' and x.get('consumer') == consumer
                            for x in self._rows()), 'First independent acceptance must not repeat')
            _, manifest_ref = self.load_input(consumer)
            manifest = read(self.checked_ref(manifest_ref))
            proof = read(self.checked_ref(proof_ref))
            resource = read(self.checked_ref(resource_ref))
            ledger_path = self.checked_ref(ledger_ref)
            ledger = [json.loads(x) for x in ledger_path.read_text().splitlines() if x]
            require(proof['schema'] == PROOF_SCHEMA and proof['status'] == 'PASS_FIRST_INDEPENDENT_REPLAY'
                    and proof['consumer'] == consumer and proof['CPU_only'] is True
                    and proof['new_model_calls'] == 0 and proof['first_independent_replay'] is True
                    and type(proof['prepare_pid']) is int and type(proof['verifier_pid']) is int
                    and proof['prepare_pid'] != proof['verifier_pid']
                    and proof['input_manifest_ref'] == manifest_ref
                    and proof['full_input_signature'] == manifest['full_signature']
                    and proof['GPU_input_signature'] == manifest['full_signature']
                    and proof['normal_processor_from_original_RGB_verified'] is True
                    and proof['output_token_decode_grammar_parser_native_verified'] is True,
                    'First independent RGB/normal-processor/input/token/native proof is incomplete')
            RGB_ref = proof['original_RGB_ref']
            RGB_path = self.checked_ref(RGB_ref, 'staging')
            require(manifest['original_metadata']['frame_array_path'] == str(RGB_path) and
                    manifest['original_metadata']['frame_array_sha256'] == RGB_ref['sha256'],
                    'Independent replay did not bind this input to its still-present original RGB')
            require(resource['status'] == 'completed' and type(resource['exit_code']) is int and resource['exit_code'] == 0
                    and resource['name'] == proof['gpu_job_name']
                    and [row for row in ledger if row.get('name') == resource['name']] == [resource],
                    'Unique naturally completed GPU resource/ledger receipt is required')
            evidence = proof['retained_evidence_refs']
            require(isinstance(evidence, dict) and
                    {'request', 'raw', 'done', 'CPU_input_proof'} <= set(evidence),
                    'Raw/tokens/request/done/original CPU evidence must remain retained')
            for ref in evidence.values():
                self.checked_ref(ref)
            if self.policy['mode'] == 'PRODUCTION':
                require(proof.get('validation_scope') == 'PRODUCTION_FIRST_INDEPENDENT_REPLAY' and
                        proof.get('verifier_code_sha256') == self.policy['independent_replay_code_sha256'] and
                        resource.get('validation_scope') != 'PURE_SYNTHETIC_NOT_REAL_TERMINAL' and
                        read(self.checked_ref(evidence['raw'])).get('actual_model_call') is True,
                        'Synthetic/test receipts cannot authorize production RGB release')
            self._append(dict(event='CONSUMER_ACCEPTED', consumer=consumer,
                input_manifest_ref=manifest_ref, proof_ref=proof_ref,
                resource_ref=resource_ref, ledger_ref=ledger_ref,
                retained_evidence_refs=evidence, first_independent_replay=True))

    def _closure(self, lease):
        require(lease['frozen_consumers_ref'] == self.frozen_ref, 'Global frozen consumer table changed')
        self.checked_ref(lease['frozen_consumers_ref'])
        rows = self._rows()
        registrations = [x for x in rows if x.get('event') == 'RGB_LEASE_REGISTERED'
                         and x.get('lease_id') == lease['lease_id']]
        require(len(registrations) == 1, 'Exactly one original frozen lease registration is required')
        self.checked_ref(registrations[0]['lease_ref'])
        require(not any(x.get('lease_id') == lease['lease_id'] and
                        x.get('event') in ('RGB_RELEASE_INTENT', 'RGB_RELEASED') for x in rows),
                'Release was already attempted: preserve records and require explicit recovery')
        accepted = {}
        for row in rows:
            if row.get('event') == 'CONSUMER_ACCEPTED':
                require(row['consumer'] not in accepted, 'Duplicate first replay acceptance')
                accepted[row['consumer']] = row
        closure = []
        for consumer in lease['consumers']:
            require(consumer in accepted, 'Pending frozen consumer blocks RGB release: '+consumer)
            row = accepted[consumer]
            _, current = self.load_input(consumer)  # Every reachable canonical tensor SHA must still exist.
            require(current == row['input_manifest_ref'], 'Accepted permanent input manifest changed')
            manifest = read(self.checked_ref(current))
            for field in ('frame_array_path', 'frame_array_sha256', 'source_sha256',
                          'source_frame_ordinals', 'sample_exact_pts', 'pixel_sha256'):
                require(manifest['original_metadata'][field] == lease['original_metadata'][field],
                        'A frozen consumer references another RGB/native source: '+consumer)
            require(manifest['identity']['source_sha256'] == lease['original_metadata']['source_sha256']
                    and manifest['identity']['source_ordinals'] == lease['original_metadata']['source_frame_ordinals']
                    and manifest['identity']['exact_pts'] == lease['original_metadata']['sample_exact_pts'],
                    'Canonical input source/ordinals/PTS are not the leased RGB identity')
            for key in ('proof_ref', 'resource_ref', 'ledger_ref'):
                self.checked_ref(row[key])
            for ref in row['retained_evidence_refs'].values():
                self.checked_ref(ref)
            closure.append(row)
        return closure

    def release_rgb(self, lease_id):
        """Release this new RGB file once; retain canonical and all historical refs."""
        valid_id(lease_id)
        lease_rel = f'permanent/leases/{lease_id}.json'
        lease_path = self.path(lease_rel, 'permanent')
        with self.locked():
            lease = read(lease_path)
            require(lease['schema'] == SCHEMA and lease['lease_id'] == lease_id and
                    lease['artifact_role'] == 'EPHEMERAL_NATIVE_RGB_STAGING', 'Only registered new RGB staging')
            closure = self._closure(lease)
            target = self.checked_ref(lease['rgb_ref'], 'staging')
            info = target.stat()
            require(stat.S_ISREG(info.st_mode) and [info.st_dev, info.st_ino] == lease['original_inode'],
                    'RGB staging inode changed; do not remove another file')
            intent = dict(event='RGB_RELEASE_INTENT', lease_id=lease_id,
                lease_ref=self.ref(lease_rel), historical_RGB_ref=lease['rgb_ref'],
                consumers=lease['consumers'], accepted_first_replay_count=len(closure),
                actual_RGB_present=True, canonical_files_verified_present=True)
            self._append(intent)  # Intent is not a claim that deletion succeeded.
            if os.name == 'posix' and os.unlink in os.supports_dir_fd:
                self._unlink_no_follow(lease['rgb_ref']['relative'], lease['original_inode'])
            else:
                # Synthetic Windows path checks include junction/reparse ancestors.
                # Production roots are Linux-only and use descriptor-relative unlink.
                require(self.policy['mode'] == 'PURE_SYNTHETIC', 'Secure Linux production unlink is required')
                _no_links(target)
                latest = target.stat()
                require([latest.st_dev, latest.st_ino] == lease['original_inode'], 'Staging target replaced')
                target.unlink()
            require(not target.exists(), 'RGB release did not complete')
            receipt = dict(event='RGB_RELEASED', lease_id=lease_id,
                historical_RGB_path=str(target), historical_RGB_ref=lease['rgb_ref'],
                consumers=lease['consumers'], RGB_present=False,
                canonical_files_retained=True, old_success_files_deleted=0,
                model_calls_in_this_module=0)
            self._append(receipt)
            return receipt

    def _unlink_no_follow(self, relative, expected_inode):
        # Open each directory relative to an already verified root FD. A swapped
        # symlink ancestor cannot redirect unlink into an old/external directory.
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fds = [os.open(self.base.anchor, flags)]
        try:
            for part in self.base.parts[1:]:
                fds.append(os.open(part, flags, dir_fd=fds[-1]))
            parts = relative.split('/')
            for part in parts[:-1]:
                fds.append(os.open(part, flags, dir_fd=fds[-1]))
            info = os.stat(parts[-1], dir_fd=fds[-1], follow_symlinks=False)
            require(stat.S_ISREG(info.st_mode) and [info.st_dev, info.st_ino] == expected_inode,
                    'Staging final target is a link or different inode')
            os.unlink(parts[-1], dir_fd=fds[-1])
        finally:
            for fd in reversed(fds):
                os.close(fd)

    def staging_state(self, lease_id):
        valid_id(lease_id)
        lease = read(self.path(f'permanent/leases/{lease_id}.json', 'permanent'))
        rows = [x for x in self._rows() if x.get('lease_id') == lease_id]
        released = [x for x in rows if x['event'] == 'RGB_RELEASED']
        path = self.path(lease['rgb_ref']['relative'], 'staging')
        if released:
            require(len(released) == 1 and not path.exists(), 'Historical released staging path reappeared')
            return dict(state='RELEASED', present=False, historical_RGB_ref=lease['rgb_ref'],
                        release_receipt=released[0])
        if any(x['event'] == 'RGB_RELEASE_INTENT' for x in rows):
            return dict(state='RELEASE_ATTEMPT_UNCONFIRMED_REQUIRES_EXPLICIT_RECOVERY', present=path.exists(),
                        historical_RGB_ref=lease['rgb_ref'])
        self.checked_ref(lease['rgb_ref'], 'staging')
        return dict(state='LIVE_STAGING', present=True, historical_RGB_ref=lease['rgb_ref'])
