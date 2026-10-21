"""First CPU-only nine-native-frame inputs for the fixed motion42 probe.

prepare(root) is single-use and retains successful inputs on every failure.
model_case(root, case_ref) only reloads accepted lossless tensors; it never
decodes media, calls a processor, or changes CUDA visibility.  No model lives
in this module.  Registration binds code_ref, manifest_ref, prior_code_root,
and cut_module_ref before prepare is invoked.
"""
from __future__ import annotations

import argparse
import ast
from fractions import Fraction
import gzip
import hashlib
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import traceback
from types import SimpleNamespace


PARTITION = {'fit': ['S24', 'S15', 'S03', 'S20'],
             'process': ['S02', 'S06', 'S08', 'S23']}
SOURCES = tuple(s for ids in PARTITION.values() for s in ids)
INPUT_KEYS = {'pixel_values', 'image_grid_thw', 'input_ids', 'attention_mask'}
MAX_OUTPUT_BYTES = 20 * 1024 * 1024
FAILURE_RESERVE_BYTES = 64 * 1024
PROMPT = ('Below is a video frame to be re-framed (cropped) to %d:%d.\n'
          'Point out the center of the most important subject or region to keep. '
          'Use normalized integer coordinates in range 0~1000: x is horizontal '
          '(0=left, 1000=right), y is vertical (0=top, 1000=bottom).\n'
          'Output ONLY JSON (no other text): {"center": [x, y]}') % (9, 16)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def ref(path):
    path = Path(path).resolve(strict=True)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def checked(reference, workspace):
    require(isinstance(reference, dict) and type(reference.get('bytes')) is int
            and re.fullmatch('[0-9a-f]{64}', reference.get('sha256', '')),
            'An exact path/bytes/SHA256 reference is required')
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(workspace) and path.is_file(), 'Bound file escaped workspace')
    actual = ref(path)
    require(all(actual[k] == reference[k] for k in actual), 'Bound file identity changed: ' + str(path))
    return path


def readref(reference, workspace):
    return json.loads(checked(reference, workspace).read_text(encoding='utf-8'))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def write_new(path, data):
    with Path(path).open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


class OutputBudget:
    """Use actual encoded bytes, preserving room for a small failure receipt."""
    def __init__(self, root):
        self.root = Path(root)

    def total(self):
        return sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())

    def write(self, path, data):
        path = Path(path)
        require(path.parent.resolve().is_relative_to(self.root) and not path.exists(),
                'Only new files inside this run may be written')
        needed = len(data) + FAILURE_RESERVE_BYTES
        require(self.total() + needed <= MAX_OUTPUT_BYTES,
                'Actual new output exceeds registered20MiB; retain successful files')
        require(shutil.disk_usage(self.root).free >= needed,
                'Actual next durable buffer plus failure receipt cannot fit; retain successful files')
        write_new(path, data)
        return ref(path)

    def save(self, path, value):
        return self.write(path, json_bytes(value))


def interval_start(source_sha256, n_frames):
    require(re.fullmatch('[0-9a-f]{64}', source_sha256 or '') and type(n_frames) is int
            and n_frames >= 9, 'Nine exact native frames and source SHA256 required')
    return int(hashlib.sha256(('motion42:' + source_sha256).encode()).hexdigest(), 16) % (n_frames - 8)


def crop_geometry(width, height):
    """Continuous maximum legal9:16 crop; no native pixels are cropped here."""
    require(type(width) is int and type(height) is int and width > 0 and height > 0,
            'Positive native dimensions required')
    crop_w = min(Fraction(width), Fraction(height * 9, 16))
    crop_h = crop_w * 16 / 9
    return dict(aspect=[9, 16], width_exact=str(crop_w), height_exact=str(crop_h),
                maximum_legal=True, model_receives_complete_native_RGB=True)


def context(root):
    root = Path(root).resolve(strict=True)
    workspace = root.parent.parent.resolve(strict=True)
    registration = json.loads((root / 'registration42.json').read_text(encoding='utf-8'))
    require(checked(registration['code_ref'], workspace) == Path(__file__).resolve(),
            'Exact new motion42 implementation must be registered')
    manifest = readref(registration['manifest_ref'], workspace)
    require(Path(manifest['workspace_root']).resolve(strict=True) == workspace,
            'Input manifest workspace identity changed')
    require(registration.get('source_partition', PARTITION) == PARTITION,
            'The fixed exposed8source partition cannot change')
    return root, workspace, registration, manifest


