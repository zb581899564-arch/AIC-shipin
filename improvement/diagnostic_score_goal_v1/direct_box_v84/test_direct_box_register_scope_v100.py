import copy
import datetime as dt
import importlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import direct_box_register_scope_v100 as reg100
import direct_box_inference_v107 as inference
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crop_confirm_prepare_v36 as builder36
import crop_geometry_v31 as geometry
import direct_box_math_preclamp_v105 as math105
import numpy as np
import direct_box_conditional_review_v109 as review109
import crop_policy_v33 as policy33


def r(name):return dict(path='/synthetic/'+name,sha256='a'*64)


def quality(arms=('DIRECT','ANCHORED_HALF')):
    return dict(status=reg100.NATIVE,fixed_final_checkpoint=True,new_updates=778,total_adopted_plus_new_updates=798,
        hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',admitted_arm_names=list(arms),
        arms={a:dict(quality=dict(admitted=a in arms)) for a in reg100.ARMS},
        training_completion=r('trained105final778'),adapter_weights=r('adapter105'),head_weights=r('head105'),
        output_acceptance=r('nativeQA'),control_result70=r('old70'))


class Fake:
    def __init__(self,root,plan,documents):
        self.root=Path(root);self.meta=self.root/'direct_box_scope_registration_100';self.plan=plan
        self.documents=documents;self.reads=[];self.writes={}
    def read(self,ref):
        self.reads.append(ref['path'])
        return copy.deepcopy(self.documents[ref['path']]) if ref['path'] in self.documents else json.loads(Path(ref['path']).read_text())
    def write(self,path,value):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x') as f:json.dump(value,f)
        self.writes[str(path)]=copy.deepcopy(value);return reg100.reference(path)
    def bind(self,ref):return Path(ref['path'])
    def module(self,key):return {'metadata_builder_code36':builder36,'geometry_code':geometry,'math_code':math105,'GPU_code':inference}[key]
    def budget(self,key):return dict(max_seconds=100,max_new_bytes=1000000,deadline_utc='2099-01-01T00:00:00Z',GPU_job='synthetic_'+key)


