"""Bounded log/target/grammar diagnosis. No pixels, model inference or fitting."""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time


def read(p):
    return json.loads(Path(p).read_text())


def ref(p):
    p = Path(p).resolve()
    data = p.read_bytes()
    return dict(path=str(p), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def bound(r):
    p = Path(r['path'])
    assert ref(p) == r, 'Bound diagnostic source changed'
    return p


def save(p, value):
    with Path(p).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def h(value):
    return hashlib.sha256((value + ':branch29').encode()).hexdigest()


def run(root):
    started = time.monotonic()
    reg = read(root / 'registration28.json')
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU process masks only itself'
    assert ref(__file__) == reg['code_ref']
    save(root / 'cpu_claim28.json', dict(pid=os.getpid(), registration=ref(root / 'registration28.json')))
    train = read(bound(reg['training_prepared_ref']))
    rows = [json.loads(line) for line in bound(train['training_targets']).read_text().splitlines() if line]
    assert len(rows) == 2236
    by_uid = defaultdict(list)
    requests = {}
    for row in rows:
        by_uid[row['uid']].append(row)
        if row['uid'] not in requests:
            requests[row['uid']] = read(bound(row['input_ref']))
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(reg['model_directory'], local_files_only=True)
    spec = importlib.util.spec_from_file_location('frozen_grammar28', bound(reg['grammar_ref']))
    grammar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(grammar)
    candidate_ids = set(grammar.ascii_token_candidates(tokenizer))
    blocked = []
    target_prefixes = Counter()
    tested = set()
    for row in rows:
        request = requests[row['uid']]
        duration = Fraction(request['plan']['window_end_exact']) - Fraction(request['plan']['window_start_exact'])
        ids = row['suffix_ids']
        key = (tuple(ids), str(duration))
        target_prefixes[tuple(ids[:3])] += row['weight']
        if key in tested:
            continue
        tested.add(key)
        g = grammar.BoundedSegmentsGrammar(duration, max_segments=6, allow_empty=True)
        reasons = []
        assert ids[-1] == 151645
        text = tokenizer.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if text != row['target_json']:
            reasons.append('TOKEN_TARGET_TEXT_MISMATCH')
        if not g.complete(text):
            reasons.append('COMPLETE_TARGET_EXCLUDED_BY_GRAMMAR')
        previous = ''
        for i, token in enumerate(ids[:-1]):
            current = tokenizer.decode(ids[:i+1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
            if token not in candidate_ids or not current.startswith(previous) or len(current) <= len(previous) or not g.valid_prefix(current):
                reasons.append('TOKEN_PREFIX_UNREACHABLE_AT_%d' % i)
                break
            previous = current
        if reasons:
            blocked.append(dict(uid=row['uid'], reviewer=row['reviewer'], reasons=reasons,
                                suffix_ids=ids, target_json=row['target_json']))
    losses = [json.loads(line) for line in bound(reg['training_micro_ref']).read_text().splitlines() if line]
    raw = [x for x in losses if x['event'] == 'RAW_LOSS']
    assert len(raw) == 2236 and {x['micro'] for x in raw} == set(range(2236))
    target_map = {(x['uid'], x['reviewer']):x for x in rows}
    buckets = defaultdict(list)
    for x in raw:
        empty = not json.loads(target_map[(x['uid'], x['reviewer'])]['target_json'])['segments']
        buckets[(min(3, x['micro'] * 4 // 2236), 'empty' if empty else 'nonempty')].append(x['actual_token_mean_CE'])
    loss_summary = [dict(quartile=q+1, target=kind, observations=len(v), mean_token_CE=math.fsum(v)/len(v))
                    for (q,kind),v in sorted(buckets.items())]
    windows = []
    for uid, rs in by_uid.items():
        empty = sum(not json.loads(x['target_json'])['segments'] for x in rs)
        windows.append(dict(uid=uid, sid=rs[0]['sid'], empty_reviewers=empty, reviewers=len(rs),
                            empty_fraction=empty/len(rs), all_reviewers_nonempty=empty == 0))
    selected = []
    used_sources = set()
    for kind, predicate in [('unanimous_nonempty', lambda x:x['empty_fraction'] == 0),
                            ('mixed_nonempty_majority', lambda x:0 < x['empty_fraction'] < .5)]:
        eligible = sorted([x for x in windows if predicate(x)], key=lambda x:h(x['uid']))
        chosen = []
        for item in eligible:
            if item['sid'] not in used_sources:
                chosen.append(item)
                used_sources.add(item['sid'])
            if len(chosen) == 2:
                break
        assert len(chosen) == 2, 'Predeclared diagnostic strata unavailable; no substitute'
        for item in chosen:
            row = min([x for x in by_uid[item['uid']] if json.loads(x['target_json'])['segments']],
                      key=lambda x:h('%s:%s' % (x['uid'], x['reviewer'])))
            selected.append(dict(domain='training', stratum=kind, uid=item['uid'], sid=item['sid'],
                                 input_ref=row['input_ref'], nonempty_probe_ids=row['suffix_ids'],
                                 nonempty_probe_text=row['target_json'], human_empty_fraction=item['empty_fraction'],
                                 nonempty_probe_role='ONE_ORIGINAL_HUMAN_TARGET_NOT_ORACLE_SELECTION'))
    dev = read(bound(reg['development_prepared_ref']))
    dev_by_source = defaultdict(list)
    for r in dev['inputs']:
        request = read(bound(r))
        old_path = Path(reg['original_INIT_directory']) / (request['uid'] + '.output.json')
        old = read(old_path)
        if old['parsed_exact_segments']:
            dev_by_source[request['sid']].append((r, request, old_path, old))
    for sid in sorted(dev_by_source, key=h)[:4]:
        r, request, old_path, old = min(dev_by_source[sid], key=lambda x:h(x[1]['uid']))
        selected.append(dict(domain='development', stratum='hash_source_window_original_INIT_nonempty',
                             uid=request['uid'], sid=sid, input_ref=r, nonempty_probe_ids=old['generated_ids'],
                             nonempty_probe_text=old['raw_text'], original_INIT_ref=ref(old_path),
                             nonempty_probe_role='ADOPTED_ORIGINAL_MODEL_PROPOSAL_NOT_HUMAN_GT'))
    assert len(selected) == 8
    result = dict(status='COMPLETE_LOG_AND_TARGET_GRAMMAR_DIAGNOSTIC_NO_MODEL',
                  targets=2236, unique_target_duration_paths=len(tested), grammar_blocked_paths=len(blocked),
                  blocked_examples=blocked[:12], loss_quartiles=loss_summary,
                  window_consensus=dict(total=len(windows), unanimous_nonempty=sum(x['empty_fraction']==0 for x in windows),
                                        mixed=sum(0<x['empty_fraction']<1 for x in windows), unanimous_empty=sum(x['empty_fraction']==1 for x in windows)),
                  first3_target_token_routes=[dict(ids=list(k), decoded=tokenizer.decode(k), source_weight=v)
                                              for k,v in target_prefixes.most_common(8)],
                  empty_tokens=tokenizer.encode('{"segments":[]}', add_special_tokens=False)+[151645],
                  opening_tokens=tokenizer.encode('{"segments":[', add_special_tokens=False),
                  fixed_next_probe_selection=selected, selection_frozen_before_new_probability_measurements=True,
                  selection_rule=reg['selection_rule'], model_calls=0, new_fit=0, pixel_decode_or_processor_calls=0,
                  official_or_independent_quality_not_measured=True, elapsed_seconds=time.monotonic()-started)
    save(root/'result28.json', result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('blocked_examples','fixed_next_probe_selection')}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    run(parser.parse_args().root)
