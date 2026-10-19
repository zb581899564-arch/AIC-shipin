"""SYNTHETIC adoption contracts, never evidence about actual Linux QA or weights.

All files are temporary metadata/text fixtures.  The formal fixture has exactly
426 synthetic sources and 522 windows.  No model can be loaded or called.  The
real JSON/EOS/native-PTS membership checks execute with a character tokenizer;
only validate_token_path is mocked.  Actual Qwen tokenizer/grammar compatibility
is NOT verified by this suite and remains an explicit execution prerequisite.
The 43-window check-adoption tests mock the inherited adoption delegate itself,
so they verify delegation/coverage/failure propagation, not repeat its old QA.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import adoption
from .contracts import reference, save_new, strict_load


FIXTURE = "SYNTHETIC_CONTENT_CHOICE_ADOPTION_TEST_NOT_REAL_QA"


class CharacterTokenizer:
    """Only a reversible test alphabet; never identified as a Qwen tokenizer."""
    def encode(self, text):
        return [ord(character) + 100 for character in text]

    def decode(self, ids, **kwargs):
        return "".join(chr(token - 100) for token in ids)


class NoModelRuntime:
    eos = 99999

    def __init__(self, base):
        self.base_before = deepcopy(base)
        self.tokenizer = CharacterTokenizer()
        self.model_calls = 0

    def forbidden(self, *args, **kwargs):
        self.model_calls += 1
        raise AssertionError("SYNTHETIC ADOPTION MUST NOT LOAD OR CALL A MODEL")

    load = generate = generate_sample = score_features = score = forbidden


class Journal:
    def __init__(self):
        self.rows = []
        self.context = {}

    def __call__(self, event, value):
        self.rows.append((event, value))


class Budget:
    def __init__(self): self.calls = 0
    def check(self): self.calls += 1


class FormalFixture:
    """Immutable shared synthetic origin; each scenario writes new child refs."""
    def __init__(self, root):
        self.root = Path(root)
        self.counter = 0
        self.base = dict(sha256=hashlib.sha256(b"SYNTHETIC_BASE_IDENTITY_NOT_MODEL_BYTES").hexdigest(),
                         parameters=8767123696)
        self.weights = self.put("origin/SYNTHETIC_TIME_IDENTITY.txt", b"No model weights are stored in this fixture")
        self.acceptance = self.save("origin/input_acceptance.json", dict(fixture=FIXTURE))
        config_ref = self.save("origin/model_config.json", dict(fixture=FIXTURE, expected_base_sha256=self.base["sha256"]))
        self.registration = self.save("origin/registration.json", dict(fixture=FIXTURE,
            first_input_acceptance_ref=self.acceptance, original_TIME_ref=self.weights, model_config_ref=config_ref))
        self.restoration = self.save("origin/TIME_restoration.json", dict(fixture=FIXTURE,
            status="PASS_ORIGINAL_TIME_ROLE_AND_FROZEN_FLAGS_RESTORED_41", model_role="TIME",
            restored_trainable_parameters=0, restored_disabled_layers=0, all144_TIME_layers_enabled=True,
            optimizer_updates=0, model_forwards_in_restoration=0))
        self.sources, self.requests, self.request_refs, self.clocks = {}, {}, {}, {}
        self.outputs, self.details = [], []
        tokenizer = CharacterTokenizer()
        for number in range(426):
            sid = str(number)
            source_sha = hashlib.sha256(("SYNTHETIC_SOURCE_" + sid).encode()).hexdigest()
            clock = dict(fixture=FIXTURE, source_sha256=source_sha,
                normalized_exact_pts=["0", "1/2", "1", "3/2"], physical_end_exact="2")
            clock_ref = self.save("origin/clocks/" + sid + ".json", clock)
            self.sources[sid] = dict(id=sid, group="production", source_sha256=source_sha, clock_ref=clock_ref)
            self.clocks[sid] = clock
            ranges = [(0, 1), (1, 2)] if number < 96 else [(0, 2)]
            for index, (start, end) in enumerate(ranges):
                uid = "SYN_" + sid.zfill(3) + "_W" + str(index)
                prefix_signature = dict(shape=[1, 3], dtype="torch.int64",
                    sha256=hashlib.sha256(("SYNTHETIC_PREFIX_" + uid).encode()).hexdigest())
                request = dict(fixture=FIXTURE, uid=uid, sid=sid, source_sha256=source_sha,
                    source_clock_ref=clock_ref, plan=dict(window_start_exact=str(start), window_end_exact=str(end)),
                    input_signature={"input_ids": prefix_signature})
                request_ref = self.save("origin/requests/" + uid + ".json", request)
                self.requests[uid], self.request_refs[uid] = request, request_ref
                empty = uid == "SYN_000_W0"
                text = '{"segments":[]}' if empty else '{"segments":[[0,0.5]]}'
                ids = tokenizer.encode(text) + [NoModelRuntime.eos]
                raw = dict(fixture=FIXTURE, uid=uid, sid=sid, request_ref=request_ref,
                    generated_ids=ids, model_role="TIME", model_weights_ref=self.weights,
                    actual_prefix_signature={"input_ids": prefix_signature},
                    expected_prefix_signature={"input_ids": prefix_signature})
                raw_ref = self.save("origin/raw/" + uid + ".json", raw)
                output = dict(fixture=FIXTURE, uid=uid, sid=sid, request_ref=request_ref,
                    generated_ids=ids, raw_text=text, raw_token_ref=raw_ref, model_role="TIME",
                    model_weights_ref=self.weights, adapter_disabled_actual_forward=False, forward_role_flag_checks=1)
                output_ref = self.save("origin/outputs/" + uid + ".json", output)
                self.outputs.append(output_ref)
                self.details.append(dict(uid=uid, sid=sid, output_ref=output_ref,
                    native_ranges=[] if empty else [[start * 2, start * 2 + 1]]))
        assert len(self.sources) == 426 and len(self.requests) == len(self.outputs) == 522
        self.base_ref = self.save("origin/BASE_NOT_A_CONTROL.json", dict(fixture=FIXTURE,
            model_role="BASE", status="SYNTHETIC_BASE_SENTINEL_MUST_NOT_BE_CONSUMED",
            adapter_disabled_actual_forward=True))
        self.store = SimpleNamespace(scope="production", workspace=self.root,
            source_ids=tuple(self.sources), case_ids=tuple(self.requests), sources=self.sources,
            requests=self.requests, request_refs=self.request_refs, clocks=self.clocks)
        self.manifest = dict(workspace_root=str(self.root),
            model_spec=dict(adapter_weights=self.weights, base_sha256=self.base["sha256"]),
            scopes={"production": dict(input_acceptance_ref=self.acceptance)})

    def put(self, name, value):
        path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream: stream.write(value)
        return reference(path)

    def save(self, name, value):
        return self.put(name, (json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n").encode())

    def scenario(self, *, raw_change=None, output_change=None, detail_change=None,
                 complete_change=None, qa_change=None, resource_change=None, mapping=False):
        self.counter += 1
        stem = "scenario_" + str(self.counter).zfill(3) + "/"
        outputs, details = deepcopy(self.outputs), deepcopy(self.details)
        first = strict_load(outputs[0]["path"])
        raw = strict_load(first["raw_token_ref"]["path"])
        if raw_change: raw_change(raw)
        first["raw_token_ref"] = self.save(stem + "first_raw.json", raw)
        if output_change: output_change(first)
        outputs[0] = self.save(stem + "first_output.json", first)
        details[0]["output_ref"] = outputs[0]
        if detail_change: detail_change(details[0])
        complete = dict(fixture=FIXTURE, status="PASS_ALL426_FORMAL_SUMMARY_GENERATIONS_41", model_role="TIME",
            sources=426, windows=522, optimizer_updates=0, labels_read=False,
            role_terminal="completed", role_exit_code=0, adapter_disabled_actual_forward=False,
            old_TIME_unchanged=True, all_parameter_flags_unchanged=True,
            original_TIME_exact_FP32_bits_unchanged=True, TIME_flags_restored=True,
            base_fingerprint=self.base, model_weights_ref=self.weights, input_acceptance_ref=self.acceptance,
            registration_ref=self.registration, outputs=outputs, TIME_frozen_flag_restoration_ref=self.restoration)
        if complete_change: complete_change(complete)
        complete_ref = self.save(stem + "TIME_completion.json", complete)
        role_refs = {"TIME": complete_ref, "BASE": self.base_ref} if mapping else [complete_ref, self.base_ref]
        top = self.save(stem + "top_completion.json", dict(fixture=FIXTURE,
            status="PASS_BOTH_ORIGINAL_TIME_BASE_FORMAL_GENERATIONS_41", optimizer_updates=0,
            labels_read=False, sources=426, windows_per_role=522, roles=["TIME", "BASE"],
            original_TIME_ref=self.weights, registration_ref=self.registration, role_completion_refs=role_refs))
        resource = dict(fixture=FIXTURE, status="completed", exit_code=0)
        if resource_change: resource_change(resource)
        resource_ref = self.save(stem + "resource.json", resource)
        qa = dict(fixture=FIXTURE, status="PASS_BOTH_ROLES_FIRST_INDEPENDENT_TOKEN_GRAMMAR_NATIVE_QA_41",
            unique_ledger_equal=True, invalid_outputs=0, sources=426, windows_per_role=522, total_outputs=1044,
            resource_ref=resource_ref, registration_ref=self.registration, completion_ref=top,
            roles={"TIME": dict(completion_ref=complete_ref, outputs=complete["outputs"], details=details),
                   "BASE": dict(completion_ref=self.base_ref, outputs=[], details=[],
                                fixture="SYNTHETIC_UNREAD_BASE_SENTINEL_NOT_FULL_BASE_QA")})
        if qa_change: qa_change(qa)
        qa_ref = self.save(stem + "QA.json", qa)
        directory = self.root / stem / "new_adoption"
        directory.mkdir()
        return qa_ref, directory


class AdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="aic_adoption_SYNTHETIC_")
        cls.fixture = FormalFixture(cls.temp.name)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.runtime = NoModelRuntime(self.fixture.base)
        self.journal, self.budget = Journal(), Budget()
        # This mock is explicit: real Qwen grammar/tokenizer compatibility is
        # outside this metadata adoption suite. JSON/native mapping remains real.
        gate = patch.object(adoption, "validate_token_path", return_value=None)
        self.grammar_boundary = gate.start()
        self.addCleanup(gate.stop)

    def formal(self, scenario, *, store=None, manifest=None):
        qa, directory = scenario
        return adoption.adopt_formal(self.runtime, store or self.fixture.store,
            manifest or self.fixture.manifest, qa["path"], directory,
            self.journal, self.budget, object(), [])

    def check_fixture(self):
        self.fixture.counter += 1
        directory = self.fixture.root / ("check_scenario_" + str(self.fixture.counter))
        directory.mkdir()
        cases = tuple("SYN_CHECK_" + str(i).zfill(2) for i in range(43))
        store = SimpleNamespace(scope="check", workspace=self.fixture.root,
            source_ids=tuple("SYN_CHECK_SOURCE_" + str(i) for i in range(8)), case_ids=cases)
        return directory, store

    def test_check43_delegates_once_without_loading_a_model(self):
        directory, store = self.check_fixture()
        captured = {}
        def inherited(runtime, actual_store, ids, manifest, out, journal, budget, grammar, vocabulary):
            captured.update(runtime=runtime, store=actual_store, ids=ids, out=out)
            return [save_new(out / (uid + ".json"), dict(fixture=FIXTURE, uid=uid,
                status="ACCEPTED", new_model_calls=0, inherited_boundary_mocked=True)) for uid in ids]
        with patch.object(adoption, "adopt_reference", side_effect=inherited) as delegated:
            result = adoption.adopt_check(self.runtime, store, {}, directory,
                                          self.journal, self.budget, object(), [])
        self.assertEqual(delegated.call_count, 1)
        self.assertEqual(captured["ids"], list(store.case_ids))
        self.assertIs(captured["store"], store)
        self.assertEqual(captured["out"], directory / "adopted_original_time")
        self.assertEqual(set(result), set(store.case_ids))
        self.assertEqual(self.runtime.model_calls, 0)

    def test_check_missing_control_or_delegate_failure_cannot_regenerate(self):
        for kind in ("missing", "foreign", "failed"):
            with self.subTest(kind=kind):
                directory, store = self.check_fixture()
                def inherited(runtime, actual_store, ids, manifest, out, journal, budget, grammar, vocabulary):
                    if kind == "failed": raise ValueError("SYNTHETIC_HISTORICAL_ORIGIN_FAILED")
                    retained = ids[:-1] if kind == "missing" else ids[:-1] + ["SYN_FOREIGN"]
                    return [save_new(out / (uid + ".json"), dict(fixture=FIXTURE, uid=uid)) for uid in retained]
                with patch.object(adoption, "adopt_reference", side_effect=inherited) as delegated:
                    with self.assertRaises(ValueError):
                        adoption.adopt_check(self.runtime, store, {}, directory,
                                             self.journal, self.budget, object(), [])
                    self.assertEqual(delegated.call_count, 1)
                self.assertEqual(self.runtime.model_calls, 0)

    def test_formal522_all426_time_controls_actual_native_parse_no_base_read_or_model(self):
        scenario = self.fixture.scenario()
        actual_load = adoption.strict_load
        with patch.object(adoption, "strict_load", wraps=actual_load) as reads:
            result = self.formal(scenario)
        self.assertEqual(set(result), set(self.fixture.store.case_ids))
        self.assertEqual(len(result), 522)
        loaded = [strict_load(ref["path"]) for ref in result.values()]
        self.assertEqual(len({row["source_id"] for row in loaded}), 426)
        self.assertTrue(all(row["new_model_calls"] == 0 and row["actual_model_call"] is False
                            and row["adopted_historical_model_call"] is True for row in loaded))
        self.assertEqual(sum(row["legal_empty"] for row in loaded), 1)
        by_uid = {row["uid"]: row for row in loaded}
        self.assertEqual(by_uid["SYN_000_W0"]["selected_ordinals"], [])
        self.assertEqual(by_uid["SYN_000_W1"]["selected_ordinals"], [2])
        self.assertEqual(by_uid["SYN_096_W0"]["selected_ordinals"], [0])
        read_paths = {str(Path(call.args[0]).resolve()) for call in reads.call_args_list}
        self.assertNotIn(self.fixture.base_ref["path"], read_paths)
        self.assertEqual(self.budget.calls, 522)
        self.assertEqual(len(self.journal.rows), 522)
        self.assertTrue(all(event == "formal_control_adopted" and row["new_model_calls"] == 0 for event, row in self.journal.rows))
        self.assertEqual(self.grammar_boundary.call_count, 522)
        self.assertEqual(self.runtime.model_calls, 0)

    def test_formal_role_completion_mapping_format_is_supported(self):
        result = self.formal(self.fixture.scenario(mapping=True))
        self.assertEqual(len(result), 522)
        self.assertEqual(self.runtime.model_calls, 0)

    def test_formal_incomplete_or_duplicate_denominators_fail_closed(self):
        for kind in ("sources", "windows", "missing_output", "duplicate_output", "foreign_uid"):
            with self.subTest(kind=kind):
                store = self.fixture.store
                kwargs = {}
                if kind in ("sources", "windows"):
                    store = SimpleNamespace(**vars(store))
                    key = "source_ids" if kind == "sources" else "case_ids"
                    setattr(store, key, getattr(store, key)[:-1])
                elif kind == "missing_output":
                    kwargs["complete_change"] = lambda value: value["outputs"].pop()
                elif kind == "duplicate_output":
                    kwargs["complete_change"] = lambda value: value["outputs"].__setitem__(1, value["outputs"][0])
                else:
                    kwargs["output_change"] = lambda value: value.update(uid="SYN_FOREIGN")
                with self.assertRaises(ValueError):
                    self.formal(self.fixture.scenario(**kwargs), store=store)
                self.assertEqual(self.runtime.model_calls, 0)

    def test_formal_failed_job_invalid_qa_or_unfrozen_time_cannot_be_adopted(self):
        changes = (
            dict(resource_change=lambda value: value.update(status="failed", exit_code=1)),
            dict(resource_change=lambda value: value.update(exit_code=None)),
            dict(qa_change=lambda value: value.update(invalid_outputs=1)),
            dict(qa_change=lambda value: value.update(unique_ledger_equal=False)),
            dict(complete_change=lambda value: value.update(role_exit_code=1)),
            dict(complete_change=lambda value: value.update(optimizer_updates=1)),
            dict(complete_change=lambda value: value.update(original_TIME_exact_FP32_bits_unchanged=False)),
            dict(complete_change=lambda value: value.update(adapter_disabled_actual_forward=True)),
        )
        for index, kwargs in enumerate(changes):
            with self.subTest(case=index), self.assertRaises(ValueError):
                self.formal(self.fixture.scenario(**kwargs))
        self.assertEqual(self.grammar_boundary.call_count, 0)
        self.assertEqual(self.runtime.model_calls, 0)

    def test_base_role_cannot_be_mislabelled_as_time_control(self):
        def substitute(qa):
            qa["roles"]["TIME"]["completion_ref"] = self.fixture.base_ref
        for kwargs in (dict(qa_change=substitute),
                       dict(output_change=lambda value: value.update(model_role="BASE")),
                       dict(output_change=lambda value: value.update(adapter_disabled_actual_forward=True))):
            with self.subTest(kwargs=list(kwargs)), self.assertRaises(ValueError):
                self.formal(self.fixture.scenario(**kwargs))
        self.assertEqual(self.grammar_boundary.call_count, 0)
        self.assertEqual(self.runtime.model_calls, 0)

    def test_raw_prefix_tokens_request_and_weights_bindings_are_checked(self):
        other = self.fixture.request_refs["SYN_000_W1"]
        changes = (
            dict(raw_change=lambda value: value["actual_prefix_signature"]["input_ids"].update(sha256="f" * 64)),
            dict(raw_change=lambda value: value["generated_ids"].append(123)),
            dict(raw_change=lambda value: value.update(request_ref=other)),
            dict(raw_change=lambda value: value.update(model_weights_ref=self.fixture.base_ref)),
            dict(output_change=lambda value: value.update(request_ref=other)),
            dict(output_change=lambda value: value.update(model_weights_ref=self.fixture.base_ref)),
        )
        for index, kwargs in enumerate(changes):
            with self.subTest(case=index), self.assertRaises(ValueError):
                self.formal(self.fixture.scenario(**kwargs))
        self.assertEqual(self.grammar_boundary.call_count, 0)
        self.assertEqual(self.runtime.model_calls, 0)

    def test_decoded_text_eos_and_original_native_qa_disagreement_are_rejected(self):
        changes = (
            dict(output_change=lambda value: value.update(raw_text='{"segments":[[0,0.5]]}')),
            dict(raw_change=lambda value: value["generated_ids"].pop(),
                 output_change=lambda value: value["generated_ids"].pop()),
            dict(detail_change=lambda value: value.update(native_ranges=[[1, 2]])),
        )
        for index, kwargs in enumerate(changes):
            with self.subTest(case=index), self.assertRaises(ValueError):
                self.formal(self.fixture.scenario(**kwargs))
        self.assertEqual(self.runtime.model_calls, 0)

    def test_original_base_or_adapter_identity_mismatch_prevents_adoption(self):
        self.runtime.base_before["parameters"] += 1
        with self.assertRaisesRegex(ValueError, "same frozen parameters"):
            self.formal(self.fixture.scenario())
        self.runtime.base_before = deepcopy(self.fixture.base)
        manifest = deepcopy(self.fixture.manifest)
        manifest["model_spec"]["adapter_weights"] = self.fixture.base_ref
        with self.assertRaisesRegex(ValueError, "model/input/role identity"):
            self.formal(self.fixture.scenario(), manifest=manifest)
        self.assertEqual(self.runtime.model_calls, 0)

    def test_hash_changed_raw_metadata_is_rejected_without_fallback(self):
        scenario = self.fixture.scenario()
        qa = strict_load(scenario[0]["path"])
        first = strict_load(qa["roles"]["TIME"]["outputs"][0]["path"])
        raw_path = Path(first["raw_token_ref"]["path"])
        # Deliberate corruption is isolated to this new synthetic scenario.
        raw_path.write_text(raw_path.read_text() + " ")
        with self.assertRaises(ValueError):
            self.formal(scenario)
        self.assertEqual(self.runtime.model_calls, 0)

    def test_actual_json_to_vfr_native_mapping_with_only_grammar_boundary_mocked(self):
        clock = dict(normalized_exact_pts=["0", "1/10", "1/3", "7/10"], physical_end_exact="1")
        request = dict(plan=dict(window_start_exact="1/10", window_end_exact="1"))
        text = '{"segments":[[0,0.3]]}'
        ids = self.runtime.tokenizer.encode(text) + [self.runtime.eos]
        selected = adoption.validate_answer(self.runtime, request, clock, text, ids, object(), [])
        self.assertEqual(selected, [1, 2])
        self.assertEqual(self.grammar_boundary.call_args.args[3], Fraction(9, 10))
        self.assertEqual(self.runtime.model_calls, 0)


if __name__ == "__main__":
    unittest.main()
