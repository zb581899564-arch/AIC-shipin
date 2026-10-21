"""Metadata adoption, first original-policy no-op scores, independent readout."""
import argparse
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
from unittest.mock import patch


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def save(p,value):
    with Path(p).open('x')as f:json.dump(value,f,indent=2,allow_nan=False)


CASE_KEYS={'uid','sid','role','request_ref','noop_source_ref','old_window_ref','suffix','answer','input_signature','counterfactual_input_signature'}


def validate_case(c):
    assert set(c)==CASE_KEYS and c['role']in ['fit','process'],'No supervision fields in model cases'
    assert isinstance(c['suffix'],list)and 0<len(c['suffix'])<=512 and all(type(t)is int and t>=0 for t in c['suffix'])
    assert isinstance(c['answer'],str)and c['answer']


def choose_native_group(actions,scores,baseline):
    assert len(actions)==len(scores)>0 and all(math.isfinite(v)for v in scores)
    return max(range(len(actions)),key=lambda j:(scores[j],-len(actions[j]^baseline),len(actions[j]&baseline),-j))


def checked(r,W):
    p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(W)and ref(p)==r;return p


def context(root):
    N=Path(root).resolve(strict=True);R=N.parent;W=R.parent;reg=json.loads((N/'registration31.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):return json.loads(checked(r,W).read_text())
    protocol=read(reg['protocol_ref']);oldreg=read(reg['registration19_ref']);coll=read(oldreg['train_collection_ref']);manifest=read(coll['asset_manifest_ref'])
    sys.path.insert(0,oldreg['prior_code_root'])
    from improvement.native_preference_v1 import inputs as inp
    class FastStore(inp.NativeInputStore):
        def _source_pixels(self,sid):
            def once(path,mode='rb',*args,**kwargs):
                assert mode=='rb';return io.BytesIO(gzip.decompress(Path(path).read_bytes()))
            with patch.object(inp.gzip,'open',once):return super()._source_pixels(sid)
    return N,R,W,reg,protocol,coll,manifest,FastStore,read


def prepare(root):
    N,R,W,reg,p,coll,manifest,Store,read=context(root);start=time.monotonic();support=read(reg['completion30_ref'])
    assert support['status']=='ELIGIBLE_FOR_SEPARATE_BASELINE_SCORE_AND_LOSS_REVIEW_ONLY'
    store=Store(manifest,'train');cases={};supported={};old_scores=0
    for role,refs in support['target_refs_by_role'].items():
        assert role in ['fit','process']
        for r in refs:
            target=read(r);sid=target['sid'];assert target['cohort']==role and sid in support['source_partition'][role]
            supported[sid]=True
            for w in target['windows']:
                uid=w['uid'];req=read(w['request_ref']);assert req==store.requests[uid]and req['sid']==sid
                for group in w['groups']:
                    for v in group['variants']:
                        if v['kind']=='OLD_ACCEPTED_SUFFIX':old_scores+=2;continue
                        assert v['kind']=='NEW_EXACT_BASELINE_NOOP'and v['model_score_unknown']and uid not in cases
                        raw=read(v['source_noop_ref']);row=next(q for q in raw['windows']if q['uid']==uid)
                        assert raw['complete_source_support']and raw['source_sha256']==req['source_sha256']
                        assert row['status']=='PASS_EXACT_BASELINE_NOOP_NATIVE_TOKEN_GRAMMAR'and row['new_native_action']
                        old=read(coll['window_refs'][uid]);assert old['input_signature']==req['input_signature']and old['labels_read']is False
                        assert 0<len(row['suffix'])<=512 and row['answer_tokens']==len(row['suffix'])
                        cases[uid]=dict(uid=uid,sid=sid,role=role,request_ref=w['request_ref'],noop_source_ref=v['source_noop_ref'],
                            old_window_ref=coll['window_refs'][uid],suffix=row['suffix'],answer=row['answer'],
                            input_signature=req['input_signature'],counterfactual_input_signature=old['counterfactual_input_signature'])
    store.close();assert cases and len(cases)*2<=p['maximum_new_logical_scores']
    for c in cases.values():validate_case(c)
    save(N/'cases31.json',cases)
    accepted=dict(status='PASS_METADATA_ONLY_FIRST_B_SCORE_TARGET_ADOPTION_31',cases_ref=ref(N/'cases31.json'),
        source_partition=support['source_partition'],supported_sources=sorted(supported),
        forced_unchanged_sources=[sid for values in support['source_partition'].values()for sid in values if sid not in supported],
        new_B_suffixes=len(cases),maximum_actual_forwards=2*len(cases),logical_scores=2*len(cases),old_logical_scores_adopted=old_scores,
        old_pixel_text_QA_adopted=True,new_four_tensor_QA_claimed=False,new_tokenization=0,new_decode=0,new_encode=0,
        model_case_has_labels=False,seconds=time.monotonic()-start,automatic_GPU=False)
    assert accepted['seconds']<p['maximum_CPU_prepare_seconds'];save(N/'acceptance31.json',accepted);print(json.dumps(accepted))


def gpu(root):
    N,R,W,reg,p,coll,manifest,Store,read=context(root);a=json.loads((N/'gpu_admission31.json').read_text())
    assert a['approved']and a['code_ref']==ref(__file__)
    accepted=read(a['acceptance_ref']);cases=read(accepted['cases_ref'])
    sys.path.insert(0,str(W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    from improvement.native_preference_v1.runtime import QwenPreferenceRuntime,canonical_frozen_hash,tensor_signature
    from improvement.content_choice_v1.runtime import permute_visual
    start=time.monotonic();events=N/'events31.jsonl'
    def event(kind,payload):
        with events.open('a')as f:f.write(json.dumps(dict(kind=kind,elapsed=time.monotonic()-start,**payload),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def budget(forward=False):assert time.monotonic()-start<p['maximum_GPU_seconds']
    runtime=QwenPreferenceRuntime(manifest['model_spec'],check_budget=budget,on_event=event);runtime.load()
    before=runtime._adapter_state();store=Store(manifest,'train');rows=[];cache={};adopted=0
    for uid,c in cases.items():
        validate_case(c)
        req,values,_=store.case(uid);assert req['input_signature']==c['input_signature']
        moved=permute_visual(values);assert tensor_signature(torch,moved)==c['counterfactual_input_signature']
        raw=dict(uid=uid,sid=c['sid'],role=c['role'],input_signature=c['input_signature'],counterfactual_input_signature=c['counterfactual_input_signature'],suffix=c['suffix'])
        for arm,v in [('real',values),('shifted',moved)]:
            event('BEGIN_FIRST_ORIGINAL_POLICY_B_SCORE',dict(uid=uid,arm=arm))
            key=(json.dumps(tensor_signature(torch,v),sort_keys=True),tuple(c['suffix']))
            if key in cache:
                value=cache[key];adopted+=1;event('B_SCORE_ADOPTED_IDENTICAL_CURRENT_INPUT',dict(uid=uid,arm=arm,logprob=value))
            else:
                value=runtime.score(v,c['suffix']);cache[key]=value
                event('B_SCORE_RAW_ACCEPTED',dict(uid=uid,arm=arm,logprob=value))
            assert math.isfinite(value);raw[arm]=value
        path=N/(uid+'_scores31.json');save(path,raw);rows.append(ref(path))
    store.close();assert runtime.counts['top_level_forward_calls']==runtime.counts['sequence_scores_completed']
    assert runtime.counts['top_level_forward_calls']+adopted==accepted['logical_scores']
    assert runtime.counts['backward_calls']==runtime.counts['optimizer_steps']==runtime.counts['generation_calls']==0
    after=runtime._adapter_state();assert len(before)==288 and all(torch.equal(before[k].view(torch.uint8),after[k].view(torch.uint8))for k in before)
    base_after=canonical_frozen_hash(runtime.model,torch);assert base_after==runtime.base_before
    runtime._original_files();runtime._inventory(False)
    save(N/'gpu_completion31.json',dict(status='ENGINEERING_COMPLETE_ORIGINAL_TIME_NEW_B_SCORES_ONLY',score_refs=rows,
        actual_forwards=runtime.counts['top_level_forward_calls'],adopted_identical_scores=adopted,logical_scores=accepted['logical_scores'],
        counts=dict(runtime.counts),new_updates=0,new_backwards=0,new_generations=0,original288TIME_bytes_frozen=True,
        base_before=runtime.base_before,base_after=base_after,seconds=time.monotonic()-start,labels_read=False,production_admitted=False))


def review(root):
    import numpy as np
    N,R,W,reg,p,coll,manifest,Store,read=context(root);accepted=read(ref(N/'acceptance31.json'));cases=read(accepted['cases_ref']);support=read(reg['completion30_ref'])
    done=read(ref(N/'gpu_completion31.json'));assert done['base_before']==done['base_after']and done['original288TIME_bytes_frozen']
    assert done['actual_forwards']+done['adopted_identical_scores']==accepted['logical_scores']
    scores={v['uid']:v for r in done['score_refs']for v in [read(r)]};assert set(scores)==set(cases)
    for uid,s in scores.items():
        c=cases[uid];assert s['suffix']==c['suffix']and s['input_signature']==c['input_signature']and s['counterfactual_input_signature']==c['counterfactual_input_signature']
        assert all(math.isfinite(s[a])for a in ['real','shifted'])
    store=Store(manifest,'train');target_by_sid={t['sid']:t for rr in support['target_refs_by_role'].values()for r in rr for t in [read(r)]};rows=[]
    def utility(selected,labels):
        selected=sorted(selected);tp=labels[selected].sum(axis=0,dtype=np.int64);den=len(selected)+labels.sum(axis=0,dtype=np.int64)
        return float(np.divide(2.*tp,den,out=np.ones_like(tp,dtype=float),where=den!=0).mean())
    for role,ids in accepted['source_partition'].items():
        for sid in ids:
            human=store.source_supervision(sid);n=len(human['clock']['normalized_exact_pts']);B=set(human['baseline']);labels=np.zeros((n,len(human['raters'])),bool)
            assert all(len(mask)==n and all(mask)for mask in human['known_masks'])
            for j,truth in enumerate(human['raters']):labels[sorted(truth),j]=True
            baseline=utility(B,labels)
            if sid not in target_by_sid:
                assert sid in accepted['forced_unchanged_sources']
                rows.append(dict(sid=sid,role=role,forced_B=True,baseline_F1=baseline,arms={a:dict(F1=baseline,added=0,deleted=0,ambiguous_windows=0)for a in ['real','shifted','uniform']}));continue
            target=target_by_sid[sid];assert target['cohort']==role and target['source_sha256']==human['source_sha256'];arms={}
            for arm in ['real','shifted','uniform']:
                selected=set();old_selected=set();statistics=[];total_score=0.;witness_score=0.
                for wi,w in enumerate(target['windows']):
                    aa=[];ll=[];old_aa=[];old_ll=[];lens=[]
                    for group in w['groups']:
                        variants=[];native=None;lengths=[]
                        for v in group['variants']:
                            if v['kind']=='OLD_ACCEPTED_SUFFIX':
                                raw=read(v['window_ref'])['slots'][v['slot']];current=set(raw['selected_ordinals']);lp=v['original_'+arm+'_logp']if arm!='uniform'else 0.
                                old_aa.append(current);old_ll.append(lp);lengths.append(len(raw['ids']))
                            else:
                                raw_source=read(v['source_noop_ref']);raw=next(r for r in raw_source['windows']if r['uid']==w['uid']);current=set(raw['selected_ordinals'])
                                lp=scores[w['uid']][arm]if arm!='uniform'else 0.;lengths.append(len(raw['suffix']))
                            if native is None:native=current
                            assert native==current;variants.append(lp)
                        aa.append(native);ll.append(max(variants));lens.append(lengths)
                    j=choose_native_group(aa,ll,B);selected|=aa[j];total_score+=ll[j]
                    k=choose_native_group(old_aa,old_ll,B);old_selected|=old_aa[k]
                    witness_score+=ll[target['one_witness_program'][wi]]
                    sorted_scores=sorted(ll,reverse=True);margin=sorted_scores[0]-sorted_scores[1]if len(ll)>1 else None
                    statistics.append(dict(uid=w['uid'],winner_native_group=j,baseline_group=w['baseline_group'],winner_score=ll[j],baseline_score=ll[w['baseline_group']],
                        winner_margin=margin,ambiguous=margin is not None and margin<=1e-6,variant_token_lengths=lens))
                if arm=='uniform':assert selected==B,'Same-score retention ties must reconstruct B'
                arms[arm]=dict(F1=utility(selected,labels),old_noB_F1=utility(old_selected,labels),delta_vs_B=utility(selected,labels)-baseline,
                    delta_vs_same_old_pool=utility(selected,labels)-utility(old_selected,labels),selected_frames=len(selected),added=len(selected-B),deleted=len(B-selected),
                    changed_by_B_action=len(selected^old_selected),ambiguous_windows=sum(r['ambiguous']for r in statistics),
                    total_MAP_logp=total_score,witness_logp=witness_score,witness_minus_MAP_logp=witness_score-total_score,windows=statistics)
            rows.append(dict(sid=sid,role=role,forced_B=False,baseline_F1=baseline,reference_witness_F1=target['witness_F1'],arms=arms))
    store.close();macro={}
    for role in ['fit','process']:
        rr=[r for r in rows if r['role']==role];assert len(rr)==4
        macro[role]=dict(baseline_F1=float(np.mean([r['baseline_F1']for r in rr])),forced_B=sum(r['forced_B']for r in rr),arms={a:dict(F1=float(np.mean([r['arms'][a]['F1']for r in rr])),
            changed_sources=sum(bool(r['arms'][a]['added']or r['arms'][a]['deleted'])for r in rr),ambiguous_windows=sum(r['arms'][a]['ambiguous_windows']for r in rr))for a in ['real','shifted','uniform']})
    save(N/'review31.json',dict(status='COMPLETE_BASELINE_INCLUSIVE_ORIGINAL_POLICY_DIAGNOSTIC_NOT_TRAINING_ADMISSION',macro=macro,rows=rows,
        score_token_native_QA='PASS_ALL_NEW_B_SCORES_AND_FULL_SOURCE_READOUT_31',old_scores_adopted=True,new_model_calls_in_review=0,new_updates=0,
        all_highest_model_score_gold_programs='UNKNOWN_NOT_SOLVED',automatic_training=False,production_admitted=False,new_ZIP=0,official_submissions=0))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['prepare','gpu','review'],required=True);ap.add_argument('--run-root',required=True);args=ap.parse_args()
    try:globals()[args.phase](args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'31.json'),dict(status='ACTUAL_FAILURE_PRESERVED_NO_EMPTY_OR_AUTOMATIC_RETRY',traceback=traceback.format_exc()));raise
