#!/usr/bin/env python3
"""CPU contract tests; synthetic numerical fixtures only."""
from __future__ import annotations
import argparse
import copy
import io
import json
import math
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

import a_contract as legacy
from pts_contract import *
from exact_pts import exact_native_pts, verify_native_encoding
from test_helpers import make_fixture, temporal_for

HERE = Path(__file__).resolve().parent


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cpu_pts_fixture_", dir=HERE)
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.manifest, self.registry, self.path = make_fixture(self.root, native_ids=("7",))
        self.clocks = load_clocks(self.manifest, self.path, legacy.sha(self.path))

    def test_registry_uses_separate_cfr_end_contract(self):
        self.assertFalse(self.registry["records"][0]["decord_binding"]["end_pass"])
        self.assertEqual(self.clocks["0"]["branch"], BRANCH_CFR)
        self.assertEqual(self.clocks["7"]["branch"], BRANCH_NATIVE)

    def test_native_plan_half_open_exact_boundaries(self):
        c = self.clocks["7"]
        plan = native_clip_plan(c, float(c["pts"][2]), float(c["pts"][8]))
        self.assertEqual(plan["source_frame_ids"], list(range(2,8)))
        self.assertEqual(plan["exact_window_local_pts"][0], 0.0)

    def test_native_uniform_max64_preserves_frame_ordinal_sampling(self):
        c = self.clocks["7"]
        p = native_clip_plan(c, 0.0, float(c["duration"]))
        self.assertEqual(len(p["source_frame_ids"]), 64)
        self.assertEqual((p["source_frame_ids"][0],p["source_frame_ids"][-1]),(0,64))
        self.assertEqual(p["source_frame_ids"], sorted(set(p["source_frame_ids"])))

    def test_native_each_frame_time_roundtrip(self):
        c = self.clocks["7"]
        for i in range(len(c["pts"])-1):
            start, end = float(c["pts"][i]), float(c["pts"][i+1])
            self.assertEqual(native_segment_frames(c,0.0,float(c["duration"]),[[start,end]]),[i])

    def test_native_last_frame_endpoint(self):
        c = self.clocks["7"]
        self.assertEqual(native_segment_frames(c,0.0,float(c["duration"]),
                         [[float(c["pts"][-1]),float(c["duration"])]]),[64])

    def test_gap_contains_no_frame_blocks(self):
        c = self.clocks["7"]
        gap_start = float(c["pts"][32])+0.01
        gap_end = float(c["pts"][33])-0.01
        with self.assertRaisesRegex(ValueError,"NO_SOURCE_FRAMES"):
            native_clip_plan(c,gap_start,gap_end)

    def test_empty_and_zero_frame_segment_block(self):
        c = self.clocks["7"]
        for segments in ([], [[0.001,0.002]]):
            with self.assertRaises(ValueError):
                native_segment_frames(c,0.0,float(c["duration"]),segments)

    def test_30s_no_overlap_and_short_tail_unchanged(self):
        c = dict(self.clocks["7"],duration=Fraction(601,10))
        row = dict(self.manifest["records"][7],scope_end_sec=60.1)
        self.assertEqual(window_schedule(row,"REMATCH426",c),[(0.0,30.0),(30.0,60.0)])

    def test_mixed_branch_cfr_selected_keys_same_as_original(self):
        temporal = temporal_for(self.manifest,self.clocks)
        actual = select_frames(self.manifest,temporal,self.clocks)
        original_manifest = legacy_manifest(self.manifest)
        original_temporal = copy.deepcopy(temporal)
        original_temporal[7]["windows"][0]["end_sec"] = original_manifest["records"][7]["scope_end_sec"]
        original_temporal[7]["windows"][0]["parsed_segments"] = [[0.0,original_manifest["records"][7]["scope_end_sec"]]]
        expected = legacy.select_frames(original_manifest,original_temporal)
        self.assertEqual([r for r in actual if r["video_id"]!="7"],[r for r in expected if r["video_id"]!="7"])

    def test_all_cfr_original_selected_and_prediction_bytes(self):
        with tempfile.TemporaryDirectory(prefix="cpu_cfr_fixture_",dir=HERE) as other:
            manifest, registry, path = make_fixture(Path(other))
            clocks = load_clocks(manifest,path,legacy.sha(path))
            temporal = temporal_for(manifest,clocks)
            expected = legacy.select_frames(legacy_manifest(manifest),temporal)
            actual = select_frames(manifest,temporal,clocks)
            self.assertEqual(json.dumps(actual,sort_keys=True),json.dumps(expected,sort_keys=True))
            def compose_for(selected):
                shots, requests, outputs = [], [], []
                for row in manifest["records"]:
                    frames = [r["source_frame"] for r in selected if r["video_id"]==row["video_id"]]
                    for f in frames:
                        shots.append({"video_id":row["video_id"],"source_frame":f,"is_shot_start":f==frames[0]})
                    for f in legacy.anchor_frames(frames,8):
                        request = {"video_id":row["video_id"],"source_frame":f,"anchor_request_sha256":"a"*64,
                                   "expected_pixel_sha256":"b"*64}
                        requests.append(request)
                        outputs.append({**request,"status":"MODEL_OK","used_fallback":False,
                                        "spatial_source":"QWEN_ANCHOR_SAME_FRAME","decoded_pixel_sha256":"b"*64,
                                        "box_xyw":[14,0,36]})
                return legacy.compose(legacy_manifest(manifest),selected,shots,requests,outputs)[0]
            self.assertEqual(json.dumps(compose_for(actual),sort_keys=True),json.dumps(compose_for(expected),sort_keys=True))

    def reject_registry(self, change):
        payload = copy.deepcopy(self.registry)
        change(payload)
        path = self.root/"changed_registry.json"
        legacy.write_json(path,payload)
        manifest = copy.deepcopy(self.manifest)
        manifest["clock_registry"]={"path":str(path),"sha256":legacy.sha(path)}
        with self.assertRaises(ValueError):
            load_clocks(manifest,path,legacy.sha(path))

    def test_bad_identity_stops(self):
        self.reject_registry(lambda r:r["records"][7].__setitem__("identity_pass",False))

    def test_native_missing_endpoint_stops(self):
        self.reject_registry(lambda r:r["records"][7].__setitem__("native_clock_usable",False))

    def test_native_packet_end_binding_stops(self):
        self.reject_registry(lambda r:r["records"][7]["decord_binding"].__setitem__("end_pass",False))

    def test_cfr_old_interval_gate_stops(self):
        self.reject_registry(lambda r:r["records"][0]["decord_binding"].__setitem__("legacy_interval_pass",False))

    def test_branch_cannot_be_chosen_by_output(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["records"][7]["clock_branch"]=BRANCH_CFR
        with self.assertRaises(ValueError):
            load_clocks(manifest,self.path,legacy.sha(self.path))

    def test_missing_source_denominator_stops(self):
        self.reject_registry(lambda r:r["records"].pop())

    def test_array_byte_identity_stops(self):
        path=Path(self.registry["records"][0]["clock_arrays"]["path"])
        path.write_text(path.read_text()+" ",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"ARRAY_SHA"):
            load_clocks(self.manifest,self.path,legacy.sha(self.path))

    def test_snapshot_config_vendor_unchanged(self):
        from run_pts import verify_vendor
        verify_vendor()

    def processor(self):
        class Fake:
            def _calculate_timestamps(self,ids,fps,merge_size=2):
                return ["ORIGINAL"]
            class Tokenizer:
                text=""
                def decode(self,ids,skip_special_tokens=False):
                    return self.text
            tokenizer=Tokenizer()
        return Fake()

    def plan(self,n):
        return {"source_frame_ids":list(range(n)),"source_relative_pts":[.01+.04*i for i in range(n)],
                "window_start":0.0}

    def test_processor_odd_padding_final_pair_is_duplicate_last_pts(self):
        processor=self.processor()
        original=processor._calculate_timestamps
        with exact_native_pts(processor,self.plan(3),25.0) as r:
            times=processor._calculate_timestamps([0,1,2],25.0,2)
            self.assertAlmostEqual(times[0],.03)
            self.assertAlmostEqual(times[1],.09)
            processor.tokenizer.text="<0.0 seconds><0.1 seconds>"
            verify_native_encoding(processor,{"video_grid_thw":[[2,4,4]],"input_ids":[[1]]},r)
            self.assertEqual(r["padded_source_frame_ids"],[0,1,2,2])
        self.assertEqual(processor._calculate_timestamps,original)
        self.assertNotIn("_calculate_timestamps",processor.__dict__)

    def test_fractional_endpoint_legacy_failure_reproduced_and_restored(self):
        from vendor.temporal_common import parse_segments
        from pts_contract import parse_native_segments
        duration=float(Fraction(739,60))
        raw=json.dumps({"segments":[[0,12.3167]]})
        old,errors,_=parse_segments(raw,duration)
        self.assertEqual(errors,[])
        self.assertGreater(old[0][1],duration)
        clock={"branch":BRANCH_NATIVE,"pts":[Fraction(0),Fraction(12)],"duration":Fraction(739,60)}
        with self.assertRaisesRegex(ValueError,"INVALID_NATIVE_PARSED_SEGMENT"):
            native_segment_frames(clock,0.0,duration,old)
        parsed,errors,_,events=parse_native_segments(raw,duration)
        self.assertEqual(errors,[])
        self.assertEqual(parsed,[[0.0,duration]])
        self.assertEqual(len(events),1)
        self.assertEqual(native_segment_frames(clock,0.0,duration,parsed),[0,1])

    def test_fractional_packet_endpoint_rounding_contract(self):
        from pts_contract import parse_native_segments
        for endpoint in (Fraction(739,60),Fraction(739,2997),Fraction(1,2997),Fraction(1234567,2997)):
            duration=float(endpoint)
            parsed,errors,_,events=parse_native_segments(json.dumps({"segments":[[0,duration]]}),duration)
            self.assertEqual(errors,[])
            self.assertLessEqual(parsed[0][1],duration)
            self.assertEqual(len(events),int(round(duration,4)>duration))
            clock={"branch":BRANCH_NATIVE,"pts":[Fraction(0)],"duration":endpoint}
            self.assertEqual(native_segment_frames(clock,0.0,duration,parsed),[0])

    def test_native_parser_preserves_input_failures_and_no_frame_stop(self):
        from pts_contract import parse_native_segments
        duration=float(Fraction(739,60))
        for segments in ([],[[0,duration+.002]],[[0,.1]]*6,[[1,0]],[[0,"bad"]]):
            parsed,errors,_,events=parse_native_segments(json.dumps({"segments":segments}),duration)
            self.assertIsNone(parsed)
            self.assertTrue(errors)
            self.assertEqual(events,[])
        parsed,errors,_,_=parse_native_segments(json.dumps({"segments":[[.2,.3]]}),duration)
        self.assertEqual(errors,[])
        clock={"branch":BRANCH_NATIVE,"pts":[Fraction(0),Fraction(1)],"duration":Fraction(739,60)}
        with self.assertRaisesRegex(ValueError,"NO_NATIVE_SOURCE_FRAMES"):
            native_segment_frames(clock,0.0,duration,parsed)

    def test_processor_single_frame_padding(self):
        processor=self.processor()
        with exact_native_pts(processor,self.plan(1),25.0) as r:
            self.assertEqual(processor._calculate_timestamps([0,0],25.0,2),[.01])
        self.assertEqual(r["padded_source_frame_ids"],[0,0])
        self.assertEqual(r["source_frame_ids"],[0])
        self.assertEqual(r["explicit_input_padding_copies"],1)
        self.assertEqual(r["implicit_processor_padding_copies"],0)

    def test_single_frame_pixel_padding_is_same_physical_frame(self):
        import numpy as np
        from native_frames import prepare_native_processor_input
        original=np.arange(48,dtype=np.uint8).reshape(1,4,4,3)
        metadata={"frames_indices":[0],"fps":25.0,"total_num_frames":1}
        padded, actual=prepare_native_processor_input(original,metadata,self.plan(1))
        self.assertEqual(actual["frames_indices"],[0,0])
        self.assertTrue(np.array_equal(padded[0],original[0]))
        self.assertTrue(np.array_equal(padded[0],padded[1]))
        self.assertEqual(metadata["frames_indices"],[0])

    def test_single_frame_unpadded_metadata_is_rejected(self):
        processor=self.processor()
        with self.assertRaisesRegex(ValueError,"NATIVE_IDENTITY"):
            with exact_native_pts(processor,self.plan(1),25.0):
                processor._calculate_timestamps([0],25.0,2)

    def test_processor_wrong_index_restores_instance(self):
        processor=self.processor()
        original=processor._calculate_timestamps
        with self.assertRaises(ValueError):
            with exact_native_pts(processor,self.plan(3),25.0):
                processor._calculate_timestamps([0,1,3],25.0,2)
        self.assertEqual(processor._calculate_timestamps,original)

    def test_processor_wrong_patch_grid_stops(self):
        processor=self.processor()
        with self.assertRaises(ValueError):
            with exact_native_pts(processor,self.plan(3),25.0) as r:
                processor._calculate_timestamps([0,1,2],25.0,2)
                processor.tokenizer.text="<0.0 seconds><0.1 seconds>"
                verify_native_encoding(processor,{"video_grid_thw":[[3,4,4]],"input_ids":[[1]]},r)

    def test_processor_native_clock_not_avgfps(self):
        p=self.plan(3)
        p["source_relative_pts"]=[.01,.05,.65]
        processor=self.processor()
        with exact_native_pts(processor,p,25.0) as r:
            times=processor._calculate_timestamps([0,1,2],25.0,2)
            self.assertAlmostEqual(times[0],.03)
            self.assertAlmostEqual(times[1],.65)

    def test_native_inference_failure_never_empty(self):
        temporal=temporal_for(self.manifest,self.clocks)
        temporal[7]["windows"][0].update(status="INFERENCE_FAILURE",output_valid=False,parsed_segments=None)
        with self.assertRaises(ValueError):
            select_frames(self.manifest,temporal,self.clocks)

    def test_temporal_only_admission_cannot_run_spatial(self):
        from run_pts import verify_admission
        adm={"variant":VARIANT,"stage":"A_PTS_NONTEST_E2E","authorized":True,"manifest_sha256":"a"*64,
             "clock_registry_sha256":"b"*64,"source_lock_sha256":legacy.sha(HERE/"source_lock.json"),
             "run_dir":str(self.root.resolve()),"resource_preflight_pass":True,"shared_gpu_queue_approved":True,
             "disk_peak_within_80gib":True,"budget_runner_required":True,"allowed_stages":["temporal"],
             "space_inference_admitted":False}
        path=self.root/"admission.json"; legacy.write_json(path,adm)
        with self.assertRaisesRegex(ValueError,"scope"):
            verify_admission(path,"a"*64,"NONTEST_FROZEN8",self.root,"b"*64,"spatial")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists(): raise FileExistsError("preserve CPU evidence")
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
    payload={"status":"PASS_CPU_CONTRACT_ONLY" if result.wasSuccessful() else "BLOCK_CPU_CONTRACT",
             "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
             "output":stream.getvalue(),"variant":VARIANT,"test_file_sha256":legacy.sha(__file__),
             "source_lock_sha256":legacy.sha(HERE/"source_lock.json"),"real_processor_verified":False,
             "real_decoder_verified":False,"GPU_used":False,"contest_media_read":False,"labels_read":False}
    legacy.write_json(args.output,payload)
    print(stream.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__=="__main__":
    raise SystemExit(main())
