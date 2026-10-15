"""Padding-aware deterministic resize cap; physical/native inputs stay intact.

The installed Qwen smart_resize uses physical T in its downscale beta, while
the processor can pad odd T to an even temporal grid. Keep the original call
unchanged whenever that actual grid fits the original total pixel budget.
"""
import copy

LEGACY_VIDEO_SIZE = {'shortest_edge': 4096, 'longest_edge': 25165824}
MAX_FRAMES = 128
MAX_INPUT = 16384
_EVIDENCE_ATTRIBUTE = '_aic_padding_aware_resize_evidence'


def _smart_resize_function():
    from transformers.models.qwen3_vl.video_processing_qwen3_vl import smart_resize
    return smart_resize


def padding_resize_plan(processor, shape, smart_resize_fn=None):
    """Predict only: no frame conversion, sampling, tensor processing or padding."""
    vp = processor.video_processor
    physical, height, width = int(shape[0]), int(shape[-2]), int(shape[-1])
    temporal = int(vp.temporal_patch_size)
    patch, merge = int(vp.patch_size), int(vp.merge_size)
    if len(shape) != 4 or not 1 <= physical <= MAX_FRAMES or temporal != 2 or patch != 16 or merge != 2:
        raise ValueError('fixed Qwen native-video processor geometry required')
    if getattr(vp, 'do_resize', True) is not True:
        raise ValueError('fixed original processor resize must remain enabled')
    resize = _smart_resize_function() if smart_resize_fn is None else smart_resize_fn
    effective = ((physical + temporal - 1) // temporal) * temporal
    budget = LEGACY_VIDEO_SIZE['longest_edge']
    minimum = LEGACY_VIDEO_SIZE['shortest_edge']

    def predict(cap):
        h, w = resize(num_frames=physical, height=height, width=width,
            temporal_factor=temporal, factor=patch*merge, min_pixels=minimum, max_pixels=cap)
        if type(h) is not int or type(w) is not int or h <= 0 or w <= 0 or h % patch or w % patch:
            raise ValueError('installed smart_resize prediction is not a valid processor grid')
        return [effective//temporal, h//patch, w//patch], h*w*effective

    original_grid, original_total = predict(budget)
    result = dict(adjusted=False, physical_input_frames=physical, processor_effective_frames=effective,
        original_total_pixel_budget=budget, original_resize_cap=budget,
        actual_resize_cap=budget, original_predicted_grid=original_grid,
        original_predicted_total_pixels=original_total, predicted_grid=original_grid,
        predicted_total_pixels=original_total, installed_odd_temporal_padding_only=True,
        new_input_padding_copies=0, native_frames_removed=0)
    if original_total <= budget:
        return result

    # Deterministic beta correction. It is a resize-control limit, not a new
    # accepted total budget. The actual installed grid remains authoritative.
    cap = budget*physical//effective
    grid, total = predict(cap)
    if total > budget:
        # Rounded t_bar or minimum-dimension clamping can prevent the simple
        # ratio from activating a small enough resize. Find the greatest legal
        # integer cap below that ratio using predictions, never image retries.
        low, high = minimum, cap
        low_grid, low_total = predict(low)
        if low_total > budget:
            raise ValueError('no padding-aware resize cap fits the unchanged total budget')
        while low + 1 < high:
            mid = (low + high)//2
            mid_grid, mid_total = predict(mid)
            if mid_total <= budget:
                low, low_grid, low_total = mid, mid_grid, mid_total
            else:
                high = mid
        cap, grid, total = low, low_grid, low_total
    if not minimum <= cap <= budget or total > budget:
        raise ValueError('padding-aware prediction exceeds unchanged pixel budget')
    result.update(adjusted=True, actual_resize_cap=cap, predicted_grid=grid,
        predicted_total_pixels=total, rule='FLOOR_BUDGET_TIMES_PHYSICAL_OVER_EFFECTIVE_THEN_BOUNDED_GRID_PREDICTION')
    return result


def encode(processor, *, video_size=None, max_input=MAX_INPUT, **kwargs):
    videos = kwargs.pop('videos')
    metadata = kwargs.pop('video_metadata')
    if len(videos) != 1 or len(metadata) != 1 or not 1 <= int(videos[0].shape[0]) <= MAX_FRAMES:
        raise ValueError('registered one-video/128-frame input required')
    if kwargs.pop('do_sample_frames', False) is not False or kwargs.pop('truncation', False) is not False:
        raise ValueError('implicit sampling/truncation forbidden')
    if any(key.endswith('_kwargs') for key in kwargs):
        raise ValueError('nested overrides forbidden')
    padding = kwargs.pop('padding', True)
    tensors = kwargs.pop('return_tensors', 'pt')
    size = copy.deepcopy(LEGACY_VIDEO_SIZE if video_size is None else video_size)
    if size != LEGACY_VIDEO_SIZE or max_input != MAX_INPUT:
        raise ValueError('unchanged total pixel and token budgets required')
    plan = padding_resize_plan(processor, videos[0].shape)
    resize_size = copy.deepcopy(size)
    if plan['adjusted']:
        resize_size['longest_edge'] = plan['actual_resize_cap']
    encoded = processor(**kwargs, videos=videos,
        text_kwargs={'padding': padding, 'truncation': False},
        common_kwargs={'return_tensors': tensors},
        videos_kwargs={'video_metadata': copy.deepcopy(metadata), 'do_sample_frames': False,
                       'return_metadata': True, 'size': resize_size})
    grid = encoded['video_grid_thw'][0].tolist()
    pixels = int(grid[1] * grid[2] * processor.video_processor.patch_size ** 2)
    effective_frames = int(grid[0] * processor.video_processor.temporal_patch_size)
    if (int(videos[0].shape[0]) * pixels > size['longest_edge'] or
            effective_frames * pixels > size['longest_edge'] or pixels <= 0):
        raise ValueError('actual processed video pixels exceed unchanged total budget')
    if not 0 < int(encoded['input_ids'].shape[1]) <= MAX_INPUT:
        raise ValueError('expanded input exceeds 16384 tokens; no truncation permitted')
    if plan['adjusted']:
        if grid != plan['predicted_grid'] or effective_frames*pixels != plan['predicted_total_pixels']:
            raise ValueError('actual processor grid differs from padding-aware resize prediction')
        # BatchFeature.data is exactly what model.generate receives. Keep this
        # control proof as an ordinary object attribute, never a data key.
        object.__setattr__(encoded, _EVIDENCE_ATTRIBUTE, copy.deepcopy(plan))
    return encoded


def identity(processor, encoded, n_frames):
    grid = encoded['video_grid_thw'][0].tolist()
    pixels = int(grid[1] * grid[2] * processor.video_processor.patch_size ** 2)
    effective_frames = int(grid[0] * processor.video_processor.temporal_patch_size)
    result = dict(sampled_frames=int(n_frames), video_grid_thw=grid,
        actual_pixels_per_frame=pixels, processor_effective_frames=effective_frames,
        processor_total_pixels=effective_frames*pixels,
        input_tokens=int(encoded['input_ids'].shape[1]), explicit_size=copy.deepcopy(LEGACY_VIDEO_SIZE),
        max_physical_frames=MAX_FRAMES, truncation=False, implicit_sampling=False)
    try:
        adjustment = object.__getattribute__(encoded, _EVIDENCE_ATTRIBUTE)
    except AttributeError:
        adjustment = None
    if adjustment is not None:
        if _EVIDENCE_ATTRIBUTE in encoded:
            raise ValueError('resize evidence must not be a model input data key')
        result['padding_aware_resize'] = copy.deepcopy(adjustment)
    return result
