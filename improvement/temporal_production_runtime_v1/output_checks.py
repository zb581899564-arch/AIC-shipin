"""Independent strict output-token/native checks; never repairs failed raw."""
from fractions import Fraction as F
import json
import math

import pr_contract as c


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


def independent_verify(meta,text):
    """Read only frozen candidate/native metadata, no original video or GT."""
    first,last=map(F,meta['original_interval_exact'])
    lo,hi=F(meta['window_start']),F(meta['window_end'])
    c.require(0<=lo<=first<last<=hi and hi-lo<=30,'Original full-window candidate identity invalid')
    points=list(map(F,meta['sample_exact_pts']))
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
        boundaries_changed=False,new_candidate_created=False,uncertainty_gate=meta['uncertainty_gate'],successful_model_call_required=True)


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
