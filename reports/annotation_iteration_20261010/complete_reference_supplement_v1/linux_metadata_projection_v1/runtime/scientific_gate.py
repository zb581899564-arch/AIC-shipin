"""Fixed final-only, exact-Fraction silver diagnostic. Never an official score."""
from fractions import Fraction as F
from common import require


def reference_coverage(jobs, references, quality):
    """Prediction-independent reference sufficiency, checked before any GPU work."""
    groups = {}; dev = []
    locked_keys = [k for k, j in jobs.items() if j['role'] == 'locked_evaluation']
    for key, job in jobs.items():
        if job['role'] == 'process_dev':
            dev.append(key)
    require(all(k in references for k in dev+locked_keys), 'complete evaluation references pending')
    for key in locked_keys:
        r = references[key]
        g = groups.setdefault(jobs[key]['source_group'], dict(keep=[], no=[], complete=0))
        g['keep'].extend(r['keep_global_exact']); g['no'].extend(r['no_global_exact'])
        g['complete'] += not r['unknown_global_exact'] and not r.get('consequential_unknowns')
    tests = dict(dev_four_windows_two_sources=len(dev) == 4 and len({jobs[k]['source_group'] for k in dev}) == 2,
        locked_eight_windows_four_sources=len(locked_keys) == 8 and len(groups) == 4,
        locked_complete_silver_min=sum(g['complete'] for g in groups.values()) >= 6,
        locked_all_four_sources_informative=all(quality.duration(g['keep']) > 0 or quality.duration(g['no']) >= 5 for g in groups.values()),
        positive_locked_sources_min=sum(quality.duration(g['keep']) > 0 for g in groups.values()) >= 3,
        locked_sources_with_at_least_5sec_no_min=sum(quality.duration(g['no']) >= 5 for g in groups.values()) >= 2)
    return dict(status='PASS_FIXED_EVALUATION_REFERENCE_COVERAGE' if all(tests.values()) else 'STOP_INSUFFICIENT_FIXED_EVALUATION_REFERENCES_NO_GPU', checks=tests)


def summarize(jobs, references, predictions, quality, event_module, role):
    keys = sorted(k for k, j in jobs.items() if j['role'] == role)
    require(set(predictions) == set(keys), 'evaluation prediction denominator differs')
    groups = {}
    for key in keys:
        row = predictions[key]
        require(row['status'] in ('MODEL_OK', 'LEGAL_EMPTY') and row['parsed_segments'] is not None,
                'engineering/parser failure cannot enter scientific metrics')
        j, r = jobs[key], references[key]; w = j['window']
        start, end = F(w['domain_start_exact']), F(w['domain_end_exact'])
        p = [[F(a)+start, F(b)+start] for a, b in row['parsed_segments']]
        wm = quality.metrics([(start, end)], r['keep_global_exact'], r['no_global_exact'], r['unknown_global_exact'], p)
        g = groups.setdefault(j['source_group'], dict(domain=[], keep=[], no=[], unknown=[], prediction=[],
            reference_events=[], predicted_events=[], positive_empty_windows=0, complete_windows=0, window_count=0))
        g['window_count'] += 1
        g['domain'].append([start, end])
        for dest, src in (('keep', 'keep_global_exact'), ('no', 'no_global_exact'), ('unknown', 'unknown_global_exact')):
            g[dest].extend(r[src])
        g['prediction'].extend(p)
        g['predicted_events'].extend([[x] for x in p])
        for e in r['events']:
            a, b = map(F, e['local'])
            event = [[start+a, start+b]]
            require(quality.duration(quality.intersection(event, r['keep_global_exact'])) == quality.duration(event),
                    'event does not belong to confirmed KEEP')
            g['reference_events'].append(event)
        g['positive_empty_windows'] += bool(wm['known_positive_duration'] and not p)
        g['complete_windows'] += not r['unknown_global_exact'] and not r.get('consequential_unknowns')
    for g in groups.values():
        args = [g[n] for n in ('domain', 'keep', 'no', 'unknown')]
        g['metrics'] = quality.metrics(*args, g['prediction'])
        g['event_metrics'] = event_module.match_events(g['reference_events'], g['predicted_events'])
    return groups


