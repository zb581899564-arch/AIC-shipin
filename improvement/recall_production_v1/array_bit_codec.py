"""Bit-exact cache for nonempty NumPy CPU arrays with canonical C strides.

No pickle, torch, model, quantization or dtype conversion. Plain zlib and
itemsize byte-plane-shuffled zlib are computed in RAM; ties choose plain and
only the selected payload is stored. The caller supplies load byte limits.

Zero-offset NumPy/base-buffer storage must be verifiable. Unknown owners,
subclasses, float16, object/structured/flexible dtypes, scalars, empty arrays
and unsupported layouts are rejected rather than copied into another layout.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import zlib

import numpy as np

MAGIC = b'AIC-AB1\x00'
SCHEMA = 'NUMPY_DENSE_ARRAY_BIT_CACHE_V1'
PREFIX = struct.Struct('>8sI32s')
MAX_HEADER_BYTES = 65536  # Structural format bound, not a resource admission threshold.
ZLIB_LEVEL = 6
PLAIN = 'PLAIN_ZLIB'
SHUFFLED = 'BYTE_PLANES_ZLIB'
HEADER_KEYS = frozenset(('schema', 'dtype', 'shape', 'strides', 'order', 'offset_bytes',
    'raw_nbytes', 'raw_sha256', 'payload_nbytes', 'payload_sha256', 'representation',
    'shuffle_itemsize', 'zlib_level', 'plain_zlib_nbytes', 'byte_planes_zlib_nbytes'))


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, minimum, message):
    _require(type(value) is int and value >= minimum, message)
    return value


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _digest(value):
    _require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'Explicit lowercase SHA256 required')


def _dtype(value):
    try:
        dtype = np.dtype(value)
    except (TypeError, ValueError) as error:
        raise ValueError('Invalid NumPy dtype') from error
    _require(dtype.fields is None and dtype.subdtype is None and dtype.metadata is None and not dtype.hasobject,
             'Object/structured/subarray/metadata dtypes are unsupported')
    allowed = ((dtype.kind == 'b' and dtype.itemsize == 1) or
               (dtype.kind in 'iu' and dtype.itemsize in (1, 2, 4, 8)) or
               (dtype.kind == 'f' and dtype.itemsize in (4, 8)))
    _require(allowed, 'Only bool, fixed-width integers and float32/float64 are supported; no float16 conversion')
    return dtype


def _shape(shape):
    _require(isinstance(shape, (list, tuple)) and bool(shape) and
             all(type(axis) is int and axis > 0 for axis in shape), 'Nonempty positive-integer shape required; scalar/empty arrays are unsupported')
    return tuple(shape)


def _strides(shape, itemsize):
    stride, result = itemsize, []
    for axis in reversed(shape):
        result.append(stride); stride *= axis
    return tuple(reversed(result))


def _storage_address(array):
    """Find the start of a verifiable backing allocation without importing owners."""
    owner, seen = array, set()
    while True:
        _require(id(owner) not in seen, 'Cyclic or unverifiable array storage owner')
        seen.add(id(owner))
        if type(owner) is np.ndarray:
            if owner.base is None:
                _require(owner.flags.owndata, 'Array backing allocation cannot be verified')
                return owner.__array_interface__['data'][0]
            owner = owner.base
        elif isinstance(owner, memoryview):
            owner = owner.obj
        else:
            try:
                buffer = memoryview(owner)
                _require(buffer.c_contiguous and buffer.nbytes > 0, 'Contiguous nonempty backing buffer required')
                return np.frombuffer(buffer, dtype=np.uint8).__array_interface__['data'][0]
            except (TypeError, BufferError) as error:
                raise ValueError('Unknown backing owner; zero offset cannot be proven without an explicit adapter') from error


def _array_metadata(array):
    _require(type(array) is np.ndarray, 'An ordinary NumPy CPU ndarray is required; subclasses/devices are unsupported')
    dtype = _dtype(array.dtype); shape = _shape(array.shape)
    strides = _strides(shape, dtype.itemsize)
    _require(array.flags.c_contiguous and array.strides == strides,
             'Canonical dense C strides required; unsupported layouts are not repaired')
    _require(array.__array_interface__['data'][0] == _storage_address(array), 'Nonzero backing-storage offset is unsupported')
    return dtype, shape, strides


def _canonical(header):
    return json.dumps(header, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'Duplicate JSON header key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('Nonfinite JSON constant is forbidden: '+value)


def _validate_header(header):
    _require(isinstance(header, dict) and set(header) == HEADER_KEYS and header['schema'] == SCHEMA,
             'Exact versioned array cache header required')
    _require(isinstance(header['dtype'], str), 'Canonical dtype string required')
    dtype = _dtype(header['dtype'])
    _require(dtype.str == header['dtype'], 'Noncanonical dtype encoding')
    shape = _shape(header['shape']); expected_strides = _strides(shape, dtype.itemsize)
    _require(isinstance(header['strides'], list) and all(type(value) is int for value in header['strides']) and
        tuple(header['strides']) == expected_strides and header['order'] == 'C' and
        type(header['offset_bytes']) is int and header['offset_bytes'] == 0,
        'Only recorded canonical C strides and offset zero are supported')
    raw_size = math.prod(shape)*dtype.itemsize
    _require(_integer(header['raw_nbytes'], 1, 'Positive raw byte count required') == raw_size,
             'Header dtype/shape/raw byte count differs')
    _integer(header['payload_nbytes'], 1, 'Positive compressed payload byte count required')
    plain_size = _integer(header['plain_zlib_nbytes'], 1, 'Positive plain-zlib size required')
    shuffled_size = _integer(header['byte_planes_zlib_nbytes'], 1, 'Positive shuffled-zlib size required')
    expected_representation = SHUFFLED if shuffled_size < plain_size else PLAIN
    _require(header['representation'] == expected_representation and header['payload_nbytes'] == min(plain_size, shuffled_size) and
        type(header['shuffle_itemsize']) is int and header['shuffle_itemsize'] == dtype.itemsize and
        type(header['zlib_level']) is int and header['zlib_level'] == ZLIB_LEVEL,
        'Deterministic representation, itemsize or compression settings differ')
    _digest(header['raw_sha256']); _digest(header['payload_sha256'])
    return dtype, shape, raw_size


def _parse(cache):
    _require(type(cache) is bytes and len(cache) >= PREFIX.size, 'Complete immutable cache bytes required')
    magic, header_size, header_sha = PREFIX.unpack_from(cache)
    _require(magic == MAGIC and 0 < header_size <= MAX_HEADER_BYTES, 'Unknown/truncated cache format or invalid header length')
    payload_start = PREFIX.size+header_size
    _require(payload_start <= len(cache), 'Truncated JSON header')
    header_bytes = cache[PREFIX.size:payload_start]
    _require(hashlib.sha256(header_bytes).digest() == header_sha, 'JSON header SHA256 differs')
    try:
        header = json.loads(header_bytes.decode('ascii'), object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ValueError('Invalid JSON cache header') from error
    dtype, shape, raw_size = _validate_header(header)
    _require(_canonical(header) == header_bytes, 'Noncanonical JSON cache header')
    payload = memoryview(cache)[payload_start:]
    _require(payload.nbytes == header['payload_nbytes'] and _sha(payload) == header['payload_sha256'],
             'Truncated/extra payload or payload SHA256 differs')
    return header, dtype, shape, raw_size, payload


def encode_array(array):
    """Encode once into a deterministic header plus exactly one chosen payload.

    Both compression candidates, raw bytes and byte-plane scratch exist in RAM
    during this call. No peak-memory or full-production disk claim is made.
    """
    dtype, shape, strides = _array_metadata(array)
    raw = array.tobytes(order='C')
    planes = np.frombuffer(raw, dtype=np.uint8).reshape(-1, dtype.itemsize).T.tobytes(order='C')
    plain = zlib.compress(raw, level=ZLIB_LEVEL)
    shuffled = zlib.compress(planes, level=ZLIB_LEVEL)
    representation, payload = (SHUFFLED, shuffled) if len(shuffled) < len(plain) else (PLAIN, plain)
    header = dict(schema=SCHEMA, dtype=dtype.str, shape=list(shape), strides=list(strides), order='C', offset_bytes=0,
        raw_nbytes=len(raw), raw_sha256=_sha(raw), payload_nbytes=len(payload), payload_sha256=_sha(payload),
        representation=representation, shuffle_itemsize=dtype.itemsize, zlib_level=ZLIB_LEVEL,
        plain_zlib_nbytes=len(plain), byte_planes_zlib_nbytes=len(shuffled))
    header_bytes = _canonical(header)
    _require(len(header_bytes) <= MAX_HEADER_BYTES, 'Header exceeds the structural format bound')
    return PREFIX.pack(MAGIC, len(header_bytes), hashlib.sha256(header_bytes).digest())+header_bytes+payload


def inspect_cache(cache):
    """Validate header/payload integrity; raw hash is checked by decode_array."""
    return _parse(cache)[0]


def decode_array(cache, *, max_raw_bytes):
    """Return a read-only ndarray with identical dtype/shape/strides/raw bits.

    max_raw_bytes is a caller-supplied capacity bound, checked before inflation.
    Header/raw/payload hashes provide integrity, not authenticity; the future
    source lock must bind the complete cache file SHA and production identity.
    """
    _integer(max_raw_bytes, 1, 'An explicit positive maximum raw byte count is required')
    header, dtype, shape, raw_size, payload = _parse(cache)
    _require(raw_size <= max_raw_bytes, 'Array exceeds the caller raw-byte allowance')
    try:
        inflater = zlib.decompressobj()
        decoded = inflater.decompress(payload, raw_size+1)
    except zlib.error as error:
        raise ValueError('Invalid zlib payload') from error
    _require(len(decoded) == raw_size and inflater.eof and not inflater.unconsumed_tail and not inflater.unused_data,
             'Truncated/oversized/concatenated zlib stream')
    if header['representation'] == SHUFFLED:
        raw = np.frombuffer(decoded, dtype=np.uint8).reshape(dtype.itemsize, -1).T.tobytes(order='C')
    else:
        raw = decoded
    _require(_sha(raw) == header['raw_sha256'], 'Original raw array byte SHA256 differs')
    try:
        array = np.frombuffer(raw, dtype=dtype).reshape(shape)
    except (ValueError, OverflowError) as error:
        raise ValueError('Recorded shape is unsupported by this NumPy runtime') from error
    _require(array.strides == tuple(header['strides']) and array.dtype.str == header['dtype'] and
             array.flags.c_contiguous and not array.flags.writeable, 'Decoded original layout/dtype/read-only contract differs')
    return array


def save_array(path, array):
    """Exclusively create a new cache, fsync it, and retain partials on failure."""
    cache = encode_array(array)
    with Path(path).open('xb') as output:
        _require(output.write(cache) == len(cache), 'Short cache write; preserve the partial file')
        output.flush(); os.fsync(output.fileno())
    return inspect_cache(cache)


def load_array(path, *, max_raw_bytes, max_cache_bytes):
    """Read one explicitly bounded cache; no overwrite, retry or discovery."""
    _integer(max_cache_bytes, 1, 'An explicit positive maximum cache byte count is required')
    with Path(path).open('rb') as source:
        cache = source.read(max_cache_bytes+1)
    _require(len(cache) <= max_cache_bytes, 'Cache exceeds the caller file-byte allowance')
    return decode_array(cache, max_raw_bytes=max_raw_bytes)
