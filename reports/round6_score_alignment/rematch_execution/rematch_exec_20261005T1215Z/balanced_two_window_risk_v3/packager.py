"""Native-nearest assembler with original exact spatial/strict procedure."""
import argparse,json,subprocess,sys,zipfile
from types import SimpleNamespace
import bw_common as c
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
        c.require(terminal['status']=='PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS' and terminal['total_windows']==521 and
            terminal['fresh_model_calls']+terminal['reused_exact_original_calls']==521,'rematch incomplete')
    for job in plan['jobs']:
        item=job['metadata']
        record=dict(video_id=job['video_id'],targetRatioWH=item['targetRatioWH'],video_path=item['source_path'],
            n_frames=item['n_frames'],fps=item['fps_num']/item['fps_den'],arm='ORIGINAL_B0_PROMPT_WITH_BALANCED_TWO_WINDOW',windows=[])
        for ix,part in enumerate(job['windows']):
            value=c.checked(c.done_path(scope,job,ix,'BW',cc),job,ix,'BW',original_ex)
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
        fresh_model_calls=c.read(out/(scope+'.completion.json'))['fresh_model_calls'],
        exact_original_calls_reused=c.read(out/(scope+'.completion.json'))['reused_exact_original_calls'],new_overview_calls=0))


def select_balanced(manifest,temporal,clocks,plan):
    from fractions import Fraction as F
    from bisect import bisect_left
    from contracts import validate_segments
    meta={r['video_id']:r for r in manifest['records']};by_id={r['video_id']:r for r in temporal};jobs={j['video_id']:j for j in plan['jobs']}
    c.require(len(by_id)==len(temporal)==len(meta) and set(meta)==set(by_id)==set(jobs)==set(clocks),'selector identities')
    selected=[]
    for vid in sorted(meta):
        item=meta[vid];row=by_id[vid];job=jobs[vid];clock=clocks[vid]
        a=clock['arrays'];tick=F(a['raw_time_base']);origin=a['raw_first_pts_ticks']*tick
        points=[p*tick-origin for p in a['native_pts_ticks']]
        c.require(row['n_frames']==item['n_frames'] and row['video_path']==item['source_path'] and row['targetRatioWH']==item['targetRatioWH'] and
            row['fps']==item['fps_num']/item['fps_den'] and len(row['windows'])==len(job['windows']),'selector source/window identity')
        chosen=set()
        for ix,(value,part) in enumerate(zip(row['windows'],job['windows'])):
            c.require(value['output_valid'] is True and not value['parse_errors'] and value['start_sec']==part['start_sec'] and
                value['end_sec']==part['end_sec'] and value['clock_record_sha256']==clock['clock_record_sha256'],'failed/wrong-clock window')
            segments=value['parsed_segments'];validate_segments(segments,part['end_sec']-part['start_sec'])
            c.require(value['status']==('MODEL_OK' if segments else 'LEGAL_EMPTY'),'invalid empty/failure status')
            if c.is_changed(part):
                start=F(part['window']['exact_normalized_start'])
                for a,b in segments:
                    first,stop=bisect_left(points,start+F(str(a))),bisect_left(points,start+F(str(b)))
                    c.require(first<stop,'no actual frame in exact new segment');chosen.update(range(first,stop))
            else:
                from native_segment_contract import native_segment_ranges
                for first,stop in native_segment_ranges(segments,[float(x) for x in points],part['start_sec'],part['end_sec']-part['start_sec']):chosen.update(range(first,stop))
        for ordinal in sorted(chosen):
            selected.append(dict(video_id=vid,source_frame=ordinal,source_path=item['source_path'],source_width=item['width'],source_height=item['height'],
                source_n_frames=item['n_frames'],fps=item['fps_num']/item['fps_den'],target_ratio_wh=item['targetRatioWH']))
    return selected

def schedule_space(scope,out,manifest,clocks,ref):
    import shutil
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));selected=select_balanced(manifest,old.rows(out/'temporal.jsonl'),clocks,plan)
    cache=c.RUN/'b_score_aligned_package_v4'/(scope+'_01');frozen=c.RUN/'teacher_student_autopilot_v14/cache_01'/(scope+'.json')
    evidence=production.b2_cache_evidence(scope,ref);c.require({k:v for k,v in c.read(frozen).items() if k!='utc'}==evidence,'complete exact spatial cache authority changed')
    schedule=c.read(cache/'schedule.stage.json');field=old.rows(cache/'field_frames.jsonl')
    c.require(field==production.helpers()[3].field_frames(manifest,clocks),'all source field identity/algorithm differs')
    from field_contract import build_field_requests
    c.require(build_field_requests(field,old.rows(cache/'field_shots.jsonl'),8)==old.rows(cache/'anchor_requests.jsonl'),'space request identity differs')
    old.write_rows(out/'selected.jsonl',selected)
    for name in ('field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl'):
        shutil.copyfile(cache/name,out/name);c.require(c.sha(out/name)==evidence['files'][name],'copied complete field bytes changed')
    c.save(out/'schedule.stage.json',dict(schedule,selected_frames=len(selected),source_cache=str(cache),reused_time_independent_source_field=True))
    space=c.read(cache/'spatial.stage.json');space.update(reused_cache=True,model_calls_this_candidate=0,source_cache=str(cache),anchor_output_sha256=c.sha(out/'anchor_output.jsonl'))
    c.save(out/'spatial.stage.json',space)
    c.save(out/'cache_reuse_receipt.json',dict(status='PASS_COMPLETE_EXACT_SPATIAL_SOURCE_FIELD_NEW_BALANCED_SELECTION',frozen_cache_receipt_sha256=c.sha(frozen),
        selected_sha256=c.sha(out/'selected.jsonl'),original_space_cost_preserved=True,new_spatial_calls=0,files=evidence['files']))

def finish(scope):
    ex.verify()
    _, old, frames, production = rt.bind_helpers()
    out = rt.HERE / (scope + "_01")
    ref, manifest, clocks = old.inputs(scope)
    # Fail before scheduling rather than silently start a different spatial job.
    cc.require((rt.RUN / "teacher_student_autopilot_v14/cache_01" / (scope + ".json")).is_file(), "exact full spatial cache missing")
    schedule_space(scope,out,manifest,clocks,ref)
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
    pending = out / "candidate_BALANCED_TWO_WINDOW_8B.PENDING.zip"
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
    candidate = out / "candidate_BALANCED_TWO_WINDOW_8B.zip"
    cc.require(not candidate.exists(), "final ZIP already exists")
    pending.rename(candidate)
    accepted.update(status="PASS_COMPLETE_BALANCED_TWO_WINDOW_8B_PACKAGE_ON_LINUX", candidate=str(candidate), scope=scope,
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

