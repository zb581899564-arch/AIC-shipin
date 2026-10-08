"""Own B1 assembler with original exact spatial/strict packaging procedure."""
import argparse,json,subprocess,sys,zipfile
from types import SimpleNamespace
import nd_common as c
original_rt, original_ex, cc, student, old, frames, production = c.helpers()
rt=SimpleNamespace(HERE=c.HERE,RUN=c.RUN,raw_write=c.save,bind_helpers=lambda:(student,old,frames,production))
ex=SimpleNamespace(verify=c.verify,read=c.read,sha=c.sha)

def assemble(scope):
    c.verify()
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'))
    out=c.HERE/(scope+'_01');out.mkdir(exist_ok=True);rows=[]
    model=c.read(c.HERE/'input_01/resume_manifest.json')['model_identity']
    if scope=='rematch':
        terminal=c.read(out/'rematch.completion.json')
        c.require(terminal['status']=='PASS_ALL_NESTED_DENSITY_ATTEMPTS' and terminal['fresh_model_calls']==521,'rematch incomplete')
    for job in plan['jobs']:
        item=job['metadata']
        record=dict(video_id=job['video_id'],targetRatioWH=item['targetRatioWH'],video_path=item['source_path'],
            n_frames=item['n_frames'],fps=item['fps_num']/item['fps_den'],arm='ORIGINAL_B0_PROMPT_WITH_NESTED_NATIVE_DENSITY',windows=[])
        for ix,part in enumerate(job['windows']):
            value=c.checked(c.done_path(scope,job,ix,'D',cc),job,ix,'D',original_ex)
            c.require(value['model_identity']==model,'wrong production model')
            record['windows'].append(dict(value,start_sec=part['start_sec'],end_sec=part['end_sec'],index=ix,
                clock_record_sha256=part['clock_record_sha256'],clock_branch=part['clock_branch'],
                raw_source_pts_origin_sec=part['raw_source_pts_origin_sec']))
        rows.append(record)
    c.require(len(rows)==(8 if scope=='nontest' else 426),'scope denominator')
    old.write_rows(out/'temporal.jsonl',rows)
    c.save(out/'temporal.stage.json',dict(status='PASS_TEMPORAL_EXECUTION',videos=len(rows),
        windows=sum(len(x['windows']) for x in rows),invalid_windows=0,output_sha256=c.sha(out/'temporal.jsonl'),
        logical_parameters=8782459120,allow_empty=True,all_original_local_windows_run=True,
        selected_adapter_sha256=model['adapter_sha256'],new_optimizer_updates=0,
        nontest_exact_existing_B1_reuse=False,new_overview_calls=0))

def finish(scope):
    ex.verify()
    _, old, frames, production = rt.bind_helpers()
    out = rt.HERE / (scope + "_01")
    ref, manifest, clocks = old.inputs(scope)
    # Fail before scheduling rather than silently start a different spatial job.
    cc.require((rt.RUN / "teacher_student_autopilot_v14/cache_01" / (scope + ".json")).is_file(), "exact full spatial cache missing")
    production.scheduling(scope, out)
    space = ex.read(out / "spatial.stage.json")
    cc.require(space["status"] in ("PASS_STRICT_SOURCE_FIELD_SPATIAL", "PASS_EMPTY_SPACE_NO_MODEL_CALL") and
        (space.get("reused_cache") is True or space["status"] == "PASS_EMPTY_SPACE_NO_MODEL_CALL"), "unregistered fresh spatial execution")
    from field_contract import compose_from_field
    from package_contract import package, validate_predictions, keyset
    selected = old.rows(out / "selected.jsonl")
    projected = frames.legacy_manifest(manifest)
    predictions, provenance = compose_from_field(projected, selected, old.rows(out / "field_shots.jsonl"),
        old.rows(out / "anchor_requests.jsonl"), old.rows(out / "anchor_output.jsonl"))
    old.write_rows(out / "predictions.jsonl", predictions)
    old.write_rows(out / "provenance.jsonl", provenance)
    accepted = validate_predictions(projected, predictions, keyset(selected), provenance)
    rt.raw_write(out / "metadata.json", {"records": manifest["records"], "errors": []})
    pending = out / "candidate_NESTED_DENSITY_8B.PENDING.zip"
    accepted.update(package(out / "predictions.jsonl", pending))
    subprocess.run([sys.executable, "-B", str(rt.RUN / "baseline_a_pts_v1/vendor/independent_validate.py"),
        "--strict-loader-root", str(rt.RUN / "baseline_a_pts_v1/vendor/frozen_strict_loader"),
        "--metadata", str(out / "metadata.json"), "--selected", str(out / "selected.jsonl"),
        "--predictions", str(out / "predictions.jsonl"), "--provenance", str(out / "provenance.jsonl"),
        "--zip", str(pending), "--report", str(out / "independent_validation.json")], check=True)
    independent = ex.read(out / "independent_validation.json")
    production.check_independent(independent, scope, len(selected))
    for name, key in (("predictions.jsonl", "predictions_sha256"), ("provenance.jsonl", "provenance_sha256")):
        cc.require(ex.sha(out / name) == independent[key], "independently accepted output SHA differs")
    cc.require(independent["zip_sha256"] == ex.sha(pending), "independently accepted archive SHA differs")
    with zipfile.ZipFile(pending) as z:
        cc.require(z.namelist() == ["predictions.jsonl"] and z.testzip() is None and
            z.read("predictions.jsonl") == (out / "predictions.jsonl").read_bytes(), "actual ZIP CRC/content failure")
    candidate = out / "candidate_NESTED_DENSITY_8B.zip"
    cc.require(not candidate.exists(), "final ZIP already exists")
    pending.rename(candidate)
    accepted.update(status="PASS_COMPLETE_NESTED_DENSITY_8B_PACKAGE_ON_LINUX", candidate=str(candidate), scope=scope,
        actual_zip_bytes=candidate.stat().st_size, actual_zip_sha256=ex.sha(candidate),
        complete_pipeline_parameters=8782459120, shared_base_counted_once=True,
        selected_adapter_sha256="8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23",
        new_optimizer_updates=0, new_spatial_model_calls=0, old_spatial_cost_preserved=True,
        official_score=None, uploaded=False, automatic_return=False, source_lock_sha256=ex.sha(rt.HERE / "source_lock.json"))
    rt.raw_write(out / "package.stage.json", accepted)
    print(json.dumps(accepted), flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('assemble','finish'));p.add_argument('scope',choices=('nontest','rematch'))
    args=p.parse_args();globals()[args.stage](args.scope)
