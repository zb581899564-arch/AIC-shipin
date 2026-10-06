"""One frozen comparison on the final holdout, ordered only by development results."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time

from evaluation_v2.temporal import evaluate_rows, compare, read_jsonl

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
PYTHON = str(ROOT / 'env/qwen3vl/bin/python')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dev-run', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--name-prefix', required=True)
    ap.add_argument('--max-seconds-per-policy', type=int, default=7200)
    args = ap.parse_args()
    dev = Path(args.dev_run)
    summary = json.loads((dev / 'summary.json').read_text())
    if summary['status'] != 'completed' or summary.get('holdout_used'):
        raise ValueError('development must be complete without holdout use')
    qualified = summary['qualified']
    if not qualified or len(qualified) != len(set(qualified)):
        raise ValueError('no unique development-qualified candidate list')
    if any(p not in ('multi', 'windowed') for p in qualified):
        raise ValueError('only frozen untrained policies are supported by this suite')
    sources = json.loads((dev / 'input_lock.json').read_text())
    for relative, digest in sources.items():
        path = dev / 'dev_frozen.jsonl' if relative == 'dev' else ROOT / relative
        if sha(path) != digest:
            raise ValueError('development source drift: ' + relative)
    baseline_record = json.loads((dev / 'single_report.json').read_text())
    if sha(dev / 'single_predictions.jsonl') != baseline_record['predictions_sha256']:
        raise ValueError('development baseline prediction drift')
    dev_refs = read_jsonl(dev / 'dev_frozen.jsonl')
    baseline = evaluate_rows(read_jsonl(dev / 'single_predictions.jsonl'), dev_refs)
    for policy in qualified:
        candidate = json.loads((dev / (policy + '_report.json')).read_text())
        if sha(dev / (policy + '_predictions.jsonl')) != candidate['predictions_sha256']:
            raise ValueError('development prediction drift: ' + policy)
        actual = evaluate_rows(read_jsonl(dev / (policy + '_predictions.jsonl')), dev_refs)
        if not compare(actual, baseline)['eligible_dev']:
            raise ValueError('candidate failed independent development recheck: ' + policy)
        if actual['metrics'] != candidate['metrics']:
            raise ValueError('development metric report drift: ' + policy)
    expected_order = sorted(qualified, key=lambda p: (
        -summary['results'][p]['metrics']['f1'], summary['results'][p]['wall_seconds']))
    if qualified != expected_order:
        raise ValueError('candidate order must be frozen by development F1 then speed')
    holdout = CAMPAIGN / 'frozen_data/holdout.jsonl'
    refs = read_jsonl(holdout)
    if len(refs) < 50 or len({r['video_id'] for r in refs}) != len(refs):
        raise ValueError('holdout size or unique identity gate failed')
    if {r['source_group'] for r in refs} & {r['source_group'] for r in dev_refs}:
        raise ValueError('holdout source overlap')
    data_lock = json.loads((CAMPAIGN / 'frozen_data/lock.json').read_text())
    for split in ('train', 'dev', 'holdout'):
        if sha(CAMPAIGN / ('frozen_data/' + split + '.jsonl')) != data_lock['structural_media_audit'][split]['sha256']:
            raise ValueError('frozen split identity changed: ' + split)
    if sha(dev / 'dev_frozen.jsonl') != data_lock['structural_media_audit']['dev']['sha256']:
        raise ValueError('development comparison did not use the campaign canonical dev split')
    train_refs = read_jsonl(CAMPAIGN / 'frozen_data/train.jsonl')
    if {r['source_group'] for r in refs} & {r['source_group'] for r in train_refs}:
        raise ValueError('holdout source overlap with training candidates')
    # Identity is independently bound here, even if the media-origin training
    # gate remains unresolved. These results remain internal diagnostics.
    out = Path(args.output).resolve()
    if not out.is_relative_to(ROOT):
        raise ValueError('holdout output must remain in the project workspace')
    if out.exists():
        raise ValueError('output already exists; preserve prior holdout evidence')
    plan = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                status='frozen_before_any_holdout_inference', dev_run=str(dev),
                candidate_order=qualified, policies=['single'] + qualified,
                holdout_sha256=sha(holdout), source_hashes=sources,
                dev_summary_sha256=sha(dev / 'summary.json'),
                suite_sha256=sha(__file__), data_lock_sha256=sha(CAMPAIGN / 'frozen_data/lock.json'),
                output=str(out), training_used=False, official_aic_score=None,
                selection='first dev-ranked candidate with holdout F1 >= single baseline',
                allow_holdout_tuning=False)
    # Campaign-wide exclusive marker prevents a second independently selected
    # final comparison. Recovery of an interrupted exact plan is supervised.
    with (CAMPAIGN / 'holdout_comparison_lock.json').open('x') as stream:
        stream.write(json.dumps(plan, indent=2) + '\n')
    out.mkdir(parents=True)
    (out / 'holdout_frozen.jsonl').write_bytes(holdout.read_bytes())
    write(out / 'plan.json', plan)
    results = {}
    for policy in plan['policies']:
        for relative, digest in sources.items():
            path = dev / 'dev_frozen.jsonl' if relative == 'dev' else ROOT / relative
            if sha(path) != digest:
                raise ValueError('source changed during holdout: ' + relative)
        if sha(out / 'holdout_frozen.jsonl') != plan['holdout_sha256']:
            raise ValueError('holdout identity drift')
        pred = out / (policy + '_predictions.jsonl')
        write(out / 'progress.json', dict(status='running', policy=policy, completed=list(results)))
        cmd = [PYTHON, str(CAMPAIGN / 'budget_run.py'), '--name', args.name_prefix + '_' + policy,
               '--max-seconds', str(args.max_seconds_per_policy), '--', PYTHON,
               '-m', 'inference_v2.baseline_v2', '--model', str(ROOT / 'models/Qwen3-VL-4B-Instruct'),
               '--index', str(out / 'holdout_frozen.jsonl'), '--temporal-only', '--query-aware',
               '--temporal-policy', policy, '--constrained-json', '--temporal-out', str(pred),
               '--raw-out', str(out / (policy + '_raw.jsonl'))]
        started = time.monotonic()
        code = subprocess.run(cmd, cwd=ROOT).returncode
        if code:
            write(out / 'progress.json', dict(status='failed', policy=policy, returncode=code))
            raise SystemExit(code)
        try:
            report = evaluate_rows(read_jsonl(pred), refs)
            report.update(policy=policy, wall_seconds=time.monotonic() - started,
                          reference_sha256=plan['holdout_sha256'], predictions_sha256=sha(pred))
            if policy != 'single':
                if 'metrics' not in results['single']:
                    raise ValueError('invalid holdout baseline')
                report['comparison'] = compare(report, results['single'])
                report['accepted_holdout'] = report['comparison']['delta_f1_pp'] >= 0
        except ValueError as error:
            report = dict(policy=policy, status='diagnostic_rejected', reason=str(error),
                          accepted_holdout=False)
        write(out / (policy + '_report.json'), report)
        results[policy] = report
    accepted = [p for p in qualified if results[p].get('accepted_holdout')]
    result = dict(status='completed', candidate_order=qualified, accepted_in_dev_order=accepted,
                  selected=accepted[0] if accepted else None, holdout_used=True,
                  holdout_tuning=False, training_used=False, official_aic_score=None,
                  results={p: {k: v for k, v in r.items() if k != 'rows'} for p, r in results.items()})
    write(out / 'summary.json', result)
    write(out / 'progress.json', dict(status='completed', accepted=accepted))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
