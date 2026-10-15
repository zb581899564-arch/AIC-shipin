"""Independent strict output-token/native checks; never repairs failed raw."""
from fractions import Fraction as F
import json
import math

import pr_contract as c


def independent_structural_result(row,source):
    """Rebuild pre-model UNKNOWN from the frozen source/window, never failed raw."""
    c.require(row['execution']!='MODEL' and row['source_id']==source['source_id'] and
        row['kind'] in ('ENDPOINT','VERIFY'),'A typed frozen structural request is required')
    windows=[window for window in source['windows'] if window['original_case_id']==row['original_case_id']]
    c.require(len(windows)==1,'Structural request has no unique original window')
    window=windows[0];events=[event for event in window['events'] if event['event_id']==row['event_id']]
    c.require(len(events)==1,'Structural request has no unique original candidate')
    event=events[0]
    for key in ('original_case_id','original_segment_index','original_interval_exact',
                'original_native_cut_interval_exact','original_native_cut_source_ordinals'):
        c.require(row[key]==event[key],'Structural original candidate identity changed')
    if row['kind']=='ENDPOINT':
        points=list(map(F,source['physical_plan_clock']['normalized_exact_pts']))
        lo,hi=F(row['window_start']),F(row['window_end'])
        c.require(row['execution']=='STRUCTURAL_UNKNOWN_NO64' and
            sum(lo<=point<hi for point in points)<64 and row['source_frame_ordinals'] is None,
            'Endpoint structural UNKNOWN requires the original insufficient native window')
        side=row['side'];legacy=row['original_endpoint_exact'];native=row['original_native_cut_endpoint_exact']
        c.require(side in ('start','end') and row['request_id']==row['event_id']+'.'+side and
            legacy==event['original_interval_exact'][side=='end'] and
            native==event['original_native_cut_interval_exact'][side=='end'],
            'Structural endpoint side/dual point differs')
        result=dict(request_id=row['request_id'],event_id=row['event_id'],side=side,
            raw_decision={'decision':'UNKNOWN'},applied_decision='UNKNOWN_INSUFFICIENT_DISTINCT_NATIVE_FRAMES',
            original_endpoint_exact=legacy,endpoint_exact=legacy,legacy_recipe_original_endpoint_exact=legacy,
            original_native_cut_endpoint_exact=native,refiner_native_cut_endpoint_exact=native,
            native_endpoint_exact=native,displacement_exact='0',changed=False,
            actual_model_call=False,declared_before_model=True)
        c.require(row['structural_endpoint_result']==result,'Structural endpoint result changed')
        return result
    n=row['original_visual_sample_count'];ordinals=window['original_frame_ordinals']
    c.require(row['execution']=='STRUCTURAL_UNKNOWN_ORIGINAL_VIEW_NO64' and type(n)is int and 1<=n<64 and
        window['original_visual_sample_count']==n==len(ordinals)==len(set(ordinals)) and
        row['required_distinct_native_frames']==64 and row['request_id']==row['event_id']+'.verify' and
        row['source_frame_ordinals']==row['verify_original_frame_ordinals']==ordinals and
        row['original_frame_pixel_sha256']==window['original_frame_pixel_sha256'] and len(row['original_frame_pixel_sha256'])==n and
        row['verify_eligible_source_ordinal_bounds']==window['eligible_source_ordinal_bounds'] and
        row['new_processor_and_input_proof_required'] is False and 'lease_id' not in row and
        row['verify_view_kind']=='PREDECLARED_SHORT_ORIGINAL_VIEW_NO_MODEL_CONTEXT',
        'Short VERIFY needs the original actual count/ordinals/pixel metadata; no lease, processor or padding')
    result=dict(event_id=row['event_id'],request_id=row['request_id'],original_case_id=row['original_case_id'],
        original_segment_index=row['original_segment_index'],original_interval_exact=row['original_interval_exact'],
        original_native_cut_interval_exact=row['original_native_cut_interval_exact'],
        decision='UNKNOWN',candidate_kept=True,retained_interval_exact=row['original_interval_exact'],
        applied_decision='UNKNOWN_SHORT_ORIGINAL_VISUAL_CONTEXT_UNAVAILABLE',boundaries_changed=False,
        new_candidate_created=False,uncertainty_gate='SHORT_ORIGINAL_VISUAL_CONTEXT_UNAVAILABLE',
        successful_model_call_required=False,actual_model_call=False,predeclared_skip=True,declared_before_model=True,
        original_visual_sample_count=n,required_distinct_native_frames=64,
        verify_view_kind='PREDECLARED_SHORT_ORIGINAL_VIEW_NO_MODEL_CONTEXT',dual_coordinate_schema=row['dual_coordinate_schema'])
    c.require(row['structural_verify_result']==result,'Short VERIFY must preserve the candidate as UNKNOWN, without fake raw/GPU')
    return result


