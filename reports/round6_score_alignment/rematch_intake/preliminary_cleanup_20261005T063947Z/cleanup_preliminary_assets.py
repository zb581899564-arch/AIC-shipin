import os, json, pathlib, hashlib, shutil, subprocess, zipfile, zlib, time, stat
from datetime import datetime, timezone
os.umask(0o077)
RUN_ID = "preliminary_cleanup_20261005T063947Z"
WORK = pathlib.Path("/home/inspur/aic_video_work")
DATA = pathlib.Path("/home/inspur/aic_video_data")
OUT = WORK / "round6_score_alignment/rematch_intake" / RUN_ID
MODEL = WORK / "orarl_round1/model/Video-ORA-4B"
ENV = WORK / "orarl_round1/env/orarl_hf"
OLD_ZIP = DATA / "test/基于视频大模型的通用视频高光剪辑.zip"
OUT.mkdir(parents=True, exist_ok=True)
record = {"run_id": RUN_ID, "state": "PRECHECK", "authority": "User explicitly requested deleting unused preliminary assets to free space on 2026-10-05.", "removed": [], "scope": "Five abandoned OraRL weight shards, its isolated environment, and one CRC-confirmed duplicate preliminary ZIP. Retain actual train/test media, labels, all reports/source/configs/adapters/submissions, current Qwen model and environments, and rematch ZIP."}
def save():
    record["updated_utc"] = datetime.now(timezone.utc).isoformat()
    tmp = OUT / "cleanup_result.json.tmp"
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    os.replace(tmp, OUT / "cleanup_result.json")
def digest(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(8*1024*1024), b""): h.update(b)
    return h.hexdigest()
def safe(p, exact):
    assert p == exact and p.is_absolute()
    assert p.resolve() == p, "resolved path differs: " + str(p)
    for a in [p] + list(p.parents):
        if a == pathlib.Path("/"): break
        assert not a.is_symlink(), "symlink ancestor: " + str(a)
def snapshot(paths):
    rows = {}
    for base in paths:
        for folder, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if not pathlib.Path(folder,d).is_symlink()]
            for name in files:
                p = pathlib.Path(folder,name)
                if p.is_symlink(): continue
                s = p.stat()
                rows[str(p)] = [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]
    return rows
def check_processes(targets):
    conflicts = []
    for p in pathlib.Path("/proc").iterdir():
        if not p.name.isdecimal(): continue
        try:
            if p.stat().st_uid != os.getuid(): continue
            text = (p/"cmdline").read_bytes().replace(bytes([0]),b" ").decode(errors="replace")
            text += (p/"maps").read_text(errors="replace")
            for n in ["exe","cwd"]:
                try: text += os.readlink(p/n)
                except OSError: pass
            for fd in (p/"fd").iterdir():
                try: text += os.readlink(fd)
                except OSError: pass
            if any(str(t) in text for t in targets): conflicts.append(int(p.name))
        except (OSError, PermissionError): pass
    assert not conflicts, "target assets in use by pids: " + repr(conflicts)
def qwen_probe():
    script = 'import json,sys,torch,transformers,peft,cv2,decord,qwen_vl_utils;print(json.dumps({"executable":sys.executable,"torch":torch.__version__,"transformers":transformers.__version__,"peft":peft.__version__,"opencv":cv2.__version__,"decord":decord.__version__,"cpu_imports_ok":True}))'
    p = subprocess.run([str(WORK/"env/qwen3vl_isolated_20260910/bin/python"),"-B","-c",script],capture_output=True,text=True,timeout=40)
    assert p.returncode == 0, "retained Qwen environment failed CPU import"
    return json.loads(p.stdout)
