"""Exact permanent input codec and restricted paths; no producer or model.

Production cache IO needs an independently approved new-root policy. Synthetic
IO is limited to this campaign's dedicated critic/cache_codec_06 fixture root.
"""
from contextlib import contextmanager
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat

SCHEMA = 'PRODUCTION_EXACT_STREAM_CACHE_V1'
CAMPAIGN = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
SYNTHETIC_ROOT = (CAMPAIGN/'cache_codec_06/synthetic_01' if os.name == 'posix' else
    Path(__file__).resolve().parents[2]/
    'reports/twenty_hour_five_20261014_v1/critic/cache_codec_06/synthetic_01')
VISUAL_KEYS = frozenset(('pixel_values', 'pixel_values_videos', 'image_grid_thw',
                        'video_grid_thw', 'second_per_grid_ts', 'video_timestamps'))
IDENTITY_FIELDS = frozenset(('source_sha256', 'source_ordinals', 'exact_pts',
    'context_origin_exact', 'grid', 'processor_assets', 'preprocessing_code'))


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def valid_id(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value)
            and '..' not in value, 'Invalid fixed consumer/artifact identifier')
    return value


def json_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(',', ':')).encode('utf-8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def _no_links(path):
    """Reject symlinks and Windows junction/reparse ancestors, including base."""
    path = Path(path).absolute()
    for component in (path, *path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and
                not getattr(info, 'st_file_attributes', 0) &
                getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400),
                'Symlink/junction/reparse path is forbidden: '+str(component))


