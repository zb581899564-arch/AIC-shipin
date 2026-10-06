"""New full-stage fork: preserve the original R7 millisecond endpoint semantics."""
from sft_contract import (require,finite,is_sha,segments_valid,load_original_train,ORIGINAL_TRAIN_SHA)


def rounded_source_end_ok(end,row):
    exact=row["n_frames"]*row["fps_den"]/row["fps_num"]
    if end<=exact+1e-6:
        return True
    return abs(end-round(exact,3))<=1e-9 and 0<end-exact<=0.000500001


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
        require(finite(start) and finite(end) and 0<=start<end and rounded_source_end_ok(end,row)
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

