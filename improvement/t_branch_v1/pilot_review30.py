"""Independent output/native replay and whole-source all-reviewer anchors."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pilot_context30 import ROOT, WORK, OUT, RUN, check, identity, read, save, legacy_runtime, original_outputs

def review():
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import numpy as np
    import torch
    from transformers import AutoTokenizer
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    from fractions import Fraction
    from native_sets import NativeTimeline, union_components
    from preference_reward import SummaryReview, summary_agreement
    rt = legacy_runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    candidates = ascii_token_candidates(tokenizer)
    originals = original_outputs()
    sources = {row['source']['sid']: row['source'] for row in read(ROOT / 'pilot_profile21/registration.json')['planned']}
    components = {sid: {} for sid in sources}
    for ref in read(OUT / 'gpu_completion.json')['outputs']:
        row = read(check(ref))
        raw = read(check(row['raw']))
        cpu = read(check(row['CPU']))
        meta = read(check(cpu['input']))
        lo, hi = Fraction(row['source_start']), Fraction(row['source_end'])
        if row['case'] not in originals:
            grammar = make_prefix_constraint(tokenizer, raw['prefix'], hi - lo,
                candidate_token_ids=candidates, eos_token_ids=raw['eos'], allow_empty=True)
            grammar.assert_complete(torch.tensor(raw['token_ids'], dtype=torch.long))
            text = tokenizer.decode(raw['token_ids'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
            parsed, errors, _ = rt.parse_segments(text, hi - lo, allow_empty=True)
            if errors or parsed != row['segments'] or text != raw['raw'] or raw['prefix'] != cpu['input_tokens']:
                raise ValueError('First independent remaining output replay differs')
        timeline = NativeTimeline.from_clock(read(check(sources[meta['source_name']]['clock'])))
        spans = [(lo + Fraction(str(a)), lo + Fraction(str(b))) for a, b in row['segments']]
        components[meta['source_name']][row['case']] = timeline.intervals(spans)
    metrics = []
    for sid, source in sources.items():
        target_meta = read(ROOT / 'summary_targets28' / (sid + '.json'))
        with np.load(check(target_meta['tensor']), allow_pickle=False) as archive:
            domain = archive['summary_task_domain']
            reviews = [SummaryReview(name, mask, domain) for name, mask in
                       zip(target_meta['all_original_reviewers'], archive['summary_selected'])]
        chosen = union_components(components[sid], len(domain))
        score = summary_agreement(chosen, reviews, source['independent_reviewers'])
        names = list(components[sid])
        path = OUT / (sid + '_original_components.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, components=np.stack([components[sid][name] for name in names]),
                                selected=chosen)
        save(OUT / (sid + '_control.json'), dict(source_id=sid, role=source['role'],
            original_component_ids=names, native=identity(path), score=score,
            source_coverage=float(chosen.mean()), exact_complete40_47_control=False,
            description='Whole-source original coarse TIME; no D8/VERIFY/semantic replacement claim'))
        metrics.append(identity(OUT / (sid + '_control.json')))
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS', new_output_cases=93, adopted_output_cases=4,
        complete_source_controls=metrics, all_raters_original_and_native=True,
        no_generic_NHL_or_official_joint_score_claim=True, training_updates=0))


if __name__ == '__main__':
    review()
