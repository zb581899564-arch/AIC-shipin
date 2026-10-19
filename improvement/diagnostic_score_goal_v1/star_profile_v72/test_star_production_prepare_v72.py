import copy
import hashlib
import tempfile
from pathlib import Path
import unittest
from unittest import mock

import numpy as np
import torch

import crop_geometry_v31 as geometry
import crop_image_input_v31 as image
import crop_observation_v34 as recovery
import star_profile_prepare_v72 as profile58
import star_production_prepare_v72 as production


def ref(name):
    return dict(path='/frozen/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def domain_inputs():
    accepted, metadata, baseline, clocks, refs = [], [], [], {}, {}
    for i in range(426):
        sid = str(i); is16 = i < 2; ratio = [16,9] if is16 else [9,16]
        chunks = []
        if is16:
            grids = [[1,2,4] if j == 1 else [1,2,2] for j in range(40)]
            chunks = [dict(path=ref(sid+'.pt')['path'], sha256=ref(sid+'.pt')['sha256'], samples=list(range(40)),
                          grid=grids, pixel_shape=[sum(g[1]*g[2] for g in grids),1536])]
            points = [str(j)+'/10' for j in range(80)]
            clocks[sid] = dict(video_id=sid, source_sha256=ref('video'+sid)['sha256'], n_frames=80, normalized_exact_pts=points)
            refs[sid] = dict(clock=ref(sid+'.clock'), acceptance=ref(sid+'.acceptance'))
        accepted.append(dict(id=sid, name=sid, native_frames=80, feature_cells=40 if is16 else 0,
            clock_sha256=ref(sid+'.clock')['sha256'], chunks=chunks,
            baseline=[False]*80))  # Legacy40.46 mask is deliberately not an authority.
        metadata.append(dict(video_id=sid, source_sha256=ref('video'+sid)['sha256'], n_frames=80, width=128,height=96,targetRatioWH=ratio))
        frames = range(40) if i == 0 else (range(1,40) if i == 1 else ([2] if i == 2 else []))
        baseline.append(dict(video_id=sid, targetRatioWH=ratio,
            predictions=[dict(frame=j,bboxes=[0,0,128]) for j in frames]))
    return dict(sources=accepted),dict(records=metadata),baseline,clocks,refs


class ProductionTests(unittest.TestCase):
    def test_even_observation_index_precedes_protected40_47_intersection_and_preserves_whole426(self):
        args = domain_inputs(); domain = production.compile_domain(*args,geometry)
        self.assertEqual((domain['all_D_count'],domain['selected_D_count'],domain['official_source_count']), (79,39,426))
        video1 = {s['native_ordinal'] for s in domain['selected_D'] if s['video_id']=='1'}
        self.assertNotIn(1,video1); self.assertIn(2,video1)  # Not even positions AFTER selected-mask filtering.
        self.assertTrue(all(s['observation_index']%2==0 for s in domain['selected_D']))
        self.assertIn(('0',2), {(s['video_id'],s['native_ordinal']) for s in domain['selected_D']})
        self.assertEqual(len({s['source_id'] for s in domain['selected_D']}),39)
        self.assertEqual(len({s['source_sha256'] for s in domain['selected_D']}),2)
        self.assertTrue(all(s['video_id'] in ('0','1') for s in domain['selected_D']))
        self.assertEqual(domain['all_D_sha256'],production.digest(domain['all_D']))
        self.assertTrue(all(s['all_unregistered_frames_unchanged'] for s in domain['official_sources']))

    def test_actual_cumulative_layout_and_exact_pts_fail_closed(self):
        args = domain_inputs(); domain = production.compile_domain(*args,geometry)
        row = next(s for s in domain['selected_D'] if s['video_id']=='0' and s['native_ordinal']==2)
        self.assertEqual((row['source_layout']['row_start'],row['source_layout']['row_end_exclusive']), (12,16))
        self.assertEqual(row['native_pts_exact'],'2/10')
        for fault in ('PTS','clock_SHA','grid','ordinal','426'):
            a,m,b,c,r = copy.deepcopy(args)
            if fault=='PTS': c['0']['normalized_exact_pts'][2]=c['0']['normalized_exact_pts'][1]
            elif fault=='clock_SHA': r['0']['clock']['sha256']='a'*64
            elif fault=='grid': a['sources'][0]['chunks'][0]['pixel_shape'][0]+=1
            elif fault=='ordinal': a['sources'][0]['chunks'][0]['samples'][2]=1
            else: b.pop()
            with self.subTest(fault=fault), self.assertRaises(ValueError): production.compile_domain(a,m,b,c,r,geometry)

    def test_fixed_pilot32_and_explicit_remaining_exact_partition_no_allD_switch(self):
        domain = production.compile_domain(*domain_inputs(),geometry); original = ref('original61')
        reg = dict(selection=production.SELECTION)
        pilot = dict(status=production.PILOT_GATE, registration=original, selected_D_sha256=domain['selected_D_sha256'],pilot_source_ids=domain['pilot_source_ids'])
        rest = dict(schema='STAR_PRODUCTION_REMAINING_CPU_V72',original_registration=original,
            remaining_source_ids=domain['remaining_source_ids'],expected_sources=39,observations=39,
            official_source_count=426,affected_video_count=2,max_additional_bytes=1000,selection=production.SELECTION)
        production.validate_continuation(reg,rest,pilot,domain,original)
        self.assertEqual(len(domain['pilot_source_ids']),32)
        self.assertFalse(set(domain['pilot_source_ids'])&set(domain['remaining_source_ids']))
        for change in (dict(rest,remaining_source_ids=domain['pilot_source_ids'][:1]+domain['remaining_source_ids']),
                       dict(rest,selection='ALL_D'),dict(rest,expected_sources=38)):
            with self.assertRaises(ValueError): production.validate_continuation(reg,change,pilot,domain,original)
        changed = copy.deepcopy(domain); changed['selected_D'][0]['baseline_box'][1]+=1
        with self.assertRaises(ValueError): production.validate_continuation(reg,rest,pilot,changed,original)
        plan=production.case_plan(domain['selected_D']); self.assertEqual(len(plan['pair_index']),sum(len(s['pool']) for s in domain['selected_D']))
        self.assertTrue(all(c['source_id'].startswith('official:') for c in plan['cases']))

    def test_explicit_two_admission_levels_and_both_new_quality_gates(self):
        reg=dict(schema=production.SCHEMA,selection=production.SELECTION,protected_baseline=dict(path='/frozen/40.47.zip',sha256=production.PROTECTED_SHA),
            resized20_quality=ref('q20'),resized19_quality=ref('q19'),adapter_weights=ref('adapter'),value_weights=ref('value'))
        q20=dict(status='PASS_STAR_RESIZED20_PROFILE_ONLY',primary='UTILITY',quality=dict(admitted=True),adapter_weights=ref('adapter'),value_weights=ref('value'))
        q19=dict(q20,status='PASS_STAR_RESIZED19_CONFIRM_ONLY')
        pilot=dict(status='ADMIT_STAR_PRODUCTION_CPU_PILOT32_ONLY',production_prepare_approved=True,production_admitted=False,
            whole426_preserved=True,selection=production.SELECTION,resized20_quality=ref('q20'),resized19_quality=ref('q19'),adapter_weights=ref('adapter'),value_weights=ref('value'))
        production.validate_quality(reg,q20,q19,pilot,pilot=True)
        with self.assertRaises(ValueError): production.validate_quality(reg,q20,q19,pilot,pilot=False)
        with self.assertRaises(ValueError): production.validate_quality(reg,q20,dict(q19,status='STOP'),pilot,pilot=True)

    def test_real_chunk_row_prefix_check_and_virtual177_adopts_successful35_without_recovery(self):
        rgb = np.arange(32*32*3,dtype=np.uint16).reshape(32,32,3).astype(np.uint8)
        p0,g0=recovery.forward_pack_observation_rgb(rgb); p1,g1=recovery.forward_pack_observation_rgb(np.tile(rgb,(1,2,1)))
        payload=dict(pixel_values=torch.cat([p0,p1]),image_grid_thw=torch.cat([g0,g1]))
        layout=dict(tensor_ref=ref('177chunk'),pixel_key='pixel_values',row_start=4,row_end_exclusive=12,
            grid_thw=[1,2,4],grid_locator=dict(kind='TENSOR_ROW',key='image_grid_thw',row_index=1),normalization='FLOAT32(u-127.5)/127.5')
        vision=production.extract_chunk_row(payload,layout); recovered,proof=recovery.recover_observation_rgb(**dict(pixels=vision['pixel_values'],grid=vision['image_grid_thw']))
        checked=recovery.independent_recovery_check(vision['pixel_values'],vision['image_grid_thw'],recovered,proof)
        source=dict(source_id='official:177:native:10',video_id='177',source_sha256=ref('177')['sha256'],width=1920,height=1080,
            source_layout=layout,sample_ordinal=10,native_ordinal=10,chunk_sample_index=1,accepted_input_ref=ref('177acceptance'))
        receipt=dict(status='PASS_RESIZED_OBSERVATION_LAYOUT_ONLY',entry=dict(source_id='official:177',source_sha256=source['source_sha256'],
            layout=layout,accepted_input_ref=source['accepted_input_ref']),formula_code=ref('recovery34'),native_dimensions=[1920,1080],
            native_RGB_recovered=False,recovery=proof,independent_recovery=checked,resized_RGB=ref('old35plane'))
        adopted=production.adopt_plane35(source,vision,[receipt],lambda r:recovered,ref('recovery34'))
        self.assertEqual(adopted['adopted'],ref('old35plane'))
        with self.assertRaises(ValueError): production.extract_chunk_row(payload,dict(layout,row_start=0,row_end_exclusive=8))
        bad=copy.deepcopy(receipt);bad['recovery']['input_pixel_tensor_sha256']='0'*64
        with self.assertRaises(ValueError): production.adopt_plane35(source,vision,[bad],lambda r:recovered,ref('recovery34'))
        other=dict(source,video_id='262');self.assertIsNone(production.adopt_plane35(other,vision,[receipt],lambda r:recovered,ref('recovery34')))

    def test_production_reader_consumes_only_registered_chunkrow_and_new_lossless_crops(self):
        rng=np.random.default_rng(61);pixels,grid=recovery.forward_pack_observation_rgb(rng.integers(0,256,(32,32,3),dtype=np.uint8))
        vision=dict(pixel_values=pixels,image_grid_thw=grid);compressed,codec=profile58.encode_crop(vision)
        layout=dict(tensor_ref=ref('chunk'),pixel_key='pixel_values',row_start=0,row_end_exclusive=4,grid_thw=[1,2,2],
            grid_locator=dict(kind='TENSOR_ROW',key='image_grid_thw',row_index=0),normalization='FLOAT32(u-127.5)/127.5')
        tokens=dict(input_ids=torch.tensor([[1,2]]),attention_mask=torch.tensor([[1,1]]));g=torch.cat([grid]*3)
        packed=image.pack_image_pixels([pixels]*3,g);owner='official:177:native:10'
        q=dict(id='case',source_id=owner,source_sha256=ref('177')['sha256'],role='production',scope='production',profile=production.PROFILE,
            native_RGB_recovered=False,reference_or_target_in_prompt=False,selection=production.SELECTION,video_id='177',native_ordinal=10,
            observation_index=2,class_token_ids=[15,16,17],adapter_weights=ref('adapter'),value_weights=ref('value'),
            protected_baseline=ref('40.47'),source_layout=layout,vision_inputs=[ref('chunk'),ref('a.gz'),ref('b.gz')],
            vision_codecs=[dict(codec=production.SOURCE_CODEC,decoded_signature=production.signature(vision)),codec,codec],
            tokens=ref('tokens'),image_grid_thw=g.tolist(),input_signature=production.signature(dict(**tokens,**packed)))
        e={k:q[k] for k in ('id','source_id','source_sha256','role')};e['input']=ref('request')
        prepared=dict(schema='STAR_PRODUCTION_PREPARED_V72',scope='production',profile=production.PROFILE,native_RGB_recovered=False,
            selection=production.SELECTION,official_source_count=426,inference_inputs=[e],execution_entries=[e],adopted_success={},sources=1,
            class_token_ids=[15,16,17],adapter_weights=ref('adapter'),value_weights=ref('value'),protected_baseline=ref('40.47'),CPU_targets=None)
        gate=dict(status=production.GATE,prepared=ref('prepared'),registration=ref('reg'),scope='production',official_source_count=426,sources=1,
            native_RGB_recovered=False,first_independent_crop_processor_QA=True,first_compressed_save_and_reader_roundtrip=True)
        data={ref('chunk')['path']:vision,ref('tokens')['path']:tokens}
        reader=production.ProductionInputs(prepared,gate=gate,prepared_ref=ref('prepared'),registration_ref=ref('reg'),load_json=lambda r:q,
            load_tensor=lambda r:data[r['path']],load_bytes=lambda r:compressed,image=image)
        values,_=reader.get(e['input']);self.assertEqual(production.signature(values),q['input_signature'])
        with self.assertRaises(ValueError): reader.get(ref('unregistered'))
        with self.assertRaises(ValueError): production.ProductionInputs(prepared,gate=dict(gate,status=production.PILOT_GATE),prepared_ref=ref('prepared'),
            registration_ref=ref('reg'),load_json=lambda r:q,load_tensor=lambda r:data[r['path']],load_bytes=lambda r:compressed,image=image)

    def test_writer_actual_byte_budget_and_exclusive_create(self):
        with tempfile.TemporaryDirectory(prefix='utility61_pure_') as temporary:
            root=Path(temporary).resolve();self.assertTrue(root.name.startswith('utility61_pure_'))
            writer=production.Writer(root,limit=4);writer.write(root/'a',b'abcd');self.assertEqual(writer.bytes,4)
            with self.assertRaises(ValueError): writer.write(root/'b',b'e')
            with self.assertRaises(FileExistsError): production.Writer(root).write(root/'a',b'x')
            with mock.patch.object(production.shutil,'disk_usage',return_value=type('Disk',(),dict(free=0))()):
                with self.assertRaises(ValueError): production.Writer(root).write(root/'c',b'x')


if __name__=='__main__':unittest.main()
