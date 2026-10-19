import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch
import direct_box_inference_v97 as gpu
import direct_box_gpu_recovery_v93 as helper
import direct_box_math_recovery_v93 as math93


def fake_ref(name): return dict(path='/synthetic/'+name, sha256='a'*64)


def bounded(reference):
    path=Path(reference['path']).resolve()
    if not path.is_file() or gpu.ref(path)!=reference: raise ValueError('Missing or changed bound file')
    return path


def registration(root,phase='formal',count=500,video_count=350):
    reg={name:fake_ref(name) for name in gpu.GPU_REFS}
    reg.update(schema=gpu.SCHEMA,phase=phase,inference_admitted=True,GPU_code=dict(path=str(Path(gpu.__file__).resolve()),sha256='a'*64),
        CPU_registration=dict(path=str(root/'cpu.json'),sha256='a'*64),prepared=dict(path=str(root/'prepared.json'),sha256='a'*64),
        input_acceptance=dict(path=str(root/'gate.json'),sha256='a'*64),output_directory=str(root/'direct_box_inference_97'/phase),
        expected_inputs=count,expected_sources=count,admitted_arm_names=['ANCHORED_HALF'])
    def summary(status,result,arms):
        return dict(status=status,result=result,admitted_arm_names=arms,
            **{k:reg[k] for k in ('training_completion','adapter_weights','head_weights')})
    reg['native20_quality_summary']=summary('PASS_DIRECT_BOX93_NATIVE20_QUALIFIED_ARMS',reg['native20_quality_result'],['DIRECT','ANCHORED_HALF'] if phase=='formal' else ['ANCHORED_HALF'])
    if phase=='formal':
        reg.update(confirm19_quality_result=fake_ref('confirm19_quality_result'),production_admitted=True,
            official_source_count=426,affected_video_count=video_count,expected_affected_videos=video_count,
            affected_video_ids=['video'+str(i) for i in range(video_count)],whole426_preserved=True,
            time_selection_unchanged=True,selection='OBS_INDEX_EVEN')
        reg['confirm19_quality_summary']=summary('PASS_DIRECT_BOX95_CONFIRM19_QUALIFIED_ARMS',reg['confirm19_quality_result'],['ANCHORED_HALF'])
    return reg


