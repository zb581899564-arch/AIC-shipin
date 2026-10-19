import copy
import hashlib
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

import crop_full_readout_extract_v51 as extract


def ref(path):
    return dict(path='/synthetic/'+path, sha256=hashlib.sha256(path.encode()).hexdigest())


def fixtures():
    weights = ref('final500.safetensors')
    raw_ref = ref('first.pt')
    signature = {k:dict(shape=[1], sha256='a'*64) for k in extract.INPUT_KEYS}
    docs = {}
    predictions = []
    for i in range(2):
        identifier = 'case'+str(i)
        input_ref, receipt_ref = ref(identifier+'.input.json'), ref(identifier+'.receipt.json')
        request = dict(id=identifier, source_id='gnmc:train:source', source_sha256='b'*64,
            class_token_ids=[15, 16, 17], input_signature=copy.deepcopy(signature))
        receipt = dict(**request, input=input_ref, model_role='GAIN_pilot128', raw_logits=copy.deepcopy(raw_ref),
            full_vocabulary_size=extract.VOCAB_SIZE, raw_dtype='torch.float32',
            # No probabilities are re-used or quality re-evaluated by extract.
            probabilities=['deliberately', 'not', 'read'], class_logits=['not', 'read', 'either'])
        docs[input_ref['path']], docs[receipt_ref['path']] = request, receipt
        predictions.append(dict(id=identifier, source_id=request['source_id'], source_sha256=request['source_sha256'],
            input=input_ref, receipt=receipt_ref, adapter_weights=weights))
    raw = torch.arange(extract.VOCAB_SIZE, dtype=torch.float32)/8-30
    columns = np.arange(100, 100+extract.READOUT_SIZE, dtype=np.int64)
    loads, binds = [], []

    def bound(value):
        binds.append(copy.deepcopy(value))
        return value['path']

    def load_tensor(path):
        loads.append(path)
        return raw

    callbacks = dict(expected_role='GAIN_pilot128', load_json=lambda p:docs[p], load_tensor=load_tensor, bound=bound)
    return predictions, columns, weights, docs, raw, loads, binds, callbacks


