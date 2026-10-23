"""Adopt fresh pages after exact counter-only difference; first GPU still pending."""
import json
import re
import traceback

import localized_query122 as stage
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'localized_query_remaining123'


def adopt_fresh_pages():
    fresh_path = ROOT / 'official_freshness122/completion.json'
    fresh = read(fresh_path); original = read(check(fresh['original_full_rule_read']))
    checked = {}
    for name, current in fresh['pages'].items():
        before = check(original['pages'][name]['source']).read_text()
        after = check(current['source']).read_text()
        # Only the literal public read counter may differ; entire other bytes must match.
        if re.sub(r'[0-9,]+ 次阅读', '<READ_COUNTER>', before) != re.sub(r'[0-9,]+ 次阅读', '<READ_COUNTER>', after):
            raise ValueError('Fresh official content has changes beyond reviewed read counters')
        checked[name] = dict(current=current['source'], previous=original['pages'][name]['source'],
            exact_after_only_literal_read_counter_removal=True)
    path = OUT / 'official_counter_only_review.json'
    save(path, dict(state='CURRENT_PRIMARY_CONTENT_LINKS_AND_CATALOG_UNCHANGED_ONLY_READ_COUNTERS',
        fresh_direct_read=identity(fresh_path), pages=checked,
        adopted_original_complete_rule_read=fresh['original_full_rule_read'],
        no_new_download_or_changed_rule_waiver=True, no_special_permission_claim=True))
    return identity(path)


def main():
    OUT.mkdir()
    failure = read(stage.OUT / 'failure.json')
    if (failure['resource'] is not None or (stage.OUT / 'GPU_launch.json').exists()
            or (stage.OUT / 'source_input_lock.json').exists()
            or 'Primary page changed' not in failure['traceback']):
        raise ValueError('Only exact pre-GPU rule-read stop is eligible; no successful work repeated')
    save(OUT / 'registration.json', dict(original_pre_GPU_failure=identity(stage.OUT / 'failure.json'),
        code=identity(stage.CODE / 'localized_query_remaining123.py'),
        unchanged_protocol=identity(stage.CODE / 'localized_query_protocol122.json'),
        scope='Read-counter-only reviewed fresh-page adoption; first actual25 masked model/CPU unchanged',
        actual_prior_GPU_calls=0, actual_prior_GPU_seconds=0, no_retry_of_successful_web_read=True))
    stage.review = adopt_fresh_pages
    protocol, capacity = stage.admission()
    stage.run('localized_query122_gpu.py', 'GPU', protocol, capacity, gpu=True)
    resource = read(stage.RUN / 'controller' / (stage.JOB + '.resource.json'))
    rows = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in rows if row.get('name') == stage.JOB] != [resource]:
        raise ValueError('Natural new masked8B terminal and unique ledger disagree')
    stage.run('localized_query122_cpu.py', 'first_complete_CPU', protocol, capacity)
    cpu = read(stage.OUT / 'CPU_completion.json')
    result = dict(state=cpu['state'], first_CPU=identity(stage.OUT / 'CPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=protocol['Goal_GPU_seconds_before'] + resource['charged_seconds'],
        actual_new_logical_windows=25, actual_new_physical_model_forwards=50, actual_new_native_decisions=800,
        local_information_gate_pass=cpu['local_information_gate_pass'],
        original122_pre_GPU_failure_preserved=True, no_automatic_training_confirmation_or_production=True, new_T_ZIPs=0)
    save(stage.OUT / 'completion_remaining123.json', result)
    save(OUT / 'completion.json', result)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            path = stage.RUN / 'controller' / (stage.JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), resource=read(path) if path.exists() else None,
                preserve_all_old_failure_success_and_fees=True, no_automatic_retry=True))
        raise
