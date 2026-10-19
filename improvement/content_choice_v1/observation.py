"""Fixed-budget selection of already retained, real sparse observations.

The only intervention is which cached images the two original views expose.
Neither labels, proposed output intervals, audio, new media decoding nor a new
image encoder enters the selection rule.  Sparse visual change is not optical
flow or continuous motion.  The original prompt and processor text expansion
are retained, but timestamps and the actual four-tensor signature are rebuilt.
"""
from bisect import bisect_left
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math

import numpy as np

from ..native_preference_v1.assets import check_ref, require


POLICY = "FIXED_PTS_STRATA_PATCH_RGB_CHANGE_V1"
MAX_OBSERVATIONS = 64
DESCRIPTOR_DIMENSIONS = 12


def uniform_cells(indices):
    """Independent spelling of the historical endpoint-preserving sample_even."""
    require(isinstance(indices, (list, tuple)) and len(indices) >= 2
            and all(type(i) is int and i >= 0 for i in indices)
            and list(indices) == sorted(set(indices)), "Ordered real source cells required")
    count = min(MAX_OBSERVATIONS, len(indices) - len(indices) % 2)
    return [indices[(j * (len(indices) - 1)) // (count - 1)] for j in range(count)]


def fixed_time_strata(indices, sample_pts):
    """Nonempty exact-PTS Voronoi strata around the original uniform samples.

    A midpoint belongs to the earlier stratum.  Each uniform centre is itself
    an actual observation, so irregular/VFR timestamps never require padding,
    borrowing across strata or inventing a frame in an empty time bin.
    """
    uniform = uniform_cells(indices)
    points = [Fraction(value) for value in sample_pts]
    require(points and all(a < b for a, b in zip(points, points[1:]))
            and indices[-1] < len(points), "Strictly ordered exact sample PTS required")
    boundaries = [(points[a] + points[b]) / 2 for a, b in zip(uniform, uniform[1:])]
    strata = [[] for _ in uniform]
    for cell in indices:
        strata[bisect_left(boundaries, points[cell])].append(cell)
    require(all(centre in members for centre, members in zip(uniform, strata))
            and [cell for members in strata for cell in members] == list(indices),
            "Fixed temporal strata lost or duplicated an observation")
    return uniform, strata, boundaries


def select_cells(indices, sample_pts, descriptors):
    """One representative per fixed stratum; exact endpoints, no tunable knobs.

    Score is mean absolute RGB-descriptor change to the adjacent real samples
    of this view.  Interior cells use both neighbours; no Excerpt neighbour is
    borrowed from outside its registered window.  Ties prefer the original
    uniform observation, then the earlier native cell.  No epsilon or label
    dependent threshold is used.
    """
    uniform, strata, boundaries = fixed_time_strata(indices, sample_pts)
    values = np.asarray(descriptors)
    require(values.dtype.kind == "f" and values.ndim == 2
            and values.shape == (len(sample_pts), DESCRIPTOR_DIMENSIONS)
            and bool(np.isfinite(values).all()), "Finite source-by-12 RGB descriptors required")
    scores = {}
    for position, cell in enumerate(indices):
        neighbours = indices[max(0, position - 1):position] + indices[position + 1:position + 2]
        score = math.fsum(float(abs(float(a) - float(b)))
                         for neighbour in neighbours for a, b in zip(values[cell], values[neighbour]))
        score /= DESCRIPTOR_DIMENSIONS * len(neighbours)
        require(math.isfinite(score), "Nonfinite visual change score")
        scores[cell] = score
    selected = [min(members, key=lambda cell: (-scores[cell], cell != centre, cell))
                for centre, members in zip(uniform, strata)]
    selected[0], selected[-1] = indices[0], indices[-1]
    require(selected == sorted(set(selected)) and len(selected) == len(uniform)
            and all(cell in members for cell, members in zip(selected, strata)),
            "Same-budget real-observation selection failed")
    return selected, dict(uniform_cells=uniform, selected_cells=selected,
        available_observations=len(indices), observations=len(selected),
        changed_observations=sum(a != b for a, b in zip(uniform, selected)),
        stratum_sizes=list(map(len, strata)),
        stratum_midpoints_exact=list(map(str, boundaries)),
        selected_change_scores=[scores[cell] for cell in selected],
        endpoints_preserved=True, padding=0)


def patch_descriptor_array(pixels, grid_hw):
    """12 float64 means of normalized RGB in four actual spatial quadrants.

    This operates directly on the original Qwen patch16/temporal2/merge2 layout.
    It does not reconstruct native RGB or rescale/encode an image.  The two
    image temporal copies must be byte-identical.  The low-dimensional summary
    deliberately cannot recover actions absent from the retained observations.
    """
    require(isinstance(grid_hw, (list, tuple)) and len(grid_hw) == 2
            and all(type(value) is int and value > 0 and value % 2 == 0 for value in grid_hw),
            "Positive even merge2 spatial grid required")
    height, width = grid_hw
    values = np.asarray(pixels)
    require(values.dtype == np.float32 and values.shape == (height * width, 1536)
            and bool(np.isfinite(values).all()), "Finite retained float32 patch matrix required")
    image = values.reshape(height * width, 3, 2, 16, 16)
    require(image[:, :, 0].tobytes() == image[:, :, 1].tobytes(),
            "Original individual-image temporal copies differ")
    means = image[:, :, 0].mean(axis=(-1, -2), dtype=np.float64)
    # The flattened tokens are merge-block-major, not plain image row-major.
    spatial = means.reshape(height // 2, width // 2, 2, 2, 3).transpose(0, 2, 1, 3, 4).reshape(height, width, 3)
    descriptor = np.concatenate([spatial[y:y + height // 2, x:x + width // 2].mean(axis=(0, 1))
        for y in (0, height // 2) for x in (0, width // 2)])
    require(descriptor.shape == (DESCRIPTOR_DIMENSIONS,) and bool(np.isfinite(descriptor).all()),
            "Finite quadrant RGB descriptor required")
    return descriptor


def _descriptors(store, sid, frames, grid, ordinals, cache):
    if cache is None:
        if not hasattr(store, "_content_choice_descriptor_cache"):
            store._content_choice_descriptor_cache = {}
        cache = store._content_choice_descriptor_cache
    require(isinstance(cache, dict), "Explicit mutable descriptor cache must be a dictionary")
    source = store.sources[sid]
    identity = dict(policy=POLICY, sid=sid, source_sha256=source["source_sha256"],
                    clock_ref=source["clock_ref"], patches=source["patches"], grid=grid, ordinals=ordinals)
    key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if cache.get("identity") == key:
        values = cache["descriptors"]
        require(isinstance(values, np.ndarray) and values.shape == (len(frames), DESCRIPTOR_DIMENSIONS)
                and values.dtype == np.float64 and bool(np.isfinite(values).all())
                and hashlib.sha256(values.tobytes()).hexdigest() == cache["descriptor_sha256"],
                "Descriptor cache changed")
        return values, False, key
    values = []
    for frame in frames:
        require(frame.device.type == "cpu" and not frame.requires_grad, "Detached CPU retained patches required")
        values.append(patch_descriptor_array(frame.detach().numpy(), grid))
    descriptors = np.asarray(values, dtype=np.float64)
    # Keep just one source, matching NativeInputStore's bounded pixel cache.
    cache.clear()
    cache.update(identity=key, descriptors=descriptors,
                 descriptor_sha256=hashlib.sha256(descriptors.tobytes()).hexdigest())
    return descriptors, True, key


def pack_selected_pixels(frames, grid_hw, ordinals, exact_pts, start, end, owner, chosen):
    """Construct two real temporal2 views from an explicit, independently checked plan."""
    import torch
    height, width = grid_hw
    points = list(map(Fraction, exact_pts))
    require(points and points[0] == 0 and all(a < b for a, b in zip(points, points[1:]))
            and len(frames) == len(ordinals) and ordinals == sorted(set(ordinals))
            and all(type(i) is int and 0 <= i < len(points) for i in ordinals)
            and len(chosen) == 2 and 0 <= Fraction(start) < Fraction(end),
            "Exact complete native observation clock and two-view window required")
    blocks, videos = [], []
    for role, indices, origin in (("Overview", chosen[0], Fraction(0)),
                                  ("Excerpt", chosen[1], Fraction(start))):
        require(indices == sorted(set(indices)) and len(indices) >= 2 and len(indices) % 2 == 0
                and len(indices) <= MAX_OBSERVATIONS
                and all(type(i) is int and 0 <= i < len(frames) for i in indices),
                "Ordered even real view observations required")
        times = [points[ordinals[i]] for i in indices]
        require(role != "Excerpt" or all(Fraction(start) <= value < Fraction(end) for value in times),
                "Excerpt observation escaped its fixed output window")
        for a, b in zip(indices[::2], indices[1::2]):
            for cell in (a, b):
                value = frames[cell]
                require(value.device.type == "cpu" and value.dtype == torch.float32
                        and value.shape == (height * width, 1536) and not value.requires_grad
                        and bool(torch.isfinite(value).all()), "Finite detached original CPU image patches required")
                slices = value.reshape(height * width, 3, 2, 16, 16)
                require(torch.equal(slices[:, :, 0].contiguous().view(torch.uint8),
                                    slices[:, :, 1].contiguous().view(torch.uint8)),
                        "Individual-image temporal copies differ")
            left = frames[a].reshape(height * width, 3, 2, 16, 16)[:, :, 0]
            right = frames[b].reshape(height * width, 3, 2, 16, 16)[:, :, 0]
            blocks.append(torch.stack((left, right), 2).reshape(height * width, 1536))
        videos.append(dict(role=role, owner=deepcopy(owner), cells=list(indices),
            native_ordinals=[ordinals[i] for i in indices], exact_pts=list(map(str, times)),
            origin_exact=str(origin), group_timestamps_exact=[str((a + b) / 2 - origin)
                for a, b in zip(times[::2], times[1::2])], observations=len(indices), groups=len(indices) // 2, padding=0))
    values = dict(pixel_values_videos=torch.cat(blocks).contiguous(),
                  video_grid_thw=torch.tensor([[v["groups"], height, width] for v in videos], dtype=torch.int64))
    plan = dict(videos=videos, window_start_exact=str(Fraction(start)), window_end_exact=str(Fraction(end)),
                sparse_visual_observations_not_continuous_motion=True, new_media_decodes=0, new_image_processor_calls=0)
    return values, plan


def build_observation_case(store, uid, processor, cache=None):
    """Return (new request, four CPU tensors, complete source clock, diagnostic).

    The driver persists a new prefix for changed input and fills ``prefix_ref``;
    the old prefix is retained only as ``old_prefix_ref``.  NO_EFFECT returns the
    exact old tensors and prefix, so successful original generation can be
    adopted instead of run again.  All model/text QA uses the caller's explicitly
    loaded local processor; this function never creates or downloads one.
    """
    original, before, clock = store.case(uid)
    sid = original["sid"]
    check_ref(store.request_refs[uid], store.workspace)
    frames, grid, ordinals = store._source_pixels(sid)
    contract = store._helpers()
    points = list(map(Fraction, clock["normalized_exact_pts"]))
    start, end = (Fraction(original["plan"][key]) for key in ("window_start_exact", "window_end_exact"))
    local = [index for index, ordinal in enumerate(ordinals) if start <= points[ordinal] < end]
    eligible = [list(range(len(frames))), local]
    require([video["role"] for video in original["plan"]["videos"]] == ["Overview", "Excerpt"],
            "The original two view roles must be retained")
    require([uniform_cells(indices) for indices in eligible]
            == [video["cells"] for video in original["plan"]["videos"]],
            "Independent original uniform sampling differs from accepted input")
    descriptors, newly_computed, cache_identity = _descriptors(store, sid, frames, grid, ordinals, cache)
    sample_pts = [points[ordinal] for ordinal in ordinals]
    chosen, diagnostics = [], []
    for role, indices in zip(("Overview", "Excerpt"), eligible):
        cells, diagnostic = select_cells(indices, sample_pts, descriptors)
        chosen.append(cells); diagnostics.append(dict(role=role, **diagnostic))
    changed = any(value["changed_observations"] for value in diagnostics)
    request = deepcopy(original)
    request.update(old_input_ref=deepcopy(store.request_refs[uid]), observation_policy=POLICY)
    visual_tokens = sum(int(t) * int(h) * int(w) // 4 for t, h, w in before["video_grid_thw"].tolist())
    diagnostic = dict(schema="AIC_CONTENT_CHOICE_OBSERVATION_QA_V1", policy=POLICY, uid=uid, sid=sid,
        descriptor_identity=cache_identity, source_descriptors_newly_computed=newly_computed,
        source_observations=len(frames), descriptor_dimensions=DESCRIPTOR_DIMENSIONS, views=diagnostics,
        old_visual_tokens=visual_tokens, new_visual_tokens=visual_tokens,
        old_prefix_tokens=int(before["input_ids"].shape[1]),
        input_labels_used=False, output_selection_used=False, new_media_decodes=0,
        new_image_processor_calls=0, continuous_motion_observed=False)
    if not changed:
        diagnostic.update(status="NO_EFFECT", new_prefix_tokens=diagnostic["old_prefix_tokens"],
                          prefix_token_delta=0, changed_pixel_bytes=False, actual_plan_changed=False,
                          same_budget=True, old_success_can_be_adopted=True, proposed_plan_discarded=False)
        return request, before, clock, diagnostic
    pixels, plan = pack_selected_pixels(frames, grid, ordinals, clock["normalized_exact_pts"], start, end,
        dict(source_id=sid, source_sha256=original["source_sha256"]), chosen)
    # This independently uses channel slices, not the builder's temporal stack.
    contract.independent_pixels(frames, grid, pixels, plan, ordinals, clock["normalized_exact_pts"])
    require(plan["window_start_exact"] == original["plan"]["window_start_exact"]
            and plan["window_end_exact"] == original["plan"]["window_end_exact"],
            "Observation intervention changed an output window")
    require(pixels["video_grid_thw"].tolist() == before["video_grid_thw"].tolist(),
            "Visual token budget or two-view geometry changed")
    if contract.signature(pixels)["pixel_values_videos"] == original["input_signature"]["pixel_values_videos"]:
        # Different native times could change the text even when pixels match.
        # Discard the entire proposal and explicitly return the original clock,
        # plan, prefix and all four tensors before adopting an old answer.
        diagnostic.update(status="NO_EFFECT", new_prefix_tokens=diagnostic["old_prefix_tokens"],
            prefix_token_delta=0, same_budget=True, actual_plan_changed=False, changed_pixel_bytes=False,
            proposed_plan_discarded=True, discarded_proposed_plan=plan,
            independent_pixel_QA=True, old_success_can_be_adopted=True)
        return request, before, clock, diagnostic
    encoded, metadata = contract.build_text(processor, plan, pixels["video_grid_thw"], clock["physical_end_exact"])
    require(metadata["prompt"] == original["text"]["prompt"]
            and metadata["raw_template"] == original["text"]["raw_template"],
            "Observation intervention changed the question or chat template")
    values = dict(**pixels, **encoded)
    contract.independent_text(processor, plan, values, metadata)
    signature = contract.signature(values)
    request.update(plan=plan, text=metadata, input_signature=signature,
                   old_prefix_ref=request.pop("prefix_ref"), first_new_pixel_text_native_QA=True)
    diagnostic.update(status="PASS_FIRST_CHANGED_OBSERVATION_CPU_QA",
        new_prefix_tokens=metadata["prefix_tokens"], prefix_token_delta=metadata["prefix_tokens"] - diagnostic["old_prefix_tokens"],
        same_budget=True, actual_plan_changed=True, changed_pixel_bytes=True, proposed_plan_discarded=False,
        independent_pixel_QA=True, independent_processor_text_QA=True,
        old_success_can_be_adopted=False)
    return request, values, clock, diagnostic
