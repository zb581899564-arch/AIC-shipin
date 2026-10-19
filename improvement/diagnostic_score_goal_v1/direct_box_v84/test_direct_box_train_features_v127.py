import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import numpy as np
import torch
import direct_box_train_feature_gpu_v127 as gpu
import direct_box_train_feature_review_v127 as qa
import direct_box_gpu_preclamp_v105 as helper
import direct_box_math_preclamp_v105 as math105
import direct_box_review_v84 as review84
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crop_geometry_v31 as geometry


def r(name):return dict(path='/synthetic/'+name,sha256='a'*64)


def fixture(root,*,fail_head=False):
    root=Path(root);out=root/'raw';out.mkdir();inputs={};entries=[];sources=[]
    for i in range(3):
        cid='i'+str(i);sid='train'+str(i);sha=f'{i:064x}'
        v=dict(input_ids=torch.ones((1,5),dtype=torch.int64),attention_mask=torch.ones((1,5),dtype=torch.int64),
            pixel_values=torch.zeros((4,1536),dtype=torch.float32),image_grid_thw=torch.tensor([[1,2,2]],dtype=torch.int64))
        q=dict(id=cid,source_id=sid,source_sha256=sha,role='train',width=160,height=100,
            reference_or_target_in_prompt=False,input_signature=helper.signature(v),image_grid_thw=[[1,2,2]])
        path=root/(cid+'.json');gpu.save(path,q);qr=gpu.ref(path);inputs[qr['path']]=(v,q)
        entries.append(dict(id=cid,source_id=sid,source_sha256=sha,role='train',input=qr))
        sources.append(dict(source_id=sid,source_sha256=sha,role='train',width=160,height=100))
    calls=[]
    def core(**values):
        calls.append(values);return SimpleNamespace(last_hidden_state=torch.arange(1,4097,dtype=torch.float32).reshape(1,1,4096))
    class Model:
        def eval(self):return self
        def parameters(self):return iter(())
        def get_base_model(self):return SimpleNamespace(model=core)
    head=torch.nn.Linear(4096,3)
    with torch.no_grad():head.weight.fill_(.001);head.bias.copy_(torch.tensor([.001,-.001,-.02]))
    head.requires_grad_(False)
    if fail_head:
        def broken(_):raise RuntimeError('head failed after raw hidden')
        head.forward=broken
    def tensor_file(path,value,_):
        with Path(path).open('xb') as f:torch.save(value,f);f.flush();os.fsync(f.fileno())
    reg=dict(purpose='CRITIC_TRAIN_FEATURES_ONLY',expected_inputs=3,prepared=r('prepared87'),CPU_registration=r('CPU87'),input_acceptance=r('gate622'),
        training_completion=r('trained105'),adapter_weights=r('adapter105'),head_weights=r('head105'))
    registration=r('GPU127');trace=dict(attempted=[],raw=[])
    old_to=torch.Tensor.to
    def cpu_to(self,*args,**kwargs):return self if args and args[0]=='cuda:0' else old_to(self,*args,**kwargs)
    with mock.patch.object(torch.Tensor,'to',cpu_to),mock.patch.object(torch.cuda,'synchronize'):
        completion=gpu.extract_stage(out,reg,registration,entries,SimpleNamespace(get=lambda rr:inputs[rr['path']]),
            Model(),head,helper,math105,SimpleNamespace(_deadline=lambda _:None,_tensor_file=tensor_file),torch,trace)
    integrity=dict(status=gpu.INTEGRITY,registration=registration,training_completion=reg['training_completion'],adapter_all288_exact=True,
        head_all2_exact=True,all_weights_frozen=True,targets_read=False,no_training=True)
    return SimpleNamespace(out=out,reg=reg,registration=registration,done=gpu.read(completion['path']),integrity=integrity,
        entries=entries,sources=sources,head=head.state_dict(),calls=calls,trace=trace)


def review(f,load_tensor=None,load_json=None):
    return qa.review_scope(f.reg,f.registration,f.done,f.integrity,f.entries,f.sources,f.head,
        load_json=load_json or (lambda rr:gpu.read(rr['path'])),
        load_tensor=load_tensor or (lambda rr:torch.load(rr['path'],map_location='cpu',weights_only=True)),
        load_events=lambda rr:[json.loads(s) for s in Path(rr['path']).read_text().splitlines() if s],
        math105=math105,review84=review84,geometry=geometry,torch=torch,expected_count=3)


