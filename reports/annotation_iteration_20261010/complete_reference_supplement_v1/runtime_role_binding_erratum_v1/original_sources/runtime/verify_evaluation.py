"""Independent CPU reconstruction of all24 final-only evaluation answers.

Reuses completed native CPU input receipts byte-exactly. Does not load a model,
decode another video or turn a failed response into an empty interval.
"""
import argparse
import math
from pathlib import Path
from fractions import Fraction as F
from common import admit, bound, load, read, require, save, sha, verify_lock
from evaluate import validate_final
from objective import classify
from native_runtime import native_ranges
from scientific_gate import summarize, gate


def reconstruct(contract, evaluation_path, expected_evaluation_sha, training_path, expected_training_sha):
    final, training = validate_final(contract, training_path, expected_training_sha)
    ep = Path(evaluation_path).resolve(strict=True)
    folder = Path(contract['config']['evaluate_output_dir']).resolve(strict=True)
    require(ep == folder/'evaluation_receipt.json' and sha(ep) == expected_evaluation_sha,
            'foreign/changed evaluation receipt')
    evaluation = read(ep)
    require(evaluation['status'] == 'PASS_FINAL_ONLY_EVALUATION_ENGINEERING' and evaluation['final_only'] is True and
            evaluation['model_calls'] == 24 and evaluation['lock_sha256'] == contract['lock_sha'] and
            evaluation['config_sha256'] == contract['config_sha'] and
            evaluation['final_training_receipt_sha256'] == expected_training_sha,
            'complete final-only evaluation engineering absent')
    preflight = read(bound(training['native_cpu_preflight_receipt']))
    require(preflight['status'] == 'PASS_ACTUAL_CPU_NATIVE_PROCESSOR_AND_ASSISTANT_TARGET_PARITY_NOT_TRAINING' and
            preflight['lock_sha256'] == contract['lock_sha'] and preflight['config_sha256'] == contract['config_sha'] and
            preflight['model_loaded'] is False and preflight['cuda_initialized'] is False,
            'actual completed CPU input parity absent')
    input_rows = {r['window_id']: r for r in preflight['rows']}
    require(len(input_rows) == len(preflight['rows']), 'duplicate preflight window')
    run = Path(contract['config']['historical_run_root'])
    parser = load(run/'teacher_student_autopilot_v14/precision_helpers/contracts.py', 'independent_eval_parser')
    grammar = load(run/'teacher_student_autopilot_v14/precision_helpers/constrained_json.py', 'independent_eval_grammar')
    from transformers import AutoTokenizer
    import torch
    require(not torch.cuda.is_initialized(), 'independent CPU reconstruction unexpectedly initialized CUDA')
    tokenizer = AutoTokenizer.from_pretrained(contract['config']['processor_dir'],local_files_only=True)
    eos = read(Path(contract['config']['model_dir'])/'generation_config.json')['eos_token_id']
    candidates = grammar.ascii_token_candidates(tokenizer)
    keys = contract['config']['final_only_evaluation_window_ids']
    require(len(keys) == 12 and len(set(keys)) == 12, 'fixed evaluation denominator differs')
    predictions = {}; bindings = []
    for arm, adapter in (('original_B', Path(contract['config']['initial_adapter_dir'])), ('new_final', final)):
        expected_adapter_sha = sha(adapter/'adapter_model.safetensors')
        arm_folder = folder/arm
        require(len(list(arm_folder.glob('*.done.json'))) == len(list(arm_folder.glob('*.raw.json'))) == 12 and
                not list(arm_folder.glob('*.failure.json')), 'arm actual raw/done denominator or failure differs')
        predictions[arm] = {}
        for i, key in enumerate(keys):
            dp = arm_folder/('%02d.done.json'%i); done = read(dp)
            rp = Path(done['raw_receipt']).resolve(strict=True)
            require(rp == (arm_folder/('%02d.raw.json'%i)).resolve(strict=True) and sha(rp) == done['raw_sha256'],
                    'raw identity differs')
            require(done['window_id'] == key and done['arm'] == arm and done['adapter_sha256'] == expected_adapter_sha and
                    done['reference_sha256'] == contract['reference_sha'][key], 'answer arm/window/reference differs')
            raw = read(rp); w = contract['jobs'][key]['window']; duration = F(w['domain_end_exact'])-F(w['domain_start_exact'])
            require(raw['actual_model_call'] is True and raw['window'] == w, 'actual call/window declaration differs')
            detail = read(bound(input_rows[key]['input_receipt']))
            require(detail['window_id'] == key and detail['actual_native_and_reviewed_processor_equal'] is True and
                    detail['training_target_present'] is False and raw['video_identity'] == detail['evidence'],
                    'actual generation input differs from independently completed CPU preflight')
            ids = raw['output_token_ids']; scores = raw['selected_token_scores']
            require(1 <= len(ids) == len(scores) <= 256 and all(type(t) is int and t >= 0 for t in ids) and
                    all(type(s) in (int,float) and math.isfinite(s) for s in scores), 'actual generated tokens/scores invalid')
            require(raw['input_tokens'] == detail['evidence']['processor_identity']['input_tokens'] and
                    raw['input_tokens'] <= 16384, 'actual input token count differs')
            require(tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False) == raw['raw_output'],
                    'actual generated token identities do not decode to saved raw')
            constraint = grammar.make_prefix_constraint(tokenizer,raw['input_tokens'],duration,
                candidate_token_ids=candidates,eos_token_ids=eos,allow_empty=True)
            constraint.assert_complete(ids)
            require(grammar.BoundedSegmentsGrammar(duration,allow_empty=True).complete(raw['raw_output']),
                    'original grammar rejects actual raw')
            parsed, errors, warnings = parser.parse_segments(raw['raw_output'],duration,allow_empty=True)
            require(parsed is not None and not errors, 'original parser rejects actual raw')
            result = classify(raw['raw_output'],duration)
            require(result['status'] in ('MODEL_OK','LEGAL_EMPTY') and
                    result['parsed_segments'] == [[F(str(a)),F(str(b))] for a,b in parsed], 'exact/original parser mismatch')
            exact_saved = [[F(a),F(b)] for a,b in done['parsed_segments']]
            require(result['status'] == done['status'] and result['parsed_segments'] == exact_saved and
                    native_ranges(result['parsed_segments'],w) == done['native_frame_ranges'] and
                    done['parse_warnings'] == warnings, 'saved GPU acceptance differs from independent parser/native selection')
            predictions[arm][key] = result
            bindings.append(dict(window_id=key,arm=arm,adapter_sha256=expected_adapter_sha,
                done=dict(path=str(dp),sha256=sha(dp)),raw=dict(path=str(rp),sha256=sha(rp)),
                completed_input_receipt=input_rows[key]['input_receipt']))
    summaries = {arm: {role: summarize(contract['jobs'],contract['refs'],
        {k:r for k,r in rows.items() if contract['jobs'][k]['role'] == role},
        contract['quality'],contract['events'],role)
        for role in ('process_dev','locked_development_evaluation')}
        for arm,rows in predictions.items()}
    b,n = summaries['original_B'],summaries['new_final']
    scientific = gate(b['process_dev'],n['process_dev'],b['locked_development_evaluation'],n['locked_development_evaluation'],contract['quality'])
    original_gate = folder/'scientific_gate.json'
    require(sha(original_gate) == evaluation['scientific_gate_sha256'], 'original quality gate SHA differs')
    # JSON is compared by its exact rational representation, not float tolerances.
    import json
    encode = lambda x: json.loads(json.dumps(x,default=lambda v:str(v) if isinstance(v,F) else (_ for _ in ()).throw(TypeError(type(v).__name__))))
    require(encode(scientific) == read(original_gate) and encode(summaries) == evaluation['summaries'] and
            evaluation['quality_gate_passed'] == (scientific['status'] == 'PASS_FIXED_SILVER_QUALITY_GATE'),
            'independent full scientific reconstruction differs')
    verify_lock(contract['lock_path'],contract['lock_sha'])
    require(not torch.cuda.is_initialized(), 'independent CPU reconstruction initialized CUDA')
    return dict(status='PASS_INDEPENDENT_CPU_FINAL_ONLY_EVALUATION_RECONSTRUCTION',
        scientific_status=scientific['status'],quality_gate_passed=scientific['status'] == 'PASS_FIXED_SILVER_QUALITY_GATE',
        model_calls_reconstructed=24,new_model_calls=0,new_optimizer_updates=0,new_native_decodes=0,
        actual_completed_CPU_inputs_referenced=True,config_sha256=contract['config_sha'],lock_sha256=contract['lock_sha'],
        training_receipt=dict(path=str(Path(training_path).resolve()),sha256=expected_training_sha),
        evaluation_receipt=dict(path=str(ep),sha256=expected_evaluation_sha),
        final_adapter_sha256=training['final_adapter_sha256'],bindings=bindings,scientific_gate=scientific,
        quality_scope='FINITE_OBSERVATION_SILVER_DIAGNOSTIC_NOT_GOLD_OR_OFFICIAL')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','lock','expected-lock','evaluation-receipt','expected-evaluation-receipt',
                 'final-receipt','expected-final-receipt','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();contract=admit(a.config,a.lock,a.expected_lock,'candidate')
    output=Path(a.output).resolve()
    require(output.parent == Path(contract['config']['evaluate_output_dir']).resolve(), 'independent output must stay in evaluation directory')
    require(not output.exists(), 'independent successful CPU result must never be repeated')
    result=reconstruct(contract,a.evaluation_receipt,a.expected_evaluation_receipt,a.final_receipt,a.expected_final_receipt)
    save(output,result)
    print(__import__('json').dumps({k:result[k] for k in ('status','scientific_status','quality_gate_passed','model_calls_reconstructed','new_model_calls')}))
    return 0 if result['quality_gate_passed'] else 5

if __name__=='__main__':raise SystemExit(main())
