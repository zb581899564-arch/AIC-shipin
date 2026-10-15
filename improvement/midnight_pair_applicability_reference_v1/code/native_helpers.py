"""Unchanged native/Mapping-safe decode and dynamic capacity math; no old gate."""
from collections.abc import Mapping
from fractions import Fraction as F
import hashlib
import importlib
import os
from pathlib import Path
import shutil
import model_common as io

def mapping_tensors(value):
    """Accept BatchFeature/UserDict Mapping while retaining original tensor objects."""
    io.require(isinstance(value, Mapping) and bool(value), 'Actual nonempty CPU tensor Mapping required')
    return dict(value)


def verify_files(files):
    for filename, digest in files.items():
        io.checked(filename, digest)


def resource_snapshot(directory):
    values = {line.split(':')[0]: int(line.split(':')[1].split()[0])*1024
              for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    return dict(utc=io.utc(), available_memory_bytes=values['MemAvailable'],
        free_output_disk_bytes=shutil.disk_usage(directory).free, load_average=list(os.getloadavg()), pid=os.getpid())


def tensor_signature(encoded):
    """Full serialization signature, including original strides and raw bits."""
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


def decode_union_once(row, clock, wanted, folder):
    """Decode RGB once against the inherited clock, not per candidate window."""
    import av
    import numpy as np
    from PIL import Image
    output = folder/'RGB_ordinals'; output.mkdir(exist_ok=False)
    items, cursor = [], 0
    points = list(map(F, clock['original_exact_pts']))
    with av.open(row['media']['path']) as container:
        io.require(len(container.streams.video) == 1, 'Original source stream is ambiguous')
        stream = container.streams.video[0]; stream.thread_count = 1
        io.require(stream.index == clock['video_stream_index'] and stream.time_base is not None and
            F(stream.time_base) == F(clock['stream_time_base_exact']) and stream.average_rate is not None and
            F(stream.average_rate) == F(clock['fps_num'], clock['fps_den']), 'Original native source stream identity changed')
        for ordinal, frame in enumerate(container.decode(stream)):
            io.require(ordinal < len(points) and frame.pts is not None and frame.time_base is not None and
                F(frame.pts)*F(frame.time_base) == points[ordinal] and
                (frame.width, frame.height) == (clock['width'], clock['height']), 'Union RGB decode differs from inherited full native clock')
            cursor += 1
            if ordinal not in wanted:
                continue
            image = frame.to_ndarray(format='rgb24')
            io.require(image.dtype == np.uint8 and image.shape == (clock['height'], clock['width'], 3), 'Original RGB24 geometry/dtype changed')
            path = output/(str(ordinal).zfill(9)+'.png')
            with path.open('xb') as stream_file:
                Image.fromarray(image).save(stream_file, format='PNG', compress_level=1, optimize=False)
                stream_file.flush(); os.fsync(stream_file.fileno())
            with Image.open(path) as restored:
                recovered = np.asarray(restored)
                io.require(restored.mode == 'RGB' and np.array_equal(image, recovered), 'Lossless PNG roundtrip changed original RGB')
            items.append(dict(ordinal=ordinal, exact_pts=str(points[ordinal]), path=str(path), bytes=path.stat().st_size,
                sha256=io.sha(path), pixel_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
    io.require(cursor == len(points) and {item['ordinal'] for item in items} == wanted and len(items) == len(wanted),
               'Incomplete single source RGB/union-ordinal denominator')
    receipt = dict(status='PASS_SINGLE_ORIGINAL_RGB_UNION_DECODE_NOT_PROCESSOR_ADMISSION', items=items,
        source_sha256=row['media']['sha256'], original_clock_path=row['clock_path'], original_clock_sha256=row['clock_sha256'],
        inherited_complete_clock_remeasured=False, actual_new_RGB_decode_passes=1, utc=io.utc())
    io.save(folder/'rgb_union.json', receipt)
    return {item['ordinal']: item for item in items}


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
    result['registered_processor_source_sha256'] = contract['processor_source_sha256']
    io.require(result['snapshot']['available_memory_bytes'] > result['upcoming_memory_bound_bytes'] and
        result['snapshot']['free_output_disk_bytes'] > result['remaining_output_bound_bytes'],
        'Actual resources cannot hold this source union/unique-view lossless outputs; retain and stop')
    return result

