#!/usr/bin/env python3
"""Pure CPU contracts; fake model bytes/targets do not authorize real training."""
from __future__ import annotations
import argparse
import ast
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sft_contract import (FIXED, MODEL_ID, REVISION, SCOPE, ROUTE, ORIGINAL_TRAIN_SHA, AdmissionRejected, EffectiveAccumulation,
    admit, answer_string, assistant_labels, language_target_names, legacy_clip_plan, segments_valid,
    sha256, validate_trainable_names, validate_training_rows,load_original_train)
from train_sft import gradient_evidence

HERE=Path(__file__).resolve().parent


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix="sft_cpu_",dir=HERE)
        self.root=Path(self.temporary.name)
        self.model=self.root/"model"; self.model.mkdir()
        for name,value in {"config.json":{"model_type":"qwen3_vl","text_config":{"hidden_size":4096}},
                           "model.safetensors.index.json":{"weight_map":{"fake":"model-00001.safetensors"}},
                           "tokenizer.json":{},"tokenizer_config.json":{},"preprocessor_config.json":{},
                           "video_preprocessor_config.json":{}}.items(): write(self.model/name,value)
        (self.model/"model-00001.safetensors").write_bytes(b"SYNTHETIC_BYTES_NOT_A_MODEL")
        self.receipt=self.root/"model_receipt.json"
        write(self.receipt,{"repo_id":MODEL_ID,"revision":REVISION,
            "files":[{"path":p.name,"sha256":sha256(p),"size_bytes":p.stat().st_size} for p in self.model.iterdir()]})
        self.source=self.root/"synthetic_source.mp4"; self.source.write_bytes(b"SYNTHETIC_NOT_MEDIA")
        metadata={"source_path":str(self.source),"source_sha256":sha256(self.source),"n_frames":1200,
            "fps_num":30,"fps_den":1,"width":64,"height":64,"split":"train","label_status":"WEAK_TEACHER",
            "pts_audit_status":"PASS","clip_start_sec":0.0,"clip_end_sec":32.134,
            "source_bytes":self.source.stat().st_size,"source_mtime_ns":self.source.stat().st_mtime_ns}
        parents=[]
        for index in range(704):
            pid=f"parent_{index}"; parent={**metadata,"parent_sample_id":pid,"video_id":f"video_{index}",
                "youtube_id":f"source_{index%602}","source_group":f"clip_group_{index}","registered_windows":[]}
            if index==0:
                parent["registered_windows"]=[{"parent_sample_id":pid,"window_id":pid+"__w0",
                    "clip_start_sec":0.0,"clip_end_sec":30.0,"segments_clip_local":[[1.0,2.0]]},
                    {"parent_sample_id":pid,"window_id":pid+"__w1","clip_start_sec":30.0,"clip_end_sec":32.134,
                     "segments_clip_local":[[0.0,2.1339]]}]
            parents.append(parent)
        self.registry={"schema":"aic_sft8b_r7_train_registry_v1","expected_parent_count":704,
                       "origin_train_manifest_sha256":ORIGINAL_TRAIN_SHA,"records":parents}
        self.original=[{**parent,"sample_id":parent["parent_sample_id"],"source_avg_fps":30.0,
            "decoded_source_frames":1200,"pts_frame_interval_sec":1/30,"pts_max_residual_sec":0.0} for parent in parents]
        self.original_path=self.root/"synthetic_original_fixture.json"; write(self.original_path,self.original)
        self.registry_path=self.root/"registry.json"; write(self.registry_path,self.registry)
        parent=parents[0]
        self.rows=[{**{k:v for k,v in parent.items() if k!="registered_windows"},"sample_id":parent["parent_sample_id"],**window}
                   for window in parent["registered_windows"]]
        self.manifest=self.root/"train.jsonl"; self.save_rows()
        self.tc=self.root/"temporal_common.py"
        self.tc.write_text("MAX_FRAMES = 64\nMAX_PIXELS = 128 * 32 * 32\n",encoding="utf-8")
        self.core=self.root/"r7_core.py"; self.core.write_text("# synthetic helper, never imported\n",encoding="utf-8")
        spec=lambda path:{"path":str(path),"sha256":sha256(path)}
        self.config={**copy.deepcopy(FIXED),"model_dir":str(self.model),"model_receipt":spec(self.receipt),
            "train_manifest":spec(self.manifest),"r7_train_registry":spec(self.registry_path),"temporal_common":spec(self.tc),
            "r7_core":spec(self.core),"out_dir":str(self.root/"run"),"updates":5,"grad_accum":16,"lr":5e-5,
            "seed":20261006,"max_sequence_length":8192,"max_wall_seconds":1800}
        self.config_path=self.root/"config.json"; write(self.config_path,self.config)
        self.choice=self.root/"choice.json"; write(self.choice,{"authorized":True,"scope":SCOPE,"route":ROUTE,
            "authority_kind":"USER_TRAINING_REQUEST_MAIN_REGISTERED_B_ROUTE","user_request_quote":"然后推理打包开训。",
            "explicit_user_route_choice":False,"authorization_inferred_from_nonresponse":False,
            "formal_c_bce_admitted":False,"full_training_admitted":False,"fixture_only":True})
        self.admission={"schema":"aic_temporal_sft8b_admission_v1","scope":SCOPE,"authorized":True,
            "registered_route":ROUTE,"training_authorized_by_user":True,"training_authorization_evidence":spec(self.choice),"config_sha256":sha256(self.config_path),
            "train_manifest_sha256":sha256(self.manifest),"r7_train_registry_sha256":sha256(self.registry_path),
            "model_receipt_sha256":sha256(self.receipt),"source_code_sha256":{name:sha256(HERE/name) for name in ("sft_contract.py","train_sft.py")},
            "resource_preflight_pass":True,"shared_gpu_queue_approved":True,"disk_peak_within_80gib":True,
            "budget_runner_required":True,"formal_c_bce_admitted":False}
        self.admission_path=self.root/"admission.json"; write(self.admission_path,self.admission)

    def tearDown(self): self.temporary.cleanup()
    def save_rows(self):
        self.manifest.write_text("".join(json.dumps(row)+"\n" for row in self.rows),encoding="utf-8")
    def refresh_config(self):
        write(self.config_path,self.config); self.admission["config_sha256"]=sha256(self.config_path)
        write(self.admission_path,self.admission)
    def validate(self,registry,rows): return validate_training_rows(registry,rows,self.original)
    def guard_cli(self,check_only=True):
        guard=self.root/"guard"; guard.mkdir(exist_ok=True)
        (guard/"sitecustomize.py").write_text('''import sys,os,json
class Guard:
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'torch','numpy','decord','peft','transformers'}:
   open(os.environ['SFT_RUNTIME_IMPORT_MARKER'],'w').write(fullname)
   raise RuntimeError('FORBIDDEN_RUNTIME_IMPORT_BEFORE_ADMISSION')
sys.meta_path.insert(0,Guard())
# This child uses synthetic original metadata only. The real pinned loader is
# separately tested with main's actual 704 file, and never patched in runtime.
sys.path.insert(0,os.environ['SFT_TEST_CODE_ROOT'])
import sft_contract
sft_contract.load_original_train=lambda path=None: json.load(open(os.environ['SFT_TEST_ORIGIN_FIXTURE']))
''',encoding="utf-8")
        marker=self.root/"runtime_imported.txt"
        args=[sys.executable,"-B",str(HERE/"train_sft.py"),"--config",str(self.config_path),"--admission",str(self.admission_path)]
        if check_only: args.append("--check-only")
        result=subprocess.run(args,env=dict(os.environ,PYTHONPATH=str(guard),PYTHONDONTWRITEBYTECODE="1",
            SFT_RUNTIME_IMPORT_MARKER=str(marker),SFT_TEST_CODE_ROOT=str(HERE),
            SFT_TEST_ORIGIN_FIXTURE=str(self.original_path)),capture_output=True,text=True,encoding="utf-8",timeout=30)
        self.assertFalse(marker.exists(),result.stderr)
        return result

    def test_complete_stdlib_fixture_and_check_only_cli(self):
        with patch("sft_contract.load_original_train",return_value=self.original):
            contract=admit(self.config_path,self.admission_path)
        self.assertEqual(len(contract["rows"]),2)
        result=self.guard_cli()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("training_started",result.stdout)

    def test_not_authorized_refuses_before_runtime(self):
        self.admission["authorized"]=False; write(self.admission_path,self.admission)
        result=self.guard_cli(check_only=False)
        self.assertEqual(result.returncode,3)
        self.assertIn("STOP_BEFORE_RUNTIME_IMPORTS",result.stderr)

    def test_missing_user_training_request_or_main_route_before_runtime(self):
        write(self.choice,{"authorized":False,"scope":SCOPE,"route":ROUTE})
        self.admission["training_authorization_evidence"]["sha256"]=sha256(self.choice); write(self.admission_path,self.admission)
        self.assertEqual(self.guard_cli().returncode,3)

    def test_authority_does_not_fabricate_user_route_choice_or_nonresponse(self):
        original=json.loads(self.choice.read_text())
        for field in ("explicit_user_route_choice","authorization_inferred_from_nonresponse","formal_c_bce_admitted","full_training_admitted"):
            changed={**original,field:True}; write(self.choice,changed)
            self.admission["training_authorization_evidence"]["sha256"]=sha256(self.choice)
            write(self.admission_path,self.admission)
            self.assertEqual(self.guard_cli().returncode,3)

    def test_wrong_model_before_runtime(self):
        self.config["model_id"]="Qwen/Qwen3-VL-4B-Instruct"; self.refresh_config()
        result=self.guard_cli(); self.assertEqual(result.returncode,3)
        self.assertIn("fixed SFT recipe",result.stderr)

    def test_wrong_revision_and_extra_dense_head_config_stop(self):
        for key,value in (("revision","unapproved"),("dense_head",True),("modules_to_save",["lm_head"])):
            changed=copy.deepcopy(self.config); changed[key]=value
            write(self.config_path,changed); self.admission["config_sha256"]=sha256(self.config_path); write(self.admission_path,self.admission)
            self.assertEqual(self.guard_cli().returncode,3)

    def test_wrong_704_source_before_runtime(self):
        self.rows[0]["parent_sample_id"]="dev_or_confirm_not_in_704"; self.save_rows()
        self.config["train_manifest"]["sha256"]=sha256(self.manifest)
        self.admission["train_manifest_sha256"]=sha256(self.manifest); self.refresh_config()
        result=self.guard_cli(); self.assertEqual(result.returncode,3)
        self.assertIn("outside original 704",result.stderr)

    def test_source_model_and_helper_byte_change_before_runtime(self):
        for path in (self.source,self.model/"model-00001.safetensors",self.tc):
            original=path.read_bytes(); path.write_bytes(original+b"CHANGE")
            self.assertEqual(self.guard_cli().returncode,3)
            path.write_bytes(original)

    def test_bad_source_code_hash_before_runtime(self):
        self.admission["source_code_sha256"]["train_sft.py"]="f"*64; write(self.admission_path,self.admission)
        self.assertEqual(self.guard_cli().returncode,3)

    def test_no_dev_confirm_or_full_registry_swap(self):
        for mutation in (lambda r:r["records"].pop(),lambda r:r["records"][703].update(split="confirm"),
                         lambda r:r["records"][0].update(label_status="TRUE_NEGATIVE")):
            registry=copy.deepcopy(self.registry); mutation(registry)
            with self.assertRaises(AdmissionRejected): self.validate(registry,self.rows)

    def test_parent_source_group_geometry_target_join(self):
        for field,value in (("source_group","OTHER"),("source_sha256","f"*64),("window_id","UNKNOWN"),
                            ("clip_end_sec",29.0),("segments_clip_local",[[0.0,3.0]])):
            rows=copy.deepcopy(self.rows); rows[0][field]=value
            with self.assertRaises(AdmissionRejected): self.validate(self.registry,rows)

    def test_duplicate_windows_fail_but_repeated_parent_ids_work(self):
        self.assertEqual(self.rows[0]["sample_id"],self.rows[1]["sample_id"])
        self.validate(self.registry,self.rows)
        with self.assertRaises(AdmissionRejected): self.validate(self.registry,[self.rows[0],self.rows[0]])

    def test_origin_sha_and_original_parent_set_cannot_be_self_declared(self):
        registry=copy.deepcopy(self.registry); registry["origin_train_manifest_sha256"]="f"*64
        with self.assertRaises(AdmissionRejected): self.validate(registry,self.rows)
        registry=copy.deepcopy(self.registry); registry["records"][703]["parent_sample_id"]="replacement_704_parent"
        with self.assertRaises(AdmissionRejected): self.validate(registry,self.rows)
        with self.assertRaises(AdmissionRejected): load_original_train(self.original_path)

    def test_historical_cfr_and_current_metadata_must_match(self):
        for field,value in (("pts_audit_status","FAIL"),("pts_max_residual_sec",1.0),("pts_frame_interval_sec",0.0),
                            ("decoded_source_frames",1199),("source_avg_fps",25.0)):
            original=copy.deepcopy(self.original); original[0][field]=value
            with self.assertRaises(AdmissionRejected): validate_training_rows(self.registry,self.rows,original)

    def test_illegal_and_nonfinite_targets_stop(self):
        for target in ([],[[0,float("nan")]],[[0,float("inf")]],[[False,1]],[[1,1]],[[2,1]],
                       [[0,31]],[[0,2],[1,3]],[[0,1]]*6,[[0,.00001]]):
            with self.assertRaises(AdmissionRejected): answer_string(target,30)
        self.assertEqual(answer_string([[.12345,1.23456]],30),'{"segments":[[0.1235,1.2346]]}')

    def test_assistant_only_mask_left_and_right_padding(self):
        result=assistant_labels([0,0,10,11,12,20,21,0],[0,0,1,1,1,1,1,0],[0,10,11,12],[0,1,1,1])
        self.assertEqual(result["labels"],[-100,-100,-100,-100,-100,20,21,-100])
        self.assertEqual(result["tail_labels"],[-100,20,21,-100])
        self.assertEqual(result["supervised_tokens"],2)
        right=assistant_labels([10,11,20,21,0],[1,1,1,1,0],[10,11,0],[1,1,0])
        self.assertEqual(right["labels"],[-100,-100,20,21,-100])

    def test_prompt_mismatch_padding_only_and_no_answer_stop(self):
        for full,mask,prompt,pmask in (([10,20],[1,1],[11],[1]),([0],[0],[0],[0]),([10],[1],[10],[1])):
            with self.assertRaises(AdmissionRejected): assistant_labels(full,mask,prompt,pmask)

    def test_effective_accumulation_no_loss_no_step_and_fixed_counts(self):
        counter=EffectiveAccumulation(16,5)
        for _ in range(5):
            self.assertFalse(counter.record_backward(False))
            for index in range(16): self.assertEqual(counter.record_backward(True),index==15)
            counter.record_step()
        counter.finish(); self.assertEqual(counter.effective_batches,80)
        with self.assertRaises(AdmissionRejected): counter.record_backward(True)

    def test_partial_nonfinite_and_zero_effective_update_stop(self):
        counter=EffectiveAccumulation(2,1)
        with self.assertRaises(AdmissionRejected): counter.record_step()
        with self.assertRaises(AdmissionRejected): counter.record_backward(True,False)
        self.assertEqual(counter.effective_batches,0)
        counter.record_backward(True)
        with self.assertRaises(AdmissionRejected): counter.finish()
        with self.assertRaises(AdmissionRejected): counter.record_step()

    def test_lora_gradient_a_b_connection_and_initialization_boundary(self):
        import math
        fake_torch=SimpleNamespace(isfinite=lambda values:SimpleNamespace(all=lambda:all(math.isfinite(x) for x in values)),
                                   count_nonzero=lambda values:sum(x!=0 for x in values))
        names=["language_model.layers.0.self_attn.q_proj.lora_A.default.weight",
               "language_model.layers.0.self_attn.q_proj.lora_B.default.weight"]
        parameters=[SimpleNamespace(grad=[0.0]),SimpleNamespace(grad=[1.0])]
        trainable=list(zip(names,parameters))
        evidence=gradient_evidence(trainable,fake_torch,1)
        self.assertEqual((evidence["lora_A"]["nonzero"],evidence["lora_B"]["nonzero"]),(0,1))
        with self.assertRaises(AdmissionRejected): gradient_evidence(trainable,fake_torch,2)
        parameters[0].grad=[.25]
        self.assertEqual(gradient_evidence(trainable,fake_torch,2)["lora_A"]["nonzero"],1)
        for bad in (None,[0.0],[float("nan")]):
            parameters[1].grad=bad
            with self.assertRaises(AdmissionRejected): gradient_evidence(trainable,fake_torch,2)

    def test_exact_language_targets_exclude_vision_and_lm_head(self):
        names=[f"model.language_model.layers.{i}.self_attn.{p}" for i in range(2) for p in ("q_proj","k_proj","v_proj","o_proj")]
        self.assertEqual(language_target_names(names+["model.visual.q_proj","lm_head"],2),names)
        with self.assertRaises(AdmissionRejected): language_target_names(names[:-1],2)
        validate_trainable_names(["base_model.model."+names[0]+".lora_A.default.weight"])
        for name in ("base_model.model.visual.q_proj.lora_A.weight","lm_head.weight","modules_to_save.lora_A.weight"):
            with self.assertRaises(AdmissionRejected): validate_trainable_names([name])

    def test_old_r7_inclusive_clip_plan_max64_and_tail(self):
        first=legacy_clip_plan(self.rows[0]); tail=legacy_clip_plan(self.rows[1])
        self.assertEqual((first["clip_start_frame_abs"],first["clip_end_frame_abs"],first["n_sampled"]),(0,900,64))
        self.assertEqual((tail["clip_start_frame_abs"],tail["clip_end_frame_abs"]),(900,964))
        self.assertEqual(first["absolute_indices"],sorted(set(first["absolute_indices"])))

    def test_runtime_import_and_freezing_source_structure(self):
        tree=ast.parse((HERE/"train_sft.py").read_text())
        forbidden={"torch","numpy","decord","peft","transformers"}
        for node in tree.body:
            if isinstance(node,ast.Import): self.assertFalse(any(alias.name.split('.')[0] in forbidden for alias in node.names))
            if isinstance(node,ast.ImportFrom): self.assertNotIn(node.module.split('.')[0],forbidden)
        text=(HERE/"train_sft.py").read_text()
        self.assertLess(text.index("contract=admit("),text.index("return execute(contract"))
        self.assertLess(text.index("torch.cuda.init()"),text.index("import decord  #"))
        self.assertIn("parameter.requires_grad_(False)",text)
        self.assertIn("modules_to_save=None",text)
        self.assertIn("frozen_after==frozen_before",text)
        self.assertIn("is_trainable=False",text)
        self.assertNotIn("binary_cross_entropy",text)
        self.assertNotIn("DenseTimeModel",text)

    def test_actual_main_prepared_metadata_interface(self):
        root=HERE/"inputs_01"
        if not root.exists(): self.skipTest("main's independently prepared fixture not present")
        registry=json.loads((root/"r7_train_registry.json").read_text())
        rows=[json.loads(x) for x in (root/"smoke_train.jsonl").read_text().splitlines() if x.strip()]
        sources=validate_training_rows(registry,rows)
        self.assertEqual((len(registry["records"]),len(rows),len(sources)),(704,17,16))

    def test_actual_main_authority_and_false_admission_template(self):
        authority=HERE/"training_authorization_B_SMOKE.json"
        template=HERE/"smoke_admission_TEMPLATE_V2_DO_NOT_RUN.json"
        config=HERE/"smoke_config_PREPARED_NOT_ADMITTED.json"
        if not all(path.exists() for path in (authority,template,config)):
            self.skipTest("main's registered B authority/template not present")
        evidence=json.loads(authority.read_text(encoding="utf-8"))
        self.assertEqual(evidence["authority_kind"],"USER_TRAINING_REQUEST_MAIN_REGISTERED_B_ROUTE")
        self.assertEqual(evidence["user_request_quote"],"然后推理打包开训。")
        self.assertFalse(evidence["explicit_user_route_choice"])
        self.assertFalse(evidence["authorization_inferred_from_nonresponse"])
        for path in (template,HERE/"smoke_admission_TEMPLATE_DO_NOT_RUN.json"):
            if path.exists():
                with self.assertRaises(AdmissionRejected): admit(config,path)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.output and args.output.exists(): raise FileExistsError("preserve CPU SFT contract evidence")
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
    receipt={"schema":"aic_sft8b_cpu_contract_test_v1","status":"PASS_CPU_CONTRACT_ONLY" if result.wasSuccessful() else "BLOCK_CPU_CONTRACT",
        "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"output":stream.getvalue(),
        "source_sha256":{name:sha256(HERE/name) for name in ("sft_contract.py","train_sft.py","test_sft_cpu.py")},
        "runtime_imports_exercised":False,"real_processor_verified":False,"GPU_used":False,"training_started":False,
        "route_authorized_by_test":False,"quality_claim":False}
    if args.output:
        with args.output.open("x",encoding="utf-8") as target: json.dump(receipt,target,ensure_ascii=False,indent=2)
    print(json.dumps(receipt,ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__=="__main__": raise SystemExit(main())
