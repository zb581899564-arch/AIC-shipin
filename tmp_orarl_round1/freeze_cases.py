#!/usr/bin/env python3
"""Freeze the round-2 sample list and build the case files.

Writes:
  evidence/samples_frozen.json   the frozen list (built BEFORE any model output)
  cases/cases_sg.jsonl           7 x spatial_grounding on each clip's frame 0
  cases/cases_tracking.jsonl     7 clips x conditions A/B/C

Condition definitions:
  A = round-1 input: natural-language description only, NO anchor box.
  B = author protocol: anchor box inside the question (agent-reviewed box).
  C = same as B, but the anchor box comes from Video-ORA-4B's own spatial
      grounding on frame 0 (filled in AFTER the sg job by --from-sg).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

R1 = Path("/home/inspur/aic_video_work/orarl_round1")
R2 = Path("/home/inspur/aic_video_work/orarl_round2")
FFMPEG = "/usr/local/bin/ffmpeg"
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"

# ---- canonical tracking profile (eval.sh / datasets.jsonl) ----
TRACK_SAMPLING = {"fps": 1, "max_frames": 32, "min_pixels": 4096,
                  "max_pixels": 786432, "total_pixels": 8388608}
SG_SAMPLING = {"min_pixels": 65536, "max_pixels": 1048576}

# Frozen sample table. `box` = agent-reviewed first-frame anchor (norm1000),
# read off a norm1000 grid overlay by the executing agent and visually verified
# in frames/grid/anchor_boxes_check.png. NOT human ground truth.
SAMPLES = [
    dict(sample_id="clip1", stratum="S3_cut_or_leaves", source_group="wk2CeU_DcBo",
         clip=str(R1 / "clips/src_wk2CeU_DcBo_60_210_off0_len32.mp4"),
         source_path="/home/inspur/aic_video_data/videos/w/wk2CeU_DcBo_60.0_210.0.mp4",
         query="Man and woman walk through the park sidewalk together.",
         target="the man in the white sleeveless shirt",
         box=[420, 15, 1000, 1000],
         stratum_basis=("t=0/8/16 show the couple in the park; t=24 is a different street "
                        "scene -> scene cut and the target leaves; also the round-1 clip")),
    dict(sample_id="sel04", stratum="S1_visible_position_change", source_group="lwNho_1tKrc",
         clip=str(R2 / "clips/round2sel_04_lwNho_1tKrc_off0_len32.mp4"),
         source_path="/home/inspur/aic_video_data/videos/l/lwNho_1tKrc_60.0_210.0.mp4",
         query="A group of men are running then stops and walks towards a car and rides in it",
         target="the man in the blue jacket",
         box=[520, 50, 820, 800],
         stratum_basis="one man translating across the frame at t=0/8/16, present throughout"),
    dict(sample_id="sel12", stratum="S1_visible_position_change", source_group="gcrsfhqTmmk",
         clip=str(R2 / "clips/round2sel_12_gcrsfhqTmmk_off0_len32.mp4"),
         source_path="/home/inspur/aic_video_data/videos/g/gcrsfhqTmmk_60.0_210.0.mp4",
         query="A guy talking from a house",
         target="the man talking",
         box=[140, 170, 900, 1000],
         stratum_basis="single subject visible and continuous across t=0/8/16/24"),
    dict(sample_id="sel06", stratum="S2_scale_or_occlusion", source_group="iH1-Z6eB2cY",
         clip=str(R2 / "clips/round2sel_06_iH1-Z6eB2cY_off0_len32.mp4"),
         source_path="/home/inspur/aic_video_data/videos/i/iH1-Z6eB2cY_60.0_210.0.mp4",
         query="Blonde woman holds a makeup brush and palette and applies it to her face.",
         target="the blonde woman holding the makeup brush",
         box=[220, 0, 660, 700],
         stratum_basis="subject scale/pose changes markedly across t=0/8/16/24"),
    dict(sample_id="sel07", stratum="S2_scale_or_occlusion", source_group="JlWjckrziyw",
         clip=str(R2 / "clips/round2sel_07_JlWjckrziyw_off0_len32.mp4"),
         source_path="/home/inspur/aic_video_data/videos/j/JlWjckrziyw_60.0_210.0.mp4",
         query="Woman reads the synopsis of a book and comments on it.",
         target="the woman reading the book",
         box=[220, 0, 590, 700],
         stratum_basis="close-up face whose scale changes across the strip"),
    dict(sample_id="sel02", stratum="S3_cut_or_leaves", source_group="ioWAoEVYaP0",
         clip=str(R2 / "clips/round2sel_02_ioWAoEVYaP0_off0_len32.mp4"),
         source_path="/home/inspur/aic_video_data/videos/i/ioWAoEVYaP0_60.0_210.0.mp4",
         query="Chefs are cooking food on a grill for a banquet after dark.",
         target="the man in the dark jacket with glasses (the person the anchor box encloses)",
         box=[420, 210, 690, 790],
         stratum_basis=("t=0/8 show a night market; t=16 is a landscape/pool and t=24 greenery "
                        "-> scene cuts. NOTE the query's nominal subject 'chefs cooking on a "
                        "grill' is not identifiable in frame 0, so the target was defined as "
                        "the person enclosed by the verified anchor box")),
    dict(sample_id="sel08", stratum="S3_cut_or_leaves", source_group="QHFy-nWNJYk",
         clip=str(R2 / "clips/round2sel_08_QHFy-nWNJYk_off0_len32.mp4"),
         source_path="/home/inspur/aic_video_data/videos/Q/QHFy-nWNJYk_60.0_210.0.mp4",
         query="Tourists are stopping to look at the red rocky plateaus and outcrops",
         target="the woman in the red top",
         box=[40, 100, 470, 950],
         stratum_basis=("t=0/8 two people inside a vehicle; t=16 Monument Valley landscape; "
                        "t=24 camper interior -> scene cuts")),
]

REJECTED = [
    dict(sample_id="sel01", source_group="RoripwjYFp8",
         reason="query says 'woman wearing glasses' but frame 0 shows a man in a grey speckled "
                "top; the named subject is not identifiable at t=0, so no anchor box can be "
                "placed under rule R6"),
    dict(sample_id="sel03", source_group="ACMKgn5w2HY",
         reason="frame 0 is an interior with a green glass lamp and contains no person; the "
                "query subject 'woman in white' is absent at t=0"),
    dict(sample_id="sel09", source_group="mpVKDcu6R5Y",
         reason="frames show a food court and legs, not 'two women on a plane'; query does not "
                "match the visuals at any sampled time"),
    dict(sample_id="sel11", source_group="UGafHWHJrLg",
         reason="target person only appears from t=8; absent at t=0"),
    dict(sample_id="sel13", source_group="mEqAtcljxHc",
         reason="t=0 shows a woman with a flag, while the query's 'team in red uniform' only "
                "appears at t=16/24; no subject matched the query at t=0"),
    dict(sample_id="sel10", source_group="yjzmMAmgNFA",
         reason="not used: stratum ambiguous from the 4-frame strip (partial person at t=0, "
                "studio at t=8/16); rule R4 requires a clear stratum"),
    dict(sample_id="sel14", source_group="PXj6QOKJ_5Q",
         reason="not used: frames are a blurry face close-up; a reliable anchor box could not be "
                "verified at t=0"),
    dict(sample_id="sel15", source_group="bP5KfdFJzC4",
         reason="not used: 'preparing a dish with beans' does not match the frames (woman on a "
                "sofa); subject/query mismatch"),
]


def probe(p):
    o = subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_frames,avg_frame_rate",
         "-show_entries", "format=duration", "-of", "json", p], text=True)
    d = json.loads(o)
    st = d["streams"][0]
    n, dn = (st.get("avg_frame_rate") or "0/1").split("/")
    return {"width": int(st["width"]), "height": int(st["height"]),
            "fps": float(n) / float(dn) if float(dn) else None,
            "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
            "duration_sec": float(d["format"]["duration"])}


def frame0(clip, out):
    subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", "0", "-i", clip,
                    "-frames:v", "1", str(out)], check=True, stdin=subprocess.DEVNULL)
    return str(out)


def bbox_literal(box):
    """Integer [x1,y1,x2,y2] literal exactly as the author's GOT-10k prompt shows."""
    return "[" + ",".join(str(int(round(v))) for v in box) + "]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-sg", default="",
                    help="run dir of the spatial-grounding job; fills condition C boxes")
    args = ap.parse_args()

    (R2 / "cases").mkdir(exist_ok=True)
    (R2 / "frames/f0").mkdir(parents=True, exist_ok=True)

    frozen = {"built_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"],
                                                   text=True).strip(),
              "source_pool": "/home/inspur/aic_video_data/videos (read-only, non-test)",
              "test_set_excluded": "/home/inspur/aic_video_data/test is NOT used",
              "clip_construction": "ffmpeg -ss 0 -t 32 -c copy (stream copy, no re-encode); "
                                   "offset 0.0 so clip time == source time",
              "anchor_box_provenance": ("agent-reviewed initialization prior: read off a "
                                        "norm1000 grid overlay by the executing agent and "
                                        "visually verified in frames/grid/anchor_boxes_check.png. "
                                        "NOT human ground truth."),
              "condition_questions": {
                  "A": "'{desc}' only, no anchor box (round-1 style)",
                  "B": "author protocol: 'Given the bounding box [x1,y1,x2,y2] of the target "
                       "object, ...' with the agent-reviewed box",
                  "C": "author protocol wording, anchor box produced by Video-ORA-4B spatial "
                       "grounding on frame 0",
              },
              "samples": [], "rejected": REJECTED}

    sg_cases, tr_cases = [], []
    sg_boxes = {}
    if args.from_sg:
        st = json.loads((Path(args.from_sg) / "run_status.json").read_text())
        for c in st["cases"]:
            b = (c.get("parsed") or {}).get("boxes_norm1000")
            if b and c.get("task_success"):
                sg_boxes[c["sample_id"]] = b[0]

    for s in SAMPLES:
        m = probe(s["clip"])
        f0 = frame0(s["clip"], R2 / f"frames/f0/{s['sample_id']}_f0.png")
        rec = dict(s)
        rec.update(media=m, frame0=f0)
        assert m["duration_sec"] > 20, f"{s['sample_id']} clip too short: {m}"
        frozen["samples"].append(rec)

        sg_cases.append({
            "case_id": f"sg_{s['sample_id']}", "sample_id": s["sample_id"],
            "task": "spatial_grounding", "condition": "sg",
            "expression": s["target"], "image": f0, "sampling": SG_SAMPLING,
            "is_test_set": False, "ground_truth": None,
        })

        base = {"sample_id": s["sample_id"], "task": "tracking", "video": s["clip"],
                "sampling": dict(TRACK_SAMPLING), "is_test_set": False, "ground_truth": None,
                "stratum": s["stratum"]}
        # A: description only, no box
        tr_cases.append(dict(base, case_id=f"tr_{s['sample_id']}_A", condition="A",
                             question=s["target"],
                             init_box_norm1000=None, init_box_source="none",
                             target_description=s["target"]))
        # B: agent-reviewed anchor box
        tr_cases.append(dict(base, case_id=f"tr_{s['sample_id']}_B", condition="B",
                             question=(f"Given the bounding box {bbox_literal(s['box'])} of the "
                                       f"target object, please track this object throughout the "
                                       f"video."),
                             init_box_norm1000=s["box"],
                             init_box_source="agent-reviewed"))
        # C: model-generated anchor box
        cb = sg_boxes.get(s["sample_id"])
        tr_cases.append(dict(base, case_id=f"tr_{s['sample_id']}_C", condition="C",
                             question=((f"Given the bounding box {bbox_literal(cb)} of the target "
                                        f"object, please track this object throughout the video.")
                                       if cb else
                                       f"Given the bounding box of the target object "
                                       f"({s['target']}), please track this object."),
                             init_box_norm1000=cb, init_box_source="model_spatial_grounding",
                             init_box_available=bool(cb)))

    def wl(path, rows):
        Path(path).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    wl(R2 / "cases/cases_sg.jsonl", sg_cases)
    wl(R2 / "cases/cases_tracking.jsonl", tr_cases)
    (R2 / "evidence/samples_frozen.json").write_text(
        json.dumps(frozen, indent=2, ensure_ascii=False) + "\n")

    print(f"frozen samples: {len(frozen['samples'])}, rejected: {len(REJECTED)}")
    for s in frozen["samples"]:
        print(f"  {s['sample_id']:7s} {s['stratum']:28s} dur={s['media']['duration_sec']:.3f} "
              f"{s['media']['width']}x{s['media']['height']} box={s['box']}")
    print(f"\ncases: sg={len(sg_cases)} tracking={len(tr_cases)}")
    if not args.from_sg:
        print("NOTE: condition C boxes not filled yet (no --from-sg); run the sg job first")
    else:
        missing = [c["sample_id"] for c in tr_cases
                   if c["condition"] == "C" and not c.get("init_box_available")]
        print(f"C boxes filled: {len(sg_boxes)}/{len(SAMPLES)}"
              + (f"  MISSING {missing}" if missing else ""))
    print("wrote cases/cases_sg.jsonl, cases/cases_tracking.jsonl, "
          "evidence/samples_frozen.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
