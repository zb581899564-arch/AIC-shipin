"""Bound a potential full-view comparison to existing exact-frame cache identities."""
from fractions import Fraction
import hashlib
from pathlib import Path
from common import ROOT, WORK, checked, read, ref, write


def center_slots(total):
    positions = {}
    for start in range(0, total, 64):
        end = min(start + 64, total)
        for slot in range(8):
            positions.setdefault(min(start + 8 * slot, end - 1), (start // 64, slot))
    return positions


def candidates_for(source, cached):
    current = read(checked(source['clock']))
    earlier = read(checked(cached['clock_ref']))
    assert current['source_sha256'] == cached['source_sha256'] == earlier['source_sha256']
    assert [Fraction(p) for p in current['original_exact_pts']] == [Fraction(p) for p in earlier['original_exact_pts']]
    positions = center_slots(source['native_frames'])
    candidates = {}
    for patch in cached['patches']:
        if not Path(patch['path']).is_file():
            continue
        assert len(patch['samples']) == len(patch['grids'])
        for query_index, ordinal in enumerate(patch['samples']):
            if ordinal not in positions:
                continue
            cell, slot = positions[ordinal]
            candidates.setdefault(ordinal, dict(native_ordinal=ordinal, center_cell=cell,
                  center_slot=slot, context_path=patch['path'], context_sha256=patch['sha256'],
                  context_query_index=query_index, grid=patch['grids'][query_index],
                  profile=patch['profile_ref']))
    ordered = sorted(candidates, key=lambda ordinal: hashlib.sha256(
        f"FULLVIEW_METADATA10:{cached['source_sha256']}:{ordinal}".encode()).hexdigest())
    chosen = [candidates[ordinal] for ordinal in ordered[:8]]
    return dict(sid=source['sid'], name=source['name'], media_sha256=cached['source_sha256'],
          matched_existing_native_frames=len(candidates), chosen=chosen,
          native_clock_identical=True, missing_required=len(chosen) < 8)


def main():
    previous = WORK / 'native_preference_20261019_v1/assets.private.json'
    assets = read(previous)
    by_sha = {s['source_sha256']: s for s in assets['scopes']['check']['sources']}
    sources = read(ROOT / 'input_acceptance.json')['sources']
    rows = []
    for source in sources:
        sha = read(checked(source['clock']))['source_sha256']
        assert sha in by_sha
        rows.append(candidates_for(source, by_sha[sha]))
    write(ROOT / 'full_view_cache_inventory10.json', dict(
          status='METADATA_ONLY_SHARED_NATIVE_FRAMES_REGISTERED', sources=rows,
          previous_assets=ref(previous), selection='8 per source by fixed SHA, no targets or scores',
          selected_frame_count=sum(len(s['chosen']) for s in rows),
          exact_shared_frame_count=sum(s['matched_existing_native_frames'] for s in rows),
          sources_with8=sum(not s['missing_required'] for s in rows),
          actual_tensor_decode_or_inverse_test=False, actual_full_view_containment_proven=False,
          profile_synthetic_geometry_is_not_real_pixel_QA=True,
          new_media_decode=0, new_model=0, training=0,
          next_allowed='Review original processor path and verify a bounded CPU tensor inverse before registering any new model contrast',
          old_XCLIP_STOP_unchanged=True, production_allowed=False))
    print(dict(sources_with8=sum(not s['missing_required'] for s in rows),
          chosen=sum(len(s['chosen']) for s in rows), available=sum(s['matched_existing_native_frames'] for s in rows)))


if __name__ == '__main__':
    main()
