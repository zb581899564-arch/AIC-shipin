"""CPU-only renderer feasibility and final package, no semantic decisions here."""
from sr_common import *
import zipfile

def lines(p):
    with Path(p).open() as f:return [json.loads(s)for s in f if s.strip()]

def render(selected):
    inp=read(W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json')
    fps={k:bound(v)for k,v in inp['source_field_files'].items()}
    # Filter by a predetermined selected key set; no score-dependent source scan.
    chosen=[r for r in lines(fps['field_frames.jsonl'])if (r['video_id'],r['source_frame'])in selected]
    require(len(chosen)==len(selected),'Selected frames outside frozen continuous spatial field')
    sys.path[:0]=[str(RUN/'b_score_aligned_package_v4'),str(RUN/'baseline_a_pts_v1'),str(RUN/'baseline_a_pts_v1/vendor')]
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    predictions,provenance=compose_from_field(legacy_manifest(read(bound(inp['source_manifest']))),chosen,lines(fps['field_shots.jsonl']),lines(fps['anchor_requests.jsonl']),lines(fps['anchor_output.jsonl']))
    return predictions,provenance,chosen,inp

def dry():
    cpu();reg=read(ROOT/'registration.json')
    with zipfile.ZipFile(bound(reg['baseline'])) as z:base=[json.loads(x)for x in z.read('predictions.jsonl').splitlines()]
    selected={(r['video_id'],p['frame'])for r in base for p in r['predictions']}
    rows,_,_,_=render(selected)
    require(len(selected)==123506 and len(rows)==426 and canonical(rows)==canonical(base),'Zero new decisions must exactly reproduce40.47 frames/geometry')
    save(ROOT/'renderer_feasibility.json',dict(status='PASS_ZERO_OVERLAY_EXACT40_47_IN_MEMORY_NO_DUPLICATE_ZIP',records=426,frames=len(selected),canonical_sha256=canonical(rows),new_model_calls=0))
    event('RENDERER_FEASIBLE',records=426,frames=len(selected),zero_overlay_exact=True)

if __name__=='__main__':
    try:dry()
    except BaseException as e:failure('renderer',e);raise
