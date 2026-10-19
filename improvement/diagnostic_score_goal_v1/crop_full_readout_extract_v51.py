"""Callback-only extraction of the frozen V51 full-vocabulary readout.

No CLI, registration, model, processor, target loading, or filesystem I/O lives
here. The caller MUST first adopt the successful 46/33 output acceptances and
their exact final500 training/adapter identity under the new V51 protocol.
In particular, old33 prediction/receipt rows do not contain adapter weights;
passing ``weights`` records that caller-adopted identity, not a new proof of it.

``select_indices(base_sha256, final_crop_sha256, class_token_ids)`` returns the
one common, sorted int64[4096] column set. ``collect`` accepts one already-QAd
role batch. Both loaders take the result of ``bound(artifact_ref)``. The tensor
loader must return the existing CPU float32 torch.Tensor, not convert its dtype.
Only compact extracted arrays are cached, once per identical raw path/SHA.

The saved logits are W @ h projections, possibly BF16 values cast to float32.
This module neither reconstructs h nor introduces a new visual observation.
Old first raw QA is adopted: no old validate_raw, softmax, probability, token,
pixel, grid reprocessing, or three-class quality evaluation is repeated.
"""
from __future__ import annotations

import hashlib
import json
from numbers import Integral
from pathlib import PurePosixPath, PureWindowsPath

import numpy as np

VOCAB_SIZE = 151936
READOUT_SIZE = 4096
LITERAL = 'FULL_VOCAB_SWAP32_V51'
CLASS_TOKEN_IDS = (15, 16, 17)
ROLES = ('GAIN_pilot128', 'GAIN_remaining2280', 'TRAINED_screen')
INPUT_KEYS = {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}


def _require(value, message):
    if not value:
        raise ValueError(message)


def _sha(value, label):
    _require(isinstance(value, str) and len(value) == 64
             and all(c in '0123456789abcdef' for c in value), label+' must be an explicit lowercase SHA256')
    return value


def _reference(value, label):
    _require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
             and isinstance(value['path'], str)
             and (PurePosixPath(value['path']).is_absolute() or PureWindowsPath(value['path']).is_absolute()),
             label+' must be an absolute path/SHA artifact ref')
    _sha(value['sha256'], label+' SHA')
    return dict(value)


def _classes(values):
    _require(isinstance(values, (list, tuple, np.ndarray)) and len(values) == 3
             and all(isinstance(v, Integral) and not isinstance(v, (bool, np.bool_)) for v in values),
             'Three explicit actual class token IDs required')
    result = tuple(int(v) for v in values)
    _require(len(set(result)) == 3 and all(0 <= v < VOCAB_SIZE for v in result), 'Invalid actual class token IDs')
    return result


def select_indices(base_sha256, final_crop_sha256, class_token_ids):
    """SHA-rank all nonclass rows once, then return selected IDs in ID order."""
    base_sha256 = _sha(base_sha256, 'BASE')
    final_crop_sha256 = _sha(final_crop_sha256, 'Final CROP')
    excluded = set(_classes(class_token_ids))
    prefix = (base_sha256+'|'+final_crop_sha256+'|'+LITERAL+'|').encode('ascii')
    ranked = sorted((hashlib.sha256(prefix+str(i).encode('ascii')).digest(), i)
                    for i in range(VOCAB_SIZE) if i not in excluded)
    return np.array(sorted(i for _, i in ranked[:READOUT_SIZE]), dtype=np.int64)


def _indices(values, classes):
    result = np.asarray(values)
    _require(result.shape == (READOUT_SIZE,) and result.dtype.kind in 'iu'
             and result.dtype != np.bool_ and bool((result >= 0).all()) and bool((result < VOCAB_SIZE).all()),
             'Exactly4096 integer vocabulary indices required')
    result = result.astype(np.int64, copy=True)
    _require(bool((np.diff(result) > 0).all()) and not set(classes).intersection(result.tolist()),
             'Readout columns must be sorted, unique, and exclude actual class IDs')
    return result


