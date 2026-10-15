"""A single local CPU boundary candidate from immutable accepted source inputs."""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import traceback
import zipfile
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

from intervals import expanded_windows, native_membership

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/boundary_refinement_20261012_v1'
INPUT = REPORT/'input_01'
DEPENDENCIES = REPORT/'input_dependencies'
NAME = 'ASYMMETRIC_BOUNDARY_PRE075_POST050_8B'


def require(condition, why):
    if not condition:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(8<<20), b''):
            h.update(data)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    with Path(path).open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def save(path, value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write('\n')


def write_rows(path, records):
    with Path(path).open('x',encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n')


def prediction_map(records):
    result = {(r['video_id'],p['frame']):p['bboxes']
              for r in records for p in r['predictions']}
    require(len(result)==sum(len(r['predictions']) for r in records), 'Duplicate prediction keys')
    return result


def main():
    lock_path = REPORT/'production_source_lock.json'
    lock = read(lock_path)
    claim = read(REPORT/'launch.claim.json')
    require(claim['source_lock_sha256']==sha(lock_path), 'Launch source-lock SHA mismatch')
    required = {str(p.resolve()) for p in INPUT.rglob('*') if p.is_file()}
    required |= {str(p.resolve()) for p in DEPENDENCIES.rglob('*') if p.is_file()}
    required |= {str(p.resolve()) for p in Path(__file__).parent.glob('*.py')}
    required |= {str((REPORT/n).resolve()) for n in ('PROTOCOL.json','analysis_registration.json',
                  'developer_boundary_screen.json','remote_source_export_receipt.json',
                  'input_local_acceptance.json','uncertainty_diagnostic_group_v2.json')}
    require(required <= set(lock['files']), 'Missing mandatory source bindings')
    for path, digest in lock['files'].items():
        require(sha(path)==digest, 'Frozen local input/code changed: '+path)
    history = lock['historical_candidate_zip_sha256']
    require(history and all(p in lock['files'] and lock['files'][p]==h for p,h in history.items()),
            'Historical candidate comparison lacks source bindings')
    protocol = read(REPORT/'PROTOCOL.json')
    require(protocol['candidate']==NAME and protocol['padding_exact']==['3/4','1/2'], 'Registered recipe differs')
    require(protocol['selection_registered_before_new_rematch_membership'] is True, 'Recipe not fixed before production')
    source = read(INPUT/'source_bindings.json')
    require(source['production_protocol_sha256']==sha(REPORT/'PROTOCOL.json'), 'Export was not bound to fixed recipe')
    require(source['full_field_boxes_match_all_baseline_frames'] is True and source['baseline_frames']==118027, 'Unaccepted source projection')
    baseline_path = ROOT/'deliveries/BOUNDARY_CONTEXT_050_20261012/candidate_BOUNDARY_CONTEXT_050.zip'
    require(sha(baseline_path)==protocol['baseline_zip_sha256'], '40.26 baseline ZIP changed')
    with zipfile.ZipFile(baseline_path) as z:
        require(z.namelist()==['predictions.jsonl'] and z.testzip() is None, 'Baseline archive malformed')
        require(z.read('predictions.jsonl')==(INPUT/'baseline_predictions.jsonl').read_bytes(), 'Baseline input differs from actual delivered ZIP')
    sys.path[:0] = [str(DEPENDENCIES),str(INPUT/'validator')]
    from contracts import parse_segments
    from package_contract import validate_predictions, package, keyset

    metadata = read(INPUT/'metadata.json')
    manifest = read(DEPENDENCIES/'legacy_spatial_manifest.json')['manifest']
    records = {r['video_id']:r for r in metadata['records']}
    clocks = read(INPUT/'clocks.json')
    temporal = read(INPUT/'temporal_inputs.json')
    original = {r['video_id']:r for r in temporal['records']}
    require(len(records)==len(metadata['records'])==len(original)==len(temporal['records'])==426 and
            set(records)==set(clocks)==set(original)=={str(i) for i in range(426)}, '426 input identity mismatch')
    full = rows(INPUT/'full_selected.jsonl')
    field_map = {(r['video_id'],r['source_frame']):r for r in full}
    require(len(full)==len(field_map)==234158, 'Frozen full-field duplicates/denominator mismatch')
    field_by_video = defaultdict(list)
    for r in full:
        require(type(r['source_frame']) is int, 'Noninteger source field frame')
        m = records[r['video_id']]
        require(r['source_path']==m['source_path'] and r['source_n_frames']==m['n_frames'] and
                r['source_width']==m['width'] and r['source_height']==m['height'] and
                r['target_ratio_wh']==m['targetRatioWH'], 'Spatial source row metadata mismatch')
        field_by_video[r['video_id']].append(r['source_frame'])
    base_predictions = rows(INPUT/'baseline_predictions.jsonl')
    base = prediction_map(base_predictions)
    require(len(base)==118027, '40.26 baseline frame denominator differs')
    old_zip = ROOT/'deliveries/BALANCED_TWO_WINDOW_8B_20261009/candidate_BALANCED_TWO_WINDOW_8B.zip'
    require(sha(old_zip)=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496', 'Previous 37.66 artifact changed')
    with zipfile.ZipFile(old_zip) as z:
        old_records = [json.loads(line) for line in z.read('predictions.jsonl').splitlines()]
    old_keys = set(prediction_map(old_records))

    target, reproduced_base, reproduced_original = set(), set(), set()
    native_proofs = []
    windows = 0
    for vid in sorted(records):
        m, clock = records[vid], clocks[vid]
        tick = F(clock['raw_time_base']);origin = clock['raw_first_pts_ticks']*tick
        points = [p*tick-origin for p in clock['native_pts_ticks']]
        require(len(points)==m['n_frames'], 'Native source frame denominator mismatch')
        ids = sorted(field_by_video[vid])
        require(ids and ids==list(range(ids[0],ids[-1]+1)), 'Noncontiguous or duplicate frozen spatial domain')
        domain = (ids[0],ids[-1]+1)
        parts = original[vid]['windows']
        for part in parts:
            require(part['clock_record_sha256']==clock['clock_record_sha256'], 'Clock/response source binding mismatch')
            duration = float(F(part['end_exact']))-float(F(part['start_exact']))
            parsed, errors, _ = parse_segments(part['raw_output'],duration,allow_empty=True)
            require(not errors and parsed==part['segments'] and
                    part['original_status']==('MODEL_OK' if parsed else 'LEGAL_EMPTY'), 'Untouched original parser/status differs')
            for a,b in parsed:
                start = F(part['start_exact'])
                core = native_membership(points,[(start+F(str(a)),start+F(str(b)))])
                require(core and all((vid,f) in field_map for f in core), 'Original interval has zero native frames or missing original field')
            windows += 1
        exact0 = expanded_windows(parts,'0','0')
        exact050 = expanded_windows(parts,'1/2','1/2')
        exact_new = expanded_windows(parts,*protocol['padding_exact'])
        original_ids = native_membership(points,exact0,domain)
        base_ids = native_membership(points,exact050,domain)
        new_ids = native_membership(points,exact_new,domain)
        require(original_ids <= base_ids <= new_ids, 'Context removed an accepted baseline/core selection')
        reproduced_original.update((vid,f) for f in original_ids)
        reproduced_base.update((vid,f) for f in base_ids)
        target.update((vid,f) for f in new_ids)
        native_proofs.append(dict(video_id=vid,n_frames=len(points),field_domain=list(domain),
                                 original_frames=len(original_ids),baseline_frames=len(base_ids),
                                 candidate_frames=len(new_ids),added=len(new_ids-base_ids),removed=0,
                                 direct_predicate_equals_bisect=True,original_windows=len(parts)))
    require(windows==temporal['windows']==521, 'Complete original window denominator differs')
    require(reproduced_original==old_keys and len(old_keys)==102112, 'Zero-context original membership differs from delivered 37.66 ZIP')
    require(reproduced_base==set(base), 'Half-second membership does not reproduce actual 40.26 ZIP')
    require(set(base)<target<=set(field_map), 'Candidate is unchanged or lacks actual frozen source fields')
    full_predictions = rows(INPUT/'full_predictions.jsonl')
    full_boxes = prediction_map(full_predictions)
    require(set(full_boxes)==set(field_map) and all(full_boxes[k]==v for k,v in base.items()), 'Complete frozen spatial field differs from original baseline boxes')
    selected = [field_map[k] for k in sorted(target)]
    predictions = [dict(r,predictions=[p for p in r['predictions'] if (r['video_id'],p['frame']) in target]) for r in full_predictions]
    provenance = [p for p in rows(INPUT/'full_provenance.jsonl') if (p['video_id'],p['source_frame']) in target]
    require(keyset(provenance)==target, 'Missing frozen source provenance')
    report = validate_predictions(manifest,predictions,target,provenance)
    field_frames_total = len(field_map)
    # Release unused full-field objects before the independent validator starts.
    del full, field_map, field_by_video, full_predictions, full_boxes
    del base_predictions, old_records, clocks, temporal, original
    out = REPORT/'candidate_01';out.mkdir(exist_ok=False)
    for name,data in [('selected',selected),('predictions',predictions),('provenance',provenance)]:
        write_rows(out/(name+'.jsonl'),data)
    save(out/'metadata.json',metadata)
    pending = out/('candidate_'+NAME+'.PENDING.zip')
    report.update(package(out/'predictions.jsonl',pending))
    subprocess.run([sys.executable,'-B',str(INPUT/'validator/independent_validate.py'),
                    '--strict-loader-root',str(INPUT/'validator/frozen_strict_loader'),
                    '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
                    '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
                    '--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    independent = read(out/'independent_validation.json')
    require(len(independent['checks'])==11 and all(independent['checks'].values()), 'Independent 11strict failed')
    require(independent['video_records']==426 and independent['prediction_frames']==len(target) and
            independent['zip_sha256']==sha(pending) and independent['predictions_sha256']==sha(out/'predictions.jsonl'), 'Independent archive/count/SHA mismatch')
    require(independent['provenance_sha256']==sha(out/'provenance.jsonl'), 'Independent provenance file SHA differs')
    require(independent['zip_sha256'] not in set(history.values()), 'New artifact equals a historical candidate')
    with zipfile.ZipFile(pending) as z:
        require(z.namelist()==['predictions.jsonl'] and z.testzip() is None and
                z.read('predictions.jsonl')==(out/'predictions.jsonl').read_bytes(), 'Final ZIP CRC/member roundtrip failed')
    final = out/('candidate_'+NAME+'.zip');pending.rename(final)
    save(out/'native_selection_acceptance.json',dict(status='PASS_426_EXACT_NATIVE_BASELINE_PRESERVATION_AND_FULL_SOURCE_DOMAIN',
         source_lock_sha256=sha(lock_path),rows=native_proofs,baseline_frames=len(base),original_frames=len(old_keys),
         candidate_frames=len(target),added=len(target-set(base)),removed=0,all_baseline_boxes_unchanged=True,
         padding_exact=protocol['padding_exact'],whole_source_field_frames=field_frames_total,windows=windows))
    report.update(status='PASS_COMPLETE_NEW_ASYMMETRIC_BOUNDARY_RISK_ZIP_LOCAL',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  candidate=str(final.resolve()),candidate_name=NAME,zip_bytes=final.stat().st_size,zip_sha256=sha(final),
                  padding_exact=protocol['padding_exact'],original_temporal_windows=windows,
                  original_frames=len(old_keys),baseline_frames=len(base),candidate_frames=len(target),
                  added_frames=len(target-set(base)),removed_frames=0,all_baseline_boxes_unchanged=True,
                  empty_video_records=sum(not r['predictions'] for r in predictions),
                  protocol_sha256=sha(REPORT/'PROTOCOL.json'),source_lock_sha256=sha(lock_path),
                  native_acceptance_sha256=sha(out/'native_selection_acceptance.json'),
                  independent_validation_sha256=sha(out/'independent_validation.json'),
                  complete_pipeline_parameters=8782459120,baseline_user_reported_score=40.26,
                  new_model_calls=0,new_video_decodes=0,new_processor_encodes=0,new_optimizer_updates=0,
                  formal_quality_reference='FAILED_PRESERVED',scientific_quality_pass=False,
                  risk_probe=True,official_score=None,website_submitted=False)
    save(out/'completion.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        save(REPORT/'package_failure.json',dict(status='STOP_FAILURE_NO_SAME_CLAIM_RETRY',
             error=repr(exc),traceback=traceback.format_exc(),new_model_calls=0,new_optimizer_updates=0))
        raise