class FullReadoutTests(unittest.TestCase):
    def test_exact_hash_seed_and_actual_classes_not_literal_zero_one_two(self):
        seen = []

        def ascending_token_digest(data):
            seen.append(data)
            token = int(data.rsplit(b'|', 1)[1])
            return SimpleNamespace(digest=lambda:token.to_bytes(32, 'big'))

        with mock.patch.object(extract.hashlib, 'sha256', side_effect=ascending_token_digest):
            indices = extract.select_indices('a'*64, 'b'*64, [15, 16, 17])
        self.assertEqual(indices.dtype, np.int64)
        self.assertEqual(indices.shape, (4096,))
        self.assertTrue({0, 1, 2}.issubset(indices.tolist()))
        self.assertFalse({15, 16, 17}.intersection(indices.tolist()))
        self.assertEqual(indices[-1], 4098)
        self.assertEqual(seen[0], ('a'*64+'|'+'b'*64+'|FULL_VOCAB_SWAP32_V51|0').encode())
        self.assertEqual(len(seen), extract.VOCAB_SIZE-3)
        actual = extract.select_indices('a'*64, 'b'*64, [15, 16, 17])
        np.testing.assert_array_equal(actual, extract.select_indices('a'*64, 'b'*64, [15, 16, 17]))
        self.assertTrue(np.all(np.diff(actual) > 0))

    def test_raw_values_float64_no_softmax_or_centering_and_alias_read_once(self):
        predictions, indices, weights, docs, raw, loads, binds, callbacks = fixtures()
        lookup, report = extract.collect(predictions, indices, weights, **callbacks)
        self.assertEqual(set(lookup), {'case0', 'case1'})
        for value in lookup.values():
            np.testing.assert_array_equal(value['readout4096'], raw[indices].numpy().astype(np.float64))
            np.testing.assert_array_equal(value['class_logits3'], raw[[15, 16, 17]].numpy().astype(np.float64))
            self.assertEqual(value['readout4096'].dtype, np.float64)
            self.assertFalse(value['readout4096'].flags.writeable)
            self.assertEqual(value['bindings']['adapter_weights'], weights)
            self.assertEqual(value['readout_sha256'], hashlib.sha256(value['readout4096'].tobytes()).hexdigest())
        self.assertIs(lookup['case0']['readout4096'], lookup['case1']['readout4096'])
        self.assertEqual(loads, [ref('first.pt')['path']])
        self.assertEqual(report['actual_raw_reads'], 1)
        self.assertEqual(report['reused_raw_refs'], 1)
        self.assertEqual(report['actual_raw_read_bytes'], extract.VOCAB_SIZE*4)
        self.assertFalse(report['old_first_raw_QA_repeated'])
        self.assertFalse(report['softmax_applied'])

    def test_bf16_roundtrip_is_selected_rows_only_and_alias_not_counted_twice(self):
        predictions, indices, weights, docs, raw, loads, binds, callbacks = fixtures()
        raw.fill_(1.)
        raw[indices[0]] = 1.0001
        raw[9] = 1.0001  # Not a selected row; must not enter this diagnostic.
        _, report = extract.collect(predictions, indices, weights, **callbacks)
        self.assertEqual(report['bf16_roundtrip_selected_values'], 4096)
        self.assertEqual(report['bf16_roundtrip_exact_values'], 4095)
        self.assertEqual(report['bf16_roundtrip_ratio'], 4095/4096)
        self.assertIn('NOT_FULL_VOCABULARY', report['bf16_roundtrip_scope'])

    def test_old33_without_prediction_weights_requires_caller_binding_only(self):
        predictions, indices, weights, docs, raw, loads, binds, callbacks = fixtures()
        for row in predictions:
            del row['adapter_weights']
            docs[row['receipt']['path']]['model_role'] = 'TRAINED_screen'
        callbacks['expected_role'] = 'TRAINED_screen'
        lookup, _ = extract.collect(predictions, indices, weights, **callbacks)
        self.assertEqual(lookup['case0']['bindings']['adapter_binding_scope'],
                         'CALLER_ADOPTED_ACCEPTANCE_AND_FINAL500_COMPLETION')
        self.assertNotIn('weights', docs[predictions[0]['receipt']['path']])

    def test_reject_metadata_join_mismatches_before_any_tensor_read(self):
        changes = [lambda p, d:d[p[0]['receipt']['path']].update(id='wrong'),
                   lambda p, d:d[p[0]['input']['path']].update(source_sha256='c'*64),
                   lambda p, d:d[p[0]['receipt']['path']].update(input=ref('wrong.input')),
                   lambda p, d:d[p[0]['receipt']['path']].update(model_role='BASE_screen'),
                   lambda p, d:d[p[0]['receipt']['path']].update(class_token_ids=[0, 1, 2]),
                   lambda p, d:p[0].update(adapter_weights=ref('not-final500'))]
        for change in changes:
            with self.subTest(change=change):
                p, indices, weights, docs, raw, loads, binds, cb = fixtures()
                change(p, docs)
                with self.assertRaises(ValueError): extract.collect(p, indices, weights, **cb)
                self.assertEqual(loads, [])

    def test_shared_raw_rejects_cross_owner_and_conflicting_path_sha(self):
        for change_owner in (True, False):
            p, indices, weights, docs, raw, loads, binds, cb = fixtures()
            if change_owner:
                for row in (p[1], docs[p[1]['input']['path']], docs[p[1]['receipt']['path']]):
                    row['source_id'] = 'another_source'
                    row['source_sha256'] = 'c'*64
            else:
                docs[p[1]['receipt']['path']]['raw_logits']['sha256'] = 'd'*64
            with self.assertRaises(ValueError): extract.collect(p, indices, weights, **cb)
            self.assertLessEqual(len(loads), 1)

    def test_strict_raw_tensor_schema_selected_finiteness_no_conversion(self):
        p, indices, weights, docs, raw, loads, binds, cb = fixtures()
        bads = [raw.double(), raw.reshape(1, -1), raw.numpy(), raw.clone().requires_grad_()]
        bad_selected = raw.clone(); bad_selected[indices[2]] = float('nan'); bads.append(bad_selected)
        bad_class = raw.clone(); bad_class[15] = float('inf'); bads.append(bad_class)
        for bad in bads:
            with self.subTest(dtype=getattr(bad, 'dtype', None), shape=bad.shape):
                cb['load_tensor'] = lambda path, value=bad:value
                with self.assertRaises(ValueError): extract.collect(p, indices, weights, **cb)

    def test_unknown_duplicate_indices_or_id_and_callback_failure_never_empty(self):
        p, indices, weights, docs, raw, loads, binds, cb = fixtures()
        for bad in (indices[:-1], indices.astype(float), indices[::-1], np.repeat(100, 4096),
                    np.r_[15, indices[1:]], np.r_[indices[:-1], extract.VOCAB_SIZE]):
            with self.assertRaises(ValueError): extract.collect(p, bad, weights, **cb)
        with self.assertRaises(ValueError): extract.collect([], indices, weights, **cb)
        with self.assertRaises(ValueError): extract.collect([p[0], p[0]], indices, weights, **cb)
        cb['load_tensor'] = lambda path:(_ for _ in ()).throw(OSError('synthetic missing raw'))
        with self.assertRaisesRegex(OSError, 'synthetic missing raw'):
            extract.collect(p, indices, weights, **cb)
        del docs[p[0]['receipt']['path']]['raw_logits']
        with self.assertRaises(KeyError): extract.collect(p, indices, weights, **cb)


if __name__ == '__main__':
    unittest.main()