def stage_fixture(root,*,fail_head=False):
    root=Path(root);out=root/'new';out.mkdir();docs=root/'docs';docs.mkdir()
    inputs={};entries=[]
    for i,(sid,vid) in enumerate((('a','va'),('b','vb'),('b','vb'))):
        cid='i'+str(i);sha=(sid*64)
        values=dict(input_ids=torch.ones((1,5),dtype=torch.int64),attention_mask=torch.ones((1,5),dtype=torch.int64),
            pixel_values=torch.zeros((4,1536),dtype=torch.float32),image_grid_thw=torch.tensor([[1,2,2]],dtype=torch.int64))
        q=dict(id=cid,source_id=sid,source_sha256=sha,role='formal',width=160,height=100,
            reference_or_target_in_prompt=False,input_signature=helper.signature(values),image_grid_thw=[[1,2,2]],
            video_id=vid,native_ordinal=2,native_pts_exact=[1,25],observation_index=2)
        qp=docs/(cid+'.json');gpu.save(qp,q);qr=gpu.ref(qp)
        entries.append(dict(id=cid,source_id=sid,source_sha256=sha,role='formal',input=qr));inputs[qr['path']]=(values,q)
    reg=dict(phase='formal',expected_inputs=3,expected_sources=2,affected_video_count=2,expected_affected_videos=2,
        affected_video_ids=['va','vb'],selection='OBS_INDEX_EVEN',admitted_arm_names=['DIRECT'],
        prepared=fake_ref('prepared'),CPU_registration=fake_ref('CPUreg'),input_acceptance=fake_ref('gate'),
        training_completion=fake_ref('training798'),adapter_weights=fake_ref('adapter798'),head_weights=fake_ref('head798'))
    olddir=root/'old';olddir.mkdir()
    hidden_path=olddir/'hidden.pt';head_path=olddir/'head.pt'
    hidden_path.write_bytes(b'old accepted hidden; must never torch.load')
    head_path.write_bytes(b'old accepted head; must never torch.load')
    oldq=inputs[entries[1]['input']['path']][1]
    oldreceipt=dict(**{k:oldq[k] for k in ('id','source_id','source_sha256','role','width','height','input_signature','image_grid_thw')},
        input=entries[1]['input'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
        hidden_transform=math93.RECIPE['hidden_transform'],model_role='DIRECT_BOX93_TRAINED_screen',
        raw_hidden=gpu.ref(hidden_path),raw_head=gpu.ref(head_path),decoded_xyw=[0.,5.,160.])
    rp=olddir/'receipt.json';gpu.save(rp,oldreceipt)
    prediction=dict(**{k:oldreceipt[k] for k in ('id','source_id','source_sha256','input','raw_hidden','raw_head')},receipt=gpu.ref(rp))
    qa=dict(status='PASS_DIRECT_BOX93_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA',predictions=[prediction],
        **{k:reg[k] for k in ('training_completion','adapter_weights','head_weights')})
    ap=olddir/'QA.json';gpu.save(ap,qa);reg['adopted_output_acceptances']=[gpu.ref(ap)]
    calls=[]
    def core(**values):
        calls.append(values)
        return SimpleNamespace(last_hidden_state=torch.arange(1,4097,dtype=torch.float32).reshape(1,1,4096))
    class Model:
        def eval(self): return self
        def parameters(self): return iter(())
        def get_base_model(self): return SimpleNamespace(model=core)
    head=torch.nn.Linear(4096,3)
    with torch.no_grad():head.weight.fill_(.001);head.bias.copy_(torch.tensor([.001,-.001,-.01]))
    head.requires_grad_(False)
    if fail_head:
        def broken(_): raise RuntimeError('synthetic head failed after hidden persisted')
        head.forward=broken
    def tensor_file(path,value,_):
        with Path(path).open('xb') as stream:
            torch.save(value,stream);stream.flush();os.fsync(stream.fileno())
    return SimpleNamespace(out=out,reg=reg,prepared=dict(inference_inputs=entries),reader=SimpleNamespace(get=lambda r:inputs[r['path']]),
        model=Model(),head=head,frozen=SimpleNamespace(_deadline=lambda _:None,_tensor_file=tensor_file),
        calls=calls,qa_path=ap,oldreceipt=rp,oldraw=hidden_path)


class Inference97Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): torch.set_num_threads(2)

    def test_only_new798_L2_final_with_exact_old_step1_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            reg=registration(Path(temp))
            original={k:reg[k] for k in ('model_config','math_code','old_TIME','old_PAIR','old_CROP')}
            original.update(GPU_code=reg['frozen_GPU93_code'],original84_progress=fake_ref('old84step1'))
            trained=dict(status='COMPLETE_DIRECT_BOX93_NEW798_NOT_QUALITY',GPU_registration=reg['frozen_GPU93_registration'],
                completed_updates=798,successful_micro=3192,actual_training_forwards=3192,original_successful_updates=1,
                original_successful_forwards=8,original84_progress=original['original84_progress'],optimizer_reset=True,
                hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',adapter_reload_all288_exact=True,head_reload_all2_exact=True,
                adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'])
            gpu.validate_training(reg,original,trained)
            for key,value in [('completed_updates',800),('actual_training_forwards',3200),
                ('hidden_transform','UNSCALED'),('original_successful_forwards',4),('optimizer_reset',False)]:
                bad=copy.deepcopy(trained);bad[key]=value
                with self.assertRaises(ValueError):gpu.validate_training(reg,original,bad)

    def test_formal_D_not426_same_arm_and_rich_result_never_parsed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);reg=registration(root)
            with mock.patch.object(gpu,'bound',side_effect=lambda r:Path(r['path']).resolve()), mock.patch.object(gpu,'read',side_effect=AssertionError('GPU must not parse rich quality')):
                gpu.validate_admission(root,'formal',root/'direct_box_inference_registration_97_formal.json',reg)
                bad=copy.deepcopy(reg);bad['admitted_arm_names']=['DIRECT']
                with self.assertRaises(ValueError):gpu.validate_admission(root,'formal',root/'direct_box_inference_registration_97_formal.json',bad)
                bad=copy.deepcopy(reg);bad['output_directory']=str(root.parent/'escape')
                with self.assertRaises(ValueError):gpu.validate_admission(root,'formal',root/'direct_box_inference_registration_97_formal.json',bad)
                bad=copy.deepcopy(reg);bad['native20_quality_summary']['result']=fake_ref('wrongresult')
                with self.assertRaises(ValueError):gpu.validate_admission(root,'formal',root/'direct_box_inference_registration_97_formal.json',bad)

    def test_19_whitelist_missing_first_and_input_model_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);reg=registration(root,'confirm19',19)
            reg.update(prepared_schema='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V95',input_acceptance_status='PASS_DIRECT_BOX95_SOURCE_ONLY_FIRST_CPU_QA',expected_source_ids=['s'+str(i) for i in range(19)])
            entries=[dict(id=str(i),source_id='s'+str(i),source_sha256=f'{i:064x}',role='confirm',input=fake_ref(str(i))) for i in range(19)]
            prepared=dict(schema=reg['prepared_schema'],phase='confirm19',inference_inputs=entries,execution_entries=entries,adopted_success={},sources=19,
                **{k:reg[k] for k in ('training_completion','adapter_weights','head_weights','admitted_arm_names')})
            gate=dict(status=reg['input_acceptance_status'],phase='confirm19',prepared=reg['prepared'],registration=reg['CPU_registration'],sources=19,inputs=19)
            gpu.validate_inputs(reg,prepared,gate)
            bad=copy.deepcopy(prepared);bad['inference_inputs'][0]['source_id']='gnmc:test:006575.jpeg'
            with self.assertRaises(ValueError):gpu.validate_inputs(reg,bad,gate)
            bad=copy.deepcopy(prepared);bad['head_weights']=fake_ref('wronghead')
            with self.assertRaises(ValueError):gpu.validate_inputs(reg,bad,gate)

    def run_stage(self,fixture):
        original_to=torch.Tensor.to
        def cpu_to(self,*args,**kwargs):return self if args and args[0]=='cuda:0' else original_to(self,*args,**kwargs)
        trace=dict(attempted=[],raw=[])
        with mock.patch.object(gpu,'bound',side_effect=bounded),mock.patch.object(torch.Tensor,'to',cpu_to),mock.patch.object(torch.cuda,'synchronize'),mock.patch.object(torch,'load',side_effect=AssertionError('Old accepted raw must not be loaded')):
            result=gpu.inference_stage(fixture.out,fixture.reg,fake_ref('GPUreg97'),fixture.prepared,fixture.reader,
                fixture.model,fixture.head,helper,math93,fixture.frozen,torch,trace)
        return gpu.read(result['path']),trace

    def test_new_external_internal_alias_counts_and_normalized_head(self):
        # Duplicate owner below exercises the core internal alias branch; complete
        # registered manifests additionally enforce one input per unique owner.
        with tempfile.TemporaryDirectory() as temp:
            f=stage_fixture(temp);done,trace=self.run_stage(f)
            self.assertEqual((len(f.calls),done['actual_forward_calls'],done['external_adopted'],done['internal_aliases']),(1,1,1,1))
            self.assertEqual(done['model_role'],'DIRECT_BOX93_formal');self.assertEqual(done['official_source_count'],426)
            receipts=[gpu.read(e['receipt']['path']) for e in done['entries']]
            self.assertEqual([(r['actual_new_forward'],r['internal_alias'],r['external_alias']) for r in receipts],[(True,False,False),(False,False,True),(False,True,False)])
            self.assertEqual(receipts[1]['adopted_receipt'],gpu.ref(f.oldreceipt));self.assertIsNone(receipts[1]['alias_of'])
            self.assertEqual(receipts[2]['alias_of'],done['entries'][1]['receipt'])
            self.assertEqual(receipts[2]['raw_hidden'],receipts[1]['raw_hidden'])
            hidden=torch.load(receipts[0]['raw_hidden']['path'],weights_only=True)
            raw=torch.load(receipts[0]['raw_head']['path'],weights_only=True)
            self.assertTrue(torch.equal(raw,f.head(math93.normalize_hidden(hidden))))
            events=[json.loads(line) for line in Path(done['attempts']['path']).read_text().splitlines()]
            self.assertEqual([r['event'] for r in events],['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT','ADOPTED_PREVIOUSLY_QA_RAW','ACCEPTED_NEW_ROLE_RESULT','ACCEPTED_NEW_ROLE_RESULT'])
            self.assertEqual(events[3]['adopted_input'],receipts[1]['adopted_input'])
            self.assertEqual(trace['attempted'],['i0'])

    def test_head_failure_keeps_hidden_and_does_not_make_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            f=stage_fixture(temp,fail_head=True)
            with self.assertRaisesRegex(RuntimeError,'after hidden persisted'): self.run_stage(f)
            self.assertEqual(len(f.calls),1);self.assertTrue((f.out/'000000.hidden.pt').is_file())
            self.assertFalse((f.out/'000000.head.pt').exists());self.assertFalse((f.out/'completion.json').exists())

    def test_missing_prior_raw_and_wrong_prior_weights_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            f=stage_fixture(temp)
            with mock.patch.object(gpu,'bound',side_effect=bounded):
                self.assertEqual(len(gpu.adopted_index(f.reg)),1)
                f.oldraw.unlink()
                with self.assertRaises(ValueError):gpu.adopted_index(f.reg)
        with tempfile.TemporaryDirectory() as temp:
            f=stage_fixture(temp);qa=gpu.read(f.qa_path);qa['head_weights']=fake_ref('wrong')
            f.qa_path.write_text(json.dumps(qa));f.reg['adopted_output_acceptances']=[gpu.ref(f.qa_path)]
            with mock.patch.object(gpu,'bound',side_effect=bounded):
                with self.assertRaises(ValueError):gpu.adopted_index(f.reg)


if __name__=='__main__':unittest.main()
