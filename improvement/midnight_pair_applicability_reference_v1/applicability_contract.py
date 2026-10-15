"""Supplemental short-source applicability contract; no model or label access."""
import hashlib
import json
from pathlib import Path

HOME = Path('/home/inspur/aic_video_work')
MAIN = HOME/'midnight_five_verify40_46_20261015_v1'
ROOT = HOME/'midnight_pair_applicability_20261015_v1'
DEADLINE = '2026-10-15T16:00:00Z'

def require(value, message):
    if not value:
        raise ValueError(message)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()

def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))

def checked(value):
    p = Path(value['path'])
    require(p.is_relative_to(HOME) and p.is_file() and sha(p) == value['sha256'], 'Frozen source changed: '+str(p))
    return p

def save(path, value):
    with Path(path).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def original_contract(metadata):
    """Read old results solely to bind their unchanged terminal conclusions."""
    p = read(checked(metadata['original_policy_protocol_ref']))
    d = read(checked(metadata['original_development_result_ref']))
    s = read(checked(metadata['original_development_selection_ref']))
    previous = read(checked(metadata['previous_neutral_PAIR_result_ref']))
    require(p['policies'] == ['ALL_WINDOW_WORST', 'BUDGET_TWO_THIRDS', 'PAIR_ONLY']
        and p['max_selected_policies'] == 2 and s['selected_policies'] == ['ALL_WINDOW_WORST', 'PAIR_ONLY']
        and s['passed_arms'] == d['passed_arms'] == dict(ALL_WINDOW_WORST=True, BUDGET_TWO_THIRDS=False, PAIR_ONLY=True)
        and s['result_ref'] == {k: metadata['original_development_result_ref'][k] for k in ('path', 'sha256')}
        and s['confirm_metrics_examined'] is False and d['group'] == 'dev', 'Original development selection must remain frozen')
    pair = previous['policies']['PAIR_ONLY']
    require(previous['group'] == 'confirm' and previous['passed_policies']['PAIR_ONLY'] is False
        and pair['PASS'] is False and pair['gates']['real_changed_sources'] is False
        and all(v is True for k, v in pair['gates'].items() if k != 'real_changed_sources')
        and all(pair['macro'][k]['delta']['exact'] == '0' for k in ('f1', 'precision', 'recall')),
        'Prior new4 remains a genuine neutral-but-no-applicability FAILED result')
    return p, d, s

def validate_selection(root=ROOT):
    s = read(root/'new_selection.json'); protocol = read(checked(s['supplemental_protocol_ref']))
    metadata = read(root/'isolation_metadata.json'); original_contract(metadata)
    require(s['selected_policies'] == ['PAIR_ONLY'] and s['confirm_metrics_examined'] is False
        and s['confirm_metrics_examined_scope'] == 'THIS_NEW_SHORT_COHORT_ONLY'
        and s['prior_confirm_metrics_examined'] is True and s['old_confirm_result_unchanged'] is True
        and s['original_development_selection_ref'] == {k: metadata['original_development_selection_ref'][k] for k in ('path','sha256')}
        and protocol['single_additional_cohort_only'] is True and protocol['no_quality_based_replacement'] is True
        and protocol['deadline'] == DEADLINE, 'One separately frozen short-source PAIR cohort required')
    return s, protocol