def compare(base, new, quality):
    require(set(base) == set(new), 'source denominator differs')
    rows = {}; positive = []
    for name in sorted(base):
        b, c = base[name], new[name]
        require(all(b[k] == c[k] for k in ('domain', 'keep', 'no', 'unknown', 'reference_events')), 'reference changed across arms')
        bm, cm = b['metrics'], c['metrics']
        is_positive = bm['known_positive_duration'] > 0
        gain = cm['f1']-bm['f1'] if is_positive else None
        conservative = quality.conservative_gain([b[n] for n in ('domain', 'keep', 'no', 'unknown')], b['prediction'], c['prediction'])
        if not is_positive and bm['unknown_duration'] > 0:
            # No confirmed positive denominator: only identical predictions
            # establish conservative zero without inventing UNKNOWN truth.
            conservative = F(0) if quality.normalize(b['prediction']) == quality.normalize(c['prediction']) else None
        # A new selected confirmed-NO time span is a new unrelated spill,
        # even when an old false positive of equal duration disappeared.
        old_no = quality.intersection(b['prediction'], b['no'])
        new_no = quality.intersection(c['prediction'], b['no'])
        newly_spilled = quality.duration(new_no)-quality.measure(new_no, old_no)
        row = dict(positive=is_positive, f1_gain=gain, conservative_gain=conservative,
            no_fp_nonincrease=cm['fp'] <= bm['fp'], no_new_unrelated_spill=newly_spilled == 0,
            new_confirmed_no_spill_seconds=newly_spilled,
            positive_empty_nonincrease=c['positive_empty_windows'] <= b['positive_empty_windows'],
            precision_nondecrease=not is_positive or cm['precision'] >= bm['precision'],
            recall_nondecrease=not is_positive or cm['recall'] >= bm['recall'],
            event_recall_nondecrease=not is_positive or (
                b['event_metrics']['event_recall'] is not None and c['event_metrics']['event_recall'] is not None and
                c['event_metrics']['event_recall'] >= b['event_metrics']['event_recall']),
            positive_source_nondegrade=not is_positive or gain >= 0,
            unknown_conservative_nonnegative=(conservative is not None and conservative >= 0) if (is_positive or bm['unknown_duration'] > 0) else True)
        rows[name] = row
        if is_positive:
            positive.append(row)
    return dict(sources=rows, positive_sources=len(positive),
        positive_macro_gain=sum((r['f1_gain'] for r in positive), F(0))/len(positive) if positive else None,
        conservative_positive_macro_gain=sum((r['conservative_gain'] for r in positive), F(0))/len(positive) if positive else None,
        strictly_improved_sources=sum(r['f1_gain'] > 0 for r in positive))


def gate(dev_base, dev_new, locked_base, locked_new, quality):
    dev = compare(dev_base, dev_new, quality); locked = compare(locked_base, locked_new, quality)
    tests = dict(dev_four_windows_two_sources=len(dev_base) == 2 and sum(g['window_count'] for g in dev_base.values()) == 4,
        locked_eight_windows_four_sources=len(locked_base) == 4 and sum(g['window_count'] for g in locked_base.values()) == 8,
        locked_complete_silver_min=sum(g['complete_windows'] for g in locked_base.values()) >= 6,
        locked_all_four_sources_informative=all(g['metrics']['known_positive_duration'] > 0 or g['metrics']['known_no_duration'] >= 5 for g in locked_base.values()),
        positive_locked_sources_min=locked['positive_sources'] >= 3,
        locked_sources_with_at_least_5sec_no_min=sum(g['metrics']['known_no_duration'] >= 5 for g in locked_base.values()) >= 2,
        dev_positive_macro_gain_strictly_positive=dev['positive_macro_gain'] is not None and dev['positive_macro_gain'] > 0,
        locked_positive_macro_f1_gain_min=locked['positive_macro_gain'] is not None and locked['positive_macro_gain'] >= F('0.05'),
        strictly_improved_locked_sources_min=locked['strictly_improved_sources'] >= 2,
        unknown_positive_average_gain_strictly_positive=locked['conservative_positive_macro_gain'] is not None and locked['conservative_positive_macro_gain'] > 0)
    fields = ('no_fp_nonincrease', 'no_new_unrelated_spill', 'positive_empty_nonincrease', 'precision_nondecrease',
              'recall_nondecrease', 'event_recall_nondecrease', 'positive_source_nondegrade', 'unknown_conservative_nonnegative')
    for field in fields:
        tests[field] = all(row[field] for summary in (dev, locked) for row in summary['sources'].values())
    return dict(status='PASS_FIXED_SILVER_QUALITY_GATE' if all(tests.values()) else 'STOP_FIXED_SILVER_QUALITY_GATE_NO_426_NO_RETUNING',
        checks=tests, dev=dev, locked=locked, quality_claim='FINITE_OBSERVATION_SILVER_DIAGNOSTIC_NOT_GOLD_OR_OFFICIAL',
        recipe_retuning_allowed=False, official_submission_authorized=False)