def signature(encoded):
    import torch
    require(isinstance(encoded, dict) and encoded and
            all(isinstance(k, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k)
                for k in encoded), 'A nonempty complete tensor dictionary is required')
    result, storages = {}, {}
    for name, value in sorted(encoded.items()):
        require(isinstance(value, torch.Tensor) and value.device.type == 'cpu'
                and value.layout == torch.strided and not value.is_quantized,
                'Original CPU dense tensors only; no conversion or quantization')
        raw = value.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        result[name] = dict(dtype=str(value.dtype), shape=list(value.shape),
            stride=list(value.stride()), storage_offset=value.storage_offset(),
            layout=str(value.layout), requires_grad=value.requires_grad,
            bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        storage = value.untyped_storage()
        storages.setdefault((storage.data_ptr(), storage.nbytes()), []).append(name)
    return dict(tensors=result, alias_groups=sorted(sorted(names) for names in storages.values()
                                                   if len(names) > 1))


def exact_equal(left, right):
    """Check actual bytes too, including NaN bit patterns and signed zeros."""
    import torch
    if signature(left) != signature(right):
        return False
    return all(torch.equal(left[k].detach().contiguous().reshape(-1).view(torch.uint8),
                           right[k].detach().contiguous().reshape(-1).view(torch.uint8))
               for k in left)


class Store:
    def __init__(self, base):
        self.base = Path(base).absolute()
        require(self.base == SYNTHETIC_ROOT.absolute() or
                (self.base.parent == CAMPAIGN and re.fullmatch(r'production_stream_v[1-9][0-9]*', self.base.name)),
                'Old/external/nonproduction root is forbidden before reading cache metadata')
        _no_links(self.base)
        self.policy = read(self.base/'policy.json')
        self._validate_root(self.base, self.policy)
        self.frozen = read(self.path('permanent/frozen_consumers.json', 'permanent'))
        self.consumers = set(self.frozen['consumers'])
        require(self.frozen['schema'] == SCHEMA and len(self.consumers) == len(self.frozen['consumers']),
                'Frozen unique full consumer denominator is required')
        require(self.frozen['policy_sha256'] == sha(self.base/'policy.json'), 'Frozen root policy changed')
        self.frozen_ref = self.ref('permanent/frozen_consumers.json')

    @staticmethod
    def _validate_root(base, policy):
        _no_links(base)
        require(policy.get('schema') == SCHEMA and policy.get('root') == str(base),
                'Exact new cache schema/root policy required')
        if policy.get('mode') == 'PURE_SYNTHETIC':
            require(base == SYNTHETIC_ROOT.absolute(), 'Synthetic IO escaped its dedicated fixture root')
        else:
            require(policy.get('mode') == 'PRODUCTION' and base.parent == CAMPAIGN and
                    re.fullmatch(r'production_stream_v[1-9][0-9]*', base.name),
                    'Old/external/nonproduction root is forbidden')
            require(policy.get('main_agent_new_production_cache_approved') is True and
                    policy.get('new_independent_root') is True and
                    policy.get('staging_declared_ephemeral_before_model') is True and
                    policy.get('canonical_retention') == 'PERMANENT_LOSSLESS_EXACT_INPUT' and
                    isinstance(policy.get('independent_replay_code_sha256'), str) and
                    re.fullmatch(r'[0-9a-f]{64}', policy['independent_replay_code_sha256']),
                    'New explicit production cache policy must precede IO')

    @classmethod
    def create(cls, base, consumers, policy):
        base = Path(base).absolute()
        cls._validate_root(base, policy)
        require(not base.exists(), 'New independent root only; never overwrite/resume automatically')
        require(isinstance(consumers, list) and consumers and len(set(consumers)) == len(consumers),
                'Freeze the complete unique consumer table before model results')
        for item in consumers:
            valid_id(item)
        RGB_plan = cls.validate_RGB_plan(consumers, policy)
        base.mkdir()
        (base/'permanent').mkdir()
        (base/'staging').mkdir()
        (base/'staging/rgb').mkdir()
        cls._write(base/'policy.json', policy)
        cls._write(base/'permanent/frozen_consumers.json',
            dict(schema=SCHEMA, consumers=consumers, frozen_RGB_leases=RGB_plan,
                 policy_sha256=sha(base/'policy.json'),
                 model_calls_in_this_module=0))
        return cls(base)

    @staticmethod
    def validate_RGB_plan(consumers, policy):
        """Pure metadata check; cannot create or release production files."""
        RGB_plan = policy.get('frozen_RGB_leases', {})
        if policy['mode'] == 'PRODUCTION':
            require(isinstance(RGB_plan, dict) and RGB_plan, 'Freeze all RGB consumer dependencies before model results')
            covered, paths = [], set()
            for lease_id, row in RGB_plan.items():
                valid_id(lease_id)
                relative = row['rgb_relative']
                parts = relative.split('/') if isinstance(relative, str) else []
                require(len(parts) >= 3 and parts[:2] == ['staging', 'rgb'] and
                        all(p not in ('', '.', '..') for p in parts) and '\\' not in relative and ':' not in relative
                        and PurePosixPath(relative).suffix in ('.npz', '.npy', '.rgb', '.bin')
                        and relative not in paths and isinstance(row['consumers'], list) and row['consumers'],
                        'Frozen RGB plan contains an invalid or repeated staging path')
                paths.add(relative)
                covered.extend(row['consumers'])
            require(set(covered) == set(consumers) and len(covered) == len(set(covered)),
                    'Each frozen actual input consumer must have exactly one original RGB lease')
        return RGB_plan

    @staticmethod
    def _write(path, value):
        _no_links(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())

    def path(self, relative, area):
        require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative,
                'Only explicit new-root POSIX relative paths are allowed')
        parts = relative.split('/')
        require(not PurePosixPath(relative).is_absolute() and
                all(p not in ('', '.', '..') for p in parts) and parts[0] == area and
                area in ('permanent', 'staging'), 'Old, absolute or escaped path forbidden')
        if area == 'staging':
            require(len(parts) >= 3 and parts[1] == 'rgb' and
                    PurePosixPath(relative).suffix in ('.npz', '.npy', '.rgb', '.bin'),
                    'Only specifically registered new RGB staging files may be released')
        path = self.base.joinpath(*parts)
        _no_links(path)
        require(path.resolve().is_relative_to(self.base.resolve()), 'New-root path escape forbidden')
        return path

    def ref(self, relative, area='permanent'):
        path = self.path(relative, area)
        require(path.is_file(), 'Required retained/staging file is missing: '+relative)
        return dict(relative=relative, sha256=sha(path), bytes=path.stat().st_size)

    def checked_ref(self, ref, area='permanent'):
        path = self.path(ref['relative'], area)
        require(path.is_file() and path.stat().st_size == ref['bytes'] and sha(path) == ref['sha256'],
                'Required exact file changed or is missing: '+ref['relative'])
        return path

    @contextmanager
    def locked(self):
        lock = self.path('permanent/journal_write.lock', 'permanent')
        with lock.open('xb') as stream:
            stream.write(str(os.getpid()).encode())
            stream.flush()
            os.fsync(stream.fileno())
        try:
            yield
        finally:
            _no_links(lock)
            lock.unlink()  # This transaction's newly created coordination marker only.

    def write_metadata(self, relative, value):
        require(relative.startswith('permanent/proofs/'), 'Proof copies belong to the new permanent root')
        path = self.path(relative, 'permanent')
        self._write(path, value)
        return self.ref(relative)

    def write_ledger_snapshot(self, relative, records):
        require(relative.startswith('permanent/proofs/'), 'Ledger snapshot belongs to the permanent root')
        path = self.path(relative, 'permanent')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            for row in records:
                stream.write(json_bytes(row)+b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        return self.ref(relative)

    def _save_tensors(self, relative, encoded):
        import torch
        expected = signature(encoded)
        storage_codec = self.policy.get('input_storage_codec', 'TORCH_GZIP_LOSSLESS')
        require(storage_codec in ('TORCH_GZIP_LOSSLESS', 'PIXEL_UINT8_BIT_LUT_V1'), 'Unregistered storage codec')
        payload, codec_report = encoded, None
        if storage_codec == 'PIXEL_UINT8_BIT_LUT_V1':
            if __package__:
                from .pixel_dictionary import validate_roundtrip
            else:
                from pixel_dictionary import validate_roundtrip
            payload, codec_report = validate_roundtrip(encoded)
        path = self.path(relative, 'permanent')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=1, mtime=0) as cache:
                torch.save(payload, cache)  # Original tensor dtype/layout/storage or exact bit LUT; never quantize.
            raw.flush()
            os.fsync(raw.fileno())
        ref = {**self.ref(relative), 'storage_codec':storage_codec}
        if codec_report is not None:ref['codec_report'] = codec_report
        restored = self._load_tensors(ref)
        require(signature(restored) == expected and exact_equal(encoded, restored),
                'Lossless cache changed complete original tensor bytes/layout')
        return ref

    def _load_tensors(self, ref):
        import torch
        path = self.checked_ref(ref)
        require(path.suffixes[-2:] == ['.pt', '.gz'], 'Explicit lossless tensor cache format required')
        with path.open('rb') as raw:
            with gzip.GzipFile(fileobj=raw, mode='rb') as cache:
                value = torch.load(cache, map_location='cpu', weights_only=True)
                cache.seek(0, os.SEEK_END)  # Consume gzip end and CRC, not just the torch payload.
        if ref.get('storage_codec', 'TORCH_GZIP_LOSSLESS') == 'PIXEL_UINT8_BIT_LUT_V1':
            if __package__:
                from .pixel_dictionary import unpack
            else:
                from pixel_dictionary import unpack
            value = unpack(value)
        signature(value)
        return value

    def save_input(self, consumer, encoded, visual_keys, identity, metadata):
        valid_id(consumer)
        require(consumer in self.consumers, 'Unknown consumer changes the frozen denominator')
        full_signature = signature(encoded)
        require({'input_ids', 'attention_mask'} <= set(encoded), 'Full token/mask input must remain retained')
        require(isinstance(visual_keys, (list, tuple)) and len(set(visual_keys)) == len(visual_keys)
                and set(visual_keys) <= VISUAL_KEYS and set(visual_keys) <= set(encoded),
                'Text/position input cannot be deduplicated as visual payload')
        require(set(identity) == IDENTITY_FIELDS, 'Complete exact visual-cache identity fields required')
        require(re.fullmatch(r'[0-9a-f]{64}', identity['source_sha256']) and
                len(identity['source_ordinals']) == len(identity['exact_pts']) == 64 and
                len(set(identity['source_ordinals'])) == 64 and
                all(type(x) is int and x >= 0 for x in identity['source_ordinals']) and
                all(a < b for a, b in zip(identity['source_ordinals'], identity['source_ordinals'][1:])) and
                all(isinstance(x, str) for x in identity['exact_pts']),
                'Native source identity/64 ordered ordinals incomplete')
        from fractions import Fraction
        pts = [Fraction(x) for x in identity['exact_pts']]
        require(all(a < b for a, b in zip(pts, pts[1:])) and isinstance(identity['context_origin_exact'], str),
                'Exact chronological PTS/context origin are required')
        Fraction(identity['context_origin_exact'])
        for field in ('processor_assets', 'preprocessing_code'):
            require(isinstance(identity[field], dict) and identity[field] and
                    all(re.fullmatch(r'[0-9a-f]{64}', value) for value in identity[field].values()),
                    'Frozen processor/code SHA identity required')
        manifest_rel = f'permanent/inputs/{consumer}.json'
        require(not self.path(manifest_rel, 'permanent').exists(), 'Successful input must never be overwritten')
        visual_set = set(visual_keys)
        # Preserve cross-key storage aliasing. If a split would break an alias,
        # retain this request's original full dict instead of deduplicating it.
        if any(set(group) & visual_set and set(group)-visual_set for group in full_signature['alias_groups']):
            visual_set = set()
        visual = {k: v for k, v in encoded.items() if k in visual_set}
        private = {k: v for k, v in encoded.items() if k not in visual_set}
        visual_ref = None
        with self.locked():
            if visual:
                key_data = dict(identity=identity, visual_signature=signature(visual))
                key = hashlib.sha256(json_bytes(key_data)).hexdigest()
                index_rel = f'permanent/visual/{key}.json'
                index_path = self.path(index_rel, 'permanent')
                if index_path.exists():
                    previous = read(index_path)
                    require(previous['key_data'] == key_data, 'Visual identity differs despite cache-key collision')
                    restored = self._load_tensors(previous['tensor_ref'])
                    require(exact_equal(visual, restored), 'Visual bytes differ: hash-only dedup forbidden')
                    visual_ref = previous['tensor_ref']
                else:
                    visual_ref = self._save_tensors(f'permanent/visual/{key}.pt.gz', visual)
                    self._write(index_path, dict(schema=SCHEMA, key_data=key_data, tensor_ref=visual_ref))
            private_ref = self._save_tensors(f'permanent/inputs/{consumer}.private.pt.gz', private)
            manifest = dict(schema=SCHEMA, consumer=consumer, full_signature=full_signature,
                identity=identity, original_metadata=metadata, visual_keys=sorted(visual_set),
                private_keys=sorted(private), visual_ref=visual_ref, private_ref=private_ref,
                retained_exact_full_input=True, RGB_role='EPHEMERAL_NATIVE_RGB_STAGING',
                model_calls_in_this_module=0)
            self._write(self.path(manifest_rel, 'permanent'), manifest)
            restored, _ = self.load_input(consumer)
            require(exact_equal(encoded, restored), 'Complete input reconstruction changed original tensor dict')
        return self.ref(manifest_rel)

    def load_input(self, consumer):
        valid_id(consumer)
        manifest_rel = f'permanent/inputs/{consumer}.json'
        manifest = read(self.path(manifest_rel, 'permanent'))
        require(manifest['schema'] == SCHEMA and manifest['consumer'] == consumer,
                'Input manifest identity differs')
        encoded = self._load_tensors(manifest['private_ref'])
        if manifest['visual_ref']:
            visual = self._load_tensors(manifest['visual_ref'])
            require(not set(encoded) & set(visual), 'Overlapping tensor keys during reconstruction')
            encoded.update(visual)
        require(signature(encoded) == manifest['full_signature'], 'Retained full input signature differs')
        return encoded, self.ref(manifest_rel)

    def capacity(self, next_permanent_bound, staging_peak_bound, transient_bound):
        require(all(type(x) is int and x >= 0 for x in
                    (next_permanent_bound, staging_peak_bound, transient_bound)), 'Concrete nonnegative byte bounds required')
        free = shutil.disk_usage(self.base).free
        need = next_permanent_bound+staging_peak_bound+transient_bound
        return dict(status='FIT_THIS_BOUND_NOT_PRODUCTION_ADMISSION' if free >= need else 'STOP_RETAIN_ALL',
                    current_available_bytes=free, required_next_stage_bound_bytes=need,
                    automatic_precision_change=False, automatic_canonical_deletion=False)