def dictionary_helper(registration, manifest, workspace):
    """Use the retained store's exact bound-module loader without reading labels."""
    prior = Path(registration['prior_code_root']).resolve(strict=True)
    require(prior.is_relative_to(workspace), 'Retained code root must be inside workspace')
    sys.path.insert(0, str(prior))
    inputs = importlib.import_module('improvement.native_preference_v1.inputs')
    require(Path(inputs.__file__).resolve() == prior / 'improvement/native_preference_v1/inputs.py',
            'A foreign inputs module already owns the retained helper name')
    code = manifest['input_code']
    codec = inputs._bound_module('codec', code['codec'], workspace)
    dictionary = inputs._bound_module('aic_preference_dictionary_' + code['dictionary']['sha256'][:16],
                                       code['dictionary'], workspace)
    return codec, dictionary


def cut_helper(reference, workspace, cv2, np):
    """Load exact original descriptors/constant AST, avoiding unrelated CLI imports."""
    path = checked(reference, workspace)
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    constants, function = {}, []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {'HIST_THRESHOLD', 'GRAY_MAD_THRESHOLD'}:
                require(name not in constants, 'Duplicate production cut threshold')
                constants[name] = ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef) and node.name == 'descriptors':
            function.append(node)
    require(len(function) == 1 and not function[0].decorator_list
            and set(constants) == {'HIST_THRESHOLD', 'GRAY_MAD_THRESHOLD'}
            and all(type(v) in (int, float) and 0 < v <= 1 for v in constants.values()),
            'Exact production descriptor and two finite thresholds required')
    scope = {'cv2': cv2, 'np': np, '__name__': 'bound_production_cut42'}
    exec(compile(ast.Module(body=function, type_ignores=[]), str(path), 'exec'), scope)
    ast_sha256 = hashlib.sha256(ast.dump(function[0], include_attributes=False).encode()).hexdigest()
    return SimpleNamespace(descriptors=scope['descriptors'], descriptor_ast_sha256=ast_sha256, **constants)


def validate_clock(clock, source, media_path):
    n = clock['n_frames']
    require(type(n) is int and n >= 9 and len(clock['original_exact_pts']) == n
            and len(clock['normalized_exact_pts']) == n
            and clock['source_sha256'] == source['source_sha256']
            and Path(clock['source_path']).resolve(strict=True) == media_path,
            'Actual media, complete exact native clock and source identity must agree')
    original = [Fraction(v) for v in clock['original_exact_pts']]
    normalized = [Fraction(v) for v in clock['normalized_exact_pts']]
    first = Fraction(clock['first_original_pts_exact'])
    require(original[0] == first and normalized[0] == 0
            and all(a < b for a, b in zip(original, original[1:]))
            and all(a - first == b for a, b in zip(original, normalized))
            and normalized[-1] < Fraction(clock['physical_end_exact']),
            'No repaired, shifted or nonmonotonic native clock is accepted')
    crop_geometry(clock['width'], clock['height'])