class RegistrarTests(unittest.TestCase):
    def test_native_freeze_adopts20_exact_F4_and_child_plan_keeps_code_locks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();plan={k:r(k) for k in reg100.FIXED_KEYS}
            plan.update(root=str(root),deadline_utc='2099-01-01T00:00:00Z')
            native=quality(('ANCHORED_HALF',));native['registration']=plan['frozen_GPU105_registration']
            directory=root/'adapter';directory.mkdir();(directory/'adapter_config.json').write_text('{}')
            (directory/'weights').write_bytes(b'synthetic');native['adapter_weights']=reg100.reference(directory/'weights')
            original=dict(GPU_code=plan['frozen_GPU105_code'],math_code=plan['math_code'],frozen_math84_code=plan['frozen_math84_code'],
                frozen_GPU93_code=plan['frozen_GPU93_code'],frozen_math93_code=plan['frozen_math93_code'],
                preparation_code=plan['base_input_code87'],original93_progress=r('warm93'),prepared=r('old622'),input_acceptance=r('oldgate622'),CPU_registration=r('CPU87'))
            trained=dict(status='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY',completed_updates=778,successful_micro=3112,
                actual_training_forwards=3112,original_successful_updates=20,original_successful_forwards=88,total_adopted_plus_new_updates=798,
                optimizer_reset=True,GPU_registration=plan['frozen_GPU105_registration'],original93_progress=original['original93_progress'],
                adapter_reload_all288_exact=True,head_reload_all2_exact=True,adapter_directory=str(directory),
                adapter_weights=native['adapter_weights'],head_weights=native['head_weights'],TRAINED_completion=r('screen105done'))
            entries=[];docs={}
            for i in range(20):
                entry=dict(id=str(i),source_id='screen'+str(i),source_sha256=f'{i:064x}',role='screen',input=r('q'+str(i)))
                entries.append(entry);docs[entry['input']['path']]=dict(**{k:entry[k] for k in ('id','source_id','source_sha256','role')},
                    actual_input_domain='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH',reference_or_target_in_prompt=False,
                    image_grid_thw=[[1,2,2]],input_signature={k:'accepted' for k in ('input_ids','attention_mask','pixel_values','image_grid_thw')})
            qa=dict(status='PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA',registration=plan['frozen_GPU105_registration'],
                training_completion=native['training_completion'],completion=trained['TRAINED_completion'],predictions=entries,
                adapter_weights=native['adapter_weights'],head_weights=native['head_weights'])
            docs.update({plan['native20_quality_result']['path']:native,native['training_completion']['path']:trained,
                plan['frozen_GPU105_registration']['path']:original,native['output_acceptance']['path']:qa,
                original['prepared']['path']:dict(screen_inputs=entries),original['input_acceptance']['path']:dict(
                    status='PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA',prepared=original['prepared'],registration=original['CPU_registration'])})
            c=Fake(root,plan,docs);c.plan_ref=r('initialPlan')
            frozen_ref=reg100.freeze_native20(c);f=c.read(frozen_ref)
            self.assertEqual(f['admitted_arm_names'],['ANCHORED_HALF'])
            self.assertEqual(f['source_only_domain']['new_model_calls'],0)
            self.assertFalse(f['source_only_domain']['independent_quality_evidence'])
            self.assertEqual(len(f['source_only_domain']['requests']),20)
            with self.assertRaises(ValueError):reg100.freeze_native20(c)
            c.plan=dict(plan,native20_freeze=frozen_ref,remaining_capacity_admission=r('futureActualEvidence'))
            reg100.Context.frozen(c)
            c.plan['GPU_code']=r('changed107')
            with self.assertRaises(ValueError):reg100.Context.frozen(c)

    def test_fixed_arm_freeze_and_same19_subset_no_revival(self):
        native=quality(('ANCHORED_HALF',));self.assertEqual(reg100.qualify(native),['ANCHORED_HALF'])
        bad=copy.deepcopy(native);bad['status']='PASS_DIRECT_BOX84_NATIVE20_QUALIFIED_ARMS'
        with self.assertRaises(ValueError):reg100.qualify(bad)
        bad=quality();bad['admitted_arm_names']=['ANCHORED_HALF']
        with self.assertRaises(ValueError):reg100.qualify(bad)
        confirm=dict(native,status=reg100.CONFIRM,native20_quality_result=r('native'),frozen_admitted_arm_names=['ANCHORED_HALF'],arms={'ANCHORED_HALF':native['arms']['ANCHORED_HALF']})
        self.assertEqual(reg100.qualify(confirm,native=native,native_ref=r('native')),['ANCHORED_HALF'])
        confirm['head_weights']=r('different')
        with self.assertRaises(ValueError):reg100.qualify(confirm,native=native,native_ref=r('native'))

    def test_exact19_metadata_newvision_no_tensor_or_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            plan={k:r(k) for k in ('original_confirm_prepared','original_confirm_input_acceptance','remaining19_output_acceptance','remaining19_completion','original_confirm_labels','metadata_builder_code36')}
            docs={};entries=[];rows=[];outputs=[];raws=[];labels=[]
            for i in range(20):
                sid=reg100.EXCLUDED if i==0 else f'gnmc:test:{i:06d}.jpeg';sha=f'{i:064x}'
                entry=r('entry'+str(i));proof=r('proof'+str(i));entries.append(entry)
                row=dict(item_id=sid,source_sha256=sha,role='confirm',reference_available_to_inference=False,width=160,height=100,
                    RGB=r('RGB'+str(i)),new_vision=r('vision'+str(i)),new_vision_signature={'sig':i},original_proof=proof)
                rows.append(row);docs[entry['path']]=row;docs[proof['path']]=dict(source_sha256=sha,RGB_sha256='b'*64)
                if i:
                    raw=r('raw'+str(i));br=r('BASE'+str(i));out=r('result'+str(i));outputs.append(out);raws.append(raw)
                    docs[out['path']]=dict(source=entry,source_sha256=sha,item_id=sid,original_BASE=br)
                    docs[br['path']]=dict(item_id=sid,source_sha256=sha,source=entry,original_BASE_box=[0,5,160],original_BASE_raw=raw)
                    labels.append(dict(item_id=sid,source_sha256=sha,role='confirm',reference_xywh=[20.,20.,100.,40.]))
            docs[plan['original_confirm_prepared']['path']]=dict(entries=entries)
            docs[plan['original_confirm_input_acceptance']['path']]=dict(status='PASS_FIRST_ALL20_CONFIRM_BASE_AND_NEW_VISION_INPUTS',prepared=plan['original_confirm_prepared'],actual_sources=20)
            docs[plan['remaining19_output_acceptance']['path']]=dict(status='PASS_FIRST_REMAINING19_BASE_AND_ROI_QA_ORIGINAL20_INCOMPLETE',completion=plan['remaining19_completion'],actual_sources=19)
            docs[plan['remaining19_completion']['path']]=dict(status='COMPLETE_REMAINING19_BASE_AND_VISION_ORIGINAL20_INCOMPLETE',first_new_BASE_generations=19,first_new_vision_readouts=19,entries=outputs,base_calls=raws)
            docs[plan['original_confirm_labels']['path']]=labels
            native=quality();f=dict(native,native20_quality_result=r('native'),native20_quality_summary=reg100.summary(native,r('native')))
            c=Fake(temp,plan,docs);c.frozen=lambda:(f,native)
            old={k:r(k) for k in ('model_config',)};plan['frozen_GPU105_registration']=r('orig105');docs[r('orig105')['path']]=old
            for k in ('preparation_code','base_input_code87','protocol'):plan[k]=r(k)
            output=reg100.register_confirm19(c);registered=c.read(output)
            sources=c.read(registered['source_catalog'])['sources']
            self.assertEqual([s['original_entry'] for s in sources],entries[1:]);self.assertEqual(len(sources),19)
            self.assertTrue(all(s['source_vision']==row['new_vision'] for s,row in zip(sources,rows[1:])))
            self.assertNotIn(reg100.EXCLUDED,[s['source_id'] for s in sources])
            self.assertFalse(any('/vision' in p or '/RGB' in p or '/raw' in p for p in c.reads))
            targets=c.read(registered['CPU_targets'])['sources'];self.assertEqual(targets[0]['original_reference_xywh'],[20.,20.,100.,40.])
            self.assertTrue(all((t['width'],t['height'])==(s['width'],s['height']) for t,s in zip(targets,sources)))
            controls,proof=review109.controls19(sources,targets,beta70=np.zeros(11),rms47=np.ones(14),
                beta47=np.zeros(11),beta33=np.zeros(13),geometry_features=policy33.geometry_features)
            self.assertEqual(proof['scope'],'SAME_HISTORICAL19_ONLY')
            self.assertEqual(set(controls),set(review109.review84.CONTROLS))
            self.assertTrue(all(len(c['source_ids'])==19 for c in controls.values()))
            predictions=[dict(source_id=s['source_id'],source_sha256=s['source_sha256'],
                native_boxes={'DIRECT':s['baseline_box']}) for s in sources]
            evaluation=review109.review84.evaluate_scope(sources,targets,predictions,controls,
                scope='confirm19',arm_names=['DIRECT'])
            self.assertEqual(evaluation['arms']['DIRECT']['summary']['sources'],19)
            self.assertEqual(evaluation['arms']['DIRECT']['summary']['mean_gain'],0.)
            with self.assertRaises(ValueError):reg100.register_confirm19(c)

    def test_capacity_uses_actual32_projection_and_dynamic_available_resources(self):
        pilot_ref=r('pilot32');ids=['s'+str(i) for i in range(32)]
        pilot=dict(status='PASS_DIRECT_BOX106_FORMAL_CPU_PILOT32_ONLY',sources=32,entries=[dict(source_id=s) for s in ids],first_QA=[r(s) for s in ids],new_bytes_before_acceptance=32000,elapsed_seconds=16.)
        domain=dict(pilot_source_ids=ids,remaining_source_ids=['tail'+str(i) for i in range(64)])
        now=dt.datetime.now(dt.timezone.utc)
        capacity=dict(schema='EXPLICIT_DIRECT_BOX106_REMAINING_CAPACITY_ADMISSION_V100',pilot_acceptance=pilot_ref,capacity_sufficient=True,
            external_task_conflict=False,projected_additional_bytes=65000,projected_additional_seconds=33.,available_disk_bytes=100000,
            available_seconds=100.,available_ram_bytes=2000,measured_peak_rss_bytes=1000,
            measured_at_utc=(now-dt.timedelta(seconds=1)).isoformat(),valid_until_utc=(now+dt.timedelta(seconds=60)).isoformat())
        budget=dict(max_new_bytes=70000,max_seconds=40.)
        result=reg100.remaining_capacity(pilot,domain,capacity,budget,pilot_ref)
        self.assertEqual((result['linear_bytes_projection'],result['linear_seconds_projection']),(64000,32.))
        bad=copy.deepcopy(capacity);bad['available_disk_bytes']=60000
        with self.assertRaises(ValueError):reg100.remaining_capacity(pilot,domain,bad,budget,pilot_ref)
        bad=copy.deepcopy(capacity);bad['external_task_conflict']=True
        with self.assertRaises(ValueError):reg100.remaining_capacity(pilot,domain,bad,budget,pilot_ref)

    def test_exclusive_write_and_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            c=reg100.Context.__new__(reg100.Context);c.root=Path(temp).resolve()
            c.write(c.root/'one.json',dict(ok=True))
            with self.assertRaises(FileExistsError):c.write(c.root/'one.json',dict(ok=False))
            with self.assertRaises(ValueError):c.write(c.root.parent/'escape.json',{})

    def test_generated_confirm107_registration_matches_real107_validators(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();native=quality(('ANCHORED_HALF',))
            f=dict(**{k:native[k] for k in reg100.MODEL_KEYS},native20_quality_result=r('native'),native20_quality_summary=reg100.summary(native,r('native')),
                admitted_arm_names=['ANCHORED_HALF'],adapter_directory='/synthetic/adapter',adapter_config=r('config'),native_output_acceptance=r('nativeQA'))
            plan={k:r(k) for k in ('GPU_code','frozen_GPU105_code','frozen_GPU105_registration','frozen_math84_code','frozen_GPU93_code','frozen_math93_code','math_code','preparation_code',
                'conditional_review_code','frozen_review105_code','frozen_review93_code','frozen_review84_code','geometry_code','policy_code')}
            plan['GPU_code']=dict(path=str(Path(inference.__file__).resolve()),sha256='a'*64)
            sources=[dict(source_id='s'+str(i),source_sha256=f'{i:064x}') for i in range(19)]
            c=Fake(root,plan,{plan['frozen_GPU105_registration']['path']:{k:r(k) for k in ('model_config','old_TIME','old_PAIR','old_CROP')}})
            c.frozen=lambda:(f,native)
            catalog=c.write(root/'catalog.json',dict(sources=sources))
            cpu=c.write(root/'direct_box_scope_CPU_registration_106_confirm19.json',dict(source_catalog=catalog))
            entries=[dict(id=str(i),source_id=s['source_id'],source_sha256=s['source_sha256'],role='confirm',input=r('q'+str(i))) for i,s in enumerate(sources)]
            prep=c.write(root/'direct_box_scope_inputs_106/confirm19/prepared.json',dict(schema='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106',phase='confirm19',sources=19,
                source_catalog=catalog,inference_inputs=entries,execution_entries=entries,adopted_success={},admitted_arm_names=f['admitted_arm_names'],**{k:f[k] for k in reg100.MODEL_KEYS}))
            c.write(root/'direct_box_scope_inputs_106/confirm19/input_acceptance.json',dict(status='PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA',phase='confirm19',prepared=prep,registration=cpu,sources=19,inputs=19))
            with mock.patch.object(inference,'bound',side_effect=lambda ref:Path(ref['path']).resolve()):
                produced=reg100.register_inference(c,'confirm19')
            reg=c.read(produced);self.assertEqual(reg['schema'],inference.SCHEMA);self.assertEqual(reg['expected_inputs'],19)
            self.assertEqual(reg['admitted_arm_names'],['ANCHORED_HALF']);self.assertEqual(reg['old_control_result70'],native['control_result70'])


if __name__=='__main__':unittest.main()