def strict_tokens(tokenizer,raw,finite,eos):
    ids=raw['output_token_ids'];scores=raw['selected_token_scores']
    c.require(raw['actual_model_call'] is True and isinstance(ids,list) and 0<len(ids)<=256 and
        all(type(token)is int and token>=0 for token in ids) and
        raw['output_tokens']==len(ids)==raw['generated_score_count']==len(scores) and
        all(math.isfinite(float(score)) for score in scores),'Actual output/token/finite-score denominator invalid')
    c.require(raw['eos_token_ids']==list(eos) and raw['constraint_stats']['calls']>0 and
        raw['constraint_stats']['full_context_decodes']>0 and raw['constraint_stats']['dead_ends']==0,
        'Actual EOS/full-context finite grammar evidence missing')
    suffix=[];text=''
    for index,token in enumerate(ids):
        if token in eos:
            c.require(index==len(ids)-1 and text in finite,'EOS before complete canonical JSON')
            continue
        c.require(text not in finite,'Token continued past complete JSON')
        suffix.append(token)
        continued=tokenizer.decode(suffix,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        c.require(len(continued)>len(text) and continued.startswith(text) and any(value.startswith(continued) for value in finite),
            'Actual full-context token continuation left finite grammar')
        text=continued
    c.require(text in finite and text==raw['raw_output'] and
        tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)==text,
        'Actual raw/full-context generated token JSON differs; no repair')
    decision=json.loads(text)
    c.require(json.dumps(decision,separators=(',',':'))==text,'Canonical JSON parser differs')
    return decision


def coordinate_binding(meta):
    keys=('dual_coordinate_schema','original_interval_exact','original_window_exact',
          'original_native_cut_interval_exact','original_native_cut_source_ordinals')
    if meta['kind']=='ENDPOINT':
        keys+=('original_endpoint_exact','legacy_recipe_original_endpoint_exact',
               'original_native_cut_endpoint_exact','refiner_native_cut_endpoint_exact')
    else:keys+=('new_verify_window_exact','verify_eligible_source_ordinal_bounds','verify_original_frame_ordinals','physical_end_exact')
    return {key:meta[key] for key in keys}


def independent_endpoint_export(native,meta,clock):
    """Independent application projection: a native KEEP never replaces a recipe point."""
    old=F(meta['original_endpoint_exact']);pivot=F(meta['original_native_cut_endpoint_exact'])
    c.require(old==F(meta['legacy_recipe_original_endpoint_exact']) and
        pivot==F(meta['refiner_native_cut_endpoint_exact']) and
        native['request_id']==meta['request_id'] and native['event_id']==meta['event_id'] and native['side']==meta['side'] and
        F(native['original_endpoint_exact'])==pivot,'Native result/legacy recipe candidate identity differs')
    side_index=0 if meta['side']=='start' else 1
    c.require(old==F(meta['original_interval_exact'][side_index]) and
        pivot==F(meta['original_native_cut_interval_exact'][side_index]),'Dual candidate endpoint/interval mapping differs')
    candidate=F(native['endpoint_exact'])
    moved=native['applied_decision']=='REFINE' and candidate!=pivot
    if moved:c.require(0<=candidate<=F(clock['physical_end_exact']),'REFINE is outside new actual native physical domain')
    applied=candidate if moved else old
    return dict(native,original_endpoint_exact=str(old),endpoint_exact=str(applied),
        displacement_exact=str(applied-old),changed=applied!=old,
        legacy_recipe_original_endpoint_exact=str(old),original_native_cut_endpoint_exact=str(pivot),
        refiner_native_cut_endpoint_exact=str(pivot),native_endpoint_exact=str(candidate),
        native_displacement_exact=str(candidate-pivot),native_cut_actually_moved=moved,
        original_recipe_preserved=not moved,dual_coordinate_schema=meta['dual_coordinate_schema'])


