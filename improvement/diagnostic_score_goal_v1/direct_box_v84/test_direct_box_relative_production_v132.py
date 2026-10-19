import copy
import unittest

import direct_box_relative_production_v132 as production


def ref(name):
    return dict(path='/synthetic/' + name, sha256='a' * 64)


def registration(n=35):
    r = {key: ref(key) for key in production.REQUIRED_REFS}
    r.update(schema=production.SCHEMA, admitted_arms=['GEOM11'], selection=production.SELECTION,
        official_source_count=426, whole426_protected=True, all_original_times_unchanged=True,
        all_vertical_boxes_unchanged=True, outside_D_boxes_unchanged=True,
        no_nearest_or_interpolation=True, additional_parameters=production.ADDITIONAL_PARAMETERS,
        pipeline_parameters=production.PIPELINE_PARAMETERS, physical_GPU_parameters=production.PHYSICAL_GPU_PARAMETERS,
        hidden_transform=production.HIDDEN_TRANSFORM, policy='TRUST124_THEN_GEOM129_GAIN_STRICTLY_POSITIVE',
        automatic_launch=False, automatic_production=False, expected_sources=n, expected_affected_videos=1)
    r['protected_baseline']['sha256'] = production.BASELINE_SHA
    return r


def domain_fixture():
    rows = [dict(video_id=str(i), targetRatioWH=[16, 9] if i == 0 else [9, 16],
        predictions=[dict(frame=j, bboxes=[0, 0, 160]) for j in range(70)] if i == 0 else
        [dict(frame=0, bboxes=[0, 0, 90])]) for i in range(426)]
    clocks = {'0': dict(video_id='0', source_sha256='1' * 64,
        normalized_exact_pts=[str(j) + '/2' for j in range(70)])}
    all_d = [dict(video_id='0', source_sha256='1' * 64, native_ordinal=j,
        native_pts_exact=str(j) + '/2', observation_index=j) for j in range(70)]
    selected = [dict(**x, source_id='official:0:native:%d' % x['native_ordinal'], role='formal',
        width=320, height=180, baseline_box=[0, 0, 160], original_BASE_observed=True,
        targetRatioWH=[16, 9]) for x in all_d if x['observation_index'] % 2 == 0]
    domain = dict(selection=production.SELECTION, official_source_count=426,
        no_nearest_or_interpolation=True, protected_baseline_sha256=production.BASELINE_SHA,
        all_D=all_d, selected_D=selected, all_D_count=len(all_d), selected_D_count=len(selected),
        all_D_sha256=production.digest(all_d), selected_D_sha256=production.digest(selected),
        affected_video_count=1, pilot_source_ids=[s['source_id'] for s in selected[:32]],
        remaining_source_ids=[s['source_id'] for s in selected[32:]])
    return registration(), domain, selected, rows, clocks


def evidence_fixture():
    r = registration(); models = {k:r[k] for k in production.MODEL_REFS}
    old = dict(models, status='STOP_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC', admitted_arms=[],
        state=r['critic_state'], exact_save_reload=True, additional_parameters=production.ADDITIONAL_PARAMETERS,
        pipeline_parameters=production.PIPELINE_PARAMETERS, evaluations={})
    for scope,n in (('native20',20),('historical19',19)):
        old['evaluations'][scope]=dict(arms=dict(GEOM11=dict(summary=dict(sources=n),
            quality=dict(admitted=True,checks=dict(original=True)),rows=[dict(trust_changed=True,changed=False)])))
    promotion=dict(models,schema='FIXED_GEOM129_POSTHOC_CONTROL_PROMOTION_ONLY',arm='GEOM11',source_result=r['development_result'],state=r['critic_state'],
        posthoc_control_promotion=True,old128_STOP_preserved=True,no_refit=True,development_only=True,new_file_test_only=True,
        fresh8_trials=1,production_admitted=False,pipeline_parameters=production.PIPELINE_PARAMETERS,existing_development={'native20':{},'historical19':{}})
    fresh=dict(models,status=production.FRESH8_PASS,admitted_arms=['GEOM11'],quality=dict(admitted=True,checks=dict(original=True)),summary=dict(sources=8),
        development_result=r['development_result'],critic_state=r['critic_state'],promotion=r['promotion'],pipeline_parameters=production.PIPELINE_PARAMETERS,new_fit=0,automatic_production=False)
    trained=dict(status='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY',completed_updates=778,successful_micro=3112,actual_training_forwards=3112,
        original_successful_updates=20,original_successful_forwards=88,total_adopted_plus_new_updates=798,hidden_transform=production.HIDDEN_TRANSFORM,
        adapter_reload_all288_exact=True,head_reload_all2_exact=True,adapter_weights=r['adapter_weights'],head_weights=r['head_weights'])
    return r,old,promotion,fresh,trained


