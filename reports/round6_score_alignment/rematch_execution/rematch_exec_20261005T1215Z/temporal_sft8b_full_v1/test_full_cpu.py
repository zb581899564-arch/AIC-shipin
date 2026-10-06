"""CPU tests for full coverage, partial accumulation and stage rejection."""
import copy
import json
from pathlib import Path
import unittest

from full_contract import (epoch_batches,validate_config,validate_authority,validate_full_rows,
    FIXED,EXTRA,HERE,OLD,SCOPE,REQUEST)
from row_contract import rounded_source_end_ok


class FullContractTests(unittest.TestCase):
    def test_each_window_once_per_epoch(self):
        batches=epoch_batches(724,5,16,20261006)
        flat=[item for batch in batches for item in batch]
        self.assertEqual(len(flat),3620)
        for epoch in range(1,6):
            self.assertEqual(sorted(index for e,index in flat if e==epoch),list(range(724)))

    def test_partial_batch_is_not_dropped_or_padded(self):
        batches=epoch_batches(724,5,16,20261006)
        self.assertEqual(len(batches),227)
        self.assertEqual([len(batch) for batch in batches[:-1]],[16]*226)
        self.assertEqual(len(batches[-1]),4)

    def test_schedule_is_reproducible_and_epochs_shuffle(self):
        a=epoch_batches(724,5,16,20261006)
        self.assertEqual(a,epoch_batches(724,5,16,20261006))
        flat=[item for batch in a for item in batch]
        orders=[[i for e,i in flat if e==epoch] for epoch in range(1,6)]
        self.assertNotEqual(orders[0],orders[1])

    def test_invalid_batch_specs_rejected(self):
        for args in [(0,5,16,1),(724,0,16,1),(724,5,0,1),(724,5,16,0)]:
            with self.assertRaises(ValueError): epoch_batches(*args)

    def config(self):
        return {**FIXED,**{key:'CPU_FIXTURE_ONLY' for key in EXTRA}}

    def test_frozen_recipe(self):
        validate_config(self.config())
        for key,value in [('epochs',1),('grad_accum',4),('initialization','SMOKE_ADAPTER'),
                          ('final_checkpoint_only',False),('loss','BCE'),('lr',1e-3)]:
            changed=self.config(); changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): validate_config(changed)

    def authority(self):
        return dict(authorized=True,scope=SCOPE,route='TEMPORAL_8B_INTERVAL_SFT',user_request_quote=REQUEST,
            authority_kind='DIRECT_USER_FULL_8B_TRAINING_REQUEST_MAIN_B_PROTOCOL',full_training_admitted=True,
            formal_c_bce_admitted=False,authorization_inferred_from_nonresponse=False)

    def test_new_direct_request_required(self):
        validate_authority(self.authority())
        for key,value in [('user_request_quote','然后推理打包开训。'),('full_training_admitted',False),
                          ('scope','TEMPORAL_8B_SFT_SMOKE_NONTEST'),('authorized',False)]:
            changed=self.authority(); changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): validate_authority(changed)

    def test_c_bce_and_nonresponse_not_authorized(self):
        for key in ('formal_c_bce_admitted','authorization_inferred_from_nonresponse'):
            changed=self.authority(); changed[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError): validate_authority(changed)

    def population(self):
        registry=json.loads((OLD/'inputs_01/r7_train_registry.json').read_text())
        rows=[json.loads(line) for line in (OLD/'inputs_01/full_train.jsonl').read_text().splitlines() if line.strip()]
        # Synthetic old clock records only for mutation testing, not a real audit receipt.
        original=[{**parent,'sample_id':parent['parent_sample_id'],'source_avg_fps':parent['fps_num']/parent['fps_den'],
            'decoded_source_frames':parent['n_frames'],'pts_frame_interval_sec':parent['fps_den']/parent['fps_num'],
            'pts_max_residual_sec':0.0} for parent in registry['records']]
        return registry,rows,original

    def test_full_population_contract(self):
        registry,rows,original=self.population()
        self.assertEqual(len(validate_full_rows(registry,rows,original)),704)

    def test_millisecond_source_endpoint_only(self):
        row=dict(n_frames=4496,fps_num=30000,fps_den=1001)
        exact=row['n_frames']*row['fps_den']/row['fps_num']
        self.assertTrue(rounded_source_end_ok(exact,row))
        self.assertTrue(rounded_source_end_ok(round(exact,3),row))
        self.assertFalse(rounded_source_end_ok(exact+.0006,row))
        self.assertFalse(rounded_source_end_ok(exact+.0003,row))

    def test_all_registered_rounding_cases_are_bounded(self):
        _,rows,_=self.population()
        rounded=[r for r in rows if r['clip_end_sec']>r['n_frames']*r['fps_den']/r['fps_num']+1e-6]
        self.assertEqual(len(rounded),14)
        self.assertTrue(all(rounded_source_end_ok(r['clip_end_sec'],r) for r in rounded))

    def test_missing_or_duplicate_window_rejected(self):
        registry,rows,original=self.population()
        for changed in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError): validate_full_rows(registry,changed,original)

    def test_dev_or_unknown_injection_rejected(self):
        registry,rows,original=self.population()
        for key,value in [('split','dev'),('segments_clip_local',[]),('source_sha256','0'*64)]:
            changed=copy.deepcopy(rows); changed[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): validate_full_rows(registry,changed,original)


if __name__=='__main__': unittest.main(verbosity=2)