def decode_nine(media, clock, start, av, np):
    """Sequential first decode through the fixed final ordinal; never seek/pad."""
    wanted = list(range(start, start + 9))
    frames, rows = {}, []
    with av.open(str(media), mode='r') as container:
        require(len(container.streams.video) == 1, 'Exactly one video stream required')
        stream = container.streams.video[0]
        for ordinal, frame in enumerate(container.decode(stream)):
            require(ordinal < clock['n_frames'] and frame.pts is not None and frame.time_base is not None,
                    'Decoder ordinal/PTS escaped the original clock')
            exact = Fraction(frame.pts) * Fraction(frame.time_base)
            require(exact == Fraction(clock['original_exact_pts'][ordinal]),
                    'Actual decoded PTS differs from the original exact native clock')
            if ordinal < start:
                continue
            rgb = frame.to_ndarray(format='rgb24')
            require(rgb.dtype == np.uint8 and rgb.shape == (clock['height'], clock['width'], 3),
                    'Actual RGB24 native frame geometry differs')
            rgb = np.ascontiguousarray(rgb)
            frames[ordinal] = rgb
            rows.append(dict(ordinal=ordinal, original_pts_exact=str(exact),
                normalized_pts_exact=clock['normalized_exact_pts'][ordinal],
                rgb_shape=list(rgb.shape), pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
            if ordinal == wanted[-1]:
                break
    require(list(frames) == wanted, 'Missing exact native frame is failure, never empty/padding')
    return frames, rows


def gray_and_cuts(frames, cut, cv2, np):
    ordinals = list(frames)
    height, width = frames[ordinals[0]].shape[:2]
    scale = min(1., 192. / max(width, height))
    small_w, small_h = max(1, round(width * scale)), max(1, round(height * scale))
    grays, comparisons, previous = [], [], None
    for ordinal in ordinals:
        rgb = frames[ordinal]
        # This is exactly production's descriptor on a BGR native frame.
        hist, gray = cut.descriptors(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        if previous is not None:
            distance = float(cv2.compareHist(previous[0], hist, cv2.HISTCMP_BHATTACHARYYA))
            mad = float(np.mean(cv2.absdiff(previous[1], gray)) / 255.0)
            require(np.isfinite(distance) and np.isfinite(mad), 'Nonfinite production cut descriptor')
            reasons = (['HSV_HIST_CUT'] if distance >= cut.HIST_THRESHOLD else [])
            reasons += ['GRAY_MAD_CUT'] if mad >= cut.GRAY_MAD_THRESHOLD else []
            comparisons.append(dict(left_ordinal=ordinal - 1, right_ordinal=ordinal,
                hist_bhattacharyya=distance, gray_mad=mad, is_cut=bool(reasons), reasons=reasons))
        previous = hist, gray
        full_gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        grays.append(cv2.resize(full_gray, (small_w, small_h), interpolation=cv2.INTER_AREA))
    require(len(comparisons) == 8 and max(small_w, small_h) <= 192,
            'All eight native adjacent transitions and maxedge192 grayscale required')
    return np.stack(grays), comparisons


def model_values(values, torch):
    require(set(values) == INPUT_KEYS, 'Exactly the four actual single-image model tensors required')
    require(all(isinstance(v, torch.Tensor) and v.device.type == 'cpu' and v.is_contiguous()
                and not v.requires_grad for v in values.values()), 'CPU dense contiguous model inputs required')
    p, grid = values['pixel_values'], values['image_grid_thw']
    ids, mask = values['input_ids'], values['attention_mask']
    require(p.dtype == torch.float32 and p.ndim == 2 and p.shape[1] == 1536
            and bool(torch.isfinite(p).all()) and grid.dtype == torch.int64 and tuple(grid.shape) == (1, 3),
            'Actual image patch16/temporal2 FP32 and one grid required')
    t, h, w = grid[0].tolist()
    require(t == 1 and h > 0 and w > 0 and h % 2 == w % 2 == 0 and len(p) == t * h * w,
            'One image with merge2 and complete actual grid required')
    require(ids.dtype == mask.dtype == torch.int64 and ids.ndim == mask.ndim == 2
            and ids.shape == mask.shape and ids.shape[0] == 1 and ids.shape[1] > 0
            and bool((ids >= 0).all()) and bool((mask == 1).all()),
            'One unpadded, untruncated exact prefix and all-one attention mask required')
    return t, h, w


def independent_input_QA(processor, values, text, rgb, pixel_sha256, torch):
    """Actual RGB -> resize -> channel/temporal/patch proof plus token expansion."""
    from torchvision.transforms.v2 import functional as TVF
    from torchvision.transforms import InterpolationMode
    t, h, w = model_values(values, torch)
    p = processor.image_processor
    require(p.patch_size == 16 and p.temporal_patch_size == 2 and p.merge_size == 2
            and dict(p.size) == dict(shortest_edge=131072, longest_edge=131072)
            and p.do_resize and p.do_rescale and p.do_normalize and int(p.resample) == 3
            and p.__class__.__name__.endswith('Fast'), 'Original explicit128K fast image profile required')
    require(hashlib.sha256(rgb.tobytes()).hexdigest() == pixel_sha256,
            'Processor source RGB changed after exact native decode')
    image = values['pixel_values'].reshape(h // 2, w // 2, 2, 2, 3, 2, 16, 16)
    image = image.permute(4, 5, 0, 2, 6, 1, 3, 7).reshape(3, 2, h * 16, w * 16)
    require(torch.equal(image[:, 0].contiguous().view(torch.uint8),
                        image[:, 1].contiguous().view(torch.uint8)), 'Single-image temporal duplication must be exact')
    original = torch.from_numpy(rgb).permute(2, 0, 1).contiguous()
    resized = TVF.resize(original, size=[h * 16, w * 16], interpolation=InterpolationMode.BICUBIC, antialias=True)
    # Independent fused normalization follows the installed fast processor's
    # documented float32 operation order, without calling image_processor again.
    mean = torch.tensor(p.image_mean, dtype=torch.float32) * (1. / p.rescale_factor)
    std = torch.tensor(p.image_std, dtype=torch.float32) * (1. / p.rescale_factor)
    expected = TVF.normalize(resized.to(torch.float32), mean, std)
    require(torch.equal(image[:, 0].contiguous().view(torch.uint8), expected.contiguous().view(torch.uint8)),
            'Independent native RGB resize/normalization/channel/patch proof failed')
    marker = processor.vision_start_token + processor.image_token + processor.vision_end_token
    require(text.count(marker) == 1 and text.count(processor.image_token) == 1
            and PROMPT in text and processor.video_token not in text,
            'Exactly one source-owned image marker and original spatial prompt required')
    count = t * h * w // 4
    expanded = text.replace(processor.image_token, processor.image_token * count)
    prefix = processor.tokenizer(expanded, return_tensors='pt', add_special_tokens=False,
                                 padding=False, truncation=False)
    require(all(torch.equal(prefix[k], values[k]) for k in ['input_ids', 'attention_mask']),
            'Independent actual template/image-token expansion must reconstruct both prefix tensors')
    token_id = processor.tokenizer.convert_tokens_to_ids(processor.image_token)
    require(type(token_id) is int and token_id >= 0 and int((values['input_ids'] == token_id).sum()) == count,
            'Actual image token count must equal grid product divided by4')
    return dict(status='PASS_FIRST_INDEPENDENT_NATIVE_RGB_PATCH_PREFIX_FOUR_TENSOR_QA',
                actual_grid=[t, h, w], image_token_id=token_id, image_tokens=count,
                prefix_tokens=values['input_ids'].shape[1], source_RGB_resize_patch_verified=True,
                single_image_temporal_duplicate_verified=True, exact_prefix_verified=True)


def packed_values(values, dictionary, torch):
    # The retained dictionary explicitly supports this visual-key name only.
    mapped = {('pixel_values_videos' if k == 'pixel_values' else k): v for k, v in values.items()}
    payload, report = dictionary.pack(mapped)
    buffer = io.BytesIO()
    torch.save(payload, buffer)
    return gzip.compress(buffer.getvalue(), compresslevel=3), report


def unpack_values(path, dictionary, torch):
    payload = torch.load(io.BytesIO(gzip.decompress(Path(path).read_bytes())), map_location='cpu', weights_only=True)
    restored = dictionary.unpack(payload)
    require(set(restored) == (INPUT_KEYS - {'pixel_values'}) | {'pixel_values_videos'},
            'Durable exact packed single-image tensor schema differs')
    return {('pixel_values' if k == 'pixel_values_videos' else k): v for k, v in restored.items()}


def _prepare(root):
    root, workspace, reg, manifest = context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'prepare requires a dedicated CPU-only child')
    require(not any((root / name).exists() for name in ['prepare_started42.json', 'input_acceptance42.json',
                                                       'failure_prepare42.json', 'sources42', 'cases42']),
            'Single-use preparation: preserve any earlier attempt; no automatic retry')
    budget = OutputBudget(root)
    budget.save(root / 'prepare_started42.json', dict(status='FIRST_CPU_PREPARE_STARTED_NO_AUTOMATIC_RETRY',
        code_ref=reg['code_ref'], manifest_ref=reg['manifest_ref'], source_partition=PARTITION))
    started = time.monotonic()
    import av
    import cv2
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    codec, dictionary = dictionary_helper(reg, manifest, workspace)
    cut = cut_helper(reg['cut_module_ref'], workspace, cv2, np)
    spec = manifest['model_spec']
    model_dir = Path(spec['model_dir']).resolve(strict=True)
    require(model_dir.is_relative_to(workspace) and isinstance(spec['revision'], str) and spec['revision'],
            'Existing local pinned original BASE processor only')
    # Bind actual local processor/tokenizer files, without rereading model weights.
    processor_assets = []
    for item in manifest['model_files']:
        if Path(item['path']).suffix in {'.json', '.txt', '.jinja', '.model'}:
            checked(item, workspace)
            processor_assets.append(item)
    require(processor_assets, 'Retained local processor assets must be bound')
    processor = AutoProcessor.from_pretrained(spec['model_dir'], revision=spec['revision'],
        local_files_only=True, trust_remote_code=False, min_pixels=131072, max_pixels=131072)
    processor_code = [ref(inspect.getfile(type(value))) for value in [processor, processor.image_processor]]
    decode_profile = dict(PyAV_version=av.__version__, libav_versions=av.library_versions,
        sequential_decode=True, seek=False, RGB_format='rgb24', native_clock_repaired=False,
        OpenCV_version=cv2.__version__, numpy_version=np.__version__, torch_version=str(torch.__version__))
    processor_ref = budget.save(root / 'processor_metadata42.json', dict(model_spec=spec,
        asset_manifest_ref=reg['manifest_ref'], processor_assets=processor_assets, code_refs=processor_code,
        processor_class=type(processor).__name__, image_processor_class=type(processor.image_processor).__name__,
        image_processor_dict=processor.image_processor.to_dict(), min_pixels=131072, max_pixels=131072,
        prompt=PROMPT, local_files_only=True, trust_remote_code=False,
        patch_size=16, temporal_patch_size=2, merge_size=2, decode_profile=decode_profile,
        cut_descriptor_ast_sha256=cut.descriptor_ast_sha256, model_calls=0))
    source_dir, case_dir = root / 'sources42', root / 'cases42'
    source_dir.mkdir()
    case_dir.mkdir()
    catalog = {s['id']: s for s in manifest['scopes']['train']['sources']}
    require(len(catalog) == len(manifest['scopes']['train']['sources']) and set(SOURCES) <= set(catalog),
            'All fixed8sources must exist in the actual train catalog')
    source_refs, case_refs, eligible = [], [], []
    new_processor_calls = 0
    for sid in SOURCES:
        source = catalog[sid]
        require(source['group'] == 'train' and source['source_sha256'] == source['media_ref']['sha256'],
                'Selected fixed source/media byte identity required')
        media = checked(source['media_ref'], workspace)
        clock = readref(source['clock_ref'], workspace)
        validate_clock(clock, source, media)
        start = interval_start(source['source_sha256'], clock['n_frames'])
        frames, native_rows = decode_nine(media, clock, start, av, np)
        grays, comparisons = gray_and_cuts(frames, cut, cv2, np)
        folder = source_dir / sid
        folder.mkdir()
        gray_buffer = io.BytesIO()
        np.savez_compressed(gray_buffer, gray=grays, native_ordinals=np.array(list(frames), dtype=np.int64),
            original_exact_pts=np.array([r['original_pts_exact'] for r in native_rows]),
            normalized_exact_pts=np.array([str(r['normalized_pts_exact']) for r in native_rows]))
        gray_ref = budget.write(folder / 'gray42.npz', gray_buffer.getvalue())
        with np.load(checked(gray_ref, workspace), allow_pickle=False) as loaded:
            require(np.array_equal(loaded['gray'], grays)
                    and loaded['native_ordinals'].tolist() == list(frames)
                    and loaded['original_exact_pts'].tolist() == [r['original_pts_exact'] for r in native_rows]
                    and loaded['normalized_exact_pts'].tolist() == [str(r['normalized_pts_exact']) for r in native_rows],
                    'Actual retained grayscale/native/PTS buffer must read back exactly')
        same_shot = not any(r['is_cut'] for r in comparisons)
        row = dict(sid=sid, role=next(k for k, ids in PARTITION.items() if sid in ids),
            source_sha256=source['source_sha256'], media_ref=source['media_ref'], clock_ref=source['clock_ref'],
            selection='int(sha256((motion42:+source_sha256).encode()),16)%(n_frames-8)',
            interval_start=start, native_ordinals=list(frames), native_frames=native_rows,
            native_width=clock['width'], native_height=clock['height'],
            crop_geometry=crop_geometry(clock['width'], clock['height']), gray_ref=gray_ref,
            gray_shape=list(grays.shape), grayscale_maxedge=192, cut_module_ref=reg['cut_module_ref'],
            cut_descriptor_ast_sha256=cut.descriptor_ast_sha256, decode_profile=decode_profile,
            cut_thresholds=dict(hist=cut.HIST_THRESHOLD, gray_mad=cut.GRAY_MAD_THRESHOLD),
            adjacent_cut_comparisons=comparisons, eligible=same_shot,
            eligibility_reason='NINE_EXACT_NATIVE_FRAMES_SAME_PRODUCTION_SHOT' if same_shot else 'CUT_IN_FIXED_INTERVAL_NO_REPLACEMENT',
            anchor_ordinals=[start, start + 4, start + 8], evaluation_only_ordinal=start + 4,
            middle_used_for_flow_ROI_fallback_or_correction=False, labels_read=False,
            model_calls=0, new_training=0, cases=[])
        # Preserve the full native/cut evidence even if a later processor fails.
        native_ref = budget.save(folder / 'native_input42.json', row)
        if same_shot:
            eligible.append(sid)
            for offset in [0, 4, 8]:
                ordinal = start + offset
                uid = sid + '_N' + str(ordinal).zfill(8)
                text = processor.apply_chat_template([dict(role='user', content=[dict(type='image'),
                    dict(type='text', text=PROMPT)])], tokenize=False, add_generation_prompt=True,
                    enable_thinking=False)
                # This is the first real new single-image processor call.
                encoded = processor(text=[text], images=[Image.fromarray(frames[ordinal])],
                                    padding=True, return_tensors='pt')
                new_processor_calls += 1
                require(set(encoded) == INPUT_KEYS, 'Processor returned unexpected/missing model inputs')
                values = {k: encoded[k].contiguous() for k in INPUT_KEYS}
                data, report = packed_values(values, dictionary, torch)
                cache_ref = budget.write(case_dir / (uid + '.pt.gz'), data)
                # No independent QA precedes durable storage of the first result.
                primary = dict(uid=uid, sid=sid, ordinal=ordinal, anchor_offset=offset,
                    role=row['role'], source_sha256=source['source_sha256'], native_input_ref=native_ref,
                    pixel_sha256=native_rows[offset]['pixel_sha256'], exact_pts=native_rows[offset]['original_pts_exact'],
                    cache_ref=cache_ref, storage_pixel_alias='pixel_values_videos', dictionary_report=report,
                    processor_ref=processor_ref, raw_template=text, prompt=PROMPT,
                    input_signature=codec.signature(values), durable_before_first_independent_QA=True,
                    evaluation_only=offset == 4, labels_read=False)
                primary_ref = budget.save(case_dir / (uid + '.primary.json'), primary)
                require(report['pixel_values_videos']['storage'] == 'PIXEL_UINT8_BIT_LUT_V1',
                        'Lossless byte dictionary required; no large original-tensor fallback')
                restored = unpack_values(checked(cache_ref, workspace), dictionary, torch)
                require(codec.exact_equal(values, restored), 'Durable four-tensor reload lost actual original bits')
                qa = independent_input_QA(processor, restored, text, frames[ordinal], primary['pixel_sha256'], torch)
                case = dict(primary, primary_ref=primary_ref, QA=qa, packed_roundtrip='ALL_FOUR_TENSORS_BIT_EXACT',
                            status='PASS_FIRST_NATIVE_SPATIAL_SINGLE_IMAGE_INPUT_42')
                case_ref = budget.save(case_dir / (uid + '.json'), case)
                row['cases'].append(case_ref)
                case_refs.append(case_ref)
                del encoded, values, restored, data
        final_source_ref = budget.save(folder / 'source42.json', dict(row, native_input_ref=native_ref))
        source_refs.append(final_source_ref)
        del frames, grays
    require(len(source_refs) == 8 and new_processor_calls == len(case_refs) == 3 * len(eligible) <= 24,
            'All fixed8source coverage and at most3cases/source24total required')
    result = dict(status='PASS_CPU_NATIVE_MOTION_INPUTS_42_NOT_GPU_ADMISSION', source_refs=source_refs,
        case_refs=case_refs, eligible_source_ids=eligible, source_partition=PARTITION,
        sources_covered=8, ineligible_source_ids=[s for s in SOURCES if s not in eligible],
        actual_new_native_intervals_decoded=8, actual_new_native_frames_retained_as_gray=72,
        actual_new_processor_calls=new_processor_calls, new_model_calls=0, new_training=0,
        processor_ref=processor_ref, registration_ref=ref(root / 'registration42.json'),
        code_ref=reg['code_ref'], input_code_refs=manifest['input_code'], model_spec=spec,
        same_shot_eligibility_checked_before_processor=True, source_replacement=False,
        middle_frame_only_for_evaluation=True, original_clocks_modified=False,
        original_baseline_modified=False, automatic_GPU=False, seconds=time.monotonic() - started,
        output_budget_bytes=MAX_OUTPUT_BYTES, output_bytes_before_acceptance=budget.total())
    budget.save(root / 'input_acceptance42.json', result)
    return result


def prepare(root):
    """Dedicated CPU-child entry point; preserve the first natural failure."""
    try:
        return _prepare(root)
    except BaseException:
        path = Path(root) / 'failure_prepare42.json'
        if not path.exists():
            write_new(path, json_bytes(dict(status='ACTUAL_CPU_PREPARE_FAILURE_RETAIN_ALL_NO_AUTOMATIC_RETRY',
                traceback=traceback.format_exc(), new_model_calls=0, new_training=0)))
        raise


def model_case(root, case_ref):
    """Return (bound accepted case, exactly four CPU tensors); no processor/decode."""
    root, workspace, reg, manifest = context(root)
    accepted = json.loads((root / 'input_acceptance42.json').read_text(encoding='utf-8'))
    require(accepted['status'] == 'PASS_CPU_NATIVE_MOTION_INPUTS_42_NOT_GPU_ADMISSION'
            and accepted['registration_ref'] == ref(root / 'registration42.json')
            and case_ref in accepted['case_refs'], 'Only exact accepted case references may be reloaded')
    case = readref(case_ref, workspace)
    require(Path(case_ref['path']).resolve().is_relative_to(root)
            and case['status'] == 'PASS_FIRST_NATIVE_SPATIAL_SINGLE_IMAGE_INPUT_42'
            and case['sid'] in accepted['eligible_source_ids']
            and case['packed_roundtrip'] == 'ALL_FOUR_TENSORS_BIT_EXACT'
            and case['prompt'] == PROMPT and case['labels_read'] is False,
            'Accepted source/case/prompt/QA identity differs')
    native = readref(case['native_input_ref'], workspace)
    require(native['eligible'] and case['ordinal'] == native['interval_start'] + case['anchor_offset']
            and case['anchor_offset'] in [0, 4, 8] and case['evaluation_only'] == (case['anchor_offset'] == 4)
            and case['source_sha256'] == native['source_sha256']
            and case['pixel_sha256'] == native['native_frames'][case['anchor_offset']]['pixel_sha256'],
            'Reloaded single-image native ownership or evaluation-only role differs')
    import torch
    codec, dictionary = dictionary_helper(reg, manifest, workspace)
    values = unpack_values(checked(case['cache_ref'], workspace), dictionary, torch)
    model_values(values, torch)
    require(codec.signature(values) == case['input_signature'], 'Actual four-tensor reload signature differs')
    return case, values


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-root', required=True)
    args = parser.parse_args()
    # CLI is itself the dedicated CPU subprocess.  Imports and model_case do
    # not alter a caller's GPU visibility or runtime environment.
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    print(json.dumps(prepare(args.run_root), allow_nan=False))
