"""First external protected-baseline no-op action representation audit."""
import hashlib
import json
from pathlib import Path
import sys
import time
from fractions import Fraction


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    import torch
    N=Path(__file__).resolve().parent;R=N.parent;W=R.parent;started=time.monotonic()
    reg=json.loads((N/'registration28.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):
        p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(W)and ref(p)==r;return json.loads(p.read_text())
    protocol=read(reg['protocol_ref']);oldreg=read(reg['registration19_ref']);sys.path.insert(0,oldreg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    from improvement.native_preference_v1.preference import selection_answer,window_bounds,contiguous_runs,CandidateRepresentationError,parse_answer,native_selection
    from improvement.native_preference_v1.runtime import load_tokenizer,tokenize_answer
    from improvement.native_preference_v1.run import grammar_module,validate_token_path
    summaries={};outputs=[];tokenizer=None
    for scope in ['train','check']:
        coll=read(oldreg[scope+'_collection_ref']);manifest=read(coll['asset_manifest_ref']);store=NativeInputStore(manifest,scope)
        if tokenizer is None:
            tokenizer=load_tokenizer(manifest['model_spec']);grammar=grammar_module(manifest);vocabulary=frozenset(grammar.ascii_token_candidates(tokenizer))
        sources=[]
        for sid in store.source_ids:
            human=store.source_supervision(sid);clock=human['clock']['normalized_exact_pts'];baseline=set(human['baseline']);union=set();rows=[]
            assert human['source_sha256']==coll['sources'][sid]['source_sha256']
            for uid in coll['sources'][sid]['window_ids']:
                req=store.requests[uid];plan=req['plan'];start,end=plan['window_start_exact'],plan['window_end_exact']
                lo,hi=window_bounds(clock,start,end);selected={i for i in baseline if lo<=i<hi};union|=selected
                row=dict(uid=uid,source_sha256=human['source_sha256'],request_ref=store.request_refs[uid],selected_ordinals=sorted(selected),
                    selected_frames=len(selected),native_runs=len(contiguous_runs(selected)),model_calls=0,labels_enter_tokenizer=False)
                old=read(coll['window_refs'][uid]);assert old['input_signature']==req['input_signature']and old['labels_read']is False
                matches=[c['slot']for c in old['slots']if set(c['selected_ordinals'])==selected]
                if matches:
                    # These exact native actions and complete tokens already passed the old QA.
                    chosen=max((c for c in old['slots']if c['slot']in matches),key=lambda c:c['real']['logprob'])
                    row.update(status='PASS_ADOPTED_EXISTING_EXACT_NATIVE_NOOP',old_window_ref=coll['window_refs'][uid],
                        old_native_equal_slots=matches,adopted_slot=chosen['slot'],answer=chosen['text'],suffix=chosen['ids'],
                        answer_tokens=len(chosen['ids']),new_native_action=False,old_grammar_QA_adopted=True)
                    rows.append(row);continue
                try:
                    answer=selection_answer(selected,clock,start,end)
                except CandidateRepresentationError as exc:
                    row.update(status='UNSUPPORTED_FIXED_NATIVE_ANSWER_CONTRACT',reason=str(exc));rows.append(row);continue
                # Only the tiny already-accepted text-prefix tensor is read. No store.case/pixels.
                p=Path(req['prefix_ref']['path']);assert ref(p)==req['prefix_ref']
                prefix=torch.load(p,map_location='cpu',weights_only=True)
                assert Path(uid).name==uid
                with(N/(uid+'_answer_before28.json')).open('x')as f:json.dump(dict(answer=answer,selected_ordinals=sorted(selected),request_ref=store.request_refs[uid]),f,indent=2)
                suffix=tokenize_answer(tokenizer,prefix,answer)
                with(N/(uid+'_suffix_before28.json')).open('x')as f:json.dump(dict(answer=answer,suffix=suffix,request_ref=store.request_refs[uid]),f,indent=2)
                validate_token_path(tokenizer,suffix,answer,Fraction(end)-Fraction(start),grammar,vocabulary)
                reconstructed=native_selection(parse_answer(answer,Fraction(end)-Fraction(start)),clock,start,end)
                assert reconstructed==selected
                row.update(status='PASS_EXACT_BASELINE_NOOP_NATIVE_TOKEN_GRAMMAR',answer=answer,suffix=suffix,
                    prefix_tokens=int(prefix['input_ids'].shape[1]),answer_tokens=len(suffix),old_native_equal_slots=matches,
                    new_native_action=not bool(matches));rows.append(row)
                assert time.monotonic()-started<protocol['maximum_CPU_seconds']
            assert union==baseline
            passed=all(r['status'].startswith('PASS_')for r in rows)
            path=N/(scope+'_'+sid+'_noops28.json')
            with path.open('x')as f:json.dump(dict(sid=sid,scope=scope,source_sha256=human['source_sha256'],complete_source_support=passed,
                reconstructed_baseline_frames=len(union),source_baseline_frames=len(baseline),windows=rows),f,indent=2,allow_nan=False)
            outputs.append(ref(path));sources.append(dict(sid=sid,full_source_support=passed,windows=len(rows),
                supported_windows=sum(r['status'].startswith('PASS_')for r in rows),new_native_actions=sum(r.get('new_native_action',False)for r in rows),
                unsupported=[dict(uid=r['uid'],native_runs=r['native_runs'],reason=r['reason'])for r in rows if not r['status'].startswith('PASS_')]))
        store.close();summaries[scope]=dict(sources=len(sources),windows=sum(r['windows']for r in sources),
            full_source_support=sum(r['full_source_support']for r in sources),supported_windows=sum(r['supported_windows']for r in sources),
            distinct_new_native_actions=sum(r['new_native_actions']for r in sources),rows=sources)
    value=dict(status='EXTERNAL_BASELINE_NOOP_REPRESENTATION_ONLY_NOT_SELECTOR_ADMISSION',summary=summaries,outputs=outputs,
        seconds=time.monotonic()-started,new_model_calls=0,new_updates=0,new_fits=0,media_or_image_tensors_read=False,
        official_predictions_or_GT_read=False,baseline_labels_used_for_loss=False,automatic_GPU=False,new_ZIP=0,official_submissions=0)
    with(N/'completion28.json').open('x')as f:json.dump(value,f,indent=2,allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(N/'completion28.json'),summary={k:v for k,v in value.items()if k not in ['outputs','summary']}|
        dict(cohorts={k:{a:b for a,b in v.items()if a!='rows'}for k,v in summaries.items()}))))


if __name__=='__main__':main()
