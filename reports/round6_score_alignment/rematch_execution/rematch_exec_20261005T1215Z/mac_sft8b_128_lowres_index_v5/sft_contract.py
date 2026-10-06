"""Stdlib-only admission and assistant-interval CE contracts; never imports torch."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re

MODEL_ID="Qwen/Qwen3-VL-8B-Instruct"
REVISION="0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
SCOPE="TEMPORAL_8B_SFT_SMOKE_NONTEST"
ROUTE="TEMPORAL_8B_INTERVAL_SFT"
BASE_PARAMS=8_767_123_696
LORA_PARAMS=15_335_424
TOTAL_PARAMS=BASE_PARAMS+LORA_PARAMS
ORIGINAL_TRAIN_SHA="ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf"
ORIGINAL_TRAIN_RELATIVE="r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs/train_temporal.jsonl"


class AdmissionRejected(ValueError): pass


def require(condition,message):
    if not condition: raise AdmissionRejected(message)


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda:source.read(8<<20),b""): digest.update(block)
    return digest.hexdigest()


def is_sha(value):
    return isinstance(value,str) and re.fullmatch("[0-9a-f]{64}",value) is not None


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def load_original_train(path=None):
    path=Path(path) if path else Path(__file__).resolve().parents[3]/ORIGINAL_TRAIN_RELATIVE
    require(path.is_file() and sha256(path)==ORIGINAL_TRAIN_SHA,"fixed original R7 704 train file identity mismatch")
    rows=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(rows)==704 and len({row.get("sample_id") for row in rows})==704 and
            all(row.get("split")=="train" for row in rows),"fixed R7 source is not the original train-only 704")
    return rows


def read_bound(spec,name):
    require(isinstance(spec,dict) and set(spec)=={"path","sha256"} and is_sha(spec["sha256"]),
            name+" requires exact path/SHA evidence")
    path=Path(spec["path"])
    require(path.is_file() and sha256(path)==spec["sha256"],name+" byte identity mismatch")
    return path


def segments_valid(segments,duration):
    require(finite(duration) and duration>0 and isinstance(segments,list) and 1<=len(segments)<=5,
            "illegal target duration/segment count; empty or UNKNOWN is not a target")
    previous=0.0
    for segment in segments:
        require(isinstance(segment,list) and len(segment)==2 and all(finite(x) for x in segment),
                "nonfinite or nonnumeric target segment")
        a,b=segment
        require(0<=a<b<=duration+1e-9 and a>=previous-1e-9,"invalid, overlapping or backward target")
        require(0<=round(a,4)<round(b,4)<=duration+1e-9,"round4 target becomes invalid")
        previous=b
    return segments


def answer_string(segments,duration):
    segments_valid(segments,duration)
    return json.dumps({"segments":[[round(a,4),round(b,4)] for a,b in segments]},separators=(",",":"))


def assistant_labels(full_ids,full_mask,prompt_ids,prompt_mask):
    """Mask all prompt/video and padding IDs, supporting either padding side."""
    require(len(full_ids)==len(full_mask) and len(prompt_ids)==len(prompt_mask) and
            all(x in (0,1) for x in full_mask+prompt_mask),"invalid token attention mask")
    active=[i for i,mask in enumerate(full_mask) if mask]
    prompt=[value for value,mask in zip(prompt_ids,prompt_mask) if mask]
    actual=[full_ids[i] for i in active]
    require(prompt and actual[:len(prompt)]==prompt,"assistant prompt/token boundary mismatch")
    require(len(actual)>len(prompt),"no supervised assistant tokens")
    first=active[len(prompt)]
    labels=[-100]*len(full_ids)
    for position in active[len(prompt):]: labels[position]=full_ids[position]
    keep=len(full_ids)-max(0,first-1)
    return {"labels":labels,"tail_labels":labels[-keep:],"logits_to_keep":keep,
            "supervised_tokens":len(actual)-len(prompt),"prompt_tokens":len(prompt),
            "first_supervised_position":first,"assistant_token_ids":actual[len(prompt):]}


def language_target_names(module_names,layer_count):
    require(type(layer_count) is int and layer_count>0,"invalid language layer count")
    pattern=re.compile(r"^model\.language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$")
    selected=[name for name in module_names if pattern.fullmatch(name)]
    expected={f"model.language_model.layers.{i}.self_attn.{projection}"
              for i in range(layer_count) for projection in ("q_proj","k_proj","v_proj","o_proj")}
    require(set(selected)==expected and len(selected)==len(expected),"language q/k/v/o target inventory mismatch")
    return selected


def validate_trainable_names(names):
    require(names and all("lora_" in name and "visual" not in name and "modules_to_save" not in name
                          and re.search(r"language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.",name)
                          for name in names),"unexpected trainable base/vision/head/LoRA target")


class EffectiveAccumulation:
    """Only successful supervised backward calls count; no partial update."""
    def __init__(self,grad_accum,updates):
        require(type(grad_accum) is int and grad_accum>0 and type(updates) is int and updates>0,
                "positive explicit update/accumulation counts required")
        self.grad_accum,self.updates=grad_accum,updates
        self.pending=self.completed=self.effective_batches=0
    def record_backward(self,has_loss,loss_finite=True):
        if not has_loss: return False
        require(loss_finite,"nonfinite loss cannot count as an effective batch")
        require(self.completed<self.updates,"extra batch after fixed updates")
        self.pending+=1; self.effective_batches+=1
        return self.pending==self.grad_accum
    def record_step(self):
        require(self.pending==self.grad_accum,"partial or empty accumulation cannot step")
        self.completed+=1; self.pending=0
    def finish(self):
        require(self.completed==self.updates and self.pending==0 and
                self.effective_batches==self.updates*self.grad_accum,"incomplete fixed effective update count")


def legacy_clip_plan(row):
    fps=row["fps_num"]/row["fps_den"]; total=row["n_frames"]
    sf=int(math.ceil(max(0.0,row["clip_start_sec"])*fps))
    ef=int(math.floor(row["clip_end_sec"]*fps))
    sf=max(0,min(sf,total-1)); ef=max(sf+1,min(ef,total-1))
    count=ef-sf+1; samples=min(64,count)
    indices=[0] if samples==1 else [int(round(i*((count-1)/(samples-1)))) for i in range(samples)]
    if samples>1: indices[-1]=count-1
    return {"source_total_frames":total,"source_fps":fps,"clip_start_frame_abs":sf,
            "clip_end_frame_abs":ef,"n_frames_in_clip":count,"n_sampled":samples,
            "clip_local_indices":indices,"absolute_indices":[sf+i for i in indices]}


FIXED={"schema":"aic_temporal_sft8b_config_v1","model_id":MODEL_ID,"revision":REVISION,
       "max_frames":64,"max_pixels":131072,"window_seconds":30,"precision":"bf16",
       "attn_implementation":"sdpa","lora_rank":16,"lora_alpha":32,"lora_dropout":0.05,
       "modules_to_save":None,"gradient_checkpointing_use_reentrant":False,
       "loss":"ASSISTANT_INTERVAL_JSON_CE","optimizer":"AdamW","weight_decay":0.0,"grad_clip_norm":1.0,
       "adamw_betas":[0.9,0.999],"adamw_eps":1e-8}
EXTRA={"model_dir","model_receipt","train_manifest","r7_train_registry","temporal_common","r7_core",
       "out_dir","updates","grad_accum","lr","seed","max_sequence_length","max_wall_seconds"}


def verify_model_receipt(model_dir,receipt):
    controller="completed" in receipt
    require((receipt.get("repo") if controller else receipt.get("repo_id"))==MODEL_ID and
            receipt.get("revision")==REVISION,"wrong fixed 8B model receipt")
    if controller:
        require(receipt.get("status")=="COMPLETE_HASH_VERIFIED" and
                Path(receipt.get("model_path","")).resolve()==model_dir.resolve(),"8B receipt incomplete/path mismatch")
    entries=receipt.get("completed") if controller else receipt.get("files")
    require(isinstance(entries,list) and entries,"8B model receipt files missing")
    declared=set()
    for entry in entries:
        name=entry.get("name") if controller else entry.get("path")
        require(isinstance(name,str) and Path(name).name==name and name not in declared,"unsafe/duplicate model file")
        declared.add(name); source=model_dir/name
        size=entry.get("bytes") if controller else entry.get("size_bytes")
        require(type(size) is int and size>=0 and source.is_file() and source.stat().st_size==size and
                is_sha(entry.get("sha256")) and sha256(source)==entry["sha256"],"fixed model file byte mismatch")
    required={"config.json","tokenizer.json","tokenizer_config.json","preprocessor_config.json",
              "video_preprocessor_config.json","model.safetensors.index.json"}
    required.update(p.name for p in model_dir.iterdir() if p.is_file() and p.suffix in
                    (".json",".safetensors",".jinja",".txt",".model"))
    require(required<=declared and any(name.endswith(".safetensors") for name in declared),"unbound model/config/tokenizer file")
    architecture=json.loads((model_dir/"config.json").read_text())
    require(architecture.get("model_type")=="qwen3_vl" and architecture.get("text_config",{}).get("hidden_size")==4096,
            "model architecture is not pinned Qwen3-VL-8B")
    index=json.loads((model_dir/"model.safetensors.index.json").read_text())
    require(isinstance(index.get("weight_map"),dict) and index["weight_map"] and
            set(index["weight_map"].values())<=declared,"unbound model shard index")


def admit(config_path,admission_path,here=None):
    """All authority, code, model and source byte checks precede runtime imports."""
    here=Path(here or Path(__file__).parent).resolve()
    admission=json.loads(Path(admission_path).read_text(encoding="utf-8"))
    require(admission.get("schema")=="aic_temporal_sft8b_admission_v1" and admission.get("scope")==SCOPE and
            admission.get("authorized") is True and admission.get("registered_route")==ROUTE and
            admission.get("training_authorized_by_user") is True and
            admission.get("formal_c_bce_admitted") is False,"SFT smoke route not registered/authorized; C STOP remains")
    route_path=read_bound(admission.get("training_authorization_evidence"),"user training request and main B registration")
    choice=json.loads(route_path.read_text(encoding="utf-8"))
    require(choice.get("authorized") is True and choice.get("route")==ROUTE and choice.get("scope")==SCOPE and
            choice.get("authority_kind")=="USER_TRAINING_REQUEST_MAIN_REGISTERED_B_ROUTE" and
            choice.get("user_request_quote")=="然后推理打包开训。" and choice.get("explicit_user_route_choice") is False and
            choice.get("authorization_inferred_from_nonresponse") is False and choice.get("formal_c_bce_admitted") is False and
            choice.get("full_training_admitted") is False,
            "broader user training request/main B protocol evidence does not authorize this smoke")
    require(admission.get("config_sha256")==sha256(config_path),"SFT config not bound to admission")
    config=json.loads(Path(config_path).read_text(encoding="utf-8"))
    require(set(config)==set(FIXED)|EXTRA,"unknown/missing SFT recipe field")
    for key,value in FIXED.items():
        require(config[key]==value and type(config[key]) is type(value),"fixed SFT recipe changed: "+key)
    for key in ("updates","grad_accum","seed","max_sequence_length"):
        require(type(config[key]) is int and config[key]>0,"invalid explicit SFT "+key)
    for key in ("lr","max_wall_seconds"):
        require(finite(config[key]) and config[key]>0,"invalid explicit SFT "+key)
    require(all(admission.get(key) is True for key in ("resource_preflight_pass","shared_gpu_queue_approved",
                "disk_peak_within_80gib","budget_runner_required")),"SFT resources/queue not registered")
    code=admission.get("source_code_sha256")
    require(isinstance(code,dict) and set(code)=={"sft_contract.py","train_sft.py"} and
            all(is_sha(digest) and sha256(here/name)==digest for name,digest in code.items()),"SFT source code identity mismatch")
    bound={name:read_bound(config[name],name) for name in
           ("model_receipt","train_manifest","r7_train_registry","temporal_common","r7_core")}
    for key in ("model_receipt","train_manifest","r7_train_registry"):
        require(admission.get(key+"_sha256")==config[key]["sha256"],"admission does not bind "+key)
    output=Path(config["out_dir"]).resolve()
    require(here in output.parents and (not output.exists() or not any(output.iterdir())),"unsafe/nonempty SFT smoke output")
    # Verify borrowed helpers before importing them, including fixed prompt/IO.
    common=bound["temporal_common"].read_text(encoding="utf-8")
    require("MAX_FRAMES = 64" in common and "MAX_PIXELS = 128 * 32 * 32" in common,
            "R7 temporal preprocessing identity changed")
    model_dir=Path(config["model_dir"])
    require(model_dir.is_dir(),"8B model directory missing")
    verify_model_receipt(model_dir,json.loads(bound["model_receipt"].read_text(encoding="utf-8")))
    registry=json.loads(bound["r7_train_registry"].read_text(encoding="utf-8"))
    rows=[json.loads(line) for line in bound["train_manifest"].read_text(encoding="utf-8").splitlines() if line.strip()]
    original=load_original_train(bound["r7_core"].parent.parent/"inputs/train_temporal.jsonl")
    sources=validate_training_rows(registry,rows,original)
    for source,digest in sources.items():
        require(Path(source).is_file() and sha256(source)==digest,"training source bytes changed before runtime imports")
    return {"config":config,"admission":admission,"rows":rows,"sources":sources,"bound":bound,
            "config_sha256":sha256(config_path),"admission_sha256":sha256(admission_path),
            "origin_train_manifest_sha256":registry["origin_train_manifest_sha256"]}


def validate_training_rows(registry,rows,original_rows=None):
    """Train-only metadata/target join, independent of machine-local paths."""
    parents=registry.get("records")
    require(registry.get("schema")=="aic_sft8b_r7_train_registry_v1" and registry.get("expected_parent_count")==704
            and registry.get("origin_train_manifest_sha256")==ORIGINAL_TRAIN_SHA and isinstance(parents,list) and len(parents)==704,
            "not the frozen original 704 train parent registry")
    lookup={r.get("parent_sample_id"):r for r in parents}
    require(len(lookup)==704 and None not in lookup and all(isinstance(key,str) and key for key in lookup),"duplicate/missing 704 parent ID")
    original={r["sample_id"]:r for r in (load_original_train() if original_rows is None else original_rows)}
    require(set(lookup)==set(original) and len(original)==704,"registry replaced original 704 parent set")
    old_identity=("video_id","source_group","youtube_id","source_path","clip_start_sec","clip_end_sec")
    for parent in parents:
        old=original[parent["parent_sample_id"]]
        require(all(parent.get(key)==old.get(key) for key in old_identity),
                "registry parent differs from fixed original train source/window")
        require(parent.get("split")=="train" and parent.get("label_status")=="WEAK_TEACHER" and
                parent.get("pts_audit_status")=="PASS","dev/confirm/unapproved PTS parent forbidden")
        old_fps=old.get("source_avg_fps")
        require(old.get("split")=="train" and old.get("label_status")=="WEAK_TEACHER" and old.get("pts_audit_status")=="PASS" and
                finite(old_fps) and old_fps>0 and finite(old.get("pts_frame_interval_sec")) and old["pts_frame_interval_sec"]>0 and
                finite(old.get("pts_max_residual_sec")) and 0<=old["pts_max_residual_sec"]<=1/old_fps+1e-6,
                "fixed R7 parent lacks its historical approximate CFR evidence")
        require(parent.get("n_frames")==old.get("decoded_source_frames") and
                type(parent.get("fps_num")) is int and parent["fps_num"]>0 and
                type(parent.get("fps_den")) is int and parent["fps_den"]>0 and
                abs(parent["fps_num"]/parent["fps_den"]-old_fps)<=max(1e-6,old_fps*1e-6),
                "new source count/FPS differs from original R7 metadata; old byte equality is unproven")
    require(len({r.get("youtube_id") for r in parents})==602,"frozen 602 original R7 train source groups changed")
    require(rows and len({r.get("window_id") for r in rows})==len(rows),"empty/duplicate SFT window manifest")
    identity=("video_id","youtube_id","source_group","source_path","source_sha256","n_frames","fps_num","fps_den","width","height",
              "source_bytes","source_mtime_ns")
    sources={}
    for row in rows:
        require(row.get("parent_sample_id") in lookup,"SFT sample outside original 704 train")
        parent=lookup[row["parent_sample_id"]]
        require(row.get("sample_id")==row["parent_sample_id"] and all(row.get(key)==parent.get(key) for key in identity),
                "SFT window parent/source identity mismatch")
        require(row.get("split")=="train" and row.get("label_status")=="WEAK_TEACHER" and row.get("pts_audit_status")=="PASS",
                "SFT train-only weak/CFR status missing")
        require(all(type(row.get(key)) is int and row[key]>0 for key in ("n_frames","fps_num","fps_den","width","height"))
                and row["n_frames"]>=2 and is_sha(row.get("source_sha256")),"invalid source metadata/byte identity")
        start,end=row.get("clip_start_sec"),row.get("clip_end_sec")
        require(finite(start) and finite(end) and 0<=start<end<=row["n_frames"]*row["fps_den"]/row["fps_num"]+1e-6
                and end-start<=30+1e-9,"SFT window violates registered CFR 30s source contract")
        require(parent["clip_start_sec"]<=start<end<=parent["clip_end_sec"]+1e-9,"SFT window exceeds original parent clip")
        windows=parent.get("registered_windows",[])
        registered=[w for w in windows if w.get("window_id")==row["window_id"]]
        require(len(registered)==1,"window not uniquely registered under its 704 parent")
        window=registered[0]
        require(window.get("parent_sample_id",row["parent_sample_id"])==row["parent_sample_id"] and
                all(window.get(key)==row.get(key) for key in ("clip_start_sec","clip_end_sec","segments_clip_local")),
                "registered window geometry/canonical target mismatch")
        segments_valid(row.get("segments_clip_local"),end-start)
        require(row["source_path"] not in sources or sources[row["source_path"]]==row["source_sha256"],"contradictory source byte bindings")
        sources[row["source_path"]]=row["source_sha256"]
    return sources


def verify_live_gpu_reservation():
    require(os.name=="posix","SFT execution requires main's Linux shared GPU wrapper")
    path=Path("/home/inspur/aic_video_work/improvement_round1/active_gpu_job.json")
    require(path.is_file(),"shared GPU reservation missing")
    active=json.loads(path.read_text()); ancestors=set(); pid=os.getpid()
    for _ in range(32):
        ancestors.add(pid)
        if pid<=1: break
        pid=int(Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()[1])
    require(active.get("child_pid") in ancestors and active.get("runner_pid") in ancestors,
            "SFT reservation belongs to another process")