class TrainFeature127Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(2)

    def test_train602_whitelist_and_no_GT_refs(self):
        entries=[dict(id=str(i),source_id='s'+str(i),source_sha256=f'{i:064x}',role='train') for i in range(602)]
        screen=[dict(source_sha256=f'{i+1000:064x}') for i in range(20)]
        reg=dict(schema=gpu.SCHEMA,purpose='CRITIC_TRAIN_FEATURES_ONLY',feature_pass_admitted=True,expected_inputs=602,expected_sources=602,
            prepared=r('p'),CPU_registration=r('cpu87'))
        prepared=dict(schema='DIRECT_BOX_SOURCE_ONLY_INPUTS_V84',train_inputs=entries,screen_inputs=screen)
        gate=dict(status='PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA',prepared=reg['prepared'],registration=reg['CPU_registration'])
        self.assertEqual(len(gpu.validate_inputs(reg,prepared,gate)),602)
        bad=copy.deepcopy(prepared);bad['train_inputs'][0]['role']='screen'
        with self.assertRaises(ValueError):gpu.validate_inputs(reg,bad,gate)
        self.assertFalse({'train_targets','CPU_targets','source_catalog','native20_quality_result','confirm19_quality_result'}&set(gpu.GPU_REFS))

    def test_raw_first_independent_head_native_and_compact_features(self):
        with tempfile.TemporaryDirectory() as temp:
            f=fixture(temp);accepted,features=review(f)
            self.assertEqual(len(f.calls),3);self.assertEqual(accepted['status'],qa.STATUS)
            self.assertEqual(features['hidden4096'].shape,(3,4096));self.assertEqual(features['hidden4096'].dtype,np.float32)
            self.assertEqual(features['normalized_hidden4096'].dtype,np.float32)
            self.assertTrue(np.allclose(np.linalg.norm(features['normalized_hidden4096'],axis=1),1.))
            self.assertEqual(features['native_DIRECT3'].shape,(3,3));self.assertEqual(features['native_DIRECT3'].dtype,np.int64)
            self.assertEqual(features['source_ids'].tolist(),[s['source_id'] for s in f.sources])
            with (Path(temp)/'features.npz').open('xb') as stream:np.savez(stream,**features)
            with np.load(Path(temp)/'features.npz',allow_pickle=False) as loaded:self.assertTrue(all(np.array_equal(loaded[k],v) for k,v in features.items()))

    def test_bad_head_owner_alias_or_missing_raw_is_not_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            f=fixture(temp)
            def bad_raw(rr):
                value=torch.load(rr['path'],weights_only=True)
                return value+.1 if value.shape==(3,) else value
            with self.assertRaisesRegex(ValueError,'head replay'):review(f,load_tensor=bad_raw)
            def bad_owner(rr):
                d=gpu.read(rr['path'])
                if 'raw_hidden' in d:d['source_sha256']='f'*64
                return d
            with self.assertRaises(ValueError):review(f,load_json=bad_owner)
            broken=copy.deepcopy(f.done);broken['aliases']=1;f.done=broken
            with self.assertRaises(ValueError):review(f)
        with tempfile.TemporaryDirectory() as temp:
            f=fixture(temp);receipt=gpu.read(f.done['entries'][0]['receipt']['path']);Path(receipt['raw_hidden']['path']).unlink()
            with self.assertRaises(FileNotFoundError):review(f)

    def test_head_failure_preserves_first_hidden_no_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError,'after raw hidden'):fixture(temp,fail_head=True)
            self.assertTrue((Path(temp)/'raw/0000.hidden.pt').is_file())
            self.assertFalse((Path(temp)/'raw/0000.head.pt').exists());self.assertFalse((Path(temp)/'raw/completion.json').exists())

    def test_unique_natural_resource_receipt(self):
        resource=dict(name='job127',status='completed',exit_code=0)
        qa.validate_resource(resource,[dict(name='external'),resource],'job127')
        with self.assertRaises(ValueError):qa.validate_resource(resource,[resource,resource],'job127')
        with self.assertRaises(ValueError):qa.validate_resource(dict(resource,exit_code=1),[resource],'job127')


if __name__=='__main__':unittest.main()
