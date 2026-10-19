"""First scalar-output consistency review; never reloads or replays a model."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

from diagnose_underselection28 import read, ref, bound, save


def run(root):
    reg = read(root/'registration29.json')
    done = read(root/'probability_completion29.json')
    assert done['status'] == 'COMPLETE_FIXED8_TWO_ADAPTER32_PROBABILITY_FORWARDS'
    assert done['actual_new_forwards'] == 32 and done['free_generations'] == done['optimizer_updates'] == 0
    W = Path('/home/inspur/aic_video_work')
    RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    job = reg['job_name']
    resource_path = RUN/'controller'/(job+'.resource.json')
    resource = read(resource_path)
    ledger = [json.loads(l) for l in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if l]
    rows = [x for x in ledger if x.get('name') == job]
    assert len(rows) == 1 and rows[0] == resource and resource['status'] == 'completed' and resource['exit_code'] == 0
    actual = list(root.glob('forward29_*.json'))
    assert len(actual) == 32 and done['base_unchanged'] and done['adapter_weights_unchanged']
    exact = read(root/'exact_adapter_load_acceptance31.json')
    assert all(v['post_restore_all288_bit_equal_saved'] for v in exact['roles'].values())
    details = []
    all_mass = []
    for item in done['results']:
        summary = {k:item[k] for k in ('uid','sid','domain','stratum','human_empty_fraction')}
        summary['role'] = {}
        for role in ('original','trained'):
            data = item['roles'][role]
            for suffix in ('nonempty','empty'):
                raw = read(root/('forward29_%s_%s_%s.json'%(item['uid'],role,suffix)))
                assert raw['measurements'] == data[suffix]
                measure = raw['measurements']
                assert len(measure['token_CE']) == measure['tokens']
                assert all(math.isfinite(x) and x >= 0 for x in measure['token_CE'])
                assert math.isclose(sum(measure['token_CE']),measure['sum_CE'],rel_tol=1e-6,abs_tol=1e-5)
                assert math.isclose(measure['sum_CE']/measure['tokens'],measure['mean_CE'],rel_tol=1e-6,abs_tol=1e-6)
                for name in ('common_prefix_decision','canonical_opening_decision'):
                    if name not in measure:
                        continue
                    branch = measure[name]['grammar_normalized_branch_mass']
                    assert all(math.isfinite(x) and 0 <= x <= 1.00001 for x in branch.values())
                    assert abs(sum(branch.values())-1) < 1e-5
                    all_mass.append(branch)
            c = data['nonempty']['common_prefix_decision']
            e = data['empty']['common_prefix_decision']
            opening = data['nonempty']['canonical_opening_decision']
            summary['role'][role] = dict(
                common_route_logodds_nonempty_vs_empty=c['canonical_nonempty_route_log_probability']-c['canonical_empty_route_log_probability'],
                canonical_opening_branch_mass=opening['grammar_normalized_branch_mass'],
                common_top_legal=c['top_legal'],
                empty_path_mean_CE=data['empty']['mean_CE'],
                nonempty_path_mean_CE=data['nonempty']['mean_CE'],
                nonempty_first_divergence_CE=data['nonempty']['token_CE'][2],
                empty_first_divergence_CE=data['empty']['token_CE'][2],
                same_prefix_future_suffix_logodds_difference=(c['canonical_nonempty_route_log_probability']-c['canonical_empty_route_log_probability'])-(e['canonical_nonempty_route_log_probability']-e['canonical_empty_route_log_probability']))
        summary['trained_minus_original_route_logodds'] = summary['role']['trained']['common_route_logodds_nonempty_vs_empty']-summary['role']['original']['common_route_logodds_nonempty_vs_empty']
        if item['domain'] == 'development':
            old_path = W/'bottleneck_24h_20261019_v1/summary_objective_v20/summary_generation_10/TRAINED'/(item['uid']+'.output.json')
            old = read(old_path)
            summary['adopted_existing_TRAINED_output_empty'] = not old['parsed_exact_segments']
            summary['adopted_existing_TRAINED_first3_ids'] = old['generated_ids'][:3]
        details.append(summary)
    groups = defaultdict(list)
    for item in details:
        groups[item['stratum']].append(item)
    aggregate = {}
    for key, items in groups.items():
        aggregate[key] = dict(samples=len(items),
            mean_trained_minus_original_route_logodds=sum(x['trained_minus_original_route_logodds'] for x in items)/len(items),
            original_nonempty_canonical_route_wins=sum(x['role']['original']['common_route_logodds_nonempty_vs_empty']>0 for x in items),
            trained_nonempty_canonical_route_wins=sum(x['role']['trained']['common_route_logodds_nonempty_vs_empty']>0 for x in items),
            trained_nonempty_after_canonical_opening_wins=sum(x['role']['trained']['canonical_opening_branch_mass']['nonempty']>x['role']['trained']['canonical_opening_branch_mass']['empty'] for x in items))
    result = dict(status='PASS_FIRST32_PROBABILITY_SCALAR_QA_AND_EXPOSED_FIXED8_DIAGNOSTIC_REVIEW',
        QA_code_ref=ref(__file__),
        registration_ref=ref(root/'registration29.json'),probability_completion_ref=ref(root/'probability_completion29.json'),
        resource_ref=ref(resource_path),unique_ledger_equal=True,forwards=32,source_quality_metrics_not_computed=True,
        details=details,aggregate=aggregate,
        interpretation_limits=['Canonical opening already contains a token seen only on the nonempty target route; conditioning on it is not an unbiased semantic test or a production repair.',
            'Canonical token logodds compare two observed target token routes, not the complete marginal probability of all nonempty outputs.',
            'Greedy decoding follows local token probability; shorter full-answer NLL is not a quality score.',
            'Teacher-forced proposal content is future-masked; numerical prefix differences from sequence length are reported rather than hidden.',
            'Fixed train/development diagnostic samples are historical exposure and do not prove causal uniqueness, generalization or official gain.'],
        optimizer_updates=0,free_generations=0,automatic_production=False,baseline40_47_unchanged=True)
    save(root/'first_probability_output_review30.json',result)
    short = [dict(uid=x['uid'],domain=x['domain'],stratum=x['stratum'],human_empty_fraction=x['human_empty_fraction'],
                  original_route_logodds=x['role']['original']['common_route_logodds_nonempty_vs_empty'],
                  trained_route_logodds=x['role']['trained']['common_route_logodds_nonempty_vs_empty'],
                  trained_nonempty_after_opening_mass=x['role']['trained']['canonical_opening_branch_mass']['nonempty'],
                  original_nonempty_CE=x['role']['original']['nonempty_path_mean_CE'],
                  trained_nonempty_CE=x['role']['trained']['nonempty_path_mean_CE'],
                  trained_empty_CE=x['role']['trained']['empty_path_mean_CE'],
                  adopted_TRAINED_output_empty=x.get('adopted_existing_TRAINED_output_empty')) for x in details]
    print(json.dumps(dict(status=result['status'],aggregate=aggregate,details=short,
                         charged_seconds=resource['charged_seconds'],peak_gpu_mib=resource['sampled_peak_memory_mib'],
                         result_ref=ref(root/'first_probability_output_review30.json')),ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    run(p.parse_args().root)
