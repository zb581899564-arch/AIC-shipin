import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import torch

import direct_box_relative_worker_v136 as worker
import direct_box_inputs_recovery_v87 as input87
import direct_box_math_preclamp_v105 as math105
import direct_box_review_v84 as review84
import direct_box_train_feature_review_v127 as qa127
import direct_box_relative_critic_v128 as critic128
import direct_box_geom_promotion_v129 as promotion129
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crop_geometry_v31 as geometry31


def reference(path):
    p=Path(path).resolve();return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def write(path,value):
    Path(path).write_text(json.dumps(value),encoding='utf-8');return reference(path)


def fake_ref(name):return dict(path='/synthetic/'+name,sha256='a'*64)


class WorkerTests(unittest.TestCase):
    def test_nested_numpy_json_is_primitive_finite_and_unknowns_do_not_fall_back(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'new.json';worker.save(p,dict(admitted=np.bool_(True),count=np.int64(32),gain=np.float64(.02),
                nested=[dict(matrix=np.array([[np.int64(1),np.int64(2)]]),flags=(np.bool_(False),))]))
            actual=json.loads(p.read_text());self.assertIs(actual['admitted'],True);self.assertIs(type(actual['count']),int)
            self.assertEqual(actual['nested'],[dict(matrix=[[1,2]],flags=[False])])
            for bad in (np.float64('nan'),np.float64('inf'),float('-inf'),object(),{np.int64(1):'badkey'}):
                with self.subTest(bad=type(bad).__name__),self.assertRaises((ValueError,TypeError)):
                    worker.json_primitive({'nested':[bad]})

    def test_new_stage_schema_counts_and_owner_ids_allow_shared_video_sha(self):
        entries=[dict(id=str(i),source_id='official:0:native:'+str(i*2),source_sha256='a'*64,role='formal',input=fake_ref(str(i))) for i in range(32)]
        p=dict(schema=worker.INPUT_SCHEMA,scope='pilot32',CPU_targets=None,inference_inputs=entries,execution_entries=entries,sources=32)
        r=dict(prepared=fake_ref('prepared'),CPU_registration=fake_ref('CPU'),expected_inputs=32)
        g=dict(status=worker.INPUT_PASS,scope='pilot32',prepared=r['prepared'],registration=r['CPU_registration'],sources=32,inputs=32)
        self.assertEqual(worker.validate_stage_inputs(r,p,g,'pilot32'),entries)
        bad=copy.deepcopy(p);bad['inference_inputs'][1]['source_id']=bad['inference_inputs'][0]['source_id']
        with self.assertRaises(ValueError):worker.validate_stage_inputs(r,bad,g,'pilot32')
        with self.assertRaises(ValueError):worker.validate_stage_inputs(dict(r,expected_inputs=426),p,g,'pilot32')

    def test_one_chunk_cache_and_token_only_reader_reconstruct_exact_F4(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);chunk=root/'chunk.pt';tokens=root/'tokens.pt'
            torch.save({'accepted':torch.tensor([1,2,3])},chunk);torch.save(dict(input_ids=torch.tensor([[1,2]]),attention_mask=torch.ones((1,2),dtype=torch.int64)),tokens)
            q=dict(tokens=reference(tokens),source=dict(source_vision=reference(chunk)))
            packed=dict(pixel_values=torch.zeros((4,1536),dtype=torch.float32),image_grid_thw=torch.tensor([[1,2,2]]))
            tok=torch.load(tokens,weights_only=True);q['input_signature']=input87.signature(dict(**tok,**packed));qr=write(root/'q.json',q)
            reader=object.__new__(worker.ChunkReader);reader.cached_key=None;reader.raw=None;reader.actual_chunk_loads=0
            reader.base=input87;reader.domain=SimpleNamespace(extract_view=lambda raw,s,b:(packed,{}));reader.allowed={worker.key(qr):{}}
            calls=[]
            def bound(ref):calls.append(ref['path']);return Path(ref['path'])
            with mock.patch.object(worker,'bound',side_effect=bound):
                first,_=reader.get(qr);second,_=reader.get(qr)
                self.assertEqual(reader.actual_chunk_loads,1)
                self.assertEqual(calls.count(str(chunk.resolve())),1)
                self.assertEqual(input87.signature(first),input87.signature(second))
                changed=copy.deepcopy(q);changed['input_signature']['pixel_values']['sha256']='f'*64
                other=write(root/'bad.json',changed);reader.allowed[worker.key(other)]={}
                with self.assertRaises(ValueError):reader.get(other)

    def fixture(self,root,n=32):
        modelrefs={k:fake_ref(k) for k in ('training_completion','adapter_weights','head_weights')}
        r=dict(modelrefs,output_root=str(root),prepared=fake_ref('prepared'),input_acceptance=fake_ref('gate'),CPU_registration=fake_ref('CPU'),expected_inputs=n,
            domain=fake_ref('domain'),critic_state=fake_ref('state'),promotion=fake_ref('promotion'),fresh8_result=fake_ref('fresh8'),protected_baseline=fake_ref('baseline'),max_seconds=60,max_new_bytes=100000000,deadline_utc='2099-01-01T00:00:00Z')
        entries=[];requests={};sources=[]
        for i in range(n):
            s=dict(source_id='official:0:native:'+str(i*2),source_sha256='a'*64,width=320,height=180,baseline_box=[0,0,160],video_id='0',native_ordinal=i*2,native_pts_exact=str(i),observation_index=i*2)
            q=dict(s,id=str(i),role='formal',input_signature={'four':'exact'},image_grid_thw=[[1,2,2]],reference_or_target_in_prompt=False)
            qr=write(root/('q%d.json'%i),q);e=dict(id=str(i),source_id=s['source_id'],source_sha256=s['source_sha256'],role='formal',input=qr)
            entries.append(e);requests[str(i)]=q;sources.append(s)
        p=dict(schema=worker.INPUT_SCHEMA,scope='pilot32',CPU_targets=None,inference_inputs=entries,execution_entries=entries,sources=n)
        g=dict(status=worker.INPUT_PASS,scope='pilot32',prepared=r['prepared'],registration=r['CPU_registration'],sources=n,inputs=n,elapsed_seconds=.01,new_bytes=500)
        return r,p,g,entries,requests,sources

    def test_remaining_exact_tail_requires_actual_pilot_QA_and_cost_bindings(self):
        sources=[dict(source_id='owner'+str(i)) for i in range(35)];r={k:fake_ref(k) for k in ('domain','source_catalog','training_completion','adapter_weights','head_weights','critic_state','promotion','fresh8_result')}
        r.update(remaining_admission=fake_ref('remaining'),deadline_utc='2099-01-01T00:00:00Z',max_seconds=100,max_new_bytes=100000)
        d=dict(pilot_source_ids=[s['source_id'] for s in sources[:32]])
        a=dict(schema='EXPLICIT_GEOM136_MEASURED_REMAINING_ADMISSION',capacity_review_admitted=True,
            **{k:r[k] for k in ('domain','source_catalog','training_completion','adapter_weights','head_weights','critic_state','promotion','fresh8_result')},
            remaining_source_ids=[s['source_id'] for s in sources[32:]],deadline_utc=r['deadline_utc'],max_seconds=100,max_new_bytes=100000,
            pilot_output_acceptance=fake_ref('pilotQA'),pilot_input_acceptance=fake_ref('pilotInputs'),pilot_GPU_completion=fake_ref('pilotDone'),pilot_resource=fake_ref('pilotCost'))
        pilot=dict(status=worker.RAW_PASS,scope='pilot32',source_ids=d['pilot_source_ids'],actual_new_forwards=32,input_acceptance=a['pilot_input_acceptance'],completion=a['pilot_GPU_completion'],resource=a['pilot_resource'])
        with mock.patch.object(worker,'load',side_effect=lambda ref:a if ref==r['remaining_admission'] else pilot):
            self.assertEqual(worker.selected_scope(r,'prepare_remaining',sources,d),sources[32:])
            a['remaining_source_ids'][0]='owner0'
            with self.assertRaises(ValueError):worker.selected_scope(r,'prepare_remaining',sources,d)

    def test_gpu_raw_first_preserves_hidden_and_head_when_postcheck_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r,p,g,entries,requests,_=self.fixture(root)
            helper=SimpleNamespace(_input=lambda reader,e,torch:({'x':torch.zeros(1)},requests[e['id']]),_hidden=lambda *args:torch.ones(4096))
            frozen=SimpleNamespace(_tensor_file=lambda path,value,torch:worker.tensor_file(path,value,torch))
            def model(regroot,reg,callback):
                callback(None,lambda h:torch.tensor([float('nan'),0.,0.]),helper,math105,frozen,torch)
            with mock.patch.dict('os.environ',{'CUDA_VISIBLE_DEVICES':'0'}),mock.patch.object(worker,'admission'),mock.patch.object(worker,'load',side_effect=lambda ref:p if ref==r['prepared'] else g),\
                mock.patch.object(worker,'ChunkReader'),mock.patch.object(worker,'readonly_model',side_effect=model),mock.patch.object(worker,'ref',side_effect=reference),\
                mock.patch.object(torch.Tensor,'to',lambda self,*args,**kwargs:self):
                with self.assertRaises(ValueError):worker.gpu_stage(root,root/'GPU.json',r,'gpu32')
            out=root/'GPU_pilot32'
            self.assertTrue((out/'000000.hidden.pt').is_file());self.assertTrue((out/'000000.head.pt').is_file())
            failure=json.loads((out/'failure.json').read_text());self.assertEqual(len(failure['attempts']),1)
            self.assertTrue(failure['attempts'][0]['returned']);self.assertFalse((out/'completion.json').exists())

    def test_actual_raw_QA_and_policy_loop_no_GT_then_exact_pilot_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r,p,g,entries,requests,sources=self.fixture(root);out=root/'GPU_pilot32';out.mkdir()
            head=dict(weight=torch.zeros((3,4096)),bias=torch.zeros(3));hp=root/'head.pt';torch.save(head,hp);r['head_weights']=reference(hp)
            state=dict(hidden_mean=__import__('numpy').zeros(4096),PCA_components=__import__('numpy').zeros((4096,32)),RMS=__import__('numpy').ones(107),JOINT_beta=__import__('numpy').zeros(107),GEOM11_beta=__import__('numpy').zeros(11))
            statepath=root/'state.npz';__import__('numpy').savez(statepath,**state);r['critic_state']=reference(statepath)
            journal=[];records=[]
            for i,(e,s) in enumerate(zip(entries,sources)):
                hidden=torch.ones(4096);z=torch.zeros(3);hfile=out/('%d.h.pt'%i);zfile=out/('%d.z.pt'%i);torch.save(hidden,hfile);torch.save(z,zfile)
                receipt=dict(id=e['id'],source_id=s['source_id'],source_sha256=s['source_sha256'],input=e['input'],input_signature=requests[e['id']]['input_signature'],image_grid_thw=[[1,2,2]],scope='pilot32',model_role=worker.ROLE,
                    actual_new_forward=True,alias_of=None,targets_read=False,no_training=True,width=320,height=180,hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',
                    adapter_weights=r['adapter_weights'],head_weights=r['head_weights'],raw_hidden=reference(hfile),raw_head=reference(zfile),decoded_xyw=math105.decode_numpy(z.numpy(),320,180).tolist(),
                    native_binding={k:s[k] for k in ('video_id','native_ordinal','native_pts_exact','observation_index')})
                rp=write(out/('%d.receipt.json'%i),receipt);records.append(dict(e,receipt=rp))
                journal.extend([dict(event='BEGIN_NEW_ROLE_FORWARD',id=e['id'],model_role=worker.ROLE,input=e['input']),dict(event='FIRST_RAW_PERSISTED',id=e['id'],model_role=worker.ROLE,raw_hidden=receipt['raw_hidden'],raw_head=receipt['raw_head']),dict(event='ACCEPTED_NEW_ROLE_RESULT',id=e['id'],model_role=worker.ROLE,receipt=rp)])
            jp=root/'attempts.jsonl';jp.write_text(''.join(json.dumps(x)+'\n' for x in journal));regref=write(root/'GPUreg.json',dict(GPU_job='synthetic'))
            done=dict(status='COMPLETE_GEOM136_NEW_STAGE_RAW_NOT_QUALITY',scope='pilot32',model_role=worker.ROLE,sources=32,expected_inputs=32,actual_forward_calls=32,aliases=0,input_prepared=r['prepared'],input_acceptance=r['input_acceptance'],
                **{k:r[k] for k in ('training_completion','adapter_weights','head_weights','domain','critic_state','promotion','fresh8_result')},GPU_registration=regref,entries=records,attempts=reference(jp),elapsed_forward_seconds=1.,elapsed_forward_seconds_max=.1)
            donepath=root/'completion.json';r['GPU_completion']=write(donepath,done)
            trained=dict(inventory={'resident':8774803699},base_fingerprint={'sha256':'b'*64})
            integrity=dict(status='PASS_GEOM136_READONLY_MODEL_BYTE_IDENTITY',registration=regref,completion=r['GPU_completion'],adapter_all288_exact=True,head_all2_exact=True,all_weights_frozen=True,physical_GPU_parameters=8774803699,conservative_pipeline_parameters=8790372845,**trained)
            r['model_integrity']=write(root/'integrity.json',integrity);resource=dict(name='synthetic',status='completed',exit_code=0)
            r['resource_receipt_path']=str(root/'resource.json');write(r['resource_receipt_path'],resource)
            ledger=root/'ledger.jsonl';ledger.write_text(json.dumps(resource)+'\n');r['gpu_ledger_path']=str(ledger)
            r.update(raw_QA_code127=fake_ref('rawQA'),math_code=fake_ref('math'),frozen_review84_code=fake_ref('review84'),geometry_code=fake_ref('geometry'),critic_code128=fake_ref('critic'),promotion_code129=fake_ref('promotioncode'))
            lookup={worker.key(r['prepared']):p,worker.key(r['input_acceptance']):g,worker.key(r['training_completion']):trained}
            actual_load=worker.load
            modules={'rawQA127':qa127,'math105':math105,'review84':review84,'geometry31':geometry31,'critic128':critic128,'promotion129':promotion129}
            write(root/'QAreg.json',r)
            with mock.patch.dict('os.environ',{'CUDA_VISIBLE_DEVICES':''}),mock.patch.object(worker,'admission'),mock.patch.object(worker,'source_scope',return_value=(sources,{},None,None)),\
                mock.patch.object(worker,'selected_scope',return_value=sources),mock.patch.object(worker,'bound',side_effect=lambda ref:Path(ref['path'])),mock.patch.object(worker,'ref',side_effect=reference),\
                mock.patch.object(worker,'load',side_effect=lambda ref:lookup[worker.key(ref)] if worker.key(ref) in lookup else actual_load(ref)),mock.patch.object(worker,'module',side_effect=lambda ref,name:modules[name]):
                worker.review_stage(root,root/'QAreg.json',r,'qa32')
            accepted=json.loads((root/'QA_pilot32.json').read_text());self.assertEqual(accepted['actual_new_forwards'],32)
            self.assertTrue(all(x['chosen_box']==x['baseline_box'] and x['predicted_gain']==0 and x['critic_uses_hidden'] is False for x in accepted['predictions']))


if __name__=='__main__':unittest.main()
