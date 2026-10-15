"""Synthetic24-answer acceptance/negative controls; no actual model or processor."""
from contextlib import ExitStack
from fractions import Fraction as F
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import json
import sys
import unittest
from common import sha, save
from native_runtime import native_ranges
from scientific_gate import summarize, gate
from test_runtime import fixture, q, e, summaries
from verify_evaluation import reconstruct

RUN=Path(__file__).resolve().parents[3]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


class ReconstructionTests(unittest.TestCase):
    def make(self, root):
        jobs,refs,old,new=fixture()
        keys=sorted(jobs)
        for j in jobs.values():
            w=j['window'];a=F(w['domain_start_exact']);b=F(w['domain_end_exact']);first=int(a*10)
            ids=[first+i*99//63 for i in range(64)]
            w.update(window_id='synthetic',planned_source_frame_ordinals=ids,
                eligible_exact_pts=[str(a+F(i,10)) for i in range(100)],eligible_source_frame_count=100,
                planned_exact_pts=[str(F(i,10)) for i in ids],planned_actual_pts_sec=[i/10 for i in ids],
                window_pts_start_sec=float(a),window_pts_end_exclusive_sec=float(b),source_total_frames=400)
        evaluation=root/'evaluate_01';evaluation.mkdir()
        initial=root/'initial';initial.mkdir();(initial/'adapter_model.safetensors').write_bytes(b'synthetic-old')
        final=root/'final';final.mkdir();(final/'adapter_model.safetensors').write_bytes(b'synthetic-new')
        model=root/'model';model.mkdir();save(model/'generation_config.json',dict(eos_token_id=9999))
        pre=root/'cpu';pre.mkdir();rows=[];evidence={}
        for i,key in enumerate(keys):
            evidence[key]=dict(window_id=key,processor_identity=dict(input_tokens=8),synthetic_identity_only=True)
            p=pre/('%02d.input.json'%i)
            save(p,dict(window_id=key,actual_native_and_reviewed_processor_equal=True,training_target_present=False,evidence=evidence[key]))
            rows.append(dict(window_id=key,input_receipt=dict(path=str(p),sha256=sha(p))))
        pp=pre/'receipt.json';save(pp,dict(status='PASS_ACTUAL_CPU_NATIVE_PROCESSOR_AND_ASSISTANT_TARGET_PARITY_NOT_TRAINING',
            lock_sha256='lock',config_sha256='config',model_loaded=False,cuda_initialized=False,rows=rows))
        training=dict(native_cpu_preflight_receipt=dict(path=str(pp),sha256=sha(pp)),final_adapter_sha256=sha(final/'adapter_model.safetensors'))
        contract=dict(config=dict(historical_run_root=str(RUN),processor_dir=str(model),model_dir=str(model),
            evaluate_output_dir=str(evaluation),initial_adapter_dir=str(initial),final_only_evaluation_window_ids=keys),
            jobs=jobs,refs=refs,reference_sha={k:'reference-'+k for k in keys},quality=q,events=e,
            lock_sha='lock',config_sha='config',lock_path=str(root/'unused_lock'))
        token_text={0:'{"segments":[]}',250:'{"segments":[[0,2.5]]}',300:'{"segments":[[0,3]]}',7:'7'}
        for arm,predictions,adapter in [('original_B',old,initial),('new_final',new,final)]:
            folder=evaluation/arm;folder.mkdir()
            for i,key in enumerate(keys):
                p=predictions[key];t=0 if not p['parsed_segments'] else (250 if arm=='original_B' else 300)
                rp=folder/('%02d.raw.json'%i)
                save(rp,dict(actual_model_call=True,window=jobs[key]['window'],video_identity=evidence[key],input_tokens=8,
                    output_token_ids=[t],selected_token_scores=[-1.],raw_output=token_text[t]))
                dp=folder/('%02d.done.json'%i)
                save(dp,dict(window_id=key,arm=arm,adapter_sha256=sha(adapter/'adapter_model.safetensors'),
                    reference_sha256=contract['reference_sha'][key],raw_receipt=str(rp),raw_sha256=sha(rp),
                    status=p['status'],parsed_segments=p['parsed_segments'],native_frame_ranges=native_ranges(p['parsed_segments'],jobs[key]['window']),parse_warnings=[]))
        b,n=summaries(jobs,refs,old),summaries(jobs,refs,new)
        g=gate(b['process_dev'],n['process_dev'],b['locked_development_evaluation'],n['locked_development_evaluation'],q)
        gp=evaluation/'scientific_gate.json';save(gp,g)
        ep=evaluation/'evaluation_receipt.json';save(ep,dict(status='PASS_FINAL_ONLY_EVALUATION_ENGINEERING',final_only=True,
            model_calls=24,lock_sha256='lock',config_sha256='config',final_training_receipt_sha256='train',
            scientific_gate_sha256=sha(gp),quality_gate_passed=True,summaries=dict(original_B=b,new_final=n)))
        return contract,final,training,ep,token_text

    def run_fixture(self, root, mutate=None):
        contract,final,training,ep,text=self.make(root)
        if mutate:mutate(ep.parent)
        tokenizer=SimpleNamespace(decode=lambda ids,**kw: ''.join(text[t] for t in ids if t!=9999),eos_token_id=9999)
        fake_transformers=SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**kw: tokenizer))
        fake_torch=SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda:False))
        # Actual original parser/grammar are loaded. Only vocab discovery and
        # heavyweight runtime construction are mocked for synthetic fixtures.
        import verify_evaluation
        real_load=verify_evaluation.load
        def loaded(path,name):
            module=real_load(path,name)
            if name=='independent_eval_grammar':module.ascii_token_candidates=lambda token:[0,250,300,7]
            return module
        with ExitStack() as stack:
            stack.enter_context(patch('verify_evaluation.validate_final',return_value=(final,training)))
            stack.enter_context(patch('verify_evaluation.verify_lock',return_value={}))
            stack.enter_context(patch('verify_evaluation.load',side_effect=loaded))
            stack.enter_context(patch.dict(sys.modules,{'transformers':fake_transformers,'torch':fake_torch}))
            return reconstruct(contract,ep,sha(ep),'synthetic_training','train')

    def test_all24_actual_raw_reconstruction_fixture(self):
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as d:
            result=self.run_fixture(Path(d))
            self.assertTrue(result['quality_gate_passed']);self.assertEqual(len(result['bindings']),24)
            self.assertEqual(result['new_model_calls'],0)

    def test_wrong_generated_tokens_rejected_even_with_valid_json(self):
        def change(folder):
            p=folder/'new_final/00.raw.json';raw=json.loads(p.read_text());raw['output_token_ids']=[7];p.write_text(json.dumps(raw))
            dp=folder/'new_final/00.done.json';done=json.loads(dp.read_text());done['raw_sha256']=sha(p);dp.write_text(json.dumps(done))
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as d:
            with self.assertRaisesRegex(ValueError,'do not decode'):self.run_fixture(Path(d),change)

    def test_wrong_answer_arm_adapter_rejected(self):
        def change(folder):
            p=folder/'new_final/00.done.json';row=json.loads(p.read_text());row['adapter_sha256']='wrong';p.write_text(json.dumps(row))
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as d:
            with self.assertRaisesRegex(ValueError,'answer arm/window/reference'):self.run_fixture(Path(d),change)

    def test_wrong_generation_input_rejected(self):
        def change(folder):
            p=folder/'new_final/00.raw.json';raw=json.loads(p.read_text());raw['video_identity']['window_id']='foreign';p.write_text(json.dumps(raw))
            dp=folder/'new_final/00.done.json';done=json.loads(dp.read_text());done['raw_sha256']=sha(p);dp.write_text(json.dumps(done))
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as d:
            with self.assertRaisesRegex(ValueError,'generation input differs'):self.run_fixture(Path(d),change)

if __name__=='__main__':unittest.main()