def _identity(row, label):
    _require(isinstance(row, dict) and isinstance(row['id'], str) and bool(row['id'])
             and isinstance(row['source_id'], str) and bool(row['source_id']), label+' needs explicit id/source_id')
    return row['id'], row['source_id'], _sha(row['source_sha256'], label+' source')


def collect(predictions, indices, weights, *, expected_role, load_json, load_tensor,
            bound, class_token_ids=CLASS_TOKEN_IDS):
    """Return ``(lookup_by_id, report)`` without reading any real artifact here.

    Predictions are adopted 46/33 rows with id/source_id/source_sha256/input/
    receipt. Their accepted probabilities are deliberately unused. The caller
    has bound the batch acceptance to final500 ``weights`` before invoking us;
    a present46 prediction.adapter_weights must additionally agree. There is
    no invented receipt.weights requirement or implicit latest/checkpoint path.

    Each lookup row contains readout4096/class_logits3 float64 numpy arrays and
    complete raw/input/receipt/owner/token/adapter declarations. The report's
    byte count is actual loaded tensor payload (151936*4 per unique raw), NOT
    torch serialization or disk-container bytes. BF16 statistics use only the
    selected4096 values of each physically read raw; aliases are not recounted.
    No pair matrices, targets, softmax, centering, or AB-BA differences are made.
    Any missing field or callback failure propagates; no missing row becomes0.
    """
    _require(expected_role in ROLES, 'Only one exact accepted final500 role batch is supported')
    _require(isinstance(predictions, (list, tuple)) and bool(predictions), 'Nonempty adopted predictions required')
    _require(all(callable(v) for v in (load_json, load_tensor, bound)), 'Explicit bound/load callbacks required')
    adapter = _reference(weights, 'Caller-adopted final500 adapter')
    classes = _classes(class_token_ids)
    columns = _indices(indices, classes)
    import torch

    lookup, raw_cache, json_cache, path_hashes = {}, {}, {}, {}
    selected_total = roundtrip_total = 0

    def bind(reference, label):
        reference = _reference(reference, label)
        path = reference['path']
        previous = path_hashes.get(path)
        _require(previous is None or previous == reference['sha256'], 'One artifact path cannot have conflicting SHA256 refs')
        path_hashes[path] = reference['sha256']
        return reference, bound(reference)

    def document(reference, label):
        reference = _reference(reference, label)
        key = (reference['path'], reference['sha256'])
        if key not in json_cache:
            checked, path = bind(reference, label)
            value = load_json(path)
            _require(isinstance(value, dict), label+' must decode to a JSON object')
            json_cache[key] = value
        return json_cache[key]

    for prediction in predictions:
        identity = _identity(prediction, 'Prediction')
        identifier, source_id, source_sha256 = identity
        _require(identifier not in lookup, 'Duplicate accepted prediction ID')
        input_ref = _reference(prediction['input'], 'Input')
        receipt_ref = _reference(prediction['receipt'], 'Receipt')
        request = document(input_ref, 'Input')
        receipt = document(receipt_ref, 'Receipt')
        _require(_identity(request, 'Request') == identity == _identity(receipt, 'Receipt')
                 and receipt['input'] == input_ref and receipt['model_role'] == expected_role,
                 'Accepted prediction/request/receipt owner, input, or role differs')
        _require(_classes(request['class_token_ids']) == classes == _classes(receipt['class_token_ids'])
                 and isinstance(request['input_signature'], dict) and set(request['input_signature']) == INPUT_KEYS
                 and request['input_signature'] == receipt['input_signature'],
                 'Actual class IDs or adopted input signature differs')
        _require(receipt['full_vocabulary_size'] == VOCAB_SIZE and receipt['raw_dtype'] == 'torch.float32',
                 'Accepted raw must declare full151936 float32 logits')
        if 'adapter_weights' in prediction:
            _require(_reference(prediction['adapter_weights'], 'Prediction adapter') == adapter,
                     'Accepted prediction final500 adapter differs')
        if 'model_role' in prediction:
            _require(prediction['model_role'] == expected_role, 'Prediction model role differs')
        raw_ref = _reference(receipt['raw_logits'], 'Raw logits')
        key = (raw_ref['path'], raw_ref['sha256'])
        # Same physical raw is reusable only for its already accepted exact
        # owner/role/class/input signature. No old alias QA is re-run here.
        owner = json.dumps(dict(source_id=source_id, source_sha256=source_sha256,
            model_role=expected_role, class_token_ids=classes, input_signature=request['input_signature']),
            sort_keys=True, separators=(',', ':'), allow_nan=False)
        if key not in raw_cache:
            _, path = bind(raw_ref, 'Raw logits')
            raw = load_tensor(path)
            _require(isinstance(raw, torch.Tensor) and raw.device.type == 'cpu' and raw.dtype == torch.float32
                     and tuple(raw.shape) == (VOCAB_SIZE,) and not raw.requires_grad,
                     'Callback must return the existing full CPU float32 raw tensor without conversion')
            selected = raw[columns].numpy().astype(np.float64)
            three = raw[list(classes)].numpy().astype(np.float64)
            _require(bool(np.isfinite(selected).all()) and bool(np.isfinite(three).all()),
                     'New extracted readout/class values must be finite')
            # Only selected rows are examined for this new diagnostic. Exact
            # bit roundtrip also distinguishes signed zero.
            selected32 = torch.from_numpy(selected.astype(np.float32))
            back = selected32.to(torch.bfloat16).to(torch.float32)
            roundtrip = int((selected32.view(torch.int32) == back.view(torch.int32)).sum().item())
            selected_total += READOUT_SIZE
            roundtrip_total += roundtrip
            selected.setflags(write=False); three.setflags(write=False)
            raw_cache[key] = dict(owner=owner, readout4096=selected, class_logits3=three,
                readout_sha256=hashlib.sha256(selected.tobytes(order='C')).hexdigest(),
                bf16_roundtrip_selected_count=roundtrip)
            del raw
        cached = raw_cache[key]
        _require(cached['owner'] == owner, 'Shared raw ref cannot cross source, weights role, classes, or input signature')
        lookup[identifier] = dict(id=identifier, source_id=source_id, source_sha256=source_sha256,
            readout4096=cached['readout4096'], class_logits3=cached['class_logits3'],
            input=input_ref, receipt=receipt_ref, raw_logits=raw_ref, model_role=expected_role,
            class_token_ids=list(classes), readout_sha256=cached['readout_sha256'],
            bindings=dict(input=input_ref, receipt=receipt_ref, raw_logits=raw_ref,
                input_signature=request['input_signature'], adapter_weights=adapter,
                adapter_binding_scope='CALLER_ADOPTED_ACCEPTANCE_AND_FINAL500_COMPLETION'
                    if 'adapter_weights' not in prediction else 'CALLER_ADOPTED_FINAL500_AND_PREDICTION_REF'))

    reads = len(raw_cache)
    return lookup, dict(version=LITERAL, model_role=expected_role, predictions=len(lookup),
        distinct_sources=len({r['source_id'] for r in lookup.values()}), actual_raw_reads=reads,
        reused_raw_refs=len(lookup)-reads, actual_raw_read_bytes=reads*VOCAB_SIZE*4,
        byte_scope='LOADED_TENSOR_PAYLOAD_ONLY_EXCLUDES_TORCH_SERIALIZATION',
        full_vocabulary_size=VOCAB_SIZE, raw_dtype='torch.float32', readout_dtype='numpy.float64',
        readout_token_ids=columns.tolist(), class_token_ids=list(classes), adapter_weights=adapter,
        bf16_roundtrip_scope='SELECTED4096_ROWS_PER_PHYSICALLY_READ_RAW_ONLY_NOT_FULL_VOCABULARY',
        bf16_roundtrip_selected_values=selected_total, bf16_roundtrip_exact_values=roundtrip_total,
        bf16_roundtrip_ratio=roundtrip_total/selected_total, old_first_raw_QA_repeated=False,
        new_model_calls=0, softmax_applied=False, sample_centering=False, targets_read=False,
        hidden_state_reconstructed=False, new_visual_observation=False)
