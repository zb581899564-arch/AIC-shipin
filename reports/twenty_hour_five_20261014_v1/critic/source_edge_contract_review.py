"""Two pure numeric source-edge examples; no media, processor or model."""
import json
import sys
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'improvement/local_boundary_v1'))
import lb_contract as c

clock = dict(original_exact_pts=[str(F(i,25)) for i in range(250)],
             first_original_pts_exact='0', native_frames=250,
             physical_end_exact='10', last_frame_duration_exact='1/25')
examples = [('start', ['0','4'], 14), ('end', ['6','10'], 49)]
rows = []
for side, interval, index in examples:
    event = dict(event_id='SYN_'+side, original_case_id='SYN_W000',
                 original_segment_index=0, original_interval_exact=interval)
    request = c.plan_endpoint(event, side, clock)
    request['original_endpoint_continuity_verified'] = False  # current old cut0/len condition
    request['continuity_by_sample'] = {str(i): (side=='end' or ordinal>0)
                                      for i,ordinal in enumerate(request['source_frame_ordinals'])}
    decision = dict(decision='REFINE', sample_index=index)
    current = c.resolve_endpoint(decision, request)
    point = F(request['sample_boundary_exact'][index])
    anchor = F(request['same_candidate_inner_anchor_exact'])
    old = F(request['original_endpoint_exact'])
    samples = list(map(F,request['sample_exact_pts']))
    original_edge_legal = (old == 0 if side=='start' else old == 10)
    selected_outside_visible = samples[0] < point if side=='start' else point <= samples[index+1]
    correct_anchor_side = point < anchor if side=='start' else point > anchor
    inward = point > old if side=='start' else point < old
    proposed_geometry_admissible = (original_edge_legal and 1 <= index <= 62 and
        selected_outside_visible and correct_anchor_side and inward and
        request['continuity_by_sample'][str(index)] and index in request['allowed_sample_indices'])
    rows.append(dict(side=side, interval=interval, index=index,
        selected_ordinal=request['source_frame_ordinals'][index], selected_boundary=str(point),
        previous_sample=str(samples[index-1]), selected_sample=str(samples[index]),
        next_sample=str(samples[index+1]), inner_anchor=str(anchor),
        has_original_outside_context=request['has_original_outside_context'],
        current_resolution=current['applied_decision'], current_changed=current['changed'],
        proposed_geometry_admissible=proposed_geometry_admissible,
        hypothetical_semantic_requirement='candidate content changes at selected cut; same inner-anchor event; otherwise UNKNOWN',
        proves_model_effect=False))
assert all(row['current_changed'] is False and row['proposed_geometry_admissible'] for row in rows)
print(json.dumps({'status':'PASS_PURE_SOURCE_EDGE_GEOMETRY_COUNTEREXAMPLE_TO_ORIGINAL_OUTSIDE_GUARD',
                  'examples':rows,'media_reads':0,'new_model_calls':0,'worker_files_changed':False}))
