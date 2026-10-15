"""Pure synthetic runtime ABI checks; no cache IO, tokenizer assets or model."""
import copy
from fractions import Fraction as F

import pr_contract as c
from output_checks import independent_verify,strict_tokens


def run(boundary,verify,independent_endpoint,continuity):
    passed=[]
    def reject(call,label):
        try:call()
        except (ValueError,KeyError):passed.append(label);return
        raise AssertionError('Expected rejection: '+label)
    plan=dict(sources=[dict(source_id='S'+str(i)) for i in range(4)],requests=[])
    for source in plan['sources']:
        for side,execution in (('start','MODEL'),('end','STRUCTURAL_UNKNOWN_NO64'),('verify','MODEL')):
            plan['requests'].append(dict(request_id=source['source_id']+'.'+side,source_id=source['source_id'],execution=execution))
    rows=[row for row in plan['requests'] if row['source_id'] in ('S1','S2')]
    batch=dict(batch_id='SYN_B01',source_ids=['S1','S2'],logical_request_ids=[r['request_id'] for r in rows],
        request_ids=[r['request_id'] for r in rows if r['execution']=='MODEL'],actual_model_call_budget=4,
        membership_reason='FROZEN_SOURCE_ORDER_AND_ACTUAL_CAPACITY_ONLY',predictions_or_reference_metrics_used_for_membership=False)
    c.require(c.batch_membership(batch,plan)==rows,'Complete source batch mapping differs');passed.append('complete_source_batch_and_typed_skip_budget')
    bad=copy.deepcopy(batch);bad['request_ids']=bad['request_ids'][:-1];bad['actual_model_call_budget']=3
    reject(lambda:c.batch_membership(bad,plan),'source_consumer_split_rejected')
    bad=copy.deepcopy(batch);bad['source_ids']=['S2','S1']
    reject(lambda:c.batch_membership(bad,plan),'source_order_reversal_rejected')
    bad=copy.deepcopy(batch);bad['predictions_or_reference_metrics_used_for_membership']=True
    reject(lambda:c.batch_membership(bad,plan),'prediction_selected_batch_rejected')
    full=dict(sources=[dict(source_id='P_SYN_'+str(i),video_id=str(i)) for i in range(426)])
    projection=c.source_video_projection(full);c.require(set(projection.values())==set(range(426)),'Automatic official video ID mapping differs')
    passed.append('one_to_one_source_hash_to_original_video_id_without_endpoint_rehash')
    bad=copy.deepcopy(full);bad['sources'][425]['video_id']='424'
    reject(lambda:c.source_video_projection(bad),'duplicate_official_video_identity_rejected')
    class Tokenizer:
        def decode(self,ids,skip_special_tokens=False,clean_up_tokenization_spaces=False):
            return ''.join('' if token==0 and skip_special_tokens else ('<EOS>' if token==0 else chr(token)) for token in ids)
    tokenizer=Tokenizer()
    def raw(text):
        ids=list(map(ord,text))+[0]
        return dict(actual_model_call=True,output_token_ids=ids,output_tokens=len(ids),generated_score_count=len(ids),
            selected_token_scores=[0.0]*len(ids),eos_token_ids=[0],raw_output=text,
            constraint_stats=dict(calls=len(ids),full_context_decodes=len(ids),dead_ends=0))
    points=[F(i,25) for i in range(250)];origin=F(17,3);dur={str(i):'1/25' for i in range(250)}
    clock=dict(original_exact_pts=[str(p+origin) for p in points],first_original_pts_exact=str(origin),
        normalized_exact_pts=list(map(str,points)),n_frames=250,physical_end_exact='10',last_frame_duration_exact='1/25',
        physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',last_normalized_pts_exact=str(points[-1]),last_frame_duration_exact='1/25'))
    event=dict(event_id='SYN_EVENT_001',original_case_id='SYN_CASE_001',original_segment_index=0,original_interval_exact=['0','4'])
    for side in ('start','end'):
        req=boundary.plan_endpoint(event,side,clock)
        req['continuity_by_sample'],req['original_endpoint_continuity_verified']=continuity(req,clock,dur)
        req.update(all_source_exact_pts=list(map(str,points)),native_duration_by_ordinal=dur)
        for text in ('{"decision":"KEEP"}','{"decision":"UNKNOWN"}'):
            decision=strict_tokens(tokenizer,raw(text),boundary.response_strings(req),[0])
            c.require(independent_endpoint(decision,req,clock)==boundary.resolve_endpoint(decision,req),'Independent endpoint unchanged result differs')
        index=next(index for index in req['allowed_sample_indices'] if index not in (0,63) and req['continuity_by_sample'][str(index)])
        text='{"decision":"REFINE","sample_index":'+str(index)+'}'
        decision=strict_tokens(tokenizer,raw(text),boundary.response_strings(req),[0])
        c.require(independent_endpoint(decision,req,clock)==boundary.resolve_endpoint(decision,req),'Independent native-exclusive/source-edge conversion differs')
    passed.append('strict_generated_tokens_and_independent_v3_endpoint_native_conversion')
    indices=[i*249//63 for i in range(64)]
    meta=dict(case_id=event['original_case_id'],source_name='SYN_SOURCE',source_sha256='a'*64,window_start='0',window_end='10',
        source_frame_ordinals=indices,sample_exact_pts=[str(points[i]) for i in indices],audio_observed=False,reference_available_to_inference=False)
    req=dict(meta,**verify.request(event,meta))
    for decision in ('KEEP','UNKNOWN','DROP'):
        text='{"decision":"'+decision+'"}';strict_tokens(tokenizer,raw(text),verify.responses(req),[0])
        c.require(independent_verify(req,text)==verify.resolve(text,req,execution_status='MODEL_OK'),'Independent VERIFY finite/native decision differs')
    passed.append('independent_VERIFY_KEEP_UNKNOWN_DROP_same_original_candidate')
    reject(lambda:verify.resolve('{"decision":"UNKNOWN"}',req,execution_status='MODEL_FAILURE'),'model_failure_not_UNKNOWN')
    bad=raw('{"decision":"UNKNOWN"}');bad['actual_model_call']=False
    reject(lambda:strict_tokens(tokenizer,bad,verify.responses(req),[0]),'fake_model_call_rejected')
    bad=raw('{"decision":"KEEP"}');bad['selected_token_scores'][0]='inf'
    reject(lambda:strict_tokens(tokenizer,bad,verify.responses(req),[0]),'nonfinite_generation_score_rejected')
    bad=raw('{"decision":"KEEP"}');bad['output_token_ids'][0]=0
    reject(lambda:strict_tokens(tokenizer,bad,verify.responses(req),[0]),'early_EOS_rejected')
    bad=raw('{"decision":"KEEP"}');bad['raw_output']='{"decision":"UNKNOWN"}'
    reject(lambda:strict_tokens(tokenizer,bad,verify.responses(req),[0]),'raw_vs_actual_token_mismatch_rejected')
    class Parameter:
        def __init__(self,n):self.n=n;self.requires_grad=False
        def numel(self):return self.n
    class Layer:
        disable_adapters=False;lora_A=True
    class Model:
        active_adapter='default'
        def __init__(self):
            self.layers=[Layer() for _ in range(144)];self.params=[('base',Parameter(c.BASE_PARAMETERS)),
                ('lora_A',Parameter(c.ADAPTER_PARAMETERS//2)),('lora_B',Parameter(c.ADAPTER_PARAMETERS//2))]
        def named_modules(self):return [('layer'+str(i),layer) for i,layer in enumerate(self.layers)]
        def named_parameters(self):return iter(self.params)
        def parameters(self):return [p for _,p in self.params]
        def requires_grad_(self,value):
            for _,p in self.params:p.requires_grad=value
            return self
    model=Model();names=c.layer_state(model,False)['layer_names'];c.inventory(model)
    for role in ('BASE_DISABLED','TIME_ENABLED','BASE_DISABLED'):
        disabled=role=='BASE_DISABLED'
        for layer in model.layers:layer.disable_adapters=disabled
        inside=c.layer_state(model,disabled,names);c.serialized_state(inside,disabled,names)
        # Simulated PEFT exit re-enables gradients on loaded adapter tensors.
        for layer in model.layers:layer.disable_adapters=False
        if disabled:
            for _,p in model.params[1:]:p.requires_grad=True
        gradient=c.restore_gradients(model);c.require(gradient['trainable_tensor_count_after_restore']==0,'Gradient restoration failed')
        c.inventory(model);c.layer_state(model,False,names)
    passed.append('PEFT_gradient_reenable_restored_for_BASE_TIME_BASE_roles')
    return dict(status='PASS_PURE_SYNTHETIC_RUNTIME_CONTRACT_NOT_PRODUCTION_ADMISSION',checks=passed,
        source_or_GT_reads=0,media_decodes=0,processor_encodes=0,tokenizer_asset_loads=0,actual_model_calls=0,
        actual_GPU_calls=0,cache_IO=0,actual_lease_accepts_or_releases=0,
        synthetic_raw_fields_are_fixture_only_not_actual_model_evidence=True)
