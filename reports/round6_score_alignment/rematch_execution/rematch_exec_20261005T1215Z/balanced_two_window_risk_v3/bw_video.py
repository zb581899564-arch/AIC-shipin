"""Explicit legacy-equivalent video pixels; no sampling, truncation or unit guesses."""
import copy

LEGACY_VIDEO_SIZE = {'shortest_edge': 4096, 'longest_edge': 25165824}
MAX_FRAMES = 64
MAX_INPUT = 16384

def encode(processor, *, video_size=None, max_input=MAX_INPUT, **kwargs):
    videos = kwargs.pop('videos')
    metadata = kwargs.pop('video_metadata')
    if len(videos) != 1 or len(metadata) != 1 or not 1 <= int(videos[0].shape[0]) <= MAX_FRAMES:
        raise ValueError('registered one-video/64-frame input required')
    if kwargs.pop('do_sample_frames', False) is not False or kwargs.pop('truncation', False) is not False:
        raise ValueError('implicit sampling/truncation forbidden')
    if any(key.endswith('_kwargs') for key in kwargs):
        raise ValueError('nested overrides forbidden')
    padding = kwargs.pop('padding', True)
    tensors = kwargs.pop('return_tensors', 'pt')
    size = copy.deepcopy(LEGACY_VIDEO_SIZE if video_size is None else video_size)
    if set(size) != {'shortest_edge','longest_edge'} or any(type(x) is not int or x <= 0 for x in size.values()):
        raise ValueError('explicit size contract invalid')
    encoded = processor(**kwargs, videos=videos,
        text_kwargs={'padding': padding, 'truncation': False},
        common_kwargs={'return_tensors': tensors},
        videos_kwargs={'video_metadata': copy.deepcopy(metadata), 'do_sample_frames': False,
                       'return_metadata': True, 'size': size})
    grid = encoded['video_grid_thw'][0].tolist()
    patch = int(processor.video_processor.patch_size)
    pixels = int(grid[1]*grid[2]*patch*patch)
    sampled = int(videos[0].shape[0])
    # The processor size is a total-video pixel budget, not a per-frame max_pixels.
    if sampled*pixels > size['longest_edge'] or pixels <= 0:
        raise ValueError('actual processed video pixels exceed registered total budget')
    if encoded['input_ids'].shape[1] > max_input:
        raise ValueError('actual expanded input exceeds common train/dev/production token contract')
    return encoded

def identity(processor, encoded, n_frames):
    grid = encoded['video_grid_thw'][0].tolist()
    return {'sampled_frames': int(n_frames), 'video_grid_thw': grid,
            'actual_pixels_per_frame': int(grid[1]*grid[2]*processor.video_processor.patch_size**2),
            'input_tokens': int(encoded['input_ids'].shape[1]),
            'explicit_size': copy.deepcopy(LEGACY_VIDEO_SIZE), 'truncation': False}
