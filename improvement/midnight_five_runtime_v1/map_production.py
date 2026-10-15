"""Metadata-only adoption of the completed original native64 production inputs."""
from bisect import bisect_left
from collections import OrderedDict
from fractions import Fraction as F
import importlib.util,json
from pathlib import Path
from mf_common import *

OLD=HOME/'twenty_hour_five_20261014_v1'

def main():
    out=ROOT/'production_mapping';out.mkdir(exist_ok=False)
    package=OLD/'temporal_family_native_package_v3'
    inputs=read(package/'package_inputs.json');lock=read(package/'source_package_lock.json')['files']
    for key in ['events','endpoints','verification','source_clocks','production_completion']:
        require(lock[inputs[key]['path']]==inputs[key]['sha256'],'Original accepted source binding differs');checked(inputs[key])
    events=read(inputs['events']['path']);endpoints=read(inputs['endpoints']['path']);verify=read(inputs['verification']['path']);clocks=read(inputs['source_clocks']['path'])
    plan_path=OLD/'temporal_production_inputs_v5/plan_01/full_plan.json';plan=read(plan_path)
    original_module=package/'code/combine_events.py';require(lock[str(original_module)]==sha(original_module),'Frozen original VERIFY recipe changed')
    spec=importlib.util.spec_from_file_location('_midnight_frozen_recipe',original_module);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    bycase=OrderedDict();event_map={x['event_id']:x for x in events}
    for req in plan['requests']:
        if req['kind']=='VERIFY':bycase.setdefault(req['original_case_id'],[]).append(req)
    entries=[];skips=[];cache=OLD/'production_stream_v5'
    for case,requests in bycase.items():
        alive=[];representative=None
        for row in requests:
            event=event_map[row['event_id']];applied=m.candidate(event,endpoints,verify,'VERIFY')
            item=dict(event_id=event['event_id'],original_interval_exact=event['original_interval_exact'],selected_interval_exact=applied['selected_interval_exact'],decision=verify[event['event_id']]['decision'])
            common=dict(case_id=case,source_id=event['source_id'],candidate_events=[item],old_decision_ref=inputs['verification'])
            if item['decision']=='DROP':
                skips.append(dict(common,reason='OLD_VERIFY_DROP_NO_BASELINE_CONTRIBUTION'));continue
            if row['execution']!='MODEL':
                require(row['execution']=='STRUCTURAL_UNKNOWN_ORIGINAL_VIEW_NO64' and item['decision']=='UNKNOWN' and verify[event['event_id']]['actual_model_call'] is False,'Only original explicit no64 may skip new model')
                skips.append(dict(common,reason='ADOPTED_ORIGINAL_NO64_UNKNOWN_PRESERVE_BASELINE'));continue
            alive.append(item)
            if representative is None:representative=row
        if not alive:continue
        req=representative;mp=cache/'permanent/inputs'/(req['request_id']+'.json');manifest=read(mp);meta=manifest['original_metadata'];identity=manifest['identity']
        proof=cache/'permanent/proofs'/(req['request_id']+'_first_input_replay.json');qa=read(proof)
        require(qa['status']=='PASS_FIRST_INDEPENDENT_INPUT_REPLAY_EXACT' or str(qa['status']).startswith('PASS_'),'Adopted original first independent QA missing')
        ordinals=identity['source_ordinals'];points=identity['exact_pts'];source=event_map[req['event_id']]['source_id'];clock=clocks[source];pts=list(map(F,clock['normalized_exact_pts']))
        require(len(ordinals)==len(points)==64 and len(set(ordinals))==64 and list(map(F,points))==[pts[i] for i in ordinals],'Adopted original native64 source clock differs')
        lo,hi=map(F,(req['window_start'],req['window_end']))
        require(0<=lo<hi<=F(clock['physical_end_exact']) and lo<=F(points[0])<=F(points[-1])<hi,'Actual accepted original visual window domain differs')
        end=bisect_left(pts,hi)
        for r in [manifest['private_ref'],manifest['visual_ref']]:
            path=cache/r['relative'];require(path.is_file() and path.stat().st_size==r['bytes'],'Adopted successful payload missing; no recompute fallback')
        entries.append(dict(case_id=case,source_id=source,source_sha256=identity['source_sha256'],source_ordinals=ordinals,exact_pts=points,
            window_exact=[str(lo),str(hi)],window_native_end_ordinal=end,window_native_end_exact=str(hi),candidate_events=alive,
            input_kind='SPLIT_LUT',cache_root=str(cache),cache_manifest_ref=ref(mp),original_first_QA_ref=ref(proof),
            original_prompt=meta['prompt'],full_signature=manifest['full_signature']))
    require(len(events)==665 and sum(len(e['candidate_events']) for e in entries+skips)==665,'Complete original event denominator differs')
    save(out/'requests.json',dict(schema='NEW_FIVE_WAY_PRODUCTION_ADOPTED_INPUTS_V1',entries=entries,structural_skips=skips,old_package_inputs_ref=ref(package/'package_inputs.json'),old_source_lock_ref=ref(package/'source_package_lock.json'),old_plan_ref=ref(plan_path),expected_original_events=665,expected_sources=426,new_model_calls=0,new_vision_encodes=0,new_media_decodes=0))
    print(json.dumps(dict(status='PASS_METADATA_ONLY_FULL_PRODUCTION_ADOPTION',new_requests=len(entries),structural_skip_events=sum(len(e['candidate_events']) for e in skips),old_events=665)),flush=True)

if __name__=='__main__':main()
