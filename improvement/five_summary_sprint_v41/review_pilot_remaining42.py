"""Explicit remaining CPU adoption of43 raw outputs after known post-context failure; old GPU remains FAILED."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
from bisect import bisect_left
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import numpy as np
from summary_generate import read, bound, ref, save, RUN, W
from summary_contract import require
from summary_output import parse_summary
from summary_grammar6 import BoundedSegmentsGrammar
from evaluate_summary import load_requests, load_sources, native_interval_mask, metric


def run(path):
    reg = read(path); root = Path(reg['root']); folder = root/'pilot_BASE43'
    resource = RUN/'controller'/(reg['job_name']+'.resource.json')
    terminal = read(resource)
    ledger = [json.loads(line) for line in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip() and json.loads(line).get('name') == reg['job_name']]
    require(terminal['status'] == 'failed' and terminal['exit_code'] == 1 and ledger == [terminal], 'Original actual FAILED terminal is preserved')
    adoption = read(root/'pilot_raw_adoption42.json')
    require(bound(adoption['review_code_ref']) == Path(__file__).resolve(), 'Explicit remaining review code binding')
    failure = read(bound(adoption['original_model_failure_ref']))
    require(adoption['status'] == 'EXPLICIT_RAW43_DEVELOPMENT_ONLY_AFTER_CONTEXT_EXIT_FAILURE_42' and
        adoption['new_GPU_calls'] == 0 and failure['error'] == "ValueError('Inference parameters frozen')" and
        'flags(model, False)' in failure['traceback'] and len(failure['outputs']) == 43 and
        len(failure['raw_records']) == 43, 'Only actual complete43 original raw after this exact late failure')
    completion = dict(outputs=failure['outputs'])
    gate = read(bound(reg['first_dev_input_acceptance_ref'])); prepared = read(bound(gate['prepared']))
    manifest = dict(dev_prepared_ref=gate['prepared'], baseline_human_adoption_ref=reg['baseline_human_adoption_ref'])
    _, requests = load_requests(manifest); sources = load_sources(manifest, requests)
    from transformers import AutoTokenizer
    cfg = read(bound(reg['model_config_ref'])); tok = AutoTokenizer.from_pretrained(cfg['model_dir'], local_files_only=True)
    eos = tok.convert_tokens_to_ids('<|im_end|>'); require(eos == 151645, 'Actual EOS')
    seen = set(); details = []; parsed_base = {}
    for reference in completion['outputs']:
        output = read(bound(reference)); uid = output['uid']; item = requests[uid]; request = item['request']
        require(uid not in seen and output['request_ref'] == item['request_ref'] and output['model_role'] == 'BASE' and
                output['sid'] == request['sid'] and output['model_weights_ref'] == reg['initial_TIME_ref'] and
                output['role_flags'] == dict(layers=144, disabled=True, active_name='summary'), 'Identity/forward flags')
        seen.add(uid); ids = output['generated_ids']; raw = read(bound(output['raw_token_ref']))
        require(ids and ids[-1] == eos and eos not in ids[:-1] and all(type(x) is int and x >= 0 for x in ids), 'Natural token terminal')
        require(all(raw[k] == output[k] for k in ('uid','sid','request_ref','generated_ids','model_role','model_weights_ref','role_flags')), 'Raw token binding')
        text = tok.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        require(text == output['raw_text'] and BoundedSegmentsGrammar(item['end']-item['start'], max_segments=6, allow_empty=True).complete(text), 'Independent token/grammar')
        intervals = parse_summary(text, item['end']-item['start'])
        require([[str(a),str(b)] for a,b in intervals] == output['parsed_exact_segments'], 'Independent exact parser')
        absolute = [(item['start']+a,item['start']+b) for a,b in intervals]
        points = sources[output['sid']]['points']
        ranges = [[bisect_left(points,a),bisect_left(points,b)] for a,b in absolute]
        require(all(0 <= a < b <= sources[output['sid']]['end'] for a,b in absolute), 'Exact native source domain')
        parsed_base[uid] = absolute
        details.append(dict(uid=uid,sid=output['sid'],native_ranges=ranges,valid_empty=not intervals,output_ref=reference))
    require(seen == set(requests), 'Every43 output exactly once')
    qa_path = root/'first_independent_partial_output_QA42.json'
    save(qa_path, dict(status='PASS_RAW43_FIRST_OUTPUT_QA42_OLD_GPU_FAILED', outputs=completion['outputs'], windows=43,sources=8,
        original_model_failure_ref=adoption['original_model_failure_ref'],raw_adoption_ref=ref(root/'pilot_raw_adoption42.json'),resource_ref=ref(resource),unique_ledger_equal=True,original_GPU_status='failed',post_generation_base_hash_not_executed=True,
        invalid_outputs=0, details=details, no_model_replay=True, labels_read=False))
    # Existing TIME QA is adopted, not replayed; human NPZ opens only after BASE QA.
    oldqa = read(bound(reg['adopted_TIME_output_QA_ref'])); old = read(bound(reg['adopted_TIME_completion_ref']))
    require(oldqa['status'] == 'PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA' and
            oldqa['outputs'] == old['outputs'] and old['model_role'] == 'INIT_TIME', 'Actual adopted43 TIME firstQA')
    time_intervals = {sid:[] for sid in sources}
    for reference in old['outputs']:
        o = read(bound(reference)); item = requests[o['uid']]
        require(o['request_ref'] == item['request_ref'], 'Same adopted TIME input')
        time_intervals[o['sid']].extend((item['start']+F(a),item['start']+F(b)) for a,b in o['parsed_exact_segments'])
    rows = []
    for sid, data in sources.items():
        with np.load(bound(data['source']['data_ref']), allow_pickle=False) as npz:
            B, labels = npz['baseline'], npz['labels']
        T = native_interval_mask(data['points'],time_intervals[sid])
        C = native_interval_mask(data['points'],[iv for uid,ivs in parsed_base.items() if requests[uid]['request']['sid']==sid for iv in ivs])
        masks = dict(B=B,T=T,C=C,P1=B|(T&C),P2=B&(T|C),P3=T,P4=C,P5=(B&(T|C))|(T&C))
        require(B.dtype == np.bool_ and labels.dtype == np.bool_ and len(B)==len(data['points']) and labels.shape[0]==len(B), 'Original full native human domain')
        rows.append(dict(sid=sid, metrics={name:metric(mask,labels) for name,mask in masks.items()},
            differences={name:dict(added=int((mask&~B).sum()),removed=int((B&~mask).sum())) for name,mask in masks.items()}))
    names = ('B','T','C','P1','P2','P3','P4','P5')
    macro = {name:dict(**{k:float(np.mean([r['metrics'][name][k] for r in rows])) for k in ('precision','recall','f1','native_frame_coverage')},
        empty_sources=sum(r['metrics'][name]['prediction_empty'] for r in rows),
        selected_native_frames=sum(r['metrics'][name]['selected_native_frames'] for r in rows)) for name in names}
    # Deliberately broad predeclared collapse check, not the old proxy-F1 promotion gate.
    broad = (macro['C']['empty_sources'] <= reg['collapse_check']['maximum_empty_sources'] and
        macro['C']['f1'] >= reg['collapse_check']['minimum_fraction_baseline_f1']*macro['B']['f1'] and
        macro['C']['recall'] >= reg['collapse_check']['minimum_fraction_baseline_recall']*macro['B']['recall'])
    result = dict(status='COMPLETE_RAW43_EXPOSED_DEVELOPMENT_REVIEW42_OLD_GPU_FAILED', macro=macro,sources=rows,
        baseline_40_47_unchanged=True,first_BASE_output_QA_ref=ref(qa_path),
        broad_collapse_check_pass=bool(broad), collapse_check=reg['collapse_check'],
        historical_exposed_development=True,blind_test=False,official_joint_score=None,
        new_fit=0,optimizer_updates=0,adopted_TIME_calls=43,new_BASE_calls=43,
        old_proxy_F1_hard_gate_restored=False,automatic_production_admission=False,
        source_equal_all_original_raters=True,unselected_reference_is_not_ordinary=True,
        production_allowed=False)
    result.update(original_GPU_status='failed',original_failure_ref=adoption['original_model_failure_ref'],raw_adoption_ref=ref(root/'pilot_raw_adoption42.json'),post_generation_base_hash_not_executed=True,new_BASE_calls=0,adopted_failed_job_raw_calls=43)
    save(root/'pilot_comparison42.json', result)
    print(json.dumps(dict(status=result['status'],macro=macro,broad_collapse_check_pass=bool(broad))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--registration',required=True)
    run(p.parse_args().registration)