def independent_verify(meta,text):
    """Read only frozen candidate/native metadata, no original video or GT."""
    first,last=map(F,meta['original_native_cut_interval_exact'])
    lo,hi=map(F,meta['new_verify_window_exact'])
    full=list(map(F,meta['all_source_exact_pts']));physical=F(meta['physical_end_exact'])
    eligible=meta['verify_eligible_source_ordinal_bounds'];ordinals=meta['source_frame_ordinals']
    c.require(len(full)==meta['source_total_frames'] and full and full[0]==0 and all(a<b for a,b in zip(full,full[1:])) and
        physical>full[-1] and isinstance(eligible,list) and len(eligible)==2 and all(type(i)is int for i in eligible) and
        0<=eligible[0]<eligible[1]<=len(full),'Independent actual full source/VERIFY eligible ordinal domain differs')
    def cut(i):return full[i] if i<len(full) else physical
    c.require(lo==cut(eligible[0]) and hi==cut(eligible[1]) and
        F(meta['window_start'])==lo and F(meta['window_end'])==hi and
        ordinals==meta['verify_original_frame_ordinals'] and len(ordinals)==len(set(ordinals))==64 and
        all(type(i)is int and eligible[0]<=i<eligible[1] for i in ordinals) and
        all(a<b for a,b in zip(ordinals,ordinals[1:])),
        'Independent VERIFY true ordinal-context/original64 binding differs; no fake hi or replacement samples')
    core=meta['original_native_cut_source_ordinals']
    c.require(isinstance(core,list) and len(core)==2 and all(type(i)is int for i in core) and
        eligible[0]<=core[0]<core[1]<=eligible[1] and first==cut(core[0]) and last==cut(core[1]),
        'Independent original native candidate cut/ordinal mapping differs')
    c.require(0<=lo<=first<last<=hi,'Registered actual ordinal-context candidate identity invalid')
    points=list(map(F,meta['sample_exact_pts']))
    c.require(points==[full[i] for i in ordinals] and len(points)==64 and all(a<b for a,b in zip(points,points[1:])) and all(lo<=point<hi for point in points),
        'Independent VERIFY fixed native64 actual timing domain differs')
    observed=sum(first<=point<last for point in points)
    allowed=['KEEP','UNKNOWN','DROP'] if observed else ['UNKNOWN']
    c.require(observed==meta['candidate_visible_sample_count'] and allowed==meta['allowed_decisions'] and
        meta['candidate_window_local_exact']==[str(first-lo),str(last-lo)] and
        meta['audio_observed'] is False and meta['reference_available_to_inference'] is False and
        meta['reference_labels_read'] is False and meta['new_candidate_created'] is False,
        'Independent VERIFY visible-evidence/event/native gate differs')
    choices=['{"decision":"'+value+'"}' for value in allowed]
    c.require(text in choices,'Input/model/parse failure cannot become VERIFY UNKNOWN')
    decision=json.loads(text)['decision']
    return dict(event_id=meta['event_id'],request_id=meta['request_id'],original_case_id=meta['original_case_id'],
        original_segment_index=meta['original_segment_index'],source_sha256=meta['source_sha256'],
        original_interval_exact=meta['original_interval_exact'],decision=decision,candidate_kept=decision!='DROP',
        retained_interval_exact=meta['original_interval_exact'] if decision!='DROP' else None,
        boundaries_changed=False,new_candidate_created=False,uncertainty_gate=meta['uncertainty_gate'],successful_model_call_required=True,
        original_native_cut_interval_exact=meta['original_native_cut_interval_exact'],verify_view_kind=meta['verify_view_kind'],
        dual_coordinate_schema=meta['dual_coordinate_schema'])


def serialized_weights(checkpoint,terminal):
    identity=checkpoint['identity']
    c.require(identity['logical_parameters']==c.PARAMETERS and identity['base']['parameters']==c.BASE_PARAMETERS and
        identity['base']['sha256']=='74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59' and
        identity['adapter']['sha256']=='8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23' and
        identity['adapter']['tensors']==288 and identity['adapter']['actual_saved_values_equal'] is True and
        identity['adapter']['adapter_enabled'] is True,
        'Actual original base/288 saved TIME adapter identity differs')
    c.require(checkpoint['weight_check_strategy']==terminal['weight_check_strategy']==c.WEIGHT_STRATEGY and
        checkpoint['model_load_count']==terminal['model_load_count']==1 and
        terminal['full_base_and_288_adapter_rechecked'] is True and
        terminal['identity']==dict(base=identity['base'],adapter=identity['adapter']) and
        checkpoint['inventory']==terminal['inventory'] and terminal['optimizer_updates']==0,
        'Complete batch full-weight end check failed or model reloaded')
    names=checkpoint['initial_layer_state']['layer_names']
    c.serialized_state(checkpoint['initial_layer_state'],False,names);c.serialized_state(terminal['layer_state'],False,names)
    return names
