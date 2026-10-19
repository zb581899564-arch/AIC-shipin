import copy
from pathlib import Path
import struct
import unittest
import zlib
import direct_box_fresh8_contract_v130 as contract
import direct_box_fresh8_runtime_v130 as runtime


class FreshContractTests(unittest.TestCase):
    def test_fixed_exact8_payload_and_lost_source_excluded(self):
        rows=contract.fixed_sources();contract.validate_sources(rows)
        self.assertEqual(len({r['source_id'] for r in rows}),8)
        self.assertNotIn('gnmc:test:006575.jpeg',{r['source_id'] for r in rows})
        self.assertEqual(sum(r['compressed_bytes']+30 for r in rows),304262)
        with self.assertRaises(ValueError):contract.validate_sources(list(reversed(rows)))

    def test_range_fullresponse_wrongclock_or_overread_rejected(self):
        self.assertEqual(contract.range_response(206,'bytes 4-6/20',b'abc',offset=4,length=3,archive_bytes=20),b'abc')
        for status,cr,body in ((200,'bytes 4-6/20',b'abc'),(206,'bytes 4-6/21',b'abc'),(206,'bytes 4-6/20',b'abcd')):
            with self.assertRaises(ValueError):contract.range_response(status,cr,body,offset=4,length=3,archive_bytes=20)

    def test_localheader_variable_name_extra_offset_and_crc(self):
        raw=b'original member bytes';d=zlib.compressobj(wbits=-15);packed=d.compress(raw)+d.flush()
        row=dict(header_offset=100,compressed_bytes=len(packed),bytes=len(raw),crc32=zlib.crc32(raw)&0xffffffff,compression=8)
        header=struct.pack('<4s5H3I2H',b'PK\x03\x04',20,0,8,0,0,row['crc32'],len(packed),len(raw),21,9)
        self.assertEqual(contract.member_data_offset(header,row),160)
        self.assertEqual(contract.unpack_member(packed,row),raw)
        with self.assertRaises(ValueError):contract.unpack_member(packed,dict(row,crc32=0))
        with self.assertRaises(ValueError):contract.member_data_offset(header[:29],row)

    def test_known_identity_failure_does_not_choose_replacement(self):
        registry=dict(blocked_source_ids=[],blocked_media_sha256=[],blocked_RGB_sha256=[],blocked_dhash9x8=[0])
        sid=contract.fixed_sources()[0]['source_id']
        with self.assertRaises(ValueError):contract.check_identity(sid,'a'*64,'b'*64,31,registry)
        result=contract.check_identity(sid,'a'*64,'b'*64,127,registry)
        self.assertEqual(result['original_source_global_independence'],'UNKNOWN')

    def test_failed124_or_old19_cannot_admit_new8(self):
        result=dict(status=contract.DEVELOPMENT_PASS,admitted_arms=['JOINT']);r={'path':'/r','sha256':'a'*64}
        admission=dict(schema='ADMIT_FRESH8_AFTER_ACTUAL128_DEV39_V130',result=r,development_only=True,fresh8_admitted=True,
            no_new_fit_on_fresh8=True,file_level_only=True,model_refs={'m':1},critic_refs={'c':1})
        contract.validate_development(admission,result,result_ref=r,model_refs={'m':1},critic_refs={'c':1})
        with self.assertRaises(ValueError):contract.validate_development(admission,dict(result,status='PASS_DIRECT_BOX106_CONFIRM19_QUALIFIED_ARMS'),
            result_ref=r,model_refs={'m':1},critic_refs={'c':1})

    def test_command_plan_only_requires_new_workers_and16_roles(self):
        reg=dict(schema=contract.SCHEMA,root='/synthetic/newfresh8',origin_url=contract.ORIGIN,archive_bytes=contract.ARCHIVE_BYTES,
            max_range_payload_bytes=304262,sources=contract.fixed_sources(),source_plan_sha256=contract.digest(contract.fixed_sources()),
            worker_codes={s:dict(path='/synthetic/code/direct_box_fresh8_runtime_v130.py',sha256='a'*64) for s in ('cpu','gpu','review')},
            python='/synthetic/python',pipeline_parameters=contract.PIPELINE,critic_parameters=135393,new_8B_training_updates=0,new_critic_fits=0,
            CPU_max_seconds=300,CPU_max_new_bytes=100000000,GPU_max_seconds=600,GPU_job='new8',GPU_planned_output_bytes=10000000)
        p=contract.build_stage_plan(reg,'gpu',registration_path='/synthetic/newfresh8/fresh8_registration_130.json')
        self.assertEqual(p['BASE_generations']+p['DIRECT_hidden_head_forwards'],16)
        self.assertFalse(p['automatic_next_stage']);self.assertEqual(p['implementation'],'COMMAND_PLAN_ONLY_NOT_LAUNCHED')
        bad=copy.deepcopy(reg);bad['worker_codes']['gpu']['path']='/old/code/infer.py'
        with self.assertRaises(ValueError):contract.build_stage_plan(bad,'gpu',registration_path='/synthetic/newfresh8/fresh8_registration_130.json')

    def test_only_selected_annotation_numeric_objects_are_parsed(self):
        text='[{"filename":"unseen.jpeg","crop_bboxes":{"16:9":[UNPARSED_NUMERIC_CONTENT]}},{"filename":"chosen.jpeg","crop_bboxes":{"16:9":[0.1,0.2,0.8,0.9]}}]'
        rows=runtime.selected_annotation_rows(text,['chosen.jpeg'])
        self.assertEqual(rows['chosen.jpeg']['crop_bboxes']['16:9'],[.1,.2,.8,.9])
        with self.assertRaises(ValueError):runtime.selected_annotation_rows(text,['missing.jpeg'])

    def test_fixed8_quality_needs_reject_retain_and_all_five_controls(self):
        gains=[.03,.03,.03,.03,-.01,-.01,0.,0.]
        rows=[dict(source_id=str(i),baseline_iou=.5,selected_iou=.5+g,gain=g,changed=i<6,
            true_reject=i==6,true_retain=i==0) for i,g in enumerate(gains)]
        controls={k:.5 for k in runtime.GATE['strictly_beat']}
        summary,q=runtime.quality(rows,controls);self.assertTrue(q['admitted']);self.assertEqual(summary['sources'],8)
        bad=copy.deepcopy(rows);bad[6]['true_reject']=False;self.assertFalse(runtime.quality(bad,controls)[1]['admitted'])
        bad=copy.deepcopy(controls);bad['OLD33_GEOM13']=.6;self.assertFalse(runtime.quality(rows,bad)[1]['admitted'])
        with self.assertRaises(ValueError):runtime.quality(rows[:7],controls)


if __name__=='__main__':unittest.main()
