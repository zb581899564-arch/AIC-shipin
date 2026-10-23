"""Use actual same-geometry caches, not a high-resolution global worst case."""
import math
from pathlib import Path
import shutil

from summary_inputs82 import CACHE, case_name
from t_io import ROOT, check, identity, read


def geometry_references():
    refs = read(ROOT / 'pilot_input_qa29/completion.json')['accepted']
    views = read(ROOT / 'description_inputs64/all_physical_CPU_completion.json')['views']
    refs += [ref for pair in views.values() for ref in pair.values()]
    result = {}
    for ref in refs:
        cpu = read(check(ref)); meta = read(check(cpu['input']))
        pixel = cpu['detail']['tensor_signature']['pixel_values_videos']
        if pixel['dtype'] != 'torch.float32':
            raise ValueError('Known same-processor pixel dtype differs')
        key = (meta['width'], meta['height'])
        signature = dict(shape=pixel['shape'], dtype=pixel['dtype'])
        if key in result and result[key]['signature'] != signature:
            raise ValueError('Native64 same-geometry reference has inconsistent processor cost')
        result[key] = dict(signature=signature, original_CPU=ref,
            pixel_tensor_bytes=4 * math.prod(pixel['shape']))
    return result


def remaining_capacity(planned, exact):
    geometries = geometry_references(); estimate = 0; rows = []; peak_pool = 0
    for row in planned:
        source = row['source']; clock = read(check(source['clock']))
        windows = [w for w in row['windows'] if case_name(source, w) not in exact]
        if not windows:
            continue
        dimensions = (clock['width'], clock['height'])
        if dimensions not in geometries:
            raise ValueError('No accepted same-geometry processor cost reference; first profile separately')
        reference = geometries[dimensions]
        raw_bytes = 64 * dimensions[0] * dimensions[1] * 3
        # Exact serialized tensor dimensions are content-independent at fixed64
        # frames/geometry. Full allowed text budget plus native metadata is extra.
        metadata_bytes = 4 * Path(source['clock']['path']).stat().st_size + 1048576
        window_upper = raw_bytes + reference['pixel_tensor_bytes'] + 2 * 16384 * 8 + metadata_bytes
        subtotal = len(windows) * window_upper; estimate += subtotal
        peak_pool = max(peak_pool, len({i for w in windows for i in w['source_frame_ordinals']})
                        * dimensions[0] * dimensions[1] * 3)
        rows.append(dict(source=source['sid'], first_windows=len(windows), geometry=list(dimensions),
            same_geometry_reference=reference, estimated_uncompressed_cache_bytes=subtotal))
    free = shutil.disk_usage(CACHE.parent).free
    memory = {line.split(':')[0]: int(line.split()[1]) * 1024
              for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')}
    if estimate > free or peak_pool > memory['MemAvailable']:
        raise RuntimeError('Actual remaining cache/source-pool estimate exceeds current capacity')
    return dict(per_source=rows, first_missing_inputs=sum(r['first_windows'] for r in rows),
        estimated_uncompressed_cache_bytes=estimate, actual_tmpfs_free=free,
        largest_source_RGB_pool_bytes=peak_pool, actual_available_memory=memory['MemAvailable'],
        old82_global_max_multiplier_not_used=True, all_new_RGB_retained=True)


def check_actual_geometry(ref, reference):
    cpu = read(check(ref)); pixel = cpu['detail']['tensor_signature']['pixel_values_videos']
    if dict(shape=pixel['shape'], dtype=pixel['dtype']) != reference['signature']:
        raise ValueError('Actual first new processor grid differs from geometry-specific capacity proof')
