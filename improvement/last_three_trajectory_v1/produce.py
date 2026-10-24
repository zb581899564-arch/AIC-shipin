"""Derive three complete source results from immutable old native anchor answers."""
from collections import defaultdict
from pathlib import Path
import json
from common import ROOT, ASSETS, read, ref, checked, save_new, stable_key, lines
from curves import POLICIES, ShotTrajectory, groups
from improvement.final_sprint_v1.packaging import read_zip_rows, validate_box
from improvement.final_sprint_v1.contracts import validate_sources

KINDS = dict(pchip='ANCHOR_PCHIP_TRAJECTORY', median3='ANCHOR_MEDIAN3_TRAJECTORY',
             shot_representative='SHOT_REPRESENTATIVE_ANCHOR')


def bindings(assets, bound):
    output = {}
    reg = ref(ROOT/'registration.json')
    for policy in POLICIES:
        candidate_id = 'g_risk_' + policy
        binding = dict(candidate_id=candidate_id, candidate=dict(selection='protected40.48',policy=policy),
            protected_baselines=assets['protected_baselines'], registration_ref=reg,
            source_lock=ref(ROOT/'bound_inputs.json'), required_model_components=bound['actual_parameter_budget']['components'])
        output[policy] = binding
        save_new(ROOT/(policy+'_binding.json'),binding)
        (ROOT/policy).mkdir()
        (ROOT/policy/'sources').mkdir()
    return output


def derive(assets, bound, binding):
    cache = read(checked(bound['cache_ref']))
    spec = read(checked(bound['spec_ref']))
    field_refs = spec['renderer']['field_files']
    anchors = {(r['video_id'],r['source_frame']):r for r in lines(checked(field_refs['anchor_output.jsonl']))}
    shots = lines(checked(field_refs['field_shots.jsonl']))
    sources = {s['video_id']:s for s in assets['sources']}
    base_rows = read_zip_rows(checked(assets['protected_baselines']['40.48']))
    base = {r['video_id']:{p['frame']:p['bboxes'] for p in r['predictions']} for r in base_rows}
    clocks = validate_sources(assets['sources'],verify_media=False)
    result = {p:defaultdict(list) for p in POLICIES}
    for shot_id, shot in enumerate(groups(shots)):
        sid = shot[0]['video_id']
        frames = [r['source_frame'] for r in shot]
        selected = [f for f in frames if f in base[sid]]
        if not selected:
            continue
        by_frame = {f:anchors[sid,f] for f in frames if (sid,f) in anchors}
        trajectory = ShotTrajectory(frames,by_frame,clocks[sid][0])
        for policy in POLICIES:
            for frame in selected:
                box = trajectory.sample(policy,frame,clocks[sid][0][frame],base[sid][frame],sources[sid])
                validate_box(box,sources[sid])
                result[policy][sid].append(dict(frame=frame,bboxes=box,native_pts=str(clocks[sid][0][frame]),
                    shot_id=shot_id,first_anchor=trajectory.frames[0],last_anchor=trajectory.frames[-1],
                    anchor_source_count=len(trajectory.frames),representative_anchor=trajectory.frames[trajectory.representative]))
        if shot_id % 500 == 0:
            print('DERIVED_SHOT',shot_id,flush=True)
    for policy in POLICIES:
        count=changed=0
        for sid in sorted(sources):
            rows=sorted(result[policy][sid],key=lambda r:r['frame'])
            if [r['frame'] for r in rows] != sorted(base[sid]):
                raise ValueError('Any lost/extra original frame blocks this package')
            count+=len(rows)
            changed+=sum(r['bboxes'] != base[sid][r['frame']] for r in rows)
            proof=dict(schema='AIC_FINAL_SPATIAL_EVIDENCE_V1',video_id=sid,
                source_sha256=sources[sid]['media']['sha256'],binding_sha256=stable_key(binding[policy]),
                model_components=bound['actual_parameter_budget']['components'],
                algorithm=KINDS[policy],input_refs=[field_refs['anchor_output.jsonl'],field_refs['anchor_requests.jsonl'],
                    field_refs['field_shots.jsonl'],bound['cache_ref'],bound['metadata_ref'],ref(ROOT/'registration.json')],
                frames=rows,new_model_calls=0,offline_quality_validated=False)
            proof_path=ROOT/policy/'sources'/(sid+'_evidence.json')
            save_new(proof_path,proof)
            proof_ref=ref(proof_path)
            spatial=[dict(frame=r['frame'],kind='automatic_spatial',source_sha256=sources[sid]['media']['sha256'],
                          evidence=proof_ref) for r in rows]
            source_result=dict(video_id=sid,status='SUCCESS_NONEMPTY',source_sha256=sources[sid]['media']['sha256'],
                binding_sha256=stable_key(binding[policy]),predictions=[dict(frame=r['frame'],bboxes=r['bboxes']) for r in rows],
                evidence=proof_ref,spatial_provenance=spatial)
            save_new(ROOT/policy/'sources'/(sid+'.json'),source_result)
        if count != 123479 or changed == 0:
            raise ValueError('Incomplete or zero-difference risk candidate')
        save_new(ROOT/policy/'production_completion.json',dict(status='COMPLETE426_RISK_SPATIAL_DERIVATION',
            sources=426,frames=count,changed_boxes=changed,time_added=0,time_removed=0,width_changes=0,
            new_model_calls=0,policy=policy,source_lock=ref(ROOT/'bound_inputs.json')))
        print('COMPLETE_POLICY',policy,'changed',changed,flush=True)


def main():
    assets,bound=read(ASSETS),read(ROOT/'bound_inputs.json')
    derive(assets,bound,bindings(assets,bound))


if __name__ == '__main__':
    main()
