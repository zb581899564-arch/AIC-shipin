"""Synthetic lineage gates: no real checkpoint/source/GPU access."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import star_identity_v72 as identity
import star_inference_gpu_v72 as gpu


def reference(name):
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def admissions(scope='resized20'):
    reg = dict(schema=gpu.SCHEMA, scope=scope, model_role='UTILITY_STAR_'+scope, expected_inputs=240,
        expected_sources={'resized20':20, 'resized19':19, 'production':6563}[scope], profile='RESIZED_OBSERVATION_PLANE',
        adapter_weights=reference('adapter1300'), value_weights=reference('value1300'), training_completion=reference('training1300'),
        star_GPU69_code=reference('code69'), star_GPU69_registration=reference('reg69'),
        frozen_GPU55_code=reference('code55'), frozen_GPU55_registration=reference('reg55'),
        old55_STOP=reference('STOP55'), old55_completion=reference('complete55'), old55_progress=reference('progress55'),
        old55_adapter_weights=reference('adapter55'), old55_value_weights=reference('value55'),
        confirm_quality_admission=reference('confirm'), model_config=reference('config'),
        old_TIME=reference('TIME'), old_PAIR=reference('PAIR'), old_CROP=reference('CROP'),
        training_quality_admission=reference('quality70'), identity_code=reference('identity72'))
    if scope == 'production': reg.update(official_source_count=426, affected_video_count=303)
    training = dict(status='COMPLETE_FIXED_FINAL1300_STAR_VALUES_NOT_QUALITY', completed_updates=1300,
        successful_micro=5200, actual_training_forwards=10400, new_completed_updates=800,
        new_successful_micro=3200, actual_new_training_forwards=6400,
        adapter_reload_all288_exact=True, head_reload_exact=True, beta_reload_exact=True,
        inherited_optimizer_exact=True, inherited_trainables_exact=True, inherited_rng_restored=True,
        original55_quality_remains_STOP=True, inherited_completion=reg['old55_completion'], inherited_progress=reg['old55_progress'],
        adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], GPU_registration=reg['star_GPU69_registration'])
    native = dict(status='PASS_STAR_NATIVE20_ONLY', primary='UTILITY', evaluation=dict(quality=dict(admitted=True)),
        confirm_admitted=True, production_admitted=False, fixed_final_checkpoint=True,
        final_update=1300, new_updates=800, adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'],
        training_completion=reg['training_completion'], registration=reg['star_GPU69_registration'],
        inherited_STOP=reg['old55_STOP'], inherited_completion=reg['old55_completion'], inherited_progress=reg['old55_progress'])
    profile = dict(status='PASS_STAR_RESIZED20_PROFILE_ONLY', quality=dict(admitted=True),
        adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], training_completion=reg['training_completion'],
        star_GPU69_registration=reg['star_GPU69_registration'])
    confirm = dict(profile, status='PASS_STAR_RESIZED19_CONFIRM_ONLY')
    production = dict(status='ADMIT_STAR_EXACT_NATIVE_PTS_SPATIAL_ONLY', production_admitted=True,
        confirm_quality_admission=reg['confirm_quality_admission'], adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'])
    if scope == 'production': production.update(expected_sources=6563, observations=6563, official_source_count=426,
        affected_video_count=303, whole426_preserved=True)
    return reg, training, native, profile, confirm, production


def ancestors(reg):
    old = dict(GPU_code=reg['frozen_GPU55_code'], **{k:reg[k] for k in ('model_config','old_TIME','old_PAIR','old_CROP')})
    registration69 = dict(schema='UTILITY_CONNECTED_STAR_CONTINUATION_V69', GPU_code=reg['star_GPU69_code'],
        original_GPU55=reg['frozen_GPU55_registration'], frozen_GPU55_code=reg['frozen_GPU55_code'],
        **{k:reg[k] for k in ('old55_STOP','old55_completion','old55_progress','old55_adapter_weights','old55_value_weights',
            'model_config','old_TIME','old_PAIR','old_CROP')})
    stop = dict(status='STOP_UTILITY_SCREEN20_REJECTED', confirm_admitted=False, training_completion=reg['old55_completion'])
    complete = dict(status='COMPLETE_FIXED_FINAL500_UTILITY_VALUES_NOT_QUALITY', completed_updates=500,
        successful_micro=2000, actual_training_forwards=4000, GPU_registration=reg['frozen_GPU55_registration'],
        progress=reg['old55_progress'], adapter_weights=reg['old55_adapter_weights'], value_weights=reg['old55_value_weights'])
    return registration69, stop, complete, old


class StarIdentityTests(unittest.TestCase):
    def test_1300_is_separate_from_complete500_and_actual_failed55(self):
        reg, training, native, *_ = admissions()
        identity.validate_final1300(reg, training, native)
        lineage = ancestors(reg); identity.validate_ancestry(reg, *lineage)
        for change in (dict(completed_updates=500), dict(new_completed_updates=0),
                dict(GPU_registration=reg['frozen_GPU55_registration']), dict(adapter_weights=reg['old55_adapter_weights']),
                dict(inherited_progress=reference('other')), dict(original55_quality_remains_STOP=False)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                identity.validate_final1300(reg, dict(training, **change), native)
        for change in (dict(status='PASS_UTILITY_SCREEN20_ONLY'), dict(status='STOP_STAR_NATIVE20_REJECTED'),
                dict(final_update=500), dict(registration=reg['frozen_GPU55_registration']), dict(confirm_admitted=False)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                identity.validate_final1300(reg, training, dict(native, **change))
        for index, change in ((0,dict(old55_progress=reference('other'))), (1,dict(status='PASS_UTILITY_SCREEN20_ONLY')),
                (1,dict(confirm_admitted=True)), (2,dict(progress=reference('other'))), (3,dict(old_TIME=reference('other')))):
            changed = list(copy.deepcopy(lineage)); changed[index].update(change)
            with self.subTest(index=index, change=change), self.assertRaises(ValueError):
                identity.validate_ancestry(reg, *changed)

    def test_metadata_check_binds_all_refs_without_opening_progress_tensor(self):
        reg, training, native, *_ = admissions(); lineage = ancestors(reg)
        values = {reg['training_completion']['path']:training, reg['training_quality_admission']['path']:native,
            reg['star_GPU69_registration']['path']:lineage[0], reg['old55_STOP']['path']:lineage[1],
            reg['old55_completion']['path']:lineage[2], reg['frozen_GPU55_registration']['path']:lineage[3]}
        opened=[]; bounded=[]
        def read(path): opened.append(str(path)); return values[str(path).replace('\\','/')]
        def bound(ref):
            bounded.append(ref)
            return Path(identity.__file__).resolve() if ref == reg['identity_code'] else Path(ref['path'])
        with mock.patch.object(identity,'read',side_effect=read), mock.patch.object(identity,'bound',side_effect=bound):
            self.assertEqual(identity.check(reg),(training,native))
        self.assertNotIn(reg['old55_progress']['path'],opened)
        self.assertIn(reg['old55_progress'],bounded)
        self.assertNotIn(reg['adapter_weights']['path'],opened)

    def test_gpu_parses_minimal_cpu_bindings_without_original_evaluation_or_STOP(self):
        reg, training, native, *_ = admissions(); lineage = ancestors(reg)
        captured = {}
        with mock.patch.object(identity,'save',side_effect=lambda p,v:captured.update({p.name:v})):
            identity.write_bindings(Path('/synthetic'), reg, dict(native, unrelated_per_source_GT='MUST_NOT_COPY'))
        self.assertNotIn('unrelated_per_source_GT',captured['native_qualification_binding.json']['quality'])
        reg.update(training_quality_binding=reference('nativebinding'), old55_STOP_binding=reference('stopbinding'))
        values = {reg['training_completion']['path']:training,
            reg['star_GPU69_registration']['path']:lineage[0], reg['old55_completion']['path']:lineage[2],
            reg['frozen_GPU55_registration']['path']:lineage[3],
            reg['training_quality_binding']['path']:captured['native_qualification_binding.json'],
            reg['old55_STOP_binding']['path']:captured['old55_STOP_binding.json']}
        opened = []
        def read(path): opened.append(Path(path).as_posix()); return values[Path(path).as_posix()]
        def bound(r): return Path(identity.__file__).resolve() if r == reg['identity_code'] else Path(r['path'])
        with mock.patch.object(identity,'read',side_effect=read), mock.patch.object(identity,'bound',side_effect=bound):
            self.assertEqual(identity.check_gpu(reg),(training,native))
        self.assertNotIn(reg['training_quality_admission']['path'],opened)
        self.assertNotIn(reg['old55_STOP']['path'],opened)


if __name__ == '__main__': unittest.main()
