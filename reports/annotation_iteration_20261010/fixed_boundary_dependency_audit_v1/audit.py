"""Freeze the five existing ranges, then decide whether new observation is useful."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,psutil
ROOT=Path(__file__).resolve().parent; ITER=ROOT.parent
PRIOR=ITER/'independent_highlight_pilot_v3'; METHOD=ITER/'frame_binding_four_image_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review=read(PRIOR/'main_adjudication/final_review.json')
record=read(PRIOR/'main_adjudication/window_reference.json')
idx=read(PRIOR/'native_index.json'); byid={r['frame_id']:r for r in idx['frames']}
obs=ITER/'slot6_silver24_v1/observations/00_kLxoNp-UchI_W01'
manifest=read(obs/'manifest.json'); clock=read(obs/'native_clock.json');clockby={r['source_ordinal']:r for r in clock}
source=Path(manifest['source_path']);assert sha(source)==manifest['source_sha256']==idx['source_sha256']
assert sha(obs/'native_clock.json')==manifest['native_clock_sha256']
expected=[('gestureEnd','F05','F06'),('hideStart','F37','F38'),('closeStart','F45','F46'),('hideEnd','F50','F51'),('runStart','F57','F58')]
assert [b['name'] for b in review['boundary_decisions']]==[x[0] for x in expected]
frozen=[]
for b,(name,left,right) in zip(review['boundary_decisions'],expected):
    l,r=byid[left],byid[right]
    assert F(l['local_seconds_exact'])==F(b['uncertainty_start_local_exact'])
    assert F(r['local_seconds_exact'])==F(b['uncertainty_end_local_exact'])
    for f in (l,r):assert sha(Path(f['path']))==f['png_sha256']
    extra=[]
    for n in range(l['source_ordinal']+1,r['source_ordinal']):
        c=clockby[n]
        assert F(l['global_seconds_exact'])<F(c['global_seconds_exact'])<F(r['global_seconds_exact'])
        assert n not in {f['source_ordinal'] for f in idx['frames']}
        extra.append(dict(**c,new_image_generated=False,new_visual_observation=False))
    frozen.append(dict(name=name,source_sha256=idx['source_sha256'],left_existing=l,right_existing=r,
      old_chosen_edit_point_local_exact=b['chosen_local_exact'],old_point_is_not_native_cut_measurement=True,
      uncertainty_seconds_exact=str(F(r['local_seconds_exact'])-F(l['local_seconds_exact'])),
      possible_unobserved_native_frames=extra,old_boundary_not_modified=True))
save(ROOT/'frozen_five_ranges.json',dict(status='METADATA_RANGES_ONLY_NO_NEW_PIXELS',window_id=idx['window_id'],
 source=bound(source),native_clock=bound(obs/'native_clock.json'),original_final_review=bound(PRIOR/'main_adjudication/final_review.json'),
 ranges=frozen,total_possible_extra_frames=sum(len(r['possible_unobserved_native_frames']) for r in frozen)))
assert record['all_target_boundaries_adjudicated'] and not record['consequential_unknowns']
assert all(F(r['uncertainty_seconds_exact'])<=F('0.5') for r in frozen)
prior=read(PRIOR/'acceptance.json'); method=read(METHOD/'acceptance.json')
assert prior['original_silver_contract']['error']=='Unresolved teacher observation contract'
assert method['free_text_rejections']==3 and method['structured_field_comparison_pass']
safe=ITER.parents[1]/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
assert sha(safe)=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
memory=psutil.virtual_memory();disk=psutil.disk_usage(str(ROOT.anchor))
out=dict(status='STOP_BOUNDARY_DECODING_DEPENDENCY_NOT_DISCRIMINATIVE_FOR_CURRENT_BLOCKERS',utc=datetime.now(timezone.utc).isoformat(),
 ranges=bound(ROOT/'frozen_five_ranges.json'),source_identity_verified=True,old_boundaries_preserved=True,
 existing_uncertainties_within_frozen_half_second=True,existing_consequential_boundary_unknowns=0,
 blockers=[dict(component='v3 complete-reference observation contract',actual_error=prior['original_silver_contract']['error'],
 remedy_effect_of_extra_boundary_frames='None: cannot remove old out-of-whitelist read or retroactively pass old protocol.'),
 dict(component='four-image test free descriptions',facts=['F28/F29 language inference from simple','F60 running inferred from one static image'],
 remedy_effect_of_five_ranges='None: two captions and F60 motion are outside these fixed gaps; do not select new easier/expanded ranges.'),
 dict(component='complete train/locked references',qualified_first_window=False,
 remedy_effect_of_extra_boundary_frames='Native cut evidence alone does not resolve highlight preference, independent adjudication or missing denominator.'),
 dict(component='spatial reference',remedy_effect_of_extra_boundary_frames='No independent same-frame human crop reference generated.')],
 distinguishing_native_cut_from_edit_choice='New65 frames could measure where subjects/shots change inside the fixed ranges. They cannot certify high-value selection or the original midpoint edit choices. No new measurements claimed.',
 resource_snapshot=dict(available_ram_bytes=memory.available,free_disk_bytes=disk.free,
 rationale='Read-only live snapshot. No fixed admission threshold used; no decoder allocated because evidence dependency does not address blockers.'),
 decoder_budget=dict(registered_new_decode_passes=0,new_frames_generated=0,new_observations=0,new_GPU=0,new_model_calls=0,new_Pro=0,new_training=0),
 metadata_range_count=5,possible_new_native_frames=65,independent_reviewer_started=False,
 independent_reviewer_reason='No new visual evidence to adjudicate; do not repeat old whole-window opinions.',
 remaining23_not_expanded=True,new_zip=False,total_CLI_unchanged=23,cash='No new model invocation; prior cash remains UNKNOWN_NOT_ZERO',
 prior_v3=bound(PRIOR/'acceptance.json'),minimum_method=bound(METHOD/'acceptance.json'),baseline=bound(safe),
 minimal_external_review_if_chosen=dict(person='One independent editor capable of video highlight selection; not necessarily the user.',
 material='Existing same fixed W01 30s source, native64 images and actual student64 images; canonical corrected facts; all selected and rejected ranges; fixed5 endpoint pairs with their native PTS ranges.',
 task='Produce accountable complete highlight/NO/UNKNOWN preference and boundary adjudication under finite observations, disclose exposure and uncertainty. Do not read model preferences before independent initial judgment.',
 new_media_upload_required=False,must_be_human_for_current_time_silver_contract=False,
 qualification_note='Human editor is an alternative reference source, not a newly invented requirement of original finite-silver contract. One reviewed window still does not satisfy 8-12train/at least4sources/locked at least6of8 all4sources; spatial human gold remains separate.'),
 next_authorized_action_requires='A reference supplement that adds independent editorial evidence and meets original process, rather than this boundary-only dependency. No contact, paid service or new model run arranged here.')
save(ROOT/'acceptance.json',out)
print(json.dumps(dict(status=out['status'],ranges=5,possible_frames=65,actual_new_frames=0,new_model_calls=0,new_training=0,CLI=23,new_zip=False),ensure_ascii=False))
