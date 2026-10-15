"""Original native/grid/dynamic capacity pure helpers and one source RGB decode."""
from collections.abc import Mapping
from fractions import Fraction as F
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import facts_common as io

def mapping_tensors(encoded):
    io.require(isinstance(encoded, Mapping) and bool(encoded), 'Actual nonempty CPU tensor Mapping required')
    return dict(encoded)


def original_grid(end):
    """Complete original zero-origin geometry; never use an observed clip origin."""
    end = F(end)
    io.require(end > 0, 'Positive measured original physical endpoint required')
    if end <= 15:
        return {(F(0), end)}
    windows, start = set(), F(0)
    while start+15 <= end:
        windows.add((start, start+15)); start += F(15, 2)
    windows.add((end-15, end))
    return windows


def native_view(view, source, clock):
    """Pure full-clock/native64 validator and stable actual-input identity."""
    points = list(map(F, clock['original_exact_pts']))
    end = F(clock['physical_end_exact'])
    io.require(points and points[0] == 0 and len(points) == clock['native_frames'] == source['n_frames'] and
        all(a < b for a, b in zip(points, points[1:])) and end > points[-1] and
        clock['original_zero_origin_verified'] is True and F(clock['first_original_pts_exact']) == 0 and
        clock['timeline_shift_applied'] is False and F(clock['last_frame_duration_exact']) == end-points[-1] and
        (clock['width'], clock['height'], clock['fps_num'], clock['fps_den']) ==
        (source['width'], source['height'], source['fps_num'], source['fps_den']) and
        F(source['physical_end_exact']) == end and source['source_sha256'] == source['source_key'],
        'Inherited complete original clock/source identity changed; no endpoint/fps repair')
    io.require(type(source['width']) is int and type(source['height']) is int and
        source['width'] > 0 and source['height'] > 0 and type(source['fps_num']) is int and
        type(source['fps_den']) is int and source['fps_num'] > 0 and source['fps_den'] > 0,
        'Actual positive source geometry and nominal fps required')
    start, stop = F(view['window_start']), F(view['window_end'])
    io.require((start, stop) in original_grid(end) and 0 <= start < stop <= end,
               'Fixed40 view is not an original-source zero-origin 15/7.5 grid window')
    eligible = [i for i, point in enumerate(points) if start <= point < stop]
    io.require(len(eligible) >= 64, 'Fewer than 64 distinct original frames; retain and reject without padding')
    ordinals = [eligible[0]+j*(len(eligible)-1)//63 for j in range(64)]
    samples = [str(points[i]) for i in ordinals]
    io.require(view['source_frame_ordinals'] == ordinals and list(map(F, view['sample_exact_pts'])) == list(map(F, samples)) and
        view['source_name'] == source['video_id'] and view['fixed_case_id'] == source['case_id'] and
        view['source_sha256'] == source['source_sha256'] and view['source_clock_sha256'] == source['clock_sha256'] and
        view['window_role'] == 'overlap' and view['view_roles'] == ['overlap'],
        'Registered fixed40 view/native64/full-source/overlap identity differs')
    identity = dict(source_sha256=source['source_sha256'], source_clock_sha256=source['clock_sha256'],
        window_start=str(start), window_end=str(stop), source_frame_ordinals=ordinals, sample_exact_pts=samples)
    return dict(view, window_start=str(start), window_end=str(stop), sample_exact_pts=samples,
        input_view_key=hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest())


def resource_snapshot(directory):
    values = {line.split(':')[0]: int(line.split(':')[1].split()[0])*1024
              for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    return dict(utc=io.utc(), available_memory_bytes=values['MemAvailable'],
        free_output_disk_bytes=shutil.disk_usage(directory).free, load_average=list(os.getloadavg()), pid=os.getpid())


def capacity_geometry(source, size, patch_size, merge_size, temporal_patch_size, resize):
    """Pure original smart_resize planning, not a processor/encoder call."""
    io.require(set(size) == {'shortest_edge', 'longest_edge'} and all(type(size[key]) is int and size[key] > 0 for key in size) and
        (patch_size, merge_size, temporal_patch_size) == (16, 2, 2), 'Original explicit Qwen3 video patch/resize contract required')
    height, width = resize(num_frames=64, height=source['height'], width=source['width'], temporal_factor=temporal_patch_size,
        factor=patch_size*merge_size, min_pixels=size['shortest_edge'], max_pixels=size['longest_edge'])
    padded_frames = ((64+temporal_patch_size-1)//temporal_patch_size)*temporal_patch_size
    io.require(type(height) is int and type(width) is int and height > 0 and width > 0 and
        height % (patch_size*merge_size) == width % (patch_size*merge_size) == 0 and padded_frames == 64 and
        padded_frames*height*width <= size['longest_edge'], 'Original smart_resize total-video geometry exceeds the bound; no resource-gate bypass')
    grid = [padded_frames//temporal_patch_size, height//patch_size, width//patch_size]
    shape = [grid[0]*grid[1]*grid[2], 3*temporal_patch_size*patch_size*patch_size]
    pixel_bytes = shape[0]*shape[1]*4
    io.require(pixel_bytes == padded_frames*height*width*3*4, 'Dense float32 patch tensor accounting differs')
    return dict(native_frames=64, resized_height=height, resized_width=width, video_grid_thw=grid,
        pixel_values_shape=shape, pixel_values_dtype='torch.float32', pixel_tensor_bytes=pixel_bytes,
        maximum_input_ids_and_attention_bytes=16384*2*8, grid_tensor_bytes=3*8,
        tensor_payload_bound_bytes=pixel_bytes+16384*2*8+3*8,
        size_longest_edge_scope='TOTAL_VIDEO_TEMPORAL_SPATIAL_PIXELS', actual_processor_calls=0)


def capacity_numbers(source, wanted_count, view_count, geometry):
    io.require(type(wanted_count) is int and wanted_count >= 0 and type(view_count) is int and view_count >= 1,
               'Actual remaining source/view denominator required')
    pixel_bytes = source['width']*source['height']*3
    rgb64 = 64*pixel_bytes; tensor = geometry['tensor_payload_bound_bytes']
    png = pixel_bytes+((pixel_bytes//65535)+1)*32+65536
    need_disk = wanted_count*png+view_count*(rgb64+tensor+(rgb64+tensor)//1000+262144)
    # Include full original-size float32 transform scratch as well as the
    # resized patch tensor, serializer signatures and restored cached tensors.
    need_memory = 4*rgb64+6*max(4*rgb64,tensor)+32*pixel_bytes
    return dict(upcoming_memory_bound_bytes=need_memory, remaining_output_bound_bytes=need_disk,
        wanted_original_ordinals=wanted_count, remaining_unique_views=view_count,
        original_rgb64_bytes=rgb64, geometry=geometry, resource_threshold_derived_from_original_implementation=True)


def capacity(directory, source, wanted_count, view_count, processor, contract):
    video = processor.video_processor
    module = importlib.import_module(video.__class__.__module__)
    io.require(str(Path(module.__file__).resolve()) == contract['processor_source_path'] and
        io.sha(module.__file__) == contract['processor_source_sha256'] and video.size == contract['video_size'],
        'Actual original smart_resize source/config differs from the registered capacity proof')
    geometry = capacity_geometry(source, dict(video.size), video.patch_size, video.merge_size, video.temporal_patch_size, module.smart_resize)
    result = capacity_numbers(source, wanted_count, view_count, geometry)
    result['snapshot'] = resource_snapshot(directory)
    result['processor_source_sha256'] = contract['processor_source_sha256']
    io.require(result['snapshot']['available_memory_bytes'] > result['upcoming_memory_bound_bytes'] and
        result['snapshot']['free_output_disk_bytes'] > result['remaining_output_bound_bytes'],
        'Actual resources cannot hold this source union/unique-view lossless outputs; retain and stop')
    return result


def tensor_signature(encoded):
    import torch
    encoded = mapping_tensors(encoded)
    result = {}
    for key, value in encoded.items():
        io.require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.layout == torch.strided,
                   'Only original dense CPU tensors can be cached')
        raw = value.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        result[key] = dict(shape=list(value.shape), stride=list(value.stride()), dtype=str(value.dtype),
            layout=str(value.layout), storage_offset=value.storage_offset(), requires_grad=value.requires_grad,
            bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    return result


def decode_union_once(source, clock, wanted, folder):
    """Only new fixed40 RGB is decoded, once per registered complete source."""
    import av
    import numpy as np
    from PIL import Image
    output = folder/'RGB_ordinals'; output.mkdir(exist_ok=False)
    points = list(map(F, clock['original_exact_pts'])); items, cursor = [], 0
    with av.open(source['source_path']) as container:
        io.require(len(container.streams.video) == 1, 'Original source must have one unambiguous video stream')
        stream = container.streams.video[0]
        io.require(stream.average_rate is not None and F(stream.average_rate) == F(source['fps_num'], source['fps_den']),
                   'Actual original nominal fps differs from the bound successful clock')
        for ordinal, frame in enumerate(container.decode(stream)):
            io.require(ordinal < len(points) and frame.pts is not None and frame.time_base is not None and
                F(frame.pts)*F(frame.time_base) == points[ordinal] and
                (frame.width, frame.height) == (source['width'], source['height']), 'Decoded source differs from bound full native clock')
            cursor += 1
            if ordinal not in wanted:
                continue
            image = frame.to_ndarray(format='rgb24')
            io.require(image.dtype == np.uint8 and image.shape == (source['height'], source['width'], 3), 'Original RGB geometry changed')
            path = output/(str(ordinal).zfill(9)+'.png')
            with path.open('xb') as destination:
                Image.fromarray(image).save(destination, format='PNG', compress_level=1, optimize=False)
                destination.flush(); os.fsync(destination.fileno())
            with Image.open(path) as restored:
                restored.load()
                io.require(restored.mode == 'RGB' and np.array_equal(image, np.asarray(restored)), 'Lossless original PNG roundtrip changed bits')
            items.append(dict(ordinal=ordinal, exact_pts=str(points[ordinal]), path=str(path), bytes=path.stat().st_size,
                sha256=io.sha(path), pixel_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
    io.require(cursor == len(points) and len(items) == len(wanted) and {item['ordinal'] for item in items} == wanted,
               'Incomplete single-source full-clock decode or wanted RGB union')
    io.save(folder/'rgb_union.json', dict(status='PASS_SINGLE_ORIGINAL_RGB_UNION_DECODE_NOT_PROCESSOR_ADMISSION',
        source_name=source['video_id'], fixed_case_id=source['case_id'], source_sha256=source['source_sha256'],
        original_clock_path=source['clock_path'], original_clock_sha256=source['clock_sha256'], items=items,
        actual_new_RGB_decode_passes=1, inherited_complete_clock_remeasured=False, inherited_PNGs=0, utc=io.utc()))
    return {item['ordinal']: item for item in items}

