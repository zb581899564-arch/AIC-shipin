"""Single fixed CPU local-action readout experiment; accepted caches only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback

import numpy as np


def features(slot, native_count, kind):
    selected = slot["selected_ordinals"]
    runs = sum(i == 0 or value != selected[i-1] + 1 for i, value in enumerate(selected))
    shape = [len(selected) / native_count, runs / 6, len(slot["ids"]) / 512]
    if kind == "shape":
        return np.asarray(shape, dtype=np.float64)
    part = slot["real"] if kind == "content" else slot["permuted"]
    vector = np.asarray(part["feature"] + shape, dtype=np.float64)
    if vector.shape != (131,) or not np.isfinite(vector).all():
        raise ValueError("Exact finite cached128+3 feature required")
    return vector


def fit_head(records, kind, ridge=.01):
    if ridge != .01:
        raise ValueError("No ridge tuning allowed")
    dimension = 3 if kind == "shape" else 131
    rows = np.vstack([r["features"][kind] for r in records])
    scale = rows.std(axis=0)
    scale = np.where(scale > 1e-8, scale, 1)
    sources = sorted({r["sid"] for r in records})
    window_counts = {s: sum(r["sid"] == s for r in records) for s in sources}
    gram, rhs = np.eye(dimension)*ridge, np.zeros(dimension)
    pair_count = 0
    for record in records:
        values, target = record["features"][kind]/scale, record["targets"]
        pairs = [(i,j) for i in range(len(target)) for j in range(i+1, len(target))]
        if not pairs:
            continue
        weight = 1/(len(sources)*window_counts[record["sid"]]*len(pairs))
        for i,j in pairs:
            diff = values[i]-values[j]
            gram += weight*np.outer(diff,diff)
            rhs += weight*diff*(target[i]-target[j])
            pair_count += 1
    beta = np.linalg.solve(gram,rhs)
    residual = float(np.linalg.norm(gram@beta-rhs))
    if not np.isfinite(beta).all() or residual > 1e-8*(1+float(np.linalg.norm(rhs))):
        raise ValueError("Closed-form residual failed")
    return dict(kind=kind,weights=(beta/scale).tolist(),parameters=dimension,ridge=ridge,
                residual=residual,training_pairs=pair_count,train_sources=sources,solves=1,
                intercept="unnecessary_same_window_pair_differences")


def run(root):
    root=Path(root).resolve(strict=True)
    started=time.monotonic()
    spec=importlib.util.spec_from_file_location("prior_new_diagnostic",root.parent/"diagnostic.py")
    api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    reg=json.loads((root/"registration02.json").read_text())
    workspace=root.parent.parent
    protocol=api.checked_json(reg["protocol_ref"],workspace)
    diag=api.checked_json(reg["prior_new_diagnostic_ref"],workspace)
    if diag["status"]!="COMPLETE_NEW_EXTERNAL_ONLY_DIAGNOSTIC":
        raise ValueError("First new diagnostic must have completed naturally")
    sys.path.insert(0,reg["prior_code_root"])
    from improvement.native_preference_v1.inputs import NativeInputStore
    collections={scope:api.checked_json(reg[scope+"_collection_ref"],workspace) for scope in ["train","check"]}
    manifest=api.checked_json(collections["check"]["asset_manifest_ref"],workspace)
    if collections["train"]["asset_manifest_ref"]!=collections["check"]["asset_manifest_ref"]:
        raise ValueError("Train/check accepted source manifest mismatch")
    all_records,source_data={},{}
    sha_sets={}
    for scope, expected_n, expected_w in [("train",25,144),("check",8,43)]:
        complete=collections[scope]
        if (complete["scope"],complete["source_count"],complete["window_count"],complete["labels_read"])!=(scope,expected_n,expected_w,False):
            raise ValueError("Original accepted source/window denominator mismatch")
        store=NativeInputStore(manifest,scope)
        if set(complete["sources"])!=set(store.source_ids) or set(complete["window_refs"])!=set(store.case_ids):
            raise ValueError("Missing window/reference")
        sha_sets[scope]={v["source_sha256"] for v in complete["sources"].values()}
        records=[]; source_data[scope]={}
        for sid in sorted(store.source_ids):
            human=store.source_supervision(sid)
            n=len(human["clock"]["normalized_exact_pts"])
            if not all(len(m)==n and all(m) for m in human["known_masks"]):
                raise ValueError("UNKNOWN membership must not enter supervised target")
            labels=np.zeros((n,len(human["raters"])),dtype=bool)
            for r,truth in enumerate(human["raters"]):labels[sorted(truth),r]=True
            greedy=set(complete["sources"][sid]["candidates"][0]["selected_ordinals"])
            source_data[scope][sid]=dict(labels=labels,greedy=greedy,baseline=human["baseline"])
            for uid in complete["sources"][sid]["window_ids"]:
                row=api.checked_json(complete["window_refs"][uid],workspace)
                if row["status"]!="ACCEPTED" or row["source_sha256"]!=human["source_sha256"] or row["uid"]!=uid:
                    raise ValueError("Cached action identity changed")
                if row["input_signature"]!=store.requests[uid]["input_signature"]:
                    raise ValueError("Accepted input mismatch")
                plan=store.requests[uid]["plan"]
                from fractions import Fraction
                lo,hi=[Fraction(plan[k]) for k in ["window_start_exact","window_end_exact"]]
                domain={i for i,p in enumerate(human["clock"]["normalized_exact_pts"]) if lo<=Fraction(p)<hi}
                if not domain:raise ValueError("Measured nonempty native window required")
                unique=[];seen=set()
                for slot in row["slots"]:
                    chosen=tuple(slot["selected_ordinals"])
                    if slot["status"]!="ACCEPTED" or list(chosen)!=sorted(set(chosen)) or not set(chosen)<=domain:
                        raise ValueError("Failed/out-of-window action cannot be a successful empty")
                    if chosen not in seen:unique.append(slot);seen.add(chosen)
                outside=greedy-domain
                target=np.asarray([api.utility(outside|set(s["selected_ordinals"]),labels) for s in unique])
                records.append(dict(sid=sid,uid=uid,actions=[set(s["selected_ordinals"]) for s in unique],
                    slots=[s["slot"] for s in unique],targets=target,
                    features={kind:np.vstack([features(s,len(domain),kind) for s in unique])
                              for kind in protocol["feature_arms"]}))
        all_records[scope]=records
    if len(sha_sets["train"])!=25 or len(sha_sets["check"])!=8 or sha_sets["train"]&sha_sets["check"]:
        raise ValueError("Source byte train/check overlap")
    heads={kind:fit_head(all_records["train"],kind) for kind in protocol["feature_arms"]}
    api.save_new(root/"heads02.json",heads)
    reloaded=json.loads((root/"heads02.json").read_text())
    evaluations={}
    for kind,head in reloaded.items():
        chosen={s:set() for s in source_data["check"]};rank={s:[] for s in chosen};decisions=[]
        for record in all_records["check"]:
            values=record["features"][kind]@np.asarray(head["weights"])
            if not np.array_equal(values,record["features"][kind]@np.asarray(heads[kind]["weights"])):
                raise ValueError("Saved/reloaded head changed predictions")
            best=int(np.argmax(values));sid=record["sid"]
            chosen[sid].update(record["actions"][best])
            for i in range(len(values)):
                for j in range(i+1,len(values)):
                    delta=float(record["targets"][i]-record["targets"][j])
                    if delta==0:continue
                    gap=float(values[i]-values[j]);rank[sid].append(.5 if gap==0 else float(gap*delta>0))
            decisions.append(dict(uid=record["uid"],slot=record["slots"][best],score=float(values[best])))
        rows=[]
        for sid,data in source_data["check"].items():
            selected,greedy=chosen[sid],data["greedy"]
            rows.append(dict(source_id=sid,f1=api.utility(selected,data["labels"]),
                TIME_f1=api.utility(greedy,data["labels"]),baseline_f1=api.utility(data["baseline"],data["labels"]),
                local_pair_rank=sum(rank[sid])/len(rank[sid]) if rank[sid] else None,
                selected=len(selected),TIME_selected=len(greedy),added=len(selected-greedy),deleted=len(greedy-selected),
                false_empty=not selected and bool(greedy) and bool(data["labels"].any())))
        if any(r["local_pair_rank"] is None for r in rows):raise ValueError("Incomplete local ranking denominator")
        evaluations[kind]=dict(macro_f1=sum(r["f1"] for r in rows)/8,
            local_pair_rank=sum(r["local_pair_rank"] for r in rows)/8,
            sources_improved=sum(r["f1"]>r["TIME_f1"] for r in rows),
            sources_worsened=sum(r["f1"]<r["TIME_f1"] for r in rows),
            added=sum(r["added"] for r in rows),deleted=sum(r["deleted"] for r in rows),
            selected=sum(r["selected"] for r in rows),false_empty_sources=[r["source_id"] for r in rows if r["false_empty"]],
            per_source=rows)
        api.save_new(root/(kind+"_external_decisions02.json"),dict(decisions=decisions,
            selected_ordinals={s:sorted(v) for s,v in chosen.items()},historical_exposed=True,official_data=False))
    content=evaluations["content"]
    reasons=[]
    for kind in ["shape","permuted"]:
        for metric in ["macro_f1","local_pair_rank"]:
            if not content[metric]>evaluations[kind][metric]:reasons.append("CONTENT_NOT_BETTER_THAN_"+kind.upper()+"_"+metric.upper())
    if content["false_empty_sources"]:reasons.append("NEW_FALSE_EMPTY_SOURCE")
    if not content["macro_f1"]>diag["macro"]["actual_TIME_f1_adopted"]:
        reasons.append("NO_ACTUAL_COMPLETE_SOURCE_GAIN_OVER_TIME")
    if time.monotonic()-started>protocol["cpu_seconds_budget"]:raise TimeoutError("CPU budget expired")
    result=dict(status="STOP_LOCAL_CONTENT_MECHANISM" if reasons else "ELIGIBLE_FOR_NEW_EXECUTION_REVIEW_NOT_PRODUCTION",
        stop_reasons=reasons,metrics={k:{n:v for n,v in row.items() if n!="per_source"} for k,row in evaluations.items()},
        detailed= evaluations,original_TIME_f1_adopted=diag["macro"]["actual_TIME_f1_adopted"],
        original_protected_proxy_f1_adopted=diag["macro"]["protected_proxy_f1_adopted"],
        linear_solves=3,new_model_calls=0,new_backbone_updates=0,new_media_decode=0,
        head_save_reload_exact=True,seconds=time.monotonic()-started,historical_exposed=True,
        official_joint_score="UNKNOWN",automatic_production=False,automatic_submission=False)
    api.save_new(root/"completion02.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!="detailed"}))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-root",required=True);a=p.parse_args()
    try:run(a.run_root)
    except BaseException:
        root=Path(a.run_root)
        with (root/"failure02.json").open("x") as f:json.dump(dict(status="FAILED_ENGINEERING_NOT_EMPTY",traceback=traceback.format_exc()),f,indent=2)
        raise
