"""Bind delivery to the one final comparison and the predeclared challenger order."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_qualified_holdout(directory, policy, root=ROOT):
    directory, root = Path(directory).resolve(), Path(root).resolve()
    if not directory.is_relative_to(root):
        raise ValueError('holdout must remain in the project workspace')
    campaign = root / 'improvement_round1'
    plan = json.loads((directory / 'plan.json').read_text())
    lock = json.loads((campaign / 'holdout_comparison_lock.json').read_text())
    if plan != lock or Path(plan['output']).resolve() != directory:
        raise ValueError('holdout is not the unique campaign comparison')
    if sha(directory / 'holdout_frozen.jsonl') != plan['holdout_sha256']:
        raise ValueError('holdout reference identity drift')
    summary = json.loads((directory / 'summary.json').read_text())
    if summary['status'] != 'completed' or summary['candidate_order'] != plan['candidate_order']:
        raise ValueError('holdout candidate order drift or incomplete comparison')
    accepted = [p for p in plan['candidate_order'] if summary['results'][p].get('accepted_holdout')]
    if summary['accepted_in_dev_order'] != accepted or summary['selected'] != (accepted[0] if accepted else None):
        raise ValueError('holdout selection does not follow frozen development order')
    if policy not in accepted:
        raise ValueError('candidate did not pass the final holdout comparison')
    ledger = campaign / 'submission_ledger.jsonl'
    events = [json.loads(s) for s in ledger.read_text().splitlines() if s.strip()] if ledger.exists() else []
    scored = {}
    all_scores = []
    for event in events:
        if event.get('event') == 'scored' and event.get('status') == 'DONE':
            score = event.get('official_score')
            if type(score) not in (int, float) or not math.isfinite(score):
                raise ValueError('official score ledger is invalid')
            scored[event['policy']] = score
            all_scores.append(score)
    baseline = json.loads((campaign / 'submission_policy.json').read_text())['initial_score']
    if any(score > baseline for score in all_scores):
        raise ValueError('official improvement already achieved; further challengers are unnecessary')
    for previous in accepted[:accepted.index(policy)]:
        if previous not in scored:
            raise ValueError('higher-priority candidate has not completed official evaluation: ' + previous)
    return plan, summary
