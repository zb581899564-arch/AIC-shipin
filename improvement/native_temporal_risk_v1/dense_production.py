"""Prospective 426/521 dense128 prepare/run/assemble, with no RGB production cache.

Every production window is a new actual request. There is no old response alias,
fallback, endpoint repair, retry, training, or automatic website submission.
"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path
import dense_runtime as r

PREP = r.HERE/'rematch_01/prepare_01'
GPU = r.HERE/'rematch_01/gpu_01'
BEST_SOURCE_LOCK_SHA256 = '66668c77abf824e95892989f507a7ccd8ffce234da45ed3af2b0ac324322f490'
BEST_PLAN_SHA256 = '6ac37ae102836fdf2a44cbf676129a2678019fda34f81874601fe1c5dc055ae7'


def key(window):
    return r.digest([window['source_id'],window['index']])


def validate_original_plan(plan, manifest, clocks, ref):
    """Read-only schema checks against the original accepted source metadata."""
    r.require(plan['scope']=='rematch' and plan['records']==426 and plan['windows']==521 and
        plan['input_ref']==ref and len(plan['jobs'])==426 and len(manifest['records'])==426,
        'original accepted 426/521 plan scope or input reference differs')
    records={m['video_id']:m for m in manifest['records']}
    r.require(len(records)==426 and {j['video_id'] for j in plan['jobs']}==set(records)==set(clocks) and
        len({j['video_id'] for j in plan['jobs']})==426 and sum(len(j['windows']) for j in plan['jobs'])==521,
        'original accepted source/window identity denominator differs')
    for job in plan['jobs']:
        item=records[job['video_id']]; clock=clocks[job['video_id']]
        r.require(job['metadata']==item and job['source_key']==job['source_group']==item['source_sha256'],
            'original plan metadata/source key differs from clean manifest')
        r.require(item['clock_record_id']==item['video_id'] and item['clock_branch']==clock['branch'],
            'original clean manifest clock identity differs')
        arrays=clock['arrays']; origin=arrays['raw_first_pts_ticks']*r.F(arrays['raw_time_base'])
        parts=job['windows']
        # The accepted CFR schedule can end before manifest scope_end (source
        # 289 ends at 30 rather than 30.0666...). Keep its frozen original
        # endpoints instead of reinterpreting that historical schedule.
        r.require(parts and parts[0]['start_sec']==parts[0]['base_start_sec'] and
            parts[-1]['end_sec']==parts[-1]['base_end_sec'] and
            all(a['end_sec']==b['start_sec'] for a,b in zip(parts,parts[1:])),
            'original accepted base endpoints or contiguous window schedule differ')
        for part in parts:
            r.require(part['clock_record_sha256']==clock['clock_record_sha256'] and
                part['clock_branch']==clock['branch'] and part['raw_source_pts_origin_sec']==float(origin),
                'original plan window clock SHA/branch/raw origin differs')
            for name in ('window','base_window'):
                window=part[name]
                r.require(window['source_path']==item['source_path'] and
                    window['source_sha256']==item['source_sha256'] and window['source_total_frames']==item['n_frames'],
                    'original plan native window source metadata differs')
            window=part['window']
            if window!=part['base_window']:
                # Preserve the original exact balanced endpoints; do not snap a
                # decimal legacy boundary to a different native rational.
                r.require(float(r.F(window['exact_normalized_start']))==part['start_sec'] and
                    float(r.F(window['exact_normalized_end']))==part['end_sec'] and
                    r.F(window['exact_raw_start'])==origin+r.F(window['exact_normalized_start']) and
                    r.F(window['exact_raw_end'])==origin+r.F(window['exact_normalized_end']),
                    'original exact balanced raw/normalized endpoints differ')
    return dict(metadata_records_checked=426,window_clock_bindings_checked=521,
        original_accepted_plan=True,no_boundary_reinterpretation=True)


def accepted_production_windows():
    """Anchor current inputs to the old accepted lock before new CPU preparation."""
    best=r.RUN/'balanced_two_window_risk_v3'
    lock_path=best/'source_lock.json'; plan_path=best/'input_01/rematch_plan.json'
    r.require(r.sha(lock_path)==BEST_SOURCE_LOCK_SHA256, 'original accepted best source lock changed')
    lock=r.read(lock_path)
    r.require(lock['files'].get(str(plan_path))==BEST_PLAN_SHA256==r.sha(plan_path),
        'original best frozen rematch plan SHA differs')
    plan=r.read(plan_path)
    _,(_,_,_,_,old,_,_)=r.original_helpers()
    ref,manifest,clocks=old.inputs('rematch')
    for name in ('manifest','registry'):
        path=ref[name]
        r.require(lock['files'].get(path)==ref[name+'_sha256']==r.sha(path),
            'original accepted '+name+' SHA differs')
    bindings=validate_original_plan(plan,manifest,clocks,ref)
    clock_files=[]
    for vid in sorted(clocks):
        clock=clocks[vid]; reference=clock['clock_arrays']
        # The historical best lock freezes the registry, which itself freezes
        # each arrays SHA. It did not directly enumerate those arrays files.
        r.require(r.sha(reference['path'])==reference['sha256']==clock['clock_record_sha256'],
            'actual per-source clock arrays differ from the best frozen registry SHA binding')
        clock_files.append(dict(path=reference['path'],sha256=reference['sha256']))
    jobs,upstream=r.production_windows()
    r.require(upstream['source']==ref and upstream['original_plan_path']==str(plan_path) and
        upstream['original_plan_sha256']==BEST_PLAN_SHA256==r.sha(plan_path),
        'derived dense128 windows do not reference the accepted original plan')
    upstream['original_accepted_binding']=dict(bindings,source_lock_path=str(lock_path),
        source_lock_sha256=BEST_SOURCE_LOCK_SHA256,plan_frozen_sha256=BEST_PLAN_SHA256,
        manifest_frozen_sha256=ref['manifest_sha256'],registry_frozen_sha256=ref['registry_sha256'],
        clock_expected_sha_source='BEST_FROZEN_CLOCK_REGISTRY',clock_files=clock_files)
    return jobs,upstream


def prepare():
    import torch
    r.registration('rematch')
    # A prospective production registration does not replace the separate pilot gate.
    pilot=r.read(r.HERE/'pilot_01/replay_01/completion.json')
    r.require(pilot['status']=='PASS_SIX_DENSE128_INDEPENDENT_CPU_REPLAYS_NOT_QUALITY',
        'six real pilot calls require independent CPU acceptance before production preparation')
    PREP.mkdir(parents=True,exist_ok=False)
    try:
        jobs,upstream=accepted_production_windows(); processor=r.processor_cpu(); entries=[]
        for num,job in enumerate(jobs,1):
            for window in job['windows']:
                identifier=key(window); folder=PREP/identifier; folder.mkdir()
                r.save(folder/'request.json',window)
                encoded,evidence=r.encode_window(processor,window)
                r.save(folder/'proof.json',dict(window=window,input_evidence=evidence,
                    processor_weights_loaded=False,CUDA_initialized=False,new_model_calls=0,RGB_cached=False))
                entries.append(dict(key=identifier,video_id=window['source_id'],index=window['index'],
                    request_path=str(folder/'request.json'),request_sha256=r.sha(folder/'request.json'),
                    proof_path=str(folder/'proof.json'),proof_sha256=r.sha(folder/'proof.json')))
                del encoded
            print(json.dumps(dict(stage='DENSE128_REMATCH_CPU_PREPARE',videos=num,total_videos=426,
                windows=len(entries),total_windows=521)),flush=True)
        r.require(len(entries)==521 and len({e['key'] for e in entries})==521 and not torch.cuda.is_initialized(),
            'production CPU denominator or CUDA initialization differs')
        r.save(PREP/'acceptance.json',dict(status='PASS_426_521_DENSE128_REAL_NATIVE_CPU_INPUTS',utc=r.utc(),
            recipe=r.RECIPE,jobs=jobs,entries=entries,upstream=upstream,sources=426,windows=521,
            new_model_calls=0,new_optimizer_updates=0,CPU_only=True,CUDA_initialized=False,RGB_cached=False,
            pilot_replay_sha256=r.sha(r.HERE/'pilot_01/replay_01/completion.json'),
            estimated_new_output_bytes=536870912,source_plan_preserved=True,official_score=None))
    except Exception as exc:
        r.failure(PREP,exc); raise


def prepared():
    path=PREP/'acceptance.json'; value=r.read(path)
    r.require(value['status']=='PASS_426_521_DENSE128_REAL_NATIVE_CPU_INPUTS' and
        value['sources']==426 and value['windows']==521 and value['new_model_calls']==0 and
        value['CUDA_initialized'] is False and value['RGB_cached'] is False,
        'complete real production CPU inputs are not accepted')
    jobs,upstream=accepted_production_windows()
    r.require(jobs==value['jobs'] and upstream==value['upstream'] and len(value['entries'])==521,
        '426/521 production manifest or original balanced schedule differs')
    windows={key(w):w for j in jobs for w in j['windows']}; extra=[path,Path(upstream['original_plan_path'])]
    r.require(len(windows)==521 and {e['key'] for e in value['entries']}==set(windows), '521 unique accepted windows differ')
    for entry in value['entries']:
        q,p=Path(entry['request_path']),Path(entry['proof_path'])
        r.require(r.sha(q)==entry['request_sha256'] and r.sha(p)==entry['proof_sha256'], 'production CPU proof bytes changed')
        proof=r.read(p)
        r.require(r.read(q)==proof['window']==windows[entry['key']], 'actual registered production window differs')
        extra += [q,p,Path(proof['window']['source_path'])]
    extra += [Path(value['upstream']['source']['manifest']),Path(value['upstream']['source']['registry']),
              r.HERE/'pilot_01/replay_01/completion.json']
    binding=upstream['original_accepted_binding']
    extra += [Path(binding['source_lock_path'])]+[Path(c['path']) for c in binding['clock_files']]
    r.require(value['pilot_replay_sha256']==r.sha(r.HERE/'pilot_01/replay_01/completion.json'), 'independent pilot acceptance changed')
    return value,extra


def run():
    acceptance,extra=prepared(); lock=r.verify_lock('rematch',extra)
    GPU.mkdir(parents=True,exist_ok=False); attempts=GPU/'attempts.jsonl'
    try:
        with attempts.open('x',encoding='utf-8'): pass
        model,processor,identity,config=r.loaded_model()
        r.save(GPU/'model_identity.json',dict(identity=identity,selected_time_adapter_enabled=True,new_optimizer_updates=0))
        from original_grammar import ascii_token_candidates
        candidates=ascii_token_candidates(processor.tokenizer)
        proofs={e['key']:r.read(e['proof_path']) for e in acceptance['entries']}; entries=[]
        with (GPU/'temporal.jsonl').open('x',encoding='utf-8',newline='\n') as stream:
            for num,job in enumerate(acceptance['jobs'],1):
                record={k:v for k,v in job.items() if k!='windows'}; record['windows']=[]
                for window in job['windows']:
                    identifier=key(window); folder=GPU/identifier; folder.mkdir()
                    encoded,evidence=r.encode_window(processor,window)
                    r.require(evidence==proofs[identifier]['input_evidence'],'actual production request differs from independent accepted CPU proof')
                    done=r.generate(model,processor,encoded,evidence,window,folder,attempts,521,candidates)
                    one=dict(done,index=window['index'],start_sec=float(r.F(window['exact_normalized_start'])),
                        end_sec=float(r.F(window['exact_normalized_end'])),clock_branch=job['clock_branch'],
                        clock_record_sha256=window['clock_record_sha256'],raw_source_origin=window['raw_source_origin'],
                        exact_raw_start=window['exact_raw_start'],exact_raw_end=window['exact_raw_end'])
                    record['windows'].append(one)
                    entries.append(dict(key=identifier,video_id=window['source_id'],index=window['index'],
                        done_path=str(folder/'done.json'),done_sha256=r.sha(folder/'done.json')))
                    del encoded
                stream.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n'); stream.flush(); __import__('os').fsync(stream.fileno())
                print(json.dumps(dict(stage='DENSE128_REMATCH_REAL_CALLS',videos=num,total_videos=426,
                    accepted_calls=len(entries),total_calls=521)),flush=True)
        engine,_,_,_,_=r.dependencies()
        r.require(engine.frozen_identity(model,config)==identity['base'] and engine.adapter_identity(model,config)==identity['adapter'],
            'original frozen B weights changed during production inference')
        events=r.rows(attempts)
        r.require(len(entries)==521 and sum(e['event']=='BEGIN_MODEL_CALL' for e in events)==
            sum(e['event']=='ACCEPTED_MODEL_CALL' for e in events)==521,'521 actual unique terminals differ')
        r.save(GPU/'completion.json',dict(status='PASS_DENSE128_426_TEMPORAL_EXECUTION',utc=r.utc(),entries=entries,
            actual_model_calls=521,new_optimizer_updates=0,source_lock_sha256=lock['sha256'],
            cpu_acceptance_sha256=r.sha(PREP/'acceptance.json'),attempts_sha256=r.sha(attempts),
            model_identity_sha256=r.sha(GPU/'model_identity.json'),temporal_sha256=r.sha(GPU/'temporal.jsonl'),
            videos=426,windows=521,invalid_windows=0,allow_empty=True,complete_pipeline_parameters=8782459120,
            selected_adapter_sha256=r.ADAPTER_SHA,new_spatial_model_calls=0,old_response_aliases=0,official_score=None))
    except Exception as exc:
        r.failure(GPU,exc,attempts); raise


def assemble():
    acceptance,extra=prepared(); lock=r.verify_lock('rematch',extra)
    replay_path=r.HERE/'rematch_01/replay_01/completion.json'; replay=r.read(replay_path)
    terminal=r.read(GPU/'completion.json')
    r.require(replay['status']=='PASS_521_DENSE128_INDEPENDENT_CPU_REPLAYS' and len(replay['proofs'])==521 and
        replay['source_lock_sha256']==terminal['source_lock_sha256']==lock['sha256'] and
        replay['gpu_completion_sha256']==r.sha(GPU/'completion.json') and
        terminal['temporal_sha256']==r.sha(GPU/'temporal.jsonl'),'complete independent 521-call replay missing')
    out=r.HERE/'rematch_01/package_01'; out.mkdir(parents=True,exist_ok=False)
    try:
        common,(_,_,_,_,old,frames,production)=r.original_helpers()
        ref,manifest,clocks=old.inputs('rematch')
        cache=r.RUN/'b_score_aligned_package_v4/rematch_01'
        frozen=r.RUN/'teacher_student_autopilot_v14/cache_01/rematch.json'
        cache_evidence=production.b2_cache_evidence('rematch',ref)
        r.require({k:v for k,v in r.read(frozen).items() if k!='utc'}==cache_evidence,'complete time-independent source field binding differs')
        field=old.rows(cache/'field_frames.jsonl'); by_key={(f['video_id'],f['source_frame']):f for f in field}
        r.require(len(by_key)==len(field),'full-source spatial field contains duplicate frames')
        accepted={e['key']:e for e in acceptance['entries']}; terminals={e['key']:e for e in terminal['entries']}
        replayed={(p['source_id'],p['index']):p for p in replay['proofs']}
        selected=[]; chosen=set(); rows=r.rows(GPU/'temporal.jsonl')
        r.require(len(rows)==426 and len({j['video_id'] for j in rows})==426 and sum(len(j['windows']) for j in rows)==521,
            'complete temporal output denominator differs')
        temporal_by_id={j['video_id']:j for j in rows}
        r.require(set(temporal_by_id)=={j['video_id'] for j in acceptance['jobs']}, 'temporal source identities differ')
        for job in acceptance['jobs']:
            temporal=temporal_by_id[job['video_id']]
            r.require(all(temporal[k]==v for k,v in job.items() if k!='windows') and
                len(temporal['windows'])==len(job['windows']), 'temporal source metadata or window denominator differs')
            for window in job['windows']:
                identifier=key(window); entry=terminals[identifier]; done=r.read(entry['done_path']); proof=replayed[(window['source_id'],window['index'])]
                r.require(r.sha(entry['done_path'])==entry['done_sha256']==proof['done_sha256'] and
                    done['source_window']==window==r.read(accepted[identifier]['request_path']) and
                    done['output_valid'] is True and done['parse_errors']==[] and
                    done['native_frame_realizability']['ranges']==proof['native_ranges'], 'independent native membership or accepted raw differs')
                actual=temporal['windows'][window['index']]
                r.require(all(actual[k]==v for k,v in done.items()) and
                    actual['start_sec']==float(r.F(window['exact_normalized_start'])) and
                    actual['end_sec']==float(r.F(window['exact_normalized_end'])) and
                    actual['clock_record_sha256']==window['clock_record_sha256'], 'assembled temporal row differs from actual accepted raw/clock')
                for first,stop in proof['native_ranges']:
                    for ordinal in range(first,stop):
                        chosen.add((window['source_id'],ordinal))
        r.require(chosen and all(k in by_key for k in chosen),'empty complete batch or selection outside proven full-source field')
        selected=[dict(by_key[k]) for k in sorted(chosen)]
        from field_contract import compose_from_field
        from package_contract import keyset,package,validate_predictions
        projected=frames.legacy_manifest(manifest)
        predictions,provenance=compose_from_field(projected,selected,old.rows(cache/'field_shots.jsonl'),
            old.rows(cache/'anchor_requests.jsonl'),old.rows(cache/'anchor_output.jsonl'))
        old.write_rows(out/'selected.jsonl',selected); old.write_rows(out/'predictions.jsonl',predictions); old.write_rows(out/'provenance.jsonl',provenance)
        accepted_package=validate_predictions(projected,predictions,keyset(selected),provenance)
        r.save(out/'metadata.json',dict(records=manifest['records'],errors=[]))
        pending=out/'candidate_DENSE128_NATIVE_REALIZABLE_8B.PENDING.zip'
        accepted_package.update(package(out/'predictions.jsonl',pending))
        subprocess.run([sys.executable,'-B',str(r.RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
            '--strict-loader-root',str(r.RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
            '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
            '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
            '--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
        independent=r.read(out/'independent_validation.json')
        production.check_independent(independent,'rematch',len(selected))
        r.require(independent['zip_sha256']==r.sha(pending) and independent['predictions_sha256']==r.sha(out/'predictions.jsonl') and
            independent['provenance_sha256']==r.sha(out/'provenance.jsonl'),
            'independent actual artifact SHA differs')
        with zipfile.ZipFile(pending) as archive:
            r.require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None and
                archive.read('predictions.jsonl')==(out/'predictions.jsonl').read_bytes(),'actual ZIP CRC/roundtrip failed')
        final=out/'candidate_DENSE128_NATIVE_REALIZABLE_8B.zip'; pending.rename(final)
        accepted_package.update(status='PASS_COMPLETE_NEW_DENSE128_USER_AUTHORIZED_RISK_ZIP',utc=r.utc(),
            candidate=str(final),zip_bytes=final.stat().st_size,zip_sha256=r.sha(final),video_records=426,
            windows=521,prediction_frames=len(selected),source_lock_sha256=lock['sha256'],
            independent_replay_sha256=r.sha(replay_path),independent_validation_sha256=r.sha(out/'independent_validation.json'),
            source_field_files=cache_evidence['files'],source_cache=str(cache),cache_receipt_sha256=r.sha(frozen),
            recipe=r.RECIPE,new_model_calls=521,new_optimizer_updates=0,new_spatial_model_calls=0,
            complete_pipeline_parameters=8782459120,old_response_aliases=0,formal_quality_reference='FAILED_PRESERVED',
            scientific_effect_unknown=True,official_score=None,website_submitted=False)
        r.save(out/'completion.json',accepted_package)
        print(json.dumps(accepted_package),flush=True)
    except Exception as exc:
        r.failure(out,exc); raise


if __name__=='__main__':
    r.require(len(sys.argv)==2 and sys.argv[1] in ('prepare','run','assemble'),'usage: dense_production.py prepare|run|assemble')
    {'prepare':prepare,'run':run,'assemble':assemble}[sys.argv[1]]()
