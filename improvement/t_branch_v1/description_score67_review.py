"""First source-level interpretation of completed paired likelihood diagnostics."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from collections import defaultdict
import math

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'description_score67'


def main():
    cpu = read(ROOT / 'description_probe66/CPU_completion.json')
    gpu = read(OUT / 'GPU_completion.json')
    if set(gpu['outputs']) != set(cpu['tasks']) or gpu['actual_new_causal_TF_calls'] != cpu['maximum_first_TF_calls']:
        raise ValueError('First full task/role matrix incomplete')
    likelihood = {}; accepted = []
    for key, outputs in gpu['outputs'].items():
        if set(outputs) != {'BASE', 'TIME'}:
            raise ValueError('Incomplete original model-role pair')
        likelihood[key] = {}
        for role, refs in outputs.items():
            proof = read(check(refs['CPU'])); retired = read(check(refs['retirement']))
            if (proof['input_key'] != key or proof['model_role'] != role or proof['raw_projection'] != refs['raw']
                    or retired['first_CPU_proof'] != refs['CPU']):
                raise ValueError('Accepted first full-vocabulary CPU proof binding differs')
            check(refs['raw']); accepted.append(refs['CPU'])
            likelihood[key][role] = proof['mean_logp']
    groups = defaultdict(list)
    cases = []
    for case in cpu['cases']:
        row = {key: case[key] for key in ['example_id', 'source', 'role', 'publisher']}
        row['margins'] = {role: {modality: likelihood[case['variants'][modality + '_correct']][role]
            - likelihood[case['variants'][modality + '_wrong']][role] for modality in ['V', 'AV']}
            for role in ['BASE', 'TIME']}
        cases.append(row); groups[case['source']].append(row)
    sources = {}
    for sid, rows in groups.items():
        sources[sid] = dict(role=rows[0]['role'], publisher=rows[0]['publisher'], targets=len(rows),
            mean_matched_minus_misaligned_logp={role: {modality: math.fsum(r['margins'][role][modality]
                for r in rows) / len(rows) for modality in ['V', 'AV']} for role in ['BASE', 'TIME']})
    save(OUT / 'review.json', dict(state='COMPLETE_HUMAN_CONTENT_MODALITY_ROLE_DIAGNOSTIC_NOT_CANDIDATE_QUALITY',
        per_source=sources, per_example=cases, actual_first_TF_calls=len(accepted), first_CPU_proofs=accepted,
        all_original_weights_unchanged=True, source_roles_historically_exposed=True,
        margins_are_conditional_human_text_not_native_selection_or_official_F1=True,
        no_automatic_training_or_production_admission=True, new_packages=0,
        next='Use matched content margins and BASE/TIME differences to choose one supported mechanism; do not scan prompts or infer highlight quality from likelihood'))


if __name__ == '__main__':
    main()