try:
    assert subprocess.check_output(["hostname"],text=True).strip() == "inspur-NP5570M5"
    assert not (WORK/"improvement_round1/active_gpu_job.json").exists(), "active project job"
    gpu = subprocess.check_output(["nvidia-smi","--query-compute-apps=pid,process_name,used_memory","--format=csv,noheader"],text=True).strip()
    assert not gpu, "GPU compute job started; defer cleanup"
    record["gpu_compute_processes_before"] = []
    record["qwen_runtime_before"] = qwen_probe()
    safe(ENV, WORK/"orarl_round1/env/orarl_hf")
    safe(MODEL, WORK/"orarl_round1/model/Video-ORA-4B")
    safe(OLD_ZIP, DATA/"test/基于视频大模型的通用视频高光剪辑.zip")
    assert (ENV/"pyvenv.cfg").is_file()
    assert (WORK/"orarl_round1/evidence/env_pip_freeze.txt").is_file()
    check_processes([MODEL,ENV,OLD_ZIP])
    manifest = json.loads((WORK/"orarl_round1/evidence/weight_sha256_manifest.json").read_text())
    assert manifest["revision"] == "01850297d5ab2adaaf130f700ed7cec52993d956"
    shard_rows = [m for m in manifest["files"] if m["file"].endswith(".safetensors")]
    assert len(shard_rows) == 5
    deletions = []
    for row in shard_rows:
        p = MODEL/row["file"]
        safe(p, MODEL/row["file"])
        s = p.stat()
        assert s.st_nlink == 1 and s.st_size == row["local_size"]
        h = digest(p)
        assert h == row["local_sha256"], "weight identity mismatch"
        deletions.append({"path":str(p),"bytes":s.st_size,"allocated_bytes":s.st_blocks*512,"sha256":h,"identity":[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns],"reason":"Stopped OraRL spatial/tracking route; downloadable published revision preserved in recovery evidence."})
    record["weight_revision"] = manifest["revision"]
    record["weight_restore_repository"] = "OraRL/Video-ORA-4B"
    record["weight_restore_manifest"] = str(WORK/"orarl_round1/evidence/weight_sha256_manifest.json")
    env_rows = []
    for folder,dirs,files in os.walk(ENV,followlinks=False):
        for name in dirs+files:
            p = pathlib.Path(folder,name); s = p.lstat()
            row = {"path":p.relative_to(ENV).as_posix(),"bytes":s.st_size,"mode":s.st_mode,"mtime_ns":s.st_mtime_ns,"allocated_bytes":s.st_blocks*512}
            if p.is_symlink():
                row["link_target"] = os.readlink(p)
                assert p.resolve().is_relative_to(ENV), "environment symlink points outside target"
            env_rows.append(row)
    (OUT/"removed_environment_inventory.json").write_text(json.dumps({"root":str(ENV),"files":env_rows,"pip_freeze_retained":str(WORK/"orarl_round1/evidence/env_pip_freeze.txt"),"pyvenv_cfg":(ENV/"pyvenv.cfg").read_text()},ensure_ascii=False,indent=2))
    env_allocated = int(subprocess.check_output(["du","-sx","--block-size=1",str(ENV)],text=True).split("\t",1)[0])
    record["environment_allocated_bytes_before"] = env_allocated
    zipstat = OLD_ZIP.stat()
    zip_members=[]; skipped=0; checked=0
    with zipfile.ZipFile(OLD_ZIP) as z:
        for m in z.infolist():
            name=m.filename
            if not (m.flag_bits&0x800):
                try: name=name.encode("cp437").decode("utf-8")
                except (UnicodeEncodeError,UnicodeDecodeError): pass
            zip_members.append({"name":name,"bytes":m.file_size,"crc32":format(m.CRC,"08x"),"is_dir":m.is_dir()})
            if m.is_dir(): continue
            pp=pathlib.PurePosixPath(name)
            if pp.parts[0]=="__MACOSX" or pp.name==".DS_Store": skipped+=1;continue
            assert not name.startswith("/") and ".." not in pp.parts
            p=(OLD_ZIP.parent/name).resolve()
            assert p.is_relative_to(OLD_ZIP.parent.resolve()) and p.is_file() and not p.is_symlink()
            assert p.stat().st_size==m.file_size
            crc=0
            with p.open("rb") as f:
                for b in iter(lambda:f.read(4*1024*1024),b""):crc=zlib.crc32(b,crc)
            assert (crc&0xffffffff)==m.CRC, "unpacked duplicate CRC mismatch"
            checked+=1
    assert checked==348
    zhash=digest(OLD_ZIP)
    (OUT/"removed_duplicate_zip_inventory.json").write_text(json.dumps({"archive":str(OLD_ZIP),"sha256":zhash,"substantive_files_checked":checked,"all_substantive_crc_match":True,"skipped_macos_metadata":skipped,"members":zip_members,"contents_not_semantically_viewed":True},ensure_ascii=False,indent=2))
    deletions.append({"path":str(OLD_ZIP),"bytes":zipstat.st_size,"allocated_bytes":zipstat.st_blocks*512,"sha256":zhash,"identity":[zipstat.st_dev,zipstat.st_ino,zipstat.st_size,zipstat.st_mtime_ns],"reason":"348 substantive unpacked files match archive sizes and CRC; retain extracted media/index. Mac metadata excluded."})
    protected=[DATA/"videos",DATA/"labels",DATA/"test/基于视频大模型的通用视频高光剪辑",WORK/"models",WORK/"env",WORK/"temporal_round5",WORK/"training_round2_20260910",WORK/"runs",WORK/"orarl_round1/src",WORK/"orarl_round1/evidence",WORK/"orarl_round1/scripts",WORK/"orarl_round1/outputs",WORK/"orarl_round1/logs"]
    before=snapshot(protected)
    report_hash_before={str(p):digest(p) for d in ["orarl_round1","orarl_round2","orarl_round3","orarl_round4"] for p in [WORK/d/"REPORT.md"] if p.exists()}
    (OUT/"protected_assets_before.json").write_text(json.dumps({"file_metadata":before,"report_sha256":report_hash_before},ensure_ascii=False))
    record["deletion_plan"] = deletions
    record["protected_file_count"] = len(before)
    record["free_bytes_before"] = shutil.disk_usage(WORK).free
    record["state"]="READY_TO_DELETE"
    save()
    print(json.dumps({"state":"READY_TO_DELETE","delete_weight_files":5,"delete_environment":str(ENV),"delete_duplicate_zip":str(OLD_ZIP),"expected_allocated_bytes":sum(x["allocated_bytes"] for x in deletions)+env_allocated,"protected_file_count":len(before)},ensure_ascii=False),flush=True)
    check_processes([MODEL,ENV,OLD_ZIP])
    for row in deletions:
        p=pathlib.Path(row["path"]);s=p.stat()
        assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]==row["identity"],"target changed after verification"
    for row in deletions[:5]:
        pathlib.Path(row["path"]).unlink()
        record["removed"].append(dict(row,removed_utc=datetime.now(timezone.utc).isoformat()))
        save()
    safe(ENV, WORK/"orarl_round1/env/orarl_hf")
    assert getattr(shutil.rmtree,"avoids_symlink_attacks",False), "fd-based safe directory removal not available"
    shutil.rmtree(ENV)
    record["removed"].append({"path":str(ENV),"allocated_bytes":env_allocated,"reason":"Isolated unused OraRL environment. Freeze and full inventory retained.","removed_utc":datetime.now(timezone.utc).isoformat()})
    save()
    OLD_ZIP.unlink()
    record["removed"].append(dict(deletions[-1],removed_utc=datetime.now(timezone.utc).isoformat()))
    save()
    after=snapshot(protected)
    assert before==after, "protected file metadata changed"
    assert report_hash_before=={p:digest(pathlib.Path(p)) for p in report_hash_before}, "historical report hash changed"
    assert not ENV.exists() and not OLD_ZIP.exists() and all(not pathlib.Path(r["path"]).exists() for r in deletions)
    record["qwen_runtime_after"]=qwen_probe()
    record["free_bytes_after"]=shutil.disk_usage(WORK).free
    record["removed_allocated_bytes"]=sum(row["allocated_bytes"] for row in record["removed"])
    record["filesystem_free_change_bytes"]=record["free_bytes_after"]-record["free_bytes_before"]
    record["protected_metadata_unchanged"]=True
    record["historical_reports_sha256_unchanged"]=True
    record["state"]="CLEANUP_COMPLETE_VERIFIED"
    record["gpu_hours_used"]=0
    record["model_outputs_generated"]=0
    save()
    print(json.dumps({"state":record["state"],"removed_allocated_bytes":record["removed_allocated_bytes"],"removed_gib":round(record["removed_allocated_bytes"]/1024**3,4),"free_gib":round(record["free_bytes_after"]/1024**3,4),"protected_file_count":len(before),"protected_unchanged":True,"qwen_cpu_imports_ok":record["qwen_runtime_after"]["cpu_imports_ok"]},ensure_ascii=False),flush=True)
except BaseException as e:
    record["state"]="CLEANUP_FAILED_OR_PARTIAL"
    record["error"]=type(e).__name__+": "+str(e)
    save()
    raise
