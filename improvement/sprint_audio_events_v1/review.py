"""Independent token/grammar/native replay; exact overlapping-frame unions."""
from bisect import bisect_left
from fractions import Fraction
import json
import numpy as np
from common import ROOT, read, write, checked, reference
from context import legacy


def outputs(tokenizer, old):
    from summary_grammar6 import BoundedSegmentsGrammar
    from summary_output import parse_summary
    result = {}
    for entry in read(ROOT/'time_completion.json')['outputs']:
        row = read(checked(entry));raw = read(checked(row['raw_token_ref']))
        request = read(checked(row['request_ref']))
        prefix = read(checked(row['input_ref']))
        for key in ['uid', 'condition', 'generated_ids', 'input_ref', 'weight_ref']:
            if row[key] != raw[key]:
                raise ValueError('Raw token ledger differs from parsed output')
        if row['weight_ref'] != old['initial_TIME_ref'] or prefix['request_ref'] != row['request_ref']:
            raise ValueError('Output model/input identity differs')
        ids = row['generated_ids']
        if not ids or ids[-1] != 151645 or 151645 in ids[:-1]:
            raise ValueError('Incomplete output is failure, never valid rejection')
        text = tokenizer.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        start = Fraction(request['plan']['window_start_exact'])
        end = Fraction(request['plan']['window_end_exact'])
        if text != row['raw_text'] or not BoundedSegmentsGrammar(end-start, max_segments=6, allow_empty=True).complete(text):
            raise ValueError('Independent token/grammar replay failed')
        spans = parse_summary(text, end-start)
        if row['parsed_exact_segments'] != [[str(a),str(b)] for a,b in spans]:
            raise ValueError('Independent grammar/parser join failed')
        clock = read(checked(request['source_clock_ref']))
        points = list(map(Fraction, clock['normalized_exact_pts']))
        result[row['uid'], row['condition']] = [[bisect_left(points, start+a), bisect_left(points, start+b)] for a,b in spans]
    if len(result) != 16:
        raise ValueError('Incomplete registered output set')
    return result


def evaluate(control, new, human):
    from evaluate_summary import metric
    selected = set(uid for uid, condition in new)
    sids = {control[uid]['sid'] for uid in selected}
    rows = []
    for sid in sorted(sids):
        with np.load(checked(human[sid]['data_ref']), allow_pickle=False) as saved:
            labels = saved['labels']
        masks = {name:np.zeros(len(labels), bool) for name in ['visual', 'correct', 'shifted']}
        domain = np.zeros(len(labels), bool)
        for uid, item in control.items():
            if item['sid'] != sid:
                continue
            for condition, mask in masks.items():
                ranges = new[uid, condition] if uid in selected and condition != 'visual' else item['native_ranges']
                for a,b in ranges:
                    if not 0 <= a < b <= len(labels):
                        raise ValueError('Native output leaves original human frame ordinal')
                    mask[a:b] = True
        for item in read(ROOT/'input_acceptance.json')['rows']:
            if item['sid'] != sid:
                continue
            clock = read(checked(item['clock_ref']))
            pts = list(map(Fraction, clock['normalized_exact_pts']))
            if len(pts) != len(labels):
                raise ValueError('Original author labels and native decode rows differ')
            domain[bisect_left(pts,Fraction(item['start_exact'])):bisect_left(pts,Fraction(item['end_exact']))] = True
        full = {key:metric(value, labels) for key,value in masks.items()}
        excerpt = {key:metric(value[domain], labels[domain]) for key,value in masks.items()}
        rows.append(dict(sid=sid, full_source=full, treated_excerpt=excerpt,
            selected_frames={key:int(value.sum()) for key,value in masks.items()},
            correct_vs_visual_changed=int((masks['correct'] != masks['visual']).sum()),
            correct_vs_shift_changed=int((masks['correct'] != masks['shifted']).sum()),
            original_reviewers=labels.shape[1], overlapping_frames_counted_once=True))
    return rows


def main():
    from transformers import AutoTokenizer
    reg, old, module = legacy()
    tokenizer = AutoTokenizer.from_pretrained(read(checked(old['model_config_ref']))['model_dir'], local_files_only=True)
    new = outputs(tokenizer, old)
    qa = read(checked(reg['adopted_original_INIT_QA_ref']))
    control = {row['uid']:row for row in qa['details']}
    human = {row['sid']:row for row in read(checked(reg['existing_external_human_catalog_ref']))['sources']}
    rows = evaluate(control, new, human)
    means = {scope:{name:float(np.mean([row[scope][name]['f1'] for row in rows]))
        for name in ['visual', 'correct', 'shifted']} for scope in ['full_source', 'treated_excerpt']}
    improvement = [row['full_source']['correct']['f1']-row['full_source']['visual']['f1'] for row in rows]
    alignment = [row['full_source']['correct']['f1']-row['full_source']['shifted']['f1'] for row in rows]
    evidence = (means['full_source']['correct'] > max(means['full_source']['visual'], means['full_source']['shifted'])
        and sum(value > 0 for value in improvement) >= 2 and sum(value > 0 for value in alignment) >= 2)
    write(ROOT/'independent_output_qa.json', dict(status='PASS_ALL16_FIRST_TOKEN_GRAMMAR_NATIVE_REPLAY',
        actual_outputs=len(new), original43_control_adopted=True, successful_empty_is_not_failure=True))
    result = dict(status='A0_EXTERNAL_SIGNAL_REQUIRES_REVIEW' if evidence else 'STOP_FIXED_A0_NO_STABLE_ALIGNED_AUDIO_BENEFIT',
        sources=rows, macro_f1=means, correct_better_than_visual_sources=sum(value > 0 for value in improvement),
        correct_better_than_shifted_sources=sum(value > 0 for value in alignment),
        actual_new_TIME_calls=16, new_PANN_forwards=8, actual_train_updates=0,
        original_TIME_control_not_exact_40_47_pipeline=True,
        historically_exposed_four_source_diagnostic_not_blind=True,
        summary_unselected_not_explicit_ordinary=True, official_joint_score=None,
        full_source_four_has_untreated_original_windows=True, automatic_production=False)
    write(ROOT/'review.json', result)
    print(json.dumps({key:value for key,value in result.items() if key!='sources'}), flush=True)


if __name__ == '__main__':
    main()
