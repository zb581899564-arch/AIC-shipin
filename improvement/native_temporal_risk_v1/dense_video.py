"""Prospective 128-frame wrapper; the original total pixel budget is unchanged."""
import copy

LEGACY_VIDEO_SIZE = {'shortest_edge': 4096, 'longest_edge': 25165824}
MAX_FRAMES = 128
MAX_INPUT = 16384


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
    encoded = processor(**kwargs, videos=videos,
        text_kwargs={'padding': padding, 'truncation': False},
        common_kwargs={'return_tensors': tensors},
        videos_kwargs={'video_metadata': copy.deepcopy(metadata), 'do_sample_frames': False,
                       'return_metadata': True, 'size': size})
    grid = encoded['video_grid_thw'][0].tolist()
    pixels = int(grid[1] * grid[2] * processor.video_processor.patch_size ** 2)
    effective_frames = int(grid[0] * processor.video_processor.temporal_patch_size)
    if (int(videos[0].shape[0]) * pixels > size['longest_edge'] or
            effective_frames * pixels > size['longest_edge'] or pixels <= 0):
        raise ValueError('actual processed video pixels exceed unchanged total budget')
    if not 0 < int(encoded['input_ids'].shape[1]) <= MAX_INPUT:
        raise ValueError('expanded input exceeds 16384 tokens; no truncation permitted')
    return encoded


def identity(processor, encoded, n_frames):
    grid = encoded['video_grid_thw'][0].tolist()
    pixels = int(grid[1] * grid[2] * processor.video_processor.patch_size ** 2)
    effective_frames = int(grid[0] * processor.video_processor.temporal_patch_size)
    return dict(sampled_frames=int(n_frames), video_grid_thw=grid,
        actual_pixels_per_frame=pixels, processor_effective_frames=effective_frames,
        processor_total_pixels=effective_frames*pixels,
        input_tokens=int(encoded['input_ids'].shape[1]), explicit_size=copy.deepcopy(LEGACY_VIDEO_SIZE),
        max_physical_frames=MAX_FRAMES, truncation=False, implicit_sampling=False)