class ProductionContractTests(unittest.TestCase):
    def test_new_posthoc_promotion_and_true_fresh8_do_not_relabel_old128_stop(self):
        r,old,promotion,fresh,trained=evidence_fixture()
        result=production.validate_lineage(r,old,promotion,fresh,trained)
        self.assertFalse(result['execution_supported'])
        self.assertEqual(old['admitted_arms'],[])
        for what in ('old_pass','fresh_stop','new_state','refit'):
            rr,oo,pp,ff,tt=copy.deepcopy((r,old,promotion,fresh,trained))
            if what=='old_pass':oo['status']='PASS_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC'
            elif what=='fresh_stop':ff['status']='STOP_FRESH8_FIXED_GEOM129_FILE_CONFIRMATION_V134'
            elif what=='new_state':ff['critic_state']=ref('another_state')
            else:pp['no_refit']=False
            with self.subTest(what=what),self.assertRaises(ValueError):production.validate_lineage(rr,oo,pp,ff,tt)

    def test_valid_owner_metadata_allows_repeated_video_hash_and_d_is_not_426(self):
        r, d, sources, rows, clocks = domain_fixture()
        report = production.validate_owner_domain(r, d, sources, rows, clocks)
        self.assertEqual(report['sources'], 35)
        self.assertEqual(report['official_source_count'], 426)
        self.assertEqual(report['affected_video_count'], 1)
        self.assertFalse(report['execution_supported'])

    def test_owner_pts_original_box_and_selected_intersection_are_strict(self):
        for mutation in ('pts', 'box', 'missing_even', 'duplicate_observation'):
            r, d, sources, rows, clocks = domain_fixture()
            if mutation == 'pts':
                d['all_D'][0]['native_pts_exact'] = '1/100'
            elif mutation == 'box':
                sources[0]['baseline_box'] = [1, 0, 160]
            elif mutation == 'missing_even':
                sources.pop(); r['expected_sources'] -= 1
                d['selected_D_count'] -= 1; d['remaining_source_ids'].pop()
            else:
                d['all_D'][1]['observation_index'] = 0
            d['all_D_sha256'] = production.digest(d['all_D'])
            d['selected_D_sha256'] = production.digest(d['selected_D'])
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                production.validate_owner_domain(r, d, sources, rows, clocks)

    def test_source_order_and_owner_id_cannot_be_relabelled(self):
        for mutation in ('order', 'owner'):
            r, d, sources, rows, clocks = domain_fixture()
            if mutation == 'order':
                sources[0], sources[1] = sources[1], sources[0]
            else:
                sources[0]['source_id'] = 'whole_video:0'
            d['selected_D_sha256'] = production.digest(d['selected_D'])
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                production.validate_owner_domain(r, d, sources, rows, clocks)

    def test_pilot32_exact_remaining_never_schedules_successful_owners(self):
        _, d, sources, _, _ = domain_fixture()
        first = production.stage_partition(d, sources, stage='pilot32')
        accepted = dict(status='PASS_RELATIVE132_PILOT32_FIRST_RAW_CPU_QA', owner_ids=first['owner_ids'],
            new_forward_calls=32, first_input_QA_complete=True, first_output_QA_complete=True)
        rest = production.stage_partition(d, sources, stage='remaining', accepted_pilot=accepted)
        self.assertEqual(first['scheduled_new_owners'], 32)
        self.assertEqual(rest['scheduled_new_owners'], 3)
        self.assertFalse(set(first['owner_ids']) & set(rest['owner_ids']))
        self.assertTrue(rest['requires_separate_budget_and_execution_admission'])
        self.assertFalse(rest['execution_supported'])
        with self.assertRaises(ValueError):
            production.stage_partition(d, sources, stage='pilot32', accepted_pilot=accepted)
        with self.assertRaises(ValueError):
            production.stage_partition(d, sources, stage='remaining')

    def test_overlay_preserves_vertical_outside_d_and_every_original_time(self):
        _, _, sources, rows, _ = domain_fixture()
        after = copy.deepcopy(rows); after[0]['predictions'][0]['bboxes'] = [2, 0, 160]
        report = production.validate_protected_overlay(rows, after, sources)
        self.assertEqual(report['changed_owners'], [('0', 0)])
        self.assertFalse(report['independent11strict_verified'])
        self.assertFalse(report['package_qualified'])
        for mutation in ('vertical', 'outside', 'time'):
            bad = copy.deepcopy(after)
            if mutation == 'vertical':
                bad[1]['predictions'][0]['bboxes'] = [1, 0, 90]
            elif mutation == 'outside':
                bad[0]['predictions'][1]['bboxes'] = [1, 0, 160]
            else:
                bad[0]['predictions'][0]['frame'] = 999
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                production.validate_protected_overlay(rows, bad, sources)

    def test_schema_rejects_incomplete_parameter_count_automatic_actions_and_path_escape(self):
        for key, value in (('pipeline_parameters', 8790237452), ('automatic_launch', True),
                           ('expected_affected_videos', 427), ('official_source_count', 35)):
            r = registration(); r[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                production.validate_schema(r)
        r = registration(); r['critic_state']['path'] = '/synthetic/../unbound'
        with self.assertRaises(ValueError):
            production.validate_schema(r)


if __name__ == '__main__':
    unittest.main()
