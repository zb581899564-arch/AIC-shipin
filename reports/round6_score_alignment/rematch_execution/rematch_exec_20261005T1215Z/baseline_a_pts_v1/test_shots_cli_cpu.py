#!/usr/bin/env python3
"""Full child-process CLI regression with controlled synthetic CPU decoders.

Real codec/frame identity is covered by the separate lossless decoder test.
Here actual CLI, source/clock validation, descriptors and serialization execute;
only video decoder I/O is replaced with deterministic distinguishable frames.
"""
from __future__ import annotations
import argparse
import ast
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from a_contract import sha, write_json, write_rows
from pts_contract import VARIANT
from test_helpers import make_fixture

HERE=Path(__file__).resolve().parent

def rewrite_fixture(path,payload):
    """Only this test's temporary synthetic fixture is intentionally mutated."""
    path.write_text(json.dumps(payload,sort_keys=True)+"\n",encoding="utf-8")

def source_path(path):
    # The production manifest contract is POSIX. On Windows, a drive-rooted
    # /ai/... path is also resolved on this test process's current G: drive.
    text=path.as_posix()
    return text[2:] if os.name=="nt" else text

# sitecustomize loads in the child interpreter before the actual script entry.
# The trace proves rejection before either decoder is opened or consumed.
SHIM=r'''
import json, os, sys, types
from pathlib import Path
from fractions import Fraction
import cv2
import numpy as np

def trace(kind, **fields):
    with open(os.environ["A_PTS_CLI_TRACE"],"a",encoding="utf-8") as stream:
        stream.write(json.dumps({"kind":kind,**fields},sort_keys=True)+"\n")

def rgb(index):
    frame=np.zeros((64,64,3),dtype=np.uint8)
    frame[:]=[index*3%256,255-index*2,index*7%256]
    for bit in range(7):
        frame[0:8,bit*8:(bit+1)*8]=255 if index&(1<<bit) else 0
    return frame

class Capture:
    def __init__(self,path):
        self.path=str(path); self.cursor=0
        trace("CFR_OPEN",path=self.path)
    def isOpened(self): return True
    def set(self,key,value):
        assert key==cv2.CAP_PROP_POS_FRAMES
        self.cursor=int(value); trace("CFR_SEEK",frame=self.cursor)
        return True
    def read(self):
        trace("CFR_READ",frame=self.cursor)
        if self.cursor>=65: return False,None
        result=rgb(self.cursor)[:,:,::-1].copy(); self.cursor+=1
        return True,result
    def release(self): pass
cv2.VideoCapture=Capture

class ND:
    def __init__(self,array): self.array=array
    def asnumpy(self): return self.array
class Reader:
    def __init__(self,path,ctx=None):
        self.cursor=0; self.path=str(path)
        trace("NATIVE_OPEN",path=self.path)
        self.clock=json.loads((Path(os.environ["A_PTS_CLI_CLOCK_ROOT"])/(Path(path).stem+".clock_arrays.json")).read_text())
    def __len__(self): return self.clock["n_frames"]
    def get_avg_fps(self): return 30.0
    def get_frame_timestamp(self,indices):
        origin=self.clock["raw_first_pts_ticks"]
        tick=Fraction(self.clock["raw_time_base"])
        values=[(float((self.clock["native_pts_ticks"][i]-origin)*tick),
                 float((self.clock["native_frame_end_pts_ticks"][i]-origin)*tick)) for i in indices]
        trace("NATIVE_ALL_CLOCK",frames=len(indices))
        return ND(np.asarray(values,dtype=np.float32))
    def next(self):
        trace("NATIVE_NEXT",frame=self.cursor)
        result=ND(rgb(self.cursor)); self.cursor+=1
        return result
decord=types.ModuleType("decord")
decord.cpu=lambda index:("SYNTHETIC_CPU",index)
decord.VideoReader=Reader
sys.modules["decord"]=decord
'''


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="cli_synthetic_",dir=HERE)
        self.root=Path(self.temp.name)
        self.shim=self.root/"shim"; self.shim.mkdir()
        (self.shim/"sitecustomize.py").write_text(SHIM,encoding="utf-8")
        self.manifest,self.registry,self.registry_path=make_fixture(self.root,native_ids=("7",))
        media=self.root/"synthetic_media"; media.mkdir()
        for row,clock in zip(self.manifest["records"],self.registry["records"]):
            path=media/(row["video_id"]+".mp4")
            path.write_bytes(("CONTROLLED_SYNTHETIC_DECODER_ONLY_"+row["video_id"]).encode())
            row["source_path"]=source_path(path); row["source_sha256"]=sha(path)
            clock["source_sha256"]=row["source_sha256"]
            array_path=Path(clock["clock_arrays"]["path"])
            arrays=json.loads(array_path.read_text()); arrays["source_sha256"]=row["source_sha256"]
            rewrite_fixture(array_path,arrays); clock["clock_arrays"]["sha256"]=sha(array_path)
        self.manifest["allowed_source_roots"]=[source_path(media)]
        self.save_registry()
        self.manifest_path=self.root/"manifest.json"; write_json(self.manifest_path,self.manifest)
        self.selected=self.root/"selected.jsonl"
        self.selected_rows=[]
        for vid in ("0","7"):
            row=self.manifest["records"][int(vid)]
            for index in (0,1,2,10,11,64):
                self.selected_rows.append({"video_id":vid,"source_frame":index,"source_path":row["source_path"],
                    "source_width":64,"source_height":64,"source_n_frames":65,"fps":30.0,"target_ratio_wh":[9,16]})
        write_rows(self.selected,self.selected_rows)
        self.trace=self.root/"decoder_trace.jsonl"
        self.env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTHONPATH=str(self.shim),
                      A_PTS_CLI_TRACE=str(self.trace),A_PTS_CLI_CLOCK_ROOT=str(self.root))

    def tearDown(self): self.temp.cleanup()

    def save_registry(self):
        rewrite_fixture(self.registry_path,self.registry)
        self.manifest["clock_registry"]={"path":str(self.registry_path),"sha256":sha(self.registry_path)}

    def command(self,script="detect_shots_pts.py",manifest_sha=None,registry_sha=None):
        argv=[sys.executable,"-B",str(HERE/script),"--manifest",str(self.manifest_path),
              "--expected-manifest-sha256",manifest_sha or sha(self.manifest_path),
              "--clock-registry",str(self.registry_path),"--expected-clock-registry-sha256",
              registry_sha or sha(self.registry_path)]
        if script=="infer_anchors_pts.py":
            argv += ["--requests",str(self.selected),"--expected-requests-sha256","f"*64,
                     "--output",str(self.root/"anchors.jsonl")]
        else:
            argv += ["--selected",str(self.selected),"--output",str(self.root/"shots.jsonl"),
                     "--summary",str(self.root/"summary.json"),"--allowed-root",
                     self.manifest["allowed_source_roots"][0]]
        return argv

    def invoke(self,argv):
        return subprocess.run(argv,env=self.env,cwd=HERE,text=True,encoding="utf-8",errors="replace",
                              capture_output=True,timeout=30)

    def trace_rows(self):
        return [json.loads(line) for line in self.trace.read_text().splitlines()] if self.trace.exists() else []

    def assert_complete_against_original(self):
        completed=self.invoke(self.command())
        self.assertEqual(completed.returncode,0,completed.stderr)
        rows=[json.loads(line) for line in (self.root/"shots.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows),12)
        self.assertEqual([(r["video_id"],r["source_frame"]) for r in rows],
                         [(r["video_id"],r["source_frame"]) for r in self.selected_rows])
        summary=json.loads((self.root/"summary.json").read_text())
        self.assertEqual(summary["selected_sha256"],sha(self.selected))
        self.assertEqual(summary["output_sha256"],sha(self.root/"shots.jsonl"))
        self.assertEqual((summary["hist_threshold"],summary["gray_mad_threshold"]),(.35,.18))
        baseline=self.invoke([sys.executable,"-B",str(HERE/"vendor/detect_shots_sequential.py"),
            "--selected",str(self.selected),"--output",str(self.root/"original_shots.jsonl"),
            "--summary",str(self.root/"original_summary.json"),"--allowed-root",self.manifest["allowed_source_roots"][0]])
        self.assertEqual(baseline.returncode,0,baseline.stderr)
        self.assertEqual((self.root/"shots.jsonl").read_bytes(),(self.root/"original_shots.jsonl").read_bytes())

    def test_full_cli_native_and_cfr_branches(self):
        self.assert_complete_against_original()
        trace=self.trace_rows()
        self.assertTrue(any(r["kind"]=="CFR_OPEN" for r in trace))
        self.assertEqual([r["frame"] for r in trace if r["kind"]=="NATIVE_NEXT"],list(range(65)))
        self.assertTrue(any(r["kind"]=="NATIVE_ALL_CLOCK" and r["frames"]==65 for r in trace))

    def test_full_cli_all_cfr_matches_original_bytes(self):
        row=self.manifest["records"][7]; clock=self.registry["records"][7]
        row.update(clock_branch="CFR_LEGACY",scope_end_sec=65/30)
        clock.update(cfr_eligible=True,native_clock_usable=False,duration_seconds=65/30,native_end_sec=None,
                     terminal_evidence={"kind":"LEGACY_CFR_N_DIV_FPS"},
                     decord_binding={"start_pass":True,"end_pass":False,"legacy_interval_pass":True,"float_dtype":"float32"})
        path=Path(clock["clock_arrays"]["path"]); arrays=json.loads(path.read_text())
        arrays["native_frame_end_pts_ticks"]=None
        from fractions import Fraction
        arrays["native_pts_ticks"]=[arrays["raw_first_pts_ticks"]+i*3000 for i in range(65)]
        arrays["source_relative_pts"]=[float(Fraction(i,30)) for i in range(65)]
        arrays["source_relative_pts_rational"]=[str(Fraction(i,30)) for i in range(65)]
        rewrite_fixture(path,arrays); clock["clock_arrays"]["sha256"]=sha(path)
        self.save_registry(); rewrite_fixture(self.manifest_path,self.manifest)
        self.assert_complete_against_original()
        self.assertFalse(any(r["kind"].startswith("NATIVE_") for r in self.trace_rows()))

    def test_wrong_manifest_hash_before_decode_both_cli_entries(self):
        for script in ("detect_shots_pts.py","infer_anchors_pts.py"):
            result=self.invoke(self.command(script,manifest_sha="f"*64))
            self.assertNotEqual(result.returncode,0)
            self.assertIn("manifest identity changed",result.stderr)
        self.assertEqual(self.trace_rows(),[])

    def test_malformed_manifest_before_decode_both_cli_entries(self):
        self.manifest["schema"]="MALFORMED_UNREGISTERED_SCHEMA"; rewrite_fixture(self.manifest_path,self.manifest)
        for script in ("detect_shots_pts.py","infer_anchors_pts.py"):
            result=self.invoke(self.command(script))
            self.assertNotEqual(result.returncode,0)
            self.assertIn("V2_NATIVE_CLOCK_MANIFEST_REQUIRED",result.stderr)
        self.assertEqual(self.trace_rows(),[])

    def test_wrong_registry_hash_before_decode_both_cli_entries(self):
        for script in ("detect_shots_pts.py","infer_anchors_pts.py"):
            result=self.invoke(self.command(script,registry_sha="f"*64))
            self.assertNotEqual(result.returncode,0)
            self.assertIn("MANIFEST_CLOCK_REGISTRY_BINDING_MISMATCH",result.stderr)
        self.assertEqual(self.trace_rows(),[])

    def test_spatial_request_hash_fails_before_decoder_and_model(self):
        result=self.invoke(self.command("infer_anchors_pts.py"))
        self.assertNotEqual(result.returncode,0)
        self.assertIn("anchor request hash differs",result.stderr)
        self.assertEqual(self.trace_rows(),[])

    def test_sha_not_assigned_inside_either_main(self):
        for name in ("detect_shots_pts.py","infer_anchors_pts.py"):
            tree=ast.parse((HERE/name).read_text())
            main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="main")
            stores=[node.id for node in ast.walk(main) if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Store)]
            self.assertNotIn("sha",stores)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError("preserve CLI regression evidence")
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CliTests))
    receipt={"schema":"aic_native_pts_full_cli_cpu_regression_v1","variant":VARIANT,
             "status":"PASS_FULL_CLI_CPU_CONTROLLED_DECODERS" if result.wasSuccessful() else "BLOCK_FULL_CLI_CPU_REGRESSION",
             "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
             "output":stream.getvalue(),"source_lock_sha256":sha(HERE/"source_lock.json"),"test_file_sha256":sha(__file__),
             "complete_cli_child_processes":True,"actual_descriptor_and_serialization":True,
             "controlled_decoder_io":True,"real_codec_identity_proved":False,"contest_media_read":False,
             "labels_read":False,"model_weights_loaded":False,"GPU_used":False}
    write_json(args.output,receipt); print(stream.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__=="__main__": raise SystemExit(main())
