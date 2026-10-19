"""First independent token/grammar/native QA after one natural GPU terminal."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from summary_output import parse_summary
from summary_grammar6 import BoundedSegmentsGrammar

W = Path('/home/inspur/aic_video_work')
ROOT = W/'bottleneck_24h_20261019_v1/summary_objective_v20'
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def read(p):return json.loads(Path(p).read_text())


def ref(p):
    p = Path(p)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def bound(r):
    p = Path(r['path']).resolve()
    if not p.is_relative_to(W) or not p.is_file() or ref(p)['sha256'] != r['sha256']:
        raise ValueError('QA bound reference changed/outside work root')
    return p


def run(role):
    reg = read(ROOT/'summary_generation_registration_10.json')
    resource = RUN/'controller'/(reg['job_names'][role]+'.resource.json')
    terminal = read(resource)
    ledger = [json.loads(x) for x in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if x.strip() and json.loads(x).get('name') == reg['job_names'][role]]
    assert terminal['status'] == 'completed' and terminal['exit_code'] == 0 and ledger == [terminal], 'Unique natural terminal/ledger required'
    folder = ROOT/'summary_generation_10'/role
    completion = read(folder/'completion.json')
    assert completion['status'] == 'PASS_ALL43_MATCHED_SUMMARY_GENERATIONS' and completion['model_role'] == role
    assert completion['optimizer_updates'] == 0 and completion['old_TIME_unchanged']
    assert completion['inventory']['conservative_pipeline_parameters'] == 8797892873 <= 9000000000
    if role == 'INIT_TIME':weight_ref = reg['initial_TIME_ref']
    else:weight_ref = read(ROOT/'summary_final_weights_frozen_10.json')['final_adapter_ref']
    assert completion['model_weights_ref'] == weight_ref
    bound(weight_ref)
    gate = read(bound(reg['first_dev_input_acceptance_ref']))
    prepared = read(bound(gate['prepared']))
    expected = {read(bound(r))['uid']:r for r in prepared['inputs']}
    assert len(expected) == len(completion['outputs']) == 43
    from transformers import AutoTokenizer
    cfg = read(bound(reg['model_config_ref']))
    tok = AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    eos = tok.convert_tokens_to_ids('<|im_end|>'); assert eos == 151645
    details = []; seen = set(); clocks = {}
    for reference in completion['outputs']:
        output = read(bound(reference)); uid = output['uid']
        assert uid not in seen and output['model_role'] == role and output['model_weights_ref'] == weight_ref
        assert output['request_ref'] == expected[uid]; seen.add(uid)
        request = read(bound(output['request_ref'])); assert output['sid'] == request['sid']
        ids = output['generated_ids']
        assert ids and ids[-1] == eos and eos not in ids[:-1] and all(type(x) is int and x >= 0 for x in ids)
        raw = read(bound(output['raw_token_ref']))
        assert all(raw[k] == output[k] for k in ('uid','sid','request_ref','generated_ids','model_role','model_weights_ref'))
        text = tok.decode(ids[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        assert text == output['raw_text']
        start, end = F(request['plan']['window_start_exact']), F(request['plan']['window_end_exact'])
        assert BoundedSegmentsGrammar(end-start,max_segments=6,allow_empty=True).complete(text)
        segments = parse_summary(text,end-start)
        assert [[str(a),str(b)]for a,b in segments] == output['parsed_exact_segments']
        if request['sid'] not in clocks:
            c = read(bound(request['source_clock_ref'])); clocks[request['sid']] = c
        c = clocks[request['sid']]; points = list(map(F,c['normalized_exact_pts']))
        assert c['source_sha256'] == request['source_sha256'] and 0 <= start < end <= F(c['physical_end_exact'])
        ranges = []
        for a,b in segments:
            lo,hi = bisect_left(points,start+a),bisect_left(points,start+b)
            assert 0 <= lo <= hi <= len(points)
            assert all(start+a <= points[i] < start+b for i in range(lo,hi))
            ranges.append([lo,hi])
        details.append(dict(uid=uid,sid=request['sid'],native_ranges=ranges,
            selected_native_frames=sum(b-a for a,b in ranges),valid_empty_JSON=not segments,
            segments_without_native_frames=sum(a==b for a,b in ranges),output_ref=reference))
    assert seen == set(expected) and len(clocks) == 8
    path = folder/'first_independent_output_QA.json'
    with path.open('x') as f:
        json.dump(dict(status='PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA',model_role=role,
            outputs=completion['outputs'],resource_ref=ref(resource),completion_ref=ref(folder/'completion.json'),
            unique_ledger_equal=True,sources=8,windows=43,invalid_outputs=0,details=details,
            no_model_replay=True,no_media_or_processor=True,reference_labels_read=False),f,indent=2)
    print(json.dumps(dict(status='PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA',model_role=role,windows=43)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--role',choices=['INIT_TIME','TRAINED'],required=True)
    run(p.parse_args().role)
